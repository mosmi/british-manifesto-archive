/* ============================================================
   THE BRITISH MANIFESTO ARCHIVE — Holyrood elections
   Scottish Parliament elections (1999–)
   ============================================================ */

let _holyroodIndex = null;

async function loadHolyroodIndex() {
  if (_holyroodIndex) return _holyroodIndex;
  try {
    _holyroodIndex = await fetchTyped('/data/devolved/holyrood/index.json', 'json');
    return _holyroodIndex;
  } catch {
    return null;
  }
}

async function loadHolyroodElection(id) {
  try {
    return await fetchTyped(`/data/devolved/holyrood/${id}.json`, 'json');
  } catch {
    return null;
  }
}

/** Load Holyrood HexJSON files */
const _holyroodHexCache = new Map();
async function loadHolyroodHexLayout(year) {
  if (_holyroodHexCache.has(year)) return _holyroodHexCache.get(year);
  try {
    const res = await fetch(`/data/hex/holyrood/${year}.hexjson?v=${ASSETS_VERSION}`, { cache: 'no-cache' });
    if (!res.ok) return null;
    const data = await res.json();
    _holyroodHexCache.set(year, data);
    return data;
  } catch (_) {
    return null;
  }
}

/** Render regional list side panel next to the hexmap */
function renderHolyroodRegionalPanel(panelEl, regionalList, electionYear) {
  if (!panelEl || !Array.isArray(regionalList) || regionalList.length === 0) return;

  panelEl.innerHTML = '';
  panelEl.hidden = false;

  const heading = document.createElement('div');
  heading.className = 'hexmap-outside-heading';
  heading.textContent = 'Regional List Seats';
  panelEl.appendChild(heading);

  const note = document.createElement('p');
  note.className = 'hexmap-outside-note';
  note.textContent = 'These 56 regional members are elected via closed party lists in eight regions (7 seats each).';
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
      const colour = holyroodPartyColor(member.party);
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
  const pageId = resolvePartyId(row.party);
  const color = holyroodPartyColor(pageId);
  const name = holyroodPartyName(row, year);
  const inner = (pageId && PARTIES?.[pageId])
    ? devolvedPartyLink(pageId, name, year)
    : name;
  return `<div class="result-party-name"><div class="result-party-swatch" style="background:${color}"></div>${inner}</div>`;
}

