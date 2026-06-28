#!/usr/bin/env python3
"""
Build data/hex/ni-assembly.hexjson — the standalone Northern Ireland Assembly
constituency hexmap.

Each constituency returns 5 (since 2017) or 6 (1998-2016) MLAs.
We store the complete list of seats won by party in each constituency under 'seats_list'
and the plurality party under 'party'.
"""

import json, os

# Normalised hex grid coordinates
GRID = {
    "Newry and Armagh":              {"q": 2, "r": 1},
    "Upper Bann":                    {"q": 1, "r": 2},
    "Lagan Valley":                  {"q": 2, "r": 2},
    "Belfast South and Mid Down":    {"q": 3, "r": 2},   # 2022+ name
    "South Down":                    {"q": 4, "r": 2},
    "Fermanagh and South Tyrone":    {"q": 0, "r": 3},
    "Belfast West":                  {"q": 2, "r": 3},
    "Belfast East":                  {"q": 3, "r": 3},
    "Strangford":                    {"q": 4, "r": 3},
    "West Tyrone":                   {"q": 0, "r": 4},
    "Mid Ulster":                    {"q": 1, "r": 4},
    "South Antrim":                  {"q": 2, "r": 4},
    "Belfast North":                 {"q": 3, "r": 4},
    "North Down":                    {"q": 4, "r": 4},
    "Foyle":                         {"q": 0, "r": 5},
    "East Londonderry":              {"q": 1, "r": 5},
    "North Antrim":                  {"q": 2, "r": 5},
    "East Antrim":                   {"q": 3, "r": 5},
}

