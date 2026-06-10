#!/usr/bin/env python3
"""
Place historic constituency results on the 2024 UK hexmap scaffold (odd-r).

The 2024 HexJSON defines the canonical q/r grid used by the live map. Historic
constituencies are matched by name (with aliases), seeded from the 1983 map when
names are unchanged, then placed by geographic proximity via parlconst.org GeoJSON
centroids (1974 or 1983 boundary vintage as appropriate).

Usage:
  python3 scripts/import-historical-hexmaps.py
  python3 scripts/import-historical-hexmaps.py --election feb1974
"""

from __future__ import annotations

from collections.abc import Callable

import argparse
import importlib.util
import json
import math
import os
import re
import unicodedata
from collections import deque
from difflib import get_close_matches
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEX_DIR = ROOT / "data" / "hex"
OUT_DIR = ROOT / "data" / "constituencies"
SCAFFOLD_HEX = HEX_DIR / "uk-constituencies-2024.hexjson"
ANCHORS_JSON = HEX_DIR / "historic-to-2024-anchors.json"
SUCCESSOR_MAP_JSON = HEX_DIR / "1974-abolished-wikipedia-replaced-by.json"
SUCCESSOR_MAP_1955_JSON = HEX_DIR / "1955-abolished-wikipedia-replaced-by.json"
GEOJSON_DIR = Path(
    os.environ.get(
        "HISTORICAL_HEXMAP_GEOJSON_DIR",
        "/Users/mosmi/Documents/Codex/historical-uk-hexmaps/sources/geojson",
    )
)
GEOJSON = Path(
    os.environ.get(
        "HISTORICAL_HEXMAP_GEOJSON",
        str(GEOJSON_DIR / "1983-combined.geojson"),
    )
)

ELECTIONS = (
    "1983",
    "1987",
    "1992",
    "feb1974",
    "oct1974",
    "1979",
    "1955",
    "1959",
    "1964",
    "1966",
    "1970",
)
LAYOUT = "odd-r"
HEX_LAYOUT_FILE = "uk-constituencies-2024.hexjson"

# Elections on the 1955–1970 boundary vintage (630 seats).
PRE_FEB1974_ELECTIONS = frozenset({"1955", "1959", "1964", "1966", "1970"})

# Boundary vintage for geographic centroids (parlconst.org GeoJSON in sources/geojson/)
BOUNDARY_GEO_FILES: dict[str, tuple[str, ...]] = {
    "1955": (
        "1955-scotland-1955.geojson",
        "1955-wales-1955.geojson",
        "1955-england-1955.geojson",
        "1955-northern-ireland-1950.geojson",
    ),
    "1974": (
        "1974-scotland-1974.geojson",
        "1974-wales-1974.geojson",
        "1974-england-1974.geojson",
        "1974-northern-ireland-1974.geojson",
    ),
    "1983": (
        "1983-scotland-1983.geojson",
        "1983-wales-1983.geojson",
        "1983-england-1983.geojson",
        "1983-northern-ireland-1983.geojson",
    ),
}

ELECTION_BOUNDARY: dict[str, str] = {
    "1955": "1955",
    "1959": "1955",
    "1964": "1955",
    "1966": "1955",
    "1970": "1955",
    "feb1974": "1974",
    "oct1974": "1974",
    "1979": "1974",
    "1983": "1983",
    "1987": "1983",
    "1992": "1983",
}

# When importing earlier vintages, inherit hex cells from this election for unchanged names.
ELECTION_REFERENCE_SEED: dict[str, str] = {
    "1955": "feb1974",
    "1959": "1955",
    "1964": "1955",
    "1966": "1955",
    "1970": "1955",
    "feb1974": "1983",
    "oct1974": "1983",
    "1979": "1983",
}

# Same seat, different spelling between HoC datasets (1955 vs 1959–1970).
REFERENCE_SEED_ALIASES: dict[str, str] = {
    "bethnall green": "bethnal green",
    "banffshire": "banff",
    "cardiganshire": "cardigan",
    "llanelly": "llanelli",
    "morcambe and lonsdale": "morecambe and lonsdale",
    "wanstead and woodford": "woodford",
    "liverpool exchange": "liverpool scotland exchange",
    "richmond (surrey)": "richmond upon thames",
}

GEO_COORD_OVERRIDES: dict[str, tuple[float, float]] = {
    # 1955 GeoJSON has duplicate bare "Richmond" features; last merge wins without these.
    "richmond (yorks)": (-1.782883724398474, 54.400366159692375),
    "richmond (surrey)": (-0.2807250168057037, 51.457451450834434),
    "richmond upon thames": (-0.2807250168057037, 51.457451450834434),
    # HoC label; 1955 GeoJSON uses "City of London & Westminster South" feature name.
    "london and westminster - cities of": (-0.1265, 51.5135),
    "city of london and westminster south": (-0.1265, 51.5135),
    "paddington": (-0.18877866771498467, 51.52170288084911),
}

NI_PARTIES = frozenset({"uup", "dup", "sdlp", "sinnfein", "upup", "uuup", "vanguard"})
NI_NAME_HINTS = (
    "antrim", "armagh", "belfast", "down", "fermanagh", "londonderry",
    "tyrone", "derry", "foyle", "lagan", "strangford", "upper bann",
)

# Historic constituency name → 2024 HexJSON constituency name
HISTORIC_TO_2024: dict[str, str] = {
    "ynys mon": "Ynys Môn",
    "anglesey": "Ynys Môn",
    "montgomery": "Montgomeryshire and Glyndŵr",
    "montgomeryshire": "Montgomeryshire and Glyndŵr",
    "richmond and barnes": "Richmond Park",
    "richmond (yorks)": "Richmond and Northallerton",
    "richmond (surrey)": "Richmond Park",
    "southwark and bermondsey": "Bermondsey and Old Southwark",
    "southwark": "Bermondsey and Old Southwark",
    "lewisham west": "Lewisham West and East Dulwich",
    "milton keynes": "Milton Keynes North",
    "milton keynes north east": "Milton Keynes North",
    "milton keynes south west": "Milton Keynes Central",
    "monmouth": "Monmouthshire",
    "caithness and sutherland": "Caithness, Sutherland and Easter Ross",
    "carrick cumnock and doon valley": "Ayr, Carrick and Cumnock",
    "kilmarnock and loudon": "Kilmarnock and Loudoun",
    "kilmarnock and loudoun": "Kilmarnock and Loudoun",
    "leeds south and morley": "Leeds South",
    "liverpool broadgreen": "Liverpool Broad Green",
    "newcastle upon tyne central": "Newcastle upon Tyne Central",
    "great grimsby": "Great Grimsby and Cleethorpes",
    "devon west and torridge": "Torridge and Tavistock",
    "fife central": "Cowdenbeath and Kirkcaldy",
    "chester": "City of Chester",
    "city of chester": "City of Chester",
    "welshpool and montgomery": "Montgomeryshire and Glyndŵr",
    "kirkaldy": "Cowdenbeath and Kirkcaldy",
    "kirkcaldy": "Cowdenbeath and Kirkcaldy",
    "gillingham": "Gillingham and Rainham",
    "sheffield hillsborough": "Sheffield Brightside and Hillsborough",
    "sheffield hillborough": "Sheffield Brightside and Hillsborough",
    "tweedale ettrick and lauderdale": "Dumfriesshire, Clydesdale and Tweeddale",
    "tweeddale ettrick and lauderdale": "Dumfriesshire, Clydesdale and Tweeddale",
    "hertfordshire west": "South West Hertfordshire",
    "hertfordshire w": "South West Hertfordshire",
    "cannock and burtwood": "Cannock Chase",
    "cannock and burntwood": "Cannock Chase",
    "worcestshire south": "Worcestershire South",
    "rydale": "Thirsk and Malton",
    "ryedale": "Thirsk and Malton",
    "western isles": "Na h-Eileanan an Iar",
    "wyre": "Lancaster and Wyre",
    "york": "York Central",
    "worsley": "Worsley and Eccles",
    "stirling": "Stirling and Strathallan",
    "motherwell south": "Motherwell, Wishaw and Carluke",
    "renfrew west and inverclyde": "Inverclyde and Renfrewshire West",
    "ross cromarty and skye": "Inverness, Skye and West Ross-shire",
    "strathkelvin and bearsden": "Mid Dunbartonshire",
    "roxburgh and berwickshire": "Berwickshire, Roxburgh and Selkirk",
    "tayside north": "Angus and Perthshire Glens",
}

# Extra anchors from data/hex/historic-to-2024-anchors.json (Wikipedia / 1983 GeoJSON)
CELL_GEO_1983_NAMES: dict[str, list[str]] = {}
MANUAL_HEX: dict[str, tuple[int, int]] = {}
_REFERENCE_PINNED: frozenset[str] = frozenset()
_MANUAL_PINS_APPLIED: bool = False
GEO_NAME_ALIASES: dict[str, str] = {}
DISPLAY_NAMES: dict[str, str] = {}

# 1983-only scaffold cells with no same-name 1974 seat (legacy; packing no longer uses these).
VINTAGE_GAP_FILLS: dict[tuple[int, int], str] = {
    (46, -37): "Ogmore",
    (50, -40): "Bristol South East",
    (50, -41): "Somerset North",
}

# Wikipedia "Replaced by" overrides where the scraped value is wrong or post-1974.
SUCCESSOR_OVERRIDES_1955: dict[str, list[str]] = {
    "llanelly": ["Llanelli"],
    "london and westminster cities of": ["City of London & Westminster South"],
    "london westminster cities of": ["City of London & Westminster South"],
    "merton and mordern": ["Mitcham & Morden"],
    "stoke newington and hackney north": ["Hackney North & Stoke Newington"],
    "stratford": ["Stratford-on-Avon"],
    "southwark": ["Bermondsey"],
    "stepney": ["Stepney & Poplar"],
    "poplar": ["Stepney & Poplar"],
    "brixton": ["Lambeth Central", "Streatham"],
    "clapham": ["Lambeth Central", "Streatham"],
    "islington east": ["Islington Central", "Islington North"],
    "barons court": ["Fulham", "Hammersmith North"],
    "oxford": ["Oxford East", "Oxfordshire West and Abingdon"],
    "battersea south": ["Tooting", "Battersea North"],
    "plymouth sutton": ["Plymouth Moor View", "Plymouth Sutton and Devonport"],
    "devon north": ["North Devon"],
    "bilston": ["Wolverhampton North East", "Wolverhampton South East"],
    "billericay": ["Basildon", "Brentwood & Ongar"],
    "bebington": ["Bebington & Ellesmere Port"],
    "bethnal green": ["Bethnal Green & Bow"],
    "pontefract": ["Pontefract & Castleford"],
    "montgomery": ["Montgomeryshire"],
    "richmond (surrey)": ["Richmond upon Thames"],
    "liverpool exchange": ["Liverpool Scotland Exchange"],
    "hull north": ["Kingston upon Hull North", "Kingston upon Hull East"],
    "the hartlepools": ["Hartlepool"],
    "sedgefield": ["Sedgefield"],
    "dover": ["Dover & Deal"],
    "west ham north": ["Newham North West", "Newham North East"],
    "west ham south": ["Newham South"],
    "east ham south": ["Newham North East", "Newham South"],
    "east ham north": ["Newham North East"],
    "woolwich east": ["Woolwich"],
    "paddington north": ["Paddington"],
    "paddington south": ["Paddington"],
    "kensington north": ["Kensington"],
    "kensington south": ["Kensington"],
    "windsor": ["Windsor"],
}

# Max geographic separation (degrees) between abolished seat and a Wikipedia successor.
MAX_SUCCESSOR_GEO_DEG = 0.22

# Wikipedia "Replaced by" overrides where the scraped value is wrong or post-1983.
SUCCESSOR_OVERRIDES: dict[str, list[str]] = {
    "anglesey": ["Ynys Mon"],
    "caernarvon": ["Caernarfon"],
    "cardigan": ["Ceredigion & Pembroke North"],
    "conway": ["Conwy"],
    "isle of ely": ["Cambridgeshire North East", "Cambridgeshire South East"],
    "southgate": ["Enfield Southgate", "Hornsey & Wood Green"],
    "st marylebone": ["Westminster North", "City of London & Westminster South"],
    "wood green": ["Hornsey & Wood Green", "Tottenham"],
    "woolwich west": ["Woolwich"],
}

# Normalise successor labels from Wikipedia to 1983 constituency names.
SUCCESSOR_NAME_ALIASES: dict[str, str] = {
    "cardiganshire": "ceredigion and pembroke north",
    "ne cambridgeshire": "cambridgeshire north east",
    "se cambridgeshire": "cambridgeshire south east",
    "aberconwy": "conwy",
    "bermondsey west": "southwark and bermondsey",
    "rotherhithe": "southwark and bermondsey",
    "batley": "batley and spen",
    "spen": "batley and spen",
    "argyll": "argyll and bute",
    "bute": "argyll and bute",
    "carrick": "carrick cumnock and doon valley",
    "doon valley": "carrick cumnock and doon valley",
    "galloway": "galloway and upper nithsdale",
    "upper nithsdale": "galloway and upper nithsdale",
    "central suffolk": "suffolk central",
    "hampstead": "hampstead and highgate",
    "highgate": "hampstead and highgate",
    "carshalton": "carshalton and wallington",
    "wallington": "carshalton and wallington",
    "dover county": "dover",
    "blyth": "blyth valley",
    "cramlington": "blyth valley",
    "killingworth most": "blyth valley",
    "hackney south": "hackney south and shoreditch",
    "stoke newington": "hackney north and stoke newington",
    "holborn and st pancras": "holborn and st pancras south",
    "westminster south": "city of london and westminster south",
    "city of london": "city of london and westminster south",
}

# Normalise Wikipedia successor labels to feb1974 constituency names.
SUCCESSOR_NAME_ALIASES_1974: dict[str, str] = {
    "bethnal green and bow": "bethnall green and bow",
    "bethnal green bow": "bethnall green and bow",
    "city of london and westminster south": "city of london and westminster south",
    "cities of london and westminster": "city of london and westminster south",
    "chipping barnet": "chipping barnet",
    "south hertfordshire": "south hertfordshire",
    "bebington and ellesmere port": "bebington and ellesmere port",
    "hackney north and stoke newington": "hackney north and stoke newington",
    "stepney and poplar": "stepney and poplar",
    "richmond and barnes": "richmond upon thames",
    "richmond barnes": "richmond upon thames",
    "kingston upon hull north cottingham": "kingston upon hull north",
    "hartlepool": "hartlepool",
    "christchurch and lymington": "christchurch and lymington",
    "bournemouth east": "bournemouth east",
    "pontefract and castleford": "pontefract and castleford",
    "stirling falkirk and grangemouth": "stirling falkirk and grangemouth",
    "greenock and port glasgow": "greenock and port glasgow",
    "motherwell and wishaw": "motherwell and wishaw",
    "lewisham deptford": "lewisham west",
    "southwark and bermondsey": "bermondsey",
    "bermondsey west": "bermondsey",
    "rotherhithe": "bermondsey",
    "fulham": "fulham",
    "hammersmith north": "hammersmith north",
    "manchester central": "manchester central",
    "warley east": "warley east",
    "warley west": "warley west",
    "west bromwich east": "west bromwich east",
    "west bromwich west": "west bromwich west",
}

# Normalise known typos in HoC / PDF constituency names before lookup
TYPO_FIXES: dict[str, str] = {
    "kirkaldy": "kirkcaldy",
    "rydale": "ryedale",
    "burtwood": "burntwood",
    "worcestshire": "worcestershire",
    "tweedale": "tweeddale",
    "cannock and burtwood": "cannock and burntwood",
    "bethnall": "bethnal",
    "aukland": "auckland",
    "morcambe": "morecambe",
    "hillsborough": "hillborough",
}

ALLIANCE_LABELS = (
    "alliance (lib)",
    "alliance (sdp)",
    "alliance (liberal)",
    "sdp-liberal alliance",
    "sdp - liberal alliance",
)

# Word-level fixes for HoC / politicsresources.net scrape typos (applied to display names).
DISPLAY_WORD_FIXES: tuple[tuple[str, str], ...] = (
    ("Bethnall", "Bethnal"),
    ("Morcambe", "Morecambe"),
    ("Mordern", "Morden"),
    ("Kirkaldy", "Kirkcaldy"),
    ("Rydale", "Ryedale"),
    ("Burtwood", "Burntwood"),
    ("Worcestshire", "Worcestershire"),
    ("Hillborough", "Hillsborough"),
    ("Aukland", "Auckland"),
    ("Tweedale", "Tweeddale"),
    ("Hertfordhire", "Hertfordshire"),
    ("Coln", "Colne"),
    ("Caernarvon", "Caernarfon"),
    ("Llanelly", "Llanelli"),
    ("Mansfiield", "Mansfield"),
    ("Lunesdale", "Lonsdale"),
)


