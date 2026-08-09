/* ============================================================
   THE BRITISH MANIFESTO ARCHIVE — European Parliament region map
   Geographic regions + seat-square clusters (PR era, 1999–2019)
   ============================================================ */

const _euroRegionLayoutCache = new Map();
const _euroRegionResultsCache = new Map();

async function loadEuroRegionLayout() {
  if (_euroRegionLayoutCache.has('v1')) return _euroRegionLayoutCache.get('v1');
  try {
    const res = await fetch(`/data/maps/euro-regions.json?v=${ASSETS_VERSION}`, { cache: 'no-cache' });
    if (!res.ok) throw new Error(res.statusText);
    const data = await res.json();
    _euroRegionLayoutCache.set('v1', data);
    return data;
  } catch {
    return null;
  }
}

async function loadEuroRegionResults(year) {
  const key = String(year);
  if (_euroRegionResultsCache.has(key)) return _euroRegionResultsCache.get(key);
  try {
    const res = await fetch(`/data/devolved/euro/regions/${year}.json?v=${ASSETS_VERSION}`, { cache: 'no-cache' });
    if (!res.ok) throw new Error(res.statusText);
    const data = await res.json();
    _euroRegionResultsCache.set(key, data);
    return data;
  } catch {
    return null;
  }
}

/**
 * Per-region waffle layouts (Commons Library style).
 * Keyed by region id → optional seat-count overrides, then a default.
 * `cols` = rectangular grid; `rows` = irregular row lengths (e.g. West Midlands 3-2-2).
 */
const EURO_SEAT_GRIDS = {
  scotland: { 8: { cols: 4 }, 7: { cols: 4 }, default: { cols: 3 } },
  'northern-ireland': { default: { cols: 2 } },
  'north-east': { 4: { cols: 2 }, default: { cols: 2 } },
  'north-west': { 10: { cols: 2 }, 9: { rows: [3, 3, 3] }, default: { cols: 2 } },
  'yorkshire-humber': { 7: { cols: 4 }, default: { cols: 3 } },
  'east-midlands': { 6: { cols: 3 }, default: { cols: 3 } },
  'west-midlands': {
    8: { cols: 4 },
    7: { rows: [3, 2, 2] },
    6: { cols: 3 },
    default: { rows: [3, 2, 2] },
  },
  wales: { 5: { cols: 3 }, default: { cols: 2 } },
  'east-of-england': { 8: { cols: 4 }, default: { cols: 4 } },
  london: { 10: { cols: 5 }, 9: { rows: [3, 3, 3] }, default: { cols: 4 } },
  'south-east': { 11: { rows: [4, 4, 3] }, default: { cols: 5 } },
  'south-west': { 7: { cols: 4 }, default: { cols: 3 } },
};

/** Fallback rectangular cols when a region has no explicit layout. */
function euroSeatGridCols(seats) {
  if (seats <= 3) return Math.max(1, seats);
  if (seats <= 6) return 3;
  if (seats <= 8) return 4;
  return 5;
}

/** Resolve waffle grid for a region given its seat magnitude that year. */
function euroSeatGridFor(regionId, seatCount) {
  const spec = EURO_SEAT_GRIDS[regionId];
  if (!spec) return { cols: euroSeatGridCols(seatCount) };
  if (spec.cols != null || spec.rows != null) return spec; // legacy flat form
  return spec[seatCount] || spec.default || { cols: euroSeatGridCols(seatCount) };
}

/**
 * Seat colours in Commons Library order: parties grouped, largest seat haul first
 * (Scotland → SNP×3, Brexit, Lib Dem, Con — not d’Hondt election order).
 */
function euroSeatsForWaffle(regionData) {
  const results = regionData?.results || [];
  if (results.length) {
    const seats = [];
    results.forEach(r => {
      for (let i = 0; i < (r.seats || 0); i++) {
        seats.push({ party: r.party, partyLabel: r.partyLabel });
      }
    });
    if (seats.length) return seats;
  }
  return (regionData?.members || []).map(m => ({
    party: m.party,
    partyLabel: m.partyLabel,
  }));
}

