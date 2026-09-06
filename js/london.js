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
    return _londonIndex;
  } catch {
    return null;
  }
}

async function loadLondonElection(id) {
  try {
    return await fetchTyped(`/data/devolved/london/${id}.json`, 'json');
  } catch {
    return null;
  }
}

/** Load London Assembly HexJSON (GLA constituency map). */
const _londonHexCache = new Map();
async function loadLondonHexLayout(year) {
  if (_londonHexCache.has(year)) return _londonHexCache.get(year);
  try {
    const res = await fetch(`/data/hex/london/${year}.hexjson?v=${ASSETS_VERSION}`, { cache: 'no-cache' });
    if (!res.ok) return null;
    const data = await res.json();
    _londonHexCache.set(year, data);
    return data;
  } catch (_) {
    return null;
  }
}

/** Load Greater London Council HexJSON (borough or single-member divisions). */
const _glcHexCache = new Map();
async function loadGlcHexLayout(year) {
  if (_glcHexCache.has(year)) return _glcHexCache.get(year);
  try {
    const res = await fetch(`/data/hex/glc/${year}.hexjson?v=${ASSETS_VERSION}`, { cache: 'no-cache' });
    if (!res.ok) return null;
    const data = await res.json();
    _glcHexCache.set(year, data);
    return data;
  } catch (_) {
    return null;
  }
}

/** Side panel for the 11 London-wide list Assembly members. */
function renderLondonListPanel(panelEl, regionalList, electionYear) {
  if (!panelEl || !Array.isArray(regionalList) || regionalList.length === 0) return;

  panelEl.innerHTML = '';
  panelEl.hidden = false;

  const heading = document.createElement('div');
  heading.className = 'hexmap-outside-heading';
  heading.textContent = 'London-wide List Seats';
  panelEl.appendChild(heading);

  const note = document.createElement('p');
  note.className = 'hexmap-outside-note';
  note.textContent = 'These 11 additional members are elected from a closed London-wide party list (d\'Hondt), topping up the 14 constituency seats.';
  panelEl.appendChild(note);

  const rowsWrap = document.createElement('div');
  rowsWrap.className = 'hexmap-outside-rows';

  regionalList.forEach(reg => {
    const row = document.createElement('div');
    row.className = 'hexmap-outside-row';

    const label = document.createElement('div');
    label.className = 'hexmap-outside-name';
    label.textContent = reg.region;
    row.appendChild(label);

    const swatches = document.createElement('div');
    swatches.className = 'hexmap-outside-swatches';

    (reg.members || []).forEach(member => {
      const sw = document.createElement('span');
      sw.className = 'hexmap-outside-swatch';
      const colour = londonPartyColor(member.party);
      sw.style.background = colour || '#CCCCCC';
      const partyLabel = getPartyName(member.party, electionYear);
      sw.title = `${member.name} (${partyLabel})`;
      sw.setAttribute('aria-label', `${reg.region}: ${member.name}, ${partyLabel}`);
      swatches.appendChild(sw);
    });

    row.appendChild(swatches);
    rowsWrap.appendChild(row);
  });

  panelEl.appendChild(rowsWrap);
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
  const partyId = row.party ? resolvePartyId(row.party) : null;
  const color = londonPartyColor(partyId || row.party);
  const name = londonPartyName(row, year);
  // Link when the row has a canonical PARTIES id (mayoral labels alone are not enough).
  const inner = (typeof devolvedPartyLink === 'function')
    ? devolvedPartyLink(partyId, name, year)
    : ((partyId && PARTIES?.[partyId])
      ? `<a href="/party/${partyId}" class="inline-party-link">${name}</a>`
      : name);
  return `<div class="result-party-name"><div class="result-party-swatch" style="background:${color}"></div>${inner}</div>`;
}

