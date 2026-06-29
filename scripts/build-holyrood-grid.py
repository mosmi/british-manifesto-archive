#!/usr/bin/env python3
"""Generate data/hex/holyrood-grid.json — the hex grid for the 73 Scottish
Parliament constituencies, keyed by the canonical (2011-2021) constituency names
that build-holyrood-hex.py maps every election onto.

The layout is taken directly from the Devolved Elections "Land Doesn't Vote"
Scotland constituency hexmap (2026 boundaries):
https://devolvedelections.co.uk/blog/land-doesnt-vote-hexmaps/

Each DDE hex centre was converted from its SVG pixel position into our odd-r
(pointy-top) axial coordinates — higher r = north, higher q = east — matching
js/hexmap.js and the Open Innovations convention. The 2026 boundary names were
then translated onto our canonical 2011-2021 namespace (e.g. "Glasgow Central"
-> glasgow kelvin, "Bathgate" -> linlithgow). Two adjustments were needed:
  * glasgow pollok — 2026 merges Cathcart+Pollok into one hex, so Pollok (a
    separate seat in 2011-2021) is placed in the free cell just SW of Cathcart.
  * The 2026-only "Edinburgh Northern" hex (DDE cell q6 r4) has no 2011-2021
    equivalent; it is wired up as a 2026 overflow cell in build-holyrood-hex.py.

Run this, eyeball the printed ASCII preview, then run build-holyrood-hex.py to
regenerate the per-election hexjson files.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "hex" / "holyrood-grid.json"

# Canonical constituency (normalized 2011-2021 name) -> (q, r), from the DDE
# 2026 Scotland hexmap. Sorted north (high r) to south.
COORDS = {
    "shetland":                                    (7, 16),
    "orkney":                                      (5, 15),
    "caithness sutherland and ross":               (4, 13),
    "skye lochaber and badenoch":                  (4, 12),
    "moray":                                       (6, 12),
    "banffshire and buchan coast":                 (7, 12),
    "aberdeenshire east":                          (8, 12),
    "na h eileanan an iar":                        (1, 11),
    "argyll and bute":                             (3, 11),
    "inverness and nairn":                         (4, 11),
    "aberdeenshire west":                          (5, 11),
    "aberdeen donside":                            (6, 11),
    "aberdeen central":                            (7, 11),
    "dumbarton":                                   (4, 10),
    "perthshire north":                            (5, 10),
    "aberdeen south and north kincardine":         (6, 10),
    "angus north and mearns":                      (7, 10),
    "greenock and inverclyde":                     (2, 9),
    "perthshire south and kinross shire":          (3, 9),
    "dundee city west":                            (4, 9),
    "dundee city east":                            (5, 9),
    "angus south":                                 (6, 9),
    "clydebank and milngavie":                     (2, 8),
    "strathkelvin and bearsden":                   (3, 8),
    "falkirk west":                                (4, 8),
    "stirling":                                    (5, 8),
    "mid fife and glenrothes":                     (6, 8),
    "north east fife":                             (7, 8),
    "glasgow anniesland":                          (1, 7),
    "glasgow maryhill and springburn":             (2, 7),
    "cumbernauld and kilsyth":                     (3, 7),
    "falkirk east":                                (4, 7),
    "cowdenbeath":                                 (5, 7),
    "kirkcaldy":                                   (6, 7),
    "glasgow pollok":                              (0, 6),
    "paisley":                                     (1, 6),
    "glasgow kelvin":                              (2, 6),
    "glasgow shettleston":                         (3, 6),
    "glasgow provan":                              (4, 6),
    "dunfermline":                                 (5, 6),
    "cunninghame north":                           (0, 5),
    "glasgow cathcart":                            (1, 5),
    "glasgow southside":                           (2, 5),
    "rutherglen":                                  (3, 5),
    "clackmannanshire and dunblane":               (4, 5),
    "renfrewshire south":                          (1, 4),
    "uddingston and bellshill":                    (2, 4),
    "coatbridge and chryston":                     (3, 4),
    "linlithgow":                                  (4, 4),
    "edinburgh western":                           (5, 4),
    "edinburgh northern and leith":                (7, 4),
    "cunninghame south":                           (0, 3),
    "renfrewshire north and west":                 (1, 3),
    "motherwell and wishaw":                       (2, 3),
    "airdrie and shotts":                          (3, 3),
    "almond valley":                               (4, 3),
    "edinburgh pentlands":                         (5, 3),
    "edinburgh central":                           (6, 3),
    "ayr":                                         (0, 2),
    "kilmarnock and irvine valley":                (1, 2),
    "eastwood":                                    (2, 2),
    "east kilbride":                               (3, 2),
    "hamilton larkhall and stonehouse":            (4, 2),
    "midlothian north and musselburgh":            (5, 2),
    "edinburgh southern":                          (6, 2),
    "edinburgh eastern":                           (7, 2),
    "carrick cumnock and doon valley":             (1, 1),
    "clydesdale":                                  (2, 1),
    "midlothian south tweeddale and lauderdale":   (3, 1),
    "east lothian":                                (4, 1),
    "galloway and west dumfries":                  (2, 0),
    "dumfriesshire":                               (3, 0),
    "ettrick roxburgh and berwickshire":           (4, 0),
}


def short(name):
    parts = name.split()
    if name.startswith("glasgow"):
        return "G" + parts[1][:2].title()
    if name.startswith("edinburgh"):
        return "E" + parts[1][:2].title()
    return (parts[0][:3]).title()


def preview():
    rs = [r for _, r in COORDS.values()]
    qs = [q for q, _ in COORDS.values()]
    by_pos = {(q, r): short(n) for n, (q, r) in COORDS.items()}
    print("\nodd-r preview (north at top; odd rows shifted right):\n")
    for r in range(max(rs), min(rs) - 1, -1):
        indent = "   " if (r % 2 != 0) else ""
        cells = []
        for q in range(min(qs), max(qs) + 1):
            cells.append(f"{by_pos.get((q, r), '.'):>5}")
        print(f"r{r:>2} {indent}" + " ".join(cells))
    print()


def main():
    seen = {}
    for name, pos in COORDS.items():
        if pos in seen:
            raise SystemExit(f"DUPLICATE position {pos}: {name} and {seen[pos]}")
        seen[pos] = name
    if len(COORDS) != 73:
        raise SystemExit(f"Expected 73 constituencies, got {len(COORDS)}")

    doc = {
        "_comment": "Hex grid for the 73 Scottish Parliament constituencies, adapted from the "
                    "Devolved Elections 'Land Doesn't Vote' 2026 Scotland hexmap. "
                    "Generated by scripts/build-holyrood-grid.py.",
        "layout": "odd-r",
        "hexes": {name: {"q": q, "r": r} for name, (q, r) in COORDS.items()},
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({len(COORDS)} hexes)")
    preview()


if __name__ == "__main__":
    main()
