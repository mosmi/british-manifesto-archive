#!/usr/bin/env python3
"""Write data/devolved/senedd/*.json election files.

Seat and vote figures sourced from House of Commons Library research briefings
in each Wales election folder (RP99-51 through CBP-9282). 2026 from BBC results.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "devolved" / "senedd"
ASSETS = json.loads((ROOT / "scripts" / "senedd-assets.json").read_text())

MANIFESTO_TITLES = {
    "1999": {
        "welshlab": "Welsh Labour Manifesto 1999",
        "plaid": "Plaid Cymru Manifesto 1999",
    },
    "2003": {
        "welshlab": "Welsh Labour Manifesto 2003",
        "welshcon": "Welsh Conservative Manifesto 2003",
        "welshlibdem": "Welsh Liberal Democrats Manifesto 2003",
        "plaid": "Plaid Cymru Manifesto 2003",
    },
    "2007": {
        "welshlab": "Welsh Labour Manifesto 2007",
        "welshcon": "Welsh Conservative Manifesto 2007",
        "welshlibdem": "Welsh Liberal Democrats Manifesto 2007",
        "plaid": "Plaid Cymru Manifesto 2007",
        "ukip": "UKIP Wales Manifesto 2007",
    },
    "2011": {
        "welshlab": "Welsh Labour Manifesto 2011",
        "welshcon": "Welsh Conservative Manifesto 2011",
        "welshlibdem": "Welsh Liberal Democrats Manifesto 2011",
        "plaid": "Plaid Cymru Manifesto 2011",
        "walesgrn": "Wales Green Party Manifesto 2011",
        "ukip": "UKIP Wales Manifesto 2011",
        "cooperative": "Welsh Co-operative Party Manifesto 2011",
    },
    "2016": {
        "welshlab": "Welsh Labour Manifesto 2016",
        "welshcon": "Welsh Conservatives Manifesto 2016",
        "welshlibdem": "Welsh Liberal Democrats Manifesto 2016",
        "plaid": "Plaid Cymru Manifesto 2016",
        "walesgrn": "Wales Green Party Manifesto 2016",
        "ukip": "UKIP Wales Manifesto 2016",
        "cooperative": "Welsh Co-operative Party Manifesto 2016",
    },
    "2021": {
        "welshlab": "Welsh Labour Manifesto 2021",
        "welshcon": "Welsh Conservative Manifesto 2021",
        "welshlibdem": "Welsh Liberal Democrats Manifesto 2021",
        "plaid": "Plaid Cymru Manifesto 2021",
        "walesgrn": "Wales Green Party Manifesto 2021",
        "reform": "Reform UK Wales Manifesto 2021",
        "ukip": "UKIP Wales Manifesto 2021",
        "gwlad": "Gwlad Manifesto 2021",
        "propel": "Propel Manifesto 2021",
        "abolish": "Abolish the Welsh Assembly Party Manifesto 2021",
        "communist": "Welsh Communist Party Manifesto 2021",
        "tusc": "Welsh TUSC Manifesto 2021",
        "cooperative": "Welsh Co-operative Party Manifesto 2021",
    },
    "2026": {
        "plaid": "Plaid Cymru Manifesto 2026",
        "reform": "Reform UK Wales Manifesto 2026",
        "welshlab": "Welsh Labour Manifesto 2026",
        "welshcon": "Welsh Conservatives Manifesto 2026",
        "walesgrn": "Wales Green Party Manifesto 2026",
        "welshlibdem": "Welsh Liberal Democrats Manifesto 2026",
        "gwlad": "Gwlad Manifesto 2026",
        "propel": "Propel Manifesto 2026",
        "heritage": "Heritage Party Wales Manifesto 2026",
        "communist": "Communist Party of Britain Manifesto 2026",
        "tusc": "Welsh TUSC Manifesto 2026",
        "cooperative": "Welsh Co-operative Party Manifesto 2026",
    },
}

ELECTIONS = [
    {
        "id": "1999", "year": 1999, "displayYear": "1999", "date": "6 May 1999",
        "title": "1999 National Assembly for Wales election",
        "turnout": 46.0, "control": "welshlab", "firstMinister": "Alun Michael",
        "majority": False,
        "summary": "Wales's first devolved election established a Labour-led administration. Labour won 28 of 60 seats — three short of a majority — and formed a coalition with the Liberal Democrats. Plaid Cymru became the principal opposition with 17 seats. The Conservatives won all nine of their seats through the regional lists, having failed to win a single constituency.",
        "highlights": [
            "First elections to the National Assembly for Wales since the 1997 referendum",
            "Labour wins 28 seats; coalition government with Liberal Democrats",
            "Plaid Cymru second largest party with 17 AMs",
            "Conservatives win nine regional list seats without a constituency victory",
            "Turnout approximately 46% on both ballots",
        ],
        "parliament": {
            "results": [
                {"party": "welshlab", "constituencySeats": 27, "listSeats": 1, "seats": 28, "constituencyPct": 37.6, "listPct": 35.4},
                {"party": "plaid", "constituencySeats": 9, "listSeats": 8, "seats": 17, "constituencyPct": 28.4, "listPct": 30.5},
                {"party": "welshcon", "constituencySeats": 1, "listSeats": 8, "seats": 9, "constituencyPct": 15.8, "listPct": 16.5},
                {"party": "welshlibdem", "constituencySeats": 3, "listSeats": 3, "seats": 6, "constituencyPct": 13.5, "listPct": 12.5},
            ],
        },
        "sources": [
            {"label": "House of Commons Library — 1999 Welsh Assembly election (RP99-51)", "url": "https://commonslibrary.parliament.uk/research-briefings/rp99-51/"},
        ],
    },
    {
        "id": "2003", "year": 2003, "displayYear": "2003", "date": "1 May 2003",
        "title": "2003 National Assembly for Wales election",
        "turnout": 38.2, "control": "welshlab", "firstMinister": "Rhodri Morgan",
        "majority": False,
        "summary": "Labour remained the largest party with 30 seats, up two from 1999, and Rhodri Morgan continued as First Minister in coalition with the Liberal Democrats. Plaid Cymru fell sharply to 12 seats. Turnout dropped to 38.2% — down eight points — the lowest in any Senedd election until 2026.",
        "highlights": [
            "Labour increases to 30 seats under Rhodri Morgan",
            "Plaid Cymru loses five seats, falling to 12 AMs",
            "Conservatives gain two seats to 11",
            "Half of all AMs elected are women — 30 of 60",
            "Turnout falls to 38.2%",
        ],
        "parliament": {
            "results": [
                {"party": "welshlab", "constituencySeats": 30, "listSeats": 0, "seats": 30, "constituencyPct": 40.0, "listPct": 36.6},
                {"party": "welshcon", "constituencySeats": 1, "listSeats": 10, "seats": 11, "constituencyPct": 19.9, "listPct": 19.2},
                {"party": "welshlibdem", "constituencySeats": 3, "listSeats": 3, "seats": 6, "constituencyPct": 14.1, "listPct": 12.7},
                {"party": "plaid", "constituencySeats": 5, "listSeats": 7, "seats": 12, "constituencyPct": 21.2, "listPct": 19.7},
                {"partyLabel": "Others", "constituencySeats": 1, "listSeats": 0, "seats": 1},
            ],
            "otherListVotes": [
                {"name": "UK Independence Party", "pct": 2.9},
            ],
        },
        "sources": [
            {"label": "House of Commons Library — 2003 Welsh Assembly election (RP03-45)", "url": "https://commonslibrary.parliament.uk/research-briefings/rp03-45/"},
        ],
    },
    {
        "id": "2007", "year": 2007, "displayYear": "2007", "date": "3 May 2007",
        "title": "2007 National Assembly for Wales election",
        "turnout": 43.5, "control": "welshlab", "firstMinister": "Rhodri Morgan",
        "majority": False,
        "summary": "Labour remained the largest party with 26 seats but fell four short of 2003. After weeks of negotiation, Rhodri Morgan formed a coalition with Plaid Cymru — the One Wales agreement. The Conservatives gained a seat to 12; Plaid Cymru rose to 15.",
        "highlights": [
            "Labour wins 26 seats — down four from 2003",
            "Labour–Plaid Cymru coalition formed under the One Wales agreement",
            "Plaid Cymru gains three seats to 15",
            "Mohammad Asghar becomes first minority ethnic AM (Plaid Cymru, regional list)",
            "Turnout rises to 43.5%",
        ],
        "parliament": {
            "results": [
                {"party": "welshlab", "constituencySeats": 24, "listSeats": 2, "seats": 26, "constituencyPct": 32.2, "listPct": 29.6},
                {"party": "plaid", "constituencySeats": 7, "listSeats": 8, "seats": 15, "constituencyPct": 22.4, "listPct": 21.0},
                {"party": "welshcon", "constituencySeats": 5, "listSeats": 7, "seats": 12, "constituencyPct": 22.4, "listPct": 21.5},
                {"party": "welshlibdem", "constituencySeats": 3, "listSeats": 3, "seats": 6, "constituencyPct": 14.8, "listPct": 11.7},
                {"partyLabel": "Others", "constituencySeats": 1, "listSeats": 0, "seats": 1},
            ],
        },
        "sources": [
            {"label": "House of Commons Library — 2007 Welsh Assembly election (RP07-45)", "url": "https://commonslibrary.parliament.uk/research-briefings/rp07-45/"},
        ],
        "supplementaryDocuments": [
            {
                "title": "One Wales agreement",
                "pdf": "/documents/supplementary/senedd/2007/one-wales-agreement.pdf",
            },
        ],
    },
    {
        "id": "2011", "year": 2011, "displayYear": "2011", "date": "5 May 2011",
        "title": "2011 National Assembly for Wales election",
        "turnout": 41.4, "control": "welshlab", "firstMinister": "Carwyn Jones",
        "majority": False,
        "summary": "Labour won exactly half the Assembly — 30 of 60 seats — its best Senedd performance by vote share (39.6%). Carwyn Jones continued as First Minister in minority government. The Conservatives recorded their best result to date with 14 seats; Plaid Cymru fell to 11.",
        "highlights": [
            "Labour wins 30 seats — half the Assembly",
            "Best Labour and Conservative performances in any Senedd election",
            "Worst Plaid Cymru and Liberal Democrat performances to date",
            "Carwyn Jones continues as First Minister",
            "Turnout 41.4%",
        ],
        "parliament": {
            "results": [
                {"party": "welshlab", "constituencySeats": 28, "listSeats": 2, "seats": 30, "constituencyPct": 42.3, "listPct": 36.9},
                {"party": "welshcon", "constituencySeats": 6, "listSeats": 8, "seats": 14, "constituencyPct": 25.0, "listPct": 22.5},
                {"party": "plaid", "constituencySeats": 5, "listSeats": 6, "seats": 11, "constituencyPct": 19.3, "listPct": 17.9},
                {"party": "welshlibdem", "constituencySeats": 1, "listSeats": 4, "seats": 5, "constituencyPct": 10.6, "listPct": 8.0},
            ],
        },
        "sources": [
            {"label": "House of Commons Library — 2011 Welsh Assembly election (RP11-40)", "url": "https://commonslibrary.parliament.uk/research-briefings/rp11-40/"},
        ],
    },
    {
        "id": "2016", "year": 2016, "displayYear": "2016", "date": "5 May 2016",
        "title": "2016 National Assembly for Wales election",
        "turnout": 45.4, "control": "welshlab", "firstMinister": "Carwyn Jones",
        "majority": False,
        "summary": "Labour remained the largest party with 29 seats but fell one short of a majority. UKIP entered the Assembly for the first time with seven regional AMs. Plaid Cymru overtook the Conservatives as the second-largest party. The Liberal Democrats collapsed from five seats to one.",
        "highlights": [
            "Labour wins 29 seats — one short of a majority",
            "UKIP wins seven regional seats on its first Senedd contest",
            "Plaid Cymru becomes second-largest party with 12 seats",
            "Liberal Democrats fall from five seats to one",
            "Turnout rises to 45.4%",
        ],
        "parliament": {
            "results": [
                {"party": "welshlab", "constituencySeats": 27, "listSeats": 2, "seats": 29, "constituencyPct": 34.7, "listPct": 31.5},
                {"party": "plaid", "constituencySeats": 6, "listSeats": 6, "seats": 12, "constituencyPct": 20.5, "listPct": 20.8},
                {"party": "welshcon", "constituencySeats": 6, "listSeats": 5, "seats": 11, "constituencyPct": 21.1, "listPct": 18.8},
                {"party": "ukip", "constituencySeats": 0, "listSeats": 7, "seats": 7, "listPct": 12.7},
                {"party": "welshlibdem", "constituencySeats": 1, "listSeats": 0, "seats": 1, "constituencyPct": 7.1, "listPct": 7.1},
            ],
            "otherListVotes": [
                {"name": "Wales Green Party", "pct": 2.7},
            ],
        },
        "sources": [
            {"label": "House of Commons Library — 2016 Welsh Assembly election (CBP-7594)", "url": "https://commonslibrary.parliament.uk/research-briefings/cbp-7594/"},
        ],
    },
    {
        "id": "2021", "year": 2021, "displayYear": "2021", "date": "6 May 2021",
        "title": "2021 Senedd Cymru election",
        "turnout": 46.5, "control": "welshlab", "firstMinister": "Mark Drakeford",
        "majority": False,
        "summary": "Labour won 30 seats again with 38.0% of the combined vote and Mark Drakeford continued as First Minister. The Conservatives became the second-largest party with 16 seats, overtaking Plaid Cymru. UKIP lost all seven seats won in 2016. The Senedd was formally renamed Senedd Cymru / Welsh Parliament in 2020.",
        "highlights": [
            "Labour wins 30 seats under Mark Drakeford",
            "Conservatives second largest with 16 seats — best Tory Senedd result",
            "UKIP loses all seven seats won in 2016",
            "Plaid Cymru holds 13 seats despite slight vote share fall",
            "Turnout 46.5% — highest since 1999 bar 2016",
        ],
        "parliament": {
            "results": [
                {"party": "welshlab", "constituencySeats": 27, "listSeats": 3, "seats": 30, "constituencyPct": 39.9, "listPct": 36.2},
                {"party": "welshcon", "constituencySeats": 8, "listSeats": 8, "seats": 16, "constituencyPct": 26.1, "listPct": 25.1},
                {"party": "plaid", "constituencySeats": 5, "listSeats": 8, "seats": 13, "constituencyPct": 20.3, "listPct": 20.7},
                {"party": "welshlibdem", "constituencySeats": 0, "listSeats": 1, "seats": 1, "listPct": 4.6},
            ],
            "otherListVotes": [
                {"name": "Wales Green Party", "pct": 3.0},
                {"name": "Abolish the Welsh Assembly Party", "pct": 1.6},
                {"name": "Reform UK", "pct": 1.6},
            ],
        },
        "sources": [
            {"label": "House of Commons Library — 2021 Senedd election (CBP-9282)", "url": "https://commonslibrary.parliament.uk/research-briefings/cbp-9282/"},
        ],
    },
    {
        "id": "2026", "year": 2026, "displayYear": "2026", "date": "7 May 2026",
        "title": "2026 Senedd Cymru election",
        "turnout": 51.6, "control": "plaid", "firstMinister": None,
        "majority": False,
        "summary": "The 2026 election was the first under a reformed Senedd of 96 members elected by closed-list proportional representation across 16 six-member constituencies. Plaid Cymru became the largest party for the first time with 43 seats, ending Labour's quarter-century as the leading party. Reform UK entered the Senedd with 34 seats on its first contest. Labour collapsed from 30 to nine seats.",
        "highlights": [
            "First election under closed-list PR with 96 Members",
            "Plaid Cymru largest party for the first time — 43 seats",
            "Reform UK wins 34 seats on its first Senedd contest",
            "Labour falls from 30 to nine seats",
            "Turnout 51.6% — highest since devolution",
        ],
        "parliament": {
            "system": "Closed list proportional representation",
            "totalSeats": 96,
            "majorityThreshold": 49,
            "results": [
                {"party": "plaid", "seats": 43, "votes": 444665, "pct": 35.4},
                {"party": "reform", "seats": 34, "votes": 367985, "pct": 29.3},
                {"party": "welshlab", "seats": 9, "votes": 139203, "pct": 11.1},
                {"party": "welshcon", "seats": 7, "votes": 134926, "pct": 10.7},
                {"party": "walesgrn", "seats": 2, "votes": 84608, "pct": 6.7},
                {"party": "welshlibdem", "seats": 1, "votes": 56012, "pct": 4.5},
            ],
            "otherListVotes": [
                {"name": "Independent", "votes": 14063, "pct": 1.1},
                {"name": "Heritage Party", "votes": 5474, "pct": 0.4},
                {"name": "Propel", "votes": 4032, "pct": 0.3},
                {"name": "Gwlad", "votes": 2479, "pct": 0.2},
            ],
        },
        "sources": [
            {"label": "BBC News — Wales election results 2026", "url": "https://www.bbc.com/news/election/2026/wales/results"},
        ],
    },
]


def manifesto_entries(eid: str) -> list[dict]:
    entry = next(e for e in ASSETS if e["id"] == eid)
    titles = MANIFESTO_TITLES.get(eid, {})
    out = []
    for m in entry["manifestos"]:
        party = m["party"]
        row = {
            "title": titles.get(party, party.replace("-", " ").title()),
            "pdf": f"/manifestos/senedd/{eid}/{party}/manifesto.pdf",
            "cover": f"/manifestos/senedd/{eid}/{party}/cover.png",
            "party": party,
        }
        out.append(row)
    return out


def enrich_parliament(p: dict, year: int) -> dict:
    if p.get("system") == "Closed list proportional representation":
        return dict(p)
    base = {
        "totalSeats": 60,
        "constituencySeats": 40,
        "listSeats": 20,
        "majorityThreshold": 31,
        "system": "Additional Member System",
    }
    base.update(p)
    return base


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    index = []
    for e in ELECTIONS:
        doc = dict(e)
        doc["body"] = "senedd"
        doc["parliament"] = enrich_parliament(doc["parliament"], e["year"])
        doc["manifestos"] = manifesto_entries(e["id"])
        (OUT / f"{e['id']}.json").write_text(
            json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        index.append({
            "id": e["id"],
            "body": "senedd",
            "year": e["year"],
            "displayYear": e["displayYear"],
            "date": e["date"],
            "title": "Senedd Cymru election",
            "control": e["control"],
            "winnerName": e.get("firstMinister") or "",
            "firstMinister": e.get("firstMinister"),
        })
    (OUT / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {len(ELECTIONS)} elections to {OUT}")


if __name__ == "__main__":
    main()
