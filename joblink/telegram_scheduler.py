"""Scheduler - every 3h fetch 20 new posts from 10 channels, post to your channel+group+site+bot"""
from __future__ import annotations
import time, os, json, sys
from datetime import datetime

# add parent
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from joblink.telegram_monitor import fetch_all, merge_and_save, get_stats, format_for_telegram
from joblink.channel_poster import ChannelPoster

# Config from env
# Never hard-code Telegram credentials. Set BOT_TOKEN or TELEGRAM_BOT_TOKEN at runtime.
BOT_TOKEN = os.environ.get("BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN") or ""
CHANNEL_ID = os.environ.get("CHANNEL_ID", "@joblink_tr_ir")  # or https://t.me/+WALqOptGwnwyNmU0 ID
GROUP_ID = os.environ.get("GROUP_ID", "@joblink_group")  # or -1002089796813

# For private invite links, need to use chat_id numeric if bot is admin, but public username works if bot admin
CHANNELS_TO_POST = [CHANNEL_ID, GROUP_ID]

def post_to_telegram(posts, poster: ChannelPoster):
    """Post each with inline buttons"""
    count = 0
    for post in posts[:20]:  # 20 max
        try:
            text, keyboard = format_for_telegram(post)
            # Build InlineKeyboardMarkup dict for Bot API
            # keyboard is list of rows, each row list of dicts with text/url
            # Convert to Telegram API format
            inline_keyboard = keyboard  # already correct format for our poster?
            # Our ChannelPoster expects text + reply_markup as dict
            # We'll call send directly
            for chat_id in CHANNELS_TO_POST:
                try:
                    poster.bot_send_message(chat_id, text, reply_markup={"inline_keyboard": inline_keyboard})
                    print(f"Posted {post['id']} to {chat_id}")
                    time.sleep(1.5)  # avoid flood
                except Exception as e:
                    print(f"Failed post {post['id']} to {chat_id}: {e}")
            count += 1
        except Exception as e:
            print(f"Format/post error {post.get('id')}: {e}")
    return count

def job_once():
    print(f"\n[{datetime.now().isoformat()}] Starting fetch job...")
    new_posts = fetch_all(limit_per_channel=5, total_limit=20)
    print(f"Fetched {len(new_posts)} new")
    merged = merge_and_save(new_posts, keep=200)
    print(f"Merged total {len(merged)} - stats {get_stats()}")
    # Post to Telegram if token available
    if BOT_TOKEN and BOT_TOKEN != "dummy":
        try:
            poster = ChannelPoster(bot_token=BOT_TOKEN)
            # Only post the NEW ones (not all merged)
            posted = post_to_telegram(new_posts, poster)
            print(f"Posted {posted} to {CHANNELS_TO_POST}")
        except Exception as e:
            print(f"Poster init/post failed: {e}")
    else:
        print("No BOT_TOKEN, skipping Telegram post")
    return new_posts

def run_forever(interval_hours: int = 3):
    print(f"Scheduler running every {interval_hours}h - channels: 10 - posts: ~20 each run")
    print(f"Channel: {CHANNEL_ID} Group: {GROUP_ID}")
    while True:
        try:
            job_once()
        except Exception as e:
            print(f"Job failed: {e}")
        print(f"Sleeping {interval_hours}h...")
        time.sleep(interval_hours * 3600)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--hours", type=int, default=3, help="Interval hours")
    args = parser.parse_args()
    if args.once:
        job_once()
    else:
        run_forever(interval_hours=args.hours)