def load_wikipedia_aliases():
    spec = importlib.util.spec_from_file_location(
        "build_wikipedia_hex_layout",
        ROOT / "scripts" / "build-wikipedia-hex-layout.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.alias_keys, mod.norm_name, mod.match_hex_position


def load_fetch_module():
    spec = importlib.util.spec_from_file_location(
        "fetch_constituency_data",
        ROOT / "scripts" / "fetch-constituency-data.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


alias_keys, norm_name, match_hex_position = load_wikipedia_aliases()


def load_anchor_data() -> None:
    global CELL_GEO_1983_NAMES, MANUAL_HEX, GEO_NAME_ALIASES, DISPLAY_NAMES
    if not ANCHORS_JSON.exists():
        return
    data = json.loads(ANCHORS_JSON.read_text(encoding="utf-8"))
    for key, target in (data.get("historicTo2024") or {}).items():
        HISTORIC_TO_2024.setdefault(historic_norm(key), target)
    CELL_GEO_1983_NAMES = data.get("cellGeo1983Names") or {}
    MANUAL_HEX = {
        norm_name(key): (int(coord[0]), int(coord[1]))
        for key, coord in (data.get("manualHex") or {}).items()
        if isinstance(coord, (list, tuple)) and len(coord) == 2
        and not str(key).startswith("_")
    }
    GEO_NAME_ALIASES = {
        norm_name(key): norm_name(value)
        for key, value in (data.get("geoNameAliases") or {}).items()
        if not str(key).startswith("_")
    }
    DISPLAY_NAMES = {
        norm_name(key): str(value)
        for key, value in (data.get("displayNames") or {}).items()
        if not str(key).startswith("_")
    }


def normalize_historic_mappings() -> None:
    """Re-key historic mappings with historic_norm so (Yorks) suffixes match lookups."""
    global HISTORIC_TO_2024, REFERENCE_SEED_ALIASES, GEO_COORD_OVERRIDES
    global SUCCESSOR_OVERRIDES_1955, SUCCESSOR_OVERRIDES
    HISTORIC_TO_2024 = {historic_norm(k): v for k, v in HISTORIC_TO_2024.items()}
    REFERENCE_SEED_ALIASES = {
        historic_norm(k): historic_norm(v) for k, v in REFERENCE_SEED_ALIASES.items()
    }
    GEO_COORD_OVERRIDES = {
        historic_norm(k): v for k, v in GEO_COORD_OVERRIDES.items()
    }
    SUCCESSOR_OVERRIDES_1955 = {
        historic_norm(k): v for k, v in SUCCESSOR_OVERRIDES_1955.items()
    }
    SUCCESSOR_OVERRIDES = {
        historic_norm(k): v for k, v in SUCCESSOR_OVERRIDES.items()
    }


def manual_hex_frozen() -> frozenset[str]:
    """Manual hex overrides are immobile only after apply_manual_hex_overrides runs."""
    return frozenset(MANUAL_HEX.keys()) if _MANUAL_PINS_APPLIED else frozenset()


def all_pinned_names() -> frozenset[str]:
    return manual_hex_frozen() | _REFERENCE_PINNED


def historic_norm(name: str) -> str:
    n = norm_name(name)
    for wrong, right in TYPO_FIXES.items():
        if wrong in n:
            n = n.replace(wrong, right)
    return n


def reference_keys(name: str) -> list[str]:
    """Lookup keys for matching a seat to a reference election layout."""
    keys: list[str] = []
    seen: set[str] = set()
    for key in (*alias_keys(name), historic_norm(name), norm_name(name)):
        if key and key not in seen:
            seen.add(key)
            keys.append(key)
    alias = REFERENCE_SEED_ALIASES.get(historic_norm(name))
    if alias:
        for key in (*alias_keys(alias), alias):
            if key and key not in seen:
                seen.add(key)
                keys.append(key)
    return keys


normalize_historic_mappings()
load_anchor_data()


def hex_neighbors(q: int, r: int) -> list[tuple[int, int]]:
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if r % 2:
        dirs += [(1, 1), (-1, 1)]
    else:
        dirs += [(1, -1), (-1, -1)]
    return [(q + dq, r + dr) for dq, dr in dirs]


def hex_distance(q1: int, r1: int, q2: int, r2: int) -> int:
    """Axial hex distance (odd-r offset coordinates)."""
    aq = q1 - (r1 - (r1 & 1)) // 2
    ar = r1
    bq = q2 - (r2 - (r2 & 1)) // 2
    br = r2
    return (abs(aq - bq) + abs(aq + ar - bq - br) + abs(ar - br)) // 2


def region_to_nation(region: str) -> str | None:
    region = str(region or "")
    if region.startswith("S"):
        return "scotland"
    if region.startswith("W"):
        return "wales"
    if region.startswith("E"):
        return "england"
    if region.startswith("N"):
        return "northern-ireland"
    return None


def geo_for_2024_cell(name: str, geo_lookup: dict[str, tuple[float, float]]) -> tuple[float, float] | None:
    geo = geo_for_name(name, geo_lookup)
    if geo:
        return geo
    for alt in CELL_GEO_1983_NAMES.get(name, []):
        geo = geo_for_name(alt, geo_lookup)
        if geo:
            return geo
    return None


def build_cell_geos(
    geo_lookup: dict[str, tuple[float, float]],
    scaffold_coords: set[tuple[int, int]],
) -> dict[tuple[int, int], tuple[float, float]]:
    data = json.loads(SCAFFOLD_HEX.read_text(encoding="utf-8"))
    cell_geos: dict[tuple[int, int], tuple[float, float]] = {}
    for cell in data["hexes"].values():
        coord = (cell["q"], cell["r"])
        geo = geo_for_2024_cell(cell.get("n", ""), geo_lookup)
        if geo:
            cell_geos[coord] = geo
    missing = [coord for coord in scaffold_coords if coord not in cell_geos]
    for _ in range(24):
        progress = False
        for coord in list(missing):
            neighbours = [n for n in hex_neighbors(*coord) if n in cell_geos]
            if not neighbours:
                continue
            lon = sum(cell_geos[n][0] for n in neighbours) / len(neighbours)
            lat = sum(cell_geos[n][1] for n in neighbours) / len(neighbours)
            cell_geos[coord] = (lon, lat)
            missing.remove(coord)
            progress = True
        if not progress:
            break
    return cell_geos


def geo_for_name(name: str, geo_lookup: dict[str, tuple[float, float]]) -> tuple[float, float] | None:
    hn = historic_norm(name)
    if hn in GEO_COORD_OVERRIDES:
        return GEO_COORD_OVERRIDES[hn]
    alias = GEO_NAME_ALIASES.get(hn)
    if alias:
        for key in alias_keys(alias):
            geo = geo_lookup.get(historic_norm(key)) or geo_lookup.get(key)
            if geo:
                return geo
    mapped = HISTORIC_TO_2024.get(hn)
    if mapped and historic_norm(mapped) != hn:
        via_2024 = geo_for_name(mapped, geo_lookup)
        if via_2024:
            return via_2024
    for key in alias_keys(name):
        geo = geo_lookup.get(historic_norm(key)) or geo_lookup.get(key)
        if geo:
            return geo
    return None


FUZZY_STOP_TOKENS = frozenset({
    "north", "south", "east", "west", "central", "upon", "and", "the", "of",
    "tyne", "city", "mid", "st", "upon", "with", "de", "la", "le", "under",
})


def meaningful_token_overlap(a: str, b: str) -> bool:
    left = set(a.split()) - FUZZY_STOP_TOKENS
    right = set(b.split()) - FUZZY_STOP_TOKENS
    return bool(left & right)


def fuzzy_2024_match(candidate: str, by_name: dict[str, dict]) -> dict | None:
    """Conservative fuzzy match — avoids collisions like Workington→Orpington."""
    base = historic_norm(candidate)
    keys = list(by_name.keys())
    for match in get_close_matches(base, keys, n=3, cutoff=0.88):
        if base == match:
            return by_name[match]
        shared = set(base.split()) & set(match.split())
        if shared and meaningful_token_overlap(base, match):
            return by_name[match]
        if base[:5] == match[:5] or base in match or match in base:
            if meaningful_token_overlap(base, match) or len(base) <= 5:
                return by_name[match]
    return None


def neighbor_occupied_count(coord: tuple[int, int], occupied: set[tuple[int, int]]) -> int:
    return sum(1 for n in hex_neighbors(*coord) if n in occupied)


def anchor_coord(c: dict, by_name: dict[str, dict]) -> tuple[int, int] | None:
    pos = lookup_2024_name(c["name"], by_name, c.get("nation"))
    if pos:
        return (pos["q"], pos["r"])
    return None


def historic_anchor_taken(
    c: dict, occupied: set[tuple[int, int]], by_name: dict[str, dict]
) -> bool:
    """True when a seat maps to a 2024 anchor cell already claimed by another seat."""
    if historic_norm(c["name"]) not in HISTORIC_TO_2024:
        return False
    anchor = anchor_coord(c, by_name)
    return bool(anchor and anchor in occupied)


def snap_england_anchors(
    constituencies: list[dict],
    assigned_pos: dict[int, tuple[int, int]],
    occupied: set[tuple[int, int]],
    england_coords: set[tuple[int, int]],
    by_name: dict[str, dict],
) -> None:
    """Claim empty 2024 anchor cells for seats with a direct successor mapping."""
    for i, c in enumerate(constituencies):
        if c.get("nation") != "england":
            continue
        if historic_norm(c["name"]) in all_pinned_names():
            continue
        anchor = anchor_coord(c, by_name)
        if not anchor or anchor not in england_coords or anchor in occupied:
            continue
        old = assigned_pos.get(i)
        if old == anchor:
            continue
        if old:
            occupied.discard(old)
        assigned_pos[i] = anchor
        occupied.add(anchor)


def _cascade_movable(
    i: int,
    constituencies: list[dict],
    pinned: frozenset[str],
) -> bool:
    return historic_norm(constituencies[i]["name"]) not in pinned


def adjacent_empty_cells(occupied: set[tuple[int, int]]) -> set[tuple[int, int]]:
    gaps: set[tuple[int, int]] = set()
    for coord in occupied:
        for nbr in hex_neighbors(*coord):
            if nbr not in occupied:
                gaps.add(nbr)
    return gaps


def count_surrounded_holes(
    occupied: set[tuple[int, int]], *, min_neighbors: int = 5
) -> int:
    return sum(
        1
        for gap in adjacent_empty_cells(occupied)
        if neighbor_occupied_count(gap, occupied) >= min_neighbors
    )


def peripheral_empty_scaffold_cells(
    nation_coords: set[tuple[int, int]],
    occupied: set[tuple[int, int]],
) -> set[tuple[int, int]]:
    """Empty scaffold cells connected to the coast (≤2 occupied neighbours)."""
    empty = nation_coords - occupied
    peripheral: set[tuple[int, int]] = set()
    for start in empty:
        if neighbor_occupied_count(start, occupied) > 2:
            continue
        queue: deque[tuple[int, int]] = deque([start])
        seen = {start}
        while queue:
            coord = queue.popleft()
            peripheral.add(coord)
            for nbr in hex_neighbors(*coord):
                if nbr in empty and nbr not in seen:
                    seen.add(nbr)
                    queue.append(nbr)
    return peripheral


def interior_empty_scaffold_cells(
    nation_coords: set[tuple[int, int]],
    occupied: set[tuple[int, int]],
) -> list[tuple[int, int]]:
    """Empty scaffold cells fully enclosed inland (e.g. a 2×2 hole with 3–4 neighbours each)."""
    empty = nation_coords - occupied
    peripheral = peripheral_empty_scaffold_cells(nation_coords, occupied)
    flood_interior = empty - peripheral
    # Empty cells on the sea edge of the scaffold are acceptable coastal pockets.
    coastal = {
        cell
        for cell in flood_interior
        if any(nbr not in nation_coords for nbr in hex_neighbors(*cell))
    }
    return sorted(
        flood_interior - coastal,
        key=lambda c: (-neighbor_occupied_count(c, occupied), c),
    )


def eliminate_interior_scaffold_gaps(
    constituencies: list[dict],
    assigned_pos: dict[int, tuple[int, int]],
    occupied: set[tuple[int, int]],
    nation_coords: set[tuple[int, int]],
) -> None:
    """Fill inland scaffold holes that are too weakly surrounded for zero_surrounded_holes."""
    for _ in range(64):
        interior = interior_empty_scaffold_cells(nation_coords, occupied)
        if not interior:
            return
        gap = interior[0]
        if fill_interior_hole_via_chain(
            constituencies, assigned_pos, occupied, nation_coords, gap
        ):
            continue
        if relocate_interior_scaffold_empties(
            constituencies, assigned_pos, occupied, nation_coords
        ):
            continue
        if fill_single_surrounded_hole(
            constituencies, assigned_pos, occupied, gap
        ):
            continue
        break


def seat_at(
    assigned_pos: dict[int, tuple[int, int]], coord: tuple[int, int]
) -> int | None:
    return next((idx for idx, pos in assigned_pos.items() if pos == coord), None)


def cascade_scaffold_gaps_to_periphery(
    constituencies: list[dict],
    assigned_pos: dict[int, tuple[int, int]],
    occupied: set[tuple[int, int]],
    nation_coords: set[tuple[int, int]],
    cell_geos: dict[tuple[int, int], tuple[float, float]],
    geo_lookup: dict[str, tuple[float, float]],
) -> bool:
    """Fill empty scaffold cells by sliding a neighbour north or west; gaps move outward."""
    pinned = all_pinned_names()
    rows = sorted({r for _q, r in nation_coords})
    cols = sorted({q for q, _r in nation_coords})
    moved = False

    def try_slide(i: int, gap: tuple[int, int], donor: tuple[int, int]) -> None:
        nonlocal moved
        if gap not in cell_geos or donor not in cell_geos:
            return
        if neighbor_occupied_count(gap, occupied) < 3:
            return
        hg = geo_for_name(constituencies[i]["name"], geo_lookup)
        if not hg:
            return
        if geo_sqdist(hg, cell_geos[gap]) > 0.55**2:
            return
        assigned_pos[i] = gap
        occupied.remove(donor)
        occupied.add(gap)
        moved = True

    for q in cols:
        for r in rows:
            gap = (q, r)
            if gap in occupied or gap not in nation_coords:
                continue
            donor = (q, r - 1)
            if donor not in occupied or donor not in nation_coords:
                continue
            i = seat_at(assigned_pos, donor)
            if i is None or not _cascade_movable(i, constituencies, pinned):
                continue
            try_slide(i, gap, donor)

    for r in rows:
        row_qs = sorted(q for q, rr in nation_coords if rr == r)
        for q in row_qs:
            gap = (q, r)
            if gap in occupied or gap not in nation_coords:
                continue
            donor = (q + 1, r)
            if donor not in occupied or donor not in nation_coords:
                continue
            i = seat_at(assigned_pos, donor)
            if i is None or not _cascade_movable(i, constituencies, pinned):
                continue
            try_slide(i, gap, donor)

    return moved


def cascade_england_gaps_to_periphery(
    constituencies: list[dict],
    assigned_pos: dict[int, tuple[int, int]],
    occupied: set[tuple[int, int]],
    england_coords: set[tuple[int, int]],
    cell_geos: dict[tuple[int, int], tuple[float, float]],
    geo_lookup: dict[str, tuple[float, float]],
) -> bool:
    return cascade_scaffold_gaps_to_periphery(
        constituencies,
        assigned_pos,
        occupied,
        england_coords,
        cell_geos,
        geo_lookup,
    )


def compact_england_internal_gaps(
    constituencies: list[dict],
    assigned_pos: dict[int, tuple[int, int]],
    occupied: set[tuple[int, int]],
    england_coords: set[tuple[int, int]],
) -> None:
    """Cascade seats one hex west into sandwiched empty scaffold cells in a row."""
    pinned = all_pinned_names()
    rows = sorted({r for _q, r in england_coords})
    max_q = max(q for q, _r in england_coords)

    for _ in range(max_q + 2):
        moved = False
        for r in rows:
            row_qs = sorted(q for q, rr in england_coords if rr == r)
            for q in row_qs[:-1]:
                gap = (q, r)
                if gap in occupied:
                    continue
                wq = q - 1
                while wq >= row_qs[0] and (wq, r) not in england_coords:
                    wq -= 1
                if (wq, r) not in occupied:
                    continue
                eq = q + 1
                if (eq, r) not in england_coords or (eq, r) not in occupied:
                    continue
                i = next(
                    (idx for idx, pos in assigned_pos.items() if pos == (eq, r)),
                    None,
                )
                if i is None:
                    continue
                name_key = historic_norm(constituencies[i]["name"])
                if name_key in pinned:
                    continue
                assigned_pos[i] = gap
                occupied.remove((eq, r))
                occupied.add(gap)
                moved = True
        if not moved:
            break


def fill_england_scaffold_gaps(
    constituencies: list[dict],
    assigned_pos: dict[int, tuple[int, int]],
    occupied: set[tuple[int, int]],
    england_coords: set[tuple[int, int]],
    cell_geos: dict[tuple[int, int], tuple[float, float]],
    geo_lookup: dict[str, tuple[float, float]],
    by_name: dict[str, dict],
    *,
    aggressive: bool = False,
) -> None:
    """Move historic seats into empty 2024 England cells surrounded by neighbours."""
    england_indices = [
        i for i, c in enumerate(constituencies) if c.get("nation") == "england"
    ]
    protected = {
        i
        for i in england_indices
        if historic_norm(constituencies[i]["name"]) in all_pinned_names()
        or anchor_coord(constituencies[i], by_name) == assigned_pos.get(i)
    }

    for _ in range(len(england_coords)):
        gaps = sorted(
            (c for c in england_coords if c not in occupied and c in cell_geos),
            key=lambda c: (-neighbor_occupied_count(c, occupied), c),
        )
        if not gaps:
            break

        moved = False
        min_neighbors = 2 if aggressive else 3
        for gap in gaps:
            gap_n = neighbor_occupied_count(gap, occupied)
            if gap_n < min_neighbors:
                continue
            gap_geo = cell_geos[gap]
            best_i = None
            best_score = -1e9

            ranked: list[tuple[float, int, float, int]] = []
            for i in england_indices:
                cur = assigned_pos.get(i)
                if not cur or cur == gap:
                    continue
                if historic_norm(constituencies[i]["name"]) in all_pinned_names():
                    continue
                hg = geo_for_name(constituencies[i]["name"], geo_lookup)
                if not hg:
                    continue
                cur_geo = cell_geos.get(cur)
                cur_dist = geo_sqdist(hg, cur_geo) if cur_geo else 1e9
                new_dist = geo_sqdist(hg, gap_geo)
                gain = cur_dist - new_dist
                cur_n = neighbor_occupied_count(cur, occupied)
                ranked.append((new_dist, -gain, cur_n, i))

            if gap_n >= 5 and ranked:
                ranked.sort(key=lambda row: (row[0], row[1], row[2]))
                min_gain = -0.02 if aggressive else 0.0
                max_new = 0.55**2 if aggressive else 0.45**2
                for new_dist, neg_gain, cur_n, i in ranked[:12]:
                    gain = -neg_gain
                    if new_dist > max_new:
                        continue
                    if gain <= min_gain:
                        continue
                    if i in protected and gain <= 0.03:
                        continue
                    best_i = i
                    break

            if best_i is None:
                for i in england_indices:
                    cur = assigned_pos.get(i)
                    if not cur or cur == gap:
                        continue
                    if historic_norm(constituencies[i]["name"]) in all_pinned_names():
                        continue
                    hg = geo_for_name(constituencies[i]["name"], geo_lookup)
                    if not hg:
                        continue
                    cur_geo = cell_geos.get(cur)
                    cur_dist = geo_sqdist(hg, cur_geo) if cur_geo else 1e9
                    new_dist = geo_sqdist(hg, gap_geo)
                    gain = cur_dist - new_dist
                    cur_n = neighbor_occupied_count(cur, occupied)
                    score = gain + 0.03 * (gap_n - cur_n)
                    if i in protected and gain <= 0.03:
                        score -= 0.5
                    if gap_n >= 5 and new_dist < 0.35**2:
                        score += 0.15
                    min_gain = -0.02 if aggressive and gap_n >= 4 else 0.0
                    max_new = 1.1**2 if aggressive else 1.0**2
                    if gain <= min_gain or new_dist > max_new:
                        continue
                    if score > best_score:
                        best_score = score
                        best_i = i

            if best_i is not None:
                old = assigned_pos[best_i]
                occupied.discard(old)
                assigned_pos[best_i] = gap
                occupied.add(gap)
                moved = True
                break
        if not moved:
            break


def is_renamed_seat(name: str, reference_placements: dict[str, tuple[int, int]]) -> bool:
    """True when this vintage seat has no same-name placement in the reference election."""
    return not any(key in reference_placements for key in reference_keys(name))


def reference_home_coord(
    name: str, reference_placements: dict[str, tuple[int, int]]
) -> tuple[int, int] | None:
    for key in reference_keys(name):
        if key in reference_placements:
            return reference_placements[key]
    return None


def successor_name_match_score(seat_name: str, ref_name: str) -> int:
    sn = historic_norm(seat_name)
    rn = historic_norm(ref_name)
    if rn in sn or sn in rn:
        return 2
    for token in rn.split():
        if len(token) >= 5 and token in sn:
            return 1
    return 0


def allow_successor_anchor_move(
    seat_name: str,
    cur: tuple[int, int],
    gap: tuple[int, int],
    gap_ref_name: str,
    ref_coord_names: dict[tuple[int, int], str],
    ref_geo_lookup: dict[str, tuple[float, float]],
    hg: tuple[float, float] | None,
    occupied: set[tuple[int, int]],
) -> bool:
    """Allow moving between two successor anchors without ping-ponging."""
    cur_ref_name = ref_coord_names.get(cur, "")
    cur_score = successor_name_match_score(seat_name, cur_ref_name)
    gap_score = successor_name_match_score(seat_name, gap_ref_name)
    if cur_score > gap_score:
        return False
    if cur_score == gap_score and cur_score > 0:
        return gap < cur
    if cur_score == gap_score == 0 and hg:
        gap_ref_geo = geo_for_name(gap_ref_name, ref_geo_lookup)
        cur_ref_geo = geo_for_name(cur_ref_name, ref_geo_lookup)
        if gap_ref_geo and cur_ref_geo:
            if geo_sqdist(hg, gap_ref_geo) + 0.002 >= geo_sqdist(hg, cur_ref_geo):
                gap_nb = neighbor_occupied_count(gap, occupied)
                cur_nb = neighbor_occupied_count(cur, occupied)
                if gap_nb <= cur_nb:
                    return False
    return True


def resolve_gap_geo(
    gap: tuple[int, int],
    cell_geos: dict[tuple[int, int], tuple[float, float]],
    ref_geo: tuple[float, float] | None,
) -> tuple[float, float] | None:
    if gap in cell_geos:
        return cell_geos[gap]
    if ref_geo:
        return ref_geo
    nbr_geos = [cell_geos[n] for n in hex_neighbors(*gap) if n in cell_geos]
    if nbr_geos:
        return (
            sum(g[0] for g in nbr_geos) / len(nbr_geos),
            sum(g[1] for g in nbr_geos) / len(nbr_geos),
        )
    return None


def fill_coastal_pockets(
    constituencies: list[dict],
    assigned_pos: dict[int, tuple[int, int]],
    occupied: set[tuple[int, int]],
    scot_coords: set[tuple[int, int]],
    wales_coords: set[tuple[int, int]],
    england_coords: set[tuple[int, int]],
    geo_lookup: dict[str, tuple[float, float]],
    reference_placements: dict[str, tuple[int, int]] | None = None,
) -> None:
    """Slide renamed seats into off-scaffold coastal cells surrounded by the map."""
    gb_coords = england_coords | scot_coords | wales_coords
    candidate_gaps: set[tuple[int, int]] = set()
    for coord in occupied:
        for nbr in hex_neighbors(*coord):
            if nbr not in occupied and nbr not in gb_coords:
                candidate_gaps.add(nbr)

    for _ in range(16):
        gaps = sorted(
            (g for g in candidate_gaps if g not in occupied),
            key=lambda c: (-neighbor_occupied_count(c, occupied), c),
        )
        moved = False
        for gap in gaps:
            if neighbor_occupied_count(gap, occupied) < 6:
                continue
            candidates: list[tuple[int, int, int]] = []
            for i, c in enumerate(constituencies):
                if is_ni_constituency(c):
                    continue
                if reference_placements and not is_renamed_seat(
                    c["name"], reference_placements
                ):
                    continue
                cur = assigned_pos.get(i)
                if not cur or hex_distance(cur[0], cur[1], gap[0], gap[1]) != 1:
                    continue
                home = (
                    reference_home_coord(c["name"], reference_placements)
                    if reference_placements
                    else None
                )
                if home and cur == home:
                    continue
                candidates.append((i, 0 if historic_norm(c["name"]) == "kilmarnock" else 1, i))
            candidates.sort(key=lambda item: (item[1], item[2]))
            for i, _, _ in candidates:
                cur = assigned_pos[i]
                occupied.discard(cur)
                assigned_pos[i] = gap
                occupied.add(gap)
                candidate_gaps.discard(gap)
                for nbr in hex_neighbors(*gap):
                    if nbr not in occupied:
                        candidate_gaps.add(nbr)
                moved = True
                break
            if moved:
                break
        if not moved:
            break


def reference_gap_claimants(
    gap: tuple[int, int],
    ref_name: str,
    ref_geo: tuple[float, float] | None,
    seat_meta: list[tuple[int, str, tuple[float, float] | None, set[tuple[int, int]]]],
    assigned_pos: dict[int, tuple[int, int]],
    reference_placements: dict[str, tuple[int, int]],
    ref_coord_names: dict[tuple[int, int], str],
    ref_geo_lookup: dict[str, tuple[float, float]],
    cell_geos: dict[tuple[int, int], tuple[float, float]],
    manual_pinned: frozenset[str],
    occupied: set[tuple[int, int]] | None = None,
    *,
    adjacent_only: bool = False,
) -> list[tuple[int, float, float, int]]:
    if occupied is None:
        occupied = set(assigned_pos.values())
    claimants: list[tuple[int, float, float, int]] = []
    for i, name, hg, succ_coords in seat_meta:
        if historic_norm(name) in manual_pinned:
            continue
        cur = assigned_pos.get(i)
        if cur == gap:
            continue
        hex_d = hex_distance(cur[0], cur[1], gap[0], gap[1]) if cur else 999
        max_d = (2 if gap in succ_coords else 1) if adjacent_only else 999
        if hex_d > max_d:
            continue

        home = reference_home_coord(name, reference_placements)
        if home == gap:
            claimants.append((-1, 0.0, -float(hex_d), i))
            continue

        if ref_name and historic_norm(name) == historic_norm(ref_name):
            claimants.append((-1, 0.0, -float(hex_d), i))
            continue

        if gap in succ_coords:
            if (
                cur
                and cur in succ_coords
                and cur != gap
                and not allow_successor_anchor_move(
                    name,
                    cur,
                    gap,
                    ref_name,
                    ref_coord_names,
                    ref_geo_lookup,
                    hg,
                    occupied,
                )
            ):
                continue
            geo_d = geo_sqdist(hg, ref_geo) if hg and ref_geo else float(hex_d)
            claimants.append((0, geo_d, -float(hex_d), i))
            continue

        if home and cur == home:
            continue

        if not is_renamed_seat(name, reference_placements):
            continue
        gap_geo = resolve_gap_geo(gap, cell_geos, ref_geo)
        cur_geo = cell_geos.get(cur) if cur else None
        if not gap_geo:
            continue
        if hg and ref_geo and hex_d <= 4:
            geo_d = geo_sqdist(hg, ref_geo)
            if geo_d <= 0.16**2:
                new_fit = geo_sqdist(hg, gap_geo)
                old_fit = geo_sqdist(hg, cur_geo) if cur_geo else geo_d + 1.0
                if new_fit + 0.002 < old_fit:
                    claimants.append((2, geo_d, -float(hex_d), i))
                    continue
        if cur_geo and hex_d <= 2 and not succ_coords:
            shift = geo_sqdist(cur_geo, gap_geo)
            claimants.append((3, shift, -float(hex_d), i))
    claimants.sort()
    return claimants


def orphan_reference_gap_claimants(
    gap: tuple[int, int],
    ref_name: str,
    ref_geo: tuple[float, float] | None,
    seat_meta: list[tuple[int, str, tuple[float, float] | None, set[tuple[int, int]]]],
    assigned_pos: dict[int, tuple[int, int]],
    reference_placements: dict[str, tuple[int, int]],
    ref_coord_names: dict[tuple[int, int], str],
    ref_geo_lookup: dict[str, tuple[float, float]],
    cell_geos: dict[tuple[int, int], tuple[float, float]],
    manual_pinned: frozenset[str],
    *,
    max_hex_d: int = 2,
) -> list[tuple[int, float, float, int]]:
    """Fill empty 1983 cells using renamed seats when no successor claimant exists."""
    gap_geo = resolve_gap_geo(gap, cell_geos, ref_geo)
    if not gap_geo:
        return []
    claimants: list[tuple[int, float, float, int]] = []
    for i, name, _hg, succ_coords in seat_meta:
        if historic_norm(name) in manual_pinned:
            continue
        if not is_renamed_seat(name, reference_placements):
            continue
        cur = assigned_pos.get(i)
        if not cur or cur == gap:
            continue
        hex_d = hex_distance(cur[0], cur[1], gap[0], gap[1])
        if hex_d > max_hex_d:
            continue
        home = reference_home_coord(name, reference_placements)
        if home and cur == home:
            continue
        if gap in succ_coords:
            continue
        cur_geo = cell_geos.get(cur)
        if not cur_geo:
            continue
        shift = geo_sqdist(cur_geo, gap_geo)
        claimants.append((4, shift, -float(hex_d), i))
    claimants.sort()
    return claimants


def _pick_gap_claimants(
    gap: tuple[int, int],
    ref_name: str,
    ref_geo: tuple[float, float] | None,
    seat_meta: list[tuple[int, str, tuple[float, float] | None, set[tuple[int, int]]]],
    assigned_pos: dict[int, tuple[int, int]],
    occupied: set[tuple[int, int]],
    reference_placements: dict[str, tuple[int, int]],
    ref_coord_names: dict[tuple[int, int], str],
    ref_geo_lookup: dict[str, tuple[float, float]],
    cell_geos: dict[tuple[int, int], tuple[float, float]],
    manual_pinned: frozenset[str],
    *,
    adjacent_only: bool = False,
    allow_orphan: bool = False,
) -> list[tuple[int, float, float, int]]:
    claimants = reference_gap_claimants(
        gap,
        ref_name,
        ref_geo,
        seat_meta,
        assigned_pos,
        reference_placements,
        ref_coord_names,
        ref_geo_lookup,
        cell_geos,
        manual_pinned,
        occupied,
        adjacent_only=adjacent_only,
    )
    if claimants:
        return claimants
    if adjacent_only or allow_orphan:
        return orphan_reference_gap_claimants(
            gap,
            ref_name,
            ref_geo,
            seat_meta,
            assigned_pos,
            reference_placements,
            ref_coord_names,
            ref_geo_lookup,
            cell_geos,
            manual_pinned,
        )
    return claimants


def gap_has_successor_claimant(
    gap: tuple[int, int],
    seat_meta: list[tuple[int, str, tuple[float, float] | None, set[tuple[int, int]]]],
) -> bool:
    return any(gap in succ_coords for _i, _name, _hg, succ_coords in seat_meta)


def fill_vintage_reference_gaps(
    constituencies: list[dict],
    assigned_pos: dict[int, tuple[int, int]],
    occupied: set[tuple[int, int]],
    reference_placements: dict[str, tuple[int, int]],
    ref_coord_names: dict[tuple[int, int], str],
    successor_map: dict[str, list[str]],
    geo_lookup: dict[str, tuple[float, float]],
    ref_geo_lookup: dict[str, tuple[float, float]],
    cell_geos: dict[tuple[int, int], tuple[float, float]],
    england_coords: set[tuple[int, int]],
    scot_coords: set[tuple[int, int]],
    wales_coords: set[tuple[int, int]],
    ni_coords: set[tuple[int, int]],
) -> None:
    """Move vintage seats into empty cells that held their 1983 successor or geographic match."""
    manual_pinned = manual_hex_frozen()
    gb_coords = england_coords | scot_coords | wales_coords
    ref_coords = set(ref_coord_names)

    seat_meta: list[tuple[int, str, tuple[float, float] | None, set[tuple[int, int]]]] = []
    for i, c in enumerate(constituencies):
        if is_ni_constituency(c):
            continue
        pool = nation_pool(
            c, ni_coords, scot_coords, wales_coords, england_coords, gb_coords
        )
        hg = geo_for_name(c["name"], geo_lookup)
        successors = successors_for_seat(c["name"], successor_map) or []
        succ_coords = {
            coord
            for s in successors
            if (coord := resolve_reference_placement(s, reference_placements))
        }
        seat_meta.append((i, c["name"], hg, succ_coords & pool))

    for _ in range(128):
        gaps = sorted(
            (coord for coord in ref_coords if coord not in occupied and coord in gb_coords),
            key=lambda c: (
                -neighbor_occupied_count(c, occupied),
                -int(gap_has_successor_claimant(c, seat_meta)),
                c,
            ),
        )
        if not gaps:
            break
        moved = False
        for gap in gaps:
            ref_name = ref_coord_names.get(gap, "")
            ref_geo = geo_for_name(ref_name, ref_geo_lookup) if ref_name else None
            claimants = _pick_gap_claimants(
                gap,
                ref_name,
                ref_geo,
                seat_meta,
                assigned_pos,
                occupied,
                reference_placements,
                ref_coord_names,
                ref_geo_lookup,
                cell_geos,
                manual_pinned,
                allow_orphan=True,
            )
            if not claimants:
                continue
            best_i = claimants[0][3]
            cur = assigned_pos.get(best_i)
            if cur:
                occupied.discard(cur)
            assigned_pos[best_i] = gap
            occupied.add(gap)
            moved = True
            break
        if not moved:
            break


def fill_adjacent_reference_gaps(
    constituencies: list[dict],
    assigned_pos: dict[int, tuple[int, int]],
    occupied: set[tuple[int, int]],
    reference_placements: dict[str, tuple[int, int]],
    ref_coord_names: dict[tuple[int, int], str],
    successor_map: dict[str, list[str]],
    geo_lookup: dict[str, tuple[float, float]],
    ref_geo_lookup: dict[str, tuple[float, float]],
    cell_geos: dict[tuple[int, int], tuple[float, float]],
    england_coords: set[tuple[int, int]],
    scot_coords: set[tuple[int, int]],
    wales_coords: set[tuple[int, int]],
    ni_coords: set[tuple[int, int]],
    *,
    pinned_names: frozenset[str] | None = None,
) -> None:
    """Fill empty 1983 cells that touch an occupied neighbour (one-hex slides)."""
    manual_pinned = manual_hex_frozen() | (pinned_names or frozenset())
    gb_coords = england_coords | scot_coords | wales_coords
    ref_coords = set(ref_coord_names)

    seat_meta: list[tuple[int, str, tuple[float, float] | None, set[tuple[int, int]]]] = []
    for i, c in enumerate(constituencies):
        if is_ni_constituency(c):
            continue
        pool = nation_pool(
            c, ni_coords, scot_coords, wales_coords, england_coords, gb_coords
        )
        hg = geo_for_name(c["name"], geo_lookup)
        successors = successors_for_seat(c["name"], successor_map) or []
        succ_coords = {
            coord
            for s in successors
            if (coord := resolve_reference_placement(s, reference_placements))
        }
        seat_meta.append((i, c["name"], hg, succ_coords & pool))

    for _ in range(96):
        gaps = sorted(
            (
                coord
                for coord in ref_coords
                if coord not in occupied
                and coord in gb_coords
                and neighbor_occupied_count(coord, occupied) >= 1
            ),
            key=lambda c: (
                -neighbor_occupied_count(c, occupied),
                -int(gap_has_successor_claimant(c, seat_meta)),
                c,
            ),
        )
        if not gaps:
            break
        moved = False
        for gap in gaps:
            ref_name = ref_coord_names.get(gap, "")
            ref_geo = geo_for_name(ref_name, ref_geo_lookup) if ref_name else None
            claimants = _pick_gap_claimants(
                gap,
                ref_name,
                ref_geo,
                seat_meta,
                assigned_pos,
                occupied,
                reference_placements,
                ref_coord_names,
                ref_geo_lookup,
                cell_geos,
                manual_pinned,
                adjacent_only=True,
            )
            if not claimants:
                continue
            best_i = claimants[0][3]
            cur = assigned_pos.get(best_i)
            if cur:
                occupied.discard(cur)
            assigned_pos[best_i] = gap
            occupied.add(gap)
            moved = True
            break
        if not moved:
            break


def connected_components(
    occupied: set[tuple[int, int]],
) -> list[set[tuple[int, int]]]:
    remaining = set(occupied)
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = next(iter(remaining))
        comp: set[tuple[int, int]] = set()
        queue = [start]
        while queue:
            coord = queue.pop()
            if coord not in remaining:
                continue
            remaining.remove(coord)
            comp.add(coord)
            for nbr in hex_neighbors(*coord):
                if nbr in remaining:
                    queue.append(nbr)
        components.append(comp)
    return components


def repair_isolated_constituencies(
    constituencies: list[dict],
    assigned_pos: dict[int, tuple[int, int]],
    occupied: set[tuple[int, int]],
    reference_placements: dict[str, tuple[int, int]],
    ref_coord_names: dict[tuple[int, int], str],
    successor_map: dict[str, list[str]],
    geo_lookup: dict[str, tuple[float, float]],
    ref_geo_lookup: dict[str, tuple[float, float]],
    cell_geos: dict[tuple[int, int], tuple[float, float]],
    england_coords: set[tuple[int, int]],
    scot_coords: set[tuple[int, int]],
    wales_coords: set[tuple[int, int]],
    ni_coords: set[tuple[int, int]],
) -> None:
    """Fill bridge cells so small islands (e.g. Harwich) reconnect to the mainland."""
    manual_pinned = manual_hex_frozen()
    gb_coords = england_coords | scot_coords | wales_coords
    ref_coords = set(ref_coord_names)

    seat_meta: list[tuple[int, str, tuple[float, float] | None, set[tuple[int, int]]]] = []
    for i, c in enumerate(constituencies):
        if is_ni_constituency(c):
            continue
        pool = nation_pool(
            c, ni_coords, scot_coords, wales_coords, england_coords, gb_coords
        )
        hg = geo_for_name(c["name"], geo_lookup)
        successors = successors_for_seat(c["name"], successor_map) or []
        succ_coords = {
            coord
            for s in successors
            if (coord := resolve_reference_placement(s, reference_placements))
        }
        seat_meta.append((i, c["name"], hg, succ_coords & pool))

    for _ in range(32):
        components = connected_components(occupied)
        if len(components) <= 1:
            break
        mainland = max(components, key=len)
        moved = False
        for comp in components:
            if comp is mainland:
                continue
            bridge_gaps: set[tuple[int, int]] = set()
            for coord in comp:
                for nbr in hex_neighbors(*coord):
                    if nbr not in occupied and nbr in ref_coords and nbr in gb_coords:
                        bridge_gaps.add(nbr)
            for gap in sorted(
                bridge_gaps,
                key=lambda c: (-neighbor_occupied_count(c, occupied), c),
            ):
                ref_name = ref_coord_names.get(gap, "")
                ref_geo = geo_for_name(ref_name, ref_geo_lookup) if ref_name else None
                claimants = _pick_gap_claimants(
                    gap,
                    ref_name,
                    ref_geo,
                    seat_meta,
                    assigned_pos,
                    occupied,
                    reference_placements,
                    ref_coord_names,
                    ref_geo_lookup,
                    cell_geos,
                    manual_pinned,
                    adjacent_only=True,
                )
                if not claimants:
                    claimants = _pick_gap_claimants(
                        gap,
                        ref_name,
                        ref_geo,
                        seat_meta,
                        assigned_pos,
                        occupied,
                        reference_placements,
                        ref_coord_names,
                        ref_geo_lookup,
                        cell_geos,
                        manual_pinned,
                        allow_orphan=True,
                    )
                if not claimants:
                    continue
                best_i = claimants[0][3]
                cur = assigned_pos.get(best_i)
                if cur:
                    occupied.discard(cur)
                assigned_pos[best_i] = gap
                occupied.add(gap)
                moved = True
                break
            if moved:
                break
        if not moved:
            break


def vintage_gap_pinned_names() -> frozenset[str]:
    return frozenset(historic_norm(name) for name in VINTAGE_GAP_FILLS.values())


def apply_vintage_gap_fills(
    constituencies: list[dict],
    assigned_pos: dict[int, tuple[int, int]],
    occupied: set[tuple[int, int]],
) -> None:
    """Pin renamed (and a few adjacent) seats into known 1983-only scaffold holes."""
    name_to_index = {
        historic_norm(c["name"]): i for i, c in enumerate(constituencies)
    }
    for coord, seat_name in VINTAGE_GAP_FILLS.items():
        key = historic_norm(seat_name)
        i = name_to_index.get(key)
        if i is None:
            continue
        old = assigned_pos.get(i)
        if old == coord:
            continue
        if coord in occupied and assigned_pos.get(i) != coord:
            blocker = next(
                (idx for idx, pos in assigned_pos.items() if pos == coord and idx != i),
                None,
            )
            if blocker is None or not old:
                continue
            assigned_pos[blocker] = old
        elif old:
            occupied.discard(old)
        assigned_pos[i] = coord
        occupied.add(coord)


def fill_surrounded_hex_gaps(
    constituencies: list[dict],
    assigned_pos: dict[int, tuple[int, int]],
    occupied: set[tuple[int, int]],
    cell_geos: dict[tuple[int, int], tuple[float, float]],
    geo_lookup: dict[str, tuple[float, float]],
    england_coords: set[tuple[int, int]],
    scot_coords: set[tuple[int, int]],
    wales_coords: set[tuple[int, int]],
    ni_coords: set[tuple[int, int]],
    reference_placements: dict[str, tuple[int, int]] | None = None,
) -> None:
    """Fill off-scaffold holes surrounded by placed seats (e.g. Scottish border pockets)."""
    manual_pinned = manual_hex_frozen()
    gb_coords = england_coords | scot_coords | wales_coords
    candidate_gaps: set[tuple[int, int]] = set()
    for coord in occupied:
        for nbr in hex_neighbors(*coord):
            if nbr not in occupied:
                candidate_gaps.add(nbr)

    for _ in range(24):
        moved = False
        gaps = sorted(
            (
                g
                for g in candidate_gaps
                if g not in occupied and neighbor_occupied_count(g, occupied) >= 4
            ),
            key=lambda c: (-neighbor_occupied_count(c, occupied), c),
        )
        for gap in gaps:
            gap_geo = resolve_gap_geo(gap, cell_geos, None)
            if not gap_geo:
                continue
            best_i = None
            best_score = -1e9
            for i, c in enumerate(constituencies):
                if is_ni_constituency(c):
                    continue
                if historic_norm(c["name"]) in manual_pinned:
                    continue
                if reference_placements:
                    cur = assigned_pos.get(i)
                    if cur and any(
                        reference_placements.get(key) == cur for key in alias_keys(c["name"])
                    ):
                        continue
                cur = assigned_pos.get(i)
                if not cur or cur == gap:
                    continue
                if hex_distance(cur[0], cur[1], gap[0], gap[1]) > 1:
                    continue
                hg = geo_for_name(c["name"], geo_lookup)
                cur_geo = cell_geos.get(cur)
                if not cur_geo:
                    cur_geo = hg
                if not cur_geo:
                    continue
                if hg:
                    gain = geo_sqdist(hg, cur_geo) - geo_sqdist(hg, gap_geo)
                else:
                    gain = geo_sqdist(cur_geo, gap_geo)
                if gain <= 0.001:
                    continue
                score = gain + 0.02 * neighbor_occupied_count(gap, occupied)
                if score > best_score:
                    best_score = score
                    best_i = i
            if best_i is None:
                continue
            old = assigned_pos[best_i]
            occupied.discard(old)
            assigned_pos[best_i] = gap
            occupied.add(gap)
            candidate_gaps.discard(gap)
            for nbr in hex_neighbors(*gap):
                if nbr not in occupied:
                    candidate_gaps.add(nbr)
            moved = True
            break
        if not moved:
            break


def densify_england_scaffold(
    constituencies: list[dict],
    assigned_pos: dict[int, tuple[int, int]],
    occupied: set[tuple[int, int]],
    england_coords: set[tuple[int, int]],
    cell_geos: dict[tuple[int, int], tuple[float, float]],
    geo_lookup: dict[str, tuple[float, float]],
    by_name: dict[str, dict],
) -> None:
    """Pack England onto the 2024 mainland after manual pins — cascade gaps to the coast."""
    for _ in range(max(len(england_coords), 96)):
        if not cascade_england_gaps_to_periphery(
            constituencies,
            assigned_pos,
            occupied,
            england_coords,
            cell_geos,
            geo_lookup,
        ):
            break


def repair_scaffold_bridges(
    constituencies: list[dict],
    assigned_pos: dict[int, tuple[int, int]],
    occupied: set[tuple[int, int]],
    gb_coords: set[tuple[int, int]],
    cell_geos: dict[tuple[int, int], tuple[float, float]],
    geo_lookup: dict[str, tuple[float, float]],
) -> None:
    """Reconnect small mainland islands by sliding a neighbour into an empty scaffold bridge cell."""
    pinned = all_pinned_names()
    for _ in range(32):
        components = connected_components(occupied)
        if len(components) <= 1:
            break
        mainland = max(components, key=len)
        moved = False
        for comp in components:
            if comp is mainland:
                continue
            bridge_gaps: set[tuple[int, int]] = set()
            for coord in comp:
                for nbr in hex_neighbors(*coord):
                    if nbr not in occupied and nbr in gb_coords:
                        bridge_gaps.add(nbr)
            for gap in sorted(
                bridge_gaps,
                key=lambda c: (-neighbor_occupied_count(c, occupied), c),
            ):
                gap_geo = cell_geos.get(gap)
                if not gap_geo:
                    continue
                best_i = None
                best_score = -1e9
                for i, c in enumerate(constituencies):
                    if is_ni_constituency(c):
                        continue
                    if historic_norm(c["name"]) in pinned:
                        continue
                    cur = assigned_pos.get(i)
                    if not cur or cur == gap:
                        continue
                    if hex_distance(cur[0], cur[1], gap[0], gap[1]) != 1:
                        continue
                    if cur not in mainland and cur not in comp:
                        continue
                    cur_geo = cell_geos.get(cur)
                    hg = geo_for_name(c["name"], geo_lookup) or cur_geo
                    if not cur_geo or not hg:
                        continue
                    gain = geo_sqdist(hg, cur_geo) - geo_sqdist(hg, gap_geo)
                    if gain <= 0.001:
                        continue
                    score = gain + 0.02 * neighbor_occupied_count(gap, occupied)
                    if score > best_score:
                        best_score = score
                        best_i = i
                if best_i is None:
                    continue
                old = assigned_pos[best_i]
                occupied.discard(old)
                assigned_pos[best_i] = gap
                occupied.add(gap)
                moved = True
                break
            if moved:
                break
        if not moved:
            break



def bfs_scaffold_path(
    start: tuple[int, int],
    goal: tuple[int, int],
    nation_coords: set[tuple[int, int]],
) -> list[tuple[int, int]] | None:
    if start == goal:
        return [start]
    queue: list[tuple[int, int]] = [start]
    prev: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    for current in queue:
        for nbr in hex_neighbors(*current):
            if nbr not in nation_coords or nbr in prev:
                continue
            prev[nbr] = current
            if nbr == goal:
                path = [goal]
                while path[-1] is not start:
                    path.append(prev[path[-1]])  # type: ignore[index]
                path.reverse()
                return path
            queue.append(nbr)
    return None



def snapshot_positions(
    assigned_pos: dict[int, tuple[int, int]],
    occupied: set[tuple[int, int]],
) -> tuple[dict[int, tuple[int, int]], set[tuple[int, int]]]:
    return dict(assigned_pos), set(occupied)


def restore_positions(
    assigned_pos: dict[int, tuple[int, int]],
    occupied: set[tuple[int, int]],
    snap: tuple[dict[int, tuple[int, int]], set[tuple[int, int]]],
) -> None:
    assigned_pos.clear()
    assigned_pos.update(snap[0])
    occupied.clear()
    occupied.update(snap[1])


def surrounded_hole_score(occupied: set[tuple[int, int]]) -> tuple[int, int]:
    """Lower is better: (surrounded count, total excess neighbour exposure)."""
    holes = [
        g
        for g in adjacent_empty_cells(occupied)
        if neighbor_occupied_count(g, occupied) >= 5
    ]
    exposure = sum(max(0, neighbor_occupied_count(g, occupied) - 4) for g in holes)
    return (len(holes), exposure)


def apply_if_fewer_holes(
    assigned_pos: dict[int, tuple[int, int]],
    occupied: set[tuple[int, int]],
    action: Callable[[], bool],
) -> bool:
    before = surrounded_hole_score(occupied)
    snap = snapshot_positions(assigned_pos, occupied)
    if not action():
        return False
    after = surrounded_hole_score(occupied)
    if after > before:
        restore_positions(assigned_pos, occupied, snap)
        return False
    return True


def fill_interior_hole_via_chain(
    constituencies: list[dict],
    assigned_pos: dict[int, tuple[int, int]],
    occupied: set[tuple[int, int]],
    nation_coords: set[tuple[int, int]],
    gap: tuple[int, int],
) -> bool:
    """Fill a surrounded scaffold hole by sliding seats along a path from the periphery."""
    manual = manual_hex_frozen()
    sources = sorted(
        (
            c
            for c in nation_coords
            if c in occupied and neighbor_occupied_count(c, occupied) <= 4
        ),
        key=lambda c: (
            neighbor_occupied_count(c, occupied),
            len(bfs_scaffold_path(gap, c, nation_coords) or []),
            c,
        ),
    )
    for source in sources:
        path = bfs_scaffold_path(gap, source, nation_coords)
        if not path or len(path) < 2:
            continue
        moves: list[tuple[int, tuple[int, int]]] = []
        blocked = False
        for idx in range(1, len(path)):
            recipient = path[idx - 1]
            donor = path[idx]
            if donor not in occupied:
                blocked = True
                break
            i = seat_at(assigned_pos, donor)
            if i is None or historic_norm(constituencies[i]["name"]) in manual:
                blocked = True
                break
            moves.append((i, recipient))
        if blocked or not moves:
            continue
        for i, recipient in moves:
            old = assigned_pos[i]
            occupied.discard(old)
            assigned_pos[i] = recipient
            occupied.add(recipient)
        return gap in occupied
    return False


def relocate_interior_scaffold_empties(
    constituencies: list[dict],
    assigned_pos: dict[int, tuple[int, int]],
    occupied: set[tuple[int, int]],
    nation_coords: set[tuple[int, int]],
) -> bool:
    """Fill or slide interior scaffold holes toward the nation boundary."""
    empty_cells = [c for c in nation_coords if c not in occupied]
    interior = sorted(
        (c for c in empty_cells if neighbor_occupied_count(c, occupied) >= 5),
        key=lambda c: (-neighbor_occupied_count(c, occupied), c),
    )
    if not interior:
        return False

    gap = interior[0]
    if fill_interior_hole_via_chain(
        constituencies, assigned_pos, occupied, nation_coords, gap
    ):
        return True

    manual = manual_hex_frozen()
    peripheral_targets = sorted(
        (
            c
            for c in empty_cells
            if c != gap and neighbor_occupied_count(c, occupied) <= 3
        ),
        key=lambda c: (len(bfs_scaffold_path(gap, c, nation_coords) or []), c),
    )

    for target in peripheral_targets:
        path = bfs_scaffold_path(gap, target, nation_coords)
        if not path or len(path) < 2:
            continue

        blank = gap
        moved = False
        for nxt in path[1:]:
            if nxt not in hex_neighbors(*blank):
                moved = False
                break
            if nxt not in occupied:
                blank = nxt
                moved = True
                continue
            i = seat_at(assigned_pos, nxt)
            if i is None:
                moved = False
                break
            if historic_norm(constituencies[i]["name"]) in manual:
                moved = False
                break
            assigned_pos[i] = blank
            occupied.remove(nxt)
            occupied.add(blank)
            blank = nxt
            moved = True

        if moved:
            return True
    return False


def fill_single_surrounded_hole(
    constituencies: list[dict],
    assigned_pos: dict[int, tuple[int, int]],
    occupied: set[tuple[int, int]],
    gap: tuple[int, int],
) -> bool:
    """Move the best adjacent seat into one surrounded empty cell."""
    if neighbor_occupied_count(gap, occupied) < 5:
        return False
    manual = manual_hex_frozen()
    gap_n = neighbor_occupied_count(gap, occupied)
    best_i: int | None = None
    best_score = -1e9
    for nbr in hex_neighbors(*gap):
        if nbr not in occupied:
            continue
        i = seat_at(assigned_pos, nbr)
        if i is None or is_ni_constituency(constituencies[i]):
            continue
        if historic_norm(constituencies[i]["name"]) in manual:
            continue
        vac_n = neighbor_occupied_count(nbr, occupied)
        score = float(gap_n - vac_n)
        if score > best_score:
            best_score = score
            best_i = i
    if best_i is None:
        return False
    old = assigned_pos[best_i]
    occupied.discard(old)
    assigned_pos[best_i] = gap
    occupied.add(gap)
    return True


def eliminate_surrounded_holes(
    constituencies: list[dict],
    assigned_pos: dict[int, tuple[int, int]],
    occupied: set[tuple[int, int]],
    cell_geos: dict[tuple[int, int], tuple[float, float]],
    geo_lookup: dict[str, tuple[float, float]],
    *,
    topology_only: bool = False,
) -> bool:
    """Slide a neighbour into any empty cell surrounded by five or more seats."""
    manual = manual_hex_frozen()
    holes = sorted(
        (
            g
            for g in adjacent_empty_cells(occupied)
            if neighbor_occupied_count(g, occupied) >= 5
        ),
        key=lambda c: (-neighbor_occupied_count(c, occupied), c),
    )
    if not holes:
        return False

    for gap in holes:
        gap_geo = resolve_gap_geo(gap, cell_geos, None)
        gap_n = neighbor_occupied_count(gap, occupied)
        best_i: int | None = None
        best_score = -1e9

        for nbr in hex_neighbors(*gap):
            if nbr not in occupied:
                continue
            i = seat_at(assigned_pos, nbr)
            if i is None or is_ni_constituency(constituencies[i]):
                continue
            if historic_norm(constituencies[i]["name"]) in manual:
                continue
            vac_n = neighbor_occupied_count(nbr, occupied)
            topo = 0.2 * (gap_n - vac_n)
            hg = geo_for_name(constituencies[i]["name"], geo_lookup)
            cur_geo = cell_geos.get(nbr) or hg
            if gap_geo and hg and cur_geo:
                gain = geo_sqdist(hg, cur_geo) - geo_sqdist(hg, gap_geo)
                new_dist = geo_sqdist(hg, gap_geo)
            else:
                gain = 0.0
                new_dist = 0.0
            score = topo + gain
            if not topology_only and gap_geo and hg and cur_geo:
                if gap_n >= 6:
                    min_gain, max_dist = -0.2, 0.9**2
                else:
                    min_gain, max_dist = -0.12, 0.8**2
                if gain < min_gain:
                    continue
                if new_dist > max_dist:
                    continue
            if score > best_score:
                best_score = score
                best_i = i

        if best_i is None:
            for nbr in hex_neighbors(*gap):
                if nbr not in occupied:
                    continue
                i = seat_at(assigned_pos, nbr)
                if i is None or is_ni_constituency(constituencies[i]):
                    continue
                if historic_norm(constituencies[i]["name"]) in manual:
                    continue
                vac_n = neighbor_occupied_count(nbr, occupied)
                score = float(gap_n - vac_n)
                if score > best_score:
                    best_score = score
                    best_i = i

        if best_i is None:
            continue
        old = assigned_pos[best_i]
        occupied.discard(old)
        assigned_pos[best_i] = gap
        occupied.add(gap)
        return True
    return False


def try_hole_action(
    constituencies: list[dict],
    assigned_pos: dict[int, tuple[int, int]],
    occupied: set[tuple[int, int]],
    england_coords: set[tuple[int, int]],
    scot_coords: set[tuple[int, int]],
    wales_coords: set[tuple[int, int]],
    gap: tuple[int, int],
) -> bool:
    for coords in (england_coords, scot_coords, wales_coords):
        if gap in coords and gap not in occupied:
            if fill_interior_hole_via_chain(
                constituencies,
                assigned_pos,
                occupied,
                coords,
                gap,
            ):
                return True
            break
    return fill_single_surrounded_hole(
        constituencies,
        assigned_pos,
        occupied,
        gap,
    )


def zero_surrounded_holes(
    constituencies: list[dict],
    assigned_pos: dict[int, tuple[int, int]],
    occupied: set[tuple[int, int]],
    england_coords: set[tuple[int, int]],
    scot_coords: set[tuple[int, int]],
    wales_coords: set[tuple[int, int]],
    cell_geos: dict[tuple[int, int], tuple[float, float]],
    geo_lookup: dict[str, tuple[float, float]],
    *,
    max_iterations: int = 400,
) -> None:
    """Drive surrounded-hole count to zero using chain fills and local slides."""
    for _ in range(max_iterations):
        if count_surrounded_holes(occupied) == 0:
            return
        holes = sorted(
            (
                g
                for g in adjacent_empty_cells(occupied)
                if neighbor_occupied_count(g, occupied) >= 5
            ),
            key=lambda c: (-neighbor_occupied_count(c, occupied), c),
        )
        moved = False
        before = surrounded_hole_score(occupied)

        for gap in holes:
            if apply_if_fewer_holes(
                assigned_pos,
                occupied,
                lambda gap=gap: try_hole_action(
                    constituencies,
                    assigned_pos,
                    occupied,
                    england_coords,
                    scot_coords,
                    wales_coords,
                    gap,
                ),
            ):
                moved = True
                break

        if moved:
            continue

        for gap_a in holes:
            snap_a = snapshot_positions(assigned_pos, occupied)
            if not try_hole_action(
                constituencies,
                assigned_pos,
                occupied,
                england_coords,
                scot_coords,
                wales_coords,
                gap_a,
            ):
                continue
            mid = surrounded_hole_score(occupied)
            if mid < before:
                moved = True
                break
            holes_b = sorted(
                (
                    g
                    for g in adjacent_empty_cells(occupied)
                    if neighbor_occupied_count(g, occupied) >= 5
                ),
                key=lambda c: (-neighbor_occupied_count(c, occupied), c),
            )
            for gap_b in holes_b:
                snap_mid = snapshot_positions(assigned_pos, occupied)
                if (
                    try_hole_action(
                        constituencies,
                        assigned_pos,
                        occupied,
                        england_coords,
                        scot_coords,
                        wales_coords,
                        gap_b,
                    )
                    and surrounded_hole_score(occupied) < before
                ):
                    moved = True
                    break
                restore_positions(assigned_pos, occupied, snap_mid)
            if moved:
                break
            restore_positions(assigned_pos, occupied, snap_a)

        if not moved:
            for gap_a in holes:
                snap_a = snapshot_positions(assigned_pos, occupied)
                if not try_hole_action(
                    constituencies,
                    assigned_pos,
                    occupied,
                    england_coords,
                    scot_coords,
                    wales_coords,
                    gap_a,
                ):
                    continue
                holes_b = sorted(
                    (
                        g
                        for g in adjacent_empty_cells(occupied)
                        if neighbor_occupied_count(g, occupied) >= 5
                    ),
                    key=lambda c: (-neighbor_occupied_count(c, occupied), c),
                )
                for gap_b in holes_b:
                    snap_b = snapshot_positions(assigned_pos, occupied)
                    if not try_hole_action(
                        constituencies,
                        assigned_pos,
                        occupied,
                        england_coords,
                        scot_coords,
                        wales_coords,
                        gap_b,
                    ):
                        continue
                    if surrounded_hole_score(occupied) < before:
                        moved = True
                        break
                    holes_c = sorted(
                        (
                            g
                            for g in adjacent_empty_cells(occupied)
                            if neighbor_occupied_count(g, occupied) >= 5
                        ),
                        key=lambda c: (-neighbor_occupied_count(c, occupied), c),
                    )
                    for gap_c in holes_c:
                        if (
                            try_hole_action(
                                constituencies,
                                assigned_pos,
                                occupied,
                                england_coords,
                                scot_coords,
                                wales_coords,
                                gap_c,
                            )
                            and surrounded_hole_score(occupied) < before
                        ):
                            moved = True
                            break
                        restore_positions(assigned_pos, occupied, snap_b)
                    if moved:
                        break
                    restore_positions(assigned_pos, occupied, snap_b)
                if moved:
                    break
                restore_positions(assigned_pos, occupied, snap_a)

        if not moved:
            manual = manual_hex_frozen()
            for gap in holes:
                for nbr in hex_neighbors(*gap):
                    if nbr not in occupied:
                        continue
                    for outward in hex_neighbors(*nbr):
                        if outward in occupied or outward in hex_neighbors(*gap):
                            continue
                        i = seat_at(assigned_pos, nbr)
                        if i is None or is_ni_constituency(constituencies[i]):
                            continue
                        if historic_norm(constituencies[i]["name"]) in manual:
                            continue
                        snap = snapshot_positions(assigned_pos, occupied)
                        old = assigned_pos[i]
                        occupied.discard(old)
                        assigned_pos[i] = outward
                        occupied.add(outward)
                        if surrounded_hole_score(occupied) < before:
                            moved = True
                            break
                        restore_positions(assigned_pos, occupied, snap)
                    if moved:
                        break
                if moved:
                    break

        if not moved:
            break

    stall = 0
    while count_surrounded_holes(occupied) > 0 and stall < 32:
        holes = sorted(
            (
                g
                for g in adjacent_empty_cells(occupied)
                if neighbor_occupied_count(g, occupied) >= 5
            ),
            key=lambda c: (-neighbor_occupied_count(c, occupied), c),
        )
        before = count_surrounded_holes(occupied)
        if not fill_single_surrounded_hole(
            constituencies, assigned_pos, occupied, holes[0]
        ):
            break
        after = count_surrounded_holes(occupied)
        if after >= before:
            stall += 1
        else:
            stall = 0


def pack_scaffold_holes(
    constituencies: list[dict],
    assigned_pos: dict[int, tuple[int, int]],
    occupied: set[tuple[int, int]],
    england_coords: set[tuple[int, int]],
    scot_coords: set[tuple[int, int]],
    wales_coords: set[tuple[int, int]],
    cell_geos: dict[tuple[int, int], tuple[float, float]],
    geo_lookup: dict[str, tuple[float, float]],
    *,
    max_zero_iters: int = 64,
) -> None:
    """Fill interior scaffold holes after manual pins, respecting pinned seats."""
    eliminate_interior_scaffold_gaps(
        constituencies,
        assigned_pos,
        occupied,
        england_coords,
    )
    zero_surrounded_holes(
        constituencies,
        assigned_pos,
        occupied,
        england_coords,
        scot_coords,
        wales_coords,
        cell_geos,
        geo_lookup,
        max_iterations=max_zero_iters,
    )
    for _ in range(32):
        if not eliminate_surrounded_holes(
            constituencies,
            assigned_pos,
            occupied,
            cell_geos,
            geo_lookup,
        ):
            break
    eliminate_interior_scaffold_gaps(
        constituencies,
        assigned_pos,
        occupied,
        england_coords,
    )


def final_repack_gb_scaffold(
    constituencies: list[dict],
    assigned_pos: dict[int, tuple[int, int]],
    occupied: set[tuple[int, int]],
    england_coords: set[tuple[int, int]],
    scot_coords: set[tuple[int, int]],
    wales_coords: set[tuple[int, int]],
    ni_coords: set[tuple[int, int]],
    cell_geos: dict[tuple[int, int], tuple[float, float]],
    geo_lookup: dict[str, tuple[float, float]],
    by_name: dict[str, dict],
) -> None:
    """1983-style solid finish: cascade scaffold gaps outward, then eliminate interior holes."""
    gb_coords = england_coords | scot_coords | wales_coords

    repair_scaffold_bridges(
        constituencies,
        assigned_pos,
        occupied,
        gb_coords,
        cell_geos,
        geo_lookup,
    )

    eliminate_interior_scaffold_gaps(
        constituencies,
        assigned_pos,
        occupied,
        england_coords,
    )

    zero_surrounded_holes(
        constituencies,
        assigned_pos,
        occupied,
        england_coords,
        scot_coords,
        wales_coords,
        cell_geos,
        geo_lookup,
        max_iterations=400,
    )

    eliminate_interior_scaffold_gaps(
        constituencies,
        assigned_pos,
        occupied,
        england_coords,
    )


def pack_gb_scaffold_solid(
    constituencies: list[dict],
    assigned_pos: dict[int, tuple[int, int]],
    occupied: set[tuple[int, int]],
    england_coords: set[tuple[int, int]],
    scot_coords: set[tuple[int, int]],
    wales_coords: set[tuple[int, int]],
    ni_coords: set[tuple[int, int]],
    cell_geos: dict[tuple[int, int], tuple[float, float]],
    geo_lookup: dict[str, tuple[float, float]],
    by_name: dict[str, dict],
) -> None:
    final_repack_gb_scaffold(
        constituencies,
        assigned_pos,
        occupied,
        england_coords,
        scot_coords,
        wales_coords,
        ni_coords,
        cell_geos,
        geo_lookup,
        by_name,
    )


def correct_severe_geo_outliers(
    constituencies: list[dict],
    assigned_pos: dict[int, tuple[int, int]],
    occupied: set[tuple[int, int]],
    england_coords: set[tuple[int, int]],
    cell_geos: dict[tuple[int, int], tuple[float, float]],
    geo_lookup: dict[str, tuple[float, float]],
    by_name: dict[str, dict],
    scot_coords: set[tuple[int, int]],
    wales_coords: set[tuple[int, int]],
    ni_coords: set[tuple[int, int]],
    delta_threshold: float = 1.0,
    min_improvement: float = 0.2,
) -> None:
    """Move seats back toward their 1983 centroid when geo fit is poor."""
    pinned = all_pinned_names()
    england_with_geo = [coord for coord in england_coords if coord in cell_geos]

    for _ in range(12):
        moved = False
        candidates: list[tuple[float, int]] = []
        for i, c in enumerate(constituencies):
            if c.get("nation") != "england":
                continue
            if historic_norm(c["name"]) in pinned:
                continue
            if delta_threshold < 1.0 and historic_norm(c["name"]) in HISTORIC_TO_2024:
                continue
            hg = geo_for_name(c["name"], geo_lookup)
            if not hg:
                continue
            cur = assigned_pos.get(i)
            if not cur or cur not in cell_geos:
                continue
            cur_d = geo_deg_distance(hg, cell_geos[cur])
            nearest_d = min(
                geo_deg_distance(hg, cell_geos[coord]) for coord in england_with_geo
            )
            delta = cur_d - nearest_d
            if delta < delta_threshold:
                continue
            candidates.append((delta, i))

        for _delta, i in sorted(candidates, reverse=True):
            c = constituencies[i]
            hg = geo_for_name(c["name"], geo_lookup)
            if not hg:
                continue
            cur = assigned_pos.get(i)
            if not cur or cur not in cell_geos:
                continue
            cur_d = geo_deg_distance(hg, cell_geos[cur])
            nearest_d = min(
                geo_deg_distance(hg, cell_geos[coord]) for coord in england_with_geo
            )
            if cur_d - nearest_d < delta_threshold:
                continue

            if delta_threshold < 1.0 and historic_norm(c["name"]) in HISTORIC_TO_2024:
                continue

            anchor = lookup_2024_name(c["name"], by_name, "england")
            if anchor and (anchor["q"], anchor["r"]) == cur:
                if delta_threshold >= 1.0 and cur_d - nearest_d < 1.0:
                    continue
                if delta_threshold < 1.0 and cur_d - nearest_d < 0.5:
                    continue

            target: tuple[int, int] | None = None
            if anchor:
                ac = (anchor["q"], anchor["r"])
                if ac in cell_geos:
                    ad = geo_deg_distance(hg, cell_geos[ac])
                    if ad <= nearest_d + 0.2:
                        target = ac
            if target is None:
                target = min(
                    england_with_geo,
                    key=lambda coord: geo_deg_distance(hg, cell_geos[coord]),
                )

            forbidden = forbidden_coords(
                c, england_coords, scot_coords, wales_coords, ni_coords
            )
            new_coord: tuple[int, int] | None = None
            if target not in occupied:
                new_coord = target
            else:
                blocker = next(
                    (
                        idx
                        for idx, pos in assigned_pos.items()
                        if pos == target and idx != i
                    ),
                    None,
                )
                if blocker is not None and cur != target:
                    if historic_norm(constituencies[blocker]["name"]) in pinned:
                        blocker = None
                if blocker is not None and cur != target:
                    bh = geo_for_name(constituencies[blocker]["name"], geo_lookup)
                    if bh and cur in cell_geos:
                        swap_score = geo_deg_distance(bh, cell_geos[cur]) + geo_deg_distance(
                            hg, cell_geos[target]
                        )
                        keep_score = geo_deg_distance(bh, cell_geos[target]) + cur_d
                        if swap_score < keep_score - 0.05:
                            occupied.discard(target)
                            occupied.discard(cur)
                            assigned_pos[blocker] = cur
                            assigned_pos[i] = target
                            occupied.add(cur)
                            occupied.add(target)
                            moved = True
                            continue
                pool = occupied - {cur}
                new_coord = overflow_beside_anchor(
                    target, pool, forbidden, hg, cell_geos
                )
            if not new_coord or new_coord == cur or new_coord not in cell_geos:
                continue
            new_d = geo_deg_distance(hg, cell_geos[new_coord])
            if new_d >= cur_d - min_improvement:
                continue
            occupied.discard(cur)
            assigned_pos[i] = new_coord
            occupied.add(new_coord)
            moved = True
        if not moved:
            break


def geo_viable_coord(
    c: dict,
    coord: tuple[int, int],
    cell_geos: dict[tuple[int, int], tuple[float, float]],
    geo_lookup: dict[str, tuple[float, float]],
    nation_coords: set[tuple[int, int]],
    *,
    max_slip: float = 0.22,
) -> bool:
    """Reject relocations that leave a seat on the wrong nation band or far from its geo fit."""
    if coord not in cell_geos or coord not in nation_coords:
        return False
    hg = geo_for_name(c["name"], geo_lookup)
    if not hg:
        return True
    nearest = min(
        geo_deg_distance(hg, cell_geos[nc])
        for nc in nation_coords
        if nc in cell_geos
    )
    return geo_deg_distance(hg, cell_geos[coord]) <= nearest + max_slip


def nation_coords_for(
    c: dict,
    england_coords: set[tuple[int, int]],
    scot_coords: set[tuple[int, int]],
    wales_coords: set[tuple[int, int]],
    ni_coords: set[tuple[int, int]],
) -> set[tuple[int, int]]:
    nation = c.get("nation")
    if nation == "scotland":
        return scot_coords
    if nation == "wales":
        return wales_coords
    if nation == "northern-ireland":
        return ni_coords
    return england_coords


def relocate_displaced_seat(
    seat_index: int,
    assigned_pos: dict[int, tuple[int, int]],
    constituencies: list[dict],
    occupied: set[tuple[int, int]],
    cell_geos: dict[tuple[int, int], tuple[float, float]],
    geo_lookup: dict[str, tuple[float, float]],
    by_name: dict[str, dict],
    *,
    exclude: set[tuple[int, int]] | None = None,
    england_coords: set[tuple[int, int]] | None = None,
    scot_coords: set[tuple[int, int]] | None = None,
    wales_coords: set[tuple[int, int]] | None = None,
    ni_coords: set[tuple[int, int]] | None = None,
) -> bool:
    """Move a seat to a nearby empty hex ranked by geographic fit."""
    c = constituencies[seat_index]
    nation_pool = (
        nation_coords_for(c, england_coords or set(), scot_coords or set(), wales_coords or set(), ni_coords or set())
        if england_coords is not None
        else set(cell_geos)
    )
    hg = geo_for_name(c["name"], geo_lookup)
    anchor = anchor_coord(c, by_name) or assigned_pos.get(seat_index)
    if not anchor:
        return False
    cur = assigned_pos.get(seat_index)
    exclude = exclude or set()
    pool = {coord for coord in occupied if coord not in exclude}
    if cur:
        pool.discard(cur)
    relocation = overflow_beside_anchor(
        anchor, pool, set(), hg, cell_geos
    )
    if relocation and not geo_viable_coord(
        c, relocation, cell_geos, geo_lookup, nation_pool
    ):
        relocation = None
    if not relocation or relocation == cur or relocation in exclude:
        candidates = ranked_cells_for(
            c,
            {
                coord
                for coord in cell_geos
                if coord not in occupied and coord not in exclude and coord in nation_pool
            },
            cell_geos,
            geo_lookup,
            by_name,
        )
        relocation = next(
            (
                coord
                for coord in candidates
                if geo_viable_coord(c, coord, cell_geos, geo_lookup, nation_pool)
            ),
            None,
        )
    if not relocation or relocation == cur or relocation in exclude:
        return False
    if cur:
        occupied.discard(cur)
    assigned_pos[seat_index] = relocation
    occupied.add(relocation)
    return True


def apply_manual_hex_overrides(
    assigned_pos: dict[int, tuple[int, int]],
    constituencies: list[dict],
    occupied: set[tuple[int, int]],
    cell_geos: dict[tuple[int, int], tuple[float, float]] | None = None,
    geo_lookup: dict[str, tuple[float, float]] | None = None,
    by_name: dict[str, dict] | None = None,
    *,
    england_coords: set[tuple[int, int]] | None = None,
    scot_coords: set[tuple[int, int]] | None = None,
    wales_coords: set[tuple[int, int]] | None = None,
    ni_coords: set[tuple[int, int]] | None = None,
) -> None:
    """Pin specific historic seats to hexes where the 2024 scaffold geometry is misleading."""
    global _MANUAL_PINS_APPLIED
    geo_ready = bool(cell_geos and geo_lookup and by_name)
    pin_jobs: list[tuple[int, tuple[int, int]]] = []
    for i, c in enumerate(constituencies):
        key = historic_norm(c["name"])
        coord = MANUAL_HEX.get(key) or MANUAL_HEX.get(norm_name(c.get("name", "")))
        if coord is not None:
            pin_jobs.append((i, coord))
    for i, new_coord in sorted(pin_jobs, key=lambda job: job[0]):
        c = constituencies[i]
        old_coord = assigned_pos.get(i)
        if old_coord == new_coord:
            continue
        if new_coord in occupied and assigned_pos.get(i) != new_coord:
            blocker = next(
                (idx for idx, pos in assigned_pos.items() if pos == new_coord and idx != i),
                None,
            )
            if blocker is None:
                if not old_coord:
                    continue
            elif geo_ready and england_coords is not None:
                occupied.discard(new_coord)
                blocker_c = constituencies[blocker]
                blocker_pool = nation_coords_for(
                    blocker_c, england_coords, scot_coords, wales_coords, ni_coords
                )
                if not relocate_displaced_seat(
                    blocker,
                    assigned_pos,
                    constituencies,
                    occupied,
                    cell_geos,
                    geo_lookup,
                    by_name,
                    exclude={new_coord},
                    england_coords=england_coords,
                    scot_coords=scot_coords,
                    wales_coords=wales_coords,
                    ni_coords=ni_coords,
                ):
                    if old_coord and old_coord not in occupied:
                        bg = geo_for_name(blocker_c["name"], geo_lookup)
                        swap_ok = False
                        if (
                            bg
                            and old_coord in cell_geos
                            and new_coord in cell_geos
                            and geo_viable_coord(
                                blocker_c, old_coord, cell_geos, geo_lookup, blocker_pool
                            )
                        ):
                            swap_ok = geo_deg_distance(bg, cell_geos[old_coord]) <= (
                                geo_deg_distance(bg, cell_geos[new_coord]) + 0.12
                            )
                        if swap_ok:
                            assigned_pos[blocker] = old_coord
                            occupied.add(old_coord)
                        else:
                            occupied.add(new_coord)
                            continue
                    else:
                        occupied.add(new_coord)
                        continue
            else:
                continue
        elif old_coord:
            occupied.discard(old_coord)
        assigned_pos[i] = new_coord
        occupied.add(new_coord)
    _MANUAL_PINS_APPLIED = True


def fix_coast_band_displaced(
    constituencies: list[dict],
    assigned_pos: dict[int, tuple[int, int]],
    occupied: set[tuple[int, int]],
    cell_geos: dict[tuple[int, int], tuple[float, float]],
    geo_lookup: dict[str, tuple[float, float]],
    by_name: dict[str, dict],
    england_coords: set[tuple[int, int]],
    scot_coords: set[tuple[int, int]],
    wales_coords: set[tuple[int, int]],
    ni_coords: set[tuple[int, int]],
    *,
    max_r: int = -43,
) -> None:
    """Move unpinned inland seats off the south-coast hex band after manual pins."""
    pinned = all_pinned_names()
    england_with_geo = [coord for coord in cell_geos]
    for i, c in enumerate(constituencies):
        if c.get("nation") != "england":
            continue
        if historic_norm(c["name"]) in pinned:
            continue
        cur = assigned_pos.get(i)
        if not cur or cur[1] > max_r:
            continue
        hg = geo_for_name(c["name"], geo_lookup)
        if not hg or cur not in cell_geos:
            continue
        cur_d = geo_deg_distance(hg, cell_geos[cur])
        nearest_d = min(
            geo_deg_distance(hg, cell_geos[coord]) for coord in england_with_geo
        )
        if cur_d - nearest_d < 0.35:
            continue
        relocate_displaced_seat(
            i,
            assigned_pos,
            constituencies,
            occupied,
            cell_geos,
            geo_lookup,
            by_name,
            england_coords=england_coords,
            scot_coords=scot_coords,
            wales_coords=wales_coords,
            ni_coords=ni_coords,
        )


def build_scaffold_geo(
    geo_lookup: dict[str, tuple[float, float]],
    scaffold_coords: set[tuple[int, int]],
) -> dict[tuple[int, int], tuple[float, float]]:
    """Legacy wrapper — prefer build_cell_geos."""
    return build_cell_geos(geo_lookup, scaffold_coords)


def build_scaffold() -> tuple[
    dict[str, dict],
    set[tuple[int, int]],
    set[tuple[int, int]],
    set[tuple[int, int]],
    set[tuple[int, int]],
    set[tuple[int, int]],
    set[tuple[int, int]],
]:
    data = json.loads(SCAFFOLD_HEX.read_text(encoding="utf-8"))
    by_name: dict[str, dict] = {}
    scaffold_coords: set[tuple[int, int]] = set()
    ni_coords: set[tuple[int, int]] = set()
    scot_coords: set[tuple[int, int]] = set()
    wales_coords: set[tuple[int, int]] = set()
    england_coords: set[tuple[int, int]] = set()
    gb_coords: set[tuple[int, int]] = set()
    for code, cell in data["hexes"].items():
        region = str(cell.get("region") or "")
        pos = {
            "q": cell["q"],
            "r": cell["r"],
            "code": code,
            "n": cell.get("n", ""),
            "region": region,
            "nation": region_to_nation(region),
        }
        coord = (pos["q"], pos["r"])
        scaffold_coords.add(coord)
        if region.startswith("N"):
            ni_coords.add(coord)
        elif region.startswith("S"):
            scot_coords.add(coord)
            gb_coords.add(coord)
        elif region.startswith("W"):
            wales_coords.add(coord)
            gb_coords.add(coord)
        else:
            england_coords.add(coord)
            gb_coords.add(coord)
        for key in alias_keys(cell.get("n", "")):
            by_name[key] = pos
    return by_name, scaffold_coords, ni_coords, gb_coords, scot_coords, wales_coords, england_coords


def lookup_2024_name(
    name: str, by_name: dict[str, dict], nation: str | None = None
) -> dict | None:
    def nation_ok(pos: dict) -> bool:
        if not nation or not pos.get("nation"):
            return True
        return pos["nation"] == nation

    base = historic_norm(name)
    mapped = HISTORIC_TO_2024.get(base)
    if mapped:
        for key in alias_keys(mapped):
            if key in by_name and nation_ok(by_name[key]):
                return by_name[key]
    for key in alias_keys(name):
        fixed = historic_norm(key)
        if fixed != key:
            for fk in alias_keys(fixed):
                if fk in by_name and nation_ok(by_name[fk]):
                    return by_name[fk]
        if key in by_name and nation_ok(by_name[key]):
            return by_name[key]
    pos = fuzzy_2024_match(name, by_name)
    if pos and nation_ok(pos):
        return pos
    return None


def ring_centroid_area(coords: list[list[float]]) -> tuple[float, float, float]:
    if len(coords) < 3:
        return 0.0, 0.0, 0.0
    area2 = cx = cy = 0.0
    for (x1, y1), (x2, y2) in zip(coords, coords[1:] + coords[:1]):
        cross = x1 * y2 - x2 * y1
        area2 += cross
        cx += (x1 + x2) * cross
        cy += (y1 + y2) * cross
    if abs(area2) < 1e-12:
        xs = [p[0] for p in coords]
        ys = [p[1] for p in coords]
        return sum(xs) / len(xs), sum(ys) / len(ys), 0.0
    return cx / (3.0 * area2), cy / (3.0 * area2), area2 / 2.0


def feature_centroid(feature: dict) -> tuple[float, float]:
    geom = feature["geometry"]
    polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    total = cx = cy = 0.0
    for poly in polys:
        ring = poly[0]
        px, py, area = ring_centroid_area(ring)
        weight = abs(area) or 1.0
        cx += px * weight
        cy += py * weight
        total += weight
    return cx / total, cy / total


def _merge_geo_features(lookup: dict[str, tuple[float, float]], path: Path) -> None:
    if not path.exists():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    for feature in data.get("features", []):
        props = feature.get("properties") or {}
        name = props.get("Name") or props.get("name") or ""
        if not name:
            continue
        lon, lat = feature_centroid(feature)
        for key in alias_keys(name):
            lookup[key] = (lon, lat)
            fixed = historic_norm(key)
            if fixed != key:
                lookup[fixed] = (lon, lat)


def _nation_from_geo_filename(filename: str) -> str:
    low = filename.lower()
    if "scotland" in low:
        return "scotland"
    if "wales" in low:
        return "wales"
    if "northern" in low:
        return "northern-ireland"
    return "england"


def load_geo_nation_index(boundary: str = "1983") -> dict[str, str]:
    """Constituency name → nation from boundary GeoJSON file membership."""
    index: dict[str, str] = {}
    nation_files = BOUNDARY_GEO_FILES.get(boundary, BOUNDARY_GEO_FILES["1983"])
    for filename in nation_files:
        path = GEOJSON_DIR / filename
        if not path.exists():
            continue
        nation = _nation_from_geo_filename(filename)
        data = json.loads(path.read_text(encoding="utf-8"))
        for feature in data.get("features", []):
            props = feature.get("properties") or {}
            name = props.get("Name") or props.get("name") or ""
            if not name:
                continue
            for key in alias_keys(name):
                index[key] = nation
                index[historic_norm(key)] = nation
    return index


def fix_constituency_nations(
    constituencies: list[dict], nation_index: dict[str, str]
) -> None:
    """Correct nation labels using boundary GeoJSON (fixes HoC scrape typos like [S] for [E])."""
    for c in constituencies:
        if is_ni_constituency(c):
            c["nation"] = "northern-ireland"
            continue
        for key in reference_keys(c["name"]):
            nation = nation_index.get(key) or nation_index.get(historic_norm(key))
            if nation:
                c["nation"] = nation
                break


def load_geo_lookup(boundary: str = "1983") -> dict[str, tuple[float, float]]:
    lookup: dict[str, tuple[float, float]] = {}
    nation_files = BOUNDARY_GEO_FILES.get(boundary, BOUNDARY_GEO_FILES["1983"])
    for filename in nation_files:
        _merge_geo_features(lookup, GEOJSON_DIR / filename)
    if lookup:
        return lookup
    fallback = GEOJSON_DIR / f"{boundary}-combined.geojson"
    if fallback.exists():
        _merge_geo_features(lookup, fallback)
    if lookup:
        return lookup
    if not GEOJSON.exists():
        return {}
    _merge_geo_features(lookup, GEOJSON)
    return lookup


def load_reference_placements(reference_id: str) -> dict[str, tuple[int, int]]:
    """Name → (q, r) from a previously imported election (typically 1983)."""
    path = OUT_DIR / f"{reference_id}.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    placements: dict[str, tuple[int, int]] = {}
    for c in data.get("constituencies") or []:
        q, r = c.get("q"), c.get("r")
        if q is None or r is None:
            continue
        coord = (q, r)
        for key in reference_keys(c.get("name", "")):
            placements.setdefault(key, coord)
    return placements


def build_reference_coord_names(reference_id: str) -> dict[tuple[int, int], str]:
    """(q, r) → display name from a reference election (typically 1983)."""
    path = OUT_DIR / f"{reference_id}.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[tuple[int, int], str] = {}
    for c in data.get("constituencies") or []:
        q, r = c.get("q"), c.get("r")
        if q is None or r is None:
            continue
        out.setdefault((q, r), c.get("name", ""))
    return out


def successor_geo_plausible(
    seat_name: str,
    successor_name: str,
    seat_geo_lookup: dict[str, tuple[float, float]],
    succ_geo_lookup: dict[str, tuple[float, float]],
    *,
    max_deg: float = MAX_SUCCESSOR_GEO_DEG,
) -> bool:
    """Reject successor labels whose centroids are implausibly far from the seat."""
    seat_geo = geo_for_name(seat_name, seat_geo_lookup)
    succ_geo = geo_for_name(successor_name, succ_geo_lookup)
    if not seat_geo or not succ_geo:
        return True
    dx = seat_geo[0] - succ_geo[0]
    dy = seat_geo[1] - succ_geo[1]
    return dx * dx + dy * dy <= max_deg * max_deg


def filter_plausible_successors(
    seat_name: str,
    successors: list[str],
    seat_geo_lookup: dict[str, tuple[float, float]],
    succ_geo_lookup: dict[str, tuple[float, float]],
) -> list[str]:
    plausible = [
        s
        for s in successors
        if successor_geo_plausible(seat_name, s, seat_geo_lookup, succ_geo_lookup)
    ]
    return plausible or successors


def seed_from_reference_election(
    constituencies: list[dict],
    reference_placements: dict[str, tuple[int, int]],
    assigned_pos: dict[int, tuple[int, int]],
    occupied: set[tuple[int, int]],
) -> frozenset[str]:
    """Seed unchanged-name seats from the reference election (initial layout only)."""
    pinned: set[str] = set()
    for i, c in enumerate(constituencies):
        coord = None
        for key in reference_keys(c["name"]):
            if key in reference_placements:
                coord = reference_placements[key]
                break
        if coord is None or coord in occupied:
            continue
        assigned_pos[i] = coord
        occupied.add(coord)
        pinned.add(historic_norm(c["name"]))
    return frozenset(pinned)


def parse_wikipedia_successor_parts(raw: str) -> list[str]:
    """Split and clean a Wikipedia infobox 'Replaced by' field."""
    if not raw:
        return []
    text = raw
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.I | re.S)
    text = re.sub(r"<br\s*/?>", "; ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "; ", text)
    text = re.sub(r"\{\{ubl\|([^}]+)\}\}", r"\1", text, flags=re.I)
    text = re.sub(r"\[\[([^|\]]+)\|([^\]]+)\]\]", r"\2", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    text = text.replace("''", "")
    text = re.sub(r"\([^)]*abolished[^)]*\)", "", text, flags=re.I)
    text = re.sub(r"[{}]", "", text)
    parts: list[str] = []
    for chunk in re.split(r"\s*;\s*|\s+and\s+", text):
        chunk = chunk.strip(" ,.")
        chunk = re.sub(r"\s*\([^)]*\)", "", chunk).strip()
        if not chunk or chunk.startswith("|") or "electorate" in chunk.lower():
            continue
        if chunk.lower() in {"minor part", "majority"}:
            continue
        parts.append(chunk)
    return parts


def load_wikipedia_successor_map(
    reference_seed_id: str = "1983",
) -> dict[str, list[str]]:
    """Load Wikipedia successor chains keyed by historic_norm(abolished seat name)."""
    if reference_seed_id == "feb1974":
        path = SUCCESSOR_MAP_1955_JSON
        name_field = "name1955"
        overrides = SUCCESSOR_OVERRIDES_1955
    else:
        path = SUCCESSOR_MAP_JSON
        name_field = "name1974"
        overrides = SUCCESSOR_OVERRIDES

    out: dict[str, list[str]] = {key: list(names) for key, names in overrides.items()}
    if not path.exists():
        return out
    rows = json.loads(path.read_text(encoding="utf-8"))
    for row in rows:
        name = row.get(name_field, "")
        if not name:
            continue
        key = historic_norm(name)
        if key in overrides:
            continue
        parts = parse_wikipedia_successor_parts(str(row.get("replacedBy", "")))
        if parts:
            out[key] = parts
    return out


def successors_for_seat(name: str, successor_map: dict[str, list[str]]) -> list[str] | None:
    """Resolve Wikipedia successor list, including display-name variants (e.g. Montgomery)."""
    key = historic_norm(name)
    if key in successor_map:
        return successor_map[key]
    for src_key, display in DISPLAY_NAMES.items():
        if historic_norm(display) == key and src_key in successor_map:
            return successor_map[src_key]
    return None


def resolve_reference_placement(
    name: str,
    reference_placements: dict[str, tuple[int, int]],
    *,
    successor_name_aliases: dict[str, str] | None = None,
) -> tuple[int, int] | None:
    """Map a successor label to its hex from the reference election."""
    aliases = successor_name_aliases if successor_name_aliases is not None else SUCCESSOR_NAME_ALIASES
    alias = aliases.get(historic_norm(name))
    if alias:
        for key in alias_keys(alias):
            if key in reference_placements:
                return reference_placements[key]
            hk = historic_norm(key)
            if hk in reference_placements:
                return reference_placements[hk]
    for key in alias_keys(name):
        if key in reference_placements:
            return reference_placements[key]
        hk = historic_norm(key)
        if hk in reference_placements:
            return reference_placements[hk]
    base = historic_norm(name)
    ref_keys = list(reference_placements.keys())
    for match in get_close_matches(base, ref_keys, n=5, cutoff=0.72):
        if meaningful_token_overlap(base, match) or (
            len(base) >= 5 and match.startswith(base[:5])
        ):
            return reference_placements[match]
    for key in ref_keys:
        if base in key or key in base:
            if meaningful_token_overlap(base, key):
                return reference_placements[key]
    return None


def pick_successor_anchor(
    c: dict,
    successors: list[str],
    reference_placements: dict[str, tuple[int, int]],
    geo_lookup: dict[str, tuple[float, float]],
    *,
    successor_name_aliases: dict[str, str] | None = None,
    succ_geo_lookup: dict[str, tuple[float, float]] | None = None,
) -> tuple[int, int] | None:
    """Choose the best-matching reference successor cell for an abolished/renamed seat."""
    succ_geo_lookup = succ_geo_lookup or geo_lookup
    seat_geo = geo_for_name(c["name"], geo_lookup)
    successors = filter_plausible_successors(
        c["name"], successors, geo_lookup, succ_geo_lookup
    )
    candidates: list[tuple[float, tuple[int, int], str]] = []
    for succ in successors:
        coord = resolve_reference_placement(
            succ, reference_placements, successor_name_aliases=successor_name_aliases
        )
        if not coord:
            continue
        if seat_geo:
            succ_geo = geo_for_name(succ, succ_geo_lookup)
            dist = geo_sqdist(seat_geo, succ_geo) if succ_geo else 1e9
        else:
            dist = float(len(candidates))
        candidates.append((dist, coord, succ))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[2]))
    return candidates[0][1]


def seed_from_wikipedia_successors(
    constituencies: list[dict],
    successor_map: dict[str, list[str]],
    reference_placements: dict[str, tuple[int, int]],
    assigned_pos: dict[int, tuple[int, int]],
    occupied: set[tuple[int, int]],
    geo_lookup: dict[str, tuple[float, float]],
    cell_geos: dict[tuple[int, int], tuple[float, float]],
    england_coords: set[tuple[int, int]],
    scot_coords: set[tuple[int, int]],
    wales_coords: set[tuple[int, int]],
    ni_coords: set[tuple[int, int]],
    *,
    successor_name_aliases: dict[str, str] | None = None,
    succ_geo_lookup: dict[str, tuple[float, float]] | None = None,
) -> frozenset[str]:
    """Seed renamed/abolished seats near their Wikipedia successor cells (initial layout only)."""
    succ_geo_lookup = succ_geo_lookup or geo_lookup
    pinned: set[str] = set()
    for i, c in enumerate(constituencies):
        if i in assigned_pos:
            continue
        successors = successors_for_seat(c["name"], successor_map)
        if not successors:
            continue
        successors = filter_plausible_successors(
            c["name"], successors, geo_lookup, succ_geo_lookup
        )
        anchor = pick_successor_anchor(
            c,
            successors,
            reference_placements,
            geo_lookup,
            successor_name_aliases=successor_name_aliases,
            succ_geo_lookup=succ_geo_lookup,
        )
        if not anchor:
            continue
        forbidden = forbidden_coords(
            c, england_coords, scot_coords, wales_coords, ni_coords
        )
        hg = geo_for_name(c["name"], geo_lookup)
        coord: tuple[int, int] | None = None
        best_rank = (1e18, 999, 999)
        for succ in successors:
            succ_anchor = resolve_reference_placement(
                succ,
                reference_placements,
                successor_name_aliases=successor_name_aliases,
            )
            if not succ_anchor:
                continue
            if not successor_geo_plausible(
                c["name"], succ, geo_lookup, succ_geo_lookup
            ):
                continue
            if succ_anchor not in occupied and succ_anchor not in forbidden:
                candidate = succ_anchor
            else:
                candidate = overflow_beside_anchor(
                    succ_anchor, occupied, forbidden, hg, cell_geos
                )
            if not candidate:
                continue
            succ_geo = geo_for_name(succ, succ_geo_lookup)
            consistency = (
                geo_sqdist(hg, succ_geo) if hg and succ_geo else 1e9
            )
            anchor_dist = hex_distance(*candidate, *succ_anchor)
            cell_rank = (
                geo_sqdist(hg, cell_geos[candidate])
                if hg and candidate in cell_geos
                else anchor_dist
            )
            rank = (consistency, anchor_dist, cell_rank)
            if rank < best_rank:
                best_rank = rank
                coord = candidate
        if not coord:
            continue
        assigned_pos[i] = coord
        occupied.add(coord)
        pinned.add(historic_norm(c["name"]))
    return frozenset(pinned)


def mercator_y(lat: float) -> float:
    lat = max(min(lat, 85.0), -85.0)
    return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def is_ni_constituency(c: dict) -> bool:
    if c.get("nation") == "northern-ireland":
        return True
    if c.get("party") in NI_PARTIES:
        return True
    n = norm_name(c.get("name", ""))
    return any(h in n for h in NI_NAME_HINTS)


def nation_pool(
    c: dict,
    ni_coords: set[tuple[int, int]],
    scot_coords: set[tuple[int, int]],
    wales_coords: set[tuple[int, int]],
    england_coords: set[tuple[int, int]],
    gb_coords: set[tuple[int, int]],
) -> set[tuple[int, int]]:
    if is_ni_constituency(c):
        return ni_coords
    nation = c.get("nation")
    if nation == "scotland":
        return scot_coords
    if nation == "wales":
        return wales_coords
    if nation == "england":
        return england_coords
    return gb_coords


def forbidden_coords(
    c: dict,
    england_coords: set[tuple[int, int]],
    scot_coords: set[tuple[int, int]],
    wales_coords: set[tuple[int, int]],
    ni_coords: set[tuple[int, int]],
) -> set[tuple[int, int]]:
    if is_ni_constituency(c):
        return england_coords | scot_coords | wales_coords
    nation = c.get("nation")
    if nation == "scotland":
        return england_coords | wales_coords | ni_coords
    if nation == "wales":
        return england_coords | scot_coords | ni_coords
    if nation == "england":
        return scot_coords | wales_coords | ni_coords
    return set()


def overflow_beside_anchor(
    anchor: tuple[int, int],
    occupied: set[tuple[int, int]],
    forbidden: set[tuple[int, int]],
    geo_hint: tuple[float, float] | None = None,
    cell_geos: dict[tuple[int, int], tuple[float, float]] | None = None,
) -> tuple[int, int] | None:
    """Place an overflow seat in expanding rings around its 2024 anchor cell."""
    if anchor not in occupied and anchor not in forbidden:
        return anchor

    def rank(candidate: tuple[int, int]) -> tuple:
        hex_d = hex_distance(*anchor, *candidate)
        if geo_hint and cell_geos:
            if candidate in cell_geos:
                geo_d = geo_sqdist(geo_hint, cell_geos[candidate])
            elif anchor in cell_geos:
                # Rough bearing: prefer neighbours that move toward the historic centroid
                geo_d = geo_sqdist(geo_hint, cell_geos[anchor]) + hex_d * 0.05
            else:
                geo_d = hex_d
        else:
            geo_d = hex_d
        return (hex_d, geo_d, candidate)

    visited: set[tuple[int, int]] = {anchor}
    frontier = {anchor}
    while frontier:
        candidates: list[tuple[int, int]] = []
        next_frontier: set[tuple[int, int]] = set()
        for coord in frontier:
            for nbr in hex_neighbors(*coord):
                if nbr in forbidden or nbr in visited:
                    continue
                visited.add(nbr)
                if nbr not in occupied:
                    candidates.append(nbr)
                else:
                    next_frontier.add(nbr)
        if candidates:
            return min(candidates, key=rank)
        frontier = next_frontier
    return None


def nearest_free_cell(
    target: tuple[int, int],
    occupied: set[tuple[int, int]],
    allowed: set[tuple[int, int]],
    forbidden: set[tuple[int, int]] | None = None,
) -> tuple[int, int] | None:
    forbidden = forbidden or set()
    if target in allowed and target not in occupied:
        return target
    free_in_region = sorted(
        (coord for coord in allowed if coord not in occupied),
        key=lambda coord: (hex_distance(*target, *coord), coord),
    )
    if free_in_region:
        return free_in_region[0]
    queue = deque(sorted(allowed))
    visited = set(allowed)
    while queue:
        q, r = queue.popleft()
        for nbr in hex_neighbors(q, r):
            if nbr in visited or nbr in forbidden:
                continue
            visited.add(nbr)
            if nbr not in occupied:
                return nbr
            queue.append(nbr)
    return None


def ranked_cells_for(
    c: dict,
    pool: set[tuple[int, int]],
    cell_geos: dict[tuple[int, int], tuple[float, float]],
    geo_lookup: dict[str, tuple[float, float]],
    by_name: dict[str, dict],
) -> list[tuple[int, int]]:
    pos = lookup_2024_name(c["name"], by_name, c.get("nation"))
    if pos:
        anchor = (pos["q"], pos["r"])
    else:
        anchor = None
    hg = geo_for_name(c["name"], geo_lookup)
    coords = [coord for coord in pool if coord in cell_geos]
    if hg:
        coords.sort(key=lambda coord: (geo_sqdist(hg, cell_geos[coord]), coord))
    elif anchor:
        coords.sort(key=lambda coord: (hex_distance(*anchor, *coord), coord))
    if anchor and anchor in pool and anchor not in coords:
        coords.insert(0, anchor)
    elif anchor and anchor in coords:
        coords.remove(anchor)
        coords.insert(0, anchor)
    return coords


def geo_sqdist(
    a: tuple[float, float], b: tuple[float, float]
) -> float:
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


def assign_nation_by_geo(
    indices: list[int],
    constituencies: list[dict],
    pool: set[tuple[int, int]],
    cell_geos: dict[tuple[int, int], tuple[float, float]],
    geo_lookup: dict[str, tuple[float, float]],
    by_name: dict[str, dict],
    occupied: set[tuple[int, int]],
    assigned_pos: dict[int, tuple[int, int]],
    england_coords: set[tuple[int, int]],
    scot_coords: set[tuple[int, int]],
    wales_coords: set[tuple[int, int]],
    ni_coords: set[tuple[int, int]],
) -> None:
    """Assign historic seats within a nation using anchor names, then geographic fit."""
    unassigned = set(indices)

    # Pass A — explicit historic→2024 anchors (Wikipedia / boundary successors)
    anchor_claims: dict[tuple[int, int], list[tuple[float, int]]] = {}
    for i in list(unassigned):
        c = constituencies[i]
        anchor_pos = lookup_2024_name(c["name"], by_name, c.get("nation"))
        if not anchor_pos:
            continue
        coord = (anchor_pos["q"], anchor_pos["r"])
        if coord not in pool:
            continue
        hg = geo_for_name(c["name"], geo_lookup)
        score = 0.0 if hg and coord in cell_geos else 0.0
        if hg and coord in cell_geos:
            score = geo_sqdist(hg, cell_geos[coord])
        anchor_claims.setdefault(coord, []).append((score, i))
    for coord, claims in anchor_claims.items():
        if coord in occupied:
            continue
        _score, winner = min(claims, key=lambda x: (x[0], x[1]))
        assigned_pos[winner] = coord
        occupied.add(coord)
        unassigned.discard(winner)

    # Pass B — each remaining cell gets the closest unassigned seat by 1983 centroid
    remaining_pool = {coord for coord in pool if coord not in occupied and coord in cell_geos}
    cell_rankings: dict[tuple[int, int], list[tuple[float, int]]] = {
        coord: [] for coord in remaining_pool
    }
    for i in unassigned:
        c = constituencies[i]
        if historic_anchor_taken(c, occupied, by_name):
            continue
        hg = geo_for_name(c["name"], geo_lookup)
        if not hg:
            continue
        for coord in cell_rankings:
            cell_rankings[coord].append((geo_sqdist(hg, cell_geos[coord]), i))
    for coord in cell_rankings:
        cell_rankings[coord].sort(key=lambda x: (x[0], x[1]))

    for coord in sorted(cell_rankings, key=lambda c: cell_rankings[c][0][0] if cell_rankings[c] else 999):
        if coord in occupied:
            continue
        for _score, i in cell_rankings[coord]:
            if i not in unassigned:
                continue
            assigned_pos[i] = coord
            occupied.add(coord)
            unassigned.remove(i)
            break

    # Pass C — overflow hexes in rings around each seat's 2024 anchor
    overflow_jobs: list[tuple[tuple[int, int], int, tuple[float, float] | None]] = []
    for i in list(unassigned):
        c = constituencies[i]
        anchor_pos = lookup_2024_name(c["name"], by_name, c.get("nation"))
        ranked = ranked_cells_for(c, pool, cell_geos, geo_lookup, by_name)
        if anchor_pos:
            anchor = (anchor_pos["q"], anchor_pos["r"])
        elif ranked:
            anchor = ranked[0]
        else:
            continue
        hg = geo_for_name(c["name"], geo_lookup)
        overflow_jobs.append((anchor, i, hg))

    overflow_jobs.sort(
        key=lambda job: (
            job[0],
            geo_sqdist(job[2], cell_geos[job[0]]) if job[2] and job[0] in cell_geos else 0.0,
            job[1],
        )
    )

    for anchor, i, hg in overflow_jobs:
        forbidden = forbidden_coords(
            constituencies[i], england_coords, scot_coords, wales_coords, ni_coords
        )
        free = overflow_beside_anchor(anchor, occupied, forbidden, hg, cell_geos)
        if free:
            assigned_pos[i] = free
            occupied.add(free)
            unassigned.discard(i)

    for i in list(unassigned):
        c = constituencies[i]
        ranked = ranked_cells_for(c, pool, cell_geos, geo_lookup, by_name)
        for coord in ranked:
            if coord not in occupied:
                assigned_pos[i] = coord
                occupied.add(coord)
                unassigned.discard(i)
                break


def assign_positions(
    constituencies: list[dict],
    by_name: dict[str, dict],
    scaffold_coords: set[tuple[int, int]],
    ni_coords: set[tuple[int, int]],
    gb_coords: set[tuple[int, int]],
    scot_coords: set[tuple[int, int]],
    wales_coords: set[tuple[int, int]],
    england_coords: set[tuple[int, int]],
    geo_lookup: dict[str, tuple[float, float]],
    reference_placements: dict[str, tuple[int, int]] | None = None,
    reference_seed_id: str | None = None,
    *,
    seed_wikipedia_successors: bool = True,
) -> int:
    global _REFERENCE_PINNED, _MANUAL_PINS_APPLIED
    _REFERENCE_PINNED = frozenset()
    _MANUAL_PINS_APPLIED = False
    cell_geos = build_cell_geos(geo_lookup, scaffold_coords)
    occupied: set[tuple[int, int]] = set()
    assigned_pos: dict[int, tuple[int, int]] = {}

    if reference_placements:
        _REFERENCE_PINNED = seed_from_reference_election(
            constituencies, reference_placements, assigned_pos, occupied
        )
        if seed_wikipedia_successors and reference_seed_id in ("feb1974", "1983"):
            successor_map = load_wikipedia_successor_map(reference_seed_id)
            name_aliases = (
                SUCCESSOR_NAME_ALIASES_1974
                if reference_seed_id == "feb1974"
                else SUCCESSOR_NAME_ALIASES
            )
            succ_geo_lookup = (
                load_geo_lookup("1974")
                if reference_seed_id == "feb1974"
                else load_geo_lookup("1983")
            )
            if successor_map:
                extra_pinned = seed_from_wikipedia_successors(
                    constituencies,
                    successor_map,
                    reference_placements,
                    assigned_pos,
                    occupied,
                    geo_lookup,
                    cell_geos,
                    england_coords,
                    scot_coords,
                    wales_coords,
                    ni_coords,
                    successor_name_aliases=name_aliases,
                    succ_geo_lookup=succ_geo_lookup,
                )
                _REFERENCE_PINNED = frozenset(set(_REFERENCE_PINNED) | set(extra_pinned))

    nation_indices: dict[str, list[int]] = {
        "northern-ireland": [],
        "scotland": [],
        "wales": [],
        "england": [],
        "other": [],
    }
    for i, c in enumerate(constituencies):
        if i in assigned_pos:
            continue
        if is_ni_constituency(c):
            nation_indices["northern-ireland"].append(i)
        elif c.get("nation") in nation_indices:
            nation_indices[c["nation"]].append(i)
        else:
            nation_indices["other"].append(i)

    fully_seeded = len(assigned_pos) == len(constituencies)
    mostly_seeded_layout = (
        reference_placements is not None
        and len(assigned_pos) >= len(constituencies) - 15
    )

    if not fully_seeded:
        assign_nation_by_geo(
            nation_indices["scotland"],
            constituencies,
            scot_coords,
            cell_geos,
            geo_lookup,
            by_name,
            occupied,
            assigned_pos,
            england_coords,
            scot_coords,
            wales_coords,
            ni_coords,
        )
        assign_nation_by_geo(
            nation_indices["wales"],
            constituencies,
            wales_coords,
            cell_geos,
            geo_lookup,
            by_name,
            occupied,
            assigned_pos,
            england_coords,
            scot_coords,
            wales_coords,
            ni_coords,
        )
        assign_nation_by_geo(
            nation_indices["northern-ireland"],
            constituencies,
            ni_coords,
            cell_geos,
            geo_lookup,
            by_name,
            occupied,
            assigned_pos,
            england_coords,
            scot_coords,
            wales_coords,
            ni_coords,
        )
        assign_nation_by_geo(
            nation_indices["england"],
            constituencies,
            england_coords,
            cell_geos,
            geo_lookup,
            by_name,
            occupied,
            assigned_pos,
            england_coords,
            scot_coords,
            wales_coords,
            ni_coords,
        )
        for i in nation_indices["other"]:
            c = constituencies[i]
            pool = gb_coords - ni_coords
            ranked = ranked_cells_for(c, pool, cell_geos, geo_lookup, by_name)
            forbidden = forbidden_coords(
                c, england_coords, scot_coords, wales_coords, ni_coords
            )
            for coord in ranked:
                if coord not in occupied:
                    assigned_pos[i] = coord
                    occupied.add(coord)
                    break
            else:
                free = nearest_free_cell(
                    ranked[0] if ranked else (0, 0),
                    occupied,
                    pool,
                    forbidden,
                )
                if free:
                    assigned_pos[i] = free
                    occupied.add(free)

        snap_england_anchors(
            constituencies,
            assigned_pos,
            occupied,
            england_coords,
            by_name,
        )

        fill_england_scaffold_gaps(
            constituencies,
            assigned_pos,
            occupied,
            england_coords,
            cell_geos,
            geo_lookup,
            by_name,
        )

        snap_england_anchors(
            constituencies,
            assigned_pos,
            occupied,
            england_coords,
            by_name,
        )

        fill_england_scaffold_gaps(
            constituencies,
            assigned_pos,
            occupied,
            england_coords,
            cell_geos,
            geo_lookup,
            by_name,
        )

        snap_england_anchors(
            constituencies,
            assigned_pos,
            occupied,
            england_coords,
            by_name,
        )

        if not mostly_seeded_layout:
            compact_england_internal_gaps(
                constituencies,
                assigned_pos,
                occupied,
                england_coords,
            )

        cascade_iters = 6 if mostly_seeded_layout else 48
        for _ in range(cascade_iters):
            if not cascade_england_gaps_to_periphery(
                constituencies,
                assigned_pos,
                occupied,
                england_coords,
                cell_geos,
                geo_lookup,
            ):
                break

        if not reference_placements:
            correct_severe_geo_outliers(
                constituencies,
                assigned_pos,
                occupied,
                england_coords,
                cell_geos,
                geo_lookup,
                by_name,
                scot_coords,
                wales_coords,
                ni_coords,
                delta_threshold=1.0,
                min_improvement=0.2,
            )
            correct_severe_geo_outliers(
                constituencies,
                assigned_pos,
                occupied,
                england_coords,
                cell_geos,
                geo_lookup,
                by_name,
                scot_coords,
                wales_coords,
                ni_coords,
                delta_threshold=0.5,
                min_improvement=0.12,
            )

        if not mostly_seeded_layout:
            densify_england_scaffold(
                constituencies,
                assigned_pos,
                occupied,
                england_coords,
                cell_geos,
                geo_lookup,
                by_name,
            )

            if reference_placements:
                final_repack_gb_scaffold(
                    constituencies,
                    assigned_pos,
                    occupied,
                    england_coords,
                    scot_coords,
                    wales_coords,
                    ni_coords,
                    cell_geos,
                    geo_lookup,
                    by_name,
                )

    apply_manual_hex_overrides(
        assigned_pos,
        constituencies,
        occupied,
        cell_geos,
        geo_lookup,
        by_name,
        england_coords=england_coords,
        scot_coords=scot_coords,
        wales_coords=wales_coords,
        ni_coords=ni_coords,
    )

    if reference_placements:
        final_repack_gb_scaffold(
            constituencies,
            assigned_pos,
            occupied,
            england_coords,
            scot_coords,
            wales_coords,
            ni_coords,
            cell_geos,
            geo_lookup,
            by_name,
        )
        fix_coast_band_displaced(
            constituencies,
            assigned_pos,
            occupied,
            cell_geos,
            geo_lookup,
            by_name,
            england_coords,
            scot_coords,
            wales_coords,
            ni_coords,
        )
        pack_scaffold_holes(
            constituencies,
            assigned_pos,
            occupied,
            england_coords,
            scot_coords,
            wales_coords,
            cell_geos,
            geo_lookup,
            max_zero_iters=96,
        )

    matched = 0
    for i, c in enumerate(constituencies):
        coord = assigned_pos.get(i)
        if coord:
            c["q"], c["r"] = coord
            c["code"] = f"HIST-{historic_norm(c['name']).replace(' ', '-')[:48]}"
            matched += 1
        else:
            c.pop("q", None)
            c.pop("r", None)
            c.pop("code", None)
    return matched


def correct_display_name(name: str) -> str:
    """Fix known constituency name spelling errors for display."""
    if not name:
        return name
    fixed = name.replace("&Westminster", "& Westminster")
    key = norm_name(fixed)
    if key in DISPLAY_NAMES:
        return DISPLAY_NAMES[key]
    result = fixed
    for wrong, right in DISPLAY_WORD_FIXES:
        result = re.sub(rf"\b{re.escape(wrong)}\b", right, result, flags=re.IGNORECASE)
    return result


def fix_constituency_display_names(constituencies: list[dict]) -> None:
    for c in constituencies:
        c["name"] = correct_display_name(c.get("name", ""))


def fix_alliance_parties(constituencies: list[dict]) -> None:
    for c in constituencies:
        label = (c.get("partyLabel") or "").strip().lower()
        if label in ALLIANCE_LABELS or label.startswith("alliance ("):
            c["party"] = "libdem"
            c["partyLabel"] = "SDP–Liberal Alliance"


def rebuild_index(fetch_mod) -> None:
    all_ids = (
        list(fetch_mod.BATCH_ELECTIONS.keys())
        + list(fetch_mod.INDIVIDUAL_ELECTIONS.keys())
        + ["2019", "2024"]
    )
    index = []
    for eid in all_ids:
        path = OUT_DIR / f"{eid}.json"
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            index.append(
                {
                    "id": eid,
                    "available": data.get("totalSeats", 0) > 0,
                    "seats": data.get("totalSeats", 0),
                    "matchedHexes": data.get("matchedHexes", 0),
                    "source": data.get("source"),
                    "hexLayout": data.get("hexLayout"),
                }
            )
        else:
            index.append({"id": eid, "available": False})
    (OUT_DIR / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")


def import_election(
    election_id: str,
    by_name: dict[str, dict],
    scaffold_coords: set[tuple[int, int]],
    ni_coords: set[tuple[int, int]],
    gb_coords: set[tuple[int, int]],
    scot_coords: set[tuple[int, int]],
    wales_coords: set[tuple[int, int]],
    england_coords: set[tuple[int, int]],
    geo_lookup: dict[str, tuple[float, float]],
    reference_placements: dict[str, tuple[int, int]] | None = None,
    reference_seed_id: str | None = None,
    *,
    seed_wikipedia_successors: bool = True,
) -> int:
    path = OUT_DIR / f"{election_id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    constituencies = data.get("constituencies") or []
    fix_alliance_parties(constituencies)
    boundary = ELECTION_BOUNDARY.get(election_id, "1983")
    fix_constituency_nations(constituencies, load_geo_nation_index(boundary))
    matched = assign_positions(
        constituencies,
        by_name,
        scaffold_coords,
        ni_coords,
        gb_coords,
        scot_coords,
        wales_coords,
        england_coords,
        geo_lookup,
        reference_placements=reference_placements,
        reference_seed_id=reference_seed_id,
        seed_wikipedia_successors=seed_wikipedia_successors,
    )
    fix_constituency_display_names(constituencies)

    data["layout"] = LAYOUT
    data["hexLayout"] = HEX_LAYOUT_FILE
    data["matchedHexes"] = matched
    data["totalSeats"] = len(constituencies)
    note = "2024 UK hexmap scaffold (ODI/open-innovations)"
    if note not in (data.get("source") or ""):
        data["source"] = f"{data.get('source', '')} · hex layout: {note}".strip(" ·")

    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"  → {election_id}: {matched}/{len(constituencies)} hex-matched")
    return matched


def main() -> None:
    parser = argparse.ArgumentParser(description="Import historic layouts onto 2024 scaffold")
    parser.add_argument("--election", choices=ELECTIONS)
    args = parser.parse_args()

    if not SCAFFOLD_HEX.exists():
        raise SystemExit(f"Missing scaffold: {SCAFFOLD_HEX}")

    by_name, scaffold_coords, ni_coords, gb_coords, scot_coords, wales_coords, england_coords = (
        build_scaffold()
    )
    print(f"2024 scaffold: {len(scaffold_coords)} cells")

    targets = [args.election] if args.election else list(ELECTIONS)
    for election_id in targets:
        boundary = ELECTION_BOUNDARY.get(election_id, "1983")
        geo_lookup = load_geo_lookup(boundary)
        print(f"  {election_id}: {boundary} geo names: {len(geo_lookup)}")

        reference_placements = None
        seed_id = ELECTION_REFERENCE_SEED.get(election_id)
        if seed_id:
            reference_placements = load_reference_placements(seed_id)

        import_election(
            election_id,
            by_name,
            scaffold_coords,
            ni_coords,
            gb_coords,
            scot_coords,
            wales_coords,
            england_coords,
            geo_lookup,
            reference_placements=reference_placements,
            reference_seed_id=seed_id,
            seed_wikipedia_successors=seed_id in ("feb1974", "1983"),
        )

    rebuild_index(load_fetch_module())
    print("Done.")


AUDIT_SKIP_NORMS = frozenset({"st ives", "workington", "isle of wight"})


def geo_deg_distance(
    a: tuple[float, float], b: tuple[float, float]
) -> float:
    return geo_sqdist(a, b) ** 0.5


def audit_england_placements(
    constituencies: list[dict],
    by_name: dict[str, dict],
    geo_lookup: dict[str, tuple[float, float]],
    cell_geos: dict[tuple[int, int], tuple[float, float]],
    england_coords: set[tuple[int, int]],
) -> list[dict]:
    """Flag England seats whose assigned hex is a poor geographic fit."""
    skip = AUDIT_SKIP_NORMS
    issues: list[dict] = []
    england_with_geo = [coord for coord in england_coords if coord in cell_geos]

    for c in constituencies:
        if c.get("nation") != "england":
            continue
        q, r = c.get("q"), c.get("r")
        if q is None or r is None:
            continue
        if historic_norm(c["name"]) in skip:
            continue

        hg = geo_for_name(c["name"], geo_lookup)
        if not hg:
            continue

        cur = (q, r)
        if cur not in cell_geos:
            continue
        cur_d = geo_deg_distance(hg, cell_geos[cur])
        nearest_d = min(geo_deg_distance(hg, cell_geos[coord]) for coord in england_with_geo)
        delta = cur_d - nearest_d

        anchor = lookup_2024_name(c["name"], by_name, "england")
        anchor_name = anchor.get("n") if anchor else None
        anchor_hex = (
            hex_distance(q, r, anchor["q"], anchor["r"]) if anchor else None
        )

        reasons: list[str] = []
        if cur_d > 0.8:
            reasons.append(f"geo {cur_d:.2f}° from centroid")
        if delta > 0.25:
            reasons.append(f"{delta:.2f}° worse than geo-nearest cell")
        if anchor_hex is not None and anchor_hex > 8:
            reasons.append(f"{anchor_hex} hex from anchor {anchor_name}")
        if (
            anchor_name
            and anchor_hex is not None
            and anchor_hex > 6
            and not meaningful_token_overlap(
                historic_norm(c["name"]), historic_norm(anchor_name)
            )
        ):
            reasons.append(f"weak name match to anchor {anchor_name}")

        if reasons:
            issues.append(
                {
                    "name": c["name"],
                    "q": q,
                    "r": r,
                    "cur_d": round(cur_d, 3),
                    "nearest_d": round(nearest_d, 3),
                    "delta": round(delta, 3),
                    "anchor": anchor_name,
                    "anchor_hex": anchor_hex,
                    "reasons": reasons,
                }
            )

    issues.sort(key=lambda row: (-row["delta"], -row["cur_d"]))
    return issues


if __name__ == "__main__":
    main()
