"""Matching = the "dispatch" of the marketplace.

Hybrid scorer, deliberately explainable (a candidate must be told WHY a job was
picked and WHAT is missing - that gap list is the product, not the score):

    score = 100 * (0.34*skill + 0.26*semantic + 0.14*language + 0.12*location
                   + 0.08*seniority + 0.06*salary) * gates * recency

`semantic` is BM25 by default; if ``HF_TOKEN`` is set it is blended 50/50 with
cosine similarity of multilingual e5 embeddings via the Hugging Face inference
endpoint (no local model download -> runs on a free Space / a Worker).
"""

from __future__ import annotations

import json
import math
import os
import time
from collections import Counter, defaultdict
from typing import Iterable, Sequence

import httpx

from .config import SETTINGS
from .normalize import content_tokens, detect_family, jaccard, norm_text
from .models import Candidate, Gap, Job, Match, LANG_LEVELS, SKILL_LEVELS

# Below this we would rather tell the seeker "nothing good today" than push a wrong ad -
# in a migration market a bad recommendation costs more trust than no recommendation.
MIN_SEND_SCORE = 32.0

# Occupation families that plausibly overlap in a blue-collar market. "industry" and
# "skilled_trade" must not fight each other; "software" vs "service" must.
FAMILY_CLUSTERS = [
    {"software", "data_ai", "design"},
    {"skilled_trade", "industry", "construction", "logistics"},
    {"service", "customer", "marketing_sales", "teaching_lang"},
    {"finance_admin", "hr_recruiting", "management", "legal"},
    {"healthcare"},
]


def family_conflict(a: str | None, b: str | None) -> bool:
    """True when two occupation families are genuinely unrelated."""
    if not a or not b:
        return False
    if a == b:
        return False
    return not any(a in c and b in c for c in FAMILY_CLUSTERS)

WEIGHTS = {"skill": 0.34, "semantic": 0.26, "language": 0.14,
           "location": 0.12, "seniority": 0.08, "salary": 0.06}
SENIORITY_ORDER = ["intern", "junior", "mid", "senior", "lead", "manager"]

FA_ADVICE = {
    "skill": "مهارت «{x}» را در رزومه اثبات کن (لینک نمونه‌کار/گیت‌هاب یا یک پروژه کوچک).",
    "skill_trade": "برای این شغل یدی، مدرک فنی‌حرفه‌ای/کارت مهارت + عکس نمونه‌کار را به رزومه اضافه کن.",
    "visa": ("کارفرمای ترکیه‌ای باید «Çalışma izni» (مجوز کار) را درخواست کند؛ این کار قانونی "
             "۴ تا ۸ هفته و قرارداد امضاشده می‌خواهد. هیچ‌وقت با ویزای توریستی شروع نکن."),
    "language": "برای این آگهی سطح زبان «{x}» لازم است؛ فعلاً رزومه‌ات را انگلیسی-محور بفرست.",
    "logistics": "این شغلحضوری است و کارجو باید جابه‌جایی/ویزا داشته باشد.",
    "salary": "حقوق خواسته‌ی تو از سقف آگهی بالاتر است؛ یا مذاکره کن یا آگهی را فیلتر کن.",
}


