#!/usr/bin/env python3
"""Build European Parliament regional seat JSON for PR-era elections (1999–2014).

Reads Commons Library research-paper PDFs under
  data/sources/european-parliament-elections/commons-library/

Writes:
  data/devolved/euro/regions/{1999,2004,2009,2014}.json

Validates regional seat totals against data/devolved/euro/<year>.json.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/sources/european-parliament-elections/commons-library"
OUT_DIR = ROOT / "data/devolved/euro/regions"

REGION_META = {
    "north-east": {"code": "NE", "name": "North East"},
    "north-west": {"code": "NW", "name": "North West"},
    "yorkshire-humber": {"code": "Y&H", "name": "Yorkshire and the Humber"},
    "east-midlands": {"code": "EM", "name": "East Midlands"},
    "west-midlands": {"code": "WM", "name": "West Midlands"},
    "east-of-england": {"code": "E", "name": "East of England"},
    "london": {"code": "L", "name": "London"},
    "south-east": {"code": "SE", "name": "South East"},
    "south-west": {"code": "SW", "name": "South West"},
    "wales": {"code": "W", "name": "Wales"},
    "scotland": {"code": "S", "name": "Scotland"},
    "northern-ireland": {"code": "NI", "name": "Northern Ireland"},
}

REGION_ORDER = list(REGION_META.keys())

REGION_ALIASES = {
    "north east": "north-east",
    "north west": "north-west",
    "yorkshire and the humber": "yorkshire-humber",
    "yorkshire & the humber": "yorkshire-humber",
    "yorks & humber": "yorkshire-humber",
    "yorks and humber": "yorkshire-humber",
    "east midlands": "east-midlands",
    "west midlands": "west-midlands",
    "east": "east-of-england",
    "eastern": "east-of-england",
    "east of england": "east-of-england",
    "london": "london",
    "south east": "south-east",
    "south west": "south-west",
    "wales": "wales",
    "scotland": "scotland",
    "northern ireland": "northern-ireland",
}

PARTY_ALIASES = {
    "conservative": "conservative",
    "labour": "labour",
    "liberal democrat": "libdem",
    "liberal democrats": "libdem",
    "ukip": "ukip",
    "uk independence": "ukip",
    "uk independence party": "ukip",
    "green": "green",
    "snp": "snp",
    "scottish national": "snp",
    "plaid cymru": "plaid",
    "plaid": "plaid",
    "bnp": "bnp",
    "british national party": "bnp",
    "sinn fein": "sinnfein",
    "sinn féin": "sinnfein",
    "dup": "dup",
    "democratic unionist": "dup",
    "uup": "uup",
    "ulster unionist": "uup",
    "ulster unionists": "uup",
    "sdlp": "sdlp",
}

SOURCES = {
    2014: {
        "pdf": "RP14-32.pdf",
        "label": "House of Commons Library — European Parliament Elections 2014 (RP14-32)",
        "url": "https://commonslibrary.parliament.uk/research-briefings/rp14-32/",
        "file": "data/sources/european-parliament-elections/commons-library/RP14-32.pdf",
        "mep_marker": "2.8 UK MEPs by party",
        "share_parties": ["conservative", "labour", "libdem", "ukip", "nat", "green", "bnp", "other"],
    },
    2009: {
        "pdf": "RP09-53.pdf",
        "label": "House of Commons Library — European Parliament Elections 2009 (RP09-53)",
        "url": "https://commonslibrary.parliament.uk/research-briefings/rp09-53/",
        "file": "data/sources/european-parliament-elections/commons-library/RP09-53.pdf",
        "mep_marker": "Appendix 2\n\nUK MEPs by party",
        "share_parties": ["conservative", "ukip", "labour", "libdem", "nat", "green", "bnp", "other"],
    },
    2004: {
        "pdf": "RP04-50.pdf",
        "label": "House of Commons Library — European Parliament Elections 2004 (RP04-50)",
        "url": "https://commonslibrary.parliament.uk/research-briefings/rp04-50/",
        "file": "data/sources/european-parliament-elections/commons-library/RP04-50.pdf",
        "mep_marker": "Appendix table 3: UK MEPs by party\n\n",
        "share_parties": ["conservative", "labour", "libdem", "ukip", "nat", "other"],
        # Green folded into "Others" in the GB summary table — regional chapter shares
        "green_pct": {"london": 8.4, "south-east": 7.9},
    },
    1999: {
        "pdf": "RP99-64.pdf",
        "label": "House of Commons Library — Elections to the European Parliament June 1999 (RP99-64)",
        "url": "https://commonslibrary.parliament.uk/research-briefings/rp99-64/",
        "file": "data/sources/european-parliament-elections/commons-library/RP99-64.pdf",
        "share_parties": ["conservative", "labour", "libdem", "nat", "green", "ukip", "other"],
    },
}

# Turnout % by region (from RP regional totals / Table 3 / NI narrative)
TURNOUT = {
    2014: {
        "north-east": 30.9, "north-west": 33.3, "yorkshire-humber": 33.5,
        "east-midlands": 33.2, "west-midlands": 33.1, "east-of-england": 36.0,
        "london": 40.1, "south-east": 36.3, "south-west": 36.9,
        "wales": 32.0, "scotland": 33.4, "northern-ireland": 51.0,
    },
    2009: {
        "north-east": 30.4, "north-west": 31.5, "yorkshire-humber": 32.3,
        "east-midlands": 36.9, "west-midlands": 34.7, "east-of-england": 37.3,
        "london": 33.3, "south-east": 37.3, "south-west": 38.6,
        "wales": 30.4, "scotland": 28.5, "northern-ireland": 42.4,
    },
    2004: {
        "north-east": 40.8, "north-west": 40.8, "yorkshire-humber": 42.0,
        "east-midlands": 43.5, "west-midlands": 35.8, "east-of-england": 36.4,
        "london": 37.3, "south-east": 36.6, "south-west": 37.7,
        "wales": 41.4, "scotland": 30.7, "northern-ireland": 51.2,
    },
    1999: {
        "north-east": 19.5, "north-west": 19.5, "yorkshire-humber": 19.6,
        "east-midlands": 22.6, "west-midlands": 20.9, "east-of-england": 24.5,
        "london": 23.0, "south-east": 24.7, "south-west": 27.5,
        "wales": 28.1, "scotland": 24.7, "northern-ireland": 57.0,
    },
}

# NI STV seat-winners (first-preference % from site election JSON / RP)
NI_MEMBERS = {
    2014: [
        ("Martina Anderson", "sinnfein", 1),
        ("Diane Dodds", "dup", 2),
        ("Jim Nicholson", "uup", 3),
    ],
    2009: [
        ("Bairbre de Brún", "sinnfein", 1),
        ("Jim Nicholson", "uup", 2),
        ("Diane Dodds", "dup", 3),
    ],
    2004: [
        ("Jim Allister", "dup", 1),
        ("Bairbre de Brún", "sinnfein", 2),
        ("Jim Nicholson", "uup", 3),
    ],
    1999: [
        ("Ian Paisley", "dup", 1),
        ("John Hume", "sdlp", 2),
        ("Jim Nicholson", "uup", 3),
    ],
}

ROW_ALIASES = {
    "north east": "north-east",
    "north west": "north-west",
    "yorks & humber": "yorkshire-humber",
    "yorks and humber": "yorkshire-humber",
    "yorkshire & the humber": "yorkshire-humber",
    "yorkshire and the humber": "yorkshire-humber",
    "east midlands": "east-midlands",
    "west midlands": "west-midlands",
    "east": "east-of-england",
    "eastern": "east-of-england",
    "london": "london",
    "south east": "south-east",
    "south west": "south-west",
    "wales": "wales",
    "scotland": "scotland",
}


def pdf_text(pdf_name: str) -> str:
    path = SRC / pdf_name
    return subprocess.check_output(["pdftotext", "-layout", str(path), "-"], text=True)


def norm_region(name: str) -> str | None:
    key = re.sub(r"\s+", " ", name.strip().lower())
    return REGION_ALIASES.get(key)


def norm_party(name: str) -> str | None:
    key = re.sub(r"\s+", " ", name.strip().lower())
    key = key.replace("é", "e").replace("ó", "o")
    if key in PARTY_ALIASES:
        return PARTY_ALIASES[key]
    for alias, pid in PARTY_ALIASES.items():
        if key.startswith(alias):
            return pid
    return None


def parse_mep_list(text: str, marker: str) -> list[dict]:
    """Parse 'Name … Region … Round' blocks under party headings."""
    idx = text.find(marker)
    if idx < 0:
        # try last occurrence of shortened marker
        short = marker.split("\n")[0]
        idx = text.rfind(short)
    if idx < 0:
        raise ValueError(f"MEP marker not found: {marker!r}")

    chunk = text[idx : idx + 12000]
    # stop at next major section
    for stop in (
        "\n3  ",
        "\n3\t",
        "\nII ",
        "\nOf the ",
        "\nRESEARCH PAPER",
        "Results across the European Union",
    ):
        j = chunk.find(stop, 200)
        if j > 0:
            chunk = chunk[:j]
            break

    party = None
    members: list[dict] = []
    party_header = re.compile(
        r"^(Conservative|Labour|Liberal Democrats?|UKIP|Green|BNP|SNP|"
        r"Plaid Cymru|Sinn Fein|Sinn Féin|DUP|UUP|Ulster Unionists?)\s*$",
        re.M | re.I,
    )
    # Name (possibly with title) + region + round number at end
    row_re = re.compile(
        r"^\s+(.+?)\s{2,}("
        + "|".join(
            re.escape(a)
            for a in sorted(REGION_ALIASES.keys(), key=len, reverse=True)
        )
        + r")\s+(\d+)\s*$",
        re.M | re.I,
    )

    for line in chunk.splitlines():
        ph = party_header.match(line.strip())
        if ph:
            party = norm_party(ph.group(1))
            continue
        if not party:
            continue
        m = row_re.match(line)
        if not m:
            continue
        name = re.sub(r"\s+", " ", m.group(1)).strip()
        # drop leading titles already in name; tidy
        name = name.replace("William (The Earl of) Dartmouth", "William Dartmouth")
        name = name.replace("William, Earl of Dartmouth", "William Dartmouth")
        name = re.sub(r"^Dr\s+", "", name)
        region = norm_region(m.group(2))
        if not region or region == "northern-ireland":
            # NI handled separately for consistent STV naming
            continue
        order = int(m.group(3))
        members.append(
            {"name": name, "party": party, "region": region, "order": order}
        )
    return members


def parse_1999_meps(text: str) -> list[dict]:
    """Parse Appendix 1 region×party grid for 1999."""
    idx = text.find("Appendix 1 - MEPs elected by region")
    if idx < 0:
        raise ValueError("1999 MEP appendix not found")
    chunk = text[idx : idx + 5000]
    # Fixed transcription from RP99-64 Appendix 1 (layout is multi-column and fragile)
    raw = {
        "east-midlands": [
            ("Roger Helmer", "conservative", 1),
            ("Mel Read", "labour", 2),
            ("William Newton-Dunn", "conservative", 3),
            ("Phillip Whitehead", "labour", 4),
            ("Christopher Heaton-Harris", "conservative", 5),
            ("Nicholas Clegg", "libdem", 6),
        ],
        "east-of-england": [
            ("Robert Sturdy", "conservative", 1),
            ("Eryl McNally", "labour", 2),
            ("Christopher Beazley", "conservative", 3),
            ("Richard Howitt", "labour", 4),
            ("Bashir Khanbhai", "conservative", 5),
            ("Andrew Duff", "libdem", 6),
            ("Geoffrey Van Orden", "conservative", 7),
            ("Jeffrey Titford", "ukip", 8),
        ],
        "london": [
            ("Theresa Villiers", "conservative", 1),
            ("Pauline Green", "labour", 2),
            ("John Bowis", "conservative", 3),
            ("Claude Moraes", "labour", 4),
            ("Nicholas Bethell", "conservative", 5),
            ("Robert Evans", "labour", 6),
            ("Charles Tannock", "conservative", 7),  # RP99-64 prints "Timothy"; Charles is correct
            ("Richard Balfe", "labour", 8),
            ("Sarah Ludford", "libdem", 9),
            ("Jean Lambert", "green", 10),
        ],
        "north-east": [
            ("Alan Donnelly", "labour", 1),
            ("Martin Callanan", "conservative", 2),
            ("Stephen Hughes", "labour", 3),
            ("Mo O'Toole", "labour", 4),
        ],
        "north-west": [
            ("Richard Inglewood", "conservative", 1),
            ("Arlene McCarthy", "labour", 2),
            ("Robert Atkins", "conservative", 3),
            ("Gary Titley", "labour", 4),
            ("David Sumberg", "conservative", 5),
            ("Terry Wynn", "labour", 6),
            ("Den Dover", "conservative", 7),
            ("Brian Simpson", "labour", 8),
            ("Jacqueline Foster", "conservative", 9),
            ("Chris Davies", "libdem", 10),
        ],
        "south-east": [
            ("James Provan", "conservative", 1),
            ("Roy Perry", "conservative", 2),
            ("Daniel Hannan", "conservative", 3),
            ("James Elles", "conservative", 4),
            ("Nirj Deva", "conservative", 5),
            ("Peter Skinner", "labour", 6),
            ("Mark Watts", "labour", 7),
            ("Emma Nicholson", "libdem", 8),
            ("Christopher Huhne", "libdem", 9),
            ("Caroline Lucas", "green", 10),
            ("Nigel Farage", "ukip", 11),
        ],
        "south-west": [
            ("Caroline Jackson", "conservative", 1),
            ("Giles Chichester", "conservative", 2),
            ("Alexander Stockton", "conservative", 3),
            ("Neil Parish", "conservative", 4),
            ("Glyn Ford", "labour", 5),
            ("Graham Watson", "libdem", 6),
            ("Michael Holmes", "ukip", 7),
        ],
        "west-midlands": [
            ("John Corrie", "conservative", 1),
            ("Philip Bushill-Matthews", "conservative", 2),
            ("John Harbour", "conservative", 3),
            ("Philip Bradbourn", "conservative", 4),
            ("Simon Murphy", "labour", 5),
            ("Michael Cashman", "labour", 6),
            ("Neena Gill", "labour", 7),
            ("Liz Lynne", "libdem", 8),
        ],
        "yorkshire-humber": [
            ("Edward McMillan-Scott", "conservative", 1),
            ("Linda McAvan", "labour", 2),
            ("Timothy Kirkhope", "conservative", 3),
            ("David Bowe", "labour", 4),
            ("Robert Goodwill", "conservative", 5),
            ("Richard Corbett", "labour", 6),
            ("Diana Wallis", "libdem", 7),
        ],
        "wales": [
            ("Glenys Kinnock", "labour", 1),
            ("Jonathan Evans", "conservative", 2),
            ("Jill Evans", "plaid", 3),
            ("Eluned Morgan", "labour", 4),
            ("Eurig Wyn", "plaid", 5),
        ],
        "scotland": [
            ("David Martin", "labour", 1),
            ("Ian Hudghton", "snp", 2),
            ("Struan Stevenson", "conservative", 3),
            ("William Miller", "labour", 4),
            ("Neil MacCormick", "snp", 5),
            ("John Purvis", "conservative", 6),
            ("Elspeth Attwooll", "libdem", 7),
            ("Catherine Stihler", "labour", 8),
        ],
    }
    # Prefer d’Hondt round order from Table 4 where it clarifies seat order
    members: list[dict] = []
    for rid, rows in raw.items():
        for name, party, order in rows:
            members.append(
                {"name": name, "party": party, "region": rid, "order": order}
            )
    _ = chunk  # retained for source-trace in reviews
    return members


def parse_share_table(text: str, parties: list[str]) -> dict[str, dict[str, float]]:
    """Parse 'Share of vote' regional matrix → {region: {party: pct}}.

    England rows often omit a blank SNP/PC column (no placeholder token). When the
    token count is one short and a `nat` column is expected, insert a None there
    for English regions only.
    """
    m = re.search(r"Share of vote(?:\s*\(%\))?\n", text)
    if not m:
        raise ValueError("Share of vote table not found")
    chunk = text[m.end() : m.end() + 2500]
    out: dict[str, dict[str, float]] = {}
    england = {
        "north-east", "north-west", "yorkshire-humber", "east-midlands",
        "west-midlands", "east-of-england", "london", "south-east", "south-west",
    }
    for line in chunk.splitlines():
        line = line.rstrip()
        if not line.strip():
            continue
        if line.strip().startswith("Great Britain"):
            break
        if line.strip().startswith("England"):
            continue
        rm = re.match(r"^\s*([A-Za-z &]+?)\s{2,}(.+)$", line)
        if not rm:
            continue
        rid = ROW_ALIASES.get(rm.group(1).strip().lower())
        if not rid:
            continue
        tokens = re.findall(r"\d+\.\d+%|\d+%|(?<!\d)0(?!\d)|—|-", rm.group(2))
        if tokens and tokens[-1] in ("100%", "100.0%"):
            tokens = tokens[:-1]
        vals: list[float | None] = []
        for tok in tokens:
            if tok in ("—", "-", "0"):
                vals.append(None)
            else:
                vals.append(float(tok.rstrip("%")))

        # Blank SNP/PC column omitted in some England rows (1999 / 2004)
        if "nat" in parties and rid in england and len(vals) == len(parties) - 1:
            nat_idx = parties.index("nat")
            vals = vals[:nat_idx] + [None] + vals[nat_idx:]

        if len(vals) < len(parties) - 1:
            continue
        vals = vals[: len(parties)]
        while len(vals) < len(parties):
            vals.append(None)

        pdata: dict[str, float] = {}
        for pid, val in zip(parties, vals):
            if val is None or pid in ("other", "nat"):
                continue
            pdata[pid] = val
        nat_idx = parties.index("nat") if "nat" in parties else -1
        if nat_idx >= 0 and nat_idx < len(vals) and vals[nat_idx] is not None:
            if rid == "scotland":
                pdata["snp"] = vals[nat_idx]
            elif rid == "wales":
                pdata["plaid"] = vals[nat_idx]
        out[rid] = pdata
    return out


def build_region(
    rid: str,
    members: list[dict],
    shares: dict[str, float],
    turnout: float | None,
    green_pct_override: dict[str, float] | None = None,
) -> dict:
    meta = REGION_META[rid]
    members_sorted = sorted(members, key=lambda m: m["order"])
    seat_counts: dict[str, int] = defaultdict(int)
    for m in members_sorted:
        seat_counts[m["party"]] += 1

    results = []
    # Commons Library waffle order: largest seat haul first, then vote share
    ordered_parties = sorted(
        seat_counts.keys(),
        key=lambda p: (-seat_counts[p], -(shares.get(p) or 0), p),
    )
    for party in ordered_parties:
        pct = shares.get(party)
        if pct is None and green_pct_override and party == "green":
            pct = green_pct_override.get(rid)
        row = {"party": party, "seats": seat_counts[party]}
        if pct is not None:
            row["pct"] = round(pct, 1)
        results.append(row)

    out = {
        "id": rid,
        "code": meta["code"],
        "name": meta["name"],
        "seats": len(members_sorted),
        "members": [
            {"name": m["name"], "party": m["party"], "order": i + 1}
            for i, m in enumerate(members_sorted)
        ],
        "results": results,
    }
    if turnout is not None:
        out["turnout"] = turnout
    return out


def build_year(year: int) -> dict:
    cfg = SOURCES[year]
    text = pdf_text(cfg["pdf"])

    if year == 1999:
        members = parse_1999_meps(text)
    else:
        members = parse_mep_list(text, cfg["mep_marker"])

    by_region: dict[str, list[dict]] = defaultdict(list)
    for m in members:
        by_region[m["region"]].append(m)

    shares = parse_share_table(text, cfg["share_parties"])
    # Attach NI first-preference shares from election JSON
    election = json.loads((ROOT / f"data/devolved/euro/{year}.json").read_text())
    ni_share = {
        r["party"]: r["pct"]
        for r in election["parliament"]["results"]
        if r["party"] in ("sinnfein", "dup", "uup", "sdlp", "alliance") and r.get("seats", 0) > 0
    }

    regions = []
    for rid in REGION_ORDER:
        if rid == "northern-ireland":
            ni_members = [
                {"name": n, "party": p, "order": o}
                for n, p, o in NI_MEMBERS[year]
            ]
            regions.append(
                build_region(
                    rid,
                    ni_members,
                    ni_share,
                    TURNOUT[year].get(rid),
                )
            )
            continue
        if rid not in by_region:
            raise ValueError(f"{year}: missing members for {rid}")
        regions.append(
            build_region(
                rid,
                by_region[rid],
                shares.get(rid, {}),
                TURNOUT[year].get(rid),
                cfg.get("green_pct"),
            )
        )

    payload = {
        "year": year,
        "source": {
            "label": cfg["label"],
            "url": cfg["url"],
            "file": cfg["file"],
        },
        "regions": regions,
    }
    validate(year, payload, election)
    return payload


def validate(year: int, payload: dict, election: dict) -> None:
    total = sum(r["seats"] for r in payload["regions"])
    expected = election["parliament"]["totalSeats"]
    if total != expected:
        raise SystemExit(f"{year}: region seats {total} != election total {expected}")

    from_regions: dict[str, int] = defaultdict(int)
    for r in payload["regions"]:
        for m in r["members"]:
            from_regions[m["party"]] += 1
        if len(r["members"]) != r["seats"]:
            raise SystemExit(f"{year} {r['id']}: members {len(r['members'])} != seats {r['seats']}")
        if sum(x["seats"] for x in r["results"]) != r["seats"]:
            raise SystemExit(f"{year} {r['id']}: results seats mismatch")

    expected_seats = {
        r["party"]: r["seats"]
        for r in election["parliament"]["results"]
        if r.get("seats", 0) > 0
    }
    if dict(from_regions) != expected_seats:
        # show diff
        keys = sorted(set(from_regions) | set(expected_seats))
        diffs = {
            k: (from_regions.get(k, 0), expected_seats.get(k, 0))
            for k in keys
            if from_regions.get(k, 0) != expected_seats.get(k, 0)
        }
        raise SystemExit(f"{year}: party seat mismatch vs election JSON: {diffs}")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for year in (2014, 2009, 2004, 1999):
        payload = build_year(year)
        out = OUT_DIR / f"{year}.json"
        out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        n = sum(r["seats"] for r in payload["regions"])
        print(f"Wrote {out.relative_to(ROOT)} ({n} seats, {len(payload['regions'])} regions)")


if __name__ == "__main__":
    main()
