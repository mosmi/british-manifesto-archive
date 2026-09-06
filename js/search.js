/* ============================================================
   Client search — two labelled modes:
   1) Catalogue: parties, elections, manifesto titles, portals
   2) Full text: inverted index over manifesto.md transcriptions
   ============================================================ */

const SEARCH_MIN_LEN = 2;
const SEARCH_LIMIT = 24;
const FULLTEXT_MIN_LEN = 3;
const FULLTEXT_META_URL = () =>
  `/data/fulltext-meta.json?v=${typeof ASSETS_VERSION !== 'undefined' ? ASSETS_VERSION : ''}`;
const FULLTEXT_INDEX_URL = bust =>
  `/data/fulltext-index.json?v=${encodeURIComponent(bust || (typeof ASSETS_VERSION !== 'undefined' ? ASSETS_VERSION : ''))}`;

const TYPE_ORDER = ['party', 'election', 'manifesto', 'portal', 'nation', 'passage'];
const TYPE_LABELS = {
  party: 'Parties',
  election: 'Elections',
  manifesto: 'Manifestos',
  portal: 'Institutions',
  nation: 'Nations',
  passage: 'In manifesto text',
};

const SEARCH_MODE_KEY = 'manifestos-search-mode';

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
        aliases: [p.name, p.shortName, p.id].filter(Boolean),
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
        aliases: [e.displayYear, e.id, e.pm].filter(Boolean),
      });
    });
  }

  if (typeof NATIONS !== 'undefined') {
    Object.values(NATIONS).forEach(n => {
      items.push({
        type: 'nation',
        id: n.id,
        title: n.name,
        subtitle: n.id === 'europe'
          ? 'Pan-European political families'
          : `${n.constituencies} Westminster constituencies`,
        body: n.description || '',
        href: n.id === 'europe' ? '/party/european-groups' : `/nation/${n.id}`,
        color: '#c9a84c',
        aliases: [n.name, n.id],
      });
    });
  }

  if (typeof DEVOLVED_PORTALS !== 'undefined') {
    Object.values(DEVOLVED_PORTALS).forEach(portal => {
      items.push({
        type: 'portal',
        id: `portal-${portal.id}`,
        title: portal.label,
        subtitle: portal.subtitle || nodeLabel('elections'),
        body: `${portal.description || ''} ${portal.id} devolved election manifestos`,
        href: `/election/${portal.id}`,
        color: '#c9a84c',
        aliases: [portal.label, portal.subtitle, portal.id].filter(Boolean),
      });
    });
  }

  return items;
}

let _searchItems = null;
let _searchLastToggle = null;
let _searchExtrasLoaded = false;
let _searchMode = 'catalogue'; // 'catalogue' | 'fulltext'
let _fulltextIndex = null;
let _fulltextIndexPromise = null;
const _fulltextPlainCache = new Map();
let _fulltextSnippetGen = 0;

function getSearchItems() {
  if (!_searchItems) _searchItems = buildSearchIndex();
  return _searchItems;
}

function pushSearchItem(item) {
  const items = getSearchItems();
  if (items.some(existing => existing.id === item.id && existing.type === item.type)) return;
  items.push(item);
}

function getStoredSearchMode() {
  try {
    const v = sessionStorage.getItem(SEARCH_MODE_KEY);
    if (v === 'fulltext' || v === 'catalogue') return v;
  } catch (_) { /* ignore */ }
  return 'catalogue';
}

function setStoredSearchMode(mode) {
  _searchMode = mode;
  try { sessionStorage.setItem(SEARCH_MODE_KEY, mode); } catch (_) { /* ignore */ }
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
  const aliases = (item.aliases || []).map(a => String(a).toLowerCase());
  let score = 0;

  tokens.forEach(t => {
    if (title === t) score += 40;
    else if (aliases.some(a => a === t)) score += 36;
    else if (title.startsWith(t)) score += 24;
    else if (title.includes(t)) score += 16;
    else if (aliases.some(a => a.startsWith(t) || a.includes(t))) score += 12;
    else if (subtitle.includes(t)) score += 6;
    else if (hay.includes(t)) score += 1;
  });

  if (item.type === 'party' && typeof PARTIES !== 'undefined' && PARTIES[item.id]?.isPrimary) {
    score += 8;
  }
  if (item.type === 'manifesto' && tokens.includes('manifesto')) score += 6;
  if (item.type === 'election' && tokens.some(t => /^\d{4}$/.test(t) && title.includes(t))) score += 10;
  if (
    item.type === 'election'
    && item.href?.startsWith('/election/')
    && tokens.length === 1
    && /^\d{4}$/.test(tokens[0])
  ) {
    score += 6;
  }
  return score;
}

