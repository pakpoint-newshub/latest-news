from flask import Flask, render_template, jsonify, request, send_file
import os
from database import init_db, get_articles, get_stats, get_sources, export_articles, get_article_by_id
from collector import fetch_all_news, scrape_full_article_content
from distribution import (
    load_config, save_config, get_social_share_links,
    broadcast_article, post_to_telegram, post_to_discord, post_to_slack
)

app = Flask(__name__)

# Ensure DB initialized on startup
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/articles', methods=['GET'])
def api_get_articles():
    source = request.args.get('source')
    category = request.args.get('category')
    search = request.args.get('search')
    is_op_raw = request.args.get('is_opinion')
    has_vid_raw = request.args.get('has_video')
    limit = int(request.args.get('limit', 40))
    offset = int(request.args.get('offset', 0))

    is_opinion = True if is_op_raw == 'true' else (False if is_op_raw == 'false' else None)
    has_video = True if has_vid_raw == 'true' else (False if has_vid_raw == 'false' else None)

    data = get_articles(
        source=source if source and source != 'All' else None,
        category=category if category and category != 'All' else None,
        search=search,
        is_opinion=is_opinion,
        has_video=has_video,
        limit=limit,
        offset=offset
    )
    return jsonify({'status': 'success', 'data': data})

@app.route('/api/articles/<int:article_id>', methods=['GET'])
def api_get_article_details(article_id):
    article = get_article_by_id(article_id)
    if not article:
        return jsonify({'status': 'error', 'message': 'Article not found'}), 404

    # Scrape full content if snippet is short
    if request.args.get('full') == 'true' and len(article.get('content', '')) < 300:
        scraped = scrape_full_article_content(article['link'])
        if scraped:
            article['content'] = scraped

    # Include share links
    share_links = get_social_share_links(article)
    article['share_links'] = share_links

    return jsonify({'status': 'success', 'article': article})

@app.route('/api/stats', methods=['GET'])
def api_get_stats():
    stats = get_stats()
    return jsonify({'status': 'success', 'stats': stats})

@app.route('/api/sources', methods=['GET'])
def api_get_sources():
    sources = get_sources(enabled_only=False)
    return jsonify({'status': 'success', 'sources': sources})

@app.route('/api/fetch', methods=['POST'])
def api_trigger_fetch():
    try:
        report = fetch_all_news()
        stats = get_stats()
        return jsonify({
            'status': 'success',
            'message': f"Fetched {report['total_fetched']} feeds. Added {report['total_new_inserted']} new articles.",
            'report': report,
            'stats': stats
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/export/<fmt>', methods=['GET'])
def api_export_data(fmt):
    if fmt.lower() not in ['json', 'csv']:
        return jsonify({'status': 'error', 'message': 'Invalid format. Use json or csv'}), 400

    filename = f"pakistan_news_export.{fmt.lower()}"
    file_path = export_articles(format_type=fmt.lower(), file_path=filename)

    return send_file(file_path, as_attachment=True, download_name=filename)

# Social Media Endpoints
@app.route('/api/social/share/<int:article_id>', methods=['GET'])
def api_social_share_links(article_id):
    article = get_article_by_id(article_id)
    if not article:
        return jsonify({'status': 'error', 'message': 'Article not found'}), 404

    links = get_social_share_links(article)
    return jsonify({'status': 'success', 'links': links, 'article': article})

@app.route('/api/social/post', methods=['POST'])
def api_social_post_article():
    data = request.json or {}
    article_id = data.get('article_id')
    channels = data.get('channels', [])

    if not article_id:
        return jsonify({'status': 'error', 'message': 'article_id is required'}), 400

    article = get_article_by_id(article_id)
    if not article:
        return jsonify({'status': 'error', 'message': 'Article not found'}), 404

    results = broadcast_article(article, target_channels=channels)
    return jsonify({'status': 'success', 'results': results})

@app.route('/api/social/config', methods=['GET', 'POST'])
def api_social_config():
    if request.method == 'POST':
        new_config = request.json or {}
        save_config(new_config)
        return jsonify({'status': 'success', 'message': 'Configuration updated successfully', 'config': new_config})
    else:
        config = load_config()
        return jsonify({'status': 'success', 'config': config})

def run_app(host='127.0.0.1', port=5000):
    print(f"Launching Pakistan News Dashboard at http://{host}:{port}")
    app.run(host=host, port=port, debug=False)

if __name__ == '__main__':
    run_app()
