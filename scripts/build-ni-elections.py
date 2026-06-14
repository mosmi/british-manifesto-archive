#!/usr/bin/env python3
"""Write data/devolved/stormont/*.json election files.

Seat and vote figures sourced from House of Commons Library research briefings
in each Northern Ireland election folder (RP98-76 through CBP-9549).
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "devolved" / "stormont"
ASSETS = json.loads((ROOT / "scripts" / "ni-assets.json").read_text())

MANIFESTO_TITLES = {
    "1998": {
        "alliance": "Alliance Party 1998 Manifesto",
        "nicon": "Northern Ireland Conservatives 1998 Manifesto",
        "dup": "Democratic Unionist Party 1998 Manifesto",
        "niwc": "Northern Ireland Women's Coalition 1998 Manifesto",
        "sdlp": "Social Democratic and Labour Party 1998 Manifesto",
        "sinnfein": "Sinn Féin 1998 Manifesto",
        "uup": "Ulster Unionist Party 1998 Manifesto",
        "workerspartyie": "Workers' Party 1998 Manifesto"
    },
    "2003": {
        "alliance": "Alliance Party 2003 Manifesto",
        "nicon": "Northern Ireland Conservatives 2003 Manifesto",
        "dup": "Democratic Unionist Party 2003 Manifesto",
        "gpni": "Green Party NI 2003 Manifesto",
        "niwc": "Northern Ireland Women's Coalition 2003 Manifesto",
        "pup": "Progressive Unionist Party 2003 Manifesto",
        "sdlp": "Social Democratic and Labour Party 2003 Manifesto",
        "sinnfein": "Sinn Féin 2003 Manifesto",
        "uup": "Ulster Unionist Party 2003 Manifesto",
        "workerspartyie": "Workers' Party 2003 Manifesto",
        "sea": "Socialist Environmental Alliance 2003 Manifesto"
    },
    "2007": {
        "alliance": "Alliance Party 2007 Manifesto",
        "nicon": "Northern Ireland Conservatives 2007 Manifesto",
        "dup": "Democratic Unionist Party 2007 Manifesto",
        "gpni": "Green Party NI 2007 Manifesto",
        "pup": "Progressive Unionist Party 2007 Manifesto",
        "sdlp": "Social Democratic and Labour Party 2007 Manifesto",
        "sinnfein": "Sinn Féin 2007 Manifesto",
        "uup": "Ulster Unionist Party 2007 Manifesto",
        "ukup": "UK Unionist Party 2007 Manifesto",
        "workerspartyie": "Workers' Party 2007 Manifesto",
        "rsf": "Republican Sinn Féin 2007 Manifesto",
        "sea": "Socialist Environmental Alliance 2007 Manifesto"
    },
    "2011": {
        "alliance": "Alliance Party 2011 Manifesto",
        "dup": "Democratic Unionist Party 2011 Manifesto",
        "gpni": "Green Party NI 2011 Manifesto",
        "pup": "Progressive Unionist Party 2011 Manifesto",
        "sdlp": "Social Democratic and Labour Party 2011 Manifesto",
        "sinnfein": "Sinn Féin 2011 Manifesto",
        "uup": "Ulster Unionist Party 2011 Manifesto",
        "tuv": "Traditional Unionist Voice 2011 Manifesto",
        "workerspartyie": "Workers' Party 2011 Manifesto"
    },
    "2016": {
        "alliance": "Alliance Party 2016 Manifesto",
        "dup": "Democratic Unionist Party 2016 Manifesto",
        "gpni": "Green Party NI 2016 Manifesto",
        "pup": "Progressive Unionist Party 2016 Manifesto",
        "sdlp": "Social Democratic and Labour Party 2016 Manifesto",
        "sinnfein": "Sinn Féin 2016 Manifesto",
        "uup": "Ulster Unionist Party 2016 Manifesto",
        "tuv": "Traditional Unionist Voice 2016 Manifesto",
        "workerspartyie": "Workers' Party 2016 Manifesto",
        "ukip": "UKIP Northern Ireland 2016 Manifesto",
        "nicon": "Northern Ireland Conservatives 2016 Manifesto"
    },
    "2017": {
        "alliance": "Alliance Party 2017 Manifesto",
        "dup": "Democratic Unionist Party 2017 Manifesto",
        "gpni": "Green Party NI 2017 Manifesto",
        "sdlp": "Social Democratic and Labour Party 2017 Manifesto",
        "sinnfein": "Sinn Féin 2017 Manifesto",
        "uup": "Ulster Unionist Party 2017 Manifesto",
        "tuv": "Traditional Unionist Voice 2017 Manifesto",
        "workerspartyie": "Workers' Party 2017 Manifesto",
        "pbp": "People Before Profit 2017 Manifesto",
        "nicon": "Northern Ireland Conservatives 2017 Manifesto"
    },
    "2022": {
        "alliance": "Alliance Party 2022 Manifesto",
        "dup": "Democratic Unionist Party 2022 Manifesto",
        "gpni": "Green Party NI 2022 Manifesto",
        "sdlp": "Social Democratic and Labour Party 2022 Manifesto",
        "sinnfein": "Sinn Féin 2022 Manifesto",
        "uup": "Ulster Unionist Party 2022 Manifesto",
        "tuv": "Traditional Unionist Voice 2022 Manifesto",
        "workerspartyie": "Workers' Party 2022 Manifesto",
        "pbp": "People Before Profit 2022 Manifesto"
    }
}

ELECTIONS = [
    {
        "id": "1998", "year": 1998, "displayYear": "1998", "date": "25 June 1998",
        "title": "1998 Northern Ireland Assembly election",
        "turnout": 69.9, "control": "uup", "firstMinister": "David Trimble",
        "deputyFirstMinister": "Seamus Mallon", "majority": False,
        "summary": "Following the historic signing of the Good Friday Agreement in April 1998 and its subsequent endorsement in a referendum, the 1998 election established the first devolved Northern Ireland Assembly. The Ulster Unionist Party (UUP) emerged as the largest party with 28 seats, closely followed by the Social Democratic and Labour Party (SDLP) with 24. A power-sharing Executive was formed with David Trimble (UUP) as First Minister and Seamus Mallon (SDLP) as deputy First Minister. Hardline unionists opposing the agreement, led by the DUP, won a combined total of 28 seats.",
        "highlights": [
            "First elections to the new Northern Ireland Assembly established under the Good Friday Agreement",
            "UUP wins 28 seats; David Trimble elected First Minister",
            "SDLP is the largest nationalist party with 24 seats; Seamus Mallon becomes deputy First Minister",
            "Anti-Agreement unionists win 28 seats, setting up ongoing constitutional tension",
            "Northern Ireland Women's Coalition wins two seats, representing grassroots cross-community voices"
        ],
        "parliament": {
            "system": "Single Transferable Vote",
            "totalSeats": 108,
            "majorityThreshold": 55,
            "results": [
                {"party": "uup", "seats": 28, "pct": 21.3},
                {"party": "sdlp", "seats": 24, "pct": 22.0},
                {"party": "dup", "seats": 20, "pct": 18.1},
                {"party": "sinnfein", "seats": 18, "pct": 17.7},
                {"party": "alliance", "seats": 6, "pct": 6.5},
                {"party": "ukup", "seats": 5, "pct": 4.5},
                {"party": "pup", "seats": 2, "pct": 2.5},
                {"party": "niwc", "seats": 2, "pct": 1.6},
                {"partyLabel": "Independent Unionist", "seats": 3, "pct": 2.8}
            ]
        },
        "sources": [
            {"label": "House of Commons Library — Northern Ireland Assembly Elections: 25 June 1998 (RP98-76)", "url": "https://commonslibrary.parliament.uk/research-briefings/rp98-76/"}
        ]
    },
    {
        "id": "2003", "year": 2003, "displayYear": "2003", "date": "26 November 2003",
        "title": "2003 Northern Ireland Assembly election",
        "turnout": 64.0, "control": "dup", "firstMinister": "Ian Paisley",
        "deputyFirstMinister": "Martin McGuinness", "majority": False,
        "summary": "The 2003 election took place during a period of suspension of the devolved institutions, which had been reinstated under direct rule in October 2002. The DUP overtook the UUP to become the largest unionist party, winning 30 seats to the UUP's 27. Similarly, Sinn Féin overtook the SDLP as the largest nationalist party, winning 24 seats to the SDLP's 18. Because of the deadlock between the DUP (who refused to share power with Sinn Féin without a decommissioning of IRA weapons) and Sinn Féin, the Executive was not restored, and direct rule continued.",
        "highlights": [
            "DUP becomes the largest unionist party with 30 seats, overtaking the UUP",
            "Sinn Féin becomes the largest nationalist party with 24 seats, overtaking the SDLP",
            "Devolved institutions remain suspended; direct rule from London continues",
            "Alliance Party holds 6 seats",
            "Robert McCartney (UKUP) and David Ervine (PUP) hold individual seats"
        ],
        "parliament": {
            "system": "Single Transferable Vote",
            "totalSeats": 108,
            "majorityThreshold": 55,
            "results": [
                {"party": "dup", "seats": 30, "pct": 25.7},
                {"party": "uup", "seats": 27, "pct": 22.7},
                {"party": "sinnfein", "seats": 24, "pct": 23.5},
                {"party": "sdlp", "seats": 18, "pct": 17.0},
                {"party": "alliance", "seats": 6, "pct": 3.7},
                {"party": "pup", "seats": 1, "pct": 1.2},
                {"party": "ukup", "seats": 1, "pct": 0.8},
                {"partyLabel": "Independent", "seats": 1, "pct": 0.8}
            ],
            "otherListVotes": [
                {"name": "Green Party NI", "pct": 0.4},
                {"name": "Socialist Environmental Alliance", "pct": 0.4},
                {"name": "Workers' Party", "pct": 0.2}
            ]
        },
        "sources": [
            {"label": "House of Commons Library — Northern Ireland Assembly Elections (RP03-21)", "url": "https://commonslibrary.parliament.uk/research-briefings/rp03-21/"}
        ]
    },
    {
        "id": "2007", "year": 2007, "displayYear": "2007", "date": "7 March 2007",
        "title": "2007 Northern Ireland Assembly election",
        "turnout": 62.3, "control": "dup", "firstMinister": "Ian Paisley",
        "deputyFirstMinister": "Martin McGuinness", "majority": False,
        "summary": "Following the St Andrews Agreement in 2006, the DUP and Sinn Féin agreed to enter power-sharing. The election confirmed their positions as the leading unionist and nationalist parties respectively. The DUP grew to 36 seats and Sinn Féin to 28. In May 2007, a historic Executive was formed with Ian Paisley (DUP) as First Minister and Martin McGuinness (Sinn Féin) as deputy First Minister, ushering in a decade of relative political stability under their joint leadership.",
        "highlights": [
            "Devolution restored following the St Andrews Agreement and IRA decommissioning",
            "DUP and Sinn Féin consolidate their positions as the dominant parties",
            "Historic power-sharing Executive formed by Ian Paisley and Martin McGuinness",
            "Green Party NI wins its first Assembly seat (Brian Wilson in North Down)",
            "Alliance Party increases its share, winning 7 seats"
        ],
        "parliament": {
            "system": "Single Transferable Vote",
            "totalSeats": 108,
            "majorityThreshold": 55,
            "results": [
                {"party": "dup", "seats": 36, "pct": 30.1},
                {"party": "sinnfein", "seats": 28, "pct": 26.2},
                {"party": "uup", "seats": 18, "pct": 14.9},
                {"party": "sdlp", "seats": 16, "pct": 15.2},
                {"party": "alliance", "seats": 7, "pct": 5.2},
                {"party": "gpni", "seats": 1, "pct": 1.7},
                {"party": "pup", "seats": 1, "pct": 0.6},
                {"partyLabel": "Independent", "seats": 1, "pct": 0.8}
            ],
            "otherListVotes": [
                {"name": "UK Unionist Party", "pct": 1.5},
                {"name": "Socialist Environmental Alliance", "pct": 0.3},
                {"name": "Workers' Party", "pct": 0.1}
            ]
        },
        "sources": [
            {"label": "House of Commons Library — 2007 Northern Ireland Assembly election results (RP07-32)", "url": "https://commonslibrary.parliament.uk/research-briefings/rp07-32/"}
        ]
    },
    {
        "id": "2011", "year": 2011, "displayYear": "2011", "date": "5 May 2011",
        "title": "2011 Northern Ireland Assembly election",
        "turnout": 54.7, "control": "dup", "firstMinister": "Peter Robinson",
        "deputyFirstMinister": "Martin McGuinness", "majority": False,
        "summary": "The 2011 election saw the DUP and Sinn Féin remain firmly in control, winning 38 and 29 seats respectively. Peter Robinson (DUP), who had succeeded Paisley as DUP leader and First Minister, continued in office alongside Martin McGuinness. The Alliance Party grew to 8 seats, including a constituency win in East Belfast. Traditional Unionist Voice (TUV), founded in opposition to power-sharing with Sinn Féin, won its first seat via leader Jim Allister in North Antrim.",
        "highlights": [
            "First Assembly to complete a full term without suspension since 1998",
            "DUP holds 38 seats, Sinn Féin holds 29 seats",
            "Peter Robinson and Martin McGuinness continue as joint heads of the Executive",
            "Alliance Party rises to 8 seats",
            "TUV enters the Assembly for the first time with Jim Allister"
        ],
        "parliament": {
            "system": "Single Transferable Vote",
            "totalSeats": 108,
            "majorityThreshold": 55,
            "results": [
                {"party": "dup", "seats": 38, "pct": 30.0},
                {"party": "sinnfein", "seats": 29, "pct": 26.9},
                {"party": "uup", "seats": 16, "pct": 13.2},
                {"party": "sdlp", "seats": 14, "pct": 14.2},
                {"party": "alliance", "seats": 8, "pct": 7.7},
                {"party": "tuv", "seats": 1, "pct": 2.5},
                {"party": "gpni", "seats": 1, "pct": 0.9},
                {"partyLabel": "Independent Unionist", "seats": 1, "pct": 0.7}
            ],
            "otherListVotes": [
                {"name": "Workers' Party", "pct": 0.4},
                {"name": "Progressive Unionist Party", "pct": 0.2}
            ]
        },
        "sources": [
            {"label": "House of Commons Library — Northern Ireland Assembly Election 2011 (RP11-42)", "url": "https://commonslibrary.parliament.uk/research-briefings/rp11-42/"}
        ]
    },
    {
        "id": "2016", "year": 2016, "displayYear": "2016", "date": "5 May 2016",
        "title": "2016 Northern Ireland Assembly election",
        "turnout": 54.9, "control": "dup", "firstMinister": "Arlene Foster",
        "deputyFirstMinister": "Martin McGuinness", "majority": False,
        "summary": "Arlene Foster led the DUP into her first election as leader, retaining 38 seats. Sinn Féin won 28 seats. Following the election, Foster became First Minister alongside Martin McGuinness. The election saw People Before Profit (PBP) win two seats in Belfast West and Foyle, while the Green Party increased its representation to two seats. This was the final election before the size of the Assembly was reduced to 90 members.",
        "highlights": [
            "Arlene Foster leads DUP to 38 seats in her first election as leader",
            "People Before Profit wins two seats on a radical left-wing platform",
            "Green Party NI doubles its seats to two",
            "UUP and SDLP decide to exit the Executive to form the official Opposition",
            "Turnout remains steady at 54.9%"
        ],
        "parliament": {
            "system": "Single Transferable Vote",
            "totalSeats": 108,
            "majorityThreshold": 55,
            "results": [
                {"party": "dup", "seats": 38, "pct": 29.2},
                {"party": "sinnfein", "seats": 28, "pct": 24.0},
                {"party": "uup", "seats": 16, "pct": 12.6},
                {"party": "sdlp", "seats": 12, "pct": 12.0},
                {"party": "alliance", "seats": 8, "pct": 7.0},
                {"party": "gpni", "seats": 2, "pct": 2.7},
                {"party": "pbp", "seats": 2, "pct": 2.0},
                {"party": "tuv", "seats": 1, "pct": 3.4},
                {"partyLabel": "Independent", "seats": 1, "pct": 2.2}
            ],
            "otherListVotes": [
                {"name": "UK Independence Party", "pct": 1.5},
                {"name": "Conservatives", "pct": 0.4},
                {"name": "Workers' Party", "pct": 0.2},
                {"name": "Progressive Unionist Party", "pct": 0.9}
            ]
        },
        "sources": [
            {"label": "House of Commons Library — Northern Ireland Assembly Election 2016 (CBP-7575)", "url": "https://commonslibrary.parliament.uk/research-briefings/cbp-7575/"}
        ]
    },
    {
        "id": "2017", "year": 2017, "displayYear": "2017", "date": "2 March 2017",
        "title": "2017 Northern Ireland Assembly election",
        "turnout": 64.8, "control": "dup", "firstMinister": "Arlene Foster",
        "deputyFirstMinister": "Michelle O'Neill", "majority": False,
        "summary": "Triggered by the resignation of Martin McGuinness in protest over the RHI ('cash for ash') scandal, the 2017 snap election was fought under a reduced Assembly size of 90 seats. The election was highly polarized, resulting in a dramatic rise in turnout to 64.8%. Sinn Féin, led for the first time by Michelle O'Neill, surged to 27 seats, finishing just one seat and 0.2% behind the DUP (28 seats). Unionist parties lost their collective overall majority in the Stormont Assembly for the first time since partition. Following the election, power-sharing remained collapsed for three years until the New Decade, New Approach agreement in January 2020.",
        "highlights": [
            "Snap election triggered by the collapse of the power-sharing Executive over RHI scandal",
            "Assembly size reduced from 108 to 90 members",
            "Sinn Féin finishes just one seat behind DUP, winning 27 seats",
            "Unionism loses its overall legislative majority in Northern Ireland for the first time",
            "Institutions remain suspended for three years post-election"
        ],
        "parliament": {
            "system": "Single Transferable Vote",
            "totalSeats": 90,
            "majorityThreshold": 46,
            "results": [
                {"party": "dup", "seats": 28, "pct": 28.1},
                {"party": "sinnfein", "seats": 27, "pct": 27.9},
                {"party": "sdlp", "seats": 12, "pct": 11.9},
                {"party": "uup", "seats": 10, "pct": 12.9},
                {"party": "alliance", "seats": 8, "pct": 9.1},
                {"party": "gpni", "seats": 2, "pct": 2.3},
                {"party": "tuv", "seats": 1, "pct": 2.6},
                {"party": "pbp", "seats": 1, "pct": 1.8},
                {"partyLabel": "Independent", "seats": 1, "pct": 2.2}
            ],
            "otherListVotes": [
                {"name": "Conservatives", "pct": 0.3},
                {"name": "Workers' Party", "pct": 0.2}
            ]
        },
        "sources": [
            {"label": "House of Commons Library — Northern Ireland Assembly Election 2017 (CBP-7920)", "url": "https://commonslibrary.parliament.uk/research-briefings/cbp-7920/"}
        ]
    },
    {
        "id": "2022", "year": 2022, "displayYear": "2022", "date": "5 May 2022",
        "title": "2022 Northern Ireland Assembly election",
        "turnout": 63.6, "control": "sinnfein", "firstMinister": "Michelle O'Neill",
        "deputyFirstMinister": "Emma Little-Pengelly", "majority": False,
        "summary": "In a historic result, Sinn Féin became the largest party in the Northern Ireland Assembly for the first time, winning 27 seats to the DUP's 25. This marked the first time a nationalist or republican party had topped the poll in Northern Ireland's history. The Alliance Party recorded a major surge, winning 17 seats and cementing itself as a strong centrist, cross-community third force. Devolution was not restored immediately due to DUP protests over the Northern Ireland Protocol, but was eventually restored in February 2024 with Michelle O'Neill appointed First Minister.",
        "highlights": [
            "Sinn Féin becomes the largest party, earning the right to nominate the First Minister",
            "Alliance Party records a major surge, rising to 17 seats",
            "DUP collapses to 25 seats amid protests over the post-Brexit Northern Ireland Protocol",
            "Michelle O'Neill becomes the first nationalist First Minister in February 2024",
            "Unionist representation continues to fragment, with TUV winning 7.6% of votes but only 1 seat"
        ],
        "parliament": {
            "system": "Single Transferable Vote",
            "totalSeats": 90,
            "majorityThreshold": 46,
            "results": [
                {"party": "sinnfein", "seats": 27, "pct": 29.0},
                {"party": "dup", "seats": 25, "pct": 21.3},
                {"party": "alliance", "seats": 17, "pct": 13.5},
                {"party": "uup", "seats": 9, "pct": 11.2},
                {"party": "sdlp", "seats": 8, "pct": 9.1},
                {"party": "tuv", "seats": 1, "pct": 7.6},
                {"party": "pbp", "seats": 1, "pct": 1.4},
                {"partyLabel": "Independent", "seats": 2, "pct": 3.7}
            ],
            "otherListVotes": [
                {"name": "Green Party NI", "pct": 2.2},
                {"name": "Workers' Party", "pct": 0.1}
            ]
        },
        "sources": [
            {"label": "House of Commons Library — Northern Ireland Assembly Election 2022 (CBP-9549)", "url": "https://commonslibrary.parliament.uk/research-briefings/cbp-9549/"}
        ]
    }
]


def manifesto_entries(eid: str) -> list[dict]:
    entry = next(e for e in ASSETS if e["id"] == eid)
    titles = MANIFESTO_TITLES.get(eid, {})
    out = []
    for m in entry["manifestos"]:
        party = m["party"]
        row = {
            "title": titles.get(party, party.replace("-", " ").title() + " Manifesto " + eid),
            "pdf": f"/manifestos/stormont/{eid}/{party}/manifesto.pdf",
            "cover": f"/manifestos/stormont/{eid}/{party}/cover.png",
            "party": party,
        }
        out.append(row)
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    index = []
    for e in ELECTIONS:
        doc = dict(e)
        doc["body"] = "stormont"
        doc["manifestos"] = manifesto_entries(e["id"])
        (OUT / f"{e['id']}.json").write_text(
            json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        index.append({
            "id": e["id"],
            "body": "stormont",
            "year": e["year"],
            "displayYear": e["displayYear"],
            "date": e["date"],
            "title": "Northern Ireland Assembly election",
            "control": e["control"],
            "winnerName": e.get("firstMinister") or "",
            "firstMinister": e.get("firstMinister"),
            "deputyFirstMinister": e.get("deputyFirstMinister"),
        })
    (OUT / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {len(ELECTIONS)} elections to {OUT}")


if __name__ == "__main__":
    main()
