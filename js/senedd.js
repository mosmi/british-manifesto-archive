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

/** Load Senedd HexJSON files */
const _seneddHexCache = new Map();
async function loadSeneddHexLayout(year) {
  if (_seneddHexCache.has(year)) return _seneddHexCache.get(year);
  try {
    const res = await fetch(`/data/hex/senedd/${year}.hexjson?v=${ASSETS_VERSION}`, { cache: 'no-cache' });
    if (!res.ok) return null;
    const data = await res.json();
    _seneddHexCache.set(year, data);
    return data;
  } catch (_) {
    return null;
  }
}

/** Render regional list side panel next to the hexmap (1999–2021) */
function renderSeneddRegionalPanel(panelEl, regionalList, electionYear) {
  if (!panelEl || !Array.isArray(regionalList) || regionalList.length === 0) return;

  panelEl.innerHTML = '';
  panelEl.hidden = false;

  const heading = document.createElement('div');
  heading.className = 'hexmap-outside-heading';
  heading.textContent = 'Regional List Seats';
  panelEl.appendChild(heading);

  const note = document.createElement('p');
  note.className = 'hexmap-outside-note';
  note.textContent = 'These 20 regional members are elected via closed party lists in five regions (4 seats each).';
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
      const colour = getPartyColor(member.party, electionYear);
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
  const pageId = resolvePartyId(row.party);
  const color = seneddPartyColor(pageId);
  const name = seneddPartyName(row, year);
  const inner = (pageId && PARTIES?.[pageId])
    ? devolvedPartyLink(pageId, name, year)
    : name;
  return `<div class="result-party-name"><div class="result-party-swatch" style="background:${color}"></div>${inner}</div>`;
}

function seneddIsClosedList(p) {
  return p?.system === 'Closed list proportional representation';
}

