import time
import re
import urllib.parse
from datetime import datetime
import feedparser
import requests
from bs4 import BeautifulSoup
from database import get_sources, insert_articles, update_source_last_fetched, DEFAULT_DB_PATH

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

JOURNALIST_KEYWORDS = [
    'imran riaz', 'shahbaz gill', 'siddique jaan', 'sami abraham', 
    'moeed pirzada', 'sabir shakir', 'hamid mir', 'najam sethi', 
    'mazhar abbas', 'cyril almeida', 'zahid hussain', 'raza rumi'
]

def clean_html(raw_html):
    """Clean HTML tags and return plain text snippet."""
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)
    text = re.sub(r'\s+', ' ', text)
    return text[:500]

def extract_image(entry, raw_summary=""):
    """Extract article thumbnail/image URL from RSS entry structure."""
    if hasattr(entry, 'media_content') and entry.media_content:
        for media in entry.media_content:
            if 'url' in media and (media.get('medium') == 'image' or media.get('type', '').startswith('image')):
                return media['url']
            elif 'url' in media:
                return media['url']

    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
        if isinstance(entry.media_thumbnail, list) and len(entry.media_thumbnail) > 0:
            return entry.media_thumbnail[0].get('url', '')

    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enc in entry.enclosures:
            if enc.get('type', '').startswith('image/') or 'url' in enc:
                return enc.get('href') or enc.get('url')

    content_to_check = raw_summary
    if hasattr(entry, 'content') and entry.content:
        content_to_check += " " + entry.content[0].value

    if content_to_check:
        soup = BeautifulSoup(content_to_check, 'html.parser')
        img = soup.find('img')
        if img and img.get('src'):
            return img['src']

    return ""

def extract_video_url(entry, raw_summary=""):
    """Extract embedded video URL or YouTube video link from RSS entry."""
    if hasattr(entry, 'yt_videoid') and entry.yt_videoid:
        return f"https://www.youtube.com/embed/{entry.yt_videoid}"

    if hasattr(entry, 'media_player') and entry.media_player:
        if isinstance(entry.media_player, dict) and 'url' in entry.media_player:
            return entry.media_player['url']

    if hasattr(entry, 'media_content') and entry.media_content:
        for media in entry.media_content:
            if media.get('medium') == 'video' or media.get('type', '').startswith('video/'):
                url = media.get('url', '')
                if 'youtube.com/watch' in url:
                    video_id = urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get('v', [''])[0]
                    if video_id: return f"https://www.youtube.com/embed/{video_id}"
                return url

    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enc in entry.enclosures:
            if enc.get('type', '').startswith('video/'):
                return enc.get('href') or enc.get('url')

    content_to_check = raw_summary
    if hasattr(entry, 'content') and entry.content:
        content_to_check += " " + entry.content[0].value

    if content_to_check:
        soup = BeautifulSoup(content_to_check, 'html.parser')
        iframe = soup.find('iframe')
        if iframe and iframe.get('src'):
            src = iframe['src']
            if 'youtube.com' in src or 'vimeo.com' in src or 'dailymotion.com' in src:
                return src

        video_tag = soup.find('video')
        if video_tag:
            source = video_tag.find('source')
            if source and source.get('src'):
                return source['src']
            elif video_tag.get('src'):
                return video_tag['src']

    link = entry.get('link', '')
    if 'youtube.com/watch' in link or 'youtu.be/' in link:
        if 'youtu.be/' in link:
            video_id = link.split('youtu.be/')[-1].split('?')[0]
            return f"https://www.youtube.com/embed/{video_id}"
        else:
            video_id = urllib.parse.parse_qs(urllib.parse.urlparse(link).query).get('v', [''])[0]
            if video_id: return f"https://www.youtube.com/embed/{video_id}"

    return ""

