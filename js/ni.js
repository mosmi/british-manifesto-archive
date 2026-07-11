/* ============================================================
   THE BRITISH MANIFESTO ARCHIVE — Stormont elections
   Northern Ireland Assembly elections (1998–)
   ============================================================ */

let _niIndex = null;

/** Load the pre-built NI Assembly constituency hexjson for a given year. */
const _niHexCache = new Map();
async function loadNIHexLayout(year) {
  if (_niHexCache.has(year)) return _niHexCache.get(year);
  try {
    const res = await fetch(`/data/hex/stormont/${year}.hexjson?v=${ASSETS_VERSION}`, { cache: 'no-cache' });
    if (!res.ok) return null;
    const data = await res.json();
    _niHexCache.set(year, data);
    return data;
  } catch (_) {
    return null;
  }
}

async function loadNIIndex() {
  if (_niIndex) return _niIndex;
  try {
    _niIndex = await fetchTyped('/data/devolved/stormont/index.json', 'json');
    return _niIndex;
  } catch {
    return null;
  }
}

async function loadNIElection(id) {
  try {
    return await fetchTyped(`/data/devolved/stormont/${id}.json`, 'json');
  } catch {
    return null;
  }
}

function niNum(n) {
  return typeof n === 'number' ? n.toLocaleString('en-GB') : '—';
}

function niPartyColor(id) {
  return (id && typeof getPartyColor === 'function') ? getPartyColor(id) : '#6b7280';
}

function niPartyName(row, year) {
  if (row.partyLabel) return row.partyLabel;
  if (row.party && typeof PARTIES !== 'undefined' && PARTIES[row.party]) {
    return getPartyName(row.party, year);
  }
  return row.name || row.party || '—';
}

function niPartyCell(row, year) {
  const pageId = resolvePartyId(row.party);
  const color = niPartyColor(pageId);
  const name = niPartyName(row, year);
  const inner = (pageId && PARTIES?.[pageId])
    ? devolvedPartyLink(pageId, name, year)
    : name;
  return `<div class="result-party-name"><div class="result-party-swatch" style="background:${color}"></div>${inner}</div>`;
}

function niManifestoCard(m, electionOrYear) {
  const election = normalizeDevolvedElection(electionOrYear);
  return buildDevolvedManifestoCard(m, election, {
    color: niPartyColor(m.party),
    partyName: niPartyName(m, election.year),
  });
}

function niParliamentSection(election) {
  const p = election.parliament;
  if (!p || !Array.isArray(p.results)) return '';
  const rows = p.results.slice().sort((x, y) => y.seats - x.seats).map(r => {
    const pct = typeof r.pct === 'number' ? r.pct.toFixed(1) + '%' : '—';
    return `<tr>
      <td>${niPartyCell(r, election.year)}</td>
      <td><strong style="color:var(--cream)">${r.seats}</strong></td>
      <td style="color:var(--text-muted)">${pct}</td>
    </tr>`;
  }).join('');
  const others = (p.otherListVotes || []).length
    ? `<details class="london-others"><summary>Other parties (no first-preference seats)</summary>
        <table class="results-table"><thead><tr><th scope="col">Party</th><th scope="col">First Pref. %</th></tr></thead>
        <tbody>${p.otherListVotes.map(o => `<tr><td>${o.name}</td><td style="color:var(--text-muted)">${typeof o.pct === 'number' ? o.pct.toFixed(1) + '%' : '—'}</td></tr>`).join('')}</tbody></table>
      </details>`
    : '';
  return `
    <div class="results-section">
      <span class="section-label">Northern Ireland Assembly · ${p.system || 'Single Transferable Vote'}</span>
      <h2>Assembly Result</h2>
      <table class="results-table london-assembly-table">
        <thead><tr><th scope="col">Party</th><th scope="col">Seats (of ${p.totalSeats})</th><th scope="col">First Pref. %</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
      <p style="font-size:0.75rem;color:var(--text-faint);margin-top:0.75rem">MLAs elected across multi-member constituencies under the Single Transferable Vote (STV) system. Under power-sharing rules, a formal overall majority is not required; instead, the Executive is formed jointly with cross-community support.</p>
      ${others}
    </div>`;
}

