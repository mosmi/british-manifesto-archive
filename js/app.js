/* ============================================================
   THE BRITISH MANIFESTO ARCHIVE — App
   History API SPA routing + page rendering
   ============================================================ */

const SITE = {
  name: SITE_META.name,
  domain: SITE_META.domain,
  url: SITE_META.url,
  description: SITE_META.defaultDescription,
  ogImage: SITE_META.defaultOgImage,
  ogImageWidth: SITE_META.defaultOgImageWidth,
  ogImageHeight: SITE_META.defaultOgImageHeight,
  ogImageAlt: SITE_META.defaultOgImageAlt,
  titleSuffix: SITE_META.titleSuffix,
  homeTitle: SITE_META.homeTitle,
};

// Manifesto text without a PDF scan (electionId/partyId) — legacy override;
// prefer data/manifesto-assets.json once loaded.
const MANIFESTO_TEXT_ONLY = new Set([
  '2001/omrlp',
  '2005/omrlp',
  '2015/omrlp',
]);

function hasManifestoPdf(electionId, partyId) {
  const key = `${electionId}/${partyId}`;
  if (MANIFESTO_TEXT_ONLY.has(key)) return false;
  const assets = getManifestoAssetFlags(electionId, partyId);
  if (assets) return Boolean(assets.pdf);
  const pdfPath = `/manifestos/${electionId}/${partyId}/manifesto.pdf`;
  return Boolean(getPdfSize(pdfPath));
}

let MANIFESTO_ARCHIVE = null;
let _manifestoAssets = null;

async function initManifestoArchive() {
  try {
    const items = await fetchTyped('/data/manifestos-index.json', 'json');
    MANIFESTO_ARCHIVE = new Set(items.map(i => `${i.electionId}/${i.partyId}`));
  } catch {
    MANIFESTO_ARCHIVE = new Set();
  }
}

async function initManifestoAssets() {
  try {
    _manifestoAssets = await fetchTyped(
      `/data/manifesto-assets.json?v=${ASSETS_VERSION}`,
      'json'
    );
  } catch {
    _manifestoAssets = {};
  }
}

function getManifestoAssetFlags(electionId, partyId) {
  if (!_manifestoAssets) return null;
  const key = `${electionId}/${partyId}`;
  // After the inventory loads, a missing key means nothing is on disk for this folder.
  if (Object.prototype.hasOwnProperty.call(_manifestoAssets, key)) {
    return _manifestoAssets[key];
  }
  return { pdf: false, md: false, cover: false };
}

function hasManifestoCover(electionId, partyId) {
  const assets = getManifestoAssetFlags(electionId, partyId);
  if (assets) return Boolean(assets.cover);
  // Unknown until assets load — assume cover may exist (img onerror handles miss).
  return true;
}

function hasManifestoMarkdown(electionId, partyId) {
  const assets = getManifestoAssetFlags(electionId, partyId);
  if (assets) return Boolean(assets.md);
  return MANIFESTO_TEXT_ONLY.has(`${electionId}/${partyId}`)
    || (MANIFESTO_ARCHIVE?.has(`${electionId}/${partyId}`) ?? false);
}

function hasManifestoContent(electionId, partyId) {
  const assets = getManifestoAssetFlags(electionId, partyId);
  if (assets) return Boolean(assets.pdf || assets.md);
  return hasManifestoPdf(electionId, partyId)
    || MANIFESTO_TEXT_ONLY.has(`${electionId}/${partyId}`)
    || (MANIFESTO_ARCHIVE?.has(`${electionId}/${partyId}`) ?? false);
}

// ── PDF File Size Index ───────────────────────────────────────
let _pdfSizes = {};

async function initPdfSizes() {
  try {
    _pdfSizes = await fetchTyped('/data/pdf-sizes.json', 'json');
  } catch {
    _pdfSizes = {};
  }
}

/**
 * Returns a formatted size string for the given PDF URL path,
 * e.g. "4.7 MB", or an empty string if unknown.
 * Exposed globally so devolved modules can call it.
 */
function getPdfSize(path) {
  return _pdfSizes[path] || '';
}
window.getPdfSize = getPdfSize;

// ── SPA route-change accessibility ───────────────────────────
// Creates a visually-hidden live region that announces page titles
// to screen readers on each SPA navigation.
let _liveRegion = null;
function getOrCreateLiveRegion() {
  if (!_liveRegion) {
    _liveRegion = document.createElement('div');
    _liveRegion.setAttribute('aria-live', 'polite');
    _liveRegion.setAttribute('aria-atomic', 'true');
    _liveRegion.className = 'sr-only';
    _liveRegion.id = 'route-announcer';
    document.body.appendChild(_liveRegion);
  }
  return _liveRegion;
}

function announceRouteChange(title) {
  const region = getOrCreateLiveRegion();
  // Brief delay so screen readers pick up the change after DOM settles
  setTimeout(() => {
    region.textContent = '';
    requestAnimationFrame(() => {
      region.textContent = title || document.title;
    });
  }, 100);
}

// ── Progressive image fade-in ─────────────────────────────────
function initLazyImage(img) {
  if (img.classList.contains('img-loaded')) return;
  if (img.complete && img.naturalWidth > 0) {
    img.classList.add('img-loaded');
  } else {
    img.addEventListener('load', () => img.classList.add('img-loaded'), { once: true });
    img.addEventListener('error', () => img.classList.add('img-loaded'), { once: true });
  }
}

function initLazyImages(container) {
  if (!container) return;
  container.querySelectorAll('img.img-lazy').forEach(initLazyImage);
}

function setupLazyImageObserver() {
  const app = document.getElementById('app');
  if (!app) return;

  const observer = new MutationObserver(mutations => {
    mutations.forEach(mutation => {
      mutation.addedNodes.forEach(node => {
        if (node.nodeType === Node.ELEMENT_NODE) {
          if (node.matches && node.matches('img.img-lazy')) {
            initLazyImage(node);
          }
          if (node.querySelectorAll) {
            node.querySelectorAll('img.img-lazy').forEach(initLazyImage);
          }
        }
      });
    });
  });

  observer.observe(app, { childList: true, subtree: true });
}

// Not shown in election-page manifesto lists (no manifestos published)
const MANIFESTO_EXCLUDED_PARTIES = new Set(['speaker', 'independent']);

function setPageTitle(pageTitle) {
  document.title = formatDocumentTitle(pageTitle);
}

function setOgImage(imageUrl, alt) {
  const url = imageUrl || SITE.ogImage;
  const altText = alt || SITE.ogImageAlt;
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
  ensureMeta('og-image', 'property', 'og:image', url);
  ensureMeta('og-image-width', 'property', 'og:image:width', String(SITE.ogImageWidth));
  ensureMeta('og-image-height', 'property', 'og:image:height', String(SITE.ogImageHeight));
  ensureMeta('og-image-alt', 'property', 'og:image:alt', altText);
  ensureMeta('twitter-image', 'name', 'twitter:image', url);
  const twitterCard = document.getElementById('twitter-card');
  if (twitterCard) twitterCard.setAttribute('content', 'summary_large_image');
}

function setPageMeta({ title, description, path = '/', noindex = false } = {}) {
  const pageTitle = formatDocumentTitle(title);
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

  let hreflangEl = document.getElementById('hreflang-link');
  if (!hreflangEl) {
    hreflangEl = document.createElement('link');
    hreflangEl.id = 'hreflang-link';
    hreflangEl.rel = 'alternate';
    hreflangEl.hreflang = 'en-GB';
    document.head.appendChild(hreflangEl);
  }
  hreflangEl.href = canonical;

  const twitterTitle = document.getElementById('twitter-title');
  if (twitterTitle) twitterTitle.setAttribute('content', pageTitle);

  const twitterDesc = document.getElementById('twitter-description');
  if (twitterDesc) twitterDesc.setAttribute('content', pageDescription);

  setOgImage(ogImageForPath(path), ogImageAltForTitle(title));

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

function setInert(el, value) {
  if ('inert' in el) {
    el.inert = value;
  } else {
    if (value) {
      el.setAttribute('aria-hidden', 'true');
      el.style.pointerEvents = 'none';
    } else {
      el.removeAttribute('aria-hidden');
      el.style.pointerEvents = '';
    }
  }
}

const NavController = {
  _open: null,

  open(menu, button, dropdown = null) {
    this.closeAll();
    menu.classList.add('is-open');
    menu.setAttribute('aria-hidden', 'false');
    setInert(menu, false);
    button.setAttribute('aria-expanded', 'true');
    this._open = { menu, button, dropdown };
  },

  closeAll(returnFocusTo = null) {
    if (this._open) {
      this._open.menu.classList.remove('is-open');
      this._open.menu.setAttribute('aria-hidden', 'true');
      setInert(this._open.menu, true);
      this._open.button.setAttribute('aria-expanded', 'false');
      this._open = null;
    }
    document.querySelectorAll('.dropdown-menu.is-open, .dropdown-mega.is-open').forEach(menu => {
      menu.classList.remove('is-open');
      menu.setAttribute('aria-hidden', 'true');
      setInert(menu, true);
    });
    document.querySelectorAll('.nav-dropdown .nav-btn[aria-expanded="true"]').forEach(btn => {
      btn.setAttribute('aria-expanded', 'false');
    });
    if (returnFocusTo) returnFocusTo.focus();
  },

  isOpen() {
    return this._open !== null;
  }
};

function closeAllNavMenus(returnFocusTo = null) {
  NavController.closeAll(returnFocusTo);
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
    NavController.open(menu, button, dropdown);
  };

  const hide = () => {
    clearTimeout(hideTimer);
    hideTimer = setTimeout(() => {
      if (!dropdown.contains(document.activeElement) && !dropdown.matches(':hover') && !menu.matches(':hover')) {
        NavController.closeAll();
      }
    }, 150);
  };

  const toggle = () => {
    const isOpen = menu.classList.contains('is-open');
    if (isOpen) NavController.closeAll(button);
    else show();
  };

  button.addEventListener('click', e => {
    e.preventDefault();
    toggle();
  });

  button.addEventListener('keydown', e => {
    if (e.key === 'Escape' && menu.classList.contains('is-open')) {
      e.preventDefault();
      NavController.closeAll(button);
    }
  });

  const setupHoverHandlers = () => {
    if (HOVER_FINE.matches && window.innerWidth > 640) {
      dropdown.addEventListener('mouseenter', show);
      dropdown.addEventListener('mouseleave', hide);
      menu.addEventListener('mouseenter', show);
      menu.addEventListener('mouseleave', hide);
    }
  };

  setupHoverHandlers();

  dropdown.addEventListener('focusout', e => {
    setTimeout(() => {
      if (!dropdown.contains(document.activeElement) && NavController._open?.menu === menu) {
        NavController.closeAll();
      }
    }, 10);
  });

  menu.addEventListener('click', e => {
    if (e.target.closest('a')) {
      NavController.closeAll();
    }
  });
}

document.addEventListener('click', e => {
  if (NavController.isOpen() && !NavController._open.dropdown?.contains(e.target) && !NavController._open.menu?.contains(e.target)) {
    NavController.closeAll();
  }
});

document.addEventListener('keydown', e => {
  if (e.key === 'Escape' && NavController.isOpen()) {
    const btn = NavController._open.button;
    NavController.closeAll(btn);
  }
});

document.addEventListener('DOMContentLoaded', async () => {
  initTheme();
  await Promise.all([initManifestoArchive(), initManifestoAssets(), initPdfSizes()]);
  buildNav();
  setupMobileMenu();
  setupNavDropdowns();
  setupSearch();
  setupThemeToggle();
  setupLazyImageObserver();
  setupRouter();
  route();
});

const THEME_STORAGE_KEY = 'bma-theme';
let _refreshThemeToggle = null;

function systemPrefersLight() {
  return window.matchMedia('(prefers-color-scheme: light)').matches;
}

/** Explicit localStorage choice wins; otherwise follow the OS. */
function resolveTheme() {
  const stored = localStorage.getItem(THEME_STORAGE_KEY);
  if (stored === 'light' || stored === 'dark') return stored;
  return systemPrefersLight() ? 'light' : 'dark';
}

function initTheme() {
  applyTheme(resolveTheme());

  const mq = window.matchMedia('(prefers-color-scheme: light)');
  const onSystemThemeChange = () => {
    // Stay out of the way once the user has toggled a preference.
    if (localStorage.getItem(THEME_STORAGE_KEY)) return;
    applyTheme(resolveTheme());
    if (typeof route === 'function') route();
  };
  if (typeof mq.addEventListener === 'function') {
    mq.addEventListener('change', onSystemThemeChange);
  } else if (typeof mq.addListener === 'function') {
    mq.addListener(onSystemThemeChange); // older Safari
  }
}

function applyTheme(theme) {
  const isLight = theme === 'light';
  if (isLight) {
    document.documentElement.setAttribute('data-theme', 'light');
  } else {
    document.documentElement.removeAttribute('data-theme');
  }
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.setAttribute('content', isLight ? '#f7f3ea' : '#090e1c');
  if (typeof _refreshThemeToggle === 'function') _refreshThemeToggle();
}

function setupThemeToggle() {
  const btn = document.getElementById('theme-toggle');
  if (!btn) return;
  const refresh = () => {
    const isLight = document.documentElement.getAttribute('data-theme') === 'light';
    btn.textContent = isLight ? '☾ Dark' : '☀ Light';
    btn.setAttribute('aria-pressed', String(isLight));
  };
  _refreshThemeToggle = refresh;
  refresh();
  btn.addEventListener('click', () => {
    const isLight = document.documentElement.getAttribute('data-theme') === 'light';
    const next = isLight ? 'dark' : 'light';
    localStorage.setItem(THEME_STORAGE_KEY, next);
    applyTheme(next);
    refresh();
    route();
  });
}

// ── Router ────────────────────────────────────────────────────
function getPath() {
  let path = window.location.pathname || '/';
  if (path.length > 1 && path.endsWith('/')) path = path.slice(0, -1);
  return path || '/';
}

function navigate(path, { replace = false } = {}) {
  const normalized = path.startsWith('/') ? path : `/${path}`;
  const current = `${window.location.pathname}${window.location.search}${window.location.hash}`;
  if (replace) {
    history.replaceState(null, '', normalized);
  } else if (current !== normalized) {
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
    if (a.hasAttribute('download')) return;
    if (/\.(pdf|png|jpe?g|webp|svg|zip|md)$/i.test(href.split('?')[0])) return;
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
  
  // Close all navigation menus on page transition
  NavController.closeAll();
  closeMobileMenu();

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
  } else if (path === '/devolved/euro/other-parties') {
    renderEuroOtherParties(app);
  } else if (path.startsWith('/devolved/euro/')) {
    renderEuroElection(app, path.replace('/devolved/euro/', ''));
  } else if (path === '/devolved/euro') {
    renderEuroPortal(app);
  } else if (path.startsWith('/devolved/')) {
    renderDevolved(app, path.replace('/devolved/', ''));
  } else if (path === '/others') {
    renderOthers(app);
  } else if (path.startsWith('/manifesto/')) {
    const parts = path.split('/').filter(Boolean);
    if (parts.length >= 4) {
      // Legacy London ids: /manifesto/london/gla-2000/slug → /manifesto/london/2000/slug
      let electionSeg = parts[2];
      if (parts[1] === 'london') {
        const legacy = String(electionSeg).match(/^(?:gla|glc|lcc)-(\d{4})$/);
        if (legacy) {
          navigate(`/manifesto/london/${legacy[1]}/${parts[3]}`, { replace: true });
          return;
        }
      }
      renderManifesto(app, parts[1] + '/' + electionSeg, parts[3]);
    } else {
      renderManifesto(app, parts[1], parts[2]);
    }
  } else if (path === '/elections') {
    renderElectionsHub(app);
  } else if (path === '/devolved') {
    renderDevolvedHub(app);
  } else if (path === '/parties' || path === '/parties/all') {
    renderPartiesHub(app, path === '/parties/all');
  } else if (path === '/nations') {
    renderNationsHub(app);
  } else if (path === '/about') {
    renderAbout(app);
  } else {
    renderNotFound(app);
  }
  window.scrollTo({ top: 0, behavior: 'instant' });
  // Honour in-page anchors after SPA render (route always resets scroll above)
  const hashId = decodeURIComponent((window.location.hash || '').replace(/^#/, ''));
  if (hashId) {
    const hashTarget = document.getElementById(hashId);
    if (hashTarget) {
      requestAnimationFrame(() => {
        hashTarget.scrollIntoView({ behavior: 'instant', block: 'start' });
      });
    }
  }
  // Trigger fade-in for any lazy cover images rendered by this route
  initLazyImages(document.getElementById('app'));
  // Move focus to main landmark so keyboard/SR users know the page changed
  const mainEl = document.getElementById('app');
  if (mainEl) {
    mainEl.focus();
  }
  // Announce the new page title to screen readers
  announceRouteChange(document.title);
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
  return devolvedPartyLink(id, label, year);
}

function nationLink(id, label) {
  if (!NATIONS[id]) return label;
  return `<a href="/nation/${id}" class="inline-nation-link">${label}</a>`;
}

/** Flag emoji (aria-hidden) + text for nation group headings (I13). */
const NATION_HEADING_PARTS = {
  england: { flag: '🏴󠁧󠁢󠁥󠁮󠁧󠁿', text: 'England & UK-wide' },
  scotland: { flag: '🏴󠁧󠁢󠁳󠁣󠁴󠁿', text: 'Scotland' },
  wales: { flag: '🏴󠁧󠁢󠁷󠁬󠁳󠁿', text: 'Wales' },
  'northern-ireland': { flag: '🇮🇪', text: 'Northern Ireland' },
  others: { flag: '', text: 'Other Parties' },
  alliances: { flag: '🇪🇺', text: 'Alliances' },
};

function nationHeadingLabelHtml(nationId) {
  const parts = NATION_HEADING_PARTS[nationId];
  if (!parts) return nationId;
  const flag = parts.flag
    ? `<span aria-hidden="true">${parts.flag}</span> `
    : '';
  return `${flag}${parts.text}`;
}

function partyBreadcrumbItems(party) {
  const crumbs = [
    { label: 'Home', href: '/' },
    { label: 'Parties', href: '/parties' },
  ];
  // `nation: 'england'` is the mega-menu "England & UK-wide" bucket (Labour,
  // Conservatives, Reform UK, …). Do not insert a bare "England" crumb for those
  // parties — they are not England-only. Territorial nations keep their crumb.
  const nationId = party.nation && party.nation !== 'others' ? party.nation : null;
  if (nationId && nationId !== 'england' && typeof getNationLabel === 'function') {
    crumbs.push({ label: getNationLabel(nationId), href: `/nation/${nationId}` });
  }
  crumbs.push({ label: party.shortName });
  return crumbs;
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
    a.className = 'dropdown-item-with-dot';
    a.innerHTML = `<span class="type-dot dot-${portal.id}" aria-hidden="true"></span><div class="dropdown-text"><strong>${portal.label}</strong><span class="dropdown-sub">${portal.subtitle}</span></div>`;
    el.appendChild(a);
  });
  const hub = document.createElement('a');
  hub.href = '/devolved';
  hub.className = 'mega-all-link';
  hub.textContent = 'All elections beyond Westminster →';
  el.appendChild(hub);
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
      a.className = 'dropdown-item-with-dot';
      a.innerHTML = `<span class="type-dot dot-uk" aria-hidden="true"></span><span>${e.displayYear} — ${PARTIES[e.winner]?.shortName || ''}</span>`;
      el.appendChild(a);
    });
  });
  const hub = document.createElement('a');
  hub.href = '/elections';
  hub.className = 'mega-all-link';
  hub.textContent = 'All UK general elections →';
  el.appendChild(hub);
}

