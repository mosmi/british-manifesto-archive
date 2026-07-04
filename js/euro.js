/* ============================================================
   THE BRITISH MANIFESTO ARCHIVE — European Parliament elections
   UK European Parliament elections (1979–2019)
   ============================================================ */

let _euroIndex = null;

async function loadEuroIndex() {
  if (_euroIndex) return _euroIndex;
  try {
    _euroIndex = await fetchTyped('/data/devolved/euro/index.json', 'json');
  } catch {
    _euroIndex = [];
  }
  return _euroIndex;
}

async function loadEuroElection(id) {
  try {
    return await fetchTyped(`/data/devolved/euro/${id}.json`, 'json');
  } catch {
    return null;
  }
}

function euroNum(n) {
  return typeof n === 'number' ? n.toLocaleString('en-GB') : '—';
}

function euroPartyColor(id) {
  return (id && typeof getPartyColor === 'function') ? getPartyColor(id) : '#6b7280';
}

function euroPartyName(row, year) {
  if (row.partyLabel) return row.partyLabel;
  if (row.party && typeof PARTIES !== 'undefined' && PARTIES[row.party]) {
    return getPartyName(row.party, year);
  }
  return row.name || row.party || '—';
}

function euroPartyCell(row, year) {
  const color = euroPartyColor(row.party);
  const name = euroPartyName(row, year);
  const inner = (row.party && PARTIES?.[row.party])
    ? `<a href="/party/${row.party}" class="inline-party-link">${name}</a>`
    : name;
  return `<div class="result-party-name"><div class="result-party-swatch" style="background:${color}"></div>${inner}</div>`;
}

