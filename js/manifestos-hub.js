/* ============================================================
   /manifesto — cover-led index of every folder in manifesto-assets.json
   Route-loaded. Does not load chamber modules.
   ============================================================ */

const MANIFESTO_BROWSE_PAGE_SIZE = 60;

const MANIFESTO_CHAMBERS = [
  { id: 'westminster', label: 'Westminster' },
  { id: 'euro',        label: 'European Parliament' },
  { id: 'stormont',    label: 'Northern Ireland Assembly' },
  { id: 'holyrood',    label: 'Scottish Parliament' },
  { id: 'london',      label: 'London Mayor & Assembly' },
  { id: 'senedd',      label: 'Welsh Parliament' },
];

const MANIFESTO_CHAMBER_SHORT = {
  westminster: 'Westminster',
  euro: 'European Parliament',
  stormont: 'Stormont',
  holyrood: 'Holyrood',
  london: 'London',
  senedd: 'Senedd',
};

const MANIFESTO_AVAILABILITY = [
  { id: 'text', label: 'Read online',  test: r => r.hasText },
  { id: 'pdf',  label: 'Original PDF', test: r => r.hasPdf },
];

const MANIFESTO_SORTS = [
  { id: 'year-desc', label: 'Year — newest first' },
  { id: 'year-asc',  label: 'Year — oldest first' },
  { id: 'party-asc', label: 'Party A–Z' },
];

let _manifestoBrowseRows = null;

function manifestoBrowseEscape(value) {
  if (typeof escapeHtmlText === 'function') return escapeHtmlText(value);
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function buildManifestoBrowseRows() {
  if (_manifestoBrowseRows) return _manifestoBrowseRows;

  const assets = typeof getManifestoAssetMap === 'function' ? getManifestoAssetMap() : {};
  const rows = [];

  Object.entries(assets).forEach(([key, flags]) => {
    const { electionId, partyId } = splitArchiveKey(key);
    if (!electionId || !partyId) return;

    const chamber = electionKindFromId(electionId);
    const year = electionYearFromId(electionId);
    const party = PARTIES[partyId] || {};
    const partyName = (typeof getPartyName === 'function')
      ? getPartyName(partyId, year)
      : (party.shortName || partyId);

    const distinctive = (typeof distinctiveManifestoTitle === 'function')
      ? distinctiveManifestoTitle(electionId, partyId)
      : '';
    const title = distinctive || conventionalManifestoTitle(partyName, year || electionId);

    rows.push({
      key,
      electionId,
      partyId,
      partyName,
      partySort: (party.shortName || partyName || partyId).toLowerCase(),
      colour: (typeof getPartyColor === 'function' ? getPartyColor(partyId, year) : party.color) || '#6b7280',
      chamber,
      chamberLabel: MANIFESTO_CHAMBER_SHORT[chamber] || chamber,
      year: year || 0,
      yearLabel: manifestoYearLabel(electionId, year),
      decade: year ? Math.floor(year / 10) * 10 : 0,
      title,
      distinctive: Boolean(distinctive),
      hasCover: Boolean(flags && flags.cover),
      hasPdf: Boolean(flags && flags.pdf),
      hasText: Boolean(flags && flags.md),
      url: `/manifesto/${electionId}/${partyId}`,
      search: `${title} ${partyName} ${partyId} ${year || ''} ${MANIFESTO_CHAMBER_SHORT[chamber] || ''}`.toLowerCase(),
    });
  });

  rows.sort(manifestoComparator('year-desc'));
  _manifestoBrowseRows = rows;
  return rows;
}

function manifestoYearLabel(electionId, year) {
  const id = String(electionId || '');
  if (/^feb1974/.test(id)) return 'Feb 1974';
  if (/^oct1974/.test(id)) return 'Oct 1974';
  return year ? String(year) : id;
}

function manifestoComparator(sort) {
  if (sort === 'year-asc') {
    return (a, b) => (a.year - b.year) || a.partySort.localeCompare(b.partySort, 'en-GB');
  }
  if (sort === 'party-asc') {
    return (a, b) => a.partySort.localeCompare(b.partySort, 'en-GB') || (b.year - a.year);
  }
  return (a, b) => (b.year - a.year) || a.partySort.localeCompare(b.partySort, 'en-GB');
}

function readManifestoBrowseFilters() {
  const params = new URLSearchParams(window.location.search);
  return {
    q: params.get('q') || '',
    chamber: params.get('chamber') || '',
    decade: params.get('decade') || '',
    year: params.get('year') || '',
    have: params.get('have') || '',
    party: params.get('party') || '',
    sort: params.get('sort') || '',
  };
}

function writeManifestoBrowseFilters(filters) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([k, v]) => { if (v) params.set(k, v); });
  const qs = params.toString();
  const next = qs ? `/manifesto?${qs}` : '/manifesto';
  if (`${window.location.pathname}${window.location.search}` !== next) {
    history.replaceState(null, '', next);
  }
}

