#!/usr/bin/env python3
"""Simplify ONS European Electoral Region boundaries into a lightweight SVG path asset.

Reads:
  data/sources/commons-library/eer-2018-ugcb.geojson

Writes:
  data/maps/euro-regions.json

Coordinates are projected to a fixed SVG viewBox (lon/lat → x/y) with heavy
Douglas–Peucker simplification so the runtime asset stays small.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/sources/commons-library/eer-2018-ugcb.geojson"
OUT = ROOT / "data/maps/euro-regions.json"

# ONS name → site region id
NAME_TO_ID = {
    "North East": "north-east",
    "North West": "north-west",
    "Yorkshire and The Humber": "yorkshire-humber",
    "East Midlands": "east-midlands",
    "West Midlands": "west-midlands",
    "Eastern": "east-of-england",
    "London": "london",
    "South East": "south-east",
    "South West": "south-west",
    "Wales": "wales",
    "Scotland": "scotland",
    "Northern Ireland": "northern-ireland",
}

REGION_ORDER = [
    "scotland",
    "northern-ireland",
    "north-east",
    "north-west",
    "yorkshire-humber",
    "east-midlands",
    "west-midlands",
    "wales",
    "east-of-england",
    "london",
    "south-east",
    "south-west",
]

# SVG viewBox padding / size
VB_W = 420
VB_H = 560
PAD = 12

# Extra simplification for Scotland's fragmented coastline
EPSILON = {
    "scotland": 0.045,
    "northern-ireland": 0.025,
    "south-west": 0.025,
    "default": 0.018,
}

# Optional nudges from the projected ONS centroid (SVG dx/dy).
# London is a callout to the east — its dense land area can't hold 8 squares.
SEAT_NUDGES = {
    "scotland": {"dx": 8, "dy": -18},          # clear of Highland islands
    "northern-ireland": {"dx": 0, "dy": -4},
    "north-east": {"dx": 6, "dy": -2},
    "north-west": {"dx": -4, "dy": 0},
    "yorkshire-humber": {"dx": 4, "dy": -4},
    "east-midlands": {"dx": 2, "dy": -6},
    "west-midlands": {"dx": -2, "dy": 11},     # +15 vs prior (-4)
    "wales": {"dx": -6, "dy": -8},
    "east-of-england": {"dx": 10, "dy": -4},
    "south-east": {"dx": 28, "dy": 33},        # below London callout (+25 vs prior)
    "south-west": {"dx": -8, "dy": 5},         # -10 vs prior (15)
    "london": {
        "dx": 78, "dy": -6,
        "callout": True,
        # attach stays on the geographic centroid
    },
}

# Short labels drawn near clusters
SHORT_LABELS = {
    "scotland": "Scotland",
    "northern-ireland": "N. Ireland",
    "north-east": "North East",
    "north-west": "North West",
    "yorkshire-humber": "Yorks & Humber",
    "east-midlands": "East Midlands",
    "west-midlands": "West\nMidlands",
    "wales": "Wales",
    "east-of-england": "East",
    "london": "London",
    "south-east": "South East",
    "south-west": "South West",
}


def perpendicular_distance(pt, start, end):
    (x, y), (x1, y1), (x2, y2) = pt, start, end
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(x - x1, y - y1)
    t = ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    projx, projy = x1 + t * dx, y1 + t * dy
    return math.hypot(x - projx, y - projy)


def douglas_peucker(points, epsilon):
    if len(points) < 3:
        return points
    start, end = points[0], points[-1]
    max_dist = -1.0
    index = 0
    for i in range(1, len(points) - 1):
        d = perpendicular_distance(points[i], start, end)
        if d > max_dist:
            max_dist = d
            index = i
    if max_dist > epsilon:
        left = douglas_peucker(points[: index + 1], epsilon)
        right = douglas_peucker(points[index:], epsilon)
        return left[:-1] + right
    return [start, end]


def ring_area(ring):
    a = 0.0
    for i in range(len(ring) - 1):
        x1, y1 = ring[i]
        x2, y2 = ring[i + 1]
        a += x1 * y2 - x2 * y1
    return abs(a) * 0.5


def project_bounds(features):
    min_lon = min_lat = float("inf")
    max_lon = max_lat = float("-inf")

    def walk(coords, depth):
        nonlocal min_lon, max_lon, min_lat, max_lat
        if depth == 0:
            lon, lat = coords[0], coords[1]
            min_lon = min(min_lon, lon)
            max_lon = max(max_lon, lon)
            min_lat = min(min_lat, lat)
            max_lat = max(max_lat, lat)
        else:
            for c in coords:
                walk(c, depth - 1)

    for f in features:
        g = f["geometry"]
        depth = 2 if g["type"] == "Polygon" else 3
        walk(g["coordinates"], depth)
    return min_lon, min_lat, max_lon, max_lat


def make_projector(bounds):
    min_lon, min_lat, max_lon, max_lat = bounds
    # Slight latitude stretch so Britain isn't too squat
    lat_mid = (min_lat + max_lat) / 2
    cos_mid = math.cos(math.radians(lat_mid))
    width = (max_lon - min_lon) * cos_mid
    height = max_lat - min_lat
    scale = min((VB_W - 2 * PAD) / width, (VB_H - 2 * PAD) / height)

    def project(lon, lat):
        x = PAD + (lon - min_lon) * cos_mid * scale
        y = PAD + (max_lat - lat) * scale
        return (round(x, 2), round(y, 2))

    return project


def simplify_ring(ring, epsilon, project):
    pts = [(float(lon), float(lat)) for lon, lat in ring]
    # Drop tiny rings (islets) before simplify
    if ring_area(pts) < 0.002:
        return None
    simp = douglas_peucker(pts, epsilon)
    if len(simp) < 3:
        return None
    # Close ring
    if simp[0] != simp[-1]:
        simp.append(simp[0])
    return [project(lon, lat) for lon, lat in simp]


def geom_to_path(geom, epsilon, project):
    parts = []
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    # Keep largest few polygons per region (mainland + major islands)
    scored = []
    for poly in polys:
        outer = poly[0]
        scored.append((ring_area([(c[0], c[1]) for c in outer]), poly))
    scored.sort(reverse=True)
    keep = scored[:6] if len(scored) > 6 else scored

    for _, poly in keep:
        for i, ring in enumerate(poly):
            # Only keep holes that are reasonably large
            if i > 0 and ring_area([(c[0], c[1]) for c in ring]) < 0.01:
                continue
            proj_ring = simplify_ring(ring, epsilon if i == 0 else epsilon * 1.5, project)
            if not proj_ring or len(proj_ring) < 4:
                continue
            cmds = [f"M{proj_ring[0][0]},{proj_ring[0][1]}"]
            for x, y in proj_ring[1:]:
                cmds.append(f"L{x},{y}")
            cmds.append("Z")
            parts.append("".join(cmds))
    return "".join(parts)


def main():
    raw = json.loads(SRC.read_text())
    features = raw["features"]
    bounds = project_bounds(features)
    project = make_projector(bounds)

    by_id = {}
    for f in features:
        name = f["properties"].get("eer18nm")
        rid = NAME_TO_ID.get(name)
        if not rid:
            raise SystemExit(f"Unmapped ONS region name: {name!r}")
        eps = EPSILON.get(rid, EPSILON["default"])
        path = geom_to_path(f["geometry"], eps, project)
        if not path:
            raise SystemExit(f"Empty path for {rid}")
        lon = f["properties"].get("long")
        lat = f["properties"].get("lat")
        cx, cy = project(float(lon), float(lat))
        nudge = SEAT_NUDGES.get(rid, {})
        seat_x = round(cx + nudge.get("dx", 0), 2)
        seat_y = round(cy + nudge.get("dy", 0), 2)
        entry = {
            "id": rid,
            "name": name if name != "Eastern" else "East of England",
            "path": path,
            "label": SHORT_LABELS[rid],
            "seatX": seat_x,
            "seatY": seat_y,
        }
        if nudge.get("callout"):
            entry["callout"] = True
            entry["attachX"] = cx
            entry["attachY"] = cy
        by_id[rid] = entry

    regions = [by_id[rid] for rid in REGION_ORDER]

    # Tight viewBox around land + seat clusters (drops empty side gutters so the
    # SVG can fill the viz panel width like the parliament chart).
    xs, ys = [], []
    for r in regions:
        nums = [float(n) for n in re.findall(r"[-+]?\d*\.?\d+", r["path"])]
        xs.extend(nums[0::2])
        ys.extend(nums[1::2])
        # Seat waffle + label footprint
        xs.extend([r["seatX"] - 34, r["seatX"] + 34])
        ys.extend([r["seatY"] - 28, r["seatY"] + 22])
        if r.get("callout"):
            xs.extend([r["attachX"], r["seatX"] + 40])
            ys.extend([r["attachY"], r["seatY"]])
    pad = 10
    min_x, max_x = min(xs) - pad, max(xs) + pad
    min_y, max_y = min(ys) - pad, max(ys) + pad
    view_box = [
        round(min_x, 2),
        round(min_y, 2),
        round(max_x - min_x, 2),
        round(max_y - min_y, 2),
    ]

    doc = {
        "viewBox": view_box,
        "source": {
            "label": "ONS European Electoral Regions (Dec 2018) UGCB — simplified",
            "url": "https://geoportal.statistics.gov.uk/datasets/ons::european-electoral-regions-december-2018-boundaries-uk-bgc-2/about",
            "file": "data/sources/commons-library/eer-2018-ugcb.geojson",
        },
        "regions": regions,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(doc, ensure_ascii=False, separators=(",", ":"))
    OUT.write_text(text + "\n")
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes, {len(regions)} regions)")


if __name__ == "__main__":
    main()