function runCatalogueSearch(query) {
  const tokens = tokenizeQuery(query);
  if (!tokens.length) return [];
  if (tokens.join('').length < SEARCH_MIN_LEN && tokens.every(t => t.length < SEARCH_MIN_LEN)) {
    return [];
  }

  return getSearchItems()
    .map(item => {
      const displayHay = `${item.title} ${item.subtitle} ${item.body} ${(item.aliases || []).join(' ')}`;
      const hay = displayHay.toLowerCase();
      if (!tokens.every(t => hay.includes(t))) return null;
      const score = scoreSearchHit(item, tokens, hay);
      const primary = tokens[0];
      const idx = hay.indexOf(primary);
      const snippetStart = Math.max(0, idx === -1 ? 0 : idx - 40);
      const snippetLen = Math.min(displayHay.length, snippetStart + primary.length + 80);
      const snippet = displayHay.slice(snippetStart, snippetLen).replace(/\s+/g, ' ').trim();
      return {
        ...item,
        score,
        snippet: (snippetStart > 0 ? '…' : '') + snippet + (snippetLen < hay.length ? '…' : ''),
      };
    })
    .filter(Boolean)
    .sort((a, b) => b.score - a.score || a.title.localeCompare(b.title, 'en-GB'))
    .slice(0, SEARCH_LIMIT);
}

/** Levenshtein distance with early exit when exceeding maxDist. */
function editDistance(a, b, maxDist = 2) {
  if (a === b) return 0;
  const la = a.length;
  const lb = b.length;
  if (Math.abs(la - lb) > maxDist) return maxDist + 1;
  if (!la) return lb;
  if (!lb) return la;
  let prev = new Array(lb + 1);
  let curr = new Array(lb + 1);
  for (let j = 0; j <= lb; j++) prev[j] = j;
  for (let i = 1; i <= la; i++) {
    curr[0] = i;
    let rowMin = curr[0];
    for (let j = 1; j <= lb; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      curr[j] = Math.min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost);
      if (curr[j] < rowMin) rowMin = curr[j];
    }
    if (rowMin > maxDist) return maxDist + 1;
    [prev, curr] = [curr, prev];
  }
  return prev[lb];
}

/**
 * Catalogue “Did you mean…?” suggestions when exact search is empty.
 * Fuzzy-matches party/election/portal/nation titles and aliases only (not full text).
 */
function catalogueDidYouMean(query, limit = 5) {
  const tokens = tokenizeQuery(query).filter(t => t.length >= 4);
  if (!tokens.length) return [];

  const seen = new Set();
  const scored = [];

  getSearchItems().forEach(item => {
    if (!['party', 'election', 'portal', 'nation'].includes(item.type)) return;
    const labels = [item.title, ...(item.aliases || [])]
      .map(s => String(s || '').toLowerCase())
      .filter(Boolean);
    let best = Infinity;
    labels.forEach(label => {
      const words = label.split(/[^a-z0-9]+/).filter(w => w.length >= 3);
      const pool = words.length ? words : [label.replace(/[^a-z0-9]+/g, '')];
      tokens.forEach(t => {
        const maxDist = t.length >= 6 ? 2 : 1;
        pool.forEach(w => {
          if (!w || Math.abs(w.length - t.length) > maxDist) return;
          const d = editDistance(t, w, maxDist);
          if (d > 0 && d <= maxDist && d < best) best = d;
        });
      });
    });
    if (best === Infinity) return;
    const key = `${item.type}:${item.id}`;
    if (seen.has(key)) return;
    seen.add(key);
    let score = 20 - best * 6;
    if (item.type === 'party' && PARTIES?.[item.id]?.isPrimary) score += 8;
    if (item.type === 'party') score += 4;
    scored.push({
      query: item.title,
      title: item.title,
      type: item.type,
      href: item.href,
      color: item.color,
      score,
      distance: best,
    });
  });

  return scored
    .sort((a, b) => b.score - a.score || a.distance - b.distance || a.title.localeCompare(b.title, 'en-GB'))
    .slice(0, limit);
}

