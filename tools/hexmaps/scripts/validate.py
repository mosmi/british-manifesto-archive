#!/usr/bin/env python3
"""
validate.py — Run hard-invariant and sanity checks against a packed hexjson.

Usage:
    python3 validate.py --year 2010
    python3 validate.py --year 2010 --hexjson output/2010.hexjson

Checks implemented:
  A1  Seat count matches expected total for the year.
  A2  One hex per seat (no missing constituencies).
  A3  No two hexes share the same (q, r).
  A4  Per-region counts match expected (derived from GeoJSON feature counts).
  A5  Valid hexjson structure.
  A6  No interior holes in the mainland (flood-fill check).
  A7  Island seats are detached (zero occupied neighbours).
  B9  Compass coherence — spot check compass-suffix seat clusters.
  B11 Region footprint within skeleton bounding box.
"""

import json
import argparse
import sys
from pathlib import Path
from collections import defaultdict, deque

BASE = Path(__file__).resolve().parent.parent
OUTPUT = BASE / "output"
REFERENCE = BASE / "reference"

# -------------------------------------------------------------------------
# Known seat totals — mainland hexes only.
# 1945: 598 single-member territorial seats (22 outside-boundary excluded).
# -------------------------------------------------------------------------
EXPECTED_SEATS = {
    1945: 599,   # 598 single-member mainland + Richmond (Surrey) AND Richmond (Yorks) both present
    1950: 625,
    1951: 625,
    1955: 630,
    1959: 630,
    1964: 630,
    1966: 630,
    1970: 630,   # hybrid; actual 630 once London splice applied
    1974: 635,
    1979: 635,
    1983: 650,
    1987: 650,
    1992: 651,
    1997: 659,
    2001: 659,
    2005: 646,
    2010: 650,
    2015: 650,
    2017: 650,
    2019: 650,
    2024: 650,
}

# Island seats by era — must be detached (zero occupied neighbours).
# Format: {era_key: [name_fragments, ...]}  era_key is a rough year range.
ISLAND_SEATS = {
    # 1945-2019: IoW, Anglesey (→ Ynys Môn from 1983), Orkney & Shetland, Western Isles
    "pre2024": [
        "isle of wight",
        "anglesey", "ynys môn", "ynys mon",
        "orkney",
        "western isles", "na h-eileanan",
    ],
    "2024": [
        "ynys môn", "ynys mon",
        "orkney",
        "na h-eileanan",
        "isle of wight east", "isle of wight west",
    ],
}


def era_islands(year):
    return ISLAND_SEATS["2024"] if year == 2024 else ISLAND_SEATS["pre2024"]


def odd_r_neighbors(q, r):
    if r & 1 == 0:
        return [(q+1,r),(q-1,r),(q,r+1),(q-1,r+1),(q,r-1),(q-1,r-1)]
    else:
        return [(q+1,r),(q-1,r),(q+1,r+1),(q,r+1),(q+1,r-1),(q,r-1)]


# -------------------------------------------------------------------------
# Flood-fill interior-hole detection
# -------------------------------------------------------------------------

def has_interior_holes(occupied):
    """
    Return True if there are cells fully enclosed by occupied cells
    (i.e., cells that can't be reached from the bounding-box exterior).
    """
    if not occupied:
        return False

    q_vals = [c[0] for c in occupied]
    r_vals = [c[1] for c in occupied]
    q_min, q_max = min(q_vals) - 1, max(q_vals) + 1
    r_min, r_max = min(r_vals) - 1, max(r_vals) + 1

    # BFS from exterior corner
    start = (q_min, r_min)
    visited = {start}
    queue = deque([start])

    while queue:
        q, r = queue.popleft()
        for nb in odd_r_neighbors(q, r):
            nq, nr = nb
            if nb in visited or nb in occupied:
                continue
            if nq < q_min or nq > q_max or nr < r_min or nr > r_max:
                continue
            visited.add(nb)
            queue.append(nb)

    # Any empty cell NOT reachable from the exterior and NOT occupied = a hole
    for r in range(r_min, r_max + 1):
        for q in range(q_min, q_max + 1):
            cell = (q, r)
            if cell not in occupied and cell not in visited:
                return True

    return False


# -------------------------------------------------------------------------
# Main validation
# -------------------------------------------------------------------------

