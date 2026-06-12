/* ============================================================
   THE BRITISH MANIFESTO ARCHIVE — Holyrood elections
   Scottish Parliament elections (1999–)
   ============================================================ */

let _holyroodIndex = null;

async function loadHolyroodIndex() {
  if (_holyroodIndex) return _holyroodIndex;
  try {
    _holyroodIndex = await fetchTyped('/data/devolved/holyrood/index.json', 'json');
  } catch {
    _holyroodIndex = [];
  }
  return _holyroodIndex;
}

async function loadHolyroodElection(id) {
  try {
    return await fetchTyped(`/data/devolved/holyrood/${id}.json`, 'json');
  } catch {
    return null;
  }
}

function holyroodNum(n) {
  return typeof n === 'number' ? n.toLocaleString('en-GB') : '—';
}

function holyroodPartyColor(id) {
  return (id && typeof getPartyColor === 'function') ? getPartyColor(id) : '#6b7280';
}

function holyroodPartyName(row, year) {
  if (row.partyLabel) return row.partyLabel;
  if (row.party && typeof PARTIES !== 'undefined' && PARTIES[row.party]) {
    return getPartyName(row.party, year);
  }
  return row.name || row.party || '—';
}

function holyroodPartyCell(row, year) {
  const color = holyroodPartyColor(row.party);
  const name = holyroodPartyName(row, year);
  const inner = (row.party && PARTIES?.[row.party])
    ? `<a href="/party/${row.party}" class="inline-party-link">${name}</a>`
    : name;
  return `<div class="result-party-name"><div class="result-party-swatch" style="background:${color}"></div>${inner}</div>`;
}

function holyroodManifestoCard(m, year) {
  const color = holyroodPartyColor(m.party);
  const partyName = holyroodPartyName(m, year);
  const heading = m.candidate || partyName;
  return `
    <div class="manifesto-card" style="--party-color:${color};--party-dim:rgba(0,0,0,0.04)">
      <a href="${m.pdf}" class="manifesto-thumb" target="_blank" rel="noopener" aria-label="Open the ${heading} manifesto PDF">
        <img src="${m.cover}" alt="${heading} manifesto cover"
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
          <div class="manifesto-link-info"><div class="manifesto-link-title">Manifesto</div><div class="manifesto-link-sub">PDF document</div></div>
        </a>
      </div>
    </div>`;
}

function holyroodParliamentSection(election) {
  const p = election.parliament;
  if (!p || !Array.isArray(p.results)) return '';
  const rows = p.results.slice().sort((x, y) => y.seats - x.seats).map(r => {
    const listPct = typeof r.listPct === 'number' ? r.listPct.toFixed(1) + '%' : '—';
    const constPct = typeof r.constituencyPct === 'number' ? r.constituencyPct.toFixed(1) + '%' : '—';
    return `<tr>
      <td>${holyroodPartyCell(r, election.year)}</td>
      <td style="color:var(--text-muted);text-align:center">${r.constituencySeats ?? '—'}</td>
      <td style="color:var(--text-muted);text-align:center">${r.listSeats ?? '—'}</td>
      <td><strong style="color:var(--cream)">${r.seats}</strong></td>
      <td style="color:var(--text-muted)">${constPct}</td>
      <td style="color:var(--text-muted)">${listPct}</td>
    </tr>`;
  }).join('');
  const others = (p.otherListVotes || []).length
    ? `<details class="london-others"><summary>Other parties on the regional list (no seats)</summary>
        <table class="results-table"><thead><tr><th>Party</th><th>List votes</th><th>%</th></tr></thead>
        <tbody>${p.otherListVotes.map(o => `<tr><td>${o.name}</td><td style="color:var(--text-muted)">${typeof o.votes === 'number' ? holyroodNum(o.votes) : '—'}</td><td style="color:var(--text-muted)">${typeof o.pct === 'number' ? o.pct.toFixed(1) + '%' : '—'}</td></tr>`).join('')}</tbody></table>
      </details>`
    : '';
  return `
    <div class="results-section">
      <span class="section-label">Scottish Parliament · ${p.system || 'Additional Member System'}</span>
      <h2>Parliament Result</h2>
      <table class="results-table london-assembly-table">
        <thead><tr><th>Party</th><th title="Constituency seats" style="text-align:center">Const.</th><th title="Regional list seats" style="text-align:center">List</th><th>Seats (of ${p.totalSeats})</th><th>Const. %</th><th>List %</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
      <p style="font-size:0.75rem;color:var(--text-faint);margin-top:0.75rem">${p.constituencySeats || 73} constituency MSPs elected by first-past-the-post and ${p.listSeats || 56} regional MSPs allocated by party-list vote (modified d'Hondt). A majority requires ${p.majorityThreshold || 65} seats.</p>
      ${others}
    </div>`;
}