function ensureFulltextIndex() {
  if (_fulltextIndex) return Promise.resolve(_fulltextIndex);
  if (_fulltextIndexPromise) return _fulltextIndexPromise;
  _fulltextIndexPromise = fetchTyped(FULLTEXT_META_URL(), 'json')
    .catch(() => null)
    .then(meta => {
      const bust = meta?.generated || meta?.fingerprint || '';
      return fetchTyped(FULLTEXT_INDEX_URL(bust), 'json');
    })
    .then(data => {
      _fulltextIndex = data;
      return data;
    })
    .catch(err => {
      _fulltextIndexPromise = null;
      throw err;
    });
  return _fulltextIndexPromise;
}

function stripMarkdownPlain(text, lower = false) {
  const plain = String(text || '')
    .replace(/^---[\s\S]*?---\n/, '')
    .replace(/!\[[^\]]*\]\([^)]+\)/g, ' ')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/[#>*_`~|]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  return lower ? plain.toLowerCase() : plain;
}

async function loadManifestoPlain(electionId, partyId) {
  const key = `${electionId}/${partyId}`;
  if (_fulltextPlainCache.has(key)) return _fulltextPlainCache.get(key);
  const path = `/manifestos/${electionId}/${partyId}/manifesto.md`;
  try {
    const raw = await fetchTyped(path, 'markdown');
    const plain = stripMarkdownPlain(raw);
    _fulltextPlainCache.set(key, plain);
    return plain;
  } catch {
    _fulltextPlainCache.set(key, '');
    return '';
  }
}

function excerptAround(plain, tokens, radius = 70) {
  if (!plain) return '';
  const hay = plain.toLowerCase();
  let best = -1;
  let term = tokens[0] || '';
  tokens.forEach(t => {
    const idx = hay.indexOf(t);
    if (idx !== -1 && (best === -1 || idx < best)) {
      best = idx;
      term = t;
    }
  });
  if (best === -1) {
    return plain.slice(0, radius * 2).trim() + (plain.length > radius * 2 ? '…' : '');
  }
  const start = Math.max(0, best - radius);
  const end = Math.min(plain.length, best + term.length + radius);
  return (start > 0 ? '…' : '') + plain.slice(start, end).trim() + (end < plain.length ? '…' : '');
}