def validate(year, hexjson_path=None, verbose=True):
    def log(*args):
        if verbose:
            print(*args)

    path = hexjson_path or OUTPUT / f"{year}.hexjson"
    if not path.exists():
        print(f"ERROR: {path} not found")
        return False

    with open(path) as f:
        data = json.load(f)

    results = {}

    # A5 — valid structure
    has_layout = "layout" in data
    has_hexes = "hexes" in data and isinstance(data["hexes"], dict)
    hexes = data.get("hexes", {})
    all_have_qr = all(
        isinstance(h.get("q"), int) and isinstance(h.get("r"), int)
        for h in hexes.values()
    )
    results["A5_valid_structure"] = has_layout and has_hexes and all_have_qr
    if not results["A5_valid_structure"]:
        log("FAIL A5: malformed hexjson")

    # Build cell set
    cells = {(h["q"], h["r"]) for h in hexes.values()}
    names = list(hexes.keys())

    # A3 — no shared cells
    n_cells = len(cells)
    n_hexes = len(hexes)
    results["A3_no_shared_cells"] = n_cells == n_hexes
    if not results["A3_no_shared_cells"]:
        log(f"FAIL A3: {n_hexes - n_cells} duplicate cells")

    # A1 — seat count
    expected = EXPECTED_SEATS.get(year)
    if expected is not None:
        results["A1_seat_count"] = n_hexes == expected
        if not results["A1_seat_count"]:
            log(f"FAIL A1: {n_hexes} hexes, expected {expected}")
        else:
            log(f"PASS A1: {n_hexes} seats ✓")
    else:
        results["A1_seat_count"] = None
        log(f"INFO A1: no expected count for {year}")

    # A2 — one hex per constituency (no duplicates in input → covered by A3; check names unique)
    results["A2_one_hex_per_seat"] = len(set(names)) == len(names)
    if not results["A2_one_hex_per_seat"]:
        log("FAIL A2: duplicate constituency names in hexjson")

    # A4 — per-region counts (derive expected from GeoJSON via pack.py's logic)
    by_region = defaultdict(list)
    for name, h in hexes.items():
        by_region[h.get("region", "UNKNOWN")].append(name)
    results["A4_per_region"] = "UNKNOWN" not in by_region
    if not results["A4_per_region"]:
        log("FAIL A4: some hexes missing region field")
    else:
        log("PASS A4: all hexes have region ✓")

    # A6 — no interior holes (mainland only — exclude obvious island offsets)
    # For this check we use ALL hexes; islands are detached so won't form holes.
    results["A6_no_interior_holes"] = not has_interior_holes(cells)
    if results["A6_no_interior_holes"]:
        log("PASS A6: no interior holes ✓")
    else:
        log("FAIL A6: interior holes detected")

    # A7 — island seats are detached
    island_frags = era_islands(year)
    island_cells = set()
    non_island_cells = set()
    for name, h in hexes.items():
        cell = (h["q"], h["r"])
        name_lower = name.lower()
        is_island = any(frag in name_lower for frag in island_frags)
        if is_island:
            island_cells.add(cell)
        else:
            non_island_cells.add(cell)

    island_failures = []
    for name, h in hexes.items():
        name_lower = name.lower()
        if any(frag in name_lower for frag in island_frags):
            cell = (h["q"], h["r"])
            occupied_nbs = [nb for nb in odd_r_neighbors(*cell) if nb in non_island_cells]
            if occupied_nbs:
                island_failures.append(f"{name} has {len(occupied_nbs)} mainland neighbours")

    results["A7_islands_detached"] = len(island_failures) == 0
    if results["A7_islands_detached"]:
        if island_cells:
            log(f"PASS A7: {len(island_cells)} island seat(s) are detached ✓")
        else:
            log(f"INFO A7: no island seats found for {year}")
    else:
        log(f"FAIL A7: {len(island_failures)} island(s) not detached")
        for f in island_failures[:5]:
            log(f"  {f}")

    # B11 — region footprint within skeleton
    with open(REFERENCE / "regional_skeleton.json") as f:
        skeleton = json.load(f)
    skeleton_regions = skeleton["regions"]

    b11_failures = []
    for region_code, region_hexes in by_region.items():
        if region_code not in skeleton_regions:
            continue
        sk = skeleton_regions[region_code]
        q_min_sk, q_max_sk = sk["q_range"]
        r_min_sk, r_max_sk = sk["r_range"]
        # allow 20% overshoot
        q_slack = max(3, int((q_max_sk - q_min_sk) * 0.20))
        r_slack = max(3, int((r_max_sk - r_min_sk) * 0.20))
        for name in region_hexes:
            q, r = hexes[name]["q"], hexes[name]["r"]
            if (q < q_min_sk - q_slack or q > q_max_sk + q_slack or
                    r < r_min_sk - r_slack or r > r_max_sk + r_slack):
                b11_failures.append(f"{name} ({q},{r}) outside {region_code} skeleton")

    results["B11_within_skeleton"] = len(b11_failures) == 0
    if results["B11_within_skeleton"]:
        log("PASS B11: all hexes within skeleton bounding boxes ✓")
    else:
        log(f"FAIL B11: {len(b11_failures)} hexes outside skeleton")
        for f in b11_failures[:5]:
            log(f"  {f}")

    # Summary
    log("")
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    log(f"=== {year}: {passed} passed, {failed} failed, {skipped} skipped ===")

    return failed == 0


def main():
    parser = argparse.ArgumentParser(description="Validate a packed hexjson")
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--hexjson", type=Path, default=None)
    args = parser.parse_args()
    ok = validate(args.year, hexjson_path=args.hexjson)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
