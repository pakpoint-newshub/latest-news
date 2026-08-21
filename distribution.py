import json
import urllib.parse
import os
import requests
import tweepy
from database import mark_article_posted

CONFIG_PATH = "config.json"

def load_config():
    """Load social media configuration."""
    if not os.path.exists(CONFIG_PATH):
        return {
            "hashtags": "#Pakistan #PakistanNews #LatestNews",
            "auto_post_on_fetch": False,
            "watcher": {
                "enabled": True,
                "interval_minutes": 10,
                "post_to_twitter": True,
                "post_to_telegram": False,
                "post_to_discord": False
            },
            "twitter": {
                "enabled": False,
                "api_key": "",
                "api_secret": "",
                "access_token": "",
                "access_token_secret": "",
                "bearer_token": ""
            },
            "telegram": {"enabled": False, "bot_token": "", "chat_id": ""},
            "discord": {"enabled": False, "webhook_url": ""},
            "slack": {"enabled": False, "webhook_url": ""},
            "custom_webhook": {"enabled": False, "webhook_url": ""}
        }
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config_data):
    """Save social media configuration."""
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)
    return True

def format_article_message(article, platform='general'):
    """Format article content into platform-tailored post text."""
    config = load_config()
    hashtags = config.get('hashtags', '#Pakistan #PakistanNews')
    title = article.get('title', '')
    source = article.get('source_name', 'News')
    summary = article.get('summary', '') or ''
    link = article.get('link', '')

    if platform == 'twitter':
        # X (Twitter) 280-character limit formatting
        is_op = article.get('is_opinion')
        prefix = "📹 " if article.get('has_video') else ("✍️ Opinion: " if is_op else "📰 ")
        
        # Calculate available title length
        # Twitter t.co link takes 23 chars, hashtags ~30 chars, prefix ~15 chars -> title ~200 chars max
        max_title_len = 180
        short_title = title if len(title) <= max_title_len else title[:max_title_len - 3] + "..."
        
        tweet_text = f"{prefix}{short_title}\n\nVia {source}\n🔗 {link}\n\n{hashtags}"
        return tweet_text[:280]

    elif platform == 'telegram':
        return (
            f"<b>📰 {title}</b>\n\n"
            f"<i>Source: {source}</i>\n"
            f"{summary[:200]}...\n\n"
            f"🔗 <a href='{link}'>Read Full Story</a>\n\n"
            f"{hashtags}"
        )
    elif platform == 'discord':
        return {
            "embeds": [{
                "title": title,
                "url": link,
                "description": summary[:250],
                "color": 1095793 if not article.get('is_opinion') else 11032055,
                "footer": {"text": f"Source: {source} • {hashtags}"},
                "thumbnail": {"url": article.get('image_url', '')} if article.get('image_url') else None
            }]
        }
    elif platform == 'slack':
        return {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*<{link}|{title}>*\n_Source: {source}_\n{summary[:250]}\n{hashtags}"
                    }
                }
            ]
        }
    else:  # General plain text
        return f"📰 {title}\nSource: {source}\n\n{summary[:250]}\n\nRead more: {link}\n{hashtags}"

def get_social_share_links(article):
    """Generate 1-click web sharing URLs for social platforms."""
    config = load_config()
    hashtags = config.get('hashtags', '#Pakistan #PakistanNews')
    title = article.get('title', '')
    link = article.get('link', '')

    text = f"{title}\n{hashtags}"
    encoded_text = urllib.parse.quote(text)
    encoded_link = urllib.parse.quote(link)

    return {
        "twitter": f"https://twitter.com/intent/tweet?text={encoded_text}&url={encoded_link}",
        "telegram": f"https://t.me/share/url?url={encoded_link}&text={encoded_text}",
        "whatsapp": f"https://api.whatsapp.com/send?text={encoded_text}%20{encoded_link}",
        "linkedin": f"https://www.linkedin.com/sharing/share-offsite/?url={encoded_link}",
        "facebook": f"https://www.facebook.com/sharer/sharer.php?u={encoded_link}"
    }

