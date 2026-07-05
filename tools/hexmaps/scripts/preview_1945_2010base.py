#!/usr/bin/env python3
"""Side-by-side preview: standard 1945 hexjson vs 1945-on-2010-base."""
import json, math
from collections import Counter
from pathlib import Path

BASE    = Path(__file__).resolve().parent.parent
OUTPUT  = BASE / "output"
PREVIEW = BASE / "preview"

# ── hex geometry (same as compare_test_1945.py) ───────────────────────────
R     = 75.0 / math.sqrt(3)
A     = 37.5
ROW_H = 1.5 * R
COL_W = 75.0

HEX_PATH = (
    f"M{A:.4f},{-R/2:.4f}v{R:.4f}l{-A:.4f},{R/2:.4f}"
    f"l{-A:.4f},{-R/2:.4f}v{-R:.4f}l{A:.4f},{-R/2:.4f}Z"
)

def hex_center(q, r):
    return q * COL_W + (A if r % 2 != 0 else 0.0), -r * ROW_H

def neighbors(q, r):
    if r % 2 == 0:
        return [(q-1,r-1),(q,r-1),(q-1,r),(q+1,r),(q-1,r+1),(q,r+1)]
    else:
        return [(q,r-1),(q+1,r-1),(q-1,r),(q+1,r),(q,r+1),(q+1,r+1)]

def make_svg(hexjson_path: Path) -> tuple[str, dict, dict]:
    data    = json.loads(hexjson_path.read_text())["hexes"]
    pos     = {(d["q"], d["r"]): (nm, d) for nm, d in data.items()}
    centers = {(d["q"], d["r"]): hex_center(d["q"], d["r"]) for d in data.values()}

    xs = [c[0] for c in centers.values()]
    ys = [c[1] for c in centers.values()]
    pad = A + 6
    vx, vy = min(xs)-pad, min(ys)-pad
    vw, vh = max(xs)-min(xs)+2*pad, max(ys)-min(ys)+2*pad

    fills = []
    for nm, d in data.items():
        cx, cy = centers[(d["q"], d["r"])]
        colour = d.get("colour", "#555555")
        safe   = nm.replace("&","&amp;").replace("<","&lt;")
        fills.append(
            f'<path fill="{colour}" d="{HEX_PATH}" transform="translate({cx:.2f},{cy:.2f})">'
            f'<title>{safe}</title></path>'
        )

    seen, lines = set(), []
    for nm, d in data.items():
        q, r = d["q"], d["r"]
        reg_a = d.get("region", "")
        cx_a, cy_a = centers[(q, r)]
        for nq, nr in neighbors(q, r):
            key = tuple(sorted([(q,r),(nq,nr)]))
            if key in seen: continue
            seen.add(key)
            nb = pos.get((nq, nr))
            if nb is None: continue
            if reg_a != nb[1].get("region", ""):
                mx, my = (cx_a+centers[(nq,nr)][0])/2, (cy_a+centers[(nq,nr)][1])/2
                dx, dy = centers[(nq,nr)][0]-cx_a, centers[(nq,nr)][1]-cy_a
                d2 = math.hypot(dx, dy)
                px, py = -dy/d2, dx/d2
                h = R/2
                x1,y1,x2,y2 = mx-px*h,my-py*h,mx+px*h,my+py*h
                lines.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>')

    sw = vw / 300
    svg = (
        f'<svg viewBox="{vx:.1f} {vy:.1f} {vw:.1f} {vh:.1f}" '
        f'xmlns="http://www.w3.org/2000/svg" style="width:100%;display:block;">'
        f'<g>{"".join(fills)}</g>'
        f'<g fill="none" stroke="white" stroke-width="{sw:.1f}" stroke-linecap="round">'
        + "".join(lines) + "</g></svg>"
    )
    party_counts  = dict(Counter(d.get("party", "Other") for d in data.values()))
    party_colours = {d.get("party"): d.get("colour") for d in data.values()}
    return svg, party_counts, party_colours

PARTY_ORDER = [
    "Labour","Conservative","Liberal","National Liberal",
    "ILP","Communist","Common Wealth",
    "Irish Labour","Republican Labour","Independent Labour",
    "Nationalist","Protestant Unionist","Independent Republican",
    "DUP","Sinn Féin","SDLP","UUP","Alliance NI",
    "Speaker","Independent","Other",
]

def text_colour(hx):
    h = hx.lstrip("#")
    if len(h)==3: h="".join(c*2 for c in h)
    r2,g2,b2 = int(h[0:2],16),int(h[2:4],16),int(h[4:6],16)
    return "#000" if 0.299*r2+0.587*g2+0.114*b2 > 140 else "#fff"

def legend_html(pc, pcol):
    ordered = sorted(pc.items(),
                     key=lambda kv:(PARTY_ORDER.index(kv[0]) if kv[0] in PARTY_ORDER else 99,-kv[1]))
    items = []
    for party, count in ordered:
        colour = pcol.get(party,"#555")
        tc     = text_colour(colour)
        items.append(
            f'<li style="display:flex;align-items:center;gap:5px;margin:2px 0">'
            f'<span style="display:inline-block;width:18px;height:18px;background:{colour};'
            f'border-radius:3px;flex-shrink:0"></span>'
            f'<span style="flex:1;font-size:12px">{party}</span>'
            f'<span style="font-size:12px;color:#aaa">{count}</span></li>'
        )
    return "<ul style='list-style:none;margin:0;padding:0'>"+"".join(items)+"</ul>"

svg_std, pc_std, pcol_std = make_svg(OUTPUT / "1945.hexjson")
svg_new, pc_new, pcol_new = make_svg(OUTPUT / "1945_on_2010base.hexjson")

html = f"""<!DOCTYPE html>
<html><head><meta charset=utf-8>
<title>1945 — standard vs 2010-base</title>
<style>
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ background:#1a1a2e; color:#eee; font-family:sans-serif; padding:8px; }}
h3 {{ font-size:12px; margin:4px 0 6px; color:#ccc; line-height:1.4; }}
.grid {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; }}
.col {{ display:flex; flex-direction:column; gap:6px; }}
.map-box {{ background:#111; border-radius:6px; padding:4px; }}
.legend-box {{ background:#111; border-radius:6px; padding:6px; max-height:300px; overflow-y:auto; font-size:11px; }}
</style>
</head><body>
<div class=grid>
  <div class=col>
    <h3>Standard 1945<br>(geography-derived pack, 2024 boundaries as base)</h3>
    <div class=map-box>{svg_std}</div>
    <div class=legend-box>{legend_html(pc_std, pcol_std)}</div>
  </div>
  <div class=col>
    <h3>1945 on 2010 hex base<br>(1945 seats Hungarian-assigned to 2010 hex positions, {sum(pc_new.values())} seats placed, 56 hexes empty)</h3>
    <div class=map-box>{svg_new}</div>
    <div class=legend-box>{legend_html(pc_new, pcol_new)}</div>
  </div>
</div>
</body></html>"""

out = PREVIEW / "1945_vs_2010base.html"
out.write_text(html)
print(f"Wrote {out}")
