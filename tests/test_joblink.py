from __future__ import annotations

import json
from dataclasses import dataclass, field

import pytest

from joblink.config import SETTINGS, Source
from joblink.httpfetch import Fetched, _cache_get, _cache_put
from joblink.models import Job
from joblink.normalize import (content_tokens, detect_city, detect_family, detect_lang_req,
                               detect_remote, detect_skills, norm_text, parse_salary)
from joblink.adapters import job_postings, links, JsonLdBoard, LinkedInGuest
from joblink.matcher import BM25, Matcher
from joblink.models import Candidate, Skill, Language
from joblink.intake import candidate_from_cv, parse_cv
from joblink.store import Store


# --------------------------------------------------------------------------- #
# normalisation
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("raw,expect", [
    ("برنامه‌نویس  پایتون", "برنامه نویسی پایتون".replace("سی", "سی")),
    ("İstanbul  İlan", "istanbul ilan"),
])
def test_norm_text_smoke(raw, expect):
    assert norm_text(raw)


def test_zwnj_and_arabic_yeh_fold():
    assert norm_text("پایتون") == norm_text("پاي\u062a\u0648ن")
    assert "پایتون" in norm_text("برنامه‌نویسی پایتون")


def test_skills_both_languages():
    tr, _ = detect_skills("En az 3 yıl Python ve Django deneyimi, Docker ve AWS bilen")
    fa, _ = detect_skills("برنامه‌نویس پایتون با تجربه جنگو و داکر و آماوب وب سرویس REST")
    assert {"python", "django", "docker"} <= set(tr)
    assert "python" in fa and "react" not in fa


def test_salary_tr_and_ir():
    s = parse_salary("Maaş: 45.000 - 60.000 TL brüt")
    assert s and s.monthly_min == 45000 and s.currency == "TRY"
    t = parse_salary("حقوق ۱۵ میلیون تومان")
    assert t and t.monthly_min == 15_000_000 and t.currency == "TOMAN"
    assert parse_salary("Maaş belirtilmedi") is None


def test_family_city_remote_lang():
    assert detect_family("Yazılım Geliştirici Uzmanı") == "software"
    assert detect_city("Kocaeli / Gebze", "TR") == "Kocaeli"
    assert detect_city("تهران، ونک", "IR") == "تهران"
    assert detect_remote("Uzaktan çalışma mümkündür") is True
    assert detect_remote("Ofiste tam zamanlı") is False
    assert detect_lang_req("İyi derecede İngilizce, orta düzey Türkçe")["en"] >= 4


def test_tokenizer_stops_at_stopwords():
    toks = content_tokens("ve ile bir deneyimli Python developer")
    assert "python" in toks
    assert "ve" not in toks and "bir" not in toks


# --------------------------------------------------------------------------- #
# parsing real HTML shapes (fixtures mirror the live markup we measured)
# --------------------------------------------------------------------------- #
ELEMAN_DETAIL = """
<html><head><title>Mağaza Müdiresi - secret cv</title>
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"JobPosting","title":"Kıdemli Python Geliştirici",
 "description":"En az 5 yıl Python, Django, REST API, Docker. İyi derecede İngilizce gerekir. Maaş: 90.000 - 120.000 TL. Uzaktan çalışma mümkündür.",
 "datePosted":"2026-09-01","employmentType":"FULL_TIME","jobLocationType":"TELECOMMUTE",
 "qualifications":["5 yıl Python","Django","Kubernetes tercihen"],
 "skills":["python","django","docker"],
 "baseSalary":{"@type":"MonetaryAmount","currency":"TRY",
   "value":{"@type":"QuantitativeValue","minValue":90000,"maxValue":120000}},
 "hiringOrganization":{"@type":"Organization","name":"Nova Yazılım A.Ş."}}
</script></head><body>
<a href="https://www.eleman.net/is-ilani/kdemli-python-gelistirici-i4762405">ilan</a>
</body></html>
"""

LISTING_HTML = """
<div><a href="https://www.eleman.net/is-ilani/a-i1">a</a>
<a href="/is-ilani/b-i2">b</a>
<a href="https://x.com/nope">skip</a></div>
"""


def test_ldjson_and_link_discovery():
    assert job_postings(ELEMAN_DETAIL)[0]["title"] == "Kıdemli Python Geliştirici"
    got = links(LISTING_HTML, r"/is-ilani/", "https://www.eleman.net/is-ilanlari")
    assert got == ["https://www.eleman.net/is-ilani/a-i1", "https://www.eleman.net/is-ilani/b-i2"]


