// Pakistan News Hub - Client Application Logic

document.addEventListener('DOMContentLoaded', () => {
  let currentSource = 'All';
  let isOpinionOnly = null;
  let isVideoOnly = null;
  let searchQuery = '';
  let searchTimeout = null;

  // DOM Elements
  const newsGrid = document.getElementById('news-grid');
  const searchInput = document.getElementById('search-input');
  const sourceFilters = document.getElementById('source-filters');
  const btnFetchNews = document.getElementById('btn-fetch-news');
  const syncIcon = document.getElementById('sync-icon');
  const btnExportJson = document.getElementById('btn-export-json');
  const btnExportCsv = document.getElementById('btn-export-csv');
  const btnSocialConfig = document.getElementById('btn-social-config');

  // Modals
  const articleModal = document.getElementById('article-modal');
  const modalCloseBtn = document.getElementById('modal-close-btn');
  const modalBody = document.getElementById('modal-body');

  const configModal = document.getElementById('config-modal');
  const configCloseBtn = document.getElementById('config-close-btn');
  const configCancelBtn = document.getElementById('config-cancel-btn');
  const socialConfigForm = document.getElementById('social-config-form');

  const toastContainer = document.getElementById('toast-container');

  // Stat Elements
  const statTotalArticles = document.getElementById('stat-total-articles');
  const statTotalSources = document.getElementById('stat-total-sources');
  const statArticlesToday = document.getElementById('stat-articles-today');
  const statOpinionArticles = document.getElementById('stat-opinion-articles');
  const statVideoArticles = document.getElementById('stat-video-articles');
  const statPostedTwitter = document.getElementById('stat-posted-twitter');

  // Initialize
  fetchStats();
  fetchArticles();

  // Event Listeners
  searchInput.addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    searchQuery = e.target.value.trim();
    searchTimeout = setTimeout(() => {
      fetchArticles();
    }, 300);
  });

  sourceFilters.addEventListener('click', (e) => {
    const pill = e.target.closest('.pill');
    if (pill) {
      document.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');

      if (pill.hasAttribute('data-opinion')) {
        isOpinionOnly = true;
        isVideoOnly = null;
        currentSource = 'All';
      } else if (pill.hasAttribute('data-video')) {
        isVideoOnly = true;
        isOpinionOnly = null;
        currentSource = 'All';
      } else {
        isOpinionOnly = null;
        isVideoOnly = null;
        currentSource = pill.getAttribute('data-source') || 'All';
      }
      fetchArticles();
    }
  });

  btnFetchNews.addEventListener('click', triggerFetch);
  btnExportJson.addEventListener('click', () => window.location.href = '/api/export/json');
  btnExportCsv.addEventListener('click', () => window.location.href = '/api/export/csv');

  btnSocialConfig.addEventListener('click', openConfigModal);
  configCloseBtn.addEventListener('click', () => configModal.classList.remove('active'));
  configCancelBtn.addEventListener('click', () => configModal.classList.remove('active'));
  socialConfigForm.addEventListener('submit', saveSocialConfig);

  modalCloseBtn.addEventListener('click', closeModal);
  articleModal.addEventListener('click', (e) => {
    if (e.target === articleModal) closeModal();
  });
  configModal.addEventListener('click', (e) => {
    if (e.target === configModal) configModal.classList.remove('active');
  });

  // Fetch Dashboard Stats
  async function fetchStats() {
    try {
      const res = await fetch('/api/stats');
      const data = await res.json();
      if (data.status === 'success') {
        const stats = data.stats;
        statTotalArticles.textContent = stats.total_articles.toLocaleString();
        statTotalSources.textContent = stats.total_sources;
        statArticlesToday.textContent = stats.articles_today.toLocaleString();
        statOpinionArticles.textContent = (stats.opinion_articles || 0).toLocaleString();
        statVideoArticles.textContent = (stats.video_articles || 0).toLocaleString();
        if (statPostedTwitter) statPostedTwitter.textContent = (stats.posted_to_twitter || 0).toLocaleString();
      }
    } catch (err) {
      console.error('Error loading stats:', err);
    }
  }

  // Fetch News Articles
  async function fetchArticles() {
    newsGrid.innerHTML = `
      <div class="loading-state">
        <div class="spinner"></div>
        <p>Searching database records...</p>
      </div>
    `;

    try {
      const params = new URLSearchParams({ limit: 40 });
      if (currentSource && currentSource !== 'All') params.append('source', currentSource);
      if (isOpinionOnly) params.append('is_opinion', 'true');
      if (isVideoOnly) params.append('has_video', 'true');
      if (searchQuery) params.append('search', searchQuery);

      const res = await fetch(`/api/articles?${params.toString()}`);
      const result = await res.json();

      if (result.status === 'success') {
        renderArticles(result.data.articles);
      } else {
        newsGrid.innerHTML = `<div class="empty-state"><p>Error fetching news articles.</p></div>`;
      }
    } catch (err) {
      console.error('Error fetching articles:', err);
      newsGrid.innerHTML = `<div class="empty-state"><p>Unable to connect to database server.</p></div>`;
    }
  }

  // Render Articles Grid
  function renderArticles(articles) {
    if (!articles || articles.length === 0) {
      newsGrid.innerHTML = `
        <div class="empty-state">
          <i class="fa-solid fa-newspaper" style="font-size: 3rem; color: var(--text-dim); margin-bottom: 1rem;"></i>
          <h3>No Items Found</h3>
          <p style="margin-top: 0.5rem;">Try adjusting your search query or click "Fetch News" to update feeds.</p>
        </div>
      `;
      return;
    }

    newsGrid.innerHTML = articles.map(art => {
      const isOp = art.is_opinion || art.category === 'Journalist Opinion';
      const hasVid = art.has_video || art.video_url || art.category === 'Video News';
      
      let sourceClass = getSourceClass(art.source_name);
      if (hasVid) sourceClass = 'video';
      if (isOp) sourceClass = 'opinion';

      const timeFormatted = formatRelativeTime(art.published_at || art.scraped_at);
      const imageSrc = art.image_url || getFallbackImage(art.source_name);
      const share = getShareUrls(art.title, art.link);

      return `
        <article class="news-card ${isOp ? 'is-opinion-card' : ''}">
          <div class="card-media-wrapper" onclick="openArticleModal(${art.id})" style="cursor: pointer;">
            <img class="card-media" src="${imageSrc}" alt="${escapeHtml(art.title)}" onerror="this.src='${getFallbackImage(art.source_name)}'">
            ${hasVid ? `<div class="video-play-overlay"><i class="fa-solid fa-play"></i></div>` : ''}
          </div>

          <div class="card-body">
            <div class="card-meta">
              <span class="source-tag ${sourceClass}">
                ${hasVid ? '<i class="fa-solid fa-video"></i> VIDEO REPORT' : (isOp ? 'JOURNALIST OPINION' : escapeHtml(art.source_name))}
              </span>
              <span class="card-time"><i class="fa-regular fa-clock"></i> ${timeFormatted}</span>
            </div>
            <h3 class="card-title">${escapeHtml(art.title)}</h3>
            ${isOp ? `
              <div class="opinion-badge-bar">
                <i class="fa-solid fa-pen-nib"></i> Open Journalist Perspective (Non-Endorsement)
              </div>
            ` : ''}
            <p class="card-snippet">${escapeHtml(art.summary || 'No preview snippet available.')}</p>
            
            <div style="margin-bottom: 1rem; display: flex; align-items: center; gap: 0.4rem;">
              <span style="font-size: 0.75rem; color: var(--text-dim); margin-right: 0.2rem;">Share:</span>
              <a href="${share.twitter}" target="_blank" rel="noopener" class="btn-social-icon twitter" title="Share to X/Twitter"><i class="fa-brands fa-x-twitter"></i></a>
              <a href="${share.telegram}" target="_blank" rel="noopener" class="btn-social-icon telegram" title="Share to Telegram"><i class="fa-brands fa-telegram"></i></a>
              <a href="${share.whatsapp}" target="_blank" rel="noopener" class="btn-social-icon whatsapp" title="Share to WhatsApp"><i class="fa-brands fa-whatsapp"></i></a>
              <a href="${share.linkedin}" target="_blank" rel="noopener" class="btn-social-icon linkedin" title="Share to LinkedIn"><i class="fa-brands fa-linkedin-in"></i></a>
              <a href="${share.facebook}" target="_blank" rel="noopener" class="btn-social-icon facebook" title="Share to Facebook"><i class="fa-brands fa-facebook-f"></i></a>
            </div>

            <div class="card-footer">
              <button class="btn btn-secondary btn-sm" onclick="openArticleModal(${art.id})">
                <i class="fa-solid ${hasVid ? 'fa-circle-play' : 'fa-expand'}"></i> ${hasVid ? 'Watch Video' : 'Quick View'}
              </button>
              <a href="${art.link}" target="_blank" rel="noopener noreferrer" class="card-link">
                Read Source <i class="fa-solid fa-arrow-up-right-from-square"></i>
              </a>
            </div>
          </div>
        </article>
      `;
    }).join('');
  }

  // Fetch Latest News Trigger
  async function triggerFetch() {
    btnFetchNews.disabled = true;
    syncIcon.classList.add('fa-spin');
    showToast('Syncing latest news, videos, and opinion feeds...', 'info');

    try {
      const res = await fetch('/api/fetch', { method: 'POST' });
      const data = await res.json();

      if (data.status === 'success') {
        showToast(`Sync complete! ${data.report.total_new_inserted} new articles added.`, 'success');
        fetchStats();
        fetchArticles();
      } else {
        showToast(`Sync error: ${data.message}`, 'error');
      }
    } catch (err) {
      showToast('Failed to trigger news collection.', 'error');
    } finally {
      btnFetchNews.disabled = false;
      syncIcon.classList.remove('fa-spin');
    }
  }

  // Open Article Detail Modal
  window.openArticleModal = async function(articleId) {
    articleModal.classList.add('active');
    modalBody.innerHTML = `
      <div class="loading-state">
        <div class="spinner"></div>
        <p>Loading details...</p>
      </div>
    `;

    try {
      const res = await fetch(`/api/articles/${articleId}?full=true`);
      const data = await res.json();

      if (data.status === 'success') {
        const art = data.article;
        const isOp = art.is_opinion || art.category === 'Journalist Opinion';
        const hasVid = art.has_video || art.video_url || art.category === 'Video News';
        const links = art.share_links || getShareUrls(art.title, art.link);

        let videoEmbedHtml = '';
        if (art.video_url) {
          if (art.video_url.includes('youtube.com') || art.video_url.includes('vimeo.com') || art.video_url.includes('dailymotion.com')) {
            videoEmbedHtml = `
              <div class="video-responsive-container">
                <iframe src="${art.video_url}" allowfullscreen allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"></iframe>
              </div>
            `;
          } else if (art.video_url.endsWith('.mp4')) {
            videoEmbedHtml = `
              <div class="video-responsive-container">
                <video controls src="${art.video_url}"></video>
              </div>
            `;
          }
        }

        modalBody.innerHTML = `
          <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;">
            <span class="source-tag ${hasVid ? 'video' : (isOp ? 'opinion' : getSourceClass(art.source_name))}">
              ${hasVid ? '<i class="fa-solid fa-video"></i> VIDEO REPORT' : (isOp ? 'JOURNALIST OPINION' : escapeHtml(art.source_name))}
            </span>
            <span class="card-time">${formatRelativeTime(art.published_at || art.scraped_at)}</span>
          </div>

          <h2 style="font-family: 'Outfit'; font-size: 1.5rem; margin-bottom: 1rem; color: #fff;">${escapeHtml(art.title)}</h2>

          ${isOp ? `
            <div style="background: rgba(245, 158, 11, 0.12); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 8px; padding: 0.75rem; font-size: 0.85rem; color: #fde68a; margin-bottom: 1.25rem;">
              <i class="fa-solid fa-triangle-exclamation"></i> <strong>Open Opinion Notice:</strong> Expresses individual journalist commentary for public discussion. Does not constitute an endorsement.
            </div>
          ` : ''}

          ${videoEmbedHtml ? videoEmbedHtml : (art.image_url ? `<img src="${art.image_url}" style="width: 100%; max-height: 300px; object-fit: cover; border-radius: 12px; margin-bottom: 1.5rem;">` : '')}

          <div style="line-height: 1.8; color: var(--text-muted); font-size: 1rem; margin-bottom: 2rem;">
            ${escapeHtml(art.content || art.summary).replace(/\n/g, '<br><br>')}
          </div>

          <div style="border-top: 1px solid var(--border-color); padding-top: 1.25rem; margin-bottom: 1.5rem;">
            <h4 style="font-size: 0.9rem; color: var(--text-main); margin-bottom: 0.75rem;"><i class="fa-solid fa-share-nodes"></i> Broadcast / Share to Social & X:</h4>
            <div style="display: flex; gap: 0.6rem; flex-wrap: wrap;">
              <a href="${links.twitter}" target="_blank" rel="noopener" class="btn btn-secondary btn-sm"><i class="fa-brands fa-x-twitter"></i> Post to X</a>
              <a href="${links.telegram}" target="_blank" rel="noopener" class="btn btn-secondary btn-sm"><i class="fa-brands fa-telegram"></i> Telegram</a>
              <a href="${links.whatsapp}" target="_blank" rel="noopener" class="btn btn-secondary btn-sm"><i class="fa-brands fa-whatsapp"></i> WhatsApp</a>
              <a href="${links.linkedin}" target="_blank" rel="noopener" class="btn btn-secondary btn-sm"><i class="fa-brands fa-linkedin-in"></i> LinkedIn</a>
              <a href="${links.facebook}" target="_blank" rel="noopener" class="btn btn-secondary btn-sm"><i class="fa-brands fa-facebook"></i> Facebook</a>
              <button class="btn btn-primary btn-sm" onclick="broadcastToSocial(${art.id})"><i class="fa-solid fa-paper-plane"></i> Auto-Post API</button>
            </div>
          </div>

          <div style="display: flex; gap: 1rem;">
            <a href="${art.link}" target="_blank" rel="noopener" class="btn btn-primary">
              <i class="fa-solid fa-external-link"></i> Open Original News Article / Video Link
            </a>
          </div>
        `;
      }
    } catch (err) {
      modalBody.innerHTML = `<p>Error loading details.</p>`;
    }
  };

  // Broadcast via API
  window.broadcastToSocial = async function(articleId) {
    showToast('Dispatching post to configured social webhooks & X API...', 'info');
    try {
      const res = await fetch('/api/social/post', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ article_id: articleId })
      });
      const data = await res.json();
      if (data.status === 'success') {
        showToast('Broadcast command completed successfully!', 'success');
        fetchStats();
      } else {
        showToast(`Broadcast failed: ${data.message}`, 'error');
      }
    } catch (err) {
      showToast('Error broadcasting article.', 'error');
    }
  };

  // Social Config Modal Functions
  async function openConfigModal() {
    configModal.classList.add('active');
    try {
      const res = await fetch('/api/social/config');
      const data = await res.json();
      if (data.status === 'success') {
        const cfg = data.config;
        document.getElementById('cfg-tw-key').value = cfg.twitter?.api_key || '';
        document.getElementById('cfg-tw-secret').value = cfg.twitter?.api_secret || '';
        document.getElementById('cfg-tw-token').value = cfg.twitter?.access_token || '';
        document.getElementById('cfg-tw-toksecret').value = cfg.twitter?.access_token_secret || '';

        document.getElementById('cfg-hashtags').value = cfg.hashtags || '#Pakistan #PakistanNews';
        document.getElementById('cfg-tg-token').value = cfg.telegram?.bot_token || '';
        document.getElementById('cfg-tg-chat').value = cfg.telegram?.chat_id || '';
        document.getElementById('cfg-discord-url').value = cfg.discord?.webhook_url || '';
        document.getElementById('cfg-slack-url').value = cfg.slack?.webhook_url || '';
      }
    } catch (err) {
      console.error('Error loading social config:', err);
    }
  }

  async function saveSocialConfig(e) {
    e.preventDefault();
    const configData = {
      hashtags: document.getElementById('cfg-hashtags').value.trim(),
      twitter: {
        enabled: !!(document.getElementById('cfg-tw-key').value.trim() && document.getElementById('cfg-tw-token').value.trim()),
        api_key: document.getElementById('cfg-tw-key').value.trim(),
        api_secret: document.getElementById('cfg-tw-secret').value.trim(),
        access_token: document.getElementById('cfg-tw-token').value.trim(),
        access_token_secret: document.getElementById('cfg-tw-toksecret').value.trim()
      },
      telegram: {
        enabled: !!document.getElementById('cfg-tg-token').value.trim(),
        bot_token: document.getElementById('cfg-tg-token').value.trim(),
        chat_id: document.getElementById('cfg-tg-chat').value.trim()
      },
      discord: {
        enabled: !!document.getElementById('cfg-discord-url').value.trim(),
        webhook_url: document.getElementById('cfg-discord-url').value.trim()
      },
      slack: {
        enabled: !!document.getElementById('cfg-slack-url').value.trim(),
        webhook_url: document.getElementById('cfg-slack-url').value.trim()
      }
    };

    try {
      const res = await fetch('/api/social/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(configData)
      });
      const result = await res.json();
      if (result.status === 'success') {
        showToast('Social media & X API credentials saved!', 'success');
        configModal.classList.remove('active');
        fetchStats();
      } else {
        showToast('Failed to save configuration.', 'error');
      }
    } catch (err) {
      showToast('Error saving settings.', 'error');
    }
  }

  function closeModal() {
    articleModal.classList.remove('active');
  }

  // Toast System
  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast`;
    const icon = type === 'success' ? 'fa-circle-check' : (type === 'error' ? 'fa-circle-exclamation' : 'fa-circle-info');
    toast.innerHTML = `<i class="fa-solid ${icon}" style="color: var(--primary);"></i> <span>${escapeHtml(message)}</span>`;
    toastContainer.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
  }

  // Share URL Generator
  function getShareUrls(title, link) {
    const text = encodeURIComponent(title + "\n#Pakistan #PakistanNews");
    const url = encodeURIComponent(link);

    return {
      twitter: `https://twitter.com/intent/tweet?text=${text}&url=${url}`,
      telegram: `https://t.me/share/url?url=${url}&text=${text}`,
      whatsapp: `https://api.whatsapp.com/send?text=${text}%20${url}`,
      linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${url}`,
      facebook: `https://www.facebook.com/sharer/sharer.php?u=${url}`
    };
  }

  // Utilities
  function getSourceClass(name) {
    if (name.includes('Dawn')) return 'dawn';
    if (name.includes('Tribune')) return 'tribune';
    if (name.includes('Geo')) return 'geo';
    return '';
  }

  function getFallbackImage(name) {
    return 'https://images.unsplash.com/photo-1585829365295-ab7cd400c167?w=600&auto=format&fit=crop&q=60';
  }

  function formatRelativeTime(dateStr) {
    if (!dateStr) return 'Recently';
    const date = new Date(dateStr);
    if (isNaN(date)) return dateStr;

    const seconds = Math.floor((new Date() - date) / 1000);
    if (seconds < 60) return 'Just now';
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
  }
});
