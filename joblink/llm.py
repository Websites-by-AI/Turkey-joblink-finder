"""LLM layer — for the things an LLM is actually good at here, and nothing else.

Hard rules (they are the reason this file is short):

1. **The LLM never ranks.** Ranking stays in `matcher.py` (BM25 + skill lexicon + gates) because a
   marketplace must be able to answer "why was this person not shown this job" — a model opinion
   cannot be audited, a scored function can.
2. **No PII in prompts.** Before anything leaves the process we strip phones/emails/national ids and
   send the pseudonym only. A candidate's phone number has no business in a third-party API.
3. **Grounded or silent.** Prompts are built from *our own* store (the job row + the candidate's
   normalized profile + our policy notes). If the model can't answer from that, we use the template.
4. **Cache by hash of prompt**, so an explanation costs once.

What it is good for (measured value, not vibes): turning `gaps` into a short Persian action list,
rewriting a CV summary into the TR "Özet" style, and drafting the employer message.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass
from typing import Any

import httpx

from .config import SETTINGS

ROUTER_V1 = "https://router.huggingface.co/v1"
CACHE_DDL = """
CREATE TABLE IF NOT EXISTS llm_cache (
  key TEXT PRIMARY KEY, model TEXT, out TEXT, ts TEXT, chars INTEGER
);
"""

# Phones/e-mails/national ids must never leave the process.
REDACTIONS = [
    (re.compile(r"(?<!\d)(?:\+98|0)?9\d{9}(?!\d)"), "[phone-ir]"),
    (re.compile(r"(?<!\d)(?:\+90)\s?5\d{2}\s?\d{3}\s?\d{2}\s?\d{2}(?!\d)"), "[phone-tr]"),
    (re.compile(r"\b0[1-9]\d{9}\b"), "[phone]"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[email]"),
    (re.compile(r"\b\d{10}\b"), "[id]"),
    (re.compile(r"(Telegram|WhatsApp|آی‌جی|اینستا)\s*[:：]?\s*@?\w{4,}", re.I), "[contact]"),
]

SYSTEM = (
    "You are JobLink's assistant. You only use facts from the CONTEXT block. "
    "You never invent salary, visa rules, dates or requirements. "
    "Answer in the language asked, in plain text, no markdown headings. "
    "If CONTEXT is not enough, reply with exactly: INSUFFICIENT"
)

POLICY_NOTES = (
    "Product policy: we never contact the candidate's employer for them; we never charge the job "
    "seeker to apply; on-site Turkish work requires an employer-sponsored work permit (Çalışma izni) "
    "applied for inside Türkiye - the platform only reminds people to verify this with the employer "
    "and official channels, it does not give legal advice; salary figures are always monthly gross in TL."
)


def redact(text: str | None) -> str:
    t = text or ""
    for rx, sub in REDACTIONS:
        t = rx.sub(sub, t)
    return t


@dataclass
class LLMResult:
    text: str
    ok: bool
    model: str
    cached: bool = False
    error: str = ""
    chars_in: int = 0


class LLM:
    def __init__(self, db: sqlite3.Connection | None = None, model: str | None = None,
                 timeout: float = 60.0):
        self.db = db
        self.model = model or SETTINGS.hf_llm_model
        self.token = SETTINGS.hf_token
        self.timeout = timeout
        self.enabled = bool(self.token)
        if self.db is not None:
            self.db.executescript(CACHE_DDL)
            self.db.commit()

    # ---------------- plumbing ----------------
    def _key(self, prompt: str) -> str:
        return hashlib.sha1(f"{self.model}|{prompt}".encode()).hexdigest()

    def _cache_get(self, key: str) -> str | None:
        if self.db is None:
            return None
        row = self.db.execute("SELECT out FROM llm_cache WHERE key=?", (key,)).fetchone()
        return row[0] if row else None

    def _cache_put(self, key: str, prompt: str, out: str) -> None:
        if self.db is None or not out:
            return
        from .models import now_iso
        self.db.execute("INSERT OR REPLACE INTO llm_cache(key,model,out,ts,chars) VALUES(?,?,?,?,?)",
                        (key, self.model, out, now_iso(), len(prompt)))
        self.db.commit()

    def ask(self, prompt: str, *, max_tokens: int = 420, temperature: float = 0.2,
            persist: bool = True) -> LLMResult:
        prompt = redact(f"{prompt}\n\n(GROUNDING NOTES: {POLICY_NOTES})")[:12000]
        if not self.enabled:
            return LLMResult("", False, self.model, error="HF_TOKEN unset - LLM disabled")
        key = self._key(prompt)
        hit = self._cache_get(key) if persist else None
        if hit is not None:
            return LLMResult(hit, True, self.model, cached=True, chars_in=len(prompt))
        body = {
            "model": self.model,
            "messages": [{"role": "system", "content": SYSTEM},
                         {"role": "user", "content": prompt}],
            "max_tokens": max_tokens, "temperature": temperature, "stream": False,
        }
        try:
            with httpx.Client(timeout=self.timeout) as c:
                r = c.post(f"{ROUTER_V1}/chat/completions",
                           headers={"Authorization": f"Bearer {self.token}",
                                    "content-type": "application/json"}, json=body)
                if r.status_code == 403 and "Inference Providers" in r.text:
                    self.enabled = False
                    return LLMResult("", False, self.model, chars_in=len(prompt), error=PERMISSION_HINT)
                r.raise_for_status()
                data = r.json()
            out = (data.get("choices") or [{}])[0].get("message", {}).get("content", "").strip()
        except Exception as exc:  # noqa: BLE001 - the template path must still work
            return LLMResult("", False, self.model, chars_in=len(prompt),
                             error=f"{type(exc).__name__}: {str(exc)[:180]}")
        out = re.sub(r"^```(?:\w+)?\s*|\s*```$", "", out).strip()
        if persist:
            self._cache_put(key, prompt, out)
        return LLMResult(out, bool(out), self.model, chars_in=len(prompt))


PERMISSION_HINT = (
    "403 from the router: this token authenticates but is not allowed to call Inference Providers. "
    "Create a fine-grained token with the 'Inference Providers' scope (HF → Settings → Access Tokens), "
    "or use a classic read token. Docs: huggingface.co/docs/inference-providers"
)

# ---------------- the three prompts we actually need ----------------
def explain_match(llm: LLM, cand, job, match) -> str:
    """Why this ad, and the two things to fix first. Falls back to a deterministic template."""
    gaps = "؛ ".join(f"{g.item} ({g.advice})" for g in match.gaps[:3]) or "—"
    ctx = (
        f"CANDIDATE (pseudonym {cand.pseudonym}): {redact(cand.headline)}; "
        f"{cand.years_experience:g} yrs; skills={', '.join(s.name for s in cand.skills)[:300]}; "
        f"languages={cand.lang_map}; wants_remote={cand.open_to_remote}; "
        f"will_relocate={cand.open_to_relocate_tr}\n"
        f"JOB: {redact(job.title)} at {job.company or '—'} ({job.city or 'TR'}), "
        f"{job.employment_type or '—'}, remote={job.remote}, "
        f"salary={'—' if not job.salary_min else f'{job.salary_min:,.0f} {job.currency or 'TRY'}'}\n"
        f"JOB TEXT: {redact(job.description)[:1200]}\n"
        f"MATCH SCORE {match.score:.0f}/100; shared skills: {', '.join(match.matched_skills) or '—'}; "
        f"gaps: {gaps}\n"
        "TASK: in Persian, 3 short bullets: (1) why this fits them, (2) the single most blocking gap, "
        "(3) one concrete action for this week. Max 60 words. No legal or visa advice beyond the notes."
    )
    res = llm.ask(ctx)
    if res.ok and res.text and "INSUFFICIENT" not in res.text.upper():
        return res.text
    return template_explain(cand, job, match)


def template_explain(cand, job, match) -> str:
    """Deterministic fallback — the report must never be empty because an API was down."""
    shared = "، ".join(match.matched_skills[:3]) or "عنوان شغلی"
    lines = [f"• چرا این آگهی: هم‌پوشانی روی {shared}"
              + (f" در {job.city}" if job.city else "")
              + (f" با حقوق {job.salary_min:,.0f} {job.currency or 'TRY'}" if job.salary_min else "")]
    if match.gaps:
        g = match.gaps[0]
        lines.append(f"• مهم‌ترین فاصله: {g.item}")
        lines.append(f"• اقدام این هفته: {g.advice or 'رزومه را دقیقاً حول همین کلمه بازنویسی کن.'}")
    else:
        lines.append("• اقدام این هفته: رزومه را به فرمت ترکی (Özet / Deneyim / Beceriler) دربیاور.")
    return "\n".join(lines)


def tailoring_note(llm: LLM, cand, job) -> str:
    ctx = (
        "TASK: rewrite the candidate's 3-line summary for this specific Turkish ad, in Turkish, "
        "plain text, no buzzwords you cannot ground.\n"
        f"CANDIDATE: {redact(cand.headline)} | {cand.years_experience:g} yrs | "
        f"{', '.join(s.name for s in cand.skills)[:200]}\n"
        f"AD TITLE: {redact(job.title)}\n"
        f"AD REQUIREMENTS: {redact('; '.join(job.requirements))[:400] or '—'}"
    )
    res = llm.ask(ctx, max_tokens=220)
    return res.text if res.ok else ""


def estimate_cost(chars: int, per_mtok_in: float = 0.02) -> str:
    """Router pricing is per million tokens (measured on /v1/models: Llama-3.1-8B = 0.02/1M in)."""
    tok = chars / 4
    return f"≈{tok:,.0f} tokens ≈ ${tok / 1e6 * per_mtok_in:.6f}"