function holyroodManifestoCard(m, electionOrYear) {
  const election = normalizeDevolvedElection(electionOrYear);
  return buildDevolvedManifestoCard(m, election, {
    color: holyroodPartyColor(m.party),
    partyName: holyroodPartyName(m, election.year),
  });
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
        <table class="results-table"><thead><tr><th scope="col">Party</th><th scope="col">List votes</th><th scope="col">%</th></tr></thead>
        <tbody>${p.otherListVotes.map(o => `<tr><td>${o.name}</td><td style="color:var(--text-muted)">${typeof o.votes === 'number' ? holyroodNum(o.votes) : '—'}</td><td style="color:var(--text-muted)">${typeof o.pct === 'number' ? o.pct.toFixed(1) + '%' : '—'}</td></tr>`).join('')}</tbody></table>
      </details>`
    : '';
  return `
    <div class="results-section">
      <span class="section-label">Scottish Parliament · ${p.system || 'Additional Member System'}</span>
      <h2>Parliament Result</h2>
      <table class="results-table london-assembly-table">
        <thead><tr><th scope="col">Party</th><th scope="col" title="Constituency seats" style="text-align:center">Const.</th><th scope="col" title="Regional list seats" style="text-align:center">List</th><th scope="col">Seats (of ${p.totalSeats})</th><th scope="col">Const. %</th><th scope="col">List %</th></tr></thead>
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

  const [election, indexRaw] = await Promise.all([loadHolyroodElection(id), loadHolyroodIndex()]);
  const index = indexRaw || [];
  if (!election) { renderNotFound(app); return; }

  const winnerId = election.control;
  const winner = (winnerId && PARTIES?.[winnerId]) ? PARTIES[winnerId] : {};
  const badge = typeof winnerBadgeStyle === 'function'
    ? winnerBadgeStyle(winnerId, election.year)
    : { dim: winner.dim || 'var(--gold-dim)', css: `--party-color:${winner.color || 'var(--gold)'};--party-dim:${winner.dim || 'var(--gold-dim)'}` };
  const fm = election.firstMinister || '';

  setPageMeta({ title: `${election.displayYear} Scottish Parliament election`, description: devolvedElectionDescription('holyrood', election.displayYear, DEVOLVED_PORTALS?.holyrood), path: `/devolved/holyrood/${id}` });

  const sorted = [...index].sort((a, b) => a.year - b.year);
  const pos = sorted.findIndex(e => e.id === id);
  const prev = pos > 0 ? sorted[pos - 1] : null;
  const next = pos >= 0 && pos < sorted.length - 1 ? sorted[pos + 1] : null;

  const summaryParas = (election.summary || '').split('\n\n').map(p => `<p>${p.trim()}</p>`).join('');
  const highlightItems = (election.highlights || []).map(h => `<div class="highlight-item"><div class="highlight-marker"></div><span>${h}</span></div>`).join('');

  const majorityNote = election.majority ? ' — majority government' : election.parliament?.results?.find(r => r.party === winnerId)?.seats >= (election.parliament?.majorityThreshold || 65) - 1 ? '' : ' — minority government';
  const winnerBadge = fm
    ? `<div class="election-winner-badge" style="${badge.css}"><div class="winner-dot"></div>${fm} — First Minister${majorityNote}</div>`
    : '';

  const turnoutLine = typeof election.turnout === 'number'
    ? `<div class="election-date">Turnout ${election.turnout.toFixed(1)}%</div>` : '';

  const manifestosSection = (election.manifestos || []).length
    ? `<div class="manifestos-section">
        <span class="section-label">Party Manifestos</span>
        <h2>Documents</h2>
        <p class="manifestos-intro">Manifestos published by parties contesting the ${election.displayYear} Scottish Parliament election, ordered by seats won.</p>
        <div class="manifesto-grid">${holyroodManifestosBySeats(election).map(m => holyroodManifestoCard(m, election)).join('')}</div>
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
      { label: 'Beyond Westminster', href: '/devolved' },
      { label: 'Scottish Parliament', href: '/devolved/holyrood' },
      { label: election.displayYear },
    ])}
    <section class="election-hero" style="--party-glow:${badge.dim}">
      <div class="election-hero-bg"></div>
      <div class="election-hero-inner">
        <div>
          <div class="election-eyebrow">Scottish Parliament</div>
          <h1 class="election-title">${election.displayYear}</h1>
          <div class="election-date">${election.date}</div>
          ${turnoutLine}
          ${winnerBadge}
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
            <div class="viz-tabs" role="tablist">
              <button type="button" class="viz-tab active" id="holyrood-tab-parliament" data-viz="parliament" role="tab" aria-selected="true" aria-controls="holyrood-viz-parliament" tabindex="0">Parliament</button>
              <button type="button" class="viz-tab" id="holyrood-tab-hexmap" data-viz="hexmap" role="tab" aria-selected="false" aria-controls="holyrood-viz-hexmap" tabindex="-1">Constituencies</button>
            </div>
            <div class="viz-pane active" id="holyrood-viz-parliament" role="tabpanel" aria-labelledby="holyrood-tab-parliament">
              <div class="parliament-card viz-card">
                <div class="parliament-card-title">Scottish Parliament</div>
                <div class="parliament-card-sub">${chartTotal} seats · majority ${election.parliament?.majorityThreshold || 65}</div>
                <div id="holyrood-chart-container"></div>
                <div class="parliament-legend" id="holyrood-chart-legend"></div>
              </div>
            </div>
            <div class="viz-pane" id="holyrood-viz-hexmap" role="tabpanel" aria-labelledby="holyrood-tab-hexmap" hidden>
              <div class="parliament-card viz-card">
                <div class="parliament-card-title">Constituency Map</div>
                <div class="parliament-card-sub" id="holyrood-hexmap-subtitle">Constituency results</div>
                <div id="holyrood-hexmap-container" class="hexmap-container"></div>
                <div class="parliament-legend hexmap-legend" id="holyrood-hexmap-legend" hidden></div>
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
    requestAnimationFrame(() => {
      const cont = document.getElementById('holyrood-chart-container');
      const leg = document.getElementById('holyrood-chart-legend');
      if (cont) drawParliamentChart(cont, chartResults, chartTotal);
      if (leg) buildParliamentLegend(leg, chartResults, election.year);

      // Wire up tab switching
      const tabs = document.querySelectorAll('#holyrood-tab-parliament, #holyrood-tab-hexmap');
      const panes = { parliament: document.getElementById('holyrood-viz-parliament'), hexmap: document.getElementById('holyrood-viz-hexmap') };
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
          loadHolyroodHexLayout(election.year).then(hexjson => {
            const hexCont = document.getElementById('holyrood-hexmap-container');
            const hexLeg = document.getElementById('holyrood-hexmap-legend');
            const subtitleEl = document.getElementById('holyrood-hexmap-subtitle');
            if (!hexCont) return;
            if (!hexjson?.hexes) {
              hexCont.innerHTML = '<p class="hexmap-empty">Constituency map not yet available for this election.</p>';
              return;
            }

            if (subtitleEl) {
              subtitleEl.textContent = 'Constituency results (first-past-the-post) + regional lists';
            }

            const data = hexjsonToDrawData(hexjson, election.year);

            // Enrich constituency tooltip/details
            data.constituencies = data.constituencies.map(c => {
              const cell = hexjson.hexes[c.key];
              const mpText = cell?.winner || 'Winner unknown';
              return {
                ...c,
                mp: mpText,
              };
            });

            // If we have regional list seats, wrap in a two-column flex layout
            if (hexjson.regional_list) {
              hexCont.innerHTML = '';
              const wrap = document.createElement('div');
              wrap.className = 'hexmap-1945-wrap';

              const mapCol = document.createElement('div');
              mapCol.className = 'hexmap-1945-map';

              const outsideCol = document.createElement('div');
              outsideCol.className = 'hexmap-outside-panel';
              outsideCol.id = 'holyrood-regional-panel';

              wrap.appendChild(mapCol);
              wrap.appendChild(outsideCol);
              hexCont.appendChild(wrap);

              drawHexmap(mapCol, data, {
                legendEl: null,
                electionYear: election.year,
                electionId: election.id
              });

              renderHolyroodRegionalPanel(outsideCol, hexjson.regional_list, election.year);
            } else {
              drawHexmap(hexCont, data, {
                legendEl: null,
                electionYear: election.year,
                electionId: election.id
              });
            }

            // Build aggregated legend
            if (hexLeg) {
              const constsForLegend = [...data.constituencies];
              if (hexjson.regional_list) {
                hexjson.regional_list.forEach(reg => {
                  reg.members.forEach(member => {
                    constsForLegend.push({
                      party: member.party,
                      partyLabel: getPartyName(member.party, election.year)
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
          if (e.key === 'ArrowLeft')  { e.preventDefault(); tabs[0]?.focus(); switchTab('parliament'); }
        });
      });
    });
  }
}

async function renderHolyroodPortal(app) {
  const portal = (typeof DEVOLVED_PORTALS !== 'undefined') ? DEVOLVED_PORTALS.holyrood : null;
  setPageMeta({
    title: `${portal?.label || 'Scottish Parliament'} Elections`,
    description: `Election results and party manifestos for the ${portal?.label || 'Scottish Parliament'}.`,
    path: '/devolved/holyrood',
  });

  const index = await loadHolyroodIndex();
  if (!index) {
    if (typeof renderDataError === 'function') {
      renderDataError(app, {
        message: 'Scottish Parliament election list failed to load.',
        onRetry: () => renderHolyroodPortal(app),
      });
    } else {
      app.innerHTML = '<p role="alert">Scottish Parliament election list failed to load.</p>';
    }
    return;
  }
  const sorted = index.slice().sort((a, b) => b.year - a.year);
  const cards = sorted.map(e => buildDevolvedTimelineCard(`/devolved/holyrood/${e.id}`, e)).join('');

  const nation = (typeof NATIONS !== 'undefined') ? NATIONS.scotland : null;
  const navConfig = (typeof NAV_PARTIES !== 'undefined') ? NAV_PARTIES.scotland : null;
  const partyLinks = navConfig ? navConfig.parties.map(pid => nationPartyLinkHtml(pid)).join('') : '';

  app.innerHTML = `
    ${renderBreadcrumb([
      { label: 'Home', href: '/' },
      { label: 'Beyond Westminster', href: '/devolved' },
      { label: 'Scottish Parliament' },
    ])}
    <section class="devolved-hero">
      <div class="devolved-hero-inner">
        <div>
          <span class="section-label">${portal?.subtitle || 'Holyrood'}</span>
          <h1 class="devolved-hero-title">Scottish Parliament</h1>
          <div class="gold-rule"></div>
          <p class="devolved-hero-desc">${portal?.description || 'The Scottish Parliament at Holyrood elects 129 MSPs every five years under the Additional Member System.'}</p>
          ${nation ? `<a href="/nation/${portal?.nation || 'scotland'}" class="devolved-nation-link">View Scotland nation page →</a>` : ''}
        </div>
        <div class="nation-parties-card devolved-hero-parties">
          <div class="section-label" style="margin-bottom:1rem">Parties in the Scottish Parliament</div>
          ${partyLinks}
          <a href="/devolved/holyrood/other-parties" class="holyrood-other-link">Other Scottish parties →</a>
        </div>
      </div>
    </section>
    <div class="devolved-body">
      <div class="london-era">
        <div class="london-era-head"><h2>Holyrood elections (1999–)</h2><p>Every Scottish Parliament election since devolution, with results, seat charts, and archived party manifestos.</p></div>
        <div class="timeline-grid">${cards}</div>
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
    .map(pid => buildPartyBrowseCard(pid, { fullName: true, meta: true }))
    .join('');

  app.innerHTML = `
    ${renderBreadcrumb([
      { label: 'Home', href: '/' },
      { label: 'Beyond Westminster', href: '/devolved' },
      { label: 'Scottish Parliament', href: '/devolved/holyrood' },
      { label: 'Other Scottish parties' },
    ])}
    <div class="about-section">
      <span class="section-label">Holyrood</span>
      <h1>Other Scottish Parties</h1>
      <div class="gold-rule"></div>
      <p style="color:var(--text-muted);margin-bottom:1rem">Parties that have contested Scottish Parliament elections but are not among the principal groups on the Holyrood portal. Many appear only on the regional list under AMS.</p>
      <p style="color:var(--text-muted);margin-bottom:0.75rem">For parties that have contested Westminster seats:</p>
      <a href="/others" class="cross-archive-link">Other Parties →</a>
      <div class="others-grid">${cards}</div>
    </div>
  `;
}

/** Holyrood manifestos and election results for a party (party pages). */
async function getHolyroodPartyHistory(partyId) {
  const index = (await loadHolyroodIndex()) || [];
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