function euroManifestoCard(m, year) {
  const color = euroPartyColor(m.party);
  const partyName = euroPartyName(m, year);
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

function euroParliamentSection(election) {
  const p = election.parliament;
  if (!p || !Array.isArray(p.results)) return '';

  const rows = p.results.slice().sort((x, y) => y.seats - x.seats).map(r => {
    const pct = typeof r.pct === 'number' ? r.pct.toFixed(1) + '%' : '—';
    return `<tr>
      <td>${euroPartyCell(r, election.year)}</td>
      <td><strong style="color:var(--cream)">${r.seats}</strong></td>
      <td style="color:var(--text-muted)">${pct}</td>
    </tr>`;
  }).join('');

  return `
    <div class="results-section">
      <span class="section-label">Seat Breakdown</span>
      <h2>Electoral Results</h2>
      <table class="results-table">
        <thead>
          <tr>
            <th>Party</th>
            <th>Seats</th>
            <th>Vote Share (%)</th>
          </tr>
        </thead>
        <tbody>
          ${rows}
        </tbody>
      </table>
    </div>`;
}

function euroManifestosBySeats(election) {
  const man = election.manifestos || [];
  const results = election.parliament?.results || [];
  const order = {};
  results.forEach((r, idx) => { order[r.party] = idx; });
  return man.slice().sort((a, b) => {
    const oa = order[a.party] ?? 999;
    const ob = order[b.party] ?? 999;
    return oa - ob;
  });
}

// Manifesto grouping — mirrors the Westminster nation sections, plus a
// pan-European "Alliances" group for transnational parties (e.g. PES).
const EURO_GROUP_ORDER = ['england', 'scotland', 'wales', 'northern-ireland', 'others', 'alliances'];
const EURO_GROUP_LABELS = {
  england: '🏴󠁧󠁢󠁥󠁮󠁧󠁿 England & UK-wide',
  scotland: '🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scotland',
  wales: '🏴󠁧󠁢󠁷󠁬󠁳󠁿 Wales',
  'northern-ireland': '🇮🇪 Northern Ireland',
  others: 'Other parties',
  alliances: '🇪🇺 Alliances',
};

function euroManifestoGroupKey(m) {
  if (m.group) return m.group;
  const nation = (m.party && typeof PARTIES !== 'undefined' && PARTIES[m.party]) ? PARTIES[m.party].nation : null;
  return nation || 'others';
}

function euroManifestoGroupsHtml(election) {
  const sorted = euroManifestosBySeats(election);
  const grouped = {};
  sorted.forEach(m => {
    const key = euroManifestoGroupKey(m);
    (grouped[key] = grouped[key] || []).push(m);
  });
  const present = EURO_GROUP_ORDER.filter(k => grouped[k]?.length);
  if (present.length <= 1) {
    return `<div class="manifesto-grid">${sorted.map(m => euroManifestoCard(m, election.year)).join('')}</div>`;
  }
  const headingFor = (k) => (typeof nationLink === 'function' && k !== 'others' && k !== 'alliances')
    ? nationLink(k, EURO_GROUP_LABELS[k])
    : EURO_GROUP_LABELS[k];
  return present.map(k => `<div class="manifesto-nation-group">
        <h3 class="manifesto-nation-heading">${headingFor(k)}</h3>
        <div class="manifesto-grid">${grouped[k].map(m => euroManifestoCard(m, election.year)).join('')}</div>
      </div>`).join('');
}

async function renderEuroElection(app, id) {
  const election = await loadEuroElection(id);
  if (!election) {
    renderNotFound(app);
    return;
  }

  setPageMeta({
    title: `${election.displayYear} European Parliament election`,
    description: `Results and party manifestos for the ${election.displayYear} European Parliament election in the UK.`,
    path: `/devolved/euro/${id}`,
  });

  const index = await loadEuroIndex();
  const currIdx = index.findIndex(e => e.id === id);
  const prev = currIdx > 0 ? index[currIdx - 1] : null;
  const next = currIdx < index.length - 1 && currIdx !== -1 ? index[currIdx + 1] : null;

  const winnerId = election.control;
  const winner = PARTIES[winnerId] || {};
  const color = winner.color || 'var(--gold)';
  const dim = winner.dim || 'var(--gold-dim)';

  const winnerName = election.winnerName || winner.shortName || '';
  const winnerBadge = winnerId
    ? `<div class="election-winner-badge" style="--party-color:${color};--party-dim:${dim}">
        <div class="winner-dot" style="background:${color}"></div>
        Largest party: ${winnerName}
       </div>`
    : '';

  const summaryParas = election.summary
    ? election.summary.split('\n\n').map(p => `<p>${p}</p>`).join('')
    : '';

  const highlightItems = (election.highlights || []).length
    ? `<ul class="highlights-ul">${election.highlights.map(h => `<li>${h}</li>`).join('')}</ul>`
    : '';

  const turnoutLine = typeof election.turnout === 'number'
    ? `<div class="election-date">UK Turnout ${election.turnout.toFixed(1)}%</div>` : '';

  const manifestosSection = (election.manifestos || []).length
    ? `<div class="manifestos-section">
        <span class="section-label">Party Manifestos</span>
        <h2>Documents</h2>
        <p class="manifestos-intro">Manifestos published by parties contesting the ${election.displayYear} European Parliament election, grouped by nation and by pan-European alliance.</p>
        ${euroManifestoGroupsHtml(election)}
      </div>`
    : '<div class="manifestos-section"><span class="section-label">Party Manifestos</span><h2>Documents</h2><p style="color:var(--text-muted)">No manifestos currently on record for this election.</p></div>';

  const sources = (election.sources || []).length
    ? `<div class="london-sources"><span class="section-label">Sources</span><ul>${election.sources.map(s => `<li><a href="${s.url}" target="_blank" rel="noopener">${s.label}</a></li>`).join('')}</ul></div>`
    : '';

  const chartResults = election.parliament?.results || [];
  const chartTotal = election.parliament?.totalSeats || 73;
  const hasChart = chartResults.length > 0;

  app.innerHTML = `
    ${renderBreadcrumb([
      { label: 'Home', href: '/' },
      { label: 'Beyond Westminster', href: '/devolved' },
      { label: 'European Parliament', href: '/devolved/euro' },
      { label: election.displayYear },
    ])}
    <section class="election-hero" style="--party-glow:${dim}">
      <div class="election-hero-bg"></div>
      <div class="election-hero-inner">
        <div>
          <div class="election-eyebrow">European Parliament</div>
          <h1 class="election-title">${election.displayYear}</h1>
          <div class="election-date">${election.date}</div>
          ${turnoutLine}
          ${winnerBadge}
        </div>
        <div class="election-nav-btns">
          ${prev ? `<a class="election-nav-btn" href="/devolved/euro/${prev.id}">← ${prev.displayYear}</a>` : ''}
          ${next ? `<a class="election-nav-btn" href="/devolved/euro/${next.id}">${next.displayYear} →</a>` : ''}
        </div>
      </div>
    </section>

    <div class="election-body">
      <div class="election-grid">
        <div>
          ${summaryParas ? `<span class="section-label">Election Summary</span><div class="election-summary">${summaryParas}</div>` : ''}
          ${highlightItems ? `<div class="highlights-list"><h3>Key Moments</h3>${highlightItems}</div>` : ''}
          ${euroParliamentSection(election)}
        </div>
        <div>
          ${hasChart ? `<div class="viz-panel">
            <div class="parliament-card viz-card">
              <div class="parliament-card-title">UK MEP Delegation</div>
              <div class="parliament-card-sub">${chartTotal} seats · majority ${election.parliament?.majorityThreshold || 37}</div>
              <div id="euro-chart-container"></div>
              <div class="parliament-legend" id="euro-chart-legend"></div>
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
      const cont = document.getElementById('euro-chart-container');
      const leg = document.getElementById('euro-chart-legend');
      if (cont) drawParliamentChart(cont, chartResults, chartTotal);
      if (leg) buildParliamentLegend(leg, chartResults, election.year);
    });
  }
}