# Detailed seats won per constituency
RESULTS = {
    1998: {
        "Belfast East":                  ["dup", "dup", "uup", "uup", "alliance", "ukup"],
        "Belfast North":                 ["uup", "uup", "dup", "sinnfein", "sdlp", "pup"],
        "Belfast South":                 ["uup", "uup", "sdlp", "sdlp", "niwc", "dup"],
        "Belfast West":                  ["sinnfein", "sinnfein", "sinnfein", "sinnfein", "sdlp", "pup"],
        "East Antrim":                   ["uup", "uup", "dup", "dup", "alliance", "ukup"],
        "East Londonderry":              ["uup", "uup", "sdlp", "sdlp", "dup", "independent"],
        "Fermanagh and South Tyrone":    ["uup", "uup", "sdlp", "sdlp", "dup", "sinnfein"],
        "Foyle":                         ["sdlp", "sdlp", "sdlp", "sinnfein", "dup", "uup"],
        "Lagan Valley":                  ["uup", "uup", "sdlp", "dup", "alliance", "ukup"],
        "Mid Ulster":                    ["sinnfein", "sinnfein", "sinnfein", "sdlp", "uup", "dup"],
        "Newry and Armagh":              ["sdlp", "sdlp", "sinnfein", "sinnfein", "uup", "dup"],
        "North Antrim":                  ["dup", "dup", "dup", "uup", "uup", "sdlp"],
        "North Down":                    ["uup", "uup", "uup", "alliance", "ukup", "niwc"],
        "South Antrim":                  ["uup", "uup", "dup", "ukup", "sdlp", "alliance"],
        "South Down":                    ["sdlp", "sdlp", "sdlp", "sinnfein", "uup", "dup"],
        "Strangford":                    ["uup", "uup", "dup", "dup", "alliance", "ukup"],
        "Upper Bann":                    ["uup", "uup", "dup", "sdlp", "sinnfein", "independent"],
        "West Tyrone":                   ["sinnfein", "sinnfein", "sdlp", "sdlp", "uup", "dup"],
    },
    2003: {
        "Belfast East":                  ["uup", "uup", "dup", "dup", "pup", "alliance"],
        "Belfast North":                 ["dup", "dup", "sinnfein", "sinnfein", "uup", "sdlp"],
        "Belfast South":                 ["uup", "uup", "sdlp", "sdlp", "dup", "sinnfein"],
        "Belfast West":                  ["sinnfein", "sinnfein", "sinnfein", "sinnfein", "sdlp", "dup"],
        "East Antrim":                   ["dup", "dup", "dup", "uup", "uup", "alliance"],
        "East Londonderry":              ["dup", "dup", "uup", "uup", "sinnfein", "sdlp"],
        "Fermanagh and South Tyrone":    ["sinnfein", "sinnfein", "uup", "uup", "dup", "sdlp"],
        "Foyle":                         ["sdlp", "sdlp", "sdlp", "sinnfein", "sinnfein", "dup"],
        "Lagan Valley":                  ["uup", "uup", "uup", "dup", "sdlp", "alliance"],
        "Mid Ulster":                    ["sinnfein", "sinnfein", "sinnfein", "dup", "uup", "sdlp"],
        "Newry and Armagh":              ["sinnfein", "sinnfein", "sinnfein", "dup", "uup", "sdlp"],
        "North Antrim":                  ["dup", "dup", "dup", "sinnfein", "sdlp", "uup"],
        "North Down":                    ["uup", "uup", "dup", "dup", "alliance", "ukup"],
        "South Antrim":                  ["dup", "dup", "uup", "uup", "sdlp", "alliance"],
        "South Down":                    ["sinnfein", "sinnfein", "sdlp", "sdlp", "dup", "uup"],
        "Strangford":                    ["dup", "dup", "dup", "uup", "uup", "alliance"],
        "Upper Bann":                    ["dup", "dup", "uup", "uup", "sdlp", "sinnfein"],
        "West Tyrone":                   ["sinnfein", "sinnfein", "dup", "uup", "sdlp", "independent"],
    },
    2007: {
        "Belfast East":                  ["dup", "dup", "dup", "uup", "alliance", "pup"],
        "Belfast North":                 ["dup", "dup", "sinnfein", "sinnfein", "uup", "sdlp"],
        "Belfast South":                 ["sdlp", "sinnfein", "uup", "dup", "alliance", "alliance"],
        "Belfast West":                  ["sinnfein", "sinnfein", "sinnfein", "sinnfein", "sinnfein", "sdlp"],
        "East Antrim":                   ["dup", "dup", "dup", "uup", "uup", "alliance"],
        "East Londonderry":              ["dup", "dup", "dup", "sinnfein", "uup", "sdlp"],
        "Fermanagh and South Tyrone":    ["sinnfein", "sinnfein", "sinnfein", "dup", "dup", "uup"],
        "Foyle":                         ["sdlp", "sdlp", "sdlp", "sinnfein", "sinnfein", "dup"],
        "Lagan Valley":                  ["dup", "dup", "dup", "uup", "uup", "alliance"],
        "Mid Ulster":                    ["sinnfein", "sinnfein", "sinnfein", "dup", "dup", "uup"],
        "Newry and Armagh":              ["sinnfein", "sinnfein", "sinnfein", "dup", "uup", "sdlp"],
        "North Antrim":                  ["dup", "dup", "dup", "dup", "sinnfein", "uup"],
        "North Down":                    ["uup", "uup", "dup", "dup", "alliance", "gpni"],
        "South Antrim":                  ["dup", "dup", "uup", "sinnfein", "alliance", "sdlp"],
        "South Down":                    ["sinnfein", "sinnfein", "sdlp", "sdlp", "dup", "uup"],
        "Strangford":                    ["dup", "dup", "dup", "uup", "uup", "alliance"],
        "Upper Bann":                    ["dup", "dup", "sinnfein", "sinnfein", "uup", "sdlp"],
        "West Tyrone":                   ["sinnfein", "sinnfein", "dup", "uup", "sdlp", "independent"],
    },
    2011: {
        "Belfast East":                  ["dup", "dup", "dup", "alliance", "alliance", "uup"],
        "Belfast North":                 ["dup", "dup", "dup", "sinnfein", "sinnfein", "sdlp"],
        "Belfast South":                 ["sdlp", "sdlp", "alliance", "dup", "sinnfein", "uup"],
        "Belfast West":                  ["sinnfein", "sinnfein", "sinnfein", "sinnfein", "sinnfein", "sdlp"],
        "East Antrim":                   ["dup", "dup", "dup", "uup", "alliance", "sinnfein"],
        "East Londonderry":              ["dup", "dup", "dup", "sdlp", "independent", "sinnfein"],
        "Fermanagh and South Tyrone":    ["sinnfein", "sinnfein", "sinnfein", "dup", "dup", "uup"],
        "Foyle":                         ["sdlp", "sdlp", "sdlp", "sinnfein", "sinnfein", "dup"],
        "Lagan Valley":                  ["dup", "dup", "dup", "dup", "uup", "alliance"],
        "Mid Ulster":                    ["sinnfein", "sinnfein", "sinnfein", "dup", "uup", "sdlp"],
        "Newry and Armagh":              ["sinnfein", "sinnfein", "sinnfein", "sdlp", "sdlp", "dup"],
        "North Antrim":                  ["dup", "dup", "dup", "sinnfein", "uup", "tuv"],
        "North Down":                    ["dup", "dup", "dup", "uup", "alliance", "gpni"],
        "South Antrim":                  ["dup", "dup", "sinnfein", "uup", "sdlp", "alliance"],
        "South Down":                    ["sdlp", "sdlp", "sdlp", "sinnfein", "sinnfein", "dup"],
        "Strangford":                    ["dup", "dup", "dup", "uup", "uup", "alliance"],
        "Upper Bann":                    ["dup", "dup", "sinnfein", "sinnfein", "uup", "sdlp"],
        "West Tyrone":                   ["sinnfein", "sinnfein", "sinnfein", "dup", "dup", "uup"],
    },
    2016: {
        "Belfast East":                  ["dup", "dup", "dup", "alliance", "alliance", "uup"],
        "Belfast North":                 ["dup", "dup", "dup", "sinnfein", "sinnfein", "sdlp"],
        "Belfast South":                 ["dup", "dup", "sinnfein", "sdlp", "alliance", "gpni"],
        "Belfast West":                  ["sinnfein", "sinnfein", "sinnfein", "sinnfein", "sdlp", "pbp"],
        "East Antrim":                   ["dup", "dup", "dup", "uup", "alliance", "sinnfein"],
        "East Londonderry":              ["dup", "dup", "dup", "sinnfein", "sdlp", "independent"],
        "Fermanagh and South Tyrone":    ["dup", "dup", "sinnfein", "sinnfein", "uup", "sdlp"],
        "Foyle":                         ["sdlp", "sdlp", "sinnfein", "sinnfein", "dup", "pbp"],
        "Lagan Valley":                  ["dup", "dup", "dup", "uup", "uup", "alliance"],
        "Mid Ulster":                    ["sinnfein", "sinnfein", "sinnfein", "dup", "uup", "sdlp"],
        "Newry and Armagh":              ["sinnfein", "sinnfein", "sinnfein", "sdlp", "uup", "dup"],
        "North Antrim":                  ["dup", "dup", "dup", "tuv", "sinnfein", "uup"],
        "North Down":                    ["dup", "dup", "dup", "alliance", "uup", "gpni"],
        "South Antrim":                  ["dup", "dup", "dup", "sinnfein", "uup", "alliance"],
        "South Down":                    ["sdlp", "sdlp", "sinnfein", "sinnfein", "dup", "uup"],
        "Strangford":                    ["dup", "dup", "dup", "uup", "uup", "alliance"],
        "Upper Bann":                    ["dup", "dup", "sinnfein", "sinnfein", "uup", "uup"],
        "West Tyrone":                   ["sinnfein", "sinnfein", "sinnfein", "dup", "uup", "sdlp"],
    },
    2017: {
        "Belfast East":                  ["dup", "dup", "dup", "alliance", "uup"],
        "Belfast North":                 ["dup", "dup", "sinnfein", "sinnfein", "sdlp"],
        "Belfast South":                 ["dup", "sinnfein", "sdlp", "alliance", "gpni"],
        "Belfast West":                  ["sinnfein", "sinnfein", "sinnfein", "sinnfein", "pbp"],
        "East Antrim":                   ["dup", "dup", "uup", "uup", "alliance"],
        "East Londonderry":              ["dup", "dup", "sinnfein", "sdlp", "uup"],
        "Fermanagh and South Tyrone":    ["sinnfein", "sinnfein", "dup", "dup", "uup"],
        "Foyle":                         ["sinnfein", "sinnfein", "sdlp", "sdlp", "dup"],
        "Lagan Valley":                  ["dup", "dup", "dup", "uup", "alliance"],
        "Mid Ulster":                    ["sinnfein", "sinnfein", "sinnfein", "dup", "sdlp"],
        "Newry and Armagh":              ["sinnfein", "sinnfein", "sinnfein", "sdlp", "dup"],
        "North Antrim":                  ["dup", "dup", "sinnfein", "uup", "tuv"],
        "North Down":                    ["dup", "dup", "alliance", "uup", "gpni"],
        "South Antrim":                  ["dup", "dup", "sinnfein", "uup", "alliance"],
        "South Down":                    ["sinnfein", "sinnfein", "sdlp", "sdlp", "dup"],
        "Strangford":                    ["dup", "dup", "dup", "uup", "alliance"],
        "Upper Bann":                    ["dup", "dup", "sinnfein", "sinnfein", "uup"],
        "West Tyrone":                   ["sinnfein", "sinnfein", "sinnfein", "dup", "sdlp"],
    },
    2022: {
        "Belfast East":                  ["dup", "dup", "alliance", "alliance", "uup"],
        "Belfast North":                 ["sinnfein", "sinnfein", "dup", "dup", "alliance"],
        "Belfast South":                 ["sinnfein", "dup", "alliance", "alliance", "sdlp"],
        "Belfast West":                  ["sinnfein", "sinnfein", "sinnfein", "sinnfein", "pbp"],
        "East Antrim":                   ["dup", "dup", "alliance", "alliance", "uup"],
        "East Londonderry":              ["dup", "dup", "sinnfein", "sdlp", "independent"],
        "Fermanagh and South Tyrone":    ["sinnfein", "sinnfein", "sinnfein", "dup", "uup"],
        "Foyle":                         ["sinnfein", "sinnfein", "sdlp", "sdlp", "dup"],
        "Lagan Valley":                  ["dup", "dup", "alliance", "alliance", "uup"],
        "Mid Ulster":                    ["sinnfein", "sinnfein", "sinnfein", "dup", "sdlp"],
        "Newry and Armagh":              ["sinnfein", "sinnfein", "sinnfein", "dup", "sdlp"],
        "North Antrim":                  ["dup", "sinnfein", "alliance", "uup", "tuv"],
        "North Down":                    ["alliance", "alliance", "dup", "uup", "independent"],
        "South Antrim":                  ["dup", "dup", "sinnfein", "alliance", "uup"],
        "South Down":                    ["sinnfein", "sinnfein", "dup", "alliance", "sdlp"],
        "Strangford":                    ["dup", "dup", "alliance", "alliance", "uup"],
        "Upper Bann":                    ["dup", "dup", "sinnfein", "alliance", "uup"],
        "West Tyrone":                   ["sinnfein", "sinnfein", "sinnfein", "dup", "sdlp"],
    },
}

