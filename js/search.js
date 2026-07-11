/* ============================================================
   Client search — lightweight index over bundled data.
   Token AND matching; indexes parties, elections, nations,
   manifesto documents, and devolved election portals.
   ============================================================ */

const SEARCH_MIN_LEN = 2;

function buildSearchIndex() {
  const items = [];

  if (typeof PARTIES !== 'undefined') {
    Object.values(PARTIES).forEach(p => {
      if (p.id === 'others') return;
      items.push({
        type: 'party',
        id: p.id,
        title: p.shortName,
        subtitle: p.spectrum,
        body: `${p.name} ${p.description || ''} manifesto`,
        href: `/party/${p.id}`,
        color: p.color,
      });
    });
  }

  if (typeof ELECTIONS !== 'undefined') {
    ELECTIONS.forEach(e => {
      const winner = PARTIES?.[e.winner];
      items.push({
        type: 'election',
        id: e.id,
        title: `${e.displayYear} General Election`,
        subtitle: winner ? `${winner.shortName} victory · ${e.pm}` : e.pm,
        body: `${e.summary || ''} ${(e.highlights || []).join(' ')} manifesto`,
        href: `/election/${e.id}`,
        color: winner?.color || '#c9a84c',
      });
    });
  }

  if (typeof NATIONS !== 'undefined') {
    Object.values(NATIONS).forEach(n => {
      items.push({
        type: 'nation',
        id: n.id,
        title: n.name,
        subtitle: `${n.constituencies} Westminster constituencies`,
        body: n.description || '',
        href: `/nation/${n.id}`,
        color: '#c9a84c',
      });
    });
  }

  if (typeof DEVOLVED_PORTALS !== 'undefined') {
    Object.values(DEVOLVED_PORTALS).forEach(portal => {
      items.push({
        type: 'portal',
        id: `portal-${portal.id}`,
        title: portal.label,
        subtitle: portal.subtitle || 'Beyond Westminster',
        body: `${portal.description || ''} ${portal.id} devolved election manifestos`,
        href: `/devolved/${portal.id}`,
        color: '#c9a84c',
      });
    });
  }

  return items;
}

let _searchItems = null;
let _searchLastToggle = null;
let _searchExtrasLoaded = false;

function getSearchItems() {
  if (!_searchItems) _searchItems = buildSearchIndex();
  return _searchItems;
}

function pushSearchItem(item) {
  const items = getSearchItems();
  if (items.some(existing => existing.id === item.id && existing.type === item.type)) return;
  items.push(item);
}

/** Split query into tokens; every token must appear (AND). */
function tokenizeQuery(query) {
  return query
    .trim()
    .toLowerCase()
    .split(/[^a-z0-9&]+/i)
    .map(t => t.trim())
    .filter(t => t.length > 0);
}

function scoreSearchHit(item, tokens, hay) {
  const title = (item.title || '').toLowerCase();
  const subtitle = (item.subtitle || '').toLowerCase();
  let score = 0;
  tokens.forEach(t => {
    if (title.includes(t)) score += 8;
    else if (subtitle.includes(t)) score += 4;
    else if (hay.includes(t)) score += 1;
  });
  // Prefer manifesto docs when the query mentions manifesto
  if (item.type === 'manifesto' && tokens.includes('manifesto')) score += 6;
  if (item.type === 'election' && tokens.some(t => /^\d{4}$/.test(t) && title.includes(t))) score += 3;
  return score;
}

