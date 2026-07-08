/* ============================================================
   THE BRITISH MANIFESTO ARCHIVE — Hexmap (Constituency Cartogram)
   Interactive SVG hex grid for Westminster election results
   Coordinate system aligned with ODI HexJSON / odi.hexmap.js
   ============================================================ */

const HEX_SQRT3 = Math.sqrt(3);

/** Apply odd/even row/column offset used by HexJSON layouts. */
function updateHexPos(q, r, layout) {
  let pq = q;
  let pr = r;
  if (layout === 'odd-r' && (r % 2) !== 0) pq += 0.5;
  if (layout === 'even-r' && (r % 2) === 0) pq += 0.5;
  if (layout === 'odd-q' && (q % 2) !== 0) pr += 0.5;
  if (layout === 'even-q' && (q % 2) === 0) pr += 0.5;
  return { q: pq, r: pr };
}

function isPointyLayout(layout) {
  return layout.endsWith('-r');
}

/**
 * Convert HexJSON q/r to pixel offset from grid centre (north-up).
 * Matches ODI Leeds odi.hexmap.js drawHex().
 */
function hexToPixel(q, r, size, layout, range) {
  const p = updateHexPos(q, r, layout);
  const ss = size * 0.5;
  const cs = (size * HEX_SQRT3) / 2;

  if (isPointyLayout(layout)) {
    return {
      x: (p.q - range.q.mid) * cs * 2,
      y: -(p.r - range.r.mid) * ss * 3,
    };
  }

  return {
    x: (p.q - range.q.mid) * ss * 3,
    y: -(p.r - range.r.mid) * cs * 2,
  };
}

function computeRange(constituencies, layout) {
  const range = {
    q: { min: Infinity, max: -Infinity },
    r: { min: Infinity, max: -Infinity },
  };

  constituencies.forEach(c => {
    const p = updateHexPos(c.q, c.r, layout);
    range.q.min = Math.min(range.q.min, p.q);
    range.q.max = Math.max(range.q.max, p.q);
    range.r.min = Math.min(range.r.min, p.r);
    range.r.max = Math.max(range.r.max, p.r);
  });

  range.q.d = range.q.max - range.q.min;
  range.r.d = range.r.max - range.r.min;
  range.q.mid = range.q.min + range.q.d / 2;
  range.r.mid = range.r.min + range.r.d / 2;
  return range;
}

/** Hex size that fits the viewport (ODI Leeds sizing). */
function hexSizeForViewport(width, height, range, layout) {
  const pad = 0.6;
  if (isPointyLayout(layout)) {
    return Math.min(
      (0.5 * height) / (range.r.d * 0.75 + pad),
      (height / HEX_SQRT3) / (range.q.d + pad)
    );
  }
  return Math.min(
    (height / HEX_SQRT3) / (range.r.d + pad),
    (0.5 * width) / (range.q.d * 0.75 + pad)
  );
}

/** SVG point string for a flat-topped hexagon (north-up). */
function flatTopHexPoints(cx, cy, size) {
  const ss = size * 0.5;
  const cs = (size * HEX_SQRT3) / 2;
  const verts = [
    [0, -cs],
    [ss, -cs / 2],
    [ss, cs / 2],
    [0, cs],
    [-ss, cs / 2],
    [-ss, -cs / 2],
  ];
  return verts.map(([dx, dy]) => `${(cx + dx).toFixed(2)},${(cy + dy).toFixed(2)}`).join(' ');
}

/** SVG point string for a pointy-topped hexagon (north-up, ODI path). */
function pointyTopHexPoints(cx, cy, size) {
  const ss = size * 0.5;
  const cs = (size * HEX_SQRT3) / 2;
  let x = cx + cs;
  let y = cy - ss;
  const parts = [`${x.toFixed(2)},${y.toFixed(2)}`];
  [[0, 2 * ss], [-cs, ss], [-cs, -ss], [0, -2 * ss], [cs, -ss], [cs, ss]].forEach(([dx, dy]) => {
    x += dx;
    y += dy;
    parts.push(`${x.toFixed(2)},${y.toFixed(2)}`);
  });
  return parts.join(' ');
}

