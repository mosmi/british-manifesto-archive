#!/usr/bin/env python3
"""
Build compact HexJSON layouts from Wikipedia hex cartogram SVGs (Jonas Magnus Lystad)
and the ODI Leeds BBC layout for 2010 boundaries.

Sources:
  1997/2001 → File:1997_UK_General_Election_Constituencies.svg (659 seats, same boundaries)
  2001      → File:2001_UK_General_Election_Constituencies.svg (same grid, can reuse 1997)
  2005      → File:2005_UK_General_Election_Constituencies.svg (646 seats)
  2010      → ODI Leeds uk-constituencies-2019-BBC.hexjson (650 seats)

Usage:
  python3 scripts/build-wikipedia-hex-layout.py
  python3 scripts/build-wikipedia-hex-layout.py --apply
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import re
import unicodedata
import urllib.error
import urllib.request
from difflib import get_close_matches
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEX_DIR = ROOT / "data" / "hex"
CACHE_DIR = ROOT / "data" / "cache" / "wikipedia-hex"
OUT_DIR = ROOT / "data" / "constituencies"
UA = "Mozilla/5.0 (compatible; BritishManifestoArchive/1.0; +research)"

WIKIPEDIA_SVGS = {
    "1997": "https://upload.wikimedia.org/wikipedia/commons/1/11/1997_UK_General_Election_Constituencies.svg",
    "2001": "https://upload.wikimedia.org/wikipedia/commons/3/39/2001_UK_General_Election_Constituencies.svg",
    "2005": "https://upload.wikimedia.org/wikipedia/commons/8/84/2005_UK_General_Election_Constituencies.svg",
}

ODI_2010_URL = (
    "https://raw.githubusercontent.com/odileeds/hexmaps/gh-pages/maps/"
    "uk-constituencies-2019-BBC.hexjson"
)

ELECTION_LAYOUT = {
    "1997": "1997",
    "2001": "1997",  # same boundary vintage as 1997
    "2005": "2005",
    "2010": "2010",
}

# Known SVG id ↔ archive name mismatches
MANUAL_ALIASES: dict[str, str] = {
    "brent east": "brent central",  # 1997 SVG labels Brent East seat as BrentCentral
    "richmond": "richmond yorks",
    "city of chester": "cityofchester",
    "chester city of": "cityofchester",
    "chester city of": "cityofchester",
    "city of durham": "cityofdurham",
    "durham city of": "cityofdurham",
    "durham city of": "cityofdurham",
    "city of york": "cityofyork",
    "york city of": "cityofyork",
    "ynys mon ieuan": "ynys mon",
    "ynys-mon ieuan": "ynys mon",
    "regents park and kensington north": "regentx27sparkandnorthkensington",
    "ayrshire central": "central ayrshire",
    "ayrshire north and arran": "north ayrshire and arran",
    "bedfordshire mid": "mid bedfordshire",
    "devon west and torridge": "torridge and west devon",
    "dorset mid and poole north": "mid dorset and poole north",
    "faversham and kent mid": "faversham and mid kent",
    "hull east": "kingston upon hull east",
    "hull north": "kingston upon hull north",
    "hull west and hessle": "kingston upon hull west and hessle",
    "norfolk mid": "mid norfolk",
    "maldon and chelmsford east": "maldon and east chelmsford",
    "north east fife": "fife north east",
    "central fife": "fife central",
    "basildon south and thurrock east": "basildon and thurrock south",
    "na h-eileanan an iar western isles": "na h-eileanan an iar",
    "suffolk central and ipswich north": "central suffolk and north ipswich",
    "worcester city of": "worcester",
    "stoke-on-trent central": "stoke on trent central",
    "stoke-on-trent north": "stoke on trent north",
    "stoke-on-trent south": "stoke on trent south",
    "newcastle upon tyne central": "newcastle upon tyne central",
}

HEX_W = 13.9
HEX_DX = 1.5 * HEX_W
HEX_DY = math.sqrt(3) * HEX_W

COMPASS_WORDS = (
    ("north east", "ne"),
    ("north west", "nw"),
    ("south east", "se"),
    ("south west", "sw"),
    ("north", "n"),
    ("south", "s"),
    ("east", "e"),
    ("west", "w"),
)


def load_fetch_module():
    spec = importlib.util.spec_from_file_location(
        "fetch_constituency_data",
        ROOT / "scripts" / "fetch-constituency-data.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fetch_url(url: str, cache_path: Path | None = None) -> bytes:
    if cache_path and cache_path.exists():
        return cache_path.read_bytes()
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()
    if cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(data)
    return data


def norm_name(name: str) -> str:
    name = unicodedata.normalize("NFKC", name or "")
    name = name.replace("\u2019", "'").replace("&", " and ")
    name = re.sub(r"^ni\s+", "", name, flags=re.I)
    name = re.sub(r"\s+", " ", name).strip().lower()
    name = name.replace(" upon ", "-upon-").replace(" under ", "-under-")
    name = re.sub(r"[^\w\s-]", "", name)
    # Strip corrupt MP suffixes from HoC PDF parse errors
    name = re.sub(r"\s+(nick|john|geoffrey|ieuan)$", "", name)
    return name


def expanded_norm(name: str) -> str:
    n = norm_name(name)
    n = re.sub(r"\bcity of\s+", "", n)
    n = re.sub(r",?\s*city of$", "", n)
    return n


def alias_keys(name: str) -> set[str]:
    keys: set[str] = set()
    base = expanded_norm(name)
    if not base:
        return keys
    variants = {base}
    if base.startswith("city of "):
        variants.add(base[8:] + " city")
        variants.add("cityof" + base[8:].replace(" ", ""))
    if base.endswith(" city"):
        variants.add("city of " + base[:-5])
        variants.add("cityof" + base[:-5].replace(" ", ""))
    if base.startswith("the "):
        variants.add(base[4:] + ", the")
    if base.endswith(", the"):
        variants.add("the " + base[:-5])
    for direction in ("west", "east", "north", "south"):
        if base.startswith(direction + " "):
            variants.add(base[len(direction) + 1 :] + " " + direction)
        if base.endswith(" " + direction):
            variants.add(direction + " " + base[: -len(direction) - 1])
    for long, short in COMPASS_WORDS:
        variants.add(base.replace(long, short))
        variants.add(base.replace(short, long))
    if base.startswith("mid "):
        variants.add(f"{base[4:]} mid")
    if base.endswith(" mid"):
        variants.add(f"mid {base[:-4]}")
    for v in list(variants):
        keys.add(v)
        keys.add(v.replace(" and ", " & "))
        keys.add(v.replace(" & ", " and "))
        keys.add(v.replace("-", " "))
        keys.add(v.replace(" ", ""))
        keys.add(v.replace("-upon-", " upon "))
    manual = MANUAL_ALIASES.get(base)
    if manual:
        keys.add(manual)
        keys.add(manual.replace(" ", ""))
    return {k for k in keys if k}


def svg_id_to_name(svg_id: str) -> str:
    s = re.sub(r"000000\d+.*$", "", svg_id)
    s = re.sub(r"_000001\d+.*$", "", s)
    s = re.sub(r"(?<=[a-zA-Z])\d{10,}.*$", "", s)  # BanffandBuchan0000015370…
    s = s.replace("_", " ")
    s = re.sub(r"x27", "'", s, flags=re.I)
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", s)
    s = re.sub(r"(\d)([A-Za-z])", r"\1 \2", s)
    s = re.sub(r"cityof", "city of ", s, flags=re.I)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def pixel_to_hex(cx: float, cy: float, ox: float, oy: float) -> tuple[int, int]:
    q = round((cx - ox) / HEX_DX)
    r = round((cy - oy - (q % 2) * HEX_DY / 2) / HEX_DY)
    return q, r


def calibrate_origin(items: list[dict]) -> tuple[float, float]:
    min_cx = min(i["cx"] for i in items)
    min_cy = min(i["cy"] for i in items)
    best = (999, 0.0, 0.0)
    for ox in (min_cx - HEX_DX, min_cx, min_cx + HEX_DX / 2):
        for oy in (min_cy - HEX_DY, min_cy, min_cy - HEX_DY / 2):
            seen: set[tuple[int, int]] = set()
            collisions = 0
            for it in items:
                q, r = pixel_to_hex(it["cx"], it["cy"], ox, oy)
                if (q, r) in seen:
                    collisions += 1
                seen.add((q, r))
            if collisions < best[0]:
                best = (collisions, ox, oy)
    return best[1], best[2]


def parse_svg_hexes(svg_text: str) -> dict[str, dict]:
    pattern = re.compile(r'<path id="([^"]+)"[^>]*d="M([\d.]+),([\d.]+)')
    items = []
    for match in pattern.finditer(svg_text):
        svg_id = match.group(1)
        x, y = float(match.group(2)), float(match.group(3))
        items.append(
            {
                "id": svg_id,
                "name": svg_id_to_name(svg_id),
                "cx": x - HEX_W,
                "cy": y + 8,
            }
        )

    ox, oy = calibrate_origin(items)
    hexes: dict[str, dict] = {}
    for item in items:
        q, r = pixel_to_hex(item["cx"], item["cy"], ox, oy)
        code = f"WIKI-{norm_name(item['name']).replace(' ', '-')[:48]}"
        hexes[code] = {"n": item["name"], "q": q, "r": r, "svgId": item["id"]}

    # SVG y-axis grows southward; ODI HexJSON / hexmap.js expects r to grow northward.
    rs = [h["r"] for h in hexes.values()]
    r_max = max(rs)
    for h in hexes.values():
        h["r"] = r_max - h["r"]

    qs = [h["q"] for h in hexes.values()]
    q_min, r_min = min(qs), min(h["r"] for h in hexes.values())
    for h in hexes.values():
        h["q"] -= q_min
        h["r"] -= r_min

    return hexes


def download_svg(boundary_id: str) -> str:
    url = WIKIPEDIA_SVGS[boundary_id]
    cache = CACHE_DIR / f"{boundary_id}.svg"
    return fetch_url(url, cache).decode("utf-8")


def build_wikipedia_hexjson(boundary_id: str) -> dict:
    print(f"Parsing Wikipedia hex SVG for {boundary_id}…")
    svg = download_svg(boundary_id)
    hexes = parse_svg_hexes(svg)
    occupied = {(h["q"], h["r"]) for h in hexes.values()}

    def neighbors(q: int, r: int) -> list[tuple[int, int]]:
        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        if q % 2:
            dirs += [(1, 1), (-1, 1)]
        else:
            dirs += [(1, -1), (-1, -1)]
        return [(q + dq, r + dr) for dq, dr in dirs]

    adj = sum(1 for q, r in occupied if any(n in occupied for n in neighbors(q, r)))
    print(f"  → {len(hexes)} hexes, {adj}/{len(occupied)} with adjacent neighbours")
    return {
        "layout": "odd-q",
        "source": f"Wikipedia hex cartogram ({boundary_id} UK General Election Constituencies.svg)",
        "boundarySet": boundary_id,
        "hexes": hexes,
    }


def download_odi_2010_hexjson() -> dict:
    print("Downloading ODI Leeds BBC hex layout for 2010 boundaries…")
    cache = CACHE_DIR / "odi-2010.hexjson"
    payload = json.loads(fetch_url(ODI_2010_URL, cache))
    payload["source"] = "ODI Leeds / BBC (uk-constituencies-2019-BBC.hexjson)"
    payload["boundarySet"] = "2010"
    occupied = {(h["q"], h["r"]) for h in payload["hexes"].values()}

    def neighbors(q: int, r: int) -> list[tuple[int, int]]:
        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        if q % 2:
            dirs += [(1, 1), (-1, 1)]
        else:
            dirs += [(1, -1), (-1, -1)]
        return [(q + dq, r + dr) for dq, dr in dirs]

    adj = sum(1 for q, r in occupied if any(n in occupied for n in neighbors(q, r)))
    print(f"  → {len(payload['hexes'])} hexes, {adj}/{len(occupied)} with adjacent neighbours")
    return payload


def save_hexjson(boundary_id: str, payload: dict) -> Path:
    HEX_DIR.mkdir(parents=True, exist_ok=True)
    path = HEX_DIR / f"uk-constituencies-{boundary_id}.hexjson"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"  → wrote {path.name}")
    return path


def build_hex_lookup(hex_path: Path) -> tuple[str, dict[str, dict]]:
    hex_data = json.loads(hex_path.read_text(encoding="utf-8"))
    layout = hex_data.get("layout", "odd-q")
    lookup: dict[str, dict] = {}
    for code, hex_def in hex_data.get("hexes", {}).items():
        pos = {
            "q": hex_def["q"],
            "r": hex_def["r"],
            "code": code,
            "layoutName": hex_def.get("n", ""),
        }
        for key in alias_keys(hex_def.get("n", "")):
            lookup[key] = pos
    return layout, lookup


def match_hex_position(name: str, lookup: dict[str, dict]) -> dict | None:
    keys = list(lookup.keys())
    for candidate in alias_keys(name):
        if candidate in lookup:
            return lookup[candidate]
    for candidate in alias_keys(name):
        close = get_close_matches(candidate, keys, n=1, cutoff=0.84)
        if close:
            return lookup[close[0]]
    return None


def apply_layout_to_election(election_id: str, boundary_id: str) -> None:
    election_path = OUT_DIR / f"{election_id}.json"
    hex_path = HEX_DIR / f"uk-constituencies-{boundary_id}.hexjson"
    if not election_path.exists():
        print(f"  ! Skipping {election_id}: no constituency data")
        return
    if not hex_path.exists():
        print(f"  ! Skipping {election_id}: missing {hex_path.name}")
        return

    data = json.loads(election_path.read_text(encoding="utf-8"))
    constituencies = data.get("constituencies") or []
    layout, hex_lookup = build_hex_lookup(hex_path)

    matched = 0
    for c in constituencies:
        pos = match_hex_position(c["name"], hex_lookup)
        if pos:
            c["q"] = pos["q"]
            c["r"] = pos["r"]
            c["code"] = pos.get("code")
            matched += 1
        else:
            c.pop("q", None)
            c.pop("r", None)
            c.pop("code", None)

    data["layout"] = layout
    data["hexLayout"] = hex_path.name
    data["matchedHexes"] = matched
    data["totalSeats"] = len(constituencies)
    note = json.loads(hex_path.read_text(encoding="utf-8")).get("source", "hex layout")
    if note not in (data.get("source") or ""):
        data["source"] = f"{data.get('source', '')} · hex layout: {note}".strip(" ·")

    election_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"  → {election_id}: {matched}/{len(constituencies)} hex-matched")


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Wikipedia/ODI hex layouts")
    parser.add_argument("--apply", action="store_true", help="Apply layouts to election JSON files")
    args = parser.parse_args()

    for boundary_id in ("1997", "2005"):
        save_hexjson(boundary_id, build_wikipedia_hexjson(boundary_id))

    save_hexjson("2010", download_odi_2010_hexjson())

    if args.apply:
        fetch_mod = load_fetch_module()
        print("Applying layouts to elections…")
        for election_id, boundary_id in ELECTION_LAYOUT.items():
            apply_layout_to_election(election_id, boundary_id)
        # Re-apply ODI layout to 2015/2017/2019 which share 2010 boundaries
        for election_id in ("2015", "2017", "2019"):
            apply_layout_to_election(election_id, "2010")
        rebuild_index(fetch_mod)
        print("Done.")


if __name__ == "__main__":
    main()
