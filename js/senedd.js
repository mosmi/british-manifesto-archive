/* ============================================================
   THE BRITISH MANIFESTO ARCHIVE — Senedd elections
   Welsh Parliament elections (1999–)
   ============================================================ */

let _seneddIndex = null;

async function loadSeneddIndex() {
  if (_seneddIndex) return _seneddIndex;
  try {
    _seneddIndex = await fetchTyped('/data/devolved/senedd/index.json', 'json');
  } catch {
    _seneddIndex = [];
  }
  return _seneddIndex;
}

async function loadSeneddElection(id) {
  try {
    return await fetchTyped(`/data/devolved/senedd/${id}.json`, 'json');
  } catch {
    return null;
  }
}

function seneddNum(n) {
  return typeof n === 'number' ? n.toLocaleString('en-GB') : '—';
}

function seneddPartyColor(id) {
  return (id && typeof getPartyColor === 'function') ? getPartyColor(id) : '#6b7280';
}

function seneddPartyName(row, year) {
  if (row.partyLabel) return row.partyLabel;
  if (row.party && typeof PARTIES !== 'undefined' && PARTIES[row.party]) {
    return getPartyName(row.party, year);
  }
  return row.name || row.party || '—';
}

function seneddPartyCell(row, year) {
  const color = seneddPartyColor(row.party);
  const name = seneddPartyName(row, year);
  const inner = (row.party && PARTIES?.[row.party])
    ? `<a href="/party/${row.party}" class="inline-party-link">${name}</a>`
    : name;
  return `<div class="result-party-name"><div class="result-party-swatch" style="background:${color}"></div>${inner}</div>`;
}

function seneddIsClosedList(p) {
  return p?.system === 'Closed list proportional representation';
}