/** Sort manifesto cards to follow parliament seat order (largest party first). */
function niManifestosBySeats(election) {
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

async function renderNIElection(app, id) {
  setPageMeta({ title: 'Northern Ireland Assembly election', description: 'Northern Ireland Assembly election results.', path: `/devolved/stormont/${id}` });
  app.innerHTML = `<div class="election-body"><div class="manifesto-skeleton" role="status" aria-label="Loading"><div class="skeleton-line skeleton-title"></div><div class="skeleton-line"></div><div class="skeleton-line w-60"></div></div></div>`;

  const [election, indexRaw] = await Promise.all([loadNIElection(id), loadNIIndex()]);
  const index = indexRaw || [];
  if (!election) { renderNotFound(app); return; }

  const winnerId = election.control;
  const winner = (winnerId && PARTIES?.[winnerId]) ? PARTIES[winnerId] : {};
  const color = winner.color || 'var(--gold)';
  const dim = winner.dim || 'var(--gold-dim)';
  const fm = election.firstMinister || '';
  const dfm = election.deputyFirstMinister || '';

  setPageMeta({
    title: `${election.displayYear} Northern Ireland Assembly election`,
    description: devolvedElectionDescription('stormont', election.displayYear, DEVOLVED_PORTALS?.stormont),
    path: `/devolved/stormont/${id}`,
  });

  const sorted = [...index].sort((a, b) => a.year - b.year);
  const pos = sorted.findIndex(e => e.id === id);
  const prev = pos > 0 ? sorted[pos - 1] : null;
  const next = pos >= 0 && pos < sorted.length - 1 ? sorted[pos + 1] : null;

  const summaryParas = (election.summary || '').split('\n\n').map(p => `<p>${p.trim()}</p>`).join('');
  const highlightItems = (election.highlights || []).map(h => `<div class="highlight-item"><div class="highlight-marker"></div><span>${h}</span></div>`).join('');

  let winnerBadge = '';
  if (fm && dfm) {
    winnerBadge = `<div class="election-winner-badge" style="--party-color:${color};--party-dim:${dim}"><div class="winner-dot"></div>${fm} (First Minister) & ${dfm} (deputy First Minister)</div>`;
  } else if (fm) {
    winnerBadge = `<div class="election-winner-badge" style="--party-color:${color};--party-dim:${dim}"><div class="winner-dot"></div>${fm} — First Minister</div>`;
  } else if (winnerId && PARTIES?.[winnerId]) {
    winnerBadge = `<div class="election-winner-badge" style="--party-color:${color};--party-dim:${dim}"><div class="winner-dot"></div>Largest party: ${PARTIES[winnerId].shortName}</div>`;
  }

  const turnoutLine = typeof election.turnout === 'number'
    ? `<div class="election-date">Turnout ${election.turnout.toFixed(1)}%</div>` : '';

  const manifestosSection = (election.manifestos || []).length
    ? `<div class="manifestos-section">
        <span class="section-label">Party Manifestos</span>
        <h2>Documents</h2>
        <p class="manifestos-intro">Manifestos published by parties contesting the ${election.displayYear} Northern Ireland Assembly election, ordered by seats won.</p>
        <div class="manifesto-grid">${niManifestosBySeats(election).map(m => niManifestoCard(m, election)).join('')}</div>
      </div>`
    : '';

  const sources = (election.sources || []).length
    ? `<div class="london-sources"><span class="section-label">Sources</span><ul>${election.sources.map(s => `<li><a href="${s.url}" target="_blank" rel="noopener">${s.label}</a></li>`).join('')}</ul></div>`
    : '';

  const chartResults = election.parliament?.results || [];
  const chartTotal = election.parliament?.totalSeats || 90;
  const hasChart = chartResults.length > 0;

  app.innerHTML = `
    ${renderBreadcrumb([
      { label: 'Home', href: '/' },
      { label: 'Beyond Westminster', href: '/devolved' },
      { label: 'Northern Ireland Assembly', href: '/devolved/stormont' },
      { label: election.displayYear },
    ])}
    <section class="election-hero" style="--party-glow:${dim}">
      <div class="election-hero-bg"></div>
      <div class="election-hero-inner">
        <div>
          <div class="election-eyebrow">Northern Ireland Assembly</div>
          <h1 class="election-title">${election.displayYear}</h1>
          <div class="election-date">${election.date}</div>
          ${turnoutLine}
          ${winnerBadge}
        </div>
        <div class="election-nav-btns">
          ${prev ? `<a class="election-nav-btn" href="/devolved/stormont/${prev.id}">← ${prev.displayYear}</a>` : ''}
          ${next ? `<a class="election-nav-btn" href="/devolved/stormont/${next.id}">${next.displayYear} →</a>` : ''}
        </div>
      </div>
    </section>

    <div class="election-body">
      <div class="election-grid">
        <div>
          ${summaryParas ? `<span class="section-label">Election Summary</span><div class="election-summary">${summaryParas}</div>` : ''}
          ${highlightItems ? `<div class="highlights-list"><h3>Key Moments</h3>${highlightItems}</div>` : ''}
          ${niParliamentSection(election)}
        </div>
        <div>
          ${hasChart ? `
          <div class="viz-panel">
            <div class="viz-tabs" role="tablist">
              <button type="button" class="viz-tab active" id="ni-tab-parliament" data-viz="parliament" role="tab" aria-selected="true" aria-controls="ni-viz-parliament" tabindex="0">Assembly</button>
              <button type="button" class="viz-tab" id="ni-tab-hexmap" data-viz="hexmap" role="tab" aria-selected="false" aria-controls="ni-viz-hexmap" tabindex="-1">Constituencies</button>
            </div>
            <div class="viz-pane active" id="ni-viz-parliament" role="tabpanel" aria-labelledby="ni-tab-parliament">
              <div class="parliament-card viz-card">
                <div class="parliament-card-title">Northern Ireland Assembly</div>
                <div class="parliament-card-sub">${chartTotal} seats · majority ${election.parliament?.majorityThreshold || 46}</div>
                <div id="stormont-chart-container"></div>
                <div class="parliament-legend" id="stormont-chart-legend"></div>
              </div>
            </div>
            <div class="viz-pane" id="ni-viz-hexmap" role="tabpanel" aria-labelledby="ni-tab-hexmap" hidden>
              <div class="parliament-card viz-card">
                <div class="parliament-card-title">Constituency Map</div>
                <div class="parliament-card-sub" id="ni-hexmap-subtitle">Plurality party per constituency (${election.year >= 2017 ? 5 : 6} MLAs each, STV)</div>
                <div id="stormont-hexmap-container" class="hexmap-container"></div>
                <div class="parliament-legend hexmap-legend" id="stormont-hexmap-legend" hidden></div>
              </div>
            </div>
          </div>` : ''}
        </div>
      </div>

      ${manifestosSection}
      ${sources}
    </div>
  `;

  if (hasChart) {
    requestAnimationFrame(async () => {
      const cont = document.getElementById('stormont-chart-container');
      const leg = document.getElementById('stormont-chart-legend');
      if (cont) drawParliamentChart(cont, chartResults, chartTotal);
      if (leg) buildParliamentLegend(leg, chartResults, election.year);

      // Wire up tab switching
      const tabs = document.querySelectorAll('#ni-tab-parliament, #ni-tab-hexmap');
      const panes = { parliament: document.getElementById('ni-viz-parliament'), hexmap: document.getElementById('ni-viz-hexmap') };
      let hexmapLoaded = false;

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
          loadNIHexLayout(election.year).then(hexjson => {
            const hexCont = document.getElementById('stormont-hexmap-container');
            const hexLeg = document.getElementById('stormont-hexmap-legend');
            if (!hexCont) return;
            if (!hexjson?.hexes) {
              hexCont.innerHTML = '<p class="hexmap-empty">Constituency map not yet available for this election.</p>';
              return;
            }
            const formatSeatsList = (seatsList, year) => {
              if (!Array.isArray(seatsList) || seatsList.length === 0) return '';
              const counts = {};
              seatsList.forEach(pid => {
                const pIdNormalized = (pid || 'others').toLowerCase().replace(/\s+/g, '');
                counts[pIdNormalized] = (counts[pIdNormalized] || 0) + 1;
              });
              const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
              return sorted.map(([pid, count]) => {
                const name = getPartyName(pid, year);
                return `${name} ${count}`;
              }).join(' · ');
            };

            const data = hexjsonToDrawData(hexjson, election.year);
            // Enrich tooltip: show seats won per constituency
            data.constituencies = data.constituencies.map(c => {
              const cell = hexjson.hexes[c.key];
              const seatsList = cell?.seats_list;
              let mpText = '';
              if (Array.isArray(seatsList) && seatsList.length > 0) {
                mpText = formatSeatsList(seatsList, election.year);
              } else {
                mpText = `${cell?.seats || 0} seats won · most by ${c.partyLabel}`;
              }
              return {
                ...c,
                mp: mpText,
              };
            });
            drawHexmap(hexCont, data, {
              legendEl: hexLeg,
              electionYear: election.year,
            });
            if (hexLeg) hexLeg.hidden = false;
          });
        }
      };

      tabs.forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.viz));
        tab.addEventListener('keydown', e => {
          if (e.key === 'ArrowRight') { e.preventDefault(); tabs[1]?.focus(); switchTab('hexmap'); }
          if (e.key === 'ArrowLeft')  { e.preventDefault(); tabs[0]?.focus(); switchTab('parliament'); }
        });
      });
    });
  }
}

