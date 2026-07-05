/* ============================================================
   THE BRITISH MANIFESTO ARCHIVE — London elections
   London County Council (1946–61), Greater London Council
   (1964–85), and Greater London Authority (2000–) elections.
   ============================================================ */

const LONDON_BODY_LABELS = {
  lcc: 'London County Council',
  glc: 'Greater London Council',
  gla: 'Greater London Authority',
};

let _londonIndex = null;

async function loadLondonIndex() {
  if (_londonIndex) return _londonIndex;
  try {
    _londonIndex = await fetchTyped('/data/devolved/london/index.json', 'json');
  } catch {
    _londonIndex = [];
  }
  return _londonIndex;
}

async function loadLondonElection(id) {
  try {
    return await fetchTyped(`/data/devolved/london/${id}.json`, 'json');
  } catch {
    return null;
  }
}

function londonNum(n) {
  return typeof n === 'number' ? n.toLocaleString('en-GB') : '—';
}

function londonPartyColor(id) {
  return (id && typeof getPartyColor === 'function') ? getPartyColor(id) : '#6b7280';
}

/** Display name for a London candidate/result row (party id or free-text label). */
function londonPartyName(row, year) {
  if (row.partyLabel) return row.partyLabel;
  if (row.party && typeof PARTIES !== 'undefined' && PARTIES[row.party]) {
    return getPartyName(row.party, year);
  }
  return row.name || row.party || '—';
}

function londonPartyCell(row, year) {
  const color = londonPartyColor(row.party);
  const name = londonPartyName(row, year);
  const inner = (row.party && PARTIES?.[row.party])
    ? `<a href="/party/${row.party}" class="inline-party-link">${name}</a>`
    : name;
  return `<div class="result-party-name"><div class="result-party-swatch" style="background:${color}"></div>${inner}</div>`;
}

// ── BOOKLET PROMO BOX (London Elects, 2004+) ──────────────────
function londonBookletBox(booklet) {
  if (!booklet || !booklet.pdf) return '';
  return `
    <section class="london-booklet" aria-label="Official candidate booklet">
      <a class="london-booklet-cover" href="${booklet.pdf}" target="_blank" rel="noopener">
        <img src="${booklet.cover}?v=${ASSETS_VERSION}" alt="Front cover of the ${booklet.title}" loading="lazy" decoding="async">
      </a>
      <div class="london-booklet-body">
        <span class="section-label">London Elects</span>
        <h2>${booklet.title}</h2>
        <p>Ahead of every mayoral and Assembly election since 2004, London Elects has posted an official booklet to every London household. It explains how the elections work and how to vote, and carries an election address written by each candidate for Mayor.</p>
        <a class="london-booklet-btn" href="${booklet.pdf}" target="_blank" rel="noopener">↓ Open the candidate booklet (PDF)</a>
      </div>
    </section>`;
}

// ── MANIFESTO CARDS (London, PDF-first) ───────────────────────
function londonManifestoCard(m, year) {
  const color = londonPartyColor(m.party);
  const partyName = londonPartyName(m, year);
  const heading = m.candidate || partyName;
  const pdfSize = (typeof window.getPdfSize === 'function' && m.pdf) ? window.getPdfSize(m.pdf) : '';
  const pdfSizeLabel = pdfSize ? ` · ${pdfSize}` : '';
  return `
    <div class="manifesto-card" style="--party-color:${color};--party-dim:rgba(0,0,0,0.04)">
      <a href="${m.pdf}" class="manifesto-thumb" target="_blank" rel="noopener" aria-label="Open the ${heading} manifesto PDF">
        <img src="${m.cover}?v=${ASSETS_VERSION}" alt="${heading} manifesto cover"
          class="img-lazy" loading="lazy" decoding="async"
          onerror="this.style.display='none';this.nextElementSibling.style.display='flex';">
        <div class="manifesto-thumb-placeholder" style="display:none">
          <svg viewBox="0 0 48 64" fill="none" xmlns="http://www.w3.org/2000/svg" class="thumb-doc-icon">
            <rect x="12" y="10" width="32" height="44" rx="2" fill="currentColor" opacity="0.9"/>
          </svg>
          <span class="thumb-year">${year}</span>
        </div>
      </a>
      <div class="manifesto-card-header">
        <div class="manifesto-party-dot" style="background:${color}"></div>
        <div class="manifesto-party-name">${heading}</div>
        ${m.party && PARTIES?.[m.party] ? `<div class="manifesto-party-tag">${partyName}</div>` : ''}
      </div>
      <div class="manifesto-card-body">
        ${m.title ? `<p class="london-manifesto-title">${m.title}</p>` : ''}
        <a href="${m.pdf}" class="manifesto-link" target="_blank" rel="noopener">
          <span class="manifesto-link-icon">📄</span>
          <div class="manifesto-link-info"><div class="manifesto-link-title">Manifesto</div><div class="manifesto-link-sub">PDF document${pdfSizeLabel}</div></div>
        </a>
      </div>
    </div>`;
}

