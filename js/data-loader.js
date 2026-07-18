/* ============================================================
   Lazy election data loader — falls back to bundled ELECTIONS
   ============================================================ */

const ASSETS_VERSION = '2026071811';

const _electionCache = new Map();

/** Fetch JSON or markdown; reject SPA HTML fallbacks (Cloudflare 200 + text/html). */
async function fetchTyped(url, expected) {
  const r = await fetch(url, { cache: 'no-cache' });
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
    const res = await fetch(`/data/elections/${id}.json`);
    if (res.ok) {
      const data = await res.json();
      _electionCache.set(id, data);
      return data;
    }
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