// ── BOOKLET PROMO BOX (London Elects, 2004+) ──────────────────
function londonBookletBox(booklet) {
  if (!booklet || !booklet.pdf) return '';
  return `
    <section class="london-booklet" aria-label="Official candidate booklet">
      <a class="london-booklet-cover" href="${booklet.pdf}" target="_blank" rel="noopener">
        <img src="${withAssetsVersion(booklet.cover)}" alt="Front cover of the ${booklet.title}" width="356" height="504" loading="lazy" decoding="async">
      </a>
      <div class="london-booklet-body">
        <span class="section-label">London Elects</span>
        <h2>${booklet.title}</h2>
        <p>Ahead of every mayoral and Assembly election since 2004, London Elects has posted an official booklet to every London household. It explains how the elections work and how to vote, and carries an election address written by each candidate for Mayor.</p>
        <a class="london-booklet-btn" href="${booklet.pdf}" target="_blank" rel="noopener">↓ Open the candidate booklet (PDF)</a>
      </div>
    </section>`;
}

function londonManifestoCard(m, electionOrYear) {
  const isObj = electionOrYear && typeof electionOrYear === 'object';
  const electionId = isObj ? electionOrYear.id : String(electionOrYear);
  const year = isObj ? electionOrYear.year : electionOrYear;
  
  const color = londonPartyColor(m.party);
  const partyName = londonPartyName(m, year);
  const heading = m.candidate || partyName;
  const pdfSize = (typeof window.getPdfSize === 'function' && m.pdf) ? window.getPdfSize(m.pdf) : '';

  // Route slug = folder id (not affiliation): livingstone ≠ independent
  const routeSlug = londonManifestoRouteSlug(m);
  const hasText = routeSlug
    ? (MANIFESTO_ARCHIVE?.has(`london/${electionId}/${routeSlug}`) ?? false)
    : false;

  const textLink = hasText
    ? `<a href="/manifesto/london/${electionId}/${routeSlug}" class="manifesto-link">
         <span class="manifesto-link-icon" aria-hidden="true">📝</span>
         <div class="manifesto-link-info"><div class="manifesto-link-title">Read Online</div><div class="manifesto-link-sub">Formatted text version</div></div>
       </a>`
    : '';

  const thumbHref = hasText ? `/manifesto/london/${electionId}/${routeSlug}` : m.pdf;
  const thumbTarget = hasText ? '' : 'target="_blank" rel="noopener"';
  const thumbLabel = hasText
    ? `Read ${heading} ${year} manifesto online`
    : `Open the ${heading} manifesto PDF`;
  const pdfLink = m.pdf && typeof pdfCtaHtml === 'function'
    ? pdfCtaHtml({ href: m.pdf, size: pdfSize, scanNote: true })
    : '';

  const coverSrc = m.cover;
  const showCover = coverSrc && (typeof hasCoverForPath === 'function' ? hasCoverForPath(coverSrc) : Boolean(coverSrc));
  const coverHtml = showCover && typeof coverPictureHtml === 'function'
    ? coverPictureHtml({ src: coverSrc, alt: '' })
    : '';
  const thumbInner = `${coverHtml}
        <div class="manifesto-thumb-placeholder" style="display:${showCover ? 'none' : 'flex'}">
          <svg viewBox="0 0 48 64" fill="none" xmlns="http://www.w3.org/2000/svg" class="thumb-doc-icon">
            <rect x="12" y="10" width="32" height="44" rx="2" fill="currentColor" opacity="0.9"/>
          </svg>
          <span class="thumb-year">${year}</span>
        </div>`;
  const headerInner = `
        <span class="manifesto-party-dot" style="background:${color}"></span>
        <span class="manifesto-party-name">${heading}</span>
        ${m.party && PARTIES?.[m.party] ? `<span class="manifesto-party-tag">${partyName}</span>` : ''}`;
  const bodyParts = [];
  if (m.title) bodyParts.push(`<p class="london-manifesto-title">${m.title}</p>`);
  if (m.pdf && thumbHref !== m.pdf) bodyParts.push(pdfLink);
  if (hasText && thumbHref !== `/manifesto/london/${electionId}/${routeSlug}`) bodyParts.push(textLink);

  return manifestoCardShell({
    style: `--party-color:${color};--party-dim:rgba(0,0,0,0.04)`,
    href: thumbHref || '#',
    target: thumbTarget,
    label: thumbLabel,
    thumbInner,
    headerInner,
    bodyInner: bodyParts.filter(Boolean).join(''),
  });
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
  const runoffHead = isSV ? '<th scope="col" style="text-align:right">Run-off</th><th scope="col">%</th>' : '';
  return `
    <div class="results-section">
      <span class="section-label">Mayor of London · ${m.system || 'First-past-the-post'}</span>
      <h2>Mayoral Result</h2>
      <table class="results-table london-mayor-table">
        <thead><tr><th scope="col">Candidate</th><th scope="col">${isSV ? 'First round' : 'Votes'}</th><th scope="col">%</th>${runoffHead}<th scope="col"></th></tr></thead>
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
        <table class="results-table"><thead><tr><th scope="col">Party</th><th scope="col">List votes</th><th scope="col">%</th></tr></thead>
        <tbody>${a.otherListVotes.map(o => `<tr><td>${o.name}</td><td style="color:var(--text-muted)">${londonNum(o.votes)}</td><td style="color:var(--text-muted)">${typeof o.pct === 'number' ? o.pct.toFixed(1) + '%' : '—'}</td></tr>`).join('')}</tbody></table>
      </details>`
    : '';
  return `
    <div class="results-section">
      <span class="section-label">London Assembly · ${a.system || 'Additional Member System'}</span>
      <h2>Assembly Result</h2>
      <table class="results-table london-assembly-table">
        <thead><tr><th scope="col">Party</th><th scope="col" title="Constituency seats" style="text-align:center">Const.</th><th scope="col" title="London-wide list seats" style="text-align:center">List</th><th scope="col">Seats (of ${a.totalSeats})</th><th scope="col">List vote %</th></tr></thead>
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
  const hasVotes = c.results.some(r => typeof r.votes === 'number');
  const rows = c.results.slice().sort((x, y) => y.seats - x.seats).map(r => {
    const color = londonPartyColor(r.party);
    const isWinner = r.party === election.control;
    const pct = typeof r.pct === 'number' ? r.pct.toFixed(1) + '%' : '—';
    const votesCell = hasVotes
      ? `<td style="color:var(--text-muted)">${typeof r.votes === 'number' ? londonNum(r.votes) : '—'}</td>`
      : '';
    return `<tr>
      <td>${londonPartyCell(r, election.year)}${isWinner ? ' <span class="majority-badge">✦ Control</span>' : ''}</td>
      <td><div class="result-seats-bar-wrap"><div class="result-seats-bar"><div class="result-seats-fill" style="width:${((r.seats || 0) / maxSeats * 100).toFixed(1)}%;background:${color}"></div></div><strong style="color:var(--cream);min-width:32px">${r.seats}</strong></div></td>
      ${votesCell}
      <td style="color:var(--text-muted)">${pct}</td>
    </tr>`;
  }).join('');
  const otherPct = o => typeof o.pct !== 'number' ? '—'
    : (o.pct > 0 && o.pct < 0.05 ? '&lt;0.1%' : o.pct.toFixed(1) + '%');
  // Same styling as the main table: swatch + party link (falls back to a
  // neutral swatch and the printed ballot label for parties without a page).
  const otherName = o => londonPartyCell({ ...o, partyLabel: o.partyLabel || o.name }, election.year);
  const others = (c.otherVotes || []).length
    ? `<details class="london-others"><summary>Other parties (no seats)</summary>
        <table class="results-table"><thead><tr><th scope="col">Party</th><th scope="col">Votes</th><th scope="col">%</th></tr></thead>
        <tbody>${c.otherVotes.map(o => `<tr><td>${otherName(o)}</td><td style="color:var(--text-muted)">${typeof o.votes === 'number' ? londonNum(o.votes) : '—'}</td><td style="color:var(--text-muted)">${otherPct(o)}</td></tr>`).join('')}</tbody></table>
        ${c.otherVotesNote ? `<p style="font-size:0.75rem;color:var(--text-faint);margin-top:0.5rem">${c.otherVotesNote}</p>` : ''}
      </details>`
    : '';
  return `
    <div class="results-section">
      <span class="section-label">${LONDON_BODY_LABELS[election.body] || 'Council'}</span>
      <h2>Council Composition</h2>
      <table class="results-table">
        <thead><tr><th scope="col">Party</th><th scope="col">Councillors (of ${c.totalSeats})</th>${hasVotes ? '<th scope="col">Votes</th>' : ''}<th scope="col">Vote %</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
      ${c.note ? `<p style="font-size:0.75rem;color:var(--text-faint);margin-top:0.75rem">${c.note}</p>` : ''}
      ${others}
    </div>`;
}

// ── LONDON ELECTION PAGE ──────────────────────────────────────
/** Legacy prefixed ids (gla-2000 / glc-1964 / lcc-1946) → year-only. */
function normalizeLondonElectionId(id) {
  const m = String(id || '').match(/^(?:gla|glc|lcc)-(\d{4})$/);
  return m ? m[1] : id;
}

async function renderLondonElection(app, id) {
  const canonicalId = normalizeLondonElectionId(id);
  if (canonicalId !== id) {
    navigate(`/election/london/${canonicalId}`, { replace: true });
    return;
  }

  setPageMeta({ title: 'London election', description: 'London election results.', path: `/election/london/${id}` });
  app.innerHTML = `<div class="election-body"><div class="manifesto-skeleton" role="status" aria-label="Loading"><div class="skeleton-line skeleton-title"></div><div class="skeleton-line"></div><div class="skeleton-line w-60"></div></div></div>`;

  const [election, indexRaw] = await Promise.all([loadLondonElection(id), loadLondonIndex()]);
  const index = indexRaw || [];
  if (!election) { renderNotFound(app); return; }

  const bodyLabel = LONDON_BODY_LABELS[election.body] || 'London';
  const winnerId = election.mayorWinner || election.control;
  const winner = (winnerId && PARTIES?.[winnerId]) ? PARTIES[winnerId] : {};
  const badge = typeof winnerBadgeStyle === 'function'
    ? winnerBadgeStyle(winnerId, election.year)
    : { dim: winner.dim || 'var(--gold-dim)', css: `--party-color:${winner.color || 'var(--gold)'};--party-dim:${winner.dim || 'var(--gold-dim)'}` };
  const winnerName = election.mayorWinnerName || election.winnerName || '';

  setPageMeta({
    title: `${election.displayYear} ${DEVOLVED_PORTALS?.london?.label || 'London'} Election`,
    description: devolvedElectionDescription('london', election.displayYear, DEVOLVED_PORTALS?.london),
    path: `/election/london/${id}`,
  });

  // Prev/next within the same era, ordered by year
  const sorted = [...index].sort((a, b) => a.year - b.year);
  const pos = sorted.findIndex(e => e.id === id);
  const prev = pos > 0 ? sorted[pos - 1] : null;
  const next = pos >= 0 && pos < sorted.length - 1 ? sorted[pos + 1] : null;

  const summaryParas = (election.summary || '').split('\n\n').map(p => `<p>${p.trim()}</p>`).join('');
  const highlightItems = (election.highlights || []).map(h => `<div class="highlight-item"><div class="highlight-marker"></div><span>${h}</span></div>`).join('');

  const winnerBadge = winnerName
    ? `<div class="election-winner-badge" style="${badge.css}"><div class="winner-dot"></div>${election.mayorWinner ? `${winnerName} — Mayor of London` : `${winner.shortName || winnerName} control`}</div>`
    : '';

  const manifestosSection = (election.manifestos || []).length
    ? `<div class="manifestos-section" id="election-documents" data-rail="Documents">
        <span class="section-label">Candidate Manifestos</span>
        <h2>Documents</h2>
        <p class="manifestos-intro">The principal manifesto published by each major party or mayoral candidate.</p>
        <div class="manifesto-grid">${election.manifestos.map(m => londonManifestoCard(m, election)).join('')}</div>
      </div>`
    : '';

  const sources = (election.sources || []).length
    ? `<div class="london-sources" id="election-sources" data-rail="Sources"><span class="section-label">Sources</span><ul>${election.sources.map(s => `<li><a href="${s.url}" target="_blank" rel="noopener">${s.label}</a></li>`).join('')}</ul></div>`
    : '';

  const hasChart = (election.assembly?.results?.length) || (election.council?.results?.length);
  const chartResults = election.assembly?.results || election.council?.results || [];
  const chartTotal = election.assembly?.totalSeats || election.council?.totalSeats || 0;
  const chartTitle = election.assembly ? 'London Assembly' : bodyLabel;
  const isGla = election.body === 'gla' && !!election.assembly?.results?.length;
  const isGlc = election.body === 'glc' && !!election.council?.results?.length;
  const hasHexmap = isGla || isGlc;
  const primaryTabLabel = isGlc ? 'Council' : 'Assembly';
  const primaryTabId = 'london-tab-primary';
  const primaryPaneId = 'london-viz-primary';

  const vizPanel = !hasChart ? '' : hasHexmap ? `<div class="viz-panel">
            <div class="viz-tabs" role="tablist">
              <button type="button" class="viz-tab active" id="${primaryTabId}" data-viz="primary" role="tab" aria-selected="true" aria-controls="${primaryPaneId}" tabindex="0">${primaryTabLabel}</button>
              <button type="button" class="viz-tab" id="london-tab-hexmap" data-viz="hexmap" role="tab" aria-selected="false" aria-controls="london-viz-hexmap" tabindex="-1">Constituencies</button>
            </div>
            <div class="viz-pane active" id="${primaryPaneId}" role="tabpanel" aria-labelledby="${primaryTabId}">
              <div class="parliament-card viz-card">
                <div class="parliament-card-title">${chartTitle}</div>
                <div class="parliament-card-sub">${chartTotal} seats · majority ${Math.floor(chartTotal / 2) + 1}</div>
                <div id="london-chart-container"></div>
                <div class="parliament-legend" id="london-chart-legend"></div>
              </div>
            </div>
            <div class="viz-pane" id="london-viz-hexmap" role="tabpanel" aria-labelledby="london-tab-hexmap" hidden>
              <div class="parliament-card viz-card">
                <div class="parliament-card-title">Constituency Map</div>
                <div class="parliament-card-sub" id="london-hexmap-subtitle">Constituency results</div>
                <div id="london-hexmap-container" class="hexmap-container"></div>
                <div class="parliament-legend hexmap-legend" id="london-hexmap-legend" hidden></div>
              </div>
            </div>
          </div>` : `<div class="viz-panel">
            <div class="parliament-card viz-card">
              <div class="parliament-card-title">${chartTitle}</div>
              <div class="parliament-card-sub">${chartTotal} seats</div>
              <div id="london-chart-container"></div>
              <div class="parliament-legend" id="london-chart-legend"></div>
            </div>
          </div>`;

  app.innerHTML = `
    ${renderBreadcrumb([
      { label: nodeLabel('home'), href: '/' },
      { label: nodeLabel('elections'), href: '/election' },
      { label: 'London Mayor & Assembly', href: '/election/london' },
      { label: election.displayYear },
    ])}
    <section class="election-hero" style="--party-glow:${badge.dim}">
      <div class="election-hero-bg"></div>
      <div class="election-hero-inner">
        <div>
          <div class="election-eyebrow">${bodyLabel}</div>
          <h1 class="election-title">${election.displayYear}</h1>
          <div class="election-date">${election.date}</div>
          ${winnerBadge}
        </div>
        <div class="election-nav-btns">
          ${prev ? `<a class="election-nav-btn" href="/election/london/${prev.id}">← ${prev.displayYear}</a>` : ''}
          ${next ? `<a class="election-nav-btn" href="/election/london/${next.id}">${next.displayYear} →</a>` : ''}
        </div>
      </div>
    </section>

    <div class="election-body">
      <div class="election-grid">
        <div>
          ${summaryParas ? `<span class="section-label">Election Summary</span><div class="election-summary" id="election-summary" data-rail="Summary">${summaryParas}</div>` : ''}
          ${highlightItems ? `<div class="highlights-list"><h3>Key Moments</h3>${highlightItems}</div>` : ''}
          ${londonMayorSection(election)}
          ${londonAssemblySection(election)}
          ${londonCouncilSection(election)}
        </div>
        <div>
          ${vizPanel}
        </div>
      </div>

      ${londonBookletBox(election.booklet)}
      ${manifestosSection}
      ${sources}
    </div>
  `;
  if (typeof attachPageRail === 'function') attachPageRail(app);

  if (hasChart) {
    requestAnimationFrame(() => {
      const cont = document.getElementById('london-chart-container');
      const leg = document.getElementById('london-chart-legend');
      if (cont) drawParliamentChart(cont, chartResults, chartTotal);
      if (leg) buildParliamentLegend(leg, chartResults, election.year);

      if (!hasHexmap) return;

      const tabs = document.querySelectorAll('#london-tab-primary, #london-tab-hexmap');
      const panes = {
        primary: document.getElementById('london-viz-primary'),
        hexmap: document.getElementById('london-viz-hexmap'),
      };
      let hexmapLoaded = false;

      const formatGlcSeatsList = (seatsList) => {
        if (!Array.isArray(seatsList) || seatsList.length === 0) return '';
        const counts = {};
        seatsList.forEach(pid => {
          const key = (pid || 'others').toLowerCase().replace(/\s+/g, '');
          counts[key] = (counts[key] || 0) + 1;
        });
        return Object.entries(counts)
          .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
          .map(([pid, count]) => `${getPartyName(pid, election.year)} ${count}`)
          .join(' · ');
      };

      const switchTab = (targetViz) => {
        tabs.forEach(t => {
          const active = t.dataset.viz === targetViz;
          t.classList.toggle('active', active);
          t.setAttribute('aria-selected', active);
          t.tabIndex = active ? 0 : -1;
        });
        Object.entries(panes).forEach(([viz, pane]) => {
          if (!pane) return;
          const active = viz === targetViz;
          pane.classList.toggle('active', active);
          pane.hidden = !active;
        });

        if (targetViz === 'hexmap' && !hexmapLoaded) {
          hexmapLoaded = true;
          const loadHex = isGlc ? loadGlcHexLayout : loadLondonHexLayout;
          loadHex(election.year).then(hexjson => {
            const hexCont = document.getElementById('london-hexmap-container');
            const hexLeg = document.getElementById('london-hexmap-legend');
            const subtitleEl = document.getElementById('london-hexmap-subtitle');
            if (!hexCont) return;
            if (!hexjson?.hexes) {
              hexCont.innerHTML = '<p class="hexmap-empty">Constituency map not yet available for this election.</p>';
              return;
            }

            if (subtitleEl) {
              if (isGlc) {
                const y = election.year;
                subtitleEl.textContent = y <= 1970
                  ? 'Borough multi-member divisions (bloc vote)'
                  : 'Single-member divisions (same as parliamentary constituencies)';
              } else {
                subtitleEl.textContent = 'Constituency results (first-past-the-post) + London-wide list';
              }
            }

            const data = hexjsonToDrawData(hexjson, election.year);
            data.constituencies = data.constituencies.map(c => {
              const cell = hexjson.hexes[c.key];
              let mp = cell?.winner || 'Winner unknown';
              if (isGlc && Array.isArray(cell?.seats_list) && cell.seats_list.length > 0) {
                const seatSummary = formatGlcSeatsList(cell.seats_list);
                mp = seatSummary
                  ? (cell.winner ? `${seatSummary} — ${cell.winner}` : seatSummary)
                  : mp;
              }
              return { ...c, mp };
            });

            if (isGla && hexjson.regional_list) {
              hexCont.innerHTML = '';
              const wrap = document.createElement('div');
              wrap.className = 'hexmap-1945-wrap';

              const mapCol = document.createElement('div');
              mapCol.className = 'hexmap-1945-map';

              const outsideCol = document.createElement('div');
              outsideCol.className = 'hexmap-outside-panel';
              outsideCol.id = 'london-list-panel';

              wrap.appendChild(mapCol);
              wrap.appendChild(outsideCol);
              hexCont.appendChild(wrap);

              drawHexmap(mapCol, data, {
                legendEl: null,
                electionYear: election.year,
                electionId: election.id,
              });
              renderLondonListPanel(outsideCol, hexjson.regional_list, election.year);
            } else {
              drawHexmap(hexCont, data, {
                legendEl: null,
                electionYear: election.year,
                electionId: election.id,
              });
            }

            if (hexLeg) {
              const constsForLegend = [...data.constituencies];
              if (isGla && hexjson.regional_list) {
                hexjson.regional_list.forEach(reg => {
                  (reg.members || []).forEach(member => {
                    constsForLegend.push({
                      party: member.party,
                      partyLabel: getPartyName(member.party, election.year),
                    });
                  });
                });
              }
              buildHexmapLegend(hexLeg, constsForLegend, election.year);
              hexLeg.hidden = false;
            }
          });
        }
      };

      tabs.forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.viz));
        tab.addEventListener('keydown', e => {
          if (e.key === 'ArrowRight') { e.preventDefault(); tabs[1]?.focus(); switchTab('hexmap'); }
          if (e.key === 'ArrowLeft')  { e.preventDefault(); tabs[0]?.focus(); switchTab('primary'); }
        });
      });
    });
  }
}

// ── LONDON PORTAL (timeline of all London elections) ──────────
async function renderLondonPortal(app) {
  const portal = (typeof DEVOLVED_PORTALS !== 'undefined') ? DEVOLVED_PORTALS.london : null;
  setPageMeta({
    title: `${portal?.label || 'London Mayor & Assembly'} Elections`,
    description: `Election results and party manifestos for the ${portal?.label || 'London Mayor & Assembly'}.`,
    path: '/election/london',
  });

  const index = await loadLondonIndex();
  if (!index) {
    if (typeof renderDataError === 'function') {
      renderDataError(app, {
        message: 'London election list failed to load.',
        onRetry: () => renderLondonPortal(app),
      });
    } else {
      app.innerHTML = '<p role="alert">London election list failed to load.</p>';
    }
    return;
  }
  const byEra = { lcc: [], glc: [], gla: [] };
  index.forEach(e => { (byEra[e.body] || (byEra[e.body] = [])).push(e); });

  const eraBlock = (key, title, blurb) => {
    const items = (byEra[key] || []).slice().sort((a, b) => b.year - a.year);
    if (!items.length) return '';
    const cards = items.map(e => buildDevolvedTimelineCard(`/election/london/${e.id}`, e)).join('');
    return `<div class="london-era">
      <div class="london-era-head"><h2>${title}</h2><p>${blurb}</p></div>
      <div class="timeline-grid">${cards}</div>
    </div>`;
  };

  app.innerHTML = `
    ${renderBreadcrumb([
      { label: nodeLabel('home'), href: '/' },
      { label: nodeLabel('elections'), href: '/election' },
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

// ── PARTY-PAGE HISTORY (used by renderParty in app.js) ────────
/** Folder / route slug for a London manifesto (unique per election). */
function londonManifestoRouteSlug(m) {
  if (m?.id) return m.id;
  const path = m?.pdf || m?.md || m?.cover || '';
  const segs = path.split('/').filter(Boolean);
  if (segs.length >= 2) return segs[segs.length - 2];
  return m?.party || null;
}

/** @deprecated Use londonManifestoRouteSlug — kept as alias for callers. */
function londonManifestoPartySlug(m) {
  return londonManifestoRouteSlug(m);
}

/** Ken Livingstone persona match (Independent 2000, Labour 2004–12). */
function londonIsLivingstoneName(name) {
  return typeof name === 'string' && /ken\s+livingstone/i.test(name);
}

function londonMayorCandidateForParty(election, partyId) {
  const canonical = typeof resolvePartyId === 'function' ? resolvePartyId(partyId) : partyId;
  return (election.mayor?.candidates || []).find(c => {
    const cParty = c.party && typeof resolvePartyId === 'function' ? resolvePartyId(c.party) : c.party;
    if (cParty === canonical || cParty === partyId) return true;
    return canonical === 'livingstone' && londonIsLivingstoneName(c.name);
  }) || null;
}

/** True when this party/persona won the mayoralty (or council control). */
function londonPartyLedElection(partyId, election) {
  const canonical = typeof resolvePartyId === 'function' ? resolvePartyId(partyId) : partyId;
  if (election.control === canonical || election.control === partyId) return true;
  if (election.mayorWinner === canonical || election.mayorWinner === partyId) return true;
  // Livingstone won 2004 under Labour affiliation — still a mayoral win on his page.
  if (canonical === 'livingstone') {
    const cand = londonMayorCandidateForParty(election, 'livingstone');
    return !!(cand && cand.elected);
  }
  return false;
}

/** Elections contested + manifestos held across LCC / GLC / GLA for one party. */
async function getLondonPartyHistory(partyId) {
  const canonical = typeof resolvePartyId === 'function' ? resolvePartyId(partyId) : partyId;
  const index = (await loadLondonIndex()) || [];
  const elections = [];
  const manifestos = [];
  await Promise.all(index.map(async (meta) => {
    const election = await loadLondonElection(meta.id);
    if (!election) return;
    let result = election.council?.results?.find(r => r.party === canonical)
      || election.assembly?.results?.find(r => r.party === canonical)
      || election.council?.otherVotes?.find(r => r.party === canonical)
      || null;
    if (result) {
      result = {
        party: canonical,
        seats: result.seats ?? 0,
        pct: (typeof result.pct === 'number' ? result.pct
          : (typeof result.listPct === 'number' ? result.listPct : null)),
      };
    }
    // Match persona/folder id OR affiliation party (independent ≠ livingstone).
    // Livingstone also pulls Labour-banner years where he was the mayoral candidate.
    const partyManifestos = (election.manifestos || []).filter(m => {
      const route = londonManifestoRouteSlug(m);
      const affiliation = m.party && typeof resolvePartyId === 'function'
        ? resolvePartyId(m.party) : m.party;
      if (route === canonical || route === partyId
        || affiliation === canonical || affiliation === partyId) return true;
      return canonical === 'livingstone' && londonIsLivingstoneName(m.candidate);
    });
    const mayorCand = londonMayorCandidateForParty(election, canonical);
    const isMayorWinner = election.mayorWinner === canonical;
    if (result || partyManifestos.length || isMayorWinner || mayorCand) {
      elections.push({ election, result: result || { party: canonical, seats: 0, pct: null } });
      partyManifestos.forEach(m => manifestos.push({ election, manifesto: m }));
    }
  }));
  elections.sort((a, b) => b.election.year - a.election.year);
  manifestos.sort((a, b) => b.election.year - a.election.year);
  return { elections, manifestos };
}

/** Result row for the party page's London section. */
function londonPartyElectionRow(partyId, { election, result }, maxSeats, color) {
  const isMayor = typeof londonPartyLedElection === 'function'
    ? londonPartyLedElection(partyId, election) && !!election.mayor
    : election.mayorWinner === partyId;
  const isControl = election.control === partyId
    || (typeof resolvePartyId === 'function' && election.control === resolvePartyId(partyId));
  const led = typeof londonPartyLedElection === 'function'
    ? londonPartyLedElection(partyId, election)
    : (isMayor || isControl);
  const cls = led ? 'won' : 'lost';
  const label = isMayor ? '✦ Mayor' : isControl ? '✦ Control' : result.seats > 0 ? 'Opposition' : 'No seats';
  const sub = LONDON_BODY_LABELS[election.body] || 'London';
  const barW = ((result.seats / maxSeats) * 100).toFixed(1);
  const pct = typeof result.pct === 'number' ? result.pct : null;
  return `<a class="party-election-row" href="/election/london/${election.id}">
    <div class="per-year">${election.displayYear}</div>
    <div><div class="per-outcome ${cls}">${label}</div><div style="font-size:0.78rem;color:var(--text-faint);margin-top:0.3rem">${sub}</div></div>
    <div class="per-seats-wrap"><div class="per-seats-num">${result.seats}</div><div class="per-seats-label">seats</div></div>
    <div class="per-bar-wrap"><div class="per-bar"><div class="per-bar-fill" style="width:${barW}%;background:${color}"></div></div><div class="per-pct">${pct != null ? pct.toFixed(1) + '% vote' : '—'}</div></div>
  </a>`;
}