function manifestoBrowseMatches(row, filters) {
  if (filters.chamber && row.chamber !== filters.chamber) return false;
  if (filters.decade && String(row.decade) !== String(filters.decade)) return false;
  if (filters.year && String(row.year) !== String(filters.year)) return false;
  if (filters.party && row.partyId !== filters.party) return false;
  if (filters.have) {
    const facet = MANIFESTO_AVAILABILITY.find(f => f.id === filters.have);
    if (facet && !facet.test(row)) return false;
  }
  const q = (filters.q || '').trim().toLowerCase();
  if (q && !row.search.includes(q)) return false;
  return true;
}

function manifestoDensityCaption(year, n) {
  const noun = n === 1 ? 'document' : 'documents';
  return `${year} · ${n} ${noun}`;
}

function manifestoDensityAxisHtml(first, last, span, plotW, pad, bw, BASE) {
  const xBar = y => pad + Math.round(((y - first) / span) * (plotW - bw));
  const xCenter = y => xBar(y) + bw / 2;
  const bits = [];
  const years = [first];
  const decade0 = Math.ceil((first + 1) / 10) * 10;
  for (let y = decade0; y < last; y += 10) years.push(y);
  years.push(last);
  years.forEach(y => {
    const x = xCenter(y);
    bits.push(`<line class="manifesto-density-tick" x1="${x}" y1="${BASE}" x2="${x}" y2="${BASE + 5}"></line>`);
    bits.push(`<text x="${x}" y="${BASE + 18}" text-anchor="middle">${y}</text>`);
  });
  return bits.join('');
}

function renderManifestoDensityHtml(rows, filters) {
  const scoped = rows.filter(r => (!filters.chamber || r.chamber === filters.chamber) && r.year);
  const byYear = new Map();
  scoped.forEach(r => byYear.set(r.year, (byYear.get(r.year) || 0) + 1));
  if (!byYear.size) return '';

  const years = [...byYear.keys()].sort((a, b) => a - b);
  const first = years[0];
  const last = years[years.length - 1];
  const max = Math.max(...byYear.values());

  const PLOT_W = 1072, PAD = 22, H = 132, BASE = 102, PLOT = 78;
  const span = Math.max(1, last - first);
  const slot = PLOT_W / (span + 1);
  const bw = Math.max(4, Math.min(26, slot - 3));
  const W = PLOT_W + PAD * 2;

  const selected = years.find(y => String(filters.year) === String(y));
  const idle = selected
    ? `${manifestoDensityCaption(selected, byYear.get(selected))}. Click the bar again to clear.`
    : `Documents held per year, ${first}–${last}. Hover a bar for the year, or click to filter.`;

  const bars = years.map(y => {
    const n = byYear.get(y);
    const h = Math.max(3, Math.round((n / max) * PLOT));
    const x = PAD + Math.round(((y - first) / span) * (PLOT_W - bw));
    const active = String(filters.year) === String(y);
    const labelY = Math.max(14, BASE - h - 8);
    const caption = manifestoDensityCaption(y, n);
    return `<g class="manifesto-density-bar${active ? ' is-active' : ''}" role="listitem">
      <rect x="${x}" y="${BASE - h}" width="${Math.round(bw)}" height="${h}" rx="2"></rect>
      <text class="manifesto-density-year" x="${Math.round(x + bw / 2)}" y="${labelY}" text-anchor="middle">${y}</text>
      <rect class="manifesto-density-hit" x="${x - 2}" y="0" width="${Math.round(bw) + 4}" height="${BASE}"
            data-browse-group="year" data-browse-value="${y}" data-caption="${manifestoBrowseEscape(caption)}"
            tabindex="0" role="button"
            aria-label="${n} manifesto${n === 1 ? '' : 's'} from ${y}" aria-pressed="${active ? 'true' : 'false'}"></rect>
    </g>`;
  }).join('');

  return `<section class="manifesto-density" aria-labelledby="manifesto-density-label">
    <div class="manifesto-density-head">
      <span class="parties-browse-label" id="manifesto-density-label">The archive over time</span>
      <p class="manifesto-density-note" id="manifesto-density-note" data-idle="${manifestoBrowseEscape(idle)}" aria-live="polite">${manifestoBrowseEscape(idle)}</p>
    </div>
    <svg class="manifesto-density-chart" viewBox="0 0 ${W} ${H}" role="list"
         aria-label="Documents held per year from ${first} to ${last} on a calendar scale, peaking at ${max} in one year">
      <line class="manifesto-density-axis" x1="0" y1="${BASE}" x2="${W}" y2="${BASE}"></line>
      ${bars}
      <g class="manifesto-density-ticks">${manifestoDensityAxisHtml(first, last, span, PLOT_W, PAD, bw, BASE)}</g>
    </svg>
  </section>`;
}

