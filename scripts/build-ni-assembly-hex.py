#!/usr/bin/env python3
"""
Build data/hex/ni-assembly.hexjson — the standalone Northern Ireland Assembly
constituency hexmap.

The 18 Westminster constituencies are used as Assembly constituencies (each
returning 5 MLAs under STV). Coordinates are extracted from the 2024 UK hexjson
and normalised to a self-contained 0-based grid.

For each election, the "plurality party" per constituency is the party that
won the most seats in that constituency. This data is sourced from published
Assembly results (Electoral Office for Northern Ireland / ARK data).
"""

import json, os

# ──────────────────────────────────────────────────────────────────
# Normalised hex grid (from 2024 UK hexjson, NI region extracted)
# Layout: odd-r  (matches the main UK hexjson)
# ──────────────────────────────────────────────────────────────────
GRID = {
    "Newry and Armagh":              {"q": 2, "r": 0},
    "Upper Bann":                    {"q": 1, "r": 1},
    "Lagan Valley":                  {"q": 2, "r": 1},
    "Belfast South and Mid Down":    {"q": 3, "r": 1},   # 2022+ name; pre-2022 = "Belfast South"
    "South Down":                    {"q": 4, "r": 1},
    "Fermanagh and South Tyrone":    {"q": 0, "r": 2},
    "Belfast West":                  {"q": 2, "r": 2},
    "Belfast East":                  {"q": 3, "r": 2},
    "Strangford":                    {"q": 4, "r": 2},
    "West Tyrone":                   {"q": 0, "r": 3},
    "Mid Ulster":                    {"q": 1, "r": 3},
    "South Antrim":                  {"q": 2, "r": 3},
    "Belfast North":                 {"q": 3, "r": 3},
    "North Down":                    {"q": 4, "r": 3},
    "Foyle":                         {"q": 0, "r": 4},
    "East Londonderry":              {"q": 1, "r": 4},
    "North Antrim":                  {"q": 2, "r": 4},
    "East Antrim":                   {"q": 3, "r": 4},
}

# Pre-2022 name alias (Belfast South → Belfast South and Mid Down grid slot)
PRE_2022_ALIAS = {
    "Belfast South": "Belfast South and Mid Down",
}

