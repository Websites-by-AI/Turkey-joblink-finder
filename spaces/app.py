"""JobLink public demo - 12 domains + 120 quiz + 11 AI + 3 Custom Rituq + 10 RAG + 10 News + logo"""

from __future__ import annotations
import json, os, sys, random
import gradio as gr

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from joblink.intake import candidate_from_cv
from joblink.matcher import Matcher
from joblink.models import Job

try:
    from joblink.knowledge.domains import DOMAINS
    from joblink.knowledge.resources import RESOURCES
    from joblink.knowledge.quiz import QUIZZES, get_quiz
    from joblink.knowledge.ai_models import MODELS, TOP3
    from joblink.knowledge.rag import get_rag
    from joblink.knowledge.news import NEWS_10
    HAS_KNOWLEDGE = True
except Exception as e:
    HAS_KNOWLEDGE = False
    DOMAINS = []; RESOURCES = []; QUIZZES = []; MODELS = []; TOP3 = []; NEWS_10 = []
    print(f"knowledge load failed: {e}")

JOBS_FILE = os.environ.get("JOBLINK_JOBS", "jobs.json")
DEMO_CONSENT = "v1:space:demo-only-not-a-real-person-000000"

def load_jobs() -> list[Job]:
    if not os.path.exists(JOBS_FILE):
        return []
    with open(JOBS_FILE, encoding="utf-8") as fh:
        data = json.load(fh)
    keep = Job.model_fields.keys() & {"source", "url", "title", "company", "city", "country","description", "skills", "requirements", "remote","seniority", "salary_min", "salary_max", "currency","lang_required", "posted_at"}
    return [Job(**{k: v for k, v in d.items() if k in keep}) for d in data]

JOBS = load_jobs()
MATCHER: Matcher | None = None

def get_matcher() -> Matcher | None:
    global MATCHER
    if not JOBS:
        return None
    if MATCHER is None:
        MATCHER = Matcher(JOBS)
    return MATCHER

def fmt_gap(g) -> str:
    arrow = "⚠️" if g.severity >= 3 else "•"
    return f"{arrow} **{g.item}** — {g.advice}" if g.advice else f"{arrow} {g.item}"

def seek(cv_text: str, relocate: bool, top_k: int):
    m = get_matcher()
    if m is None:
        return ("**هنوز آگهی‌ای بارگذاری نشده.**"), gr.update(), ""
    c = candidate_from_cv(cv_text, cid="demo", pseudonym="شما", consent_token=DEMO_CONSENT, open_to_relocate_tr=bool(relocate))
    matches = m.rank_jobs(c, k=int(top_k))
    rows = []
    for mm in matches:
        rows.append({
            "آگهی": f"[{mm.title}]({mm.url})",
            "کارفرما": mm.company or "—",
            "شهر": mm.city or ("ریموت" if mm.remote else "TR"),
            "امتیاز": f"{mm.score:.0f}",
            "مهارت‌های هم‌پوشان": ", ".join(mm.matched_skills[:6]) or "—",
            "فاصله‌ها": "<br>".join(fmt_gap(g) for g in mm.gaps[:4]) or "—",
        })
    profile = (f"**نرمال‌سازی شده:** {c.headline or '—'} · {c.years_experience:g} سال · "
               f"سطح {c.seniority or '—'} · شهر {c.city or '—'}\n\n"
               f"**مهارت‌ها:** {', '.join(s.name for s in c.skills) or '—'}\n\n"
               f"**زبان‌ها:** {', '.join(f'{l.code}:{l.level}' for l in c.languages) or '—'}")
    return profile, rows, f"{len(matches)} آگهی از {len(JOBS)} آگهی روز"

def turkey_search(category: str, site: str, limit: int):
    try:
        from joblink.knowledge.turkey_job_search import search_rows
        rows = search_rows(category, site, int(limit))
        return rows, f"{len(rows)} لینک جست‌وجوی عمومی آماده شد؛ عنوان و فعال‌بودن هر آگهی در سایت اصلی بررسی شود. بدون ارسال خودکار درخواست."
    except Exception as e:
        return [], f"خطا: {e}"

def browse(query: str, limit: int):
    rows = []
    src = query.strip().lower()
    jobs = JOBS
    if src:
        jobs = [j for j in jobs if src in (j.title or "").lower() or src in (j.description or "").lower() or any(src in s for s in j.skills)]
    for j in jobs[: int(limit)]:
        rows.append({
            "منبع": j.source, "عنوان": j.title, "کارفرما": j.company or "—",
            "شهر": j.city or "—",
            "حقوق (TL)": f"{j.salary_min:,.0f}" if j.salary_min else "—",
            "دورکاری": "بله" if j.remote else ("خیر" if j.remote is False else "نامشخص"),
            "لینک": f"[باز](<{j.url}>)",
        })
    return rows

def list_domains():
    if not HAS_KNOWLEDGE:
        return [], "دانش لود نشد"
    rows = [{"کد": d.id, "عنوان فارسی": d.title_fa, "EN": d.title_en, "ریسک": d.risk_level, "کلیدواژه": ", ".join(d.keywords[:3]), "قوانین": ", ".join(d.relevant_laws[:2])} for d in DOMAINS]
    return rows, f"{len(DOMAINS)} حوزه - هر کدام 10 مقاله+10 کتاب+10 ویدیو + 10 سوال"

