"""SQLite storage. The DDL is deliberately kept to SQL that Google's D1
(Cloudflare's SQLite edge DB) also accepts, so the same schema can move to the
edge without a rewrite (see worker/)."""

from __future__ import annotations

import json
import os
import sqlite3
from typing import Iterable

from .models import Candidate, Job, Match

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
  uid            TEXT PRIMARY KEY,
  source         TEXT NOT NULL,
  country        TEXT NOT NULL,
  title          TEXT NOT NULL,
  company        TEXT,
  city           TEXT,
  url            TEXT NOT NULL,
  description    TEXT,
  family         TEXT,
  seniority      TEXT,
  remote         INTEGER,
  employment     TEXT,
  salary_min     REAL,
  salary_max     REAL,
  currency       TEXT,
  lang_required  TEXT,
  must_have      TEXT,
  skills         TEXT,
  posted_at      TEXT,
  scraped_at     TEXT,
  last_seen_at   TEXT,
  status         TEXT DEFAULT 'open',
  quality_score  REAL,
  quality_flags  TEXT,
  search_text    TEXT
);
CREATE INDEX IF NOT EXISTS jobs_seen    ON jobs(last_seen_at);
CREATE INDEX IF NOT EXISTS jobs_family  ON jobs(family);
CREATE INDEX IF NOT EXISTS jobs_source  ON jobs(source);

CREATE TABLE IF NOT EXISTS candidates (
  cid            TEXT PRIMARY KEY,
  pseudonym      TEXT,
  headline       TEXT,
  country        TEXT,
  city           TEXT,
  seniority      TEXT,
  years_exp      REAL,
  skills         TEXT,
  languages      TEXT,
  expect_min     REAL,
  expect_cur     TEXT,
  open_remote    INTEGER,
  open_relocate  INTEGER,
  cv_text        TEXT,
  consent_token  TEXT NOT NULL,
  consent_at     TEXT,
  source         TEXT,
  contact_hash   TEXT,
  created_at     TEXT,
  updated_at     TEXT,
  search_text    TEXT
);

CREATE TABLE IF NOT EXISTS matches (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  cid            TEXT NOT NULL,
  job_uid        TEXT NOT NULL,
  source         TEXT,
  url            TEXT,
  title          TEXT,
  company        TEXT,
  city           TEXT,
  remote         INTEGER,
  score          REAL,
  components     TEXT,
  matched_skills TEXT,
  gaps           TEXT,
  created_at     TEXT,
  UNIQUE(cid, job_uid)
);
CREATE INDEX IF NOT EXISTS match_cid ON matches(cid, score DESC);

