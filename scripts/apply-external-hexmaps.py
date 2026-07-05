#!/usr/bin/env python3
"""
Apply externally-built election hexjson layouts to constituency JSON files.

Source hexjsons (with party colours) live in data/hex/elections/{year}.hexjson.
Name matching reuses normalisation logic from the hexmaps colour.py project.

Usage:
  python3 scripts/apply-external-hexmaps.py
  python3 scripts/apply-external-hexmaps.py --election 1955
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import unicodedata
from collections import Counter
from difflib import get_close_matches
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEX_DIR = ROOT / "data" / "hex" / "elections"
OUT_DIR = ROOT / "data" / "constituencies"
INDEX_PATH = OUT_DIR / "index.json"

ELECTION_TO_HEX = {
    "1945": "1945",
    "1950": "1950",
    "1951": "1951",
    "1955": "1955",
    "1959": "1959",
    "1964": "1964",
    "1966": "1966",
    "1970": "1970",
    "feb1974": "1974",
    "oct1974": "1974",
    "1979": "1979",
    "1983": "1983",
    "1987": "1987",
    "1992": "1992",
    "1997": "1997",
    "2001": "2001",
    "2005": "2005",
    "2010": "2010",
    "2015": "2015",
    "2017": "2017",
    "2019": "2019",
    "2024": "2024",
}

# Optional import of battle-tested matchers from the vendored hexmaps toolkit
# (tools/hexmaps/, moved in task-006). The legacy ~/Claude path is kept last as
# a fallback for any environment that hasn't picked up the move yet.
_COLOUR_MOD = None
for candidate in [
    ROOT / "tools" / "hexmaps" / "scripts" / "colour.py",
    Path("/Users/mosmi/Claude/claude-code/hexmaps/scripts/colour.py"),
]:
    if candidate.exists():
        spec = importlib.util.spec_from_file_location("hex_colour", candidate)
        if spec and spec.loader:
            _COLOUR_MOD = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(_COLOUR_MOD)
            break

if _COLOUR_MOD:
    normalise = _COLOUR_MOD.normalise
    expand_compass = _COLOUR_MOD.expand_compass
    collapse_directionals = _COLOUR_MOD.collapse_directionals
    sorted_words = _COLOUR_MOD.sorted_words
    CROSSWALK = _COLOUR_MOD.CROSSWALK
else:
    _NORMALIZE_RE = re.compile(r"[^a-z0-9 ]")
    _SPACE_RE = re.compile(r"\s+")
    _COMPASS = [
        ("nw", "north west"), ("ne", "north east"),
        ("sw", "south west"), ("se", "south east"),
        ("n", "north"), ("s", "south"), ("e", "east"), ("w", "west"),
    ]

    def normalise(name: str) -> str:
        s = unicodedata.normalize("NFKD", name.lower().strip())
        s = s.replace("&", " and ").replace("/", " ").replace("-", " ").replace(".", " ").replace(",", " ")
        s = _NORMALIZE_RE.sub("", s)
        return _SPACE_RE.sub(" ", s).strip()

    def expand_compass(s: str) -> str:
        for abbr, full in _COMPASS:
            s = re.sub(r"\b" + abbr + r"\b", full, s)
        return _SPACE_RE.sub(" ", s).strip()

    def collapse_directionals(s: str) -> str:
        for long, short in (("western", "west"), ("northern", "north"), ("eastern", "east"), ("southern", "south")):
            s = re.sub(r"\b" + long + r"\b", short, s)
        return _SPACE_RE.sub(" ", s).strip()

    def sorted_words(s: str) -> str:
        return " ".join(sorted(s.split()))

    CROSSWALK = {}

# Constituency JSON name → hexjson key hints (after normalisation).
SITE_ALIASES: dict[str, list[str]] = {
    "caernarfon": ["caernarvon"],
    "dunfermline": ["dunfermline burghs"],
    "kirkcaldy": ["kirkcaldy burghs"],
    "woodford": ["wanstead and woodford"],
    "falmouth and cambourne": ["falmouth and camborne"],
    "hull east": ["kingston upon hull east", "kingston upon hull e"],
    "hull north": ["kingston upon hull north", "kingston upon hull n"],
    "hull west": ["kingston upon hull west", "kingston upon hull w"],
    "llanelli": ["llanelly"],
    "city of chester": ["chester", "city of chester"],
    "chester": ["city of chester"],
    "cities of london and westminster": ["cities of london and westmister"],
    "richmond surrey": ["richmond b"],
    "richmond yorks": ["richmond a"],
    "wolverhampton north east": ["wolverhamton north east", "wolverhamton ne"],
    "wolverhampton south west": ["wolverhamton south west", "wolverhamton sw"],
    "mansfield": ["mansfiield", "mansfield"],
    "haltemprice": ["kingston upon hull haltemprice", "kingston-upon-hull haltemprice"],
    "hull central": ["kingston upon hull central", "kingston-upon-hull central", "kingston upon hull cenrtral"],
    "st pancras": ["st pancras north", "st pancras n"],
    "durham": ["city of durham"],
    "richmond yorks": ["richmond"],
    "richmond upon thames": ["richmond and barnes", "richmond park", "richmond b"],
    "oxfordshire west and abingdon": ["oxford west and abingdon", "oxford w and abingdon"],
    "welwyn and hatfield": ["welwyn hatfield"],
    "milton keynes north east": ["milton keynes ne"],
    "milton keynes south west": ["milton keynes sw"],
    "milton keynes north": ["milton keynes n"],
    "milton keynes south": ["milton keynes s"],
    "southend west": ["southend w"],
    "york": ["city of york"],
    "na h eileanan an iar western isles": ["na h eileanan an iar"],
    "kingston upon hull north and cottingham": ["hull north and cottingham", "hull n and cottingham"],
    "kingston upon hull west and haltemprice": ["hull west and haltemprice", "hull w and haltemprice"],
    "morecambe and lonsdale": ["morecambe and lunesdale", "morecambe & lunesdale"],
    "morecambe & lonsdale": ["morecambe & lunesdale", "morecambe and lunesdale"],
}

_RICHMOND_PAREN = re.compile(r"^richmond (?:\((surrey|yorks)\)|(surrey|yorks))$", re.I)
_RICHMOND_AMBIG = re.compile(r"^Richmond \([A-Z]\)$")
_LONDON_PREFIX = re.compile(r"^(?:Lambeth|Wandsworth):\s*", re.I)
# Known PDF-parse artefacts in constituency JSON (full bad name → cleaned).
_CORRUPTED_NAMES = {
    "Guildford Nick": "Guildford",
    "Solihull John": "Solihull",
    "Wealden Geoffrey": "Wealden",
    "Cardiff Central Jon": "Cardiff Central",
    "Carmarthen East & Dinefwr Alan": "Carmarthen East & Dinefwr",
    "East Lothian John": "East Lothian",
    "Ynys-Mon Ieuan": "Ynys Môn",
}


def clean_constituency_name(name: str) -> str:
    """Normalise constituency JSON quirks before hex lookup."""
    if name in _CORRUPTED_NAMES:
        return _CORRUPTED_NAMES[name]
    cleaned = _LONDON_PREFIX.sub("", name.strip())
    # 1970 split seats: "Wandsworth Putney" → "Putney"; keep "Wandsworth Central" as-is.
    if cleaned.startswith("Wandsworth ") and cleaned != "Wandsworth Central":
        cleaned = cleaned[len("Wandsworth ") :]
    return cleaned.replace("Ynys-Mon", "Ynys Môn").replace("Ynys-mon", "Ynys Môn").strip()


def name_keys(name: str) -> set[str]:
    norm = normalise(name)
    exp = expand_compass(norm)
    col = collapse_directionals(exp)
    keys = {norm, exp, col, sorted_words(exp), sorted_words(col)}
    m = _RICHMOND_PAREN.match(norm)
    if m:
        which = m.group(1).lower()
        keys.add(f"richmond {which}")
    return {k for k in keys if k}


def hex_keys(hex_name: str, hex_data: dict) -> set[str]:
    keys = set()
    for raw in (hex_name, hex_data.get("n", "")):
        if raw:
            keys |= name_keys(raw)
    return keys


def crosswalk_targets(expanded: str) -> list[str]:
    cw = CROSSWALK.get(expanded)
    if cw is None:
        return []
    return [cw] if isinstance(cw, str) else list(cw)


def build_hex_index(hexes: dict) -> dict[str, tuple[str, dict]]:
    index: dict[str, tuple[str, dict]] = {}
    for hex_name, hex_data in hexes.items():
        for key in hex_keys(hex_name, hex_data):
            index.setdefault(key, (hex_name, hex_data))
    return index


def constituency_targets(name: str) -> list[str]:
    cleaned = clean_constituency_name(name)
    norm = normalise(cleaned)
    exp = expand_compass(norm)
    targets = [norm, exp, collapse_directionals(exp), sorted_words(exp)]
    targets.extend(crosswalk_targets(exp))
    for alias in SITE_ALIASES.get(exp, SITE_ALIASES.get(norm, [])):
        targets.append(alias)
        targets.append(expand_compass(alias))
    return targets


def match_hex(
    name: str,
    hex_index: dict[str, tuple[str, dict]],
    hexes: dict,
    used: set[str],
) -> tuple[str, dict] | None:
    for target in constituency_targets(name):
        hit = hex_index.get(target)
        if hit and hit[0] not in used:
            return hit

    # Suffix match on expanded forms (unambiguous only).
    exp = expand_compass(normalise(name))
    suffix_hits: list[tuple[str, dict]] = []
    for hex_name, hex_data in hexes.items():
        if hex_name in used:
            continue
        hex_exp = expand_compass(normalise(hex_name))
        if exp == hex_exp or sorted_words(exp) == sorted_words(hex_exp):
            suffix_hits.append((hex_name, hex_data))
        else:
            for cw_target in crosswalk_targets(hex_exp):
                if exp == cw_target or sorted_words(exp) == sorted_words(cw_target):
                    suffix_hits.append((hex_name, hex_data))
                    break
    if len(suffix_hits) == 1:
        return suffix_hits[0]

    # Close fuzzy match on normalised names (last resort).
    norm = normalise(name)
    pool = [hn for hn in hexes if hn not in used]
    close = get_close_matches(norm, [normalise(h) for h in pool], n=1, cutoff=0.92)
    if close:
        for hn in pool:
            if normalise(hn) == close[0]:
                return hn, hexes[hn]
    return None


def apply_election(election_id: str, *, dry_run: bool = False) -> tuple[int, int, list[str]]:
    hex_year = ELECTION_TO_HEX.get(election_id)
    if not hex_year:
        raise ValueError(f"No hexjson mapping for election {election_id}")

    hex_path = HEX_DIR / f"{hex_year}.hexjson"
    data_path = OUT_DIR / f"{election_id}.json"
    if not hex_path.exists():
        raise FileNotFoundError(hex_path)
    if not data_path.exists():
        raise FileNotFoundError(data_path)

    hexjson = json.loads(hex_path.read_text(encoding="utf-8"))
    data = json.loads(data_path.read_text(encoding="utf-8"))
    hexes = hexjson["hexes"]
    hex_index = build_hex_index(hexes)

    used_hexes: set[str] = set()
    unmatched: list[str] = []
    matched = 0

    # Richmond (A)/(B) or Richmond (Surrey)/(Yorks) pre-assign by r-coordinate.
    richmond_hex = [(n, d) for n, d in hexes.items() if _RICHMOND_AMBIG.match(n)]
    richmond_constituencies: dict[str, int] = {}
    for i, c in enumerate(data["constituencies"]):
        cleaned = clean_constituency_name(c["name"])
        m = _RICHMOND_PAREN.match(normalise(cleaned))
        if m:
            which = (m.group(1) or m.group(2)).lower()
            richmond_constituencies[which] = i
        elif normalise(cleaned) in {"richmond upon thames", "richmond and barnes", "richmond park"}:
            richmond_constituencies.setdefault("surrey", i)
        elif normalise(cleaned) == "richmond yorks" or cleaned == "Richmond (Yorks)":
            richmond_constituencies.setdefault("yorks", i)

    preassigned: dict[int, tuple[str, dict]] = {}
    if len(richmond_hex) == 2 and len(richmond_constituencies) >= 1:
        richmond_hex.sort(key=lambda item: item[1].get("r", 0))
        if "yorks" in richmond_constituencies:
            hn, hd = richmond_hex[0]
            preassigned[richmond_constituencies["yorks"]] = (hn, hd)
            used_hexes.add(hn)
        if "surrey" in richmond_constituencies:
            hn, hd = richmond_hex[1]
            preassigned[richmond_constituencies["surrey"]] = (hn, hd)
            used_hexes.add(hn)
    elif len(richmond_hex) == 1:
        # Single unambiguous Richmond hex (1983+ Yorkshire seat).
        for i, c in enumerate(data["constituencies"]):
            if normalise(clean_constituency_name(c["name"])) in {"richmond yorks", "richmond"}:
                hn, hd = richmond_hex[0]
                preassigned[i] = (hn, hd)
                used_hexes.add(hn)
                break

    for i, c in enumerate(data["constituencies"]):
        if i in preassigned:
            hex_name, hex_data = preassigned[i]
        else:
            hit = match_hex(clean_constituency_name(c["name"]), hex_index, hexes, used_hexes)
            if not hit:
                unmatched.append(c["name"])
                c.pop("hexColour", None)
                continue
            hex_name, hex_data = hit
            used_hexes.add(hex_name)

        c["q"] = hex_data["q"]
        c["r"] = hex_data["r"]
        if hex_data.get("colour"):
            c["hexColour"] = hex_data["colour"]
        if hex_data.get("region"):
            c["region"] = hex_data["region"]
        matched += 1

    data["layout"] = hexjson.get("layout", "odd-r")
    data["hexLayout"] = f"elections/{hex_year}.hexjson"
    if "external hexmaps project" not in (data.get("source") or "").lower():
        note = "hex layout: external hexmaps project"
        data["source"] = f"{data.get('source', '').strip()} · {note}".strip(" ·")
    data["matchedHexes"] = matched

    if not dry_run:
        data_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return matched, len(data["constituencies"]), unmatched


def update_index() -> None:
    if not INDEX_PATH.exists():
        return
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    for row in index:
        eid = row.get("id")
        path = OUT_DIR / f"{eid}.json"
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        row["matchedHexes"] = data.get("matchedHexes", 0)
        row["hexLayout"] = data.get("hexLayout")
    INDEX_PATH.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply external hexjson layouts to constituency data")
    parser.add_argument("--election", action="append", help="Election id (repeatable). Default: all mapped elections.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    election_ids = args.election or sorted(ELECTION_TO_HEX.keys(), key=lambda x: (len(x), x))
    total_unmatched: list[tuple[str, list[str]]] = []

    for eid in election_ids:
        matched, total, unmatched = apply_election(eid, dry_run=args.dry_run)
        pct = 100 * matched / total if total else 0
        print(f"{eid}: {matched}/{total} ({pct:.1f}%)")
        if unmatched:
            print(f"  unmatched ({len(unmatched)}): {', '.join(unmatched[:8])}" + (" …" if len(unmatched) > 8 else ""))
            total_unmatched.append((eid, unmatched))

    if not args.dry_run:
        update_index()

    if total_unmatched:
        sys.exit(1)


if __name__ == "__main__":
    main()