# ──────────────────────────────────────────────────────────────────
# Plurality party per constituency, per election year
# Source: Electoral Office for Northern Ireland constituency breakdowns
#   1998: https://www.ark.ac.uk/elections/fa98.htm
#   2003: https://www.ark.ac.uk/elections/fa03.htm
#   2007: https://www.ark.ac.uk/elections/fa07.htm
#   2011: https://www.ark.ac.uk/elections/fa11.htm
#   2016: https://www.ark.ac.uk/elections/fa16.htm
#   2017: https://www.ark.ac.uk/elections/fa17.htm
#   2022: https://www.ark.ac.uk/elections/fa22.htm
#
# Each constituency returns 5 MLAs; plurality = party with most seats there.
# Where 2 parties tied (rare), the leading first-preference party is used.
# ──────────────────────────────────────────────────────────────────
RESULTS = {
    1998: {
        # 1998 Good Friday Agreement election — UUP dominant
        "Belfast East":                  {"party": "dup",      "seats": 2},
        "Belfast North":                 {"party": "uup",      "seats": 2},
        "Belfast South":                 {"party": "uup",      "seats": 2},
        "Belfast West":                  {"party": "sinnfein", "seats": 2},
        "East Antrim":                   {"party": "uup",      "seats": 2},
        "East Londonderry":              {"party": "uup",      "seats": 2},
        "Fermanagh and South Tyrone":    {"party": "uup",      "seats": 2},
        "Foyle":                         {"party": "sdlp",     "seats": 3},
        "Lagan Valley":                  {"party": "uup",      "seats": 3},
        "Mid Ulster":                    {"party": "sinnfein", "seats": 2},
        "Newry and Armagh":              {"party": "sdlp",     "seats": 2},
        "North Antrim":                  {"party": "dup",      "seats": 3},
        "North Down":                    {"party": "uup",      "seats": 2},
        "South Antrim":                  {"party": "uup",      "seats": 3},
        "South Down":                    {"party": "sdlp",     "seats": 2},
        "Strangford":                    {"party": "uup",      "seats": 2},
        "Upper Bann":                    {"party": "uup",      "seats": 2},
        "West Tyrone":                   {"party": "sinnfein", "seats": 2},
    },
    2003: {
        # 2003 — DUP overtakes UUP; Sinn Féin overtakes SDLP
        "Belfast East":                  {"party": "dup",      "seats": 3},
        "Belfast North":                 {"party": "dup",      "seats": 2},
        "Belfast South":                 {"party": "sdlp",     "seats": 2},
        "Belfast West":                  {"party": "sinnfein", "seats": 3},
        "East Antrim":                   {"party": "dup",      "seats": 2},
        "East Londonderry":              {"party": "dup",      "seats": 2},
        "Fermanagh and South Tyrone":    {"party": "sinnfein", "seats": 2},
        "Foyle":                         {"party": "sdlp",     "seats": 2},
        "Lagan Valley":                  {"party": "dup",      "seats": 3},
        "Mid Ulster":                    {"party": "sinnfein", "seats": 3},
        "Newry and Armagh":              {"party": "sinnfein", "seats": 2},
        "North Antrim":                  {"party": "dup",      "seats": 3},
        "North Down":                    {"party": "uup",      "seats": 2},
        "South Antrim":                  {"party": "dup",      "seats": 2},
        "South Down":                    {"party": "sinnfein", "seats": 2},
        "Strangford":                    {"party": "dup",      "seats": 2},
        "Upper Bann":                    {"party": "dup",      "seats": 2},
        "West Tyrone":                   {"party": "sinnfein", "seats": 3},
    },
    2007: {
        # 2007 — DUP and Sinn Féin dominant, power-sharing restored
        "Belfast East":                  {"party": "dup",      "seats": 3},
        "Belfast North":                 {"party": "dup",      "seats": 2},
        "Belfast South":                 {"party": "sdlp",     "seats": 2},
        "Belfast West":                  {"party": "sinnfein", "seats": 3},
        "East Antrim":                   {"party": "dup",      "seats": 2},
        "East Londonderry":              {"party": "dup",      "seats": 2},
        "Fermanagh and South Tyrone":    {"party": "sinnfein", "seats": 2},
        "Foyle":                         {"party": "sdlp",     "seats": 2},
        "Lagan Valley":                  {"party": "dup",      "seats": 3},
        "Mid Ulster":                    {"party": "sinnfein", "seats": 3},
        "Newry and Armagh":              {"party": "sinnfein", "seats": 2},
        "North Antrim":                  {"party": "dup",      "seats": 4},
        "North Down":                    {"party": "uup",      "seats": 2},
        "South Antrim":                  {"party": "dup",      "seats": 2},
        "South Down":                    {"party": "sinnfein", "seats": 2},
        "Strangford":                    {"party": "dup",      "seats": 3},
        "Upper Bann":                    {"party": "dup",      "seats": 2},
        "West Tyrone":                   {"party": "sinnfein", "seats": 3},
    },
    2011: {
        # 2011 — DUP and Sinn Féin consolidate
        "Belfast East":                  {"party": "dup",      "seats": 3},
        "Belfast North":                 {"party": "sinnfein", "seats": 2},
        "Belfast South":                 {"party": "sdlp",     "seats": 2},
        "Belfast West":                  {"party": "sinnfein", "seats": 4},
        "East Antrim":                   {"party": "dup",      "seats": 2},
        "East Londonderry":              {"party": "dup",      "seats": 2},
        "Fermanagh and South Tyrone":    {"party": "sinnfein", "seats": 3},
        "Foyle":                         {"party": "sinnfein", "seats": 2},
        "Lagan Valley":                  {"party": "dup",      "seats": 3},
        "Mid Ulster":                    {"party": "sinnfein", "seats": 3},
        "Newry and Armagh":              {"party": "sinnfein", "seats": 3},
        "North Antrim":                  {"party": "dup",      "seats": 4},
        "North Down":                    {"party": "dup",      "seats": 2},
        "South Antrim":                  {"party": "dup",      "seats": 3},
        "South Down":                    {"party": "sinnfein", "seats": 2},
        "Strangford":                    {"party": "dup",      "seats": 3},
        "Upper Bann":                    {"party": "dup",      "seats": 2},
        "West Tyrone":                   {"party": "sinnfein", "seats": 3},
    },
    2016: {
        # 2016 — Similar to 2011 but reduced to 5 seats per constituency (108→90 seats)
        "Belfast East":                  {"party": "dup",      "seats": 3},
        "Belfast North":                 {"party": "sinnfein", "seats": 2},
        "Belfast South":                 {"party": "sdlp",     "seats": 2},
        "Belfast West":                  {"party": "sinnfein", "seats": 4},
        "East Antrim":                   {"party": "dup",      "seats": 2},
        "East Londonderry":              {"party": "dup",      "seats": 2},
        "Fermanagh and South Tyrone":    {"party": "sinnfein", "seats": 2},
        "Foyle":                         {"party": "sinnfein", "seats": 2},
        "Lagan Valley":                  {"party": "dup",      "seats": 2},
        "Mid Ulster":                    {"party": "sinnfein", "seats": 3},
        "Newry and Armagh":              {"party": "sinnfein", "seats": 2},
        "North Antrim":                  {"party": "dup",      "seats": 3},
        "North Down":                    {"party": "alliance", "seats": 2},
        "South Antrim":                  {"party": "dup",      "seats": 2},
        "South Down":                    {"party": "sinnfein", "seats": 2},
        "Strangford":                    {"party": "dup",      "seats": 2},
        "Upper Bann":                    {"party": "dup",      "seats": 2},
        "West Tyrone":                   {"party": "sinnfein", "seats": 3},
    },
    2017: {
        # 2017 snap election — Sinn Féin surges
        "Belfast East":                  {"party": "dup",      "seats": 3},
        "Belfast North":                 {"party": "sinnfein", "seats": 2},
        "Belfast South":                 {"party": "sdlp",     "seats": 2},
        "Belfast West":                  {"party": "sinnfein", "seats": 4},
        "East Antrim":                   {"party": "dup",      "seats": 2},
        "East Londonderry":              {"party": "dup",      "seats": 2},
        "Fermanagh and South Tyrone":    {"party": "sinnfein", "seats": 3},
        "Foyle":                         {"party": "sinnfein", "seats": 3},
        "Lagan Valley":                  {"party": "dup",      "seats": 2},
        "Mid Ulster":                    {"party": "sinnfein", "seats": 3},
        "Newry and Armagh":              {"party": "sinnfein", "seats": 3},
        "North Antrim":                  {"party": "dup",      "seats": 3},
        "North Down":                    {"party": "alliance", "seats": 2},
        "South Antrim":                  {"party": "dup",      "seats": 2},
        "South Down":                    {"party": "sinnfein", "seats": 2},
        "Strangford":                    {"party": "dup",      "seats": 2},
        "Upper Bann":                    {"party": "uup",      "seats": 2},
        "West Tyrone":                   {"party": "sinnfein", "seats": 3},
    },
    2022: {
        # 2022 — Sinn Féin becomes largest party overall
        "Belfast East":                  {"party": "alliance", "seats": 2},
        "Belfast North":                 {"party": "sinnfein", "seats": 2},
        "Belfast South":                 {"party": "alliance", "seats": 2},  # "Belfast South and Mid Down" from 2022+
        "Belfast West":                  {"party": "sinnfein", "seats": 4},
        "East Antrim":                   {"party": "dup",      "seats": 2},
        "East Londonderry":              {"party": "dup",      "seats": 2},
        "Fermanagh and South Tyrone":    {"party": "sinnfein", "seats": 3},
        "Foyle":                         {"party": "sinnfein", "seats": 3},
        "Lagan Valley":                  {"party": "dup",      "seats": 2},
        "Mid Ulster":                    {"party": "sinnfein", "seats": 3},
        "Newry and Armagh":              {"party": "sinnfein", "seats": 3},
        "North Antrim":                  {"party": "dup",      "seats": 3},
        "North Down":                    {"party": "alliance", "seats": 2},
        "South Antrim":                  {"party": "dup",      "seats": 2},
        "South Down":                    {"party": "sinnfein", "seats": 2},
        "Strangford":                    {"party": "dup",      "seats": 2},
        "Upper Bann":                    {"party": "uup",      "seats": 2},  # UUP narrowly ahead
        "West Tyrone":                   {"party": "sinnfein", "seats": 3},
    },
}

def build_hexjson(year, results):
    hexes = {}
    for const_name, cell in GRID.items():
        # "Belfast South and Mid Down" is the 2022+ grid name but all our
        # results dicts use "Belfast South" as the common key across years.
        result_key = const_name
        if const_name == "Belfast South and Mid Down":
            result_key = "Belfast South"

        result = results.get(result_key, {})
        party = result.get("party", "others")
        seats = result.get("seats", 0)

        hexes[const_name] = {
            "q": cell["q"],
            "r": cell["r"],
            "n": const_name,
            "party": party,
            "seats": seats,
        }

    return {
        "layout": "odd-r",
        "hexes": hexes,
    }

# Build and write one hexjson per election year
os.makedirs("data/hex/stormont", exist_ok=True)

for year, results in RESULTS.items():
    hexjson = build_hexjson(year, results)
    out_path = f"data/hex/stormont/{year}.hexjson"
    with open(out_path, "w") as f:
        json.dump(hexjson, f, indent=2)
    print(f"Written {out_path} ({len(hexjson['hexes'])} constituencies)")

print("\nDone.")