function hexPoints(cx, cy, size, layout) {
  return isPointyLayout(layout)
    ? pointyTopHexPoints(cx, cy, size)
    : flatTopHexPoints(cx, cy, size);
}

function getSeatOffsets(cx, cy, size, count) {
  if (count === 5) {
    const d = size * 0.26;
    return [
      { x: cx - d, y: cy - d },
      { x: cx + d, y: cy - d },
      { x: cx, y: cy },
      { x: cx - d, y: cy + d },
      { x: cx + d, y: cy + d }
    ];
  }
  if (count === 6) {
    const dx = size * 0.23;
    const dy = size * 0.32;
    return [
      { x: cx - dx, y: cy - dy },
      { x: cx + dx, y: cy - dy },
      { x: cx - dx, y: cy },
      { x: cx + dx, y: cy },
      { x: cx - dx, y: cy + dy },
      { x: cx + dx, y: cy + dy }
    ];
  }
  const offsets = [];
  const rows = Math.ceil(Math.sqrt(count));
  const cols = Math.ceil(count / rows);
  const dx = (size * 0.5) / cols;
  const dy = (size * 0.5) / rows;
  let idx = 0;
  for (let r = 0; r < rows && idx < count; r++) {
    for (let c = 0; c < cols && idx < count; c++) {
      const x = cx + (c - (cols - 1) / 2) * dx * 2;
      const y = cy + (r - (rows - 1) / 2) * dy * 2;
      offsets.push({ x, y });
      idx++;
    }
  }
  return offsets;
}