def test_jsonld_board_maps_fields():
    src = Source("t", "T", "TR", "jobs", "jsonld_board", "https://example.com")
    ad = JsonLdBoard(src)
    job = ad.parse_detail(ELEMAN_DETAIL, "https://www.eleman.net/is-ilani/a-i1")
    assert job and job.title == "Kıdemli Python Geliştirici"
    assert job.company == "Nova Yazılım A.Ş."
    assert job.salary_min == 90000 and job.currency == "TRY"
    assert job.remote is True
    assert "python" in job.skills and "django" in job.skills
    assert job.lang_required.get("en", 0) >= 4
    assert job.posted_at == "2026-09-01"


def test_linkedin_card_parser():
    frag = """
<div class="base-card x"><a class="base-card__full-link y" href="https://tr.linkedin.com/jobs/view/senior-python-engineer-at-x-4453241960?pos=1">
</a><h3 class="base-search-card__title">Senior Python Engineer</h3>
<h4 class="base-search-card__subtitle">Acme Yazılım</h4>
<span class="job-search-card__location">Istanbul, Turkey</span>
<time class="job-search-card__listdate" datetime="2026-09-05">5 days ago</time></div>
"""
    src = Source("linkedin_tr", "LI", "TR", "jobs", "linkedin_guest", "https://tr.linkedin.com")
    jobs = LinkedInGuest(src).parse_card(frag, "u")
    assert len(jobs) == 1
    assert jobs[0].title == "Senior Python Engineer"
    assert jobs[0].url.endswith("4453241960")
    assert jobs[0].posted_at == "2026-09-05"


# --------------------------------------------------------------------------- #
# matcher behaviour - the thing that must not regress
# --------------------------------------------------------------------------- #
def _job(**kw) -> Job:
    base = dict(source="t", url="https://x/1", title="Python Developer", country="TR",
                description="Python Django REST Docker", skills=["python", "django", "docker"],
                remote=True)
    base.update(kw)
    return Job(**base)


def _cand(**kw) -> Candidate:
    base = dict(cid="c1", pseudonym="C1", headline="Python developer",
                skills=[Skill(name="python", level=3), Skill(name="django", level=3)],
                languages=[Language(code="en", level=4)],
                consent_token="v1:demo:synthetic-consent", cv_text="5 yıl Python Django REST API")
    base.update(kw)
    return Candidate(**base)


def test_bm25_ranks_python_cv_to_python_job():
    jobs = [_job(), _job(url="https://x/2", title="Garson aranıyor",
                         description="restoran müşteri karşılama servis", skills=[])]
    m = Matcher(jobs)
    top = m.rank_jobs(_cand(), k=2)
    assert top[0].url == "https://x/1"
    # a wrong-trade ad must be pushed below (or filtered out of) the list, never above
    assert all(t.url == "https://x/1" for t in top)
    assert m.rank_jobs(_cand(), k=2, include_blocked=True)[1].score < top[0].score


def test_onsite_gate_blocks_non_relocator():
    onsite = _job(url="https://x/3", title="Python Developer (İstanbul)", remote=False, city="Istanbul")
    m = Matcher([onsite])
    assert m.rank_jobs(_cand(open_to_relocate_tr=False)) == []
    assert m.rank_jobs(_cand(open_to_relocate_tr=True))


def test_turkish_language_gap_is_reported():
    j = _job(url="https://x/4", title="Müşteri temsilcisi", remote=True,
             lang_required={"tr": 5, "en": 3}, skills=["customer_service"])
    m = Matcher([j])
    match = m.rank_jobs(_cand(), k=1, include_blocked=True)[0]
    assert any(g.kind == "language" and "Türkçe" in g.item for g in match.gaps)
    assert match.score < 30        # explicit language demand unmet -> filtered from the send list
    assert m.rank_jobs(_cand(), k=1) == []


def test_consent_required_to_store():
    st = Store(":memory:")
    with pytest.raises(Exception):
        st.upsert_candidate(_cand(consent_token=None))
    st.upsert_candidate(_cand())
    assert st.stats()["candidates"] == 1