/** Mega-menu label — Reform stays one party page with nation-qualified labels. */
function megaPartyLabel(nationId, pid) {
  if (pid === 'reform') {
    if (nationId === 'scotland') return 'Reform UK Scotland';
    if (nationId === 'wales') return 'Reform UK Wales';
  }
  return PARTIES[pid]?.shortName || pid;
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
    const partyIds = nation.megaParties || nation.parties;
    partyIds.forEach(pid => {
      const p = PARTIES[pid];
      if (!p) return;
      const a = document.createElement('a');
      a.href = `/party/${pid}`;
      a.className = 'mega-party-link';
      const dot = document.createElement('span');
      dot.className = 'mega-dot';
      if (typeof dotStyle === 'function') dot.setAttribute('style', dotStyle(p.color));
      else dot.style.background = p.color;
      a.appendChild(dot);
      a.appendChild(document.createTextNode(megaPartyLabel(nationId, pid)));
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
    if (nationId === 'europe') {
      const epOthers = document.createElement('a');
      epOthers.href = '/devolved/euro/other-parties';
      epOthers.className = 'mega-all-link';
      epOthers.textContent = 'Other EP parties →';
      col.appendChild(epOthers);
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
    if (typeof dotStyle === 'function') dot.setAttribute('style', dotStyle(p.color));
    else dot.style.background = p.color;
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

  const hub = document.createElement('a');
  hub.href = '/parties/all';
  hub.className = 'mega-all-link mega-hub-link';
  hub.textContent = 'All parties →';
  mega.appendChild(hub);
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
          <nav class="hero-ways" aria-label="Ways into the archive">
            <p class="hero-ways-kicker">Four ways in</p>
            <ul class="hero-ways-list">
              <li><a href="/elections"><span class="hero-ways-label">Westminster</span><span class="hero-ways-hint">General elections</span></a></li>
              <li><a href="/devolved"><span class="hero-ways-label">Beyond Westminster</span><span class="hero-ways-hint">Devolved &amp; European</span></a></li>
              <li><a href="/nations"><span class="hero-ways-label">Nations</span><span class="hero-ways-hint">By place</span></a></li>
              <li><a href="/parties"><span class="hero-ways-label">Parties</span><span class="hero-ways-hint">Every platform</span></a></li>
            </ul>
          </nav>
          <div class="hero-stats">
            <div><div class="hero-stat-num">71</div><div class="hero-stat-label">Elections</div></div>
            <div><div class="hero-stat-num">${Object.keys(PARTIES).filter(k => k !== 'others').length}</div><div class="hero-stat-label">Parties</div></div>
            <div><div class="hero-stat-num">650</div><div class="hero-stat-label">Commons Seats</div></div>
            <div><div class="hero-stat-num">4</div><div class="hero-stat-label">Nations</div></div>
          </div>
        </header>

        <!-- Mobile Accordion Selector -->
        <div class="mobile-accordion-section" id="mobile-accordion-section">
          <div style="text-align:center;color:var(--text-muted);padding:2rem;">Loading election selector…</div>
        </div>

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
              <div class="parliament-legend home-chart-legend" id="home-chart-legend"></div>
            </div>

            <div class="election-slider-panel">
              <div class="slider-wrap">
                <button type="button" class="slider-step-btn" id="slider-prev" aria-label="Previous election">◀</button>
                <div class="slider-track-wrap" style="position: relative; flex: 1; margin: 0 10px; padding-top: 20px;">
                  <div class="slider-year-badge" id="slider-year-badge"></div>
                  <div class="slider-thumb-marker" id="slider-thumb-marker" aria-hidden="true"></div>
                  <div class="slider-election-ticks" id="slider-election-ticks" aria-hidden="true"></div>
                  <input type="range" class="election-slider" id="election-slider" min="0" max="${ELECTIONS.length - 1}" value="${_homeElectionIndex}" aria-label="Select general election year" style="margin: 0; width: 100%;">
                  <div class="slider-ticks" id="slider-ticks" style="margin-top: 6px;"></div>
                </div>
                <button type="button" class="slider-step-btn" id="slider-next" aria-label="Next election">▶</button>
              </div>
            </div>
          </div>

          <aside class="dashboard-sidebar" id="dashboard-sidebar" aria-label="Election timeline"></aside>
        </div>
      </div>
    </section>

    <section class="latest-section">
      <div class="latest-header">
        <div>
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

    <section class="browse-section nations-browse-section">
      <div class="browse-section-inner">
        <div class="browse-section-header">
          <h2>Browse by Nation</h2>
          <div class="gold-rule"></div>
        </div>
        <p class="browse-section-lede">Party geography and Westminster results by nation. For devolved legislatures, use <a href="/devolved">Beyond Westminster</a>.</p>
        <div class="nations-grid" id="nations-grid"></div>
        <a href="/nations" class="browse-section-link">Explore all four nations →</a>
      </div>
    </section>

    <section class="browse-section parties-browse-section">
      <div class="browse-section-inner">
        <div class="browse-section-header">
          <h2>Browse by Party</h2>
          <div class="gold-rule"></div>
        </div>
        <div class="parties-grid" id="featured-parties-grid"></div>
        <a href="/parties" class="browse-section-link">View all parties →</a>
      </div>
    </section>
  `;

  renderNationsGrid();
  renderFeaturedPartiesGrid();
  initHomeDashboard();
  loadLatestManifestos();

  // Load devolved and euro indexes in parallel to build the mobile accordion selector
  const portals = ['holyrood', 'senedd', 'stormont', 'london', 'euro'];
  Promise.all(portals.map(async id => {
    try {
      const idx = await fetchTyped(`/data/devolved/${id}/index.json`, 'json');
      return idx.map(e => ({ ...e, type: id }));
    } catch {
      return [];
    }
  })).then(results => {
    const westminster = ELECTIONS.map(e => ({
      id: e.id,
      year: e.year,
      displayYear: e.displayYear,
      title: `${e.displayYear} UK General Election`,
      type: 'uk',
      url: `/election/${e.id}`
    }));

    const allElections = [...westminster];
    results.flat().forEach(e => {
      let title = '';
      let url = '';
      if (e.type === 'holyrood') {
        title = `${e.displayYear} Scottish Parliament`;
        url = `/devolved/holyrood/${e.id}`;
      } else if (e.type === 'senedd') {
        title = `${e.displayYear} Welsh Parliament`;
        url = `/devolved/senedd/${e.id}`;
      } else if (e.type === 'stormont') {
        title = `${e.displayYear} Northern Ireland Assembly`;
        url = `/devolved/stormont/${e.id}`;
      } else if (e.type === 'london') {
        title = `${e.displayYear} London Mayor & Assembly`;
        url = `/devolved/london/${e.id}`;
      } else if (e.type === 'euro') {
        title = `${e.displayYear} European Parliament`;
        url = `/devolved/euro/${e.id}`;
      }
      allElections.push({
        id: e.id,
        year: e.year,
        displayYear: e.displayYear,
        title,
        type: e.type,
        url
      });
    });

    // Group by decade
    const groups = {};
    allElections.forEach(e => {
      const decade = Math.floor(e.year / 10) * 10;
      const decadeLabel = `${decade}s`;
      if (!groups[decadeLabel]) groups[decadeLabel] = [];
      groups[decadeLabel].push(e);
    });

    const typeOrder = { uk: 0, holyrood: 1, senedd: 2, stormont: 3, london: 4, euro: 5 };
    Object.keys(groups).forEach(decadeLabel => {
      groups[decadeLabel].sort((a, b) => {
        if (b.year !== a.year) return b.year - a.year;
        return (typeOrder[a.type] ?? 99) - (typeOrder[b.type] ?? 99);
      });
    });

    const sortedDecades = Object.keys(groups).sort((a, b) => b.localeCompare(a));

    const accordionSection = document.getElementById('mobile-accordion-section');
    if (accordionSection) {
      accordionSection.innerHTML = sortedDecades.map((dec, i) => {
        const bodyId = `accordion-body-${dec.replace(/\s/g, '-')}`;
        const headerId = `accordion-header-${dec.replace(/\s/g, '-')}`;
        const isOpen = i === 0;
        const listHtml = groups[dec].map(e => `
          <a href="${e.url}" class="election-item">
            <span class="type-dot dot-${e.type}" aria-hidden="true"></span>
            <span class="election-label">${e.title}</span>
            <span class="election-arrow" aria-hidden="true">›</span>
          </a>
        `).join('');

        return `
          <div class="accordion-item${isOpen ? ' open' : ''}" data-decade="${dec}">
            <button type="button"
              class="accordion-header${isOpen ? ' open' : ''}"
              id="${headerId}"
              aria-expanded="${isOpen}"
              aria-controls="${bodyId}">
              <span>${dec} <span class="count">(${groups[dec].length} elections)</span></span>
              <span class="chevron" aria-hidden="true"${isOpen ? ' style="transform:rotate(90deg);color:var(--gold);"' : ''}>▶</span>
            </button>
            <div class="accordion-body" id="${bodyId}" role="region" aria-labelledby="${headerId}"${isOpen ? '' : ' hidden'}>
              ${listHtml}
            </div>
          </div>
        `;
      }).join('');

      // Add event listeners to toggle accordion
      accordionSection.querySelectorAll('.accordion-item').forEach(item => {
        const header = item.querySelector('.accordion-header');
        const chevron = item.querySelector('.chevron');
        const bodyId = header.getAttribute('aria-controls');
        const body = document.getElementById(bodyId);

        header.addEventListener('click', () => {
          const isOpen = item.classList.contains('open');

          // Collapse all other items
          accordionSection.querySelectorAll('.accordion-item').forEach(el => {
            el.classList.remove('open');
            const h = el.querySelector('.accordion-header');
            const c = el.querySelector('.chevron');
            const bId = h.getAttribute('aria-controls');
            const b = document.getElementById(bId);
            h.classList.remove('open');
            h.setAttribute('aria-expanded', 'false');
            c.style.transform = '';
            c.style.color = '';
            if (b) b.hidden = true;
          });

          if (!isOpen) {
            item.classList.add('open');
            header.classList.add('open');
            header.setAttribute('aria-expanded', 'true');
            chevron.style.transform = 'rotate(90deg)';
            chevron.style.color = 'var(--gold)';
            if (body) body.hidden = false;
          }
        });
      });
    }
  });
}


function initHomeDashboard() {
  const slider = document.getElementById('election-slider');
  if (!slider) return;

  buildSliderTicks();

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

const SLIDER_YEAR_START = 1945;
const SLIDER_YEAR_END = 2024;
const SLIDER_YEAR_SPAN = SLIDER_YEAR_END - SLIDER_YEAR_START;
const SLIDER_LABEL_YEARS = [1945, 1955, 1966, 1974, 1987, 2001, 2015, 2024];

function electionCalendarYear(election) {
  if (election.id === 'feb1974') return 1974.12;
  if (election.id === 'oct1974') return 1974.79;
  return election.year;
}

function calendarYearToSliderPct(y) {
  return ((y - SLIDER_YEAR_START) / SLIDER_YEAR_SPAN) * 100;
}

function electionIndexToSliderPct(idx) {
  const election = ELECTIONS[idx];
  return election ? calendarYearToSliderPct(electionCalendarYear(election)) : 0;
}

function electionIndexForLabelYear(y) {
  if (y === 1974) return ELECTIONS.findIndex(e => e.id === 'feb1974');
  if (y === 2024) return ELECTIONS.length - 1;
  return ELECTIONS.findIndex(e => e.year === y);
}

function positionSliderThumb(idx) {
  const pct = electionIndexToSliderPct(idx);
  const thumbOffset = `calc(${pct}% + (${8 - pct * 0.16}px))`;
  const badge = document.getElementById('slider-year-badge');
  const marker = document.getElementById('slider-thumb-marker');
  if (badge) badge.style.left = thumbOffset;
  if (marker) marker.style.left = thumbOffset;

  document.querySelectorAll('.slider-election-tick').forEach(el => {
    el.classList.toggle('is-active', parseInt(el.getAttribute('data-idx'), 10) === idx);
  });
}

function buildSliderTicks() {
  const electionTicksEl = document.getElementById('slider-election-ticks');
  if (electionTicksEl) {
    electionTicksEl.innerHTML = ELECTIONS.map((e, idx) => {
      const pct = electionIndexToSliderPct(idx);
      return `<button type="button" class="slider-election-tick" style="left:${pct}%" data-idx="${idx}" aria-label="${e.displayYear || e.year} election"></button>`;
    }).join('');

    electionTicksEl.querySelectorAll('.slider-election-tick').forEach(btn => {
      btn.addEventListener('click', () => {
        _homeElectionIndex = parseInt(btn.getAttribute('data-idx'), 10);
        const slider = document.getElementById('election-slider');
        if (slider) slider.value = _homeElectionIndex;
        updateHomeDashboard(_homeElectionIndex);
      });
    });
  }

  const el = document.getElementById('slider-ticks');
  if (!el) return;

  el.innerHTML = SLIDER_LABEL_YEARS.map(y => {
    const pct = calendarYearToSliderPct(y);
    const idx = electionIndexForLabelYear(y);
    const shift = y === SLIDER_YEAR_START ? '0%' : (y === SLIDER_YEAR_END ? '-100%' : '-50%');
    return `<button type="button" class="slider-tick" style="left:${pct}%;--tick-shift:${shift}" data-idx="${idx}">${y}</button>`;
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

function updateHomeDashboard(idx) {
  const election = ELECTIONS[idx];
  if (!election) return;

  const winner = PARTIES[election.winner] || {};
  const winnerSeats = (election.results.find(r => r.party === election.winner) || {}).seats || 0;
  const winnerPct = (election.results.find(r => r.party === election.winner) || {}).percentage || 0;

  const dashboard = document.getElementById('home-dashboard');
  if (dashboard) {
    dashboard.style.removeProperty('--party-glow');
    dashboard.style.removeProperty('--party-accent');
  }

  const label = document.getElementById('dashboard-election-label');
  if (label) label.textContent = `${election.displayYear} General Election`;

  const meta = document.getElementById('dashboard-election-meta');
  if (meta) {
    const winnerColour = typeof partyTextColour === 'function'
      ? partyTextColour(election.winner, election.year)
      : getPartyColor(election.winner, election.year);
    meta.innerHTML = `<span style="color:${winnerColour}">${winner.shortName || ''}</span> victory · ${winnerSeats} seats · ${winnerPct > 0 ? winnerPct.toFixed(1) + '% vote' : election.pm}`;
  }

  const link = document.getElementById('dashboard-election-link');
  if (link) link.href = `/election/${election.id}`;

  const chart = document.getElementById('home-parliament-chart');
  if (chart) drawParliamentChart(chart, election.results, election.totalSeats, election.year);

  const theme = typeof getCurrentTheme === 'function' ? getCurrentTheme() : 'dark';
  const thumbColor = theme === 'light'
    ? '#e4003b'
    : (typeof barColour === 'function'
      ? barColour(getPartyColor(election.winner, election.year), theme)
      : getPartyColor(election.winner, election.year));

  const badge = document.getElementById('slider-year-badge');
  if (badge) {
    badge.textContent = election.displayYear || election.year;
    badge.style.backgroundColor = thumbColor;
    badge.style.setProperty('--party-color', thumbColor);
  }

  const marker = document.getElementById('slider-thumb-marker');
  if (marker) marker.style.setProperty('--slider-thumb', thumbColor);

  positionSliderThumb(idx);

  const legend = document.getElementById('home-chart-legend');
  if (legend) buildParliamentLegend(legend, election.results, election.year);

  buildDashboardSidebar(idx);
}

// Historical popular vote shares lookup by election.id to solve missing data
const HISTORICAL_SHARES = {
  snp: {
    '1970': 1.1,
    'feb1974': 2.0,
    'oct1974': 2.9,
    '1979': 1.6,
    '1983': 1.1,
    '1987': 1.3,
    '1992': 1.9,
    '1997': 2.0,
    '2001': 1.8,
    '2005': 1.5,
    '2010': 1.7
  },
  plaid: {
    'feb1974': 0.6,
    'oct1974': 0.6,
    '1979': 0.4,
    '1983': 0.4,
    '1987': 0.4,
    '1992': 0.5,
    '1997': 0.5,
    '2001': 0.6,
    '2005': 0.6,
    '2010': 0.6,
    '2015': 0.6,
    '2017': 0.5,
    '2019': 0.5
  },
  green: {
    '2010': 1.0,
    '2017': 1.6,
    '2019': 2.7
  },
  ukip: {
    '2015': 12.6
  }
};

function getHistoricalPercentage(partyId, electionId, dbPct) {
  if (dbPct > 0) return dbPct; // use DB value if populated
  return HISTORICAL_SHARES[partyId]?.[electionId] || 0;
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
    const accent = typeof partyAccentDerivedForYear === 'function'
      ? partyAccentDerivedForYear(e.winner, e.year)
      : { surface: winner.color, kicker: winner.color };
    return `<a href="/election/${e.id}" class="timeline-card${active}" style="--card-accent:${accent.surface}">
      <div class="timeline-card-year">${e.displayYear}</div>
      <div class="timeline-card-party" style="color:${accent.kicker}">${winner.shortName || ''}</div>
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

  fetchTyped(`/data/latest-additions.json?v=${ASSETS_VERSION}`, 'json')
    .then(items => {
      if (!items.length) {
        track.innerHTML = '<p class="latest-empty">Manifesto documents will appear here as they are added to the archive.</p>';
        return;
      }

      track.innerHTML = items.map(item => {
        const party = PARTIES[item.partyId] || {};
        const displayYear = item.year || item.electionId;
        const yearNum = parseInt(String(displayYear).replace(/\D/g, '').slice(0, 4), 10);
        const partyLabel = (typeof getPartyName === 'function' && item.partyId)
          ? getPartyName(item.partyId, Number.isFinite(yearNum) ? yearNum : null)
          : (party.shortName || item.partyId);
        const cover = item.cover || `/manifestos/${item.electionId}/${item.partyId}/cover.png?v=${ASSETS_VERSION}`;
        const coverFb = item.coverFallback || `/manifestos/${item.electionId}/${item.partyId}/cover.jpg?v=${ASSETS_VERSION}`;
        const rawTitle = item.title || item.label || `${partyLabel} ${displayYear}`;
        // Titles from the index often end with the year ("… Manifesto 1992"); euro
        // slogan titles do not — always render year as its own line for consistency.
        const yearStr = String(displayYear || '').trim();
        const title = yearStr && new RegExp(`\\b${yearStr.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*$`).test(rawTitle)
          ? rawTitle.replace(new RegExp(`\\s*${yearStr.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*$`), '').trim()
          : rawTitle;
        const url = item.url || `/manifesto/${item.electionId}/${item.partyId}`;
        const target = item.isPdf ? ' target="_blank" rel="noopener"' : '';

        const accent = typeof partyAccentDerived === 'function'
          ? partyAccentDerived(item.partyId)
          : { kicker: party.color || '#c9a84c', surface: party.color || '#333' };
        const ghostColour = typeof ghostTint === 'function'
          ? ghostTint(accent.raw || party.color, getCurrentTheme())
          : accent.surface;

        return `<a href="${url}" class="latest-card"${target} style="--party-color:${accent.surface};--party-ghost:${ghostColour}">
          <div class="latest-card-cover">
            <img src="${cover}?v=${ASSETS_VERSION}" alt="Cover of the ${rawTitle}" class="img-lazy" loading="lazy" decoding="async" onerror="if(this.dataset.fb){this.style.display='none';this.nextElementSibling.style.display='flex';}else{this.dataset.fb=1;this.src='${coverFb}';}">
            <div class="latest-card-cover-fallback" style="--party-surface:${accent.surface};--party-ghost:${ghostColour}" aria-hidden="true"><span class="latest-cover-label">Scan unavailable</span></div>
          </div>
          <div class="latest-card-body">
            <div class="latest-card-party" style="color:${accent.kicker}">${partyLabel}</div>
            <div class="latest-card-title">${title}</div>
            ${yearStr ? `<div class="latest-card-year">${yearStr}</div>` : ''}
          </div>
        </a>`;
      }).join('');

      initLazyImages(track);
      setupLatestCarousel();
    })
    .catch(() => {
      if (typeof renderDataError === 'function') {
        renderDataError(track, {
          message: 'Latest additions failed to load.',
          onRetry: () => loadLatestManifestos(),
        });
      } else {
        track.innerHTML = '<p class="latest-empty" role="alert">Latest additions failed to load.</p>';
      }
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

function electionWinnerLabel(e) {
  const winner = PARTIES[e.winner] || {};
  const winnerResult = (e.results || []).find(r => r.party === e.winner);
  const seats = winnerResult?.seats || 0;
  const threshold = getMajorityThreshold(e.totalSeats || 650);
  const name = winner.shortName || winner.name || '';
  if (seats >= threshold) return `${name} victory · ${seats} seats`;
  return `${name} minority · ${seats} seats`;
}

function electionSeatBarHtml(e) {
  const theme = typeof getCurrentTheme === 'function' ? getCurrentTheme() : 'dark';
  const sorted = (e.results || []).filter(r => r.seats > 0).sort((a, b) => b.seats - a.seats);
  const top3 = sorted.slice(0, 3);
  const restSeats = sorted.slice(3).reduce((s, r) => s + r.seats, 0);
  let html = top3.map(r => {
    const raw = getPartyColor(r.party, e.year);
    const bg = typeof barColour === 'function'
      ? barColour(raw, theme)
      : (typeof surfaceColour === 'function' ? surfaceColour(raw, theme) : raw);
    return `<div class="seats-segment" style="flex:${r.seats};background:${bg}"></div>`;
  }).join('');
  if (restSeats > 0) {
    html += `<div class="seats-segment" style="flex:${restSeats};background:#4a5364"></div>`;
  }
  return html;
}

function electionCardHtml(e) {
  const theme = typeof getCurrentTheme === 'function' ? getCurrentTheme() : 'dark';
  const accent = typeof partyAccentDerivedForYear === 'function'
    ? partyAccentDerivedForYear(e.winner, e.year, theme)
    : { surface: getPartyColor(e.winner, e.year), kicker: getPartyColor(e.winner, e.year), border: `rgba(255,255,255,0.07)`, raw: getPartyColor(e.winner, e.year) };
  const ghostDigits = String(e.displayYear || e.year).replace(/\D/g, '').slice(-2) || String(e.year).slice(-2);
  const longLabel = String(e.displayYear).includes(' ') || String(e.displayYear).length > 5;
  const ghostColour = typeof ghostTint === 'function'
    ? ghostTint(accent.raw, theme)
    : (typeof rgbaHex === 'function' ? rgbaHex(accent.raw, 0.07) : accent.raw);
  return `<a href="/election/${e.id}" class="election-card" data-winner="${e.winner}" style="--party-border:${accent.border};--party-ghost:${ghostColour};--party-kicker:${accent.kicker};--party-surface:${accent.surface}">
    <div class="card-ghost-year" aria-hidden="true">${ghostDigits}</div>
    <span class="election-type-chip">General election</span>
    <div class="card-year${longLabel ? ' long-label' : ''}">${e.displayYear}</div>
    <div class="card-date">${e.date}</div>
    <div class="card-winner"><div class="card-winner-dot"></div>${electionWinnerLabel(e)}</div>
    <div class="card-pm">PM: <span>${e.pm}</span></div>
    <div class="card-seats-bar">${electionSeatBarHtml(e)}</div>
  </a>`;
}

const HOME_NATION_ICONS = {
  england: '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
  wales: '🏴󠁧󠁢󠁷󠁬󠁳󠁿',
  scotland: '🏴󠁧󠁢󠁳󠁣󠁴󠁿',
  'northern-ireland': '🇮🇪',
};
const NATION_ICONS = { ...HOME_NATION_ICONS, europe: '🇪🇺' };
const NATIONS_HUB_ORDER = ['england', 'wales', 'scotland', 'northern-ireland', 'europe'];

const NATION_CARD_ACCENTS = {
  england: { border: 'rgba(224,90,90,0.3)' },
  wales: { border: 'rgba(224,90,100,0.3)' },
  scotland: { border: 'rgba(90,150,220,0.3)' },
  'northern-ireland': { border: 'rgba(158,195,230,0.3)' },
};

function nationHubMetaLine(id) {
  const nation = NATIONS[id];
  if (!nation) return '';
  const devolved = id === 'europe'
    ? 'European Parliament (1979–2019)'
    : (nation.devolvedBody ? nation.devolvedBody : 'No devolved parliament');
  return id === 'europe'
    ? `${nation.constituencies} UK MEPs (2019) · ${devolved}`
    : `${nation.constituencies} Westminster MPs · ${devolved}`;
}

function buildNationHubCardHtml(id) {
  const nation = NATIONS[id];
  if (!nation) return '';
  const meta = nationHubMetaLine(id);
  const excerpt = nation.description.length > 160
    ? `${nation.description.slice(0, 160).replace(/\s+\S*$/, '')}…`
    : nation.description;
  const accent = NATION_CARD_ACCENTS[id] || { border: 'var(--hairline)' };
  const motif = nationCardMotifHtml(id);
  return `<a href="/nation/${id}" class="hub-nation-card nation-card" style="--nation-border:${accent.border}">
    ${motif}
    <strong>${nation.name}</strong>
    <span class="hub-nation-meta">${meta}</span>
    <p>${excerpt}</p>
    <span class="hub-card-cta">${id === 'europe' ? 'View Europe' : 'View nation'} →</span>
  </a>`;
}

function nationCardMotifHtml(id) {
  switch (id) {
    case 'england':
      return `<div class="nation-motif nation-motif-zone nation-motif-england" aria-hidden="true"><span class="nation-motif-cross-h"></span><span class="nation-motif-cross-v"></span></div>`;
    case 'wales':
      return `<div class="nation-motif nation-motif-zone nation-motif-wales" aria-hidden="true"><span class="nation-motif-wales-triangle"></span></div>`;
    case 'scotland':
      return `<div class="nation-motif nation-motif-zone nation-motif-scotland" aria-hidden="true"><span class="nation-motif-saltire-a"></span><span class="nation-motif-saltire-b"></span></div>`;
    case 'northern-ireland':
      return `<div class="nation-motif nation-motif-zone nation-motif-ni" aria-hidden="true"><span class="nation-motif-hex nation-motif-hex-a"></span><span class="nation-motif-hex nation-motif-hex-b"></span></div>`;
    case 'europe':
      return `<div class="nation-motif nation-motif-zone nation-motif-europe" aria-hidden="true"><span class="nation-motif-ring"></span></div>`;
    default:
      return '';
  }
}

function renderNationsGrid() {
  const grid = document.getElementById('nations-grid');
  if (!grid) return;
  grid.innerHTML = Object.keys(HOME_NATION_ICONS)
    .map(id => buildNationHubCardHtml(id))
    .join('');
}

async function renderFeaturedPartiesGrid() {
  const grid = document.getElementById('featured-parties-grid');
  if (!grid) return;
  if (typeof loadPartyHoldings === 'function') await loadPartyHoldings();
  grid.innerHTML = [
    'conservative', 'labour', 'libdem',
    'snp', 'plaid', 'green', 'reform', 'dup', 'sinnfein',
  ].map(id => buildPartyBrowseCard(id)).join('');
}

// ── MANIFESTO CARD BUILDER ────────────────────────────────────
/** Scottish/Welsh editions whose seats are nested inside UK Lab/Con/LD totals. */
const TERRITORIAL_SEAT_CHILDREN = {
  labour: ['scottishlab', 'welshlab'],
  conservative: ['scottishcon', 'welshcon'],
  libdem: ['scottishlibdem', 'welshlibdem'],
};

function getElectionPartyResult(election, pid) {
  const fromResults = (election.results || []).find(r => r.party === pid);
  if (fromResults) return fromResults;
  const pr = (election.partyResults || {})[pid];
  return pr || null;
}

/** Party ids shown on this election’s manifesto grid (same set as the cards). */
function manifestoPartiesOnPage(election) {
  return [
    ...(election.results || []).filter(r => r.seats > 0).map(r => r.party),
    ...(election.extraManifestoParties || []),
  ].filter((v, i, a) => a.indexOf(v) === i && v !== 'others' && PARTIES[v] && !MANIFESTO_EXCLUDED_PARTIES.has(v));
}

function electionHasTerritorialSeatEditions(election) {
  const shown = manifestoPartiesOnPage(election);
  return Object.values(TERRITORIAL_SEAT_CHILDREN).some(children =>
    children.some(c => shown.includes(c))
  );
}

/** Seat count for a manifesto card badge; England-only for Lab/Con/LD when territorial editions are shown. */
function getManifestoCardSeatCount(election, pid) {
  const result = getElectionPartyResult(election, pid);
  const seats = result?.seats ?? 0;
  const children = TERRITORIAL_SEAT_CHILDREN[pid];
  if (!children) return seats;
  const shown = manifestoPartiesOnPage(election);
  if (!children.some(c => shown.includes(c))) return seats;
  const subtract = children.reduce(
    (n, c) => n + (getElectionPartyResult(election, c)?.seats || 0),
    0
  );
  return Math.max(0, seats - subtract);
}

function buildManifestoCard(pid, election, opts = {}) {
  const p = PARTIES[pid];
  const theme = typeof getCurrentTheme === 'function' ? getCurrentTheme() : 'dark';
  const accent = typeof partyAccentDerivedForYear === 'function'
    ? partyAccentDerivedForYear(pid, election.year, theme)
    : { surface: p.color, kicker: p.color, raw: p.color, border: p.dim };
  const partyBar = typeof barColour === 'function'
    ? barColour(getPartyColor(pid, election.year), theme)
    : p.color;
  const ghostYear = String(election.year);
  const ghostColour = typeof ghostNumeral === 'function'
    ? ghostNumeral(accent.raw, theme)
    : (typeof ghostTint === 'function' ? ghostTint(accent.raw, theme) : accent.surface);
  const dotCss = typeof dotStyle === 'function' ? dotStyle(getPartyColor(pid, election.year), theme) : `background:${p.color}`;
  const displayName  = (election.manifestoPartyLabels && election.manifestoPartyLabels[pid]) || getPartyName(pid, election.year);
  const pdfPath      = `/manifestos/${election.id}/${pid}/manifesto.pdf`;
  const textPath     = `/manifesto/${election.id}/${pid}`;
  const coverPath    = `/manifestos/${election.id}/${pid}/cover.png?v=${ASSETS_VERSION}`;
  const coverFallback= `/manifestos/${election.id}/${pid}/cover.jpg?v=${ASSETS_VERSION}`;
  const hasPdf       = hasManifestoPdf(election.id, pid);
  const hasCover     = hasManifestoCover(election.id, pid);
  const thumbHref    = hasPdf ? pdfPath : textPath;
  const thumbTarget  = hasPdf ? ' target="_blank" rel="noopener"' : '';
  const thumbLabel   = hasPdf
    ? `Open ${displayName} ${election.displayYear} manifesto PDF`
    : `Read ${displayName} ${election.displayYear} manifesto online`;

  // Party pages pass opts.result (full UK or territorial history). Election pages use the helper.
  const seats = opts.result
    ? (opts.result.seats ?? 0)
    : getManifestoCardSeatCount(election, pid);
  const headerName = opts.showYearAsTitle
    ? election.displayYear
    : partyLink(pid, displayName, election.year);
  const englandOnlySeats = !opts.result
    && Boolean(TERRITORIAL_SEAT_CHILDREN[pid])
    && electionHasTerritorialSeatEditions(election);
  const seatsTag = seats === 0
    ? '<div class="manifesto-party-tag no-seats-tag">No seats won</div>'
    : englandOnlySeats
      ? `<div class="manifesto-party-tag" title="England seats only — Scottish and Welsh seats appear on those parties’ cards">${seats} England seat${seats !== 1 ? 's' : ''}</div>`
      : `<div class="manifesto-party-tag">${seats} seat${seats !== 1 ? 's' : ''}</div>`;

  const pdfSize = hasPdf ? getPdfSize(pdfPath) : '';
  const pdfLinkFinal = hasPdf
    ? pdfCtaHtml({ href: pdfPath, size: pdfSize, scanNote: true })
    : '';

  const thumbInner = hasCover
    ? `<img src="${coverPath}" alt="${displayName} ${election.displayYear} manifesto cover"
          class="img-lazy" loading="lazy" decoding="async"
          onerror="if(this.dataset.fb){this.style.display='none';this.nextElementSibling.style.display='flex';}else{this.dataset.fb=1;this.src='${coverFallback}';}">
        <div class="manifesto-thumb-placeholder" style="display:none">
          <div class="manifesto-placeholder-topbar"></div>
          <div class="manifesto-placeholder-ghost" aria-hidden="true">${ghostYear}</div>
          <span class="manifesto-placeholder-label">Scan not yet archived</span>
        </div>`
    : `<div class="manifesto-thumb-placeholder" style="display:flex">
          <div class="manifesto-placeholder-topbar"></div>
          <div class="manifesto-placeholder-ghost" aria-hidden="true">${ghostYear}</div>
          <span class="manifesto-placeholder-label">Scan not yet archived</span>
        </div>`;

  return `<div class="manifesto-card" style="--party-color:${partyBar};--party-dim:${accent.border};--party-surface:${accent.surface};--party-ghost:${ghostColour};--party-kicker:${accent.kicker}">
      <a href="${thumbHref}" class="manifesto-thumb"${thumbTarget} aria-label="${thumbLabel}">
        ${thumbInner}
      </a>
      <div class="manifesto-card-header">
        <div class="manifesto-party-dot" style="${dotCss}"></div>
        <div class="manifesto-party-name">${headerName}</div>
        ${seatsTag}
      </div>
      <div class="manifesto-card-body">
        ${pdfLinkFinal}
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
    title: `${election.displayYear} UK General Election Results & Manifestos`,
    description: westminsterElectionDescription(election),
    path: `/election/${id}`,
  });

  const winner   = PARTIES[election.winner] || {};
  const theme = typeof getCurrentTheme === 'function' ? getCurrentTheme() : 'dark';
  const winnerAccent = typeof partyAccentDerivedForYear === 'function'
    ? partyAccentDerivedForYear(election.winner, election.year, theme)
    : { kicker: winner.color, border: winner.dim, surface: winner.color };
  const color    = winnerAccent.kicker || winner.color || 'var(--gold)';
  const dim      = winnerAccent.border || winner.dim || 'var(--gold-dim)';
  const barSurface = typeof barColour === 'function'
    ? barColour(getPartyColor(election.winner, election.year), theme)
    : winnerAccent.surface;
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
  const hasNiOnlyPlaceholder = election.results.some(
    r => (r.seats > 0 || r.votes > 0) && r.votes === 0 && PARTIES[r.party]?.nation === 'northern-ireland'
  );
  const resultRows = election.results
    .filter(r => r.seats > 0 || r.votes > 0)
    .sort((a, b) => b.seats - a.seats)
    .map(r => {
      const isWinner = r.party === election.winner;
      // NI parties with no vote total yet — mark Vote % as NI-only (not a hard-coded slug list)
      const niOnly   = r.votes === 0 && PARTIES[r.party]?.nation === 'northern-ireland';
      const votesDisplay   = r.votes   > 0 ? r.votes.toLocaleString()   : '—';
      const pctDisplay     = r.percentage > 0 ? r.percentage.toFixed(1) + '%' : (niOnly ? '<span style="font-size:0.72rem;color:var(--text-faint)">NI only</span>' : '—');
      const swatchCol = typeof barColour === 'function'
        ? barColour(getPartyColor(r.party, election.year), theme)
        : getPartyColor(r.party, election.year);
      return `<tr>
        <td><div class="result-party-name"><div class="result-party-swatch" style="background:${swatchCol}"></div>${partyLink(r.party, null, election.year)}${isWinner && hasMaj ? ' <span class="majority-badge">✦ Majority</span>' : ''}${isWinner && !hasMaj ? ' <span class="majority-badge">✦ Largest party</span>' : ''}</div></td>
        <td><div class="result-seats-bar-wrap"><div class="result-seats-bar"><div class="result-seats-fill" style="width:${(r.seats/maxSeats*100).toFixed(1)}%;background:${swatchCol}"></div></div><strong style="color:var(--cream);min-width:32px">${r.seats}</strong></div></td>
        <td style="color:var(--text-muted)">${votesDisplay}</td>
        <td style="color:var(--text-muted)">${pctDisplay}</td>
      </tr>`;
    }).join('');
  const resultsFootnote = hasNiOnlyPlaceholder
    ? `<p style="font-size:0.75rem;color:var(--text-faint);margin-top:0.75rem">† Where a UK-wide vote total is not yet recorded for a Northern Ireland party, Vote % is marked NI only.</p>`
    : (election.year >= 2010
      ? `<p style="font-size:0.75rem;color:var(--text-faint);margin-top:0.75rem">Vote totals from the House of Commons Library <a href="https://electionresults.parliament.uk/" target="_blank" rel="noopener">UK Parliament election results</a> (UK-wide shares).</p>`
      : '');


  // Manifesto section — results parties + extraManifestoParties (deduplicated)
  const manifestoPartyIds = manifestoPartiesOnPage(election);

  const NATION_ORDER  = ['england', 'scotland', 'wales', 'northern-ireland', 'others'];
  const grouped = {};
  manifestoPartyIds.forEach(pid => {
    const n = PARTIES[pid].nation || 'others';
    if (!grouped[n]) grouped[n] = [];
    grouped[n].push(pid);
  });
  // Minor / "Other Parties" cards follow A–Z by display name (nation groups keep results order)
  if (grouped.others) {
    const labelFor = (pid) =>
      (election.manifestoPartyLabels && election.manifestoPartyLabels[pid])
      || getPartyName(pid, election.year)
      || pid;
    grouped.others.sort((a, b) => labelFor(a).localeCompare(labelFor(b), 'en', { sensitivity: 'base' }));
  }
  const presentNations = NATION_ORDER.filter(n => grouped[n]?.length);
  const manifestoGridContent = presentNations.length > 1
    ? presentNations.map(n => `<div class="manifesto-nation-group">
        <h3 class="manifesto-nation-heading">${n === 'others' ? nationHeadingLabelHtml(n) : nationLink(n, nationHeadingLabelHtml(n))}</h3>
        <div class="manifesto-grid">${grouped[n].map(pid => buildManifestoCard(pid, election)).join('')}</div>
      </div>`).join('')
    : `<div class="manifesto-grid">${manifestoPartyIds.map(pid => buildManifestoCard(pid, election)).join('')}</div>`;
  const territorialSeatsNote = electionHasTerritorialSeatEditions(election)
    ? `<p class="manifestos-intro manifestos-seat-note" style="margin-top:0.5rem"><strong>Seat badges:</strong> Labour, Conservative and Liberal Democrat cards show <em>England seats</em> only so totals are not double-counted. Scottish and Welsh party cards show that nation’s seats. The results table above is UK-wide.</p>`
    : '';
  const videoIds = Array.isArray(election.youtubeId)
    ? election.youtubeId.filter(Boolean)
    : (election.youtubeId ? [election.youtubeId] : []);
  const videoSection = videoIds.length
    ? `<div class="video-section"><span class="section-label">Election Night</span><h2>Broadcast Recording</h2>${videoIds.map((id, i) => {
        const start = i === 0 && election.youtubeStart ? `?start=${election.youtubeStart}` : '';
        return `<div class="video-wrap"><iframe src="https://www.youtube.com/embed/${id}${start}" title="Election night broadcast recording" allow="accelerometer;autoplay;clipboard-write;encrypted-media;gyroscope;picture-in-picture" allowfullscreen loading="lazy"></iframe></div>`;
      }).join('')}</div>`
    : '';

  app.innerHTML = `
    ${renderBreadcrumb([
      { label: 'Home', href: '/' },
      { label: 'General Elections', href: '/elections' },
      { label: election.displayYear },
    ])}
    <section class="election-hero">
      <div class="election-hero-bg"></div>
      <div class="election-hero-inner">
        <div>
          <div class="election-eyebrow">United Kingdom General Election</div>
          <h1 class="election-title">${election.displayYear}</h1>
          <div class="election-date">${election.date}</div>
          <div class="election-winner-badge" style="--party-color:${color};--party-dim:${dim};--party-surface:${barSurface}">
            <div class="winner-dot" style="background:${barSurface}"></div>${winner.shortName} victory — ${election.pm} (PM)
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
          ${highlightItems ? `<div class="highlights-list"><h2>Key Moments</h2>${highlightItems}</div>` : ''}

          <div class="results-section">
            <span class="section-label">Seat Distribution</span>
            <h2>Results</h2>
            <table class="results-table">
              <caption class="sr-only">${election.displayYear} UK general election results by party</caption>
              <thead><tr><th scope="col">Party</th><th scope="col">Seats (of ${election.totalSeats})</th><th scope="col">Votes</th><th scope="col">Vote %</th></tr></thead>
              <tbody>${resultRows}</tbody>
            </table>
            ${resultsFootnote}
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
        ${territorialSeatsNote}
        ${manifestoGridContent}
      </div>

      ${videoSection}
    </div>
  `;

  requestAnimationFrame(() => {
    const c = document.getElementById('parliament-svg-container');
    const l = document.getElementById('parliament-legend');
    if (c) { drawParliamentChart(c, election.results, election.totalSeats, election.year); buildParliamentLegend(l, election.results, election.year); }
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

/**
 * Party-hero wins aside.
 * - Westminster majors with extra chambers: big Westminster count + chamber count chips (no year pills).
 * - Single non-Westminster chamber with ≤5 wins: big count + chamber + year chips.
 * Numeral colour from CSS (--party-color / --party-kicker), matching Founded.
 * @param {{
 *   westYears: string[],
 *   chambers: { id: string, label: string, href: string, years: string[], kind: 'won'|'largest'|'mayor' }[],
 * }} opts
 */
function partyWinsAsideHtml({ westYears = [], chambers = [] }) {
  const westCount = westYears.length;
  const nonWest = chambers.filter(c => c.years.length);
  if (!westCount && !nonWest.length) return '';

  const yearChips = (chamber) => {
    const years = chamber.years || [];
    if (!years.length || years.length > 5) return '';
    return `<ul class="wins-years">${years.map(y => {
      const href = typeof chamber.yearHref === 'function'
        ? chamber.yearHref(y)
        : (chamber.href || '#');
      return `<li><a class="wins-year" href="${href}">${y}</a></li>`;
    }).join('')}</ul>`;
  };

  const kindLabel = (kind, n) => {
    if (kind === 'mayor') return n === 1 ? 'Mayoral win' : 'Mayoral wins';
    if (kind === 'won') return n === 1 ? 'Election won' : 'Elections won';
    return 'Largest party';
  };

  // Westminster hero figure (+ optional extra-chamber count chips, no year row).
  if (westCount > 0) {
    const extra = nonWest.map(c =>
      `<a class="wins-chamber-chip" href="${c.href}"><span class="wins-chamber-chip-label">${c.label}</span><span class="wins-chamber-chip-count">${c.years.length}</span></a>`
    ).join('');
    return `<aside class="party-elections-won-badge" aria-label="Elections won">
      <div class="elections-won-label">Election${westCount === 1 ? '' : 's'} won</div>
      <div class="elections-won-num">${westCount}</div>
      <div class="wins-chamber">Westminster</div>
      ${extra ? `<div class="wins-chamber-chips">${extra}</div>` : ''}
    </aside>`;
  }

  // Non-Westminster only — one chamber: count + years when small.
  if (nonWest.length === 1) {
    const c = nonWest[0];
    const n = c.years.length;
    return `<aside class="party-elections-won-badge" aria-label="${kindLabel(c.kind, n)}">
      <div class="elections-won-label">${kindLabel(c.kind, n)}</div>
      <div class="elections-won-num">${n}</div>
      <div class="wins-chamber">${c.label}</div>
      ${yearChips(c)}
    </aside>`;
  }

  // Multiple non-Westminster chambers, no Westminster — chamber count chips.
  const total = nonWest.reduce((s, c) => s + c.years.length, 0);
  const chips = nonWest.map(c =>
    `<a class="wins-chamber-chip" href="${c.href}"><span class="wins-chamber-chip-label">${c.label}</span><span class="wins-chamber-chip-count">${c.years.length}</span></a>`
  ).join('');
  return `<aside class="party-elections-won-badge" aria-label="Contests led">
    <div class="elections-won-label">Contests led</div>
    <div class="elections-won-num">${total}</div>
    <div class="wins-chamber-chips">${chips}</div>
  </aside>`;
}

/**
 * Party-hero “Elections contested” meta.
 * @param {{ count: number, label: string, href?: string }[]} chambers
 * 1 chamber → scalar dd; 2+ → wrap chips (optionally linking to on-page sections).
 */
function partyContestedMetaHtml(chambers) {
  if (!chambers || !chambers.length) {
    return `<div class="party-meta-item"><dt>Elections contested</dt><dd>0</dd></div>`;
  }
  if (chambers.length === 1) {
    const c = chambers[0];
    return `<div class="party-meta-item"><dt>Elections contested</dt><dd>${c.count} ${c.label}</dd></div>`;
  }
  const chips = chambers.map(c => {
    const inner = `<span class="election-chip-count">${c.count}</span><span class="election-chip-label">${c.label}</span>`;
    return c.href
      ? `<li><a class="election-chip" href="${c.href}">${inner}</a></li>`
      : `<li><span class="election-chip">${inner}</span></li>`;
  }).join('');
  return `<div class="party-meta-item party-meta-item--elections">
    <dt>Elections contested</dt>
    <dd><ul class="election-chips">${chips}</ul></dd>
  </div>`;
}

/** Wrap a results list in a <details> fold (closed on mobile, open on desktop). */
function partyResultsFoldHtml(rowsHtml, count) {
  if (!rowsHtml) return '';
  const n = Number(count) || 0;
  const label = n === 1 ? 'Show 1 contest' : `Show ${n} contests`;
  return `<details class="party-results-fold">
    <summary class="party-results-fold-summary"><span>${label}</span></summary>
    <div class="party-results-list">${rowsHtml}</div>
  </details>`;
}

/** Scroll to #party-* after SPA render. Do not open mobile folds — chips jump to the
 *  section heading; the user expands “Show N contests” if they want the list. */
function scrollToPartyHash() {
  const id = decodeURIComponent((window.location.hash || '').replace(/^#/, ''));
  if (!id) return;
  const section = document.getElementById(id);
  if (!section || !section.classList.contains('party-elections-section')) return;
  section.scrollIntoView({ block: 'start' });
}

/** Desktop: force results folds open; mobile: closed by default. */
function initPartyResultsFolds() {
  const folds = document.querySelectorAll('.party-results-fold');
  if (!folds.length) return;
  const mq = window.matchMedia('(min-width: 901px)');
  const sync = () => {
    folds.forEach(d => { d.open = mq.matches; });
  };
  if (!window.__partyResultsFoldsBound) {
    window.__partyResultsFoldsBound = true;
    mq.addEventListener('change', () => {
      document.querySelectorAll('.party-results-fold').forEach(d => {
        d.open = mq.matches;
      });
    });
  }
  sync();
  // After fold state is set, scroll to hash target (element may not have existed at nav time).
  requestAnimationFrame(() => scrollToPartyHash());
}

// ── CO-OPERATIVE PARTY CUSTOM PAGE ───────────────────────────
async function renderCooperativePartyPage(app, party) {
  const color = party.color;
  const theme = typeof getCurrentTheme === 'function' ? getCurrentTheme() : 'dark';
  const kickerCol = typeof partyTextColour === 'function' ? partyTextColour('cooperative', null, theme) : color;
  const barCol = typeof barColour === 'function' ? barColour(color, theme) : color;
  const coopChambers = [
    { count: 22, label: 'Westminster', href: '#party-westminster' },
    { count: 7, label: 'Holyrood', href: '#party-holyrood' },
    { count: 7, label: 'Senedd', href: '#party-senedd' },
  ];
  setPageMeta({
    title: party.shortName,
    description: buildPartyMetaDescription(party, coopChambers.map(c => `${c.count} ${c.label}`)),
    path: '/party/cooperative',
  });
  const partyLede = partyLedeText(party.description);
  const contestedMetaHtml = partyContestedMetaHtml(coopChambers);

  // Load devolved history to get the manifestos
  const holyroodHistory = (typeof getHolyroodPartyHistory === 'function')
    ? await getHolyroodPartyHistory('cooperative')
    : { elections: [], manifestos: [] };
  const holyroodManifestos = holyroodHistory.manifestos;
  const holyroodItems = holyroodManifestos.map(({ election, manifesto }) =>
    holyroodManifestoCard(manifesto, election)
  ).join('');

  const seneddHistory = (typeof getSeneddPartyHistory === 'function')
    ? await getSeneddPartyHistory('cooperative')
    : { elections: [], manifestos: [] };
  const seneddManifestos = seneddHistory.manifestos;
  const seneddItems = seneddManifestos.map(({ election, manifesto }) =>
    seneddManifestoCard(manifesto, election)
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
      <div class="per-bar-wrap"><div class="per-bar"><div class="per-bar-fill" style="width:${barW}%;background:${typeof barColour === 'function' ? barColour(color) : color}"></div></div></div>
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
      <div class="per-bar-wrap"><div class="per-bar"><div class="per-bar-fill" style="width:${barW}%;background:${typeof barColour === 'function' ? barColour(color) : color}"></div></div></div>
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
      <div class="per-bar-wrap"><div class="per-bar"><div class="per-bar-fill" style="width:${barW}%;background:${typeof barColour === 'function' ? barColour(color) : color}"></div></div></div>
    </a>`;
  }).join('');

  app.innerHTML = `
    ${renderBreadcrumb(partyBreadcrumbItems(party))}
    <section class="party-hero" style="--party-color:${color};--party-kicker:${kickerCol}">
      <div class="party-hero-bg"></div>
      <div class="party-hero-inner">
        <div class="party-hero-main">
          <div class="party-color-bar" style="background:${barCol}"></div>
          <h1 class="party-hero-title">${party.name}</h1>
          ${partyLede ? `<p class="party-lede">${partyLede}</p>` : ''}
          <div class="party-hero-stats">
            <dl class="party-hero-meta">
              <div class="party-meta-item"><dt>Founded</dt><dd>${party.founded || '—'}</dd></div>
              <div class="party-meta-item"><dt>Spectrum</dt><dd>${party.spectrum}</dd></div>
              ${contestedMetaHtml}
            </dl>
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
        <div class="gold-rule" style="background:${barCol}"></div>
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

      <div class="party-elections-section" id="party-westminster">
        <span class="section-label">Electoral Record</span>
        <h2>Westminster Joint Representatives</h2>
        <div class="gold-rule" style="background:${barCol}"></div>
        ${partyResultsFoldHtml(westminsterRows, coopWestminsterData.length)}
      </div>

      <div class="party-manifestos-section">
        <span class="section-label">Documents</span>
        <h2>Westminster Manifestos</h2>
        <div class="gold-rule" style="background:${barCol}"></div>
        ${manifestoItems ? `<div class="manifesto-grid">${manifestoItems}</div>` : '<p style="color:var(--text-muted)">No Westminster manifestos on record.</p>'}
      </div>

      <div class="party-elections-section" id="party-holyrood">
        <span class="section-label">Holyrood</span>
        <h2>Scottish Parliament Joint Representatives</h2>
        <div class="gold-rule" style="background:${barCol}"></div>
        ${partyResultsFoldHtml(holyroodRows, coopHolyroodData.length)}
      </div>

      <div class="party-manifestos-section">
        <span class="section-label">Holyrood</span>
        <h2>Scottish Parliament Manifestos</h2>
        <div class="gold-rule" style="background:${barCol}"></div>
        ${holyroodItems ? `<div class="manifesto-grid">${holyroodItems}</div>` : '<p style="color:var(--text-muted)">No Scottish Parliament manifestos on record.</p>'}
      </div>

      <div class="party-elections-section" id="party-senedd">
        <span class="section-label">Senedd Cymru</span>
        <h2>Welsh Parliament Joint Representatives</h2>
        <div class="gold-rule" style="background:${barCol}"></div>
        ${partyResultsFoldHtml(seneddRows, coopSeneddData.length)}
      </div>

      <div class="party-manifestos-section">
        <span class="section-label">Senedd Cymru</span>
        <h2>Welsh Parliament Manifestos</h2>
        <div class="gold-rule" style="background:${barCol}"></div>
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
  initPartyResultsFolds();
}

// ── PARTY PAGE ────────────────────────────────────────────────
async function renderParty(app, id) {
  const partyId = resolvePartyId(id);
  const party = PARTIES[partyId];
  if (!party) { renderNotFound(app); return; }
  // Canonicalise aliased slugs in the URL bar (e.g. /party/brexit → /party/reform).
  if (id && partyId && id !== partyId && getPath() === `/party/${id}`) {
    history.replaceState(null, '', `/party/${partyId}`);
  }
  if (partyId === 'cooperative') {
    await renderCooperativePartyPage(app, party);
    return;
  }

  const color = party.color;
  const theme = typeof getCurrentTheme === 'function' ? getCurrentTheme() : 'dark';
  const kickerCol = typeof partyTextColour === 'function' ? partyTextColour(partyId, null, theme) : color;
  const barCol = typeof barColour === 'function' ? barColour(color, theme) : color;
  const isAllianceParty = typeof isEuroAllianceParty === 'function' && isEuroAllianceParty(partyId);

  const partyElections = isAllianceParty ? [] : ELECTIONS.map(e => {
    const r = e.results.find(res => res.party === partyId || res.party === id);
    if (r) return { election: e, result: r };
    const pr = (e.partyResults || {})[partyId] || (e.partyResults || {})[id];
    if (pr) return { election: e, result: pr };
    if ((e.extraManifestoParties || []).includes(partyId) || (e.extraManifestoParties || []).includes(id)) {
      return { election: e, result: { party: partyId, seats: 0, votes: 0, percentage: 0 } };
    }
    return null;
  }).filter(Boolean);

  // Catch manifesto-only elections missing from results / extraManifestoParties
  // (e.g. text editions for parties that won no seats and weren't listed yet).
  if (!isAllianceParty && MANIFESTO_ARCHIVE) {
    const seen = new Set(partyElections.map(pe => pe.election.id));
    ELECTIONS.forEach(e => {
      if (seen.has(e.id)) return;
      if (hasManifestoContent(e.id, partyId)) {
        partyElections.push({
          election: e,
          result: { party: partyId, seats: 0, votes: 0, percentage: 0 },
        });
      }
    });
    partyElections.sort((a, b) => a.election.year - b.election.year);
  }

  const westWinYears = partyElections
    .filter(pe => pe.election.winner === partyId)
    .map(pe => pe.election.displayYear || String(pe.election.year));
  const maxSeats = Math.max(1, ...partyElections.map(pe => pe.result.seats));

  const electionRows = partyElections.slice().reverse().map(({ election: e, result: r }) => {
    const isWon   = e.winner === partyId;
    const isCoal  = partyId === 'libdem' && e.id === '2010';
    const cls     = isWon ? 'won' : isCoal ? 'coalition' : 'lost';
    const label   = isWon ? '✦ Won' : isCoal ? '⊕ Coalition' : 'Opposition';
    const barW    = ((r.seats / maxSeats) * 100).toFixed(1);
    return `<a class="party-election-row" href="/election/${e.id}">
      <div class="per-year">${e.displayYear}</div>
      <div><div class="per-outcome ${cls}">${label}</div><div style="font-size:0.78rem;color:var(--text-faint);margin-top:0.3rem">${e.pm}</div></div>
      <div class="per-seats-wrap"><div class="per-seats-num">${r.seats}</div><div class="per-seats-label">seats</div></div>
      <div class="per-bar-wrap"><div class="per-bar"><div class="per-bar-fill" style="width:${barW}%;background:${typeof barColour === 'function' ? barColour(color) : color}"></div></div><div class="per-pct">${r.percentage > 0 ? r.percentage.toFixed(1) + '% vote' : '—'}</div></div>
    </a>`;
  }).join('');

  const manifestoElections = partyElections.filter(({ election: e }) =>
    hasManifestoContent(e.id, partyId)
  );
  const manifestoItems = manifestoElections.slice().reverse().map(({ election: e, result: r }) =>
    buildManifestoCard(partyId, e, { result: r, showYearAsTitle: true })
  ).join('');

  const holyroodHistory = (typeof getHolyroodPartyHistory === 'function')
    ? await getHolyroodPartyHistory(partyId)
    : { elections: [], manifestos: [] };
  const holyroodElections = holyroodHistory.elections;
  const holyroodManifestos = holyroodHistory.manifestos;

  const seneddHistory = (typeof getSeneddPartyHistory === 'function')
    ? await getSeneddPartyHistory(partyId)
    : { elections: [], manifestos: [] };
  const seneddElections = seneddHistory.elections;
  const seneddManifestos = seneddHistory.manifestos;

  const niHistory = (typeof getNIPartyHistory === 'function')
    ? await getNIPartyHistory(partyId)
    : { elections: [], manifestos: [] };
  const niElections = niHistory.elections;
  const niManifestos = niHistory.manifestos;

  const euroHistory = (typeof getEuroPartyHistory === 'function')
    ? await getEuroPartyHistory(partyId)
    : { elections: [], manifestos: [] };
  const euroElections = euroHistory.elections;
  const euroManifestos = euroHistory.manifestos;

  const londonHistory = (!isAllianceParty && typeof getLondonPartyHistory === 'function')
    ? await getLondonPartyHistory(partyId)
    : { elections: [], manifestos: [] };
  const londonElections = londonHistory.elections;
  const londonManifestos = londonHistory.manifestos;

  const maxHolyroodSeats = Math.max(1, ...holyroodElections.map(pe => pe.result.seats));
  const holyroodElectionRows = holyroodElections.map(pe =>
    holyroodPartyElectionRow(partyId, pe, maxHolyroodSeats, color)
  ).join('');

  const holyroodItems = holyroodManifestos.map(({ election, manifesto }) =>
    holyroodManifestoCard(manifesto, election)
  ).join('');

  const maxSeneddSeats = Math.max(1, ...seneddElections.map(pe => pe.result.seats));
  const seneddElectionRows = seneddElections.map(pe =>
    seneddPartyElectionRow(partyId, pe, maxSeneddSeats, color)
  ).join('');

  const seneddItems = seneddManifestos.map(({ election, manifesto }) =>
    seneddManifestoCard(manifesto, election)
  ).join('');

  const maxNISeats = Math.max(1, ...niElections.map(pe => pe.result.seats));
  const niElectionRows = niElections.map(pe =>
    niPartyElectionRow(partyId, pe, maxNISeats, color)
  ).join('');

  const niItems = niManifestos.map(({ election, manifesto }) =>
    niManifestoCard(manifesto, election)
  ).join('');

  const maxEuroSeats = Math.max(1, ...euroElections.map(pe => pe.result.seats));
  const euroElectionRows = euroElections.map(pe =>
    euroPartyElectionRow(partyId, pe, maxEuroSeats, color)
  ).join('');

  const euroItems = euroManifestos.map(({ election, manifesto }) =>
    euroManifestoCard(manifesto, election)
  ).join('');

  const maxLondonSeats = Math.max(1, ...londonElections.map(pe => pe.result.seats));
  const londonElectionRows = londonElections.map(pe =>
    londonPartyElectionRow(partyId, pe, maxLondonSeats, color)
  ).join('');

  const londonItems = londonManifestos.map(({ election, manifesto }) =>
    londonManifestoCard(manifesto, election)
  ).join('');

  const contestedChambers = [];
  if (!isAllianceParty && partyElections.length) {
    contestedChambers.push({ count: partyElections.length, label: 'Westminster', href: '#party-westminster' });
  }
  if (!isAllianceParty && holyroodElections.length) {
    contestedChambers.push({ count: holyroodElections.length, label: 'Holyrood', href: '#party-holyrood' });
  }
  if (!isAllianceParty && seneddElections.length) {
    contestedChambers.push({ count: seneddElections.length, label: 'Senedd', href: '#party-senedd' });
  }
  if (!isAllianceParty && niElections.length) {
    contestedChambers.push({ count: niElections.length, label: 'Stormont', href: '#party-stormont' });
  }
  if (euroElections.length) {
    contestedChambers.push({ count: euroElections.length, label: 'Europe', href: '#party-europe' });
  }
  if (!isAllianceParty && londonElections.length) {
    contestedChambers.push({ count: londonElections.length, label: 'London', href: '#party-london' });
  }
  // Meta description keeps the fuller European Parliament wording.
  const contestedParts = contestedChambers.map(c => (
    c.label === 'Europe' ? `${c.count} European Parliament` : `${c.count} ${c.label}`
  ));
  const contestedMetaHtml = partyContestedMetaHtml(contestedChambers);
  const partyLede = partyLedeText(party.description);

  const winYear = pe => pe.election.displayYear || String(pe.election.year);
  const winId = pe => pe.election.id || winYear(pe);
  const ledByControl = (list) => list.filter(pe =>
    pe.election.control === partyId
    || (typeof resolvePartyId === 'function' && pe.election.control === resolvePartyId(partyId))
  );
  const winChambers = [];
  const holyroodLed = ledByControl(holyroodElections);
  if (holyroodLed.length) {
    winChambers.push({
      id: 'holyrood', label: 'Holyrood', href: '#party-holyrood', kind: 'largest',
      years: holyroodLed.map(winYear),
      yearHref: (y) => {
        const pe = holyroodLed.find(p => winYear(p) === y);
        return `/devolved/holyrood/${winId(pe)}`;
      },
    });
  }
  const seneddLed = ledByControl(seneddElections);
  if (seneddLed.length) {
    winChambers.push({
      id: 'senedd', label: 'Senedd', href: '#party-senedd', kind: 'largest',
      years: seneddLed.map(winYear),
      yearHref: (y) => {
        const pe = seneddLed.find(p => winYear(p) === y);
        return `/devolved/senedd/${winId(pe)}`;
      },
    });
  }
  const stormontLed = ledByControl(niElections);
  if (stormontLed.length) {
    winChambers.push({
      id: 'stormont', label: 'Stormont', href: '#party-stormont', kind: 'largest',
      years: stormontLed.map(winYear),
      yearHref: (y) => {
        const pe = stormontLed.find(p => winYear(p) === y);
        return `/devolved/stormont/${winId(pe)}`;
      },
    });
  }
  const euroLed = ledByControl(euroElections);
  if (euroLed.length) {
    winChambers.push({
      id: 'europe', label: 'Europe', href: '#party-europe', kind: 'won',
      years: euroLed.map(winYear),
      yearHref: (y) => {
        const pe = euroLed.find(p => winYear(p) === y);
        return `/devolved/euro/${winId(pe)}`;
      },
    });
  }
  const londonLed = londonElections.filter(pe =>
    typeof londonPartyLedElection === 'function'
      ? londonPartyLedElection(partyId, pe.election)
      : pe.election.mayorWinner === partyId || pe.election.control === partyId
  );
  if (londonLed.length) {
    const hasMayorWin = londonLed.some(pe => pe.election.mayor || pe.election.mayorWinner);
    winChambers.push({
      id: 'london', label: 'London', href: '#party-london',
      kind: hasMayorWin ? 'mayor' : 'largest',
      years: londonLed.map(winYear),
      yearHref: (y) => {
        const pe = londonLed.find(p => winYear(p) === y);
        return `/devolved/london/${winId(pe)}`;
      },
    });
  }

  const ukMembers = isAllianceParty && typeof getEuroAllianceUkMembers === 'function'
    ? getEuroAllianceUkMembers(partyId)
    : [];
  const membersCard = ukMembers.length
    ? `<div class="nation-parties-card party-hero-members">
        <div class="section-label" style="margin-bottom:1rem">British member parties</div>
        ${ukMembers.map(pid => nationPartyLinkHtml(pid)).join('')}
        <a href="/devolved/euro" class="holyrood-other-link">European Parliament archive →</a>
      </div>`
    : '';
  const winsAside = membersCard
    ? ''
    : partyWinsAsideHtml({ westYears: westWinYears, chambers: winChambers });
  const heroInnerClass = membersCard ? ' party-hero-inner--with-aside' : '';
  const statsClass = winsAside ? ' party-hero-stats--with-wins' : '';

  setPageMeta({
    title: party.shortName,
    description: buildPartyMetaDescription(party, contestedParts),
    path: `/party/${partyId}`,
  });

  app.innerHTML = `
    ${renderBreadcrumb(partyBreadcrumbItems(party))}
    <section class="party-hero" style="--party-color:${color};--party-kicker:${kickerCol}">
      <div class="party-hero-bg"></div>
      <div class="party-hero-inner${heroInnerClass}">
        <div class="party-hero-main">
          <div class="party-color-bar" style="background:${barCol}"></div>
          <h1 class="party-hero-title">${party.name}</h1>
          ${partyLede ? `<p class="party-lede">${partyLede}</p>` : ''}
          <div class="party-hero-stats${statsClass}">
            <dl class="party-hero-meta">
              <div class="party-meta-item"><dt>Founded</dt><dd>${party.founded || '—'}</dd></div>
              <div class="party-meta-item"><dt>Spectrum</dt><dd>${party.spectrum}</dd></div>
              ${contestedMetaHtml}
            </dl>
            ${winsAside}
          </div>
        </div>
        ${membersCard}
      </div>
    </section>

    <div class="party-body">
      <div class="party-description">${party.description}</div>
      ${!isAllianceParty ? `<div class="party-elections-section" id="party-westminster">
        <span class="section-label">Electoral Record</span>
        <h2>Westminster Results</h2>
        <div class="gold-rule" style="background:${barCol}"></div>
        ${electionRows ? partyResultsFoldHtml(electionRows, partyElections.length) : '<p style="color:var(--text-muted)">No Westminster election data available.</p>'}
      </div>
      <div class="party-manifestos-section">
        <span class="section-label">Documents</span>
        <h2>Westminster Manifestos</h2>
        <div class="gold-rule" style="background:${barCol}"></div>
        ${manifestoItems ? `<div class="manifesto-grid">${manifestoItems}</div>` : '<p style="color:var(--text-muted)">No Westminster manifestos on record.</p>'}
      </div>` : ''}
      ${!isAllianceParty && holyroodElectionRows ? `<div class="party-elections-section" id="party-holyrood">
        <span class="section-label">Holyrood</span>
        <h2>Scottish Parliament Results</h2>
        <div class="gold-rule" style="background:${barCol}"></div>
        ${partyResultsFoldHtml(holyroodElectionRows, holyroodElections.length)}
      </div>` : ''}
      ${!isAllianceParty && holyroodItems ? `<div class="party-manifestos-section">
        <span class="section-label">Holyrood</span>
        <h2>Scottish Parliament Manifestos</h2>
        <div class="gold-rule" style="background:${barCol}"></div>
        <div class="manifesto-grid">${holyroodItems}</div>
      </div>` : ''}
      ${!isAllianceParty && seneddElectionRows ? `<div class="party-elections-section" id="party-senedd">
        <span class="section-label">Senedd Cymru</span>
        <h2>Welsh Parliament Results</h2>
        <div class="gold-rule" style="background:${barCol}"></div>
        ${partyResultsFoldHtml(seneddElectionRows, seneddElections.length)}
      </div>` : ''}
      ${!isAllianceParty && seneddItems ? `<div class="party-manifestos-section">
        <span class="section-label">Senedd Cymru</span>
        <h2>Welsh Parliament Manifestos</h2>
        <div class="gold-rule" style="background:${barCol}"></div>
        <div class="manifesto-grid">${seneddItems}</div>
      </div>` : ''}
      ${!isAllianceParty && niElectionRows ? `<div class="party-elections-section" id="party-stormont">
        <span class="section-label">Stormont</span>
        <h2>Northern Ireland Assembly Results</h2>
        <div class="gold-rule" style="background:${barCol}"></div>
        ${partyResultsFoldHtml(niElectionRows, niElections.length)}
      </div>` : ''}
      ${!isAllianceParty && niItems ? `<div class="party-manifestos-section">
        <span class="section-label">Stormont</span>
        <h2>Northern Ireland Assembly Manifestos</h2>
        <div class="gold-rule" style="background:${barCol}"></div>
        <div class="manifesto-grid">${niItems}</div>
      </div>` : ''}
      ${euroElectionRows ? `<div class="party-elections-section" id="party-europe">
        <span class="section-label">European Parliament</span>
        <h2>European Parliament Results</h2>
        <div class="gold-rule" style="background:${barCol}"></div>
        ${isAllianceParty ? '<p style="color:var(--text-muted);font-size:0.85rem;margin-bottom:1rem">Seats held by UK parties in this EP political group at the constitutive session after each election.</p>' : ''}
        ${partyResultsFoldHtml(euroElectionRows, euroElections.length)}
      </div>` : ''}
      ${euroItems ? `<div class="party-manifestos-section">
        <span class="section-label">European Parliament</span>
        <h2>European Parliament Manifestos</h2>
        <div class="gold-rule" style="background:${barCol}"></div>
        <div class="manifesto-grid">${euroItems}</div>
      </div>` : ''}
      ${londonElectionRows ? `<div class="party-elections-section" id="party-london">
        <span class="section-label">London · LCC / GLC / GLA</span>
        <h2>London Results</h2>
        <div class="gold-rule" style="background:${barCol}"></div>
        ${partyResultsFoldHtml(londonElectionRows, londonElections.length)}
      </div>` : ''}
      ${londonItems ? `<div class="party-manifestos-section">
        <span class="section-label">London</span>
        <h2>London Manifestos</h2>
        <div class="gold-rule" style="background:${barCol}"></div>
        <div class="manifesto-grid">${londonItems}</div>
      </div>` : ''}
    </div>
  `;
  initPartyResultsFolds();
}

// ── NATION PAGE ───────────────────────────────────────────────
function westminsterYearCell(yearLabel) {
  const election = ELECTIONS.find(e => e.displayYear === yearLabel);
  if (!election || election.year < 1945) {
    return `<td style="font-family:var(--font-display);color:var(--cream)">${yearLabel}</td>`;
  }
  return `<td style="font-family:var(--font-display);color:var(--cream)"><a href="/election/${election.id}" class="results-table-link">${yearLabel}</a></td>`;
}

/** Theme-safe party text colour for nation-page tables (SNP yellow etc.). */
function nationPartyTextColor(partyId, fallbackHex) {
  if (partyId && typeof partyTextColour === 'function' && PARTIES?.[partyId]) {
    return partyTextColour(partyId);
  }
  return fallbackHex || '#6b7280';
}

function nationTablePartyHeading(partyId, label, color) {
  const resolved = partyId ? nationPartyTextColor(partyId, color) : color;
  const style = resolved ? ` style="color:${resolved}"` : '';
  if (!partyId || !PARTIES?.[partyId]) {
    return `<th scope="col"${style}>${label}</th>`;
  }
  return `<th scope="col"${style}><a href="/party/${partyId}" class="results-table-link">${label}</a></th>`;
}

function nationArchiveLink(id) {
  const links = {
    scotland: { href: '/devolved/holyrood', label: 'Scottish Parliament results →' },
    wales: { href: '/devolved/senedd', label: 'Senedd results →' },
    'northern-ireland': { href: '/devolved/stormont', label: 'Northern Ireland Assembly results →' },
    europe: { href: '/devolved/euro', label: 'European Parliament results →' },
  };
  const link = links[id];
  if (!link) return '';
  return `<a href="${link.href}" class="cross-archive-link">${link.label}</a>`;
}

function renderNation(app, id) {
  const nation = NATIONS[id];
  if (!nation) { renderNotFound(app); return; }
  setPageMeta({
    title: nation.name,
    description: nation.description
      ? truncateMetaDescription(nation.description, 155)
      : (id === 'europe'
        ? 'Pan-European political families that contested European Parliament elections in the United Kingdom from 1979 to 2019.'
        : `UK general election results, seat history, and manifestos for ${nation.name}.`),
    path: `/nation/${id}`,
  });

  const navConfig = NAV_PARTIES[id];
  const partyLinks = navConfig ? navConfig.parties.map(pid => nationPartyLinkHtml(pid)).join('') : '';

  const keyFacts = (nation.keyFacts || []).map(f => `<div class="highlight-item"><div class="highlight-marker"></div><span>${f}</span></div>`).join('');

  let euroSection = '';
  if (id === 'europe' && typeof EURO_ALLIANCE_UK_SEATS !== 'undefined') {
    const families = [
      { id: 'sand', label: 'S&D', color: '#E4003B' },
      { id: 'epp', label: 'EPP', color: '#003399' },
      { id: 'renew', label: 'Renew', color: '#FFD700' },
      { id: 'greensefa', label: 'G/EFA', color: '#009639' },
      { id: 'guengl', label: 'GUE/NGL', color: '#E30613' },
      { id: 'ecr', label: 'ECR', color: '#1B3A6B' },
      { id: 'inddem', label: 'Eurosceptic', color: '#70147A' },
      { id: '_other', label: 'Other', color: 'var(--text-muted)', keys: ['identity', 'uen', 'other'] },
    ];
    const seatCount = (seats, family) => {
      if (family.keys) return family.keys.reduce((sum, key) => sum + (seats[key] || 0), 0);
      return seats[family.id] || 0;
    };
    const years = Object.keys(EURO_ALLIANCE_UK_SEATS).map(Number).sort((a, b) => a - b);
    const rows = years.map((year) => {
      const seats = EURO_ALLIANCE_UK_SEATS[year];
      const total = Object.values(seats).reduce((sum, n) => sum + n, 0);
      const cells = families.map(f => {
        const n = seatCount(seats, f);
        return `<td style="color:${f.color};font-weight:600">${n > 0 ? n : '—'}</td>`;
      }).join('');
      return `<tr>
        <td style="font-family:var(--font-display);color:var(--cream)"><a href="/devolved/euro/${year}" style="color:inherit;text-decoration:none">${year}</a></td>
        ${cells}
        <td style="color:var(--cream-dark);font-size:0.8rem">${total}</td>
      </tr>`;
    }).join('');
    const header = families.map(f => {
      if (f.id === '_other') return `<th scope="col" style="color:${f.color}">${f.label}</th>`;
      return nationTablePartyHeading(f.id, f.label, f.color);
    }).join('');
    euroSection = `<div class="devolved-section" style="margin-bottom:2.5rem">
      <span class="section-label">European Parliament Elections</span>
      <h2>UK MEPs by Political Family, 1979–2019</h2>
      <div class="gold-rule"></div>
      <p style="color:var(--text-muted);font-size:0.85rem;margin-bottom:1.5rem">Seats held by UK parties in each EP political group at the constitutive session after each election. Includes non-attached MEPs mapped to the closest family line (e.g. Brexit Party 2019, BNP 2009). UK Conservatives sat in the European Democrats and EPP-ED groups before forming ECR in 2009. <a href="/devolved/euro">View full European Parliament archive →</a></p>
      <div style="overflow-x:auto"><table class="results-table">
        <thead><tr><th scope="col">Year</th>${header}<th scope="col">Total</th></tr></thead>
        <tbody>${rows}</tbody>
      </table></div>
    </div>`;
  }

  // Westminster GE results table
  let westminsterSection = '';
  if (id === 'england' && nation.westminsterResults) {
    const rows = nation.westminsterResults.map(r => `<tr>
      ${westminsterYearCell(r.year)}
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
        <thead><tr><th scope="col">Year</th>${nationTablePartyHeading('conservative', 'Con', '#0087DC')}${nationTablePartyHeading('labour', 'Lab', '#E4003B')}${nationTablePartyHeading('libdem', 'LD', '#FAA61A')}<th scope="col">Other</th><th scope="col">Total</th></tr></thead>
        <tbody>${rows}</tbody>
      </table></div>
    </div>`;
  } else if (id === 'wales' && nation.westminsterResults) {
    const rows = nation.westminsterResults.map(r => `<tr>
      ${westminsterYearCell(r.year)}
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
        <thead><tr><th scope="col">Year</th>${nationTablePartyHeading('welshcon', 'Con', '#0087DC')}${nationTablePartyHeading('welshlab', 'Lab', '#E4003B')}${nationTablePartyHeading('welshlibdem', 'LD', '#FAA61A')}${nationTablePartyHeading('plaid', 'Plaid', '#008672')}<th scope="col">Other</th><th scope="col">Total</th></tr></thead>
        <tbody>${rows}</tbody>
      </table></div>
    </div>`;
  } else if (id === 'scotland' && nation.westminsterResults) {
    const snpCol = nationPartyTextColor('snp', '#FDF38E');
    const rows = nation.westminsterResults.map(r => `<tr>
      ${westminsterYearCell(r.year)}
      <td style="color:${nationPartyTextColor('scottishcon', '#0087DC')};font-weight:600">${r.con > 0 ? r.con : '—'}</td>
      <td style="color:${nationPartyTextColor('scottishlab', '#E4003B')};font-weight:600">${r.lab > 0 ? r.lab : '—'}</td>
      <td style="color:${nationPartyTextColor('scottishlibdem', '#FAA61A')};font-weight:600">${r.ld > 0 ? r.ld : '—'}</td>
      <td style="color:${snpCol};font-weight:600">${r.snp > 0 ? r.snp : '—'}</td>
      <td style="color:var(--text-muted)">${r.other > 0 ? r.other : '—'}</td>
      <td style="color:var(--cream-dark);font-size:0.8rem">${r.total}</td>
    </tr>`).join('');
    westminsterSection = `<div class="devolved-section" style="margin-bottom:2.5rem">
      <span class="section-label">Westminster General Elections</span>
      <h2>Seats Won: Scotland, 1918–2024</h2>
      <div class="gold-rule"></div>
      <p style="color:var(--text-muted);font-size:0.85rem;margin-bottom:1.5rem">"LD" includes Coalition Liberal (1918), National Liberal (1922–45), Liberal/SDP Alliance (1983–87), Liberal Democrats (1988–). Scotland had 71–72 seats 1918–2001; reduced to 59 from 2005, and 57 from 2024. "Other" in the interwar period includes ILP MPs (Glasgow). The precise breakdown of "Other" seats is not available in the source document. Sources: HC Library CBP-7529 (1918–2019); HC Library CBP-10009 (2024).</p>
      <div style="overflow-x:auto"><table class="results-table">
        <thead><tr><th scope="col">Year</th>${nationTablePartyHeading('scottishcon', 'Con')}${nationTablePartyHeading('scottishlab', 'Lab')}${nationTablePartyHeading('scottishlibdem', 'LD')}${nationTablePartyHeading('snp', 'SNP')}<th scope="col">Other</th><th scope="col">Total</th></tr></thead>
        <tbody>${rows}</tbody>
      </table></div>
    </div>`;
  } else if (id === 'northern-ireland' && nation.westminsterEarly && nation.westminsterResults) {
    const earlyRows = nation.westminsterEarly.map(r => `<tr>
      ${westminsterYearCell(r.year)}
      <td style="color:#0087DC;font-weight:600">${r.unionist}</td>
      <td style="color:#2AA82C;font-weight:600">${r.nationalist > 0 ? r.nationalist : '—'}</td>
      <td style="color:var(--text-muted)">${r.other > 0 ? r.other : '—'}</td>
      <td style="color:var(--cream-dark);font-size:0.8rem">${r.total}</td>
    </tr>`).join('');
    const modernRows = nation.westminsterResults.map(r => `<tr>
      ${westminsterYearCell(r.year)}
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
        <thead><tr><th scope="col">Year</th><th scope="col" style="color:#0087DC">Unionist¹</th><th scope="col" style="color:#2AA82C">Nationalist</th><th scope="col">Other</th><th scope="col">Total</th></tr></thead>
        <tbody>${earlyRows}</tbody>
      </table></div>
      <p style="color:var(--cream-dark);font-size:0.85rem;font-weight:600;margin-bottom:0.5rem">1974–2024</p>
      <div style="overflow-x:auto"><table class="results-table">
        <thead><tr><th scope="col">Year</th>${nationTablePartyHeading('uup', 'UUP', '#48A5EE')}${nationTablePartyHeading('sdlp', 'SDLP', '#2AA82C')}${nationTablePartyHeading('dup', 'DUP', '#D46A4C')}${nationTablePartyHeading('sinnfein', 'Sinn Féin', '#326760')}<th scope="col">Other²</th><th scope="col">Total</th></tr></thead>
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
      <td><span style="color:${nationPartyTextColor('welshlab', '#E4003B')};font-weight:600">${r.lab}</span></td>
      <td><span style="color:${nationPartyTextColor('plaid', '#008672')};font-weight:600">${r.pc}</span></td>
      <td><span style="color:${nationPartyTextColor('welshcon', '#0087DC')};font-weight:600">${r.con}</span></td>
      <td><span style="color:${nationPartyTextColor('welshlibdem', '#FAA61A')};font-weight:600">${r.ld}</span></td>
      ${r.ukip !== undefined ? `<td><span style="color:${nationPartyTextColor('ukip', '#70147A')};font-weight:600">${r.ukip > 0 ? r.ukip : '—'}</span></td>` : '<td>—</td>'}
      <td><span style="color:${nationPartyTextColor('reform', '#12B6CF')};font-weight:600">${r.reform > 0 ? r.reform : '—'}</span></td>
    </tr>`).join('');
    devolvedTable = `<div class="devolved-section">
      <span class="section-label">Senedd Cymru Elections</span>
      <h2>Welsh Parliament Results</h2>
      <div class="gold-rule"></div>
      <p style="color:var(--text-muted);font-size:0.9rem;margin-bottom:1.5rem">60 Members elected by AMS (1999–2021); 96 Members from 2026 under closed-list PR. Labour was the largest party at every election until 2026. <a href="/devolved/senedd">View full Senedd archive →</a></p>
      <table class="results-table">
        <thead><tr><th scope="col">Year</th>${nationTablePartyHeading('welshlab', 'Labour')}${nationTablePartyHeading('plaid', 'Plaid')}${nationTablePartyHeading('welshcon', 'Cons.')}${nationTablePartyHeading('welshlibdem', 'Lib Dem')}${nationTablePartyHeading('ukip', 'UKIP')}${nationTablePartyHeading('reform', 'Reform')}</tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
  }

  if (id === 'scotland' && nation.holyroodResults) {
    const rows = nation.holyroodResults.map(r => `<tr>
      <td style="color:var(--cream);font-family:var(--font-display);font-size:1.1rem"><a href="/devolved/holyrood/${r.year}" style="color:inherit;text-decoration:none">${r.year}</a></td>
      <td><span style="color:${nationPartyTextColor('snp', '#FDF38E')};font-weight:600">${r.snp}</span></td>
      <td><span style="color:${nationPartyTextColor('scottishlab', '#E4003B')};font-weight:600">${r.lab}</span></td>
      <td><span style="color:${nationPartyTextColor('scottishcon', '#0087DC')};font-weight:600">${r.con}</span></td>
      <td><span style="color:${nationPartyTextColor('scottishlibdem', '#FAA61A')};font-weight:600">${r.ld}</span></td>
      <td><span style="color:${nationPartyTextColor('scottishgrn', '#00B140')};font-weight:600">${r.grn}</span></td>
      <td><span style="color:${nationPartyTextColor('reform', '#12B6CF')};font-weight:600">${r.reform > 0 ? r.reform : '—'}</span></td>
    </tr>`).join('');
    devolvedTable = `<div class="devolved-section">
      <span class="section-label">Scottish Parliament Elections</span>
      <h2>Holyrood Results</h2>
      <div class="gold-rule"></div>
      <p style="color:var(--text-muted);font-size:0.9rem;margin-bottom:1.5rem">129 MSPs elected by Additional Member System (73 constituency + 56 regional). The SNP has governed Scotland since 2007. <a href="/devolved/holyrood">View full Holyrood archive →</a></p>
      <table class="results-table">
        <thead><tr><th scope="col">Year</th>${nationTablePartyHeading('snp', 'SNP')}${nationTablePartyHeading('scottishlab', 'Labour')}${nationTablePartyHeading('scottishcon', 'Cons.')}${nationTablePartyHeading('scottishlibdem', 'Lib Dem')}${nationTablePartyHeading('scottishgrn', 'Greens')}${nationTablePartyHeading('reform', 'Reform')}</tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
  }

  if (id === 'northern-ireland' && nation.assemblyResults) {
    const rows = nation.assemblyResults.map(r => `<tr>
      <td style="color:var(--cream);font-family:var(--font-display);font-size:1.1rem">${r.year}</td>
      <td><span style="color:${nationPartyTextColor('dup', '#D46A4C')};font-weight:600">${r.dup}</span></td>
      <td><span style="color:${nationPartyTextColor('sinnfein', '#326760')};font-weight:600">${r.sf}</span></td>
      <td><span style="color:${nationPartyTextColor('uup', '#48A5EE')};font-weight:600">${r.uup}</span></td>
      <td><span style="color:${nationPartyTextColor('sdlp', '#2AA82C')};font-weight:600">${r.sdlp}</span></td>
      <td><span style="color:${nationPartyTextColor('alliance', '#F6CB2F')};font-weight:600">${r.alliance}</span></td>
    </tr>`).join('');
    devolvedTable = `<div class="devolved-section">
      <span class="section-label">Northern Ireland Assembly Elections</span>
      <h2>Stormont Results</h2>
      <div class="gold-rule"></div>
      <p style="color:var(--text-muted);font-size:0.9rem;margin-bottom:1.5rem">90 MLAs elected by Single Transferable Vote (5 per constituency). In 2022 Sinn Féin became the largest party for the first time since partition in 1922. Source: HC Library CBP-7529.</p>
      <table class="results-table">
        <thead><tr><th scope="col">Year</th>${nationTablePartyHeading('dup', 'DUP')}${nationTablePartyHeading('sinnfein', 'Sinn Féin')}${nationTablePartyHeading('uup', 'UUP')}${nationTablePartyHeading('sdlp', 'SDLP')}${nationTablePartyHeading('alliance', 'Alliance')}</tr></thead>
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
        <span class="section-label">${id === 'europe' ? 'United Kingdom — European Alliances' : 'United Kingdom — Four Nations'}</span>
        <h1 class="nation-hero-title">${nation.name}</h1>
        <div class="gold-rule"></div>
        <div class="nation-hero-stats">
          ${id === 'europe' ? `
          <div class="nation-stat"><div class="nation-stat-num">73</div><div class="nation-stat-label">UK MEPs (2019)</div></div>
          <div class="nation-stat"><div class="nation-stat-num">1979–2019</div><div class="nation-stat-label">Nine EP Elections</div></div>
          <div class="nation-stat"><div class="nation-stat-num" style="font-size:0.85rem;letter-spacing:0.04em">${nation.electoralSystem.split(';')[0].trim()}</div><div class="nation-stat-label">Electoral System</div></div>
          ` : `
          <div class="nation-stat"><div class="nation-stat-num">${nation.constituencies}</div><div class="nation-stat-label">Westminster Constituencies</div></div>
          ${nation.devolvedBody ? `<div class="nation-stat"><div class="nation-stat-num">${nation.devolvedYear}</div><div class="nation-stat-label">${nation.devolvedBody} Established</div></div>` : '<div class="nation-stat"><div class="nation-stat-num">—</div><div class="nation-stat-label">No Devolved Parliament</div></div>'}
          <div class="nation-stat"><div class="nation-stat-num" style="font-size:0.85rem;letter-spacing:0.04em">${nation.electoralSystem.split(';')[0].trim()}</div><div class="nation-stat-label">Westminster Electoral System</div></div>
          `}
        </div>
      </div>
    </section>

    <div class="nation-body">
      <div class="nation-grid">
        <div>
          <p class="nation-description">${nation.description}</p>
          ${keyFacts ? `<div class="highlights-list" style="margin-top:2rem"><h3>Key Facts</h3>${keyFacts}</div>` : ''}
          ${euroSection}
          ${westminsterSection}
          ${devolvedTable}
          <p style="font-size:0.75rem;color:var(--text-faint);margin-top:1.5rem">Source: ${nation.source}</p>
        </div>
        <div class="nation-aside">
          <div class="nation-parties-card">
            <div class="section-label" style="margin-bottom:1rem">${id === 'europe' ? 'Alliance families' : `Parties in ${nation.name}`}</div>
            ${partyLinks}
            ${id === 'england' ? `<a href="/others" class="nation-party-link" style="--party-color:var(--gold)"><span class="nation-party-dot" style="background:var(--gold)"></span><span>Other parties →</span></a>` : ''}
            ${id === 'scotland' ? `<a href="/devolved/holyrood/other-parties" class="holyrood-other-link">Other Scottish parties →</a>` : ''}
            ${id === 'wales' ? `<a href="/devolved/senedd/other-parties" class="holyrood-other-link">Other Welsh parties →</a>` : ''}
            ${id === 'northern-ireland' ? `<a href="/devolved/stormont/other-parties" class="holyrood-other-link">Other Northern Irish parties →</a>` : ''}
            ${id === 'europe' ? `<a href="/devolved/euro/other-parties" class="holyrood-other-link">Other EP parties →</a>` : ''}
          </div>
          ${nationArchiveLink(id)}
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
    description: `Election results and party manifestos for the ${portal.label}.`,
    path: `/devolved/${id}`,
  });

  const nation = NATIONS[portal.nation];
  const navConfig = NAV_PARTIES[portal.nation];
  const partyLinks = navConfig ? navConfig.parties.map(pid => nationPartyLinkHtml(pid)).join('') : '';

  app.innerHTML = `
    ${renderBreadcrumb([
      { label: 'Home', href: '/' },
      { label: 'Beyond Westminster', href: '/devolved' },
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
    description: 'Smaller and historical UK political parties and the manifestos they published.',
    path: '/others',
  });
  const cards = [...OTHERS_PARTIES]
    .sort((a, b) => (PARTIES[a]?.name || a).localeCompare(PARTIES[b]?.name || b, 'en-GB'))
    .map(pid => buildPartyBrowseCard(pid, { fullName: true, meta: true }))
    .join('');

  app.innerHTML = `
    <div class="about-section">
      <span class="section-label">Parties</span>
      <h1>Other Parties</h1>
      <div class="gold-rule"></div>
      <p style="color:var(--text-muted);margin-bottom:1.5rem">Smaller, fringe, single-issue, and historical parties that have contested UK general elections. Many have had a disproportionate influence on British politics despite winning few or no seats.</p>
      <div class="others-devolved-grid">
        <div class="others-devolved-cell">
          <div class="others-devolved-label">Scottish Parliament</div>
          <a href="/devolved/holyrood/other-parties" class="others-devolved-link"><span>Other Scottish Parties</span><span class="others-devolved-arrow" aria-hidden="true">→</span></a>
        </div>
        <div class="others-devolved-cell">
          <div class="others-devolved-label">Welsh Parliament</div>
          <a href="/devolved/senedd/other-parties" class="others-devolved-link"><span>Other Welsh Parties</span><span class="others-devolved-arrow" aria-hidden="true">→</span></a>
        </div>
        <div class="others-devolved-cell">
          <div class="others-devolved-label">Northern Ireland Assembly</div>
          <a href="/devolved/stormont/other-parties" class="others-devolved-link"><span>Other Northern Irish Parties</span><span class="others-devolved-arrow" aria-hidden="true">→</span></a>
        </div>
        <div class="others-devolved-cell">
          <div class="others-devolved-label">European Parliament</div>
          <a href="/devolved/euro/other-parties" class="others-devolved-link"><span>Other European Parliament Parties</span><span class="others-devolved-arrow" aria-hidden="true">→</span></a>
        </div>
      </div>
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
  if (raw === 'null' || raw === 'Null' || raw === 'NULL' || raw === '~') return null;
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

function extractManifestoDocTitle(body) {
  if (!body) return '';
  const italic = body.match(/^\*([^*\n]+)\*/m);
  if (italic) return italic[1].trim();
  return '';
}

function estimateReadingMinutes(text) {
  const words = (text || '').trim().split(/\s+/).filter(Boolean).length;
  return Math.max(1, Math.round(words / 220));
}

function enhanceManifestoHtml(html, accent) {
  const wrap = document.createElement('div');
  wrap.innerHTML = html;
  wrap.style.setProperty('--manifesto-party-colour', accent.surface);
  // Keep chrome <h1> as the sole page heading — demote the document's first H1
  // (from manifesto.md) to a styled masthead (I07 / sandbox/i07-manifesto-heading.html).
  const firstH1 = wrap.querySelector('h1');
  if (firstH1) {
    const masthead = document.createElement('p');
    masthead.className = 'manifesto-doc-masthead';
    masthead.innerHTML = firstH1.innerHTML;
    firstH1.replaceWith(masthead);
  }
  wrap.querySelectorAll('h2').forEach((h2, idx) => {
    if (!h2.id) h2.id = `section-${idx + 1}`;
    const label = h2.textContent.trim();
    if (!h2.querySelector('.manifesto-section-link')) {
      h2.innerHTML = `<a href="#${h2.id}" class="manifesto-section-link">${label}</a>`;
    }
  });
  const firstP = wrap.querySelector('p:not(.manifesto-doc-masthead)');
  if (firstP) firstP.classList.add('manifesto-lede');
  return wrap.innerHTML;
}

function buildManifestoTocLinks(headings) {
  return headings.map((h, i) => {
    const id = h.id || `section-${i + 1}`;
    const label = h.querySelector('.manifesto-section-link')?.textContent?.trim()
      || h.textContent.trim();
    return `<a href="#${id}" class="manifesto-toc-link" data-section-index="${i}">${label}</a>`;
  }).join('');
}

function manifestoNavOffset() {
  const navH = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--nav-h'), 10) || 68;
  return navH + 24;
}

function scrollToManifestoSection(id, { smooth = true } = {}) {
  const el = document.getElementById(id);
  if (!el) return false;
  const top = el.getBoundingClientRect().top + window.scrollY - manifestoNavOffset();
  window.scrollTo({ top: Math.max(0, top), behavior: smooth ? 'smooth' : 'auto' });
  return true;
}

function bindManifestoSectionLinks(root, onNavigate) {
  if (!root) return;
  root.querySelectorAll('a[href^="#section-"]').forEach(link => {
    link.addEventListener('click', (e) => {
      const id = link.getAttribute('href').slice(1);
      if (!id) return;
      e.preventDefault();
      if (scrollToManifestoSection(id)) {
        history.replaceState(null, '', `${getPath()}#${id}`);
        if (typeof onNavigate === 'function') onNavigate(id);
      }
    });
  });
}

function applyManifestoSectionHash() {
  const hash = window.location.hash;
  if (!hash.startsWith('#section-')) return;
  const id = hash.slice(1);
  requestAnimationFrame(() => {
    if (scrollToManifestoSection(id, { smooth: false })) {
      const headings = [...document.querySelectorAll('#manifesto-content h2[id]')];
      const idx = headings.findIndex(h => h.id === id);
      if (idx >= 0) {
        document.querySelectorAll('.manifesto-toc-link').forEach((link, i) => {
          link.classList.toggle('is-active', i === idx);
        });
        const cur = document.getElementById('manifesto-section-current');
        if (cur) cur.textContent = String(idx + 1);
      }
    }
  });
}

function buildManifestoHeaderMetaHtml(election, meta, body) {
  const items = [`<span>${election.date}</span>`];
  if (meta?.party_leader) items.push(`<span>${meta.party_leader}</span>`);
  const wordCount = (body || '').trim().split(/\s+/).filter(Boolean).length;
  if (wordCount > 0 || meta?.page_count) {
    const estPages = meta?.page_count || Math.max(1, Math.round(wordCount / 450));
    items.push(`<span>${estPages} pages</span>`);
  }
  const docTitle = extractManifestoDocTitle(body || '');
  if (docTitle) items.push(`<em class="meta-doc-title">${docTitle}</em>`);
  return items.join('<span class="meta-sep" aria-hidden="true">·</span>');
}

function manifestoLoadErrorHtml(pdfPath, hasPdf) {
  return `<div class="manifesto-empty-state" role="alert">
    <div class="manifesto-empty-kicker">Couldn’t load manifesto text</div>
    <p class="manifesto-empty-text">The text file failed to load. Check your connection and try again.</p>
    <div class="manifesto-empty-actions">
      <button type="button" class="manifesto-btn-solid" id="manifesto-retry">Try again</button>
      ${hasPdf ? `<a href="${pdfPath}" class="manifesto-btn-ghost" target="_blank" rel="noopener">View original PDF</a>` : ''}
    </div>
  </div>`;
}

function manifestoEmptyStateHtml(pdfPath, hasPdf) {
  const bodyCopy = hasPdf
    ? "This manifesto hasn't been transcribed yet, but the original scan is available."
    : "This manifesto hasn't been transcribed yet.";
  return `<div class="manifesto-empty-state">
    <div class="manifesto-empty-kicker">Text version not yet archived</div>
    <p class="manifesto-empty-text">${bodyCopy}</p>
    <div class="manifesto-empty-actions">
      ${hasPdf ? `<a href="${pdfPath}" class="manifesto-btn-solid" target="_blank" rel="noopener">View original PDF</a>` : ''}
      <a href="/about" class="manifesto-btn-ghost">How to contribute</a>
    </div>
  </div>`;
}

/** No PDF, no cover, and no Markdown — the document is not in the archive yet. */
function manifestoUnavailableHtml({ electionUrl, electionLabel, partyUrl, partyName }) {
  const partyLink = partyUrl
    ? `<a href="${partyUrl}" class="manifesto-btn-solid">${partyName} party page</a>`
    : '';
  return `<div class="manifesto-empty-state manifesto-empty-state--unavailable">
    <div class="manifesto-empty-kicker">Not yet in the archive</div>
    <p class="manifesto-empty-text">
      We don’t currently hold a PDF, cover image, or readable text for this manifesto.
      It may not have survived in a form we can publish, or it may still be waiting to be sourced.
    </p>
    <div class="manifesto-empty-actions">
      <a href="${electionUrl}" class="manifesto-btn-solid">${electionLabel}</a>
      ${partyLink}
      <a href="/about#contact-and-corrections" class="manifesto-btn-ghost">Contact and corrections</a>
    </div>
  </div>`;
}

function setupManifestoCite() {
  const citeEl = document.getElementById('manifesto-cite');
  if (!citeEl) return;
  const textEl = document.getElementById('manifesto-cite-text');
  const citation = (textEl?.textContent || '').replace(/\s+/g, ' ').trim();
  const urlEl = citeEl.querySelector('.manifesto-cite-url');
  const url = (urlEl?.textContent || window.location.href).trim();

  const flash = (btn, label) => {
    if (!btn) return;
    const prev = btn.textContent;
    btn.textContent = label;
    setTimeout(() => { btn.textContent = prev; }, 1600);
  };

  document.getElementById('manifesto-copy-citation')?.addEventListener('click', async () => {
    const btn = document.getElementById('manifesto-copy-citation');
    try {
      await navigator.clipboard.writeText(citation);
      flash(btn, 'Copied');
    } catch (_) {
      flash(btn, 'Copy failed');
    }
  });
  document.getElementById('manifesto-copy-link')?.addEventListener('click', async () => {
    const btn = document.getElementById('manifesto-copy-link');
    try {
      await navigator.clipboard.writeText(url);
      flash(btn, 'Copied');
    } catch (_) {
      flash(btn, 'Copy failed');
    }
  });
}

function setupManifestoFind(contentEl) {
  const desktop = document.getElementById('manifesto-find');
  const mobile = document.getElementById('manifesto-find-mobile');
  const isEmpty = contentEl.classList.contains('manifesto-content--empty')
    || contentEl.querySelector('.manifesto-empty-state');
  if (isEmpty || !contentEl.textContent?.trim()) {
    if (desktop) desktop.hidden = true;
    if (mobile) mobile.hidden = true;
    return;
  }
  if (desktop) desktop.hidden = false;
  if (mobile) mobile.hidden = false;

  const inputs = [
    document.getElementById('manifesto-find-input'),
    document.getElementById('manifesto-find-input-mobile'),
  ].filter(Boolean);
  const counts = [
    document.getElementById('manifesto-find-count'),
    document.getElementById('manifesto-find-count-mobile'),
  ].filter(Boolean);
  const prevBtns = [
    document.getElementById('manifesto-find-prev'),
    document.getElementById('manifesto-find-prev-mobile'),
  ].filter(Boolean);
  const nextBtns = [
    document.getElementById('manifesto-find-next'),
    document.getElementById('manifesto-find-next-mobile'),
  ].filter(Boolean);

  let marks = [];
  let active = -1;
  let debounceTimer = null;

  const clearMarks = () => {
    contentEl.querySelectorAll('mark.manifesto-find-hit').forEach(mark => {
      const parent = mark.parentNode;
      if (!parent) return;
      parent.replaceChild(document.createTextNode(mark.textContent), mark);
      parent.normalize();
    });
    marks = [];
    active = -1;
  };

  const paintCount = () => {
    const label = !marks.length
      ? (inputs[0]?.value.trim() ? '0 matches' : '')
      : `${active + 1} of ${marks.length}`;
    counts.forEach(el => { el.textContent = label; });
    const disabled = marks.length === 0;
    [...prevBtns, ...nextBtns].forEach(btn => { btn.disabled = disabled; });
    marks.forEach((m, i) => m.classList.toggle('is-current', i === active));
  };

  const goTo = (index) => {
    if (!marks.length) return;
    active = ((index % marks.length) + marks.length) % marks.length;
    paintCount();
    const el = marks[active];
    el.scrollIntoView({ block: 'center', behavior: 'smooth' });
  };

  const runFind = (query) => {
    clearMarks();
    const q = (query || '').trim();
    if (q.length < 2) {
      paintCount();
      return;
    }
    const qLower = q.toLowerCase();
    const walker = document.createTreeWalker(contentEl, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        if (!node.nodeValue || !node.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
        if (node.parentElement?.closest('script, style')) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      },
    });
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(node => {
      const text = node.nodeValue;
      const lower = text.toLowerCase();
      let from = 0;
      let idx = lower.indexOf(qLower, from);
      if (idx === -1) return;
      const frag = document.createDocumentFragment();
      while (idx !== -1) {
        if (idx > from) frag.appendChild(document.createTextNode(text.slice(from, idx)));
        const mark = document.createElement('mark');
        mark.className = 'manifesto-find-hit';
        mark.textContent = text.slice(idx, idx + q.length);
        frag.appendChild(mark);
        marks.push(mark);
        from = idx + q.length;
        idx = lower.indexOf(qLower, from);
      }
      if (from < text.length) frag.appendChild(document.createTextNode(text.slice(from)));
      node.parentNode?.replaceChild(frag, node);
    });
    if (marks.length) goTo(0);
    else paintCount();
  };

  const syncInputs = (value, source) => {
    inputs.forEach(input => {
      if (input !== source) input.value = value;
    });
  };

  inputs.forEach(input => {
    input.addEventListener('input', () => {
      syncInputs(input.value, input);
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => runFind(input.value), 120);
    });
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        if (e.shiftKey) goTo(active - 1);
        else goTo(active + 1);
      } else if (e.key === 'Escape') {
        e.preventDefault();
        input.value = '';
        syncInputs('', input);
        clearMarks();
        paintCount();
        input.blur();
      }
    });
  });
  prevBtns.forEach(btn => btn.addEventListener('click', () => goTo(active - 1)));
  nextBtns.forEach(btn => btn.addEventListener('click', () => goTo(active + 1)));

  const onSlash = (e) => {
    if (e.key !== '/' || e.metaKey || e.ctrlKey || e.altKey) return;
    const tag = (e.target?.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea' || e.target?.isContentEditable) return;
    if (!document.getElementById('manifesto-content')) return;
    e.preventDefault();
    const target = window.matchMedia('(max-width: 900px)').matches
      ? document.getElementById('manifesto-find-input-mobile')
      : document.getElementById('manifesto-find-input');
    const mobilePanel = document.querySelector('.manifesto-toc-mobile');
    if (target === document.getElementById('manifesto-find-input-mobile') && mobilePanel) {
      mobilePanel.open = true;
    }
    target?.focus();
    target?.select();
  };
  document.addEventListener('keydown', onSlash);
}

