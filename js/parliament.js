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
function drawParliamentChart(container, results, totalSeats) {
  container.innerHTML = '';

  const W = Math.max(container.clientWidth || 340, 200);
  const H = Math.round(W * 0.52);
  const cx = W / 2;
  const cy = H - 14;

  // Tune dot radius and row spacing based on seat count
  const dotR    = W < 300 ? 2.5 : W < 500 ? 3.5 : 4.2;
  const rowGap  = dotR * 2.75;
  const innerR  = W * 0.13;
  const outerR  = W * 0.47;

  // ── Compute seats per row proportionally ──────────────────
  const numRows = Math.max(4, Math.round((outerR - innerR) / rowGap));
  const radii   = Array.from({ length: numRows }, (_, i) => innerR + i * ((outerR - innerR) / (numRows - 1)));
  const totalCirc = radii.reduce((s, r) => s + r, 0);

  let seatsPerRow = radii.map(r => Math.round(totalSeats * r / totalCirc));
  const assigned  = seatsPerRow.reduce((s, n) => s + n, 0);
  seatsPerRow[numRows - 1] += totalSeats - assigned; // correct rounding

  // ── Generate all seat positions ───────────────────────────
  const allPositions = [];
  seatsPerRow.forEach((n, rowIdx) => {
    const r = radii[rowIdx];
    for (let i = 0; i < n; i++) {
      // t goes 0→1 left→right; add small padding (0.5/n) so dots don't fall exactly at 0° or 180°
      const t = (i + 0.5) / n;
      const angle = Math.PI * (1 - t); // π (left) → 0 (right)
      allPositions.push({
        x:   cx + r * Math.cos(angle),
        y:   cy - r * Math.sin(angle),
        t,       // left→right position for colouring
        rowIdx,
      });
    }
  });

  // ── Sort by t (left → right) for party colouring ─────────
  allPositions.sort((a, b) => a.t - b.t);

  // ── Build flat colour array in political spectrum order ───
  const resultMap = {};
  results.forEach(r => { resultMap[r.party] = r.seats; });

  const colours = [];
  for (const partyId of SPECTRUM_ORDER) {
    const seats = resultMap[partyId] || 0;
    const colour = getPartyColor(partyId);
    for (let i = 0; i < seats; i++) colours.push(colour);
  }
  // safety top-up for "others" or rounding
  while (colours.length < totalSeats) colours.push(getPartyColor('others'));

  // ── Build SVG ─────────────────────────────────────────────
  const NS  = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(NS, 'svg');
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  svg.setAttribute('width',  '100%');
  svg.setAttribute('height', H);
  svg.style.display = 'block';

  // Subtle background arc lines for depth
  const arcGroup = document.createElementNS(NS, 'g');
  arcGroup.setAttribute('fill', 'none');
  arcGroup.setAttribute('stroke', 'rgba(255,255,255,0.04)');
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

  // Centre line (Speaker's position marker)
  const line = document.createElementNS(NS, 'line');
  line.setAttribute('x1', cx);
  line.setAttribute('y1', cy);
  line.setAttribute('x2', cx);
  line.setAttribute('y2', cy - innerR * 0.6);
  line.setAttribute('stroke', 'rgba(201,168,76,0.35)');
  line.setAttribute('stroke-width', '1.5');
  line.setAttribute('stroke-dasharray', '3,3');
  svg.appendChild(line);

  // Majority line (horizontal dashed across at majority threshold)
  const majAngle = Math.PI / 2; // top of semicircle = 90° = majority point
  const majRadius = (innerR + outerR) / 2;
  const majLine = document.createElementNS(NS, 'line');
  majLine.setAttribute('x1', (cx - majRadius - dotR * 3).toFixed(1));
  majLine.setAttribute('y1', (cy - majRadius * 0.02).toFixed(1));
  majLine.setAttribute('x2', (cx + majRadius + dotR * 3).toFixed(1));
  majLine.setAttribute('y2', (cy - majRadius * 0.02).toFixed(1));
  majLine.setAttribute('stroke', 'rgba(201,168,76,0)');
  svg.appendChild(majLine);

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
    dot.style.background = getPartyColor(r.party);

    const label = document.createElement('span');
    label.textContent = getPartyName(r.party, year);

    const seats = document.createElement('span');
    seats.className = 'legend-seats';
    seats.textContent = `${r.seats}`;

    item.appendChild(dot);
    item.appendChild(label);
    item.appendChild(seats);
    legendEl.appendChild(item);
  });
}
