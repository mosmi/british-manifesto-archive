/* ============================================================
   THE BRITISH MANIFESTO ARCHIVE — App
   History API SPA routing + page rendering
   ============================================================ */

const SITE = {
  name: 'The British Manifesto Archive',
  domain: 'www.manifestos.org.uk',
  url: 'https://www.manifestos.org.uk',
  description: 'A comprehensive digital archive of UK general election manifestos from 1945 to 2024. Browse party manifestos, election results, and constituency maps.',
  ogImage: 'https://www.manifestos.org.uk/og-image.jpg',
  ogImageWidth: 1024,
  ogImageHeight: 537,
  ogImageAlt: 'The British Manifesto Archive — a digital repository of UK political party manifestos',
};

const ASSETS_VERSION = '20260615';

// Manifesto text without a PDF scan (electionId/partyId)
const MANIFESTO_TEXT_ONLY = new Set([
  '2001/omrlp',
  '2005/omrlp',
  '2015/omrlp',
]);

function hasManifestoPdf(electionId, partyId) {
  return !MANIFESTO_TEXT_ONLY.has(`${electionId}/${partyId}`);
}

let MANIFESTO_ARCHIVE = null;

async function initManifestoArchive() {
  try {
    const items = await fetchTyped('/data/manifestos-index.json', 'json');
    MANIFESTO_ARCHIVE = new Set(items.map(i => `${i.electionId}/${i.partyId}`));
  } catch {
    MANIFESTO_ARCHIVE = new Set();
  }
}

function hasManifestoContent(electionId, partyId) {
  return hasManifestoPdf(electionId, partyId)
    || MANIFESTO_TEXT_ONLY.has(`${electionId}/${partyId}`)
    || (MANIFESTO_ARCHIVE?.has(`${electionId}/${partyId}`) ?? false);
}

// Not shown in election-page manifesto lists (no manifestos published)
const MANIFESTO_EXCLUDED_PARTIES = new Set(['speaker', 'independent']);

function setPageTitle(pageTitle) {
  document.title = pageTitle
    ? `${pageTitle} — ${SITE.domain}`
    : `${SITE.name} — ${SITE.domain}`;
}

function setOgImage(show) {
  const ids = ['og-image', 'og-image-width', 'og-image-height', 'og-image-alt', 'twitter-image'];
  const twitterCard = document.getElementById('twitter-card');

  if (show) {
    const ensureMeta = (id, attr, key, value) => {
      let el = document.getElementById(id);
      if (!el) {
        el = document.createElement('meta');
        el.id = id;
        el.setAttribute(attr, key);
        document.head.appendChild(el);
      }
      el.setAttribute('content', value);
    };
    ensureMeta('og-image', 'property', 'og:image', SITE.ogImage);
    ensureMeta('og-image-width', 'property', 'og:image:width', String(SITE.ogImageWidth));
    ensureMeta('og-image-height', 'property', 'og:image:height', String(SITE.ogImageHeight));
    ensureMeta('og-image-alt', 'property', 'og:image:alt', SITE.ogImageAlt);
    ensureMeta('twitter-image', 'name', 'twitter:image', SITE.ogImage);
    if (twitterCard) twitterCard.setAttribute('content', 'summary_large_image');
  } else {
    ids.forEach(id => document.getElementById(id)?.remove());
    if (twitterCard) twitterCard.setAttribute('content', 'summary');
  }
}

function setPageMeta({ title, description, path = '/', noindex = false } = {}) {
  const pageTitle = title
    ? `${title} — ${SITE.domain}`
    : `${SITE.name} — ${SITE.domain}`;
  const pageDescription = description || SITE.description;
  const canonical = path === '/' ? `${SITE.url}/` : `${SITE.url}${path}`;

  setPageTitle(title);

  const desc = document.getElementById('meta-description');
  if (desc) desc.setAttribute('content', pageDescription);

  const ogTitle = document.getElementById('og-title');
  if (ogTitle) ogTitle.setAttribute('content', pageTitle);

  const ogDesc = document.getElementById('og-description');
  if (ogDesc) ogDesc.setAttribute('content', pageDescription);

  const ogUrl = document.getElementById('og-url');
  if (ogUrl) ogUrl.setAttribute('content', canonical);

  const canonicalEl = document.getElementById('canonical-link');
  if (canonicalEl) canonicalEl.setAttribute('href', canonical);

  const twitterTitle = document.getElementById('twitter-title');
  if (twitterTitle) twitterTitle.setAttribute('content', pageTitle);

  const twitterDesc = document.getElementById('twitter-description');
  if (twitterDesc) twitterDesc.setAttribute('content', pageDescription);

  setOgImage(path === '/');

  let robotsMeta = document.getElementById('meta-robots');
  if (noindex) {
    if (!robotsMeta) {
      robotsMeta = document.createElement('meta');
      robotsMeta.id = 'meta-robots';
      robotsMeta.name = 'robots';
      document.head.appendChild(robotsMeta);
    }
    robotsMeta.setAttribute('content', 'noindex');
  } else if (robotsMeta) {
    robotsMeta.remove();
  }
}

const HOVER_FINE = window.matchMedia('(hover: hover) and (pointer: fine)');
let _openNavMenu = null;

function closeAllNavMenus(returnFocusTo = null) {
  document.querySelectorAll('.dropdown-menu.is-open, .dropdown-mega.is-open').forEach(menu => {
    menu.classList.remove('is-open');
    menu.setAttribute('aria-hidden', 'true');
    menu.inert = true;
  });
  document.querySelectorAll('.nav-dropdown .nav-btn[aria-expanded="true"]').forEach(btn => {
    btn.setAttribute('aria-expanded', 'false');
  });
  _openNavMenu = null;
  if (returnFocusTo) returnFocusTo.focus();
}

function closeMobileMenu() {
  const links = document.getElementById('nav-links');
  const btn = document.getElementById('mobile-menu-btn');
  if (links) links.classList.remove('open');
  if (btn) btn.setAttribute('aria-expanded', 'false');
}

function setupNavMenu(dropdown, button, menu) {
  if (!dropdown || !button || !menu) return;
  let hideTimer;

  const show = () => {
    clearTimeout(hideTimer);
    if (_openNavMenu && _openNavMenu.menu !== menu) {
      closeAllNavMenus();
    }
    menu.classList.add('is-open');
    menu.setAttribute('aria-hidden', 'false');
    menu.inert = false;
    button.setAttribute('aria-expanded', 'true');
    _openNavMenu = { dropdown, button, menu };
  };

  const hide = (returnFocus = false) => {
    hideTimer = setTimeout(() => {
      menu.classList.remove('is-open');
      menu.setAttribute('aria-hidden', 'true');
      menu.inert = true;
      button.setAttribute('aria-expanded', 'false');
      if (_openNavMenu?.menu === menu) _openNavMenu = null;
      if (returnFocus) button.focus();
    }, 150);
  };

  const toggle = () => {
    const isOpen = menu.classList.contains('is-open');
    if (isOpen) hide(true);
    else show();
  };

  button.addEventListener('click', e => {
    const href = button.getAttribute('href');
    if (href && HOVER_FINE.matches) {
      return;
    }
    e.preventDefault();
    toggle();
  });

  button.addEventListener('keydown', e => {
    if (e.key === 'Escape' && menu.classList.contains('is-open')) {
      e.preventDefault();
      clearTimeout(hideTimer);
      hide(true);
    }
  });

  if (HOVER_FINE.matches) {
    dropdown.addEventListener('mouseenter', show);
    dropdown.addEventListener('mouseleave', () => hide(false));
    menu.addEventListener('mouseenter', show);
    menu.addEventListener('mouseleave', () => hide(false));
  }

  dropdown.addEventListener('focusout', e => {
    if (!dropdown.contains(e.relatedTarget)) hide(false);
  });

  menu.addEventListener('click', e => {
    if (e.target.closest('a')) {
      clearTimeout(hideTimer);
      closeAllNavMenus();
    }
  });
}

document.addEventListener('click', e => {
  if (_openNavMenu && !_openNavMenu.dropdown.contains(e.target)) {
    closeAllNavMenus();
  }
});

document.addEventListener('keydown', e => {
  if (e.key === 'Escape' && _openNavMenu) {
    const btn = _openNavMenu.button;
    closeAllNavMenus(btn);
  }
});

document.addEventListener('DOMContentLoaded', async () => {
  await initManifestoArchive();
  buildNav();
  setupMobileMenu();
  setupNavDropdowns();
  setupSearch();
  setupRouter();
  route();
});

// ── Router ────────────────────────────────────────────────────
function getPath() {
  let path = window.location.pathname || '/';
  if (path.length > 1 && path.endsWith('/')) path = path.slice(0, -1);
  return path || '/';
}

function navigate(path, { replace = false } = {}) {
  const normalized = path.startsWith('/') ? path : `/${path}`;
  if (replace) {
    history.replaceState(null, '', normalized);
  } else if (getPath() !== normalized) {
    history.pushState(null, '', normalized);
  }
  closeAllNavMenus();
  closeMobileMenu();
  route();
}

function migrateHashRoute() {
  const hash = window.location.hash;
  if (hash.startsWith('#/')) {
    const path = hash.slice(1) || '/';
    history.replaceState(null, '', path);
    window.location.hash = '';
  }
}

function setupRouter() {
  migrateHashRoute();

  document.addEventListener('click', e => {
    const a = e.target.closest('a[href]');
    if (!a) return;
    const href = a.getAttribute('href');
    if (!href) return;

    if (href.startsWith('#/')) {
      e.preventDefault();
      navigate(href.slice(1));
      return;
    }

    if (!href.startsWith('/') || a.target === '_blank') return;
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    if (a.origin && a.origin !== window.location.origin) return;

    e.preventDefault();
    navigate(href);
  });

  window.addEventListener('popstate', route);
}

function route() {
  const path = getPath();
  const app  = document.getElementById('app');
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));

  if (path === '/') {
    renderHome(app);
  } else if (path.startsWith('/election/')) {
    renderElection(app, path.replace('/election/', ''));
  } else if (path.startsWith('/party/')) {
    renderParty(app, path.replace('/party/', ''));
  } else if (path.startsWith('/nation/')) {
    renderNation(app, path.replace('/nation/', ''));
  } else if (path.startsWith('/devolved/london/')) {
    renderLondonElection(app, path.replace('/devolved/london/', ''));
  } else if (path === '/devolved/london') {
    renderLondonPortal(app);
  } else if (path === '/devolved/holyrood/other-parties') {
    renderHolyroodOtherParties(app);
  } else if (path.startsWith('/devolved/holyrood/')) {
    renderHolyroodElection(app, path.replace('/devolved/holyrood/', ''));
  } else if (path === '/devolved/holyrood') {
    renderHolyroodPortal(app);
  } else if (path === '/devolved/senedd/other-parties') {
    renderSeneddOtherParties(app);
  } else if (path.startsWith('/devolved/senedd/')) {
    renderSeneddElection(app, path.replace('/devolved/senedd/', ''));
  } else if (path === '/devolved/senedd') {
    renderSeneddPortal(app);
  } else if (path === '/devolved/stormont/other-parties') {
    renderNIOtherParties(app);
  } else if (path.startsWith('/devolved/stormont/')) {
    renderNIElection(app, path.replace('/devolved/stormont/', ''));
  } else if (path === '/devolved/stormont') {
    renderNIPortal(app);
  } else if (path.startsWith('/devolved/')) {
    renderDevolved(app, path.replace('/devolved/', ''));
  } else if (path === '/others') {
    renderOthers(app);
  } else if (path.startsWith('/manifesto/')) {
    const parts = path.split('/').filter(Boolean);
    renderManifesto(app, parts[1], parts[2]);
  } else if (path === '/elections') {
    renderElectionsHub(app);
  } else if (path === '/devolved') {
    renderDevolvedHub(app);
  } else if (path === '/parties') {
    renderPartiesHub(app);
  } else if (path === '/nations') {
    renderNationsHub(app);
  } else if (path === '/about') {
    renderAbout(app);
  } else {
    renderNotFound(app);
  }
  window.scrollTo({ top: 0, behavior: 'instant' });
}

// ── Shared UI helpers ─────────────────────────────────────────
function renderBreadcrumb(items) {
  const crumbs = items.map((item, i) => {
    const isLast = i === items.length - 1;
    if (isLast || !item.href) {
      return `<span class="breadcrumb-current">${item.label}</span>`;
    }
    return `<a href="${item.href}" class="breadcrumb-link">${item.label}</a>`;
  }).join('');
  return `<nav class="breadcrumb" aria-label="Breadcrumb">${crumbs}</nav>`;
}

function partyLink(id, label, year) {
  const name = label || getPartyName(id, year);
  if (!id || id === 'others' || !PARTIES[id]) return name;
  return `<a href="/party/${id}" class="inline-party-link">${name}</a>`;
}

function nationLink(id, label) {
  if (!NATIONS[id]) return label;
  return `<a href="/nation/${id}" class="inline-nation-link">${label}</a>`;
}

// ── Navigation ────────────────────────────────────────────────
function buildNav() {
  buildElectionsDropdown();
  buildDevolvedDropdown();
  buildPartiesMega();
}

function buildDevolvedDropdown() {
  const el = document.getElementById('devolved-dropdown');
  if (!el || typeof DEVOLVED_PORTALS === 'undefined') return;
  Object.values(DEVOLVED_PORTALS).forEach(portal => {
    const a = document.createElement('a');
    a.href = `/devolved/${portal.id}`;
    a.innerHTML = `<strong>${portal.label}</strong><span class="dropdown-sub">${portal.subtitle}</span>`;
    el.appendChild(a);
  });
}

function setupNavDropdowns() {
  document.querySelectorAll('#nav-desktop-only .nav-dropdown').forEach(dropdown => {
    const button = dropdown.querySelector('.nav-btn');
    const menu = dropdown.querySelector('.dropdown-menu, .dropdown-mega');
    if (menu) {
      menu.setAttribute('aria-hidden', 'true');
      menu.inert = true;
    }
    setupNavMenu(dropdown, button, menu);
  });
}

