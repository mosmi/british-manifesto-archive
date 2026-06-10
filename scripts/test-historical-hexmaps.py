#!/usr/bin/env python3
"""Validation checks for historical hexmap imports (1955–1992)."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "constituencies"

NI_PARTIES = frozenset({"uup", "dup", "sdlp", "sinnfein", "upup", "uuup", "vanguard"})


def neighbors(q: int, r: int) -> set[tuple[int, int]]:
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if r % 2:
        dirs += [(1, 1), (-1, 1)]
    else:
        dirs += [(1, -1), (-1, -1)]
    return {(q + dq, r + dr) for dq, dr in dirs}


def load(election_id: str) -> dict:
    return json.loads((OUT / f"{election_id}.json").read_text(encoding="utf-8"))


def test_seat_counts() -> None:
    for eid, expected in (
        ("1955", 630),
        ("1959", 630),
        ("1964", 630),
        ("1966", 630),
        ("1970", 630),
        ("feb1974", 635),
        ("oct1974", 635),
        ("1979", 635),
        ("1983", 650),
        ("1987", 650),
        ("1992", 651),
    ):
        assert load(eid)["totalSeats"] == expected, eid


def test_hex_match_rates() -> None:
    for eid, expected in (
        ("1955", 630),
        ("1959", 630),
        ("1964", 630),
        ("1966", 630),
        ("1970", 630),
        ("feb1974", 635),
        ("1987", 650),
        ("1992", 651),
    ):
        data = load(eid)
        placed = sum(1 for c in data["constituencies"] if c.get("q") is not None)
        assert data["matchedHexes"] == expected, f"{eid} matchedHexes"
        assert placed == expected, f"{eid} placed constituencies"
        assert data["layout"] == "odd-r", f"{eid} layout"


PRE1974_ELECTIONS = ("1955", "1959", "1964", "1966", "1970")
VINTAGE1974_ELECTIONS = ("feb1974", "oct1974", "1979")


def _england_scaffold() -> set[tuple[int, int]]:
    hex2024 = json.loads(
        (ROOT / "data" / "hex" / "uk-constituencies-2024.hexjson").read_text()
    )
    return {
        (cell["q"], cell["r"])
        for cell in hex2024["hexes"].values()
        if str(cell.get("region") or "").startswith("E")
    }


def test_pre1974_england_scaffold_fill() -> None:
    """1955–1970 England should pack solidly on the 2024 scaffold (630 seats)."""
    england_scaffold = _england_scaffold()
    for eid in PRE1974_ELECTIONS:
        data = load(eid)
        england_seats = [
            c
            for c in data["constituencies"]
            if c.get("nation") == "england" and c.get("q") is not None
        ]
        on_scaffold = sum(
            1 for c in england_seats if (c["q"], c["r"]) in england_scaffold
        )
        empty = england_scaffold - {(c["q"], c["r"]) for c in england_seats}
        occupied = {(c["q"], c["r"]) for c in england_seats}
        surrounded = sum(
            1
            for coord in empty
            if sum(1 for n in neighbors(*coord) if n in occupied) >= 5
        )
        off_scaffold = len(england_seats) - on_scaffold
        assert off_scaffold <= 25, (
            f"{eid}: {off_scaffold} England seats off scaffold (expected coast/edge only)"
        )
        assert len(empty) <= 55, (
            f"{eid}: {len(empty)} empty England scaffold cells "
            "(630 seats vs 650 cells; empties should be peripheral)"
        )
        assert surrounded == 0, (
            f"{eid}: {surrounded} interior England holes with 5+ neighbours"
        )
        interior = _interior_empty_scaffold(england_scaffold, occupied)
        assert not interior, (
            f"{eid}: {len(interior)} inland empty scaffold cells remain {interior[:6]}"
        )


def _interior_empty_scaffold(
    england_scaffold: set[tuple[int, int]], occupied: set[tuple[int, int]]
) -> list[tuple[int, int]]:
    """Test helper mirroring import script interior-empty detection."""
    from collections import deque

    empty = england_scaffold - occupied
    peripheral: set[tuple[int, int]] = set()
    for start in empty:
        if sum(1 for n in neighbors(*start) if n in occupied) > 2:
            continue
        queue: deque[tuple[int, int]] = deque([start])
        seen = {start}
        while queue:
            coord = queue.popleft()
            peripheral.add(coord)
            for nbr in neighbors(*coord):
                if nbr in empty and nbr not in seen:
                    seen.add(nbr)
                    queue.append(nbr)
    flood_interior = empty - peripheral
    coastal = {
        cell
        for cell in flood_interior
        if any(nbr not in england_scaffold for nbr in neighbors(*cell))
    }
    return sorted(flood_interior - coastal)


def test_1974_shared_names_mostly_on_scaffold() -> None:
    """Unchanged 1974 names should stay on the England scaffold after solid packing."""
    england_scaffold = _england_scaffold()
    data83 = load("1983")
    names83 = {c["name"] for c in data83["constituencies"]}
    for eid in VINTAGE1974_ELECTIONS:
        data = load(eid)
        shared = [
            c
            for c in data["constituencies"]
            if c["name"] in names83 and c.get("q") is not None
        ]
        assert len(shared) >= 390, f"{eid}: expected most unchanged names placed"
        off = sum(
            1
            for c in shared
            if c.get("nation") == "england" and (c["q"], c["r"]) not in england_scaffold
        )
        assert off <= 25, f"{eid}: {off} shared England names off scaffold after packing"


def test_1974_england_scaffold_fill() -> None:
    """1974 England should pack like 1983 — interior holes cascaded to coast/periphery."""
    england_scaffold = _england_scaffold()
    for eid in VINTAGE1974_ELECTIONS:
        data = load(eid)
        england_seats = [
            c
            for c in data["constituencies"]
            if c.get("nation") == "england" and c.get("q") is not None
        ]
        on_scaffold = sum(
            1 for c in england_seats if (c["q"], c["r"]) in england_scaffold
        )
        empty = england_scaffold - {(c["q"], c["r"]) for c in england_seats}
        occupied = {(c["q"], c["r"]) for c in england_seats}
        surrounded = sum(
            1
            for coord in empty
            if sum(1 for n in neighbors(*coord) if n in occupied) >= 5
        )
        off_scaffold = len(england_seats) - on_scaffold
        assert off_scaffold <= 25, (
            f"{eid}: {off_scaffold} England seats off scaffold (expected coast/edge only)"
        )
        assert len(empty) <= 50, (
            f"{eid}: {len(empty)} empty England scaffold cells "
            "(635 seats vs 650 cells; empties should be peripheral)"
        )
        assert surrounded == 0, (
            f"{eid}: {surrounded} interior England holes with 5+ neighbours"
        )


def test_1974_few_surrounded_scaffold_gaps() -> None:
    """1974 maps should have at most a handful of deeply surrounded empty England cells."""
    hex2024 = json.loads(
        (ROOT / "data" / "hex" / "uk-constituencies-2024.hexjson").read_text()
    )
    for eid in VINTAGE1974_ELECTIONS:
        data = load(eid)
        occupied = {
            (c["q"], c["r"])
            for c in data["constituencies"]
            if c.get("nation") == "england" and c.get("q") is not None
        }
        surrounded = 0
        for cell in hex2024["hexes"].values():
            if not str(cell.get("region") or "").startswith("E"):
                continue
            coord = (cell["q"], cell["r"])
            if coord in occupied:
                continue
            if sum(1 for n in neighbors(*coord) if n in occupied) >= 5:
                surrounded += 1
        assert surrounded == 0, (
            f"{eid}: {surrounded} empty England cells still have 5+ neighbours"
        )


def test_1974_no_surrounded_map_holes() -> None:
    """No empty hex ring cell on the GB map should be surrounded by five or more seats."""
    for eid in VINTAGE1974_ELECTIONS:
        data = load(eid)
        occupied = {
            (c["q"], c["r"])
            for c in data["constituencies"]
            if c.get("q") is not None and c.get("party") not in NI_PARTIES
        }
        surrounded = sum(
            1
            for gap in adjacent_map_gaps(occupied)
            if sum(1 for n in neighbors(*gap) if n in occupied) >= 5
        )
        assert surrounded == 0, f"{eid}: {surrounded} visible interior map holes remain"


def adjacent_map_gaps(occupied: set[tuple[int, int]]) -> set[tuple[int, int]]:
    gaps: set[tuple[int, int]] = set()
    for coord in occupied:
        gaps |= neighbors(*coord)
    gaps -= occupied
    return gaps


def test_1974_landmark_adjacent_gaps() -> None:
    """Deprecated: packing quality is enforced by test_1974_england_scaffold_fill."""
    test_1974_england_scaffold_fill()


def test_harwich_connected_to_mainland() -> None:
    """Harwich must share a hex component with the bulk of Great Britain seats."""
    for eid in VINTAGE1974_ELECTIONS:
        data = load(eid)
        occupied = {(c["q"], c["r"]) for c in data["constituencies"]}
        harwich = next(
            (c["q"], c["r"])
            for c in data["constituencies"]
            if c["name"] == "Harwich"
        )
        seen = {harwich}
        queue = [harwich]
        while queue:
            coord = queue.pop()
            for nbr in neighbors(*coord):
                if nbr in occupied and nbr not in seen:
                    seen.add(nbr)
                    queue.append(nbr)
        assert len(seen) >= 600, f"{eid}: Harwich isolated ({len(seen)} seats in component)"


def test_feb_and_oct_1974_same_hex_layout() -> None:
    feb = {c["name"]: (c["q"], c["r"]) for c in load("feb1974")["constituencies"]}
    oct_ = {c["name"]: (c["q"], c["r"]) for c in load("oct1974")["constituencies"]}
    assert feb == oct_


def test_milton_keynes_adjacent() -> None:
    data = load("1992")
    by_name = {c["name"]: c for c in data["constituencies"]}
    ne = by_name["Milton Keynes North East"]
    sw = by_name["Milton Keynes South West"]
    assert ne.get("q") is not None and sw.get("q") is not None
    assert (ne["q"], ne["r"]) in neighbors(sw["q"], sw["r"])


def test_ni_parties_in_inset() -> None:
    """NI-winning parties should occupy the western inset (low q band)."""
    for eid in ("1983", "1987", "1992"):
        data = load(eid)
        ni_q = [
            c["q"]
            for c in data["constituencies"]
            if c.get("party") in NI_PARTIES and c.get("q") is not None
        ]
        gb_q = [
            c["q"]
            for c in data["constituencies"]
            if c.get("party") not in NI_PARTIES and c.get("q") is not None
        ]
        assert ni_q, f"{eid}: no NI seats placed"
        assert max(ni_q) < max(gb_q), f"{eid}: NI seats should sit west of mainland (lower q)"


def test_alliance_mapped_to_libdem() -> None:
    data = load("1983")
    alliance = [c for c in data["constituencies"] if "Alliance" in (c.get("partyLabel") or "")]
    assert alliance, "expected Alliance seats in 1983"
    assert all(c["party"] == "libdem" for c in alliance)


def test_ynys_mon_matches_2024_scaffold() -> None:
    ref = load("2024")
    ref_ynys = next(c for c in ref["constituencies"] if "ynys" in c["name"].lower())
    for eid in ("1983", "1987", "1992"):
        data = load(eid)
        assert data["hexLayout"] == "uk-constituencies-2024.hexjson", f"{eid} hexLayout"
        ynys = next(c for c in data["constituencies"] if "ynys" in c["name"].lower())
        assert (ynys["q"], ynys["r"]) == (ref_ynys["q"], ref_ynys["r"]), f"{eid} Ynys Môn"


def test_western_isles_in_scotland() -> None:
    ref = load("2024")
    ref_wi = next(c for c in ref["constituencies"] if "eileanan" in c["name"].lower())
    for eid in ("1983", "1987", "1992"):
        data = load(eid)
        wi = next(c for c in data["constituencies"] if c["name"] == "Western Isles")
        assert (wi["q"], wi["r"]) == (ref_wi["q"], ref_wi["r"]), f"{eid} Western Isles"
        assert wi["r"] > -20, f"{eid} Western Isles should sit in the Scotland band, not the south coast"


def test_scottish_seats_stay_in_scotland() -> None:
    hex2024 = json.loads((ROOT / "data" / "hex" / "uk-constituencies-2024.hexjson").read_text())
    scot_coords = {
        (cell["q"], cell["r"])
        for cell in hex2024["hexes"].values()
        if str(cell.get("region") or "").startswith("S")
    }
    england_coords = {
        (cell["q"], cell["r"])
        for cell in hex2024["hexes"].values()
        if str(cell.get("region") or "").startswith("E")
    }
    for eid in ("1983", "1987", "1992"):
        data = load(eid)
        for c in data["constituencies"]:
            if c.get("nation") != "scotland" or c.get("q") is None:
                continue
            coord = (c["q"], c["r"])
            assert coord not in england_coords, (
                f"{eid} {c['name']} placed on an England hex at {coord}"
            )
            if coord not in scot_coords:
                # 1983–92 had up to 72 Scottish seats vs 57 on the 2024 map — overflow
                # must still sit beside the Scotland cluster, not on the south coast.
                assert c["r"] > -20, (
                    f"{eid} {c['name']} Scottish overflow too far south at {coord}"
                )


def test_overflow_seats_beside_anchors() -> None:
    """Pre-devolution overflow seats should sit near their 2024 successor cell."""
    by_name = {}
    spec = importlib.util.spec_from_file_location(
        "import_historical_hexmaps",
        ROOT / "scripts" / "import-historical-hexmaps.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    by_name, *_ = mod.build_scaffold()

    checks = [
        ("1983", "Motherwell South", "scotland", 3),
        ("1983", "Glasgow Hillhead", "scotland", 3),
        ("1983", "Glasgow Maryhill", "scotland", 3),
        ("1983", "Glasgow Pollok", "scotland", 3),
        ("1983", "Edinburgh Pentlands", "scotland", 3),
        ("1983", "Ogmore", "wales", 3),
        ("1983", "Caernarfon", "wales", 3),
    ]
    for eid, name, nation, max_hex_dist in checks:
        data = load(eid)
        c = next(x for x in data["constituencies"] if x["name"] == name)
        anchor = mod.lookup_2024_name(name, by_name, nation)
        assert anchor, f"{name} missing anchor"
        dist = mod.hex_distance(c["q"], c["r"], anchor["q"], anchor["r"])
        assert dist <= max_hex_dist, f"{eid} {name} is {dist} hexes from {anchor['n']}"
        # must not sit on the Western Isles anchor unless it is Western Isles
        wi = mod.lookup_2024_name("Western Isles", by_name, "scotland")
        if name != "Western Isles" and nation == "scotland":
            wi_dist = mod.hex_distance(c["q"], c["r"], wi["q"], wi["r"])
            assert wi_dist > 2, f"{eid} {name} wrongly placed by Western Isles at {wi_dist}"


def test_totnes_connected_to_mainland() -> None:
    """Totnes should sit beside the Plymouth/Devon cluster, not on a lone coastal hex."""
    for eid in ("feb1974", "oct1974", "1979"):
        data = load(eid)
        totnes = next(c for c in data["constituencies"] if c["name"] == "Totnes")
        assert totnes.get("q") is not None, f"{eid}: Totnes has no hex"
        occupied = {
            (c["q"], c["r"])
            for c in data["constituencies"]
            if c.get("q") is not None
        }
        coord = (totnes["q"], totnes["r"])
        nbr_count = sum(1 for n in neighbors(*coord) if n in occupied)
        assert nbr_count >= 2, (
            f"{eid}: Totnes at {coord} only has {nbr_count} occupied neighbour(s)"
        )


def test_st_ives_beside_cornwall() -> None:
    data = load("1983")
    by_name = {c["name"]: c for c in data["constituencies"]}
    st = by_name["St Ives"]
    cn = by_name["Cornwall North"]
    cse = by_name["Cornwall South East"]
    st_coord = (st["q"], st["r"])
    assert st_coord in neighbors(cn["q"], cn["r"]), f"St Ives {st_coord} not beside Cornwall North"
    assert st_coord in neighbors(cse["q"], cse["r"]), (
        f"St Ives {st_coord} not beside Cornwall South East"
    )


def test_workington_beside_copeland() -> None:
    data = load("1983")
    by_name = {c["name"]: c for c in data["constituencies"]}
    workington = by_name["Workington"]
    copeland = by_name["Copeland"]
    assert (workington["q"], workington["r"]) in neighbors(copeland["q"], copeland["r"]), (
        f"Workington ({workington['q']},{workington['r']}) not beside Copeland"
    )


def test_liverpool_exchange_in_merseyside() -> None:
    """Liverpool Exchange (1955–1970) should sit in the Liverpool cluster, not on the south coast."""
    for eid in PRE1974_ELECTIONS:
        data = load(eid)
        by_name = {c["name"]: c for c in data["constituencies"]}
        exchange = by_name["Liverpool Exchange"]
        kirkdale = by_name["Liverpool Kirkdale"]
        assert exchange.get("q") is not None
        assert (exchange["q"], exchange["r"]) in neighbors(kirkdale["q"], kirkdale["r"]), (
            f"{eid}: Liverpool Exchange ({exchange['q']},{exchange['r']}) "
            f"not beside Kirkdale ({kirkdale['q']},{kirkdale['r']})"
        )
        assert exchange["r"] >= -28, (
            f"{eid}: Liverpool Exchange too far south (r={exchange['r']})"
        )


def _find_seat(by_name: dict[str, dict], *candidates: str) -> dict | None:
    for name in candidates:
        if name in by_name:
            return by_name[name]
    return None


def test_pre1974_landmark_misplaced_seats() -> None:
    """1955–1970 seats reported as misplaced should sit in their regional clusters."""
    mod = _load_import_module()
    for eid in PRE1974_ELECTIONS:
        data = load(eid)
        by_name = {c["name"]: c for c in data["constituencies"]}
        occupied = {
            (c["q"], c["r"])
            for c in data["constituencies"]
            if c.get("q") is not None
        }

        battersea_s = by_name.get("Battersea South")
        battersea_n = by_name.get("Battersea North")
        if battersea_s and battersea_n:
            assert battersea_s["q"] <= 65, (
                f"{eid}: Battersea South on east coast (q={battersea_s['q']})"
            )
            assert mod.hex_distance(
                battersea_s["q"], battersea_s["r"],
                battersea_n["q"], battersea_n["r"],
            ) <= 2, (
                f"{eid}: Battersea South ({battersea_s['q']},{battersea_s['r']}) "
                f"far from Battersea North ({battersea_n['q']},{battersea_n['r']})"
            )

        barons = by_name.get("Barons Court")
        fulham = by_name.get("Fulham")
        hammersmith = by_name.get("Hammersmith North")
        if barons and fulham and hammersmith:
            assert mod.hex_distance(
                barons["q"], barons["r"], fulham["q"], fulham["r"]
            ) <= 2, f"{eid}: Barons Court far from Fulham"
            assert mod.hex_distance(
                barons["q"], barons["r"], hammersmith["q"], hammersmith["r"]
            ) <= 2, f"{eid}: Barons Court far from Hammersmith North"

        oxford = by_name.get("Oxford")
        abingdon = by_name.get("Abingdon")
        if oxford and abingdon:
            assert oxford["r"] >= -42, (
                f"{eid}: Oxford on south coast (r={oxford['r']})"
            )
            assert mod.hex_distance(
                oxford["q"], oxford["r"], abingdon["q"], abingdon["r"]
            ) <= 3, (
                f"{eid}: Oxford ({oxford['q']},{oxford['r']}) "
                f"far from Abingdon ({abingdon['q']},{abingdon['r']})"
            )

        for name, min_nbrs in (("Plymouth Sutton", 4), ("Devon North", 2)):
            seat = by_name.get(name)
            if seat is None or seat.get("q") is None:
                continue
            coord = (seat["q"], seat["r"])
            nbr_count = sum(1 for n in neighbors(*coord) if n in occupied)
            assert nbr_count >= min_nbrs, (
                f"{eid}: {name} at {coord} only has {nbr_count} mainland neighbour(s)"
            )

        wi = by_name.get("Western Isles")
        if wi is not None:
            assert (wi["q"], wi["r"]) == (47, -2), f"{eid}: Western Isles hex"
            assert (47, -3) not in occupied, f"{eid}: Western Isles gap cell (47,-3) filled"
            wi_nbrs = sum(1 for n in neighbors(47, -2) if n in occupied)
            assert wi_nbrs == 1, (
                f"{eid}: Western Isles should connect to mainland via one hex, got {wi_nbrs}"
            )
            assert (48, -3) in occupied, f"{eid}: Ross & Cromarty should sit at (48,-3)"


def test_inner_london_boundary_seats() -> None:
    """Key 1955 London seats should sit in the inner London cluster, not on the east coast."""
    mod = _load_import_module()
    for eid in PRE1974_ELECTIONS:
        data = load(eid)
        by_name = {c["name"]: c for c in data["constituencies"]}
        greenwich = by_name.get("Greenwich")
        islington_n = by_name.get("Islington North")
        assert greenwich is not None, f"{eid}: missing Greenwich anchor"
        paddington = by_name.get("Paddington North")
        cities = (
            by_name.get("Cities of London & Westminster")
            or by_name.get("London & Westminster - Cities of")
        )
        brixton = _find_seat(by_name, "Brixton", "Lambeth: Brixton")
        clapham = _find_seat(by_name, "Clapham", "Wandsworth Clapham")
        wandsworth_c = by_name.get("Wandsworth Central")
        norwood = _find_seat(by_name, "Norwood", "Lambeth: Norwood")
        northwood = _find_seat(by_name, "Ruislip Northwood", "Ruislip-Northwood")
        brentford = by_name.get("Brentford & Chiswick")
        bucks_south = by_name.get("Buckinghamshire South")
        fulham = by_name.get("Fulham")
        islington_e = by_name.get("Islington East")
        for seat_name, max_dq in (
            ("Brixton", 4),
            ("Woolwich West", 3),
            ("Woolwich East", 3),
            ("West Ham North", 4),
            ("West Ham South", 3),
            ("East Ham South", 4),
            ("East Ham North", 4),
        ):
            seat = _find_seat(by_name, seat_name)
            if seat is None and seat_name == "Brixton":
                seat = brixton
            if seat is None:
                continue
            assert seat.get("q") is not None
            assert abs(seat["q"] - greenwich["q"]) <= max_dq, (
                f"{eid}: {seat_name} too far east (q={seat['q']}, "
                f"Greenwich q={greenwich['q']})"
            )
            assert seat["r"] >= greenwich["r"] - 5, (
                f"{eid}: {seat_name} too far north (r={seat['r']})"
            )
        if brixton is not None and brixton.get("q") is not None:
            assert brixton["q"] in (61, 62, 63) and -43 <= brixton["r"] <= -41, (
                f"{eid}: Brixton should sit in inner south London "
                f"({brixton['q']},{brixton['r']}), not on the south coast"
            )
        if clapham is not None and clapham.get("q") is not None:
            assert clapham["q"] in (61, 62, 63) and -43 <= clapham["r"] <= -41, (
                f"{eid}: Clapham at ({clapham['q']},{clapham['r']})"
            )
        if wandsworth_c is not None and wandsworth_c.get("q") is not None:
            assert wandsworth_c["q"] in (59, 60, 61, 62) and -43 <= wandsworth_c["r"] <= -41, (
                f"{eid}: Wandsworth Central on south coast "
                f"({wandsworth_c['q']},{wandsworth_c['r']})"
            )
        if norwood is not None and norwood.get("q") is not None:
            assert norwood["q"] in (61, 62, 63, 64) and -43 <= norwood["r"] <= -40, (
                f"{eid}: Norwood on south coast ({norwood['q']},{norwood['r']})"
            )
        if northwood is not None and northwood.get("q") is not None:
            assert northwood["q"] in (58, 59, 60, 61) and -38 <= northwood["r"] <= -34, (
                f"{eid}: Ruislip Northwood misplaced ({northwood['q']},{northwood['r']})"
            )
        if brentford is not None and brentford.get("q") is not None:
            assert brentford["q"] in (57, 58, 59, 60, 61) and -42 <= brentford["r"] <= -39, (
                f"{eid}: Brentford & Chiswick on south coast "
                f"({brentford['q']},{brentford['r']})"
            )
        twickenham = by_name.get("Twickenham")
        putney = by_name.get("Putney")
        if twickenham is not None and twickenham.get("q") is not None:
            assert twickenham["q"] in (57, 58, 59, 60) and -42 <= twickenham["r"] <= -40, (
                f"{eid}: Twickenham on south coast ({twickenham['q']},{twickenham['r']})"
            )
            if putney is not None and putney.get("q") is not None:
                assert mod.hex_distance(
                    twickenham["q"], twickenham["r"],
                    putney["q"], putney["r"],
                ) <= 4, (
                    f"{eid}: Twickenham ({twickenham['q']},{twickenham['r']}) "
                    f"far from Putney ({putney['q']},{putney['r']})"
                )
        windsor = by_name.get("Windsor")
        winchester = by_name.get("Winchester")
        if windsor is not None and windsor.get("q") is not None:
            assert windsor["q"] in (55, 56, 57, 58) and -40 <= windsor["r"] <= -37, (
                f"{eid}: Windsor misplaced ({windsor['q']},{windsor['r']})"
            )
            if winchester is not None and winchester.get("q") is not None:
                assert (windsor["q"], windsor["r"]) != (winchester["q"], winchester["r"]), (
                    f"{eid}: Windsor shares Winchester cell"
                )
                assert mod.hex_distance(
                    windsor["q"], windsor["r"],
                    winchester["q"], winchester["r"],
                ) <= 3, (
                    f"{eid}: Windsor ({windsor['q']},{windsor['r']}) "
                    f"far from Winchester ({winchester['q']},{winchester['r']})"
                )
        if bucks_south is not None and bucks_south.get("q") is not None:
            assert bucks_south["q"] in (55, 56, 57, 58, 59, 60) and -38 <= bucks_south["r"] <= -34, (
                f"{eid}: Buckinghamshire South on south coast "
                f"({bucks_south['q']},{bucks_south['r']})"
            )
        devizes = by_name.get("Devizes")
        if devizes is not None and devizes.get("q") is not None:
            assert devizes["q"] in (50, 51, 52, 53, 54) and -42 <= devizes["r"] <= -37, (
                f"{eid}: Devizes on south coast ({devizes['q']},{devizes['r']})"
            )
        if islington_e is not None and islington_e.get("q") is not None and islington_n:
            assert abs(islington_e["q"] - islington_n["q"]) <= 2, (
                f"{eid}: Islington East at ({islington_e['q']},{islington_e['r']}) "
                f"far from Islington North ({islington_n['q']},{islington_n['r']})"
            )
            assert abs(islington_e["r"] - islington_n["r"]) <= 3, (
                f"{eid}: Islington East r={islington_e['r']} vs north r={islington_n['r']}"
            )
        if cities is not None and cities.get("q") is not None:
            assert 60 <= cities["q"] <= 64, (
                f"{eid}: {cities['name']} should sit in central London (q={cities['q']})"
            )
            assert -42 <= cities["r"] <= -38, (
                f"{eid}: {cities['name']} should sit in central London (r={cities['r']})"
            )
        if paddington is not None and paddington.get("q") is not None:
            assert 57 <= paddington["q"] <= 61, (
                f"{eid}: Paddington North should sit in west London (q={paddington['q']})"
            )
            assert -43 <= paddington["r"] <= -39, (
                f"{eid}: Paddington North should sit in west London (r={paddington['r']})"
            )
            if fulham is not None and fulham.get("r") is not None:
                assert paddington["r"] >= fulham["r"], (
                    f"{eid}: Paddington North (r={paddington['r']}) south of "
                    f"Fulham (r={fulham['r']})"
                )
        woolwich_e = by_name.get("Woolwich East")
        woolwich_w = by_name.get("Woolwich West")
        if woolwich_e is not None and woolwich_w is not None:
            assert woolwich_e.get("q") is not None and woolwich_w.get("q") is not None
            assert abs(woolwich_e["q"] - woolwich_w["q"]) <= 2, (
                f"{eid}: Woolwich East ({woolwich_e['q']},{woolwich_e['r']}) "
                f"far from Woolwich West ({woolwich_w['q']},{woolwich_w['r']})"
            )
            assert abs(woolwich_e["r"] - woolwich_w["r"]) <= 2, (
                f"{eid}: Woolwich East r={woolwich_e['r']} vs west r={woolwich_w['r']}"
            )
        east_ham_n = by_name.get("East Ham North")
        east_ham_s = by_name.get("East Ham South")
        if east_ham_n is not None and east_ham_s is not None:
            assert east_ham_n.get("q") is not None and east_ham_s.get("q") is not None
            assert abs(east_ham_n["q"] - east_ham_s["q"]) <= 4, (
                f"{eid}: East Ham North ({east_ham_n['q']},{east_ham_n['r']}) "
                f"far from East Ham South ({east_ham_s['q']},{east_ham_s['r']})"
            )
            assert abs(east_ham_n["r"] - east_ham_s["r"]) <= 3, (
                f"{eid}: East Ham North r={east_ham_n['r']} vs south r={east_ham_s['r']}"
            )

def test_pre1974_england_relative_placements() -> None:
    """England seats should be unique, regionally coherent, and near their anchors when possible."""
    mod = _load_import_module()
    by_name, scaffold_coords, *_rest, england_coords = mod.build_scaffold()
    geo_lookup = mod.load_geo_lookup()
    cell_geos = mod.build_cell_geos(geo_lookup, scaffold_coords)

    pin_targets: dict[tuple[int, int], list[str]] = {}
    for key, coord in mod.MANUAL_HEX.items():
        pin_targets.setdefault(coord, []).append(key)
    pin_conflicts = {cell: keys for cell, keys in pin_targets.items() if len(keys) > 1}
    assert not pin_conflicts, f"Manual pin conflicts: {pin_conflicts}"

    inland_on_coast = (
        "winchester",
        "bath",
        "basingstoke",
        "reading",
        "devizes",
        "wokingham",
        "brentford",
        "paddington",
        "fulham",
        "brixton",
        "wandsworth",
        "buckinghamshire",
    )
    anchor_checks = {
        "Winchester": (55, -40),
        "Bath": (51, -40),
        "Basingstoke": (55, -39),
        "Devizes": (53, -38),
    }

    for eid in PRE1974_ELECTIONS:
        data = load(eid)
        by_cell: dict[tuple[int, int], list[str]] = {}
        for c in data["constituencies"]:
            q, r = c.get("q"), c.get("r")
            if q is None:
                continue
            by_cell.setdefault((q, r), []).append(c["name"])
        dups = {cell: names for cell, names in by_cell.items() if len(names) > 1}
        assert not dups, f"{eid}: duplicate hex cells {dups}"

        by_name_e = {c["name"]: c for c in data["constituencies"]}
        for seat_name, anchor in anchor_checks.items():
            seat = by_name_e.get(seat_name)
            if seat is None or seat.get("q") is None:
                continue
            assert mod.hex_distance(seat["q"], seat["r"], anchor[0], anchor[1]) <= 2, (
                f"{eid}: {seat_name} at ({seat['q']},{seat['r']}) "
                f"far from anchor {anchor}"
            )
            if seat_name == "Winchester":
                bath = by_name_e.get("Bath")
                if bath is not None and bath.get("q") is not None:
                    assert (seat["q"], seat["r"]) != (bath["q"], bath["r"]), (
                        f"{eid}: Winchester shares Bath's cell"
                    )

        for c in data["constituencies"]:
            if c.get("nation") != "england":
                continue
            q, r = c.get("q"), c.get("r")
            if q is None or r not in (-44, -45):
                continue
            if any(token in c["name"].lower() for token in inland_on_coast):
                raise AssertionError(
                    f"{eid}: inland seat {c['name']} on south-coast band ({q},{r})"
                )


def test_southwark_lewisham_in_inner_london() -> None:
    """Southwark and Lewisham West belong in inner London, not on the east coast."""
    for eid in PRE1974_ELECTIONS + VINTAGE1974_ELECTIONS:
        data = load(eid)
        by_name = {c["name"]: c for c in data["constituencies"]}
        southwark = by_name.get("Southwark") or by_name.get("Southwark & Bermondsey")
        lewisham = by_name.get("Lewisham West")
        if southwark is not None and southwark.get("q") is not None:
            greenwich = by_name.get("Greenwich")
            if greenwich is not None:
                assert abs(southwark["r"] - greenwich["r"]) <= 2, (
                    f"{eid}: Southwark ({southwark['q']},{southwark['r']}) "
                    f"not near Greenwich ({greenwich['q']},{greenwich['r']})"
                )
            assert southwark["r"] >= -44, (
                f"{eid}: Southwark too far north/east (r={southwark['r']})"
            )
        if lewisham is not None and lewisham.get("q") is not None:
            lew_anchor = by_name.get("Lewisham North") or by_name.get("Lewisham South")
            if lew_anchor is not None:
                assert abs(lewisham["r"] - lew_anchor["r"]) <= 2, (
                    f"{eid}: Lewisham West ({lewisham['q']},{lewisham['r']}) "
                    f"not near {lew_anchor['name']} ({lew_anchor['q']},{lew_anchor['r']})"
                )
            assert lewisham["r"] >= -44, (
                f"{eid}: Lewisham West too far north/east (r={lewisham['r']})"
            )


def test_richmond_yorks_not_in_surrey() -> None:
    """Richmond (Yorks) must sit in Yorkshire, not on the Richmond-upon-Thames/Surrey hex."""
    for eid in PRE1974_ELECTIONS + VINTAGE1974_ELECTIONS:
        data = load(eid)
        by_name = {c["name"]: c for c in data["constituencies"]}
        yorks = by_name.get("Richmond (Yorks)")
        if yorks is None:
            continue
        surrey_names = [
            n
            for n in by_name
            if "richmond" in n.lower()
            and ("surrey" in n.lower() or "thames" in n.lower() or "barnes" in n.lower())
        ]
        assert yorks.get("q") is not None
        assert yorks["r"] >= -30, (
            f"{eid}: Richmond (Yorks) too far south (r={yorks['r']})"
        )
        for sname in surrey_names:
            s = by_name[sname]
            if s.get("q") is None:
                continue
            assert (yorks["q"], yorks["r"]) != (s["q"], s["r"]), (
                f"{eid}: Richmond (Yorks) collocated with {sname}"
            )
            assert abs(yorks["r"] - s["r"]) >= 15, (
                f"{eid}: Richmond (Yorks) ({yorks['q']},{yorks['r']}) "
                f"too close to {sname} ({s['q']},{s['r']})"
            )


def test_hull_north_beside_west() -> None:
    data = load("1983")
    by_name = {c["name"]: c for c in data["constituencies"]}
    north = by_name["Hull North"]
    west = by_name["Hull West"]
    assert (north["q"], north["r"]) in neighbors(west["q"], west["r"]), (
        f"Hull North ({north['q']},{north['r']}) not adjacent to Hull West"
    )


def test_england_scaffold_fill() -> None:
    """Historic England should pack onto the 2024 mainland; only boundary-reform gaps remain."""
    data = load("1983")
    hex2024 = json.loads(
        (ROOT / "data" / "hex" / "uk-constituencies-2024.hexjson").read_text()
    )
    england_scaffold = {
        (cell["q"], cell["r"])
        for cell in hex2024["hexes"].values()
        if str(cell.get("region") or "").startswith("E")
    }
    england_seats = [
        c
        for c in data["constituencies"]
        if c.get("nation") == "england" and c.get("q") is not None
    ]
    on_scaffold = sum(
        1 for c in england_seats if (c["q"], c["r"]) in england_scaffold
    )
    empty = england_scaffold - {(c["q"], c["r"]) for c in england_seats}
    occupied = {(c["q"], c["r"]) for c in england_seats}
    surrounded = sum(
        1
        for coord in empty
        if sum(1 for n in neighbors(*coord) if n in occupied) >= 5
    )
    off_scaffold = len(england_seats) - on_scaffold
    assert off_scaffold <= 10, (
        f"{off_scaffold} England seats still off the 2024 scaffold "
        "(expected overflow pins only)"
    )
    assert len(empty) <= 32, (
        f"{len(empty)} empty England scaffold cells "
        "(~20 from boundary reform plus coast/periphery; interior holes cascaded outward)"
    )
    assert surrounded <= 4, (
        f"{surrounded} interior England scaffold holes still surrounded by 5+ neighbours"
    )


def test_few_surrounded_scaffold_gaps() -> None:
    """Empty 2024-only cells deep inside England should mostly be filled."""
    import importlib.util

    data = load("1983")
    hex2024 = json.loads(
        (ROOT / "data" / "hex" / "uk-constituencies-2024.hexjson").read_text()
    )
    occupied = {
        (c["q"], c["r"])
        for c in data["constituencies"]
        if c.get("nation") == "england" and c.get("q") is not None
    }
    surrounded = 0
    for cell in hex2024["hexes"].values():
        if not str(cell.get("region") or "").startswith("E"):
            continue
        coord = (cell["q"], cell["r"])
        if coord in occupied:
            continue
        if sum(1 for n in neighbors(*coord) if n in occupied) >= 5:
            surrounded += 1
    assert surrounded <= 4, f"{surrounded} empty England cells still have 5+ neighbours"


def test_landmark_adjacent_gaps() -> None:
    """2024-only hexes beside well-known seats should mostly be filled."""
    data = load("1983")
    hex2024 = json.loads(
        (ROOT / "data" / "hex" / "uk-constituencies-2024.hexjson").read_text()
    )
    occupied = {
        (c["q"], c["r"])
        for c in data["constituencies"]
        if c.get("nation") == "england" and c.get("q") is not None
    }
    landmarks = [
        "Gloucester",
        "Coventry North West",
        "Mid Bedfordshire",
        "Hertford and Stortford",
        "Cambridge",
        "Amber Valley",
        "Stafford",
    ]
    for lm in landmarks:
        cell = next(c for c in hex2024["hexes"].values() if c["n"] == lm)
        coord = (cell["q"], cell["r"])
        empty_nbs = sum(
            1 for n in neighbors(*coord) if n not in occupied
        )
        assert empty_nbs <= 2, f"{lm} still has {empty_nbs} empty neighbours"


def test_manchester_gorton_in_north_west() -> None:
    data = load("1983")
    gorton = next(c for c in data["constituencies"] if "Gorton" in c["name"])
    assert gorton["r"] > -30, f"Manchester Gorton too far south/east at ({gorton['q']},{gorton['r']})"
    assert 52 <= gorton["q"] <= 58, f"Manchester Gorton q out of band ({gorton['q']})"


def test_central_london_south_of_edmonton() -> None:
    data = load("1983")
    by_name = {c["name"]: c for c in data["constituencies"]}
    edmonton = by_name["Edmonton"]
    city = next(
        c for c in data["constituencies"] if "westminster south" in c["name"].lower()
    )
    west = by_name["Westminster North"]
    assert city["r"] < edmonton["r"], "City of London should sit south of Edmonton on the hex map"
    assert west["r"] < edmonton["r"], "Westminster North should sit south of Edmonton"


def test_bethnal_green_spelling() -> None:
    """HoC scrape typos must not appear in displayed constituency names."""
    bad_fragments = (
        "bethnall",
        "morcambe",
        "mordern",
        "kirkaldy",
        "rydale",
        "burtwood",
        "worcestshire",
        "hillborough",
        "lunesdale",
        "hertfordhire",
        "llanelly",
    )
    for eid in (
        "1945",
        "1950",
        "1951",
        "1955",
        "1959",
        "1964",
        "1966",
        "1970",
        "feb1974",
        "oct1974",
        "1979",
        "1983",
        "1987",
        "1992",
        "1997",
        "2001",
        "2005",
        "2010",
        "2015",
        "2017",
        "2019",
        "2024",
    ):
        path = ROOT / "data" / "constituencies" / f"{eid}.json"
        if not path.exists():
            continue
        data = load(eid)
        for c in data["constituencies"]:
            lower = c["name"].lower()
            for bad in bad_fragments:
                assert bad not in lower, (
                    f"{eid}: '{c['name']}' still contains typo fragment '{bad}'"
                )
            if re.search(r"\bcaernarvon\b(?!shire)", lower):
                assert False, f"{eid}: '{c['name']}' should use Caernarfon spelling"
            if "coln valley" in lower:
                assert False, f"{eid}: '{c['name']}' should be Colne Valley"
    data83 = load("1983")
    names = [c["name"] for c in data83["constituencies"] if "bethnal" in c["name"].lower()]
    assert names, "expected Bethnal Green seat on 1983 map"


def _load_import_module():
    path = ROOT / "scripts" / "import-historical-hexmaps.py"
    spec = importlib.util.spec_from_file_location("import_hex", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_england_geo_placement_audit() -> None:
    """No severe misplacements; the original audit batch must be clear."""
    mod = _load_import_module()
    by_name, scaffold_coords, *_rest, england_coords = mod.build_scaffold()
    geo_lookup = mod.load_geo_lookup()
    cell_geos = mod.build_cell_geos(geo_lookup, scaffold_coords)
    data = load("1983")
    issues = mod.audit_england_placements(
        data["constituencies"],
        by_name,
        geo_lookup,
        cell_geos,
        england_coords,
    )
    by_name_issues = {row["name"]: row for row in issues}
    severe = [
        row
        for row in issues
        if row["delta"] >= 1.0 or row["cur_d"] >= 1.2 or (row["anchor_hex"] or 0) > 10
    ]
    assert not severe, (
        f"{len(severe)} severe England misplacements: "
        + ", ".join(f"{r['name']} Δ={r['delta']:.2f}" for r in severe[:8])
    )
    original_batch = [
        "Norfolk North West",
        "Norfolk Mid",
        "Cornwall South East",
        "Birmingham Sparkbrook",
        "Surbiton",
        "Poole",
        "Thanet North",
        "Sheffield Brightside",
        "Staffordshire South East",
        "Newbury",
        "Kensington",
        "South Hams",
        "Lindsey East",
        "Denton and Reddish",
        "Hastings & Rye",
        "Halesowen & Stourbridge",
        "Cornwall North",
        "Plymouth Devonport",
    ]
    still_bad = []
    for seat in original_batch:
        row = by_name_issues.get(seat)
        if row is None:
            alt = seat.replace("&", "and")
            row = next((r for n, r in by_name_issues.items() if alt in n), None)
        if row and (row["delta"] >= 0.5 or row["cur_d"] >= 0.8):
            still_bad.append(f"{row['name']} Δ={row['delta']:.2f}")
    assert not still_bad, f"Original audit batch still flagged: {', '.join(still_bad)}"


def test_birmingham_small_heath_in_birmingham() -> None:
    data = load("1983")
    seat = next(c for c in data["constituencies"] if "Small Heath" in c["name"])
    sparkbrook = next(c for c in data["constituencies"] if c["name"] == "Birmingham Sparkbrook")
    assert seat["r"] > -38, f"Small Heath too far south at ({seat['q']},{seat['r']})"
    assert 53 <= seat["q"] <= 57
    assert abs(seat["r"] - sparkbrook["r"]) <= 2, "Small Heath should sit near Sparkbrook"


def test_denton_and_reddish_in_north_west() -> None:
    data = load("1983")
    denton = next(c for c in data["constituencies"] if "Denton" in c["name"])
    assert denton["r"] > -30, f"Denton & Reddish too far south/east at ({denton['q']},{denton['r']})"
    assert 52 <= denton["q"] <= 58


def test_display_name_normalisation() -> None:
    data = load("1983")
    names = {c["name"] for c in data["constituencies"]}
    assert "Bishop Auckland" in names
    assert "Bethnal Green and Stepney" in names
    assert "Denton and Reddish" in names
    assert not any(" & " in n for n in names if n in {
        "Holborn and St Pancras South",
        "Oxfordshire West and Abingdon",
        "Welwyn and Hatfield",
        "Ellesmere Port and Neston",
        "Denton and Reddish",
    })


def test_west_bromwich_west_near_black_country() -> None:
    data = load("1983")
    by_name = {c["name"]: c for c in data["constituencies"]}
    west = by_name["West Bromwich West"]
    east = by_name["West Bromwich East"]
    assert west["r"] > -35, f"West Bromwich West too far south at ({west['q']},{west['r']})"
    assert (west["q"], west["r"]) in neighbors(east["q"], east["r"]), (
        "West Bromwich West should sit beside West Bromwich East"
    )
    assert 51 <= west["q"] <= 56, f"West Bromwich West q out of West Midlands band ({west['q']})"


def test_reading_east_inland_not_by_gosport() -> None:
    data = load("1983")
    by_name = {c["name"]: c for c in data["constituencies"]}
    reading = by_name["Reading East"]
    gosport = by_name["Gosport"]
    reading_west = by_name["Reading West"]
    assert reading["r"] > -41, f"Reading East too far south at ({reading['q']},{reading['r']})"
    assert (reading["q"], reading["r"]) not in neighbors(gosport["q"], gosport["r"])
    assert (reading["q"], reading["r"]) in neighbors(
        reading_west["q"], reading_west["r"]
    ), f"Reading East {reading['q']},{reading['r']} should sit beside Reading West {reading_west['q']},{reading_west['r']}"


def test_cambridge_internal_gaps_filled() -> None:
    """Cambridgeshire cluster should occupy the St Neots / NW Cambs scaffold cells."""
    data = load("1983")
    by_name = {c["name"]: c for c in data["constituencies"]}
    cambridge = by_name["Cambridge"]
    south_west = by_name["Cambridgeshire South West"]
    assert (south_west["q"], south_west["r"]) == (64, -31), (
        f"Cambridgeshire SW should sit in St Neots cell, got ({south_west['q']},{south_west['r']})"
    )
    assert cambridge["q"] in (64, 65) and cambridge["r"] == -30
    assert abs(cambridge["q"] - south_west["q"]) <= 1


def test_1974_abolished_seats_near_wikipedia_successors() -> None:
    """234 seats abolished/renamed by 1983 should sit near their successor cells."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "import_historical_hexmaps",
        ROOT / "scripts" / "import-historical-hexmaps.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    successor_map = mod.load_wikipedia_successor_map()
    ref = mod.load_reference_placements("1983")
    canonical = sorted(successor_map.keys())
    names83 = {c["name"] for c in load("1983")["constituencies"]}

    def find_seat(data: dict, canonical_key: str) -> dict | None:
        alt_keys = {canonical_key}
        if canonical_key == "montgomeryshire":
            alt_keys.add("montgomery")
        for c in data["constituencies"]:
            if mod.historic_norm(c["name"]) in alt_keys:
                return c
        for src_key, display in mod.DISPLAY_NAMES.items():
            if src_key in alt_keys:
                for c in data["constituencies"]:
                    if mod.historic_norm(c["name"]) == mod.historic_norm(display):
                        return c
        return None

    assert len(canonical) == 234

    for eid in ("feb1974", "oct1974", "1979"):
        data = load(eid)
        too_far: list[str] = []
        unresolved: list[str] = []
        missing: list[str] = []
        for key in canonical:
            c = find_seat(data, key)
            if c is None:
                missing.append(key)
                continue
            if c["name"] in names83:
                # Renamed to match 1983 before this election (e.g. Montgomeryshire → Montgomery).
                continue
            assert c.get("q") is not None, f"{eid}: {key} has no hex"
            successors = mod.successors_for_seat(c["name"], successor_map) or []
            anchors: list[tuple[int, int]] = []
            for succ in successors:
                coord = mod.resolve_reference_placement(succ, ref)
                if coord:
                    anchors.append(coord)
            if not anchors:
                unresolved.append(key)
                continue
            seat = (c["q"], c["r"])
            best = min(mod.hex_distance(*seat, *anchor) for anchor in anchors)
            if best > 9:
                too_far.append(f"{key} (d={best})")
        assert not missing, f"{eid}: missing canonical seats {missing[:8]}"
        assert not unresolved, f"{eid}: no 1983 successor resolved for {unresolved[:8]}"
        assert len(too_far) <= 2, (
            f"{eid}: seats far from Wikipedia successors after solid packing: {too_far[:8]}"
        )