function runSearch(query) {
  const tokens = tokenizeQuery(query);
  if (!tokens.length) return [];
  if (tokens.join('').length < SEARCH_MIN_LEN && tokens.every(t => t.length < SEARCH_MIN_LEN)) {
    return [];
  }

  return getSearchItems()
    .map(item => {
      const hay = `${item.title} ${item.subtitle} ${item.body}`.toLowerCase();
      if (!tokens.every(t => hay.includes(t))) return null;
      const score = scoreSearchHit(item, tokens, hay);
      const primary = tokens[0];
      const idx = hay.indexOf(primary);
      const snippetStart = Math.max(0, idx === -1 ? 0 : idx - 40);
      const snippetLen = Math.min(hay.length, snippetStart + primary.length + 80);
      const snippet = hay.slice(snippetStart, snippetLen).replace(/\s+/g, ' ').trim();
      return {
        ...item,
        score,
        snippet: (snippetStart > 0 ? '…' : '') + snippet + (snippetLen < hay.length ? '…' : ''),
      };
    })
    .filter(Boolean)
    .sort((a, b) => b.score - a.score || a.title.localeCompare(b.title, 'en-GB'))
    .slice(0, 12);
}

function getSearchFocusables(overlay) {
  return Array.from(overlay.querySelectorAll(
    'input:not([disabled]), button:not([disabled]), a[href]'
  )).filter(el => el.offsetParent !== null || el === overlay.querySelector('.search-input'));
}

function setupSearch() {
  const toggle = document.getElementById('search-toggle');
  const overlay = document.getElementById('search-overlay');
  const panel = overlay?.querySelector('.search-panel');
  const input = document.getElementById('search-input');
  const results = document.getElementById('search-results');
  if (!toggle || !overlay || !panel || !input || !results) return;

  let activeResultIndex = -1;

  const getResultLinks = () => Array.from(results.querySelectorAll('.search-result'));

  const open = () => {
    _searchLastToggle = toggle;
    overlay.classList.add('is-open');
    overlay.setAttribute('aria-hidden', 'false');
    overlay.inert = false;
    panel.setAttribute('aria-modal', 'true');

    document.getElementById('main-nav')?.setAttribute('inert', '');
    document.getElementById('app')?.setAttribute('inert', '');
    document.getElementById('main-footer')?.setAttribute('inert', '');

    input.value = '';
    results.innerHTML = '<p class="search-hint" id="search-status">Search parties, elections, and archive descriptions.</p>';
    activeResultIndex = -1;
    setTimeout(() => input.focus(), 50);
    loadSearchExtraItems();
  };

  const close = () => {
    overlay.classList.remove('is-open');
    overlay.setAttribute('aria-hidden', 'true');
    overlay.inert = true;
    panel.setAttribute('aria-modal', 'false');

    document.getElementById('main-nav')?.removeAttribute('inert');
    document.getElementById('app')?.removeAttribute('inert');
    document.getElementById('main-footer')?.removeAttribute('inert');

    activeResultIndex = -1;
    if (_searchLastToggle) _searchLastToggle.focus();
  };

  const updateStatus = count => {
    let status = document.getElementById('search-status');
    if (!status) {
      status = document.createElement('p');
      status.id = 'search-status';
      status.className = 'search-sr-status';
      status.setAttribute('aria-live', 'polite');
      status.setAttribute('aria-atomic', 'true');
      panel.appendChild(status);
    }
    if (count === null) {
      status.textContent = '';
    } else if (count === 0) {
      status.textContent = 'No results found.';
    } else {
      status.textContent = `${count} result${count !== 1 ? 's' : ''}.`;
    }
  };

  const highlightResult = index => {
    const links = getResultLinks();
    links.forEach((a, i) => a.classList.toggle('is-active', i === index));
    if (links[index]) links[index].focus();
  };

  const renderHits = () => {
    const hits = runSearch(input.value);
    activeResultIndex = -1;

    if (!input.value.trim()) {
      results.innerHTML = '<p class="search-hint">Search parties, elections, and archive descriptions.</p>';
      updateStatus(null);
      return;
    }
    if (!hits.length) {
      results.innerHTML = '<p class="search-empty">No results found.</p>';
      updateStatus(0);
      return;
    }

    updateStatus(hits.length);
    results.innerHTML = hits.map(hit => `
      <a href="${hit.href}" class="search-result" data-close-search>
        <span class="search-result-dot" style="background:${hit.color}"></span>
        <span class="search-result-body">
          <span class="search-result-title">${hit.title}</span>
          <span class="search-result-sub">${hit.subtitle || ''}</span>
          ${hit.snippet ? `<span class="search-result-snippet">${hit.snippet}</span>` : ''}
        </span>
        <span class="search-result-type">${hit.type}</span>
      </a>
    `).join('');

    results.querySelectorAll('[data-close-search]').forEach(a => {
      a.addEventListener('click', close);
    });
  };

  toggle.addEventListener('click', open);
  overlay.querySelector('.search-backdrop')?.addEventListener('click', close);
  overlay.querySelector('.search-close')?.addEventListener('click', close);

  overlay.addEventListener('keydown', e => {
    if (!overlay.classList.contains('is-open')) return;

    if (e.key === 'Tab') {
      const focusables = getSearchFocusables(overlay);
      if (!focusables.length) return;
      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
      return;
    }

    if (e.key === 'Escape') {
      close();
      return;
    }

    const links = getResultLinks();
    if (!links.length) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      activeResultIndex = Math.min(links.length - 1, activeResultIndex + 1);
      highlightResult(activeResultIndex);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      activeResultIndex = Math.max(0, activeResultIndex - 1);
      highlightResult(activeResultIndex);
    } else if (e.key === 'Enter' && activeResultIndex >= 0 && document.activeElement === input) {
      e.preventDefault();
      links[activeResultIndex].click();
    }
  });

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && overlay.classList.contains('is-open')) close();
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      overlay.classList.contains('is-open') ? close() : open();
    }
  });

  input.addEventListener('input', renderHits);

  overlay.inert = true;
  results.innerHTML = '<p class="search-hint">Search parties, elections, and archive descriptions.</p>';

  loadSearchExtraItems();
}

