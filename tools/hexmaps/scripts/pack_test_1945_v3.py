#!/usr/bin/env python3
"""
pack_test_1945_v3.py — 1945 test: London capped at 75, SE wraps around London's north.

Builds on v1 (pack_test_1945.py) with two key changes:
  1. SE northern wrap: after non-SE regions shrink, BFS-expand SE's mask into
     freed cells at r=-34 to -35 north of London (the gap visible in v1).
     The expanded mask is then shrunk to the target count with coast + northern
     arc cells pinned, so the interior Surrey/Kent tier absorbs the removals.
  2. Joint Hungarian across London (75 seats) + SE (85 seats) simultaneously,
     finding the globally-optimal placement of all 160 seats into the combined
     160-cell mask.

Usage:
    python3 scripts/pack_test_1945_v3.py
    # Output: output/1945_test_v3.hexjson
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

LCC_LON, LCC_LAT  = -0.09, 51.51
LONDON_GROW_R_FLOOR = -43
SHRINK_PREFER_NORTH = {"E12000009"}   # only SW; SE handled specially below


def pack_1945_v3(london_cap: int = 75, output_path: Path | None = None, verbose: bool = True):
    def log(*args):
        if verbose:
            print(*args)

    log(f"=== Packing 1945 v3 — SE northern wrap + joint London/SE Hungarian ===")
    masks_2024, eng_pts = load_2024_reference()

    mainland_feats, island_feats, outside_names = load_year_features(1945)
    log(f"  {len(mainland_feats)} mainland + {len(island_feats)} island"
        f" + {len(outside_names)} outside-boundary")

    # Standard region assignment
    by_region: dict[str, list] = defaultdict(list)
    for name, source, lon, lat in mainland_feats:
        region = assign_region(source, lon, lat, eng_pts)
        by_region[region].append((name, lon, lat))

    # --- Reclassify outer-London seats as SE (same as v1) ---
    london_seats = by_region.get("E12000007", [])
    if len(london_seats) > london_cap:
        london_by_dist = sorted(
            london_seats,
            key=lambda s: (s[1] - LCC_LON) ** 2 + (s[2] - LCC_LAT) ** 2,
        )
        keep       = london_by_dist[:london_cap]
        reclassify = london_by_dist[london_cap:]
        by_region["E12000007"] = keep
        by_region["E12000008"].extend(reclassify)
        log(f"  Reclassified {len(reclassify)} outer-London seats → SE")

    log("Region seat counts:")
    for code, seats in sorted(by_region.items()):
        log(f"  {code}: {len(seats):3d}  (2024 mask: {len(masks_2024.get(code, []))})")

    island_cells  = {(q, r) for _, q, r, _ in island_feats}
    island_buffer = island_cells | {nb for q, r in island_cells for nb in odd_r_neighbors(q, r)}

    # growing_region_cells for adj_benefit scoring
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

    # SE anchor cells: pre-1974 anchor set (SE_PRE74_DROP removed in pack.py)
    # but v3 keeps (59,-35) and (60,-35) since SE is much larger here (85 vs 48).
    # Also pin the Sussex/Kent coast cells that pack.py anchors for 1983+.
    SE_COAST_EXTRA = {
        (70, -43),   # Hastings
        (70, -44),   # Bexhill
        (69, -45),   # Eastbourne
        (68, -45),   # Lewes
    }
    SE_BASE_ANCHORS = REGION_ANCHOR_CELLS["E12000008"] | SE_COAST_EXTRA
    # (do NOT subtract SE_PRE74_DROP — SE is 85 seats here, not 48)

    effective_anchors = {}
    for region, cells in REGION_ANCHOR_CELLS.items():
        if region == "E12000008":
            effective_anchors[region] = SE_BASE_ANCHORS
        else:
            effective_anchors[region] = cells

    # -------------------------------------------------------------------------
    # Pass 1a — shrink all regions EXCEPT SE (so EoE frees northern arc cells)
    # -------------------------------------------------------------------------
    for region, seats in by_region.items():
        if region == "E12000008":
            continue
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

    # -------------------------------------------------------------------------
    # Pass 1b — SE northern wrap then shrink to target
    # -------------------------------------------------------------------------
    se_base_2024 = current_masks["E12000008"]   # 2024 SE mask, untouched so far
    n_se = len(by_region["E12000008"])          # 85 seats

    # All cells occupied by non-SE regions after Pass 1a
    all_occupied_non_se = (
        {c for reg, mask in current_masks.items() if reg != "E12000008" for c in mask}
        | island_buffer | PERMANENT_GAPS
    )

    # Northern wrap: claim ALL freed EoE cells (cells that were EoE in 2024 but
    # freed by the 1945 EoE shrink).  Claiming the entire freed block — not just
    # the r=-34/-35 row — prevents the freed cells at r=-31 to -33 from becoming
    # interior holes when the lower arc rows form a ceiling above them.
    eoe_2024_mask = (
        set(masks_2024.get("E12000006", [])) - island_buffer - PERMANENT_GAPS
    )
    reachable = (eoe_2024_mask - all_occupied_non_se) - se_base_2024
    log(f"  SE northern arc: {len(reachable)} freed-EoE cells → r range "
        f"{min(r for _,r in reachable) if reachable else 'n/a'} to "
        f"{max(r for _,r in reachable) if reachable else 'n/a'}")

    se_expanded = se_base_2024 | reachable
    # Pin: existing SE anchors (coast + junctions + Bucks/Berks tier) + all northern arc cells
    SE_FULL_ANCHORS = SE_BASE_ANCHORS | reachable

    # Shrink SE from expanded pool to n_se.
    # prefer_remove_north=False → remove most-southern unanchored cells first
    # (interior Surrey/Kent at r=-42 to -43), keeping both the coast and the new
    # northern arc.
    current_masks["E12000008"] = shrink_mask(
        se_expanded,
        n_se,
        beneficiary_cells=growing_region_cells,
        prefer_remove_north=False,
        pinned_cells=SE_FULL_ANCHORS,
    )
    log(f"  SE mask after reshape: {len(current_masks['E12000008'])} cells")
    north_cells = sorted(c for c in current_masks["E12000008"] if c[1] >= -35)
    log(f"  SE cells at r>=-35: {north_cells}")

    # -------------------------------------------------------------------------
    # Pass 2 — grow regions that are larger than their masks (NE, NW, etc.)
    # -------------------------------------------------------------------------
    all_occupied = (
        {c for mask in current_masks.values() for c in mask}
        | island_buffer | PERMANENT_GAPS
    )

    for region, seats in sorted(by_region.items()):
        if region in ("E12000007", "E12000008"):
            continue   # London unchanged (mask already at 75); SE already reshaped
        n    = len(seats)
        base = current_masks.get(region, set())
        if n > len(base):
            base_list = list(base)
            centroid_hint = None
            if base_list:
                centroid_hint = (
                    sum(c[0] for c in base_list) / len(base_list),
                    sum(c[1] for c in base_list) / len(base_list),
                )
            r_floor = None
            grown   = grow_mask(base, n, all_occupied,
                                centroid_hint=centroid_hint, r_floor=r_floor)
            current_masks[region] = grown
            all_occupied.update(grown - base)

    # -------------------------------------------------------------------------
    # Assignment — joint Hungarian across London + SE
    # -------------------------------------------------------------------------
    hexes: dict = {}
    warnings = []

    london_mask = set(current_masks.get("E12000007", []))
    se_mask     = set(current_masks.get("E12000008", []))

    combined_seats = (
        [(name, lon, lat) for name, lon, lat in by_region.get("E12000007", [])]
        + [(name, lon, lat) for name, lon, lat in by_region.get("E12000008", [])]
    )
    combined_mask = list(london_mask | se_mask)

    if len(combined_mask) < len(combined_seats):
        warnings.append(
            f"London+SE: only {len(combined_mask)} cells for {len(combined_seats)} seats"
        )

    log(f"  Joint Hungarian: {len(combined_seats)} seats × {len(combined_mask)} cells")
    joint_assignment = geographic_assign_region(
        combined_seats,
        combined_mask,
        use_hungarian=True,
    )
    for name, (q, r) in joint_assignment.items():
        region = "E12000007" if (q, r) in london_mask else "E12000008"
        hexes[name] = {"n": name, "q": q, "r": r, "region": region}

    # All other regions — geographic Hungarian where already used, else greedy
    for region, seats in by_region.items():
        if region in ("E12000007", "E12000008"):
            continue
        mask_set = set(current_masks.get(region, []))
        n = len(seats)
        if len(mask_set) < n:
            warnings.append(f"{region}: only {len(mask_set)} cells for {n} seats")
        assignment = geographic_assign_region(
            [(name, lon, lat) for name, lon, lat in seats],
            list(mask_set),
            use_hungarian=False,
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

    hexes = fill_holes(hexes, {}, island_buffer=island_buffer)

    for w in warnings:
        log(f"  WARNING: {w}")

    output = {"layout": "odd-r", "hexes": hexes}
    OUTPUT.mkdir(exist_ok=True)
    out_path = output_path or OUTPUT / "1945_test_v3.hexjson"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    log(f"\nWrote {len(hexes)}/{len(mainland_feats)+len(island_feats)} hexes → {out_path}")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--london-cap", type=int, default=75)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    pack_1945_v3(london_cap=args.london_cap, output_path=args.output)