function buildElectionsDropdown() {
  const el = document.getElementById('elections-dropdown');
  const decades = {};
  ELECTIONS.forEach(e => {
    const dec = Math.floor(e.year / 10) * 10;
    if (!decades[dec]) decades[dec] = [];
    decades[dec].push(e);
  });
  Object.keys(decades).sort().forEach(dec => {
    const label = document.createElement('span');
    label.className = 'dropdown-section-label';
    label.textContent = `${dec}s`;
    el.appendChild(label);
    decades[dec].forEach(e => {
      const a = document.createElement('a');
      a.href = `/election/${e.id}`;
      a.textContent = `${e.displayYear} — ${PARTIES[e.winner]?.shortName || ''}`;
      el.appendChild(a);
    });
  });
}

function buildPartiesMega() {
  const mega = document.getElementById('parties-mega');
  if (!mega) return;

  // Nation columns
  Object.entries(NAV_PARTIES).forEach(([nationId, nation]) => {
    const col = document.createElement('div');
    col.className = 'mega-col';
    const heading = document.createElement('a');
    heading.href = `/nation/${nationId}`;
    heading.className = 'mega-nation-heading';
    heading.textContent = nation.label;
    col.appendChild(heading);
    nation.parties.forEach(pid => {
      const p = PARTIES[pid];
      if (!p) return;
      const a = document.createElement('a');
      a.href = `/party/${pid}`;
      a.className = 'mega-party-link';
      const dot = document.createElement('span');
      dot.className = 'mega-dot';
      dot.style.background = p.color;
      a.appendChild(dot);
      a.appendChild(document.createTextNode(p.shortName));
      col.appendChild(a);
    });
    if (nationId === 'scotland') {
      const scottishOthers = document.createElement('a');
      scottishOthers.href = '/devolved/holyrood/other-parties';
      scottishOthers.className = 'mega-all-link';
      scottishOthers.textContent = 'Other Scottish parties →';
      col.appendChild(scottishOthers);
    }
    if (nationId === 'wales') {
      const welshOthers = document.createElement('a');
      welshOthers.href = '/devolved/senedd/other-parties';
      welshOthers.className = 'mega-all-link';
      welshOthers.textContent = 'Other Welsh parties →';
      col.appendChild(welshOthers);
    }
    if (nationId === 'northern-ireland') {
      const niOthers = document.createElement('a');
      niOthers.href = '/devolved/stormont/other-parties';
      niOthers.className = 'mega-all-link';
      niOthers.textContent = 'Other NI parties →';
      col.appendChild(niOthers);
    }
    mega.appendChild(col);
  });

  // Others column — featured parties + link to full list
  const othersCol = document.createElement('div');
  othersCol.className = 'mega-col';
  const othersHeading = document.createElement('a');
  othersHeading.href = '/others';
  othersHeading.className = 'mega-nation-heading';
  othersHeading.textContent = 'Others';
  othersCol.appendChild(othersHeading);
  const featured = typeof OTHERS_FEATURED !== 'undefined' ? OTHERS_FEATURED : OTHERS_PARTIES.slice(0, 6);
  const sortedFeatured = [...featured].sort((a, b) => {
    const nameA = PARTIES[a]?.shortName || '';
    const nameB = PARTIES[b]?.shortName || '';
    return nameA.localeCompare(nameB, 'en-GB');
  });
  sortedFeatured.forEach(pid => {
    const p = PARTIES[pid];
    if (!p) return;
    const a = document.createElement('a');
    a.href = `/party/${pid}`;
    a.className = 'mega-party-link';
    const dot = document.createElement('span');
    dot.className = 'mega-dot';
    dot.style.background = p.color;
    a.appendChild(dot);
    a.appendChild(document.createTextNode(p.shortName));
    othersCol.appendChild(a);
  });
  const allOthers = document.createElement('a');
  allOthers.href = '/others';
  allOthers.className = 'mega-all-link';
  allOthers.textContent = 'All other parties →';
  othersCol.appendChild(allOthers);
  mega.appendChild(othersCol);
}

function setupMobileMenu() {
  const btn = document.getElementById('mobile-menu-btn');
  const links = document.getElementById('nav-links');
  if (!btn || !links) return;

  btn.setAttribute('aria-expanded', 'false');
  btn.addEventListener('click', () => {
    const open = links.classList.toggle('open');
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
  });

  btn.addEventListener('keydown', e => {
    if (e.key === 'Escape' && links.classList.contains('open')) {
      closeMobileMenu();
      btn.focus();
    }
  });
}

// ── HOME ──────────────────────────────────────────────────────
let _homeElectionIndex = null;

function renderHome(app) {
  setPageMeta({ path: '/' });
  _homeElectionIndex = ELECTIONS.length - 1;

  app.innerHTML = `
    <section class="home-dashboard" id="home-dashboard">
      <div class="home-dashboard-bg" id="home-dashboard-bg"></div>
      <div class="home-dashboard-inner">
        <header class="home-dashboard-header">
          <h1 class="hero-title">The British<br><em>Manifesto Archive</em></h1>
          <p class="hero-subtitle">Digital repository of UK political history — manifesto documents, electoral results, and campaign records for every post-war election.</p>
          <div class="hero-stats">
            <div><div class="hero-stat-num">62</div><div class="hero-stat-label">Elections</div></div>
            <div><div class="hero-stat-num">${Object.keys(PARTIES).filter(k => k !== 'others').length}</div><div class="hero-stat-label">Parties</div></div>
            <div><div class="hero-stat-num">650</div><div class="hero-stat-label">Commons Seats</div></div>
            <div><div class="hero-stat-num">4</div><div class="hero-stat-label">Nations</div></div>
          </div>
        </header>

        <div class="dashboard-layout">
          <div class="dashboard-main-col">
            <div class="dashboard-parliament-card">
              <div class="dashboard-parliament-head">
                <div>
                  <div class="dashboard-election-label" id="dashboard-election-label"></div>
                  <div class="dashboard-election-meta" id="dashboard-election-meta"></div>
                </div>
                <a href="#" class="dashboard-election-link" id="dashboard-election-link">View election →</a>
              </div>
              <div id="home-parliament-chart" class="home-parliament-chart"></div>
              <div class="share-bar" id="home-share-bar"></div>
              <div class="share-labels" id="home-share-labels"></div>
            </div>

            <div class="election-slider-panel">
              <div class="slider-legend" id="home-slider-legend"></div>
              <div class="slider-wrap">
                <button type="button" class="slider-step-btn" id="slider-prev" aria-label="Previous election">◀</button>
                <input type="range" class="election-slider" id="election-slider" min="0" max="${ELECTIONS.length - 1}" value="${_homeElectionIndex}" aria-label="Select general election year">
                <button type="button" class="slider-step-btn" id="slider-next" aria-label="Next election">▶</button>
              </div>
              <div class="slider-ticks" id="slider-ticks"></div>
            </div>
          </div>

          <aside class="dashboard-sidebar" id="dashboard-sidebar" aria-label="Election timeline"></aside>
        </div>
      </div>
    </section>

    <section class="latest-section">
      <div class="latest-header">
        <div>
          <span class="section-label">Archive</span>
          <h2>Latest Additions</h2>
          <div class="gold-rule"></div>
        </div>
        <div class="carousel-controls">
          <button type="button" class="carousel-btn" id="latest-prev" aria-label="Previous">◀</button>
          <button type="button" class="carousel-btn" id="latest-next" aria-label="Next">▶</button>
        </div>
      </div>
      <div class="latest-track-wrap">
        <div class="latest-track" id="latest-track">
          <div class="latest-loading">Loading manifestos…</div>
        </div>
      </div>
    </section>

    <section class="timeline-section">
      <div class="timeline-header">
        <div>
          <span class="section-label">All General Elections</span>
          <h2>The Electoral Record</h2>
          <div class="gold-rule"></div>
        </div>
        <div class="timeline-filter">
          <button class="filter-btn active" data-filter="all">All</button>
          <button class="filter-btn" data-filter="labour">Labour</button>
          <button class="filter-btn" data-filter="conservative">Conservative</button>
        </div>
      </div>
      <div class="timeline-grid" id="timeline-grid"></div>
    </section>

    <section class="browse-section nations-browse-section">
      <div class="browse-section-inner">
        <div class="browse-section-header">
          <span class="section-label">United Kingdom</span>
          <h2>Browse by Nation</h2>
          <div class="gold-rule"></div>
        </div>
        <div class="nations-grid" id="nations-grid"></div>
        <a href="/nations" class="browse-section-link">Explore all four nations →</a>
      </div>
    </section>

    <section class="browse-section parties-browse-section">
      <div class="browse-section-inner">
        <div class="browse-section-header">
          <span class="section-label">Political Parties</span>
          <h2>Browse by Party</h2>
          <div class="gold-rule"></div>
        </div>
        <div class="parties-grid" id="featured-parties-grid"></div>
        <a href="/parties" class="browse-section-link">View all parties →</a>
      </div>
    </section>
  `;

  renderTimelineGrid();
  renderNationsGrid();
  renderFeaturedPartiesGrid();
  setupTimelineFilter();
  initHomeDashboard();
  loadLatestManifestos();
}

function initHomeDashboard() {
  const slider = document.getElementById('election-slider');
  if (!slider) return;

  buildSliderTicks();
  buildSliderLegend();

  slider.addEventListener('input', () => {
    _homeElectionIndex = parseInt(slider.value, 10);
    updateHomeDashboard(_homeElectionIndex);
  });

  document.getElementById('slider-prev')?.addEventListener('click', () => {
    if (_homeElectionIndex > 0) {
      _homeElectionIndex--;
      slider.value = _homeElectionIndex;
      updateHomeDashboard(_homeElectionIndex);
    }
  });

  document.getElementById('slider-next')?.addEventListener('click', () => {
    if (_homeElectionIndex < ELECTIONS.length - 1) {
      _homeElectionIndex++;
      slider.value = _homeElectionIndex;
      updateHomeDashboard(_homeElectionIndex);
    }
  });

  updateHomeDashboard(_homeElectionIndex);
}

function buildSliderTicks() {
  const el = document.getElementById('slider-ticks');
  if (!el) return;
  const marks = [1945, 1964, 1979, 1997, 2010, 2019, 2024];
  el.innerHTML = marks.map(year => {
    const idx = ELECTIONS.findIndex(e => e.year === year);
    if (idx === -1) return '';
    const pct = (idx / (ELECTIONS.length - 1)) * 100;
    return `<button type="button" class="slider-tick" style="left:${pct}%" data-idx="${idx}">${year}</button>`;
  }).join('');
  el.querySelectorAll('.slider-tick').forEach(btn => {
    btn.addEventListener('click', () => {
      _homeElectionIndex = parseInt(btn.getAttribute('data-idx'), 10);
      const slider = document.getElementById('election-slider');
      if (slider) slider.value = _homeElectionIndex;
      updateHomeDashboard(_homeElectionIndex);
    });
  });
}

function buildSliderLegend() {
  const el = document.getElementById('home-slider-legend');
  if (!el) return;
  const ids = ['conservative', 'labour', 'libdem', 'snp', 'green', 'others'];
  el.innerHTML = ids.map(id => {
    const p = PARTIES[id];
    const color = p?.color || '#6b7280';
    const name = p?.shortName || 'Others';
    return `<span class="slider-legend-item" data-party="${id}"><i style="background:${color}"></i><span class="slider-legend-label">${name}</span></span>`;
  }).join('');
}

function updateHomeDashboard(idx) {
  const election = ELECTIONS[idx];
  if (!election) return;

  const winner = PARTIES[election.winner] || {};
  const winnerSeats = (election.results.find(r => r.party === election.winner) || {}).seats || 0;
  const winnerPct = (election.results.find(r => r.party === election.winner) || {}).percentage || 0;

  const dashboard = document.getElementById('home-dashboard');
  if (dashboard) {
    dashboard.style.setProperty('--party-glow', winner.dim || 'rgba(201,168,76,0.12)');
    dashboard.style.setProperty('--party-accent', winner.color || '#c9a84c');
  }

  const label = document.getElementById('dashboard-election-label');
  if (label) label.textContent = `${election.displayYear} General Election`;

  const meta = document.getElementById('dashboard-election-meta');
  if (meta) {
    meta.innerHTML = `<span style="color:${winner.color}">${winner.shortName || ''}</span> · ${winnerSeats} seats · ${winnerPct > 0 ? winnerPct.toFixed(1) + '% vote' : election.pm}`;
  }

  const link = document.getElementById('dashboard-election-link');
  if (link) link.href = `/election/${election.id}`;

  const chart = document.getElementById('home-parliament-chart');
  if (chart) drawParliamentChart(chart, election.results, election.totalSeats);

  buildHomeShareBar(election);
  buildDashboardSidebar(idx);

  const libdemLegend = document.querySelector('#home-slider-legend [data-party="libdem"] .slider-legend-label');
  if (libdemLegend) libdemLegend.textContent = getPartyName('libdem', election.year);
}

function buildHomeShareBar(election) {
  const bar = document.getElementById('home-share-bar');
  const labels = document.getElementById('home-share-labels');
  if (!bar || !labels) return;

  const sorted = [...election.results]
    .filter(r => r.seats > 0)
    .sort((a, b) => b.seats - a.seats)
    .slice(0, 6);

  bar.innerHTML = sorted.map(r => {
    const pct = (r.seats / election.totalSeats) * 100;
    return `<div class="share-segment" style="width:${pct.toFixed(2)}%;background:${getPartyColor(r.party)}" title="${getPartyName(r.party, election.year)}: ${r.seats} seats"></div>`;
  }).join('');

  labels.innerHTML = sorted.map(r => {
    const pct = (r.seats / election.totalSeats * 100).toFixed(1);
    return `<span class="share-label"><i style="background:${getPartyColor(r.party)}"></i>${pct}%</span>`;
  }).join('');
}