function setupManifestoReader(contentEl, paperEl, accent) {
  const headings = [...contentEl.querySelectorAll('h2[id]')];
  const tocHtml = buildManifestoTocLinks(headings);
  const tocList = document.getElementById('manifesto-toc-list');
  const tocMobileList = document.getElementById('manifesto-toc-mobile-list');
  const tocMeta = document.getElementById('manifesto-toc-meta');
  const tocLabel = document.getElementById('manifesto-toc-label');
  const tocDivider = document.getElementById('manifesto-toc-divider');
  const minutes = estimateReadingMinutes(contentEl.textContent || '');
  const isEmpty = contentEl.classList.contains('manifesto-content--empty')
    || Boolean(contentEl.querySelector('.manifesto-empty-state'));

  const tocAside = document.querySelector('.manifesto-toc');
  const tocMobilePanel = document.querySelector('.manifesto-toc-mobile');
  const hasToc = headings.length > 0;
  const showSidebar = !isEmpty && (hasToc || Boolean(document.getElementById('manifesto-find')));
  if (tocAside) tocAside.hidden = !showSidebar;
  if (tocMobilePanel) tocMobilePanel.hidden = !showSidebar;
  if (tocLabel) tocLabel.hidden = !hasToc;
  if (tocDivider) tocDivider.hidden = !hasToc;
  if (tocList) {
    tocList.innerHTML = tocHtml;
    tocList.hidden = !hasToc;
  }
  if (tocMobileList) {
    tocMobileList.innerHTML = tocHtml;
    tocMobileList.hidden = !hasToc;
  }
  if (tocMeta) {
    tocMeta.innerHTML = isEmpty
      ? ''
      : `Reading time ~${minutes} min${hasToc ? `<br>Section <span id="manifesto-section-current">1</span> of ${Math.max(headings.length, 1)}` : ''}`;
  }

  setupManifestoCite();
  setupManifestoFind(contentEl);

  const progressRead = document.getElementById('manifesto-progress-read');
  const progressTrack = document.getElementById('manifesto-progress-track');
  if (progressTrack) {
    progressTrack.style.background = typeof rgbaHex === 'function'
      ? rgbaHex(accent.raw, 0.15)
      : 'rgba(255,255,255,0.15)';
  }
  if (progressRead) progressRead.style.background = accent.surface;

  const links = document.querySelectorAll('.manifesto-toc-link');
  const setActive = (index) => {
    links.forEach((link, i) => {
      link.classList.toggle('is-active', i === index);
      if (i === index) {
        link.style.borderLeftColor = accent.surface;
        link.style.background = typeof rgbaHex === 'function' ? rgbaHex(accent.raw, 0.10) : 'rgba(255,255,255,0.08)';
      } else {
        link.style.borderLeftColor = 'transparent';
        link.style.background = 'transparent';
      }
    });
    const cur = document.getElementById('manifesto-section-current');
    if (cur && index >= 0) cur.textContent = String(index + 1);
  };

  const updateProgress = () => {
    if (!paperEl || !progressRead) return;
    const start = paperEl.getBoundingClientRect().top + window.scrollY;
    const end = start + paperEl.offsetHeight - window.innerHeight;
    const pct = end > start
      ? Math.min(100, Math.max(0, ((window.scrollY - start) / (end - start)) * 100))
      : (window.scrollY > start ? 100 : 0);
    progressRead.style.width = `${pct}%`;
  };

  function varNavOffset() {
    return manifestoNavOffset();
  }

  bindManifestoSectionLinks(document, (id) => {
    const idx = headings.findIndex(h => h.id === id);
    if (idx >= 0) setActive(idx);
  });
  applyManifestoSectionHash();
  window.addEventListener('hashchange', applyManifestoSectionHash);

  if (headings.length && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      const visible = entries.filter(e => e.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (visible) {
        const idx = headings.indexOf(visible.target);
        if (idx >= 0) setActive(idx);
      }
    }, { rootMargin: `-${varNavOffset()}px 0px -55% 0px`, threshold: [0, 0.25, 0.5, 1] });
    headings.forEach(h => observer.observe(h));
  } else if (headings.length) {
    setActive(0);
  }

  window.addEventListener('scroll', updateProgress, { passive: true });
  updateProgress();
  if (hasToc) setActive(0);
}