def test_1955_abolished_seats_near_wikipedia_successors() -> None:
    """117 seats without exact feb1974 names should sit near their 1974 successor cells."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "import_historical_hexmaps",
        ROOT / "scripts" / "import-historical-hexmaps.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    successor_map = mod.load_wikipedia_successor_map("feb1974")
    ref = mod.load_reference_placements("feb1974")
    names55 = {c["name"] for c in load("1955")["constituencies"]}

    def has_direct_seed(name: str) -> bool:
        for key in mod.reference_keys(name):
            if key in ref:
                return True
        return False

    canonical = sorted(successor_map.keys())
    assert len(canonical) >= 110

    data = load("1955")
    too_far: list[str] = []
    unresolved: list[str] = []
    for key in canonical:
        seat = next(
            (c for c in data["constituencies"] if mod.historic_norm(c["name"]) == key),
            None,
        )
        if seat is None:
            continue
        if has_direct_seed(seat["name"]):
            continue
        assert seat.get("q") is not None, f"1955: {key} has no hex"
        successors = mod.successors_for_seat(seat["name"], successor_map) or []
        anchors: list[tuple[int, int]] = []
        for succ in successors:
            coord = mod.resolve_reference_placement(
                succ, ref, successor_name_aliases=mod.SUCCESSOR_NAME_ALIASES_1974
            )
            if coord:
                anchors.append(coord)
        if not successors:
            continue
        if not anchors:
            unresolved.append(key)
            continue
        seat_coord = (seat["q"], seat["r"])
        best = min(mod.hex_distance(*seat_coord, *anchor) for anchor in anchors)
        if best > 9:
            too_far.append(f"{key} (d={best})")
    assert len(unresolved) <= 8, f"1955: no feb1974 successor resolved for {unresolved[:10]}"
    assert len(too_far) <= 5, (
        f"1955: seats far from Wikipedia successors after packing: {too_far[:10]}"
    )


def main() -> int:
    tests = [
        test_seat_counts,
        test_hex_match_rates,
        test_pre1974_england_scaffold_fill,
        test_1974_shared_names_mostly_on_scaffold,
        test_1974_england_scaffold_fill,
        test_1974_few_surrounded_scaffold_gaps,
        test_1974_no_surrounded_map_holes,
        test_1974_landmark_adjacent_gaps,
        test_harwich_connected_to_mainland,
        test_1974_abolished_seats_near_wikipedia_successors,
        test_1955_abolished_seats_near_wikipedia_successors,
        test_feb_and_oct_1974_same_hex_layout,
        test_ynys_mon_matches_2024_scaffold,
        test_western_isles_in_scotland,
        test_scottish_seats_stay_in_scotland,
        test_overflow_seats_beside_anchors,
        test_st_ives_beside_cornwall,
        test_totnes_connected_to_mainland,
        test_workington_beside_copeland,
        test_liverpool_exchange_in_merseyside,
        test_inner_london_boundary_seats,
        test_pre1974_landmark_misplaced_seats,
        test_pre1974_england_relative_placements,
        test_southwark_lewisham_in_inner_london,
        test_richmond_yorks_not_in_surrey,
        test_hull_north_beside_west,
        test_manchester_gorton_in_north_west,
        test_central_london_south_of_edmonton,
        test_bethnal_green_spelling,
        test_england_geo_placement_audit,
        test_birmingham_small_heath_in_birmingham,
        test_denton_and_reddish_in_north_west,
        test_display_name_normalisation,
        test_west_bromwich_west_near_black_country,
        test_reading_east_inland_not_by_gosport,
        test_cambridge_internal_gaps_filled,
        test_england_scaffold_fill,
        test_few_surrounded_scaffold_gaps,
        test_landmark_adjacent_gaps,
        test_milton_keynes_adjacent,
        test_ni_parties_in_inset,
        test_alliance_mapped_to_libdem,
    ]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"OK  {test.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {test.__name__}: {exc}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