function drawHexmap(container, data, options = {}) {
  container.innerHTML = '';
  if (!data?.constituencies?.length) {
    container.innerHTML = '<p class="hexmap-empty">Constituency-level data is not yet available for this election.</p>';
    return;
  }

  const layout = data.layout || 'odd-q';
  const constituencies = data.constituencies.filter(c => c.q != null && c.r != null);
  if (!constituencies.length) {
    container.innerHTML = '<p class="hexmap-empty">Could not layout constituencies on the hex grid.</p>';
    return;
  }

  const range = computeRange(constituencies, layout);

  const W = Math.max(container.clientWidth || 320, 280);
  const H = Math.max(W * 1.4, 360);
  const size = hexSizeForViewport(W, H, range, layout) * 0.98;

  const pixels = constituencies.map(c => {
    const p = hexToPixel(c.q, c.r, size, layout, range);
    return { ...c, px: p.x, py: p.y };
  });

  const minX = Math.min(...pixels.map(p => p.px));
  const maxX = Math.max(...pixels.map(p => p.px));
  const minY = Math.min(...pixels.map(p => p.py));
  const maxY = Math.max(...pixels.map(p => p.py));

  const hexPad = size * 0.95;
  const viewMinX = minX - hexPad;
  const viewMinY = minY - hexPad;
  const viewW = maxX - minX + hexPad * 2;
  const viewH = maxY - minY + hexPad * 2;

  const offsetX = -viewMinX;
  const offsetY = -viewMinY;

  const NS = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(NS, 'svg');
  svg.setAttribute('viewBox', `0 0 ${viewW.toFixed(1)} ${viewH.toFixed(1)}`);
  svg.setAttribute('width', '100%');
  svg.setAttribute('height', '100%');
  svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
  svg.setAttribute('class', 'hexmap-svg');
  svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label', `Constituency map, ${constituencies.length} seats`);

  const skipLink = document.createElement('a');
  skipLink.className = 'skip-link skip-map-link';
  skipLink.href = '#hexmap-skip-target';
  skipLink.textContent = 'Skip constituency map';

  const tooltip = document.createElement('div');
  tooltip.className = 'hexmap-tooltip';
  tooltip.setAttribute('hidden', '');

  const detail = document.createElement('div');
  detail.className = 'hexmap-detail';
  detail.innerHTML = '<span class="hexmap-detail-placeholder">Hover a constituency to see the result. Click for manifesto links.</span>';

  const svgWrap = document.createElement('div');
  svgWrap.className = 'hexmap-svg-wrap';
  svgWrap.appendChild(svg);

  const skipTarget = document.createElement('div');
  skipTarget.id = 'hexmap-skip-target';
  skipTarget.className = 'hexmap-skip-target';
  skipTarget.tabIndex = -1;

  container.appendChild(skipLink);
  container.appendChild(svgWrap);
  container.appendChild(tooltip);
  container.appendChild(detail);
  container.appendChild(skipTarget);

  if (options.legendEl) {
    buildHexmapLegend(options.legendEl, constituencies, options.electionYear);
  }

  let activeHex = null;
  const hexElements = [];
  let focusedHexIndex = 0;

  const focusHexAt = index => {
    if (!hexElements.length) return;
    focusedHexIndex = ((index % hexElements.length) + hexElements.length) % hexElements.length;
    hexElements.forEach((el, i) => el.setAttribute('tabindex', i === focusedHexIndex ? '0' : '-1'));
    hexElements[focusedHexIndex].focus();
  };

  pixels.forEach(c => {
    const cx = c.px + offsetX;
    const cy = c.py + offsetY;
    const colour = c.hexColour || getPartyColor(c.party, options.electionYear);

    const g = document.createElementNS(NS, 'g');
    g.setAttribute('class', 'hexmap-hex');
    g.setAttribute('tabindex', hexElements.length === 0 ? '0' : '-1');
    g.setAttribute('role', 'button');
    g.setAttribute('aria-label', `${c.name}, ${c.mp || 'MP unknown'}, ${c.partyLabel || getPartyName(c.party, options.electionYear)}`);
    g.dataset.name = c.name;
    g.dataset.mp = c.mp || '';
    g.dataset.party = c.party || 'others';
    g.dataset.partyLabel = c.partyLabel || getPartyName(c.party, options.electionYear);

    const hasSeatsList = Array.isArray(c.seatsList) && c.seatsList.length > 0;
    const polyFill = hasSeatsList ? 'var(--navy-light)' : colour;

    const poly = document.createElementNS(NS, 'polygon');
    poly.setAttribute('points', hexPoints(cx, cy, size * 0.96, layout));
    poly.setAttribute('fill', polyFill);
    poly.setAttribute('stroke', 'rgba(255,255,255,0.12)');
    poly.setAttribute('stroke-width', '0.6');
    poly.setAttribute('opacity', '0.92');

    g.appendChild(poly);

    if (hasSeatsList) {
      const offsets = getSeatOffsets(cx, cy, size, c.seatsList.length);
      const dotRadius = c.seatsList.length <= 5 ? size * 0.12 : size * 0.11;

      c.seatsList.forEach((partyId, idx) => {
        const offset = offsets[idx] || { x: cx, y: cy };
        const dot = document.createElementNS(NS, 'circle');
        dot.setAttribute('cx', offset.x.toFixed(2));
        dot.setAttribute('cy', offset.y.toFixed(2));
        dot.setAttribute('r', dotRadius.toFixed(2));
        const dotColor = getPartyColor(partyId, options.electionYear);
        dot.setAttribute('fill', dotColor);
        dot.setAttribute('stroke', 'rgba(0, 0, 0, 0.2)');
        dot.setAttribute('stroke-width', '0.4');
        g.appendChild(dot);
      });
    }

    const showTip = (e) => {
      tooltip.hidden = false;
      tooltip.innerHTML = `<strong>${c.name}</strong><span>${c.mp || '—'} · ${c.partyLabel || getPartyName(c.party, options.electionYear)}</span>`;
      const box = container.getBoundingClientRect();
      const x = (e.clientX || box.left) - box.left;
      const y = (e.clientY || box.top) - box.top;
      tooltip.style.left = `${Math.min(Math.max(x, 8), box.width - 180)}px`;
      tooltip.style.top = `${Math.max(y - 48, 4)}px`;
      poly.setAttribute('opacity', '1');
      poly.setAttribute('stroke', 'rgba(242,232,204,0.85)');
      poly.setAttribute('stroke-width', '1.4');
    };

    const hideTip = () => {
      if (activeHex === g) return;
      tooltip.hidden = true;
      poly.setAttribute('opacity', '0.92');
      poly.setAttribute('stroke', 'rgba(255,255,255,0.12)');
      poly.setAttribute('stroke-width', '0.6');
    };

    const selectHex = () => {
      if (activeHex) {
        const prevPoly = activeHex.querySelector('polygon');
        if (prevPoly) {
          prevPoly.setAttribute('opacity', '0.92');
          prevPoly.setAttribute('stroke', 'rgba(255,255,255,0.12)');
          prevPoly.setAttribute('stroke-width', '0.6');
        }
        activeHex.classList.remove('is-selected');
      }
      activeHex = g;
      g.classList.add('is-selected');
      poly.setAttribute('opacity', '1');
      poly.setAttribute('stroke', 'var(--gold-light)');
      poly.setAttribute('stroke-width', '2');

      let actionLinks = '';
      if (hasSeatsList) {
        const uniqueParties = [...new Set(c.seatsList)].filter(pid => pid !== 'others' && PARTIES[pid]);
        uniqueParties.forEach(pid => {
          if (options.electionId) {
            actionLinks += `<a href="/manifesto/${options.electionId}/${pid}" class="hexmap-detail-link">Read ${getPartyName(pid, options.electionYear)} manifesto →</a>`;
          }
          actionLinks += `<a href="/party/${pid}" class="hexmap-detail-link hexmap-detail-link-muted">${getPartyName(pid, options.electionYear)} party page</a>`;
        });
      } else {
        const partyId = c.party;
        const hasManifesto = options.electionId && partyId && partyId !== 'others' && PARTIES[partyId];
        if (hasManifesto) {
          actionLinks += `<a href="/manifesto/${options.electionId}/${partyId}" class="hexmap-detail-link">Read ${getPartyName(partyId, options.electionYear)} manifesto →</a>`;
        }
        if (partyId && partyId !== 'others' && PARTIES[partyId]) {
          actionLinks += `<a href="/party/${partyId}" class="hexmap-detail-link hexmap-detail-link-muted">${getPartyName(partyId, options.electionYear)} party page</a>`;
        }
      }

      detail.innerHTML = `
        <div class="hexmap-detail-inner">
          <div class="hexmap-detail-swatch" style="background:${colour}"></div>
          <div>
            <div class="hexmap-detail-name">${c.name}</div>
            <div class="hexmap-detail-mp">${c.mp || '—'}</div>
            <div class="hexmap-detail-party">${c.partyLabel || getPartyName(c.party, options.electionYear)}</div>
            <div class="hexmap-detail-actions">${actionLinks}</div>
          </div>
        </div>`;

      if (typeof options.onSelect === 'function') {
        options.onSelect(c);
      }
    };

    g.addEventListener('mouseenter', showTip);
    g.addEventListener('mousemove', showTip);
    g.addEventListener('mouseleave', hideTip);
    g.addEventListener('click', selectHex);
    g.addEventListener('focus', () => {
      const idx = hexElements.indexOf(g);
      if (idx >= 0) focusedHexIndex = idx;
      showTip({ clientX: container.getBoundingClientRect().left + container.clientWidth / 2, clientY: container.getBoundingClientRect().top + 40 });
    });
    g.addEventListener('blur', hideTip);
    g.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        selectHex();
      } else if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
        e.preventDefault();
        focusHexAt(focusedHexIndex + 1);
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        e.preventDefault();
        focusHexAt(focusedHexIndex - 1);
      } else if (e.key === 'Home') {
        e.preventDefault();
        focusHexAt(0);
      } else if (e.key === 'End') {
        e.preventDefault();
        focusHexAt(hexElements.length - 1);
      }
    });

    hexElements.push(g);
    svg.appendChild(g);
  });
}