/** Sort manifesto cards to follow parliament seat order (largest party first). */
function holyroodManifestosBySeats(election) {
  const manifestos = election.manifestos || [];
  const results = election.parliament?.results || [];
  const seatRank = new Map();
  results.slice()
    .sort((a, b) => b.seats - a.seats)
    .forEach((r, i) => { if (r.party) seatRank.set(r.party, i); });
  const tailRank = seatRank.size;
  return manifestos.slice().sort((a, b) => {
    const ra = a.party && seatRank.has(a.party) ? seatRank.get(a.party) : tailRank;
    const rb = b.party && seatRank.has(b.party) ? seatRank.get(b.party) : tailRank;
    if (ra !== rb) return ra - rb;
    return 0;
  });
}

async function renderHolyroodElection(app, id) {
  setPageMeta({ title: 'Holyrood election', description: 'Scottish Parliament election results.', path: `/devolved/holyrood/${id}` });
  app.innerHTML = `<div class="election-body"><div class="manifesto-skeleton" role="status" aria-label="Loading"><div class="skeleton-line skeleton-title"></div><div class="skeleton-line"></div><div class="skeleton-line w-60"></div></div></div>`;

  const [election, index] = await Promise.all([loadHolyroodElection(id), loadHolyroodIndex()]);
  if (!election) { renderNotFound(app); return; }

  const winnerId = election.control;
  const winner = (winnerId && PARTIES?.[winnerId]) ? PARTIES[winnerId] : {};
  const color = winner.color || 'var(--gold)';
  const dim = winner.dim || 'var(--gold-dim)';
  const fm = election.firstMinister || '';

  setPageMeta({
    title: `${election.displayYear} Scottish Parliament election`,
    description: `Results and manifestos from the ${election.displayYear} Holyrood election.`,
    path: `/devolved/holyrood/${id}`,
  });

  const sorted = [...index].sort((a, b) => a.year - b.year);
  const pos = sorted.findIndex(e => e.id === id);
  const prev = pos > 0 ? sorted[pos - 1] : null;
  const next = pos >= 0 && pos < sorted.length - 1 ? sorted[pos + 1] : null;

  const summaryParas = (election.summary || '').split('\n\n').map(p => `<p>${p.trim()}</p>`).join('');
  const highlightItems = (election.highlights || []).map(h => `<div class="highlight-item"><div class="highlight-marker"></div><span>${h}</span></div>`).join('');

  const majorityNote = election.majority ? ' — majority government' : election.parliament?.results?.find(r => r.party === winnerId)?.seats >= (election.parliament?.majorityThreshold || 65) - 1 ? '' : ' — minority government';
  const winnerBadge = fm
    ? `<div class="election-winner-badge" style="--party-color:${color};--party-dim:${dim}"><div class="winner-dot"></div>${fm} — First Minister${majorityNote}</div>`
    : '';

  const turnoutBadge = typeof election.turnout === 'number'
    ? `<div class="election-meta-chip">Turnout ${election.turnout.toFixed(1)}%</div>` : '';

  const manifestosSection = (election.manifestos || []).length
    ? `<div class="manifestos-section">
        <span class="section-label">Party Manifestos</span>
        <h2>Documents</h2>
        <p class="manifestos-intro">Manifestos published by parties contesting the ${election.displayYear} Scottish Parliament election, ordered by seats won.</p>
        <div class="manifesto-grid">${holyroodManifestosBySeats(election).map(m => holyroodManifestoCard(m, election.year)).join('')}</div>
      </div>`
    : '';

  const sources = (election.sources || []).length
    ? `<div class="london-sources"><span class="section-label">Sources</span><ul>${election.sources.map(s => `<li><a href="${s.url}" target="_blank" rel="noopener">${s.label}</a></li>`).join('')}</ul></div>`
    : '';

  const chartResults = election.parliament?.results || [];
  const chartTotal = election.parliament?.totalSeats || 129;
  const hasChart = chartResults.length > 0;

  app.innerHTML = `
    ${renderBreadcrumb([
      { label: 'Home', href: '/' },
      { label: 'Devolved Parliaments', href: '/devolved' },
      { label: 'Scottish Parliament', href: '/devolved/holyrood' },
      { label: election.displayYear },
    ])}
    <section class="election-hero" style="--party-glow:${dim}">
      <div class="election-hero-bg"></div>
      <div class="election-hero-inner">
        <div>
          <div class="election-eyebrow">Scottish Parliament</div>
          <h1 class="election-title">${election.displayYear}</h1>
          <div class="election-date">${election.date}</div>
          ${winnerBadge}
          ${turnoutBadge}
        </div>
        <div class="election-nav-btns">
          ${prev ? `<a class="election-nav-btn" href="/devolved/holyrood/${prev.id}">← ${prev.displayYear}</a>` : ''}
          ${next ? `<a class="election-nav-btn" href="/devolved/holyrood/${next.id}">${next.displayYear} →</a>` : ''}
        </div>
      </div>
    </section>

    <div class="election-body">
      <div class="election-grid">
        <div>
          ${summaryParas ? `<span class="section-label">Election Summary</span><div class="election-summary">${summaryParas}</div>` : ''}
          ${highlightItems ? `<div class="highlights-list"><h3>Key Moments</h3>${highlightItems}</div>` : ''}
          ${holyroodParliamentSection(election)}
        </div>
        <div>
          ${hasChart ? `<div class="viz-panel">
            <div class="parliament-card viz-card">
              <div class="parliament-card-title">Scottish Parliament</div>
              <div class="parliament-card-sub">${chartTotal} seats · majority ${election.parliament?.majorityThreshold || 65}</div>
              <div id="holyrood-chart-container"></div>
              <div class="parliament-legend" id="holyrood-chart-legend"></div>
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
      const cont = document.getElementById('holyrood-chart-container');
      const leg = document.getElementById('holyrood-chart-legend');
      if (cont) drawParliamentChart(cont, chartResults, chartTotal);
      if (leg) buildParliamentLegend(leg, chartResults, election.year);
    });
  }
}

