"""Telegram intake + notification bot (the seeker-side acquisition channel) + Knowledge Quiz.

Why Telegram and not a web form: in the blue-collar / Iran-resident segment the phone already
has Telegram, a form has brutal drop-off, and the consent capture is a single tap.

Legal shape:
    /start  -> consent message, nothing stored
    /katil  -> explicit opt-in, consent_token minted
    <text>  -> parsed as CV, stored, matches returned
    /hayir  -> consent revoked, row + matches deleted (KVKK m.7 / GDPR art.17)
    /danesh -> knowledge base (12 domains)
    /azmoon -> 10-question quiz per domain
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from .intake import candidate_from_cv
from .matcher import Matcher
from .store import Store

# knowledge base (12 domains)
try:
    from .knowledge.domains import DOMAINS
    from .knowledge.resources import RESOURCES
    from .knowledge.bot_quiz import quiz_manager
    HAS_KNOWLEDGE = True
except Exception:
    HAS_KNOWLEDGE = False
    DOMAINS = []
    RESOURCES = []
    quiz_manager = None

CONSENT_TEXT = (
    "JobLink آگهی‌های استخدام ترکیه را با رزومهٔ تو مقایسه می‌کند.\n\n"
    "برای ادامه باید بگویی «می‌خوام» تا:\n"
    "• رزومه‌ات پیش ما ذخیره و برای مهارت‌ها پردازش شود\n"
    "• فقط وقتی مچ خوبی پیدا شد، کارفرما پروفایل *بدون نام و شماره* تو را ببیند\n"
    "• هر وقت خواستی با /hayir همه‌چیز حذف شود\n\n"
    "قوانین: joblink.example/privacy — پاسخ: /katil"
)
WELCOME = "عالی ✅ حالا متن رزومه‌ات را بفرست (فارسی، ترکی یا انگلیسی فرقی نمی‌کند)."
NOT_YET = "اول باید رضایت بدهی: /katil"
NO_MATCH = ("امروز آگهی متناسبی پیدا نشد. این خوب است: ما آگهی بی‌ربط پیشنهاد نمی‌دهیم.\n"
            "مهارت یا شهرت را در /profil بنویس تا دوباره نگاه کنم.")
HELP = ("/katil ثبت‌نام · /haziri آمادهٔ مهاجرت · /dorkari فقط دورکاری\n"
        "/shoghle ۵ پیشنهاد جدید · /hayir حذف کامل داده‌ها\n"
        "/danesh لیست حوزه‌های حقوقی · /danesh d01 جزئیات\n"
        "/azmoon آزمون 10 سوالی · /azmoon d01 آزمون اجازه کار\n"
        "جواب آزمون: عدد 1-4 بفرست")
RELOCATE_HINT = ("{n} آگهی هم‌مهارت پیدا شد ولی **حضوری** است. اگر واقعاً آمادهٔ رفتی، /haziri را بزن "
                 "تا دوباره نگاه کنم. (بدون Çalışma izni هیچ‌وقت شروع نکن — راهنما: joblink.example/visa)")

QUIZ_DDL = """
CREATE TABLE IF NOT EXISTS quiz_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  chat_id TEXT, domain_id TEXT, score INTEGER, total INTEGER, pct INTEGER, ts TEXT
);
CREATE TABLE IF NOT EXISTS quiz_state (
  chat_id TEXT PRIMARY KEY, domain_id TEXT, current INTEGER, score INTEGER, questions TEXT
);
"""


def api_caller(token: str) -> Callable[..., dict]:
    """Real Bot API transport (long-poll is fine: <1 req/s)."""
    import httpx

    def api(method: str, **kw: Any) -> dict:
        with httpx.Client(timeout=45.0) as c:
            r = c.post(f"https://api.telegram.org/bot{token}/{method}", json=kw)
            return r.json()
    return api


@dataclass
class Bot:
    store: Store
    api: Callable[..., dict]
    offset: int = 0
    top_k: int = 5
    admins: list[int] = field(default_factory=list)
    sent: list[tuple[int, str]] = field(default_factory=list)      # captured replies (tests/dry-run)

    # ---------------- outbound ----------------
    def send(self, chat_id: int, text: str, reply_markup: dict | None = None) -> None:
        self.sent.append((chat_id, text))
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        self.api("sendMessage", **payload)

    def send_with_buttons(self, chat_id: int, text: str, buttons: list[list[dict]]) -> None:
        """Inline buttons for cards and callbacks."""
        self.send(chat_id, text, reply_markup={"inline_keyboard": buttons})

    def main_reply_keyboard(self) -> dict:
        """Persistent bottom keyboard: users can operate without typing commands."""
        return {"keyboard": [
            [{"text": "💼 شغل‌ها"}, {"text": "📡 آگهی‌های زنده"}],
            [{"text": "📚 دانش"}, {"text": "📝 آزمون"}],
            [{"text": "🌐 زبان"}, {"text": "🔗 لینک‌ها"}],
            [{"text": "📢 کانال"}, {"text": "👥 گروه"}],
            [{"text": "❌ حذف اطلاعات"}],
        ], "resize_keyboard": True, "is_persistent": True, "input_field_placeholder": "از دکمه‌ها استفاده کنید؛ نوشتن رزومه اختیاری است"}

    def send_with_menu(self, chat_id: int, text: str) -> None:
        self.send(chat_id, text, reply_markup=self.main_reply_keyboard())

    # ---------------- keyboards ----------------
    def language_keyboard(self) -> list[list[dict]]:
        return [[
            {"text": "🇮🇷 فارسی", "callback_data": "lang_fa"},
            {"text": "🇹🇷 Türkçe", "callback_data": "lang_tr"},
            {"text": "🇬🇧 English", "callback_data": "lang_en"},
            {"text": "🇸🇦 العربية", "callback_data": "lang_ar"},
        ], [{"text": "🔙 منوی اصلی", "callback_data": "start"}]]

    def main_keyboard(self) -> list[list[dict]]:
        return [
            [{"text": "📚 پایگاه دانش", "callback_data": "danesh"}, {"text": "📝 آزمون", "callback_data": "azmoon"}],
            [{"text": "💼 5 شغل جدید", "callback_data": "shoghle"}, {"text": "📡 زنده 10 کانال", "callback_data": "telegram_live"}],
            [{"text": "🔗 10 کانال لیست", "callback_data": "tg_channels"}, {"text": "🔗 لینک‌ها", "callback_data": "links"}],
            [{"text": "🌐 زبان / Language", "callback_data": "language"}],
            [{"text": "📢 کانال", "url": "https://t.me/+WALqOptGwnwyNmU0"}, {"text": "👥 گروه", "url": "https://t.me/+YmyYph5XV-NlN2I8"}],
            [{"text": "🤖 ربات", "url": "https://t.me/joblink_AI_bot"}, {"text": "🚀 Space 12 تب", "url": "https://huggingface.co/spaces/sosa123454321/joblink"}],
        ]

    def danesh_keyboard(self) -> list[list[dict]]:
        # 12 domains in 3 rows of 4
        rows = []
        for i in range(0, 12, 4):
            row = []
            for d in DOMAINS[i:i+4]:
                row.append({"text": f"{d.id} {d.title_fa[:12]}", "callback_data": f"danesh_{d.id}"})
            rows.append(row)
        rows.append([{"text": "🔙 بازگشت", "callback_data": "start"}])
        return rows

    def azmoon_keyboard(self) -> list[list[dict]]:
        rows = []
        for i in range(0, 12, 4):
            row = []
            for d in DOMAINS[i:i+4]:
                row.append({"text": f"{d.id}", "callback_data": f"azmoon_{d.id}"})
            rows.append(row)
        rows.append([{"text": "🎲 تصادفی", "callback_data": "azmoon_random"}, {"text": "🔙 بازگشت", "callback_data": "start"}])
        return rows

    def job_keyboard(self, job_url: str, domain_id="d01") -> list[list[dict]]:
        return [
            [{"text": "📄 لینک اصلی", "url": job_url}, {"text": "📚 قوانین", "callback_data": f"danesh_{domain_id}"}],
            [{"text": "💬 بحث در گروه", "url": "https://t.me/+YmyYph5XV-NlN2I8"}, {"text": "📢 کانال", "url": "https://t.me/+WALqOptGwnwyNmU0"}],
            [{"text": "🔙 5 شغل دیگر", "callback_data": "shoghle"}]
        ]

    # ---------------- consent ----------------
    @staticmethod
    def mint_token(chat_id: int | str) -> str:
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        h = hashlib.sha256(f"joblink|{chat_id}|{ts}".encode()).hexdigest()[:16]
        return f"v1:{ts}:tg:{chat_id}:{h}"

    def optin(self, chat_id: int, update_id: int) -> None:
        from .models import now_iso
        self.store.db.execute(
            """INSERT INTO consent (cid, chat_id, action, token, ts, update_id)
               VALUES(?,?,?,?,?,?)""",
            (f"tg-{chat_id}", str(chat_id), "granted", self.mint_token(chat_id), now_iso(), update_id))
        self.store.db.commit()
        self.send(chat_id, WELCOME + "\n\n" + HELP)

    def optout(self, chat_id: int, update_id: int) -> None:
        from .models import now_iso
        cid = f"tg-{chat_id}"
        self.store.db.execute(
            "INSERT INTO consent (cid, chat_id, action, token, ts, update_id) VALUES(?,?,?,?,?,?)",
            (cid, str(chat_id), "revoked", "revoked:" + now_iso(), now_iso(), update_id))
        self.store.db.commit()
        self.store.db.execute("DELETE FROM candidates WHERE cid=?", (cid,))
        self.store.db.execute("DELETE FROM matches WHERE cid=?", (cid,))
        self.store.db.commit()
        self.send(chat_id, "همه‌چیز پاک شد. اگر دوباره خواستی: /katil")

    def current_token(self, chat_id: int) -> str | None:
        row = self.store.db.execute(
            """SELECT token FROM consent WHERE chat_id=? AND action='granted'
               ORDER BY id DESC LIMIT 1""", (str(chat_id),)).fetchone()
        if row is None:
            return None
        gone = self.store.db.execute(
            """SELECT 1 FROM consent WHERE chat_id=? AND action='revoked' AND id >
               (SELECT id FROM consent WHERE token=? LIMIT 1)""", (str(chat_id), row["token"])).fetchone()
        return None if gone else row["token"]

    # ---------------- preferences ----------------
    def set_prefs(self, chat_id: int, *, relocate: bool | None = None,
                  remote: bool | None = None) -> None:
        cid = f"tg-{chat_id}"
        cur = self.store.db.execute("SELECT cid FROM candidates WHERE cid=?", (cid,)).fetchone()
        if cur is None:
            self.send(chat_id, NOT_YET)
            return
        if relocate is not None:
            self.store.db.execute("UPDATE candidates SET open_relocate=? WHERE cid=?",
                                  (int(relocate), cid))
        if remote is not None:
            self.store.db.execute("UPDATE candidates SET open_remote=? WHERE cid=?", (int(remote), cid))
        self.store.db.commit()
        self.rerank(chat_id, prefix="تنظیم شد ✅\n\n")

    def rerank(self, chat_id: int, *, prefix: str = "") -> None:
        cid = f"tg-{chat_id}"
        cand = next((c for c in self.store.candidates() if c.cid == cid), None)
        if cand is None:
            self.send(chat_id, NOT_YET)
            return
        ms = Matcher(self.store.jobs()).rank_jobs(cand, k=self.top_k)
        if not ms:
            self.send(chat_id, NO_MATCH)
            return
        lines = [f"{prefix}{len(ms)} آگهی:", ""]
        for i, m in enumerate(ms, 1):
            gap = " · فاصله: " + ", ".join(g.item for g in m.gaps[:2]) if m.gaps else ""
            lines.append(f"{i}) {m.title} — {m.company or '—'} ({m.city or 'TR'}) "
                         f"امتیاز {m.score:.0f}{gap}\n   {m.url}")
        self.send(chat_id, "\n".join(lines)[:3900])

    # ---------------- knowledge ----------------
    def handle_danesh(self, chat_id: int, args: str) -> None:
        if not HAS_KNOWLEDGE:
            self.send(chat_id, "پایگاه دانش هنوز لود نشده.")
            return
        arg = args.strip().lower()
        if not arg:
            # list domains with buttons
            self.send_with_buttons(chat_id, "📚 پایگاه دانش JobLink — 12 حوزه — یکی را انتخاب کن:", self.danesh_keyboard())
            return
        parts = arg.split()
        did = parts[0]
        # find domain
        dom = next((x for x in DOMAINS if x.id==did or x.slug==did), None)
        if not dom:
            self.send_with_buttons(chat_id, f"حوزه {did} پیدا نشد. یکی را انتخاب کن:", self.danesh_keyboard())
            return
        if len(parts)>=2 and parts[1] in ("manabe","منابع","resources"):
            # show resources
            res = [r for r in RESOURCES if r.domain_id==dom.id]
            articles = [r for r in res if r.kind=="article"][:5]
            books = [r for r in res if r.kind=="book"][:5]
            videos = [r for r in res if r.kind=="video"][:5]
            lines = [f"📖 منابع {dom.title_fa} ({dom.id}):\n"]
            lines.append("📰 مقالات:")
            for a in articles:
                lines.append(f"• {a.title} - {a.url}")
            lines.append("\n📚 کتاب‌ها:")
            for b in books:
                lines.append(f"• {b.title} - {b.author} {b.year}")
            lines.append("\n🎥 ویدیوها:")
            for v in videos:
                lines.append(f"• {v.title}")
            lines.append(f"\nبرای آزمون: /azmoon {dom.id}")
            self.send_with_buttons(chat_id, "\n".join(lines)[:3900], [[{"text": f"📝 آزمون {dom.id}", "callback_data": f"azmoon_{dom.id}"}, {"text": "📚 لیست حوزه‌ها", "callback_data": "danesh"}]])
        else:
            # show domain detail
            lines = [
                f"📘 {dom.title_fa} ({dom.id})",
                f"EN: {dom.title_en}",
                f"ریسک: {dom.risk_level}",
                f"\n{dom.description_fa}",
                f"\nچرا مهم: {dom.why_needed}",
                f"\nقوانین: {', '.join(dom.relevant_laws)}",
                f"کلیدواژه: {', '.join(dom.keywords[:5])}",
                f"\nمنابع: 10 مقاله + 10 کتاب + 10 ویدیو موجود است",
            ]
            self.send_with_buttons(chat_id, "\n".join(lines)[:3900], [[{"text": "📖 منابع", "callback_data": f"danesh_{dom.id}"}, {"text": f"📝 آزمون {dom.id}", "callback_data": f"azmoon_{dom.id}"}], [{"text": "📚 لیست حوزه‌ها", "callback_data": "danesh"}, {"text": "🔙 بازگشت", "callback_data": "start"}]])

    def handle_azmoon(self, chat_id: int, args: str) -> None:
        if not HAS_KNOWLEDGE or not quiz_manager:
            self.send(chat_id, "سیستم آزمون هنوز آماده نیست.")
            return
        arg = args.strip().lower()
        did = None
        if arg:
            # extract domain id
            candidate = arg.split()[0]
            if any(d.id==candidate or d.slug==candidate for d in DOMAINS):
                did = candidate
        if not did:
            # show keyboard to choose domain
            self.send_with_buttons(chat_id, "📝 آزمون — 12 حوزه — یکی را انتخاب کن:", self.azmoon_keyboard())
            return
        sess = quiz_manager.start(chat_id, domain_id=did)
        title = quiz_manager.get_domain_title(sess.domain_id)
        self.send_with_buttons(chat_id, f"📝 آزمون {title} شروع شد - 10 سوال\n\n" + quiz_manager.format_question(sess.questions[0]), [[{"text": "1", "callback_data": "quiz_0"}, {"text": "2", "callback_data": "quiz_1"}, {"text": "3", "callback_data": "quiz_2"}, {"text": "4", "callback_data": "quiz_3"}]])

    def handle_quiz_answer(self, chat_id: int, text: str) -> bool:
        """Return True if it was a quiz answer and handled."""
        if not HAS_KNOWLEDGE or not quiz_manager:
            return False
        sess = quiz_manager.sessions.get(chat_id)
        if not sess:
            return False
        if sess.current >= len(sess.questions):
            return False
        # parse 1-4
        m = re.match(r"^\s*([1-4])\s*$", text.strip())
        if not m:
            # also allow A-D
            m2 = re.match(r"^\s*([a-dA-D])\s*$", text.strip())
            if m2:
                choice = ord(m2.group(1).lower()) - ord('a')
            else:
                return False
        else:
            choice = int(m.group(1))-1
        res = quiz_manager.answer(chat_id, choice)
        if res.get("error"):
            return False
        # feedback
        icon = "✅ درست!" if res["is_correct"] else f"❌ غلط - جواب درست: {res['correct_index']+1}) {res['correct_text']}"
        msg = f"{icon}\n📖 {res['explanation']}\n\nامتیاز: {res['score']}/{res['total']}"
        if res["finished"]:
            # save to DB
            try:
                from .models import now_iso
                pct = res["score"]*100//res["total"] if res["total"] else 0
                self.store.db.execute(
                    "INSERT INTO quiz_results (chat_id,domain_id,score,total,pct,ts) VALUES (?,?,?,?,?,?)",
                    (str(chat_id), res["domain_id"], res["score"], res["total"], pct, now_iso()))
                self.store.db.commit()
            except Exception:
                pass
            msg += "\n\n" + quiz_manager.format_result(chat_id)
            # clear session after final? keep for stats but remove to allow new
            # we keep but will be overwritten on next /azmoon
            del quiz_manager.sessions[chat_id]
        else:
            # next question
            next_q = quiz_manager.current_question(chat_id)
            if next_q:
                msg += "\n\n---\n\n" + quiz_manager.format_question(next_q)
        self.send(chat_id, msg[:3900])
        return True

    # ---------------- the product ----------------
    def handle_cv(self, chat_id: int, text: str) -> None:
        token = self.current_token(chat_id)
        if not token:
            self.send(chat_id, NOT_YET)
            return
        cid = f"tg-{chat_id}"
        cand = candidate_from_cv(text, cid=cid, pseudonym=f"TG-{str(chat_id)[-4:]}",
                                 consent_token=token, contact=text and None)
        self.store.upsert_candidate(cand)
        jobs = self.store.jobs()
        if not jobs:
            self.send(chat_id, "هنوز آگهی‌ای این‌جا نیست؛ روز بعد سر بزن.")
            return
        matcher = Matcher(jobs)
        matches = matcher.rank_jobs(cand, k=self.top_k)
        if not matches:
            nearby = matcher.blocked_by_logistics(cand)
            if nearby:
                titles = "، ".join(j.title for j, _ in nearby[:3])
                self.send(chat_id, RELOCATE_HINT.format(n=len(nearby)) + f"\n\nمثال‌ها: {titles}")
            else:
                self.send(chat_id, NO_MATCH)
            return
        lines = [f"برای تو {len(matches)} آگهی پیدا کردم:\n"]
        for i, m in enumerate(matches, 1):
            gap = " · باید حل شود: " + ", ".join(g.item for g in m.gaps[:2]) if m.gaps else ""
            lines.append(f"{i}) {m.title} — {m.company or 'کارفرما'} ({m.city or 'TR'}) "
                         f"امتیاز {m.score:.0f}{gap}\n   {m.url}")
        lines.append("\n" + "/shoghle بعدی ۵ تا · /hayir حذف داده‌ها · /danesh برای حقوق")
        self.send(chat_id, "\n".join(lines)[:3900])

    def handle_group_events(self, msg: dict, chat_id: int) -> bool:
        """Handle group events: new members, left, etc. Return True if handled."""
        # New members
        new_members = msg.get("new_chat_members") or []
        if new_members:
            for member in new_members:
                if member.get("is_bot"):
                    # Bot added to group
                    if member.get("id") == 8949733969:  # joblink_AI_bot
                        self.send(chat_id, "🤖 سلام! من JobLink ربات هستم — به گروه اضافه شدم!\n\n"
                                  "دستورات:\n"
                                  "/danesh d01 — قوانین اجازه کار\n"
                                  "/azmoon d01 — آزمون\n"
                                  "/shoghle — 5 آگهی جدید (در PV)\n\n"
                                  "برای تنظیمات: BotFather → Group Privacy → Turn off\n"
                                  "کانال: @joblink_tr_ir (یا لینک دعوت شما)\n"
                                  "دیتاست: hf.co/datasets/sosa123454321/joblink-knowledge-fa-tr")
                else:
                    # Human joined
                    name = member.get("first_name") or "دوست"
                    try:
                        from .channel_poster import ChannelPoster
                        poster = ChannelPoster(bot_token=None, store=self.store)
                        # Use api directly
                        poster.token = self.api.__closure__[0].cell_contents if hasattr(self.api, '__closure__') and self.api.__closure__ else None
                    except Exception:
                        pass
                    self.send(chat_id, f"سلام {name} به گروه JobLink خوش آمدی! 🤝\n\n"
                              "رزومه‌ات را در PV ربات @joblink_AI_bot بفرست (نه گروه — امنیت)\n"
                              "/danesh — پایگاه دانش 12 حوزه\n"
                              "/azmoon — آزمون\n"
                              "📢 کانال: @joblink_tr_ir\n"
                              "قوانین: احترام، بدون اسپم، بدون شماره در گروه")
            return True
        return False

    def handle_channel_post(self, chat_id: int, args: str) -> None:
        """OT command: /post [city] [skill] — post jobs to channel/group"""
        # Only admins can post
        if chat_id not in self.admins and self.admins:
            self.send(chat_id, "❌ فقط ادمین‌ها می‌توانند پست کنند — برای OT")
            return
        parts = args.split()
        city = parts[0] if len(parts)>=1 else None
        skill = parts[1] if len(parts)>=2 else None
        try:
            from .channel_poster import ChannelPoster, get_jobs_for_posting, format_job_for_channel
            jobs = get_jobs_for_posting(self.store, limit=5, city=city, skill=skill)
            if not jobs:
                self.send(chat_id, "آگهی‌ای پیدا نشد")
                return
            for job in jobs:
                text = format_job_for_channel(job, lang="fa")
                self.send(chat_id, text)
        except Exception as e:
            self.send(chat_id, f"خطا در پست: {e}")

    def handle_telegram_live(self, chat_id: int, args: str = "") -> None:
        """Show 20 live posts from 10 channels with buttons + AI chat"""
        try:
            import json, os, re
            from pathlib import Path
            # find file
            paths = [
                Path(__file__).parent.parent / "data" / "telegram_posts.json",
                Path(__file__).parent.parent / "spaces" / "telegram_posts.json",
                Path(__file__).parent.parent / "spaces" / "knowledge" / "telegram_posts.json",
            ]
            data = []
            for p in paths:
                if p.exists():
                    data = json.loads(p.read_text(encoding="utf-8"))
                    break
            if not data:
                self.send(chat_id, "هنوز پست زنده‌ای نیست — python -m joblink.telegram_monitor اجرا کن")
                return
            # filter by args if given
            if args:
                q = args.lower()
                data = [d for d in data if q in d.get("text","").lower() or q in d.get("channel_username","").lower() or q in d.get("category","").lower()]
            # send first 5 as separate messages with buttons to avoid flood, rest as summary
            count = 0
            for post in data[:5]:
                txt = post.get("text","")[:400]
                txt_masked = re.sub(r"(\+?90|0)?\s?5\d{2}\s?\d{3}\s?\d{2}\s?\d{2}", "05XX XXX XX XX", txt)
                msg = f"📡 {post.get('channel_title_fa')} — @{post.get('channel_username')}\n\n{txt_masked}\n\n📅 {post.get('date','')[:10]} — 👁 {post.get('views','')} — {post.get('category','')}\n⚠️ {post.get('commission','')}"
                kb = [
                    [{"text": "📄 پست اصلی", "url": post.get("link","https://t.me/karyabi06666")}, {"text": "📚 قوانین", "callback_data": "danesh_d01"}],
                    [{"text": "💬 بحث گروه", "url": "https://t.me/+YmyYph5XV-NlN2I8"}, {"text": "📢 کانال", "url": "https://t.me/+WALqOptGwnwyNmU0"}],
                    [{"text": f"🔗 @{post.get('channel_username')}", "url": f"https://t.me/{post.get('channel_username')}"}, {"text": "🤖 ربات", "url": "https://t.me/joblink_AI_bot"}],
                ]
                self.send_with_buttons(chat_id, msg[:3500], kb)
                count += 1
            # summary of rest
            if len(data) > 5:
                lines = [f"📋 {len(data)} پست زنده از 10 کانال — 5 تا بالا نمایش داده شد — بقیه:\n"]
                for p in data[5:15]:
                    lines.append(f"• {p.get('channel_title_fa')} @{p.get('channel_username')} — {p.get('text','')[:60]}... — {p.get('link')}")
                lines.append("\nبرای فیلتر: /telegram_live نظافت یا /telegram_live Şişli")
                lines.append("برای چت AI: بنویس 'کار بسته‌بندی با جای خواب می‌خوام' → RAG + این پست‌ها")
                self.send(chat_id, "\n".join(lines)[:3800])
            # stats
            try:
                from .telegram_channels import CHANNELS_10
                best = len([c for c in CHANNELS_10 if c.is_best])
                self.send_with_buttons(chat_id, f"✅ {count} پست از {len(data)} نمایش داده شد — 10 کانال (بهترین {best}) — هر 3 ساعت آپدیت — ساعت کاری: 08:00-18:00 معمول، 11-21 و 16-02 شیفت، حقوق 25K-70K", [[{"text": "🔗 10 کانال لیست", "callback_data": "tg_channels"}, {"text": "📡 Space 12 تب", "url": "https://huggingface.co/spaces/sosa123454321/joblink"}]])
            except Exception:
                pass
        except Exception as e:
            self.send(chat_id, f"خطا در telegram_live: {e}")

    def handle_tg_channels(self, chat_id: int) -> None:
        try:
            from .telegram_channels import CHANNELS_10
            lines = ["📡 10 کانال کاریابی تلگرام — هر 3 ساعت 20 پست:\n"]
            for c in CHANNELS_10:
                lines.append(f"{c.id} @{c.username} — {c.title_fa} — {c.members} عضو — {c.commission} — {'✅ بهترین' if c.is_best else ''}\n  {c.category}\n  تماس: {c.contact_public} — {c.url}\n")
            lines.append("\nبرای زنده: /telegram_live — برای فیلتر: /telegram_live نظافت")
            self.send(chat_id, "\n".join(lines)[:3800])
        except Exception as e:
            self.send(chat_id, f"خطا: {e}")

    def handle_digest(self, chat_id: int) -> None:
        """OT command: /digest — daily digest"""
        try:
            from .channel_poster import ChannelPoster
            # Build digest manually
            jobs = self.store.jobs(limit=5)
            if not jobs:
                self.send(chat_id, "آگهی‌ای نیست")
                return
            lines = [f"📅 **آگهی‌های امروز — {len(jobs)} فرصت**\n"]
            for i, job in enumerate(jobs[:5], 1):
                salary = f"{job.salary_min:,.0f} TL" if job.salary_min else "توافقی"
                lines.append(f"{i}) {job.title} — {job.company or '—'} ({job.city or 'TR'}) — {salary}\n   {job.url}\n")
            try:
                from .knowledge.domains import DOMAINS
                import random
                tip = random.choice([d for d in DOMAINS if d.risk_level=="high"])
                lines.append(f"\n📚 نکته امروز: {tip.title_fa}\n{tip.description_fa[:200]}...\n/danesh {tip.id}")
            except Exception:
                pass
            lines.append("\n🤖 @joblink_AI_bot — /shoghle برای شخصی")
            self.send(chat_id, "\n".join(lines)[:3900])
        except Exception as e:
            self.send(chat_id, f"خطا: {e}")

    def handle_callback(self, callback: dict) -> None:
        """Handle inline keyboard callbacks"""
        chat_id = (callback.get("message") or {}).get("chat", {}).get("id") or callback.get("from", {}).get("id")
        if not chat_id:
            return
        data = callback.get("data") or ""
        # Answer callback to remove loading
        try:
            self.api("answerCallbackQuery", callback_query_id=callback.get("id"))
        except Exception:
            pass

        if data == "start":
            self.send_with_buttons(chat_id, CONSENT_TEXT + "\n\n" + HELP, self.main_keyboard())
        elif data == "language":
            self.send_with_buttons(chat_id, "🌐 زبان را انتخاب کنید / Dil seçin / Choose a language / اختر اللغة:", self.language_keyboard())
        elif data.startswith("lang_"):
            messages = {
                "lang_fa": "🇮🇷 زبان فارسی انتخاب شد. برای بازگشت از /start استفاده کنید.",
                "lang_tr": "🇹🇷 Türkçe seçildi. Ana menü için /start yazın.",
                "lang_en": "🇬🇧 English selected. Use /start for the main menu.",
                "lang_ar": "🇸🇦 تم اختيار العربية. أرسل /start للقائمة الرئيسية.",
            }
            self.send_with_buttons(chat_id, messages.get(data, "Language selected."), self.main_keyboard())
        elif data == "danesh":
            self.send_with_buttons(chat_id, "📚 پایگاه دانش — 12 حوزه — یکی را انتخاب کن:", self.danesh_keyboard())
        elif data.startswith("danesh_"):
            did = data[7:]
            self.handle_danesh(chat_id, did)
        elif data == "azmoon":
            self.send_with_buttons(chat_id, "📝 آزمون — 12 حوزه — انتخاب کن:", self.azmoon_keyboard())
        elif data.startswith("azmoon_"):
            did = data[7:]
            if did == "random":
                self.handle_azmoon(chat_id, "")
            else:
                self.handle_azmoon(chat_id, did)
        elif data.startswith("quiz_"):
            # Quiz answer via button
            try:
                choice = int(data[5:])
                self.handle_quiz_answer_via_button(chat_id, choice)
            except Exception:
                pass
        elif data == "shoghle":
            self.rerank(chat_id)
        elif data == "tg_channels":
            self.handle_tg_channels(chat_id)
        elif data == "telegram_live":
            self.handle_telegram_live(chat_id)
        elif data == "links":
            self.send_with_buttons(chat_id, "🔗 لینک‌ها:\n"
                      "🤖 ربات: @joblink_AI_bot\n"
                      "📢 کانال: https://t.me/+WALqOptGwnwyNmU0\n"
                      "👥 گروه: https://t.me/+YmyYph5XV-NlN2I8\n"
                      "📚 دیتاست: hf.co/datasets/sosa123454321/joblink-knowledge-fa-tr\n"
                      "🚀 Space: hf.co/spaces/sosa123454321/joblink", self.main_keyboard())
        else:
            self.send(chat_id, f"دستور {data} — /help")

    def handle_quiz_answer_via_button(self, chat_id: int, choice_idx: int) -> None:
        if not HAS_KNOWLEDGE or not quiz_manager:
            return
        sess = quiz_manager.sessions.get(chat_id)
        if not sess:
            return
        res = quiz_manager.answer(chat_id, choice_idx)
        if res.get("error"):
            return
        icon = "✅ درست!" if res["is_correct"] else f"❌ غلط - جواب درست: {res['correct_index']+1}) {res['correct_text']}"
        msg = f"{icon}\n📖 {res['explanation']}\n\nامتیاز: {res['score']}/{res['total']}"
        if res["finished"]:
            try:
                from .models import now_iso
                pct = res["score"]*100//res["total"] if res["total"] else 0
                self.store.db.execute(
                    "INSERT INTO quiz_results (chat_id,domain_id,score,total,pct,ts) VALUES (?,?,?,?,?,?)",
                    (str(chat_id), res["domain_id"], res["score"], res["total"], pct, now_iso()))
                self.store.db.commit()
            except Exception:
                pass
            msg += "\n\n" + quiz_manager.format_result(chat_id)
            del quiz_manager.sessions[chat_id]
            self.send_with_buttons(chat_id, msg[:3900], self.main_keyboard())
        else:
            next_q = quiz_manager.current_question(chat_id)
            if next_q:
                msg += "\n\n---\n\n" + quiz_manager.format_question(next_q)
                self.send_with_buttons(chat_id, msg[:3900], [[{"text": "1", "callback_data": "quiz_0"}, {"text": "2", "callback_data": "quiz_1"}, {"text": "3", "callback_data": "quiz_2"}, {"text": "4", "callback_data": "quiz_3"}]])

    def handle_update(self, up: dict) -> None:
        # Callback query (inline buttons)
        if "callback_query" in up:
            self.handle_callback(up["callback_query"])
            # Update offset
            self.offset = max(self.offset, int(up.get("update_id", 0)))
            return

        msg = up.get("message") or {}
        chat_id = (msg.get("chat") or {}).get("id")
        if chat_id is None:
            return
        # Group events first
        if self.handle_group_events(msg, chat_id):
            return
        text = (msg.get("text") or "").strip()
        low = text.lower()
        # Reply-keyboard labels map to actions; users do not need to type commands.
        button_commands = {
            "💼 شغل‌ها": "/shoghle", "📡 آگهی‌های زنده": "/telegram_live",
            "📚 دانش": "/danesh", "📝 آزمون": "/azmoon", "🌐 زبان": "__language__",
            "🔗 لینک‌ها": "__links__", "📢 کانال": "__channel__", "👥 گروه": "__group__",
            "❌ حذف اطلاعات": "/hayir",
        }
        mapped = button_commands.get(text)
        if mapped == "__language__":
            self.send_with_buttons(chat_id, "🌐 زبان را انتخاب کنید / Dil seçin / Choose a language / اختر اللغة:", self.language_keyboard())
            return
        if mapped == "__links__":
            self.send_with_buttons(chat_id, "🔗 لینک‌ها:\n🤖 https://t.me/joblink_AI_bot\n📢 https://t.me/+WALqOptGwnwyNmU0\n👥 https://t.me/+YmyYph5XV-NlN2I8\n🚀 https://huggingface.co/spaces/sosa123454321/joblink", self.main_keyboard())
            return
        if mapped == "__channel__":
            self.send_with_menu(chat_id, "📢 کانال JobLink:\nhttps://t.me/+WALqOptGwnwyNmU0")
            return
        if mapped == "__group__":
            self.send_with_menu(chat_id, "👥 گروه گفت‌وگو:\nhttps://t.me/+YmyYph5XV-NlN2I8")
            return
        if mapped:
            low = mapped
        if low.startswith("/start"):
            self.send_with_menu(chat_id, CONSENT_TEXT + "\n\n" + HELP + "\n\n🤖 ربات: @joblink_AI_bot\n📢 کانال: https://t.me/+WALqOptGwnwyNmU0\n👥 گروه: https://t.me/+YmyYph5XV-NlN2I8\n\nاز دکمه‌های پایین استفاده کنید؛ برای مچینگ، ارسال متن رزومه اختیاری است.")
        elif low.startswith(("/katil", "/join", "/optin")):
            self.optin(chat_id, up.get("update_id", 0))
        elif low.startswith(("/hayir", "/optout", "/del")):
            self.optout(chat_id, up.get("update_id", 0))
        elif low.startswith(("/haziri", "/relocate")):
            self.set_prefs(chat_id, relocate=True)
        elif low.startswith(("/dorkari", "/remote")):
            self.set_prefs(chat_id, relocate=False, remote=True)
        elif low.startswith(("/shoghle", "/jobs", "/profil")):
            self.rerank(chat_id)
        elif low.startswith("/help"):
            self.send(chat_id, HELP + "\n\n📚 /danesh — 12 حوزه\n📝 /azmoon — آزمون\n📅 /digest — خلاصه روزانه (OT)\n📤 /post [شهر] [مهارت] — پست به کانال (OT)")
        elif low.startswith("/danesh"):
            args = text[7:].strip()
            self.handle_danesh(chat_id, args)
        elif low.startswith("/azmoon") or low.startswith("/azmun") or low.startswith("/quiz"):
            parts = text.split(maxsplit=1)
            args = parts[1] if len(parts)>1 else ""
            self.handle_azmoon(chat_id, args)
        elif low.startswith("/telegram_live") or low.startswith("/live") or low.startswith("/tg_live") or low.startswith("/tg_channels") or low.startswith("/channels"):
            if "channel" in low:
                self.handle_tg_channels(chat_id)
            else:
                # extract args after command
                parts = text.split(maxsplit=1)
                args = parts[1] if len(parts)>1 else ""
                self.handle_telegram_live(chat_id, args)
        elif low.startswith("/post10"):
            # Post 10 fields fa+tr
            try:
                from .channel_poster import ChannelPoster
                poster = ChannelPoster(store=self.store)
                # Try to get token from api closure if possible
                # For tests, use sent
                count = 0
                # Use same logic as channel_poster.post_10_fields but via send
                from .channel_poster import get_jobs_for_posting, format_job_for_channel
                fields = [
                    ("temizlik", "نظافت", "Temizlik"),
                    ("paketleme", "بسته‌بندی", "Paketleme"),
                    ("güvenlik", "امنیت", "Güvenlik"),
                    ("yazılım", "برنامه‌نویسی", "Yazılım"),
                    ("muhasebe", "حسابداری", "Muhasebe"),
                    ("satış", "فروش", "Satış"),
                    ("depo", "انباردار", "Depo"),
                    ("şoför", "راننده", "Şoför"),
                    ("aşçı", "آشپز", "Aşçı"),
                    ("danesh", "کیس Marfa", "Vaka"),
                ]
                for keyword, fa_name, tr_name in fields:
                    jobs = get_jobs_for_posting(self.store, limit=1, skill=keyword)
                    if not jobs:
                        jobs = get_jobs_for_posting(self.store, limit=1)
                    if jobs:
                        job = jobs[0]
                        combined = f"**{fa_name} / {tr_name}** — دیروز\n\n{format_job_for_channel(job, lang='fa')}"
                        # With buttons
                        kb = [
                            [{"text": "📄 لینک اصلی", "url": job.url}, {"text": "📚 قوانین", "callback_data": "danesh_d01"}],
                            [{"text": "💬 بحث در گروه", "url": "https://t.me/+YmyYph5XV-NlN2I8"}, {"text": "📢 کانال", "url": "https://t.me/+WALqOptGwnwyNmU0"}]
                        ]
                        self.send_with_buttons(chat_id, combined[:3800], kb)
                        count += 1
                self.send(chat_id, f"✅ {count} پست 10 زمینه دیروز ارسال شد — فارسی+ترکی — با دکمه پنجره‌ای — برای کانال و گروه آماده گفتگو")
            except Exception as e:
                self.send(chat_id, f"خطا در post10: {e}")
        elif low.startswith("/post"):
            args = text[5:].strip()
            self.handle_channel_post(chat_id, args)
        elif low.startswith("/digest"):
            self.handle_digest(chat_id)
        elif low.startswith("/links"):
            self.send_with_buttons(chat_id, "🔗 لینک‌ها:\n"
                      "🤖 ربات: @joblink_AI_bot — https://t.me/joblink_AI_bot\n"
                      "📢 کانال: @joblink_tr_ir — https://t.me/+WALqOptGwnwyNmU0\n"
                      "👥 گروه: @joblink_group — https://t.me/+YmyYph5XV-NlN2I8\n"
                      "📚 دیتاست: https://huggingface.co/datasets/sosa123454321/joblink-knowledge-fa-tr\n"
                      "🚀 Space: https://huggingface.co/spaces/sosa123454321/joblink\n"
                      "💻 کد: https://github.com/sosa123454321/joblink\n"
                      "🤖 Qwen3-0.6B: https://huggingface.co/Qwen/Qwen3-Embedding-0.6B\n"
                      "🤖 bge-m3: https://huggingface.co/BAAI/bge-m3", self.main_keyboard())
        elif self.handle_quiz_answer(chat_id, text):
            pass
        elif len(text) >= 40:
            self.handle_cv(chat_id, text)
        else:
            self.send(chat_id, HELP)

    # ---------------- loops ----------------
    def poll_once(self, *, timeout: int = 0) -> int:
        data = self.api("getUpdates", offset=self.offset + 1, timeout=timeout,
                        allowed_updates=["message"])
        ups = data.get("result") or []
        for up in ups:
            try:
                self.handle_update(up)
            except Exception as exc:  # noqa: BLE001 - never die on one bad message
                self.sent.append((0, f"error: {type(exc).__name__}: {exc}"))
            self.offset = max(self.offset, int(up.get("update_id", 0)))
        return len(ups)

    def run(self, *, poll: int = 25) -> None:
        while True:
            try:
                self.poll_once(timeout=poll)
            except Exception:  # noqa: BLE001
                time.sleep(3)

    def broadcast(self, cid_filter: Callable[[str], bool] | None = None, k: int = 3) -> int:
        """Nightly digest: '۳ شغل امروز' to every consented candidate. Return count sent."""
        jobs = self.store.jobs()
        if not jobs:
            return 0
        m = Matcher(jobs)
        sent = 0
        for c in self.store.candidates():
            if cid_filter and not cid_filter(c.cid):
                continue
            chat = self.store.db.execute(
                "SELECT chat_id FROM consent WHERE cid=? AND action='granted' ORDER BY id DESC",
                (c.cid,)).fetchone()
            if not chat:
                continue
            ms = m.rank_jobs(c, k=k)
            if not ms:
                continue
            body = "\n".join(f"• {x.title} ({x.city or 'TR'}) {x.score:.0f}\n  {x.url}" for x in ms)
            self.send(int(chat["chat_id"]), f"سلام {c.pseudonym}، امروز این‌ها برای توست:\n{body}")
            sent += 1
        return sent


# Consent + candidate-chat linkage lives in its own table so the deletion path is trivial.
CONSENT_DDL = """
CREATE TABLE IF NOT EXISTS consent (
  id INTEGER PRIMARY KEY AUTOINCREMENT, cid TEXT, chat_id TEXT, action TEXT,
  token TEXT, ts TEXT, update_id INTEGER
);
CREATE INDEX IF NOT EXISTS consent_chat ON consent(chat_id, action);
CREATE TABLE IF NOT EXISTS quiz_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  chat_id TEXT, domain_id TEXT, score INTEGER, total INTEGER, pct INTEGER, ts TEXT
);
"""


def ensure_schema(store: Store) -> None:
    store.db.executescript(CONSENT_DDL)
    store.db.executescript(QUIZ_DDL)
    store.db.commit()