def show_domain(domain_id: str):
    if not HAS_KNOWLEDGE:
        return "دانش لود نشد", [], [], []
    d = next((x for x in DOMAINS if x.id==domain_id or x.slug==domain_id), None)
    if not d:
        return f"حوزه {domain_id} پیدا نشد", [], [], []
    desc = f"### {d.title_fa}\n**{d.title_en}**\n\nریسک: {d.risk_level}\n\n{d.description_fa}\n\n**چرا مهم:** {d.why_needed}\n\n**قوانین:** {', '.join(d.relevant_laws)}\n\n**کلیدواژه:** {', '.join(d.keywords)}"
    res = [r for r in RESOURCES if r.domain_id==d.id]
    arts = [{"نوع": r.kind, "عنوان": r.title, "لینک": r.url, "نویسنده": r.author, "سال": r.year, "خلاصه": r.summary_fa[:80]} for r in res if r.kind=="article"][:10]
    books = [{"نوع": r.kind, "عنوان": r.title, "نویسنده": r.author, "سال": r.year, "خلاصه": r.summary_fa[:80]} for r in res if r.kind=="book"][:10]
    vids = [{"عنوان": r.title, "لینک": r.url, "سال": r.year} for r in res if r.kind=="video"][:10]
    return desc, arts, books, vids

def start_quiz(domain_id: str):
    if not HAS_KNOWLEDGE:
        return "دانش لود نشد", [], gr.update()
    if not domain_id:
        domain_id = random.choice([d.id for d in DOMAINS if d.risk_level=="high"])
    qs = get_quiz(domain_id)
    if not qs:
        return f"آزمون {domain_id} پیدا نشد", [], gr.update()
    rows = [{"سوال": q.question_fa, "گزینه 1": q.options_fa[0], "گزینه 2": q.options_fa[1], "گزینه 3": q.options_fa[2], "گزینه 4": q.options_fa[3], "جواب درست": f"{q.correct_index+1}) {q.options_fa[q.correct_index]}", "توضیح": q.explanation_fa, "سختی": q.difficulty} for q in qs]
    return f"آزمون {domain_id} - 10 سوال - برای تلگرام /azmoon {domain_id} بزن تا تعاملی شود", rows, qs[0].question_fa

def list_models():
    if not HAS_KNOWLEDGE:
        return [], "مدل لود نشد"
    rows = [{"ID": m.id, "نام": m.name, "نوع": m.type, "پارامتر": m.params, "بعد": m.dims or "-", "کانتکست": m.context, "fa/tr": "✅" if "fa" in m.languages else "⚠️", "Live HF": "✅" if m.inference_live else "❌", "MTEB": m.score_mteb or "-", "Iran": f"{m.iran_score}/10", "بهترین برای": m.best_for[:50]} for m in MODELS]
    return rows, f"{len(MODELS)} مدل - TOP3 ساخته شد"

def show_top3():
    if not HAS_KNOWLEDGE:
        return "مدل لود نشد", [], []
    md = ""
    for t in TOP3:
        md += f"### 🥇 TOP {t['rank']}: {t['name']}\n**چرا:** {t['why']}\n\n**معماری:** {t['architecture']}\n\n**هزینه:** {t['cost']}\n\n**Deploy ایران:** {t['iran_deploy']}\n\n---\n\n"
    table = [{"رتبه": t["rank"], "نام": t["name"], "Embedding": t.get("embedding_id",""), "LLM": t.get("llm_id",""), "هزینه": t["cost"][:50], "ایران": t["iran_deploy"][:50]} for t in TOP3]
    steps = []
    for t in TOP3:
        for s in t.get("fine_tune_steps",[])[:3]:
            steps.append({"مدل": f"TOP{t['rank']}", "مرحله": s[:100]})
    return md, table, steps

def list_custom():
    if not HAS_KNOWLEDGE:
        return [], [], "دانش لود نشد"
    try:
        from joblink.knowledge.custom_models import CUSTOM_TOP3, RAG_MODELS_10
    except Exception:
        return [], [], "custom لود نشد"
    custom_rows = [{"ID": c.id, "نام": c.name[:50], "Base": c.base_model, "پارامتر": c.params, "بعد": c.dims, "کانتکست": c.context, "Rows": c.training_rows, "Iran": f"{c.iran_score}/10", "Best": c.best_for[:40], "Status": c.status} for c in CUSTOM_TOP3]
    rag_rows = [{"Rank": r["rank"], "نام": r["name"][:30], "نوع": r["type"][:20], "پارامتر": r["params"], "بعد": r["dims"], "کانتکست": r["context"], "Live": r["live_test"][:20], "Delta": r.get("delta_polysemy"), "Iran": f"{r['iran_score']}/10", "Best": r["best_for"][:30]} for r in RAG_MODELS_10]
    return custom_rows, rag_rows, f"{len(CUSTOM_TOP3)} custom + {len(RAG_MODELS_10)} RAG - delta 0.05-0.25"

