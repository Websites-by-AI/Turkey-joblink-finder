"""Embeddings, with a persistent cache and three honest backends.

Measured 2026-09-13 (so this module is written around it):
  * `api-inference.huggingface.co` is DEAD (connection closed, no HTTP response). The live router is
    `https://router.huggingface.co/hf-inference/models/<repo>` or the OpenAI-compatible
    `https://router.huggingface.co/v1/embeddings`.
  * Free account = **$0.10 / month** of Inference Providers credit; PRO $9/mo = $2. A 5k-ad corpus
    re-embedded per deploy would eat that instantly. So: embed ONCE, store the vector, never re-pay.

Backends, in the order you should actually use them:
  ``off``     BM25 + skill lexicon only (default; zero cost, already good on short TR ads)
  ``local``   sentence-transformers / ONNX inside the crawler container (free, best for bulk)
  ``router``  HF Inference Providers (fine for a per-query rerank on a handful of texts)

Every vector is cached in SQLite keyed by sha1(model + text), so re-running the pipeline costs
nothing and a Space restart loses no work.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sqlite3
from typing import Iterable

import httpx

from .config import SETTINGS

ROUTER_HF = "https://router.huggingface.co/hf-inference/models/{model}"
ROUTER_V1 = "https://router.huggingface.co/v1"

DDL = """
CREATE TABLE IF NOT EXISTS embeddings (
  key   TEXT PRIMARY KEY,
  model TEXT NOT NULL,
  dim   INTEGER,
  vec   TEXT NOT NULL,
  ts    TEXT
);
"""


def _l2(v: list[float]) -> list[float]:
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def cos(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    return sum(x * y for x, y in zip(a, b))


class Embedder:
    """Unified interface; ``enabled`` False -> callers fall back to their lexical score."""

    def __init__(self, db: sqlite3.Connection | None = None, mode: str | None = None,
                 model: str | None = None):
        self.db = db
        self.model = model or SETTINGS.hf_embed_model
        self.last_error = ""
        forced = (mode or SETTINGS.hf_embed_mode or "auto").lower()
        self.mode = self._auto_mode() if forced == "auto" else forced
        self.token = SETTINGS.hf_token
        self.mem: dict[str, list[float]] = {}
        if self.db is not None:
            self.db.executescript(DDL)
            self.db.commit()

    def _auto_mode(self) -> str:
        if SETTINGS.hf_token:
            return "router"
        try:                                   # local install wins: free and offline-safe
            import sentence_transformers  # noqa: F401
            return "local"
        except Exception:
            return "off"

    @property
    def enabled(self) -> bool:
        return self.mode in ("router", "local") and bool(self.token or self.mode == "local")

    def status(self) -> dict:
        return {"mode": self.mode, "model": self.model, "enabled": self.enabled,
                "token": "set" if self.token else "unset", "error": self.last_error}

    # ---------------- cache ----------------
    @staticmethod
    def _key(model: str, text: str) -> str:
        return hashlib.sha1(f"{model}|{text}".encode("utf-8")).hexdigest()

    def _cache_get(self, text: str) -> list[float] | None:
        if self.db is None:
            return self.mem.get(text)
        if text in self.mem:
            return self.mem[text]
        row = self.db.execute("SELECT vec FROM embeddings WHERE key=? AND model=?",
                              (self._key(self.model, text), self.model)).fetchone()
        if row is None:
            return None
        v = json.loads(row[0])
        self.mem[text] = v
        return v

    def _cache_put(self, text: str, vec: list[float]) -> None:
        self.mem[text] = vec
        if self.db is None:
            return
        from .models import now_iso
        self.db.execute("INSERT OR REPLACE INTO embeddings(key,model,dim,vec,ts) VALUES(?,?,?,?,?)",
                        (self._key(self.model, text), self.model, len(vec), json.dumps(vec), now_iso()))
        self.db.commit()

    # ---------------- backends ----------------
    def embed(self, texts: list[str], *, truncate: int = 1800,
              persist: bool = True) -> dict[str, list[float]]:
        out: dict[str, list[float]] = {}
        todo: list[str] = []
        for t in dict.fromkeys(x[:truncate] for x in texts if x):
            hit = self._cache_get(t)
            if hit:
                out[t] = hit
            else:
                todo.append(t)
        if not todo or not self.enabled:
            return out
        vectors: list[list[float]] = []
        try:
            # Batch small: one POST with 5k ads is a 9 MB body and providers reject it. 8 texts per
            # request also means one transient 5xx costs us 8 texts, not the whole corpus.
            size = 8 if self.mode == "router" else 64
            for i in range(0, len(todo), size):
                chunk = todo[i:i + size]
                vecs = self._router(chunk) if self.mode == "router" else self._local(chunk)
                if len(vecs) != len(chunk):
                    raise ValueError(f"provider returned {len(vecs)} vectors for {len(chunk)} texts")
                vectors.extend(vecs)
        except PermissionError as exc:
            self.mode = "off"
            self.last_error = str(exc)
            return out
        except Exception as exc:  # noqa: BLE001 - a model outage must not kill ingestion
            self.mode = "off"
            self.last_error = f"{type(exc).__name__}: {str(exc)[:180]}"
            if not vectors:
                return out
        for t, v in zip(todo, vectors):
            v = _l2(list(v))
            if persist:
                self._cache_put(t, v)
            else:
                self.mem[t] = v
            out[t] = v
        return out

    def _router(self, texts: list[str]) -> list[list[float]]:
        headers = {"Authorization": f"Bearer {self.token}", "content-type": "application/json"}
        with httpx.Client(timeout=60.0) as c:
            # OpenAI-compatible route first: it is the documented 2026 path and works for any
            # model a provider serves; fall back to the model-scoped hf-inference route.
            r = c.post(f"{ROUTER_V1}/embeddings", headers=headers,
                       json={"model": self.model, "input": texts})
            if r.status_code == 403 and "Inference Providers" in r.text:
                raise PermissionError(
                    "token authenticates but lacks the Inference Providers scope - create a "
                    "fine-grained token with that permission (HF Settings -> Access Tokens)")
            if r.status_code in (400, 404, 422):
                r = c.post(ROUTER_HF.format(model=self.model), headers=headers,
                       json={"inputs": texts, "parameters": {"truncate": True, "normalize": True}})
            if r.status_code == 403 and "Inference Providers" in r.text:
                raise PermissionError(
                    "token authenticates but lacks the Inference Providers scope - create a "
                    "fine-grained token with that permission (HF Settings -> Access Tokens)")
            r.raise_for_status()
            data = r.json()
        if isinstance(data, dict) and data.get("error"):
            raise RuntimeError(f"router: {str(data['error'])[:160]}")
        if "data" in data:
            return [d["embedding"] for d in sorted(data["data"], key=lambda d: d.get("index", 0))]
        flat = data
        while isinstance(flat, list) and flat and isinstance(flat[0], list) and not isinstance(flat[0][0], (int, float)):
            flat = flat[0]
        if flat and isinstance(flat[0], dict):
            return [x["embedding"] for x in flat]
        if flat and isinstance(flat[0], list):
            return flat
        return [flat]

    def cost_note(self, n_texts: int, avg_chars: int = 1500) -> str:
        """Rough token count so a free-tier user knows before they hit the wall ($0.10/month)."""
        toks = int(n_texts * avg_chars / 3.5)
        return f"~{toks:,} tokens for {n_texts} texts; free HF credit is $0.10/mo, so cache aggressively"

    def _local(self, texts: list[str]) -> list[list[float]]:
        from sentence_transformers import SentenceTransformer  # type: ignore
        key = "_st_" + self.model
        st = getattr(self, key, None) or SentenceTransformer(self.model, device="cpu")
        setattr(self, key, st)
        prefix = "query: " if "e5" in self.model else ""      # e5 needs query/passage prefixes
        return [list(v) for v in st.encode([prefix + t for t in texts], normalize_embeddings=True)]

    # ---------------- stats ----------------
    def coverage(self, texts: Iterable[str]) -> float:
        got = 0
        tot = 0
        for t in texts:
            tot += 1
            if self._cache_get(t[:1800]):
                got += 1
        return (got / tot) if tot else 0.0
