#!/usr/bin/env python3
"""
pack_1945_on_2010base.py — map 1945 election onto the 2010 hex layout.

Uses the Open Innovations 2010 constituency hexjson (odd-r, q:-17→13, r:-16→28)
as the fixed tile positions, with three regional treatments:

  Scotland  — 2010 SC cells (59) expanded to fit 1945's ~65 mainland Scottish
               seats using grow_mask, then Hungarian-assigned.  Orkney &
               Shetland and Western Isles snap to the 2010 island positions.

  N Ireland — 6 1945 NI seats Hungarian-assigned to the best 6 of the 18
               2010 NI cells.

  Rest      — England + Wales Hungarian-assigned across all remaining 2010 cells.

Output: output/1945_on_2010base.hexjson
        python3 scripts/colour.py --year 1945 --hexjson output/1945_on_2010base.hexjson
"""

import json, re, math
from pathlib import Path
from collections import defaultdict

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pack import (
    load_2024_reference, load_year_features, assign_region,
    compute_centroid, grow_mask, geographic_assign_region,
    odd_r_neighbors, OUTSIDE_BOUNDARY_1945, _lap_solve,
)

BASE      = Path(__file__).resolve().parent.parent
REFERENCE = BASE / "reference"
SOURCES   = BASE / "sources" / "geojson"
OUTPUT    = BASE / "output"

HEXJSON_2010 = REFERENCE / "constituencies_2010.hexjson"
GEOJSON_2010 = SOURCES / "2010-combined.geojson"

# 2010 positions for Scottish islands (do not allocate to mainland pool)
SCOT_ISLAND_CELLS = {(-5, 28), (-8, 26)}  # Orkney & Shetland, Western Isles

_DIR_EXPAND = {
    r"\bN\b": "North", r"\bS\b": "South", r"\bE\b": "East", r"\bW\b": "West",
    r"\bNE\b": "North East", r"\bNW\b": "North West",
    r"\bSE\b": "South East", r"\bSW\b": "South West",
    r"\bCen\b": "Central", r"\bCentl\b": "Central",
}

