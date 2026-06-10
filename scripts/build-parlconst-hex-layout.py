#!/usr/bin/env python3
"""
Build HexJSON constituency layouts from parlconst.org uMap boundary data.

parlconst.org embeds constituency maps on uMap (OpenStreetMap France). GeoJSON
can be downloaded via https://umap.openstreetmap.fr/map/{id}/download/

Boundary vintages:
  - 1997 (Fifth Periodic Review): 1997 & 2001 elections
  - 2005 (Scotland reform): 2005 election (England/Wales/NI unchanged)
  - 2010 (Sixth Periodic Review): 2010 election

Usage:
  python3 scripts/build-parlconst-hex-layout.py
  python3 scripts/build-parlconst-hex-layout.py --apply
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import re
import time
import unicodedata
import urllib.error
import urllib.request
from difflib import get_close_matches
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEX_DIR = ROOT / "data" / "hex"
CACHE_DIR = ROOT / "data" / "cache" / "parlconst"
OUT_DIR = ROOT / "data" / "constituencies"
UA = "Mozilla/5.0 (compatible; BritishManifestoArchive/1.0; +research)"

# uMap map IDs embedded on parlconst.org (via Google Sites → uMap OpenStreetMap)
BOUNDARY_SETS: dict[str, list[int]] = {
    "1997": [
        956685,  # England (South)
        958244,  # England (Midlands)
        967570,  # England (North)
        885990,  # Wales
        918262,  # Scotland (pre-2005)
        919580,  # Northern Ireland
    ],
    "2005": [
        956685,
        958244,
        967570,
        885990,
        918267,  # Scotland (2005 reform)
        919580,
    ],
    # 2010 boundaries use ODI Leeds BBC layout via build-wikipedia-hex-layout.py
}

ELECTION_LAYOUT = {
    "1997": "1997",
    "2001": "1997",
    "2005": "2005",
}


def load_fetch_module():
    spec = importlib.util.spec_from_file_location(
        "fetch_constituency_data",
        ROOT / "scripts" / "fetch-constituency-data.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fetch_url(url: str, cache_path: Path | None = None, retries: int = 4) -> bytes:
    if cache_path and cache_path.exists():
        return cache_path.read_bytes()
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = resp.read()
            if cache_path:
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_bytes(data)
            return data
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_err = exc
            time.sleep(1.5 * (attempt + 1))
    raise last_err  # type: ignore[misc]


def norm_name(name: str) -> str:
    name = unicodedata.normalize("NFKC", name or "")
    name = name.replace("\u2019", "'").replace("&", " and ")
    name = re.sub(r"\s+", " ", name).strip().lower()
    name = name.replace(" upon ", "-upon-").replace(" under ", "-under-")
    name = re.sub(r"[^\w\s-]", "", name)
    return name


def expanded_norm(name: str) -> str:
    """Expand parlconst-style abbreviations for cross-source name matching."""
    n = norm_name(name)
    n = re.sub(r"\bcity of\s+", "", n)
    n = re.sub(r",?\s*city of$", "", n)
    n = re.sub(r"\bn$", "north", n)
    n = re.sub(r"\bs$", "south", n)
    n = re.sub(r"\be$", "east", n)
    n = re.sub(r"\bw$", "west", n)
    n = re.sub(r"\bn(?=\s)", "north ", n)
    n = re.sub(r"\bs(?=\s)", "south ", n)
    n = re.sub(r"\be(?=\s)", "east ", n)
    n = re.sub(r"\bw(?=\s)", "west ", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n


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


def alias_keys(name: str) -> set[str]:
    keys = set()
    base = expanded_norm(name)
    if not base:
        return keys
    variants = {base}
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
    return {k for k in keys if k}


def build_hex_lookup(hex_path: Path) -> tuple[str, dict[str, dict]]:
    hex_data = json.loads(hex_path.read_text(encoding="utf-8"))
    layout = hex_data.get("layout", "odd-q")
    lookup: dict[str, dict] = {}
    for code, hex_def in hex_data.get("hexes", {}).items():
        pos = {"q": hex_def["q"], "r": hex_def["r"], "code": code, "layoutName": hex_def.get("n", "")}
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


def feature_centroid(feature: dict) -> tuple[float, float] | None:
    geom = feature.get("geometry") or {}
    gtype = geom.get("type")
    if gtype == "Point":
        lon, lat = geom["coordinates"][:2]
        return lon, lat
    if gtype == "Polygon":
        rings = geom.get("coordinates") or []
        ring = rings[0] if rings else []
    elif gtype == "MultiPolygon":
        polys = geom.get("coordinates") or []
        if not polys:
            return None
        ring = max(polys, key=lambda p: len(p[0]) if p else 0)[0]
    else:
        return None
    if not ring:
        return None
    lon = sum(p[0] for p in ring) / len(ring)
    lat = sum(p[1] for p in ring) / len(ring)
    return lon, lat


def axial_distance(q1: int, r1: int, q2: int, r2: int) -> int:
    x1, z1 = q1, r1
    y1 = -x1 - z1
    x2, z2 = q2, r2
    y2 = -x2 - z2
    return max(abs(x1 - x2), abs(y1 - y2), abs(z1 - z2))


def download_umap_features(map_id: int) -> list[dict]:
    cache = CACHE_DIR / f"umap-{map_id}.json"
    payload = json.loads(fetch_url(f"https://umap.openstreetmap.fr/map/{map_id}/download/", cache))
    features: list[dict] = []
    for layer in payload.get("layers", []):
        features.extend(layer.get("features", []))
    return features


def collect_boundary_features(boundary_id: str) -> list[dict]:
    items: list[dict] = []
    for map_id in BOUNDARY_SETS[boundary_id]:
        for feature in download_umap_features(map_id):
            props = feature.get("properties") or {}
            name = props.get("Name") or props.get("name") or props.get("n")
            if not name:
                continue
            centroid = feature_centroid(feature)
            if not centroid:
                continue
            items.append({"name": name.strip(), "lon": centroid[0], "lat": centroid[1]})
    return items


def hexify_constituencies(items: list[dict], grid_width: int = 90) -> dict[str, dict]:
    """Assign odd-q hex coordinates from geographic centroids."""
    if not items:
        return {}

    lons = [i["lon"] for i in items]
    lats = [i["lat"] for i in items]
    min_lon, max_lon = min(lons), max(lons)
    min_lat, max_lat = min(lats), max(lats)
    lon_span = max(max_lon - min_lon, 0.01)
    lat_span = max(max_lat - min_lat, 0.01)

    # Scale so GB+NI fits a tall odd-q grid (north-up, NI west).
    height = max(int(grid_width * lat_span / lon_span * 1.35), grid_width)

    scored = []
    for item in items:
        x = (item["lon"] - min_lon) / lon_span * grid_width
        y = (max_lat - item["lat"]) / lat_span * height
        scored.append({**item, "x": x, "y": y})
    scored.sort(key=lambda i: (i["y"], i["x"]))

    occupied: set[tuple[int, int]] = set()
    hexes: dict[str, dict] = {}

    for item in scored:
        tx, ty = item["x"], item["y"]
        q0 = round(tx / 1.5)
        r0 = round(ty / math.sqrt(3))

        chosen = None
        best_metric = float("inf")
        for radius in range(0, 80):
            for q in range(q0 - radius, q0 + radius + 1):
                for r in range(r0 - radius, r0 + radius + 1):
                    if axial_distance(q, r, q0, r0) > radius:
                        continue
                    if (q, r) in occupied:
                        continue
                    px = q * 1.5
                    pr = r * math.sqrt(3)
                    metric = (px - tx) ** 2 + (pr - ty) ** 2
                    if metric < best_metric:
                        best_metric = metric
                        chosen = (q, r)
            if chosen:
                break

        if not chosen:
            q, r = q0, r0
            while (q, r) in occupied:
                r += 1
            chosen = (q, r)

        occupied.add(chosen)
        code = f"PCON-{norm_name(item['name']).replace(' ', '-')[:40]}"
        hexes[code] = {"n": item["name"], "q": chosen[0], "r": chosen[1]}

    return hexes


def build_hexjson(boundary_id: str) -> dict:
    print(f"Building hex layout for {boundary_id} boundary set…")
    items = collect_boundary_features(boundary_id)
    print(f"  → {len(items)} constituencies from parlconst.org uMap")
    hexes = hexify_constituencies(items)
    return {
        "layout": "odd-q",
        "source": "parlconst.org (uMap boundary data)",
        "boundarySet": boundary_id,
        "hexes": hexes,
    }


def save_hexjson(boundary_id: str, payload: dict) -> Path:
    HEX_DIR.mkdir(parents=True, exist_ok=True)
    path = HEX_DIR / f"uk-constituencies-{boundary_id}.hexjson"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"  → wrote {path.name} ({len(payload['hexes'])} hexes)")
    return path


def apply_layout_to_election(fetch_mod, election_id: str, boundary_id: str) -> None:
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
    hex_data = json.loads(hex_path.read_text(encoding="utf-8"))
    layout = hex_data.get("layout", "odd-q")
    _, hex_lookup = build_hex_lookup(hex_path)

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
    note = "parlconst.org uMap boundaries"
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
    parser = argparse.ArgumentParser(description="Build parlconst hex layouts")
    parser.add_argument("--apply", action="store_true", help="Apply layouts to election JSON files")
    parser.add_argument("--boundary", choices=list(BOUNDARY_SETS.keys()))
    args = parser.parse_args()

    targets = [args.boundary] if args.boundary else list(BOUNDARY_SETS.keys())
    for boundary_id in targets:
        payload = build_hexjson(boundary_id)
        save_hexjson(boundary_id, payload)

    if args.apply:
        fetch_mod = load_fetch_module()
        print("Applying layouts to elections…")
        for election_id, boundary_id in ELECTION_LAYOUT.items():
            apply_layout_to_election(fetch_mod, election_id, boundary_id)
        rebuild_index(fetch_mod)
        print("Done.")


if __name__ == "__main__":
    main()
