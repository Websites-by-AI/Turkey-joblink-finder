"""Supply-side quality & fraud gate.

This matters *more* in the blue-collar/migration vertical than in tech: the people using
the result are often ready to sell a car and pay a "recruiter" to get a job in Istanbul.
So every ingested offer is screened before it can ever be matched.

Rules are heuristic and cheap on purpose; they are a triage queue for a human, not a verdict.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re

from .normalize import norm_text

# Turkish statutory *net* minimum wage, 2026. Update by env, not by edit, when it changes.
MIN_MONTHLY_TRY = 26_005

_FEE_WORDS = ("ücret karşılığı", "pesin ödeme", "kapora", "komisyon yatır", "ön ödeme yap",
              "para karsılığında", "scam", "vize ücreti karşılığında", "کارمزد بده", "پول بده")
_CONTACT_WORDS = ("whatsapp", "iptal hattı", "iletisim: 0", "ara: 0", "+90 5", "05", "تماس با واتساپ")
_VAGUE = ("firma adı gizlidir", "firma adı gizli", "gizli firma")


@dataclass
class Quality:
    ok: bool = True
    score: float = 1.0
    flags: list[str] = field(default_factory=list)

    def flag(self, name: str, *, penalty: float = 0.0, blocking: bool = False) -> "Quality":
        self.flags.append(name)
        self.score = max(0.0, self.score - penalty)
        if blocking:
            self.ok = False
        return self


def screen(job, *, today: str | None = None) -> Quality:
    """Return a :class:`Quality`. ``ok=False`` means: do not show this to a job seeker."""
    q = Quality()
    title = norm_text(job.title)
    blob = norm_text(f"{job.title} {job.company or ''} {job.description}")
    reqs = " ".join(norm_text(r) for r in job.requirements)

    if not title or len(title) < 4:
        q.flag("no-title", penalty=0.4)
    if not job.company:
        q.flag("no-company", penalty=0.15)
    elif any(v in blob for v in _VAGUE):
        q.flag("hidden-employer", penalty=0.25)          # normal for some sectors, but flag it
    # Card-only sources (state JSON, mobile feeds) legitimately have no long description:
    # flag thin text only when the ad is ALSO unstructured, or every ad looks "thin".
    if len(norm_text(job.description)) < 220 and not reqs and not job.skills:
        q.flag("thin-description", penalty=0.15)
    if not job.city and job.remote is None:
        q.flag("no-location", penalty=0.2)

    # money sanity
    if job.salary_min:
        cur = (job.currency or "TRY").upper()
        if cur == "TRY" and job.salary_min < MIN_MONTHLY_TRY:
            q.flag("below-minimum-wage", penalty=0.35,
                   blocking=False)      # could be part-time: never silently, always visible
    else:
        q.flag("no-salary-stated", penalty=0.05)

    # scam patterns that specifically prey on migration-hopeful applicants
    if any(w in blob for w in _FEE_WORDS):
        q.flag("asks-money-from-applicant", penalty=1.0, blocking=True)
    phone_heavy = len(re.findall(r"(?:\+90|0)(?:5\d{2}|2\d{2})[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}",
                                 job.description or ""))
    if phone_heavy >= 2 and not job.company:
        q.flag("contact-only-listing", penalty=0.5, blocking=True)

    # freshness
    seen = getattr(job, "scraped_at", "") or ""
    posted = getattr(job, "posted_at", "") or ""
    if posted and re.match(r"\d{4}-\d{2}-\d{2}", posted):
        try:
            from datetime import datetime, timezone
            d = datetime.fromisoformat(posted)
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
            age = (datetime.now(timezone.utc) - d).days
            if age > 45:
                q.flag(f"old-ad-{age}d", penalty=0.3)
            if age < 0:
                q.flag("future-date", penalty=0.1)
        except ValueError:
            pass
    elif not seen:
        q.flag("no-timestamp", penalty=0.05)
    return q