# --------------------------------------------------------------------------- #
# lexical core
# --------------------------------------------------------------------------- #
class BM25:
    def __init__(self, docs: Sequence[Sequence[str]], k1: float = 1.4, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs = [list(d) for d in docs]
        self.df: Counter[str] = Counter()
        self.tf = []
        for d in self.docs:
            c = Counter(d)
            self.tf.append(c)
            self.df.update(c.keys())
        self.n = max(1, len(self.docs))
        self.avgdl = sum(len(d) for d in self.docs) / self.n if self.docs else 1.0

    def score(self, qi: int, query: Sequence[str]) -> float:
        tf, dl = self.tf[qi], len(self.docs[qi]) or 1
        s = 0.0
        for t in set(query):
            f = tf.get(t, 0)
            if not f:
                continue
            idf = math.log(1 + (self.n - self.df[t] + 0.5) / (self.df[t] + 0.5))
            s += idf * (f * (self.k1 + 1)) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
        return s

    def max_possible(self, query: Sequence[str]) -> float:
        """Used to squash raw BM25 into 0..1 across jobs of one query."""
        best = 0.0
        for i in range(self.n):
            best = max(best, self.score(i, query))
        return best or 1.0


# --------------------------------------------------------------------------- #
# embeddings - transport + persistent cache live in joblink/emb.py
# --------------------------------------------------------------------------- #
from .emb import Embedder          # noqa: E402
from .emb import cos as _cos       # noqa: E402


# --------------------------------------------------------------------------- #
# the engine
# --------------------------------------------------------------------------- #
class Matcher:
    def __init__(self, jobs: list[Job], embedder: Embedder | None = None, db=None):
        self.jobs = jobs
        self.by_uid = {j.uid: j for j in jobs}
        self.index = BM25([content_tokens(j.search_text) for j in jobs])
        self.skills = {j.uid: set(j.skills) for j in jobs}
        self.family = {j.uid: detect_family(j.search_text) for j in jobs}
        self.embedder = embedder if embedder is not None else Embedder(db=db)
        self._jvec: dict[str, list[float]] = {}

    def _job_vectors(self, uids: list[str]) -> dict[str, list[float]]:
        """Vectors for these jobs, straight from the persistent cache. Costs nothing after the
        first pass, which is the whole point: the free HF quota is $0.10 per month."""
        missing = [u for u in uids if u not in self._jvec]
        if missing and self.embedder.enabled:
            texts = [self.by_uid[u].search_text[:1800] for u in missing]
            emb = self.embedder.embed(texts)
            for u, t in zip(missing, texts):
                v = emb.get(t)
                if v:
                    self._jvec[u] = v
        return {u: self._jvec[u] for u in uids if u in self._jvec}

    # ---- gates -------------------------------------------------------------
    @staticmethod
    def gates(cand: Candidate, job: Job) -> tuple[float, list[Gap]]:
        """Multiplicative gate in [0,1] + blocking gaps. 0 means: do not send this."""
        mult, gaps = 1.0, []
        if job.remote is False and not cand.open_to_relocate_tr:
            mult *= 0.0
            gaps.append(Gap(kind="logistics", item=f"onsite in {job.city or 'TR'}", severity=3,
                            advice=FA_ADVICE["logistics"]))
        tr_need = job.lang_required.get("tr", 0)
        tr_have = cand.lang_map.get("tr", 0)
        # Blue-collar/service ads in TR usually *expect* spoken Turkish without writing it down.
        # Surface that as a gap, but never invent a hard requirement and then disqualify people
        # for it: an *implied* need costs far less than an explicitly stated one.
        implied_tr = not job.lang_required.get("tr")
        if implied_tr and job.remote is False and detect_family(job.search_text) in {
                "skilled_trade", "service", "industry", "construction", "logistics", "customer"}:
            tr_need = 2
        if tr_need and tr_have < tr_need:
            if implied_tr:
                mult *= 0.85
            elif job.remote is False:
                mult *= 0.15
            else:
                mult *= 0.75
            lvl = "A1" if tr_need <= 2 else f"B{max(1, tr_need - 1)}"
            gaps.append(Gap(kind="language", item=f"Türkçe {lvl}",
                            severity=2 if implied_tr else (3 if job.remote is False else 2),
                            advice=FA_ADVICE["language"].format(x=f"Türkçe {lvl} (مکالمه‌محور)")))
        en_need = job.lang_required.get("en", 0)
        if en_need and cand.lang_map.get("en", 0) < en_need - 1:
            mult *= 0.6
            gaps.append(Gap(kind="language", item="English", severity=2,
                            advice=FA_ADVICE["language"].format(x="English")))
        # migration reality for an Iran-resident seeker on an on-site Turkish offer
        if (job.country == "TR" and job.remote is False and cand.country == "IR"
                and not cand.work_permit_eu_tr):
            gaps.append(Gap(kind="logistics", item="Çalışma izni / ویزای کاری", severity=2,
                            advice=FA_ADVICE["visa"]))
            mult *= 0.92
        return mult, gaps

    # ---- pieces ------------------------------------------------------------
    def skill_score(self, cand: Candidate, job: Job) -> tuple[float, list[str], list[Gap]]:
        have = cand.skill_map
        need = self.skills[job.uid]
        gaps: list[Gap] = []
        if not need:
            return 0.25, [], gaps        # an ad that names no requirements cannot earn skill credit
        cov, matched = 0.0, []
        for s in need:
            lv = have.get(s.lower())
            if lv is None:
                gaps.append(Gap(kind="skill", item=s, severity=2,
                                 advice=FA_ADVICE["skill"].format(x=s)))
                continue
            w = min(1.0, 0.45 + 0.18 * lv.level)
            cov += w
            matched.append(s)
        score = cov / len(need)
        # over-qualification is a soft penalty, not a rejection
        extra = len(have) - len(need)
        if extra > 8:
            score *= 0.95
        return score, matched, gaps

    @staticmethod
    def language_score(cand: Candidate, job: Job) -> float:
        need = job.lang_required or {}
        have = cand.lang_map
        if not need:
            return 0.7 if have.get("en", 0) >= 3 else 0.5
        vals = []
        for code, lvl in need.items():
            vals.append(min(1.0, have.get(code, 0) / max(1, lvl)))
        return sum(vals) / len(vals)

    @staticmethod
    def location_score(cand: Candidate, job: Job) -> float:
        if job.remote:
            return 1.0 if cand.open_to_remote else 0.3
        if job.country == cand.country:
            return 0.9
        if cand.open_to_relocate_tr:
            return 0.72 if not cand.work_permit_eu_tr else 0.9
        return 0.05

    @staticmethod
    def seniority_score(cand: Candidate, job: Job) -> float:
        a, b = cand.seniority, job.seniority
        if not a or not b:
            return 0.55
        if a == b:
            return 1.0
        d = abs(SENIORITY_ORDER.index(a) - SENIORITY_ORDER.index(b)) if a in SENIORITY_ORDER and b in SENIORITY_ORDER else 2
        return {1: 0.7, 2: 0.4}.get(d, 0.2)

    @staticmethod
    def salary_score(cand: Candidate, job: Job) -> float:
        from .config import FX_TO_USD
        exp = cand.expect_salary_min
        if not exp:
            return 0.6
        if not job.salary_min:
            return 0.55
        cur = (job.currency or "TRY").upper()
        k = FX_TO_USD.get(cur)
        if not k:
            return 0.5
        lo = job.salary_min * k
        hi = (job.salary_max or job.salary_min) * k
        if exp <= lo:
            return 1.0
        if exp <= hi * 1.15:
            return 0.75
        return 0.25

    # ---- main API ----------------------------------------------------------
    def score(self, cand: Candidate, job: Job, sem_raw: float, sem_max: float,
               cvec: list[float] | None) -> Match:
        gate, gate_gaps = self.gates(cand, job)
        skill, matched, sgaps = self.skill_score(cand, job)
        comp = {
            "skill": skill,
            "semantic": min(1.0, sem_raw / sem_max) if sem_max else 0.0,
            "language": self.language_score(cand, job),
            "location": self.location_score(cand, job),
            "seniority": self.seniority_score(cand, job),
            "salary": self.salary_score(cand, job),
        }
        if cvec:
            jv = self._job_vectors([job.uid]).get(job.uid)
            if jv:
                comp["semantic"] = 0.5 * comp["semantic"] + 0.5 * max(0.0, _cos(cvec, jv))
        # occupation family: a welder must not be shown a house-cleaning ad just because
        # neither side extracted skills. Mismatch across families is near-disqualifying.
        cf, jf = detect_family(cand.search_text), self.family[job.uid]
        same_family = bool(jf and cf and jf == cf)
        conflict = family_conflict(cf, jf)
        if conflict:
            # Cross-cluster collision (welder vs "kaynak kodu" software ad, designer vs pizza
            # shift): discount hard; the exclusion rule below handles the rest.
            comp["semantic"] *= 0.55
            comp["skill"] *= 0.35
            gate_mult = 0.6
        elif jf and cf and not same_family:
            gate_mult = 0.92          # neighbouring trade: keep, just no bonus
        base = sum(WEIGHTS[k] * comp[k] for k in WEIGHTS)
        gaps = gate_gaps + sgaps
        gate_mult = 1.0
        if sgaps and detect_family(job.search_text) in {"skilled_trade", "industry", "construction"}:
            for g in sgaps[:2]:
                g.advice = g.advice or FA_ADVICE["skill_trade"]
                if not g.advice:
                    g.advice = FA_ADVICE["skill_trade"]
        if comp["salary"] <= 0.3:
            gaps.append(Gap(kind="logistics", item="salary expectation", severity=1,
                            advice=FA_ADVICE["salary"]))
        age_days = _age_days(job.scraped_at)
        recency = 1 / (1 + math.exp((age_days - 14) / 6)) * 0.25 + 0.75
        score = 100 * base * gate * gate_mult * recency
        if same_family:
            score *= 1.10                       # small nudge toward the right trade
        if conflict and len(matched) < 2:
            # Genuinely different trade with no real skill overlap -> do not send.
            # If the ad names no family at all, still refuse when there is no skill
            # overlap and no lexical signal (otherwise every unlabelled pizza shift ranks).
            score = 0.0
        # Every recommendation must carry at least one concrete reason: a shared skill, a shared
        # occupation, or a strong lexical hit. Without evidence we stay silent — in a migration
        # market a wrong "top job" costs more trust than an empty list.
        # 0.6 because short ads score high on BM25 by accident ("İstanbul", "çalışma", "vardiya")
        if not matched and comp["semantic"] < 0.6:
            score = 0.0
        return Match(cid=cand.cid, job_uid=job.uid, source=job.source, url=job.url,
                     title=job.title, company=job.company, city=job.city, remote=job.remote,
                     score=round(score, 2), components=comp,
                     matched_skills=matched,
                     gaps=sorted(gaps, key=lambda g: -g.severity)[:8])

    def rank_jobs(self, cand: Candidate, k: int = 10, *, include_blocked: bool = False,
                  min_score: float = MIN_SEND_SCORE) -> list[Match]:
        q = content_tokens(cand.search_text)
        sem_max = self.index.max_possible(q)
        cvec = None
        if self.embedder.enabled:
            key = cand.search_text[:1800]
            # one short text per candidate, and not persisted: profiles change, so paying to keep
            # a stale vector is worse than recomputing a single line.
            cvec = self.embedder.embed([key], persist=False).get(key)
        raw = [(self.index.score(i, q), j) for i, j in enumerate(self.jobs)]
        raw.sort(key=lambda x: -x[0])
        shortlist = raw[: max(60, k * 8)]      # cheap recall, expensive ranking
        out = [self.score(cand, j, s, sem_max, cvec) for s, j in shortlist]
        if not include_blocked:
            out = [m for m in out if m.score >= min_score]
        out.sort(key=lambda m: -m.score)
        return out[:k]

    def blocked_by_logistics(self, cand: Candidate) -> list[tuple[Job, float]]:
        """Ads that would be a decent skill fit but are killed by a logistics gate
        (on-site without relocation readiness, or an unmet visa requirement).
        Returning them lets the UX ask a question instead of showing an empty list."""
        out = []
        for job in self.jobs:
            mult, gaps = self.gates(cand, job)
            if mult > 0:
                continue
            if not any(g.kind == "logistics" for g in gaps):
                continue
            q = content_tokens(cand.search_text)
            skill, matched, _ = self.skill_score(cand, job)
            if matched or skill >= 0.5 or self.index.score(self.jobs.index(job), q) > 1.0:
                out.append((job, skill))
        out.sort(key=lambda x: -x[1])
        return out[:5]

    def rank_candidates(self, job: Job, k: int = 10,
                        candidates: Iterable[Candidate] = ()) -> list[tuple[Candidate, float, list[str]]]:
        """Employer-side view (same matrix, transposed)."""
        res = []
        for c in candidates:
            m = self.score(c, job, self.index.score(self.jobs.index(job), content_tokens(c.search_text)),
                           self.index.max_possible(content_tokens(c.search_text)), None)
            if m.score > 0:
                res.append((c, m.score, m.matched_skills))
        res.sort(key=lambda x: -x[1])
        return res[:k]


def _age_days(iso: str | None) -> float:
    if not iso:
        return 7.0
    from datetime import datetime, timezone
    try:
        d = datetime.fromisoformat(iso)
    except ValueError:
        return 7.0
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return max(0.0, (datetime.now(timezone.utc) - d).total_seconds() / 86400)
