#!/usr/bin/env python3
"""
pack_test_1945_v2.py — 1945 test using historical "Southern" and "South Eastern"
civil defence regions, splitting the current monolithic SE + outer-London area.

Region definitions (approximate 1945 civil defence regions):
  LONDON_LCC   — inner London County Council boroughs (~43 seats)
  SOUTHERN     — Middlesex + Berkshire + Buckinghamshire + Oxfordshire
                 + Hampshire + Isle of Wight (~53 seats)
  SOUTH_EASTERN — Surrey + Kent + East Sussex + West Sussex
                  + outer south/east London suburbs (~47 seats)

All other ONS regions (Scotland, Wales, NI, NE, NW, Yorks, East Midlands,
West Midlands, East, South West) are processed with the standard algorithm.

Usage:
    python3 scripts/pack_test_1945_v2.py
    # Output: output/1945_test_v2.hexjson
    python3 scripts/compare_test_1945.py  (update paths to include v2)
"""

import json, math
from pathlib import Path
from collections import defaultdict

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pack import (
    load_2024_reference, load_year_features, assign_region,
    shrink_mask, grow_mask, geographic_assign_region, fill_holes,
    odd_r_neighbors, REGION_ANCHOR_CELLS, PERMANENT_GAPS,
    SE_COASTAL_PREASSIGN, BRIGHTON_PREASSIGN_1983, _lap_solve,
)

BASE   = Path(__file__).resolve().parent.parent
OUTPUT = BASE / "output"

LCC_LON, LCC_LAT = -0.09, 51.51   # geographic LCC centroid
LCC_Q,   LCC_R   = 63.0, -40.0    # hex centroid of inner London

LONDON_GROW_R_FLOOR = -43

# Seats that make the Southern/SE distinction unclear — use lon/lat rules
def classify_seat(name: str, lon: float, lat: float, standard_region: str) -> str:
    """Classify a London- or SE-classified seat into one of three new regions."""
    dist_lcc = math.hypot(lon - LCC_LON, lat - LCC_LAT)

    if standard_region == "E12000007":          # currently London-classified
        if dist_lcc < 0.085:
            return "LONDON_LCC"
        # Northern outer London = Middlesex (high lat + northwest quadrant)
        if (lon < -0.20 and lat > 51.40) or (-0.20 <= lon < 0.05 and lat > 51.55):
            return "SOUTHERN"
        return "SOUTH_EASTERN"                   # south/east London suburbs

    elif standard_region == "E12000008":         # currently SE-classified
        if lon < -0.50:                          # Hampshire, Berks, Bucks, Oxon, IoW
            return "SOUTHERN"
        return "SOUTH_EASTERN"                   # Surrey, Kent, Sussex

    return standard_region                       # all other regions unchanged


def build_custom_masks(masks_2024: dict) -> dict[str, set]:
    """
    Split the combined London-2024 + SE-2024 cell pool into three non-overlapping
    masks that serve as starting points for the shrink/grow passes.

    London LCC  : innermost 43 cells of the 2024 London mask (by hex distance
                  from the LCC centroid q=63, r=-40).
    Southern    : remaining 32 outer-London cells  +  SE cells with q ≤ 61.
    South Eastern: SE cells with q > 61.
    """
    lon_pool = sorted(
        masks_2024["E12000007"],
        key=lambda c: (c[0] - LCC_Q) ** 2 + (c[1] - LCC_R) ** 2,
    )
    lcc_mask    = set(lon_pool[:43])     # innermost 43
    outer_lon   = set(lon_pool[43:])     # outer 32 (Middlesex territory)

    se_pool = masks_2024["E12000008"]
    se_west = {c for c in se_pool if c[0] <= 61}   # Southern cells
    se_east = {c for c in se_pool if c[0] > 61}    # South Eastern cells

    custom: dict[str, set] = {
        k: v for k, v in masks_2024.items()
        if k not in ("E12000007", "E12000008")
    }
    custom["LONDON_LCC"]    = lcc_mask
    custom["SOUTHERN"]      = outer_lon | se_west     # 32 + 56 = 88 cells
    custom["SOUTH_EASTERN"] = se_east                 # 35 cells (grows to 47)
    return custom


