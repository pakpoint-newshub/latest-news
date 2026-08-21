import sqlite3
import json
import csv
import os
from datetime import datetime

DEFAULT_DB_PATH = "news_database.db"

DEFAULT_SOURCES = [
    {
        "name": "Dawn News",
        "feed_url": "https://www.dawn.com/feeds/pakistan",
        "website_url": "https://www.dawn.com",
        "category": "General News"
    },
    {
        "name": "The Express Tribune",
        "feed_url": "https://tribune.com.pk/feed/pakistan",
        "website_url": "https://tribune.com.pk",
        "category": "General News"
    },
    {
        "name": "Geo TV",
        "feed_url": "https://www.geo.tv/rss/1/1",
        "website_url": "https://www.geo.tv",
        "category": "Broadcasting"
    },
    {
        "name": "Al Jazeera - Pakistan",
        "feed_url": "https://www.aljazeera.com/xml/rss/all.xml",
        "website_url": "https://www.aljazeera.com",
        "category": "International"
    },
    {
        "name": "Google News (Pakistan)",
        "feed_url": "https://news.google.com/rss/search?q=Pakistan&hl=en-PK&gl=PK&ceid=PK:en",
        "website_url": "https://news.google.com",
        "category": "Aggregator"
    },
    {
        "name": "Dawn Opinion & Columns",
        "feed_url": "https://www.dawn.com/feeds/opinion",
        "website_url": "https://www.dawn.com/opinion",
        "category": "Journalist Opinion"
    },
    {
        "name": "Express Tribune Opinion",
        "feed_url": "https://tribune.com.pk/feed/opinion",
        "website_url": "https://tribune.com.pk/opinion",
        "category": "Journalist Opinion"
    },
    {
        "name": "Journalist Commentary & Open Analysis",
        "feed_url": "https://news.google.com/rss/search?q=Pakistan+Journalist+Opinion+OR+Hamid+Mir+OR+Najam+Sethi+OR+Mazhar+Abbas+OR+Cyril+Almeida&hl=en-PK&gl=PK&ceid=PK:en",
        "website_url": "https://news.google.com",
        "category": "Journalist Opinion"
    },
    {
        "name": "Social Media Journalists (Imran Riaz, Siddique Jaan, Shahbaz Gill)",
        "feed_url": "https://news.google.com/rss/search?q=Imran+Riaz+Khan+OR+Shahbaz+Gill+OR+Siddique+Jaan+OR+Sabir+Shakir+OR+Moeed+Pirzada+OR+Sami+Abraham&hl=en-PK&gl=PK&ceid=PK:en",
        "website_url": "https://news.google.com",
        "category": "Journalist Opinion"
    },
    {
        "name": "Pakistan Video News & Bulletins",
        "feed_url": "https://news.google.com/rss/search?q=Pakistan+News+Video+OR+Bulletin+OR+Live&hl=en-PK&gl=PK&ceid=PK:en",
        "website_url": "https://news.google.com",
        "category": "Video News"
    }
]