/** Cell positions for a rectangular or irregular waffle, centred on (0,0). */
function euroWaffleCells(seatCount, gridSpec, size, gap) {
  const step = size + gap;
  let rowLengths;
  if (gridSpec?.rows?.length) {
    rowLengths = gridSpec.rows.slice();
  } else {
    const cols = gridSpec?.cols || euroSeatGridCols(seatCount);
    const rows = Math.ceil(seatCount / cols);
    rowLengths = [];
    let remaining = seatCount;
    for (let r = 0; r < rows; r++) {
      const n = Math.min(cols, remaining);
      rowLengths.push(n);
      remaining -= n;
    }
  }
  const maxCols = Math.max(...rowLengths, 1);
  const gridW = maxCols * size + (maxCols - 1) * gap;
  const gridH = rowLengths.length * size + (rowLengths.length - 1) * gap;
  const cells = [];
  let i = 0;
  rowLengths.forEach((n, row) => {
    const rowW = n * size + (n - 1) * gap;
    const x0 = -gridW / 2 + (gridW - rowW) / 2; // centre short rows
    for (let col = 0; col < n && i < seatCount; col++, i++) {
      cells.push({
        x: x0 + col * step,
        y: -gridH / 2 + row * step,
      });
    }
  });
  return { cells, gridW, gridH };
}

function euroSeatPartyLabel(party, year, partyLabel) {
  if (partyLabel) return partyLabel;
  if (typeof getPartyName === 'function') return getPartyName(party, year);
  return party;
}

function euroSeatColor(party, year) {
  return (typeof getPartyColor === 'function') ? getPartyColor(party, year) : '#6b7280';
}

/**
 * Draw interactive UK EP regional seat map into containerEl.
 * @param {HTMLElement} containerEl
 * @param {object} layout - data/maps/euro-regions.json
 * @param {object} results - data/devolved/euro/regions/<year>.json
 * @param {object} opts
 * @param {number} opts.year
 * @param {HTMLElement|null} opts.legendEl
 * @param {HTMLElement|null} opts.detailEl
 * @param {Array} opts.nationalResults - election.parliament.results for legend
 */