// ── MAYORAL RESULTS TABLE (GLA) ───────────────────────────────
function londonMayorSection(election) {
  const m = election.mayor;
  if (!m || !Array.isArray(m.candidates)) return '';
  const first = c => (typeof c.firstVotes === 'number' ? c.firstVotes : c.votes) || 0;
  const firstP = c => (typeof c.firstPct === 'number' ? c.firstPct : c.pct);
  const isSV = m.candidates.some(c => typeof c.finalVotes === 'number');
  const maxVotes = Math.max(...m.candidates.map(first), 1);
  const rows = m.candidates.map(c => {
    const color = londonPartyColor(c.party);
    const fp = firstP(c);
    const pct = typeof fp === 'number' ? fp.toFixed(1) + '%' : '—';
    const runoff = isSV
      ? `<td style="color:var(--cream);text-align:right">${typeof c.finalVotes === 'number' ? londonNum(c.finalVotes) : '<span style="color:var(--text-faint)">—</span>'}</td>
         <td style="color:var(--text-muted)">${typeof c.finalPct === 'number' ? c.finalPct.toFixed(1) + '%' : ''}</td>`
      : '';
    const nameCell = c.party === undefined && !c.partyLabel
      ? `<div class="result-party-name"><div class="result-party-swatch" style="background:${color}"></div>${c.name}</div>`
      : `${londonPartyCell(c, election.year)}${c.name ? `<div class="london-cand-name">${c.name}</div>` : ''}`;
    return `<tr${c.elected ? ' class="london-row-winner"' : ''}>
      <td>${nameCell}</td>
      <td><div class="result-seats-bar-wrap"><div class="result-seats-bar"><div class="result-seats-fill" style="width:${(first(c) / maxVotes * 100).toFixed(1)}%;background:${color}"></div></div><strong style="color:var(--cream);min-width:64px">${londonNum(first(c))}</strong></div></td>
      <td style="color:var(--text-muted)">${pct}</td>
      ${runoff}
      <td>${c.elected ? '<span class="majority-badge">✦ Elected</span>' : ''}</td>
    </tr>`;
  }).join('');
  const runoffHead = isSV ? '<th style="text-align:right">Run-off</th><th>%</th>' : '';
  return `
    <div class="results-section">
      <span class="section-label">Mayor of London · ${m.system || 'First-past-the-post'}</span>
      <h2>Mayoral Result</h2>
      <table class="results-table london-mayor-table">
        <thead><tr><th>Candidate</th><th>${isSV ? 'First round' : 'Votes'}</th><th>%</th>${runoffHead}<th></th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
      ${isSV ? '<p style="font-size:0.75rem;color:var(--text-faint);margin-top:0.5rem">Under the Supplementary Vote, the top two candidates went to a run-off in which second preferences for eliminated candidates were redistributed.</p>' : ''}
      ${m.systemNote ? `<p style="font-size:0.75rem;color:var(--text-faint);margin-top:0.4rem">${m.systemNote}</p>` : ''}
    </div>`;
}