async function indexManifestosForSearch() {
  try {
    const items = await fetchTyped('/data/manifestos-index.json', 'json');
    items.forEach(m => {
      const party = PARTIES?.[m.partyId];
      const label = m.label || `${party?.shortName || m.partyId} ${m.electionId}`;
      pushSearchItem({
        type: 'manifesto',
        id: `manifesto-${m.electionId}-${m.partyId}`,
        title: label,
        subtitle: `${m.electionId} · ${party?.shortName || m.partyId}`,
        body: `${party?.name || ''} ${m.electionId} manifesto ${label}`,
        href: `/manifesto/${m.electionId}/${m.partyId}`,
        color: party?.color || '#c9a84c',
      });
    });
  } catch (err) {
    console.error('Error indexing manifestos in search:', err);
  }
}

async function indexDevolvedPortal(loaderName, portalId, label, color) {
  if (typeof globalThis[loaderName] !== 'function') return;
  try {
    const idx = await globalThis[loaderName]();
    if (!Array.isArray(idx)) return;
    idx.forEach(e => {
      const year = e.displayYear || e.year || e.id;
      pushSearchItem({
        type: 'election',
        id: `${portalId}-${e.id}`,
        title: `${year} ${label}`,
        subtitle: e.winnerName || e.firstMinister || e.title || '',
        body: `${e.title || ''} ${label} ${portalId} election manifesto ${year}`,
        href: `/devolved/${portalId}/${e.id}`,
        color: color || '#c9a84c',
      });
    });
  } catch (err) {
    console.error(`Error indexing ${portalId} elections in search:`, err);
  }
}

async function loadSearchExtraItems() {
  if (_searchExtrasLoaded) return;
  _searchExtrasLoaded = true;

  await Promise.all([
    indexManifestosForSearch(),
    indexDevolvedPortal('loadEuroIndex', 'euro', 'European Parliament Election', '#F59E0B'),
    indexDevolvedPortal('loadHolyroodIndex', 'holyrood', 'Scottish Parliament Election', '#0065BD'),
    indexDevolvedPortal('loadSeneddIndex', 'senedd', 'Senedd Election', '#C8102E'),
    indexDevolvedPortal('loadNIIndex', 'stormont', 'Northern Ireland Assembly Election', '#D4AF37'),
    indexDevolvedPortal('loadLondonIndex', 'london', 'London Election', '#EE3A43'),
  ]);
}
