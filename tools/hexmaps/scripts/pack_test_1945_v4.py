#!/usr/bin/env python3
"""
pack_test_1945_v4.py — 1945: full natural London + region-free resize.

Key differences from v3:
  - No London cap: London grows from 75 to its full ~112 natural 1945 seats.
    Outer-London/Middlesex constituencies stay in London (not reclassified to SE).
  - No SE northern wrap: SE shrinks from 91 → ~48 (its natural 1945 count),
    staying entirely south/southeast of London.  Thames Estuary gap preserved.
  - Hungarian matching applied independently to London and SE (both improved
    over pack.py's greedy Dijkstra for London).
  - All other regions (NE, NW, Scotland, Wales) grow freely into freed space.

Output: output/1945_test_v4.hexjson
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

LONDON_GROW_R_FLOOR = -43
# Neither SE nor SW uses prefer_remove_north; we rely on anchors instead.
SHRINK_PREFER_NORTH: set = set()

# For 1945 SE (48 seats vs 2024's 91):
#   - No junction anchors (59,-43),(58,-42),(68,-42) — those isolate SE cells in
#     London territory when SE is small.
#   - Pin the full r=-44 south-coast bridge so Hampshire↔Sussex stays connected.
#   - Pin the inner western corridor (q=54–57, r=-37 to -42): these cells fill the
#     void between SW England and London that otherwise becomes 46 interior holes.
#   - Pin the Kent corridor (q=68–72, r=-39 to -42) for East-Kent connectivity.
#   With 89 starting cells and 62 anchors, shrinking to 48 will trim 14 anchors
#   (those most peripheral / adjacent to growing London); the critical coast and
#   corridor cells survive because they are deep inside SE territory.
SE_ANCHORS_1945 = frozenset(
    # South coast bridge r=-44 (full width Hampshire→Kent)
    {(q, -44) for q in range(55, 71)}
    # Deep south coast r=-45 (IoW + eastern Sussex)
    | {(54, -45), (68, -45), (69, -45)}
    # Inner western corridor (fills SW/London junction holes)
    | {(q, r) for q in range(54, 58) for r in range(-42, -36)}
    # Kent corridor
    | {(q, r) for q in range(68, 73) for r in range(-42, -38)}
)

# For 1945 SW (45 seats vs 2024's 58):
#   - Pin Cornwall (far south) so it is never removed.
#   - Pin the junction zone (q=51–53, r=-36 to -42): SW's eastern cells that
#     bridge the gap between SW England and SE/London, preventing western holes.
SW_ANCHORS_1945 = frozenset(
    # Cornwall southern tip
    {(43, -46), (43, -45), (44, -45), (44, -44), (45, -44), (46, -44)}
    # Junction zone: SW's eastern edge (r=-36 to -42)
    | {(q, r) for q in range(51, 54) for r in range(-42, -35)}
)


def pack_1945_v4(output_path: Path | None = None, verbose: bool = True):
    def log(*args):
        if verbose:
            print(*args)

    log("=== Packing 1945 v4 — full natural London, free region resize ===")
    masks_2024, eng_pts = load_2024_reference()

    mainland_feats, island_feats, outside_names = load_year_features(1945)
    log(f"  {len(mainland_feats)} mainland + {len(island_feats)} island"
        f" + {len(outside_names)} outside-boundary")

    # GOR polygon artefacts: a handful of 1945 constituencies whose centroids
    # fall just inside the wrong modern GOR polygon.  Override before bucketing.
    REGION_OVERRIDES: dict[str, str] = {
        "Uxbridge":              "E12000007",  # Middlesex → London (centroid in EoE polygon)
        "Rochester, Gillingham": "E12000008",  # Medway → SE  (centroid in EoE polygon)
        "Brigg":                 "E12000004",  # N Lincs → EM (centroid in YH polygon)
    }

    by_region: dict[str, list] = defaultdict(list)
    for name, source, lon, lat in mainland_feats:
        region = REGION_OVERRIDES.get(name) or assign_region(source, lon, lat, eng_pts)
        by_region[region].append((name, lon, lat))

    log("Region seat counts:")
    for code, seats in sorted(by_region.items()):
        log(f"  {code}: {len(seats):3d}  (2024 mask: {len(masks_2024.get(code, []))})")

    island_cells  = {(q, r) for _, q, r, _ in island_feats}
    island_buffer = island_cells | {nb for q, r in island_cells for nb in odd_r_neighbors(q, r)}

    # Which regions need more cells than their 2024 mask?
    growing_region_cells: set = set()
    for region, seats in by_region.items():
        if len(seats) > len(masks_2024.get(region, [])):
            cells = list(masks_2024.get(region, []))
            if region == "E12000007":
                cells = [c for c in cells if c[1] > LONDON_GROW_R_FLOOR]
            growing_region_cells.update(cells)

    # London will grow northward from r=-37 into r=-33 to -36.  Pre-hint those
    # cells so EoE's shrink prioritises removing its southernmost (London-adjacent)
    # cells first — preventing the alternating London/EoE pattern at r=-33/-34.
    growing_region_cells.update(
        (q, r) for q in range(57, 69) for r in range(-36, -32)
    )

    current_masks = {
        r: set(c) - island_buffer - PERMANENT_GAPS
        for r, c in masks_2024.items()
    }

    # -------------------------------------------------------------------------
    # Pass 1 — shrink regions that are SMALLER in 1945 than 2024
    # (EoE, SE, YH, EM, WM, SW, NI)
    # London and NE/NW/Scotland/Wales are larger → handled in Pass 2.
    # -------------------------------------------------------------------------
    shrink_order = sorted(
        [(region, seats) for region, seats in by_region.items()
         if len(seats) < len(current_masks.get(region, set()))],
        key=lambda x: x[0],
    )
    for region, seats in shrink_order:
        n    = len(seats)
        base = current_masks.get(region, set())
        log(f"  Shrink {region}: {len(base)} → {n}")
        if region == "E12000008":
            anchors = SE_ANCHORS_1945
        elif region == "E12000009":
            anchors = SW_ANCHORS_1945
        else:
            anchors = REGION_ANCHOR_CELLS.get(region)
        current_masks[region] = shrink_mask(
            base, n,
            beneficiary_cells=growing_region_cells,
            prefer_remove_north=(region in SHRINK_PREFER_NORTH),
            pinned_cells=anchors,
        )

    # -------------------------------------------------------------------------
    # Pass 2 — grow regions that are LARGER in 1945 than 2024
    # (NE, NW, London, Scotland, Wales)
    # -------------------------------------------------------------------------
    all_occupied = (
        {c for mask in current_masks.values() for c in mask}
        | island_buffer | PERMANENT_GAPS
    )

    grow_order = sorted(
        [(region, seats) for region, seats in by_region.items()
         if len(seats) > len(current_masks.get(region, set()))],
        key=lambda x: x[0],
    )
    for region, seats in grow_order:
        n    = len(seats)
        base = current_masks.get(region, set())
        if not base:
            continue
        centroid = (
            sum(c[0] for c in base) / len(base),
            sum(c[1] for c in base) / len(base),
        )
        r_floor = LONDON_GROW_R_FLOOR if region == "E12000007" else None
        grown   = grow_mask(base, n, all_occupied,
                            centroid_hint=centroid, r_floor=r_floor)
        current_masks[region] = grown
        all_occupied.update(grown - base)
        log(f"  Grow {region}: {len(base)} → {len(grown)} (target {n})")

    for region, seats in by_region.items():
        n    = len(seats)
        mask = current_masks.get(region, set())
        if len(mask) < n:
            log(f"  WARNING: {region} has only {len(mask)} cells for {n} seats")

    # -------------------------------------------------------------------------
    # Assignment — Hungarian for London and SE; greedy for all others
    # -------------------------------------------------------------------------
    hexes: dict = {}

    for region, seats in by_region.items():
        mask_list = list(current_masks.get(region, set()))
        n = len(seats)
        if not mask_list:
            log(f"  WARNING: {region} has no cells")
            continue

        pre_fixed = {}
        seats_for_assign = seats

        # SE pre-assignments (1983+ Brighton cluster; SE coastal pre-assign for all years)
        # 1945 predates 1983, so only use SE_COASTAL_PREASSIGN
        if region == "E12000008":
            name_lower = {
                sn.lower().replace("&", "and").replace("-", " "): sn
                for sn, _, _ in seats
            }
            mask_set = set(mask_list)
            for frag, q_t, r_t in SE_COASTAL_PREASSIGN:
                if (q_t, r_t) not in mask_set:
                    continue
                matched = next(
                    (sn for nl, sn in name_lower.items() if frag in nl), None
                )
                if matched is None or matched in pre_fixed:
                    continue
                pre_fixed[matched] = (q_t, r_t)
                mask_set.discard((q_t, r_t))
            seats_for_assign = [(sn, lo, la) for sn, lo, la in seats
                                 if sn not in pre_fixed]
            mask_list = list(mask_set)

        use_hungarian = region in ("E12000007", "E12000008")
        assignment = geographic_assign_region(
            [(name, lon, lat) for name, lon, lat in seats_for_assign],
            mask_list,
            use_hungarian=use_hungarian,
        )
        assignment.update(pre_fixed)

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

    # Summary
    log(f"\nRegion extents in output:")
    by_reg_out: dict = defaultdict(list)
    for d in hexes.values():
        by_reg_out[d.get("region","?")].append((d["q"], d["r"]))
    for reg in sorted(by_reg_out):
        cells = by_reg_out[reg]
        qs = [q for q,r in cells]; rs = [r for q,r in cells]
        log(f"  {reg}: {len(cells)} cells  q={min(qs)}..{max(qs)}  r={min(rs)}..{max(rs)}")

    output = {"layout": "odd-r", "hexes": hexes}
    OUTPUT.mkdir(exist_ok=True)
    out_path = output_path or OUTPUT / "1945_test_v4.hexjson"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    log(f"\nWrote {len(hexes)}/{len(mainland_feats)+len(island_feats)} hexes → {out_path}")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    pack_1945_v4(output_path=args.output)