/**
 * Build a party legend from constituency results on the hexmap.
 * @param {HTMLElement} legendEl
 * @param {Array} constituencies - placed constituencies with party ids
 */
function buildHexmapLegend(legendEl, constituencies, electionYear) {
  if (!legendEl) return;
  legendEl.innerHTML = '';

  const counts = new Map();
  constituencies.forEach(c => {
    if (Array.isArray(c.seatsList) && c.seatsList.length > 0) {
      c.seatsList.forEach(pid => {
        const pIdNormalized = (pid || 'others').toLowerCase().replace(/\s+/g, '');
        const defaultLabel = getPartyName(pIdNormalized, electionYear);
        if (!counts.has(pIdNormalized)) {
          counts.set(pIdNormalized, { party: pIdNormalized, seats: 0, label: defaultLabel });
        }
        const row = counts.get(pIdNormalized);
        row.seats += 1;
      });
    } else {
      const pid = c.party || 'others';
      const defaultLabel = getPartyName(pid, electionYear);
      if (!counts.has(pid)) {
        counts.set(pid, { party: pid, seats: 0, label: defaultLabel });
      }
      const row = counts.get(pid);
      row.seats += 1;
      if (LIBERAL_LINEAGE_NAMES[pid] && electionYear != null) {
        row.label = defaultLabel;
      } else if (c.partyLabel) {
        row.label = c.partyLabel;
      }
    }
  });

  const sorted = [...counts.values()].sort((a, b) => b.seats - a.seats);
  sorted.forEach(r => {
    const item = document.createElement('div');
    item.className = 'legend-item';

    const dot = document.createElement('div');
    dot.className = 'legend-dot';
    const raw = getPartyColor(r.party, electionYear);
    if (typeof dotStyle === 'function') {
      dot.setAttribute('style', dotStyle(raw));
    } else {
      dot.style.background = raw;
    }

    const label = document.createElement('span');
    label.textContent = r.label || getPartyName(r.party, electionYear);

    const seats = document.createElement('span');
    seats.className = 'legend-seats';
    seats.textContent = `${r.seats}`;

    item.appendChild(dot);
    item.appendChild(label);
    item.appendChild(seats);
    legendEl.appendChild(item);
  });
}