def post_to_twitter(article, api_key=None, api_secret=None, access_token=None, access_token_secret=None):
    """Post article to X (Twitter) account via Tweepy (Twitter API v2)."""
    config = load_config()
    tw_cfg = config.get('twitter', {})

    key = api_key or tw_cfg.get('api_key')
    sec = api_secret or tw_cfg.get('api_secret')
    tok = access_token or tw_cfg.get('access_token')
    tok_sec = access_token_secret or tw_cfg.get('access_token_secret')

    if not key or not sec or not tok or not tok_sec:
        return {"success": False, "channel": "twitter", "error": "X (Twitter) API keys missing in config.json"}

    tweet_text = format_article_message(article, platform='twitter')

    try:
        # Initialize Tweepy v2 Client
        client = tweepy.Client(
            consumer_key=key,
            consumer_secret=sec,
            access_token=tok,
            access_token_secret=tok_sec
        )

        response = client.create_tweet(text=tweet_text)
        if response and response.data:
            tweet_id = response.data.get('id')
            mark_article_posted(article['id'], 'twitter')
            print(f"[X Auto-Poster] Successfully posted Tweet ID {tweet_id} for article #{article['id']}")
            return {"success": True, "channel": "twitter", "tweet_id": tweet_id}
        else:
            return {"success": False, "channel": "twitter", "error": "No data returned from Twitter API"}

    except Exception as e:
        print(f"[X Auto-Poster Error] {e}")
        return {"success": False, "channel": "twitter", "error": str(e)}

def post_to_telegram(article, bot_token=None, chat_id=None):
    """Post article to a Telegram Channel or Group."""
    config = load_config()
    tg_config = config.get('telegram', {})
    token = bot_token or tg_config.get('bot_token')
    cid = chat_id or tg_config.get('chat_id')

    if not token or not cid:
        return {"success": False, "channel": "telegram", "error": "Telegram bot_token or chat_id missing in config.json"}

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    message_text = format_article_message(article, platform='telegram')

    payload = {
        "chat_id": cid,
        "text": message_text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }

    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            mark_article_posted(article['id'], 'telegram')
            return {"success": True, "channel": "telegram", "response": res.json()}
        else:
            return {"success": False, "channel": "telegram", "error": f"HTTP {res.status_code}: {res.text}"}
    except Exception as e:
        return {"success": False, "channel": "telegram", "error": str(e)}

def post_to_discord(article, webhook_url=None):
    """Post article to a Discord channel via Webhook."""
    config = load_config()
    url = webhook_url or config.get('discord', {}).get('webhook_url')

    if not url:
        return {"success": False, "channel": "discord", "error": "Discord webhook_url missing in config.json"}

    payload = format_article_message(article, platform='discord')

    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code in [200, 204]:
            mark_article_posted(article['id'], 'discord')
            return {"success": True, "channel": "discord"}
        else:
            return {"success": False, "channel": "discord", "error": f"HTTP {res.status_code}: {res.text}"}
    except Exception as e:
        return {"success": False, "channel": "discord", "error": str(e)}

def post_to_slack(article, webhook_url=None):
    """Post article to a Slack channel via Webhook."""
    config = load_config()
    url = webhook_url or config.get('slack', {}).get('webhook_url')

    if not url:
        return {"success": False, "channel": "slack", "error": "Slack webhook_url missing in config.json"}

    payload = format_article_message(article, platform='slack')

    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            mark_article_posted(article['id'], 'slack')
            return {"success": True, "channel": "slack"}
        else:
            return {"success": False, "channel": "slack", "error": f"HTTP {res.status_code}: {res.text}"}
    except Exception as e:
        return {"success": False, "channel": "slack", "error": str(e)}

def post_to_custom_webhook(article, webhook_url=None):
    """Post article payload to a generic Zapier/Make/Custom webhook endpoint."""
    config = load_config()
    url = webhook_url or config.get('custom_webhook', {}).get('webhook_url')

    if not url:
        return {"success": False, "channel": "custom_webhook", "error": "Custom webhook_url missing in config.json"}

    payload = {
        "event": "new_article",
        "article": article,
        "formatted_text": format_article_message(article, platform='general'),
        "share_links": get_social_share_links(article)
    }

    try:
        res = requests.post(url, json=payload, timeout=10)
        return {"success": res.status_code in [200, 201, 202, 204], "channel": "custom_webhook"}
    except Exception as e:
        return {"success": False, "channel": "custom_webhook", "error": str(e)}

def broadcast_article(article, target_channels=None):
    """Broadcast an article across all enabled or specified social channels."""
    config = load_config()
    results = {}

    if not target_channels:
        target_channels = []
        if config.get('twitter', {}).get('enabled'): target_channels.append('twitter')
        if config.get('telegram', {}).get('enabled'): target_channels.append('telegram')
        if config.get('discord', {}).get('enabled'): target_channels.append('discord')
        if config.get('slack', {}).get('enabled'): target_channels.append('slack')
        if config.get('custom_webhook', {}).get('enabled'): target_channels.append('custom_webhook')

    for channel in target_channels:
        if channel == 'twitter':
            results['twitter'] = post_to_twitter(article)
        elif channel == 'telegram':
            results['telegram'] = post_to_telegram(article)
        elif channel == 'discord':
            results['discord'] = post_to_discord(article)
        elif channel == 'slack':
            results['slack'] = post_to_slack(article)
        elif channel == 'custom_webhook':
            results['custom_webhook'] = post_to_custom_webhook(article)

    return results
