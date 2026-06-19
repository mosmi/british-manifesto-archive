/* ============================================================
   THE BRITISH MANIFESTO ARCHIVE — Parliament Chart
   SVG-based semicircular seat visualisation
   ============================================================ */

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

  // Spacing and density: 14 rows, dotR = 6.6, innerR = 110, outerR = 430
  const dotR    = 6.6; 
  const innerR  = 110;
  const outerR  = 430; // Sized so that outer arc sits separately
  const arcR    = 464; // Visual separation radius for glowing arc

  const numRows = 14;
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
  const orderedParties = [];

  for (const partyId of SPECTRUM_ORDER) {
    const seats = resultMap[partyId] || 0;
    if (!seats) continue;
    const colour = getPartyColor(partyId, year);
    for (let i = 0; i < seats; i++) colours.push(colour);
    orderedParties.push({ partyId, color: colour, seats });
    delete resultMap[partyId];
  }
  Object.entries(resultMap).forEach(([partyId, seats]) => {
    const colour = getPartyColor(partyId, year);
    for (let i = 0; i < seats; i++) colours.push(colour);
    orderedParties.push({ partyId, color: colour, seats });
  });
  results.filter(r => !r.party && r.seats > 0).forEach(r => {
    for (let i = 0; i < r.seats; i++) colours.push('#6b7280');
    orderedParties.push({ partyId: 'none', color: '#6b7280', seats: r.seats });
  });
  
  if (colours.length < totalSeats) {
    const topupSeats = totalSeats - colours.length;
    const colour = getPartyColor('others', year);
    for (let i = 0; i < topupSeats; i++) colours.push(colour);
    orderedParties.push({ partyId: 'others', color: colour, seats: topupSeats });
  }

  const NS = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(NS, 'svg');
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  svg.setAttribute('width', '100%');
  svg.setAttribute('height', H);
  svg.style.height = 'auto';
  svg.style.display = 'block';

  // Background depth arc lines (rgba(255,255,255,0.06) stroke for better visibility)
  const arcGroup = document.createElementNS(NS, 'g');
  arcGroup.setAttribute('fill', 'none');
  arcGroup.setAttribute('stroke', 'rgba(255,255,255,0.06)');
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

  svg.appendChild(createArcSegmentsGroup(28 * scale, 18 * scale, 0.3));
  svg.appendChild(createArcSegmentsGroup(14 * scale, 6 * scale, 0.55));
  svg.appendChild(createArcSegmentsGroup(6 * scale, 2 * scale, 0.85));
  svg.appendChild(createArcSegmentsGroup(1.5 * scale, 0, 0.95)); // Crisp core line

  // Seat dots
  const dotsGroup = document.createElementNS(NS, 'g');
  allPositions.forEach((pos, i) => {
    const circle = document.createElementNS(NS, 'circle');
    circle.setAttribute('cx', pos.x.toFixed(1));
    circle.setAttribute('cy', pos.y.toFixed(1));
    circle.setAttribute('r',  dotR);
    circle.setAttribute('fill', colours[i] || '#555');
    circle.setAttribute('opacity', '0.92');
    dotsGroup.appendChild(circle);
  });
  svg.appendChild(dotsGroup);

  // Center dashed line (Speaker marker)
  const line = document.createElementNS(NS, 'line');
  line.setAttribute('x1', cx);
  line.setAttribute('y1', cy);
  line.setAttribute('x2', cx);
  line.setAttribute('y2', cy - innerR * 0.6);
  line.setAttribute('stroke', 'rgba(201,168,76,0.35)');
  line.setAttribute('stroke-width', '1.5');
  line.setAttribute('stroke-dasharray', '3,3');
  svg.appendChild(line);

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

  // Sort by seats descending, filter out zero-seat parties
  const sorted = [...results]
    .filter(r => r.seats > 0)
    .sort((a, b) => b.seats - a.seats);

  sorted.forEach(r => {
    const item = document.createElement('div');
    item.className = 'legend-item';

    const dot = document.createElement('div');
    dot.className = 'legend-dot';
    dot.style.background = r.party ? getPartyColor(r.party, year) : '#6b7280';

    const label = document.createElement('span');
    label.textContent = r.partyLabel || getPartyName(r.party, year);

    const seats = document.createElement('span');
    seats.className = 'legend-seats';
    seats.textContent = `${r.seats}`;

    item.appendChild(dot);
    item.appendChild(label);
    item.appendChild(seats);
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