function buildDashboardSidebar(idx) {
  const sidebar = document.getElementById('dashboard-sidebar');
  if (!sidebar) return;

  const cards = [];
  if (idx > 0) cards.push({ election: ELECTIONS[idx - 1], role: 'prev' });
  cards.push({ election: ELECTIONS[idx], role: 'current' });
  if (idx < ELECTIONS.length - 1) cards.push({ election: ELECTIONS[idx + 1], role: 'next' });

  sidebar.innerHTML = cards.map(({ election: e, role }) => {
    const winner = PARTIES[e.winner] || {};
    const seats = (e.results.find(r => r.party === e.winner) || {}).seats || 0;
    const pct = (e.results.find(r => r.party === e.winner) || {}).percentage || 0;
    const highlight = (e.highlights || [])[0] || e.summary.slice(0, 140) + '…';
    const active = role === 'current' ? ' is-active' : '';
    return `<a href="/election/${e.id}" class="timeline-card${active}" style="--card-accent:${winner.color}">
      <div class="timeline-card-accent"></div>
      <div class="timeline-card-year">${e.displayYear}</div>
      <div class="timeline-card-party" style="color:${winner.color}">${winner.shortName || ''}</div>
      <div class="timeline-card-stats">
        <div><strong>${seats}</strong><span>Seats</span></div>
        <div><strong>${pct > 0 ? pct.toFixed(1) + '%' : '—'}</strong><span>Vote</span></div>
        <div><strong>${e.pm.split(' ').pop()}</strong><span>PM</span></div>
      </div>
      <p class="timeline-card-summary">${highlight}</p>
      <span class="timeline-card-cta">Learn more →</span>
    </a>`;
  }).join('');
}

function loadLatestManifestos() {
  const track = document.getElementById('latest-track');
  if (!track) return;

  fetchTyped('/data/manifestos-index.json', 'json')
    .catch(() => [])
    .then(items => {
      if (!items.length) {
        track.innerHTML = '<p class="latest-empty">Manifesto documents will appear here as they are added to the archive.</p>';
        return;
      }

      track.innerHTML = items.map(item => {
        const party = PARTIES[item.partyId] || {};
        const election = getElection(item.electionId);
        const cover = `/manifestos/${item.electionId}/${item.partyId}/cover.png?v=${ASSETS_VERSION}`;
        const coverFb = `/manifestos/${item.electionId}/${item.partyId}/cover.jpg?v=${ASSETS_VERSION}`;
        const title = item.label || `${party.shortName || item.partyId} ${election?.displayYear || item.electionId}`;
        return `<a href="/manifesto/${item.electionId}/${item.partyId}" class="latest-card" style="--party-color:${party.color || '#c9a84c'}">
          <div class="latest-card-cover">
            <img src="${cover}" alt="Cover of the ${title}" loading="lazy" onerror="if(this.dataset.fb){this.style.display='none';}else{this.dataset.fb=1;this.src='${coverFb}';}">
            <div class="latest-card-cover-fallback" style="background:${party.color || '#333'}">${election?.displayYear || item.electionId}</div>
          </div>
          <div class="latest-card-body">
            <div class="latest-card-party">${party.shortName || item.partyId}</div>
            <div class="latest-card-title">${title}</div>
          </div>
        </a>`;
      }).join('');

      setupLatestCarousel();
    });
}

function setupLatestCarousel() {
  const track = document.getElementById('latest-track');
  const wrap = track?.parentElement;
  if (!track || !wrap) return;

  const step = () => {
    const card = track.querySelector('.latest-card');
    return card ? card.offsetWidth + 16 : 280;
  };

  const scroll = dir => {
    wrap.scrollBy({ left: dir * step(), behavior: 'smooth' });
  };

  document.getElementById('latest-prev')?.addEventListener('click', () => scroll(-1));
  document.getElementById('latest-next')?.addEventListener('click', () => scroll(1));
}

function electionCardHtml(e) {
  const winner = PARTIES[e.winner] || {};
  const color  = winner.color || 'var(--gold)';
  const dim    = winner.dim   || 'var(--gold-dim)';
  const barSegs = e.results.filter(r => r.seats > 0).sort((a, b) => b.seats - a.seats)
    .map(r => `<div class="seats-segment" style="width:${(r.seats / e.totalSeats * 100).toFixed(1)}%;background:${getPartyColor(r.party)}"></div>`).join('');
  return `<a href="/election/${e.id}" class="election-card" data-winner="${e.winner}" style="--party-color:${color};--party-dim:${dim}">
    <div class="card-year">${e.displayYear}</div>
    <div class="card-date">${e.date}</div>
    <div class="card-winner"><div class="card-winner-dot"></div>${winner.shortName || ''} victory</div>
    <div class="card-pm">New PM: <span>${e.pm}</span></div>
    <div class="card-seats-bar">${barSegs}</div>
  </a>`;
}

function renderTimelineGrid() {
  const grid = document.getElementById('timeline-grid');
  if (!grid) return;
  grid.innerHTML = ELECTIONS.slice().reverse().map(electionCardHtml).join('');
}

const HOME_NATION_ICONS = {
  england: '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
  wales: '🏴󠁧󠁢󠁷󠁬󠁳󠁿',
  scotland: '🏴󠁧󠁢󠁳󠁣󠁴󠁿',
  'northern-ireland': '🇮🇪',
};

function renderNationsGrid() {
  const grid = document.getElementById('nations-grid');
  if (!grid) return;
  Object.keys(HOME_NATION_ICONS).forEach(id => {
    const nation = NATIONS[id];
    if (!nation) return;
    const a = document.createElement('a');
    a.href = `/nation/${id}`;
    a.className = 'nation-card';
    a.innerHTML = `<div class="nation-icon">${HOME_NATION_ICONS[id]}</div><div class="nation-name">${nation.name}</div><div class="nation-mp">${nation.constituencies} Westminster MPs</div>`;
    grid.appendChild(a);
  });
}

function renderFeaturedPartiesGrid() {
  const grid = document.getElementById('featured-parties-grid');
  if (!grid) return;
  [
    'conservative', 'labour', 'libdem',
    'snp', 'plaid', 'green', 'reform', 'dup', 'sinnfein',
  ].forEach(id => {
    const p = PARTIES[id];
    if (!p) return;
    const a = document.createElement('a');
    a.href = `/party/${id}`;
    a.className = 'party-card';
    a.style.setProperty('--party-color', p.color);
    a.innerHTML = `<div class="party-card-name">${p.shortName}</div><div class="party-card-founded">Est. ${p.founded}</div><div class="party-card-color-swatch"></div><div class="party-card-desc">${p.description}</div>`;
    grid.appendChild(a);
  });
}

function setupTimelineFilter() {
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const f = btn.getAttribute('data-filter');
      document.querySelectorAll('.election-card').forEach(card => {
        card.style.display = (f === 'all' || card.getAttribute('data-winner') === f) ? '' : 'none';
      });
    });
  });
}

// ── MANIFESTO CARD BUILDER ────────────────────────────────────
function buildManifestoCard(pid, election, opts = {}) {
  const p = PARTIES[pid];
  const displayName  = getPartyName(pid, election.year);
  const pdfPath      = `/manifestos/${election.id}/${pid}/manifesto.pdf`;
  const textPath     = `/manifesto/${election.id}/${pid}`;
  const coverPath    = `/manifestos/${election.id}/${pid}/cover.png?v=${ASSETS_VERSION}`;
  const coverFallback= `/manifestos/${election.id}/${pid}/cover.jpg?v=${ASSETS_VERSION}`;
  const hasPdf       = hasManifestoPdf(election.id, pid);
  const thumbHref    = hasPdf ? pdfPath : textPath;
  const thumbTarget  = hasPdf ? ' target="_blank" rel="noopener"' : '';
  const thumbLabel   = hasPdf
    ? `Open ${displayName} ${election.displayYear} manifesto PDF`
    : `Read ${displayName} ${election.displayYear} manifesto online`;

  const result = opts.result;
  const noSeats = result
    ? result.seats === 0
    : !election.results.find(r => r.party === pid && r.seats > 0);
  const headerName = opts.showYearAsTitle
    ? election.displayYear
    : partyLink(pid, displayName, election.year);
  const seatsTag = result
    ? (result.seats === 0
      ? '<div class="manifesto-party-tag no-seats-tag">No seats won</div>'
      : `<div class="manifesto-party-tag">${result.seats} seat${result.seats !== 1 ? 's' : ''}</div>`)
    : (noSeats
      ? '<div class="manifesto-party-tag no-seats-tag">No seats won</div>'
      : `<div class="manifesto-party-tag">${election.displayYear}</div>`);

  const pdfLink = hasPdf
    ? `<a href="${pdfPath}" class="manifesto-link" target="_blank" rel="noopener">
          <span class="manifesto-link-icon">📄</span>
          <div class="manifesto-link-info"><div class="manifesto-link-title">Original Manifesto</div><div class="manifesto-link-sub">PDF scan of original document</div></div>
        </a>`
    : '';

  return `<div class="manifesto-card" style="--party-color:${p.color};--party-dim:${p.dim}">
      <a href="${thumbHref}" class="manifesto-thumb"${thumbTarget} aria-label="${thumbLabel}">
        <img src="${coverPath}" alt="${displayName} ${election.displayYear} manifesto cover"
          onerror="if(this.dataset.fb){this.style.display='none';this.nextElementSibling.style.display='flex';}else{this.dataset.fb=1;this.src='${coverFallback}';}">
        <div class="manifesto-thumb-placeholder" style="display:none">
          <svg viewBox="0 0 48 64" fill="none" xmlns="http://www.w3.org/2000/svg" class="thumb-doc-icon">
            <rect x="4" y="2" width="32" height="42" rx="2" fill="currentColor" opacity="0.15"/>
            <rect x="8" y="6" width="32" height="42" rx="2" fill="currentColor" opacity="0.2"/>
            <rect x="12" y="10" width="32" height="44" rx="2" fill="currentColor" opacity="0.9" stroke="currentColor" stroke-width="0.5"/>
            <line x1="19" y1="22" x2="37" y2="22" stroke="white" stroke-width="1.5" opacity="0.4"/>
            <line x1="19" y1="28" x2="37" y2="28" stroke="white" stroke-width="1.5" opacity="0.4"/>
            <line x1="19" y1="34" x2="30" y2="34" stroke="white" stroke-width="1.5" opacity="0.4"/>
          </svg>
          <span class="thumb-year">${election.displayYear}</span>
        </div>
      </a>
      <div class="manifesto-card-header">
        <div class="manifesto-party-dot" style="background:${p.color}"></div>
        <div class="manifesto-party-name">${headerName}</div>
        ${seatsTag}
      </div>
      <div class="manifesto-card-body">
        ${pdfLink}
        <a href="${textPath}" class="manifesto-link">
          <span class="manifesto-link-icon">📝</span>
          <div class="manifesto-link-info"><div class="manifesto-link-title">Read Online</div><div class="manifesto-link-sub">Formatted text version</div></div>
        </a>
      </div>
    </div>`;
}

