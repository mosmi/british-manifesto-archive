#!/usr/bin/env python3
"""Write data/devolved/holyrood/*.json election files."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "devolved" / "holyrood"
ASSETS = json.loads((ROOT / "scripts" / "holyrood-assets.json").read_text())

MANIFESTO_TITLES = {
    "sp-1999": {
        "scottishcon": "Scottish Conservative Manifesto 1999",
        "scottishgrn": "Scottish Green Party Manifesto 1999",
        "scottishlibdem": "Scottish Liberal Democrats Manifesto 1999",
        "snp": "SNP Manifesto 1999",
    },
    "sp-2003": {
        "scottishcon": "Scottish Conservative Manifesto 2003",
        "scottishgrn": "Scottish Greens Manifesto 2003",
        "scottishlab": "Scottish Labour Manifesto 2003",
        "bnp": "BNP Manifesto 2003",
        "scottishlibdem": "Liberal Democrats Manifesto 2003",
        "snp": "SNP Manifesto 2003",
        "ssp": "Scottish Socialist Party Manifesto 2003",
    },
    "sp-2007": {
        "snp": "SNP Manifesto 2007",
        "scottishcon": "Scottish Conservative Manifesto 2007",
        "scottishgrn": "Scottish Greens Manifesto 2007",
        "scottishlab": "Scottish Labour Manifesto 2007",
        "scottishlibdem": "Scottish Liberal Democrats Manifesto 2007",
        "solidarity": "Solidarity Manifesto 2007",
        "ukip": "UKIP Scotland Manifesto 2007",
        "bnp": "BNP Manifesto 2007",
        "scottishchristian": "Scottish Christian Party Manifesto 2007",
        "ssp": "Scottish Socialist Party Manifesto 2007",
    },
    "sp-2011": {
        "snp": "SNP Manifesto 2011",
        "scottishlab": "Scottish Labour Manifesto 2011",
        "scottishcon": "Scottish Conservative Manifesto 2011",
        "scottishgrn": "Scottish Greens Manifesto 2011",
        "bnp": "BNP Manifesto 2011",
        "communist": "Communist Party Manifesto 2011",
        "scottishlibdem": "Liberal Democrats Manifesto 2011",
        "ssp": "Scottish Socialist Party Manifesto 2011",
    },
    "sp-2016": {
        "rise": "RISE Manifesto 2016",
        "snp": "SNP Manifesto 2016",
        "cooperative": "Scottish Co-operative Party Manifesto 2016",
        "scottishgrn": "Scottish Greens Manifesto 2016",
        "scottishlab": "Scottish Labour Manifesto 2016",
        "scottishcon": "Scottish Conservative Manifesto 2016",
        "scottishlibdem": "Scottish Liberal Democrats Manifesto 2016",
        "ukip": "UKIP Scotland Manifesto 2016",
        "wep": "Women's Equality Party Scotland Manifesto 2016",
        "communist": "Communist Party Manifesto 2016",
    },
    "sp-2021": {
        "isp": "Independence for Scotland Party Manifesto 2021",
        "snp": "SNP Manifesto 2021",
        "scottishgrn": "Scottish Greens Manifesto 2021",
        "alba": "Alba Party Manifesto 2021",
        "allforunity": "All for Unity Manifesto 2021",
        "scottishcon": "Scottish Conservatives Manifesto 2021",
        "scottishfamily": "Scottish Family Party Manifesto 2021",
        "scottishlab": "Scottish Labour Manifesto 2021",
        "scottishlibdem": "Scottish Liberal Democrats Manifesto 2021",
        "scottishlibertarian": "Scottish Libertarian Party Manifesto 2021",
        "ukip": "UKIP Scotland Manifesto 2021",
    },
    "sp-2026": {
        "isp": "Independence for Scotland Party Manifesto 2026",
        "reform": "Reform UK Scotland Manifesto 2026",
        "snp": "SNP Manifesto 2026",
        "scottishcon": "Scottish Conservatives Manifesto 2026",
        "scottishgrn": "Scottish Greens Manifesto 2026",
        "scottishlab": "Scottish Labour Manifesto 2026",
        "scottishlibdem": "Scottish Liberal Democrats Manifesto 2026",
        "scottishlibertarian": "Scottish Libertarian Party Manifesto 2026",
        "ssp": "Scottish Socialist Party Manifesto 2026",
        "workersparty": "Scottish Workers Party of Britain Manifesto 2026",
        "sovereignty": "Sovereignty Scotland Manifesto 2026",
    },
}

PARTY_LABELS = {
    "scottishchristian": "Scottish Christian Party",
}

ELECTIONS = [
    {
        "id": "sp-1999", "year": 1999, "displayYear": "1999", "date": "6 May 1999",
        "title": "1999 Scottish Parliament election",
        "turnout": 58.0, "control": "scottishlab", "firstMinister": "Donald Dewar",
        "majority": False,
        "summary": "Scotland's first Holyrood election established a Labour-led administration in coalition with the Liberal Democrats. Donald Dewar became the inaugural First Minister. Labour won 56 of 129 seats — nine short of a majority — while the SNP became the principal opposition with 35 MSPs. The Conservatives won all 18 of their seats through the regional lists, having failed to win a single constituency.",
        "highlights": [
            "First elections to the Scottish Parliament since devolution",
            "Donald Dewar becomes Scotland's inaugural First Minister",
            "Labour–Liberal Democrat coalition government formed",
            "SNP becomes the largest opposition party with 35 MSPs",
            "Turnout 58% in constituencies, 57% on regional lists",
            "Dennis Canavan wins Falkirk West as an independent",
        ],
        "parliament": {
            "results": [
                {"party": "scottishlab", "constituencySeats": 53, "listSeats": 3, "seats": 56, "constituencyPct": 38.8, "listPct": 33.6},
                {"party": "snp", "constituencySeats": 7, "listSeats": 28, "seats": 35, "constituencyPct": 28.7, "listPct": 27.3},
                {"party": "scottishcon", "constituencySeats": 0, "listSeats": 18, "seats": 18, "constituencyPct": 15.6, "listPct": 15.4},
                {"party": "scottishlibdem", "constituencySeats": 12, "listSeats": 5, "seats": 17, "constituencyPct": 14.2, "listPct": 12.4},
                {"party": "scottishgrn", "constituencySeats": 0, "listSeats": 1, "seats": 1, "listPct": 3.6},
                {"partyLabel": "Others", "constituencySeats": 1, "listSeats": 2, "seats": 3, "listPct": 11.3},
            ],
            "otherListVotes": [
                {"name": "Scottish Socialist Party", "pct": 3.6},
                {"name": "Scottish Senior Citizens Unity Party", "pct": 1.5},
            ],
        },
        "sources": [
            {"label": "House of Commons Library — 1999 Scottish Parliament election (RP99-50)", "url": "https://commonslibrary.parliament.uk/research-briefings/rp99-50/"},
        ],
    },
    {
        "id": "sp-2003", "year": 2003, "displayYear": "2003", "date": "1 May 2003",
        "title": "2003 Scottish Parliament election",
        "turnout": 49.0, "control": "scottishlab", "firstMinister": "Jack McConnell",
        "majority": False,
        "summary": "Labour remained the largest party but lost six seats, finishing on 50 MSPs. The SNP fell to 27 seats as voters shifted towards smaller parties on the regional lists — the Scottish Greens won seven MSPs and the Scottish Socialist Party six. Jack McConnell continued as First Minister in a renewed Labour–Liberal Democrat coalition. Turnout fell sharply to 49%, down nine points from 1999.",
        "highlights": [
            "Labour retains largest party status with 50 seats",
            "Scottish Greens win seven regional MSPs",
            "Scottish Socialist Party wins six list seats",
            "Turnout falls to 49% — down from 58% in 1999",
            "Dennis Canavan retains Falkirk West as an independent",
        ],
        "parliament": {
            "results": [
                {"party": "scottishlab", "constituencySeats": 46, "listSeats": 4, "seats": 50, "constituencyPct": 34.5, "listPct": 29.4},
                {"party": "snp", "constituencySeats": 9, "listSeats": 18, "seats": 27, "constituencyPct": 23.7, "listPct": 20.9},
                {"party": "scottishcon", "constituencySeats": 3, "listSeats": 15, "seats": 18, "constituencyPct": 16.6, "listPct": 15.6},
                {"party": "scottishlibdem", "constituencySeats": 13, "listSeats": 4, "seats": 17, "constituencyPct": 15.3, "listPct": 11.8},
                {"party": "scottishgrn", "constituencySeats": 0, "listSeats": 7, "seats": 7, "listPct": 6.9},
                {"party": "ssp", "constituencySeats": 0, "listSeats": 6, "seats": 6, "listPct": 6.7},
                {"partyLabel": "Others", "constituencySeats": 2, "listSeats": 2, "seats": 4, "listPct": 4.6},
            ],
        },
        "sources": [
            {"label": "House of Commons Library — 2003 Scottish Parliament election (RP03-46)", "url": "https://commonslibrary.parliament.uk/research-briefings/rp03-46/"},
        ],
    },
    {
        "id": "sp-2007", "year": 2007, "displayYear": "2007", "date": "3 May 2007",
        "title": "2007 Scottish Parliament election",
        "turnout": 51.7, "control": "snp", "firstMinister": "Alex Salmond",
        "majority": False,
        "summary": "The SNP overtook Labour to become the largest party at Holyrood for the first time, winning 47 seats to Labour's 46. Alex Salmond returned to lead a minority SNP government after eight years of Labour rule. The SNP gained 20 seats compared with 2003, capitalising on a 9.6-point rise in its share of the vote. The Greens lost five seats; the Scottish Socialist Party was wiped out.",
        "highlights": [
            "SNP becomes largest party for the first time — 47 seats",
            "Alex Salmond becomes First Minister, leading a minority government",
            "Labour falls to 46 seats, losing its position as largest party",
            "SNP vote share rises to 32.0% — up 9.6 points from 2003",
            "Turnout 51.7% in constituencies, 52.4% on regional lists",
        ],
        "parliament": {
            "results": [
                {"party": "snp", "constituencySeats": 21, "listSeats": 26, "seats": 47, "constituencyPct": 32.9, "listPct": 31.0},
                {"party": "scottishlab", "constituencySeats": 37, "listSeats": 9, "seats": 46, "constituencyPct": 32.1, "listPct": 29.2},
                {"party": "scottishcon", "constituencySeats": 4, "listSeats": 13, "seats": 17, "constituencyPct": 16.6, "listPct": 13.9},
                {"party": "scottishlibdem", "constituencySeats": 11, "listSeats": 5, "seats": 16, "constituencyPct": 16.2, "listPct": 11.3},
                {"party": "scottishgrn", "constituencySeats": 0, "listSeats": 2, "seats": 2, "listPct": 4.0},
                {"partyLabel": "Margo MacDonald (Independent)", "constituencySeats": 0, "listSeats": 1, "seats": 1},
            ],
        },
        "sources": [
            {"label": "House of Commons Library — 2007 Scottish Parliament election (RP07-46)", "url": "https://commonslibrary.parliament.uk/research-briefings/rp07-46/"},
        ],
    },
    {
        "id": "sp-2011", "year": 2011, "displayYear": "2011", "date": "5 May 2011",
        "title": "2011 Scottish Parliament election",
        "turnout": 50.3, "control": "snp", "firstMinister": "Alex Salmond",
        "majority": True,
        "summary": "The SNP won an outright majority — 69 of 129 seats — with 44.7% of the regional vote, a result thought impossible under the Additional Member System. Alex Salmond's government secured a mandate for an independence referendum. Labour fell to 37 seats; the Liberal Democrats collapsed from 16 to five seats as voters punished the party for its Westminster coalition with the Conservatives.",
        "highlights": [
            "SNP wins historic overall majority — 69 of 129 seats",
            "First majority government at Holyrood under the AMS electoral system",
            "SNP takes 53 constituency seats including traditional Labour heartlands",
            "Liberal Democrats lose 11 seats, falling to five MSPs",
            "Mandate secured for the 2014 independence referendum",
        ],
        "parliament": {
            "results": [
                {"party": "snp", "constituencySeats": 53, "listSeats": 16, "seats": 69, "constituencyPct": 45.4, "listPct": 44.0},
                {"party": "scottishlab", "constituencySeats": 15, "listSeats": 22, "seats": 37, "constituencyPct": 31.7, "listPct": 26.3},
                {"party": "scottishcon", "constituencySeats": 3, "listSeats": 12, "seats": 15, "constituencyPct": 13.9, "listPct": 12.4},
                {"party": "scottishlibdem", "constituencySeats": 2, "listSeats": 3, "seats": 5, "constituencyPct": 7.9, "listPct": 5.2},
                {"party": "scottishgrn", "constituencySeats": 0, "listSeats": 2, "seats": 2, "listPct": 4.4},
                {"partyLabel": "Margo MacDonald (Independent)", "constituencySeats": 0, "listSeats": 1, "seats": 1},
            ],
        },
        "sources": [
            {"label": "House of Commons Library — 2011 Scottish Parliament election (RP11-41)", "url": "https://commonslibrary.parliament.uk/research-briefings/rp11-41/"},
        ],
    },
    {
        "id": "sp-2016", "year": 2016, "displayYear": "2016", "date": "5 May 2016",
        "title": "2016 Scottish Parliament election",
        "turnout": 55.7, "control": "snp", "firstMinister": "Nicola Sturgeon",
        "majority": False,
        "summary": "The SNP won the most seats for a third consecutive election but lost its overall majority, falling to 63 MSPs. The Conservatives under Ruth Davidson more than doubled their representation to 31 seats — their best ever Holyrood result — and became the principal opposition party. Labour lost 13 seats, finishing third with 24 MSPs. Turnout rose to 55.7%, the highest since 1999.",
        "highlights": [
            "SNP wins third term but loses overall majority — 63 seats",
            "Conservatives double representation to 31 seats — best Holyrood result",
            "Ruth Davidson's Conservatives become the largest opposition party",
            "Labour falls to third place with 24 seats",
            "Turnout rises to 55.7% — highest since the inaugural 1999 election",
        ],
        "parliament": {
            "results": [
                {"party": "snp", "constituencySeats": 59, "listSeats": 4, "seats": 63, "constituencyPct": 46.5, "listPct": 41.7},
                {"party": "scottishcon", "constituencySeats": 7, "listSeats": 24, "seats": 31, "constituencyPct": 22.0, "listPct": 22.9},
                {"party": "scottishlab", "constituencySeats": 3, "listSeats": 21, "seats": 24, "constituencyPct": 22.6, "listPct": 19.1},
                {"party": "scottishlibdem", "constituencySeats": 4, "listSeats": 1, "seats": 5, "constituencyPct": 7.8, "listPct": 5.2},
                {"party": "scottishgrn", "constituencySeats": 0, "listSeats": 6, "seats": 6, "constituencyPct": 0.6, "listPct": 6.6},
            ],
            "otherListVotes": [
                {"name": "UK Independence Party", "pct": 2.0},
                {"name": "RISE", "pct": 0.6},
            ],
        },
        "sources": [
            {"label": "House of Commons Library — 2016 Scottish Parliament election (CBP-7599)", "url": "https://commonslibrary.parliament.uk/research-briefings/cbp-7599/"},
        ],
    },
    {
        "id": "sp-2021", "year": 2021, "displayYear": "2021", "date": "6 May 2021",
        "title": "2021 Scottish Parliament election",
        "turnout": 63.5, "control": "snp", "firstMinister": "Nicola Sturgeon",
        "majority": False,
        "summary": "The SNP won 64 seats — one more than in 2016 — but again fell one seat short of an overall majority. The Conservatives held 31 seats; Labour won 22. The Scottish Greens achieved their best result with eight MSPs and later entered a formal co-operation agreement with the SNP government. Alba and All for Unity contested the election on rival constitutional platforms but won no seats. Turnout reached 63.5%, the highest in Holyrood history.",
        "highlights": [
            "SNP wins 64 seats — one short of a majority",
            "Scottish Greens win eight MSPs — their best Holyrood result",
            "SNP–Green co-operation agreement formed after the election",
            "Alba Party and All for Unity contest election but win no seats",
            "Record turnout of 63.5% on the regional ballot",
        ],
        "parliament": {
            "results": [
                {"party": "snp", "constituencySeats": 62, "listSeats": 2, "seats": 64, "constituencyPct": 47.7, "listPct": 43.5},
                {"party": "scottishcon", "constituencySeats": 5, "listSeats": 26, "seats": 31, "constituencyPct": 22.5, "listPct": 22.7},
                {"party": "scottishlab", "constituencySeats": 2, "listSeats": 20, "seats": 22, "constituencyPct": 20.8, "listPct": 19.7},
                {"party": "scottishlibdem", "constituencySeats": 4, "listSeats": 0, "seats": 4, "constituencyPct": 6.5, "listPct": 6.0},
                {"party": "scottishgrn", "constituencySeats": 0, "listSeats": 8, "seats": 8, "constituencyPct": 3.6, "listPct": 4.7},
            ],
            "otherListVotes": [
                {"name": "Alba Party", "votes": 17932, "pct": 0.8},
                {"name": "All for Unity", "votes": 17932, "pct": 0.8},
                {"name": "Independence for Scotland Party", "pct": 0.6},
                {"name": "Scottish Family Party", "pct": 0.5},
            ],
        },
        "sources": [
            {"label": "House of Commons Library — 2021 Scottish Parliament election (CBP-9230)", "url": "https://commonslibrary.parliament.uk/research-briefings/cbp-9230/"},
        ],
    },
    {
        "id": "sp-2026", "year": 2026, "displayYear": "2026", "date": "7 May 2026",
        "title": "2026 Scottish Parliament election",
        "turnout": 53.2, "control": "snp", "firstMinister": "John Swinney",
        "majority": False,
        "summary": "The SNP remained the largest party with 58 seats but fell seven short of a majority in a dramatically reshaped parliament. Reform UK entered Holyrood for the first time with 17 regional MSPs, matching Scottish Labour's total. The Scottish Greens surged to 15 seats while the Conservatives collapsed from 31 to 12 — their worst result since devolution. The Liberal Democrats recovered to ten seats. Turnout was 53.2%, down ten points from the record high of 2021.",
        "highlights": [
            "SNP remains largest party with 58 seats — seven short of a majority",
            "Reform UK wins 17 regional seats on its first Holyrood contest",
            "Scottish Greens surge to 15 MSPs — up from eight in 2021",
            "Conservatives fall from 31 to 12 seats — worst Holyrood result",
            "Liberal Democrats recover to ten seats",
            "Turnout 53.2% — down from record 63.5% in 2021",
        ],
        "parliament": {
            "results": [
                {"party": "snp", "constituencySeats": 57, "listSeats": 1, "seats": 58, "constituencyVotes": 877077, "constituencyPct": 38.2, "listVotes": 625949, "listPct": 27.2},
                {"party": "scottishlab", "constituencySeats": 3, "listSeats": 14, "seats": 17, "constituencyVotes": 440708, "constituencyPct": 19.2, "listVotes": 368785, "listPct": 16.0},
                {"party": "reform", "constituencySeats": 0, "listSeats": 17, "seats": 17, "constituencyVotes": 361994, "constituencyPct": 15.8, "listVotes": 383425, "listPct": 16.6},
                {"party": "scottishgrn", "constituencySeats": 2, "listSeats": 13, "seats": 15, "constituencyVotes": 52528, "constituencyPct": 2.3, "listVotes": 321964, "listPct": 14.0},
                {"party": "scottishcon", "constituencySeats": 4, "listSeats": 8, "seats": 12, "constituencyVotes": 271740, "constituencyPct": 11.8, "listVotes": 271550, "listPct": 11.8},
                {"party": "scottishlibdem", "constituencySeats": 7, "listSeats": 3, "seats": 10, "constituencyVotes": 261408, "constituencyPct": 11.4, "listVotes": 216224, "listPct": 9.4},
            ],
            "otherListVotes": [
                {"name": "Independence for Scotland Party", "votes": 10246, "pct": 0.4},
                {"name": "Scottish Family Party", "votes": 17136, "pct": 0.7},
                {"name": "Scottish Socialist Party", "votes": 8326, "pct": 0.4},
                {"name": "Scottish Libertarian Party", "votes": 1909, "pct": 0.1},
                {"name": "Sovereignty Scotland", "pct": 0.1},
            ],
        },
        "sources": [
            {"label": "BBC News — Scotland election results 2026", "url": "https://www.bbc.com/news/election/2026/scotland/results"},
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
            "pdf": f"/manifestos/holyrood/{eid}/{party}/manifesto.pdf",
            "cover": f"/manifestos/holyrood/{eid}/{party}/cover.png",
        }
        if party in PARTY_LABELS:
            row["partyLabel"] = PARTY_LABELS[party]
        else:
            pid = party
            if pid in ("scottishcon", "scottishlab", "scottishlibdem", "scottishgrn"):
                row["party"] = pid
            elif pid in ("snp", "alba", "ssp", "ukip", "bnp", "communist", "reform",
                         "cooperative", "wep", "workersparty", "isp", "allforunity",
                         "scottishfamily", "scottishlibertarian", "sovereignty",
                         "solidarity", "rise", "scottishchristian"):
                row["party"] = pid
            else:
                row["party"] = pid
        out.append(row)
    return out


def enrich_parliament(p: dict) -> dict:
    base = {
        "totalSeats": 129,
        "constituencySeats": 73,
        "listSeats": 56,
        "majorityThreshold": 65,
        "system": "Additional Member System",
    }
    base.update(p)
    return base


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    index = []
    for e in ELECTIONS:
        doc = dict(e)
        doc["body"] = "holyrood"
        doc["parliament"] = enrich_parliament(doc["parliament"])
        doc["manifestos"] = manifesto_entries(e["id"])
        (OUT / f"{e['id']}.json").write_text(
            json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        index.append({
            "id": e["id"],
            "body": "holyrood",
            "year": e["year"],
            "displayYear": e["displayYear"],
            "date": e["date"],
            "title": "Scottish Parliament election",
            "control": e["control"],
            "winnerName": e.get("firstMinister", ""),
            "firstMinister": e.get("firstMinister"),
        })
    (OUT / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {len(ELECTIONS)} elections to {OUT}")


PARTIES_NAME = {
    "scottishlab": "Labour control",
    "snp": "SNP control",
}

if __name__ == "__main__":
    main()
