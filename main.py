import argparse
import sys
import os

# Fix Windows console UTF-8 output encoding
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from database import init_db, get_articles, get_stats, export_articles, get_sources, get_unposted_articles, get_article_by_id
from collector import fetch_all_news
from distribution import broadcast_article, get_social_share_links, format_article_message, load_config, post_to_twitter

def print_header(title):
    print("=" * 65)
    print(f" {title.center(63)} ")
    print("=" * 65)

def handle_fetch(args):
    print_header("FETCHING LATEST PAKISTAN NEWS & OPINIONS")
    init_db()
    result = fetch_all_news()
    print("\nSummary:")
    print(f" - Sources Processed: {result['total_sources']}")
    print(f" - Total Feeds Fetched: {result['total_fetched']}")
    print(f" - New Articles Added: {result['total_new_inserted']}")

def handle_list(args):
    init_db()
    data = get_articles(source=args.source, limit=args.limit)
    articles = data['articles']
    total = data['total']

    title = f"STORED ARTICLES ({len(articles)} of {total})"
    if args.source:
        title += f" [Source: {args.source}]"
    print_header(title)

    if not articles:
        print("No articles found in local database. Run 'python main.py fetch' first.")
        return

    for idx, item in enumerate(articles, 1):
        pub_time = item.get('published_at') or item.get('scraped_at')
        is_op = " [OPINION]" if item.get('is_opinion') else ""
        print(f"\n[{idx}] {item['title']}{is_op} (ID: {item['id']})")
        print(f"    Source: {item['source_name']} | Published: {pub_time}")
        print(f"    URL:    {item['link']}")

def handle_search(args):
    init_db()
    query = args.query
    data = get_articles(search=query, limit=args.limit)
    articles = data['articles']
    total = data['total']

    print_header(f"SEARCH RESULTS FOR '{query}' ({total} found)")

    if not articles:
        print(f"No articles matching '{query}' found.")
        return

    for idx, item in enumerate(articles, 1):
        is_op = " [OPINION]" if item.get('is_opinion') else ""
        print(f"\n[{idx}] {item['title']}{is_op} (ID: {item['id']})")
        print(f"    Source: {item['source_name']} | Published: {item.get('published_at')}")
        print(f"    URL:    {item['link']}")

def handle_stats(args):
    init_db()
    stats = get_stats()
    print_header("PAKISTAN NEWS DATABASE STATISTICS")
    print(f" Total Stored Articles : {stats['total_articles']}")
    print(f" Active News Sources   : {stats['total_sources']}")
    print(f" Journalist Opinions   : {stats.get('opinion_articles', 0)}")
    print(f" Video News Reports    : {stats.get('video_articles', 0)}")
    print(f" Articles Added Today  : {stats['articles_today']}")
    print(f" Posted to X (Twitter) : {stats.get('posted_to_twitter', 0)}")
    print(f" Articles Posted Social: {stats.get('posted_to_social', 0)}")
    print(f" Last Sync Timestamp   : {stats['last_sync'] or 'Never'}")
    print("\nSource Breakdown:")
    for src in stats['source_counts']:
        print(f" - {src['source_name']:<30}: {src['count']} articles")

def handle_export(args):
    init_db()
    fmt = args.format.lower()
    file_path = export_articles(format_type=fmt, file_path=args.output)
    print(f"Successfully exported database articles to: {file_path}")

def handle_post(args):
    init_db()
    channel = args.channel.lower()
    limit = args.limit

    print_header(f"BROADCASTING UNPOSTED ARTICLES TO SOCIAL ({channel.upper()})")

    unposted = get_unposted_articles(channel=channel, limit=limit)
    if not unposted:
        print(f"No unposted articles found for channel '{channel}'.")
        return

    channels_to_post = [channel] if channel != 'all' else None

    for item in unposted:
        print(f"\nPosting Article ID {item['id']}: {item['title'][:60]}...")
        res = broadcast_article(item, target_channels=channels_to_post)
        print("  Results:", res)

def handle_share(args):
    init_db()
    article = get_article_by_id(args.article_id)
    if not article:
        print(f"Article ID {args.article_id} not found.")
        return

    links = get_social_share_links(article)
    print_header(f"SOCIAL SHARE LINKS FOR ARTICLE #{article['id']}")
    print(f"Title: {article['title']}\n")
    for platform, url in links.items():
        print(f" -> {platform.capitalize():<10}: {url}")

def handle_watch(args):
    from watcher import start_watcher
    start_watcher(interval_minutes=args.interval)

def handle_serve(args):
    from app import run_app
    run_app(port=args.port, host=args.host)

def main():
    parser = argparse.ArgumentParser(description="Pakistan News Collector, X Auto-Poster & Distribution System")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Fetch
    parser_fetch = subparsers.add_parser("fetch", help="Fetch latest news & opinions into local database")
    parser_fetch.set_defaults(func=handle_fetch)

    # List
    parser_list = subparsers.add_parser("list", help="List stored articles")
    parser_list.add_argument("--source", type=str, help="Filter by source name")
    parser_list.add_argument("--limit", type=int, default=20, help="Number of articles to list")
    parser_list.set_defaults(func=handle_list)

    # Search
    parser_search = subparsers.add_parser("search", help="Search stored articles by keyword")
    parser_search.add_argument("query", type=str, help="Keyword to search for")
    parser_search.add_argument("--limit", type=int, default=20, help="Limit results")
    parser_search.set_defaults(func=handle_search)

    # Stats
    parser_stats = subparsers.add_parser("stats", help="Display database metrics")
    parser_stats.set_defaults(func=handle_stats)

    # Export
    parser_export = subparsers.add_parser("export", help="Export stored articles to JSON or CSV")
    parser_export.add_argument("--format", choices=["json", "csv"], default="json", help="Export format")
    parser_export.add_argument("--output", type=str, help="Output filepath")
    parser_export.set_defaults(func=handle_export)

    # Post
    parser_post = subparsers.add_parser("post", help="Post unposted articles to configured social channels")
    parser_post.add_argument("--channel", choices=["twitter", "telegram", "discord", "slack", "all"], default="all", help="Social channel to target")
    parser_post.add_argument("--limit", type=int, default=5, help="Number of articles to broadcast")
    parser_post.set_defaults(func=handle_post)

    # Watch
    parser_watch = subparsers.add_parser("watch", help="Start continuous background watcher daemon for news & X auto-posting")
    parser_watch.add_argument("--interval", type=int, default=10, help="Check interval in minutes (default: 10)")
    parser_watch.set_defaults(func=handle_watch)

    # Share
    parser_share = subparsers.add_parser("share", help="Generate 1-click social share links for an article ID")
    parser_share.add_argument("article_id", type=int, help="Article ID")
    parser_share.set_defaults(func=handle_share)

    # Serve
    parser_serve = subparsers.add_parser("serve", help="Launch interactive web dashboard")
    parser_serve.add_argument("--port", type=int, default=5000, help="Server port (default: 5000)")
    parser_serve.add_argument("--host", type=str, default="127.0.0.1", help="Server host (default: 127.0.0.1)")
    parser_serve.set_defaults(func=handle_serve)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        print("No command specified. Running 'fetch' followed by 'stats'...")
        handle_fetch(args)
        print("\n")
        handle_stats(args)

if __name__ == "__main__":
    main()