async function renderNIPortal(app) {
  const portal = (typeof DEVOLVED_PORTALS !== 'undefined') ? DEVOLVED_PORTALS.stormont : null;
  setPageMeta({
    title: `${portal?.label || 'Northern Ireland Assembly'} Elections`,
    description: `Election results and party manifestos for the ${portal?.label || 'Northern Ireland Assembly'}.`,
    path: '/devolved/stormont',
  });

  const index = await loadNIIndex();
  if (!index) {
    if (typeof renderDataError === 'function') {
      renderDataError(app, {
        message: 'Northern Ireland Assembly election list failed to load.',
        onRetry: () => renderNIPortal(app),
      });
    } else {
      app.innerHTML = '<p role="alert">Northern Ireland Assembly election list failed to load.</p>';
    }
    return;
  }
  const sorted = index.slice().sort((a, b) => b.year - a.year);
  const cards = sorted.map(e => buildDevolvedTimelineCard(`/devolved/stormont/${e.id}`, e)).join('');

  const nation = (typeof NATIONS !== 'undefined') ? NATIONS['northern-ireland'] : null;
  const navConfig = (typeof NAV_PARTIES !== 'undefined') ? NAV_PARTIES['northern-ireland'] : null;
  const partyLinks = navConfig ? navConfig.parties.map(pid => nationPartyLinkHtml(pid)).join('') : '';

  app.innerHTML = `
    ${renderBreadcrumb([
      { label: 'Home', href: '/' },
      { label: 'Beyond Westminster', href: '/devolved' },
      { label: 'Northern Ireland Assembly' },
    ])}
    <section class="devolved-hero">
      <div class="devolved-hero-inner">
        <div>
          <span class="section-label">${portal?.subtitle || 'Stormont'}</span>
          <h1 class="devolved-hero-title">Northern Ireland Assembly</h1>
          <div class="gold-rule"></div>
          <p class="devolved-hero-desc">${portal?.description || 'The Northern Ireland Assembly at Stormont was established under the Good Friday Agreement in 1998. It has 90 MLAs elected by the Single Transferable Vote.'}</p>
          ${nation ? `<a href="/nation/northern-ireland" class="devolved-nation-link">View Northern Ireland nation page →</a>` : ''}
        </div>
        <div class="nation-parties-card devolved-hero-parties">
          <div class="section-label" style="margin-bottom:1rem">Parties in the Assembly</div>
          ${partyLinks}
          <a href="/devolved/stormont/other-parties" class="holyrood-other-link">Other Northern Irish parties →</a>
        </div>
      </div>
    </section>
    <div class="devolved-body">
      <div class="london-era">
        <div class="london-era-head"><h2>Stormont elections (1998–)</h2><p>Every Northern Ireland Assembly election since devolution, with results, seat charts, and archived party manifestos.</p></div>
        <div class="london-timeline-grid">${cards}</div>
      </div>
    </div>
  `;
}

