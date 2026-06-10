/* ============================================================
   Lazy election data loader — falls back to bundled ELECTIONS
   ============================================================ */

const _electionCache = new Map();

/** @returns {Promise<object|null>} */
async function loadElection(id) {
  const bundled = typeof getElection === 'function' ? getElection(id) : null;
  if (_electionCache.has(id)) return _electionCache.get(id);

  try {
    const res = await fetch(`data/elections/${id}.json`);
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
