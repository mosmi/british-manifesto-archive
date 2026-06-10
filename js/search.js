/* ============================================================
   Client search — lightweight index over bundled data.
   Full manifesto text indexing (FlexSearch) planned for Phase 3.
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
        body: `${p.name} ${p.description || ''}`,
        href: `#/party/${p.id}`,
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
        body: `${e.summary || ''} ${(e.highlights || []).join(' ')}`,
        href: `#/election/${e.id}`,
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
        href: `#/nation/${n.id}`,
        color: '#c9a84c',
      });
    });
  }

  return items;
}

let _searchItems = null;

function getSearchItems() {
  if (!_searchItems) _searchItems = buildSearchIndex();
  return _searchItems;
}

function runSearch(query) {
  const q = query.trim().toLowerCase();
  if (q.length < SEARCH_MIN_LEN) return [];

  return getSearchItems()
    .map(item => {
      const hay = `${item.title} ${item.subtitle} ${item.body}`.toLowerCase();
      const idx = hay.indexOf(q);
      if (idx === -1) return null;
      const snippetStart = Math.max(0, idx - 40);
      const snippet = hay.slice(snippetStart, idx + q.length + 60).replace(/\s+/g, ' ').trim();
      return { ...item, snippet: (snippetStart > 0 ? '…' : '') + snippet + '…' };
    })
    .filter(Boolean)
    .slice(0, 12);
}

function setupSearch() {
  const toggle = document.getElementById('search-toggle');
  const overlay = document.getElementById('search-overlay');
  const input = document.getElementById('search-input');
  const results = document.getElementById('search-results');
  if (!toggle || !overlay || !input || !results) return;

  const open = () => {
    overlay.classList.add('is-open');
    overlay.setAttribute('aria-hidden', 'false');
    input.value = '';
    results.innerHTML = '';
    setTimeout(() => input.focus(), 50);
  };

  const close = () => {
    overlay.classList.remove('is-open');
    overlay.setAttribute('aria-hidden', 'true');
  };

  toggle.addEventListener('click', open);
  overlay.querySelector('.search-backdrop')?.addEventListener('click', close);
  overlay.querySelector('.search-close')?.addEventListener('click', close);

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && overlay.classList.contains('is-open')) close();
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      overlay.classList.contains('is-open') ? close() : open();
    }
  });

  input.addEventListener('input', () => {
    const hits = runSearch(input.value);
    if (!input.value.trim()) {
      results.innerHTML = '<p class="search-hint">Search parties, elections, and archive descriptions. Manifesto full-text search coming soon.</p>';
      return;
    }
    if (!hits.length) {
      results.innerHTML = '<p class="search-empty">No results found.</p>';
      return;
    }
    results.innerHTML = hits.map(hit => `
      <a href="${hit.href}" class="search-result" data-close-search>
        <span class="search-result-dot" style="background:${hit.color}"></span>
        <span class="search-result-body">
          <span class="search-result-title">${hit.title}</span>
          <span class="search-result-sub">${hit.subtitle}</span>
          ${hit.snippet ? `<span class="search-result-snippet">${hit.snippet}</span>` : ''}
        </span>
        <span class="search-result-type">${hit.type}</span>
      </a>
    `).join('');

    results.querySelectorAll('[data-close-search]').forEach(a => {
      a.addEventListener('click', close);
    });
  });

  results.innerHTML = '<p class="search-hint">Search parties, elections, and archive descriptions. Manifesto full-text search coming soon.</p>';
}