function seneddManifestoCard(m, year) {
  const color = seneddPartyColor(m.party);
  const partyName = seneddPartyName(m, year);
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

function seneddParliamentSection(election) {
  const p = election.parliament;
  if (!p || !Array.isArray(p.results)) return '';

  if (seneddIsClosedList(p)) {
    const rows = p.results.slice().sort((x, y) => y.seats - x.seats).map(r => {
      const pct = typeof r.pct === 'number' ? r.pct.toFixed(1) + '%' : '—';
      return `<tr>
        <td>${seneddPartyCell(r, election.year)}</td>
        <td><strong style="color:var(--cream)">${r.seats}</strong></td>
        <td style="color:var(--text-muted)">${typeof r.votes === 'number' ? seneddNum(r.votes) : '—'}</td>
        <td style="color:var(--text-muted)">${pct}</td>
      </tr>`;
    }).join('');
    const others = (p.otherListVotes || []).length
      ? `<details class="london-others"><summary>Other parties (no seats)</summary>
          <table class="results-table"><thead><tr><th>Party</th><th>Votes</th><th>%</th></tr></thead>
          <tbody>${p.otherListVotes.map(o => `<tr><td>${o.name}</td><td style="color:var(--text-muted)">${typeof o.votes === 'number' ? seneddNum(o.votes) : '—'}</td><td style="color:var(--text-muted)">${typeof o.pct === 'number' ? o.pct.toFixed(1) + '%' : '—'}</td></tr>`).join('')}</tbody></table>
        </details>`
      : '';
    return `
      <div class="results-section">
        <span class="section-label">Senedd Cymru · ${p.system}</span>
        <h2>Parliament Result</h2>
        <table class="results-table london-assembly-table">
          <thead><tr><th>Party</th><th>Seats (of ${p.totalSeats})</th><th>Votes</th><th>%</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
        <p style="font-size:0.75rem;color:var(--text-faint);margin-top:0.75rem">${p.totalSeats} Members elected across 16 constituencies of six seats each under closed-list proportional representation (D'Hondt). A majority requires ${p.majorityThreshold || 49} seats.</p>
        ${others}
      </div>`;
  }

  const rows = p.results.slice().sort((x, y) => y.seats - x.seats).map(r => {
    const listPct = typeof r.listPct === 'number' ? r.listPct.toFixed(1) + '%' : '—';
    const constPct = typeof r.constituencyPct === 'number' ? r.constituencyPct.toFixed(1) + '%' : '—';
    return `<tr>
      <td>${seneddPartyCell(r, election.year)}</td>
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
        <tbody>${p.otherListVotes.map(o => `<tr><td>${o.name}</td><td style="color:var(--text-muted)">${typeof o.votes === 'number' ? seneddNum(o.votes) : '—'}</td><td style="color:var(--text-muted)">${typeof o.pct === 'number' ? o.pct.toFixed(1) + '%' : '—'}</td></tr>`).join('')}</tbody></table>
      </details>`
    : '';
  return `
    <div class="results-section">
      <span class="section-label">Senedd Cymru · ${p.system || 'Additional Member System'}</span>
      <h2>Parliament Result</h2>
      <table class="results-table london-assembly-table">
        <thead><tr><th>Party</th><th title="Constituency seats" style="text-align:center">Const.</th><th title="Regional list seats" style="text-align:center">List</th><th>Seats (of ${p.totalSeats})</th><th>Const. %</th><th>List %</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
      <p style="font-size:0.75rem;color:var(--text-faint);margin-top:0.75rem">${p.constituencySeats || 40} constituency MSs elected by first-past-the-post and ${p.listSeats || 20} regional MSs allocated by party-list vote (modified d'Hondt). A majority requires ${p.majorityThreshold || 31} seats.</p>
      ${others}
    </div>`;
}

function seneddManifestosBySeats(election) {
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

async function renderSeneddElection(app, id) {
  setPageMeta({ title: 'Senedd election', description: 'Welsh Parliament election results.', path: `/devolved/senedd/${id}` });
  app.innerHTML = `<div class="election-body"><div class="manifesto-skeleton" role="status" aria-label="Loading"><div class="skeleton-line skeleton-title"></div><div class="skeleton-line"></div><div class="skeleton-line w-60"></div></div></div>`;

  const [election, index] = await Promise.all([loadSeneddElection(id), loadSeneddIndex()]);
  if (!election) { renderNotFound(app); return; }

  const winnerId = election.control;
  const winner = (winnerId && PARTIES?.[winnerId]) ? PARTIES[winnerId] : {};
  const color = winner.color || 'var(--gold)';
  const dim = winner.dim || 'var(--gold-dim)';
  const fm = election.firstMinister || '';

  setPageMeta({
    title: `${election.displayYear} Senedd Cymru election`,
    description: `Results and manifestos from the ${election.displayYear} Welsh Parliament election.`,
    path: `/devolved/senedd/${id}`,
  });

  const sorted = [...index].sort((a, b) => a.year - b.year);
  const pos = sorted.findIndex(e => e.id === id);
  const prev = pos > 0 ? sorted[pos - 1] : null;
  const next = pos >= 0 && pos < sorted.length - 1 ? sorted[pos + 1] : null;

  const summaryParas = (election.summary || '').split('\n\n').map(p => `<p>${p.trim()}</p>`).join('');
  const highlightItems = (election.highlights || []).map(h => `<div class="highlight-item"><div class="highlight-marker"></div><span>${h}</span></div>`).join('');

  const majorityNote = election.majority ? ' — majority government' : ' — largest party';
  const winnerBadge = fm
    ? `<div class="election-winner-badge" style="--party-color:${color};--party-dim:${dim}"><div class="winner-dot"></div>${fm} — First Minister${election.majority ? ' — majority government' : ''}</div>`
    : (winnerId && PARTIES?.[winnerId])
      ? `<div class="election-winner-badge" style="--party-color:${color};--party-dim:${dim}"><div class="winner-dot"></div>${PARTIES[winnerId].shortName}${majorityNote}</div>`
      : '';

  const turnoutLine = typeof election.turnout === 'number'
    ? `<div class="election-date">Turnout ${election.turnout.toFixed(1)}%</div>` : '';

  const manifestosSection = (election.manifestos || []).length
    ? `<div class="manifestos-section">
        <span class="section-label">Party Manifestos</span>
        <h2>Documents</h2>
        <p class="manifestos-intro">Manifestos published by parties contesting the ${election.displayYear} Senedd election, ordered by seats won.</p>
        <div class="manifesto-grid">${seneddManifestosBySeats(election).map(m => seneddManifestoCard(m, election.year)).join('')}</div>
      </div>`
    : '';

  const sources = (election.sources || []).length
    ? `<div class="london-sources"><span class="section-label">Sources</span><ul>${election.sources.map(s => `<li><a href="${s.url}" target="_blank" rel="noopener">${s.label}</a></li>`).join('')}</ul></div>`
    : '';

  const chartResults = election.parliament?.results || [];
  const chartTotal = election.parliament?.totalSeats || 60;
  const hasChart = chartResults.length > 0;

  app.innerHTML = `
    ${renderBreadcrumb([
      { label: 'Home', href: '/' },
      { label: 'Devolved Parliaments', href: '/devolved' },
      { label: 'Welsh Parliament', href: '/devolved/senedd' },
      { label: election.displayYear },
    ])}
    <section class="election-hero" style="--party-glow:${dim}">
      <div class="election-hero-bg"></div>
      <div class="election-hero-inner">
        <div>
          <div class="election-eyebrow">Senedd Cymru</div>
          <h1 class="election-title">${election.displayYear}</h1>
          <div class="election-date">${election.date}</div>
          ${turnoutLine}
          ${winnerBadge}
        </div>
        <div class="election-nav-btns">
          ${prev ? `<a class="election-nav-btn" href="/devolved/senedd/${prev.id}">← ${prev.displayYear}</a>` : ''}
          ${next ? `<a class="election-nav-btn" href="/devolved/senedd/${next.id}">${next.displayYear} →</a>` : ''}
        </div>
      </div>
    </section>

    <div class="election-body">
      <div class="election-grid">
        <div>
          ${summaryParas ? `<span class="section-label">Election Summary</span><div class="election-summary">${summaryParas}</div>` : ''}
          ${highlightItems ? `<div class="highlights-list"><h3>Key Moments</h3>${highlightItems}</div>` : ''}
          ${seneddParliamentSection(election)}
        </div>
        <div>
          ${hasChart ? `<div class="viz-panel">
            <div class="parliament-card viz-card">
              <div class="parliament-card-title">Senedd Cymru</div>
              <div class="parliament-card-sub">${chartTotal} seats · majority ${election.parliament?.majorityThreshold || 31}</div>
              <div id="senedd-chart-container"></div>
              <div class="parliament-legend" id="senedd-chart-legend"></div>
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
      const cont = document.getElementById('senedd-chart-container');
      const leg = document.getElementById('senedd-chart-legend');
      if (cont) drawParliamentChart(cont, chartResults, chartTotal);
      if (leg) buildParliamentLegend(leg, chartResults, election.year);
    });
  }
}

async function renderSeneddPortal(app) {
  const portal = (typeof DEVOLVED_PORTALS !== 'undefined') ? DEVOLVED_PORTALS.senedd : null;
  setPageMeta({
    title: 'Welsh Parliament',
    description: 'Senedd Cymru elections from 1999 to 2026 — results, seat breakdowns, and party manifestos.',
    path: '/devolved/senedd',
  });

  const index = await loadSeneddIndex();
  const sorted = index.slice().sort((a, b) => b.year - a.year);
  const cards = sorted.map(e => {
    const w = (e.control && PARTIES?.[e.control]) ? PARTIES[e.control] : null;
    const cColor = w?.color || 'var(--gold)';
    const sub = e.firstMinister ? `${e.firstMinister} (First Minister)` : (e.winnerName || PARTIES?.[e.control]?.shortName || '');
    return `<a href="/devolved/senedd/${e.id}" class="london-timeline-card" style="--party-color:${cColor}">
      <div class="london-timeline-year">${e.displayYear}</div>
      <div class="london-timeline-meta"><div class="london-timeline-title">${e.title || 'Senedd Cymru election'}</div><div class="london-timeline-sub">${sub}</div></div>
    </a>`;
  }).join('');

  const nation = (typeof NATIONS !== 'undefined') ? NATIONS.wales : null;
  const navConfig = (typeof NAV_PARTIES !== 'undefined') ? NAV_PARTIES.wales : null;
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
      { label: 'Welsh Parliament' },
    ])}
    <section class="devolved-hero">
      <div class="devolved-hero-inner">
        <span class="section-label">${portal?.subtitle || 'Senedd Cymru'}</span>
        <h1 class="devolved-hero-title">Welsh Parliament</h1>
        <div class="gold-rule"></div>
        <p class="devolved-hero-desc">${portal?.description || 'The Senedd Cymru elects Members of the Senedd under the Additional Member System (1999–2021) and closed-list proportional representation from 2026.'}</p>
        ${nation ? `<a href="/nation/${portal?.nation || 'wales'}" class="devolved-nation-link">View Wales nation page →</a>` : ''}
      </div>
    </section>
    <div class="devolved-body">
      <div class="london-era">
        <div class="london-era-head"><h2>Senedd elections (1999–)</h2><p>Every Welsh Parliament election since devolution, with results, seat charts, and archived party manifestos.</p></div>
        <div class="london-timeline-grid">${cards}</div>
      </div>
      <div class="devolved-grid" style="margin-top:2.5rem">
        <div></div>
        <div class="nation-parties-card">
          <div class="section-label" style="margin-bottom:1rem">Parties in the Senedd</div>
          ${partyLinks}
          <a href="/devolved/senedd/other-parties" class="holyrood-other-link">Other Welsh parties →</a>
        </div>
      </div>
    </div>
  `;
}

function renderSeneddOtherParties(app) {
  setPageMeta({
    title: 'Other Welsh Parties',
    description: 'Smaller and specialist parties that have contested Senedd Cymru elections.',
    path: '/devolved/senedd/other-parties',
  });

  const ids = (typeof SENEDD_OTHER_PARTIES !== 'undefined') ? SENEDD_OTHER_PARTIES : [];
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
      { label: 'Welsh Parliament', href: '/devolved/senedd' },
      { label: 'Other Welsh parties' },
    ])}
    <div class="about-section">
      <span class="section-label">Senedd Cymru</span>
      <h1>Other Welsh Parties</h1>
      <div class="gold-rule"></div>
      <p style="color:var(--text-muted);margin-bottom:1rem">Parties that have contested Senedd elections but are not among the principal groups on the Welsh Parliament portal. Many appear only on the regional list under AMS.</p>
      <p style="color:var(--text-muted);margin-bottom:0.75rem">For parties that have won Westminster seats:</p>
      <a href="/others" class="cross-archive-link">Other Parties →</a>
      <div class="others-grid">${cards}</div>
    </div>
  `;
}