function renderNIOtherParties(app) {
  setPageMeta({
    title: 'Other Northern Irish Parties',
    description: 'Smaller and specialist parties that have contested Northern Ireland Assembly elections.',
    path: '/devolved/stormont/other-parties',
  });

  const ids = (typeof STORMONT_OTHER_PARTIES !== 'undefined') ? STORMONT_OTHER_PARTIES : [];
  const cards = [...ids]
    .sort((a, b) => (PARTIES[a]?.name || a).localeCompare(PARTIES[b]?.name || b, 'en-GB'))
    .map(pid => buildPartyBrowseCard(pid, { fullName: true, meta: true }))
    .join('');

  app.innerHTML = `
    ${renderBreadcrumb([
      { label: 'Home', href: '/' },
      { label: 'Beyond Westminster', href: '/devolved' },
      { label: 'Northern Ireland Assembly', href: '/devolved/stormont' },
      { label: 'Other Northern Irish parties' },
    ])}
    <div class="about-section">
      <span class="section-label">Stormont</span>
      <h1>Other Northern Irish Parties</h1>
      <div class="gold-rule"></div>
      <p style="color:var(--text-muted);margin-bottom:1rem">Parties that have contested Northern Ireland Assembly elections but are not among the principal groups on the Stormont portal. Under the STV system, transfer patterns often play a critical role for these candidates.</p>
      <p style="color:var(--text-muted);margin-bottom:0.75rem">For parties that have contested Westminster seats:</p>
      <a href="/others" class="cross-archive-link">Other Parties →</a>
      <div class="others-grid">${cards}</div>
    </div>
  `;
}