function manifestoFolderFromPath(path) {
  if (!path) return null;
  const segs = path.split('/').filter(Boolean);
  return segs.length >= 2 ? segs[segs.length - 2] : null;
}

function findDevolvedManifestoEntry(election, routeSlug) {
  if (!election?.manifestos || !routeSlug) return null;
  return election.manifestos.find(m => {
    // Prefer explicit folder id — never let affiliation "independent" steal a candidate folder.
    if (m.id === routeSlug) return true;
    if (manifestoFolderFromPath(m.pdf || m.md || m.cover) === routeSlug) return true;
    // Party/label fallback only when that value is also the folder (major parties: id === party).
    if (m.party === routeSlug && (!m.id || m.id === m.party)) return true;
    const labelSlug = m.partyLabel?.toLowerCase().replace(/[^a-z0-9]/g, '');
    return Boolean(labelSlug && labelSlug === routeSlug && (!m.id || m.id === labelSlug));
  }) || null;
}

async function renderManifesto(app, electionId, partyId) {
  let election;
  const isDevolved = electionId.includes('/');
  
  if (isDevolved) {
    try {
      election = await fetchTyped(`/data/devolved/${electionId}.json`, 'json');
    } catch {
      renderNotFound(app);
      return;
    }
  } else {
    election = getElection(electionId);
  }

  if (!election) { renderNotFound(app); return; }

  // Devolved (esp. London): resolve by folder/id first — independents are not PARTIES keys.
  const mEntry = isDevolved
    ? findDevolvedManifestoEntry(election, partyId)
    : election.manifestos?.find(m =>
        m.party === partyId ||
        m.partyLabel?.toLowerCase().replace(/[^a-z0-9]/g, '') === partyId);

  const colourId = (mEntry?.party && resolvePartyId(mEntry.party)) || partyId;
  const party = PARTIES[partyId] || PARTIES[colourId] || null;
  if (!isDevolved && !party) { renderNotFound(app); return; }
  // Devolved text pages require a real manifesto entry (folder id). Affiliation-only
  // URLs like /manifesto/london/2000/independent must not open a blank viewer.
  if (isDevolved && !mEntry) { renderNotFound(app); return; }

  const displayName = (election.manifestoPartyLabels && election.manifestoPartyLabels[partyId])
    || mEntry?.candidate
    || mEntry?.partyLabel
    || (party ? getPartyName(partyId, election.year) : null)
    || (colourId !== partyId && PARTIES[colourId] ? getPartyName(colourId, election.year) : null)
    || partyId;
  const theme = typeof getCurrentTheme === 'function' ? getCurrentTheme() : 'dark';
  const accent = typeof partyAccentDerivedForYear === 'function'
    ? partyAccentDerivedForYear(colourId, election.year, theme)
    : { raw: party?.color || '#6b7280', surface: party?.color || '#6b7280', kicker: party?.color || '#6b7280' };

  const folderSlug = (mEntry && manifestoFolderFromPath(mEntry.pdf || mEntry.md || mEntry.cover)) || partyId;
  const pdfPath = mEntry?.pdf || `/manifestos/${electionId}/${folderSlug}/manifesto.pdf`;
  const mdPath = mEntry?.md
    || (mEntry?.pdf ? mEntry.pdf.replace(/manifesto\.pdf$/i, 'manifesto.md') : null)
    || `/manifestos/${electionId}/${folderSlug}/manifesto.md`;
  const hasPdf = isDevolved ? Boolean(mEntry?.pdf) : hasManifestoPdf(electionId, partyId);
  const hasCover = isDevolved
    ? Boolean(mEntry?.cover)
    : hasManifestoCover(electionId, folderSlug);
  const electionUrl = isDevolved ? `/devolved/${electionId}` : `/election/${election.id}`;
  const electionLabel = isDevolved
    ? `${election.displayYear} ${DEVOLVED_PORTALS?.[electionId.split('/')[0]]?.label || 'Devolved'} Election`
    : `${election.displayYear} Election`;
  const kickerLabel = isDevolved
    ? `${DEVOLVED_PORTALS?.[electionId.split('/')[0]]?.label?.toUpperCase() || 'DEVOLVED'} ELECTION ${election.displayYear}`
    : `GENERAL ELECTION ${election.displayYear}`;

  // Breadcrumb party link: affiliation or route slug when a party page exists.
  const breadcrumbPartyId = (PARTIES[colourId] && colourId) || (PARTIES[partyId] && partyId) || null;
  const breadcrumbParty = breadcrumbPartyId
    ? `<a href="/party/${breadcrumbPartyId}">${PARTIES[breadcrumbPartyId] ? getPartyName(breadcrumbPartyId, election.year) : displayName}</a><span aria-hidden="true">›</span>`
    : `<span>${displayName}</span><span aria-hidden="true">›</span>`;

  const assets = isDevolved
    ? {
        pdf: Boolean(mEntry?.pdf),
        md: Boolean(mEntry?.md),
        cover: Boolean(mEntry?.cover),
      }
    : getManifestoAssetFlags(electionId, folderSlug);
  const hasMd = isDevolved ? Boolean(mEntry?.md) : hasManifestoMarkdown(electionId, folderSlug);
  const whollyUnavailable = Boolean(assets) && !hasPdf && !hasCover && !hasMd;

  if (whollyUnavailable) {
    setPageMeta({
      title: `${displayName} Manifesto ${election.displayYear}`,
      description: `The ${displayName} manifesto for the ${election.displayYear} election is not yet held in The British Manifesto Archive.`,
      path: `/manifesto/${electionId}/${partyId}`,
      noindex: true,
    });
    const barSurface = typeof barColour === 'function'
      ? barColour(getPartyColor(colourId, election.year), theme)
      : accent.surface;
    app.innerHTML = `
      <div class="manifesto-viewer-page manifesto-viewer-page--unavailable">
        <header class="manifesto-viewer-header">
          <div class="manifesto-viewer-header-inner">
            <nav class="manifesto-viewer-breadcrumb" aria-label="Breadcrumb">
              <a href="/">Home</a><span aria-hidden="true">›</span>
              <a href="${electionUrl}">${electionLabel}</a><span aria-hidden="true">›</span>
              ${breadcrumbParty}
              <span class="bc-current">Manifesto</span>
            </nav>
            <div class="manifesto-viewer-title-row">
              <div>
                <div class="manifesto-viewer-kicker">
                  <div class="manifesto-viewer-kicker-rule" style="background:${barSurface}"></div>
                  <div class="manifesto-viewer-kicker-text" style="color:${accent.kicker}">${kickerLabel}</div>
                </div>
                <h1 class="manifesto-viewer-title">${displayName} Manifesto ${election.displayYear}</h1>
                <div class="manifesto-viewer-meta-row">
                  <span>${election.date}</span>
                </div>
              </div>
            </div>
          </div>
        </header>
        <div class="manifesto-viewer-body manifesto-viewer-body--unavailable">
          <div class="manifesto-paper-wrap">
            <article class="manifesto-paper manifesto-paper--empty" id="manifesto-paper">
              <div id="manifesto-content" class="manifesto-content manifesto-content--empty">
                ${manifestoUnavailableHtml({
                  electionUrl,
                  electionLabel,
                  partyUrl: breadcrumbPartyId ? `/party/${breadcrumbPartyId}` : null,
                  partyName: displayName,
                })}
              </div>
            </article>
          </div>
        </div>
      </div>
    `;
    return;
  }

  const pdfSize = hasPdf ? getPdfSize(pdfPath) : '';

  const coverPath = mEntry?.cover
    ? `${mEntry.cover}?v=${ASSETS_VERSION}`
    : `/manifestos/${electionId}/${folderSlug}/cover.png?v=${ASSETS_VERSION}`;
  const coverFallback = mEntry?.cover
    ? `${mEntry.cover}?v=${ASSETS_VERSION}`
    : `/manifestos/${electionId}/${folderSlug}/cover.jpg?v=${ASSETS_VERSION}`;

  const coverThumbOpen = hasPdf
    ? `<a href="${pdfPath}" class="manifesto-viewer-cover-thumb" target="_blank" rel="noopener" aria-label="Open ${displayName} ${election.displayYear} manifesto PDF">`
    : `<div class="manifesto-viewer-cover-thumb">`;
  const coverThumbClose = hasPdf ? '</a>' : '</div>';
  const pdfDownloadLink = hasPdf
    ? pdfCtaHtml({ href: pdfPath, size: pdfSize, compact: true })
    : '';
  const coverThumbInner = hasCover
    ? `<img src="${coverPath}" alt="${displayName} ${election.displayYear} manifesto cover"
                  width="148" height="210" decoding="async"
                  onerror="if(!this.dataset.fb){this.dataset.fb='1';this.src='${coverFallback}';}else{this.style.display='none';const ph=this.nextElementSibling;if(ph)ph.style.display='flex';}">
                <div class="manifesto-thumb-placeholder manifesto-viewer-cover-placeholder" style="display:none" aria-hidden="true">
                  <div class="manifesto-placeholder-topbar"></div>
                  <div class="manifesto-placeholder-ghost">${election.year}</div>
                  <span class="manifesto-placeholder-label">Scan not yet archived</span>
                </div>`
    : `<div class="manifesto-thumb-placeholder manifesto-viewer-cover-placeholder" style="display:flex" aria-hidden="true">
                  <div class="manifesto-placeholder-topbar"></div>
                  <div class="manifesto-placeholder-ghost">${election.year}</div>
                  <span class="manifesto-placeholder-label">Scan not yet archived</span>
                </div>`;
  const coverPanel = hasCover || hasPdf
    ? `<div class="manifesto-viewer-cover" id="manifesto-viewer-cover">
              ${coverThumbOpen}
                ${coverThumbInner}
              ${coverThumbClose}
              ${pdfDownloadLink}
            </div>`
    : '';
  const barSurface = typeof barColour === 'function'
    ? barColour(getPartyColor(colourId, election.year), theme)
    : accent.surface;

  const pageTitle = `${displayName} Manifesto ${election.displayYear}`;
  setPageMeta({
    title: pageTitle,
    description: `Read the ${displayName} manifesto from the ${election.displayYear} ${isDevolved ? 'devolved' : 'general'} election — original PDF and online text where available.`,
    path: `/manifesto/${electionId}/${partyId}`,
  });

  app.innerHTML = `
    <div class="manifesto-viewer-page">
      <header class="manifesto-viewer-header">
        <div class="manifesto-viewer-header-inner">
          <nav class="manifesto-viewer-breadcrumb" aria-label="Breadcrumb">
            <a href="/">Home</a><span aria-hidden="true">›</span>
            <a href="${electionUrl}">${electionLabel}</a><span aria-hidden="true">›</span>
            ${breadcrumbParty}
            <span class="bc-current">Manifesto</span>
          </nav>
          <div class="manifesto-viewer-title-row">
            <div>
              <div class="manifesto-viewer-kicker">
                <div class="manifesto-viewer-kicker-rule" style="background:${barSurface}"></div>
                <div class="manifesto-viewer-kicker-text" style="color:${accent.kicker}">${kickerLabel}</div>
              </div>
              <h1 class="manifesto-viewer-title">${displayName} Manifesto ${election.displayYear}</h1>
              <div class="manifesto-viewer-meta-row" id="manifesto-header-meta">
                <span>${election.date}</span>
              </div>
              <div class="manifesto-cite" id="manifesto-cite">
                <div class="manifesto-cite-label">Cite</div>
                <p class="manifesto-cite-text" id="manifesto-cite-text">${displayName} (${election.displayYear}). <em>${pageTitle}</em>. The British Manifesto Archive. <span class="manifesto-cite-url">https://www.manifestos.org.uk/manifesto/${electionId}/${partyId}</span></p>
                <div class="manifesto-cite-actions">
                  <button type="button" class="manifesto-cite-btn" id="manifesto-copy-citation">Copy citation</button>
                  <button type="button" class="manifesto-cite-btn" id="manifesto-copy-link">Copy link</button>
                </div>
                <p class="manifesto-cite-note"><a href="/about">Sources and copyright</a></p>
              </div>
            </div>
            ${coverPanel}
          </div>
        </div>
      </header>
      <div class="manifesto-viewer-body">
        <aside class="manifesto-toc" aria-label="Table of contents">
          <div class="manifesto-find" id="manifesto-find" hidden>
            <label class="manifesto-find-label" for="manifesto-find-input">Find in this manifesto</label>
            <div class="manifesto-find-row">
              <input type="search" id="manifesto-find-input" class="manifesto-find-input" placeholder="Find…" autocomplete="off" spellcheck="false" />
              <span class="manifesto-find-count" id="manifesto-find-count" aria-live="polite"></span>
              <button type="button" class="manifesto-find-nav" id="manifesto-find-prev" aria-label="Previous match" disabled>↑</button>
              <button type="button" class="manifesto-find-nav" id="manifesto-find-next" aria-label="Next match" disabled>↓</button>
            </div>
          </div>
          <div class="manifesto-toc-label" id="manifesto-toc-label">CONTENTS</div>
          <nav class="manifesto-toc-list" id="manifesto-toc-list"></nav>
          <div class="manifesto-toc-divider" id="manifesto-toc-divider"></div>
          <div class="manifesto-toc-meta" id="manifesto-toc-meta"></div>
        </aside>
        <details class="manifesto-toc-mobile">
          <summary>Contents</summary>
          <div class="manifesto-find manifesto-find--mobile" id="manifesto-find-mobile" hidden>
            <label class="manifesto-find-label" for="manifesto-find-input-mobile">Find in this manifesto</label>
            <div class="manifesto-find-row">
              <input type="search" id="manifesto-find-input-mobile" class="manifesto-find-input" placeholder="Find…" autocomplete="off" spellcheck="false" />
              <span class="manifesto-find-count" id="manifesto-find-count-mobile" aria-live="polite"></span>
              <button type="button" class="manifesto-find-nav" id="manifesto-find-prev-mobile" aria-label="Previous match" disabled>↑</button>
              <button type="button" class="manifesto-find-nav" id="manifesto-find-next-mobile" aria-label="Next match" disabled>↓</button>
            </div>
          </div>
          <nav class="manifesto-toc-list" id="manifesto-toc-mobile-list"></nav>
        </details>
        <div class="manifesto-paper-wrap">
          <article class="manifesto-paper" id="manifesto-paper">
            <div class="manifesto-paper-progress" id="manifesto-progress-track" aria-hidden="true">
              <div class="manifesto-paper-progress-read" id="manifesto-progress-read"></div>
            </div>
            <div id="manifesto-content" class="manifesto-content">
              <div class="manifesto-skeleton" role="status" aria-label="Loading manifesto text">
                <div class="skeleton-line skeleton-title"></div>
                <div class="skeleton-line w-40"></div>
                <div class="skeleton-line"></div>
                <div class="skeleton-line"></div>
                <div class="skeleton-line w-85"></div>
                <span class="sr-only">Loading manifesto…</span>
              </div>
            </div>
          </article>
        </div>
      </div>
    </div>
  `;

  // Text known absent — skip the fetch and avoid a false “connection failed” message.
  if (assets && !hasMd) {
    const contentEl = document.getElementById('manifesto-content');
    const paperEl = document.getElementById('manifesto-paper');
    contentEl.innerHTML = manifestoEmptyStateHtml(pdfPath, hasPdf);
    contentEl.classList.add('manifesto-content--empty');
    paperEl?.classList.add('manifesto-paper--empty');
    setupManifestoReader(contentEl, paperEl, accent);
    return;
  }

  fetchTyped(mdPath, 'markdown')
    .then(md => {
      const { meta, body } = splitManifestoFrontmatter(md);
      const metaEl = document.getElementById('manifesto-header-meta');
      if (metaEl) metaEl.innerHTML = buildManifestoHeaderMetaHtml(election, meta, body);

      const contentEl = document.getElementById('manifesto-content');
      const paperEl = document.getElementById('manifesto-paper');
      const isEmpty = !body.trim();
      if (isEmpty) {
        contentEl.innerHTML = manifestoEmptyStateHtml(pdfPath, hasPdf);
        contentEl.classList.add('manifesto-content--empty');
        paperEl?.classList.add('manifesto-paper--empty');
      } else {
        contentEl.innerHTML = enhanceManifestoHtml(parseMarkdown(body), accent);
        contentEl.classList.remove('manifesto-content--empty');
        paperEl?.classList.remove('manifesto-paper--empty');
      }
      setupManifestoReader(contentEl, paperEl, accent);
    })
    .catch(() => {
      const metaEl = document.getElementById('manifesto-header-meta');
      if (metaEl) metaEl.innerHTML = buildManifestoHeaderMetaHtml(election, {}, '');
      const contentEl = document.getElementById('manifesto-content');
      const paperEl = document.getElementById('manifesto-paper');
      // Prefer an honest “not archived” message over a connection-error framing
      // when we already know there is no PDF either.
      contentEl.innerHTML = hasPdf || hasMd
        ? manifestoLoadErrorHtml(pdfPath, hasPdf)
        : manifestoUnavailableHtml({
            electionUrl,
            electionLabel,
            partyUrl: breadcrumbPartyId ? `/party/${breadcrumbPartyId}` : null,
            partyName: displayName,
          });
      contentEl.classList.add('manifesto-content--empty');
      paperEl?.classList.add('manifesto-paper--empty');
      document.getElementById('manifesto-retry')?.addEventListener('click', () => {
        renderManifesto(app, electionId, partyId);
      });
      setupManifestoReader(contentEl, paperEl, accent);
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
    title: 'UK General Elections',
    description: 'Browse every UK general election from 1945 to 2024 with results, seat maps, and the party manifestos published for each.',
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
        <p>Westminster contests — every postwar UK general election with results, manifesto documents, and campaign records. For devolved legislatures, use <a href="/devolved">Beyond Westminster</a>.</p>
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
    title: 'Beyond Westminster',
    description: 'The main path into devolved and regional elections — Scottish Parliament, Welsh Parliament, Northern Ireland Assembly, London Mayor & Assembly, and UK European Parliament contests.',
    path: '/devolved',
  });

  const portalTypeChip = {
    holyrood: 'Scottish Parliament',
    senedd: 'Senedd',
    stormont: 'Stormont',
    london: 'London',
    euro: 'European Parliament',
  };
  const cards = Object.values(DEVOLVED_PORTALS).map(portal => `
    <a href="/devolved/${portal.id}" class="hub-devolved-card">
      <span class="election-type-chip">${portalTypeChip[portal.id] || 'Institution'}</span>
      <strong>${portal.label}</strong>
      <span class="hub-devolved-sub">${portal.subtitle}</span>
      <p>${portal.description}</p>
      <span class="hub-card-cta">View portal →</span>
    </a>
  `).join('');

  app.innerHTML = `
    ${renderBreadcrumb([
      { label: 'Home', href: '/' },
      { label: 'Beyond Westminster' },
    ])}
    <div class="hub-page">
      <header class="hub-page-header">
        <span class="section-label">United Kingdom — Devolved Government</span>
        <h1>Beyond Westminster</h1>
        <div class="gold-rule"></div>
        <p>Institutions and their elections — Holyrood, the Senedd, Stormont, London Mayor &amp; Assembly, and UK European Parliament contests. This is the main path into devolved content.</p>
        <p class="hub-page-crosslink">Looking for parties by geography instead? Browse <a href="/nations">The Four Nations &amp; Europe</a>. For UK general elections, see <a href="/elections">Westminster</a>.</p>
      </header>
      <div class="hub-devolved-grid">${cards}</div>
    </div>
  `;
}

