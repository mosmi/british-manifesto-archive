#!/usr/bin/env python3
"""Audit England constituency hex placements against 1983 GeoJSON centroids."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "constituencies"


def load_import_module():
    path = ROOT / "scripts" / "import-historical-hexmaps.py"
    spec = importlib.util.spec_from_file_location("import_hex", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit England hex placement quality")
    parser.add_argument(
        "--election",
        default="1983",
        choices=("1983", "1987", "1992"),
        help="Election JSON to audit (default: 1983)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on any flagged seat (default: only critical)",
    )
    args = parser.parse_args()

    mod = load_import_module()
    by_name, scaffold_coords, _ni, _gb, _sc, _wa, england_coords = mod.build_scaffold()
    geo_lookup = mod.load_geo_lookup()
    cell_geos = mod.build_cell_geos(geo_lookup, scaffold_coords)

    data = json.loads((OUT / f"{args.election}.json").read_text(encoding="utf-8"))
    issues = mod.audit_england_placements(
        data["constituencies"],
        by_name,
        geo_lookup,
        cell_geos,
        england_coords,
    )

    england_seats = sum(
        1
        for c in data["constituencies"]
        if c.get("nation") == "england" and c.get("q") is not None
    )
    critical = [
        row
        for row in issues
        if row["delta"] >= 1.0 or row["cur_d"] >= 1.2 or (row["anchor_hex"] or 0) > 10
    ]
    moderate = [
        row
        for row in issues
        if row not in critical
        and (row["delta"] >= 0.5 or row["cur_d"] >= 0.8)
    ]
    print(
        f"{args.election}: {england_seats} England seats, "
        f"{len(issues)} flagged ({len(critical)} severe, {len(moderate)} moderate)"
    )

    for row in issues:
        if row in critical:
            tag = "SEVERE"
        elif row in moderate:
            tag = "moderate"
        else:
            tag = "minor"
        anchor = row["anchor"] or "—"
        ah = row["anchor_hex"] if row["anchor_hex"] is not None else "—"
        print(
            f"  [{tag}] {row['name']}: ({row['q']},{row['r']}) "
            f"geo={row['cur_d']:.2f}° Δ={row['delta']:.2f}° "
            f"anchor={anchor} ({ah} hex) — {'; '.join(row['reasons'])}"
        )

    if args.strict:
        return 1 if issues else 0
    return 1 if critical else 0


if __name__ == "__main__":
    raise SystemExit(main())