def test_intake_parse_cv():
    c = candidate_from_cv(
        "Ali R. 6 yıl deneyimli DevOps engineer. Linux, Docker, Kubernetes, AWS. İngilizce iyi. Ankara. 2500 USD",
        cid="x1", consent_token="v1:2026:abc:def")
    names = {s.name for s in c.skills}
    assert {"docker", "kubernetes", "linux"} & names
    assert c.years_experience == 6.0
    assert c.lang_map["en"] >= 3
    assert c.contact_hash is None


def test_store_roundtrip_and_purge():
    st = Store(":memory:")
    j = _job()
    st.upsert_job(j, family=detect_family(j.search_text))
    st.upsert_candidate(_cand(cid="c9"))
    m = Matcher(st.jobs())
    ms = m.rank_jobs(_cand(cid="c9"), k=3)
    assert st.save_matches(ms) >= 1
    assert st.stats()["jobs"] == 1
    st.db.execute("UPDATE candidates SET consent_token='revoked:x' WHERE cid='c9'")
    assert st.purge_consent_revoked() == 1
    assert st.stats()["matches"] == 0


def test_cache_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(SETTINGS, "data_dir", str(tmp_path))
    url = "https://example.com/x"
    f = Fetched(url, 200, "hello", "direct")
    _cache_put(f)
    got = _cache_get(url, 3600)
    assert got and got.text == "hello" and got.cached
    assert _cache_get(url, 0) is None


def test_weird_jsonld_shapes_do_not_crash():
    """Real boards emit hiringOrganization as a list and baseSalary as a plain number."""
    html = """<script type="application/ld+json">
    {"@type":"JobPosting","title":"Üretim Elemanı","description":"Vardiyalı çalışma. Maaş 32.000 TL",
     "hiringOrganization":[{"name":"A.Ş."},{"name":"Anadolu Cam"}],
     "baseSalary":[{"@type":"MonetaryAmount","currency":"TRY","value":{"@type":"QuantitativeValue","minValue":32000}}],
     "jobLocation":[{"address":{"addressLocality":"Kocaeli"}}]}</script>"""
    src = Source("t", "T", "TR", "jobs", "jsonld_board", "https://example.com")
    j = JsonLdBoard(src).parse_detail(html, "https://www.eleman.net/is-ilani/uretim-elemani-i1")
    assert j and j.company == "A.Ş." and j.salary_min == 32000 and j.city == "Kocaeli"
    flat = """<script type="application/ld+json">
    {"@type":"JobPosting","title":"X","baseSalary":{"currency":"TRY","value":41000}}</script>"""
    j2 = JsonLdBoard(src).parse_detail(flat, "https://www.eleman.net/is-ilani/x-i2")
    assert j2 and j2.salary_min == 41000


def test_brotli_body_is_rejected_not_parsed():
    from joblink.httpfetch import Fetched
    assert Fetched("u", 200, "", "direct").looks_blocked()
    assert Fetched("u", 200, "\x00\x01\x02\x03\x04\x05\x06\x07\x08binary", "direct").looks_blocked()
    assert not Fetched("u", 200, "normal html text", "direct").looks_blocked()


def test_salary_is_not_a_job_id():
    """Regression: whole-page number scanning turned "i4762405" into a 4.7M TL salary."""
    body = "İlan No: 4762405. Pozisyon: güvenlik. Şehir İstanbul. Maaş 42.235 TL + 3000 TL yemek."
    s = parse_salary(body)
    assert s and s.monthly_min == 42235 and s.currency == "TRY"
    assert parse_salary("İlan No 4762405 - 15 çalışan - 2026") is None
    assert parse_salary("Maaş 800 TL") is None          # implausible monthly gross -> dropped
    assert parse_salary("Yıllık 900.000 TL").monthly_min == 75000.0


def test_salary_string_scalar_and_annual_unit():
    html = """<script type="application/ld+json">{"@type":"JobPosting","title":"T","description":"x",
      "baseSalary":{"@type":"MonetaryAmount","currency":"TRY",
      "value":{"@type":"QuantitativeValue","value":"45235","unitText":"MONTH"}}}</script>"""
    src = Source("t", "T", "TR", "jobs", "jsonld_board", "https://example.com")
    j = JsonLdBoard(src).parse_detail(html, "https://www.eleman.net/is-ilani/guvenlik-i1")
    assert j.salary_min == 45235
    html2 = html.replace("MONTH", "YEAR")
    assert JsonLdBoard(src).parse_detail(html2, "https://x/is-ilani/a-i2").salary_min == 45235 / 12