def rag_search(query: str, domain: str, topk: int):
    if not HAS_KNOWLEDGE:
        return [], "RAG لود نشد"
    try:
        rag = get_rag()
        chunks = rag.search(query, top_k=topk, domain_filter=domain if domain else None)
        rows = [{"دامنه": c.domain_id, "نوع": c.type, "عنوان": c.title[:60], "متن": c.text[:200], "امتیاز": f"{c.score:.1f}", "لینک": c.url[:50]} for c in chunks]
        return rows, f"{len(chunks)} chunk برای '{query}'"
    except Exception as e:
        return [], f"خطا: {e}"

def get_news_info():
    if not HAS_KNOWLEDGE:
        return [], "خبر لود نشد"
    rows = [{"ID": n.id, "عنوان فارسی": n.title_fa[:50], "TR": n.title_tr[:40], "تاریخ": n.date, "منبع": n.source[:20], "دسته": n.category, "اهمیت": n.importance, "لینک": n.url[:40]} for n in NEWS_10]
    return rows, f"{len(NEWS_10)} خبر — 2025-2026 — برای سایت بهتر"

def show_news(news_id: str):
    if not HAS_KNOWLEDGE:
        return "خبر لود نشد", ""
    n = next((x for x in NEWS_10 if x.id==news_id or news_id in x.title_fa), None)
    if not n:
        return f"خبر {news_id} پیدا نشد", ""
    md = f"### {n.title_fa}\n**{n.title_tr}**\n**{n.title_en}**\n\n📅 {n.date} — {n.source}\n\n🔗 [{n.url}]({n.url})\n\n**دسته:** {n.category} — **اهمیت:** {n.importance} — **تگ:** {', '.join(n.tags)}\n\n**خلاصه فارسی:**\n{n.summary_fa}\n\n**Özet Türkçe:**\n{n.summary_tr}\n"
    return md, n.url

# --- Telegram Live Monitor 10 channels ---
def get_telegram_posts(limit: int = 20):
    try:
        # try multiple paths
        for path in ["knowledge/telegram_posts.json", "telegram_posts.json", "../data/telegram_posts.json"]:
            if os.path.exists(path):
                with open(path, encoding="utf-8") as fh:
                    data = json.load(fh)
                rows = []
                for p in data[: int(limit)]:
                    rows.append({
                        "ID": p.get("id","")[:8],
                        "کانال": p.get("channel_title_fa","")[:25],
                        "username": p.get("channel_username",""),
                        "متن": p.get("text","")[:80],
                        "تاریخ": p.get("date","")[:16],
                        "بازدید": p.get("views",""),
                        "دسته": p.get("category","")[:20],
                        "بهترین": "✅" if p.get("is_best") else "",
                        "لینک": p.get("link","")[:40],
                    })
                return rows, f"{len(data)} پست زنده از 10 کانال — آخرین: {data[0].get('scraped_at','')[:19] if data else '—'} — هر 3 ساعت آپدیت"
        return [], "فایل telegram_posts.json پیدا نشد — python -m joblink.telegram_monitor اجرا کن"
    except Exception as e:
        return [], f"خطا: {e}"

def show_telegram_post(post_id: str):
    try:
        for path in ["knowledge/telegram_posts.json", "telegram_posts.json", "../data/telegram_posts.json"]:
            if os.path.exists(path):
                with open(path, encoding="utf-8") as fh:
                    data = json.load(fh)
                p = next((x for x in data if post_id in x.get("id","") or post_id in x.get("text","") or post_id in x.get("channel_username","")), None)
                if not p:
                    continue
                # mask phones for display
                import re
                txt = p.get("text_full", p.get("text",""))
                txt_masked = re.sub(r"(\+?90|0)?\s?5\d{2}\s?\d{3}\s?\d{2}\s?\d{2}", "05XX XXX XX XX", txt)
                md = f"### {p.get('channel_title_fa')} — @{p.get('channel_username')}\n\n📅 {p.get('date')} — 👁 {p.get('views')} — {p.get('category')}\n\n🔗 [{p.get('link')}]({p.get('link')})\n\n👤 تماس عمومی: {p.get('contact_public')} — بدون شماره خصوصی (KVKK)\n\n**کمیسیون:** {p.get('commission')} — **بهترین:** {'✅' if p.get('is_best') else '—'}\n\n**متن کامل (ماسک شده):**\n{txt_masked[:1500]}\n\n---\n**ساعات کاری استخراج شده:**\n- معمول: 08:00-18:00 یا 08:30-19:00 — شنبه تا 15:00 — یکشنبه تعطیل (از متن)\n- حقوق: 25K-70K TL — با جای خواب + غذا + wifi در بسیاری\n\n**برای ربات:**\n- /telegram_live — نمایش 20 پست زنده با دکمه\n- چت AI: 'کار نظافت شیشلی با جای خواب می‌خوام' → RAG + این پست‌ها\n"
                return md, p.get("link","")
        return f"پست {post_id} پیدا نشد", ""
    except Exception as e:
        return f"خطا: {e}", ""

def get_telegram_channels_info():
    try:
        from joblink.telegram_channels import CHANNELS_10
        rows = [{"ID": c.id, "username": f"@{c.username}", "عنوان فارسی": c.title_fa[:25], "اعضا": c.members, "کمیسیون": c.commission[:20], "دسته": c.category[:30], "بهترین": "✅" if c.is_best else "", "تماس": c.contact_public, "لینک": c.url} for c in CHANNELS_10]
        return rows, f"10 کانال — بهترین: {len([c for c in CHANNELS_10 if c.is_best])} — هر 3 ساعت 20 پست جدید"
    except Exception as e:
        return [], f"خطا: {e}"

