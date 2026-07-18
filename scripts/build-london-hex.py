#!/usr/bin/env python3
"""Build London Assembly HexJSON files for GLA elections (2000–2024).

Reads the static 14-cell layout from data/hex/london-grid.json, scrapes
constituency winners from Wikipedia election pages (where tables exist),
and merges curated election-night London-wide list members.

Usage:
  python3 scripts/build-london-hex.py
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "data" / "cache" / "wikipedia-html"
GRID_PATH = ROOT / "data" / "hex" / "london-grid.json"
OUT_DIR = ROOT / "data" / "hex" / "london"

YEARS = [2000, 2004, 2008, 2012, 2016, 2021, 2024]

PARTY_COLS = {
    "conservative": "conservative",
    "labour": "labour",
    "lib dems": "libdem",
    "lib dem": "libdem",
    "liberal democrats": "libdem",
    "london liberal democrats": "libdem",
    "green": "green",
    "ukip": "ukip",
    "reform uk": "reform",
    "reform": "reform",
    "bnp": "bnp",
}

# Election-night London-wide list AMs (d'Hondt allocation order).
# Source: Wikipedia "List of London Assembly constituencies" / election pages.
# Use election-night members (not later co-options), e.g. 2024 includes Siân Berry.
LIST_MEMBERS = {
    2000: [
        ("Sally Hamwee", "libdem"),
        ("Darren Johnson", "green"),
        ("Graham Tope", "libdem"),
        ("Victor Anderson", "green"),
        ("Lynne Featherstone", "libdem"),
        ("Trevor Phillips", "labour"),
        ("Samantha Heath", "labour"),
        ("Louise Bloom", "libdem"),
        ("Jenny Jones", "green"),
        ("David Lammy", "labour"),
        ("Eric Ollerenshaw", "conservative"),
    ],
    2004: [
        ("Lynne Featherstone", "libdem"),
        ("Jenny Jones", "green"),
        ("Graham Tope", "libdem"),
        ("Damian Hockney", "ukip"),
        ("Sally Hamwee", "libdem"),
        ("Darren Johnson", "green"),
        ("Michael Tuffrey", "libdem"),
        ("Peter Hulme-Cross", "ukip"),
        ("Nicky Gavron", "labour"),
        ("Murad Qureshi", "labour"),
        ("Dee Doocey", "libdem"),
    ],
    2008: [
        ("Michael Tuffrey", "libdem"),
        ("Jenny Jones", "green"),
        ("Dee Doocey", "libdem"),
        ("Richard Barnbrook", "bnp"),
        ("Darren Johnson", "green"),
        ("Nicky Gavron", "labour"),
        ("Andrew Boff", "conservative"),
        ("Caroline Pidgeon", "libdem"),
        ("Victoria Borwick", "conservative"),
        ("Murad Qureshi", "labour"),
        ("Gareth Bacon", "conservative"),
    ],
    2012: [
        ("Jenny Jones", "green"),
        ("Caroline Pidgeon", "libdem"),
        ("Nicky Gavron", "labour"),
        ("Andrew Boff", "conservative"),
        ("Darren Johnson", "green"),
        ("Murad Qureshi", "labour"),
        ("Gareth Bacon", "conservative"),
        ("Fiona Twycross", "labour"),
        ("Victoria Borwick", "conservative"),
        ("Tom Copley", "labour"),
        ("Stephen Knight", "libdem"),
    ],
    2016: [
        ("Siân Berry", "green"),
        ("Peter Whittle", "ukip"),
        ("Caroline Pidgeon", "libdem"),
        ("Kemi Badenoch", "conservative"),
        ("Andrew Boff", "conservative"),
        ("Fiona Twycross", "labour"),
        ("Caroline Russell", "green"),
        ("Tom Copley", "labour"),
        ("Shaun Bailey", "conservative"),
        ("Nicky Gavron", "labour"),
        ("David Kurten", "ukip"),
    ],
    # 2021 list: Lab 2 + Con 4 + Green 3 + LD 2 = 11 (totals Lab 11 / Con 9 / Green 3 / LD 2)
    2021: [
        ("Siân Berry", "green"),
        ("Caroline Pidgeon", "libdem"),
        ("Caroline Russell", "green"),
        ("Shaun Bailey", "conservative"),
        ("Zack Polanski", "green"),
        ("Susan Hall", "conservative"),
        ("Elly Baker", "labour"),
        ("Hina Bokhari", "libdem"),
        ("Sakina Sheikh", "labour"),
        ("Emma Best", "conservative"),
        ("Andrew Boff", "conservative"),
    ],
    # 2024 list: Green 3 + Con 5 + Reform 1 + LD 1 + Lab 1 = 11 (election-night; Berry before co-option)
    2024: [
        ("Siân Berry", "green"),
        ("Susan Hall", "conservative"),
        ("Alex Wilson", "reform"),
        ("Caroline Russell", "green"),
        ("Shaun Bailey", "conservative"),
        ("Emma Best", "conservative"),
        ("Hina Bokhari", "libdem"),
        ("Zack Polanski", "green"),
        ("Andrew Boff", "conservative"),
        ("Elly Baker", "labour"),
        ("Alessandro Georgiou", "conservative"),
    ],
}

# Wikipedia 2008 page lacks a constituency candidates table; hardcode election-night winners.
# Party control: same as 2004 except Labour gain of Brent and Harrow (Wikipedia analysis).
CONSTITUENCY_OVERRIDES = {
    2008: {
        "barnet and camden": ("Brian Coleman", "conservative"),
        "bexley and bromley": ("James Cleverly", "conservative"),
        "brent and harrow": ("Navin Shah", "labour"),
        "city and east": ("John Biggs", "labour"),
        "croydon and sutton": ("Steve O'Connell", "conservative"),
        "ealing and hillingdon": ("Richard Barnes", "conservative"),
        "enfield and haringey": ("Joanne McCartney", "labour"),
        "greenwich and lewisham": ("Len Duvall", "labour"),
        "havering and redbridge": ("Roger Evans", "conservative"),
        "lambeth and southwark": ("Val Shawcross", "labour"),
        "merton and wandsworth": ("Richard Tracey", "conservative"),
        "north east": ("Jennette Arnold", "labour"),
        "south west": ("Tony Arbour", "conservative"),
        "west central": ("Kit Malthouse", "conservative"),
    },
}


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self.current_table = []
        self.current_row = []
        self.current_cell = ""
        self.in_table = False
        self.in_tr = False
        self.in_cell = False

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.in_table = True
            self.current_table = []
        elif tag == "tr" and self.in_table:
            self.in_tr = True
            self.current_row = []
        elif tag in ("th", "td") and self.in_tr:
            self.in_cell = True
            self.current_cell = ""

    def handle_endtag(self, tag):
        if tag == "table" and self.in_table:
            self.in_table = False
            self.tables.append(self.current_table)
        elif tag == "tr" and self.in_tr:
            self.in_tr = False
            self.current_table.append(self.current_row)
        elif tag in ("th", "td") and self.in_cell:
            self.in_cell = False
            self.current_row.append(" ".join(self.current_cell.split()))

    def handle_data(self, data):
        if self.in_cell:
            self.current_cell += data


def normalize_const(name: str) -> str:
    name = name.replace("&", "and")
    name = re.sub(r"\[.*?\]", "", name)
    name = name.lower().replace("-", " ")
    name = re.sub(r"\s+", " ", name).strip()
    return name


def clean_winner(cell: str) -> str:
    m = re.match(r"(.+?)\s*\(", cell)
    name = (m.group(1) if m else cell).strip()
    name = re.sub(r"\[.*?\]", "", name)
    name = re.sub(r"\s*\(I\)\s*", "", name)
    return name.strip()


def fetch_wikipedia_html(year: int) -> str:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / f"{year}_london_assembly.html"
    if cache_path.exists():
        return cache_path.read_text(encoding="utf-8")
    url = f"https://en.wikipedia.org/wiki/{year}_London_Assembly_election"
    print(f"Fetching {url}...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; ManifestoArchive/1.0)"})
    with urllib.request.urlopen(req, timeout=45) as response:
        html = response.read().decode("utf-8", "replace")
    cache_path.write_text(html, encoding="utf-8")
    return html


def parse_constituency_winners(tables) -> dict[str, tuple[str, str]]:
    """Return {normalized_const: (winner, party_id)} from Wikipedia candidate tables."""
    for table in tables:
        if len(table) < 10:
            continue
        header_i = None
        for i, row in enumerate(table):
            if row and "barnet" in row[0].lower():
                header_i = max(0, i - 1)
                # skip blank header rows
                while header_i > 0 and not any(table[header_i]):
                    header_i -= 1
                break
        if header_i is None:
            continue

        header = [c.lower() for c in table[header_i]]
        col_party = {}
        for j, h in enumerate(header):
            for key, pid in PARTY_COLS.items():
                if key in h:
                    col_party[j] = pid
                    break

        winners = {}
        for row in table[header_i + 1 :]:
            if not row or not row[0].strip():
                continue
            if "source" in row[0].lower() or row[0].lower() == "constituency":
                continue
            const = normalize_const(row[0])
            for j, cell in enumerate(row[1:], start=1):
                if re.search(r"\b1st\b", cell, re.I):
                    winners[const] = (clean_winner(cell), col_party.get(j, "others"))
                    break
        if len(winners) >= 10:
            return winners
    return {}


def load_grid() -> dict:
    data = json.loads(GRID_PATH.read_text(encoding="utf-8"))
    return data["hexes"]


def build_london_hex() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    grid = load_grid()
    problems = []

    for year in YEARS:
        if year in CONSTITUENCY_OVERRIDES:
            winners = dict(CONSTITUENCY_OVERRIDES[year])
            print(f"{year}: using hardcoded constituency winners ({len(winners)})")
        else:
            html = fetch_wikipedia_html(year)
            parser = TableParser()
            parser.feed(html)
            winners = parse_constituency_winners(parser.tables)
            print(f"{year}: parsed {len(winners)} constituency winners from Wikipedia")

        if len(winners) != 14:
            problems.append(f"{year}: expected 14 constituency winners, got {len(winners)}")

        hexes = {}
        for key, cell in grid.items():
            if key not in winners:
                problems.append(f"{year}: missing winner for '{key}'")
                continue
            winner, party = winners[key]
            code = f"london-{year}-{key.replace(' ', '-')}"
            hexes[code] = {
                "n": cell["n"],
                "q": cell["q"],
                "r": cell["r"],
                "winner": winner,
                "party": party,
            }

        list_members = LIST_MEMBERS.get(year)
        if not list_members or len(list_members) != 11:
            problems.append(f"{year}: LIST_MEMBERS must have exactly 11 entries (got {len(list_members or [])})")
            list_members = list_members or []

        # Detect overlaps
        seen = {}
        for code, cell in hexes.items():
            pos = (cell["q"], cell["r"])
            if pos in seen:
                problems.append(f"{year}: OVERLAP at {pos} — '{cell['n']}' and '{seen[pos]}'")
            else:
                seen[pos] = cell["n"]

        out_doc = {
            "layout": "odd-r",
            "hexes": hexes,
            "regional_list": [
                {
                    "region": "London-wide",
                    "members": [{"name": n, "party": p} for n, p in list_members],
                }
            ],
        }
        out_path = OUT_DIR / f"{year}.hexjson"
        out_path.write_text(json.dumps(out_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"  Wrote {out_path} ({len(hexes)} constituencies, {len(list_members)} list)")

    if problems:
        print("\n=== PROBLEMS ===", file=sys.stderr)
        for p in problems:
            print("  " + p, file=sys.stderr)
        raise SystemExit(f"\n{len(problems)} problem(s).")
    print("\nAll London Assembly hexmaps built. ✓")


if __name__ == "__main__":
    build_london_hex()