function escapeHtml(s) {
  return String(s || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function runFulltextLookup(query, index) {
  const tokens = tokenizeQuery(query).filter(t => t.length >= FULLTEXT_MIN_LEN);
  if (!tokens.length) return [];

  const inv = index.inv || {};
  const docs = index.docs || [];
  let setIds = null;

  for (const token of tokens) {
    const hits = inv[token];
    if (!hits || !hits.length) return [];
    const asSet = new Set(hits);
    setIds = setIds
      ? new Set([...setIds].filter(id => asSet.has(id)))
      : asSet;
    if (!setIds.size) return [];
  }

  return [...setIds].map(docIndex => {
    const doc = docs[docIndex];
    if (!doc) return null;
    const party = PARTIES?.[doc.p];
    let score = tokens.length * 10;
    if (party?.isPrimary) score += 4;
    // Prefer more recent elections when the year is parseable.
    const yearMatch = String(doc.e).match(/(\d{4})/);
    if (yearMatch) score += Math.min(8, Math.max(0, (parseInt(yearMatch[1], 10) - 1945) / 20));
    return {
      type: 'passage',
      id: `ft-${doc.e}-${doc.p}`,
      title: doc.l || `${party?.shortName || doc.p} ${doc.e}`,
      subtitle: `${doc.e} · ${party?.shortName || doc.p}`,
      href: `/manifesto/${doc.e}/${doc.p}`,
      color: party?.color || '#c9a84c',
      electionId: doc.e,
      partyId: doc.p,
      score,
      snippet: 'Loading excerpt…',
      tokens,
    };
  })
    .filter(Boolean)
    .sort((a, b) => b.score - a.score || a.title.localeCompare(b.title, 'en-GB'))
    .slice(0, SEARCH_LIMIT);
}

function groupSearchHits(hits) {
  const groups = {};
  TYPE_ORDER.forEach(t => { groups[t] = []; });
  hits.forEach(hit => {
    if (!groups[hit.type]) groups[hit.type] = [];
    groups[hit.type].push(hit);
  });
  return TYPE_ORDER
    .filter(t => groups[t]?.length)
    .map(t => ({ type: t, label: TYPE_LABELS[t] || t, hits: groups[t] }));
}

function getSearchFocusables(overlay) {
  return Array.from(overlay.querySelectorAll(
    'input:not([disabled]), button:not([disabled]), a[href]'
  )).filter(el => el.offsetParent !== null || el === overlay.querySelector('.search-input'));
}

function searchModifierLabel() {
  const isApple = /Mac|iPhone|iPad|iPod/i.test(navigator.platform || '')
    || /Mac OS X/i.test(navigator.userAgent || '');
  return isApple ? '⌘K' : 'Ctrl+K';
}

function searchModeToggleHtml() {
  return `
    <div class="search-mode-toggle" role="tablist" aria-label="Search mode">
      <button type="button" role="tab" class="search-mode-btn${_searchMode === 'catalogue' ? ' active' : ''}" data-search-mode="catalogue" aria-selected="${_searchMode === 'catalogue' ? 'true' : 'false'}">Catalogue</button>
      <button type="button" role="tab" class="search-mode-btn${_searchMode === 'fulltext' ? ' active' : ''}" data-search-mode="fulltext" aria-selected="${_searchMode === 'fulltext' ? 'true' : 'false'}">Full text</button>
    </div>`;
}

function searchEmptyHintHtml(includeToggle = true) {
  const toggle = includeToggle ? searchModeToggleHtml() : '';
  if (_searchMode === 'fulltext') {
    const n = _fulltextIndex?.docCount;
    return `
      ${toggle}
      <p class="search-hint">
        Search inside transcribed manifesto text
        ${n ? `(${n} documents)` : ''} —
        not PDFs that have no readable text edition yet.
      </p>
      <p class="search-examples">
        Try <button type="button" class="search-example" data-query="housing">housing</button>,
        <button type="button" class="search-example" data-query="NHS">NHS</button>,
        <button type="button" class="search-example" data-query="climate">climate</button>,
        or <button type="button" class="search-example" data-query="immigration">immigration</button>.
      </p>`;
  }
  return `
    ${toggle}
    <p class="search-hint">
      Search parties, elections, and manifesto <strong>titles</strong> in the archive.
      Switch to <strong>Full text</strong> to search inside transcriptions.
    </p>
    <p class="search-examples">
      Try <button type="button" class="search-example" data-query="Labour">Labour</button>,
      <button type="button" class="search-example" data-query="2024">2024</button>,
      <button type="button" class="search-example" data-query="Attlee">Attlee</button>,
      or <button type="button" class="search-example" data-query="Holyrood">Holyrood</button>.
    </p>`;
}

function searchSuggestionsHtml(suggestions) {
  if (!suggestions?.length) return '';
  return `
    <p class="search-suggest-label">Did you mean…?</p>
    <p class="search-examples search-suggestions">
      ${suggestions.map(s => `
        <button type="button" class="search-example search-suggest" data-query="${escapeHtml(s.query)}" data-suggest-href="${escapeHtml(s.href || '')}">
          ${escapeHtml(s.title)}
        </button>`).join('')}
    </p>`;
}

function searchZeroHtml(query, suggestions = [], includeToggle = true) {
  const safe = escapeHtml(query);
  const toggle = includeToggle ? searchModeToggleHtml() : '';
  if (_searchMode === 'fulltext') {
    return `
      ${toggle}
      <div class="search-empty-block">
        <p class="search-empty">No manifesto passages for “${safe}”.</p>
        <p class="search-empty-help">
          Full-text search covers transcribed Markdown only. Try another term, or switch to Catalogue for party and election names.
        </p>
        <ul class="search-empty-links">
          <li><button type="button" class="search-switch-mode" data-search-mode="catalogue">Search the archive instead</button></li>
          <li><a href="/party/all" data-close-search>Browse all parties</a></li>
          <li><a href="/election/westminster" data-close-search>UK general elections</a></li>
        </ul>
      </div>`;
  }
  return `
    ${toggle}
    <div class="search-empty-block">
      <p class="search-empty">No catalogue matches for “${safe}”.</p>
      ${searchSuggestionsHtml(suggestions)}
      <p class="search-empty-help">
        Catalogue search covers party names, election years, and manifesto titles.
        To search policy wording inside documents, switch to Full text.
      </p>
      <ul class="search-empty-links">
        <li><button type="button" class="search-switch-mode" data-search-mode="fulltext">Search manifesto full text</button></li>
        <li><a href="/party/all" data-close-search>Browse all parties</a></li>
        <li><a href="/election/westminster" data-close-search>UK general elections</a></li>
        <li><a href="/election/2024" data-close-search>2024 general election</a></li>
      </ul>
    </div>`;
}

function searchHitHtml(hit) {
  const typeLabel = hit.type === 'passage' ? 'text' : hit.type;
  return `
    <a href="${hit.href}" class="search-result" data-close-search data-hit-id="${escapeHtml(hit.id)}">
      <span class="search-result-dot" style="background:${hit.color}"></span>
      <span class="search-result-body">
        <span class="search-result-title">${escapeHtml(hit.title)}</span>
        <span class="search-result-sub">${escapeHtml(hit.subtitle || '')}</span>
        ${hit.snippet ? `<span class="search-result-snippet">${escapeHtml(hit.snippet)}</span>` : ''}
      </span>
      <span class="search-result-type">${escapeHtml(typeLabel)}</span>
    </a>`;
}

function applySearchChrome(input, kicker) {
  if (kicker) {
    kicker.textContent = _searchMode === 'fulltext'
      ? 'Search manifesto text'
      : 'Search the archive';
  }
  if (input) {
    input.placeholder = _searchMode === 'fulltext'
      ? 'Try housing, NHS, climate, immigration…'
      : 'Try Labour, 2024, Attlee, or Holyrood…';
    const label = document.querySelector('label[for="search-input"]');
    if (label) {
      label.textContent = _searchMode === 'fulltext'
        ? 'Search inside manifesto transcriptions'
        : 'Search parties, elections, and manifesto titles';
    }
  }
}

function searchPageHref(query, mode) {
  const params = new URLSearchParams();
  const q = String(query || '').trim();
  if (q) params.set('q', q);
  if (mode === 'fulltext') params.set('mode', 'fulltext');
  const qs = params.toString();
  return qs ? `/search?${qs}` : '/search';
}

function setupSearch() {
  const toggle = document.getElementById('search-toggle');
  const overlay = document.getElementById('search-overlay');
  const panel = overlay?.querySelector('.search-panel');
  const input = document.getElementById('search-input');
  const results = document.getElementById('search-results');
  const kbdHint = document.getElementById('search-kbd-hint');
  const kicker = overlay?.querySelector('.search-panel-kicker');
  const navKbd = document.querySelector('.nav-search-kbd');
  if (!toggle || !overlay || !panel || !input || !results) return;

  _searchMode = getStoredSearchMode();
  applySearchChrome(input, kicker);

  const mod = searchModifierLabel();
  if (navKbd) navKbd.textContent = mod;
  if (kbdHint) {
    kbdHint.textContent = `Press Esc to close · ${mod} to toggle`;
  }

  let activeResultIndex = -1;
  let debounceTimer = null;

  const getResultLinks = () => Array.from(results.querySelectorAll('.search-result'));

  const bindCloseLinks = () => {
    results.querySelectorAll('[data-close-search]').forEach(a => {
      a.addEventListener('click', close);
    });
  };

  const bindExampleButtons = () => {
    results.querySelectorAll('.search-example').forEach(btn => {
      btn.addEventListener('click', () => {
        input.value = btn.getAttribute('data-query') || '';
        input.focus();
        renderHits();
      });
    });
  };

  const bindModeControls = () => {
    results.querySelectorAll('[data-search-mode]').forEach(btn => {
      btn.addEventListener('click', () => {
        const mode = btn.getAttribute('data-search-mode');
        if (mode !== 'catalogue' && mode !== 'fulltext') return;
        if (mode === _searchMode) return;
        setStoredSearchMode(mode);
        applySearchChrome(input, kicker);
        renderHits();
        if (mode === 'fulltext') ensureFulltextIndex().catch(() => {});
      });
    });
  };

  const enrichFulltextSnippets = async (hits, gen) => {
    await Promise.all(hits.map(async hit => {
      const plain = await loadManifestoPlain(hit.electionId, hit.partyId);
      if (gen !== _fulltextSnippetGen) return;
      hit.snippet = excerptAround(plain, hit.tokens || tokenizeQuery(input.value));
      const row = Array.from(results.querySelectorAll('.search-result'))
        .find(a => a.getAttribute('data-hit-id') === hit.id);
      const el = row?.querySelector('.search-result-snippet');
      if (el) el.textContent = hit.snippet;
    }));
  };

  const open = () => {
    _searchLastToggle = toggle;
    overlay.classList.add('is-open');
    overlay.setAttribute('aria-hidden', 'false');
    overlay.inert = false;
    panel.setAttribute('aria-modal', 'true');

    document.querySelector('.skip-link')?.setAttribute('inert', '');
    document.getElementById('main-nav')?.setAttribute('inert', '');
    document.getElementById('app')?.setAttribute('inert', '');
    document.getElementById('main-footer')?.setAttribute('inert', '');

    input.value = '';
    results.innerHTML = searchEmptyHintHtml();
    bindExampleButtons();
    bindModeControls();
    activeResultIndex = -1;
    setTimeout(() => input.focus(), 50);
    loadSearchExtraItems();
    if (_searchMode === 'fulltext') ensureFulltextIndex().catch(() => {});
  };

  const close = () => {
    overlay.classList.remove('is-open');
    overlay.setAttribute('aria-hidden', 'true');
    overlay.inert = true;
    panel.setAttribute('aria-modal', 'false');

    document.querySelector('.skip-link')?.removeAttribute('inert');
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

  const paintHits = hits => {
    updateStatus(hits.length);
    const groups = groupSearchHits(hits);
    results.innerHTML = `
      ${searchModeToggleHtml()}
      ${groups.map(group => `
      <section class="search-group" aria-label="${group.label}">
        <h3 class="search-group-label">${group.label}</h3>
        ${group.hits.map(searchHitHtml).join('')}
      </section>`).join('')}`;
    bindCloseLinks();
    bindModeControls();
  };

  const renderHits = async () => {
    activeResultIndex = -1;
    const q = input.value;

    if (!q.trim()) {
      results.innerHTML = searchEmptyHintHtml();
      bindExampleButtons();
      bindModeControls();
      updateStatus(null);
      return;
    }

    if (_searchMode === 'catalogue') {
      const hits = runCatalogueSearch(q);
      if (!hits.length) {
        const suggestions = catalogueDidYouMean(q.trim());
        results.innerHTML = searchZeroHtml(q.trim(), suggestions);
        bindCloseLinks();
        bindExampleButtons();
        bindModeControls();
        updateStatus(0);
        return;
      }
      paintHits(hits);
      return;
    }

    // Full text mode
    results.innerHTML = `
      ${searchModeToggleHtml()}
      <p class="search-hint">Searching manifesto text…</p>`;
    bindModeControls();

    let index;
    try {
      index = await ensureFulltextIndex();
    } catch (err) {
      console.error('Full-text index failed to load:', err);
      results.innerHTML = `
        ${searchModeToggleHtml()}
        <div class="search-empty-block">
          <p class="search-empty">Full-text index could not be loaded.</p>
          <p class="search-empty-help">Try again, or use Catalogue search for names and titles.</p>
        </div>`;
      bindModeControls();
      updateStatus(0);
      return;
    }

    if (input.value !== q) return; // stale

    const tokens = tokenizeQuery(q).filter(t => t.length >= FULLTEXT_MIN_LEN);
    if (!tokens.length) {
      results.innerHTML = `
        ${searchModeToggleHtml()}
        <p class="search-hint">Use at least ${FULLTEXT_MIN_LEN} letters per word for full-text search.</p>`;
      bindModeControls();
      updateStatus(null);
      return;
    }

    const hits = runFulltextLookup(q, index);
    if (!hits.length) {
      results.innerHTML = searchZeroHtml(q.trim());
      bindCloseLinks();
      bindModeControls();
      updateStatus(0);
      return;
    }

    paintHits(hits);
    const gen = ++_fulltextSnippetGen;
    enrichFulltextSnippets(hits, gen);
  };

  const pageLink = document.getElementById('search-page-link');

  const syncOverlayPageLink = () => {
    if (!pageLink) return;
    pageLink.href = searchPageHref(input.value, _searchMode);
  };

  toggle.addEventListener('click', () => {
    const path = typeof getPath === 'function' ? getPath() : window.location.pathname;
    if (path === '/search') {
      document.getElementById('search-page-input')?.focus();
      return;
    }
    open();
  });
  overlay.querySelector('.search-backdrop')?.addEventListener('click', close);
  overlay.querySelector('.search-close')?.addEventListener('click', close);
  document.getElementById('search-browse-link')?.addEventListener('click', close);
  pageLink?.addEventListener('click', close);

  overlay.addEventListener('keydown', e => {
    if (!overlay.classList.contains('is-open')) return;

    // 3.7: overlay is a modal; nav/app/footer are inert. Cycle Tab inside.
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
      const path = typeof getPath === 'function' ? getPath() : window.location.pathname;
      if (path === '/search' && !overlay.classList.contains('is-open')) {
        document.getElementById('search-page-input')?.focus();
        return;
      }
      overlay.classList.contains('is-open') ? close() : open();
    }
  });

  input.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    const delay = _searchMode === 'fulltext' ? 180 : 0;
    debounceTimer = setTimeout(() => { renderHits(); syncOverlayPageLink(); }, delay);
  });

  overlay.inert = true;
  results.innerHTML = searchEmptyHintHtml();
  syncOverlayPageLink();
}

