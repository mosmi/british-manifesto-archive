/* ============================================================
   Lazy election data loader — falls back to bundled ELECTIONS
   ============================================================ */

const ASSETS_VERSION = '2026062802';

const _electionCache = new Map();

/** Fetch JSON or markdown; reject SPA HTML fallbacks (Cloudflare 200 + text/html). */
async function fetchTyped(url, expected) {
  const r = await fetch(url, { cache: 'no-cache' });
  const ct = (r.headers.get('content-type') || '').toLowerCase();
  const okType = expected === 'json'
    ? ct.includes('json')
    : ct.includes('markdown') || ct.includes('text/plain');
  if (!r.ok || !okType) {
    throw new Error(`Unexpected response for ${url}: ${r.status} ${ct}`);
  }
  return expected === 'json' ? r.json() : r.text();
}

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
  } catch (_) { /* offline or missing file */ }

  if (bundled) _electionCache.set(id, bundled);
  return bundled;
}

/** Warm the cache from the bundled array (instant nav). */
function primeElectionCache() {
  if (typeof ELECTIONS === 'undefined') return;
  ELECTIONS.forEach(e => _electionCache.set(e.id, e));
}

primeElectionCache();
