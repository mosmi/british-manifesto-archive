/* ============================================================
   THE BRITISH MANIFESTO ARCHIVE — Parliament Chart
   SVG-based semicircular seat visualisation
   ============================================================ */

let _parliamentDescId = 0;

/**
 * Draws a parliament (semicircle) seat chart into a given container.
 * @param {HTMLElement} container - The element to render into
 * @param {Array} results - [{party, seats, ...}] from election data
 * @param {number} totalSeats - Total seats in parliament
 */
function drawParliamentChart(container, results, totalSeats, year) {
  container.innerHTML = '';

  // Use a fixed high-resolution vector space (aspect ratio 1000:540) to keep alignment perfect
  const W = 1000;
  const H = 540;
  const cx = 500;
  const cy = 492;

  // ── Adaptive layout: small assemblies (≤60 seats) use a compact,
  //    larger-dot layout suited to bodies like the 25-seat London Assembly.
  let dotR, innerR, outerR, arcR, numRows;
  if (totalSeats <= 40) {
    // 3 rows, large dots — balanced spacing for the 25-seat London Assembly.
    // Distributes as [5, 8, 12]: ~47px horiz gap, ~37px radial gap, 52px arc clearance.
    numRows = 3;
    dotR    = 28;
    innerR  = 165;
    outerR  = 350;
    arcR    = 430;
  } else if (totalSeats <= 130) {
    // 6 rows, medium dots — suits 60–130 seat chambers (e.g. Senedd, Holyrood)
    numRows = 6;
    dotR    = 10;
    innerR  = 135;
    outerR  = 410;
    arcR    = 448;
  } else {
    // 14 rows, small dots — optimised for the 650-seat House of Commons
    numRows = 14;
    dotR    = 5.5;
    innerR  = 110;
    outerR  = 430;
    arcR    = 464;
  }

  const radii   = Array.from({ length: numRows }, (_, i) => innerR + i * ((outerR - innerR) / (numRows - 1)));
  const totalCirc = radii.reduce((s, r) => s + r, 0);

  let seatsPerRow = radii.map(r => Math.round(totalSeats * r / totalCirc));
  const assigned  = seatsPerRow.reduce((s, n) => s + n, 0);
  seatsPerRow[numRows - 1] += totalSeats - assigned;

  const allPositions = [];
  seatsPerRow.forEach((n, rowIdx) => {
    const r = radii[rowIdx];
    for (let i = 0; i < n; i++) {
      const t = (i + 0.5) / n;
      const angle = Math.PI * (1 - t);
      allPositions.push({
        x: cx + r * Math.cos(angle),
        y: cy - r * Math.sin(angle),
        t,
        rowIdx
      });
    }
  });

  allPositions.sort((a, b) => a.t - b.t);

  const resultMap = {};
  results.forEach(r => {
    if (r.party) resultMap[r.party] = (resultMap[r.party] || 0) + r.seats;
  });

  const colours = [];
  const partyIds = [];
  const orderedParties = [];

  for (const partyId of SPECTRUM_ORDER) {
    const seats = resultMap[partyId] || 0;
    if (!seats) continue;
    const colour = getPartyColor(partyId, year);
    for (let i = 0; i < seats; i++) {
      colours.push(colour);
      partyIds.push(partyId);
    }
    orderedParties.push({ partyId, color: colour, seats });
    delete resultMap[partyId];
  }
  Object.entries(resultMap).forEach(([partyId, seats]) => {
    const colour = getPartyColor(partyId, year);
    for (let i = 0; i < seats; i++) {
      colours.push(colour);
      partyIds.push(partyId);
    }
    orderedParties.push({ partyId, color: colour, seats });
  });
  results.filter(r => !r.party && r.seats > 0).forEach(r => {
    for (let i = 0; i < r.seats; i++) {
      colours.push('#6b7280');
      partyIds.push('none');
    }
    orderedParties.push({ partyId: 'none', color: '#6b7280', seats: r.seats });
  });

  if (colours.length < totalSeats) {
    const topupSeats = totalSeats - colours.length;
    const colour = getPartyColor('others', year);
    for (let i = 0; i < topupSeats; i++) {
      colours.push(colour);
      partyIds.push('others');
    }
    orderedParties.push({ partyId: 'others', color: colour, seats: topupSeats });
  }

  // Seat totals in source data can exceed totalSeats (bad rows). Truncate so
  // party-range geometry never indexes past allPositions.
  if (colours.length > totalSeats) {
    colours.length = totalSeats;
    partyIds.length = totalSeats;
    orderedParties.length = 0;
    for (let i = 0; i < partyIds.length;) {
      const pid = partyIds[i];
      let j = i + 1;
      while (j < partyIds.length && partyIds[j] === pid) j++;
      orderedParties.push({ partyId: pid, color: colours[i], seats: j - i });
      i = j;
    }
  }

  const NS = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(NS, 'svg');
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  svg.setAttribute('width', '100%');
  svg.setAttribute('height', H);
  svg.setAttribute('role', 'img');
  const partyBits = orderedParties
    .filter(p => p.seats > 0)
    .map(p => {
      const name = p.partyId === 'none'
        ? 'Unlabelled'
        : (p.partyId === 'others'
          ? 'Others'
          : (typeof getPartyName === 'function' ? getPartyName(p.partyId, year) : p.partyId));
      return `${name} ${p.seats}`;
    });
  const summaryText = partyBits.length
    ? `Seat chart: ${partyBits.join(', ')}. ${totalSeats} seats.`
    : `Parliament seat chart, ${totalSeats} seats`;
  const desc = document.createElementNS(NS, 'desc');
  desc.id = `parliament-chart-desc-${++_parliamentDescId}`;
  desc.textContent = summaryText;
  svg.setAttribute('aria-labelledby', desc.id);
  svg.appendChild(desc);
  svg.style.height = 'auto';
  svg.style.display = 'block';
  container.classList.add('parliament-chart');
  container.style.position = 'relative';

  // Background depth arc lines
  const isLight = document.documentElement.getAttribute('data-theme') === 'light';
  const arcGroup = document.createElementNS(NS, 'g');
  arcGroup.setAttribute('fill', 'none');
  arcGroup.setAttribute('stroke', isLight ? 'rgba(20,32,58,0.08)' : 'rgba(255,255,255,0.06)');
  arcGroup.setAttribute('stroke-width', '1');
  radii.forEach(r => {
    const path = document.createElementNS(NS, 'path');
    const startX = cx + r * Math.cos(Math.PI);
    const startY = cy - r * Math.sin(Math.PI);
    const endX   = cx + r * Math.cos(0);
    const endY   = cy - r * Math.sin(0);
    path.setAttribute('d', `M${startX.toFixed(1)},${startY.toFixed(1)} A${r.toFixed(1)},${r.toFixed(1)} 0 0,1 ${endX.toFixed(1)},${endY.toFixed(1)}`);
    arcGroup.appendChild(path);
  });
  svg.appendChild(arcGroup);

  // Outer Glowing Arc - Layered for prominent dual-sided glow
  const scale = W / 500;
  const createArcSegmentsGroup = (strokeWidth, blurPx, opacityVal) => {
    const g = document.createElementNS(NS, 'g');
    g.setAttribute('fill', 'none');
    g.setAttribute('stroke-linecap', 'butt');
    g.setAttribute('stroke-width', Math.max(0.5, strokeWidth).toFixed(2));
    if (blurPx > 0) {
      g.style.filter = `blur(${blurPx.toFixed(2)}px)`;
    }
    if (opacityVal !== undefined) {
      g.setAttribute('opacity', opacityVal.toString());
    }

    let currentSeats = 0;
    orderedParties.forEach(p => {
      if (p.seats === 0) return;
      const seatStart = currentSeats;
      const seatEnd = currentSeats + p.seats;
      currentSeats = seatEnd;

      const t_start = seatStart / totalSeats;
      const t_end = seatEnd / totalSeats;

      const angle_start = Math.PI * (1 - t_start);
      const angle_end = Math.PI * (1 - t_end);

      const startX = cx + arcR * Math.cos(angle_start);
      const startY = cy - arcR * Math.sin(angle_start);
      const endX   = cx + arcR * Math.cos(angle_end);
      const endY   = cy - arcR * Math.sin(angle_end);

      const path = document.createElementNS(NS, 'path');
      path.setAttribute('stroke', p.color);
      path.setAttribute('d', `M ${startX.toFixed(2)} ${startY.toFixed(2)} A ${arcR.toFixed(2)} ${arcR.toFixed(2)} 0 0 1 ${endX.toFixed(2)} ${endY.toFixed(2)}`);
      g.appendChild(path);
    });
    return g;
  };

  if (isLight) {
    svg.appendChild(createArcSegmentsGroup(1.5 * scale, 0, 0.95));
  } else {
    svg.appendChild(createArcSegmentsGroup(28 * scale, 18 * scale, 0.3));
    svg.appendChild(createArcSegmentsGroup(14 * scale, 6 * scale, 0.55));
    svg.appendChild(createArcSegmentsGroup(6 * scale, 2 * scale, 0.85));
    svg.appendChild(createArcSegmentsGroup(1.5 * scale, 0, 0.95));
  }

  // Contiguous party ranges along the sorted seat arc (left → right)
  const partyRanges = [];
  for (let i = 0; i < partyIds.length;) {
    const pid = partyIds[i] || 'others';
    let j = i + 1;
    while (j < partyIds.length && partyIds[j] === pid) j++;
    partyRanges.push({
      partyId: pid,
      i0: i,
      i1: j - 1,
      seats: j - i,
      t0: allPositions[i].t,
      t1: allPositions[j - 1].t
    });
    i = j;
  }
  partyRanges.forEach((range, idx) => {
    const prev = partyRanges[idx - 1];
    const next = partyRanges[idx + 1];
    const pad = Math.max((range.t1 - range.t0) / Math.max(range.seats * 2, 2), 0.002);
    // Fair Voronoi boundaries between neighbouring parties — no minimum
    // expansion, or a single-seat wedge (e.g. Common Wealth) swallows
    // Communist / ILP / Ind. Labour on the outer row.
    range.hitT0 = prev ? (prev.t1 + range.t0) / 2 : Math.max(0, range.t0 - pad);
    range.hitT1 = next ? (range.t1 + next.t0) / 2 : Math.min(1, range.t1 + pad);
  });

  const annularSectorPath = (rInner, rOuter, t0, t1) => {
    const a0 = Math.PI * (1 - t0);
    const a1 = Math.PI * (1 - t1);
    const polar = (r, a) => [cx + r * Math.cos(a), cy - r * Math.sin(a)];
    const [x0o, y0o] = polar(rOuter, a0);
    const [x1o, y1o] = polar(rOuter, a1);
    const [x1i, y1i] = polar(rInner, a1);
    const [x0i, y0i] = polar(rInner, a0);
    const large = Math.abs(a0 - a1) > Math.PI ? 1 : 0;
    return [
      `M${x0o.toFixed(2)},${y0o.toFixed(2)}`,
      `A${rOuter.toFixed(2)},${rOuter.toFixed(2)} 0 ${large},1 ${x1o.toFixed(2)},${y1o.toFixed(2)}`,
      `L${x1i.toFixed(2)},${y1i.toFixed(2)}`,
      `A${rInner.toFixed(2)},${rInner.toFixed(2)} 0 ${large},0 ${x0i.toFixed(2)},${y0i.toFixed(2)}`,
      'Z'
    ].join(' ');
  };

  // Hover root: seat dots + invisible wedges (multi-seat first, singles on top)
  const hoverRoot = document.createElementNS(NS, 'g');
  hoverRoot.setAttribute('class', 'parliament-hover-root');

  const dotsGroup = document.createElementNS(NS, 'g');
  dotsGroup.setAttribute('class', 'parliament-seats');
  allPositions.forEach((pos, i) => {
    const circle = document.createElementNS(NS, 'circle');
    const pid = partyIds[i] || 'others';
    circle.setAttribute('cx', pos.x.toFixed(1));
    circle.setAttribute('cy', pos.y.toFixed(1));
    circle.setAttribute('r',  dotR);
    circle.setAttribute('fill', colours[i] || '#555');
    circle.setAttribute('data-party', pid);
    circle.classList.add('parliament-seat');
    circle.style.opacity = '0.92';
    // Wedges handle hit-testing; keep dots visible-only for pointer events
    circle.style.pointerEvents = 'none';
    dotsGroup.appendChild(circle);
  });
  hoverRoot.appendChild(dotsGroup);

  const hitGroup = document.createElementNS(NS, 'g');
  hitGroup.setAttribute('class', 'parliament-hit-wedges');
  const hitInner = Math.max(innerR - dotR * 2.5, innerR * 0.72);
  const hitOuter = Math.min(outerR + dotR * 3, arcR - 2);

  const appendWedge = (range) => {
    if (range.hitT1 <= range.hitT0) return;
    const wedge = document.createElementNS(NS, 'path');
    wedge.setAttribute('d', annularSectorPath(hitInner, hitOuter, range.hitT0, range.hitT1));
    wedge.setAttribute('fill', 'transparent');
    wedge.setAttribute('data-party', range.partyId);
    wedge.classList.add('parliament-hit-wedge');
    if (range.seats === 1) wedge.classList.add('parliament-hit-wedge-single');
    hitGroup.appendChild(wedge);
  };

  // Multi-seat wedges underneath, then single-seat wedges on top so
  // TUV / Common Wealth etc. are not swallowed by DUP / Communist / ILP.
  partyRanges.filter(r => r.seats >= 2).forEach(appendWedge);
  partyRanges.filter(r => r.seats === 1).forEach(appendWedge);
  hoverRoot.appendChild(hitGroup);
  svg.appendChild(hoverRoot);

  // Center dashed line (Speaker marker)
  const line = document.createElementNS(NS, 'line');
  line.setAttribute('x1', cx);
  line.setAttribute('y1', cy);
  line.setAttribute('x2', cx);
  line.setAttribute('y2', cy - innerR * 0.6);
  line.setAttribute('stroke', 'rgba(201,168,76,0.35)');
  line.setAttribute('stroke-width', '1.5');
  line.setAttribute('stroke-dasharray', '3,3');
  line.setAttribute('class', 'parliament-speaker-line');
  svg.appendChild(line);

  // Flourish-style centre label: seat total in party colour; name in high-contrast ink
  const labelY = cy - innerR * 0.38;
  const countSize = totalSeats <= 40 ? 78 : totalSeats <= 130 ? 58 : 52;
  const nameSize = totalSeats <= 40 ? 26 : totalSeats <= 130 ? 22 : 20;

  const labelGroup = document.createElementNS(NS, 'g');
  labelGroup.setAttribute('class', 'parliament-hover-label');
  labelGroup.style.opacity = '0';
  labelGroup.style.pointerEvents = 'none';

  const seatCountText = document.createElementNS(NS, 'text');
  seatCountText.setAttribute('class', 'parliament-hover-count');
  seatCountText.setAttribute('x', cx);
  seatCountText.setAttribute('y', labelY);
  seatCountText.setAttribute('text-anchor', 'middle');
  seatCountText.setAttribute('dominant-baseline', 'middle');
  seatCountText.setAttribute('font-size', String(countSize));
  seatCountText.setAttribute('font-weight', '600');
  seatCountText.style.fontFamily = 'var(--font-display, "Cormorant Garamond", Georgia, serif)';

  const partyNameText = document.createElementNS(NS, 'text');
  partyNameText.setAttribute('class', 'parliament-hover-name');
  partyNameText.setAttribute('x', cx);
  partyNameText.setAttribute('y', labelY + countSize * 0.52);
  partyNameText.setAttribute('text-anchor', 'middle');
  partyNameText.setAttribute('dominant-baseline', 'hanging');
  partyNameText.setAttribute('font-size', String(nameSize));
  partyNameText.setAttribute('font-weight', '600');
  partyNameText.style.fontFamily = 'var(--font-ui, "DM Sans", system-ui, sans-serif)';

  labelGroup.appendChild(seatCountText);
  labelGroup.appendChild(partyNameText);
  svg.appendChild(labelGroup);

  const partyMeta = {};
  orderedParties.forEach(p => {
    partyMeta[p.partyId] = p;
  });

  const syncLegend = (partyId) => {
    const legend = container.nextElementSibling;
    if (!legend || !legend.classList.contains('parliament-legend')) return;
    legend.querySelectorAll('.legend-item').forEach(item => {
      const match = item.dataset.party === partyId;
      item.classList.toggle('is-highlighted', Boolean(partyId) && match);
      item.classList.toggle('is-dimmed', Boolean(partyId) && !match);
    });
  };

  const highlightParty = (partyId) => {
    if (!partyId || !partyMeta[partyId]) return;
    const meta = partyMeta[partyId];
    dotsGroup.querySelectorAll('circle').forEach(c => {
      const on = c.getAttribute('data-party') === partyId;
      c.style.opacity = on ? '1' : '0.16';
    });
    line.style.opacity = '0.35';
    seatCountText.textContent = String(meta.seats);
    seatCountText.setAttribute('fill', meta.color);
    partyNameText.textContent = partyId === 'none'
      ? 'Independent'
      : (typeof getPartyName === 'function' ? getPartyName(partyId, year) : partyId);
    labelGroup.style.opacity = '1';
    container.classList.add('is-party-hover');
    syncLegend(partyId);
  };

  const clearHighlight = () => {
    dotsGroup.querySelectorAll('circle').forEach(c => { c.style.opacity = '0.92'; });
    line.style.opacity = '1';
    labelGroup.style.opacity = '0';
    seatCountText.textContent = '';
    partyNameText.textContent = '';
    container.classList.remove('is-party-hover');
    syncLegend(null);
  };

  let activeParty = null;
  const partyFromEventTarget = (target) => {
    if (!target || target === hoverRoot) return null;
    const el = typeof target.closest === 'function'
      ? target.closest('[data-party]')
      : (target.getAttribute?.('data-party') ? target : null);
    return el?.getAttribute('data-party') || null;
  };

  hoverRoot.addEventListener('pointerover', (e) => {
    const pid = partyFromEventTarget(e.target);
    if (!pid || pid === activeParty) return;
    activeParty = pid;
    highlightParty(pid);
  });
  hoverRoot.addEventListener('pointerleave', () => {
    activeParty = null;
    clearHighlight();
  });

  container._parliamentInteract = {
    highlight: (partyId) => {
      activeParty = partyId;
      highlightParty(partyId);
    },
    clear: () => {
      activeParty = null;
      clearHighlight();
    }
  };

  container.appendChild(svg);
}