async function getSeneddPartyHistory(partyId) {
  const index = await loadSeneddIndex();
  const elections = [];
  const manifestos = [];
  await Promise.all(index.map(async (meta) => {
    const election = await loadSeneddElection(meta.id);
    if (!election) return;
    const result = election.parliament?.results?.find(r => r.party === partyId);
    const partyManifestos = (election.manifestos || []).filter(m => m.party === partyId);
    if (result || partyManifestos.length) {
      elections.push({
        election,
        result: result || { party: partyId, seats: 0, listPct: null, constituencyPct: null, pct: null },
      });
      partyManifestos.forEach(m => manifestos.push({ election, manifesto: m }));
    }
  }));
  elections.sort((a, b) => b.election.year - a.election.year);
  manifestos.sort((a, b) => b.election.year - a.election.year);
  return { elections, manifestos };
}

function seneddPartyElectionRow(partyId, { election, result }, maxSeats, color) {
  const isGov = election.control === partyId;
  const cls = isGov ? 'won' : result.seats > 0 ? 'lost' : 'lost';
  const label = isGov ? '✦ Government' : result.seats > 0 ? 'Opposition' : 'No seats';
  const pct = typeof result.pct === 'number' ? result.pct
    : typeof result.listPct === 'number' ? result.listPct
    : typeof result.constituencyPct === 'number' ? result.constituencyPct
    : null;
  const barW = ((result.seats / maxSeats) * 100).toFixed(1);
  const sub = isGov && election.firstMinister
    ? `${election.firstMinister} — First Minister`
    : 'Senedd Cymru';
  const pctLabel = typeof result.pct === 'number' ? '% vote' : '% list vote';
  return `<a class="party-election-row" href="/devolved/senedd/${election.id}">
    <div class="per-year">${election.displayYear}</div>
    <div><div class="per-outcome ${cls}">${label}</div><div style="font-size:0.78rem;color:var(--text-faint);margin-top:0.3rem">${sub}</div></div>
    <div class="per-seats-wrap"><div class="per-seats-num">${result.seats}</div><div class="per-seats-label">MSs</div></div>
    <div class="per-bar-wrap"><div class="per-bar"><div class="per-bar-fill" style="width:${barW}%;background:${color}"></div></div><div class="per-pct">${pct != null ? pct.toFixed(1) + pctLabel : '—'}</div></div>
  </a>`;
}