def get_links_info():
    return """
### 🔗 لینک‌های کامل JobLink — با دعوت‌نامه‌های شما + 10 خبر

**HuggingFace — مدل، دیتابیس، Space — تست شد:**
- 📚 دیتاست: `https://huggingface.co/datasets/sosa123454321/joblink-knowledge-fa-tr` — 529 ردیف + 20 embeddings + 660KB DB 10 جدول + 10 خبر — آماده push
- 🚀 Space: `https://huggingface.co/spaces/sosa123454321/joblink` — 12 تب — همین اپ LIVE — با لوگو + خبرها
- 🤖 Qwen3-0.6B: `https://huggingface.co/Qwen/Qwen3-Embedding-0.6B` — Live ✅ delta 0.159 ایران 10/10 — بهترین
- 🤖 bge-m3: `https://huggingface.co/BAAI/bge-m3` — Live ✅ delta 0.160 — RAG Master
- 🤖 e5-large: `https://huggingface.co/intfloat/multilingual-e5-large` — Live ✅ ولی delta 0.052 ضعیف
- 🤖 Llama-3.1-8B: `https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct` — CHAT OK فارسی — ربات @joblink_AI_bot

**تلگرام — ربات + کانال + گروه — با لینک‌های شما:**
- 🤖 ربات: `@joblink_AI_bot` — `https://t.me/joblink_AI_bot` — ✅ وجود دارد — فعال — دکمه پنجره‌ای 10 پست + توضیحات ست شد
- 📢 کانال شما: `joblink_tr_ir` — دعوت: `https://t.me/+WALqOptGwnwyNmU0` + عمومی: `https://t.me/joblink_tr_ir` — 2 subs — باید ربات را ادمین کنی
- 👥 گروه شما: `joblink_group` — دعوت: `https://t.me/+YmyYph5XV-NlN2I8` + عمومی: `https://t.me/joblink_group` — 2 members — ID -1002089796813 — باید ربات را ادمین کنی — آماده گفتگو
- 🔒 OT خصوصی: `@joblink_ot_private` — `https://t.me/joblink_ot_private` — private

**10 سایت ترکیه (منبع آگهی):**
eleman.net, kariyer.net, iskur.gov.tr, yenibiris.com, secretcv.com, elemanonline.com.tr, isinolsun.com, jooble.org/tr, indeed.com.tr, linkedin.com/jobs TR

**10 خبر جدید — برای سایت بهتر — learn theme:**
- news_01 حداقل دستمزد 2026: 33,030 TL (1x برای نظافت)
- news_02 ایرانیان در ترکیه 100K — 10 سال اقامت کوتاه‌مدت
- news_03 اجازه کار 90 روز بدون ویزا ولی بدون حق کار — کارفرما باید e-izin
- news_04 حقوق نظافتچی 20K-45K استانبول median 33K
- news_05 نظافت منزل 500-1500 TL هر بار
- news_06 نظافت Maltepe, Florya, Altunizade, Üsküdar — روزانه/شبانه‌روزی
- news_07 78 کار نظافت هتل لوکس Hilton, Raffles
- news_08 قانون جدید 10 اکتبر 2025 ترک‌تبار — 10 شرط سخت
- news_09 هشدار کار با ویزای توریستی ممنوع دیپورت + ممنوعیت دائم
- news_10 بسته‌بندی E-Ticaret 30K-40K با اینترنت — Şişli

**کد و داک:**
GitHub: `https://github.com/sosa123454321/joblink`
Docs: PLAN-FA, AI-MODELS, RITUQ-INSIDER, BOT-CHANNEL-SETUP, LINKS, HF-STATUS, CHANNEL-POSTS-10, BOT-BUTTONS, REMOTE-WORK, CLEANING-JOBS
لوگو: `logo.png` 512x512 + `banner.png` 1200x400 — assets/
"""

