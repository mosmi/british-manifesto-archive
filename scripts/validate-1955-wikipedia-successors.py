#!/usr/bin/env python3
"""Validate 1955→1974 Wikipedia successor chains against boundary GeoJSON centroids."""

from __future__ import annotations

import importlib.util
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAP_JSON = ROOT / "data" / "hex" / "1955-abolished-wikipedia-replaced-by.json"
MAX_DEG = 0.55  # ~60 km; splits/mergers can be wider than a single successor cell


def load_import_module():
    spec = importlib.util.spec_from_file_location(
        "import_historical_hexmaps",
        ROOT / "scripts" / "import-historical-hexmaps.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def split_successors(raw: str) -> list[str]:
    mod = load_import_module()
    return mod.parse_wikipedia_successor_parts(raw)


def geo_deg_distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def resolve_1974_geo(name: str, geo74: dict[str, tuple[float, float]], mod) -> tuple[float, float] | None:
    g = mod.geo_for_name(name, geo74)
    if g:
        return g
    alias = mod.SUCCESSOR_NAME_ALIASES_1974.get(mod.historic_norm(name))
    if alias:
        return mod.geo_for_name(alias, geo74)
    feb = json.loads((ROOT / "data/constituencies/feb1974.json").read_text())
    ref_names = {c["name"] for c in feb["constituencies"]}
    hn = mod.historic_norm(name)
    for rn in ref_names:
        if mod.historic_norm(rn) == hn:
            return mod.geo_for_name(rn, geo74)
    from difflib import get_close_matches

    keys = [mod.historic_norm(n) for n in ref_names]
    for match in get_close_matches(hn, keys, n=3, cutoff=0.82):
        for rn in ref_names:
            if mod.historic_norm(rn) == match:
                g = mod.geo_for_name(rn, geo74)
                if g:
                    return g
    return None


def validate_row(row: dict, geo55: dict, geo74: dict, mod) -> dict:
    name = row["name1955"]
    replaced = row.get("replacedBy") or ""
    if not replaced:
        row["geoStatus"] = row.get("status", "missing_replaced_by")
        return row

    src = mod.geo_for_name(name, geo55)
    if not src:
        row["geoStatus"] = "missing_1955_geo"
        return row

    succ_names = split_successors(replaced)
    succ_geos: list[tuple[float, float]] = []
    missing: list[str] = []
    for s in succ_names:
        g = resolve_1974_geo(s, geo74, mod)
        if g:
            succ_geos.append(g)
        else:
            missing.append(s)

    if not succ_geos:
        row["geoStatus"] = "no_1974_geo"
        row["geoMissingSuccessors"] = missing
        return row

    best = min(geo_deg_distance(src, g) for g in succ_geos)
    mean_lon = sum(g[0] for g in succ_geos) / len(succ_geos)
    mean_lat = sum(g[1] for g in succ_geos) / len(succ_geos)
    mean_d = geo_deg_distance(src, (mean_lon, mean_lat))
    row["geoNearestDeg"] = round(best, 3)
    row["geoMeanDeg"] = round(mean_d, 3)
    row["geoMissingSuccessors"] = missing
    if missing:
        row["geoStatus"] = "partial_geo"
    elif best <= MAX_DEG or mean_d <= MAX_DEG:
        row["geoStatus"] = "ok"
    else:
        row["geoStatus"] = "geo_mismatch"
    return row


def main() -> None:
    if not MAP_JSON.exists():
        raise SystemExit(f"Missing {MAP_JSON} — run fetch-1955-wikipedia-replaced-by.py first")

    mod = load_import_module()
    geo55 = mod.load_geo_lookup("1955")
    geo74 = mod.load_geo_lookup("1974")
    rows = json.loads(MAP_JSON.read_text())
    validated = [validate_row(dict(row), geo55, geo74, mod) for row in rows]
    MAP_JSON.write_text(json.dumps(validated, indent=2) + "\n", encoding="utf-8")

    counts: dict[str, int] = {}
    for row in validated:
        counts[row.get("geoStatus", "?")] = counts.get(row.get("geoStatus", "?"), 0) + 1
    bad = [
        r
        for r in validated
        if r.get("geoStatus") not in ("ok", "partial_geo", "ok_unexpected_abolished")
        or (r.get("geoStatus") == "partial_geo" and not r.get("replacedBy"))
    ]
    mism = [r for r in validated if r.get("geoStatus") == "geo_mismatch"]
    partial = [r for r in validated if r.get("geoStatus") == "partial_geo"]
    missing = [r for r in validated if not r.get("replacedBy")]

    print(f"Validated {len(validated)} rows -> {MAP_JSON}")
    print("Status:", counts)
    if missing:
        print(f"\nMissing replacedBy ({len(missing)}):")
        for r in missing:
            print(f"  {r['name1955']} ({r.get('status')})")
    if mism:
        print(f"\nGeo mismatch ({len(mism)}):")
        for r in mism:
            print(
                f"  {r['name1955']}: nearest={r.get('geoNearestDeg')}° "
                f"-> {r.get('replacedBy')}"
            )
    if partial:
        print(f"\nPartial geo ({len(partial)}):")
        for r in partial[:15]:
            print(f"  {r['name1955']}: missing {r.get('geoMissingSuccessors')}")


if __name__ == "__main__":
    main()