// ── ELECTION PAGE ─────────────────────────────────────────────
function renderElection(app, id) {
  const election = getElection(id);
  if (!election) { renderNotFound(app); return; }
  setPageMeta({
    title: `${election.displayYear} General Election`,
    description: `Results, maps, and manifestos from the ${election.displayYear} UK general election.`,
    path: `/election/${id}`,
  });

  const winner   = PARTIES[election.winner] || {};
  const color    = winner.color || 'var(--gold)';
  const dim      = winner.dim   || 'var(--gold-dim)';
  const majority = getMajorityThreshold(election.totalSeats);
  const winnerSeats = (election.results.find(r => r.party === election.winner) || {}).seats || 0;
  const hasMaj   = winnerSeats >= majority;
  const idx  = ELECTIONS.findIndex(e => e.id === id);
  const prev = idx > 0 ? ELECTIONS[idx - 1] : null;
  const next = idx < ELECTIONS.length - 1 ? ELECTIONS[idx + 1] : null;

  const summaryParas = election.summary.split('\n\n').map(p => `<p>${p.trim()}</p>`).join('');
  const highlightItems = (election.highlights || []).map(h => `<div class="highlight-item"><div class="highlight-marker"></div><span>${h}</span></div>`).join('');

  // Results table — show all named parties, flag NI-only rows, show '—' for 0 votes
  const maxSeats   = Math.max(...election.results.map(r => r.seats));
  const resultRows = election.results
    .filter(r => r.seats > 0 || r.votes > 0)
    .sort((a, b) => b.seats - a.seats)
    .map(r => {
      const isWinner = r.party === election.winner;
      const niOnly   = r.votes === 0 && ['uup','vanguard','dup','sdlp','sinnfein','alliance','gpni','pup','tuv'].includes(r.party);
      const votesDisplay   = r.votes   > 0 ? r.votes.toLocaleString()   : '—';
      const pctDisplay     = r.percentage > 0 ? r.percentage.toFixed(1) + '%' : (niOnly ? '<span style="font-size:0.72rem;color:var(--text-faint)">NI only</span>' : '—');
      return `<tr>
        <td><div class="result-party-name"><div class="result-party-swatch" style="background:${getPartyColor(r.party)}"></div>${partyLink(r.party, null, election.year)}${isWinner && hasMaj ? ' <span class="majority-badge">✦ Majority</span>' : ''}${isWinner && !hasMaj ? ' <span class="majority-badge">✦ Largest party</span>' : ''}</div></td>
        <td><div class="result-seats-bar-wrap"><div class="result-seats-bar"><div class="result-seats-fill" style="width:${(r.seats/maxSeats*100).toFixed(1)}%;background:${getPartyColor(r.party)}"></div></div><strong style="color:var(--cream);min-width:32px">${r.seats}</strong></div></td>
        <td style="color:var(--text-muted)">${votesDisplay}</td>
        <td style="color:var(--text-muted)">${pctDisplay}</td>
      </tr>`;
    }).join('');

  // Manifesto section — results parties + extraManifestoParties (deduplicated)
  const manifestoPartyIds = [
    ...election.results.filter(r => r.seats > 0).map(r => r.party),
    ...(election.extraManifestoParties || []),
  ].filter((v, i, a) => a.indexOf(v) === i && v !== 'others' && PARTIES[v] && !MANIFESTO_EXCLUDED_PARTIES.has(v));

  const NATION_ORDER  = ['england', 'scotland', 'wales', 'northern-ireland', 'others'];
  const NATION_LABELS = { england: '🏴󠁧󠁢󠁥󠁮󠁧󠁿 England & UK-wide', scotland: '🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scotland', wales: '🏴󠁧󠁢󠁷󠁬󠁳󠁿 Wales', 'northern-ireland': '🇮🇪 Northern Ireland', others: 'Other Parties' };
  const grouped = {};
  manifestoPartyIds.forEach(pid => {
    const n = PARTIES[pid].nation || 'others';
    if (!grouped[n]) grouped[n] = [];
    grouped[n].push(pid);
  });
  const presentNations = NATION_ORDER.filter(n => grouped[n]?.length);
  const manifestoGridContent = presentNations.length > 1
    ? presentNations.map(n => `<div class="manifesto-nation-group">
        <h3 class="manifesto-nation-heading">${nationLink(n, NATION_LABELS[n])}</h3>
        <div class="manifesto-grid">${grouped[n].map(pid => buildManifestoCard(pid, election)).join('')}</div>
      </div>`).join('')
    : `<div class="manifesto-grid">${manifestoPartyIds.map(pid => buildManifestoCard(pid, election)).join('')}</div>`;

  const videoIds = Array.isArray(election.youtubeId)
    ? election.youtubeId.filter(Boolean)
    : (election.youtubeId ? [election.youtubeId] : []);
  const videoSection = videoIds.length
    ? `<div class="video-section"><span class="section-label">Election Night</span><h2>Broadcast Recording</h2>${videoIds.map((id, i) => {
        const start = i === 0 && election.youtubeStart ? `?start=${election.youtubeStart}` : '';
        return `<div class="video-wrap"><iframe src="https://www.youtube.com/embed/${id}${start}" allow="accelerometer;autoplay;clipboard-write;encrypted-media;gyroscope;picture-in-picture" allowfullscreen loading="lazy"></iframe></div>`;
      }).join('')}</div>`
    : `<div class="video-section"><span class="section-label">Election Night</span><h2>Broadcast Recording</h2><div class="video-wrap" style="min-height:200px"><div class="video-placeholder"><div class="video-placeholder-icon">▶</div><div class="video-placeholder-text">Add a <code>youtubeId</code> to this election in <code>js/data.js</code> to embed the broadcast recording.</div></div></div></div>`;

  app.innerHTML = `
    ${renderBreadcrumb([
      { label: 'Home', href: '/' },
      { label: 'General Elections', href: '/' },
      { label: election.displayYear },
    ])}
    <section class="election-hero" style="--party-glow:${dim}">
      <div class="election-hero-bg"></div>
      <div class="election-hero-inner">
        <div>
          <div class="election-eyebrow">United Kingdom General Election</div>
          <h1 class="election-title">${election.displayYear}</h1>
          <div class="election-date">${election.date}</div>
          <div class="election-winner-badge" style="--party-color:${color};--party-dim:${dim}">
            <div class="winner-dot"></div>${winner.shortName} victory — ${election.pm} (PM)
          </div>
        </div>
        <div class="election-nav-btns">
          ${prev ? `<a class="election-nav-btn" href="/election/${prev.id}">← ${prev.displayYear}</a>` : ''}
          ${next ? `<a class="election-nav-btn" href="/election/${next.id}">${next.displayYear} →</a>` : ''}
        </div>
      </div>
    </section>

    <div class="election-body">
      <div class="election-grid">
        <div>
          <span class="section-label">Election Summary</span>
          <div class="election-summary">${summaryParas}</div>
          ${renderSupplementaryDocuments(election.supplementaryDocuments)}
          ${highlightItems ? `<div class="highlights-list"><h3>Key Moments</h3>${highlightItems}</div>` : ''}

          <div class="results-section">
            <span class="section-label">Seat Distribution</span>
            <h2>Results</h2>
            <table class="results-table">
              <thead><tr><th>Party</th><th>Seats (of ${election.totalSeats})</th><th>Votes</th><th>Vote %</th></tr></thead>
              <tbody>${resultRows}</tbody>
            </table>
            <p style="font-size:0.75rem;color:var(--text-faint);margin-top:0.75rem">† Northern Ireland party vote totals shown as NI-wide share and are not included in UK-wide percentage figures.</p>
          </div>
        </div>

        <div>
          <div class="viz-panel">
            <div class="viz-tabs" role="tablist" aria-label="Seat visualisations">
              <button type="button" class="viz-tab active" id="viz-tab-parliament" data-viz="parliament" role="tab" aria-selected="true" aria-controls="viz-parliament" tabindex="0">Parliament</button>
              <button type="button" class="viz-tab" id="viz-tab-hexmap" data-viz="hexmap" role="tab" aria-selected="false" aria-controls="viz-hexmap" tabindex="-1">Constituencies</button>
            </div>
            <div class="viz-pane active" id="viz-parliament" role="tabpanel" aria-labelledby="viz-tab-parliament">
              <div class="parliament-card viz-card">
                <div class="parliament-card-title">House of Commons</div>
                <div class="parliament-card-sub">${election.totalSeats} seats · majority at ${majority}</div>
                <div id="parliament-svg-container"></div>
                <div class="parliament-legend" id="parliament-legend"></div>
              </div>
            </div>
            <div class="viz-pane" id="viz-hexmap" role="tabpanel" aria-labelledby="viz-tab-hexmap" hidden>
              <div class="hexmap-card viz-card">
                <div class="parliament-card-title">Constituency Map</div>
                <div class="parliament-card-sub" id="hexmap-subtitle">Each hexagon is one Westminster seat</div>
                <div id="hexmap-container" class="hexmap-container">
                  <div class="hexmap-loading">Loading constituency data…</div>
                </div>
                <div class="parliament-legend hexmap-legend" id="hexmap-legend" hidden></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="manifestos-section">
        <span class="section-label">Party Manifestos</span>
        <h2>Documents</h2>
        <p class="manifestos-intro">Parties marked "No seats won" contested the election but did not win representation.</p>
        ${manifestoGridContent}
      </div>

      ${videoSection}
    </div>
  `;

  requestAnimationFrame(() => {
    const c = document.getElementById('parliament-svg-container');
    const l = document.getElementById('parliament-legend');
    if (c) { drawParliamentChart(c, election.results, election.totalSeats); buildParliamentLegend(l, election.results, election.year); }
    setupElectionVizTabs(id);
  });
}

function setupElectionVizTabs(electionId) {
  const tabs = Array.from(document.querySelectorAll('.viz-tab'));
  const panes = {
    parliament: document.getElementById('viz-parliament'),
    hexmap: document.getElementById('viz-hexmap'),
  };
  let hexLoaded = false;

  const activateTab = tab => {
    const viz = tab.getAttribute('data-viz');
    tabs.forEach(t => {
      const active = t === tab;
      t.classList.toggle('active', active);
      t.setAttribute('aria-selected', active ? 'true' : 'false');
      t.tabIndex = active ? 0 : -1;
    });
    Object.entries(panes).forEach(([key, pane]) => {
      if (!pane) return;
      const show = key === viz;
      pane.classList.toggle('active', show);
      pane.hidden = !show;
    });
    if (viz === 'hexmap' && !hexLoaded) {
      hexLoaded = true;
      initElectionHexmap(electionId);
    }
  };

  tabs.forEach((tab, i) => {
    tab.addEventListener('click', () => activateTab(tab));
    tab.addEventListener('keydown', e => {
      if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
        e.preventDefault();
        const next = e.key === 'ArrowRight'
          ? tabs[(i + 1) % tabs.length]
          : tabs[(i - 1 + tabs.length) % tabs.length];
        activateTab(next);
        next.focus();
      }
    });
  });
}

async function initElectionHexmap(electionId) {
  const container = document.getElementById('hexmap-container');
  const subtitle = document.getElementById('hexmap-subtitle');
  if (!container) return;

  if (electionId === '1945') {
    const outsideData = await load1945OutsideBoundary();
    const hexjson = await loadHexLayoutJson('1945');
    const mainland = hexjson ? Object.keys(hexjson.hexes || {}).length : 0;
    const outside = outsideData?.counts?.constituencies || 22;
    if (subtitle) {
      subtitle.textContent = `${mainland} single-member seats on the hex map · ${outside} multi-member & university constituencies (${outsideData?.counts?.members || 42} MPs) listed separately`;
    }
    const legend = document.getElementById('hexmap-legend');
    if (legend) legend.hidden = false;
    const election = getElection(electionId);
    await draw1945Hexmap(container, { electionId, electionYear: election?.year, legendEl: legend });
    return;
  }

  const data = await loadConstituencyData(electionId);
  if (!data?.constituencies?.length) {
    container.innerHTML = '<p class="hexmap-empty">Constituency-level results for this election are not yet in the archive. Data is available for elections from 1945 onwards as it is processed.</p>';
    return;
  }

  if (subtitle) {
    const matched = data.matchedHexes;
    const note = matched > 0
      ? `${data.totalSeats} constituencies · ${matched} placed on hexmap`
      : `${data.totalSeats} constituencies · compact grid layout (historic boundaries)`;
    subtitle.textContent = note;
  }

  const legend = document.getElementById('hexmap-legend');
  if (legend) legend.hidden = false;

  const election = getElection(electionId);
  drawHexmap(container, data, { electionId, electionYear: election?.year, legendEl: legend });
}