def normalise(name: str) -> str:
    s = name.strip().replace("&", "and")
    for pattern, replacement in _DIR_EXPAND.items():
        s = re.sub(pattern, replacement, s)
    s = s.lower()
    s = re.sub(r"[',.\-()]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def build_geo_centroids(geojson_path: Path) -> dict[str, tuple[float, float]]:
    data = json.loads(geojson_path.read_text())
    out: dict = {}
    for feat in data["features"]:
        name = feat["properties"].get("Name", feat["properties"].get("name", ""))
        centroid = compute_centroid(feat["geometry"])
        if centroid:
            out[normalise(name)] = centroid
    return out


def best_centroid_match(name: str, geo_centroids: dict) -> tuple | None:
    key = normalise(name)
    if key in geo_centroids:
        return geo_centroids[key]
    tokens = set(key.split())
    best, best_score = None, 0.0
    for geo_key, centroid in geo_centroids.items():
        score = len(tokens & set(geo_key.split())) / max(len(tokens | set(geo_key.split())), 1)
        if score > best_score:
            best_score, best = score, centroid
    return best if best_score >= 0.5 else None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def pack_1945_on_2010(output_path: Path | None = None, verbose: bool = True):
    def log(*args):
        if verbose:
            print(*args)

    log("=== Packing 1945 on 2010 hex base ===")

    # ── Load 2010 hexjson ────────────────────────────────────────────────────
    hex2010    = json.loads(HEXJSON_2010.read_text())
    hexes_2010 = hex2010["hexes"]
    log(f"  2010 hexjson: {len(hexes_2010)} hexes")

    # ── Build centroid lookup for 2010 hexes ─────────────────────────────────
    geo_centroids = build_geo_centroids(GEOJSON_2010)

    hex_centroid: dict = {}
    unmatched: list = []
    for ons, h in hexes_2010.items():
        c = best_centroid_match(h["n"], geo_centroids)
        if c:
            hex_centroid[ons] = c
        else:
            unmatched.append((ons, h))

    # Last-resort: nearest already-matched hex by grid distance
    matched_ons = list(hex_centroid.keys())
    for ons, h in unmatched:
        best_ons = min(matched_ons,
                       key=lambda m: (h["q"]-hexes_2010[m]["q"])**2 + (h["r"]-hexes_2010[m]["r"])**2)
        blon, blat = hex_centroid[best_ons]
        hex_centroid[ons] = (blon + (h["q"]-hexes_2010[best_ons]["q"])*0.1,
                             blat + (h["r"]-hexes_2010[best_ons]["r"])*0.1)

    log(f"  Centroid coverage: {len(hex_centroid)}/{len(hexes_2010)}")

    # ── Load 1945 features and classify by region ────────────────────────────
    _, eng_pts = load_2024_reference()
    mainland_feats, island_feats, outside_names = load_year_features(1945)
    log(f"  1945: {len(mainland_feats)} mainland, {len(island_feats)} islands, "
        f"{len(outside_names)} outside-boundary")

    by_region: dict[str, list] = defaultdict(list)
    for name, source, lon, lat in mainland_feats:
        region = assign_region(source, lon, lat, eng_pts)
        by_region[region].append((name, lon, lat))

    scot_seats  = by_region.get("S92000003", [])
    ni_seats    = by_region.get("N92000002", [])
    other_seats = [(n, lo, la)
                   for reg, seats in by_region.items()
                   if reg not in ("S92000003", "N92000002")
                   for n, lo, la in seats]

    log(f"  Scotland: {len(scot_seats)}, NI: {len(ni_seats)}, "
        f"England+Wales: {len(other_seats)}")

    # ── Cell pools by region ─────────────────────────────────────────────────
    all_2010_cells = {(h["q"], h["r"]) for h in hexes_2010.values()}

    sc_all_cells   = {(h["q"], h["r"]) for h in hexes_2010.values() if h["a"] == "SC"}
    ni_all_cells   = [(h["q"], h["r"]) for h in hexes_2010.values() if h["a"] == "NI"]
    sc_main_cells  = sc_all_cells - SCOT_ISLAND_CELLS
    reserved_cells = sc_all_cells | set(ni_all_cells)

    other_cells = [
        (h["q"], h["r"], *hex_centroid[ons], ons, h["n"])
        for ons, h in hexes_2010.items()
        if (h["q"], h["r"]) not in reserved_cells and ons in hex_centroid
    ]
    log(f"  Cell pools — Scotland mainland: {len(sc_main_cells)}, "
        f"NI: {len(ni_all_cells)}, England+Wales: {len(other_cells)}")

    hexes_out: dict = {}

    # ── SCOTLAND ─────────────────────────────────────────────────────────────
    n_scot = len(scot_seats)
    if len(sc_main_cells) < n_scot:
        extra = n_scot - len(sc_main_cells)
        log(f"  Scotland: expanding {len(sc_main_cells)} cells by {extra} "
            f"to fit {n_scot} seats")
        # Grow into space not occupied by OTHER 2010 regions
        # (allow growth into gaps inside the SC shape and just beyond its edge)
        non_sc_occupied = all_2010_cells - sc_all_cells
        # Centroid hint = current SC mainland centroid (Central Belt)
        qs = [q for q, r in sc_main_cells]
        rs = [r for q, r in sc_main_cells]
        centroid = (sum(qs)/len(qs), sum(rs)/len(rs))
        sc_main_cells = grow_mask(
            sc_main_cells, n_scot, non_sc_occupied, centroid_hint=centroid
        )
        log(f"  Scotland expanded to {len(sc_main_cells)} cells")

    scot_assignment = geographic_assign_region(
        scot_seats, list(sc_main_cells), use_hungarian=True
    )
    for name, (q, r) in scot_assignment.items():
        hexes_out[name] = {"n": name, "q": q, "r": r, "region": "SC"}

    # ── SCOTLAND ISLANDS ─────────────────────────────────────────────────────
    # Map 1945 island names to 2010 island positions
    island_pos_map = {
        "orkney":        (-5, 28),
        "shetland":      (-5, 28),
        "western isles": (-8, 26),
        "na h-eileanan": (-8, 26),
    }
    for name, q, r, region in island_feats:
        if region == "S92000003":
            key = name.lower()
            cell = next(
                (pos for k, pos in island_pos_map.items() if k in key), None
            )
            if cell:
                hexes_out[name] = {"n": name, "q": cell[0], "r": cell[1],
                                   "region": "SC"}
        # Other islands (Anglesey, etc.) fall through to the mainland assignment below

    # ── NORTHERN IRELAND ─────────────────────────────────────────────────────
    ni_assignment = geographic_assign_region(
        ni_seats, ni_all_cells, use_hungarian=True
    )
    for name, (q, r) in ni_assignment.items():
        hexes_out[name] = {"n": name, "q": q, "r": r, "region": "NI"}

    # ── ENGLAND + WALES (+ non-Scottish islands) ─────────────────────────────
    # Also include non-Scottish island_feats in the England/Wales seats
    ew_seats = list(other_seats)
    for name, q_std, r_std, region in island_feats:
        if region != "S92000003":
            # Find this seat's centroid from mainland_feats
            match = next(
                (f for f in mainland_feats if f[0] == name), None
            )
            if match:
                ew_seats.append((name, match[2], match[3]))

    n_ew = len(ew_seats)
    n_ew_cells = len(other_cells)
    log(f"  England+Wales: {n_ew} seats → {n_ew_cells} cells")

    # Project and Hungarian-assign
    seat_lons = [lo for _, lo, _ in ew_seats]
    seat_lats = [la for _, _, la in ew_seats]
    lon_min, lon_max = min(seat_lons), max(seat_lons)
    lat_min, lat_max = min(seat_lats), max(seat_lats)

    hex_qs = [h[0] for h in other_cells]
    hex_rs = [h[1] for h in other_cells]
    q_min, q_max = min(hex_qs), max(hex_qs)
    r_min, r_max = min(hex_rs), max(hex_rs)

    def project(lon, lat):
        q_f = (q_min + (lon - lon_min) / (lon_max - lon_min) * (q_max - q_min)
               if lon_max > lon_min else (q_min + q_max) / 2)
        r_f = (r_min + (lat - lat_min) / (lat_max - lat_min) * (r_max - r_min)
               if lat_max > lat_min else (r_min + r_max) / 2)
        return q_f, r_f

    projections = [(nm, lo, la, *project(lo, la)) for nm, lo, la in ew_seats]

    log("  Building England+Wales cost matrix…")
    cost_rows = [
        [(other_cells[j][0] - q_f)**2 + 4*(other_cells[j][1] - r_f)**2
         for j in range(n_ew_cells)]
        for _, _, _, q_f, r_f in projections
    ]

    log("  Running Hungarian…")
    col_for_row = _lap_solve(cost_rows)

    assignment_log = []
    for i, (nm, lo, la, q_f, r_f) in enumerate(projections):
        j = col_for_row[i]
        q, r, hlon, hlat, ons, hname = other_cells[j]
        dist_deg = math.hypot(lo - hlon, la - hlat)
        assignment_log.append((dist_deg, nm, hname))
        region_abbr = hexes_2010.get(ons, {}).get("a", "??")
        hexes_out[nm] = {"n": nm, "q": q, "r": r, "region": region_abbr}

    # ── Report ────────────────────────────────────────────────────────────────
    assignment_log.sort(reverse=True)
    log("\n  Largest mismatches (1945 seat → 2010 hex):")
    for dist, seat, hex_name in assignment_log[:10]:
        log(f"    {dist:.2f}°  '{seat}' → '{hex_name}'")

    log(f"\n  Total seats placed: {len(hexes_out)}")
    log(f"  Empty 2010 hexes: {len(hexes_2010) - len(hexes_out)}")

    out = {"layout": "odd-r", "hexes": hexes_out}
    OUTPUT.mkdir(exist_ok=True)
    out_path = output_path or OUTPUT / "1945_on_2010base.hexjson"
    out_path.write_text(json.dumps(out, indent=2))
    log(f"\nWrote → {out_path}")
    return out


if __name__ == "__main__":
    pack_1945_on_2010()
