# 📰 Pakistan News Hub | Cloud Watcher & X (Twitter) Auto-Poster

![GitHub Repository](https://img.shields.io/badge/github-pakpoint--newshub%2Flatest--news-black?logo=github)
![Python Version](https://img.shields.io/badge/python-3.10%2B-emerald)
![Database](https://img.shields.io/badge/database-SQLite-blue)
![Framework](https://img.shields.io/badge/web-Flask-darkgreen)
![Cloud Watcher](https://img.shields.io/badge/cloud-GitHub%20Actions%20(Every%2015m)-orange)

An automated Pakistan news collector, video bulletin extractor, and digital journalist opinion monitoring system that publishes real-time news updates directly to your **X (Twitter) account**.

Official GitHub Repository: [https://github.com/pakpoint-newshub/latest-news](https://github.com/pakpoint-newshub/latest-news)

---

## ✨ Features

- **Multi-Source News Aggregator**: Dawn News, The Express Tribune, Geo TV, Al Jazeera, Google News.
- **Video News Bulletins**: Responsive embedded 16:9 video player for YouTube bulletins and news clips.
- **Digital Journalist Opinion Feeds**: Feeds from renowned Pakistani journalists (**Imran Riaz Khan**, **Shahbaz Gill**, **Siddique Jaan**, **Sabir Shakir**, **Moeed Pirzada**, **Hamid Mir**, **Najam Sethi**, etc.).
- **⚠️ Non-Endorsement Disclaimers**: Explicit notice banners attached to opinion pieces (*"Expresses individual journalist commentary for open discussion; does not constitute official news endorsement"*).
- **Automated X (Twitter) Cloud Watcher**: GitHub Actions workflow polls all news channels every 15 minutes in the cloud and automatically posts new stories to your X account.
- **Dark Glassmorphism Web Dashboard**: Real-time stats, keyword search, source filtering, quick view drawer, and social settings panel.

---

## 🚀 GitHub Deployment Commands

To deploy this project to your GitHub repository `https://github.com/pakpoint-newshub/latest-news`:

```bash
# 1. Initialize Git repository
git init

# 2. Add all project files
git add .

# 3. Commit files
git commit -m "Deploy Pakistan News Hub & X Auto-Poster"

# 4. Set main branch
git branch -M main

# 5. Connect to your repository
git remote add origin https://github.com/pakpoint-newshub/latest-news.git

# 6. Push to GitHub
git push -u origin main
```

---

## 🔑 Setting up Automated X (Twitter) Posting on GitHub

To enable **GitHub Actions** to automatically post news to your X (Twitter) account every 15 minutes:

1. Go to your repository settings on GitHub: `https://github.com/pakpoint-newshub/latest-news/settings/secrets/actions`
2. Click **New repository secret** and add the following 4 secrets from your [X Developer Portal](https://developer.x.com):
   - `TWITTER_API_KEY`: Your X API Consumer Key
   - `TWITTER_API_SECRET`: Your X API Consumer Secret
   - `TWITTER_ACCESS_TOKEN`: Your X Access Token
   - `TWITTER_ACCESS_TOKEN_SECRET`: Your X Access Token Secret
3. Once added, GitHub Actions will automatically run every 15 minutes, fetch latest Pakistan news, video bulletins & opinions, and post tweets to your X account!

---

## 💻 Local Usage Commands

```bash
# Fetch latest news, videos & opinions
python main.py fetch

# View database metrics
python main.py stats

# Post unposted news directly to X (Twitter)
python main.py post --channel twitter --limit 5

# Start local continuous watcher daemon (polls every 10 minutes)
python main.py watch --interval 10

# Launch Web Dashboard
python main.py serve --port 5000
```