function manifestoFacetButton(group, value, label, count, active) {
  return `<button type="button" class="manifesto-facet${active ? ' is-active' : ''}"
    data-browse-group="${group}" data-browse-value="${manifestoBrowseEscape(value)}" aria-pressed="${active ? 'true' : 'false'}">
    <span class="manifesto-facet-label">${manifestoBrowseEscape(label)}</span>
    <span class="manifesto-facet-count">${count}</span>
  </button>`;
}

function renderManifestoBrowseFiltersHtml(rows, filters) {
  const countFor = (group, value) => {
    const probe = { ...filters, [group]: String(value) };
    return rows.reduce((n, r) => n + (manifestoBrowseMatches(r, probe) ? 1 : 0), 0);
  };

  const chamberButtons = MANIFESTO_CHAMBERS
    .map(c => manifestoFacetButton('chamber', c.id, c.label, countFor('chamber', c.id), filters.chamber === c.id))
    .join('');

  const haveButtons = MANIFESTO_AVAILABILITY
    .map(f => manifestoFacetButton('have', f.id, f.label, countFor('have', f.id), filters.have === f.id))
    .join('');

  const decades = [...new Set(rows.map(r => r.decade).filter(Boolean))].sort((a, b) => b - a);
  const decadeChips = decades.map(d => {
    const active = String(filters.decade) === String(d);
    return `<button type="button" class="filter-btn manifesto-decade-chip${active ? ' active' : ''}"
      data-browse-group="decade" data-browse-value="${d}" aria-pressed="${active ? 'true' : 'false'}">${d}s</button>`;
  }).join('');

  const partyCounts = new Map();
  rows.forEach(r => {
    if (!manifestoBrowseMatches(r, { ...filters, party: '' })) return;
    partyCounts.set(r.partyId, (partyCounts.get(r.partyId) || 0) + 1);
  });
  const topParties = [...partyCounts.entries()]
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], 'en-GB'))
    .slice(0, 12);

  const partyRows = topParties.map(([pid, n]) => {
    const active = filters.party === pid;
    const colour = (typeof getPartyColor === 'function' ? getPartyColor(pid) : (PARTIES[pid] || {}).color) || '#6b7280';
    const name = typeof getPartyName === 'function' ? getPartyName(pid) : ((PARTIES[pid] || {}).shortName || pid);
    const style = typeof dotStyle === 'function' ? dotStyle(colour) : `background:${colour}`;
    return `<button type="button" class="manifesto-party-row${active ? ' is-active' : ''}"
      data-browse-group="party" data-browse-value="${manifestoBrowseEscape(pid)}" aria-pressed="${active ? 'true' : 'false'}">
      <span class="mega-dot" style="${style}" aria-hidden="true"></span>
      <span class="manifesto-party-name">${manifestoBrowseEscape(name)}</span>
      <span class="manifesto-facet-count">${n}</span>
    </button>`;
  }).join('');

  return `<aside class="parties-browse-sidebar manifesto-browse-filters" id="manifesto-browse-filters" aria-label="Filter manifestos">
    <div class="parties-browse-row">
      <span class="parties-browse-label" id="manifesto-facet-chamber">Chamber</span>
      <div class="manifesto-facet-list" role="group" aria-labelledby="manifesto-facet-chamber">${chamberButtons}</div>
    </div>
    <div class="parties-browse-row">
      <span class="parties-browse-label" id="manifesto-facet-have">Available</span>
      <div class="manifesto-facet-list" role="group" aria-labelledby="manifesto-facet-have">${haveButtons}</div>
    </div>
    <div class="parties-browse-row">
      <span class="parties-browse-label" id="manifesto-facet-decade">Decade</span>
      <div class="manifesto-decade-list" role="group" aria-labelledby="manifesto-facet-decade">${decadeChips}</div>
    </div>
    <div class="parties-browse-row">
      <span class="parties-browse-label" id="manifesto-facet-party">Party</span>
      <div class="manifesto-party-list" role="group" aria-labelledby="manifesto-facet-party">${partyRows}</div>
      <a href="/party/all" class="manifesto-browse-hint">${nodeLabel('allParties')} →</a>
    </div>
  </aside>`;
}

