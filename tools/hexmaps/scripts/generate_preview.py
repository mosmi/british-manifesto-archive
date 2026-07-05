#!/usr/bin/env python3
"""Generate a self-contained HTML preview of all election hexmaps."""

import json
import math
from collections import Counter
from pathlib import Path

BASE    = Path(__file__).resolve().parent.parent
OUTPUT  = BASE / "output"
PREVIEW = BASE / "preview"

YEARS = [
    1945, 1950, 1951, 1955, 1959, 1964, 1966, 1970,
    1974, 19741, 1979, 1983, 1987, 1992, 1997, 2001, 2005,
    2010, 2015, 2017, 2019, 2024,
]

YEAR_LABELS = {y: str(y) for y in YEARS}
YEAR_LABELS[1974]  = "Feb 1974"
YEAR_LABELS[19741] = "Oct 1974"

# ── Hex geometry (pointy-top, odd-r) ─────────────────────────────────────────
R     = 75.0 / math.sqrt(3)   # circumradius ≈ 43.301
A     = 37.5                   # apothem = R·√3/2
ROW_H = 1.5 * R                # row spacing ≈ 64.952
COL_W = 75.0                   # column spacing = 2·A

# Pointy-top hex path centred at origin
HEX_PATH = (
    f"M{A:.4f},{-R/2:.4f}"
    f"v{R:.4f}"
    f"l{-A:.4f},{R/2:.4f}"
    f"l{-A:.4f},{-R/2:.4f}"
    f"v{-R:.4f}"
    f"l{A:.4f},{-R/2:.4f}Z"
)


def hex_center(q: int, r: int) -> tuple[float, float]:
    return q * COL_W + (A if r % 2 != 0 else 0.0), -r * ROW_H


def neighbors_odd_r(q: int, r: int) -> list[tuple[int, int]]:
    if r % 2 == 0:
        return [(q-1,r-1),(q,r-1),(q-1,r),(q+1,r),(q-1,r+1),(q,r+1)]
    else:
        return [(q,r-1),(q+1,r-1),(q-1,r),(q+1,r),(q,r+1),(q+1,r+1)]


def region_edge(cx_a, cy_a, cx_b, cy_b) -> tuple[float, float, float, float]:
    """(x1,y1,x2,y2) of the shared edge between two adjacent hex centres."""
    mx, my = (cx_a + cx_b) / 2, (cy_a + cy_b) / 2
    dx, dy = cx_b - cx_a, cy_b - cy_a
    d  = math.hypot(dx, dy)
    px, py = -dy / d, dx / d      # perpendicular unit vector
    h  = R / 2
    return mx - px*h, my - py*h, mx + px*h, my + py*h


def make_svg(year: int) -> tuple[str, dict, dict]:
    """Return (svg_string, party_counts, party_colours)."""
    data = json.loads((OUTPUT / f"{year}.hexjson").read_text())["hexes"]

    pos     = {(d["q"], d["r"]): (nm, d) for nm, d in data.items()}
    centers = {(d["q"], d["r"]): hex_center(d["q"], d["r"]) for d in data.values()}

    # Bounding box
    xs  = [c[0] for c in centers.values()]
    ys  = [c[1] for c in centers.values()]
    pad = A + 6
    vx, vy = min(xs) - pad, min(ys) - pad
    vw, vh = max(xs) - min(xs) + 2*pad, max(ys) - min(ys) + 2*pad

    # ── Hex fills ─────────────────────────────────────────────────────────────
    fills = []
    for nm, d in data.items():
        cx, cy  = centers[(d["q"], d["r"])]
        colour  = d.get("colour", "#AAAAAA")
        safe_nm = nm.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        fills.append(
            f'<path fill="{colour}" d="{HEX_PATH}" transform="translate({cx:.2f},{cy:.2f})">'
            f'<title>{safe_nm}</title></path>'
        )

    # ── Region boundary edges ─────────────────────────────────────────────────
    seen  = set()
    lines = []
    for nm, d in data.items():
        q, r     = d["q"], d["r"]
        reg_a    = d.get("region", "")
        cx_a, cy_a = centers[(q, r)]

        for nq, nr in neighbors_odd_r(q, r):
            key = tuple(sorted([(q, r), (nq, nr)]))
            if key in seen:
                continue
            seen.add(key)

            nb = pos.get((nq, nr))
            if nb is None:
                continue                       # map edge — skip
            reg_b = nb[1].get("region", "")
            if reg_a != reg_b:
                x1, y1, x2, y2 = region_edge(cx_a, cy_a, *centers[(nq, nr)])
                lines.append(
                    f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>'
                )

    # stroke-width in SVG units — scaled so borders appear ~1.5px at 420px display
    # typical vw ≈ 2200-2500, scale ≈ 0.18 → sw=8 → ~1.4px display
    sw = vw / 300
    boundaries = (
        f'<g fill="none" stroke="white" stroke-width="{sw:.1f}" stroke-linecap="round">'
        + "".join(lines) + "</g>"
    )

    svg = (
        f'<svg viewBox="{vx:.1f} {vy:.1f} {vw:.1f} {vh:.1f}" '
        f'xmlns="http://www.w3.org/2000/svg" class="hexmap" '
        f'preserveAspectRatio="xMidYMin meet" '
        f'style="width:100%;display:block;">'
        f'<g>{"".join(fills)}</g>'
        f'{boundaries}'
        f'</svg>'
    )

    party_counts  = dict(Counter(d.get("party", "Other") for d in data.values()))
    party_colours = {d.get("party"): d.get("colour") for d in data.values()}

    return svg, party_counts, party_colours