async function renderEuroPortal(app) {
  const portal = (typeof DEVOLVED_PORTALS !== 'undefined') ? DEVOLVED_PORTALS.euro : null;
  setPageMeta({
    title: 'European Parliament',
    description: 'UK European Parliament elections from 1979 to 2019 — results, seat breakdowns, and party manifestos.',
    path: '/devolved/euro',
  });

  const index = await loadEuroIndex();
  const sorted = index.slice().sort((a, b) => b.year - a.year);
  const cards = sorted.map(e => {
    const w = (e.control && PARTIES?.[e.control]) ? PARTIES[e.control] : null;
    const cColor = w?.color || 'var(--gold)';
    const sub = e.winnerName ? `Largest: ${e.winnerName}` : '';
    return `<a href="/devolved/euro/${e.id}" class="london-timeline-card" style="--party-color:${cColor}">
      <div class="london-timeline-year">${e.displayYear}</div>
      <div class="london-timeline-meta"><div class="london-timeline-title">${e.title || 'European Parliament election'}</div><div class="london-timeline-sub">${sub}</div></div>
    </a>`;
  }).join('');

  const partyLinks = [
    'reform', 'labour', 'conservative', 'libdem', 'green', 'ukip', 'snp', 'plaid', 'alliance', 'sinnfein', 'dup', 'uup', 'sdlp'
  ].map(pid => {
    const p = PARTIES[pid];
    if (!p) return '';
    return `<a href="/party/${pid}" class="nation-party-link" style="--party-color:${p.color}">
      <span class="nation-party-dot" style="background:${p.color}"></span>
      <span>${p.shortName}</span>
    </a>`;
  }).join('');

  app.innerHTML = `
    ${renderBreadcrumb([
      { label: 'Home', href: '/' },
      { label: 'Beyond Westminster', href: '/devolved' },
      { label: 'European Parliament' },
    ])}
    <section class="devolved-hero">
      <div class="devolved-hero-inner">
        <div>
          <span class="section-label">${portal?.subtitle || 'Strasbourg & Brussels'}</span>
          <h1 class="devolved-hero-title">European Parliament</h1>
          <div class="gold-rule"></div>
          <p class="devolved-hero-desc">${portal?.description || 'The UK participated in European Parliament elections from 1979 until its exit from the European Union in 2020.'}</p>
        </div>
        <div class="nation-parties-card devolved-hero-parties">
          <div class="section-label" style="margin-bottom:1rem">Principal UK EP Parties</div>
          ${partyLinks}
          <a href="/devolved/euro/other-parties" class="holyrood-other-link">Other EP parties →</a>
        </div>
      </div>
    </section>
    <div class="devolved-body">
      <div class="london-era">
        <div class="london-era-head"><h2>European elections (1979–2019)</h2><p>Every European election contested by the UK, with full vote shares, seat distributions, and archived party manifestos.</p></div>
        <div class="london-timeline-grid">${cards}</div>
      </div>
    </div>
  `;
}

