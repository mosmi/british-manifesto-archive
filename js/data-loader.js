/* ============================================================
   Lazy election data loader — falls back to bundled ELECTIONS
   ============================================================ */

const ASSETS_VERSION = '2026090628';

const _electionCache = new Map();
const _fetchCache = new Map();
const _scriptPromises = new Map();

const COVER_CARD_W = 356;
const COVER_CARD_H = 504;

const CHAMBER_SCRIPTS = {
  london: ['/js/london.js'],
  holyrood: ['/js/holyrood.js'],
  senedd: ['/js/senedd.js'],
  stormont: ['/js/ni.js'],
  euro: ['/js/euro-map.js', '/js/euro.js'],
};

function withAssetsVersion(path) {
  if (!path) return '';
  const clean = String(path).split('?')[0];
  return ASSETS_VERSION ? `${clean}?v=${ASSETS_VERSION}` : clean;
}

function escapeAttr(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;');
}

function manifestoKeyFromAssetPath(path) {
  const clean = String(path || '').split('?')[0];
  const m = clean.match(/^\/manifestos\/(.+)\/[^/]+$/);
  return m ? m[1] : null;
}

function coverThumbUrls(path) {
  const clean = String(path || '').split('?')[0];
  const m = clean.match(/^(.*)\.(png|jpe?g)$/i);
  if (!m) return null;
  return {
    w356: withAssetsVersion(`${m[1]}-356.webp`),
    w712: withAssetsVersion(`${m[1]}-712.webp`),
    raster: withAssetsVersion(clean),
    jpg: withAssetsVersion(clean.replace(/\.png$/i, '.jpg')),
  };
}

function coverImgError(img, fallbackUrl) {
  if (!img) return;
  const fb = fallbackUrl ? String(fallbackUrl).split('?')[0] : '';
  const current = (img.getAttribute('src') || '').split('?')[0];
  if (!img.dataset.fb && fb && current !== fb) {
    img.dataset.fb = '1';
    img.src = fallbackUrl;
    return;
  }
  img.style.display = 'none';
  const ph = img.closest('picture')?.nextElementSibling || img.nextElementSibling;
  if (ph) ph.style.display = 'flex';
}
window.coverImgError = coverImgError;

/**
 * A4 <picture> for manifesto cards. Caller must only invoke when a cover exists.
 * @param {{ src: string, alt: string, className?: string, width?: number, height?: number, fallbackSrc?: string, sizes?: string }} opts
 */
function coverPictureHtml(opts) {
  const src = opts && opts.src;
  if (!src) return '';
  const alt = escapeAttr(opts.alt || '');
  const className = opts.className || 'img-lazy';
  const width = opts.width || COVER_CARD_W;
  const height = opts.height || COVER_CARD_H;
  const sizes = opts.sizes || '(max-width: 640px) 45vw, 356px';
  const loading = opts.loading || 'lazy';
  const pri = opts.fetchpriority ? ` fetchpriority="${escapeAttr(opts.fetchpriority)}"` : '';
  const urls = coverThumbUrls(src);
  if (!urls) {
    return `<img src="${withAssetsVersion(src)}" alt="${alt}" width="${width}" height="${height}" class="${className}" loading="${loading}" decoding="async"${pri}>`;
  }
  const fb = opts.fallbackSrc ? withAssetsVersion(opts.fallbackSrc) : (urls.jpg !== urls.raster ? urls.jpg : '');
  const onerror = ` onerror="coverImgError(this, '${escapeAttr(fb)}')"`;
  return `<picture>
    <source type="image/webp" srcset="${urls.w356} 356w, ${urls.w712} 712w" sizes="${sizes}">
    <img src="${urls.raster}" alt="${alt}" width="${width}" height="${height}" class="${className}" loading="${loading}" decoding="async"${pri}${onerror}>
  </picture>`;
}

function loadScript(src) {
  const url = withAssetsVersion(src);
  if (_scriptPromises.has(url)) return _scriptPromises.get(url);
  const path = String(src).split('?')[0];
  if (path.endsWith('marked.min.js') && typeof marked !== 'undefined') {
    const done = Promise.resolve();
    _scriptPromises.set(url, done);
    return done;
  }
  const existing = [...document.scripts].find(s => {
    const sPath = (s.getAttribute('src') || '').split('?')[0];
    return sPath === path || sPath.endsWith(path);
  });
  if (existing) {
    const done = existing.dataset.loaded === '1' || existing.readyState === 'complete'
      ? Promise.resolve()
      : new Promise((resolve, reject) => {
          existing.addEventListener('load', () => resolve(), { once: true });
          existing.addEventListener('error', () => reject(new Error(url)), { once: true });
        });
    _scriptPromises.set(url, done);
    return done;
  }
  const p = new Promise((resolve, reject) => {
    const el = document.createElement('script');
    el.src = url;
    el.async = false;
    el.onload = () => {
      el.dataset.loaded = '1';
      resolve();
    };
    el.onerror = () => reject(new Error(`Failed to load ${url}`));
    document.head.appendChild(el);
  });
  _scriptPromises.set(url, p);
  return p;
}

