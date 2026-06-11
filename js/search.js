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
        body: `${e.summary || ''} ${(e.highlights || []).join(' ')}`,
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

  return items;
}

let _searchItems = null;
let _searchLastToggle = null;

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
    input.value = '';
    results.innerHTML = '<p class="search-hint" id="search-status">Search parties, elections, and archive descriptions.</p>';
    activeResultIndex = -1;
    setTimeout(() => input.focus(), 50);
  };

  const close = () => {
    overlay.classList.remove('is-open');
    overlay.setAttribute('aria-hidden', 'true');
    overlay.inert = true;
    panel.removeAttribute('aria-modal');
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

  input.addEventListener('input', () => {
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

  overlay.inert = true;
  results.innerHTML = '<p class="search-hint">Search parties, elections, and archive descriptions.</p>';
}