/**
 * Builds the legend below the parliament chart.
 * @param {HTMLElement} legendEl - The element to render legend into
 * @param {Array} results - election results
 * @param {number} [year] - election year for period-correct party names
 */
function buildParliamentLegend(legendEl, results, year) {
  legendEl.innerHTML = '';
  legendEl.setAttribute('role', 'list');
  legendEl.setAttribute('aria-label', 'Seats by party');

  // Sort by seats descending, filter out zero-seat parties
  const sorted = [...results]
    .filter(r => r.seats > 0)
    .sort((a, b) => b.seats - a.seats);

  const chartEl = legendEl.previousElementSibling;
  const interact = chartEl && chartEl._parliamentInteract;

  sorted.forEach(r => {
    const item = document.createElement('div');
    item.className = 'legend-item';
    item.setAttribute('role', 'listitem');
    const partyId = r.party || 'none';
    item.dataset.party = partyId;

    const dot = document.createElement('div');
    dot.className = 'legend-dot';
    const raw = r.party ? getPartyColor(r.party, year) : '#6b7280';
    if (typeof dotStyle === 'function') {
      dot.setAttribute('style', dotStyle(raw));
    } else {
      dot.style.background = raw;
    }

    const name = r.partyLabel || getPartyName(r.party, year);
    const hasPage = partyId && partyId !== 'none' && typeof PARTIES !== 'undefined' && PARTIES[partyId];
    let label;
    if (hasPage) {
      label = document.createElement('a');
      label.href = `/party/${partyId}`;
      label.className = 'legend-party-link';
      label.textContent = name;
    } else {
      label = document.createElement('span');
      label.textContent = name;
    }

    const seats = document.createElement('span');
    seats.className = 'legend-seats';
    seats.textContent = `${r.seats}`;

    item.appendChild(dot);
    item.appendChild(label);
    item.appendChild(seats);

    if (interact) {
      item.classList.add('legend-item-interactive');
      item.setAttribute('aria-label', `${name}, ${r.seats} seats`);
      item.addEventListener('pointerenter', () => interact.highlight(partyId));
      item.addEventListener('pointerleave', () => interact.clear());
      if (hasPage) {
        label.addEventListener('focus', () => interact.highlight(partyId));
        label.addEventListener('blur', () => interact.clear());
      } else {
        item.setAttribute('tabindex', '0');
        item.addEventListener('focus', () => interact.highlight(partyId));
        item.addEventListener('blur', () => interact.clear());
      }
    }

    legendEl.appendChild(item);
  });
}

/**
 * Render supplementary / ancillary document links below an election summary.
 * @param {Array<{title: string, pdf: string}>} docs
 */
function renderSupplementaryDocuments(docs) {
  if (!docs?.length) return '';
  const buttons = docs.map(d =>
    `<a class="supplementary-doc-btn" href="${d.pdf}" target="_blank" rel="noopener">${d.title}</a>`
  ).join('');
  return `<div class="supplementary-documents">
    <span class="section-label">Supplementary Documents</span>
    <div class="supplementary-doc-list">${buttons}</div>
  </div>`;
}