function manifestoBrowseCoverUrls(row) {
  const base = `/manifestos/${row.electionId}/${row.partyId}`;
  if (row.chamber === 'euro') {
    return { src: `${base}/manifesto.png`, fallbackSrc: `${base}/cover.png` };
  }
  return { src: `${base}/cover.png`, fallbackSrc: `${base}/cover.jpg` };
}

function manifestoBrowseTileHtml(row, eager) {
  const theme = typeof getCurrentTheme === 'function' ? getCurrentTheme() : 'dark';
  const accent = typeof partyAccentDerived === 'function'
    ? partyAccentDerived(row.partyId, theme)
    : { kicker: row.colour, surface: row.colour, raw: row.colour };
  const ghost = typeof ghostTint === 'function'
    ? ghostTint(accent.raw || row.colour, theme)
    : accent.surface;

  const badges = [];
  if (row.hasText) badges.push('Read online');
  if (row.hasPdf) badges.push('PDF');

  const cover = manifestoBrowseCoverUrls(row);

  const shot = row.hasCover && typeof coverPictureHtml === 'function'
    ? coverPictureHtml({
        src: cover.src,
        fallbackSrc: cover.fallbackSrc,
        alt: `Cover of ${row.title}`,
        className: eager ? '' : 'img-lazy',
        loading: eager ? 'eager' : 'lazy',
        fetchpriority: eager ? 'high' : undefined,
        sizes: '(max-width: 560px) 44vw, (max-width: 1000px) 30vw, 176px',
      }) + `<div class="manifesto-browse-gap" style="display:none" aria-hidden="true"><span class="manifesto-browse-gap-label">No cover scan</span></div>`
    : `<div class="manifesto-browse-gap">
         <span class="manifesto-browse-gap-label">No cover scan</span>
       </div>`;

  return `<li class="manifesto-browse-item">
    <article class="manifesto-browse-tile" style="--party-color:${accent.surface};--party-ghost:${ghost}">
      <a class="manifesto-browse-link" href="${row.url}">
        <span class="manifesto-browse-shot${row.hasCover ? '' : ' is-gap'}">${shot}</span>
        <span class="manifesto-browse-party" style="color:${accent.kicker}">
          <span class="mega-dot" style="${typeof dotStyle === 'function' ? dotStyle(row.colour) : `background:${row.colour}`}" aria-hidden="true"></span>
          ${manifestoBrowseEscape(row.partyName)}
        </span>
        <span class="manifesto-browse-title">${manifestoBrowseEscape(row.title)}</span>
        <span class="manifesto-browse-meta">
          <time datetime="${row.year || ''}">${manifestoBrowseEscape(row.yearLabel)}</time>
          <span aria-hidden="true">·</span>
          <span>${manifestoBrowseEscape(row.chamberLabel)}</span>
        </span>
      </a>
      ${badges.length ? `<ul class="manifesto-browse-badges">${badges.map(b => `<li>${b}</li>`).join('')}</ul>` : ''}
    </article>
  </li>`;
}