// ── CO-OPERATIVE PARTY CUSTOM PAGE ───────────────────────────
async function renderCooperativePartyPage(app, party) {
  const color = party.color;

  // Load devolved history to get the manifestos
  const holyroodHistory = (typeof getHolyroodPartyHistory === 'function')
    ? await getHolyroodPartyHistory('cooperative')
    : { elections: [], manifestos: [] };
  const holyroodManifestos = holyroodHistory.manifestos;
  const holyroodItems = holyroodManifestos.map(({ election, manifesto }) =>
    holyroodManifestoCard(manifesto, election.year)
  ).join('');

  const seneddHistory = (typeof getSeneddPartyHistory === 'function')
    ? await getSeneddPartyHistory('cooperative')
    : { elections: [], manifestos: [] };
  const seneddManifestos = seneddHistory.manifestos;
  const seneddItems = seneddManifestos.map(({ election, manifesto }) =>
    seneddManifestoCard(manifesto, election.year)
  ).join('');

  // Load Westminster manifestos from ELECTIONS
  const partyElections = ELECTIONS.map(e => {
    if ((e.extraManifestoParties || []).includes('cooperative')) {
      return { election: e, result: { party: 'cooperative', seats: 0, votes: 0, percentage: 0 } };
    }
    return null;
  }).filter(Boolean);

  const manifestoElections = partyElections.filter(({ election: e }) =>
    hasManifestoContent(e.id, 'cooperative')
  );
  const manifestoItems = manifestoElections.slice().reverse().map(({ election: e, result: r }) =>
    buildManifestoCard('cooperative', e, { result: r, showYearAsTitle: true })
  ).join('');

  // Westminster History Table Data
  const coopWestminsterData = [
    { id: "1945", label: "1945", count: 23 },
    { id: "1950", label: "1950", count: 18 },
    { id: "1951", label: "1951", count: 16 },
    { id: "1955", label: "1955", count: 19 },
    { id: "1959", label: "1959", count: 16 },
    { id: "1964", label: "1964", count: 19 },
    { id: "1966", label: "1966", count: 18 },
    { id: "1970", label: "1970", count: 17 },
    { id: "feb1974", label: "Feb 1974", count: 16 },
    { id: "oct1974", label: "Oct 1974", count: 16 },
    { id: "1979", label: "1979", count: 17 },
    { id: "1983", label: "1983", count: 8 },
    { id: "1987", label: "1987", count: 10 },
    { id: "1992", label: "1992", count: 14 },
    { id: "1997", label: "1997", count: 26 },
    { id: "2001", label: "2001", count: 30 },
    { id: "2005", label: "2005", count: 29 },
    { id: "2010", label: "2010", count: 28 },
    { id: "2015", label: "2015", count: 24 },
    { id: "2017", label: "2017", count: 38 },
    { id: "2019", label: "2019", count: 26 },
    { id: "2024", label: "2024", count: 43 }
  ];
  
  const maxCoopWestminster = Math.max(...coopWestminsterData.map(d => d.count));
  const westminsterRows = coopWestminsterData.slice().reverse().map(d => {
    const barW = ((d.count / maxCoopWestminster) * 100).toFixed(1);
    return `<a class="party-election-row" href="/election/${d.id}">
      <div class="per-year">${d.label}</div>
      <div><div class="per-outcome won">✦ Joint Candidate</div><div style="font-size:0.78rem;color:var(--text-faint);margin-top:0.3rem">Labour/Co-op group</div></div>
      <div class="per-seats-wrap"><div class="per-seats-num">${d.count}</div><div class="per-seats-label">elected</div></div>
      <div class="per-bar-wrap"><div class="per-bar"><div class="per-bar-fill" style="width:${barW}%;background:${color}"></div></div></div>
    </a>`;
  }).join('');

  // Devolved History Table Data
  const coopHolyroodData = [
    { id: "1999", label: "1999", count: 2 },
    { id: "2003", label: "2003", count: 9 },
    { id: "2007", label: "2007", count: 9 },
    { id: "2011", label: "2011", count: 5 },
    { id: "2016", label: "2016", count: 8 },
    { id: "2021", label: "2021", count: 11 },
    { id: "2026", label: "2026", count: 11 }
  ];

  const coopSeneddData = [
    { id: "1999", label: "1999", count: 4 },
    { id: "2003", label: "2003", count: 4 },
    { id: "2007", label: "2007", count: 4 },
    { id: "2011", label: "2011", count: 9 },
    { id: "2016", label: "2016", count: 11 },
    { id: "2021", label: "2021", count: 16 },
    { id: "2026", label: "2026", count: 3 }
  ];

  const maxHolyroodCoop = Math.max(...coopHolyroodData.map(d => d.count || 0));
  const holyroodRows = coopHolyroodData.slice().reverse().map(d => {
    if (d.count === null) {
      return `<div class="party-election-row no-hover">
        <div class="per-year">${d.label}</div>
        <div><div class="per-outcome lost">Unknown</div><div style="font-size:0.78rem;color:var(--text-faint);margin-top:0.3rem">Data unavailable</div></div>
        <div class="per-seats-wrap"><div class="per-seats-num">—</div><div class="per-seats-label">elected</div></div>
        <div class="per-bar-wrap"><div class="per-bar"><div class="per-bar-fill" style="width:0%;background:${color}"></div></div></div>
      </div>`;
    }
    const barW = ((d.count / maxHolyroodCoop) * 100).toFixed(1);
    return `<a class="party-election-row" href="/devolved/holyrood/${d.id}">
      <div class="per-year">${d.label}</div>
      <div><div class="per-outcome won">✦ Joint Candidate</div><div style="font-size:0.78rem;color:var(--text-faint);margin-top:0.3rem">Labour/Co-op group</div></div>
      <div class="per-seats-wrap"><div class="per-seats-num">${d.count}</div><div class="per-seats-label">elected</div></div>
      <div class="per-bar-wrap"><div class="per-bar"><div class="per-bar-fill" style="width:${barW}%;background:${color}"></div></div></div>
    </a>`;
  }).join('');

  const maxSeneddCoop = Math.max(...coopSeneddData.map(d => d.count || 0));
  const seneddRows = coopSeneddData.slice().reverse().map(d => {
    if (d.count === null) {
      return `<div class="party-election-row no-hover">
        <div class="per-year">${d.label}</div>
        <div><div class="per-outcome lost">Unknown</div><div style="font-size:0.78rem;color:var(--text-faint);margin-top:0.3rem">Data unavailable</div></div>
        <div class="per-seats-wrap"><div class="per-seats-num">—</div><div class="per-seats-label">elected</div></div>
        <div class="per-bar-wrap"><div class="per-bar"><div class="per-bar-fill" style="width:0%;background:${color}"></div></div></div>
      </div>`;
    }
    const barW = ((d.count / maxSeneddCoop) * 100).toFixed(1);
    return `<a class="party-election-row" href="/devolved/senedd/${d.id}">
      <div class="per-year">${d.label}</div>
      <div><div class="per-outcome won">✦ Joint Candidate</div><div style="font-size:0.78rem;color:var(--text-faint);margin-top:0.3rem">Labour/Co-op group</div></div>
      <div class="per-seats-wrap"><div class="per-seats-num">${d.count}</div><div class="per-seats-label">elected</div></div>
      <div class="per-bar-wrap"><div class="per-bar"><div class="per-bar-fill" style="width:${barW}%;background:${color}"></div></div></div>
    </a>`;
  }).join('');

  const contestedLabel = '22 Westminster · 7 Holyrood · 7 Senedd';

  app.innerHTML = `
    ${renderBreadcrumb([
      { label: 'Home', href: '/' },
      { label: party.shortName },
    ])}
    <section class="party-hero" style="--party-color:${color};--party-bg:${party.dim}">
      <div class="party-hero-bg"></div>
      <div class="party-hero-inner">
        <div>
          <div class="party-color-bar" style="background:${color}"></div>
          <h1 class="party-hero-title">${party.name}</h1>
          <div class="party-hero-meta">
            <div class="party-meta-item">Founded<strong>${party.founded || '—'}</strong></div>
            <div class="party-meta-item">Spectrum<strong>${party.spectrum}</strong></div>
            <div class="party-meta-item">Elections contested<strong>${contestedLabel}</strong></div>
          </div>
        </div>
      </div>
    </section>

    <div class="party-body">
      <div class="party-description">
        ${party.description}
      </div>

      <div class="coop-representation-section">
        <span class="section-label">Current Representation</span>
        <h2>Elected Representatives</h2>
        <div class="gold-rule" style="background:${color}"></div>
        <div class="coop-rep-grid">
          <div class="coop-rep-card">
            <div class="coop-rep-num">41</div>
            <div class="coop-rep-label">House of Commons</div>
          </div>
          <div class="coop-rep-card">
            <div class="coop-rep-num">11</div>
            <div class="coop-rep-label">Scottish Parliament</div>
          </div>
          <div class="coop-rep-card">
            <div class="coop-rep-num">3</div>
            <div class="coop-rep-label">Senedd Cymru</div>
          </div>
        </div>
        <p class="coop-rep-note">
          <strong>Joint Electoral Alliance Note:</strong> The Co-operative Party does not usually stand against Labour. Candidates normally stand jointly as Labour and Co-operative, or in some devolved/list elections may appear on the ballot under a Labour description while being recognised by the Co-operative Party as part of its parliamentary group.
        </p>
      </div>

      <div class="party-elections-section">
        <span class="section-label">Electoral Record</span>
        <h2>Westminster Joint Representatives</h2>
        <div class="gold-rule" style="background:${color}"></div>
        <div class="party-results-list">${westminsterRows}</div>
      </div>

      <div class="party-manifestos-section">
        <span class="section-label">Documents</span>
        <h2>Westminster Manifestos</h2>
        <div class="gold-rule" style="background:${color}"></div>
        ${manifestoItems ? `<div class="manifesto-grid">${manifestoItems}</div>` : '<p style="color:var(--text-muted)">No Westminster manifestos on record.</p>'}
      </div>

      <div class="party-elections-section">
        <span class="section-label">Holyrood</span>
        <h2>Scottish Parliament Joint Representatives</h2>
        <div class="gold-rule" style="background:${color}"></div>
        <div class="party-results-list">${holyroodRows}</div>
      </div>

      <div class="party-manifestos-section">
        <span class="section-label">Holyrood</span>
        <h2>Scottish Parliament Manifestos</h2>
        <div class="gold-rule" style="background:${color}"></div>
        ${holyroodItems ? `<div class="manifesto-grid">${holyroodItems}</div>` : '<p style="color:var(--text-muted)">No Scottish Parliament manifestos on record.</p>'}
      </div>

      <div class="party-elections-section">
        <span class="section-label">Senedd Cymru</span>
        <h2>Welsh Parliament Joint Representatives</h2>
        <div class="gold-rule" style="background:${color}"></div>
        <div class="party-results-list">${seneddRows}</div>
      </div>

      <div class="party-manifestos-section">
        <span class="section-label">Senedd Cymru</span>
        <h2>Welsh Parliament Manifestos</h2>
        <div class="gold-rule" style="background:${color}"></div>
        ${seneddItems ? `<div class="manifesto-grid">${seneddItems}</div>` : '<p style="color:var(--text-muted)">No Welsh Parliament manifestos on record.</p>'}
      </div>

      <div class="coop-sources-section" style="margin-top: 3rem; border-top: 1px solid var(--navy-border); padding-top: 1.5rem; font-size: 0.82rem; color: var(--text-faint); line-height: 1.6;">
        <p>
          * <strong>Note on Sitting vs Elected Counts:</strong> Counts display the number of joint Labour/Co-operative representatives elected at general or devolved elections. This may differ from sitting numbers due to subsequent by-elections, defections, suspensions, or vacancies (e.g. 43 Labour/Co-operative MPs were elected in the 2024 Westminster general election, while 41 are currently sitting in the House of Commons).
        </p>
        <p>
          <strong>Sources &amp; Metadata:</strong>
        </p>
        <ul style="padding-left: 1.25rem; margin-top: 0.5rem; margin-bottom: 0.5rem;">
          <li><a href="https://party.coop/people/mps/" target="_blank" rel="noopener" style="color: var(--gold); text-decoration: underline;">Co-operative Party MPs Directory</a> (Current Commons group)</li>
          <li><a href="https://party.coop/people/msps/" target="_blank" rel="noopener" style="color: var(--gold); text-decoration: underline;">Co-operative Party MSPs Directory</a> (Current Holyrood group)</li>
          <li><a href="https://party.coop/people/ms/" target="_blank" rel="noopener" style="color: var(--gold); text-decoration: underline;">Co-operative Party MSs Directory</a> (Current Senedd group)</li>
          <li><a href="https://senedd.wales/media/oifhgrno/representatives-export.csv" target="_blank" rel="noopener" style="color: var(--gold); text-decoration: underline;">Senedd Cymru Official Members List</a></li>
          <li>Co-operative Party Annual Reports &amp; Accounts (2012, 2016, 2021, 2024)</li>
          <li>Co-operative Party Historic Westminster Election Results database</li>
        </ul>
        <p style="margin-top: 0.5rem;"><em>Data retrieved and verified: June 2026.</em></p>
      </div>
    </div>
  `;
}

// ── PARTY PAGE ────────────────────────────────────────────────
async function renderParty(app, id) {
  const party = PARTIES[id];
  if (!party) { renderNotFound(app); return; }
  if (id === 'cooperative') {
    await renderCooperativePartyPage(app, party);
    return;
  }
  setPageMeta({
    title: party.shortName,
    description: `Manifestos and election history for the ${party.shortName} in UK general elections since 1945.`,
    path: `/party/${id}`,
  });

  const color = party.color;

  const partyElections = ELECTIONS.map(e => {
    const r = e.results.find(res => res.party === id);
    if (r) return { election: e, result: r };
    const pr = (e.partyResults || {})[id];
    if (pr) return { election: e, result: pr };
    if ((e.extraManifestoParties || []).includes(id)) return { election: e, result: { party: id, seats: 0, votes: 0, percentage: 0 } };
    return null;
  }).filter(Boolean);

  const electionsWon = partyElections.filter(pe => pe.election.winner === id).length;
  const maxSeats = Math.max(1, ...partyElections.map(pe => pe.result.seats));

  const electionRows = partyElections.slice().reverse().map(({ election: e, result: r }) => {
    const isWon   = e.winner === id;
    const isCoal  = id === 'libdem' && e.id === '2010';
    const cls     = isWon ? 'won' : isCoal ? 'coalition' : 'lost';
    const label   = isWon ? '✦ Won' : isCoal ? '⊕ Coalition' : 'Opposition';
    const barW    = ((r.seats / maxSeats) * 100).toFixed(1);
    return `<a class="party-election-row" href="/election/${e.id}">
      <div class="per-year">${e.displayYear}</div>
      <div><div class="per-outcome ${cls}">${label}</div><div style="font-size:0.78rem;color:var(--text-faint);margin-top:0.3rem">${e.pm}</div></div>
      <div class="per-seats-wrap"><div class="per-seats-num">${r.seats}</div><div class="per-seats-label">seats</div></div>
      <div class="per-bar-wrap"><div class="per-bar"><div class="per-bar-fill" style="width:${barW}%;background:${color}"></div></div><div class="per-pct">${r.percentage > 0 ? r.percentage.toFixed(1) + '% vote' : '—'}</div></div>
    </a>`;
  }).join('');

  const manifestoElections = partyElections.filter(({ election: e }) =>
    hasManifestoContent(e.id, id)
  );
  const manifestoItems = manifestoElections.slice().reverse().map(({ election: e, result: r }) =>
    buildManifestoCard(id, e, { result: r, showYearAsTitle: true })
  ).join('');

  const holyroodHistory = (typeof getHolyroodPartyHistory === 'function')
    ? await getHolyroodPartyHistory(id)
    : { elections: [], manifestos: [] };
  const holyroodElections = holyroodHistory.elections;
  const holyroodManifestos = holyroodHistory.manifestos;

  const seneddHistory = (typeof getSeneddPartyHistory === 'function')
    ? await getSeneddPartyHistory(id)
    : { elections: [], manifestos: [] };
  const seneddElections = seneddHistory.elections;
  const seneddManifestos = seneddHistory.manifestos;

  const niHistory = (typeof getNIPartyHistory === 'function')
    ? await getNIPartyHistory(id)
    : { elections: [], manifestos: [] };
  const niElections = niHistory.elections;
  const niManifestos = niHistory.manifestos;

  const maxHolyroodSeats = Math.max(1, ...holyroodElections.map(pe => pe.result.seats));
  const holyroodElectionRows = holyroodElections.map(pe =>
    holyroodPartyElectionRow(id, pe, maxHolyroodSeats, color)
  ).join('');

  const holyroodItems = holyroodManifestos.map(({ election, manifesto }) =>
    holyroodManifestoCard(manifesto, election.year)
  ).join('');

  const maxSeneddSeats = Math.max(1, ...seneddElections.map(pe => pe.result.seats));
  const seneddElectionRows = seneddElections.map(pe =>
    seneddPartyElectionRow(id, pe, maxSeneddSeats, color)
  ).join('');

  const seneddItems = seneddManifestos.map(({ election, manifesto }) =>
    seneddManifestoCard(manifesto, election.year)
  ).join('');

  const maxNISeats = Math.max(1, ...niElections.map(pe => pe.result.seats));
  const niElectionRows = niElections.map(pe =>
    niPartyElectionRow(id, pe, maxNISeats, color)
  ).join('');

  const niItems = niManifestos.map(({ election, manifesto }) =>
    niManifestoCard(manifesto, election.year)
  ).join('');

  const contestedParts = [];
  if (partyElections.length) contestedParts.push(`${partyElections.length} Westminster`);
  if (holyroodElections.length) contestedParts.push(`${holyroodElections.length} Holyrood`);
  if (seneddElections.length) contestedParts.push(`${seneddElections.length} Senedd`);
  if (niElections.length) contestedParts.push(`${niElections.length} Stormont`);
  const contestedLabel = contestedParts.join(' · ') || '0';

  const nationId = party.nation && party.nation !== 'others' ? party.nation : null;
  const nationCrumb = nationId
    ? [{ label: getNationLabel(nationId), href: `/nation/${nationId}` }]
    : [];

  app.innerHTML = `
    ${renderBreadcrumb([
      { label: 'Home', href: '/' },
      ...nationCrumb,
      { label: party.shortName },
    ])}
    <section class="party-hero" style="--party-color:${color};--party-bg:${party.dim}">
      <div class="party-hero-bg"></div>
      <div class="party-hero-inner">
        <div>
          <div class="party-color-bar" style="background:${color}"></div>
          <h1 class="party-hero-title">${party.name}</h1>
          <div class="party-hero-meta">
            <div class="party-meta-item">Founded<strong>${party.founded || '—'}</strong></div>
            <div class="party-meta-item">Spectrum<strong>${party.spectrum}</strong></div>
            <div class="party-meta-item">Elections contested<strong>${contestedLabel}</strong></div>
          </div>
        </div>
        ${electionsWon > 0 ? `<div class="party-elections-won-badge"><div class="elections-won-num" style="color:${color}">${electionsWon}</div><div class="elections-won-label">Election${electionsWon !== 1 ? 's' : ''} won</div></div>` : ''}
      </div>
    </section>

    <div class="party-body">
      <div class="party-description">${party.description}</div>
      <div class="party-elections-section">
        <span class="section-label">Electoral Record</span>
        <h2>Westminster Results</h2>
        <div class="gold-rule" style="background:${color}"></div>
        ${electionRows ? `<div class="party-results-list">${electionRows}</div>` : '<p style="color:var(--text-muted)">No Westminster election data available.</p>'}
      </div>
      <div class="party-manifestos-section">
        <span class="section-label">Documents</span>
        <h2>Westminster Manifestos</h2>
        <div class="gold-rule" style="background:${color}"></div>
        ${manifestoItems ? `<div class="manifesto-grid">${manifestoItems}</div>` : '<p style="color:var(--text-muted)">No Westminster manifestos on record.</p>'}
      </div>
      ${holyroodElectionRows ? `<div class="party-elections-section">
        <span class="section-label">Holyrood</span>
        <h2>Scottish Parliament Results</h2>
        <div class="gold-rule" style="background:${color}"></div>
        <div class="party-results-list">${holyroodElectionRows}</div>
      </div>` : ''}
      ${holyroodItems ? `<div class="party-manifestos-section">
        <span class="section-label">Holyrood</span>
        <h2>Scottish Parliament Manifestos</h2>
        <div class="gold-rule" style="background:${color}"></div>
        <div class="manifesto-grid">${holyroodItems}</div>
      </div>` : ''}
      ${seneddElectionRows ? `<div class="party-elections-section">
        <span class="section-label">Senedd Cymru</span>
        <h2>Welsh Parliament Results</h2>
        <div class="gold-rule" style="background:${color}"></div>
        <div class="party-results-list">${seneddElectionRows}</div>
      </div>` : ''}
      ${seneddItems ? `<div class="party-manifestos-section">
        <span class="section-label">Senedd Cymru</span>
        <h2>Welsh Parliament Manifestos</h2>
        <div class="gold-rule" style="background:${color}"></div>
        <div class="manifesto-grid">${seneddItems}</div>
      </div>` : ''}
      ${niElectionRows ? `<div class="party-elections-section">
        <span class="section-label">Stormont</span>
        <h2>Northern Ireland Assembly Results</h2>
        <div class="gold-rule" style="background:${color}"></div>
        <div class="party-results-list">${niElectionRows}</div>
      </div>` : ''}
      ${niItems ? `<div class="party-manifestos-section">
        <span class="section-label">Stormont</span>
        <h2>Northern Ireland Assembly Manifestos</h2>
        <div class="gold-rule" style="background:${color}"></div>
        <div class="manifesto-grid">${niItems}</div>
      </div>` : ''}
    </div>
  `;
}

