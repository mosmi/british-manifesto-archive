#!/usr/bin/env python3
"""Render PNG previews of the hex map for verification."""

from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Polygon

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "previews"
ELECTION = "feb1974"

HEX_SQRT3 = math.sqrt(3)
LAYOUT = "odd-r"

PARTY_COLORS = {
    "labour": "#E4003B",
    "conservative": "#0087DC",
    "libdem": "#FAA61A",
    "green": "#00B140",
    "snp": "#FFF95D",
    "plaid": "#008142",
    "uup": "#48A5EE",
    "dup": "#D46A4C",
    "sdlp": "#4CAF50",
    "sinnfein": "#326760",
    "vanguard": "#7B68EE",
    "indlabour": "#808080",
    "independent": "#999999",
    "speaker": "#CCCCCC",
    "other": "#BBBBBB",
}

LANDMARKS = [
    "Dorset North",
    "Basingstoke",
    "Cardiff West",
    "Worcester",
    "Epping Forest",
    "Wellingborough",
    "Oswestry",
    "Walsall South",
    "Nottingham West",
    "Colchester",
    "Isle of Ely",
    "Rutland & Stamford",
    "Grantham",
    "Gainsborough",
    "Pontefract & Castleford",
    "Dumfries",
    "Hexham",
    "Gateshead West",
]

REGIONS = {
    "south_west": {
        "title": "Dorset North · Basingstoke · Worcester",
        "centres": [(51, -41), (54, -39), (53, -34)],
        "radius": 4,
    },
    "wales_marches": {
        "title": "Cardiff West · Oswestry · Walsall South",
        "centres": [(47, -37), (49, -29), (52, -30)],
        "radius": 4,
    },
    "east_midlands": {
        "title": "Wellingborough · Isle of Ely · Rutland & Stamford · Grantham",
        "centres": [(61, -33), (63, -29), (63, -27), (63, -26)],
        "radius": 5,
    },
    "east_anglia": {
        "title": "Colchester · Epping Forest · Gainsborough",
        "centres": [(67, -30), (65, -35), (61, -24)],
        "radius": 5,
    },
    "north": {
        "title": "Nottingham West · Pontefract & Castleford · Hexham · Gateshead West · Dumfries",
        "centres": [(58, -29), (60, -22), (52, -13), (53, -11), (51, -14)],
        "radius": 5,
    },
}


def update_hex_pos(q: int, r: int, layout: str) -> tuple[float, float]:
    pq, pr = float(q), float(r)
    if layout == "odd-r" and (r % 2) != 0:
        pq += 0.5
    return pq, pr


def hex_to_pixel(q: int, r: int, size: float, layout: str, range_mid: tuple[float, float]) -> tuple[float, float]:
    p = update_hex_pos(q, r, layout)
    ss = size * 0.5
    cs = (size * HEX_SQRT3) / 2
    q_mid, r_mid = range_mid
    return (p[0] - q_mid) * cs * 2, -(p[1] - r_mid) * ss * 3


def pointy_hex_verts(cx: float, cy: float, size: float) -> list[tuple[float, float]]:
    ss = size * 0.5
    cs = (size * HEX_SQRT3) / 2
    x, y = cx + cs, cy - ss
    verts = [(x, y)]
    for dx, dy in [(0, 2 * ss), (-cs, ss), (-cs, -ss), (0, -2 * ss), (cs, -ss), (cs, ss)]:
        x += dx
        y += dy
        verts.append((x, y))
    return verts


def neighbors(q: int, r: int) -> set[tuple[int, int]]:
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if r % 2:
        dirs += [(1, 1), (-1, 1)]
    else:
        dirs += [(1, -1), (-1, -1)]
    return {(q + dq, r + dr) for dq, dr in dirs}


def load_data() -> list[dict]:
    data = json.loads((ROOT / "data" / "constituencies" / f"{ELECTION}.json").read_text())
    return [c for c in data["constituencies"] if c.get("q") is not None]


def compute_range(constituencies: list[dict]) -> tuple[float, float]:
    qs, rs = [], []
    for c in constituencies:
        pq, pr = update_hex_pos(c["q"], c["r"], LAYOUT)
        qs.append(pq)
        rs.append(pr)
    return (min(qs) + max(qs)) / 2, (min(rs) + max(rs)) / 2


def seat_pixels(constituencies: list[dict], size: float = 1.0) -> dict[str, dict]:
    mid = compute_range(constituencies)
    out = {}
    for c in constituencies:
        px, py = hex_to_pixel(c["q"], c["r"], size, LAYOUT, mid)
        out[c["name"]] = {**c, "px": px, "py": py}
    return out


