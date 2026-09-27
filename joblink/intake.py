"""Opt-in candidate intake - the *legal* replacement for "scraping Iranian CVs".

The seeker side of the marketplace is built by parsing a CV the person gave us
(upload on the landing page, a Telegram bot, a WhatsApp form, an email reply).
We accept free text + a consent token and produce a structured Candidate.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone

from .models import Candidate, Language, Skill
from .normalize import (LEXICON, detect_lang_req, detect_seniority, norm_text, parse_salary)

YEARS_RE = re.compile(r"(\d{1,2})\s*(?:\+)?\s*(?:سال|ساله|yıl|yrs?|years?|seneler)", re.I)
CITY_RE = re.compile(r"(تهران|تبریز|مشهد|اصفهان|شیراز|کرج|تبریز|انکارا|استانبول|ایستانبول|istanbul|ankara|tehran|mashhad|isfahan|shiraz|tabriz)", re.I)
LANG_LABEL = {"english": "en", "ingilizce": "en", "انگلیسی": "en", "turkish": "tr", "türkçe": "tr",
              "ترکی": "tr", "استانبولی": "tr", "german": "de", "alemán": "de", "آلمانی": "de",
              "arabic": "ar", "عربی": "ar", "persian": "fa", "فارسی": "fa", "rusca": "ru", "روسی": "ru"}
LEVEL_WORDS = {"مبتدی": 1, "ضعیف": 1, "متوسط": 2, "خوب": 3, "مسلط": 4, "پیشرفته": 4, "زبانی": 3,
               "iyi": 3, "orta": 2, "çok iyi": 4, "ileri": 4, "native": 6, "fluent": 4}


def contact_hash(contact: str | None) -> str | None:
    """Store an irreversible fingerprint only - enough to dedupe, useless to leak."""
    if not contact:
        return None
    return hashlib.sha256(f"joblink|{norm_text(contact)}".encode()).hexdigest()[:32]


def parse_cv(text: str) -> dict:
    t = norm_text(text)
    skills: dict[str, Skill] = {}
    for canon, aliases in LEXICON.items():
        for a in aliases:
            na = norm_text(a)
            if na and len(na) >= 3 and na in t:
                lvl = 3 if re.search(rf"({na})(.{0,40})(expert|senior|پیشرفته|ارشد|ileri)", t) else 2
                skills[canon] = Skill(name=canon, level=lvl)
                break
    years = [int(x) for x in YEARS_RE.findall(t)]
    langs: dict[str, int] = {}
    for label, code in LANG_LABEL.items():
        for m in re.finditer(re.escape(label), t):
            win = t[max(0, m.start() - 30): m.end() + 45]
            lvl = 3
            for w, v in LEVEL_WORDS.items():
                if norm_text(w) in win:
                    lvl = max(lvl, v)
            for ltr in ("c1", "c2", "b2", "b1", "a2"):
                if ltr in win:
                    lvl = {"a2": 2, "b1": 3, "b2": 4, "c1": 5, "c2": 6}[ltr]
            langs[code] = max(langs.get(code, 0), lvl)
    for code, lvl in detect_lang_req(t).items():
        langs.setdefault(code, 0)
        _ = lvl
    sal = parse_salary(t)
    city = CITY_RE.search(text or "")
    return {
        "skills": list(skills.values()),
        "languages": [Language(code=c, level=v) for c, v in sorted(langs.items())],
        "years_experience": float(max(years)) if years else 0.0,
        "seniority": detect_seniority(t),
        "city": (city.group(1).title() if city else None),
        "expect_salary_min": (sal.monthly_min if sal else None),
        "expect_currency": (sal.currency if sal else "TOMAN"),
        "headline": next((ln.strip() for ln in (text or "").splitlines()
                          if 8 < len(ln.strip()) < 90 and re.search(r"[مهنمدروپ|develop|uzman|engineer|mühendis]", ln, re.I)), ""),
    }


def candidate_from_cv(cv_text: str, *, cid: str, pseudonym: str | None = None,
                      contact: str | None = None, consent_token: str,
                      country: str = "IR", open_remote: bool = True,
                      relocate: bool = False) -> Candidate:
    """``consent_token`` is mandatory: an explicit, timestamped, revocable opt-in.

    Expected shape from the client: ``"v1:2026-09-13T09:00:00Z:<ip|device>:sha256(checkbox-text)"``
    """
    if not consent_token or len(consent_token) < 12:
        raise ValueError("consent_token required - see PLAN-FA.md §4 before collecting anyone's CV")
    f = parse_cv(cv_text)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return Candidate(
        cid=cid, pseudonym=pseudonym or f"C-{cid[-5:].upper()}",
        headline=f["headline"], country=country, city=f["city"],
        skills=f["skills"], languages=f["languages"],
        years_experience=f["years_experience"], seniority=f["seniority"],
        expect_salary_min=f["expect_salary_min"], expect_currency=f["expect_currency"],
        open_to_remote=open_remote, open_to_relocate_tr=relocate,
        cv_text=cv_text[:20000], consent_token=consent_token, consent_at=now,
        source="cv-upload", contact_hash=contact_hash(contact),
    )