function renderNationsHub(app) {
  setPageMeta({
    title: 'The Four Nations & Europe',
    description: 'Browse parties and Westminster results by nation — England, Wales, Scotland, Northern Ireland — plus European political families. For devolved elections, use Beyond Westminster.',
    path: '/nations',
  });

  const cards = NATIONS_HUB_ORDER.map(id => buildNationHubCardHtml(id)).join('');

  app.innerHTML = `
    ${renderBreadcrumb([
      { label: 'Home', href: '/' },
      { label: 'Nations' },
    ])}
    <div class="hub-page">
      <header class="hub-page-header">
        <span class="section-label">United Kingdom</span>
        <h1>The Four Nations &amp; Europe</h1>
        <div class="gold-rule"></div>
        <p>A geography and party taxonomy — England, Wales, Scotland, and Northern Ireland, plus pan-European political families — with Westminster results by nation.</p>
        <p class="hub-page-crosslink">For devolved legislatures and their elections, go to <a href="/devolved">Beyond Westminster</a>.</p>
      </header>
      <div class="hub-nations-grid">${cards}</div>
    </div>
  `;
}

const PARTY_COLOUR_FAMILIES = [
  { id: 'red', label: 'Red', swatch: '#E4003B' },
  { id: 'orange', label: 'Orange', swatch: '#E67E22' },
  { id: 'yellow', label: 'Yellow', swatch: '#FAA61A' },
  { id: 'green', label: 'Green', swatch: '#00B140' },
  { id: 'teal', label: 'Teal', swatch: '#12B6CF' },
  { id: 'blue', label: 'Blue', swatch: '#0087DC' },
  { id: 'purple', label: 'Purple', swatch: '#70147A' },
  { id: 'magenta', label: 'Magenta', swatch: '#C51A70' },
  { id: 'brown', label: 'Brown', swatch: '#8B5E3C' },
  { id: 'grey', label: 'Grey / black', swatch: '#6b7280' },
];

