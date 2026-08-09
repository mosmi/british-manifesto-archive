#!/usr/bin/env python3
"""Build European Parliament regional seat JSON from Commons Library CBP 8600 data.

Reads:
  data/sources/commons-library/CBP-8600-2019.xlsx  (UK MEPs + Vote share by LA)

Writes:
  data/devolved/euro/regions/2019.json

Validates that regional seat totals match data/devolved/euro/2019.json.
"""

from __future__ import annotations

import json
import re
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
XLSX = ROOT / "data/sources/commons-library/CBP-8600-2019.xlsx"
ELECTION_JSON = ROOT / "data/devolved/euro/2019.json"
OUT = ROOT / "data/devolved/euro/regions/2019.json"

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_NS = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}

# CBP region codes → site region metadata (display order roughly N→S)
REGION_META = {
    "NE": {"id": "north-east", "name": "North East", "ons": "North East"},
    "NW": {"id": "north-west", "name": "North West", "ons": "North West"},
    "Y&H": {"id": "yorkshire-humber", "name": "Yorkshire and the Humber", "ons": "Yorkshire and The Humber"},
    "EM": {"id": "east-midlands", "name": "East Midlands", "ons": "East Midlands"},
    "WM": {"id": "west-midlands", "name": "West Midlands", "ons": "West Midlands"},
    "E": {"id": "east-of-england", "name": "East of England", "ons": "Eastern"},
    "L": {"id": "london", "name": "London", "ons": "London"},
    "SE": {"id": "south-east", "name": "South East", "ons": "South East"},
    "SW": {"id": "south-west", "name": "South West", "ons": "South West"},
    "W": {"id": "wales", "name": "Wales", "ons": "Wales"},
    "S": {"id": "scotland", "name": "Scotland", "ons": "Scotland"},
    "NI": {"id": "northern-ireland", "name": "Northern Ireland", "ons": "Northern Ireland"},
}

REGION_ORDER = list(REGION_META.keys())

# LA sheet Region column → CBP code
LA_REGION_TO_CODE = {
    "North East": "NE",
    "North West": "NW",
    "Yorkshire and the Humber": "Y&H",
    "East Midlands": "EM",
    "West Midlands": "WM",
    "East": "E",
    "London": "L",
    "South East": "SE",
    "South West": "SW",
    "Wales": "W",
    "Scotland": "S",
}

# CBP party slug → site party id
PARTY_MAP = {
    "brexit": "reform",
    "ld": "libdem",
    "labour": "labour",
    "green": "green",
    "con": "conservative",
    "pc": "plaid",
    "snp": "snp",
    "sf": "sinnfein",
    "alliance": "alliance",
    "dup": "dup",
}

# LA sheet columns (vote share fractions) → site party id
LA_PARTY_COLS = {
    "C": "reform",      # Brexit
    "D": "libdem",
    "E": "labour",
    "F": "green",
    "G": "conservative",
    "H": "ukip",
    "I": "nat",          # SNP in Scotland / Plaid in Wales — split below
}

# Northern Ireland first-preference shares (CBP 8600 / election JSON)
NI_RESULTS_PCT = {
    "sinnfein": 22.2,
    "dup": 21.8,
    "alliance": 18.5,
    "sdlp": 13.7,
    "uup": 9.3,
}

PARTY_LABELS_2019 = {
    "reform": "Brexit Party",
}


def colrow(cellref: str):
    m = re.match(r"([A-Z]+)(\d+)", cellref)
    return m.group(1), int(m.group(2))


def load_xlsx_sheets(path: Path) -> dict[str, dict[int, dict[str, str]]]:
    with zipfile.ZipFile(path) as z:
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        sheets = []
        for sh in wb.findall("m:sheets/m:sheet", NS):
            name = sh.attrib.get("name")
            rid = sh.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
            sheets.append((name, rid))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        rid_to_target = {el.attrib["Id"]: el.attrib["Target"] for el in rels}
        ss = []
        root = ET.fromstring(z.read("xl/sharedStrings.xml"))
        for si in root.findall("m:si", NS):
            texts = [t.text or "" for t in si.findall(".//m:t", NS)]
            ss.append("".join(texts))

        out = {}
        for name, rid in sheets:
            target = rid_to_target[rid]
            if not target.startswith("xl/"):
                target = "xl/" + target
            sheet_root = ET.fromstring(z.read(target))
            rows: dict[int, dict[str, str]] = {}
            for c in sheet_root.findall(".//m:c", NS):
                ref = c.attrib.get("r")
                if not ref:
                    continue
                col, row = colrow(ref)
                v = c.find("m:v", NS)
                if v is None:
                    continue
                val = v.text
                if c.attrib.get("t") == "s":
                    val = ss[int(val)]
                rows.setdefault(row, {})[col] = val
            out[name] = rows
        return out


def site_party(cbp_party: str) -> str:
    key = (cbp_party or "").strip().lower()
    if key not in PARTY_MAP:
        raise ValueError(f"Unknown CBP party slug: {cbp_party!r}")
    return PARTY_MAP[key]


def party_label(party_id: str) -> str | None:
    return PARTY_LABELS_2019.get(party_id)