// ── ASSEMBLY RESULTS TABLE (GLA) ──────────────────────────────
function londonAssemblySection(election) {
  const a = election.assembly;
  if (!a || !Array.isArray(a.results)) return '';
  const rows = a.results.slice().sort((x, y) => y.seats - x.seats).map(r => {
    const color = londonPartyColor(r.party);
    const listPct = typeof r.listPct === 'number' ? r.listPct.toFixed(1) + '%' : '—';
    return `<tr>
      <td>${londonPartyCell(r, election.year)}</td>
      <td style="color:var(--text-muted);text-align:center">${r.constituencySeats}</td>
      <td style="color:var(--text-muted);text-align:center">${r.listSeats}</td>
      <td><strong style="color:var(--cream)">${r.seats}</strong></td>
      <td style="color:var(--text-muted)">${listPct}</td>
    </tr>`;
  }).join('');
  const others = (a.otherListVotes || []).length
    ? `<details class="london-others"><summary>Other parties on the London-wide list (no seats)</summary>
        <table class="results-table"><thead><tr><th>Party</th><th>List votes</th><th>%</th></tr></thead>
        <tbody>${a.otherListVotes.map(o => `<tr><td>${o.name}</td><td style="color:var(--text-muted)">${londonNum(o.votes)}</td><td style="color:var(--text-muted)">${typeof o.pct === 'number' ? o.pct.toFixed(1) + '%' : '—'}</td></tr>`).join('')}</tbody></table>
      </details>`
    : '';
  return `
    <div class="results-section">
      <span class="section-label">London Assembly · ${a.system || 'Additional Member System'}</span>
      <h2>Assembly Result</h2>
      <table class="results-table london-assembly-table">
        <thead><tr><th>Party</th><th title="Constituency seats" style="text-align:center">Const.</th><th title="London-wide list seats" style="text-align:center">List</th><th>Seats (of ${a.totalSeats})</th><th>List vote %</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
      <p style="font-size:0.75rem;color:var(--text-faint);margin-top:0.75rem">${a.constituencySeats || 14} constituency members elected by first-past-the-post and ${a.listSeats || 11} London-wide members allocated by party-list vote (modified d'Hondt).</p>
      ${others}
    </div>`;
}

// ── COUNCIL RESULTS TABLE (LCC / GLC) ─────────────────────────
function londonCouncilSection(election) {
  const c = election.council;
  if (!c || !Array.isArray(c.results)) return '';
  const maxSeats = Math.max(...c.results.map(r => r.seats || 0), 1);
  const rows = c.results.slice().sort((x, y) => y.seats - x.seats).map(r => {
    const color = londonPartyColor(r.party);
    const isWinner = r.party === election.control;
    const pct = typeof r.pct === 'number' ? r.pct.toFixed(1) + '%' : '—';
    return `<tr>
      <td>${londonPartyCell(r, election.year)}${isWinner ? ' <span class="majority-badge">✦ Control</span>' : ''}</td>
      <td><div class="result-seats-bar-wrap"><div class="result-seats-bar"><div class="result-seats-fill" style="width:${((r.seats || 0) / maxSeats * 100).toFixed(1)}%;background:${color}"></div></div><strong style="color:var(--cream);min-width:32px">${r.seats}</strong></div></td>
      <td style="color:var(--text-muted)">${pct}</td>
    </tr>`;
  }).join('');
  return `
    <div class="results-section">
      <span class="section-label">${LONDON_BODY_LABELS[election.body] || 'Council'}</span>
      <h2>Council Composition</h2>
      <table class="results-table">
        <thead><tr><th>Party</th><th>Councillors (of ${c.totalSeats})</th><th>Vote %</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
      ${c.note ? `<p style="font-size:0.75rem;color:var(--text-faint);margin-top:0.75rem">${c.note}</p>` : ''}
    </div>`;
}