const PARTY_BROWSE_NATIONS = [
  { id: 'england', label: 'England' },
  { id: 'scotland', label: 'Scotland' },
  { id: 'wales', label: 'Wales' },
  { id: 'northern-ireland', label: 'Northern Ireland' },
  { id: 'europe', label: 'Europe' },
  { id: 'uk', label: 'UK-wide' },
];

const PARTY_BROWSE_CONTESTS = [
  { id: 'westminster', label: 'Westminster' },
  { id: 'holyrood', label: 'Holyrood' },
  { id: 'senedd', label: 'Senedd' },
  { id: 'stormont', label: 'Stormont' },
  { id: 'london', label: 'London' },
  { id: 'euro', label: 'Europe' },
];

function colourFamilyFromHex(hex) {
  if (typeof hexToRgb !== 'function' || typeof rgbToOklch !== 'function') return 'grey';
  const lch = rgbToOklch(hexToRgb(hex || '#6b7280'));
  if (lch.C < 0.035 && lch.L < 0.35) return 'grey';
  if (lch.C < 0.025) return 'grey';
  const h = ((lch.H % 360) + 360) % 360;
  // Browns: low–mid chroma oranges with lower lightness
  if (h >= 35 && h < 75 && lch.L < 0.55 && lch.C < 0.12) return 'brown';
  if (h < 25 || h >= 345) return 'red';
  if (h < 55) return 'orange';
  if (h < 95) return 'yellow';
  if (h < 165) return 'green';
  // Teal includes Reform UK (#12B6CF, H≈212); Conservatives sit higher (~247)
  if (h < 230) return 'teal';
  if (h < 265) return 'blue';
  if (h < 305) return 'purple';
  return 'magenta';
}