def parse_pub_date(entry):
    """Normalize RSS date formats to standard ISO string."""
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        return time.strftime('%Y-%m-%d %H:%M:%S', entry.published_parsed)
    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
        return time.strftime('%Y-%m-%d %H:%M:%S', entry.updated_parsed)
    elif hasattr(entry, 'published') and entry.published:
        return str(entry.published)
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def fetch_source_feed(source):
    """
    Fetch and parse RSS feed for a specific source.
    Returns list of parsed article dictionaries.
    """
    feed_url = source['feed_url']
    source_name = source['name']
    source_id = source['id']
    category = source.get('category', 'Pakistan')
    base_is_op = 1 if category == 'Journalist Opinion' or 'Opinion' in source_name or 'Journalist' in source_name else 0

    articles = []

    try:
        resp = requests.get(feed_url, headers=HEADERS, timeout=12)
        if resp.status_code != 200:
            print(f"[{source_name}] Warning: HTTP status {resp.status_code}")
            return articles

        feed = feedparser.parse(resp.content)

        for entry in feed.entries:
            title = entry.get('title', '').strip()
            link = entry.get('link', '').strip()

            if not title or not link:
                continue

            if 'news.google.com' in link and 'url=' in link:
                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(link).query)
                if 'url' in parsed:
                    link = parsed['url'][0]

            raw_summary = entry.get('summary', '') or entry.get('description', '')
            summary = clean_html(raw_summary)

            author = entry.get('author', '')
            published_at = parse_pub_date(entry)
            image_url = extract_image(entry, raw_summary)
            video_url = extract_video_url(entry, raw_summary)

            # Auto-detect social media journalist opinion
            full_text = (title + " " + summary + " " + author).lower()
            is_journalist_opinion = base_is_op or any(k in full_text for k in JOURNALIST_KEYWORDS)
            is_opinion = 1 if is_journalist_opinion else 0

            has_video = 1 if (video_url or category == 'Video News' or 'video' in title.lower() or 'vlog' in title.lower() or 'bulletin' in title.lower()) else 0

            disclaimer = "Digital Journalist / Vlog Opinion (Open Perspective - Non-Endorsement)" if is_opinion else None

            articles.append({
                'title': title,
                'link': link,
                'source_id': source_id,
                'source_name': source_name,
                'summary': summary,
                'content': summary,
                'author': author,
                'category': category if not is_opinion else 'Journalist Opinion',
                'published_at': published_at,
                'image_url': image_url,
                'video_url': video_url,
                'has_video': has_video,
                'is_opinion': is_opinion,
                'disclaimer': disclaimer
            })

    except Exception as e:
        print(f"[{source_name}] Error fetching feed: {e}")

    return articles

def fetch_all_news(db_path=DEFAULT_DB_PATH):
    """
    Fetch latest news from all enabled sources and save to database.
    Returns collection report summary.
    """
    sources = get_sources(enabled_only=True, db_path=db_path)
    total_fetched = 0
    total_new_inserted = 0
    source_stats = []

    print(f"Starting news collection across {len(sources)} sources...")

    for source in sources:
        fetched_articles = fetch_source_feed(source)
        count_fetched = len(fetched_articles)
        total_fetched += count_fetched

        new_count = insert_articles(fetched_articles, db_path=db_path)
        total_new_inserted += new_count

        if count_fetched > 0:
            update_source_last_fetched(source['id'], db_path=db_path)

        source_stats.append({
            'source_name': source['name'],
            'fetched': count_fetched,
            'new_inserted': new_count
        })

        print(f" -> {source['name']}: {count_fetched} articles fetched, {new_count} new saved.")

    return {
        'total_sources': len(sources),
        'total_fetched': total_fetched,
        'total_new_inserted': total_new_inserted,
        'source_stats': source_stats,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def scrape_full_article_content(url):
    """Scrape main body paragraph text from a news article URL."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return ""

        soup = BeautifulSoup(resp.text, 'html.parser')
        for script in soup(["script", "style", "header", "footer", "nav"]):
            script.decompose()

        paragraphs = soup.find_all('p')
        text_blocks = [p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 40]
        return "\n\n".join(text_blocks)
    except Exception as e:
        print(f"Scrape error for {url}: {e}")
        return ""