def test_quality_gate_blocks_pay_to_apply_ads():
    from joblink.quality import screen
    good = _job(title="Forklift Operatörü", company="Delta Lojistik A.Ş.",
                 city="Istanbul", salary_min=32000, currency="TRY",
                 description="En az 2 yıl forklift sertifikası. Maaş 32.000 TL + yol + yemek.")
    assert screen(good).ok
    scam = _job(title="Vize İçin İş", company=None,
                description="Peşin ödeme ve kapora karşılığında iş ayarlanır. 0532 111 22 33 - 0544 999 88 77")
    q = screen(scam)
    assert not q.ok and "asks-money-from-applicant" in q.flags


def test_blue_collar_onsite_ad_expects_turkish_and_flags_work_permit():
    j = _job(url="https://x/9", title="Forklift Operatörü", company="Delta",
             description="Depo, forklift, vardiyalı çalışma. Firma: Delta Lojistik", remote=False,
             city="Istanbul", skills=["forklift"], country="TR")
    m = Matcher([j])
    c = _cand(headline="Anbar işçisi / forklift", country="IR", skills=[Skill(name="forklift", level=3)],
              languages=[Language(code="fa", level=7), Language(code="en", level=3)],
              cv_text="۵ سال کار انبار و لیفتراک، تهران", open_to_relocate_tr=True)
    match = m.rank_jobs(c, k=1)[0]
    items = " ".join(g.item for g in match.gaps)
    assert "Türkçe" in items and "Çalışma izni" in items
    assert match.score >= 32       # implied Turkish must not disqualify a forklift operator