function electionYearFromId(electionId) {
  const m = String(electionId || '').match(/(\d{4})/);
  return m ? parseInt(m[1], 10) : null;
}

function electionKindFromId(electionId) {
  const id = String(electionId || '');
  if (id.startsWith('london/')) return 'london';
  if (id.includes('/')) return id.split('/')[0];
  return 'westminster';
}

function splitArchiveKey(key) {
  const i = String(key).lastIndexOf('/');
  if (i < 0) return { electionId: '', partyId: key };
  return { electionId: key.slice(0, i), partyId: key.slice(i + 1) };
}

function buildPartyBrowseRows() {
  const docsByParty = new Map();
  const contestsByParty = new Map();

  const bumpDoc = (partyId, electionId, hasPdf) => {
    if (!partyId || partyId === 'others') return;
    let row = docsByParty.get(partyId);
    if (!row) {
      row = { years: new Set(), kinds: new Set(), hasPdf: false, hasText: false };
      docsByParty.set(partyId, row);
    }
    const year = electionYearFromId(electionId);
    if (year) row.years.add(year);
    row.kinds.add(electionKindFromId(electionId));
    if (hasPdf) row.hasPdf = true;
    row.hasText = true;
  };

  const bumpContest = (partyId, kind) => {
    if (!partyId || partyId === 'others' || !kind) return;
    let set = contestsByParty.get(partyId);
    if (!set) {
      set = new Set();
      contestsByParty.set(partyId, set);
    }
    set.add(kind);
  };

  if (MANIFESTO_ARCHIVE) {
    MANIFESTO_ARCHIVE.forEach(key => {
      const { electionId, partyId } = splitArchiveKey(key);
      bumpDoc(partyId, electionId, hasManifestoPdf(electionId, partyId));
      bumpContest(partyId, electionKindFromId(electionId));
    });
  }

  Object.keys(_pdfSizes || {}).forEach(path => {
    const m = path.match(/^\/manifestos\/(.+)\/([^/]+)\/manifesto\.pdf$/i);
    if (!m) return;
    bumpDoc(m[2], m[1], true);
    bumpContest(m[2], electionKindFromId(m[1]));
  });

  // Westminster contests from bundled election results (even without a manifesto on file)
  if (typeof ELECTIONS !== 'undefined') {
    ELECTIONS.forEach(e => {
      (e.extraManifestoParties || []).forEach(pid => bumpContest(pid, 'westminster'));
      (e.results || []).forEach(r => bumpContest(r.party, 'westminster'));
      Object.keys(e.partyResults || {}).forEach(pid => bumpContest(pid, 'westminster'));
    });
  }

  return Object.values(PARTIES)
    .filter(p => p && p.id && p.id !== 'others')
    .map(p => {
      const docs = docsByParty.get(p.id) || {
        years: new Set(), kinds: new Set(), hasPdf: false, hasText: false,
      };
      const years = [...docs.years].sort((a, b) => a - b);
      const foundedDecade = partyFoundedDecadeBucket(p.founded);
      const kinds = new Set([
        ...(p.contests || []),
        ...(contestsByParty.get(p.id) || []),
        ...docs.kinds,
      ]);

      const desc = `${p.description || ''}`.toLowerCase();
      const dissolved = /\b(dissolved|disbanded|wound up|merged into)\b/.test(desc);
      let status = p.status || null;
      if (!status) {
        if (dissolved) status = 'historical';
        else if (p.isPrimary) status = 'primary';
        else status = 'active';
      }

      const colourFamily = p.colourFamily || colourFamilyFromHex(p.color);
      let hue = 0;
      let lightness = 0.5;
      if (typeof hexToRgb === 'function' && typeof rgbToOklch === 'function') {
        const lch = rgbToOklch(hexToRgb(p.color || '#6b7280'));
        hue = ((lch.H % 360) + 360) % 360;
        lightness = lch.L;
      }

      const nationLabel = (p.nation || 'others') === 'others'
        ? 'Other'
        : (typeof getNationLabel === 'function' ? getNationLabel(p.nation) : p.nation);
      const tags = [
        ...(p.spectrum || '').split(/\s*\/\s*/).map(t => t.trim()).filter(Boolean),
        ...(nationLabel ? [nationLabel] : []),
      ];

      return {
        id: p.id,
        name: p.shortName || p.name,
        fullName: p.name,
        color: p.color || '#6b7280',
        spectrum: p.spectrum || '',
        nation: p.nation || 'others',
        nationLabel,
        colourFamily,
        hue,
        lightness,
        founded: p.founded || null,
        foundedDecade,
        tags,
        kinds: [...kinds],
        hasPdf: docs.hasPdf,
        hasText: docs.hasText,
        status,
        isPrimary: Boolean(p.isPrimary),
        searchText: `${p.name} ${p.shortName || ''} ${p.id}`.toLowerCase(),
      };
    })
    .sort((a, b) => a.name.localeCompare(b.name, 'en-GB'));
}

/** Founded decade bucket: 1890 = “1890s and earlier”; else floor to decade. */
function partyFoundedDecadeBucket(founded) {
  if (founded == null || Number.isNaN(founded)) return null;
  const d = Math.floor(founded / 10) * 10;
  return d < 1900 ? 1890 : d;
}

function partyFoundedDecadeLabel(decade) {
  if (decade == null) return '';
  return decade <= 1890 ? '1890s and earlier' : `${decade}s`;
}

function partyBrowseFoundedSteps(rows) {
  const present = [...new Set(rows.map(r => r.foundedDecade).filter(d => d != null))].sort((a, b) => a - b);
  if (!present.length) return [1890, 1900];
  const max = present[present.length - 1];
  const steps = [];
  for (let d = 1890; d <= max; d += 10) steps.push(d);
  return steps;
}

function readPartyBrowseFilters() {
  const params = new URLSearchParams(window.location.search);
  const tagsRaw = params.get('tags') || '';
  return {
    q: params.get('q') || '',
    colour: params.get('colour') || '',
    nation: params.get('nation') || '',
    foundedFrom: params.get('foundedFrom') || '',
    foundedTo: params.get('foundedTo') || '',
    // legacy single-decade param
    founded: params.get('founded') || params.get('decade') || '',
    status: params.get('status') || '',
    contest: params.get('contest') || '',
    docs: params.get('docs') || '',
    tags: tagsRaw ? tagsRaw.split('|').map(t => decodeURIComponent(t)).filter(Boolean) : [],
    tagQuery: '',
  };
}

function writePartyBrowseFilters(filters) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([k, v]) => {
    if (k === 'tagQuery') return;
    if (k === 'tags') {
      if (Array.isArray(v) && v.length) params.set('tags', v.map(encodeURIComponent).join('|'));
      return;
    }
    if (v) params.set(k, v);
  });
  const qs = params.toString();
  const next = qs ? `/parties/all?${qs}` : '/parties/all';
  if (`${window.location.pathname}${window.location.search}` !== next) {
    history.replaceState(null, '', next);
  }
}

function partyBrowseRowHtml(row) {
  const meta = [row.spectrum, row.nationLabel].filter(Boolean).join(' · ');
  return `<a href="/party/${row.id}" class="parties-all-row" role="listitem" data-party-id="${row.id}">
    <span class="mega-dot" style="${typeof dotStyle === 'function' ? dotStyle(row.color) : `background:${row.color}`}" aria-hidden="true"></span>
    <span class="parties-all-name">${row.name}</span>
    <span class="parties-all-meta">${meta}</span>
  </a>`;
}

function partyBrowseMatches(row, filters, foundedSteps) {
  if (filters.q) {
    const q = filters.q.trim().toLowerCase();
    if (q && !row.searchText.includes(q)) return false;
  }
  if (filters.colour && row.colourFamily !== filters.colour) return false;
  if (filters.nation && row.nation !== filters.nation) return false;

  const steps = foundedSteps || [];
  const minStep = steps[0];
  const maxStep = steps[steps.length - 1];
  let from = filters.foundedFrom !== '' ? parseInt(filters.foundedFrom, 10) : minStep;
  let to = filters.foundedTo !== '' ? parseInt(filters.foundedTo, 10) : maxStep;
  if (filters.founded && filters.foundedFrom === '' && filters.foundedTo === '') {
    from = to = parseInt(filters.founded, 10);
  }
  const rangeActive = steps.length && (from !== minStep || to !== maxStep);
  if (rangeActive) {
    if (row.foundedDecade == null) return false;
    if (row.foundedDecade < from || row.foundedDecade > to) return false;
  }

  if (filters.status === 'primary' && !row.isPrimary) return false;
  if (filters.status === 'historical' && row.status !== 'historical') return false;
  if (filters.status === 'active' && row.status === 'historical') return false;
  if (filters.contest && !row.kinds.includes(filters.contest)) return false;
  if (filters.docs === 'pdf' && !row.hasPdf) return false;
  if (filters.docs === 'text' && !row.hasText) return false;
  if (filters.docs === 'none' && (row.hasPdf || row.hasText)) return false;
  if (filters.tags && filters.tags.length) {
    const have = new Set(row.tags || []);
    if (!filters.tags.every(t => have.has(t))) return false;
  }
  return true;
}

function partyBrowseFilterChip(group, value, label, active) {
  return `<button type="button" class="filter-btn${active ? ' active' : ''}" data-browse-group="${group}" data-browse-value="${value}" aria-pressed="${active ? 'true' : 'false'}">${label}</button>`;
}

function renderPartySpectrumHtml(rows, filters) {
  const sorted = [...rows].sort((a, b) => {
    if (a.colourFamily === 'grey' && b.colourFamily !== 'grey') return 1;
    if (b.colourFamily === 'grey' && a.colourFamily !== 'grey') return -1;
    if (a.hue !== b.hue) return a.hue - b.hue;
    return a.lightness - b.lightness;
  });
  const bars = sorted.map(r => {
    const active = !filters.colour || r.colourFamily === filters.colour;
    return `<a href="/party/${r.id}" class="parties-spectrum-bar${active ? '' : ' is-dimmed'}" data-party-id="${r.id}" style="--bar:${r.color}" title="${r.fullName}" aria-label="${r.fullName}">
      <span class="parties-spectrum-tip">${r.name}</span>
    </a>`;
  }).join('');
  return `
    <div class="parties-spectrum" aria-label="Party colour">
      <span class="parties-browse-label">Party colour</span>
      <div class="parties-spectrum-track" role="list">${bars}</div>
    </div>`;
}

function renderPartyFoundedRangeHtml(rows, filters) {
  const steps = partyBrowseFoundedSteps(rows);
  const min = 0;
  const max = Math.max(0, steps.length - 1);
  let fromIdx = 0;
  let toIdx = max;
  if (filters.foundedFrom !== '') {
    const i = steps.indexOf(parseInt(filters.foundedFrom, 10));
    if (i >= 0) fromIdx = i;
  }
  if (filters.foundedTo !== '') {
    const i = steps.indexOf(parseInt(filters.foundedTo, 10));
    if (i >= 0) toIdx = i;
  }
  if (filters.founded && filters.foundedFrom === '' && filters.foundedTo === '') {
    const i = steps.indexOf(parseInt(filters.founded, 10));
    if (i >= 0) fromIdx = toIdx = i;
  }
  if (fromIdx > toIdx) [fromIdx, toIdx] = [toIdx, fromIdx];
  const fromLabel = partyFoundedDecadeLabel(steps[fromIdx]);
  const toLabel = partyFoundedDecadeLabel(steps[toIdx]);
  const pctFrom = max === 0 ? 0 : (fromIdx / max) * 100;
  const pctTo = max === 0 ? 100 : (toIdx / max) * 100;
  return `
    <div class="parties-browse-row">
      <span class="parties-browse-label" id="parties-founded-label">Party founded</span>
      <div class="parties-founded-range" style="--founded-from:${pctFrom}%; --founded-to:${pctTo}%">
        <div class="parties-founded-track" aria-hidden="true"></div>
        <label class="sr-only" for="parties-founded-from">Founded from decade</label>
        <input type="range" id="parties-founded-from" class="parties-founded-input parties-founded-input--from" min="${min}" max="${max}" step="1" value="${fromIdx}" data-founded-handle="from" aria-labelledby="parties-founded-label" />
        <label class="sr-only" for="parties-founded-to">Founded to decade</label>
        <input type="range" id="parties-founded-to" class="parties-founded-input parties-founded-input--to" min="${min}" max="${max}" step="1" value="${toIdx}" data-founded-handle="to" aria-labelledby="parties-founded-label" />
        <div class="parties-founded-readout" aria-live="polite">${fromLabel} — ${toLabel}</div>
      </div>
    </div>`;
}

function renderPartyTagsFilterHtml(rows, filters) {
  const counts = new Map();
  rows.forEach(r => {
    (r.tags || []).forEach(t => counts.set(t, (counts.get(t) || 0) + 1));
  });
  const allTags = [...counts.keys()].sort((a, b) => a.localeCompare(b, 'en-GB'));
  const q = (filters.tagQuery || '').trim().toLowerCase();
  const visible = q ? allTags.filter(t => t.toLowerCase().includes(q)) : allTags;
  const selected = new Set(filters.tags || []);
  const rowsHtml = visible.map(t => {
    const checked = selected.has(t);
    return `<label class="parties-tag-row">
      <input type="checkbox" data-browse-tag="${t.replace(/"/g, '&quot;')}" ${checked ? 'checked' : ''} />
      <span class="parties-tag-name">${t}</span>
      <span class="parties-tag-count">${counts.get(t)}</span>
    </label>`;
  }).join('');
  return `
    <div class="parties-browse-row parties-tags-filter">
      <div class="parties-tags-head">
        <span class="parties-browse-label">Tags</span>
        <span class="parties-tags-total">${allTags.length}</span>
      </div>
      <label class="sr-only" for="parties-tags-filter-q">Filter tags</label>
      <input type="search" id="parties-tags-filter-q" class="parties-tags-filter-q" value="${(filters.tagQuery || '').replace(/"/g, '&quot;')}" placeholder="Filter tags…" autocomplete="off" />
      <div class="parties-tags-meta">${visible.length} tag${visible.length === 1 ? '' : 's'}</div>
      <div class="parties-tags-list" role="group" aria-label="Party tags">${rowsHtml || '<p class="parties-browse-hint">No tags match.</p>'}</div>
    </div>`;
}

