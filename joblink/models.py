"""Data contracts for JobLink.

Two-sided marketplace objects:

* :class:`Job`        - supply side (an employer offer, ingested from a Turkish board)
* :class:`Candidate`  - demand side (a *consented* job seeker profile, opt-in only)
* :class:`Match`      - the dispatch result: a job offered to a candidate with an explanation

PII policy (see PLAN-FA.md, section "حریم خصوصی"):
    * we never store raw contact strings, only a sha256 hash + expiry
    * a candidate row exists only if ``consent_token`` is set
"""

from __future__ import annotations

import hashlib
import html
import re
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

SKILL_LEVELS = {"none": 0, "basic": 1, "working": 2, "fluent": 3, "expert": 4}
LANG_LEVELS = {"none": 0, "a1": 1, "a2": 2, "b1": 3, "b2": 4, "c1": 5, "c2": 6, "native": 7}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _norm(s: str | None) -> str:
    if not s:
        return ""
    s = s.replace("\u200c", " ").replace("\xa0", " ")
    s = re.sub(r"<[^>]+>", " ", s)
    for _ in range(2):
        s = html.unescape(s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


class Skill(BaseModel):
    name: str                      # canonical id, e.g. "python"
    level: int = 2                 # see SKILL_LEVELS
    years: float | None = None

    def key(self) -> str:
        return self.name.lower().strip()


class Language(BaseModel):
    code: str                      # fa / tr / en / de ...
    level: int = 0                 # see LANG_LEVELS


class Job(BaseModel):
    source: str
    external_id: str | None = None
    url: str
    title: str
    company: str | None = None
    city: str | None = None
    country: str = "TR"
    description: str = ""
    requirements: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)          # canonical skill ids
    must_have: list[str] = Field(default_factory=list)
    employment_type: str | None = None                       # fulltime / parttime / freelance
    remote: bool | None = None
    seniority: str | None = None                             # junior / mid / senior / lead
    salary_min: float | None = None
    salary_max: float | None = None
    currency: str | None = None
    lang_required: dict[str, int] = Field(default_factory=dict)   # {"tr": 4, "en": 3}
    visa_sponsor: bool | None = None
    posted_at: str | None = None
    scraped_at: str = Field(default_factory=now_iso)
    raw: dict[str, Any] = Field(default_factory=dict)

    @property
    def uid(self) -> str:
        base = self.external_id or self.url
        return hashlib.sha1(f"{self.source}|{base}".encode()).hexdigest()[:20]

    @property
    def search_text(self) -> str:
        return _norm(" ".join(filter(None, [
            self.title, self.title, self.company,
            " ".join(self.skills), " ".join(self.requirements),
            self.description[:4000],
        ])))

    def clean(self) -> "Job":
        self.title = _norm(self.title)
        self.company = _norm(self.company) or None
        self.city = _norm(self.city) or None
        self.description = _norm(self.description)
        self.requirements = [_norm(r) for r in self.requirements if _norm(r)]
        return self


class Candidate(BaseModel):
    cid: str
    pseudonym: str                                  # public handle, never the real name
    headline: str = ""
    country: str = "IR"
    city: str | None = None
    skills: list[Skill] = Field(default_factory=list)
    languages: list[Language] = Field(default_factory=list)
    years_experience: float = 0.0
    seniority: str | None = None
    expect_salary_min: float | None = None
    expect_currency: str = "USD"
    open_to_remote: bool = True
    open_to_relocate_tr: bool = False
    work_permit_eu_tr: bool = False
    cv_text: str = ""
    consent_token: str | None = None                # REQUIRED for storage
    consent_at: str | None = None
    source: str = "self-declared"                   # opt-in form / CV upload / telegram bot
    contact_hash: str | None = None                 # sha256(phone|email) only
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

    @property
    def skill_map(self) -> dict[str, Skill]:
        return {s.key(): s for s in self.skills}

    @property
    def lang_map(self) -> dict[str, int]:
        return {l.code.lower(): l.level for l in self.languages}

    @property
    def search_text(self) -> str:
        return _norm(" ".join(filter(None, [
            self.headline, self.headline, self.cv_text[:4000],
            " ".join(s.name for s in self.skills),
        ])))

    def assert_consent(self) -> None:
        if not self.consent_token:
            raise ConsentError(
                f"Candidate {self.cid} has no consent_token — storing a real person's CV "
                "without explicit consent violates KVKK/GDPR and the source site's ToS."
            )


class ConsentError(RuntimeError):
    pass


class Gap(BaseModel):
    kind: Literal["skill", "language", "logistics"]
    item: str
    severity: int = 1                               # 1 nice-to-have, 3 blocking
    advice: str = ""


class Match(BaseModel):
    cid: str
    job_uid: str
    source: str
    url: str
    title: str
    company: str | None = None
    city: str | None = None
    remote: bool | None = None
    score: float
    components: dict[str, float] = Field(default_factory=dict)
    matched_skills: list[str] = Field(default_factory=list)
    gaps: list[Gap] = Field(default_factory=list)
    created_at: str = Field(default_factory=now_iso)