def get_db_connection(db_path=DEFAULT_DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path=DEFAULT_DB_PATH):
    """Initialize database schemas, seed sources, and apply migrations."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Create sources table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            feed_url TEXT NOT NULL,
            website_url TEXT,
            category TEXT DEFAULT 'General',
            enabled INTEGER DEFAULT 1,
            last_fetched_at TIMESTAMP
        )
    ''')

    # Create articles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            link TEXT UNIQUE NOT NULL,
            source_id INTEGER,
            source_name TEXT NOT NULL,
            summary TEXT,
            content TEXT,
            author TEXT,
            category TEXT DEFAULT 'Pakistan',
            published_at TIMESTAMP,
            image_url TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            posted_telegram INTEGER DEFAULT 0,
            posted_discord INTEGER DEFAULT 0,
            posted_slack INTEGER DEFAULT 0,
            posted_twitter INTEGER DEFAULT 0,
            posted_at TIMESTAMP,
            is_opinion INTEGER DEFAULT 0,
            disclaimer TEXT,
            video_url TEXT,
            has_video INTEGER DEFAULT 0,
            FOREIGN KEY (source_id) REFERENCES sources (id)
        )
    ''')

    # Seed sources if missing
    for source in DEFAULT_SOURCES:
        cursor.execute('''
            INSERT OR IGNORE INTO sources (name, feed_url, website_url, category, enabled)
            VALUES (?, ?, ?, ?, 1)
        ''', (source['name'], source['feed_url'], source['website_url'], source['category']))

    # Migration safety check
    cursor.execute("PRAGMA table_info(articles)")
    columns = [row['name'] for row in cursor.fetchall()]
    
    for col in ['posted_telegram', 'posted_discord', 'posted_slack', 'posted_twitter']:
        if col not in columns:
            cursor.execute(f"ALTER TABLE articles ADD COLUMN {col} INTEGER DEFAULT 0")
    if 'posted_at' not in columns:
        cursor.execute("ALTER TABLE articles ADD COLUMN posted_at TIMESTAMP")
    if 'is_opinion' not in columns:
        cursor.execute("ALTER TABLE articles ADD COLUMN is_opinion INTEGER DEFAULT 0")
    if 'disclaimer' not in columns:
        cursor.execute("ALTER TABLE articles ADD COLUMN disclaimer TEXT")
    if 'video_url' not in columns:
        cursor.execute("ALTER TABLE articles ADD COLUMN video_url TEXT")
    if 'has_video' not in columns:
        cursor.execute("ALTER TABLE articles ADD COLUMN has_video INTEGER DEFAULT 0")

    conn.commit()
    conn.close()

def get_sources(enabled_only=True, db_path=DEFAULT_DB_PATH):
    """Retrieve news sources."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    query = 'SELECT * FROM sources'
    if enabled_only:
        query += ' WHERE enabled = 1'
    cursor.execute(query)
    sources = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return sources

def insert_articles(articles, db_path=DEFAULT_DB_PATH):
    """
    Insert a list of article dicts into the database.
    Skips duplicate links (using INSERT OR IGNORE).
    Returns count of newly inserted articles.
    """
    if not articles:
        return 0

    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    inserted_count = 0

    for item in articles:
        is_op = 1 if (item.get('category') == 'Journalist Opinion' or item.get('is_opinion') == 1) else 0
        disc = "Digital Journalist / Social Media Vlog Opinion (Open Perspective - Non-Endorsement)" if is_op else None
        v_url = item.get('video_url', '') or ''
        has_v = 1 if (v_url or item.get('has_video') == 1 or item.get('category') == 'Video News') else 0

        cursor.execute('''
            INSERT OR IGNORE INTO articles (
                title, link, source_id, source_name, summary, content,
                author, category, published_at, image_url, scraped_at, is_opinion, disclaimer, video_url, has_video
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?)
        ''', (
            item.get('title'),
            item.get('link'),
            item.get('source_id'),
            item.get('source_name', 'Unknown'),
            item.get('summary', ''),
            item.get('content', ''),
            item.get('author', ''),
            item.get('category', 'Pakistan'),
            item.get('published_at'),
            item.get('image_url', ''),
            is_op,
            disc,
            v_url,
            has_v
        ))
        if cursor.rowcount > 0:
            inserted_count += 1

    conn.commit()
    conn.close()
    return inserted_count

def update_source_last_fetched(source_id, db_path=DEFAULT_DB_PATH):
    """Update last_fetched_at timestamp for a given source."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE sources SET last_fetched_at = CURRENT_TIMESTAMP WHERE id = ?
    ''', (source_id,))
    conn.commit()
    conn.close()

def get_articles(source=None, category=None, search=None, is_opinion=None, has_video=None, limit=50, offset=0, db_path=DEFAULT_DB_PATH):
    """Query articles with optional filtering, search, and pagination."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    conditions = []
    params = []

    if source:
        conditions.append("source_name = ?")
        params.append(source)
    if category:
        conditions.append("category = ?")
        params.append(category)
    if is_opinion is not None:
        conditions.append("is_opinion = ?")
        params.append(1 if is_opinion else 0)
    if has_video is not None:
        conditions.append("has_video = ?")
        params.append(1 if has_video else 0)
    if search:
        conditions.append("(title LIKE ? OR summary LIKE ? OR content LIKE ? OR author LIKE ?)")
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param, search_param])

    where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    query = f"SELECT * FROM articles{where_clause} ORDER BY COALESCE(published_at, scraped_at) DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor.execute(query, params)
    articles = [dict(row) for row in cursor.fetchall()]

    # Also count total matching
    count_query = f"SELECT COUNT(*) as total FROM articles{where_clause}"
    cursor.execute(count_query, params[:-2])
    total = cursor.fetchone()['total']

    conn.close()
    return {"articles": articles, "total": total, "limit": limit, "offset": offset}