def test_quality_gate_handles_naive_and_aware_dates():
    from datetime import datetime, timedelta, timezone
    from joblink.quality import screen
    for stamp in ("2026-01-05", (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()):
        assert screen(_job(title="Depo Elemanı", company="Delta", city="Istanbul",
                           salary_min=32000, currency="TRY", posted_at=stamp,
                           description="Vardiyalı depo çalışması, forklift belgeli")).ok


def test_wrong_trade_is_not_recommended_at_all():
    """A welder must get zero results rather than a cleaning ad, when nothing fits."""
    welder = _cand(headline="Jarkovci / kaynak usta", skills=[Skill(name="welding", level=4)],
                   cv_text="۱۰ سال جوشکاری ARC MIG TIG و ساخت سازه فلزی", open_to_relocate_tr=True)
    clean = _job(url="https://x/c", title="Ev Temizlik Yardımcısı", company="X",
                 description="Temizlik, ütü, çamaşır. Ankara.", skills=[], remote=False, city="Ankara")
    m = Matcher([clean])
    assert m.rank_jobs(welder, k=5) == []
    assert len(m.rank_jobs(welder, k=5, include_blocked=True)) == 1
    # and the right trade still passes
    assert m.rank_jobs(_cand(headline="Temizlik personeli", skills=[Skill(name="cleaning", level=3)],
                             cv_text="۵ سال نظافت و housekeeping", open_to_relocate_tr=True), k=2)


def test_persian_trade_cvs_get_the_right_family():
    """The whole vertical is Persian-speaking blue collar: family detection on Farsi text
    is not a nice-to-have, it is the difference between a match and a wrong suggestion."""
    from joblink.normalize import detect_family, detect_skills
    assert detect_family("جوشکار صنعتی با ۱۰ سال تجربه جوش ARC و MIG و ساخت سازه فلزی") == "skilled_trade"
    assert detect_family("اپراتور لیفتراک و کارگر انبار، شیفت، بارگیری") == "logistics"
    assert detect_family("نیروی نظافت و housekeeping هتل") == "service"
    assert detect_family("راننده پایه یک توزیع و حمل بار") == "logistics"
    assert "welding" in detect_skills("۱۰ سال جوشکاری ARC MIG و تیگ")[0]
    assert "forklift" in detect_skills("اپراتور لیفتراک با کارت")[0]


def test_welder_is_not_shown_a_cleaning_ad_even_with_both_families_known():
    weld = _job(url="https://x/w", title="Kaynak Ustası", company="Delta Metal",
                description="Üretim, kaynak, imalat. Maaş 40.000 TL.", skills=["welding"],
                remote=False, city="Istanbul",
                requirements=["en az 5 yıl kaynak deneyimi"])
    clean = _job(url="https://x/c", title="Ev Temizlik Yardımcısı", company="X",
                 description="Temizlik, ütü, çamaşır. Ankara.", skills=[], remote=False, city="Ankara")
    m = Matcher([clean, weld])
    c = _cand(headline="جوشکار صنعتی", skills=[Skill(name="welding", level=4)],
              languages=[Language(code="fa", level=7)],
              cv_text="۱۰ سال جوشکاری ARC MIG و ساخت سازه فلزی", open_to_relocate_tr=True)
    top = m.rank_jobs(c, k=3)
    assert top and top[0].url.endswith("/w")
    assert all(not t.url.endswith("/c") for t in top)


def test_match_all_replaces_previous_recommendations(tmp_path):
    """A rescoring must not leave stale rows behind (found while reviewing live output)."""
    import json as _json
    from joblink.store import Store
    from joblink.ingest import match_all
    from joblink.config import SETTINGS
    st = Store(str(tmp_path / "x.sqlite3"))
    st.upsert_job(_job(url="https://x/1"), family="software")
    st.upsert_candidate(_cand(cid="c1"))
    assert match_all(st, top_k=5)["matches"] >= 1
    st.db.execute("UPDATE jobs SET status='stale'")          # job disappears from the market
    st.db.execute("UPDATE jobs SET status='open', title='Yanlış', description='temizlik'")
    match_all(st, top_k=5)
    rows = list(st.db.execute("SELECT title FROM matches WHERE cid='c1'"))
    assert all("Python Developer" != r[0] for r in rows)


def test_turkish_polysemy_kaynak_is_not_a_skill_bridge():
    """"kaynak" = welding AND source code. A welder must never be sent a software ad because of it."""
    from joblink.normalize import detect_skills
    assert "welding" not in detect_skills("Kaynak kodlarını temiz tutan Yazılım Geliştirici arıyoruz")[0]
    assert "welding" in detect_skills("Kaynak ustası, MIG TIG, üretim bandı")[0]
    software = _job(url="https://x/sw", title="Yazılım Geliştirici", company="Nova",
                    description="Kaynak kodu, Django, Python, Jenkins. Maaş 90.000 TL.",
                    skills=["welding", "python"], remote=True, city="Istanbul")
    welder = _cand(headline="Jarkovci / kaynak ustası",
                   skills=[Skill(name="welding", level=4), Skill(name="cnc", level=3)],
                   languages=[Language(code="fa", level=7)],
                   cv_text="۱۰ سال جوشکاری ARC و MIG در کارخانه ساخت سازه فلزی",
                   open_to_relocate_tr=True)
    real_weld = _job(url="https://x/wd", title="Kaynak Ustası", company="Delta Metal",
                     description="MIG TIG kaynak, çelik konstrüksiyon. Maaş 40.000 TL.",
                     skills=["welding"], remote=False, city="Izmir")
    m = Matcher([software, real_weld])
    top = m.rank_jobs(welder, k=2)
    assert top and top[0].url.endswith("/wd")
    assert all(not t.url.endswith("/sw") for t in top)
    # and if the person will not move, an on-site weld job must not be sent either
    assert m.rank_jobs(welder.model_copy(update={"open_to_relocate_tr": False}), k=2) == []


def test_every_recommendation_needs_evidence():
    """No shared skill, no shared occupation, weak lexical signal -> stay silent."""
    odd = _job(url="https://x/odd", title="Animatör (Part Time)", company="Park",
               description="Çocuk etkinliği, hafta sonu, part time. İstanbul.", skills=[],
               remote=False, city="Istanbul", country="TR")
    welder = _cand(headline="Kaynak ustası", skills=[Skill(name="welding", level=4)],
                   languages=[Language(code="fa", level=7)], cv_text="۸ سال جوشکاری",
                   open_to_relocate_tr=True)
    assert Matcher([odd]).rank_jobs(welder, k=3) == []
    assert Matcher([odd]).rank_jobs(welder, k=3, include_blocked=True)


# --------------------------------------------------------------------------- #
# telegram intake: consent is the product, so the state machine is tested
# --------------------------------------------------------------------------- #
def _bot(tmp_path):
    from joblink.bot import Bot, ensure_schema
    calls: list[dict] = []
    st = Store(str(tmp_path / "bot.sqlite3"))
    st.db.execute("CREATE TABLE IF NOT EXISTS consent (id INTEGER PRIMARY KEY AUTOINCREMENT, cid TEXT,"
                  " chat_id TEXT, action TEXT, token TEXT, ts TEXT, update_id INTEGER)")
    ensure_schema(st)
    st.upsert_job(_job(url="https://x/f", title="Forklift Operatörü", company="Delta",
                       description="Depo, forklift, vardiya. Maaş 32.000 TL. İstanbul.",
                       skills=["forklift", "warehouse"], remote=False, city="Istanbul"))
    api = lambda m, **kw: (calls.append({"method": m, **kw}), {"ok": True, "result": []})[1]
    return Bot(store=st, api=api), calls, st


def _upd(chat, text, i=1):
    return {"update_id": i, "message": {"chat": {"id": chat}, "text": text}}


def test_telegram_flow_requires_consent_then_matches(tmp_path):
    bot, calls, st = _bot(tmp_path)
    bot.handle_update(_upd(5, "/start"))
    assert any("رضایت" in t or "می‌خوام" in t for _, t in bot.sent)
    cv = ("حسین ر. ۵ سال اپراتور لیفتراک و کارگر انبار. Forklift، بارگیری، شیفت، انبارداری. "
          "تهران. آماده کار در استانبول. حقوق 32.000 TL.")
    bot.handle_update(_upd(5, cv))                       # no consent yet
    assert "اول باید رضایت بدهی" in bot.sent[-1][1]
    bot.handle_update(_upd(5, "/katil"))                 # explicit opt-in
    bot.handle_update(_upd(5, cv))
    assert st.stats()["candidates"] == 1
    reply = bot.sent[-1][1]
    # the ad exists but is on-site, and the seeker never said they would move -> say exactly that
    assert "حضوری" in reply and "/haziri" in reply
    bot.handle_update(_upd(5, "/haziri", i=9))
    assert "Forklift Operatörü" in bot.sent[-1][1]
    assert "امتیاز" in bot.sent[-1][1]
    assert st.stats()["jobs"] == 1


def test_optout_deletes_the_person_and_their_matches(tmp_path):
    bot, calls, st = _bot(tmp_path)
    bot.handle_update(_upd(7, "/katil"))
    bot.handle_update(_upd(7, "۵ سال forklift و انبارداری در تهران، لیفتراک، بارگیری، شیفت شب، 30.000 TL"))
    assert st.stats()["candidates"] == 1 and st.stats()["matches"] >= 0
    bot.handle_update(_upd(7, "/hayir"))
    assert st.stats()["candidates"] == 0
    assert st.db.execute("SELECT COUNT(*) FROM matches").fetchone()[0] == 0
    assert bot.current_token(7) is None                   # grant is dead after revoke


def test_unrelated_chat_does_not_leak_other_people(tmp_path):
    bot, calls, st = _bot(tmp_path)
    bot.handle_update(_upd(9, "/katil"))
    bot.handle_update(_upd(9, "اپراتور forklift با ۶ سال انبارداری و بارگیری، تهران، 31.000 TL"))
    sent_to = {c for c, _ in bot.sent}
    assert sent_to == {9}
    # employer feed only exposes a pseudonym, never cv_text or contact
    from joblink.feed import build_feed
    rows = build_feed(st, with_candidates=True, limit=5)
    assert rows
    for r in rows:
        for c in r.get("candidates", []):
            assert set(c) <= {"cid", "pseudonym", "score", "skills", "matched"}


def test_feed_money_and_salary_filter(tmp_path):
    st = Store(str(tmp_path / "f.sqlite3"))
    st.upsert_job(_job(url="https://x/1", title="Aşçı", company="Mutfak", city="Istanbul",
                       salary_min=45000, salary_max=55000, currency="TRY",
                       description="Aşçı arıyoruz, maaş 45.000 - 55.000 TL"))
    st.upsert_job(_job(url="https://x/2", title="Garson", company="Kafe", city="Istanbul",
                       description="Kafe garsonu aranıyor, şartları telefonda konuşuruz"))
    from joblink.feed import build_feed, money, to_csv
    all_rows = build_feed(st, limit=10)
    strict = build_feed(st, salary_only=True, limit=10)
    assert len(all_rows) == 2 and len(strict) == 1
    m = money(next(j for j in st.jobs() if j.title == "Aşçı"))
    assert m["monthly_try"][0] == 45000 and m["monthly_usd"][0] == round(45000 * 0.024)
    assert m["monthly_toman"][0] > m["monthly_try"][0]        # toman is the big number
    assert "monthly_usd" in to_csv(all_rows).split("\n")[0]


def test_monitor_flags_silent_and_zero_sources(tmp_path):
    st = Store(str(tmp_path / "m.sqlite3"))
    from joblink.models import now_iso
    st.log_run("eleman_net", "jobs", 0, "all tiers failed: 403")
    st.log_run("careerjet_tr", "jobs", 12, "")
    from joblink.monitor import health
    h = health(st)
    assert h["sources"]["eleman_net"]["state"] == "broken"
    assert h["sources"]["careerjet_tr"]["state"] == "ok"
    assert any("eleman_net" in a for a in h["alerts"])
    assert h["sources"].get("toptalent", {}).get("state") in (None, "never-ran")


# --------------------------------------------------------------------------- #
# AI layer: the parts that are about safety, not about vibes
# --------------------------------------------------------------------------- #
def test_pii_never_leaves_the_process(tmp_path, monkeypatch):
    """The prompt builder is the last place PII can hide. Nothing identifiable may reach the wire."""
    import json as _json

    import httpx

    from joblink.config import SETTINGS as S
    from joblink.llm import redact

    cv = "رضا 09123456789 ایمیل reza@example.com تلفن +90 532 111 22 33 کد ملی 1234567890"
    for leak in ("09123456789", "reza@example.com", "532 111 22 33", "1234567890"):
        assert leak not in redact(cv), leak

    sent: dict = {}

    def fake_post(self, url, **kw):
        sent["url"] = url
        sent["headers"] = kw.get("headers", {})
        sent["json"] = kw.get("json")
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]},
                              request=httpx.Request("POST", url))

    monkeypatch.setattr(S, "hf_token", "hf_testtoken")
    monkeypatch.setattr(httpx.Client, "post", fake_post)
    from joblink.llm import LLM
    LLM(db=None).ask(f"CANDIDATE: {cv}")

    body = _json.dumps(sent["json"], ensure_ascii=False)
    assert sent["url"].endswith("/v1/chat/completions")
    assert sent["headers"]["Authorization"] == "Bearer hf_testtoken"     # auth in header only
    assert "hf_testtoken" not in body
    for leak in ("09123456789", "reza@example.com", "532 111 22 33", "1234567890"):
        assert leak not in body, f"PII reached the request: {leak}"
    assert "[phone" in body and "[email]" in body


