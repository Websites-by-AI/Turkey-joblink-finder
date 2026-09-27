"""Channel poster - posts jobs to Telegram channels/groups with site style"""

from __future__ import annotations
import os, json, random
from typing import List, Optional
from .models import Job
from .store import Store

# Site style templates - based on eleman.net, kariyer.net style
SITE_STYLE_TEMPLATES = {
    "eleman.net": "🔧 {title} — {company} | {city} | {salary} TL | {source}",
    "kariyer.net": "💼 {title} @ {company} - {city} - {skills}",
    "default": "🤝 {title} — {company} ({city}) — {salary} TL — {url}"
}

def format_job_for_channel(job: Job, style="default", lang="fa") -> str:
    """Format job in site style + Persian translation"""
    salary = f"{job.salary_min:,.0f}" if job.salary_min else "توافقی"
    skills = ", ".join(job.skills[:5]) if job.skills else "—"
    
    if lang == "fa":
        # Persian style with Turkish original
        text = f"""🤝 **{job.title}**

🏢 کارفرما: {job.company or '—'}
📍 شهر: {job.city or 'TR'} {('(ریموت)' if job.remote else '')}
💰 حقوق: {salary} TL
🛠️ مهارت‌ها: {skills}
🔗 منبع: {job.source}

📄 توضیح:
{job.description[:300]}...

🔗 لینک اصلی:
{job.url}

⚠️ هشدار حقوقی:
اگر حضوری است، بدون Çalışma izni (اجازه کار) شروع نکن — /danesh d01

#کاریابی #ترکیه #{(job.city or 'TR').replace(' ', '')} #{job.source}
"""
    else:
        text = f"{job.title} - {job.company} - {job.city} - {salary} TL\n{job.url}"
    
    return text[:3800]

def get_jobs_for_posting(store: Store, limit=5, city=None, skill=None) -> List[Job]:
    """Get latest jobs for channel posting"""
    jobs = store.jobs(limit=200)
    if city:
        jobs = [j for j in jobs if city.lower() in (j.city or "").lower()]
    if skill:
        jobs = [j for j in jobs if skill.lower() in " ".join(j.skills).lower() or skill.lower() in (j.title or "").lower()]
    # Sort by posted_at or salary
    jobs = sorted(jobs, key=lambda j: j.posted_at or "", reverse=True)
    return jobs[:limit]