/** Load constituency data for an election (cached). */
const _hexDataCache = new Map();

async function loadConstituencyData(electionId) {
  if (_hexDataCache.has(electionId)) return _hexDataCache.get(electionId);
  try {
    const res = await fetch(`/data/constituencies/${electionId}.json`);
    if (!res.ok) return null;
    const data = await res.json();
    _hexDataCache.set(electionId, data);
    return data;
  } catch (_) {
    return null;
  }
}

async function hasConstituencyData(electionId) {
  const idx = await fetch('/data/constituencies/index.json').then(r => r.ok ? r.json() : []).catch(() => []);
  if (Array.isArray(idx)) {
    const entry = idx.find(e => e.id === electionId);
    if (entry) return entry.available !== false;
  }
  const data = await loadConstituencyData(electionId);
  return !!(data?.constituencies?.length);
}

/** Map site election id → hexjson filename stem in data/hex/elections/. */
const ELECTION_HEX_YEAR = {
  1945: '1945',
  1950: '1950',
  1951: '1951',
  1955: '1955',
  1959: '1959',
  1964: '1964',
  1966: '1966',
  1970: '1970',
  feb1974: '1974',
  oct1974: '1974',
  1979: '1979',
  1983: '1983',
  1987: '1987',
  1992: '1992',
  1997: '1997',
  2001: '2001',
  2005: '2005',
  2010: '2010',
  2015: '2015',
  2017: '2017',
  2019: '2019',
  2024: '2024',
};

const _hexLayoutCache = new Map();

async function loadHexLayoutJson(electionId) {
  const year = ELECTION_HEX_YEAR[electionId];
  if (!year) return null;
  if (_hexLayoutCache.has(year)) return _hexLayoutCache.get(year);
  try {
    const res = await fetch(`/data/hex/elections/${year}.hexjson`);
    if (!res.ok) return null;
    const data = await res.json();
    _hexLayoutCache.set(year, data);
    return data;
  } catch (_) {
    return null;
  }
}

async function load1945OutsideBoundary() {
  try {
    const res = await fetch('/data/hex/1945-outside-boundary.json');
    return res.ok ? res.json() : null;
  } catch (_) {
    return null;
  }
}