def parse_meps(rows: dict[int, dict[str, str]]):
    meps_by_region: dict[str, list[dict]] = defaultdict(list)
    for r, cols in rows.items():
        if r == 1:
            continue
        name = (cols.get("B") or "").strip()
        if not name:
            continue
        party = site_party(cols.get("C") or "")
        code = (cols.get("D") or "").strip()
        if code not in REGION_META:
            raise ValueError(f"Unknown region code {code!r} for MEP {name}")
        order = int(float(cols.get("A") or 0))
        entry = {
            "name": name,
            "party": party,
            "order": order,
        }
        label = party_label(party)
        if label:
            entry["partyLabel"] = label
        meps_by_region[code].append(entry)
    for code, members in meps_by_region.items():
        members.sort(key=lambda m: m["order"])
    return meps_by_region


def aggregate_la_shares(rows: dict[int, dict[str, str]]):
    """Weighted GB regional vote shares from LA sheet (share × total votes)."""
    # region_code -> party -> vote estimate; region -> total votes / electorate
    votes = defaultdict(lambda: defaultdict(float))
    totals = defaultdict(float)
    electorate = defaultdict(float)

    for r, cols in rows.items():
        if r == 1:
            continue
        la_region = cols.get("L")
        code = LA_REGION_TO_CODE.get(la_region or "")
        if not code:
            continue
        try:
            total = float(cols.get("K") or 0)
            elect = float(cols.get("M") or 0)
        except ValueError:
            continue
        if total <= 0:
            continue
        totals[code] += total
        electorate[code] += elect
        for col, party in LA_PARTY_COLS.items():
            try:
                share = float(cols.get(col) or 0)
            except ValueError:
                continue
            est = share * total
            if party == "nat":
                if code == "S":
                    votes[code]["snp"] += est
                elif code == "W":
                    votes[code]["plaid"] += est
                # ignore elsewhere (zeros)
            else:
                votes[code][party] += est

    out = {}
    for code, party_votes in votes.items():
        t = totals[code] or 1.0
        out[code] = {
            "pct": {p: round(100.0 * v / t, 1) for p, v in sorted(party_votes.items(), key=lambda x: -x[1])},
            "turnout": round(100.0 * t / electorate[code], 1) if electorate[code] else None,
        }
    return out


def build_region(code: str, members: list[dict], la_agg: dict) -> dict:
    meta = REGION_META[code]
    seat_counts = Counter(m["party"] for m in members)
    results = []
    if code == "NI":
        for party, seats in seat_counts.items():
            row = {"party": party, "seats": seats}
            if party in NI_RESULTS_PCT:
                row["pct"] = NI_RESULTS_PCT[party]
            label = party_label(party)
            if label:
                row["partyLabel"] = label
            results.append(row)
        turnout = 45.0  # NI turnout, CBP 8600
    else:
        pct_map = (la_agg.get(code) or {}).get("pct") or {}
        for party, seats in seat_counts.items():
            row = {"party": party, "seats": seats}
            if party in pct_map:
                row["pct"] = pct_map[party]
            label = party_label(party)
            if label:
                row["partyLabel"] = label
            results.append(row)
        turnout = (la_agg.get(code) or {}).get("turnout")

    # Commons Library waffle order: most seats first, then higher vote share
    results.sort(key=lambda r: (-r["seats"], -(r.get("pct") or 0), r["party"]))

    region = {
        "id": meta["id"],
        "code": code,
        "name": meta["name"],
        "seats": len(members),
        "members": members,
        "results": results,
    }
    if turnout is not None:
        region["turnout"] = turnout
    return region


def main():
    if not XLSX.exists():
        raise SystemExit(f"Missing source spreadsheet: {XLSX}")

    sheets = load_xlsx_sheets(XLSX)
    meps = parse_meps(sheets["UK MEPs"])
    la_agg = aggregate_la_shares(sheets["Vote share by LA"])

    regions = []
    for code in REGION_ORDER:
        if code not in meps:
            raise SystemExit(f"No MEPs for region {code}")
        regions.append(build_region(code, meps[code], la_agg))

    total_seats = sum(r["seats"] for r in regions)
    party_totals = Counter()
    for r in regions:
        for m in r["members"]:
            party_totals[m["party"]] += 1

    election = json.loads(ELECTION_JSON.read_text())
    expected = {row["party"]: row["seats"] for row in election["parliament"]["results"] if row["seats"] > 0}
    if total_seats != election["parliament"]["totalSeats"]:
        raise SystemExit(f"Seat total {total_seats} != election total {election['parliament']['totalSeats']}")
    for party, seats in expected.items():
        if party_totals.get(party, 0) != seats:
            raise SystemExit(f"Party {party}: map has {party_totals.get(party, 0)} seats, election JSON has {seats}")

    doc = {
        "year": 2019,
        "source": {
            "label": "House of Commons Library — European Parliament Elections 2019 (CBP 8600)",
            "url": "https://commonslibrary.parliament.uk/research-briefings/cbp-8600/",
            "file": "data/sources/commons-library/CBP-8600-2019.xlsx",
        },
        "regions": regions,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {OUT} ({total_seats} seats, {len(regions)} regions)")
    print("Party totals:", dict(party_totals.most_common()))


if __name__ == "__main__":
    main()