-- Every scrape decision is recorded: this is what makes the pipeline auditable
-- if a site (or a data-protection authority) ever asks what we collected.
CREATE TABLE IF NOT EXISTS runs (
  id     INTEGER PRIMARY KEY AUTOINCREMENT,
  ts     TEXT,
  source TEXT,
  kind   TEXT,
  items  INTEGER,
  errors TEXT
);
"""


class Store:
    def __init__(self, path: str):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self.path = path
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        self.db.commit()

    # ---------------- jobs ----------------
    def upsert_job(self, job: Job, family: str | None = None, *, status: str = "open",
                   quality: dict | None = None) -> None:
        j = job.clean()
        self.db.execute(
            """INSERT INTO jobs(uid,source,country,title,company,city,url,description,family,
                 seniority,remote,employment,salary_min,salary_max,currency,lang_required,must_have,
                 skills,posted_at,scraped_at,last_seen_at,status,quality_score,quality_flags,search_text)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(uid) DO UPDATE SET
                 title=excluded.title, description=excluded.description,
                 salary_min=excluded.salary_min, salary_max=excluded.salary_max,
                 skills=excluded.skills, last_seen_at=excluded.last_seen_at,
                 status=excluded.status, scraped_at=excluded.scraped_at,
                 quality_score=excluded.quality_score, quality_flags=excluded.quality_flags""",
            (j.uid, j.source, j.country, j.title, j.company, j.city, j.url, j.description[:8000],
             family, j.seniority, None if j.remote is None else int(j.remote), j.employment_type,
             j.salary_min, j.salary_max, j.currency, json.dumps(j.lang_required),
             json.dumps(j.requirements, ensure_ascii=False)[:2000], json.dumps(j.skills),
             j.posted_at, j.scraped_at, j.scraped_at, status,
             (quality or {}).get("score", 1.0), json.dumps((quality or {}).get("flags", [])),
             j.search_text),
        )

    def mark_stale_jobs_closed(self, max_age_days: int = 21) -> int:
        cur = self.db.execute(
            "UPDATE jobs SET status='stale' WHERE last_seen_at < datetime('now', ?) AND status='open'",
            (f"-{int(max_age_days)} days",),
        )
        self.db.commit()
        return cur.rowcount

    def jobs(self, only_open: bool = True, limit: int | None = None,
             source: str | None = None) -> list[Job]:
        q = "SELECT * FROM jobs"
        cond, args = [], []
        if only_open:
            cond.append("status='open'")
        if source:
            cond.append("source=?")
            args.append(source)
        if cond:
            q += " WHERE " + " AND ".join(cond)
        q += " ORDER BY last_seen_at DESC"
        if limit:
            q += f" LIMIT {int(limit)}"
        out = []
        for r in self.db.execute(q, args):
            out.append(Job(
                source=r["source"], url=r["url"], title=r["title"], company=r["company"],
                city=r["city"], country=r["country"], description=r["description"] or "",
                skills=json.loads(r["skills"] or "[]"),
                requirements=json.loads(r["must_have"] or "[]"),
                employment_type=r["employment"],
                remote=None if r["remote"] is None else bool(r["remote"]),
                seniority=r["seniority"], salary_min=r["salary_min"], salary_max=r["salary_max"],
                currency=r["currency"], lang_required=json.loads(r["lang_required"] or "{}"),
                posted_at=r["posted_at"],
            ))
        return out

    # ---------------- candidates ----------------
    def upsert_candidate(self, c: Candidate) -> None:
        c.assert_consent()
        self.db.execute(
            """INSERT INTO candidates(cid,pseudonym,headline,country,city,seniority,years_exp,skills,
                 languages,expect_min,expect_cur,open_remote,open_relocate,cv_text,consent_token,
                 consent_at,source,contact_hash,created_at,updated_at,search_text)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(cid) DO UPDATE SET headline=excluded.headline, skills=excluded.skills,
                 languages=excluded.languages, cv_text=excluded.cv_text,
                 updated_at=excluded.updated_at, search_text=excluded.search_text""",
            (c.cid, c.pseudonym, c.headline, c.country, c.city, c.seniority, c.years_experience,
             json.dumps([s.model_dump() for s in c.skills], ensure_ascii=False),
             json.dumps([l.model_dump() for l in c.languages]), c.expect_salary_min, c.expect_currency,
             int(c.open_to_remote), int(c.open_to_relocate_tr), c.cv_text[:8000], c.consent_token,
             c.consent_at, c.source, c.contact_hash, c.created_at, c.updated_at, c.search_text),
        )
        self.db.commit()

    def candidates(self, limit: int | None = None) -> list[Candidate]:
        q = "SELECT * FROM candidates" + (f" LIMIT {int(limit)}" if limit else "")
        out = []
        for r in self.db.execute(q):
            out.append(Candidate(
                cid=r["cid"], pseudonym=r["pseudonym"], headline=r["headline"] or "",
                country=r["country"] or "IR", city=r["city"], seniority=r["seniority"],
                years_experience=r["years_exp"] or 0,
                skills=json.loads(r["skills"] or "[]"), languages=json.loads(r["languages"] or "[]"),
                expect_salary_min=r["expect_min"], expect_currency=r["expect_cur"] or "USD",
                open_to_remote=bool(r["open_remote"]), open_to_relocate_tr=bool(r["open_relocate"]),
                cv_text=r["cv_text"] or "", consent_token=r["consent_token"],
                consent_at=r["consent_at"], source=r["source"], contact_hash=r["contact_hash"],
                created_at=r["created_at"], updated_at=r["updated_at"],
            ))
        return out

    def purge_consent_revoked(self, days: int = 0) -> int:
        """Right-to-be-erasure path: candidates whose consent row is older than `days` and
        flagged 'revoked:' are deleted (KVKK m.7 / GDPR art.17)."""
        cur = self.db.execute(
            "DELETE FROM candidates WHERE consent_token LIKE 'revoked:%'")
        self.db.execute("DELETE FROM matches WHERE cid NOT IN (SELECT cid FROM candidates)")
        self.db.commit()
        return cur.rowcount

    # ---------------- matches ----------------
    def save_matches(self, matches: Iterable[Match]) -> int:
        n = 0
        for m in matches:
            self.db.execute(
                """INSERT INTO matches(cid,job_uid,source,url,title,company,city,remote,score,
                     components,matched_skills,gaps,created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(cid,job_uid) DO UPDATE SET score=excluded.score,
                     components=excluded.components, gaps=excluded.gaps""",
                (m.cid, m.job_uid, m.source, m.url, m.title, m.company, m.city,
                 None if m.remote is None else int(m.remote), m.score,
                 json.dumps({k: round(v, 4) for k, v in m.components.items()}),
                 json.dumps(m.matched_skills, ensure_ascii=False),
                 json.dumps([g.model_dump() for g in m.gaps], ensure_ascii=False), m.created_at),
            )
            n += 1
        self.db.commit()
        return n

    def log_run(self, source: str, kind: str, items: int, errors: str = "") -> None:
        from .models import now_iso
        self.db.execute("INSERT INTO runs(ts,source,kind,items,errors) VALUES(?,?,?,?,?)",
                        (now_iso(), source, kind, items, errors[:500]))
        self.db.commit()

    def stats(self) -> dict:
        d = {}
        for table in ("jobs", "candidates", "matches", "runs"):
            d[table] = self.db.execute(f"SELECT COUNT(*) c FROM {table}").fetchone()["c"]
        d["jobs_by_source"] = {
            r["source"]: r["c"] for r in self.db.execute(
                "SELECT source, COUNT(*) c FROM jobs GROUP BY source ORDER BY c DESC")}
        d["jobs_open"] = self.db.execute("SELECT COUNT(*) c FROM jobs WHERE status='open'").fetchone()["c"]
        d["jobs_rejected"] = self.db.execute(
            "SELECT COUNT(*) c FROM jobs WHERE status='rejected'").fetchone()["c"]
        d["top_quality_flags"] = {
            fl: n for fl, n in
            ((f, self.db.execute("SELECT COUNT(*) c FROM jobs WHERE quality_flags LIKE ?",
                                 (f'%"{f}"%',)).fetchone()["c"])
             for f in {x for (row,) in self.db.execute("SELECT quality_flags FROM jobs WHERE quality_flags IS NOT NULL")
                       for x in (json.loads(row) or [])})
            if n}
        return d

    def close(self) -> None:
        self.db.close()