class ChannelPoster:
    def __init__(self, bot_token: Optional[str]=None, store: Optional[Store]=None):
        self.token = bot_token or os.environ.get("BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN")
        self.store = store
        self.sent = []

    def _api(self, method: str, **kw):
        import httpx
        if not self.token:
            raise ValueError("BOT_TOKEN not set")
        with httpx.Client(timeout=30.0) as c:
            r = c.post(f"https://api.telegram.org/bot{self.token}/{method}", json=kw)
            return r.json()

    def bot_send_message(self, chat_id: str, text: str, reply_markup: dict | None = None, parse_mode: str = "Markdown") -> dict:
        kw = {"chat_id": chat_id, "text": text[:4000], "parse_mode": parse_mode}
        if reply_markup:
            kw["reply_markup"] = reply_markup
        return self._api("sendMessage", **kw)

    def post_job(self, job: Job, chat_id: str, style="default", lang="fa", with_buttons=True) -> dict:
        text = format_job_for_channel(job, style=style, lang=lang)
        if with_buttons:
            # Inline buttons: link + danesh + group + channel
            reply_markup = {
                "inline_keyboard": [
                    [{"text": "📄 لینک اصلی", "url": job.url}, {"text": "📚 قوانین", "url": f"https://t.me/joblink_AI_bot?start=danesh_d01"}],
                    [{"text": "💬 بحث در گروه", "url": "https://t.me/+YmyYph5XV-NlN2I8"}, {"text": "📢 کانال", "url": "https://t.me/+WALqOptGwnwyNmU0"}],
                    [{"text": "🤖 ربات", "url": "https://t.me/joblink_AI_bot"}],
                    [{"text": "🇮🇷 فارسی", "url": "https://t.me/joblink_AI_bot?start=lang_fa"}, {"text": "🇹🇷 Türkçe", "url": "https://t.me/joblink_AI_bot?start=lang_tr"}, {"text": "🇬🇧 English", "url": "https://t.me/joblink_AI_bot?start=lang_en"}, {"text": "🇸🇦 العربية", "url": "https://t.me/joblink_AI_bot?start=lang_ar"}]
                ]
            }
            res = self._api("sendMessage", chat_id=chat_id, text=text, parse_mode="Markdown", reply_markup=reply_markup)
        else:
            res = self._api("sendMessage", chat_id=chat_id, text=text, parse_mode="Markdown")
        self.sent.append((chat_id, job.title))
        return res

    def post_10_fields(self, chat_id: str, lang="both") -> int:
        """Post 10 job fields from yesterday — fa + tr — with buttons"""
        if not self.store:
            from .config import SETTINGS
            self.store = Store(SETTINGS.db_path)
        # 10 fields mapping
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
        count = 0
        for keyword, fa_name, tr_name in fields:
            jobs = get_jobs_for_posting(self.store, limit=1, skill=keyword)
            if not jobs:
                # Try city filter
                jobs = get_jobs_for_posting(self.store, limit=1)
            if jobs:
                job = jobs[0]
                if lang == "both":
                    # Post fa then tr? Or combined
                    text_fa = format_job_for_channel(job, lang="fa")
                    text_tr = format_job_for_channel(job, lang="tr") if hasattr(format_job_for_channel, '__code__') else ""
                    # Combined fa+tr
                    combined = f"{fa_name} / {tr_name}\n\n{format_job_for_channel(job, lang='fa')}\n\n--- TR ---\n{job.title} - {job.company} - {job.city}\n{job.url}"
                    reply_markup = {
                        "inline_keyboard": [
                            [{"text": "📄 لینک اصلی", "url": job.url}, {"text": "📚 قوانین", "callback_data": "danesh_d01"}],
                            [{"text": "💬 گروه", "url": "https://t.me/+YmyYph5XV-NlN2I8"}, {"text": "📢 کانال", "url": "https://t.me/+WALqOptGwnwyNmU0"}],
                        ]
                    }
                    try:
                        self._api("sendMessage", chat_id=chat_id, text=combined[:3800], parse_mode="Markdown", reply_markup=reply_markup)
                        count += 1
                    except Exception as e:
                        print(f"Failed {fa_name}: {e}")
                else:
                    self.post_job(job, chat_id=chat_id, lang=lang, with_buttons=True)
                    count += 1
        return count

    def post_jobs_batch(self, chat_id: str, limit=5, city=None, skill=None, lang="fa") -> int:
        if not self.store:
            from .config import SETTINGS
            self.store = Store(SETTINGS.db_path)
        jobs = get_jobs_for_posting(self.store, limit=limit, city=city, skill=skill)
        count = 0
        for job in jobs:
            try:
                self.post_job(job, chat_id=chat_id, lang=lang)
                count += 1
            except Exception as e:
                print(f"Failed to post {job.title}: {e}")
        return count

    def post_daily_digest(self, chat_id: str, lang="fa") -> dict:
        """Daily digest: 5 jobs + knowledge tip"""
        if not self.store:
            from .config import SETTINGS
            self.store = Store(SETTINGS.db_path)
        jobs = get_jobs_for_posting(self.store, limit=5)
        if not jobs:
            return {"ok": False, "error": "no jobs"}
        
        # Build digest
        lines = [f"📅 **آگهی‌های امروز — {len(jobs)} فرصت جدید**\n"]
        for i, job in enumerate(jobs, 1):
            salary = f"{job.salary_min:,.0f} TL" if job.salary_min else "توافقی"
            lines.append(f"{i}) {job.title} — {job.company or '—'} ({job.city or 'TR'}) — {salary}\n   {job.url}\n")
        
        # Add knowledge tip
        try:
            from .knowledge.domains import DOMAINS
            tip_domain = random.choice([d for d in DOMAINS if d.risk_level=="high"])
            lines.append(f"\n📚 **نکته حقوقی امروز:** {tip_domain.title_fa}\n{tip_domain.description_fa[:200]}...\nبرای بیشتر: /danesh {tip_domain.id} در ربات @joblink_AI_bot")
        except Exception:
            pass
        
        lines.append(f"\n🤖 ربات: @joblink_AI_bot — /shoghle برای پیشنهاد شخصی")
        text = "\n".join(lines)[:3900]
        return self._api("sendMessage", chat_id=chat_id, text=text, parse_mode="Markdown")

    def manage_group_welcome(self, chat_id: str, user_name: str) -> dict:
        """Welcome new member in group"""
        text = f"""سلام {user_name} به گروه JobLink خوش آمدی! 🤝

اینجا می‌تونی:
- رزومه‌ات را در PV ربات @joblink_AI_bot بفرستی (نه گروه — امنیت)
- درباره اجازه کار، KVKK، حقوق سوال بپرسی — /danesh
- آزمون بدی — /azmoon d01
- آگهی مشکوک گزارش کنی

📢 کانال: @joblink_tr_ir (یا لینک دعوت شما)
📚 دیتاست: hf.co/datasets/sosa123454321/joblink-knowledge-fa-tr

قوانین: احترام، بدون اسپم، بدون شماره در گروه
"""
        return self._api("sendMessage", chat_id=chat_id, text=text)

# CLI helper
if __name__=="__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--chat-id", required=True, help="Channel/group ID like @joblink_group or -1002089796813")
    p.add_argument("--limit", type=int, default=3)
    p.add_argument("--city")
    p.add_argument("--skill")
    p.add_argument("--digest", action="store_true")
    args = p.parse_args()
    poster = ChannelPoster()
    if args.digest:
        print(poster.post_daily_digest(args.chat_id))
    else:
        print(f"Posting {args.limit} jobs to {args.chat_id}")
        print(poster.post_jobs_batch(args.chat_id, limit=args.limit, city=args.city, skill=args.skill))