# Pre-defined plurality party ties or standard colors
PLURALITY_PARTY = {
    1998: {
        "Belfast East": "dup", "Belfast North": "uup", "Belfast South": "uup", "Belfast West": "sinnfein",
        "East Antrim": "uup", "East Londonderry": "uup", "Fermanagh and South Tyrone": "uup", "Foyle": "sdlp",
        "Lagan Valley": "uup", "Mid Ulster": "sinnfein", "Newry and Armagh": "sdlp", "North Antrim": "dup",
        "North Down": "uup", "South Antrim": "uup", "South Down": "sdlp", "Strangford": "uup",
        "Upper Bann": "uup", "West Tyrone": "sinnfein"
    },
    2003: {
        "Belfast East": "dup", "Belfast North": "dup", "Belfast South": "sdlp", "Belfast West": "sinnfein",
        "East Antrim": "dup", "East Londonderry": "dup", "Fermanagh and South Tyrone": "sinnfein", "Foyle": "sdlp",
        "Lagan Valley": "dup", "Mid Ulster": "sinnfein", "Newry and Armagh": "sinnfein", "North Antrim": "dup",
        "North Down": "uup", "South Antrim": "dup", "South Down": "sinnfein", "Strangford": "dup",
        "Upper Bann": "dup", "West Tyrone": "sinnfein"
    },
    2007: {
        "Belfast East": "dup", "Belfast North": "dup", "Belfast South": "sdlp", "Belfast West": "sinnfein",
        "East Antrim": "dup", "East Londonderry": "dup", "Fermanagh and South Tyrone": "sinnfein", "Foyle": "sdlp",
        "Lagan Valley": "dup", "Mid Ulster": "sinnfein", "Newry and Armagh": "sinnfein", "North Antrim": "dup",
        "North Down": "uup", "South Antrim": "dup", "South Down": "sinnfein", "Strangford": "dup",
        "Upper Bann": "dup", "West Tyrone": "sinnfein"
    },
    2011: {
        "Belfast East": "dup", "Belfast North": "sinnfein", "Belfast South": "sdlp", "Belfast West": "sinnfein",
        "East Antrim": "dup", "East Londonderry": "dup", "Fermanagh and South Tyrone": "sinnfein", "Foyle": "sinnfein",
        "Lagan Valley": "dup", "Mid Ulster": "sinnfein", "Newry and Armagh": "sinnfein", "North Antrim": "dup",
        "North Down": "dup", "South Antrim": "dup", "South Down": "sinnfein", "Strangford": "dup",
        "Upper Bann": "dup", "West Tyrone": "sinnfein"
    },
    2016: {
        "Belfast East": "dup", "Belfast North": "sinnfein", "Belfast South": "sdlp", "Belfast West": "sinnfein",
        "East Antrim": "dup", "East Londonderry": "dup", "Fermanagh and South Tyrone": "sinnfein", "Foyle": "sinnfein",
        "Lagan Valley": "dup", "Mid Ulster": "sinnfein", "Newry and Armagh": "sinnfein", "North Antrim": "dup",
        "North Down": "alliance", "South Antrim": "dup", "South Down": "sinnfein", "Strangford": "dup",
        "Upper Bann": "dup", "West Tyrone": "sinnfein"
    },
    2017: {
        "Belfast East": "dup", "Belfast North": "sinnfein", "Belfast South": "sdlp", "Belfast West": "sinnfein",
        "East Antrim": "dup", "East Londonderry": "dup", "Fermanagh and South Tyrone": "sinnfein", "Foyle": "sinnfein",
        "Lagan Valley": "dup", "Mid Ulster": "sinnfein", "Newry and Armagh": "sinnfein", "North Antrim": "dup",
        "North Down": "alliance", "South Antrim": "dup", "South Down": "sinnfein", "Strangford": "dup",
        "Upper Bann": "uup", "West Tyrone": "sinnfein"
    },
    2022: {
        "Belfast East": "alliance", "Belfast North": "sinnfein", "Belfast South": "alliance", "Belfast West": "sinnfein",
        "East Antrim": "dup", "East Londonderry": "dup", "Fermanagh and South Tyrone": "sinnfein", "Foyle": "sinnfein",
        "Lagan Valley": "dup", "Mid Ulster": "sinnfein", "Newry and Armagh": "sinnfein", "North Antrim": "dup",
        "North Down": "alliance", "South Antrim": "dup", "South Down": "sinnfein", "Strangford": "dup",
        "Upper Bann": "uup", "West Tyrone": "sinnfein"
    }
}