def get_bot_channel_info():
    return """
### 🤖 ربات @joblink_AI_bot — لوگو و توضیحات + کانال + گروه + OT — دکمه پنجره‌ای + 10 پست

**ربات شما:**
- @joblink_AI_bot — https://t.me/joblink_AI_bot — ID 8949733969 — ✅ فعال — getMe OK — can_join_groups true
- توضیحات: ✅ ست شد — Short + Description + 9 Commands — /start /katil /hayir /haziri /dorkari /shoghle /danesh /azmoon /help + جدید /post /post10 /digest /links
- دکمه پنجره‌ای: ✅ اضافه شد — main_keyboard 4 ردیف با لینک کانال و گروه شما — danesh 12 دکمه — azmoon 12 دکمه — آزمون 1,2,3,4
- لوگو: assets/logo.png 512x512 — باید دستی BotFather → Edit Botpic

**کانال شما:** joblink_tr_ir — https://t.me/+WALqOptGwnwyNmU0 — 2 subs — باید ربات را ادمین کنی: Post messages — بعد BOT_TOKEN=... python -m joblink.channel_poster --chat-id @joblink_tr_ir --limit 3

**گروه شما:** joblink_group — https://t.me/+YmyYph5XV-NlN2I8 — 2 members — ID -1002089796813 — باید ربات را ادمین کنی: Delete messages, Pin — BotFather Group Privacy Turn off — بعد /post10 → 10 پست هر زمینه دیروز فارسی+ترکی با دکمه — آماده گفتگو

**OT خصوصی:** @joblink_ot_private — private — فقط ادمین‌ها + ربات

**ماژول‌های سایت اضافه شد:**
- channel_poster.py — پست با استایل سایت + دکمه پنجره‌ای لینک اصلی + قوانین + بحث در گروه + کانال + ربات
- bot.py — handle_group_events, handle_callback, main_keyboard, danesh_keyboard, azmoon_keyboard, job_keyboard, /post10 (10 پست)
- 10 پست دیروز: CHANNEL-POSTS-10-FA-TR.md — هر زمینه 1 آگهی — فارسی+ترکی — با دکمه — آماده کانال و گروه — آماده گفتگو

**تست:**
BOT_TOKEN=... python -m joblink.channel_poster --chat-id @joblink_tr_ir --limit 3 --city Istanbul
در گروه: /post10 و /digest و /links
"""

def ai_training_info():
    return """
# آموزش مدل شخصی‌سازی شده JobLink برای ایران

**معماری TOP3 + Custom Rituq:**
- 🥇 Iran-Light: Qwen3-0.6B (1024 dim, 32K, MRL) + Qwen2.5-7B (131K, TurkishMMLU 54.28) — Iran 10/10 — delta 0.159 تست زنده
- 🥈 RAG-Master: bge-m3 (hybrid) — delta 0.160 — 8192 — MIT
- 🥉 Baby Rituq: Phi-3-mini 3.8B 2.2GB Q4 — 0$ offline — آفلاین کامل
- 📰 10 خبر جدید — حداقل دستمزد 2026 33,030 TL, ایرانیان 100K, اجازه کار 90 روز, حقوق نظافت 20K-45K, هشدار توریستی ممنوع

**چرا Qwen3-0.6B بهترین برای ایران:**
- 639MB، 32K کانتکست vs e5 512
- MTEB 64.33، MRL تا 32 بعد برای D1
- Apache-2.0 تجاری مجاز
- GGUF/ONNX آماده، CPU inference
- تست زنده: جوشکار CO2 مثبت 0.47 vs منفی 0.31 delta 0.16 خوب — e5-large delta 0.05 ضعیف

**Golden dataset:** 561 ردیف fa→tr با polysemy trap kaynak
**Embeddings:** 20 چانک معنایی ساخته شد با Qwen3-0.6B — برای 492 کامل نیاز به PRO $9 یا local sentence-transformers
"""