def pack_1945_v2(output_path: Path | None = None, verbose: bool = True):
    def log(*args):
        if verbose:
            print(*args)

    log("=== Packing 1945 v2 — Southern / South Eastern historical regions ===")
    masks_2024, eng_pts = load_2024_reference()

    mainland_feats, island_feats, outside_names = load_year_features(1945)
    log(f"  {len(mainland_feats)} mainland + {len(island_feats)} island"
        f" + {len(outside_names)} outside-boundary")

    # Standard region assignment, then reclassify London + SE
    by_region: dict[str, list] = defaultdict(list)
    for name, source, lon, lat in mainland_feats:
        std = assign_region(source, lon, lat, eng_pts)
        reg = classify_seat(name, lon, lat, std)
        by_region[reg].append((name, lon, lat))

    log("Region seat counts (vs 2024 mask / custom mask):")
    for code, seats in sorted(by_region.items()):
        log(f"  {code}: {len(seats):3d} seats")

    # Island buffer
    island_cells  = {(q, r) for _, q, r, _ in island_feats}
    island_buffer = island_cells | {
        nb for q, r in island_cells for nb in odd_r_neighbors(q, r)
    }

    # Build custom starting masks
    current_masks = {
        r: s - island_buffer - PERMANENT_GAPS
        for r, s in build_custom_masks(masks_2024).items()
    }

    # growing_region_cells for adj_benefit scoring
    growing_region_cells: set = set()
    for region, seats in by_region.items():
        if len(seats) > len(current_masks.get(region, [])):
            cells = list(current_masks.get(region, []))
            if region == "LONDON_LCC":
                cells = [c for c in cells if c[1] > LONDON_GROW_R_FLOOR]
            growing_region_cells.update(cells)

    # SE anchor cells (pre-1974: drop the cells that become islands)
    SE_PRE74_DROP = {(59, -35), (60, -35), (59, -43)}
    def anchors_for(region: str) -> set | None:
        if region in ("SOUTHERN", "SOUTH_EASTERN"):
            base = REGION_ANCHOR_CELLS.get("E12000008", set())
            return base - SE_PRE74_DROP
        return REGION_ANCHOR_CELLS.get(region)

    # Pass 1 — shrink
    # Southern: prefer_remove_north=False to keep the northern Middlesex+Bucks cells
    #           and remove excess from the southern/coastal end first.
    # South Eastern: prefer_remove_north=True to preserve the Sussex coast.
    SHRINK_PREFER_NORTH = {"E12000009", "SOUTH_EASTERN"}
    for region, seats in by_region.items():
        n    = len(seats)
        base = current_masks.get(region, set())
        if n < len(base):
            current_masks[region] = shrink_mask(
                base, n,
                beneficiary_cells=growing_region_cells,
                prefer_remove_north=(region in SHRINK_PREFER_NORTH),
                pinned_cells=anchors_for(region),
            )
        elif region not in current_masks:
            current_masks[region] = set()

    all_occupied = (
        {c for mask in current_masks.values() for c in mask}
        | island_buffer | PERMANENT_GAPS
    )

    # Pass 2 — grow (South Eastern needs to grow from 35 → 47)
    for region, seats in sorted(by_region.items()):
        n    = len(seats)
        base = current_masks.get(region, set())
        if n > len(base):
            base_list = list(base)
            if base_list:
                q_c = sum(c[0] for c in base_list) / len(base_list)
                r_c = sum(c[1] for c in base_list) / len(base_list)
                centroid = (q_c, r_c)
            else:
                centroid = None
            r_floor = LONDON_GROW_R_FLOOR if region == "LONDON_LCC" else None
            grown   = grow_mask(base, n, all_occupied,
                                centroid_hint=centroid, r_floor=r_floor)
            current_masks[region] = grown
            all_occupied.update(grown - base)

    # Assignment — Hungarian for SOUTHERN and SOUTH_EASTERN
    hexes: dict = {}
    warnings = []
    for region, seats in by_region.items():
        mask_set = set(current_masks.get(region, []))
        n = len(seats)
        if len(mask_set) < n:
            warnings.append(f"{region}: only {len(mask_set)} cells for {n} seats")
        use_hungarian = region in ("SOUTHERN", "SOUTH_EASTERN")
        assignment = geographic_assign_region(
            [(name, lon, lat) for name, lon, lat in seats],
            list(mask_set),
            use_hungarian=use_hungarian,
        )
        for name, (q, r) in assignment.items():
            hexes[name] = {"n": name, "q": q, "r": r, "region": region}

    # Islands
    for name, q, r, region in island_feats:
        hexes[name] = {"n": name, "q": q, "r": r, "region": region, "island": True}

    # South Wales q-shift (pre-1974)
    for h in hexes.values():
        if h.get("region") == "W92000004" and -38 <= h["r"] <= -34:
            h["q"] += 2

    hexes = fill_holes(hexes, {}, island_buffer=island_buffer)

    for w in warnings:
        log(f"  WARNING: {w}")

    output = {"layout": "odd-r", "hexes": hexes}
    OUTPUT.mkdir(exist_ok=True)
    out_path = output_path or OUTPUT / "1945_test_v2.hexjson"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    log(f"\nWrote {len(hexes)}/{len(mainland_feats)+len(island_feats)} hexes → {out_path}")
    return output


if __name__ == "__main__":
    pack_1945_v2()
