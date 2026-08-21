// Pakistan News Hub - Static Client Application Logic

document.addEventListener('DOMContentLoaded', () => {
  let currentSource = 'All';
  let isOpinionOnly = null;
  let isVideoOnly = null;
  let searchQuery = '';
  let searchTimeout = null;
  let allArticles = [];

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
  const statOpinionArticles = document.getElementById('stat-opinion-articles');
  const statVideoArticles = document.getElementById('stat-video-articles');
  const statPostedTwitter = document.getElementById('stat-posted-twitter');

  // Initialize
  fetchStaticDatabase();

  // Event Listeners
  searchInput.addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    searchQuery = e.target.value.trim().toLowerCase();
    searchTimeout = setTimeout(() => {
      filterAndRenderArticles();
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
      filterAndRenderArticles();
    }
  });

  btnFetchNews.addEventListener('click', () => {
    showToast('GitHub Actions handles fetching automatically in the cloud every 15 minutes!', 'info');
  });
  btnSocialConfig.addEventListener('click', () => {
    showToast('Social Config must be set via GitHub Secrets (Settings > Secrets > Actions) in the static version!', 'info');
  });

  modalCloseBtn.addEventListener('click', closeModal);
  articleModal.addEventListener('click', (e) => {
    if (e.target === articleModal) closeModal();
  });
  configModal.addEventListener('click', (e) => {
    if (e.target === configModal) configModal.classList.remove('active');
  });

  // Fetch Static Database JSON
  async function fetchStaticDatabase() {
    newsGrid.innerHTML = `
      <div class="loading-state">
        <div class="spinner"></div>
        <p>Loading latest news database...</p>
      </div>
    `;
    try {
      // Add timestamp to prevent caching
      const res = await fetch(`static/latest_news.json?t=${new Date().getTime()}`);
      if (!res.ok) {
        throw new Error('JSON not found');
      }
      allArticles = await res.json();
      calculateStats();
      filterAndRenderArticles();
    } catch (err) {
      console.error('Error loading static database:', err);
      newsGrid.innerHTML = `
        <div class="empty-state">
          <i class="fa-solid fa-triangle-exclamation" style="font-size: 3rem; color: var(--accent-red); margin-bottom: 1rem;"></i>
          <h3>Database Not Found</h3>
          <p style="margin-top: 0.5rem;">The GitHub Cloud Watcher hasn't generated the static database yet. It will appear within 15 minutes!</p>
        </div>
      `;
    }
  }

  function calculateStats() {
    statTotalArticles.textContent = allArticles.length.toLocaleString();
    let opinions = 0;
    let videos = 0;
    let postedTwitter = 0;

    allArticles.forEach(a => {
      if (a.is_opinion == 1) opinions++;
      if (a.has_video == 1) videos++;
      if (a.posted_twitter == 1) postedTwitter++;
    });

    statOpinionArticles.textContent = opinions.toLocaleString();
    statVideoArticles.textContent = videos.toLocaleString();
    if (statPostedTwitter) statPostedTwitter.textContent = postedTwitter.toLocaleString();
  }

  function filterAndRenderArticles() {
    let filtered = allArticles;

    if (currentSource && currentSource !== 'All') {
      filtered = filtered.filter(a => a.source_name === currentSource);
    }
    if (isOpinionOnly) {
      filtered = filtered.filter(a => a.is_opinion == 1);
    }
    if (isVideoOnly) {
      filtered = filtered.filter(a => a.has_video == 1);
    }
    if (searchQuery) {
      filtered = filtered.filter(a => 
        (a.title && a.title.toLowerCase().includes(searchQuery)) || 
        (a.summary && a.summary.toLowerCase().includes(searchQuery))
      );
    }

    // Limit to 40 items for performance
    const limit = 40;
    renderArticles(filtered.slice(0, limit));
  }

  // Render Articles Grid
  function renderArticles(articles) {
    if (!articles || articles.length === 0) {
      newsGrid.innerHTML = `
        <div class="empty-state">
          <i class="fa-solid fa-newspaper" style="font-size: 3rem; color: var(--text-dim); margin-bottom: 1rem;"></i>
          <h3>No Items Found</h3>
          <p style="margin-top: 0.5rem;">Try adjusting your filters.</p>
        </div>
      `;
      return;
    }

    newsGrid.innerHTML = articles.map(art => {
      const isOp = art.is_opinion == 1;
      const hasVid = art.has_video == 1;
      
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
              <a href="${share.twitter}" target="_blank" rel="noopener" class="btn-social-icon twitter"><i class="fa-brands fa-x-twitter"></i></a>
              <a href="${share.whatsapp}" target="_blank" rel="noopener" class="btn-social-icon whatsapp"><i class="fa-brands fa-whatsapp"></i></a>
              <a href="${share.facebook}" target="_blank" rel="noopener" class="btn-social-icon facebook"><i class="fa-brands fa-facebook-f"></i></a>
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

  // Open Article Detail Modal
  window.openArticleModal = function(articleId) {
    const art = allArticles.find(a => a.id === articleId);
    if (!art) return;

    articleModal.classList.add('active');
    
    const isOp = art.is_opinion == 1;
    const hasVid = art.has_video == 1;
    const links = getShareUrls(art.title, art.link);

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

      <div style="display: flex; gap: 1rem;">
        <a href="${art.link}" target="_blank" rel="noopener" class="btn btn-primary">
          <i class="fa-solid fa-external-link"></i> Open Original News Article / Video Link
        </a>
      </div>
    `;
  };

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
      whatsapp: `https://api.whatsapp.com/send?text=${text}%20${url}`,
      facebook: `https://www.facebook.com/sharer/sharer.php?u=${url}`
    };
  }

  // Utilities
  function getSourceClass(name) {
    if (!name) return '';
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