// ── LONDON ELECTION PAGE ──────────────────────────────────────
async function renderLondonElection(app, id) {
  setPageMeta({ title: 'London election', description: 'London election results.', path: `/devolved/london/${id}` });
  app.innerHTML = `<div class="election-body"><div class="manifesto-skeleton" role="status" aria-label="Loading"><div class="skeleton-line skeleton-title"></div><div class="skeleton-line"></div><div class="skeleton-line w-60"></div></div></div>`;

  const [election, index] = await Promise.all([loadLondonElection(id), loadLondonIndex()]);
  if (!election) { renderNotFound(app); return; }

  const bodyLabel = LONDON_BODY_LABELS[election.body] || 'London';
  const winnerId = election.mayorWinner || election.control;
  const winner = (winnerId && PARTIES?.[winnerId]) ? PARTIES[winnerId] : {};
  const color = winner.color || 'var(--gold)';
  const dim = winner.dim || 'var(--gold-dim)';
  const winnerName = election.mayorWinnerName || election.winnerName || '';

  setPageMeta({
    title: `${election.displayYear} ${DEVOLVED_PORTALS?.london?.label || 'London'} Election`,
    description: devolvedElectionDescription('london', election.displayYear, DEVOLVED_PORTALS?.london),
    path: `/devolved/london/${id}`,
  });

  // Prev/next within the same era, ordered by year
  const sorted = [...index].sort((a, b) => a.year - b.year);
  const pos = sorted.findIndex(e => e.id === id);
  const prev = pos > 0 ? sorted[pos - 1] : null;
  const next = pos >= 0 && pos < sorted.length - 1 ? sorted[pos + 1] : null;

  const summaryParas = (election.summary || '').split('\n\n').map(p => `<p>${p.trim()}</p>`).join('');
  const highlightItems = (election.highlights || []).map(h => `<div class="highlight-item"><div class="highlight-marker"></div><span>${h}</span></div>`).join('');

  const winnerBadge = winnerName
    ? `<div class="election-winner-badge" style="--party-color:${color};--party-dim:${dim}"><div class="winner-dot"></div>${election.mayorWinner ? `${winnerName} — Mayor of London` : `${winner.shortName || winnerName} control`}</div>`
    : '';

  const manifestosSection = (election.manifestos || []).length
    ? `<div class="manifestos-section">
        <span class="section-label">Candidate Manifestos</span>
        <h2>Documents</h2>
        <p class="manifestos-intro">The principal manifesto published by each major party or mayoral candidate.</p>
        <div class="manifesto-grid">${election.manifestos.map(m => londonManifestoCard(m, election.year)).join('')}</div>
      </div>`
    : '';

  const sources = (election.sources || []).length
    ? `<div class="london-sources"><span class="section-label">Sources</span><ul>${election.sources.map(s => `<li><a href="${s.url}" target="_blank" rel="noopener">${s.label}</a></li>`).join('')}</ul></div>`
    : '';

  const hasChart = (election.assembly?.results?.length) || (election.council?.results?.length);
  const chartResults = election.assembly?.results || election.council?.results || [];
  const chartTotal = election.assembly?.totalSeats || election.council?.totalSeats || 0;
  const chartTitle = election.assembly ? 'London Assembly' : bodyLabel;

  app.innerHTML = `
    ${renderBreadcrumb([
      { label: 'Home', href: '/' },
      { label: 'Beyond Westminster', href: '/devolved' },
      { label: 'London Mayor & Assembly', href: '/devolved/london' },
      { label: election.displayYear },
    ])}
    <section class="election-hero" style="--party-glow:${dim}">
      <div class="election-hero-bg"></div>
      <div class="election-hero-inner">
        <div>
          <div class="election-eyebrow">${bodyLabel}</div>
          <h1 class="election-title">${election.displayYear}</h1>
          <div class="election-date">${election.date}</div>
          ${winnerBadge}
        </div>
        <div class="election-nav-btns">
          ${prev ? `<a class="election-nav-btn" href="/devolved/london/${prev.id}">← ${prev.displayYear}</a>` : ''}
          ${next ? `<a class="election-nav-btn" href="/devolved/london/${next.id}">${next.displayYear} →</a>` : ''}
        </div>
      </div>
    </section>

    <div class="election-body">
      ${londonBookletBox(election.booklet)}

      <div class="election-grid">
        <div>
          ${summaryParas ? `<span class="section-label">Election Summary</span><div class="election-summary">${summaryParas}</div>` : ''}
          ${highlightItems ? `<div class="highlights-list"><h3>Key Moments</h3>${highlightItems}</div>` : ''}
          ${londonMayorSection(election)}
          ${londonAssemblySection(election)}
          ${londonCouncilSection(election)}
        </div>
        <div>
          ${hasChart ? `<div class="viz-panel">
            <div class="parliament-card viz-card">
              <div class="parliament-card-title">${chartTitle}</div>
              <div class="parliament-card-sub">${chartTotal} seats</div>
              <div id="london-chart-container"></div>
              <div class="parliament-legend" id="london-chart-legend"></div>
            </div>
          </div>` : ''}
        </div>
      </div>

      ${manifestosSection}
      ${sources}
    </div>
  `;

  if (hasChart) {
    requestAnimationFrame(() => {
      const cont = document.getElementById('london-chart-container');
      const leg = document.getElementById('london-chart-legend');
      if (cont) drawParliamentChart(cont, chartResults, chartTotal);
      if (leg) buildParliamentLegend(leg, chartResults, election.year);
    });
  }
}