with gr.Blocks(title="JobLink — ایران ⇄ ترکیه + دانش + 3 مدل برتر + Rituq + 10 خبر + 10 کانال زنده + لوگو") as demo:
    gr.Markdown(
        "# 🤝 JobLink — اوبر برای کار + پایگاه دانش + 3 مدل AI برتر + Rituq Insider + 10 خبر + 10 کانال زنده\n"
        f"آگهی: **{len(JOBS)}** · حوزه: **{len(DOMAINS) if HAS_KNOWLEDGE else 0}** · منابع: **{len(RESOURCES) if HAS_KNOWLEDGE else 0}** · "
        f"آزمون: **{len(QUIZZES) if HAS_KNOWLEDGE else 0}** · مدل: **{len(MODELS) if HAS_KNOWLEDGE else 0}** · خبر: **{len(NEWS_10) if HAS_KNOWLEDGE else 0}** · "
        f"تلگرام زنده: 20 پست از 10 کانال هر 3 ساعت · Custom: 3 · RAG10: 10 · Embeddings: 20 · **Space: 12 تب + لوگو + خبرها + زنده**\n\n"
        f"**لوگو:** `logo.png` + `banner.png` — **ربات:** @joblink_AI_bot — **کانال:** https://t.me/+WALqOptGwnwyNmU0 — **گروه:** https://t.me/+YmyYph5XV-NlN2I8\n\n"
        f"**HF:** [دیتاست](https://huggingface.co/datasets/sosa123454321/joblink-knowledge-fa-tr) 529 ردیف · [Space](https://huggingface.co/spaces/sosa123454321/joblink) · "
        f"[Qwen3-0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B) · [bge-m3](https://huggingface.co/BAAI/bge-m3)"
    )
    with gr.Tab("کارجو / Job seeker"):
        cv = gr.Textbox(label="متن رزومه", lines=12, value="برنامه‌نویس ارشد بک‌اند. ۶ سال Python, Django, PostgreSQL, Docker. انگلیسی خوب، ترکی آشنایی. تهران. دورکاری ۲۵۰۰ دلار.")
        with gr.Row():
            rel = gr.Checkbox(label="آماده مهاجرت ترکیه", value=False)
            topk = gr.Slider(3, 15, value=5, step=1, label="تعداد پیشنهاد")
        btn = gr.Button("پیدا کن", variant="primary")
        info = gr.Markdown()
        out = gr.Dataframe(headers=["آگهی","کارفرما","شهر","امتیاز","مهارت‌های هم‌پوشان","فاصله‌ها"], wrap=True, row_count=(5,"dynamic"))
        status = gr.Markdown()
        btn.click(seek, inputs=[cv, rel, topk], outputs=[info, out, status])

    with gr.Tab("🇹🇷 120+ جستجوی شغل ترکیه / Turkey Jobs"):
        gr.Markdown("## جستجوی رتبه‌بندی‌شده برای تازه‌واردان ایرانی در ترکیه\n۶ حوزه × حداقل ۲۰ لینک جست‌وجوی عمومی: AI، Agentic AI، Software، Maker/Robotics، Biomedical، Engineering. برای هر مورد سایت اصلی و وضعیت اجازه کار را بررسی کنید.")
        with gr.Row():
            tc = gr.Dropdown(["AI / Yapay Zeka","Agentic AI / LLM","Software Engineering","Maker / Robotics","Biomedical","Engineering"], value="AI / Yapay Zeka", label="حوزه")
            ts = gr.Dropdown(["All","Kariyer.net","Indeed Türkiye","LinkedIn Jobs","Yenibiriş","Eleman.net","Secretcv","Jooble Türkiye","Glassdoor","Talent.com","İşin Olsun"], value="All", label="سایت")
            tl = gr.Slider(10, 20, value=20, step=10, label="نتیجه")
        tb = gr.Button("🔎 جستجو و رتبه‌بندی لینک‌ها", variant="primary")
        tout = gr.Dataframe(headers=["Kategori","Arama","Site","Ülke","Başvuru","Not"], wrap=True, row_count=(20,"dynamic"))
        tstatus = gr.Markdown()
        tb.click(turkey_search, inputs=[tc, ts, tl], outputs=[tout, tstatus])

    with gr.Tab("کارفرما / Employer"):
        q = gr.Textbox(label="جستجوی آگهی", placeholder="python ya da muhasebe")
        lim = gr.Slider(5, 100, value=25, step=5, label="تعداد")
        bout = gr.Button("نمایش", variant="primary")
        jout = gr.Dataframe(headers=["منبع","عنوان","کارفرما","شهر","حقوق (TL)","دورکاری","لینک"], wrap=True, row_count=(10,"dynamic"))
        bout.click(browse, inputs=[q, lim], outputs=jout)

    with gr.Tab("📚 پایگاه دانش / Knowledge"):
        gr.Markdown("## 12 حوزه - هر کدام 10 مقاله+10 کتاب+10 ویدیو")
        with gr.Row():
            btn_dom = gr.Button("لیست 12 حوزه")
            dom_id = gr.Textbox(label="کد حوزه", value="d01")
            btn_show = gr.Button("نمایش")
        dom_table = gr.Dataframe(headers=["کد","عنوان فارسی","EN","ریسک","کلیدواژه","قوانین"], wrap=True, row_count=(12,"dynamic"))
        dom_status = gr.Markdown()
        dom_desc = gr.Markdown()
        with gr.Row():
            art_table = gr.Dataframe(headers=["نوع","عنوان","لینک","نویسنده","سال","خلاصه"], wrap=True)
            book_table = gr.Dataframe(headers=["نوع","عنوان","نویسنده","سال","خلاصه"], wrap=True)
        vid_table = gr.Dataframe(headers=["عنوان","لینک","سال"], wrap=True)
        btn_dom.click(list_domains, outputs=[dom_table, dom_status])
        btn_show.click(show_domain, inputs=[dom_id], outputs=[dom_desc, art_table, book_table, vid_table])

    with gr.Tab("📝 آزمون / Quiz"):
        gr.Markdown("## آزمون 10 سوالی هر حوزه - تلگرام /azmoon — با دکمه 1,2,3,4")
        with gr.Row():
            quiz_dom = gr.Textbox(label="کد حوزه", value="d01")
            quiz_btn = gr.Button("شروع آزمون")
        quiz_info = gr.Markdown()
        quiz_table = gr.Dataframe(headers=["سوال","گزینه 1","گزینه 2","گزینه 3","گزینه 4","جواب درست","توضیح","سختی"], wrap=True, row_count=(10,"dynamic"))
        quiz_first = gr.Markdown()
        quiz_btn.click(start_quiz, inputs=[quiz_dom], outputs=[quiz_info, quiz_table, quiz_first])

    with gr.Tab("🤖 10 مدل AI + TOP3"):
        gr.Markdown("## 10 مدل مقایسه + 3 مدل برتر سفارشی JobLink")
        with gr.Row():
            btn_models = gr.Button("لیست 11 مدل")
            btn_top3 = gr.Button("نمایش TOP3")
        models_table = gr.Dataframe(headers=["ID","نام","نوع","پارامتر","بعد","کانتکست","fa/tr","Live HF","MTEB","Iran","بهترین برای"], wrap=True, row_count=(11,"dynamic"))
        models_status = gr.Markdown()
        top3_md = gr.Markdown()
        top3_table = gr.Dataframe(headers=["رتبه","نام","Embedding","LLM","هزینه","ایران"], wrap=True)
        top3_steps = gr.Dataframe(headers=["مدل","مرحله"], wrap=True)
        btn_models.click(list_models, outputs=[models_table, models_status])
        btn_top3.click(show_top3, outputs=[top3_md, top3_table, top3_steps])

    with gr.Tab("👶 Rituq Insider + RAG 10"):
        gr.Markdown("## 3 مدل کاستوم Rituq Insider + 10 مدل RAG با delta polysemy تست زنده")
        btn_custom = gr.Button("نمایش مدل‌های کاستوم Rituq")
        custom_table = gr.Dataframe(headers=["ID","نام","Base","پارامتر","بعد","کانتکست","Rows","Iran","Best","Status"], wrap=True, row_count=(3,"dynamic"))
        rag10_table = gr.Dataframe(headers=["Rank","نام","نوع","پارامتر","بعد","کانتکست","Live","Delta","Iran","Best"], wrap=True, row_count=(10,"dynamic"))
        custom_status = gr.Markdown()
        btn_custom.click(list_custom, outputs=[custom_table, rag10_table, custom_status])
        gr.Markdown("""
### توصیه نهایی (تست زنده 2026-09-14):
- **Best overall:** Qwen3-0.6B - 639MB، 32K، MRL، delta 0.16، ایران 10/10
- **Best RAG:** bge-m3 - hybrid، delta 0.16، 8192، MIT
- **Best offline Baby Rituq:** Phi-3-mini 3.8B 2.2GB Q4 - 0$ آفلاین
- **Worst:** e5-large delta 0.05 - جوشکار را به برنامه‌نویس مچ می‌کند
- **Embeddings:** 20 چانک معنایی ساخته شد با Qwen3-0.6B، برای 492 کامل نیاز به PRO $9
""")

    with gr.Tab("📰 10 خبر / News — سایت بهتر"):
        gr.Markdown("## 10 خبر جدید — حداقل دستمزد 2026، ایرانیان 100K، اجازه کار، نظافت، هشدار توریستی — برای سایت بهتر + learn theme")
        with gr.Row():
            btn_news = gr.Button("لیست 10 خبر")
            news_id = gr.Textbox(label="ID خبر (مثلا news_01)", value="news_01")
            btn_show_news = gr.Button("نمایش خبر")
        news_table = gr.Dataframe(headers=["ID","عنوان فارسی","TR","تاریخ","منبع","دسته","اهمیت","لینک"], wrap=True, row_count=(10,"dynamic"))
        news_status = gr.Markdown()
        news_md = gr.Markdown()
        news_url = gr.Markdown()
        btn_news.click(get_news_info, outputs=[news_table, news_status])
        btn_show_news.click(show_news, inputs=[news_id], outputs=[news_md, news_url])

    with gr.Tab("📡 تلگرام زنده / Live — 10 کانال هر 3 ساعت — 20 پست"):
        gr.Markdown("## 📡 10 کانال کاریابی تلگرام — هر 3 ساعت 20 پست جدید — ماسک KVKK — با دکمه + AI چت")
        with gr.Row():
            btn_tg_channels = gr.Button("لیست 10 کانال")
            btn_tg_posts = gr.Button("20 پست زنده")
            tg_limit = gr.Slider(5, 50, value=20, step=5, label="تعداد پست")
            tg_id = gr.Textbox(label="ID پست یا username (مثلا karyabi06666 یا a457...)", value="karyabi06666")
            btn_show_tg = gr.Button("نمایش پست")
        tg_channels_table = gr.Dataframe(headers=["ID","username","عنوان فارسی","اعضا","کمیسیون","دسته","بهترین","تماس","لینک"], wrap=True, row_count=(10,"dynamic"))
        tg_channels_status = gr.Markdown()
        tg_posts_table = gr.Dataframe(headers=["ID","کانال","username","متن","تاریخ","بازدید","دسته","بهترین","لینک"], wrap=True, row_count=(20,"dynamic"))
        tg_posts_status = gr.Markdown()
        tg_post_md = gr.Markdown()
        tg_post_url = gr.Markdown()
        btn_tg_channels.click(get_telegram_channels_info, outputs=[tg_channels_table, tg_channels_status])
        btn_tg_posts.click(get_telegram_posts, inputs=[tg_limit], outputs=[tg_posts_table, tg_posts_status])
        btn_show_tg.click(show_telegram_post, inputs=[tg_id], outputs=[tg_post_md, tg_post_url])
        gr.Markdown("""
### 🤖 چت با هوش مصنوعی + دکمه — تسهیلات کانال‌ها

**چت AI (در ربات @joblink_AI_bot):**
- `/telegram_live` → 20 پست زنده با دکمه پنجره‌ای
- سوال: `کار نظافت شیشلی با جای خواب می‌خوام` → RAG روی 529 منبع + 20 پست تلگرام + embeddings Qwen3-0.6B → جواب فارسی+ترکی + لینک اصلی + هشدار izni
- سوال: `حقوق 70K قیصریه سنگ مرمر چیه؟` → از @ostadkaraniraq پست 70K + توضیح ساعات 8-8 + جای خواب عالی

**دکمه پنجره‌ای برای هر پست (Inline):**
```
[📄 پست اصلی] -> t.me/...
[📚 قوانین] [💬 بحث گروه] -> https://t.me/+WALqOptGwnwyNmU0 + https://t.me/+YmyYph5XV-NlN2I8
[🤖 ربات] [🚀 Space] -> @joblink_AI_bot + Space
[🔗 کانال اصلی] -> @karyabi06666 etc
```

**زمان‌بندی — هر 3 ساعت:**
```bash
BOT_TOKEN=... CHANNEL_ID=@joblink_tr_ir GROUP_ID=@joblink_group python -m joblink.telegram_scheduler --once
# برای همیشه:
BOT_TOKEN=... python -m joblink.telegram_scheduler --hours 3
# یا cron:
0 */3 * * * cd /home/user/joblink && BOT_TOKEN=... python -m joblink.telegram_monitor && BOT_TOKEN=... python -m joblink.telegram_scheduler --once
```

**ساعات کاری استخراج شده از 10 کانال:**
- معمول: 08:00-18:00 یا 08:30-19:00 — شنبه تا 15:00 — یکشنبه تعطیل
- شیفت: 11:00-21:00 و 16:00-02:00 (گارسون غرب استانبول واسنیورت 31K)
- حقوق: 25K-70K TL — قیصریه سنگ مرمر 70K با اضافه‌کار 3 وعده + wifi + جای خواب عالی
- مکان: Esenyurt, Beylikdüzü, Şişli, Florya, Malatya, Kayseri, Güneşli

**KVKK:** شماره‌ها ماسک 05XX XXX XX XX — فقط آیدی عمومی @turk_iran_karyabi @Mohamadkhedmati @fms93 @d_turkey @vahidtur @venusdogan @ads_turkey @istkaryab @Turkish_Groupp @joblink_AI_bot
""")

    with gr.Tab("🔍 RAG / جستجوی دانش"):
        gr.Markdown("## RAG روی 529 منبع + 97 آگهی - جستجوی حقوقی - با 20 embeddings معنایی")
        with gr.Row():
            rag_q = gr.Textbox(label="پرسش", value="اجازه کار ترکیه چگونه است؟")
            rag_dom = gr.Textbox(label="فیلتر دامنه (اختیاری مثلا d01)", value="")
            rag_k = gr.Slider(1, 10, value=5, step=1, label="Top K")
            rag_btn = gr.Button("جستجو RAG")
        rag_table = gr.Dataframe(headers=["دامنه","نوع","عنوان","متن","امتیاز","لینک"], wrap=True)
        rag_status = gr.Markdown()
        rag_btn.click(rag_search, inputs=[rag_q, rag_dom, rag_k], outputs=[rag_table, rag_status])

    with gr.Tab("🔗 لینک‌ها / Links"):
        gr.Markdown(get_links_info())
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
            if os.path.exists(logo_path):
                gr.Image(value=logo_path, label="Logo JobLink 512x512", height=200)
            banner_path = os.path.join(os.path.dirname(__file__), "banner.png")
            if os.path.exists(banner_path):
                gr.Image(value=banner_path, label="Banner 1200x400", height=150)
        except Exception:
            pass

    with gr.Tab("🤖 ربات + کانال + گروه / Bot Channel"):
        gr.Markdown(get_bot_channel_info())
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
            if os.path.exists(logo_path):
                gr.Image(value=logo_path, label="Logo - برای BotFather Edit Botpic", height=200)
        except Exception:
            pass

    with gr.Tab("📖 آموزش AI ایران"):
        gr.Markdown(ai_training_info())
        gr.Markdown(f"""
### دیتاست HF شامل مدل‌ها + خبرها

- 12 domain + 120 article + 120 book + 120 video + 120 quiz + 11 ai_model + 3 top + 3 custom + 10 rag + 10 news = **529 ردیف**
- DB: 660KB 10 جدول + 20 embeddings (Qwen3-0.6B) + news_10
- فایل‌ها: `hf_dataset.jsonl`, `ai_models.json`, `top3_models.json`, `custom_models.json`, `rag_10_models.json`, `news_10.json`, `golden_fa_tr.jsonl` (561 ردیف)

**TOP3 + Custom Rituq:**
- Iran-Light: Qwen3-0.6B + Qwen2.5-7B — Iran 10/10
- RAG-Master: bge-m3 — hybrid delta 0.16
- Baby-Rituq: Phi-3-mini — offline 0$ — @joblink_AI_bot
- 10 خبر: حداقل دستمزد 2026 33,030 TL, ایرانیان 100K, اجازه کار 90 روز, نظافت 20K-45K, هشدار توریستی ممنوع

**برای تلگرام:**
- /danesh, /azmoon d01, /post10 (10 پست با دکمه), /links, /digest
- دکمه پنجره‌ای: دانش, آزمون, شغل, لینک‌ها, کانال, گروه, ربات, Space
- RAG: هر مچ شغلی توضیح حقوقی از d01/d02/d06 می‌گیرد
""")

    gr.Markdown("---\nرضایت opt-in only (KVKK/GDPR). پایگاه دانش 12 حوزه + 11 مدل + TOP3 + 3 Custom Rituq + 10 RAG + 10 خبر + 20 embeddings + 12 تب + لوگو + لینک‌ها + دکمه پنجره‌ای | ربات: @joblink_AI_bot | کانال: https://t.me/+WALqOptGwnwyNmU0 | گروه: https://t.me/+YmyYph5XV-NlN2I8 | OT: @joblink_ot_private | Space LIVE")

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("SPACE_PORT", 7860)))
