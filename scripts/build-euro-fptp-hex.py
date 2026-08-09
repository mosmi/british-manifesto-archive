#!/usr/bin/env python3
"""Build European Parliament FPTP-era constituency hexjson (1979–1994).

Reads:
  data/sources/european-parliament-elections/constituency-winners-1979-1994.json
  data/sources/european-parliament-elections/westminster-to-ep/{1979,1984,1994}.json

Writes:
  data/hex/euro/{1979,1984,1989,1994}.hexjson

Geometry:
  Crosswalk centroids preserve relative geography but sit on the ~650-seat
  Westminster frame, so raw placement is sparse. This builder packs each
  nation (England / Scotland / Wales) by scaling centroids → Hungarian snap →
  component merge → hole fill, then assembles them into one contiguous GB
  outline. Highlands and Islands and Northern Ireland stay detached.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WINNERS = ROOT / "data/sources/european-parliament-elections/constituency-winners-1979-1994.json"
XW_DIR = ROOT / "data/sources/european-parliament-elections/westminster-to-ep"
OUT_DIR = ROOT / "data/hex/euro"

CROSSWALK_YEAR = {
    1979: 1979,
    1984: 1984,
    1989: 1984,
    1994: 1994,
}

NI_NAME = "Northern Ireland"
HIGHLANDS_NAME = "Highlands and Islands"

# Scale factors pull sparse Westminster-frame centroids together before snap.
# England needs stronger compression; Scotland/Wales are already small clusters.
PACK_SCALE = {
    "england": (0.40, 0.48),
    "scotland": (0.55, 0.55),
    "wales": (0.70, 0.70),
}


def slugify(name: str) -> str:
    s = name.lower().replace("&", "and")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "constituency"


def oddr_neighbors(q: int, r: int) -> list[tuple[int, int]]:
    """Neighbour offsets for odd-r (pointy-top) offset coords."""
    if r % 2 == 0:
        deltas = ((+1, 0), (0, -1), (-1, -1), (-1, 0), (-1, +1), (0, +1))
    else:
        deltas = ((+1, 0), (+1, -1), (0, -1), (-1, 0), (0, +1), (+1, +1))
    return [(q + dq, r + dr) for dq, dr in deltas]


def classify_nation(name: str) -> str:
    if name == NI_NAME:
        return "ni"
    if name == HIGHLANDS_NAME:
        return "island"
    if "Wales" in name:
        return "wales"
    if any(tok in name for tok in ("Scotland", "Glasgow", "Lothians", "Strathclyde")):
        return "scotland"
    return "england"


def lap_solve(cost_rows: list[list[float]]) -> list[int]:
    """Jonker–Volgenant assignment; returns column index per row."""
    inf = float("inf")
    n_rows = len(cost_rows)
    n_cols = len(cost_rows[0])
    if n_rows < n_cols:
        cost: list[list[float]] = list(cost_rows) + [[0.0] * n_cols] * (n_cols - n_rows)
    else:
        cost = cost_rows
    n = n_cols
    u = [0.0] * (n + 1)
    v = [0.0] * (n + 1)
    p = [0] * (n + 1)
    way = [0] * (n + 1)
    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        mins = [inf] * (n + 1)
        used = [False] * (n + 1)
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = inf
            j1 = -1
            for j in range(1, n + 1):
                if used[j]:
                    continue
                val = cost[i0 - 1][j - 1] - u[i0] - v[j]
                if val < mins[j]:
                    mins[j] = val
                    way[j] = j0
                if mins[j] < delta:
                    delta = mins[j]
                    j1 = j
            for j in range(n + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    mins[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while j0:
            p[j0] = p[way[j0]]
            j0 = way[j0]
    col_for_row = [0] * n
    for j in range(1, n + 1):
        if p[j]:
            col_for_row[p[j] - 1] = j - 1
    return col_for_row[:n_rows]


def unique_snap(float_pos: dict[str, tuple[float, float]]) -> dict[str, tuple[int, int]]:
    """Assign each seat to a unique integer cell near its float ideal (Hungarian)."""
    names = list(float_pos)
    ideals = [float_pos[n] for n in names]
    cands: set[tuple[int, int]] = set()
    for q, r in ideals:
        aq, ar = int(round(q)), int(round(r))
        stack = [(aq, ar)]
        seen = {(aq, ar)}
        for _ in range(5):
            nxt = []
            for c in stack:
                cands.add(c)
                for nb in oddr_neighbors(*c):
                    if nb not in seen:
                        seen.add(nb)
                        nxt.append(nb)
            stack = nxt
    while len(cands) < len(names) + 8:
        extra = {nb for c in cands for nb in oddr_neighbors(*c) if nb not in cands}
        if not extra:
            break
        cands |= extra
    cells = list(cands)
    cost = [
        [
            (cells[j][0] - ideals[i][0]) ** 2 + 4 * (cells[j][1] - ideals[i][1]) ** 2
            for j in range(len(cells))
        ]
        for i in range(len(names))
    ]
    assign = lap_solve(cost)
    return {names[i]: cells[assign[i]] for i in range(len(names))}


def connected_components(occupied: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    seen: set[tuple[int, int]] = set()
    comps: list[set[tuple[int, int]]] = []
    for c in occupied:
        if c in seen:
            continue
        comp: set[tuple[int, int]] = set()
        dq: deque[tuple[int, int]] = deque([c])
        seen.add(c)
        while dq:
            cur = dq.popleft()
            comp.add(cur)
            for nb in oddr_neighbors(*cur):
                if nb in occupied and nb not in seen:
                    seen.add(nb)
                    dq.append(nb)
        comps.append(comp)
    return comps


def _translate_comp(
    comp: set[tuple[int, int]], dq: int, dr: int, blocked: set[tuple[int, int]]
) -> set[tuple[int, int]] | None:
    new = {(q + dq, r + dr) for q, r in comp}
    if new & blocked:
        return None
    return new


def merge_components(
    pos: dict[str, tuple[int, int]], max_iters: int = 300
) -> dict[str, tuple[int, int]]:
    """Translate smaller components toward nearest until one contiguous blob."""
    pos = dict(pos)
    for _ in range(max_iters):
        occupied = set(pos.values())
        comps = connected_components(occupied)
        if len(comps) <= 1:
            break
        best = None
        for i, a in enumerate(comps):
            for b in comps[i + 1 :]:
                for ca in a:
                    for cb in b:
                        d = abs(ca[0] - cb[0]) + abs(ca[1] - cb[1])
                        if best is None or d < best[0]:
                            best = (d, a, b, ca, cb)
        assert best is not None
        _, a, b, ca, cb = best
        moving, from_cell, target_cell = (a, ca, cb) if len(a) <= len(b) else (b, cb, ca)
        dq = 0 if target_cell[0] == from_cell[0] else (1 if target_cell[0] > from_cell[0] else -1)
        dr = 0 if target_cell[1] == from_cell[1] else (1 if target_cell[1] > from_cell[1] else -1)
        blocked = occupied - moving
        delta = None
        for step in ((dq, dr), (dq, 0), (0, dr), (1, 0), (-1, 0), (0, 1), (0, -1)):
            if step == (0, 0):
                continue
            if _translate_comp(moving, step[0], step[1], blocked) is not None:
                delta = step
                break
        if delta is None:
            break
        pos = {
            n: ((c[0] + delta[0], c[1] + delta[1]) if c in moving else c)
            for n, c in pos.items()
        }
    return pos


def fill_holes(
    pos: dict[str, tuple[int, int]], max_passes: int = 60
) -> dict[str, tuple[int, int]]:
    """Pull peripheral seats into interior voids (cells with ≥4 occupied neighbours)."""
    pos = dict(pos)
    for _ in range(max_passes):
        cells = {v: k for k, v in pos.items()}
        occupied = set(cells)
        qs = [c[0] for c in occupied]
        rs = [c[1] for c in occupied]
        holes: list[tuple[int, tuple[int, int]]] = []
        for q in range(min(qs), max(qs) + 1):
            for r in range(min(rs), max(rs) + 1):
                if (q, r) in occupied:
                    continue
                nbs = sum(1 for nb in oddr_neighbors(q, r) if nb in occupied)
                if nbs >= 4:
                    holes.append((nbs, (q, r)))
        if not holes:
            break
        holes.sort(reverse=True)
        hole = holes[0][1]
        peri: list[tuple[int, int, tuple[int, int]]] = []
        for c in occupied:
            if any(nb not in occupied for nb in oddr_neighbors(*c)):
                nocc = sum(1 for nb in oddr_neighbors(*c) if nb in occupied)
                peri.append((nocc, (c[0] - hole[0]) ** 2 + (c[1] - hole[1]) ** 2, c))
        if not peri:
            break
        peri.sort()
        donor = peri[0][2]
        pos[cells[donor]] = hole
    return pos


def pack_group(
    cents: dict[str, tuple[float, float]], fq: float, fr: float, *, do_fill_holes: bool = True
) -> dict[str, tuple[int, int]]:
    if not cents:
        return {}
    if len(cents) == 1:
        name, (q, r) = next(iter(cents.items()))
        return {name: (int(round(q)), int(round(r)))}
    mq = sum(c[0] for c in cents.values()) / len(cents)
    mr = sum(c[1] for c in cents.values()) / len(cents)
    scaled = {n: (mq + fq * (c[0] - mq), mr + fr * (c[1] - mr)) for n, c in cents.items()}
    pos = unique_snap(scaled)
    pos = merge_components(pos)
    if do_fill_holes:
        pos = fill_holes(pos)
    return pos


def _shift(pos: dict[str, tuple[int, int]], dq: int, dr: int) -> dict[str, tuple[int, int]]:
    return {n: (c[0] + dq, c[1] + dr) for n, c in pos.items()}


def _bbox(pos: dict[str, tuple[int, int]]) -> tuple[int, int, int, int]:
    qs = [c[0] for c in pos.values()]
    rs = [c[1] for c in pos.values()]
    return min(qs), max(qs), min(rs), max(rs)


def _overlaps(a: dict[str, tuple[int, int]], b: dict[str, tuple[int, int]]) -> bool:
    return bool(set(a.values()) & set(b.values()))


def assemble_gb(
    eng: dict[str, tuple[int, int]],
    sco: dict[str, tuple[int, int]],
    wal: dict[str, tuple[int, int]],
) -> dict[str, tuple[int, int]]:
    """Place Scotland north and Wales west of England so GB is one contiguous piece."""
    eq0, _, er0, _ = _bbox(eng)
    eng = _shift(eng, -eq0, -er0)
    out = dict(eng)
    eng_bb = _bbox(eng)

    # Custom Scotland layout: place Glasgow in Central Belt row below Mid Scotland & Fife / NE Scotland
    sco_base_rel = {
        "Glasgow": (1, 1),
        "Strathclyde West": (0, 1),
        "Strathclyde East": (2, 1),
        "Lothians": (3, 1),
        "South of Scotland": (2, 0),
        "Scotland South": (2, 0),
        "Mid Scotland and Fife": (1, 2),
        "Scotland Mid & Fife": (1, 2),
        "North East Scotland": (2, 2),
        "Scotland North East": (2, 2),
    }
    for name in list(sco.keys()):
        for rel_name, rel_pos in sco_base_rel.items():
            if rel_name in name:
                sco[name] = rel_pos
                break

    sco_bb = _bbox(sco)
    eng_north = [c for c in eng.values() if c[1] >= eng_bb[3] - 1]
    target_q = sum(c[0] for c in eng_north) / len(eng_north)
    sco_qmid = (sco_bb[0] + sco_bb[1]) / 2
    sco = _shift(sco, int(round(target_q - sco_qmid)), 0)
    sco_bb = _bbox(sco)
    sco = _shift(sco, 0, eng_bb[3] + 1 - sco_bb[2])
    while _overlaps(out, sco):
        sco = _shift(sco, 0, 1)

    # Shift Scotland q left or right if needed to ensure touch with northern England
    occ_eng = set(out.values())
    if not any(nb in occ_eng for c in sco.values() for nb in oddr_neighbors(*c)):
        for dq in [1, -1, 2, -2]:
            t_sco = _shift(sco, dq, 0)
            if not _overlaps(out, t_sco) and any(nb in occ_eng for c in t_sco.values() for nb in oddr_neighbors(*c)):
                sco = t_sco
                break

    out.update(sco)

    # Wales: west of England, budged right until touching English border directly
    wal_bb = _bbox(wal)
    eng_bb = _bbox(eng)
    # Shift Wales right until it touches England
    occ = set(out.values())
    while not _overlaps(out, wal) and not any(nb in occ for c in wal.values() for nb in oddr_neighbors(*c)):
        trial = _shift(wal, 1, 0)
        if _overlaps(out, trial):
            break
        wal = trial

    out.update(wal)
    return out


def place_detached(
    out: dict[str, tuple[int, int]],
    name: str,
    q: int,
    r: int,
    *,
    away: str,
) -> None:
    """Place a seat with a one-cell buffer (no edge adjacency to mainland)."""
    occupied = set(out.values())
    while (q, r) in occupied or any(nb in occupied for nb in oddr_neighbors(q, r)):
        if away == "north":
            r += 1
        else:
            q -= 1
    out[name] = (q, r)


def compact_positions(
    centroids: dict[str, dict],
    *,
    do_fill_holes: bool = True,
) -> dict[str, tuple[int, int]]:
    """Build contiguous GB + detached Highlands from crosswalk centroids."""
    by_nation: dict[str, dict[str, tuple[float, float]]] = defaultdict(dict)
    for name, cell in centroids.items():
        by_nation[classify_nation(name)][name] = (float(cell["q"]), float(cell["r"]))

    eng = pack_group(by_nation["england"], *PACK_SCALE["england"], do_fill_holes=do_fill_holes)
    sco = pack_group(by_nation["scotland"], *PACK_SCALE["scotland"], do_fill_holes=do_fill_holes)
    wal = pack_group(by_nation["wales"], *PACK_SCALE["wales"], do_fill_holes=do_fill_holes)
    out = assemble_gb(eng, sco, wal)

    sco_cells = [out[n] for n in out if classify_nation(n) == "scotland"]
    place_detached(
        out,
        HIGHLANDS_NAME,
        int(round(sum(c[0] for c in sco_cells) / len(sco_cells))),
        max(c[1] for c in sco_cells) + 2,
        away="north",
    )
    return out


def build_year(year: int, winners_root: dict, election_json: dict) -> dict:
    xw_year = CROSSWALK_YEAR[year]
    xw = json.loads((XW_DIR / f"{xw_year}.json").read_text(encoding="utf-8"))
    centroids = xw["centroids"]
    win_election = winners_root["elections"][str(year)]
    rows = win_election["constituencies"]

    by_name: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_name[row["constituency"]].append(row)

    # Use established, validated layout for the election year
    out_file = OUT_DIR / f"{year}.hexjson"
    if out_file.exists():
        existing_data = json.loads(out_file.read_text(encoding="utf-8"))
        positions = {
            cell.get("n", k): (cell["q"], cell["r"])
            for k, cell in existing_data.get("hexes", {}).items()
            if not k.startswith("northern-ireland")
        }
    else:
        positions = compact_positions(centroids, do_fill_holes=(year == 1979))

    hexes: dict[str, dict] = {}
    party_counts: Counter[str] = Counter()

    for name, members in sorted(by_name.items()):
        if name == NI_NAME:
            ni_coords = [(-1, 13), (-1, 12), (0, 12)]
            for idx, (m, (nq, nr)) in enumerate(zip(members, ni_coords)):
                key = f"northern-ireland-{idx+1}"
                party_counts[m["party_id"]] += 1
                hexes[key] = {
                    "n": f"Northern Ireland — {m['member']}",
                    "q": nq,
                    "r": nr,
                    "party": m["party_id"],
                    "winner": m["member"],
                }
            continue

        key = slugify(name)
        q, r = positions[name]
        m = members[0]
        party_counts[m["party_id"]] += 1
        hexes[key] = {
            "n": name,
            "q": q,
            "r": r,
            "party": m["party_id"],
            "winner": m["member"],
        }

    coords = [(h["q"], h["r"]) for h in hexes.values()]
    if len(coords) != len(set(coords)):
        clash = [c for c, n in Counter(coords).items() if n > 1]
        raise SystemExit(f"{year}: residual coordinate clashes {clash}")

    expected = {
        r["party"]: r["seats"]
        for r in election_json["parliament"]["results"]
        if r.get("seats", 0) > 0
    }
    if dict(party_counts) != expected:
        raise SystemExit(
            f"{year}: party seat mismatch hex={dict(party_counts)} election={expected}"
        )

    gb = sum(1 for n in by_name if n != NI_NAME)
    expected_total = election_json["parliament"]["totalSeats"]
    if gb + 3 != expected_total:
        raise SystemExit(f"{year}: GB+NI seats {gb}+3 != {expected_total}")
    if len(hexes) != gb + 3:
        raise SystemExit(f"{year}: hex count {len(hexes)} != {gb + 3}")

    mainland = {
        (h["q"], h["r"])
        for h in hexes.values()
        if h["n"] not in (NI_NAME, HIGHLANDS_NAME)
    }
    touch = sum(
        1 for c in mainland if any(nb in mainland for nb in oddr_neighbors(*c))
    )

    return {
        "layout": "odd-r",
        "meta": {
            "year": year,
            "body": "euro",
            "system": "FPTP (GB) + STV (NI)",
            "gb_constituencies": gb,
            "ni_seats": 3,
            "layout_method": "nation-pack-assemble",
            "mainland_touch_pct": round(100 * touch / len(mainland), 1),
            "crosswalk": f"data/sources/european-parliament-elections/westminster-to-ep/{xw_year}.json",
            "winners": "data/sources/european-parliament-elections/constituency-winners-1979-1994.json",
        },
        "hexes": hexes,
    }


def main() -> None:
    winners_root = json.loads(WINNERS.read_text(encoding="utf-8"))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for year in (1979, 1984, 1989, 1994):
        election = json.loads(
            (ROOT / f"data/devolved/euro/{year}.json").read_text(encoding="utf-8")
        )
        payload = build_year(year, winners_root, election)
        out = OUT_DIR / f"{year}.hexjson"
        out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(
            f"Wrote {out.relative_to(ROOT)} "
            f"({len(payload['hexes'])} hexes, "
            f"{payload['meta']['gb_constituencies']} GB + NI, "
            f"mainland touch {payload['meta']['mainland_touch_pct']}%)"
        )


if __name__ == "__main__":
    main()