function renderManifestosHub(app) {
  const label = nodeLabel('manifestos');
  setPageMeta({
    title: label,
    description:
      'Every manifesto document in The British Manifesto Archive — Westminster, Holyrood, the Senedd, Stormont, London and the European Parliament. Filter by chamber, decade, party, or what is available to read.',
    path: '/manifesto',
  });

  const rows = buildManifestoBrowseRows();
  const filters = readManifestoBrowseFilters();
  const q = typeof escapeAttr === 'function' ? escapeAttr(filters.q || '') : manifestoBrowseEscape(filters.q || '');

  app.innerHTML = `
    ${renderBreadcrumb([
      { label: nodeLabel('home'), href: '/' },
      { label },
    ])}
    <div class="hub-page manifesto-browse-page">
      <header class="parties-browse-hero">
        <div class="parties-browse-hero-copy">
          <span class="section-label" id="manifesto-browse-count">${rows.length} documents</span>
          <h1>${label}</h1>
          <div class="gold-rule"></div>
          <p>The document shelf for the archive — Westminster, Holyrood, the Senedd, Stormont, London, and the European Parliament. For a single contest, start with <a href="/election">${nodeLabel('elections')}</a>.</p>
        </div>
      </header>

      <div id="manifesto-density-mount">${renderManifestoDensityHtml(rows, filters)}</div>

      <div class="parties-browse-layout manifesto-browse-layout">
        ${renderManifestoBrowseFiltersHtml(rows, filters)}
        <div class="parties-browse-main">
          <div class="manifesto-results-bar">
            <p class="manifesto-results-count" id="manifesto-results-count" aria-live="polite"></p>
            <div class="manifesto-results-tools">
              <label class="manifesto-filter">
                <span class="sr-only">Filter this list by title, party, or year</span>
                <input type="search" id="manifesto-browse-q" value="${q}" placeholder="Filter titles, parties, years" autocomplete="off" spellcheck="false">
              </label>
              <label class="manifesto-sort">
                <span class="sr-only">Sort manifestos</span>
                <select id="manifesto-sort">
                  ${MANIFESTO_SORTS.map(s =>
                    `<option value="${s.id}"${(filters.sort || 'year-desc') === s.id ? ' selected' : ''}>${s.label}</option>`
                  ).join('')}
                </select>
              </label>
            </div>
          </div>
          <p class="manifesto-filter-hint">This filters the covers. To look inside transcriptions, use <a href="/search">Search</a>.</p>
          <div id="manifesto-results" class="manifesto-results"></div>
        </div>
      </div>
    </div>
  `;

  setupManifestoBrowse(app, rows);
}

