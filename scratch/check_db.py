import sqlite3

conn = sqlite3.connect('news_database.db')
cur = conn.cursor()

# Check journalist articles
cur.execute("""
    SELECT title, source_name, scraped_at 
    FROM articles 
    WHERE source_name LIKE '%Journalist%' OR source_name LIKE '%Shahbaz%' 
          OR source_name LIKE '%Pirzada%' OR source_name LIKE '%Waqar%'
    ORDER BY scraped_at DESC 
    LIMIT 15
""")
print("=== JOURNALIST ARTICLES (most recent) ===")
for r in cur.fetchall():
    print(r)

# Check the most recent published_at dates
cur.execute("SELECT MAX(published_at), MIN(published_at) FROM articles")
row = cur.fetchone()
print(f"\nNewest published_at: {row[0]}")
print(f"Oldest published_at: {row[1]}")

# Check articles by scraped_at for the last 24 hours
cur.execute("""
    SELECT COUNT(*), MIN(scraped_at), MAX(scraped_at) 
    FROM articles 
    WHERE scraped_at >= datetime('now', '-24 hours')
""")
row = cur.fetchone()
print(f"\nArticles scraped in last 24 hrs: {row[0]}")
print(f"  From: {row[1]} To: {row[2]}")

conn.close()