// ── NATION PAGE ───────────────────────────────────────────────
function renderNation(app, id) {
  const nation = NATIONS[id];
  if (!nation) { renderNotFound(app); return; }
  setPageMeta({
    title: nation.name,
    description: `Election results and parties in ${nation.name} at UK general elections since 1945.`,
    path: `/nation/${id}`,
  });

  const navConfig = NAV_PARTIES[id];
  const partyLinks = navConfig ? navConfig.parties.map(pid => {
    const p = PARTIES[pid];
    if (!p) return '';
    return `<a href="/party/${pid}" class="nation-party-link" style="--party-color:${p.color}">
      <span class="nation-party-dot" style="background:${p.color}"></span>
      <span>${p.shortName}</span>
    </a>`;
  }).join('') : '';

  const keyFacts = (nation.keyFacts || []).map(f => `<div class="highlight-item"><div class="highlight-marker"></div><span>${f}</span></div>`).join('');

  // Westminster GE results table
  let westminsterSection = '';
  if (id === 'england' && nation.westminsterResults) {
    const rows = nation.westminsterResults.map(r => `<tr>
      <td style="font-family:var(--font-display);color:var(--cream)">${r.year}</td>
      <td style="color:#0087DC;font-weight:600">${r.con}</td>
      <td style="color:#E4003B;font-weight:600">${r.lab}</td>
      <td style="color:#FAA61A;font-weight:600">${r.ld}</td>
      <td style="color:var(--text-muted)">${r.other > 0 ? r.other : '—'}</td>
      <td style="color:var(--cream-dark);font-size:0.8rem">${r.total}</td>
    </tr>`).join('');
    westminsterSection = `<div class="devolved-section" style="margin-bottom:2.5rem">
      <span class="section-label">Westminster General Elections</span>
      <h2>Seats Won: England, 1918–2024</h2>
      <div class="gold-rule"></div>
      <p style="color:var(--text-muted);font-size:0.85rem;margin-bottom:1.5rem">"LD" includes Coalition Liberal (1918), National Liberal (1922–45), Liberal/SDP Alliance (1983–87), Liberal Democrats (1988–). England had 485–524 seats 1918–1992; 529 from 1997; 533 from 2010; 543 from 2024. 2024 "Other" = Reform UK 5, Green 4, five independents, Speaker 1. Sources: HC Library CBP-7529 (1918–2019); HC Library CBP-10009 (2024).</p>
      <div style="overflow-x:auto"><table class="results-table">
        <thead><tr><th>Year</th><th style="color:#0087DC">Con</th><th style="color:#E4003B">Lab</th><th style="color:#FAA61A">LD</th><th>Other</th><th>Total</th></tr></thead>
        <tbody>${rows}</tbody>
      </table></div>
    </div>`;
  } else if (id === 'wales' && nation.westminsterResults) {
    const rows = nation.westminsterResults.map(r => `<tr>
      <td style="font-family:var(--font-display);color:var(--cream)">${r.year}</td>
      <td style="color:#0087DC;font-weight:600">${r.con > 0 ? r.con : '—'}</td>
      <td style="color:#E4003B;font-weight:600">${r.lab}</td>
      <td style="color:#FAA61A;font-weight:600">${r.ld > 0 ? r.ld : '—'}</td>
      <td style="color:#008672;font-weight:600">${r.pc > 0 ? r.pc : '—'}</td>
      <td style="color:var(--text-muted)">${r.other > 0 ? r.other : '—'}</td>
      <td style="color:var(--cream-dark);font-size:0.8rem">${r.total}</td>
    </tr>`).join('');
    westminsterSection = `<div class="devolved-section" style="margin-bottom:2.5rem">
      <span class="section-label">Westminster General Elections</span>
      <h2>Seats Won: Wales, 1918–2024</h2>
      <div class="gold-rule"></div>
      <p style="color:var(--text-muted);font-size:0.85rem;margin-bottom:1.5rem">"LD" includes Coalition Liberal (1918), National Liberal (1922–45), Liberal/SDP Alliance (1983–87), Liberal Democrats (1988–). Plaid Cymru first contested Westminster elections in 1929. Wales had 35–40 seats 1918–2019; reduced to 32 from 2024. 2005 "Other" = Peter Law, Independent (Blaenau Gwent). Sources: HC Library CBP-7529 (1918–2019); HC Library CBP-10009 (2024).</p>
      <div style="overflow-x:auto"><table class="results-table">
        <thead><tr><th>Year</th><th style="color:#0087DC">Con</th><th style="color:#E4003B">Lab</th><th style="color:#FAA61A">LD</th><th style="color:#008672">Plaid</th><th>Other</th><th>Total</th></tr></thead>
        <tbody>${rows}</tbody>
      </table></div>
    </div>`;
  } else if (id === 'scotland' && nation.westminsterResults) {
    const rows = nation.westminsterResults.map(r => `<tr>
      <td style="font-family:var(--font-display);color:var(--cream)">${r.year}</td>
      <td style="color:#0087DC;font-weight:600">${r.con > 0 ? r.con : '—'}</td>
      <td style="color:#E4003B;font-weight:600">${r.lab > 0 ? r.lab : '—'}</td>
      <td style="color:#FAA61A;font-weight:600">${r.ld > 0 ? r.ld : '—'}</td>
      <td style="color:#FDF38E;font-weight:600">${r.snp > 0 ? r.snp : '—'}</td>
      <td style="color:var(--text-muted)">${r.other > 0 ? r.other : '—'}</td>
      <td style="color:var(--cream-dark);font-size:0.8rem">${r.total}</td>
    </tr>`).join('');
    westminsterSection = `<div class="devolved-section" style="margin-bottom:2.5rem">
      <span class="section-label">Westminster General Elections</span>
      <h2>Seats Won: Scotland, 1918–2024</h2>
      <div class="gold-rule"></div>
      <p style="color:var(--text-muted);font-size:0.85rem;margin-bottom:1.5rem">"LD" includes Coalition Liberal (1918), National Liberal (1922–45), Liberal/SDP Alliance (1983–87), Liberal Democrats (1988–). Scotland had 71–72 seats 1918–2001; reduced to 59 from 2005, and 57 from 2024. "Other" in the interwar period includes ILP MPs (Glasgow). The precise breakdown of "Other" seats is not available in the source document. Sources: HC Library CBP-7529 (1918–2019); HC Library CBP-10009 (2024).</p>
      <div style="overflow-x:auto"><table class="results-table">
        <thead><tr><th>Year</th><th style="color:#0087DC">Con</th><th style="color:#E4003B">Lab</th><th style="color:#FAA61A">LD</th><th style="color:#FDF38E">SNP</th><th>Other</th><th>Total</th></tr></thead>
        <tbody>${rows}</tbody>
      </table></div>
    </div>`;
  } else if (id === 'northern-ireland' && nation.westminsterEarly && nation.westminsterResults) {
    const earlyRows = nation.westminsterEarly.map(r => `<tr>
      <td style="font-family:var(--font-display);color:var(--cream)">${r.year}</td>
      <td style="color:#0087DC;font-weight:600">${r.unionist}</td>
      <td style="color:#2AA82C;font-weight:600">${r.nationalist > 0 ? r.nationalist : '—'}</td>
      <td style="color:var(--text-muted)">${r.other > 0 ? r.other : '—'}</td>
      <td style="color:var(--cream-dark);font-size:0.8rem">${r.total}</td>
    </tr>`).join('');
    const modernRows = nation.westminsterResults.map(r => `<tr>
      <td style="font-family:var(--font-display);color:var(--cream)">${r.year}</td>
      <td style="color:#48A5EE;font-weight:600">${r.uup > 0 ? r.uup : '—'}</td>
      <td style="color:#2AA82C;font-weight:600">${r.sdlp > 0 ? r.sdlp : '—'}</td>
      <td style="color:#D46A4C;font-weight:600">${r.dup > 0 ? r.dup : '—'}</td>
      <td style="color:#326760;font-weight:600">${r.sf > 0 ? r.sf : '—'}</td>
      <td style="color:var(--text-muted)">${r.other > 0 ? r.other : '—'}</td>
      <td style="color:var(--cream-dark);font-size:0.8rem">${r.total}</td>
    </tr>`).join('');
    westminsterSection = `<div class="devolved-section" style="margin-bottom:2.5rem">
      <span class="section-label">Westminster General Elections</span>
      <h2>Seats Won: Northern Ireland, 1922–2024</h2>
      <div class="gold-rule"></div>
      <p style="color:var(--text-muted);font-size:0.85rem;margin-bottom:1.5rem">Northern Ireland has returned 12 Westminster MPs since partition in 1922 (increased to 17 in 1983, then 18 in 1997). Ulster Unionists took the Conservative whip until 1974. The SDLP was founded in 1970 and the DUP in 1971; the modern party landscape dates from February 1974. Sinn Féin MPs are elected but do not take their seats (abstentionism). 1918 figures covered all of Ireland and are omitted here.</p>
      <p style="color:var(--cream-dark);font-size:0.85rem;font-weight:600;margin-bottom:0.5rem">1922–1970</p>
      <div style="overflow-x:auto;margin-bottom:2rem"><table class="results-table">
        <thead><tr><th>Year</th><th style="color:#0087DC">Unionist¹</th><th style="color:#2AA82C">Nationalist</th><th>Other</th><th>Total</th></tr></thead>
        <tbody>${earlyRows}</tbody>
      </table></div>
      <p style="color:var(--cream-dark);font-size:0.85rem;font-weight:600;margin-bottom:0.5rem">1974–2024</p>
      <div style="overflow-x:auto"><table class="results-table">
        <thead><tr><th>Year</th><th style="color:#48A5EE">UUP</th><th style="color:#2AA82C">SDLP</th><th style="color:#D46A4C">DUP</th><th style="color:#326760">Sinn Féin</th><th>Other²</th><th>Total</th></tr></thead>
        <tbody>${modernRows}</tbody>
      </table></div>
      <p style="color:var(--text-muted);font-size:0.75rem;margin-top:1rem">¹ Includes all unionist parties; UUPs took the Conservative whip until 1974. ² Includes Alliance, TUV and independents; 2024 Other = Alliance (1), TUV (1), Independent (1). Sources: HC Library CBP-7529 (1918–2019); HC Library CBP-10009 (2024).</p>
    </div>`;
  }

  // Devolved body results table if available
  let devolvedTable = '';
  if (id === 'wales' && nation.seneddResults) {
    const rows = nation.seneddResults.map(r => `<tr>
      <td style="color:var(--cream);font-family:var(--font-display);font-size:1.1rem"><a href="/devolved/senedd/${r.year}" style="color:inherit;text-decoration:none">${r.year}</a></td>
      <td><span style="color:#E4003B;font-weight:600">${r.lab}</span></td>
      <td><span style="color:#008672;font-weight:600">${r.pc}</span></td>
      <td><span style="color:#0087DC;font-weight:600">${r.con}</span></td>
      <td><span style="color:#FAA61A;font-weight:600">${r.ld}</span></td>
      ${r.ukip !== undefined ? `<td><span style="color:#70147A;font-weight:600">${r.ukip > 0 ? r.ukip : '—'}</span></td>` : '<td>—</td>'}
      <td><span style="color:#12B6CF;font-weight:600">${r.reform > 0 ? r.reform : '—'}</span></td>
    </tr>`).join('');
    devolvedTable = `<div class="devolved-section">
      <span class="section-label">Senedd Cymru Elections</span>
      <h2>Welsh Parliament Results</h2>
      <div class="gold-rule"></div>
      <p style="color:var(--text-muted);font-size:0.9rem;margin-bottom:1.5rem">60 Members elected by AMS (1999–2021); 96 Members from 2026 under closed-list PR. Labour was the largest party at every election until 2026. <a href="/devolved/senedd">View full Senedd archive →</a></p>
      <table class="results-table">
        <thead><tr><th>Year</th><th style="color:#E4003B">Labour</th><th style="color:#008672">Plaid</th><th style="color:#0087DC">Cons.</th><th style="color:#FAA61A">Lib Dem</th><th style="color:#70147A">UKIP</th><th style="color:#12B6CF">Reform</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
  }

  if (id === 'scotland' && nation.holyroodResults) {
    const rows = nation.holyroodResults.map(r => `<tr>
      <td style="color:var(--cream);font-family:var(--font-display);font-size:1.1rem"><a href="/devolved/holyrood/${r.year}" style="color:inherit;text-decoration:none">${r.year}</a></td>
      <td><span style="color:#FDF38E;font-weight:600">${r.snp}</span></td>
      <td><span style="color:#E4003B;font-weight:600">${r.lab}</span></td>
      <td><span style="color:#0087DC;font-weight:600">${r.con}</span></td>
      <td><span style="color:#FAA61A;font-weight:600">${r.ld}</span></td>
      <td><span style="color:#00B140;font-weight:600">${r.grn}</span></td>
      <td><span style="color:#12B6CF;font-weight:600">${r.reform > 0 ? r.reform : '—'}</span></td>
    </tr>`).join('');
    devolvedTable = `<div class="devolved-section">
      <span class="section-label">Scottish Parliament Elections</span>
      <h2>Holyrood Results</h2>
      <div class="gold-rule"></div>
      <p style="color:var(--text-muted);font-size:0.9rem;margin-bottom:1.5rem">129 MSPs elected by Additional Member System (73 constituency + 56 regional). The SNP has governed Scotland since 2007. <a href="/devolved/holyrood">View full Holyrood archive →</a></p>
      <table class="results-table">
        <thead><tr><th>Year</th><th style="color:#FDF38E">SNP</th><th style="color:#E4003B">Labour</th><th style="color:#0087DC">Cons.</th><th style="color:#FAA61A">Lib Dem</th><th style="color:#00B140">Greens</th><th style="color:#12B6CF">Reform</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
  }

  if (id === 'northern-ireland' && nation.assemblyResults) {
    const rows = nation.assemblyResults.map(r => `<tr>
      <td style="color:var(--cream);font-family:var(--font-display);font-size:1.1rem">${r.year}</td>
      <td><span style="color:#D46A4C;font-weight:600">${r.dup}</span></td>
      <td><span style="color:#326760;font-weight:600">${r.sf}</span></td>
      <td><span style="color:#48A5EE;font-weight:600">${r.uup}</span></td>
      <td><span style="color:#2AA82C;font-weight:600">${r.sdlp}</span></td>
      <td><span style="color:#F6CB2F;font-weight:600">${r.alliance}</span></td>
    </tr>`).join('');
    devolvedTable = `<div class="devolved-section">
      <span class="section-label">Northern Ireland Assembly Elections</span>
      <h2>Stormont Results</h2>
      <div class="gold-rule"></div>
      <p style="color:var(--text-muted);font-size:0.9rem;margin-bottom:1.5rem">90 MLAs elected by Single Transferable Vote (5 per constituency). In 2022 Sinn Féin became the largest party for the first time since partition in 1922. Source: HC Library CBP-7529.</p>
      <table class="results-table">
        <thead><tr><th>Year</th><th style="color:#D46A4C">DUP</th><th style="color:#326760">Sinn Féin</th><th style="color:#48A5EE">UUP</th><th style="color:#2AA82C">SDLP</th><th style="color:#F6CB2F">Alliance</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
  }

  app.innerHTML = `
    ${renderBreadcrumb([
      { label: 'Home', href: '/' },
      { label: 'Nations', href: '/nations' },
      { label: nation.name },
    ])}
    <section class="nation-hero">
      <div class="nation-hero-inner">
        <span class="section-label">United Kingdom — Four Nations</span>
        <h1 class="nation-hero-title">${nation.name}</h1>
        <div class="gold-rule"></div>
        <div class="nation-hero-stats">
          <div class="nation-stat"><div class="nation-stat-num">${nation.constituencies}</div><div class="nation-stat-label">Westminster Constituencies</div></div>
          ${nation.devolvedBody ? `<div class="nation-stat"><div class="nation-stat-num">${nation.devolvedYear}</div><div class="nation-stat-label">${nation.devolvedBody} Established</div></div>` : '<div class="nation-stat"><div class="nation-stat-num">—</div><div class="nation-stat-label">No Devolved Parliament</div></div>'}
          <div class="nation-stat"><div class="nation-stat-num" style="font-size:0.85rem;letter-spacing:0.04em">${nation.electoralSystem.split(';')[0].trim()}</div><div class="nation-stat-label">Westminster Electoral System</div></div>
        </div>
      </div>
    </section>

    <div class="nation-body">
      <div class="nation-grid">
        <div>
          <p class="nation-description">${nation.description}</p>
          ${keyFacts ? `<div class="highlights-list" style="margin-top:2rem"><h3>Key Facts</h3>${keyFacts}</div>` : ''}
          ${westminsterSection}
          ${devolvedTable}
          <p style="font-size:0.75rem;color:var(--text-faint);margin-top:1.5rem">Source: ${nation.source}</p>
        </div>
        <div>
          <div class="nation-parties-card">
            <div class="section-label" style="margin-bottom:1rem">Parties in ${nation.name}</div>
            ${partyLinks}
            ${id === 'england' ? `<a href="/others" class="nation-party-link" style="--party-color:var(--gold)"><span class="nation-party-dot" style="background:var(--gold)"></span><span>Other parties →</span></a>` : ''}
            ${id === 'scotland' ? `<a href="/devolved/holyrood/other-parties" class="holyrood-other-link">Other Scottish parties →</a>` : ''}
            ${id === 'wales' ? `<a href="/devolved/senedd/other-parties" class="holyrood-other-link">Other Welsh parties →</a>` : ''}
            ${id === 'northern-ireland' ? `<a href="/devolved/stormont/other-parties" class="holyrood-other-link">Other Northern Irish parties →</a>` : ''}
          </div>
        </div>
      </div>
    </div>
  `;
}

// ── DEVOLVED PORTAL PAGE ──────────────────────────────────────
function renderDevolved(app, id) {
  const portal = DEVOLVED_PORTALS?.[id];
  if (!portal) { renderNotFound(app); return; }
  setPageMeta({
    title: portal.label,
    description: `Devolved election information for ${portal.label}.`,
    path: `/devolved/${id}`,
  });

  const nation = NATIONS[portal.nation];
  const navConfig = NAV_PARTIES[portal.nation];
  const partyLinks = navConfig ? navConfig.parties.map(pid => {
    const p = PARTIES[pid];
    if (!p) return '';
    return `<a href="/party/${pid}" class="nation-party-link" style="--party-color:${p.color}">
      <span class="nation-party-dot" style="background:${p.color}"></span>
      <span>${p.shortName}</span>
    </a>`;
  }).join('') : '';

  app.innerHTML = `
    ${renderBreadcrumb([
      { label: 'Home', href: '/' },
      { label: 'Devolved Parliaments', href: '/devolved' },
      { label: portal.label },
    ])}
    <section class="devolved-hero">
      <div class="devolved-hero-inner">
        <span class="section-label">${portal.subtitle}</span>
        <h1 class="devolved-hero-title">${portal.label}</h1>
        <div class="gold-rule"></div>
        <p class="devolved-hero-desc">${portal.description}</p>
        <div class="devolved-hero-stats">
          <div class="nation-stat"><div class="nation-stat-num">${portal.established}</div><div class="nation-stat-label">Established</div></div>
          <div class="nation-stat"><div class="nation-stat-num">${portal.members}</div><div class="nation-stat-label">Members</div></div>
          <div class="nation-stat"><div class="nation-stat-num" style="font-size:0.85rem">${portal.system}</div><div class="nation-stat-label">Electoral System</div></div>
        </div>
        ${nation ? `<a href="/nation/${portal.nation}" class="devolved-nation-link">View ${nation.name} nation page →</a>` : ''}
      </div>
    </section>
    <div class="devolved-body">
      <div class="devolved-grid">
        <div>
          <span class="section-label">Manifestos</span>
          <h2>Devolved Election Documents</h2>
          <div class="gold-rule"></div>
          <p style="color:var(--text-muted);margin-bottom:1.5rem">Devolved parliament manifestos will be catalogued here as they are added to the archive. For now, browse parties contesting ${portal.body} elections below.</p>
        </div>
        <div class="nation-parties-card">
          <div class="section-label" style="margin-bottom:1rem">Parties in ${portal.label}</div>
          ${partyLinks}
        </div>
      </div>
    </div>
  `;
}

// ── OTHERS PAGE ───────────────────────────────────────────────
function renderOthers(app) {
  setPageMeta({
    title: 'Other Parties',
    description: 'Minor and regional parties that have won seats at UK general elections since 1945.',
    path: '/others',
  });
  const cards = [...OTHERS_PARTIES]
    .sort((a, b) => (PARTIES[a]?.name || a).localeCompare(PARTIES[b]?.name || b, 'en-GB'))
    .map(pid => {
    const p = PARTIES[pid];
    if (!p) return '';
    return `<a href="/party/${pid}" class="others-party-card" style="--party-color:${p.color}">
      <div class="others-party-swatch" style="background:${p.color}"></div>
      <div>
        <div class="others-party-name">${p.name}</div>
        <div class="others-party-meta">${p.spectrum}${p.founded ? ` · Est. ${p.founded}` : ''}</div>
        <div class="others-party-desc">${p.description}</div>
      </div>
    </a>`;
  }).join('');

  app.innerHTML = `
    <div class="about-section">
      <span class="section-label">Parties</span>
      <h1>Other Parties</h1>
      <div class="gold-rule"></div>
      <p style="color:var(--text-muted);margin-bottom:1rem">Smaller, fringe, single-issue, and historical parties that have contested UK general elections. Many have had a disproportionate influence on British politics despite winning few or no seats.</p>
      <p style="color:var(--text-muted);margin-bottom:0.75rem">For parties contesting the Scottish Parliament:</p>
      <a href="/devolved/holyrood/other-parties" class="cross-archive-link">Other Scottish Parties →</a>
      <p style="color:var(--text-muted);margin-bottom:0.75rem;margin-top:1.25rem">For parties contesting the Welsh Parliament:</p>
      <a href="/devolved/senedd/other-parties" class="cross-archive-link">Other Welsh Parties →</a>
      <p style="color:var(--text-muted);margin-bottom:0.75rem;margin-top:1.25rem">For parties contesting the Northern Ireland Assembly:</p>
      <a href="/devolved/stormont/other-parties" class="cross-archive-link">Other Northern Irish Parties →</a>
      <div class="others-grid">${cards}</div>
    </div>
  `;
}

// ── MANIFESTO VIEWER ──────────────────────────────────────────
function splitManifestoFrontmatter(md) {
  const text = md.replace(/^\uFEFF/, '');
  if (!text.startsWith('---')) {
    return { meta: null, body: md };
  }
  const end = text.indexOf('\n---', 3);
  if (end === -1) {
    return { meta: null, body: md };
  }
  const yaml = text.slice(3, end).trim();
  const body = text.slice(end + 4).replace(/^\n/, '');
  return { meta: parseManifestoYaml(yaml), body };
}

function parseManifestoYaml(yaml) {
  const meta = {};
  let currentKey = null;

  yaml.split('\n').forEach(line => {
    const trimmed = line.trim();
    if (!trimmed) return;

    const arrayItem = line.match(/^\s+-\s+(.+)$/);
    if (arrayItem && currentKey) {
      if (!Array.isArray(meta[currentKey])) meta[currentKey] = [];
      meta[currentKey].push(parseYamlScalar(arrayItem[1].trim()));
      return;
    }

    const kv = line.match(/^([\w-]+):\s*(.*)$/);
    if (!kv) return;

    currentKey = kv[1];
    const raw = kv[2].trim();
    if (raw === '') {
      meta[currentKey] = [];
    } else {
      meta[currentKey] = parseYamlScalar(raw);
    }
  });

  return meta;
}

function parseYamlScalar(raw) {
  if (raw === 'true') return true;
  if (raw === 'false') return false;
  if (/^\d+$/.test(raw)) return parseInt(raw, 10);
  if ((raw.startsWith('"') && raw.endsWith('"')) || (raw.startsWith("'") && raw.endsWith("'"))) {
    return raw.slice(1, -1);
  }
  return raw;
}

function humanizeSpectrum(value) {
  if (!value) return '';
  return String(value).split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join('-');
}

function humanizeGovernmentOutcome(value) {
  const labels = {
    majority: 'Majority government',
    coalition: 'Coalition government',
    opposition: 'Opposition',
    'confidence-and-supply': 'Confidence and supply',
    'hung-parliament': 'Hung parliament',
    'minority-government': 'Minority government',
  };
  if (labels[value]) return labels[value];
  return humanizeSpectrum(value).replace(/-/g, ' ');
}

function humanizeSectionTag(value) {
  return String(value).split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

function buildManifestoFrontmatterHtml(meta) {
  if (!meta || !Object.keys(meta).length) return '';

  const items = [];
  if (meta.party_leader) {
    items.push(`<span class="manifesto-meta-item"><span class="manifesto-meta-label">Leader</span>${meta.party_leader}</span>`);
  }
  if (meta.political_spectrum) {
    items.push(`<span class="manifesto-meta-item"><span class="manifesto-meta-label">Spectrum</span>${humanizeSpectrum(meta.political_spectrum)}</span>`);
  }
  if (meta.government_outcome) {
    items.push(`<span class="manifesto-meta-item"><span class="manifesto-meta-label">Outcome</span>${humanizeGovernmentOutcome(meta.government_outcome)}</span>`);
  }
  if (meta.victory === true) {
    items.push('<span class="manifesto-victory-badge">✦ Election victory</span>');
  }

  const sections = Array.isArray(meta.sections) && meta.sections.length
    ? `<div class="manifesto-section-tags">${meta.sections.map(s => `<span class="manifesto-section-tag">${humanizeSectionTag(s)}</span>`).join('')}</div>`
    : '';

  return `<div class="manifesto-frontmatter">${items.join('')}${sections}</div>`;
}

function renderManifesto(app, electionId, partyId) {
  const election = getElection(electionId);
  const party    = PARTIES[partyId];
  if (!election || !party) { renderNotFound(app); return; }
  const displayName = getPartyName(partyId, election.year);
  setPageMeta({
    title: `${displayName} ${election.displayYear} Manifesto`,
    description: `Read the ${displayName} manifesto from the ${election.displayYear} UK general election.`,
    path: `/manifesto/${electionId}/${partyId}`,
  });

  app.innerHTML = `
    <div class="manifesto-viewer-page">
      <div class="manifesto-viewer-header">
        <div class="manifesto-viewer-breadcrumb">
          <a href="/election/${election.id}">${election.displayYear} Election</a>
          <span>›</span>
          <a href="/party/${partyId}">${displayName}</a>
          <span>›</span>
          <span>Manifesto</span>
        </div>
        <h1 class="manifesto-viewer-title" style="border-left:4px solid ${party.color}">
          ${displayName}<br><span>${election.displayYear} General Election Manifesto</span>
        </h1>
        <div class="manifesto-viewer-meta">
          <div class="manifesto-viewer-meta-main">
            <span style="color:${party.color}">${election.date}</span>
            <div id="manifesto-frontmatter"></div>
          </div>
          ${hasManifestoPdf(electionId, partyId)
            ? '<a href="/manifestos/' + electionId + '/' + partyId + '/manifesto.pdf" class="manifesto-pdf-btn" target="_blank" rel="noopener">↓ Download PDF</a>'
            : ''}
        </div>
      </div>
      <div class="manifesto-viewer-body">
        <div id="manifesto-content" class="manifesto-content">
          <div class="manifesto-skeleton" role="status" aria-label="Loading manifesto text">
            <div class="skeleton-line skeleton-title"></div>
            <div class="skeleton-line w-40"></div>
            <div class="skeleton-line"></div>
            <div class="skeleton-line"></div>
            <div class="skeleton-line w-85"></div>
            <div class="skeleton-line"></div>
            <div class="skeleton-line w-90"></div>
            <div class="skeleton-line w-60"></div>
            <span class="sr-only">Loading manifesto…</span>
          </div>
        </div>
      </div>
    </div>
  `;

  fetchTyped(`/manifestos/${electionId}/${partyId}/manifesto.md`, 'markdown')
    .then(md => {
      const { meta, body } = splitManifestoFrontmatter(md);
      const frontmatterEl = document.getElementById('manifesto-frontmatter');
      if (frontmatterEl) {
        frontmatterEl.innerHTML = buildManifestoFrontmatterHtml(meta);
      }
      document.getElementById('manifesto-content').innerHTML = parseMarkdown(body);
    })
    .catch(() => {
      document.getElementById('manifesto-content').innerHTML = `
        <div class="manifesto-placeholder-msg">
          <p>No manifesto text file found at <code>manifestos/${electionId}/${partyId}/manifesto.md</code>.</p>
          ${hasManifestoPdf(electionId, partyId)
            ? `<p>You can also <a href="/manifestos/${electionId}/${partyId}/manifesto.pdf" target="_blank" rel="noopener">view the PDF scan</a> if available.</p>`
            : ''}
        </div>`;
    });
}

// Markdown → HTML via Marked (GFM: tables, blockquotes, links, etc.)
function parseMarkdown(md) {
  if (!md) return '';
  if (typeof marked === 'undefined') {
    return '<p class="manifesto-parse-error">Markdown renderer failed to load.</p>';
  }
  const html = marked.parse(md, { gfm: true, breaks: false });
  return html.replace(
    /<a href="(https?:\/\/[^"]+)"/g,
    '<a href="$1" target="_blank" rel="noopener noreferrer"'
  );
}

// ── HUB PAGES ─────────────────────────────────────────────────
function renderElectionsHub(app) {
  setPageMeta({
    title: 'General Elections',
    description: 'Browse all UK general elections from 1945 to 2024 — results, manifestos, and electoral records.',
    path: '/elections',
  });

  const cards = ELECTIONS.slice().reverse().map(electionCardHtml).join('');

  app.innerHTML = `
    ${renderBreadcrumb([
      { label: 'Home', href: '/' },
      { label: 'General Elections' },
    ])}
    <div class="hub-page">
      <header class="hub-page-header">
        <span class="section-label">United Kingdom · 1945–2024</span>
        <h1>General Elections</h1>
        <div class="gold-rule"></div>
        <p>Every postwar UK general election — electoral results, manifesto documents, and campaign records.</p>
      </header>
      <div class="timeline-filter hub-filter" id="hub-elections-filter">
        <button class="filter-btn active" data-filter="all">All</button>
        <button class="filter-btn" data-filter="labour">Labour</button>
        <button class="filter-btn" data-filter="conservative">Conservative</button>
      </div>
      <div class="timeline-grid hub-elections-grid" id="hub-elections-grid">${cards}</div>
    </div>
  `;

  document.querySelectorAll('#hub-elections-filter .filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#hub-elections-filter .filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const f = btn.getAttribute('data-filter');
      document.querySelectorAll('#hub-elections-grid .election-card').forEach(card => {
        card.style.display = (f === 'all' || card.getAttribute('data-winner') === f) ? '' : 'none';
      });
    });
  });
}

function renderDevolvedHub(app) {
  setPageMeta({
    title: 'Devolved Parliaments',
    description: 'Devolved legislatures of the United Kingdom — Scottish Parliament, Welsh Parliament, Northern Ireland Assembly, and London Mayor & Assembly.',
    path: '/devolved',
  });

  const cards = Object.values(DEVOLVED_PORTALS).map(portal => `
    <a href="/devolved/${portal.id}" class="hub-devolved-card">
      <strong>${portal.label}</strong>
      <span class="hub-devolved-sub">${portal.subtitle}</span>
      <p>${portal.description}</p>
      <span class="hub-card-cta">View portal →</span>
    </a>
  `).join('');

  app.innerHTML = `
    ${renderBreadcrumb([
      { label: 'Home', href: '/' },
      { label: 'Devolved Parliaments' },
    ])}
    <div class="hub-page">
      <header class="hub-page-header">
        <span class="section-label">United Kingdom — Devolved Government</span>
        <h1>Devolved Parliaments</h1>
        <div class="gold-rule"></div>
        <p>Legislatures with devolved powers across Scotland, Wales, Northern Ireland, and Greater London.</p>
      </header>
      <div class="hub-devolved-grid">${cards}</div>
    </div>
  `;
}

function renderNationsHub(app) {
  setPageMeta({
    title: 'The Four Nations',
    description: 'Browse the four nations of the United Kingdom — England, Wales, Scotland, and Northern Ireland — with Westminster results and devolved government.',
    path: '/nations',
  });

  const cards = Object.keys(HOME_NATION_ICONS).map(id => {
    const nation = NATIONS[id];
    if (!nation) return '';
    const devolved = nation.devolvedBody
      ? nation.devolvedBody
      : 'No devolved parliament';
    const excerpt = nation.description.length > 160
      ? `${nation.description.slice(0, 160).replace(/\s+\S*$/, '')}…`
      : nation.description;
    return `<a href="/nation/${id}" class="hub-nation-card">
      <div class="hub-nation-icon">${HOME_NATION_ICONS[id]}</div>
      <strong>${nation.name}</strong>
      <span class="hub-nation-meta">${nation.constituencies} Westminster MPs · ${devolved}</span>
      <p>${excerpt}</p>
      <span class="hub-card-cta">View nation →</span>
    </a>`;
  }).join('');

  app.innerHTML = `
    ${renderBreadcrumb([
      { label: 'Home', href: '/' },
      { label: 'Nations' },
    ])}
    <div class="hub-page">
      <header class="hub-page-header">
        <span class="section-label">United Kingdom</span>
        <h1>The Four Nations</h1>
        <div class="gold-rule"></div>
        <p>England, Wales, Scotland, and Northern Ireland — Westminster representation, devolved government, and parties contesting elections in each nation.</p>
      </header>
      <div class="hub-nations-grid">${cards}</div>
    </div>
  `;
}

function renderPartiesHub(app) {
  setPageMeta({
    title: 'Political Parties',
    description: 'Browse political parties by nation — England, Wales, Scotland, Northern Ireland, and other parties.',
    path: '/parties',
  });

  const nationSections = Object.entries(NAV_PARTIES).map(([nationId, nation]) => {
    const partyLinks = nation.parties.map(pid => {
      const p = PARTIES[pid];
      if (!p) return '';
      return `<a href="/party/${pid}" class="hub-party-link">
        <span class="mega-dot" style="background:${p.color}"></span>
        <span>${p.shortName}</span>
      </a>`;
    }).join('');

    let otherLink = '';
    if (nationId === 'scotland') {
      otherLink = `<a href="/devolved/holyrood/other-parties" class="hub-all-others-link">Other Scottish parties →</a>`;
    } else if (nationId === 'wales') {
      otherLink = `<a href="/devolved/senedd/other-parties" class="hub-all-others-link">Other Welsh parties →</a>`;
    } else if (nationId === 'northern-ireland') {
      otherLink = `<a href="/devolved/stormont/other-parties" class="hub-all-others-link">Other Northern Irish parties →</a>`;
    }

    return `<section class="hub-parties-section" aria-labelledby="hub-nation-${nationId}">
      <h2 class="hub-parties-nation-heading" id="hub-nation-${nationId}">
        <a href="/nation/${nationId}">${nation.label}</a>
      </h2>
      <div class="hub-parties-list">${partyLinks}</div>
      ${otherLink}
    </section>`;
  }).join('');

  const featured = typeof OTHERS_FEATURED !== 'undefined' ? OTHERS_FEATURED : OTHERS_PARTIES.slice(0, 6);
  const sortedFeatured = [...featured].sort((a, b) => {
    const nameA = PARTIES[a]?.shortName || '';
    const nameB = PARTIES[b]?.shortName || '';
    return nameA.localeCompare(nameB, 'en-GB');
  });
  const othersLinks = sortedFeatured.map(pid => {
    const p = PARTIES[pid];
    if (!p) return '';
    return `<a href="/party/${pid}" class="hub-party-link">
      <span class="mega-dot" style="background:${p.color}"></span>
      <span>${p.shortName}</span>
    </a>`;
  }).join('');

  app.innerHTML = `
    ${renderBreadcrumb([
      { label: 'Home', href: '/' },
      { label: 'Parties' },
    ])}
    <div class="hub-page">
      <header class="hub-page-header">
        <span class="section-label">Browse by Nation</span>
        <h1>Political Parties</h1>
        <div class="gold-rule"></div>
        <p>Parties contesting UK and devolved elections, organised by the four nations of the United Kingdom.</p>
      </header>
      <div class="hub-parties-grid">
        ${nationSections}
        <section class="hub-parties-section" aria-labelledby="hub-nation-others">
          <h2 class="hub-parties-nation-heading" id="hub-nation-others">
            <a href="/others">Others</a>
          </h2>
          <div class="hub-parties-list">${othersLinks}</div>
          <a href="/others" class="hub-all-others-link">All other parties →</a>
        </section>
      </div>
    </div>
  `;
}

// ── ABOUT PAGE ────────────────────────────────────────────────
function renderAbout(app) {
  setPageMeta({
    title: 'About',
    description: 'About manifestos.org.uk — a digital archive of UK general election manifestos, results, and maps from 1945 to 2024.',
    path: '/about',
  });
  app.innerHTML = `
    <div class="about-section">
      <span class="section-label">About this archive</span>
      <h1>The British<br>Manifesto Archive</h1>
      <p class="about-domain"><a href="https://www.manifestos.org.uk/">www.manifestos.org.uk</a></p>
      <div class="gold-rule"></div>
      <p>A comprehensive resource for the study of British democratic politics, bringing together the manifesto documents, electoral results, and campaign records of every UK general election from 1945 to 2024.</p>
      <p>The archive covers all four nations of the United Kingdom — England, Wales, Scotland and Northern Ireland — including their devolved institutions. Statistical data is sourced from the House of Commons Library Research Briefing CBP-7529, <em>UK Election Statistics: 1918–2023, A Long Century of Elections</em>.</p>

      <h2>Adding Manifesto Documents</h2>
      <p>Place files in:</p>
      <pre style="background:var(--navy-card);border:1px solid var(--navy-border);border-radius:6px;padding:1.25rem;font-size:0.85rem;color:var(--cream-dark);overflow-x:auto;margin:1rem 0">manifestos/{election-id}/{party-id}/manifesto.pdf
manifestos/{election-id}/{party-id}/manifesto.md</pre>
      <p>The <code>.md</code> file will be rendered as a formatted page using <a href="https://marked.js.org/" target="_blank" rel="noopener">Marked</a> (GFM). Supports headings, lists, tables, blockquotes, links, and images.</p>

      <h2>Election IDs</h2>
      <p><code>1945</code> <code>1950</code> <code>1951</code> <code>1955</code> <code>1959</code> <code>1964</code> <code>1966</code> <code>1970</code> <code>feb1974</code> <code>oct1974</code> <code>1979</code> <code>1983</code> <code>1987</code> <code>1992</code> <code>1997</code> <code>2001</code> <code>2005</code> <code>2010</code> <code>2015</code> <code>2017</code> <code>2019</code> <code>2024</code></p>

      <h2>Adding YouTube Videos</h2>
      <p>Add the YouTube video ID (the part after <code>v=</code>) to the <code>youtubeId</code> field in <code>js/data.js</code>.</p>

      <h2>Data Source</h2>
      <p>Electoral statistics sourced from: <em>UK Election Statistics: 1918–2023, A Long Century of Elections</em>, House of Commons Library Research Briefing CBP-7529 (August 2023), by Richard Cracknell, Elise Uberoi and Matthew Burton.</p>

      <h2>Copyright</h2>
      <p>All manifesto documents remain the copyright of their respective political parties. For educational and research purposes only.</p>
    </div>
  `;
}

// ── 404 ───────────────────────────────────────────────────────
function renderNotFound(app) {
  setPageMeta({
    title: 'Not Found',
    description: 'Page not found on manifestos.org.uk.',
    path: getPath(),
    noindex: true,
  });
  app.innerHTML = `<div class="not-found"><h1>404</h1><p>This page could not be found.</p><a href="/">Return to home</a></div>`;
}