def build_hexjson(year, results):
    hexes = {}
    for const_name, cell in GRID.items():
        # Map Belfast South and Mid Down to Belfast South for keys
        result_key = const_name
        if const_name == "Belfast South and Mid Down":
            result_key = "Belfast South"
        
        seats_list = results.get(result_key, [])
        if not seats_list and result_key == "Belfast South":
            seats_list = results.get("Belfast South and Mid Down", [])
        
        # Calculate plurality party
        plurality = PLURALITY_PARTY.get(year, {}).get(result_key, "others")
        
        # Backwards compatible seat count for plurality
        pl_seats = seats_list.count(plurality) if seats_list else 0

        hexes[const_name] = {
            "q": cell["q"],
            "r": cell["r"],
            "n": const_name,
            "party": plurality,
            "seats": pl_seats,
            "seats_list": seats_list
        }

    return {
        "layout": "odd-r",
        "hexes": hexes,
    }

# Build and write one hexjson per election year
os.makedirs("data/hex/stormont", exist_ok=True)

for year, results_dict in RESULTS.items():
    hexjson = build_hexjson(year, results_dict)
    out_path = f"data/hex/stormont/{year}.hexjson"
    with open(out_path, "w") as f:
        json.dump(hexjson, f, indent=2)
    print(f"Written {out_path} ({len(hexjson['hexes'])} constituencies)")

print("\nDone.")