async function getNIPartyHistory(partyId) {
  const index = (await loadNIIndex()) || [];
  const elections = [];
  const manifestos = [];
  await Promise.all(index.map(async (meta) => {
    const election = await loadNIElection(meta.id);
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

async function getNIManifestosForParty(partyId) {
  const { manifestos } = await getNIPartyHistory(partyId);
  return manifestos;
}

function niPartyElectionRow(partyId, { election, result }, maxSeats, color) {
  const isGov = election.control === partyId;
  const cls = isGov ? 'won' : result.seats > 0 ? 'lost' : 'lost';
  const label = isGov ? '✦ Government' : result.seats > 0 ? 'Opposition' : 'No seats';
  const pct = typeof result.pct === 'number' ? result.pct : null;
  const barW = ((result.seats / maxSeats) * 100).toFixed(1);
  const sub = isGov && election.firstMinister
    ? `${election.firstMinister} — First Minister`
    : 'Northern Ireland Assembly';
  return `<a class="party-election-row" href="/devolved/stormont/${election.id}">
    <div class="per-year">${election.displayYear}</div>
    <div><div class="per-outcome ${cls}">${label}</div><div style="font-size:0.78rem;color:var(--text-faint);margin-top:0.3rem">${sub}</div></div>
    <div class="per-seats-wrap"><div class="per-seats-num">${result.seats}</div><div class="per-seats-label">MLAs</div></div>
    <div class="per-bar-wrap"><div class="per-bar"><div class="per-bar-fill" style="width:${barW}%;background:${color}"></div></div><div class="per-pct">${pct != null ? pct.toFixed(1) + '% first-pref.' : '—'}</div></div>
  </a>`;
}