def test_explain_falls_back_to_a_deterministic_template():
    from joblink.llm import LLM, explain_match
    job = _job(url="https://x/1", title="Forklift Operatörü", company="Delta", city="Istanbul",
               description="Depo, forklift, vardiya. Maaş 32.000 TL.", skills=["forklift"], remote=False)
    cand = _cand(headline="کارگر انبار", skills=[Skill(name="forklift", level=4)],
                 cv_text="۶ سال انبارداری و لیفتراک", open_to_relocate_tr=True)
    m = Matcher([job])
    match = m.rank_jobs(cand, k=1)[0]
    text = explain_match(LLM(db=None, model="off"), cand, job, match)   # no token -> template
    assert "چرا این آگهی" in text and "اقدام این هفته" in text
    assert explain_match(LLM(db=None, model="off"), cand, job, match) == text   # stable, no drift


def test_embedder_reports_the_token_scope_problem_in_words(tmp_path, monkeypatch):
    import httpx
    from joblink.emb import Embedder
    from joblink.config import SETTINGS as S
    S.hf_token = "hf_scopeless"
    monkeypatch.setattr(httpx.Client, "post", lambda self, url, **kw: httpx.Response(
        403, text='{"error":"This authentication method does not have sufficient permissions '
                  'to call Inference Providers on behalf of user x"}',
        request=httpx.Request("POST", url)))
    e = Embedder(mode="router")
    assert e.embed(["a", "b"]) == {}
    assert e.mode == "off" and "Inference Providers" in e.last_error


def test_ai_check_without_token_is_a_clean_no_op(tmp_path, monkeypatch, capsys):
    from joblink.cli import main
    from joblink.config import SETTINGS as S
    monkeypatch.setattr(S, "hf_token", "")
    monkeypatch.setattr(S, "data_dir", str(tmp_path))
    assert main(["ai-check"]) == 0
    assert "no token" in capsys.readouterr().out
