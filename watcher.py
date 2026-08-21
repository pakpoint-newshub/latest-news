import time
import sys
import os
from datetime import datetime
from database import init_db, get_unposted_articles, get_stats
from collector import fetch_all_news
from distribution import load_config, broadcast_article, post_to_twitter, post_to_telegram, post_to_discord, post_to_slack

# Ensure UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def run_watch_cycle():
    """Single watch cycle: fetch news and auto-post unposted articles."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n=========================================================")
    print(f" 🔄 WATCHER CYCLE EXECUTING AT {timestamp} ")
    print(f"=========================================================")

    # 1. Fetch latest news & opinion feeds
    report = fetch_all_news()
    print(f" -> Feeds Checked: {report['total_fetched']} | New Articles Added: {report['total_new_inserted']}")

    # 2. Check config for auto-posting channels
    config = load_config()

    tw_enabled = config.get('twitter', {}).get('enabled', False)
    tg_enabled = config.get('telegram', {}).get('enabled', False)
    discord_enabled = config.get('discord', {}).get('enabled', False)
    slack_enabled = config.get('slack', {}).get('enabled', False)

    # 3. Auto-post to X (Twitter)
    if tw_enabled:
        unposted_tw = get_unposted_articles(channel='twitter', limit=3)
        if unposted_tw:
            print(f"\n[X Auto-Poster] Found {len(unposted_tw)} unposted articles for X account...")
            for article in unposted_tw:
                print(f" -> Posting to X: '{article['title'][:60]}...'")
                res = post_to_twitter(article)
                print(f"    Result: {res}")
        else:
            print(" -> X (Twitter): No new unposted articles.")
    else:
        print(" -> X (Twitter) Auto-Poster: Disabled in config.json (Provide API Keys to enable)")

    # 4. Auto-post to Telegram
    if tg_enabled:
        unposted_tg = get_unposted_articles(channel='telegram', limit=3)
        if unposted_tg:
            print(f"\n[Telegram Auto-Poster] Found {len(unposted_tg)} unposted articles...")
            for article in unposted_tg:
                res = post_to_telegram(article)
                print(f"    Result: {res}")

    # 5. Auto-post to Discord
    if discord_enabled:
        unposted_dc = get_unposted_articles(channel='discord', limit=3)
        if unposted_dc:
            print(f"\n[Discord Auto-Poster] Found {len(unposted_dc)} unposted articles...")
            for article in unposted_dc:
                res = post_to_discord(article)
                print(f"    Result: {res}")

    print(f"✔ Cycle finished at {datetime.now().strftime('%H:%M:%S')}")

def start_watcher(interval_minutes=10):
    """Start continuous background watcher daemon."""
    init_db()
    print(f"=========================================================")
    print(f" 🚀 PAKISTAN NEWS CONTINUOUS WATCHER DAEMON STARTED ")
    print(f" Polling all channels every {interval_minutes} minutes...")
    print(f"=========================================================")

    while True:
        try:
            run_watch_cycle()
        except Exception as e:
            print(f"[Watcher Error] Exception during cycle: {e}")

        print(f"\n⏳ Waiting {interval_minutes} minutes for next cycle... (Press Ctrl+C to stop)")
        time.sleep(interval_minutes * 60)

if __name__ == '__main__':
    interval = 10
    if len(sys.argv) > 1:
        try:
            interval = int(sys.argv[1])
        except ValueError:
            pass
    start_watcher(interval_minutes=interval)