def seats_in_region(pixels: dict[str, dict], centres: list[tuple[int, int]], radius: int) -> list[dict]:
    wanted: set[tuple[int, int]] = set()
    for cq, cr in centres:
        wanted.add((cq, cr))
        for dq in range(-radius, radius + 1):
            for dr in range(-radius, radius + 1):
                wanted.add((cq + dq, cr + dr))
    by_coord = {(c["q"], c["r"]): c for c in pixels.values()}
    expanded = set(wanted)
    changed = True
    while changed:
        changed = False
        for coord in list(expanded):
            for nbr in neighbors(*coord):
                if nbr in by_coord and nbr not in expanded:
                    expanded.add(nbr)
                    changed = True
    return [by_coord[c] for c in expanded if c in by_coord]


def draw_region(
    ax,
    seats: list[dict],
    size: float,
    mid: tuple[float, float],
    highlight: set[str],
    all_occupied: set[tuple[int, int]],
    show_labels: bool = True,
) -> None:
    polys = []
    colors = []
    for c in seats:
        px, py = hex_to_pixel(c["q"], c["r"], size, LAYOUT, mid)
        polys.append(pointy_hex_verts(px, py, size * 0.96))
        colors.append(PARTY_COLORS.get(c.get("party", "other"), "#BBBBBB"))

    ax.add_collection(PolyCollection(polys, facecolors=colors, edgecolors="#333333", linewidths=0.35, zorder=2))

    for name in highlight:
        c = next((s for s in seats if s["name"] == name), None)
        if not c:
            continue
        px, py = hex_to_pixel(c["q"], c["r"], size, LAYOUT, mid)
        ring = Polygon(
            pointy_hex_verts(px, py, size * 1.02),
            fill=False,
            edgecolor="#FFD700",
            linewidth=2.2,
            zorder=4,
        )
        ax.add_patch(ring)
        empty_nbs = [g for g in neighbors(c["q"], c["r"]) if g not in all_occupied]
        for g in empty_nbs:
            px, py = hex_to_pixel(g[0], g[1], size, LAYOUT, mid)
            gap = Polygon(
                pointy_hex_verts(px, py, size * 0.96),
                fill=True,
                facecolor="#ffffff",
                edgecolor="#FF2222",
                linewidth=2.5,
                hatch="///",
                zorder=3,
            )
            ax.add_patch(gap)
        if show_labels:
            ax.text(px, py, name.split()[0], ha="center", va="center", fontsize=6, color="white", weight="bold", zorder=5)

    xs = [hex_to_pixel(c["q"], c["r"], size, LAYOUT, mid)[0] for c in seats]
    ys = [hex_to_pixel(c["q"], c["r"], size, LAYOUT, mid)[1] for c in seats]
    pad = size * 1.8
    ax.set_xlim(min(xs) - pad, max(xs) + pad)
    ax.set_ylim(min(ys) - pad, max(ys) + pad)
    ax.set_aspect("equal")
    ax.axis("off")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    constituencies = load_data()
    all_pixels = seat_pixels(constituencies, size=1.0)
    all_occupied = {(c["q"], c["r"]) for c in constituencies}
    mid = compute_range(constituencies)

    # Full map
    fig, ax = plt.subplots(figsize=(10, 14), facecolor="#1a1a2e")
    ax.set_facecolor("#1a1a2e")
    draw_region(ax, list(all_pixels.values()), size=0.42, mid=mid, highlight=set(LANDMARKS), all_occupied=all_occupied, show_labels=False)
    ax.set_title(f"February 1974 — landmark constituencies (gold outline)", color="white", fontsize=14, pad=12)
    fig.tight_layout()
    fig.savefig(OUT / "feb1974-full-landmarks.png", dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)

    # Regional zooms
    for key, spec in REGIONS.items():
        seats = seats_in_region(all_pixels, spec["centres"], spec["radius"])
        if not seats:
            continue
        local_mid = compute_range(seats)
        fig, ax = plt.subplots(figsize=(9, 8), facecolor="#f5f5f0")
        ax.set_facecolor("#f5f5f0")
        highlights = {n for n in LANDMARKS if any(s["name"] == n for s in seats)}
        draw_region(ax, seats, size=1.0, mid=local_mid, highlight=highlights, all_occupied=all_occupied, show_labels=True)
        ax.set_title(f"February 1974 — {spec['title']}", fontsize=12, pad=10)
        fig.text(
            0.5,
            0.02,
            "Gold = your listed seats · Red hatched = empty neighbour (should be none)",
            ha="center",
            fontsize=9,
            color="#444",
        )
        fig.tight_layout(rect=(0, 0.04, 1, 1))
        fig.savefig(OUT / f"feb1974-zoom-{key}.png", dpi=180, facecolor=fig.get_facecolor())
        plt.close(fig)

    print(f"Wrote previews to {OUT}/")


if __name__ == "__main__":
    main()
