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

// Manifesto text without a PDF scan (electionId/partyId)
const MANIFESTO_TEXT_ONLY = new Set([
  '2001/omrlp',
  '2005/omrlp',
  '2015/omrlp',
]);

function hasManifestoPdf(electionId, partyId) {
  const key = `${electionId}/${partyId}`;
  if (MANIFESTO_TEXT_ONLY.has(key)) return false;
  const pdfPath = `/manifestos/${electionId}/${partyId}/manifesto.pdf`;
  return Boolean(getPdfSize(pdfPath));
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
  await Promise.all([initManifestoArchive(), initPdfSizes()]);
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

function partyBreadcrumbItems(party) {
  const crumbs = [
    { label: 'Home', href: '/' },
    { label: 'Parties', href: '/parties' },
  ];
  const nationId = party.nation && party.nation !== 'others' ? party.nation : null;
  if (nationId && typeof getNationLabel === 'function') {
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
  hub.href = '/parties';
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
    <div class="card-year${longLabel ? ' long-label' : ''}">${e.displayYear}</div>
    <div class="card-date">${e.date}</div>
    <div class="card-winner"><div class="card-winner-dot"></div>${electionWinnerLabel(e)}</div>
    <div class="card-pm">New PM: <span>${e.pm}</span></div>
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
    <span class="hub-card-cta">View nation →</span>
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

  const pdfSize = hasPdf ? getPdfSize(pdfPath) : '';
  const pdfSizeLabel = pdfSize ? ` · ${pdfSize}` : '';
  const pdfLinkFinal = hasPdf
    ? `<a href="${pdfPath}" class="manifesto-link" target="_blank" rel="noopener">
          <span class="manifesto-link-icon">📄</span>
          <div class="manifesto-link-info"><div class="manifesto-link-title">Original Manifesto</div><div class="manifesto-link-sub">PDF scan of original document${pdfSizeLabel}</div></div>
        </a>`
    : '';

  return `<div class="manifesto-card" style="--party-color:${partyBar};--party-dim:${accent.border};--party-surface:${accent.surface};--party-ghost:${ghostColour};--party-kicker:${accent.kicker}">
      <a href="${thumbHref}" class="manifesto-thumb"${thumbTarget} aria-label="${thumbLabel}">
        <img src="${coverPath}" alt="${displayName} ${election.displayYear} manifesto cover"
          class="img-lazy" loading="lazy" decoding="async"
          onerror="if(this.dataset.fb){this.style.display='none';this.nextElementSibling.style.display='flex';}else{this.dataset.fb=1;this.src='${coverFallback}';}">
        <div class="manifesto-thumb-placeholder" style="display:none">
          <div class="manifesto-placeholder-topbar"></div>
          <div class="manifesto-placeholder-ghost" aria-hidden="true">${ghostYear}</div>
          <span class="manifesto-placeholder-label">Scan not yet archived</span>
        </div>
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
  const resultRows = election.results
    .filter(r => r.seats > 0 || r.votes > 0)
    .sort((a, b) => b.seats - a.seats)
    .map(r => {
      const isWinner = r.party === election.winner;
      const niOnly   = r.votes === 0 && ['uup','vanguard','dup','sdlp','sinnfein','alliance','gpni','pup','tuv'].includes(r.party);
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
              <thead><tr><th scope="col">Party</th><th scope="col">Seats (of ${election.totalSeats})</th><th scope="col">Votes</th><th scope="col">Vote %</th></tr></thead>
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

// ── CO-OPERATIVE PARTY CUSTOM PAGE ───────────────────────────
async function renderCooperativePartyPage(app, party) {
  const color = party.color;
  const theme = typeof getCurrentTheme === 'function' ? getCurrentTheme() : 'dark';
  const kickerCol = typeof partyTextColour === 'function' ? partyTextColour('cooperative', null, theme) : color;
  const barCol = typeof barColour === 'function' ? barColour(color, theme) : color;
  const coopChambers = ['22 Westminster', '7 Holyrood', '7 Senedd'];
  setPageMeta({
    title: party.shortName,
    description: buildPartyMetaDescription(party, coopChambers),
    path: '/party/cooperative',
  });
  const partyLede = partyLedeText(party.description);

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

  const contestedLabel = '22 Westminster · 7 Holyrood · 7 Senedd';

  app.innerHTML = `
    ${renderBreadcrumb(partyBreadcrumbItems(party))}
    <section class="party-hero" style="--party-color:${color};--party-kicker:${kickerCol}">
      <div class="party-hero-bg"></div>
      <div class="party-hero-inner">
        <div>
          <div class="party-color-bar" style="background:${barCol}"></div>
          <h1 class="party-hero-title">${party.name}</h1>
          ${partyLede ? `<p class="party-lede">${partyLede}</p>` : ''}
          <dl class="party-hero-meta">
            <div class="party-meta-item"><dt>Founded</dt><dd>${party.founded || '—'}</dd></div>
            <div class="party-meta-item"><dt>Spectrum</dt><dd>${party.spectrum}</dd></div>
            <div class="party-meta-item"><dt>Elections contested</dt><dd>${contestedLabel}</dd></div>
          </dl>
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

      <div class="party-elections-section">
        <span class="section-label">Electoral Record</span>
        <h2>Westminster Joint Representatives</h2>
        <div class="gold-rule" style="background:${barCol}"></div>
        <div class="party-results-list">${westminsterRows}</div>
      </div>

      <div class="party-manifestos-section">
        <span class="section-label">Documents</span>
        <h2>Westminster Manifestos</h2>
        <div class="gold-rule" style="background:${barCol}"></div>
        ${manifestoItems ? `<div class="manifesto-grid">${manifestoItems}</div>` : '<p style="color:var(--text-muted)">No Westminster manifestos on record.</p>'}
      </div>

      <div class="party-elections-section">
        <span class="section-label">Holyrood</span>
        <h2>Scottish Parliament Joint Representatives</h2>
        <div class="gold-rule" style="background:${barCol}"></div>
        <div class="party-results-list">${holyroodRows}</div>
      </div>

      <div class="party-manifestos-section">
        <span class="section-label">Holyrood</span>
        <h2>Scottish Parliament Manifestos</h2>
        <div class="gold-rule" style="background:${barCol}"></div>
        ${holyroodItems ? `<div class="manifesto-grid">${holyroodItems}</div>` : '<p style="color:var(--text-muted)">No Scottish Parliament manifestos on record.</p>'}
      </div>

      <div class="party-elections-section">
        <span class="section-label">Senedd Cymru</span>
        <h2>Welsh Parliament Joint Representatives</h2>
        <div class="gold-rule" style="background:${barCol}"></div>
        <div class="party-results-list">${seneddRows}</div>
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
}

// ── PARTY PAGE ────────────────────────────────────────────────
async function renderParty(app, id) {
  const partyId = resolvePartyId(id);
  const party = PARTIES[partyId];
  if (!party) { renderNotFound(app); return; }
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
      <div class="per-bar-wrap"><div class="per-bar"><div class="per-bar-fill" style="width:${barW}%;background:${typeof barColour === 'function' ? barColour(color) : color}"></div></div><div class="per-pct">${r.percentage > 0 ? r.percentage.toFixed(1) + '% vote' : '—'}</div></div>
    </a>`;
  }).join('');

  const manifestoElections = partyElections.filter(({ election: e }) =>
    hasManifestoContent(e.id, id)
  );
  const manifestoItems = manifestoElections.slice().reverse().map(({ election: e, result: r }) =>
    buildManifestoCard(id, e, { result: r, showYearAsTitle: true })
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

  const contestedParts = [];
  if (!isAllianceParty && partyElections.length) contestedParts.push(`${partyElections.length} Westminster`);
  if (!isAllianceParty && holyroodElections.length) contestedParts.push(`${holyroodElections.length} Holyrood`);
  if (!isAllianceParty && seneddElections.length) contestedParts.push(`${seneddElections.length} Senedd`);
  if (!isAllianceParty && niElections.length) contestedParts.push(`${niElections.length} Stormont`);
  if (euroElections.length) contestedParts.push(`${euroElections.length} European Parliament`);
  const contestedLabel = contestedParts.join(' · ') || '0';
  const partyLede = partyLedeText(party.description);

  setPageMeta({
    title: party.shortName,
    description: buildPartyMetaDescription(party, contestedParts),
    path: `/party/${partyId}`,
  });

  app.innerHTML = `
    ${renderBreadcrumb(partyBreadcrumbItems(party))}
    <section class="party-hero" style="--party-color:${color};--party-kicker:${kickerCol}">
      <div class="party-hero-bg"></div>
      <div class="party-hero-inner">
        <div>
          <div class="party-color-bar" style="background:${barCol}"></div>
          <h1 class="party-hero-title">${party.name}</h1>
          ${partyLede ? `<p class="party-lede">${partyLede}</p>` : ''}
          <dl class="party-hero-meta">
            <div class="party-meta-item"><dt>Founded</dt><dd>${party.founded || '—'}</dd></div>
            <div class="party-meta-item"><dt>Spectrum</dt><dd>${party.spectrum}</dd></div>
            <div class="party-meta-item"><dt>Elections contested</dt><dd>${contestedLabel}</dd></div>
          </dl>
        </div>
        ${electionsWon > 0 ? `<div class="party-elections-won-badge"><div class="elections-won-num" style="color:${kickerCol}">${electionsWon}</div><div class="elections-won-label">Election${electionsWon !== 1 ? 's' : ''} won</div></div>` : ''}
      </div>
    </section>

    <div class="party-body">
      <div class="party-description">${party.description}</div>
      ${!isAllianceParty ? `<div class="party-elections-section">
        <span class="section-label">Electoral Record</span>
        <h2>Westminster Results</h2>
        <div class="gold-rule" style="background:${barCol}"></div>
        ${electionRows ? `<div class="party-results-list">${electionRows}</div>` : '<p style="color:var(--text-muted)">No Westminster election data available.</p>'}
      </div>
      <div class="party-manifestos-section">
        <span class="section-label">Documents</span>
        <h2>Westminster Manifestos</h2>
        <div class="gold-rule" style="background:${barCol}"></div>
        ${manifestoItems ? `<div class="manifesto-grid">${manifestoItems}</div>` : '<p style="color:var(--text-muted)">No Westminster manifestos on record.</p>'}
      </div>` : ''}
      ${!isAllianceParty && holyroodElectionRows ? `<div class="party-elections-section">
        <span class="section-label">Holyrood</span>
        <h2>Scottish Parliament Results</h2>
        <div class="gold-rule" style="background:${barCol}"></div>
        <div class="party-results-list">${holyroodElectionRows}</div>
      </div>` : ''}
      ${!isAllianceParty && holyroodItems ? `<div class="party-manifestos-section">
        <span class="section-label">Holyrood</span>
        <h2>Scottish Parliament Manifestos</h2>
        <div class="gold-rule" style="background:${barCol}"></div>
        <div class="manifesto-grid">${holyroodItems}</div>
      </div>` : ''}
      ${!isAllianceParty && seneddElectionRows ? `<div class="party-elections-section">
        <span class="section-label">Senedd Cymru</span>
        <h2>Welsh Parliament Results</h2>
        <div class="gold-rule" style="background:${barCol}"></div>
        <div class="party-results-list">${seneddElectionRows}</div>
      </div>` : ''}
      ${!isAllianceParty && seneddItems ? `<div class="party-manifestos-section">
        <span class="section-label">Senedd Cymru</span>
        <h2>Welsh Parliament Manifestos</h2>
        <div class="gold-rule" style="background:${barCol}"></div>
        <div class="manifesto-grid">${seneddItems}</div>
      </div>` : ''}
      ${!isAllianceParty && niElectionRows ? `<div class="party-elections-section">
        <span class="section-label">Stormont</span>
        <h2>Northern Ireland Assembly Results</h2>
        <div class="gold-rule" style="background:${barCol}"></div>
        <div class="party-results-list">${niElectionRows}</div>
      </div>` : ''}
      ${!isAllianceParty && niItems ? `<div class="party-manifestos-section">
        <span class="section-label">Stormont</span>
        <h2>Northern Ireland Assembly Manifestos</h2>
        <div class="gold-rule" style="background:${barCol}"></div>
        <div class="manifesto-grid">${niItems}</div>
      </div>` : ''}
      ${euroElectionRows ? `<div class="party-elections-section">
        <span class="section-label">European Parliament</span>
        <h2>European Parliament Results</h2>
        <div class="gold-rule" style="background:${barCol}"></div>
        ${isAllianceParty ? '<p style="color:var(--text-muted);font-size:0.85rem;margin-bottom:1rem">Seats held by UK parties in this EP political group at the constitutive session after each election.</p>' : ''}
        <div class="party-results-list">${euroElectionRows}</div>
      </div>` : ''}
      ${euroItems ? `<div class="party-manifestos-section">
        <span class="section-label">European Parliament</span>
        <h2>European Parliament Manifestos</h2>
        <div class="gold-rule" style="background:${barCol}"></div>
        <div class="manifesto-grid">${euroItems}</div>
      </div>` : ''}
    </div>
  `;
}

// ── NATION PAGE ───────────────────────────────────────────────
function westminsterYearCell(yearLabel) {
  const election = ELECTIONS.find(e => e.displayYear === yearLabel);
  if (!election || election.year < 1945) {
    return `<td style="font-family:var(--font-display);color:var(--cream)">${yearLabel}</td>`;
  }
  return `<td style="font-family:var(--font-display);color:var(--cream)"><a href="/election/${election.id}" class="results-table-link">${yearLabel}</a></td>`;
}

function nationTablePartyHeading(partyId, label, color) {
  const style = color ? ` style="color:${color}"` : '';
  if (!partyId || !PARTIES?.[partyId]) {
    return `<th scope="col"${style}>${label}</th>`;
  }
  return `<th scope="col"${style}><a href="/party/${partyId}" class="results-table-link">${label}</a></th>`;
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
    const rows = nation.westminsterResults.map(r => `<tr>
      ${westminsterYearCell(r.year)}
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
        <thead><tr><th scope="col">Year</th>${nationTablePartyHeading('scottishcon', 'Con', '#0087DC')}${nationTablePartyHeading('scottishlab', 'Lab', '#E4003B')}${nationTablePartyHeading('scottishlibdem', 'LD', '#FAA61A')}${nationTablePartyHeading('snp', 'SNP', '#FDF38E')}<th scope="col">Other</th><th scope="col">Total</th></tr></thead>
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
        <thead><tr><th scope="col">Year</th><th scope="col" style="color:#E4003B">Labour</th><th scope="col" style="color:#008672">Plaid</th><th scope="col" style="color:#0087DC">Cons.</th><th scope="col" style="color:#FAA61A">Lib Dem</th><th scope="col" style="color:#70147A">UKIP</th><th scope="col" style="color:#12B6CF">Reform</th></tr></thead>
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
        <thead><tr><th scope="col">Year</th><th scope="col" style="color:#FDF38E">SNP</th><th scope="col" style="color:#E4003B">Labour</th><th scope="col" style="color:#0087DC">Cons.</th><th scope="col" style="color:#FAA61A">Lib Dem</th><th scope="col" style="color:#00B140">Greens</th><th scope="col" style="color:#12B6CF">Reform</th></tr></thead>
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
        <thead><tr><th scope="col">Year</th><th scope="col" style="color:#D46A4C">DUP</th><th scope="col" style="color:#326760">Sinn Féin</th><th scope="col" style="color:#48A5EE">UUP</th><th scope="col" style="color:#2AA82C">SDLP</th><th scope="col" style="color:#F6CB2F">Alliance</th></tr></thead>
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
        <div>
          <div class="nation-parties-card">
            <div class="section-label" style="margin-bottom:1rem">${id === 'europe' ? 'Alliance families' : `Parties in ${nation.name}`}</div>
            ${partyLinks}
            ${id === 'england' ? `<a href="/others" class="nation-party-link" style="--party-color:var(--gold)"><span class="nation-party-dot" style="background:var(--gold)"></span><span>Other parties →</span></a>` : ''}
            ${id === 'scotland' ? `<a href="/devolved/holyrood/other-parties" class="holyrood-other-link">Other Scottish parties →</a>` : ''}
            ${id === 'wales' ? `<a href="/devolved/senedd/other-parties" class="holyrood-other-link">Other Welsh parties →</a>` : ''}
            ${id === 'northern-ireland' ? `<a href="/devolved/stormont/other-parties" class="holyrood-other-link">Other Northern Irish parties →</a>` : ''}
            ${id === 'europe' ? `<a href="/devolved/euro/other-parties" class="holyrood-other-link">Other EP parties →</a>` : ''}
          </div>
          ${id === 'europe' ? `<a href="/devolved/euro" class="cross-archive-link" style="margin-top:1rem;display:flex">European Parliament archive →</a>` : ''}
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
  wrap.querySelectorAll('h2').forEach((h2, idx) => {
    if (!h2.id) h2.id = `section-${idx + 1}`;
    const label = h2.textContent.trim();
    if (!h2.querySelector('.manifesto-section-link')) {
      h2.innerHTML = `<a href="#${h2.id}" class="manifesto-section-link">${label}</a>`;
    }
  });
  const firstP = wrap.querySelector('p');
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

function setupManifestoReader(contentEl, paperEl, accent) {
  const headings = [...contentEl.querySelectorAll('h2[id]')];
  const tocHtml = buildManifestoTocLinks(headings);
  const tocList = document.getElementById('manifesto-toc-list');
  const tocMobileList = document.getElementById('manifesto-toc-mobile-list');
  const tocMeta = document.getElementById('manifesto-toc-meta');
  const minutes = estimateReadingMinutes(contentEl.textContent || '');

  const tocAside = document.querySelector('.manifesto-toc');
  const tocMobilePanel = document.querySelector('.manifesto-toc-mobile');
  const hasToc = headings.length > 0;
  if (tocAside) tocAside.hidden = !hasToc;
  if (tocMobilePanel) tocMobilePanel.hidden = !hasToc;

  if (tocList) tocList.innerHTML = tocHtml;
  if (tocMobileList) tocMobileList.innerHTML = tocHtml;
  if (tocMeta) {
    tocMeta.innerHTML = `Reading time ~${minutes} min<br>Section <span id="manifesto-section-current">1</span> of ${Math.max(headings.length, 1)}`;
  }

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
  setActive(0);
}

function renderManifesto(app, electionId, partyId) {
  const election = getElection(electionId);
  const party    = PARTIES[partyId];
  if (!election || !party) { renderNotFound(app); return; }
  const displayName = (election.manifestoPartyLabels && election.manifestoPartyLabels[partyId])
    || getPartyName(partyId, election.year);
  const theme = typeof getCurrentTheme === 'function' ? getCurrentTheme() : 'dark';
  const accent = typeof partyAccentDerivedForYear === 'function'
    ? partyAccentDerivedForYear(partyId, election.year, theme)
    : { raw: party.color, surface: party.color, kicker: party.color };
  const pdfPath = `/manifestos/${electionId}/${partyId}/manifesto.pdf`;
  const hasPdf = hasManifestoPdf(electionId, partyId);
  const pdfSize = hasPdf ? getPdfSize(pdfPath) : '';
  const pdfSizeLabel = pdfSize ? ` · ${pdfSize}` : '';
  const coverPath = `/manifestos/${electionId}/${partyId}/cover.png?v=${ASSETS_VERSION}`;
  const coverFallback = `/manifestos/${electionId}/${partyId}/cover.jpg?v=${ASSETS_VERSION}`;
  const coverThumbOpen = hasPdf
    ? `<a href="${pdfPath}" class="manifesto-viewer-cover-thumb" target="_blank" rel="noopener" aria-label="Open ${displayName} ${election.displayYear} manifesto PDF">`
    : `<div class="manifesto-viewer-cover-thumb">`;
  const coverThumbClose = hasPdf ? '</a>' : '</div>';
  const pdfDownloadLink = hasPdf
    ? `<a href="${pdfPath}" class="manifesto-link" target="_blank" rel="noopener">
          <span class="manifesto-link-icon" aria-hidden="true">📄</span>
          <div class="manifesto-link-info"><div class="manifesto-link-title">PDF${pdfSizeLabel}</div></div>
        </a>`
    : '';
  const coverPanel = `
            <div class="manifesto-viewer-cover" id="manifesto-viewer-cover">
              ${coverThumbOpen}
                <img src="${coverPath}" alt="${displayName} ${election.displayYear} manifesto cover"
                  width="148" height="210" decoding="async"
                  onerror="if(!this.dataset.fb){this.dataset.fb='1';this.src='${coverFallback}';}else{const wrap=this.closest('.manifesto-viewer-cover');if(wrap){wrap.classList.add('is-cover-missing');if(!wrap.querySelector('.manifesto-link'))wrap.hidden=true;}}">
              ${coverThumbClose}
              ${pdfDownloadLink}
            </div>`;
  const barSurface = typeof barColour === 'function'
    ? barColour(getPartyColor(partyId, election.year), theme)
    : accent.surface;

  setPageMeta({
    title: displayName,
    description: `Read and search the full text of the ${displayName} manifesto from the ${election.displayYear} UK general election.`,
    path: `/manifesto/${electionId}/${partyId}`,
  });

  app.innerHTML = `
    <div class="manifesto-viewer-page">
      <header class="manifesto-viewer-header">
        <div class="manifesto-viewer-header-inner">
          <nav class="manifesto-viewer-breadcrumb" aria-label="Breadcrumb">
            <a href="/">Home</a><span aria-hidden="true">›</span>
            <a href="/election/${election.id}">${election.displayYear} Election</a><span aria-hidden="true">›</span>
            <a href="/party/${partyId}">${displayName}</a><span aria-hidden="true">›</span>
            <span class="bc-current">Manifesto</span>
          </nav>
          <div class="manifesto-viewer-title-row">
            <div>
              <div class="manifesto-viewer-kicker">
                <div class="manifesto-viewer-kicker-rule" style="background:${barSurface}"></div>
                <div class="manifesto-viewer-kicker-text" style="color:${accent.kicker}">GENERAL ELECTION ${election.displayYear}</div>
              </div>
              <h1 class="manifesto-viewer-title">${displayName} Manifesto ${election.displayYear}</h1>
              <div class="manifesto-viewer-meta-row" id="manifesto-header-meta">
                <span>${election.date}</span>
              </div>
            </div>
            ${coverPanel}
          </div>
        </div>
      </header>
      <div class="manifesto-viewer-body">
        <aside class="manifesto-toc" aria-label="Table of contents">
          <div class="manifesto-toc-label">CONTENTS</div>
          <nav class="manifesto-toc-list" id="manifesto-toc-list"></nav>
          <div class="manifesto-toc-divider"></div>
          <div class="manifesto-toc-meta" id="manifesto-toc-meta"></div>
        </aside>
        <details class="manifesto-toc-mobile">
          <summary>Contents</summary>
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

  fetchTyped(`/manifestos/${electionId}/${partyId}/manifesto.md`, 'markdown')
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
      contentEl.innerHTML = manifestoLoadErrorHtml(pdfPath, hasPdf);
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
    title: 'Beyond Westminster',
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
      { label: 'Beyond Westminster' },
    ])}
    <div class="hub-page">
      <header class="hub-page-header">
        <span class="section-label">United Kingdom — Devolved Government</span>
        <h1>Beyond Westminster</h1>
        <div class="gold-rule"></div>
        <p>Legislatures with devolved powers across Scotland, Wales, Northern Ireland, and Greater London.</p>
      </header>
      <div class="hub-devolved-grid">${cards}</div>
    </div>
  `;
}

function renderNationsHub(app) {
  setPageMeta({
    title: 'The Four Nations & Europe',
    description: 'Browse England, Wales, Scotland, Northern Ireland, and European political families — Westminster results and devolved government.',
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
        <p>England, Wales, Scotland, and Northern Ireland — plus pan-European political families that contested UK European elections.</p>
      </header>
      <div class="hub-nations-grid">${cards}</div>
    </div>
  `;
}

function renderPartiesHub(app) {
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
    } else     if (nationId === 'northern-ireland') {
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
        <p>Parties contesting UK, devolved, and European elections, organised by nation and pan-European alliance families.</p>
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
      <p>It brings together the founding documents of British democratic politics: what parties promised, how the country voted, and how those results reshaped Parliament and the devolved institutions — in one place, free to read and search.</p>

      <h2>What you'll find here</h2>
      <p>Every election and party in the archive is built from the same set of materials:</p>
      <ul>
        <li><strong>Manifesto documents</strong> — original PDFs alongside readable web versions where a text edition is available.</li>
        <li><strong>Election result pages</strong> — summaries, seat charts, vote shares, the key moments of each campaign, and the documents that defined it.</li>
        <li><strong>Party pages</strong> — each party's electoral record over time and the manifestos it published at successive elections.</li>
        <li><strong>Beyond Westminster hubs</strong> — dedicated sections for the Scottish Parliament, the Senedd, the Northern Ireland Assembly, the London Mayor and Assembly, and the European Parliament.</li>
        <li><strong>Ways in</strong> — browse by year, by party, by nation, or by institution, or search the whole archive from anywhere on the site.</li>
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

      <h2>Contact and corrections</h2>
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
  app.innerHTML = `<div class="not-found"><h1>404</h1><p>This page could not be found.</p><a href="/">Return to home</a></div>`;
}