function drawEuroRegionMap(containerEl, layout, results, opts = {}) {
  if (!containerEl || !layout?.regions || !results?.regions) return;

  const year = opts.year;
  const detailEl = opts.detailEl || null;
  const legendEl = opts.legendEl || null;

  const byId = new Map(results.regions.map(r => [r.id, r]));
  const vb = layout.viewBox || [0, 0, 420, 560];
  const [vx, vy, vw, vh] = vb;

  containerEl.innerHTML = '';
  containerEl.classList.add('euro-map-root');

  const wrap = document.createElement('div');
  wrap.className = 'euro-map-svg-wrap';

  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', `${vx} ${vy} ${vw} ${vh}`);
  svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label', 'UK European Parliament electoral regions and seat winners');
  svg.classList.add('euro-map-svg');

  const tooltip = document.createElement('div');
  tooltip.className = 'hexmap-tooltip euro-map-tooltip';
  tooltip.hidden = true;

  let selectedId = null;

  const showTooltip = (region, clientX, clientY) => {
    const data = byId.get(region.id);
    if (!data) return;
    const lines = (data.results || []).map(r => {
      const name = euroSeatPartyLabel(r.party, year, r.partyLabel);
      const pct = typeof r.pct === 'number' ? ` · ${r.pct}%` : '';
      return `${name} ${r.seats}${pct}`;
    });
    const turnout = typeof data.turnout === 'number' ? `<span>Turnout ${data.turnout.toFixed(1)}%</span>` : '';
    tooltip.innerHTML = `<strong>${data.name}</strong><span>${data.seats} seats</span>${turnout}<span>${lines.join('<br>')}</span>`;
    tooltip.hidden = false;
    const rect = wrap.getBoundingClientRect();
    const tx = clientX - rect.left + 12;
    const ty = clientY - rect.top + 12;
    tooltip.style.left = `${Math.min(tx, rect.width - 180)}px`;
    tooltip.style.top = `${Math.min(ty, rect.height - 80)}px`;
  };

  const hideTooltip = () => { tooltip.hidden = true; };

  const renderDetail = (regionId) => {
    if (!detailEl) return;
    const data = byId.get(regionId);
    if (!data) {
      detailEl.innerHTML = '<p class="hexmap-detail-placeholder">Select a region to see elected MEPs.</p>';
      return;
    }
    const members = (data.members || []).map(m => {
      const color = euroSeatColor(m.party, year);
      const pname = euroSeatPartyLabel(m.party, year, m.partyLabel);
      const pageId = typeof resolvePartyId === 'function' ? resolvePartyId(m.party) : m.party;
      const partyHtml = (pageId && typeof PARTIES !== 'undefined' && PARTIES[pageId] && typeof devolvedPartyLink === 'function')
        ? devolvedPartyLink(pageId, pname, year)
        : pname;
      return `<li class="euro-map-mep">
        <span class="euro-map-mep-swatch" style="background:${color}"></span>
        <span class="euro-map-mep-name">${m.name}</span>
        <span class="euro-map-mep-party">${partyHtml}</span>
      </li>`;
    }).join('');

    detailEl.innerHTML = `
      <div class="hexmap-detail-inner euro-map-detail-inner">
        <div>
          <div class="hexmap-detail-name">${data.name}</div>
          <div class="hexmap-detail-mp">${data.seats} MEPs${typeof data.turnout === 'number' ? ` · turnout ${data.turnout.toFixed(1)}%` : ''}</div>
          <ul class="euro-map-mep-list">${members}</ul>
        </div>
      </div>`;
  };

  const setSelected = (regionId) => {
    selectedId = regionId;
    svg.querySelectorAll('.euro-map-region').forEach(el => {
      el.classList.toggle('is-selected', el.dataset.regionId === regionId);
    });
    renderDetail(regionId);
  };

  // Region fills
  const regionsG = document.createElementNS('http://www.w3.org/2000/svg', 'g');
  regionsG.setAttribute('class', 'euro-map-regions');

  layout.regions.forEach(region => {
    const data = byId.get(region.id);
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', region.path);
    path.setAttribute('class', 'euro-map-region');
    path.dataset.regionId = region.id;
    path.setAttribute('tabindex', '0');
    path.setAttribute('role', 'button');
    path.setAttribute('aria-label', data ? `${data.name}, ${data.seats} seats` : region.label);

    // Tint by largest party
    const top = data?.results?.[0];
    const fill = top ? euroSeatColor(top.party, year) : 'rgba(148,163,184,0.25)';
    path.style.fill = top ? `${fill}33` : 'rgba(148,163,184,0.18)';
    path.style.stroke = 'rgba(226,232,240,0.55)';
    path.style.strokeWidth = '1';

    const onActivate = () => setSelected(region.id);
    path.addEventListener('click', onActivate);
    path.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onActivate(); }
    });
    path.addEventListener('mousemove', e => showTooltip(region, e.clientX, e.clientY));
    path.addEventListener('mouseleave', hideTooltip);
    path.addEventListener('focus', () => {
      const box = path.getBoundingClientRect();
      showTooltip(region, box.left + box.width / 2, box.top + box.height / 2);
    });
    path.addEventListener('blur', hideTooltip);

    regionsG.appendChild(path);
  });
  svg.appendChild(regionsG);

  // Seat clusters + labels
  const seatsG = document.createElementNS('http://www.w3.org/2000/svg', 'g');
  seatsG.setAttribute('class', 'euro-map-seats');

  layout.regions.forEach(region => {
    const data = byId.get(region.id);
    if (!data) return;

    // Party-grouped colours + Commons Library grid shapes (not d’Hondt order)
    const seats = euroSeatsForWaffle(data);
    const gridSpec = euroSeatGridFor(region.id, seats.length);
    const size = seats.length >= 10 ? 8 : seats.length >= 7 ? 9 : 10;
    const gap = 2;
    const { cells, gridW, gridH } = euroWaffleCells(seats.length, gridSpec, size, gap);

    if (region.callout) {
      const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line.setAttribute('x1', region.attachX);
      line.setAttribute('y1', region.attachY);
      line.setAttribute('x2', region.seatX - gridW / 2 - 4);
      line.setAttribute('y2', region.seatY);
      line.setAttribute('class', 'euro-map-callout-line');
      seatsG.appendChild(line);
    }

    const cluster = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    cluster.setAttribute('class', 'euro-map-cluster');
    cluster.dataset.regionId = region.id;
    cluster.style.cursor = 'pointer';

    seats.forEach((seat, i) => {
      const cell = cells[i];
      if (!cell) return;
      const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      rect.setAttribute('x', region.seatX + cell.x);
      rect.setAttribute('y', region.seatY + cell.y);
      rect.setAttribute('width', size);
      rect.setAttribute('height', size);
      rect.setAttribute('rx', 1.2);
      rect.setAttribute('fill', euroSeatColor(seat.party, year));
      rect.setAttribute('class', 'euro-map-seat');
      cluster.appendChild(rect);
    });

    const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    label.setAttribute('x', region.seatX);
    label.setAttribute('text-anchor', 'middle');
    label.setAttribute('class', 'euro-map-label');
    const labelText = region.label || data.name || '';
    const labelLines = labelText.split(/\n/);
    const labelGap = 5; // same gap as single-line labels (e.g. Wales)
    const labelLineH = 9;
    const waffleTop = region.seatY - gridH / 2;
    // Last line sits labelGap above the waffle; earlier lines stack upward
    const lastLineY = waffleTop - labelGap;
    const firstLineY = lastLineY - (labelLines.length - 1) * labelLineH;
    label.setAttribute('y', firstLineY);
    if (labelLines.length > 1) {
      labelLines.forEach((line, li) => {
        const tspan = document.createElementNS('http://www.w3.org/2000/svg', 'tspan');
        tspan.setAttribute('x', region.seatX);
        tspan.setAttribute('dy', li === 0 ? '0' : String(labelLineH));
        tspan.textContent = line;
        label.appendChild(tspan);
      });
    } else {
      label.textContent = labelText;
    }
    cluster.appendChild(label);

    const activate = () => setSelected(region.id);
    cluster.addEventListener('click', activate);
    cluster.addEventListener('mousemove', e => showTooltip(region, e.clientX, e.clientY));
    cluster.addEventListener('mouseleave', hideTooltip);

    seatsG.appendChild(cluster);
  });
  svg.appendChild(seatsG);

  wrap.appendChild(svg);
  wrap.appendChild(tooltip);
  containerEl.appendChild(wrap);

  if (detailEl) {
    detailEl.classList.add('hexmap-detail', 'euro-map-detail');
    detailEl.innerHTML = '<p class="hexmap-detail-placeholder">Select a region to see elected MEPs.</p>';
  }

  if (legendEl) {
    const national = opts.nationalResults || [];
    const forLegend = national
      .filter(r => r.seats > 0)
      .map(r => ({
        party: r.party,
        partyLabel: r.partyLabel || euroSeatPartyLabel(r.party, year, r.partyLabel),
      }));
    // Expand by seat count so legend counts match
    const expanded = [];
    national.filter(r => r.seats > 0).forEach(r => {
      for (let i = 0; i < r.seats; i++) {
        expanded.push({ party: r.party, partyLabel: r.partyLabel });
      }
    });
    if (typeof buildHexmapLegend === 'function') {
      buildHexmapLegend(legendEl, expanded.length ? expanded : forLegend, year);
      legendEl.hidden = false;
    }
  }
}
