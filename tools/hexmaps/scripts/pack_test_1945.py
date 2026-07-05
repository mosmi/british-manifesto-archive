#!/usr/bin/env python3
"""
pack_test_1945.py — Test pack of 1945 with outer-London constituencies
reclassified as South East instead of London.

The standard assign_region() uses 2024 centroids, which puts ~112 seats into
London for 1945 boundaries — including all of Middlesex, outer Surrey, outer
Essex and outer Kent that did not form part of the London County Council.

This test caps London at a specified seat count (default 75, matching 2024),
reclassifying the excess (most-peripheral) seats as South East, and repacks
the 1945 hex map with that adjusted assignment.

Usage:
    python3 scripts/pack_test_1945.py [--london-cap N]
    # Output: output/1945_test.hexjson  (then run colour.py --year 1945 --hexjson ...)
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pack import (
    load_2024_reference, load_year_features, assign_region,
    shrink_mask, grow_mask, geographic_assign_region, fill_holes,
    odd_r_neighbors, REGION_ANCHOR_CELLS, PERMANENT_GAPS,
    ISLAND_DEFS, SE_COASTAL_PREASSIGN, _lap_solve,
)

BASE   = Path(__file__).resolve().parent.parent
OUTPUT = BASE / "output"

# Geographic centroid of the historic London County Council area
LCC_LON, LCC_LAT = -0.09, 51.51

LONDON_GROW_R_FLOOR   = -43
SHRINK_PREFER_NORTH   = {"E12000009", "E12000008"}
SE_PRE74_DROP         = {(59, -35), (60, -35), (59, -43)}   # same as pack.py for year<1974


def pack_1945_test(london_cap: int = 75, output_path: Path | None = None, verbose: bool = True):
    def log(*args):
        if verbose:
            print(*args)

    log(f"=== Packing 1945 (test — London capped at {london_cap}) ===")
    masks_2024, eng_pts = load_2024_reference()

    mainland_feats, island_feats, outside_names = load_year_features(1945)
    log(f"  {len(mainland_feats)} mainland + {len(island_feats)} island"
        f" + {len(outside_names)} outside-boundary")

    # Standard region assignment
    by_region: dict[str, list] = defaultdict(list)
    for name, source, lon, lat in mainland_feats:
        region = assign_region(source, lon, lat, eng_pts)
        by_region[region].append((name, lon, lat))

    # --- Reclassify outer-London seats as SE ---
    london_seats = by_region.get("E12000007", [])
    if len(london_seats) > london_cap:
        # Sort by geographic distance from LCC centroid; keep the closest N.
        london_by_dist = sorted(
            london_seats,
            key=lambda s: (s[1] - LCC_LON) ** 2 + (s[2] - LCC_LAT) ** 2,
        )
        keep   = london_by_dist[:london_cap]
        reclassify = london_by_dist[london_cap:]
        by_region["E12000007"] = keep
        by_region["E12000008"].extend(reclassify)
        log(f"  Reclassified {len(reclassify)} outer-London seats → SE")
        log(f"  Outermost moved: {reclassify[-5:]}")

    log("Region seat counts (test vs 2024 mask):")
    for code, seats in sorted(by_region.items()):
        log(f"  {code}: {len(seats):3d}  (2024: {len(masks_2024.get(code, []))})")

    # Island buffer
    island_cells  = {(q, r) for _, q, r, _ in island_feats}
    island_buffer = island_cells | {nb for q, r in island_cells for nb in odd_r_neighbors(q, r)}

    # growing_region_cells — same logic as pack.py
    growing_region_cells: set = set()
    for region, seats in by_region.items():
        if len(seats) > len(masks_2024.get(region, [])):
            cells = list(masks_2024.get(region, []))
            if region == "E12000007":
                cells = [c for c in cells if c[1] > LONDON_GROW_R_FLOOR]
            growing_region_cells.update(cells)

    current_masks = {
        r: set(c) - island_buffer - PERMANENT_GAPS
        for r, c in masks_2024.items()
    }

    # Year-conditional SE anchors (pre-1974: drop the cells that become islands)
    effective_anchors = {}
    for region, cells in REGION_ANCHOR_CELLS.items():
        if region == "E12000008":
            effective_anchors[region] = cells - SE_PRE74_DROP
        else:
            effective_anchors[region] = cells

    # Pass 1 — shrink
    for region, seats in by_region.items():
        n    = len(seats)
        base = current_masks.get(region, set())
        if n < len(base):
            current_masks[region] = shrink_mask(
                base, n,
                beneficiary_cells=growing_region_cells,
                prefer_remove_north=(region in SHRINK_PREFER_NORTH),
                pinned_cells=effective_anchors.get(region),
            )
        elif region not in current_masks:
            current_masks[region] = set()

    all_occupied = (
        {c for mask in current_masks.values() for c in mask}
        | island_buffer | PERMANENT_GAPS
    )

    # Pass 2 — grow
    for region, seats in sorted(by_region.items()):
        n    = len(seats)
        base = current_masks.get(region, set())
        if n > len(base):
            base_list = list(base)
            if base_list:
                q_c = sum(c[0] for c in base_list) / len(base_list)
                r_c = sum(c[1] for c in base_list) / len(base_list)
                centroid_hint = (q_c, r_c)
            else:
                centroid_hint = None
            r_floor = LONDON_GROW_R_FLOOR if region == "E12000007" else None
            grown   = grow_mask(base, n, all_occupied,
                                centroid_hint=centroid_hint, r_floor=r_floor)
            current_masks[region] = grown
            all_occupied.update(grown - base)

    # Assignment
    hexes: dict = {}
    warnings = []
    for region, seats in by_region.items():
        mask_set = set(current_masks.get(region, []))
        n = len(seats)
        if len(mask_set) < n:
            warnings.append(f"{region}: only {len(mask_set)} cells for {n} seats")
        assignment = geographic_assign_region(
            [(name, lon, lat) for name, lon, lat in seats],
            list(mask_set),
            use_hungarian=(region == "E12000008"),
        )
        for name, (q, r) in assignment.items():
            hexes[name] = {"n": name, "q": q, "r": r, "region": region}

    # Islands
    for name, q, r, region in island_feats:
        hexes[name] = {"n": name, "q": q, "r": r, "region": region, "island": True}

    # South Wales q-shift (same as pack.py for year < 1974)
    for h in hexes.values():
        if h.get("region") == "W92000004" and -38 <= h["r"] <= -34:
            h["q"] += 2

    # Fill holes
    hexes = fill_holes(hexes, {}, island_buffer=island_buffer)

    for w in warnings:
        log(f"  WARNING: {w}")

    output = {"layout": "odd-r", "hexes": hexes}
    OUTPUT.mkdir(exist_ok=True)
    out_path = output_path or OUTPUT / "1945_test.hexjson"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    log(f"\nWrote {len(hexes)}/{len(mainland_feats)+len(island_feats)} hexes → {out_path}")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--london-cap", type=int, default=75,
                        help="Max London seats before reclassifying outer seats as SE (default 75)")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    pack_1945_test(london_cap=args.london_cap, output_path=args.output)