async function renderHolyroodPortal(app) {
  const portal = (typeof DEVOLVED_PORTALS !== 'undefined') ? DEVOLVED_PORTALS.holyrood : null;
  setPageMeta({
    title: 'Scottish Parliament',
    description: 'Scottish Parliament (Holyrood) elections from 1999 to 2026 — results, seat breakdowns, and party manifestos.',
    path: '/devolved/holyrood',
  });

  const index = await loadHolyroodIndex();
  const sorted = index.slice().sort((a, b) => b.year - a.year);
  const cards = sorted.map(e => {
    const w = (e.control && PARTIES?.[e.control]) ? PARTIES[e.control] : null;
    const cColor = w?.color || 'var(--gold)';
    const sub = e.firstMinister ? `${e.firstMinister} (First Minister)` : (e.winnerName || '');
    return `<a href="/devolved/holyrood/${e.id}" class="london-timeline-card" style="--party-color:${cColor}">
      <div class="london-timeline-year">${e.displayYear}</div>
      <div class="london-timeline-meta"><div class="london-timeline-title">${e.title || 'Scottish Parliament election'}</div><div class="london-timeline-sub">${sub}</div></div>
    </a>`;
  }).join('');

  const nation = (typeof NATIONS !== 'undefined') ? NATIONS.scotland : null;
  const navConfig = (typeof NAV_PARTIES !== 'undefined') ? NAV_PARTIES.scotland : null;
  const partyLinks = navConfig ? navConfig.parties.map(pid => {
    const p = PARTIES[pid];
    if (!p) return '';
    return `<a href="/party/${pid}" class="nation-party-link" style="--party-color:${p.color}">
      <span class="nation-party-dot" style="background:${p.color}"></span>
      <span>${p.shortName}</span>
    </a>`;
  }).join('') : '';

  app.innerHTML = `
    ${renderBreadcrumb([
      { label: 'Home', href: '/' },
      { label: 'Devolved Parliaments', href: '/devolved' },
      { label: 'Scottish Parliament' },
    ])}
    <section class="devolved-hero">
      <div class="devolved-hero-inner">
        <span class="section-label">${portal?.subtitle || 'Holyrood'}</span>
        <h1 class="devolved-hero-title">Scottish Parliament</h1>
        <div class="gold-rule"></div>
        <p class="devolved-hero-desc">${portal?.description || 'The Scottish Parliament at Holyrood elects 129 MSPs every five years under the Additional Member System.'}</p>
        ${nation ? `<a href="/nation/${portal?.nation || 'scotland'}" class="devolved-nation-link">View Scotland nation page →</a>` : ''}
      </div>
    </section>
    <div class="devolved-body">
      <div class="london-era">
        <div class="london-era-head"><h2>Holyrood elections (1999–)</h2><p>Every Scottish Parliament election since devolution, with results, seat charts, and archived party manifestos.</p></div>
        <div class="london-timeline-grid">${cards}</div>
      </div>
      <div class="devolved-grid" style="margin-top:2.5rem">
        <div></div>
        <div class="nation-parties-card">
          <div class="section-label" style="margin-bottom:1rem">Parties in the Scottish Parliament</div>
          ${partyLinks}
          <a href="/devolved/holyrood/other-parties" class="holyrood-other-link">Other Scottish parties →</a>
        </div>
      </div>
    </div>
  `;
}

