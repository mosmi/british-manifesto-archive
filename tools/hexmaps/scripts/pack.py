#!/usr/bin/env python3
"""
pack.py — Build a hexjson for a UK general election year.

Usage:
    python3 pack.py --year 2010
    python3 pack.py --year 1983 --output output/1983.hexjson

Algorithm (rank-and-fill, two-pass):
1. Load + deduplicate the year's GeoJSON; exclude island and outside-boundary seats.
2. Assign each constituency to an ONS region.
3. Shrink over-allocated 2024 masks first (preferring to free cells toward growing neighbours).
4. Grow under-allocated masks via BFS into unoccupied cells only.
5. Sort mask cells + constituencies north→south, assign 1:1.
6. Append island seats at fixed detached positions.
7. Emit hexjson.
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).resolve().parent.parent
SOURCES = BASE / "sources" / "geojson"
REFERENCE = BASE / "reference"
OUTPUT = BASE / "output"

YEAR_TO_GEOJSON = {
    1945: "1945-combined.geojson",
    1950: "1950-combined.geojson",
    1951: "1950-combined.geojson",
    1955: "1955-combined.geojson",
    1959: "1955-combined.geojson",
    1964: "1955-combined.geojson",
    1966: "1955-combined.geojson",
    1970: "1955-combined.geojson",   # same boundaries as 1955–1966; GLC (1965) changed admin areas but not parliamentary constituencies
    1974: "1974-combined.geojson",
    1979: "1974-combined.geojson",
    1983: "1983-combined.geojson",
    1987: "1983-combined.geojson",
    1992: "1983-combined.geojson",   # hybrid — MK split not yet applied
    1997: "1997-combined.geojson",
    2001: "1997-combined.geojson",
    2005: "2005-combined.geojson",
    2010: "2010-combined.geojson",
    2015: "2010-combined.geojson",
    2017: "2010-combined.geojson",
    2019: "2010-combined.geojson",
    2024: "2024-combined.geojson",
}

SOURCE_TO_REGION = {
    "scotland":         "S92000003",
    "wales":            "W92000004",
    "northern-ireland": "N92000002",
}

# ---------------------------------------------------------------------------
# Island constituency definitions
# Each entry: (name_fragment_lowercase, fixed_q, fixed_r, region_code)
# The name_fragment is matched case-insensitively against each constituency name.
# Positions chosen to be detached (no neighbours) in the hex grid.
# ---------------------------------------------------------------------------
# Cells that must remain permanently empty — never assigned and never filled.
# (43, -17) is Lough Neagh, the large lake in the centre of Northern Ireland.
# (53, -45) is the 2024 IoW West position; in pre-2024 elections there is only
# one IoW seat placed at (54, -45), so (53, -45) is left permanently empty.
PERMANENT_GAPS = {
    (43, -17),
    (53, -45),
}

# Cells that must be the LAST removed when a region's mask shrinks.
# These anchor the characteristic geographic shape of the region.
# Key: region code.  Value: set of (q, r) cells to pin.
REGION_ANCHOR_CELLS = {
    # South West: Cornwall peninsula (SW→NE chain) + Gloucester/Hereford northern tip.
    # Pinning the southern cells keeps the Cornwall chain; pinning the northern cells
    # prevents Hereford/Tewkesbury from being displaced to Devon rows.
    "E12000009": {
        (43, -46), (43, -45), (44, -45), (45, -44), (46, -44), (45, -43),  # Cornwall
        (51, -35), (52, -35), (52, -36), (53, -36), (53, -37),              # Gloucester/Hereford north
    },
    # South East: pin cells for key latitudinal tiers that otherwise get removed
    # by shrink_mask's adj_benefit scoring (cells adjacent to growing London are
    # preferentially freed, even those London can't actually absorb due to r_floor=-43).
    #  r=-35 tier: Bucks/Aylesbury (Buckingham, Chesham, Aylesbury, Banbury)
    #  r=-38 tier: Berkshire (Windsor, Reading, Wokingham, Newbury)
    #  r=-44 tier: the growing_region_cells fix (excluding London r=-43 from benefit
    #    scoring) removes adj_benefit for SE r=-44 cells. We additionally pin q=63-66
    #    as a safety net for elections where SE is unusually small.
    "E12000008": {
        (59, -35), (60, -35), (56, -38), (57, -38),  # Bucks/Berkshire north tier
        (58, -42),                                     # junction: SE west corridor / London SE corner
        (68, -42),                                     # junction: SE east corridor / London SE corner
                                                       # absent → interior holes that fill_holes patches
                                                       # by displacing seats, including via (67,-44)
        (59, -43),                                     # coast slot west of London
        (67, -44),                                     # East Sussex junction; without (68,-42) anchor,
                                                       # fill_holes uses this as chain-move peripheral
                                                       # target, leaving a gap in the coast row
        (63, -44), (64, -44), (65, -44), (66, -44),  # Brighton–Hove safety anchors
    },
}

# SE coast seats pre-assigned to fixed positions for years >= 1983.
# Processed as post-assignment swaps after geographic_assign_region.
#
# Brighton cluster (BRIGHTON_PREASSIGN_1983) applies only for 1983-1992:
#   The 1983-boundary elections have London at 84 seats, fully occupying r=-43
#   at q=60-66.  That prevents (62,-43) from becoming an interior hole, so the
#   r=-44 pre-assignments are stable.  For 1997+ London has only 73-74 seats;
#   it releases (62,-43) from its mask and the cell becomes an unclaimed interior
#   hole that fill_holes patches by pulling coast seats off r=-44.
BRIGHTON_PREASSIGN_1983 = [
    ("hove",              62, -44),
    ("brighton pavilion", 63, -44),
    ("brighton kemptown", 64, -44),
    ("sussex mid",        65, -44),
]

# East Sussex coast pre-assignments apply for all years >= 1983.
SE_COASTAL_PREASSIGN = [
    # East Sussex coast (south-east of London)
    ("eastbourne", 69, -45),
    ("lewes",      68, -45),
    ("bexhill",    70, -44),
    ("hastings",   70, -43),
]

ISLAND_DEFS = [
    # Orkney & Shetland — same position for all years
    ("orkney",        51,  0,   "S92000003"),
    # Western Isles / Na h-Eileanan an Iar — same position for all years
    ("na h-eileanan", 47, -2,   "S92000003"),
    ("western isles", 47, -2,   "S92000003"),
    # Anglesey (pre-1983) / Ynys Môn (from 1983) — same position
    ("anglesey",      46, -29,  "W92000004"),
    ("ynys m",        46, -29,  "W92000004"),
    # Isle of Wight — single seat (pre-2024). 2024 uses two seats at (54,-45)/(53,-45).
    # Place the pre-2024 single seat at the IoW East 2024 position so it lines up
    # with the 2024 map rather than sitting far south.  (53,-45) is a PERMANENT_GAP.
    ("isle of wight", 54, -45,  "E12000008"),
]

# 1945 outside-boundary seats — territorial multi-member + university.
# These are excluded from the mainland hexmap and stored separately.
OUTSIDE_BOUNDARY_1945 = {
    "antrim", "blackburn", "bolton", "brighton", "city of london", "city of london (2)",
    "derby", "down", "dundee", "fermanagh and tyrone",
    "fermanagh & tyrone",   # alternate spelling in GeoJSON
    "norwich", "oldham", "preston", "southampton", "stockport", "sunderland",
    # University seats (no GeoJSON geometry)
    "cambridge university", "combined english universities",
    "combined scottish universities", "london university",
    "oxford university", "queen's university of belfast",
    "queen’s university of belfast",   # typographic apostrophe variant
    "university of wales",
}


# ---------------------------------------------------------------------------
# Hex geometry — odd-r offset, pointy-top
# ---------------------------------------------------------------------------

def odd_r_neighbors(q, r):
    if r & 1 == 0:
        return [(q+1,r),(q-1,r),(q,r+1),(q-1,r+1),(q,r-1),(q-1,r-1)]
    else:
        return [(q+1,r),(q-1,r),(q+1,r+1),(q,r+1),(q+1,r-1),(q,r-1)]


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def compute_centroid(geometry):
    gtype = geometry["type"]
    if gtype == "Polygon":
        ring = geometry["coordinates"][0]
    elif gtype == "MultiPolygon":
        ring = max(geometry["coordinates"], key=lambda p: len(p[0]))[0]
    else:
        return 0.0, 0.0
    if not ring:
        return 0.0, 0.0
    n = len(ring)
    return sum(c[0] for c in ring) / n, sum(c[1] for c in ring) / n


# ---------------------------------------------------------------------------
# Island / outside-boundary classification
# ---------------------------------------------------------------------------

def classify_feature(name, year):
    """
    Returns:
      ('mainland', None)  — include in main pack
      ('island', (q, r, region))  — detach at fixed position
      ('outside', None)   — exclude from hexmap (1945 multi-member / university)
    """
    name_lower = name.lower()

    # 1945 outside-boundary filter
    if year == 1945 and name_lower in OUTSIDE_BOUNDARY_1945:
        return ("outside", None)

    # Island matching
    for frag, q, r, region in ISLAND_DEFS:
        if frag in name_lower:
            # In 2024, the two IoW seats are mainland-adjacent — don't detach them
            if frag == "isle of wight" and year == 2024:
                return ("mainland", None)
            return ("island", (q, r, region))

    return ("mainland", None)


# ---------------------------------------------------------------------------
# 2024 reference data
# ---------------------------------------------------------------------------

def load_2024_reference():
    """
    Returns:
        masks   — {region_code: set of (q, r)}
        eng_pts — [(lon, lat, region_code), ...]  English-region classifier training data
    """
    with open(REFERENCE / "uk-constituencies-2024.hexjson") as f:
        hexjson = json.load(f)
    with open(SOURCES / "2024-combined.geojson") as f:
        geojson = json.load(f)

    name_to_region = {h["n"].lower(): h["region"] for h in hexjson["hexes"].values()}

    masks = defaultdict(set)
    for h in hexjson["hexes"].values():
        masks[h["region"]].add((h["q"], h["r"]))

    eng_pts = []
    for feat in geojson["features"]:
        name = feat["properties"]["Name"].lower()
        region = name_to_region.get(name)
        if region and region.startswith("E12"):
            lon, lat = compute_centroid(feat["geometry"])
            eng_pts.append((lon, lat, region))

    return dict(masks), eng_pts


def nearest_english_region(lon, lat, eng_pts):
    return min(eng_pts, key=lambda t: (t[0] - lon) ** 2 + (t[1] - lat) ** 2)[2]


def assign_region(source, lon, lat, eng_pts):
    nation = source.split("/")[0]
    if nation in SOURCE_TO_REGION:
        return SOURCE_TO_REGION[nation]
    return nearest_english_region(lon, lat, eng_pts)


# ---------------------------------------------------------------------------
# GeoJSON loading + classification
# ---------------------------------------------------------------------------

def load_year_features(year):
    """
    Returns:
        mainland  — [(name, source, lon, lat), ...]
        islands   — [(name, q, r, region), ...]  with fixed detached positions
        outside   — [name, ...]  excluded from hexmap (1945 only)
    Deduplicates by name (largest outer ring wins).
    """
    fname = YEAR_TO_GEOJSON.get(year)
    if not fname:
        raise ValueError(f"No GeoJSON mapping for year {year}")

    with open(SOURCES / fname) as f:
        data = json.load(f)

    # First pass: collect all features, generating unique names where needed.
    raw = []
    unnamed_idx = 0
    for feat in data["features"]:
        name = feat["properties"].get("Name")
        source = feat["properties"]["_source"]
        lon, lat = compute_centroid(feat["geometry"])
        g = feat["geometry"]
        ring_len = (
            len(g["coordinates"][0]) if g["type"] == "Polygon"
            else max(len(p[0]) for p in g["coordinates"])
        )
        if not name:
            unnamed_idx += 1
            name = f"_Unnamed_{source}_{unnamed_idx}"
        raw.append((name, source, lon, lat, ring_len))

    # Second pass: deduplicate by name.
    # Two features with the same name but centroids >1° apart are different
    # constituencies sharing a name (e.g. Richmond Surrey vs Richmond Yorkshire)
    # — give them distinguishing suffixes.
    by_name = {}
    for name, source, lon, lat, ring_len in raw:
        if name not in by_name:
            by_name[name] = []
        by_name[name].append((source, lon, lat, ring_len))

    resolved = {}
    for name, entries in by_name.items():
        if len(entries) == 1:
            resolved[name] = entries[0][:3]  # (source, lon, lat)
        else:
            # Check if they're genuinely different constituencies
            # (centroids > 0.5° apart → different places, same name)
            lons = [e[1] for e in entries]
            lats = [e[2] for e in entries]
            spread = max(lons) - min(lons) + max(lats) - min(lats)
            if spread > 2.0:
                # Different constituencies — keep all with letter suffix
                for i, entry in enumerate(entries):
                    suffix = chr(ord("A") + i)
                    resolved[f"{name} ({suffix})"] = entry[:3]
            else:
                # Same constituency duplicated — keep largest ring
                best_e = max(entries, key=lambda e: e[3])
                resolved[name] = best_e[:3]

    # 1992: Milton Keynes was split mid-Parliament into NE and SW seats.
    # The 1983 GeoJSON has only the single pre-split seat; replace it here.
    if year == 1992 and "Milton Keynes" in resolved:
        src, lon_mk, lat_mk = resolved.pop("Milton Keynes")
        resolved["Milton Keynes NE"] = (src, lon_mk, lat_mk + 0.06)
        resolved["Milton Keynes SW"] = (src, lon_mk, lat_mk - 0.06)

    mainland, islands, outside = [], [], []
    seen_island_cells = set()   # prevent duplicate island positions

    for name, (source, lon, lat) in resolved.items():
        kind, info = classify_feature(name, year)
        if kind == "outside":
            outside.append(name)
        elif kind == "island":
            q, r, region = info
            if (q, r) in seen_island_cells:
                # Two constituencies map to same island cell (shouldn't happen)
                mainland.append((name, source, lon, lat))
            else:
                seen_island_cells.add((q, r))
                islands.append((name, q, r, region))
        else:
            mainland.append((name, source, lon, lat))

    return mainland, islands, outside


# ---------------------------------------------------------------------------
# Mask shrink / grow
# ---------------------------------------------------------------------------

def shrink_mask(cells_set, target, beneficiary_cells=None, prefer_remove_north=False,
                pinned_cells=None):
    """
    Remove peripheral cells until len == target.
    Prefer releasing cells adjacent to beneficiary_cells (growing neighbour regions).
    prefer_remove_north=True: remove cells with high r (northerly/less-negative) first,
    preserving the southern tip of the region (e.g. Cornwall for South West).
    Default (False): remove cells with low r (southerly) first.
    pinned_cells: cells that are never removed unless no unpinned cells remain.
    """
    cells_set = set(cells_set)
    benefit = set(beneficiary_cells) if beneficiary_cells else set()
    pinned = set(pinned_cells) if pinned_cells else set()

    while len(cells_set) > target:
        def score(c):
            adj_benefit = sum(1 for nb in odd_r_neighbors(*c) if nb in benefit)
            in_neighbors = sum(1 for nb in odd_r_neighbors(*c) if nb in cells_set)
            r_key = -c[1] if prefer_remove_north else c[1]
            return (-adj_benefit, in_neighbors, r_key)

        candidates = cells_set - pinned if (cells_set - pinned) else cells_set
        worst = min(candidates, key=score)
        cells_set.remove(worst)
    return cells_set


def grow_mask(cells_set, target, all_occupied, centroid_hint=None, r_floor=None):
    """Add cells adjacent to region, into unoccupied space, until len == target.
    Prefers cells closest to centroid_hint (q_c, r_c) if provided, else northernmost.
    r_floor: if set, no cell with r < r_floor is ever added (e.g. r_floor=-43 for London).
    """
    cells_set = set(cells_set)
    all_occupied = set(all_occupied)
    q_c, r_c = centroid_hint if centroid_hint else (None, None)

    while len(cells_set) < target:
        candidates = {
            nb
            for q, r in cells_set
            for nb in odd_r_neighbors(q, r)
            if nb not in all_occupied
            and (r_floor is None or nb[1] >= r_floor)
        }
        if not candidates:
            break
        if q_c is not None:
            best = min(candidates, key=lambda c: (c[0] - q_c) ** 2 + (c[1] - r_c) ** 2)
        else:
            best = max(candidates, key=lambda c: (c[1], -c[0]))
        cells_set.add(best)
        all_occupied.add(best)

    return cells_set


# ---------------------------------------------------------------------------
# Sort keys
# ---------------------------------------------------------------------------

def cell_geo_key(q, r):
    """North-first (r desc = less negative first), west-first (q asc)."""
    return (-r, q)


def seat_geo_key(lat, lon):
    return (-lat, lon)


# ---------------------------------------------------------------------------
# Post-processing: fill interior holes via chain-move BFS
# ---------------------------------------------------------------------------

def fill_holes(hexes, by_region_mask, island_buffer=None):
    """
    Detect interior holes and eliminate them using chain moves.

    For each hole, BFS through occupied cells to find the nearest 'safe-peripheral'
    cell — one adjacent to the exterior.  Then chain-shift all cells along the BFS
    path one step toward the hole, so the hole migrates to the safe-peripheral
    position (which is an edge cell, not a new interior hole).

    Multiple passes until convergence.  Returns updated hexes dict.
    island_buffer: set of cells that must stay empty (island positions + neighbours).
    """
    _island_buf = set(island_buffer) if island_buffer else set()
    from collections import deque

    hexes = {k: dict(v) for k, v in hexes.items()}
    cells    = {(h["q"], h["r"]): name for name, h in hexes.items()}
    occupied = set(cells.keys())

    if not occupied:
        return hexes

    for _pass in range(60):
        q_vals = [c[0] for c in occupied]
        r_vals = [c[1] for c in occupied]
        qmin, qmax = min(q_vals) - 1, max(q_vals) + 1
        rmin, rmax = min(r_vals) - 1, max(r_vals) + 1

        # Exterior flood-fill
        exterior: set = {(qmin, rmin)}
        ext_q: deque = deque([(qmin, rmin)])
        while ext_q:
            q, r = ext_q.popleft()
            for nb in odd_r_neighbors(q, r):
                nq, nr = nb
                if nb in exterior or nb in occupied:
                    continue
                if nq < qmin or nq > qmax or nr < rmin or nr > rmax:
                    continue
                exterior.add(nb)
                ext_q.append(nb)

        holes = [
            (q, r)
            for r in range(rmin, rmax + 1)
            for q in range(qmin, qmax + 1)
            if (q, r) not in occupied and (q, r) not in exterior
        ]
        if not holes:
            break

        fixed_any = False
        for hole in holes:
            if hole in occupied:          # filled in an earlier step of this pass
                continue
            if hole in PERMANENT_GAPS:    # Lough Neagh and similar — never fill
                continue

            # BFS from hole through occupied cells to nearest safe-peripheral cell
            # (one with at least one exterior neighbour).
            bfs_parent: dict = {}
            bfs_q: deque = deque()
            for nb in odd_r_neighbors(*hole):
                if nb in occupied:
                    bfs_parent[nb] = hole
                    bfs_q.append(nb)

            target = None
            while bfs_q and target is None:
                cur = bfs_q.popleft()
                if any(nb in exterior for nb in odd_r_neighbors(*cur)):
                    target = cur
                    break
                for nb in odd_r_neighbors(*cur):
                    if nb in occupied and nb not in bfs_parent:
                        bfs_parent[nb] = cur
                        bfs_q.append(nb)

            if target is None:
                continue

            # Rebuild path from hole to target
            path = []
            cur = target
            while cur != hole:
                path.append(cur)
                cur = bfs_parent[cur]
            path.reverse()          # [cell_adjacent_to_hole, …, target]

            # Chain-shift: move each cell one step toward hole
            prev_pos = hole
            for cell in path:
                nm = cells[cell]
                hexes[nm]["q"] = prev_pos[0]
                hexes[nm]["r"] = prev_pos[1]
                cells[prev_pos] = nm
                cells.pop(cell)
                occupied.add(prev_pos)
                occupied.discard(cell)
                prev_pos = cell   # hole migrates to the cell's old position

            # prev_pos is now target's old position — exterior-adjacent → not a new hole
            fixed_any = True

        if not fixed_any:
            break

    # ---- Connectivity repair ------------------------------------------------
    # fill_holes can chain-move a seat out of a cell that was the sole bridge
    # to an isolated seat, leaving that seat with zero occupied neighbours.
    # Fix: for each non-island isolated seat, find the nearest empty cell that
    # (a) has at least one real cluster neighbour, and (b) is not in the island
    # buffer (would put a mainland seat adjacent to a detached island).
    island_cells_in_hexes = {
        (h["q"], h["r"]) for h in hexes.values() if h.get("island")
    }
    for _ in range(20):
        isolated = [
            (q, r) for (q, r) in list(occupied)
            if not any(nb in occupied for nb in odd_r_neighbors(q, r))
        ]
        if not isolated:
            break
        for iso_pos in isolated:
            if iso_pos not in cells:
                continue  # already moved in this pass
            nm = cells[iso_pos]
            if hexes[nm].get("island"):
                continue  # never move island seats — they are meant to be detached
            # BFS from iso_pos to find nearest valid reconnection cell
            bfs_parent2: dict = {iso_pos: None}
            bfs_q2: deque = deque([iso_pos])
            target2 = None
            while bfs_q2:
                cur = bfs_q2.popleft()
                for nb in odd_r_neighbors(*cur):
                    if nb in bfs_parent2:
                        continue
                    bfs_parent2[nb] = cur
                    if nb not in occupied:
                        if nb in _island_buf:
                            continue  # would land next to an island — skip
                        real_nbs = [n2 for n2 in odd_r_neighbors(*nb)
                                    if n2 in occupied and n2 != iso_pos
                                    and n2 not in island_cells_in_hexes]
                        if real_nbs:
                            target2 = nb
                            break
                    else:
                        bfs_q2.append(nb)
                if target2:
                    break
            if target2 is None:
                continue
            hexes[nm]["q"], hexes[nm]["r"] = target2
            cells[target2] = nm
            cells.pop(iso_pos)
            occupied.add(target2)
            occupied.discard(iso_pos)

    return hexes


# ---------------------------------------------------------------------------
# Linear assignment (Jonker-Volgenant, pure Python)
# ---------------------------------------------------------------------------

def _lap_solve(cost_rows):
    """
    Solve an n×n (or n×m, n≤m) linear assignment problem minimising total cost.

    cost_rows: list of n lists, each of length m >= n.
    Returns:   list of length n — col_for_row[i] = column assigned to row i.

    Uses the Jonker-Volgenant shortest-augmenting-path algorithm (O(n³)).
    """
    INF = float('inf')
    n_rows = len(cost_rows)
    n_cols = len(cost_rows[0])

    # Pad to square with zero-cost dummy rows so the standard n×n JV applies.
    if n_rows < n_cols:
        dummy = [0.0] * n_cols
        cost = list(cost_rows) + [dummy] * (n_cols - n_rows)
    else:
        cost = cost_rows

    n = n_cols  # square dimension

    # Dual variables and matching (1-indexed internally).
    u   = [0.0] * (n + 1)   # row potentials
    v   = [0.0] * (n + 1)   # col potentials
    p   = [0]   * (n + 1)   # p[j] = row matched to col j; 0 = unmatched
    way = [0]   * (n + 1)   # predecessor in augmenting path

    for i in range(1, n + 1):
        p[0] = i
        j0   = 0
        mins = [INF]   * (n + 1)
        used = [False] * (n + 1)

        while True:
            used[j0] = True
            i0    = p[j0]
            delta = INF
            j1    = -1
            for j in range(1, n + 1):
                if not used[j]:
                    val = cost[i0 - 1][j - 1] - u[i0] - v[j]
                    if val < mins[j]:
                        mins[j] = val
                        way[j]  = j0
                    if mins[j] < delta:
                        delta = mins[j]
                        j1    = j

            for j in range(n + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j]    -= delta
                else:
                    mins[j] -= delta

            j0 = j1
            if p[j0] == 0:
                break

        while j0:
            p[j0] = p[way[j0]]
            j0    = way[j0]

    col_for_row = [0] * n
    for j in range(1, n + 1):
        if p[j]:
            col_for_row[p[j] - 1] = j - 1

    return col_for_row[:n_rows]


# ---------------------------------------------------------------------------
# Geographic 2D assignment (replaces rank-fill)
# ---------------------------------------------------------------------------

def geographic_assign_region(seats, mask_cells, use_hungarian=False):
    """
    Assign seats to mask cells using per-region linear projection.

    seats:         [(name, lon, lat), ...]
    mask_cells:    iterable of (q, r)
    use_hungarian: if True, solve globally via linear assignment (JV);
                   if False, use greedy Dijkstra (default, fast).
    Returns:       {name: (q, r)}

    Both modes use the same cost metric: (Δq)² + 4·(Δr)² from each seat's
    linearly-projected ideal position.  The 4× r-weighting keeps seats in
    the correct latitudinal band.
    """
    import heapq

    n = len(seats)
    mask = list(mask_cells)
    if not n or not mask:
        return {}

    lons = [lon for _, lon, _ in seats]
    lats = [lat for _, _, lat in seats]
    lon_min, lon_max = min(lons), max(lons)
    lat_min, lat_max = min(lats), max(lats)

    mask_qs = [q for q, r in mask]
    mask_rs = [r for q, r in mask]
    q_min_m, q_max_m = min(mask_qs), max(mask_qs)
    r_min_m, r_max_m = min(mask_rs), max(mask_rs)

    def project(lon, lat):
        q_f = (q_min_m + (lon - lon_min) / (lon_max - lon_min) * (q_max_m - q_min_m)
               if lon_max > lon_min else (q_min_m + q_max_m) / 2.0)
        r_f = (r_min_m + (lat - lat_min) / (lat_max - lat_min) * (r_max_m - r_min_m)
               if lat_max > lat_min else (r_min_m + r_max_m) / 2.0)
        return q_f, r_f

    projections = [(name, lon, lat, *project(lon, lat)) for name, lon, lat in seats]

    if use_hungarian:
        # Global optimum: build n×m cost matrix and solve LAP.
        cost_rows = [
            [(mask[j][0] - q_f) ** 2 + 4 * (mask[j][1] - r_f) ** 2
             for j in range(len(mask))]
            for _, _, _, q_f, r_f in projections
        ]
        col_for_row = _lap_solve(cost_rows)
        return {projections[i][0]: mask[col_for_row[i]] for i in range(n)}

    # Greedy Dijkstra (default) -----------------------------------------------
    # Process "most extreme from centre" first: seats projecting to either the
    # northern OR southern edge of the mask get assigned before the middle tier.
    # This ensures coastal seats claim coastal cells AND inland-outlier seats
    # (e.g. Buckingham projecting north of SE's centroid) claim northern cells,
    # before the large middle tier can block either end.
    r_center = (r_min_m + r_max_m) / 2.0
    order = sorted(range(n), key=lambda i: -abs(projections[i][4] - r_center))

    free = set(map(tuple, mask))
    assignment = {}

    for i in order:
        name, lon, lat, q_f, r_f = projections[i]

        # Dijkstra search: expand cells in order of squared Euclidean distance
        # from the continuously-projected ideal point (q_f, r_f).
        # This ensures the assigned cell is geographically nearest, not just
        # nearest by grid hop, preventing inland seats jumping to coastal cells.
        settled = set()
        heap = [(0.0, round(q_f), round(r_f))]
        assigned = False
        while heap:
            _, q, r = heapq.heappop(heap)
            if (q, r) in settled:
                continue
            settled.add((q, r))
            if len(settled) > 800:
                break
            if (q, r) in free:
                assignment[name] = (q, r)
                free.discard((q, r))
                assigned = True
                break
            for nb in odd_r_neighbors(q, r):
                nq, nr = nb
                if nb not in settled:
                    # Weight r-deviation 4x more than q-deviation.  This keeps seats in
                    # their correct latitudinal band (prevents coastal Sussex seats
                    # landing in Oxfordshire rows and vice-versa).
                    d = (nq - q_f) ** 2 + 4 * (nr - r_f) ** 2
                    heapq.heappush(heap, (d, nq, nr))

        if not assigned and free:
            cell = min(free, key=lambda c: (c[0] - q_f) ** 2 + 4 * (c[1] - r_f) ** 2)
            assignment[name] = cell
            free.discard(cell)

    return assignment


# ---------------------------------------------------------------------------
# 2024 special case — use authoritative OI positions directly
# ---------------------------------------------------------------------------

def use_oi_positions(output_path=None, verbose=True):
    """Write output/2024.hexjson using OI reference hex positions (no re-packing)."""
    def log(*args):
        if verbose:
            print(*args)

    log("=== 2024: using OI reference positions directly ===")
    oi = json.loads((REFERENCE / "uk-constituencies-2024.hexjson").read_text())
    hexes = {}
    for h in oi["hexes"].values():
        name = h["n"]
        hexes[name] = {"n": name, "q": h["q"], "r": h["r"], "region": h["region"]}

    output = {"layout": "odd-r", "hexes": hexes}
    OUTPUT.mkdir(exist_ok=True)
    out_path = output_path or OUTPUT / "2024.hexjson"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    log(f"Wrote {len(hexes)} hexes → {out_path}")
    return output


# ---------------------------------------------------------------------------
# Main packing routine
# ---------------------------------------------------------------------------

def pack_year(year, output_path=None, verbose=True):
    def log(*args):
        if verbose:
            print(*args)

    if year == 2024:
        return use_oi_positions(output_path=output_path, verbose=verbose)

    log(f"=== Packing {year} ===")
    log("Loading 2024 reference…")
    masks_2024, eng_pts = load_2024_reference()

    log(f"Loading {year} GeoJSON…")
    mainland_feats, island_feats, outside_names = load_year_features(year)
    log(f"  {len(mainland_feats)} mainland + {len(island_feats)} island"
        + (f" + {len(outside_names)} outside-boundary (1945)" if outside_names else ""))

    # Assign mainland constituencies to ONS regions
    by_region = defaultdict(list)
    for name, source, lon, lat in mainland_feats:
        region = assign_region(source, lon, lat, eng_pts)
        by_region[region].append((name, lon, lat))

    log("Region seat counts (year vs 2024):")
    for code, seats in sorted(by_region.items()):
        log(f"  {code}: {len(seats):3d}  (2024: {len(masks_2024.get(code, []))})")

    # -----------------------------------------------------------------------
    # Reserve island cells + their neighbours — neither the island cell itself
    # nor any adjacent cell can be occupied by mainland constituencies, so the
    # grow pass can't create unwanted adjacency to the island.
    # -----------------------------------------------------------------------
    island_cells = {(q, r) for _, q, r, _ in island_feats}
    island_buffer = island_cells | {
        nb for q, r in island_cells for nb in odd_r_neighbors(q, r)
    }

    # -----------------------------------------------------------------------
    # Two-pass mask adjustment
    # -----------------------------------------------------------------------

    # Region-specific mask-adjustment parameters (defined before growing_region_cells
    # so the r_floor can be applied when computing adj_benefit scores).
    # SW: shrink northward first to preserve Cornwall's south-western tip.
    # SE: shrink northward first so coastal cells are retained when SE is smaller.
    # London: don't grow south of its 2024 southern boundary (r=-43) so London
    #         seats can't appear on the south coast in historical elections.
    SHRINK_PREFER_NORTH = {"E12000009", "E12000008"}   # SW, SE
    LONDON_GROW_R_FLOOR = -43                           # London stays at r≥-43

    growing_region_cells = set()
    for region, seats in by_region.items():
        if len(seats) > len(masks_2024.get(region, [])):
            cells = masks_2024.get(region, [])
            if region == "E12000007":
                # London cannot grow below LONDON_GROW_R_FLOOR.  Exclude its
                # floor row (r=-43) from adj_benefit scoring so SE cells at r=-44
                # (south of the floor) are not preferentially freed: London can
                # never absorb them, so they shouldn't be treated as beneficiary-
                # adjacent during the SE shrink.
                cells = [c for c in cells if c[1] > LONDON_GROW_R_FLOOR]
            growing_region_cells.update(cells)

    current_masks = {
        r: set(c) - island_buffer - PERMANENT_GAPS
        for r, c in masks_2024.items()
    }

    # SE anchor cells that are only valid from 1974 onwards.
    # In 1955-1970 the London mask grows to ~99 cells (the 2024 centroid classifier
    # assigns outer-London pre-1974 constituencies to London), pushing London into
    # q=58-67 at r=-36 to -43.  This surrounds the (59,-35)/(60,-35) Bucks cells and
    # (59,-43) coast slot on all sides, making them isolated islands within London.
    # Dropping those anchors for pre-1974 years lets Hungarian place those seats in
    # the main SE body instead.
    SE_PRE74_DROP = {(59, -35), (60, -35), (59, -43)}
    effective_anchors = {}
    for region, cells in REGION_ANCHOR_CELLS.items():
        if region == "E12000008" and year < 1974:
            effective_anchors[region] = cells - SE_PRE74_DROP
        else:
            effective_anchors[region] = cells

    # Pass 1 — shrink
    for region, seats in by_region.items():
        n = len(seats)
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

    # Global occupied set after shrinking — also pre-seed with island buffer and
    # permanent gaps so neither the grow pass nor geographic_assign can use them.
    all_occupied = {c for mask in current_masks.values() for c in mask} | island_buffer | PERMANENT_GAPS

    # Pass 2 — grow
    for region, seats in sorted(by_region.items()):
        n = len(seats)
        base = current_masks.get(region, set())
        if n > len(base):
            # Grow toward the region's own centroid to avoid drifting into wrong areas
            base_list = list(base)
            if base_list:
                q_c = sum(c[0] for c in base_list) / len(base_list)
                r_c = sum(c[1] for c in base_list) / len(base_list)
                centroid_hint = (q_c, r_c)
            else:
                centroid_hint = None
            r_floor = LONDON_GROW_R_FLOOR if region == "E12000007" else None
            grown = grow_mask(base, n, all_occupied, centroid_hint=centroid_hint,
                              r_floor=r_floor)
            new_cells = grown - base
            current_masks[region] = grown
            all_occupied.update(new_cells)

    # -----------------------------------------------------------------------
    # Assign constituencies to cells
    # -----------------------------------------------------------------------
    hexes = {}
    warnings = []

    for region, seats in by_region.items():
        mask_set = set(current_masks.get(region, []))
        n = len(seats)
        if len(mask_set) < n:
            warnings.append(
                f"{region}: only {len(mask_set)} cells for {n} seats"
            )

        # London's mask occupies the central q range (q=58–68) across all
        # election years, splitting SE into a west corridor (q=53–57) and
        # east corridor (q=67–72) connected only via the coast row.  Greedy
        # Dijkstra cascades Berkshire seats east because their ideal cells are
        # London-occupied.  Hungarian matching prevents this for all years.
        #
        # Pre-assigned coast seats are locked in BEFORE Hungarian so they
        # don't pollute the global optimum or create displacement chains.
        pre_fixed = {}
        seats_for_assign = seats
        if region == "E12000008" and year >= 1983:
            # Brighton cluster only for 1983-1992 (see BRIGHTON_PREASSIGN_1983).
            preassign_list = (
                BRIGHTON_PREASSIGN_1983 + SE_COASTAL_PREASSIGN
                if year <= 1992
                else SE_COASTAL_PREASSIGN
            )
            name_lower = {
                sn.lower().replace("&", "and").replace("-", " "): sn
                for sn, _, _ in seats
            }
            for frag, q_t, r_t in preassign_list:
                if (q_t, r_t) not in mask_set:
                    continue  # target cell not in this year's mask
                matched = next(
                    (sn for nl, sn in name_lower.items() if frag in nl),
                    None,
                )
                if matched is None or matched in pre_fixed:
                    continue  # seat absent or already locked
                pre_fixed[matched] = (q_t, r_t)
                mask_set.discard((q_t, r_t))
            seats_for_assign = [(sn, lo, la) for sn, lo, la in seats
                                 if sn not in pre_fixed]

        use_hungarian = (region == "E12000008")
        assignment = geographic_assign_region(
            [(name, lon, lat) for name, lon, lat in seats_for_assign],
            list(mask_set),
            use_hungarian=use_hungarian,
        )
        assignment.update(pre_fixed)

        for name, (q, r) in assignment.items():
            hexes[name] = {"n": name, "q": q, "r": r, "region": region}

    # -----------------------------------------------------------------------
    # Append island seats at fixed detached positions
    # -----------------------------------------------------------------------
    for name, q, r, region in island_feats:
        hexes[name] = {"n": name, "q": q, "r": r, "region": region, "island": True}

    # -----------------------------------------------------------------------
    # Fill interior holes
    # -----------------------------------------------------------------------
    hexes = fill_holes(hexes, {}, island_buffer=island_buffer)

    # -----------------------------------------------------------------------
    # South Wales q-shift (pre-1974 boundaries only)
    # In 1945-1970 elections the packing leaves a 2-cell gap between the
    # South Wales bloc (r=-34 to -38) and SW England.  Shifting those cells
    # +2 in q closes the gap: rows r=-34 to -37 become flush with England
    # (gap=0), and r=-38 (Cardiff Bay / Severn Estuary) has a gap of 1 which
    # is geographically correct.  Adjacency to r=-33 (Ebbw Vale, Brecon etc.)
    # is preserved — every r=-33 seat remains a hex-neighbour of at least one
    # shifted r=-34 seat.
    # -----------------------------------------------------------------------
    if year < 1974:
        for h in hexes.values():
            if h.get("region") == "W92000004" and -38 <= h["r"] <= -34:
                h["q"] += 2

    # South Wales q-shift (1983-2005 boundaries)
    # In 1983-2005 elections, Wales rows r=-35,-36,-37 sit 2 cells west of
    # the nearest English constituencies (Wyre Forest, Hereford, Stroud).
    # Shifting those rows +2q closes the gap: Newport W, Cardiff S & Penarth,
    # and Caerphilly become flush with England (gap=0).  r=-38 (Bridgend,
    # Vale of Glamorgan) is intentionally excluded and stays in place.
    # Adjacency to r=-38 is preserved (Swansea E/Gower/Ogmore remain
    # neighbours of Bridgend and Vale of Glamorgan after the shift).
    # -----------------------------------------------------------------------
    if 1983 <= year <= 2005:
        for h in hexes.values():
            if h.get("region") == "W92000004" and -37 <= h["r"] <= -35:
                h["q"] += 2

    if warnings:
        for w in warnings:
            log(f"  WARNING: {w}")

    output = {"layout": "odd-r", "hexes": hexes}

    OUTPUT.mkdir(exist_ok=True)
    out_path = output_path or OUTPUT / f"{year}.hexjson"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    n_total = len(mainland_feats) + len(island_feats)
    log(f"\nWrote {len(hexes)}/{n_total} hexes → {out_path}")
    return output


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Pack UK election hexjson")
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    pack_year(args.year, output_path=args.output)


if __name__ == "__main__":
    main()