function setupManifestoBrowse(app, rows) {
  const hub = app.querySelector('.hub-page');
  if (!hub) return;

  let filters = readManifestoBrowseFilters();
  let shownCount = MANIFESTO_BROWSE_PAGE_SIZE;

  const activeFilterCount = () =>
    ['chamber', 'decade', 'year', 'have', 'party', 'q'].filter(k => filters[k]).length;

  const syncClearButton = () => {
    const aside = hub.querySelector('#manifesto-browse-filters');
    if (!aside) return;
    const show = activeFilterCount() > 0;
    let clearEl = aside.querySelector('.parties-browse-clear');
    if (show && !clearEl) {
      clearEl = document.createElement('p');
      clearEl.className = 'parties-browse-clear';
      clearEl.innerHTML = '<button type="button" class="parties-browse-clear-btn" data-browse-clear>Clear filters</button>';
      aside.appendChild(clearEl);
    } else if (!show && clearEl) {
      clearEl.remove();
    }
  };

  const renderResults = () => {
    const listEl = hub.querySelector('#manifesto-results');
    const countEl = hub.querySelector('#manifesto-results-count');
    const heroCountEl = hub.querySelector('#manifesto-browse-count');
    const densityMount = hub.querySelector('#manifesto-density-mount');

    const matched = rows
      .filter(r => manifestoBrowseMatches(r, filters))
      .sort(manifestoComparator(filters.sort || 'year-desc'));

    if (densityMount) densityMount.innerHTML = renderManifestoDensityHtml(rows, filters);

    if (listEl) {
      if (!matched.length) {
        listEl.innerHTML = `<p class="parties-browse-empty">No documents match these filters.
          <button type="button" class="parties-browse-clear-btn" data-browse-clear>Clear filters</button></p>`;
      } else {
        const shown = matched.slice(0, shownCount);
        const more = matched.length - shown.length;
        listEl.innerHTML = `<ul class="manifesto-browse-grid" role="list">${shown.map((row, i) => manifestoBrowseTileHtml(row, i < 4)).join('')}</ul>`
          + (more > 0
            ? `<div class="manifesto-more">
                 <p class="manifesto-more-count">Showing ${shown.length} of ${matched.length}</p>
                 <button type="button" class="manifesto-more-btn" data-browse-more>Load ${Math.min(more, MANIFESTO_BROWSE_PAGE_SIZE)} more</button>
               </div>`
            : '');
      }
      if (typeof initLazyImages === 'function') initLazyImages(listEl);
    }

    if (countEl) {
      countEl.textContent = matched.length === rows.length
        ? `${rows.length} documents`
        : `${matched.length} of ${rows.length} documents`;
    }
    if (heroCountEl) {
      heroCountEl.textContent = matched.length === rows.length
        ? `${rows.length} documents`
        : `${matched.length} of ${rows.length} documents`;
    }

    syncClearButton();
    writeManifestoBrowseFilters(filters);
  };

  const render = ({ skipFilters = false, resetPage = true } = {}) => {
    if (resetPage) shownCount = MANIFESTO_BROWSE_PAGE_SIZE;
    const filtersMount = hub.querySelector('#manifesto-browse-filters');
    const searchInput = hub.querySelector('#manifesto-browse-q');
    if (!skipFilters && filtersMount) {
      filtersMount.outerHTML = renderManifestoBrowseFiltersHtml(rows, filters);
    }
    if (searchInput && searchInput.value !== (filters.q || '')) {
      searchInput.value = filters.q || '';
    }
    if (!skipFilters) {
      const densityMount = hub.querySelector('#manifesto-density-mount');
      if (densityMount) densityMount.innerHTML = renderManifestoDensityHtml(rows, filters);
    }
    renderResults();
  };

  if (hub.dataset.manifestoBrowseBound !== '1') {
    hub.dataset.manifestoBrowseBound = '1';

    hub.addEventListener('click', e => {
      if (e.target.closest('[data-browse-clear]')) {
        filters = { q: '', chamber: '', decade: '', year: '', have: '', party: '', sort: filters.sort };
        render();
        hub.querySelector('#manifesto-browse-q')?.focus();
        return;
      }
      if (e.target.closest('[data-browse-more]')) {
        shownCount += MANIFESTO_BROWSE_PAGE_SIZE;
        render({ skipFilters: true, resetPage: false });
        return;
      }
      const btn = e.target.closest('[data-browse-group]');
      if (!btn || !hub.contains(btn)) return;
      const group = btn.getAttribute('data-browse-group');
      const value = btn.getAttribute('data-browse-value') || '';
      const next = value === '' ? '' : (String(filters[group]) === value ? '' : value);
      if (group === 'year') filters = { ...filters, year: next, decade: '' };
      else if (group === 'decade') filters = { ...filters, decade: next, year: '' };
      else filters = { ...filters, [group]: next };
      render();
    });

    const densityNote = (text) => {
      const note = hub.querySelector('#manifesto-density-note');
      if (note) note.textContent = text;
    };
    const densityIdle = () => {
      const note = hub.querySelector('#manifesto-density-note');
      if (note) note.textContent = note.dataset.idle || '';
    };
    hub.addEventListener('pointerover', e => {
      const hit = e.target.closest?.('.manifesto-density-hit');
      if (!hit || !hub.contains(hit)) return;
      densityNote(hit.getAttribute('data-caption') || hit.getAttribute('aria-label') || '');
    });
    hub.addEventListener('pointerout', e => {
      const hit = e.target.closest?.('.manifesto-density-hit');
      if (!hit) return;
      const next = e.relatedTarget && typeof e.relatedTarget.closest === 'function'
        ? e.relatedTarget.closest('.manifesto-density-hit')
        : null;
      if (next && hub.contains(next)) return;
      densityIdle();
    });
    hub.addEventListener('focusin', e => {
      const hit = e.target.closest?.('.manifesto-density-hit');
      if (!hit || !hub.contains(hit)) return;
      densityNote(hit.getAttribute('data-caption') || hit.getAttribute('aria-label') || '');
    }, true);
    hub.addEventListener('focusout', e => {
      const hit = e.target.closest?.('.manifesto-density-hit');
      if (!hit) return;
      const next = e.relatedTarget && typeof e.relatedTarget.closest === 'function'
        ? e.relatedTarget.closest('.manifesto-density-hit')
        : null;
      if (next && hub.contains(next)) return;
      densityIdle();
    }, true);

    hub.addEventListener('keydown', e => {
      if (e.key !== 'Enter' && e.key !== ' ') return;
      const hit = e.target.closest?.('.manifesto-density-hit');
      if (!hit) return;
      e.preventDefault();
      hit.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    });

    hub.addEventListener('input', e => {
      if (e.target.id !== 'manifesto-browse-q') return;
      const value = e.target.value.trim();
      clearTimeout(hub._manifestoSearchTimer);
      hub._manifestoSearchTimer = setTimeout(() => {
        filters = { ...filters, q: value };
        render({ skipFilters: true });
      }, value ? 180 : 0);
    });

    hub.addEventListener('change', e => {
      if (e.target.id !== 'manifesto-sort') return;
      filters = { ...filters, sort: e.target.value === 'year-desc' ? '' : e.target.value };
      render({ skipFilters: true });
    });
  }

  renderResults();
}

window.renderManifestosHub = renderManifestosHub;