async function ensureChamberScripts(chamber) {
  const list = CHAMBER_SCRIPTS[chamber];
  if (!list) return;
  for (const src of list) await loadScript(src);
}

function prefetchChamberScripts() {
  Object.keys(CHAMBER_SCRIPTS).forEach(id => {
    ensureChamberScripts(id).catch(() => {});
  });
}

function chamberForPath(path) {
  if (path === '/election/london' || path.startsWith('/election/london/')) return 'london';
  if (path === '/election/holyrood' || path.startsWith('/election/holyrood/')) return 'holyrood';
  if (path === '/election/senedd' || path.startsWith('/election/senedd/')) return 'senedd';
  if (path === '/election/stormont' || path.startsWith('/election/stormont/')) return 'stormont';
  if (path === '/election/euro' || path.startsWith('/election/euro/')) return 'euro';
  return null;
}

/** Party pages (and Co-op) read Holyrood/Senedd/NI/London/Euro history helpers. */
function needsAllChamberScripts(path) {
  if (!path.startsWith('/party/')) return false;
  const slug = path.slice('/party/'.length);
  if (!slug || (typeof PARTY_HUB_SLUGS !== 'undefined' && PARTY_HUB_SLUGS.includes(slug))) return false;
  return true;
}

/** Fetch JSON or markdown; reject SPA HTML fallbacks (Cloudflare 200 + text/html). One in-flight/cached promise per URL. */
async function fetchTyped(url, expected) {
  const resolved = String(url).includes('?v=') ? url : withAssetsVersion(url);
  const key = `${expected}\0${resolved}`;
  if (_fetchCache.has(key)) return _fetchCache.get(key);
  const pending = (async () => {
    const r = await fetch(resolved, { cache: 'no-cache' });
    const ct = (r.headers.get('content-type') || '').toLowerCase();
    const path = url.split('?')[0].toLowerCase();
    const okType = expected === 'json'
      ? ct.includes('json')
      : ct.includes('markdown') || ct.includes('text/plain')
        || (ct.includes('octet-stream') && path.endsWith('.md'));
    if (!r.ok || !okType) {
      throw new Error(`Unexpected response for ${url}: ${r.status} ${ct}`);
    }
    return expected === 'json' ? r.json() : r.text();
  })().catch(err => {
    _fetchCache.delete(key);
    throw err;
  });
  _fetchCache.set(key, pending);
  return pending;
}

/**
 * Visible error state for failed client-side data fetches.
 * @param {HTMLElement} container
 * @param {{ message?: string, onRetry?: () => void }} [opts]
 */
function renderDataError(container, opts = {}) {
  if (!container) return;
  const message = opts.message
    || 'This data failed to load. Check your connection and try again.';
  container.innerHTML = `<div class="data-error" role="alert">
    <p class="data-error-kicker">Couldn’t load data</p>
    <p class="data-error-text">${message}</p>
    ${opts.onRetry ? '<button type="button" class="data-error-retry">Try again</button>' : ''}
  </div>`;
  const btn = container.querySelector('.data-error-retry');
  if (btn && typeof opts.onRetry === 'function') {
    btn.addEventListener('click', () => opts.onRetry());
  }
}
window.renderDataError = renderDataError;

/** @returns {Promise<object|null>} */
async function loadElection(id) {
  const bundled = typeof getElection === 'function' ? getElection(id) : null;
  if (_electionCache.has(id)) return _electionCache.get(id);

  try {
    const data = await fetchTyped(`/data/elections/${id}.json`, 'json');
    _electionCache.set(id, data);
    return data;
  } catch (_) { /* offline or missing file — fall back to bundled */ }

  if (bundled) _electionCache.set(id, bundled);
  return bundled;
}

/** Warm the cache from the bundled array (instant nav). */
function primeElectionCache() {
  if (typeof ELECTIONS === 'undefined') return;
  ELECTIONS.forEach(e => _electionCache.set(e.id, e));
}

primeElectionCache();