function seneddManifestoCard(m, electionOrYear) {
  const election = normalizeDevolvedElection(electionOrYear);
  return buildDevolvedManifestoCard(m, election, {
    color: seneddPartyColor(m.party),
    partyName: seneddPartyName(m, election.year),
  });
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
    description: devolvedElectionDescription('senedd', election.displayYear, DEVOLVED_PORTALS?.senedd),
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
        <div class="manifesto-grid">${seneddManifestosBySeats(election).map(m => seneddManifestoCard(m, election)).join('')}</div>
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
      { label: 'Beyond Westminster', href: '/devolved' },
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
          ${renderSupplementaryDocuments(election.supplementaryDocuments)}
          ${highlightItems ? `<div class="highlights-list"><h3>Key Moments</h3>${highlightItems}</div>` : ''}
          ${seneddParliamentSection(election)}
        </div>
        <div>
          ${hasChart ? `
          <div class="viz-panel">
            <div class="viz-tabs" role="tablist">
              <button type="button" class="viz-tab active" id="senedd-tab-parliament" data-viz="parliament" role="tab" aria-selected="true" aria-controls="senedd-viz-parliament" tabindex="0">Senedd</button>
              <button type="button" class="viz-tab" id="senedd-tab-hexmap" data-viz="hexmap" role="tab" aria-selected="false" aria-controls="senedd-viz-hexmap" tabindex="-1">Constituencies</button>
            </div>
            <div class="viz-pane active" id="senedd-viz-parliament" role="tabpanel" aria-labelledby="senedd-tab-parliament">
              <div class="parliament-card viz-card">
                <div class="parliament-card-title">Senedd Cymru</div>
                <div class="parliament-card-sub">${chartTotal} seats · majority ${election.parliament?.majorityThreshold || 31}</div>
                <div id="senedd-chart-container"></div>
                <div class="parliament-legend" id="senedd-chart-legend"></div>
              </div>
            </div>
            <div class="viz-pane" id="senedd-viz-hexmap" role="tabpanel" aria-labelledby="senedd-tab-hexmap" hidden>
              <div class="parliament-card viz-card">
                <div class="parliament-card-title">Constituency Map</div>
                <div class="parliament-card-sub" id="senedd-hexmap-subtitle">Constituency results</div>
                <div id="senedd-hexmap-container" class="hexmap-container"></div>
                <div class="parliament-legend hexmap-legend" id="senedd-hexmap-legend" hidden></div>
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
      const cont = document.getElementById('senedd-chart-container');
      const leg = document.getElementById('senedd-chart-legend');
      if (cont) drawParliamentChart(cont, chartResults, chartTotal);
      if (leg) buildParliamentLegend(leg, chartResults, election.year);

      // Wire up tab switching
      const tabs = document.querySelectorAll('#senedd-tab-parliament, #senedd-tab-hexmap');
      const panes = { parliament: document.getElementById('senedd-viz-parliament'), hexmap: document.getElementById('senedd-viz-hexmap') };
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
          loadSeneddHexLayout(election.year).then(hexjson => {
            const hexCont = document.getElementById('senedd-hexmap-container');
            const hexLeg = document.getElementById('senedd-hexmap-legend');
            const subtitleEl = document.getElementById('senedd-hexmap-subtitle');
            if (!hexCont) return;
            if (!hexjson?.hexes) {
              hexCont.innerHTML = '<p class="hexmap-empty">Constituency map not yet available for this election.</p>';
              return;
            }

            if (subtitleEl) {
              if (election.year === 2026) {
                subtitleEl.textContent = 'Constituency results (6 MSs each, closed-list PR)';
              } else {
                subtitleEl.textContent = 'Constituency results (first-past-the-post) + regional lists';
              }
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

            // Enrich constituency tooltip/details
            data.constituencies = data.constituencies.map(c => {
              const cell = hexjson.hexes[c.key];
              let mpText = '';
              let partyLabel = c.partyLabel;
              if (election.year === 2026) {
                mpText = formatSeatsList(cell?.seats_list, election.year);
                partyLabel = getPartyName(c.party, election.year) + ' plurality';
              } else {
                mpText = cell?.winner || 'Winner unknown';
              }
              return {
                ...c,
                mp: mpText,
                partyLabel: partyLabel,
              };
            });


            // If we have regional list seats, wrap in a two-column flex layout just like 1945
            if (hexjson.regional_list) {
              hexCont.innerHTML = '';
              const wrap = document.createElement('div');
              wrap.className = 'hexmap-1945-wrap';

              const mapCol = document.createElement('div');
              mapCol.className = 'hexmap-1945-map';

              const outsideCol = document.createElement('div');
              outsideCol.className = 'hexmap-outside-panel';
              outsideCol.id = 'senedd-regional-panel';

              wrap.appendChild(mapCol);
              wrap.appendChild(outsideCol);
              hexCont.appendChild(wrap);

              drawHexmap(mapCol, data, {
                legendEl: null,
                electionYear: election.year,
                electionId: election.id
              });

              renderSeneddRegionalPanel(outsideCol, hexjson.regional_list, election.year);
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

async function renderSeneddPortal(app) {
  const portal = (typeof DEVOLVED_PORTALS !== 'undefined') ? DEVOLVED_PORTALS.senedd : null;
  setPageMeta({
    title: `${portal?.label || 'Welsh Parliament'} Elections`,
    description: `Election results and party manifestos for the ${portal?.label || 'Welsh Parliament'}.`,
    path: '/devolved/senedd',
  });

  const index = await loadSeneddIndex();
  const sorted = index.slice().sort((a, b) => b.year - a.year);
  const cards = sorted.map(e => buildDevolvedTimelineCard(`/devolved/senedd/${e.id}`, e)).join('');

  const nation = (typeof NATIONS !== 'undefined') ? NATIONS.wales : null;
  const navConfig = (typeof NAV_PARTIES !== 'undefined') ? NAV_PARTIES.wales : null;
  const partyLinks = navConfig ? navConfig.parties.map(pid => nationPartyLinkHtml(pid)).join('') : '';

  app.innerHTML = `
    ${renderBreadcrumb([
      { label: 'Home', href: '/' },
      { label: 'Beyond Westminster', href: '/devolved' },
      { label: 'Welsh Parliament' },
    ])}
    <section class="devolved-hero">
      <div class="devolved-hero-inner">
        <div>
          <span class="section-label">${portal?.subtitle || 'Senedd Cymru'}</span>
          <h1 class="devolved-hero-title">Welsh Parliament</h1>
          <div class="gold-rule"></div>
          <p class="devolved-hero-desc">${portal?.description || 'The Senedd Cymru elects Members of the Senedd under the Additional Member System (1999–2021) and closed-list proportional representation from 2026.'}</p>
          ${nation ? `<a href="/nation/${portal?.nation || 'wales'}" class="devolved-nation-link">View Wales nation page →</a>` : ''}
        </div>
        <div class="nation-parties-card devolved-hero-parties">
          <div class="section-label" style="margin-bottom:1rem">Parties in the Senedd</div>
          ${partyLinks}
          <a href="/devolved/senedd/other-parties" class="holyrood-other-link">Other Welsh parties →</a>
        </div>
      </div>
    </section>
    <div class="devolved-body">
      <div class="london-era">
        <div class="london-era-head"><h2>Senedd elections (1999–)</h2><p>Every Welsh Parliament election since devolution, with results, seat charts, and archived party manifestos.</p></div>
        <div class="london-timeline-grid">${cards}</div>
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
    .map(pid => buildPartyBrowseCard(pid, { fullName: true, meta: true }))
    .join('');

  app.innerHTML = `
    ${renderBreadcrumb([
      { label: 'Home', href: '/' },
      { label: 'Beyond Westminster', href: '/devolved' },
      { label: 'Welsh Parliament', href: '/devolved/senedd' },
      { label: 'Other Welsh parties' },
    ])}
    <div class="about-section">
      <span class="section-label">Senedd Cymru</span>
      <h1>Other Welsh Parties</h1>
      <div class="gold-rule"></div>
      <p style="color:var(--text-muted);margin-bottom:1rem">Parties that have contested Senedd elections but are not among the principal groups on the Welsh Parliament portal. Many appear only on the regional list under AMS.</p>
      <p style="color:var(--text-muted);margin-bottom:0.75rem">For parties that have contested Westminster seats:</p>
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
