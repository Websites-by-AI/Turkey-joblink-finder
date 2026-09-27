-- D1 schema (SQLite). Mirrors joblink/store.py so the crawler and the edge share one shape.
CREATE TABLE IF NOT EXISTS jobs (
  uid TEXT PRIMARY KEY, source TEXT NOT NULL, country TEXT NOT NULL, title TEXT NOT NULL,
  company TEXT, city TEXT, url TEXT NOT NULL, description TEXT, skills TEXT, posted_at TEXT,
  remote INTEGER, salary_min REAL, salary_max REAL, currency TEXT, family TEXT, seniority TEXT,
  lang_required TEXT, must_have TEXT, search_text TEXT,
  scraped_at TEXT, last_seen_at TEXT, status TEXT DEFAULT 'open'
);
CREATE INDEX IF NOT EXISTS jobs_seen   ON jobs(last_seen_at);
CREATE INDEX IF NOT EXISTS jobs_status ON jobs(status, source);

-- Candidates exist only when a consent token is present (application-level rule, see PLAN-FA.md §4).
CREATE TABLE IF NOT EXISTS candidates (
  cid TEXT PRIMARY KEY, pseudonym TEXT, headline TEXT, country TEXT, city TEXT,
  seniority TEXT, years_exp REAL, skills TEXT, languages TEXT, expect_min REAL, expect_cur TEXT,
  open_remote INTEGER, open_relocate INTEGER, cv_text TEXT,
  consent_token TEXT NOT NULL, consent_at TEXT, source TEXT, contact_hash TEXT,
  created_at TEXT, updated_at TEXT, search_text TEXT
);

CREATE TABLE IF NOT EXISTS matches (
  id INTEGER PRIMARY KEY AUTOINCREMENT, cid TEXT NOT NULL, job_uid TEXT NOT NULL, source TEXT,
  url TEXT, title TEXT, company TEXT, city TEXT, remote INTEGER, score REAL, components TEXT,
  matched_skills TEXT, gaps TEXT, created_at TEXT, UNIQUE(cid, job_uid)
);
CREATE INDEX IF NOT EXISTS match_cid ON matches(cid, score DESC);

CREATE TABLE IF NOT EXISTS runs (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, source TEXT, kind TEXT, items INTEGER, errors TEXT);