/** Build drawHexmap payload from a coloured hexjson file. */
function hexjsonToDrawData(hexjson, electionYear) {
  const constituencies = Object.entries(hexjson.hexes || {}).map(([key, cell]) => {
    const partyId = (cell.party || 'others').toLowerCase().replace(/\s+/g, '');
    let label = cell.partyLabel || cell.party || 'Other';
    if (typeof getPartyName === 'function' && PARTIES[partyId]) {
      label = getPartyName(partyId, electionYear);
    }
    return {
      name: cell.n || key,
      key,
      mp: '',
      party: partyId,
      partyLabel: label,
      q: cell.q,
      r: cell.r,
      hexColour: cell.colour,
      seatsList: cell.seats_list || null,
    };
  });
  return {
    layout: hexjson.layout || 'odd-r',
    constituencies,
    totalSeats: constituencies.length,
    matchedHexes: constituencies.length,
  };
}

function renderOutsideBoundaryPanel(panelEl, outsideData) {
  if (!panelEl || !outsideData?.groups?.length) return;

  panelEl.innerHTML = '';
  panelEl.hidden = false;

  const heading = document.createElement('div');
  heading.className = 'hexmap-outside-heading';
  heading.textContent = 'Multi-member & university seats';
  panelEl.appendChild(heading);

  const note = document.createElement('p');
  note.className = 'hexmap-outside-note';
  note.textContent = 'These 22 constituencies (42 MPs) are not shown on the territorial hex map — each swatch is one member returned.';
  panelEl.appendChild(note);

  const rowsWrap = document.createElement('div');
  rowsWrap.className = 'hexmap-outside-rows';

  outsideData.groups.forEach((group, groupIndex) => {
    if (groupIndex > 0) {
      const gap = document.createElement('div');
      gap.className = 'hexmap-outside-gap';
      rowsWrap.appendChild(gap);
    }

    group.seats.forEach(seat => {
      const row = document.createElement('div');
      row.className = 'hexmap-outside-row';

      const label = document.createElement('div');
      label.className = 'hexmap-outside-name';
      label.textContent = seat.name;
      row.appendChild(label);

      const swatches = document.createElement('div');
      swatches.className = 'hexmap-outside-swatches';
      (seat.members || []).forEach(member => {
        const sw = document.createElement('span');
        sw.className = 'hexmap-outside-swatch';
        sw.style.background = member.colour || '#CCCCCC';
        sw.title = `${member.name} (${member.party})`;
        sw.setAttribute('aria-label', `${seat.name}: ${member.name}, ${member.party}`);
        swatches.appendChild(sw);
      });
      row.appendChild(swatches);
      rowsWrap.appendChild(row);
    });
  });

  panelEl.appendChild(rowsWrap);
}

/**
 * 1945-only layout: mainland hexes from hexjson + outside-boundary member list.
 */
async function draw1945Hexmap(container, options = {}) {
  container.innerHTML = '';
  const [hexjson, outsideData] = await Promise.all([
    loadHexLayoutJson('1945'),
    load1945OutsideBoundary(),
  ]);

  if (!hexjson?.hexes) {
    container.innerHTML = '<p class="hexmap-empty">1945 hex layout not available.</p>';
    return;
  }

  const wrap = document.createElement('div');
  wrap.className = 'hexmap-1945-wrap';

  const mapCol = document.createElement('div');
  mapCol.className = 'hexmap-1945-map';

  const outsideCol = document.createElement('div');
  outsideCol.className = 'hexmap-outside-panel';
  outsideCol.id = 'hexmap-outside-panel';

  wrap.appendChild(mapCol);
  wrap.appendChild(outsideCol);
  container.appendChild(wrap);

  const data = hexjsonToDrawData(hexjson, options.electionYear);
  drawHexmap(mapCol, data, { ...options, legendEl: null });

  renderOutsideBoundaryPanel(outsideCol, outsideData);

  if (options.legendEl) {
    buildHexmapLegend(options.legendEl, data.constituencies, options.electionYear);
  }
}