function renderPartyBrowseFiltersHtml(rows, filters) {
  const nationsPresent = new Set(rows.map(r => r.nation));
  const colourPresent = new Set(rows.map(r => r.colourFamily));
  const contestPresent = new Set(rows.flatMap(r => r.kinds));
  const foundedSteps = partyBrowseFoundedSteps(rows);

  const colourBtns = PARTY_COLOUR_FAMILIES
    .filter(f => colourPresent.has(f.id))
    .map(f => {
      const active = filters.colour === f.id;
      return `<button type="button" class="parties-colour-swatch${active ? ' active' : ''}" data-browse-group="colour" data-browse-value="${f.id}" title="${f.label}" aria-label="${f.label}" aria-pressed="${active ? 'true' : 'false'}" style="--swatch:${f.swatch}"></button>`;
    }).join('');

  const nationBtns = [
    partyBrowseFilterChip('nation', '', 'All', !filters.nation),
    ...PARTY_BROWSE_NATIONS
      .filter(n => nationsPresent.has(n.id))
      .map(n => partyBrowseFilterChip('nation', n.id, n.label, filters.nation === n.id)),
  ].join('');

  const statusBtns = [
    partyBrowseFilterChip('status', '', 'All', !filters.status),
    partyBrowseFilterChip('status', 'primary', 'Primary', filters.status === 'primary'),
    partyBrowseFilterChip('status', 'active', 'Active', filters.status === 'active'),
    partyBrowseFilterChip('status', 'historical', 'Historical', filters.status === 'historical'),
  ].join('');

  const contestBtns = [
    partyBrowseFilterChip('contest', '', 'All', !filters.contest),
    ...PARTY_BROWSE_CONTESTS
      .filter(c => contestPresent.has(c.id))
      .map(c => partyBrowseFilterChip('contest', c.id, c.label, filters.contest === c.id)),
  ].join('');

  const docsBtns = [
    partyBrowseFilterChip('docs', '', 'All', !filters.docs),
    partyBrowseFilterChip('docs', 'pdf', 'Has PDF', filters.docs === 'pdf'),
    partyBrowseFilterChip('docs', 'text', 'In catalogue', filters.docs === 'text'),
    partyBrowseFilterChip('docs', 'none', 'No documents', filters.docs === 'none'),
  ].join('');

  const rangeActive = filters.foundedFrom || filters.foundedTo || filters.founded
    || (filters.tags && filters.tags.length);
  const hasActive = Object.entries(filters).some(([k, v]) => {
    if (k === 'tagQuery') return false;
    if (k === 'tags') return Array.isArray(v) && v.length;
    if (k === 'foundedFrom' || k === 'foundedTo' || k === 'founded') return false;
    return Boolean(v);
  }) || rangeActive;

  // Treat full-span founded range as inactive for Clear
  const steps = foundedSteps;
  const from = filters.foundedFrom !== '' ? parseInt(filters.foundedFrom, 10) : steps[0];
  const to = filters.foundedTo !== '' ? parseInt(filters.foundedTo, 10) : steps[steps.length - 1];
  const foundedConstrained = steps.length && (from !== steps[0] || to !== steps[steps.length - 1] || filters.founded);
  const showClear = hasActive || foundedConstrained || (filters.tags && filters.tags.length);

  return `
    <aside class="parties-browse-sidebar" id="parties-browse-filters" aria-label="Filter parties">
      <div class="parties-browse-row">
        <span class="parties-browse-label" id="parties-colour-label">Colour family</span>
        <div class="parties-colour-strip" role="group" aria-labelledby="parties-colour-label">
          <button type="button" class="filter-btn${filters.colour ? '' : ' active'}" data-browse-group="colour" data-browse-value="" aria-pressed="${filters.colour ? 'false' : 'true'}">All</button>
          ${colourBtns}
        </div>
      </div>
      <div class="parties-browse-row">
        <span class="parties-browse-label">Nation / Europe</span>
        <div class="timeline-filter parties-browse-stack" role="group">${nationBtns}</div>
      </div>
      ${renderPartyFoundedRangeHtml(rows, filters)}
      <div class="parties-browse-row">
        <span class="parties-browse-label">Status</span>
        <div class="timeline-filter parties-browse-stack" role="group">${statusBtns}</div>
      </div>
      ${renderPartyTagsFilterHtml(rows, filters)}
      <div class="parties-browse-row">
        <span class="parties-browse-label">Contested</span>
        <p class="parties-browse-hint">Chambers with a recorded contest or documents in the archive. Territorial parties (e.g. Welsh Lib Dems) are listed separately from their federal counterpart.</p>
        <div class="timeline-filter parties-browse-stack" role="group">${contestBtns}</div>
      </div>
      <div class="parties-browse-row">
        <span class="parties-browse-label">Documents</span>
        <div class="timeline-filter parties-browse-stack" role="group">${docsBtns}</div>
      </div>
      ${showClear ? `<p class="parties-browse-clear"><button type="button" class="parties-browse-clear-btn" data-browse-clear>Clear filters</button></p>` : ''}
    </aside>`;
}

function renderPartyBrowseSearchHtml(filters) {
  const qRaw = filters.q || '';
  const q = qRaw.replace(/"/g, '&quot;');
  const hasQ = Boolean(qRaw.trim());
  const tryChips = [
    ['Reform', 'Reform'],
    ['Labour', 'Labour'],
    ['SNP', 'SNP'],
    ['Plaid', 'Plaid'],
  ].map(([value, label]) => {
    const active = qRaw.trim().toLowerCase() === value.toLowerCase();
    return `<button type="button" class="parties-browse-try-chip${active ? ' is-active' : ''}" data-browse-q="${value}" aria-pressed="${active ? 'true' : 'false'}">${label}</button>`;
  }).join('');
  return `
    <div class="parties-browse-search" id="parties-browse-search">
      <div class="parties-browse-search-meta">
        <span>Search the archive</span>
        <button type="button" class="parties-browse-search-clear" data-browse-clear-q ${hasQ ? '' : 'hidden'}>Clear</button>
      </div>
      <form class="parties-browse-search-form" id="parties-browse-search-form" role="search">
        <label class="sr-only" for="parties-browse-q">Search parties</label>
        <input type="search" id="parties-browse-q" name="q" value="${q}" placeholder="Search by party" autocomplete="off" />
        <button type="button" class="parties-browse-search-clear-icon" data-browse-clear-q aria-label="Clear search" ${hasQ ? '' : 'hidden'}>×</button>
        <button type="submit" class="parties-browse-search-submit">Search</button>
      </form>
      <div class="parties-browse-try" aria-label="Try searching">
        <span class="parties-browse-try-label">Try:</span>
        ${tryChips}
      </div>
    </div>`;
}

function setupPartyBrowse(app, rows) {
  const hub = app.querySelector('.hub-page');
  if (!hub) return;

  let filters = readPartyBrowseFilters();
  const foundedSteps = partyBrowseFoundedSteps(rows);

  const syncFoundedFromSliders = () => {
    const fromEl = hub.querySelector('#parties-founded-from');
    const toEl = hub.querySelector('#parties-founded-to');
    if (!fromEl || !toEl || !foundedSteps.length) return null;
    let fromIdx = parseInt(fromEl.value, 10);
    let toIdx = parseInt(toEl.value, 10);
    if (Number.isNaN(fromIdx)) fromIdx = 0;
    if (Number.isNaN(toIdx)) toIdx = foundedSteps.length - 1;
    if (fromIdx > toIdx) {
      // Keep the active thumb; nudge the other
      if (document.activeElement === fromEl) toIdx = fromIdx;
      else fromIdx = toIdx;
      fromEl.value = String(fromIdx);
      toEl.value = String(toIdx);
    }
    const from = foundedSteps[fromIdx];
    const to = foundedSteps[toIdx];
    const full = fromIdx === 0 && toIdx === foundedSteps.length - 1;
    filters = {
      ...filters,
      founded: '',
      foundedFrom: full ? '' : String(from),
      foundedTo: full ? '' : String(to),
    };
    return { fromIdx, toIdx, from, to };
  };

  /** Update range chrome in place — never recreate the inputs mid-drag. */
  const paintFoundedSlider = (idxs) => {
    const wrap = hub.querySelector('.parties-founded-range');
    const readout = hub.querySelector('.parties-founded-readout');
    if (!wrap || !foundedSteps.length) return;
    const max = Math.max(0, foundedSteps.length - 1);
    const fromIdx = idxs?.fromIdx ?? 0;
    const toIdx = idxs?.toIdx ?? max;
    const pctFrom = max === 0 ? 0 : (fromIdx / max) * 100;
    const pctTo = max === 0 ? 100 : (toIdx / max) * 100;
    wrap.style.setProperty('--founded-from', `${pctFrom}%`);
    wrap.style.setProperty('--founded-to', `${pctTo}%`);
    if (readout) {
      readout.textContent = `${partyFoundedDecadeLabel(foundedSteps[fromIdx])} — ${partyFoundedDecadeLabel(foundedSteps[toIdx])}`;
    }
  };

  const foundedRangeConstrained = () => {
    if (!foundedSteps.length) return false;
    const from = filters.foundedFrom !== '' ? parseInt(filters.foundedFrom, 10) : foundedSteps[0];
    const to = filters.foundedTo !== '' ? parseInt(filters.foundedTo, 10) : foundedSteps[foundedSteps.length - 1];
    return from !== foundedSteps[0] || to !== foundedSteps[foundedSteps.length - 1] || Boolean(filters.founded);
  };

  const syncSearchChrome = () => {
    const hasQ = Boolean((filters.q || '').trim());
    hub.querySelectorAll('[data-browse-clear-q]').forEach(el => {
      el.hidden = !hasQ;
    });
    const qNorm = (filters.q || '').trim().toLowerCase();
    hub.querySelectorAll('[data-browse-q]').forEach(chip => {
      const active = qNorm === (chip.getAttribute('data-browse-q') || '').toLowerCase();
      chip.classList.toggle('is-active', active);
      chip.setAttribute('aria-pressed', active ? 'true' : 'false');
    });
  };

  const syncClearButton = () => {
    const aside = hub.querySelector('#parties-browse-filters');
    if (!aside) return;
    const hasOther = Object.entries(filters).some(([k, v]) => {
      if (k === 'tagQuery' || k === 'foundedFrom' || k === 'foundedTo' || k === 'founded') return false;
      if (k === 'tags') return Array.isArray(v) && v.length;
      return Boolean(v);
    });
    const show = hasOther || foundedRangeConstrained() || (filters.tags && filters.tags.length);
    let clearEl = aside.querySelector('.parties-browse-clear');
    if (show && !clearEl) {
      clearEl = document.createElement('p');
      clearEl.className = 'parties-browse-clear';
      clearEl.innerHTML = '<button type="button" class="parties-browse-clear-btn" data-browse-clear>Clear filters</button>';
      aside.appendChild(clearEl);
    } else if (!show && clearEl) {
      clearEl.remove();
    }
    syncSearchChrome();
  };

  const renderResults = () => {
    const listEl = hub.querySelector('#parties-all-list');
    const countEl = hub.querySelector('#parties-browse-count');
    const spectrumMount = hub.querySelector('#parties-spectrum-mount');
    const matched = rows.filter(r => partyBrowseMatches(r, filters, foundedSteps));
    if (spectrumMount) {
      spectrumMount.innerHTML = renderPartySpectrumHtml(rows, filters);
    }
    if (listEl) {
      listEl.innerHTML = matched.map(partyBrowseRowHtml).join('')
        || `<p class="parties-browse-empty">No parties match these filters. <button type="button" class="parties-browse-clear-btn" data-browse-clear>Clear filters</button></p>`;
    }
    if (countEl) {
      countEl.textContent = matched.length === rows.length
        ? `${rows.length} parties`
        : `${matched.length} of ${rows.length} parties`;
    }
    syncClearButton();
    writePartyBrowseFilters(filters);
  };

  const render = ({ skipFilters = false } = {}) => {
    const filtersMount = hub.querySelector('#parties-browse-filters');
    const searchInput = hub.querySelector('#parties-browse-q');
    if (!skipFilters && filtersMount) {
      filtersMount.outerHTML = renderPartyBrowseFiltersHtml(rows, filters);
    }
    if (searchInput && searchInput.value !== (filters.q || '')) {
      searchInput.value = filters.q || '';
    }
    renderResults();
  };

  if (hub.dataset.browseBound !== '1') {
    hub.dataset.browseBound = '1';
    hub.addEventListener('click', e => {
      const clearQBtn = e.target.closest('[data-browse-clear-q]');
      if (clearQBtn) {
        filters = { ...filters, q: '' };
        render();
        hub.querySelector('#parties-browse-q')?.focus();
        return;
      }
      const clearBtn = e.target.closest('[data-browse-clear]');
      if (clearBtn) {
        filters = {
          q: '', colour: '', nation: '', founded: '', foundedFrom: '', foundedTo: '',
          status: '', contest: '', docs: '', tags: [], tagQuery: '',
        };
        render();
        return;
      }
      const tryChip = e.target.closest('[data-browse-q]');
      if (tryChip) {
        const nextQ = tryChip.getAttribute('data-browse-q') || '';
        // Second click on the active example clears the search.
        const clear = (filters.q || '').trim().toLowerCase() === nextQ.toLowerCase();
        filters = { ...filters, q: clear ? '' : nextQ };
        render();
        return;
      }
      const spectrumBar = e.target.closest('.parties-spectrum-bar');
      if (spectrumBar && spectrumBar.getAttribute('href')) {
        return;
      }
      const btn = e.target.closest('[data-browse-group]');
      if (!btn || !hub.contains(btn) || btn.classList.contains('parties-spectrum-bar')) return;
      const group = btn.getAttribute('data-browse-group');
      const value = btn.getAttribute('data-browse-value') || '';
      const next = value === '' ? '' : (filters[group] === value ? '' : value);
      filters = { ...filters, [group]: next };
      render();
    });

    hub.addEventListener('change', e => {
      const tag = e.target.getAttribute?.('data-browse-tag');
      if (tag != null) {
        const selected = new Set(filters.tags || []);
        if (e.target.checked) selected.add(tag);
        else selected.delete(tag);
        filters = { ...filters, tags: [...selected] };
        render();
      }
    });

    hub.addEventListener('submit', e => {
      const form = e.target.closest('#parties-browse-search-form');
      if (!form) return;
      e.preventDefault();
      const input = form.querySelector('#parties-browse-q');
      filters = { ...filters, q: (input?.value || '').trim() };
      render();
    });

    hub.addEventListener('input', e => {
      if (e.target.id === 'parties-browse-q') {
        const value = e.target.value.trim();
        clearTimeout(hub._browseSearchTimer);
        hub._browseSearchTimer = setTimeout(() => {
          filters = { ...filters, q: value };
          render();
        }, value ? 180 : 0);
        return;
      }
      if (e.target.id === 'parties-tags-filter-q') {
        filters = { ...filters, tagQuery: e.target.value };
        // Re-render only the tags list without full replace would be nicer;
        // full re-render is fine and keeps checkbox state from filters.tags.
        const q = e.target.value;
        clearTimeout(hub._tagFilterTimer);
        hub._tagFilterTimer = setTimeout(() => {
          filters = { ...filters, tagQuery: q };
          render();
          const again = hub.querySelector('#parties-tags-filter-q');
          if (again) {
            again.focus();
            const len = again.value.length;
            again.setSelectionRange(len, len);
          }
        }, 120);
        return;
      }
      if (e.target.matches?.('[data-founded-handle]')) {
        const idxs = syncFoundedFromSliders();
        paintFoundedSlider(idxs);
        // Keep the range inputs mounted so the pointer drag is not interrupted
        render({ skipFilters: true });
      }
    });
  }

  render();
}

function renderPartiesHub(app, allMode = false) {
  if (allMode) {
    setPageMeta({
      title: 'All Parties',
      description: 'A–Z catalogue of every political party in The British Manifesto Archive, with search and filters for colour, nation, founding decade, and contested chambers.',
      path: '/parties/all',
    });

    const rows = buildPartyBrowseRows();
    const filters = readPartyBrowseFilters();

    app.innerHTML = `
      ${renderBreadcrumb([
        { label: 'Home', href: '/' },
        { label: 'Parties', href: '/parties' },
        { label: 'All parties' },
      ])}
      <div class="hub-page parties-browse-page">
        <header class="parties-browse-hero">
          <div class="parties-browse-hero-copy">
            <span class="section-label" id="parties-browse-count">${rows.length} parties</span>
            <h1>All parties</h1>
            <div class="gold-rule"></div>
            <p>Every party currently in the archive. Filter by colour, nation, founding decade, or contested chamber — or see the <a href="/parties">nation-grouped hub</a>.</p>
          </div>
          ${renderPartyBrowseSearchHtml(filters)}
        </header>
        <div id="parties-spectrum-mount">${renderPartySpectrumHtml(rows, filters)}</div>
        <div class="parties-browse-layout">
          ${renderPartyBrowseFiltersHtml(rows, filters)}
          <div class="parties-browse-main">
            <div class="parties-all-list" id="parties-all-list" role="list"></div>
          </div>
        </div>
      </div>
    `;
    setupPartyBrowse(app, rows);
    return;
  }

  setPageMeta({
    title: 'Political Parties',
    description: 'Browse UK political parties and their historical general election manifestos in The British Manifesto Archive.',
    path: '/parties',
  });

  const nationSections = Object.entries(NAV_PARTIES).map(([nationId, nation]) => {
    const partyLinks = nation.parties.map(pid => {
      const p = PARTIES[pid];
      if (!p) return '';
      return `<a href="/party/${pid}" class="hub-party-link">
        <span class="mega-dot" style="${typeof dotStyle === 'function' ? dotStyle(p.color) : `background:${p.color}`}"></span>
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
    } else if (nationId === 'europe') {
      otherLink = `<a href="/nation/europe" class="hub-all-others-link">All alliance families →</a>
        <a href="/devolved/euro/other-parties" class="hub-all-others-link">Other EP parties →</a>`;
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
      <span class="mega-dot" style="${typeof dotStyle === 'function' ? dotStyle(p.color) : `background:${p.color}`}"></span>
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
        <p>Parties contesting UK, devolved, and European elections, organised by nation and pan-European alliance families — or browse every party in the archive as an <a href="/parties/all">A–Z list</a>.</p>
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
    description: 'What the British Manifesto Archive covers, how to use it, our editorial approach, data sources, and how to report corrections.',
    path: '/about',
  });
  app.innerHTML = `
    <div class="about-section">
      <span class="section-label">About this archive</span>
      <h1>About the British Manifesto Archive</h1>
      <div class="gold-rule"></div>
      <p>The British Manifesto Archive is a comprehensive resource for the study of British democratic politics, bringing together the manifesto documents, electoral results, and campaign records of UK general, devolved, regional, and European Parliament elections.</p>
      <p>It brings together the founding documents of British democratic politics: what parties promised, how the country voted, and how those results reshaped Parliament and the devolved institutions — in one place, free to read.</p>

      <h2>What you'll find here</h2>
      <p>Every election and party in the archive is built from the same set of materials:</p>
      <ul>
        <li><strong>Manifesto documents</strong> — original PDFs alongside readable web versions where a text edition is available.</li>
        <li><strong>Election result pages</strong> — summaries, seat charts, vote shares, the key moments of each campaign, and the documents that defined it.</li>
        <li><strong>Party pages</strong> — each party's electoral record over time and the manifestos it published at successive elections.</li>
        <li><strong>Beyond Westminster hubs</strong> — dedicated sections for the Scottish Parliament, the Senedd, the Northern Ireland Assembly, the London Mayor and Assembly, and the European Parliament.</li>
        <li><strong>Ways in</strong> — browse by year, by party, by nation, or by institution; search the catalogue for party names, election years, and manifesto titles; or switch search to <em>Full text</em> to look inside transcribed manifesto documents.</li>
      </ul>

      <h2>How the archive is organised</h2>
      <ul>
        <li><strong>Westminster</strong> — UK general elections (<a href="/elections">/elections</a>).</li>
        <li><strong>Beyond Westminster</strong> — institutions and their elections: Holyrood, Senedd, Stormont, London, European Parliament (<a href="/devolved">/devolved</a>). This is the main path into devolved content.</li>
        <li><strong>Nations</strong> — geography and party taxonomy across England, Scotland, Wales, Northern Ireland, and Europe (<a href="/nations">/nations</a>).</li>
        <li><strong>Parties</strong> — each organisation’s record over time (<a href="/parties">/parties</a>, <a href="/parties/all">A–Z</a>).</li>
      </ul>

      <h2>Coverage</h2>
      <p>The archive spans UK general elections from 1945 to the present, and extends beyond Westminster to the devolved and regional institutions: the Scottish Parliament, the Senedd, the Northern Ireland Assembly, the London Mayor and Assembly, and the UK's European Parliament elections. It covers parties across all four nations — England, Scotland, Wales, and Northern Ireland — as well as the European parties British voters have elected.</p>
      <p>Coverage is deliberately broad, and it is still growing. Some elections are more complete than others, and a few manifestos have not survived in any public form. Where a document is missing, the record notes the gap rather than hiding it.</p>

      <h2>Using the archive</h2>
      <p>Start with an election, a party, or a nation. Election pages bring together the results and every available manifesto for that contest. Party pages show how a party's electoral fortunes and published platform change from one election to the next. Manifesto pages give you both the original document and, where available, a readable text version you can search and quote. However you arrive, the cross-links will take you from a result to the parties that contested it, and from a party to the elections that shaped it.</p>

      <h2>Editorial approach</h2>
      <p>The archive's purpose is preservation, not persuasion. Documents are reproduced as neutrally as possible: parties are neither endorsed nor criticised, and the claims made inside a manifesto are the party's own, not the archive's. Summaries, seat charts, and contextual notes exist to help you navigate and compare — they are a finding aid, not a substitute for the original text. When a summary and a source document differ, the source document is authoritative.</p>

      <h2>Data sources</h2>
      <p>The archive draws on three kinds of material:</p>
      <ul>
        <li><strong>Core historical election statistics</strong> come from the House of Commons Library Research Briefing CBP-7529, <em>UK Election Statistics: 1918–2023, A Long Century of Elections</em> (August 2023), by Richard Cracknell, Elise Uberoi, and Matthew Burton.</li>
        <li><strong>Additional election and institutional data</strong> — including 2024, the devolved legislatures, London, and the European Parliament — is compiled from public electoral sources such as official results bodies and institutional election pages.</li>
        <li><strong>Manifesto documents</strong> are drawn from the parties themselves, archived publications, library collections, and public web sources.</li>
      </ul>

      <h2>Copyright</h2>
      <p>Manifestos remain the copyright of their respective political parties or publishers. They are reproduced here for educational, historical, and research purposes. If you hold rights in a document and have a query about its inclusion, please email <a href="mailto:hello@manifestos.org.uk">hello@manifestos.org.uk</a>.</p>

      <h2 id="contact-and-corrections">Contact and corrections</h2>
      <p>This is a living archive, and extra pairs of eyes make it better. Spotted an error, a broken link, or a manifesto that should be here but isn't? Email <a href="mailto:hello@manifestos.org.uk">hello@manifestos.org.uk</a> — corrections and leads on missing documents are genuinely welcome and help keep the record accurate and complete. You can also find the archive on <a href="https://bsky.app/profile/manifestos.org.uk" rel="me">Bluesky</a>, <a href="https://mastodon.social/@manifestosuk" rel="me">Mastodon</a>, <a href="https://x.com/manifestosuk" rel="me">X</a>, <a href="https://www.instagram.com/manifestosuk/" rel="me">Instagram</a>, <a href="https://www.threads.net/@manifestosuk" rel="me">Threads</a>, and <a href="https://www.youtube.com/@manifestosuk" rel="me">YouTube</a>.</p>
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
  app.innerHTML = `<div class="not-found">
    <h1>404</h1>
    <p>This page could not be found.</p>
    <nav class="not-found-links" aria-label="Suggested destinations">
      <a href="/">Home</a>
      <a href="/elections">UK general elections</a>
      <a href="/parties/all">All parties</a>
      <a href="/devolved">Beyond Westminster</a>
      <a href="/about">About</a>
      <button type="button" class="not-found-search-btn" id="not-found-search">Search the archive</button>
    </nav>
  </div>`;
  document.getElementById('not-found-search')?.addEventListener('click', () => {
    document.getElementById('search-toggle')?.click();
  });
}