async function indexManifestosForSearch() {
  try {
    const items = await fetchTyped('/data/manifestos-index.json', 'json');
    items.forEach(m => {
      const party = PARTIES?.[m.partyId];
      const rec = (typeof manifestoTitleRecord === 'function')
        ? manifestoTitleRecord(m.electionId, m.partyId)
        : { title: '', distinctive: false };
      const partyName = party?.shortName || party?.name || m.partyId;
      const year = m.electionId;
      const pub = rec.title || '';
      const label = rec.distinctive && pub
        ? pub
        : `${partyName} manifesto, ${year}`;
      pushSearchItem({
        type: 'manifesto',
        id: `manifesto-${m.electionId}-${m.partyId}`,
        title: label,
        subtitle: `${year} · ${partyName}`,
        body: `${party?.name || ''} ${year} manifesto ${pub} ${label}`,
        href: `/manifesto/${m.electionId}/${m.partyId}`,
        color: party?.color || '#c9a84c',
        aliases: [party?.shortName, party?.name, m.electionId, m.partyId, pub].filter(Boolean),
      });
    });
  } catch (err) {
    console.error('Error indexing manifestos in search:', err);
  }
}

async function indexDevolvedPortal(portalId, label, color) {
  try {
    const idx = await fetchTyped(`/data/devolved/${portalId}/index.json`, 'json');
    if (!Array.isArray(idx)) return;
    idx.forEach(e => {
      const year = e.displayYear || e.year || e.id;
      pushSearchItem({
        type: 'election',
        id: `${portalId}-${e.id}`,
        title: `${year} ${label}`,
        subtitle: e.winnerName || e.firstMinister || e.title || '',
        body: `${e.title || ''} ${label} ${portalId} election manifesto ${year}`,
        href: `/election/${portalId}/${e.id}`,
        color: color || '#c9a84c',
        aliases: [year, label, portalId],
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
    indexDevolvedPortal('euro', 'European Parliament Election', '#F59E0B'),
    indexDevolvedPortal('holyrood', 'Scottish Parliament Election', '#0065BD'),
    indexDevolvedPortal('senedd', 'Senedd Election', '#C8102E'),
    indexDevolvedPortal('stormont', 'Northern Ireland Assembly Election', '#D4AF37'),
    indexDevolvedPortal('london', 'London Election', '#EE3A43'),
  ]);
}

function renderSearchPage(app) {
  const params = new URLSearchParams(window.location.search);
  const initialQ = params.get('q') || '';
  const initialMode = params.get('mode') === 'fulltext' ? 'fulltext' : 'catalogue';
  setStoredSearchMode(initialMode);
  const title = initialQ ? `Search: ${initialQ}` : 'Search';
  setPageMeta({
    title,
    description: 'Search parties, elections, and manifesto titles, or search inside transcribed manifesto text.',
    path: '/search',
  });

  app.innerHTML = `
    ${typeof renderBreadcrumb === 'function' ? renderBreadcrumb([
      { label: typeof nodeLabel === 'function' ? nodeLabel('home') : 'Home', href: '/' },
      { label: 'Search' },
    ]) : ''}
    <section class="search-page">
      <h1 class="search-page-title">Search</h1>
      <p class="search-page-lead">Catalogue covers parties, elections, and published manifesto titles. Full text looks inside transcribed documents.</p>
      <form class="search-page-form" id="search-page-form" role="search" action="/search" method="get">
        ${searchModeToggleHtml()}
        <label class="sr-only" for="search-page-input">Search the archive</label>
        <div class="search-page-input-row">
          <input type="search" id="search-page-input" name="q" class="search-input" value="${escapeHtml(initialQ)}" placeholder="Try Thatcher, housing, or 1997…" autocomplete="off" spellcheck="false">
          <button type="submit" class="search-page-submit">Search</button>
        </div>
        ${initialMode === 'fulltext' ? '<input type="hidden" name="mode" value="fulltext">' : ''}
      </form>
      <div id="search-page-results" class="search-results search-page-results"></div>
    </section>
  `;

  const input = document.getElementById('search-page-input');
  const results = document.getElementById('search-page-results');
  const form = document.getElementById('search-page-form');
  if (!input || !results) return;

  applySearchChrome(input, null);
  let debounceTimer = null;

  const syncUrl = () => {
    const href = searchPageHref(input.value, _searchMode);
    if (`${window.location.pathname}${window.location.search}` !== href) {
      history.replaceState(null, '', href);
    }
    const q = input.value.trim();
    setPageMeta({
      title: q ? `Search: ${q}` : 'Search',
      description: 'Search parties, elections, and manifesto titles, or search inside transcribed manifesto text.',
      path: '/search',
    });
  };

  const syncFormModeToggle = () => {
    form.querySelectorAll('.search-mode-btn').forEach(btn => {
      const on = btn.getAttribute('data-search-mode') === _searchMode;
      btn.classList.toggle('active', on);
      btn.setAttribute('aria-selected', on ? 'true' : 'false');
    });
  };

  const applyPageMode = (mode) => {
    if (mode !== 'catalogue' && mode !== 'fulltext') return;
    if (mode === _searchMode) return;
    setStoredSearchMode(mode);
    applySearchChrome(input, null);
    syncFormModeToggle();
    const hidden = form.querySelector('input[name="mode"]');
    if (mode === 'fulltext') {
      if (!hidden) {
        const el = document.createElement('input');
        el.type = 'hidden';
        el.name = 'mode';
        el.value = 'fulltext';
        form.appendChild(el);
      } else hidden.value = 'fulltext';
    } else {
      hidden?.remove();
    }
    renderHits();
    syncUrl();
    if (mode === 'fulltext') ensureFulltextIndex().catch(() => {});
  };

  form.querySelectorAll('[data-search-mode]').forEach(btn => {
    btn.addEventListener('click', () => applyPageMode(btn.getAttribute('data-search-mode')));
  });

  const bindModeControls = () => {
    results.querySelectorAll('[data-search-mode]').forEach(btn => {
      btn.addEventListener('click', () => applyPageMode(btn.getAttribute('data-search-mode')));
    });
  };

  const bindExamples = () => {
    results.querySelectorAll('.search-example').forEach(btn => {
      btn.addEventListener('click', () => {
        input.value = btn.getAttribute('data-query') || '';
        input.focus();
        renderHits();
        syncUrl();
      });
    });
  };

  const paintHits = hits => {
    const groups = groupSearchHits(hits);
    results.innerHTML = groups.map(group => `
      <section class="search-group" aria-label="${group.label}">
        <h2 class="search-group-label">${group.label}</h2>
        ${group.hits.map(searchHitHtml).join('')}
      </section>`).join('');
  };

  const renderHits = async () => {
    const q = input.value;
    if (!q.trim()) {
      results.innerHTML = searchEmptyHintHtml(false);
      bindExamples();
      bindModeControls();
      return;
    }
    if (_searchMode === 'catalogue') {
      const hits = runCatalogueSearch(q);
      if (!hits.length) {
        results.innerHTML = searchZeroHtml(q.trim(), catalogueDidYouMean(q.trim()), false);
        bindExamples();
        bindModeControls();
        return;
      }
      paintHits(hits);
      return;
    }
    results.innerHTML = `<p class="search-hint">Searching manifesto text…</p>`;
    let index;
    try {
      index = await ensureFulltextIndex();
    } catch {
      results.innerHTML = `<p class="search-empty">Full-text index could not be loaded.</p>`;
      return;
    }
    if (input.value !== q) return;
    const tokens = tokenizeQuery(q).filter(t => t.length >= FULLTEXT_MIN_LEN);
    if (!tokens.length) {
      results.innerHTML = `<p class="search-hint">Use at least ${FULLTEXT_MIN_LEN} letters per word for full-text search.</p>`;
      return;
    }
    const hits = runFulltextLookup(q, index);
    if (!hits.length) {
      results.innerHTML = searchZeroHtml(q.trim(), [], false);
      bindModeControls();
      return;
    }
    paintHits(hits);
    const gen = ++_fulltextSnippetGen;
    await Promise.all(hits.map(async hit => {
      const plain = await loadManifestoPlain(hit.electionId, hit.partyId);
      if (gen !== _fulltextSnippetGen) return;
      hit.snippet = excerptAround(plain, hit.tokens || tokenizeQuery(input.value));
      const row = results.querySelector(`[data-hit-id="${CSS.escape(hit.id)}"]`);
      const el = row?.querySelector('.search-result-snippet');
      if (el) el.textContent = hit.snippet;
    }));
  };

  form.addEventListener('submit', e => {
    e.preventDefault();
    syncUrl();
    renderHits();
  });
  input.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    const delay = _searchMode === 'fulltext' ? 180 : 0;
    debounceTimer = setTimeout(() => {
      syncUrl();
      renderHits();
    }, delay);
  });

  loadSearchExtraItems().then(() => renderHits());
  if (_searchMode === 'fulltext') ensureFulltextIndex().catch(() => {});
  requestAnimationFrame(() => input.focus());
}
window.renderSearchPage = renderSearchPage;

