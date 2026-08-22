import os
import sqlite3
import datetime
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY or GEMINI_API_KEY == "your_api_key_here":
    print("Error: GEMINI_API_KEY is missing or invalid in .env file.")
    print("Get your API key at https://aistudio.google.com/app/apikey and add it to your .env file.")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3.6-flash')

DB_PATH = "news_database.db"

def get_latest_news():
    """Retrieve the latest 5 video/opinion news items from the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = '''
        SELECT source_name, title, summary, published_at
        FROM articles
        WHERE (is_opinion = 1 OR has_video = 1)
        ORDER BY published_at DESC
        LIMIT 5
    '''
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return rows

def generate_script(news_items):
    """Call Gemini to write a YouTube script."""
    
    if not news_items:
        return "No recent news found to generate a script."
    
    news_context = ""
    for idx, item in enumerate(news_items, 1):
        news_context += f"\n--- Story {idx} ---\n"
        news_context += f"Source: {item['source_name']}\n"
        news_context += f"Headline: {item['title']}\n"
        news_context += f"Details: {item['summary']}\n"
    
    prompt = f"""
Act as a highly engaging political commentator for a Faceless YouTube Channel called "PakPoint News Hub". 
Your job is to write a thrilling, analytical, and engaging 3-5 minute YouTube video script discussing the latest news and vlogs from Pakistani journalists.

Here are the top stories for today:
{news_context}

Script Requirements:
1. Start with a very strong, hook-driven intro that grabs attention within the first 5 seconds.
2. Discuss the stories naturally. Do not just read them like a list. Weave them together into a narrative or commentary.
3. Use a conversational, authoritative, and slightly dramatic tone.
4. Add bracketed visual cues for the video editor (e.g., [Show dramatic footage of parliament], [Show screenshot of Imran Riaz Khan's tweet]).
5. End with a strong Call to Action (CTA) asking viewers to subscribe, like, and comment their opinion below.

Output purely the script in Markdown format. Do not include any other conversational filler text from the AI.
"""

    print("Sending prompt to Gemini AI...")
    response = model.generate_content(prompt)
    return response.text

def main():
    print("Fetching latest news from database...")
    items = get_latest_news()
    
    if not items:
        print("No news available from the database.")
        return
        
    script_text = generate_script(items)
    
    # Save script to file
    today_str = datetime.datetime.now().strftime("%Y_%m_%d")
    output_filename = f"youtube_scripts/script_{today_str}.md"
    
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(script_text)
        
    print(f"\nSuccess! Generated script saved to {output_filename}")

if __name__ == "__main__":
    main()