// ── LONDON PORTAL (timeline of all London elections) ──────────
async function renderLondonPortal(app) {
  const portal = (typeof DEVOLVED_PORTALS !== 'undefined') ? DEVOLVED_PORTALS.london : null;
  setPageMeta({
    title: `${portal?.label || 'London Mayor & Assembly'} Elections`,
    description: `Election results and party manifestos for the ${portal?.label || 'London Mayor & Assembly'}.`,
    path: '/devolved/london',
  });

  const index = await loadLondonIndex();
  const byEra = { lcc: [], glc: [], gla: [] };
  index.forEach(e => { (byEra[e.body] || (byEra[e.body] = [])).push(e); });

  const eraBlock = (key, title, blurb) => {
    const items = (byEra[key] || []).slice().sort((a, b) => b.year - a.year);
    if (!items.length) return '';
    const cards = items.map(e => {
      const w = (e.mayorWinner && PARTIES?.[e.mayorWinner]) ? PARTIES[e.mayorWinner]
              : (e.control && PARTIES?.[e.control]) ? PARTIES[e.control] : null;
      const cColor = w?.color || 'var(--gold)';
      const sub = e.winnerName
        ? (e.mayorWinner ? `${e.winnerName} (Mayor)` : `${e.winnerName}`)
        : (e.title || '');
      return `<a href="/devolved/london/${e.id}" class="london-timeline-card" style="--party-color:${cColor}">
        <div class="london-timeline-year">${e.displayYear}</div>
        <div class="london-timeline-meta"><div class="london-timeline-title">${e.title || ''}</div><div class="london-timeline-sub">${sub}</div></div>
      </a>`;
    }).join('');
    return `<div class="london-era">
      <div class="london-era-head"><h2>${title}</h2><p>${blurb}</p></div>
      <div class="london-timeline-grid">${cards}</div>
    </div>`;
  };

  app.innerHTML = `
    ${renderBreadcrumb([
      { label: 'Home', href: '/' },
      { label: 'Beyond Westminster', href: '/devolved' },
      { label: 'London Mayor & Assembly' },
    ])}
    <section class="devolved-hero">
      <div class="devolved-hero-inner">
        <div>
          <span class="section-label">${portal?.subtitle || 'City Hall'}</span>
          <h1 class="devolved-hero-title">London Mayor &amp; Assembly</h1>
          <div class="gold-rule"></div>
          <p class="devolved-hero-desc">London has been governed by a directly elected, London-wide body since 1889 — the London County Council, then the Greater London Council, and, since 2000, the Greater London Authority comprising an elected Mayor and 25-member Assembly.</p>
        </div>
      </div>
    </section>
    <div class="devolved-body">
      ${eraBlock('gla', 'Greater London Authority (2000–)', 'Mayor of London and the 25-member London Assembly, elected every four years.')}
      ${eraBlock('glc', 'Greater London Council (1964–1986)', 'London-wide council abolished by the Local Government Act 1985.')}
      ${eraBlock('lcc', 'London County Council (1889–1965)', 'The first directly elected authority for London; post-war elections from 1946.')}
    </div>
  `;
}