# ── Legend helpers ────────────────────────────────────────────────────────────

# Preferred display order (most prominent first)
PARTY_ORDER = [
    "Labour", "Conservative", "Liberal Democrats", "Liberal", "Alliance",
    "SNP", "Plaid Cymru", "Reform UK", "Green", "UKIP", "Brexit Party",
    "S&D", "EPP", "Renew Europe", "Greens/EFA", "GUE/NGL", "ECR",
    "Eurosceptic groups", "ID", "UEN line", "DiEM25", "Volt", "ECPM",
    "European Pirates",
    "ILP", "Communist", "Common Wealth", "National Liberal", "Respect",
    "Democratic Labour",
    "Irish Labour", "Republican Labour", "Independent Labour",
    "Nationalist", "Protestant Unionist", "Independent Republican",
    "DUP", "Sinn Féin", "SDLP", "UUP", "Alliance NI",
    "Vanguard", "Ulster Popular Unionist", "UK Unionist Party",
    "Independent Unionist", "TUV",
    "Speaker", "Independent", "Other",
]

def text_colour(hex_bg: str) -> str:
    """Return #000 or #fff for readable contrast on hex_bg."""
    h = hex_bg.lstrip("#")
    if len(h) == 3:
        h = "".join(c*2 for c in h)
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    lum = 0.299*r + 0.587*g + 0.114*b
    return "#000" if lum > 140 else "#fff"


def legend_html(party_counts: dict, party_colours: dict) -> str:
    ordered = sorted(
        party_counts.items(),
        key=lambda kv: (
            PARTY_ORDER.index(kv[0]) if kv[0] in PARTY_ORDER else 99,
            -kv[1],
        ),
    )
    items = []
    for party, count in ordered:
        colour = party_colours.get(party, "#AAAAAA")
        tc     = text_colour(colour)
        items.append(
            f'<li class="legend-item">'
            f'<span class="legend-swatch" style="background:{colour};color:{tc}">'
            f'</span>'
            f'<span class="legend-label">{party}</span>'
            f'<span class="legend-count">{count}</span>'
            f'</li>'
        )
    return f'<ul class="legend-list">{"".join(items)}</ul>'


# ── Build the page ─────────────────────────────────────────────────────────────

def build():
    PREVIEW.mkdir(exist_ok=True)

    print("Generating SVGs…")
    svgs      = {}
    legends   = {}
    for year in YEARS:
        print(f"  {year}…", end=" ", flush=True)
        svg, counts, colours = make_svg(year)
        svgs[year]    = svg
        legends[year] = legend_html(counts, colours)
        print(f"{sum(counts.values())} hexes")

    # ── Year buttons ──────────────────────────────────────────────────────────
    buttons = "".join(
        f'<button class="year-btn{" active" if y == 2024 else ""}" '
        f'data-year="{y}">{YEAR_LABELS[y]}</button>'
        for y in YEARS
    )

    # ── Map panes (hidden except 2024) ────────────────────────────────────────
    map_panes = "".join(
        f'<div class="map-pane{" active" if y == 2024 else ""}" id="map-{y}">'
        f'{svgs[y]}</div>'
        for y in YEARS
    )

    # ── Legend panes ──────────────────────────────────────────────────────────
    legend_panes = "".join(
        f'<div class="legend-pane{" active" if y == 2024 else ""}" id="leg-{y}">'
        f'{legends[y]}</div>'
        for y in YEARS
    )

    # ── Seat total lookup (JS) ────────────────────────────────────────────────
    # For subtitle line
    year_info_js = "const YEAR_INFO = {" + ",".join(
        f'{y}:{{label:"{YEAR_LABELS[y]}",seats:{sum(dict(Counter(d.get("party","Other") for d in json.loads((OUTPUT/f"{y}.hexjson").read_text())["hexes"].values())).values())}}}'
        for y in YEARS
    ) + "};"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>UK General Elections 1945–2024 — Hexmaps</title>