def get_article_by_id(article_id, db_path=DEFAULT_DB_PATH):
    """Fetch a single article by ID."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def mark_article_posted(article_id, channel, db_path=DEFAULT_DB_PATH):
    """Mark an article as posted to a specific social channel."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    col_map = {
        'telegram': 'posted_telegram',
        'discord': 'posted_discord',
        'slack': 'posted_slack',
        'twitter': 'posted_twitter'
    }
    target_col = col_map.get(channel.lower())
    if target_col:
        cursor.execute(f'''
            UPDATE articles SET {target_col} = 1, posted_at = CURRENT_TIMESTAMP WHERE id = ?
        ''', (article_id,))
    else:
        cursor.execute('''
            UPDATE articles SET posted_at = CURRENT_TIMESTAMP WHERE id = ?
        ''', (article_id,))
    conn.commit()
    conn.close()

def get_unposted_articles(channel='twitter', limit=10, db_path=DEFAULT_DB_PATH):
    """Fetch articles that have not yet been posted to a given channel."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    col_map = {
        'telegram': 'posted_telegram',
        'discord': 'posted_discord',
        'slack': 'posted_slack',
        'twitter': 'posted_twitter'
    }
    col = col_map.get(channel.lower(), 'posted_twitter')
    query = f"SELECT * FROM articles WHERE {col} = 0 ORDER BY COALESCE(published_at, scraped_at) DESC LIMIT ?"
    cursor.execute(query, (limit,))
    articles = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return articles

def get_stats(db_path=DEFAULT_DB_PATH):
    """Return database metrics and source breakdown."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total_articles FROM articles")
    total_articles = cursor.fetchone()['total_articles']

    cursor.execute("SELECT COUNT(*) as total_sources FROM sources WHERE enabled = 1")
    total_sources = cursor.fetchone()['total_sources']

    cursor.execute("SELECT source_name, COUNT(*) as count FROM articles GROUP BY source_name ORDER BY count DESC")
    source_counts = [dict(row) for row in cursor.fetchall()]

    cursor.execute("SELECT MAX(scraped_at) as last_sync FROM articles")
    last_sync = cursor.fetchone()['last_sync']

    cursor.execute("SELECT COUNT(*) as count_today FROM articles WHERE DATE(scraped_at) = DATE('now')")
    articles_today = cursor.fetchone()['count_today']

    cursor.execute("SELECT COUNT(*) as opinion_count FROM articles WHERE is_opinion = 1")
    opinion_count = cursor.fetchone()['opinion_count']

    cursor.execute("SELECT COUNT(*) as video_count FROM articles WHERE has_video = 1")
    video_count = cursor.fetchone()['video_count']

    cursor.execute("SELECT COUNT(*) as posted_count FROM articles WHERE posted_at IS NOT NULL")
    posted_count = cursor.fetchone()['posted_count']

    cursor.execute("SELECT COUNT(*) as posted_tw_count FROM articles WHERE posted_twitter = 1")
    posted_twitter_count = cursor.fetchone()['posted_tw_count']

    conn.close()
    return {
        "total_articles": total_articles,
        "total_sources": total_sources,
        "source_counts": source_counts,
        "last_sync": last_sync,
        "articles_today": articles_today,
        "opinion_articles": opinion_count,
        "video_articles": video_count,
        "posted_to_social": posted_count,
        "posted_to_twitter": posted_twitter_count
    }

def export_articles(format_type='json', file_path=None, db_path=DEFAULT_DB_PATH):
    """Export all stored articles to JSON or CSV."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM articles ORDER BY COALESCE(published_at, scraped_at) DESC")
    articles = [dict(row) for row in cursor.fetchall()]
    conn.close()

    if not file_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = f"pakistan_news_export_{timestamp}.{format_type.lower()}"

    if format_type.lower() == 'json':
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=2, ensure_ascii=False)
    elif format_type.lower() == 'csv':
        if articles:
            keys = articles[0].keys()
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(articles)

    return file_path
