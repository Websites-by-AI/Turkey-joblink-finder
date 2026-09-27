"""Telegram Monitor - fetch t.me/s/ every 3h, ~20 new posts, post to channel/group/site/bot"""
from __future__ import annotations
import json, os, re, time, hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict

import requests
from bs4 import BeautifulSoup

from .telegram_channels import CHANNELS_10, TGChannel

DATA_FILE = Path(__file__).parent.parent / "data" / "telegram_posts.json"
SPACE_FILE = Path(__file__).parent.parent / "spaces" / "knowledge" / "telegram_posts.json"
SPACE_FILE2 = Path(__file__).parent.parent / "spaces" / "telegram_posts.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JobLinkBot/1.0; +https://huggingface.co/spaces/sosa123454321/joblink)"
}

def fetch_channel_posts(channel: TGChannel, limit: int = 20) -> List[Dict]:
    """Fetch up to limit posts from t.me/s/username"""
    try:
        resp = requests.get(channel.tme_url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"Fetch {channel.username} failed {resp.status_code}")
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        messages = soup.find_all("div", class_="tgme_widget_message_wrap")
        posts = []
        for wrap in messages[-limit:]:  # last N
            try:
                # text
                text_div = wrap.find("div", class_="tgme_widget_message_text")
                text = text_div.get_text("\n", strip=True) if text_div else ""
                if not text:
                    continue
                # date
                time_tag = wrap.find("time")
                date_str = time_tag.get("datetime") if time_tag else ""
                # views
                views_span = wrap.find("span", class_="tgme_widget_message_views")
                views = views_span.get_text(strip=True) if views_span else ""
                # link
                link_a = wrap.find("a", class_="tgme_widget_message_date")
                link = link_a.get("href") if link_a else f"https://t.me/{channel.username}"
                # id
                post_id = hashlib.md5(f"{channel.username}:{text[:100]}".encode()).hexdigest()[:12]
                # filter job-related keywords
                job_keywords = ["کار", "شغل", "نظافت", "بسته", "انبار", "گارسون", "باریستا", "تمیز", "iş", "temizlik", "paket", "depo", "garson", "maaş", "حقوق", "لیر"]
                is_job = any(k in text.lower() for k in job_keywords) or len(text) > 30
                if not is_job:
                    continue
                posts.append({
                    "id": post_id,
                    "channel_id": channel.id,
                    "channel_username": channel.username,
                    "channel_title_fa": channel.title_fa,
                    "channel_url": channel.url,
                    "text": text[:1000],
                    "text_full": text,
                    "date": date_str or datetime.utcnow().isoformat(),
                    "views": views,
                    "link": link,
                    "scraped_at": datetime.utcnow().isoformat(),
                    "category": channel.category,
                    "commission": channel.commission,
                    "contact_public": channel.contact_public,
                    "is_best": channel.is_best,
                })
            except Exception as e:
                print(f"Parse error {channel.username}: {e}")
                continue
        return posts
    except Exception as e:
        print(f"Exception fetch {channel.username}: {e}")
        return []

def fetch_all(limit_per_channel: int = 5, total_limit: int = 20) -> List[Dict]:
    """Fetch from 10 channels, return up to total_limit newest"""
    all_posts: List[Dict] = []
    for ch in CHANNELS_10:
        if ch.id == "ch10":  # skip own channel to avoid loop
            continue
        posts = fetch_channel_posts(ch, limit=limit_per_channel)
        all_posts.extend(posts)
        time.sleep(0.5)  # be nice
    # sort by date desc, deduplicate by id
    seen = set()
    uniq = []
    for p in sorted(all_posts, key=lambda x: x["date"], reverse=True):
        if p["id"] not in seen:
            seen.add(p["id"])
            uniq.append(p)
    return uniq[:total_limit]

def load_existing() -> List[Dict]:
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def save_posts(posts: List[Dict]):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")
    # copy to spaces
    for dest in [SPACE_FILE, SPACE_FILE2]:
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            print(f"Copy to {dest} failed {e}")

def merge_and_save(new_posts: List[Dict], keep: int = 100) -> List[Dict]:
    existing = load_existing()
    existing_ids = {p["id"] for p in existing}
    merged = new_posts + [p for p in existing if p["id"] not in existing_ids]
    # keep newest 100
    merged = sorted(merged, key=lambda x: x.get("date",""), reverse=True)[:keep]
    save_posts(merged)
    return merged

def format_for_telegram(post: Dict) -> tuple[str, List]:
    """Return text + inline keyboard spec for channel_poster"""
    # Clean text, remove phone numbers (KVKK) - mask numbers
    text = post["text_full"]
    # mask phone numbers: 05xx xxx xx xx, +90, 0090
    text_masked = re.sub(r"(\+?90|0)?\s?5\d{2}\s?\d{3}\s?\d{2}\s?\d{2}", "05XX XXX XX XX", text)
    text_masked = re.sub(r"0090\d{10}", "0090XXXXXXXXXX", text_masked)
    # truncate
    if len(text_masked) > 800:
        text_masked = text_masked[:800] + "..."

    fa_title = post["channel_title_fa"]
    username = post["channel_username"]
    link = post["link"]
    contact = post["contact_public"]

    msg = f"""📢 {fa_title} — @{username}

{text_masked}

📅 {post['date'][:10]} — 👁 {post['views']} — {post['category']}
🔗 منبع: {link}
👤 تماس عمومی: {contact} (بدون شماره خصوصی - KVKK)
⚠️ نیاز به اجازه کار - توریستی ممنوع دیپورت

#JobLink #کاریابی_ترکیه #نظافت #بسته_بندی
"""

    # Inline buttons spec (for python-telegram-bot)
    keyboard = [
        [{"text": "📄 پست اصلی", "url": link}],
        [{"text": "📚 قوانین", "url": "https://t.me/+WALqOptGwnwyNmU0"}, {"text": "💬 بحث گروه", "url": "https://t.me/+YmyYph5XV-NlN2I8"}],
        [{"text": "🤖 ربات JobLink", "url": "https://t.me/joblink_AI_bot"}, {"text": "🚀 Space", "url": "https://huggingface.co/spaces/sosa123454321/joblink"}],
        [{"text": f"🔗 {fa_title}", "url": f"https://t.me/{username}"}],
    ]
    return msg, keyboard

def get_stats():
    posts = load_existing()
    by_channel = {}
    for p in posts:
        by_channel[p["channel_username"]] = by_channel.get(p["channel_username"], 0) + 1
    return {
        "total": len(posts),
        "by_channel": by_channel,
        "last_scraped": posts[0]["scraped_at"] if posts else None,
        "best_count": len([p for p in posts if p.get("is_best")]),
    }

if __name__ == "__main__":
    print("Fetching 10 channels, 5 each, total 20...")
    new_posts = fetch_all(limit_per_channel=5, total_limit=20)
    print(f"Fetched {len(new_posts)} new posts")
    merged = merge_and_save(new_posts, keep=100)
    print(f"Merged total {len(merged)} saved to {DATA_FILE}")
    print(get_stats())