function renderEuroOtherParties(app) {
  setPageMeta({
    title: 'Other EP Parties',
    description: 'Smaller, regional, and specialist parties that have contested European Parliament elections in the UK.',
    path: '/devolved/euro/other-parties',
  });

  const ids = (typeof EURO_OTHER_PARTIES !== 'undefined') ? EURO_OTHER_PARTIES : [];
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
      { label: 'Beyond Westminster', href: '/devolved' },
      { label: 'European Parliament', href: '/devolved/euro' },
      { label: 'Other EP parties' },
    ])}
    <div class="about-section">
      <span class="section-label">European Parliament</span>
      <h1>Other EP Parties</h1>
      <div class="gold-rule"></div>
      <p style="color:var(--text-muted);margin-bottom:1rem">Specialist, minor, or pan-European political groups that contested European elections in the UK. This includes transnational groups and regional factions.</p>
      <p style="color:var(--text-muted);margin-bottom:0.75rem">For parties that won Westminster seats:</p>
      <a href="/others" class="cross-archive-link">Other Parties →</a>
      <div class="others-grid">${cards}</div>
    </div>
  `;
}

async function getEuroPartyHistory(partyId) {
  const index = await loadEuroIndex();
  const elections = [];
  const manifestos = [];
  await Promise.all(index.map(async (meta) => {
    const election = await loadEuroElection(meta.id);
    if (!election) return;
    const result = election.parliament?.results?.find(r => r.party === partyId);
    const partyManifestos = (election.manifestos || []).filter(m => m.party === partyId);
    if (result || partyManifestos.length) {
      elections.push({
        election,
        result: result || { party: partyId, seats: 0, pct: null },
      });
      partyManifestos.forEach(m => manifestos.push({ election, manifesto: m }));
    }
  }));
  elections.sort((a, b) => b.election.year - a.election.year);
  manifestos.sort((a, b) => b.election.year - a.election.year);
  return { elections, manifestos };
}

function euroPartyElectionRow(partyId, { election, result }, maxSeats, color) {
  const isGov = election.control === partyId;
  const cls = isGov ? 'won' : result.seats > 0 ? 'lost' : 'lost';
  const label = isGov ? '✦ Largest Party' : result.seats > 0 ? 'Opposition' : 'No seats';
  const pct = typeof result.pct === 'number' ? result.pct : null;
  const barW = ((result.seats / maxSeats) * 100).toFixed(1);
  const sub = 'European Parliament';
  const pctLabel = '% vote';
  return `<a class="party-election-row" href="/devolved/euro/${election.id}">
    <div class="per-year">${election.displayYear}</div>
    <div><div class="per-outcome ${cls}">${label}</div><div style="font-size:0.78rem;color:var(--text-faint);margin-top:0.3rem">${sub}</div></div>
    <div class="per-seats-wrap"><div class="per-seats-num">${result.seats}</div><div class="per-seats-label">MEPs</div></div>
    <div class="per-bar-wrap"><div class="per-bar"><div class="per-bar-fill" style="width:${barW}%;background:${color}"></div></div><div class="per-pct">${pct != null ? pct.toFixed(1) + pctLabel : '—'}</div></div>
  </a>`;
}