<style>
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  background: #f4f4f4;
  color: #222;
  min-height: 100vh;
}}
header {{
  background: #1c1c4e;
  color: #fff;
  padding: 1.2rem 2rem 1rem;
}}
header h1 {{
  font-size: 1.4rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}}
header p {{
  font-size: 0.9rem;
  opacity: 0.75;
  margin-top: 0.2rem;
}}
.year-nav {{
  background: #fff;
  border-bottom: 1px solid #ddd;
  padding: 0.75rem 1rem;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  justify-content: center;
}}
.year-btn {{
  padding: 5px 11px;
  font-size: 0.82rem;
  border: 1px solid #ccc;
  background: #fff;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.1s, color 0.1s;
  color: #333;
}}
.year-btn:hover {{ background: #e8e8f0; }}
.year-btn.active {{
  background: #1c1c4e;
  color: #fff;
  border-color: #1c1c4e;
  font-weight: 600;
}}
.content {{
  display: flex;
  align-items: flex-start;
  gap: 1.5rem;
  max-width: 1100px;
  margin: 1.25rem auto;
  padding: 0 1rem;
}}
.map-col {{
  flex: 0 0 420px;
  max-width: 420px;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 6px;
  overflow: hidden;
  padding: 0.5rem;
}}
.map-pane {{ display: none; }}
.map-pane.active {{ display: block; }}
.hexmap {{
  display: block;
  width: 100%;
}}
.info-col {{
  flex: 1;
  min-width: 0;
}}
.info-col h2 {{
  font-size: 1.1rem;
  font-weight: 700;
  margin-bottom: 0.2rem;
}}
.info-col .subtitle {{
  font-size: 0.85rem;
  color: #666;
  margin-bottom: 1rem;
}}
.legend-pane {{ display: none; }}
.legend-pane.active {{ display: block; }}
.legend-list {{
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 4px;
}}
.legend-item {{
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.88rem;
}}
.legend-swatch {{
  width: 18px;
  height: 18px;
  border-radius: 3px;
  flex-shrink: 0;
  border: 1px solid rgba(0,0,0,0.08);
}}
.legend-label {{
  flex: 1;
}}
.legend-count {{
  color: #666;
  font-variant-numeric: tabular-nums;
  min-width: 28px;
  text-align: right;
  font-size: 0.82rem;
}}
@media (max-width: 700px) {{
  .content {{ flex-direction: column; }}
  .map-col {{ flex: none; max-width: 100%; width: 100%; }}
}}
</style>
</head>
<body>

<header>
  <h1>UK General Elections 1945–2024</h1>
  <p>Hex cartograms — each constituency one hex, coloured by winning party</p>
</header>

<nav class="year-nav">{buttons}</nav>

<div class="content">
  <div class="map-col">{map_panes}</div>

  <div class="info-col">
    <h2 id="el-title">General Election 2024</h2>
    <p class="subtitle" id="el-sub">650 constituencies</p>
    {legend_panes}
  </div>
</div>

<script>
{year_info_js}

const YEAR_LABELS = {{{",".join(f'{y}:"{YEAR_LABELS[y]}"' for y in YEARS)}}};

const btns   = document.querySelectorAll(".year-btn");
const maps   = document.querySelectorAll(".map-pane");
const legs   = document.querySelectorAll(".legend-pane");
const title  = document.getElementById("el-title");
const sub    = document.getElementById("el-sub");

function activate(year) {{
  btns.forEach(b  => b.classList.toggle("active",  +b.dataset.year === year));
  maps.forEach(m  => m.classList.toggle("active",  m.id === "map-" + year));
  legs.forEach(l  => l.classList.toggle("active",  l.id === "leg-" + year));
  const info = YEAR_INFO[year];
  title.textContent = "General Election " + YEAR_LABELS[year];
  sub.textContent   = info.seats + " constituencies";
}}

btns.forEach(b => b.addEventListener("click", () => activate(+b.dataset.year)));

// keyboard: left/right arrow to step through years
const YEARS = [{",".join(str(y) for y in YEARS)}];
document.addEventListener("keydown", e => {{
  if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
  const active = document.querySelector(".year-btn.active");
  const cur    = active ? YEARS.indexOf(+active.dataset.year) : YEARS.length - 1;
  const next   = e.key === "ArrowRight"
    ? Math.min(cur + 1, YEARS.length - 1)
    : Math.max(cur - 1, 0);
  if (next !== cur) activate(YEARS[next]);
}});
</script>
</body>
</html>"""

    out = PREVIEW / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"\nWrote {out}  ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    build()
