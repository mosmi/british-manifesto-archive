#!/usr/bin/env python3
"""Audit England constituency hex placements for a historic election."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "constituencies"


def load_import_module():
    spec = importlib.util.spec_from_file_location(
        "import_historical_hexmaps",
        ROOT / "scripts" / "import-historical-hexmaps.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--election", default="1955")
    parser.add_argument("--severe-only", action="store_true")
    args = parser.parse_args()

    mod = load_import_module()
    mod.load_anchor_data()
    mod.normalize_historic_mappings()

    path = DATA / f"{args.election}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    by_name, scaffold_coords, *_rest, england_coords = mod.build_scaffold()
    geo_lookup = mod.load_geo_lookup()
    cell_geos = mod.build_cell_geos(geo_lookup, scaffold_coords)

    by_cell: dict[tuple[int, int], list[str]] = defaultdict(list)
    for c in data["constituencies"]:
        q, r = c.get("q"), c.get("r")
        if q is None:
            continue
        by_cell[(q, r)].append(c["name"])

    dups = {cell: names for cell, names in by_cell.items() if len(names) > 1}
    pin_targets: dict[tuple[int, int], list[str]] = defaultdict(list)
    for key, coord in mod.MANUAL_HEX.items():
        pin_targets[coord].append(key)
    pin_conflicts = {cell: keys for cell, keys in pin_targets.items() if len(keys) > 1}

    issues = mod.audit_england_placements(
        data["constituencies"],
        by_name,
        geo_lookup,
        cell_geos,
        england_coords,
    )
    if args.severe_only:
        issues = [
            row
            for row in issues
            if row["delta"] >= 0.8 or row["cur_d"] >= 1.0
        ]

    print(f"Election {args.election}")
    print(f"Duplicate cells: {len(dups)}")
    for cell, names in sorted(dups.items()):
        print(f"  {cell}: {names}")

    print(f"Manual pin target conflicts: {len(pin_conflicts)}")
    for cell, keys in sorted(pin_conflicts.items()):
        print(f"  {cell}: {keys}")

    inland_coast = []
    for c in data["constituencies"]:
        if c.get("nation") != "england":
            continue
        q, r = c.get("q"), c.get("r")
        if q is None or r not in (-44, -45):
            continue
        name = c["name"].lower()
        if any(
            token in name
            for token in (
                "london",
                "winchester",
                "bath",
                "basingstoke",
                "reading",
                "devizes",
                "wokingham",
                "buckingham",
                "slough",
                "wycombe",
                "brentford",
                "paddington",
                "fulham",
                "brixton",
                "wandsworth",
            )
        ):
            inland_coast.append(c)

    print(f"Inland seats on south-coast band (r=-44/-45): {len(inland_coast)}")
    for c in inland_coast:
        print(f"  {c['name']} ({c['q']},{c['r']})")

    print(f"Geo audit issues: {len(issues)}")
    for row in issues[:40]:
        print(
            f"  {row['name']:28} ({row['q']:>3},{row['r']:>3}) "
            f"Δ={row['delta']:+.2f} d={row['cur_d']:.2f} "
            f"anchor={row['anchor']} ({row['anchor_hex']} hex)"
        )
    if len(issues) > 40:
        print(f"  ... and {len(issues) - 40} more")

    return 1 if dups or inland_coast else 0


if __name__ == "__main__":
    sys.exit(main())
