#!/usr/bin/env python3
"""Build a compact HexJSON grid for GLC 1973–81 (92 divisions).

Hand-laid from the official GLCE ‘Political representation of constituencies’
diagrams. Wider than tall (Greater London’s real proportions). Central
Westminster block matches the map: Paddington north-west of City of London
and Westminster South.

Usage:
  python3 scripts/build-glc-grid.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "hex" / "glc-grid.json"

# Wide odd-r cartogram — rows north→south, cells west→east.
# ~16 columns × 9 rows so the drawn map reads wider than tall.
ROWS: list[list[str | None]] = [
    # Far north
    [
        None,
        None,
        None,
        None,
        "Chipping Barnet",
        "Hendon North",
        "Enfield North",
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    ],
    # North fringe (Barnet / Enfield / NE)
    [
        None,
        "Harrow West",
        "Harrow East",
        "Hendon South",
        "Finchley",
        "Southgate",
        "Edmonton",
        "Chingford",
        "Wanstead and Woodford",
        "Ilford North",
        "Romford",
        "Upminster",
        None,
        None,
        None,
        None,
    ],
    # Outer north
    [
        "Ruislip-Northwood",
        "Harrow Central",
        "Brent North",
        "Brent East",
        "Hornsey",
        "Wood Green",
        "Tottenham",
        "Walthamstow",
        "Leyton",
        "Ilford South",
        "Hornchurch",
        None,
        None,
        None,
        None,
        None,
    ],
    # Mid-north
    [
        "Uxbridge",
        "Ealing North",
        "Acton",
        "Brent South",
        "Hampstead",
        "St Pancras North",
        "Islington North",
        "Hackney North and Stoke Newington",
        "Hackney Central",
        "Newham North West",
        "Newham North East",
        None,
        None,
        None,
        None,
        None,
    ],
    # North bank / inner north
    #   HammN | Kensington | Paddington | St Marylebone | Holborn | …
    [
        "Hayes and Harlington",
        "Southall",
        "Hammersmith North",
        "Kensington",
        "Paddington",
        "St Marylebone",
        "Holborn and St Pancras South",
        "Islington Central",
        "Islington South and Finsbury",
        "Hackney South and Shoreditch",
        "Bethnal Green and Bow",
        None,
        None,
        None,
        None,
        None,
    ],
    # River corridor (north bank)
    #   Kens(3) Pad(4) Mary(5)
    #   Chel(3)  ·   City(5) Stepney → Newham S → Barking → Dagenham
    # Paddington is NW of City/Westminster South
    [
        "Feltham and Heston",
        "Brentford and Isleworth",
        "Fulham",
        "Chelsea",
        None,
        "City of London and Westminster South",
        "Stepney and Poplar",
        "Newham South",
        "Barking",
        "Dagenham",
        None,
        None,
        None,
        None,
        None,
        None,
    ],
    # South bank riverside — Vauxhall under Paddington / SW of City
    [
        "Richmond",
        "Putney",
        "Battersea North",
        "Vauxhall",
        "Bermondsey",
        "Deptford",
        "Greenwich",
        "Woolwich East",
        "Erith and Crayford",
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    ],
    # Inner south
    [
        "Twickenham",
        "Battersea South",
        "Lambeth Central",
        "Peckham",
        "Lewisham West",
        "Lewisham East",
        "Woolwich West",
        "Bexleyheath",
        "Sidcup",
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    ],
    # Outer south
    [
        "Kingston upon Thames",
        "Tooting",
        "Streatham",
        "Norwood",
        "Dulwich",
        "Beckenham",
        "Chislehurst",
        "Ravensbourne",
        "Orpington",
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    ],
    # Far south
    [
        "Surbiton",
        "Wimbledon",
        "Mitcham and Morden",
        "Sutton and Cheam",
        "Carshalton",
        "Croydon North West",
        "Croydon North East",
        "Croydon Central",
        "Croydon South",
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    ],
]


def main() -> None:
    hexes: dict[str, dict] = {}
    seen: set[str] = set()
    n_rows = len(ROWS)
    for row_i, row in enumerate(ROWS):
        r = n_rows - 1 - row_i
        for q, name in enumerate(row):
            if not name:
                continue
            if name in seen:
                raise SystemExit(f"Duplicate seat: {name}")
            seen.add(name)
            key = name.lower().replace(" ", "-")
            hexes[key] = {"q": q, "r": r, "n": name}

    if len(hexes) != 92:
        # Help debug missing/extra vs a flat expected list from names in ROWS
        raise SystemExit(f"Expected 92 seats, got {len(hexes)}")

    min_q = min(h["q"] for h in hexes.values())
    min_r = min(h["r"] for h in hexes.values())
    for h in hexes.values():
        h["q"] -= min_q
        h["r"] -= min_r

    pad = next(h for h in hexes.values() if h["n"] == "Paddington")
    city = next(
        h for h in hexes.values() if h["n"] == "City of London and Westminster South"
    )
    mary = next(h for h in hexes.values() if h["n"] == "St Marylebone")
    if not (pad["r"] > city["r"] and pad["q"] < city["q"]):
        raise SystemExit(
            f"Paddington must be NW of City/Westminster South; "
            f"Pad q={pad['q']} r={pad['r']}, City q={city['q']} r={city['r']}"
        )
    if not (mary["r"] > city["r"] and mary["q"] >= city["q"]):
        raise SystemExit(
            f"St Marylebone must be N/NE of City/Westminster South; "
            f"Mary q={mary['q']} r={mary['r']}, City q={city['q']} r={city['r']}"
        )

    doc = {
        "_comment": (
            "92 GLC single-member electoral divisions (1973–1981). Wide odd-r "
            "cartogram from the GLCE ‘Political representation of constituencies’ "
            "diagrams — wider than tall like Greater London. q east, r north."
        ),
        "layout": "odd-r",
        "hexes": dict(sorted(hexes.items(), key=lambda kv: kv[1]["n"])),
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    by = {(h["q"], h["r"]): h["n"] for h in hexes.values()}
    max_q = max(q for q, _ in by)
    max_r = max(r for _, r in by)

    def short(n: str) -> str:
        return (
            n.replace(" and ", " & ")
            .replace(" North", " N")
            .replace(" South", " S")
            .replace(" East", " E")
            .replace(" West", " W")
            .replace(" Central", " C")
            .replace("City of London & Westminster S", "City/West S")
        )[:9]

    w, h = max_q + 1, max_r + 1
    aspect = (w * math.sqrt(3)) / (h * 1.5)
    print(f"Wrote {OUT} ({len(hexes)} seats)")
    print(f"Grid {w}×{h} · approx visual W/H = {aspect:.2f}\n")
    for r in range(max_r, -1, -1):
        parts = [
            f"{short(by[(q, r)]):9}" if (q, r) in by else " " * 9
            for q in range(w)
        ]
        if any(p.strip() for p in parts):
            print(f"r={r:2}|" + "|".join(parts))

    print("\nCentral block (Paddington should be NW of City/Westminster South):")
    for name in [
        "Kensington",
        "Paddington",
        "St Marylebone",
        "Chelsea",
        "City of London and Westminster South",
        "Vauxhall",
    ]:
        x = next(v for v in hexes.values() if v["n"] == name)
        print(f"  {name:40} q={x['q']:2} r={x['r']:2}")


if __name__ == "__main__":
    main()