function renderHolyroodOtherParties(app) {
  setPageMeta({
    title: 'Other Scottish Parties',
    description: 'Smaller and specialist parties that have contested Scottish Parliament elections at Holyrood.',
    path: '/devolved/holyrood/other-parties',
  });

  const ids = (typeof HOLYROOD_OTHER_PARTIES !== 'undefined') ? HOLYROOD_OTHER_PARTIES : [];
  const cards = [...ids]
    .sort((a, b) => (PARTIES[a]?.name || a).localeCompare(PARTIES[b]?.name || b, 'en-GB'))
    .map(pid => {
      const p = PARTIES[pid];
      if (!p) return '';
      return `<a href="/party/${pid}" class="others-party-card" style="--party-color:${p.color}">
        <div class="others-party-swatch" style="background:${p.color}"></div>
        <div>
          <div class="others-party-name">${p.name}</div>
          <div class="others-party-meta">${p.spectrum}${p.founded ? ` · Est. ${p.founded}` : ''}</div>
          <div class="others-party-desc">${p.description}</div>
        </div>
      </a>`;
    }).join('');

  app.innerHTML = `
    ${renderBreadcrumb([
      { label: 'Home', href: '/' },
      { label: 'Devolved Parliaments', href: '/devolved' },
      { label: 'Scottish Parliament', href: '/devolved/holyrood' },
      { label: 'Other Scottish parties' },
    ])}
    <div class="about-section">
      <span class="section-label">Holyrood</span>
      <h1>Other Scottish Parties</h1>
      <div class="gold-rule"></div>
      <p style="color:var(--text-muted);margin-bottom:1.5rem">Parties that have contested Scottish Parliament elections but are not among the principal groups on the Holyrood portal. Many appear only on the regional list under AMS. For parties that have won Westminster seats, see also <a href="/others">Other Parties</a>.</p>
      <div class="others-grid">${cards}</div>
    </div>
  `;
}

/** Holyrood manifestos and election results for a party (party pages). */
async function getHolyroodPartyHistory(partyId) {
  const index = await loadHolyroodIndex();
  const elections = [];
  const manifestos = [];
  await Promise.all(index.map(async (meta) => {
    const election = await loadHolyroodElection(meta.id);
    if (!election) return;
    const result = election.parliament?.results?.find(r => r.party === partyId);
    const partyManifestos = (election.manifestos || []).filter(m => m.party === partyId);
    if (result || partyManifestos.length) {
      elections.push({
        election,
        result: result || { party: partyId, seats: 0, listPct: null, constituencyPct: null },
      });
      partyManifestos.forEach(m => manifestos.push({ election, manifesto: m }));
    }
  }));
  elections.sort((a, b) => b.election.year - a.election.year);
  manifestos.sort((a, b) => b.election.year - a.election.year);
  return { elections, manifestos };
}

async function getHolyroodManifestosForParty(partyId) {
  const { manifestos } = await getHolyroodPartyHistory(partyId);
  return manifestos;
}

function holyroodPartyElectionRow(partyId, { election, result }, maxSeats, color) {
  const isGov = election.control === partyId;
  const cls = isGov ? 'won' : result.seats > 0 ? 'lost' : 'lost';
  const label = isGov ? '✦ Government' : result.seats > 0 ? 'Opposition' : 'No seats';
  const pct = typeof result.listPct === 'number' ? result.listPct
    : typeof result.constituencyPct === 'number' ? result.constituencyPct
    : null;
  const barW = ((result.seats / maxSeats) * 100).toFixed(1);
  const sub = isGov && election.firstMinister
    ? `${election.firstMinister} — First Minister`
    : 'Scottish Parliament';
  return `<a class="party-election-row" href="/devolved/holyrood/${election.id}">
    <div class="per-year">${election.displayYear}</div>
    <div><div class="per-outcome ${cls}">${label}</div><div style="font-size:0.78rem;color:var(--text-faint);margin-top:0.3rem">${sub}</div></div>
    <div class="per-seats-wrap"><div class="per-seats-num">${result.seats}</div><div class="per-seats-label">MSPs</div></div>
    <div class="per-bar-wrap"><div class="per-bar"><div class="per-bar-fill" style="width:${barW}%;background:${color}"></div></div><div class="per-pct">${pct != null ? pct.toFixed(1) + '% list vote' : '—'}</div></div>
  </a>`;
}
