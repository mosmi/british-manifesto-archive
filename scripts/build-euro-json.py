import json
import os

OUT_DIR = "/Users/mosmi/Documents/Antigravity/Projects/british-manifesto-archive/data/devolved/euro"
os.makedirs(OUT_DIR, exist_ok=True)

# 1979-2019 data compile
ELECTIONS_DATA = {
    "1979": {
        "date": "7 June 1979",
        "turnout": 32.7,
        "control": "conservative",
        "summary": "The first direct elections to the European Parliament saw a landslide victory for Margaret Thatcher's Conservative Party, which won 60 of the 78 Great Britain seats on 51% of the vote. Labour won 17 seats and the SNP won 1 seat in Scotland. In Northern Ireland, the DUP, SDLP, and UUP won 1 seat each under the STV system.",
        "highlights": [
            "First direct elections to the European Parliament",
            "Conservatives win 60 seats with 51% of Great Britain vote",
            "Labour wins 17 seats; SNP wins 1 seat in Scotland",
            "DUP, SDLP, and UUP win 1 seat each in Northern Ireland under STV",
            "Low turnout in Great Britain (32.1%) compared to Northern Ireland (55.6%)"
        ],
        "totalSeats": 81,
        "majorityThreshold": 41,
        "system": "First Past the Post (GB) & STV (NI)",
        "results": [
            {"party": "conservative", "seats": 60, "pct": 50.6},
            {"party": "labour", "seats": 17, "pct": 33.0},
            {"party": "snp", "seats": 1, "pct": 1.9},
            {"party": "dup", "seats": 1, "pct": 29.8},
            {"party": "sdlp", "seats": 1, "pct": 24.6},
            {"party": "uup", "seats": 1, "pct": 21.9},
            {"party": "libdem", "seats": 0, "pct": 13.1},
            {"party": "plaid", "seats": 0, "pct": 0.6},
            {"party": "green", "seats": 0, "pct": 0.1},
            {"party": "alliance", "seats": 0, "pct": 6.8}
        ],
        "manifestos": []
    },
    "1984": {
        "date": "14 June 1984",
        "turnout": 32.9,
        "control": "conservative",
        "summary": "The Conservatives under Margaret Thatcher retained their majority of UK seats, though their share fell as Labour under Neil Kinnock recovered, winning 32 seats (up 15). The SDP-Liberal Alliance failed to win any seats despite taking 19% of the Great Britain vote.",
        "highlights": [
            "Conservatives retain overall majority of UK seats (45)",
            "Labour recovers to win 32 seats under Neil Kinnock",
            "SDP-Liberal Alliance fails to win any seats despite 19.1% vote share",
            "SNP retains 1 seat; DUP, SDLP, and UUP hold Northern Ireland seats",
            "Turnout remains low at 32.9% UK-wide"
        ],
        "totalSeats": 81,
        "majorityThreshold": 41,
        "system": "First Past the Post (GB) & STV (NI)",
        "results": [
            {"party": "conservative", "seats": 45, "pct": 40.8},
            {"party": "labour", "seats": 32, "pct": 36.5},
            {"party": "libdem", "seats": 0, "pct": 19.1},
            {"party": "snp", "seats": 1, "pct": 1.7},
            {"party": "dup", "seats": 1, "pct": 33.6},
            {"party": "sdlp", "seats": 1, "pct": 22.1},
            {"party": "uup", "seats": 1, "pct": 21.5},
            {"party": "plaid", "seats": 0, "pct": 0.8},
            {"party": "green", "seats": 0, "pct": 0.5},
            {"party": "alliance", "seats": 0, "pct": 5.0}
        ],
        "manifestos": []
    },
    "1989": {
        "date": "15 June 1989",
        "turnout": 36.8,
        "control": "labour",
        "summary": "Labour won a majority of UK seats for the first time, taking 45 seats to the Conservatives' 32. The election was also notable for the Green Party (formerly the Ecology Party) receiving 14.9% of the Great Britain vote, though under the first-past-the-post system they failed to win any seats.",
        "highlights": [
            "Labour wins most UK seats (45) under Neil Kinnock",
            "Green Party achieves historic 14.9% of Great Britain vote but wins no seats",
            "SDP-Liberal Alliance vote collapses to 6.2% following their split/reorganisation",
            "Conservatives fall to 32 seats — lowest since direct elections began",
            "DUP, SDLP, and UUP retain 1 seat each in Northern Ireland"
        ],
        "totalSeats": 81,
        "majorityThreshold": 41,
        "system": "First Past the Post (GB) & STV (NI)",
        "results": [
            {"party": "labour", "seats": 45, "pct": 40.1},
            {"party": "conservative", "seats": 32, "pct": 34.7},
            {"party": "green", "seats": 0, "pct": 14.9},
            {"party": "libdem", "seats": 0, "pct": 6.2},
            {"party": "snp", "seats": 1, "pct": 2.6},
            {"party": "dup", "seats": 1, "pct": 29.9},
            {"party": "sdlp", "seats": 1, "pct": 25.5},
            {"party": "uup", "seats": 1, "pct": 22.2},
            {"party": "plaid", "seats": 0, "pct": 0.7},
            {"party": "alliance", "seats": 0, "pct": 5.2}
        ],
        "manifestos": []
    },
    "1994": {
        "date": "9 June 1994",
        "turnout": 36.5,
        "control": "labour",
        "summary": "John Major's Conservative government suffered a severe defeat, falling to just 18 seats, while Labour won a record 62 seats. The Liberal Democrats won their first-ever European seats, taking 2 in South West England, and Plaid Cymru won its first seat.",
        "highlights": [
            "Labour wins record 62 seats, dominating the Great Britain delegation",
            "Conservatives reduced to just 18 seats amidst John Major's leadership struggles",
            "Liberal Democrats win first European seats (2) under Paddy Ashdown",
            "SNP wins 2 seats; Plaid Cymru wins 1 seat in Wales",
            "STV results in NI unchanged with DUP, SDLP, and UUP holding 1 seat each"
        ],
        "totalSeats": 87,
        "majorityThreshold": 44,
        "system": "First Past the Post (GB) & STV (NI)",
        "results": [
            {"party": "labour", "seats": 62, "pct": 44.2},
            {"party": "conservative", "seats": 18, "pct": 27.9},
            {"party": "libdem", "seats": 2, "pct": 16.7},
            {"party": "snp", "seats": 2, "pct": 3.2},
            {"party": "dup", "seats": 1, "pct": 29.2},
            {"party": "sdlp", "seats": 1, "pct": 28.9},
            {"party": "uup", "seats": 1, "pct": 23.8},
            {"party": "plaid", "seats": 0, "pct": 1.1},
            {"party": "green", "seats": 0, "pct": 3.2},
            {"party": "alliance", "seats": 0, "pct": 4.1}
        ],
        "manifestos": []
    },
    "1999": {
        "date": "10 June 1999",
        "turnout": 24.0,
        "control": "conservative",
        "summary": "The introduction of the regional list proportional representation system changed the political dynamic, allowing smaller parties to win seats. The Conservatives won the most seats (36) while Labour fell to 29. The Liberal Democrats won 10, UKIP won its first 3 seats, and the Greens won 2 seats.",
        "highlights": [
            "First EP election held under regional list Proportional Representation in GB",
            "Conservatives win the most seats (36) under William Hague",
            "UKIP wins its first 3 European Parliament seats",
            "Green Party wins its first 2 seats (Caroline Lucas and Jean Lambert)",
            "Turnout drops to a record low of 24.0% UK-wide (23.1% in GB)"
        ],
        "totalSeats": 87,
        "majorityThreshold": 44,
        "system": "Regional list PR (GB) & STV (NI)",
        "results": [
            {"party": "conservative", "seats": 36, "pct": 35.8},
            {"party": "labour", "seats": 29, "pct": 28.0},
            {"party": "libdem", "seats": 10, "pct": 12.7},
            {"party": "ukip", "seats": 3, "pct": 7.0},
            {"party": "green", "seats": 2, "pct": 6.3},
            {"party": "snp", "seats": 2, "pct": 2.7},
            {"party": "plaid", "seats": 2, "pct": 1.9},
            {"party": "dup", "seats": 1, "pct": 28.4},
            {"party": "sdlp", "seats": 1, "pct": 28.1},
            {"party": "uup", "seats": 1, "pct": 17.6},
            {"party": "alliance", "seats": 0, "pct": 2.1}
        ],
        "manifestos": [
            {
                "title": "PES Manifesto 1999",
                "pdf": "/manifestos/euro/1999/pes/manifesto.pdf",
                "cover": "/manifestos/euro/1999/pes/manifesto.png",
                "party": "pes"
            }
        ]
    },
    "2004": {
        "date": "10 June 2004",
        "turnout": 38.5,
        "control": "conservative",
        "summary": "The election was marked by a strong performance by UKIP, which won 12 seats (up from 3) to tie with the Liberal Democrats. The Conservatives won the election with 27 seats, while Tony Blair's Labour Party suffered, falling to 19 seats. Sinn Féin won its first EP seat in Northern Ireland.",
        "highlights": [
            "UKIP surges to win 12 seats, matching the Liberal Democrats",
            "Labour drops to 19 seats, reflecting public dissatisfaction over the Iraq War",
            "Sinn Féin wins its first Northern Ireland seat, overtaking SDLP",
            "Conservatives win the election with 27 seats under Michael Howard",
            "Turnout recovers to 38.5% UK-wide, aided by postal voting trials"
        ],
        "totalSeats": 78,
        "majorityThreshold": 40,
        "system": "Regional list PR (GB) & STV (NI)",
        "results": [
            {"party": "conservative", "seats": 27, "pct": 26.7},
            {"party": "labour", "seats": 19, "pct": 22.6},
            {"party": "libdem", "seats": 12, "pct": 14.9},
            {"party": "ukip", "seats": 12, "pct": 16.2},
            {"party": "green", "seats": 2, "pct": 6.2},
            {"party": "snp", "seats": 2, "pct": 1.4},
            {"party": "plaid", "seats": 1, "pct": 1.0},
            {"party": "dup", "seats": 1, "pct": 32.0},
            {"party": "sinnfein", "seats": 1, "pct": 26.3},
            {"party": "uup", "seats": 1, "pct": 16.6},
            {"party": "sdlp", "seats": 0, "pct": 15.9}
        ],
        "manifestos": [
            {
                "title": "Conservative European Manifesto 2004",
                "pdf": "/manifestos/euro/2004/conservative/manifesto.pdf",
                "cover": "/manifestos/euro/2004/conservative/manifesto.png",
                "party": "conservative"
            },
            {
                "title": "Labour European Manifesto 2004",
                "pdf": "/manifestos/euro/2004/labour/manifesto.pdf",
                "cover": "/manifestos/euro/2004/labour/manifesto.png",
                "party": "labour"
            },
            {
                "title": "Green Party European Manifesto 2004",
                "pdf": "/manifestos/euro/2004/green/manifesto.pdf",
                "cover": "/manifestos/euro/2004/green/manifesto.png",
                "party": "green"
            },
            {
                "title": "SNP European Manifesto 2004",
                "pdf": "/manifestos/euro/2004/snp/manifesto.pdf",
                "cover": "/manifestos/euro/2004/snp/manifesto.png",
                "party": "snp"
            },
            {
                "title": "UKIP European Manifesto 2004",
                "pdf": "/manifestos/euro/2004/ukip/manifesto.pdf",
                "cover": "/manifestos/euro/2004/ukip/manifesto.png",
                "party": "ukip"
            },
            {
                "title": "Sinn Féin European Manifesto 2004",
                "pdf": "/manifestos/euro/2004/sinnfein/manifesto.pdf",
                "cover": "/manifestos/euro/2004/sinnfein/manifesto.png",
                "party": "sinnfein"
            },
            {
                "title": "DUP European Manifesto 2004",
                "pdf": "/manifestos/euro/2004/dup/manifesto.pdf",
                "cover": "/manifestos/euro/2004/dup/manifesto.png",
                "party": "dup"
            },
            {
                "title": "UUP European Manifesto 2004",
                "pdf": "/manifestos/euro/2004/uup/manifesto.pdf",
                "cover": "/manifestos/euro/2004/uup/manifesto.png",
                "party": "uup"
            },
            {
                "title": "SDLP European Manifesto 2004 (Part 1)",
                "pdf": "/manifestos/euro/2004/sdlp/manifesto-pt1.pdf",
                "cover": "/manifestos/euro/2004/sdlp/manifesto-pt1.png",
                "party": "sdlp"
            },
            {
                "title": "SDLP European Manifesto 2004 (Part 2)",
                "pdf": "/manifestos/euro/2004/sdlp/manifesto-pt2.pdf",
                "cover": "/manifestos/euro/2004/sdlp/manifesto-pt2.png",
                "party": "sdlp"
            },
            {
                "title": "Green Party Northern Ireland European Manifesto 2004",
                "pdf": "/manifestos/euro/2004/gpni/manifesto.pdf",
                "cover": "/manifestos/euro/2004/gpni/manifesto.png",
                "party": "gpni"
            },
            {
                "title": "Scottish Socialist Party European Manifesto 2004",
                "pdf": "/manifestos/euro/2004/ssp/manifesto.pdf",
                "cover": "/manifestos/euro/2004/ssp/manifesto.png",
                "party": "ssp"
            },
            {
                "title": "Socialist Environmental Alliance European Manifesto 2004",
                "pdf": "/manifestos/euro/2004/sea/manifesto.pdf",
                "cover": "/manifestos/euro/2004/sea/manifesto.png",
                "party": "sea"
            },
            {
                "title": "PES European Manifesto 2004",
                "pdf": "/manifestos/euro/2004/pes/manifesto.pdf",
                "cover": "/manifestos/euro/2004/pes/manifesto.png",
                "party": "pes"
            }
        ]
    },
    "2009": {
        "date": "4 June 2009",
        "turnout": 34.5,
        "control": "conservative",
        "summary": "Gordon Brown's Labour Party suffered a historic defeat, finishing third in vote share behind UKIP. The Conservatives won the election with 25 seats, while UKIP won 13 and Labour won 13. The British National Party (BNP) won its first-ever European seats, taking 2 in Yorkshire and North West England.",
        "highlights": [
            "Labour pushes to third place in vote share, trailing UKIP",
            "BNP wins its first-ever European Parliament seats (2)",
            "UKIP wins 13 seats, finishing second in seats and vote share",
            "Conservatives remain largest party with 25 seats under David Cameron",
            "Turnout falls slightly to 34.5% UK-wide"
        ],
        "totalSeats": 72,
        "majorityThreshold": 37,
        "system": "Regional list PR (GB) & STV (NI)",
        "results": [
            {"party": "conservative", "seats": 25, "pct": 27.7},
            {"party": "ukip", "seats": 13, "pct": 15.6},
            {"party": "labour", "seats": 13, "pct": 15.7},
            {"party": "libdem", "seats": 11, "pct": 13.7},
            {"party": "green", "seats": 2, "pct": 8.6},
            {"party": "bnp", "seats": 2, "pct": 6.2},
            {"party": "snp", "seats": 2, "pct": 2.1},
            {"party": "plaid", "seats": 1, "pct": 0.8},
            {"party": "dup", "seats": 1, "pct": 18.2},
            {"party": "sinnfein", "seats": 1, "pct": 26.0},
            {"party": "uup", "seats": 1, "pct": 17.1},
            {"party": "alliance", "seats": 0, "pct": 9.2}
        ],
        "manifestos": [
            {
                "title": "Liberal Democrat European Manifesto 2009",
                "pdf": "/manifestos/euro/2009/libdem/manifesto.pdf",
                "cover": "/manifestos/euro/2009/libdem/manifesto.png",
                "party": "libdem"
            },
            {
                "title": "Green Party European Manifesto 2009",
                "pdf": "/manifestos/euro/2009/green/manifesto.pdf",
                "cover": "/manifestos/euro/2009/green/manifesto.png",
                "party": "green"
            },
            {
                "title": "SNP European Manifesto 2009",
                "pdf": "/manifestos/euro/2009/snp/manifesto.pdf",
                "cover": "/manifestos/euro/2009/snp/manifesto.png",
                "party": "snp"
            },
            {
                "title": "Scottish Labour European Manifesto 2009",
                "pdf": "/manifestos/euro/2009/scottishlab/manifesto.pdf",
                "cover": "/manifestos/euro/2009/scottishlab/manifesto.png",
                "party": "scottishlab"
            },
            {
                "title": "Welsh Liberal Democrats European Manifesto 2009",
                "pdf": "/manifestos/euro/2009/welshlibdem/manifesto.pdf",
                "cover": "/manifestos/euro/2009/welshlibdem/manifesto.png",
                "party": "welshlibdem"
            },
            {
                "title": "Sinn Féin European Manifesto 2009",
                "pdf": "/manifestos/euro/2009/sinnfein/manifesto.pdf",
                "cover": "/manifestos/euro/2009/sinnfein/manifesto.png",
                "party": "sinnfein"
            },
            {
                "title": "UUP European Manifesto 2009",
                "pdf": "/manifestos/euro/2009/uup/manifesto.pdf",
                "cover": "/manifestos/euro/2009/uup/manifesto.png",
                "party": "uup"
            },
            {
                "title": "SDLP European Manifesto 2009",
                "pdf": "/manifestos/euro/2009/sdlp/manifesto.pdf",
                "cover": "/manifestos/euro/2009/sdlp/manifesto.png",
                "party": "sdlp"
            },
            {
                "title": "Green Party Northern Ireland European Manifesto 2009",
                "pdf": "/manifestos/euro/2009/gpni/manifesto.pdf",
                "cover": "/manifestos/euro/2009/gpni/manifesto.png",
                "party": "gpni"
            },
            {
                "title": "Scottish Greens European Manifesto 2009",
                "pdf": "/manifestos/euro/2009/scottishgrn/manifesto.pdf",
                "cover": "/manifestos/euro/2009/scottishgrn/manifesto.png",
                "party": "scottishgrn"
            },
            {
                "title": "TUV European Manifesto 2009",
                "pdf": "/manifestos/euro/2009/tuv/manifesto.pdf",
                "cover": "/manifestos/euro/2009/tuv/manifesto.png",
                "party": "tuv"
            },
            {
                "title": "BNP European Manifesto 2009",
                "pdf": "/manifestos/euro/2009/bnp/manifesto.pdf",
                "cover": "/manifestos/euro/2009/bnp/manifesto.png",
                "party": "bnp"
            },
            {
                "title": "BNP England European Election Leaflet 2009",
                "pdf": "/manifestos/euro/2009/bnp/leaflet.pdf",
                "cover": "/manifestos/euro/2009/bnp/leaflet.png",
                "party": "bnp"
            },
            {
                "title": "English Democrats European Manifesto 2009",
                "pdf": "/manifestos/euro/2009/englishdemocrats/manifesto.pdf",
                "cover": "/manifestos/euro/2009/englishdemocrats/manifesto.png",
                "party": "englishdemocrats"
            },
            {
                "title": "Christian Party / CPA European Election Leaflet 2009",
                "pdf": "/manifestos/euro/2009/christian/leaflet.pdf",
                "cover": "/manifestos/euro/2009/christian/leaflet.png",
                "party": "christian"
            },
            {
                "title": "PES European Manifesto 2009",
                "pdf": "/manifestos/euro/2009/pes/manifesto.pdf",
                "cover": "/manifestos/euro/2009/pes/manifesto.png",
                "party": "pes"
            },
            {
                "title": "PES European Election Flyer 2009",
                "pdf": "/manifestos/euro/2009/pes/flyer.pdf",
                "cover": "/manifestos/euro/2009/pes/flyer.png",
                "party": "pes"
            },
            {
                "title": "ELDR European Manifesto 2009",
                "pdf": "/manifestos/euro/2009/eldr/manifesto.pdf",
                "cover": "/manifestos/euro/2009/eldr/manifesto.png",
                "party": "eldr"
            }
        ]
    },
    "2014": {
        "date": "22 May 2014",
        "turnout": 35.4,
        "control": "ukip",
        "summary": "Nigel Farage's UKIP achieved a historic national victory, winning the most seats (24) and topping the poll with 27.5% of the Great Britain vote. This marked the first time since 1906 that a party other than Labour or the Conservatives had won the popular vote in a nationwide UK election. Labour rose to 20 seats, while the Conservatives fell to 19, and the Liberal Democrats were decimated, losing all but one of their 11 seats.",
        "highlights": [
            "UKIP tops the national poll with 24 seats, a historic first for a minor party",
            "Liberal Democrats suffer a catastrophic defeat, losing 10 of their 11 seats",
            "Labour returns 20 seats to push Conservatives (19) into third place",
            "Green Party gains a seat to win 3 seats overall",
            "STV in Northern Ireland returns 1 DUP, 1 Sinn Féin, and 1 UUP"
        ],
        "totalSeats": 73,
        "majorityThreshold": 37,
        "system": "Regional list PR (GB) & STV (NI)",
        "results": [
            {"party": "ukip", "seats": 24, "pct": 26.6},
            {"party": "labour", "seats": 20, "pct": 24.4},
            {"party": "conservative", "seats": 19, "pct": 23.0},
            {"party": "green", "seats": 3, "pct": 7.6},
            {"party": "snp", "seats": 2, "pct": 2.4},
            {"party": "libdem", "seats": 1, "pct": 6.6},
            {"party": "plaid", "seats": 1, "pct": 0.7},
            {"party": "sinnfein", "seats": 1, "pct": 25.5},
            {"party": "dup", "seats": 1, "pct": 20.9},
            {"party": "uup", "seats": 1, "pct": 13.3},
            {"party": "sdlp", "seats": 0, "pct": 13.0},
            {"party": "alliance", "seats": 0, "pct": 7.1}
        ],
        "manifestos": [
            {
                "title": "UKIP European Manifesto 2014",
                "pdf": "/manifestos/euro/2014/ukip/manifesto.pdf",
                "cover": "/manifestos/euro/2014/ukip/manifesto.png",
                "party": "ukip"
            },
            {
                "title": "Labour European Manifesto 2014",
                "pdf": "/manifestos/euro/2014/labour/manifesto.pdf",
                "cover": "/manifestos/euro/2014/labour/manifesto.png",
                "party": "labour"
            },
            {
                "title": "Conservative European Manifesto 2014",
                "pdf": "/manifestos/euro/2014/conservative/manifesto.pdf",
                "cover": "/manifestos/euro/2014/conservative/manifesto.png",
                "party": "conservative"
            },
            {
                "title": "Green Party European Manifesto 2014",
                "pdf": "/manifestos/euro/2014/green/manifesto.pdf",
                "cover": "/manifestos/euro/2014/green/manifesto.png",
                "party": "green"
            },
            {
                "title": "Plaid Cymru European Manifesto 2014",
                "pdf": "/manifestos/euro/2014/plaid/manifesto.pdf",
                "cover": "/manifestos/euro/2014/plaid/manifesto.png",
                "party": "plaid"
            },
            {
                "title": "SDLP European Manifesto 2014",
                "pdf": "/manifestos/euro/2014/sdlp/manifesto.pdf",
                "cover": "/manifestos/euro/2014/sdlp/manifesto.png",
                "party": "sdlp"
            },
            {
                "title": "Scottish Conservatives European Manifesto 2014",
                "pdf": "/manifestos/euro/2014/scottishcon/manifesto.pdf",
                "cover": "/manifestos/euro/2014/scottishcon/manifesto.png",
                "party": "scottishcon"
            },
            {
                "title": "Scottish Greens European Manifesto 2014",
                "pdf": "/manifestos/euro/2014/scottishgrn/manifesto.pdf",
                "cover": "/manifestos/euro/2014/scottishgrn/manifesto.png",
                "party": "scottishgrn"
            },
            {
                "title": "TUV European Manifesto 2014",
                "pdf": "/manifestos/euro/2014/tuv/manifesto.pdf",
                "cover": "/manifestos/euro/2014/tuv/manifesto.png",
                "party": "tuv"
            },
            {
                "title": "UUP European Manifesto 2014",
                "pdf": "/manifestos/euro/2014/uup/manifesto.pdf",
                "cover": "/manifestos/euro/2014/uup/manifesto.png",
                "party": "uup"
            },
            {
                "title": "Welsh Conservatives European Manifesto 2014",
                "pdf": "/manifestos/euro/2014/welshcon/manifesto.pdf",
                "cover": "/manifestos/euro/2014/welshcon/manifesto.png",
                "party": "welshcon"
            },
            {
                "title": "Welsh Liberal Democrats European Manifesto 2014",
                "pdf": "/manifestos/euro/2014/welshlibdem/manifesto.pdf",
                "cover": "/manifestos/euro/2014/welshlibdem/manifesto.png",
                "party": "welshlibdem"
            },
            {
                "title": "PES European Manifesto 2014",
                "pdf": "/manifestos/euro/2014/pes/manifesto.pdf",
                "cover": "/manifestos/euro/2014/pes/manifesto.png",
                "party": "pes"
            }
        ]
    },
    "2019": {
        "date": "23 May 2019",
        "turnout": 36.9,
        "control": "brexit",
        "summary": "Held during a period of intense parliamentary deadlock over the implementation of the Brexit referendum, the election saw the dramatic rise of the newly-formed Brexit Party, led by Nigel Farage. The Brexit Party won 29 seats and topped the poll. The Liberal Democrats had a major resurgence, taking second place with 16 seats on a strong anti-Brexit message. Labour (10) and the Conservatives (4) both suffered severe losses.",
        "highlights": [
            "Nigel Farage's new Brexit Party wins 29 seats on 32% Great Britain vote share",
            "Liberal Democrats surge to second place with 16 seats under Vince Cable",
            "Green Party has its best-ever result, winning 7 seats on 12% vote share",
            "Conservatives drop to just 4 seats (9% vote share) — their worst national result",
            "Alliance Party in NI wins its first-ever seat (Naomi Long) overtaking the UUP"
        ],
        "totalSeats": 73,
        "majorityThreshold": 37,
        "system": "Regional list PR (GB) & STV (NI)",
        "results": [
            {"party": "brexit", "seats": 29, "pct": 31.6},
            {"party": "libdem", "seats": 16, "pct": 20.3},
            {"party": "labour", "seats": 10, "pct": 14.1},
            {"party": "green", "seats": 7, "pct": 12.1},
            {"party": "conservative", "seats": 4, "pct": 9.1},
            {"party": "snp", "seats": 3, "pct": 3.6},
            {"party": "plaid", "seats": 1, "pct": 1.0},
            {"party": "alliance", "seats": 1, "pct": 18.5},
            {"party": "sinnfein", "seats": 1, "pct": 22.2},
            {"party": "dup", "seats": 1, "pct": 21.8},
            {"party": "uup", "seats": 0, "pct": 9.3},
            {"party": "sdlp", "seats": 0, "pct": 13.7}
        ],
        "manifestos": [
            {
                "title": "Alliance Party European Manifesto 2019",
                "pdf": "/manifestos/euro/2019/alliance/manifesto.pdf",
                "cover": "/manifestos/euro/2019/alliance/manifesto.png",
                "party": "alliance"
            },
            {
                "title": "Animal Politics EU European Manifesto 2019",
                "pdf": "/manifestos/euro/2019/animalpolitics/manifesto.pdf",
                "cover": "/manifestos/euro/2019/animalpolitics/manifesto.png",
                "party": "animalpolitics"
            },
            {
                "title": "Change UK European Manifesto 2019",
                "pdf": "/manifestos/euro/2019/changeuk/manifesto.pdf",
                "cover": "/manifestos/euro/2019/changeuk/manifesto.png",
                "party": "changeuk"
            },
            {
                "title": "Green Party European Manifesto 2019",
                "pdf": "/manifestos/euro/2019/green/manifesto.pdf",
                "cover": "/manifestos/euro/2019/green/manifesto.png",
                "party": "green"
            },
            {
                "title": "Labour European Manifesto 2019",
                "pdf": "/manifestos/euro/2019/labour/manifesto.pdf",
                "cover": "/manifestos/euro/2019/labour/manifesto.png",
                "party": "labour"
            },
            {
                "title": "Labour European Manifesto 2019 (Transforming Britain and Europe)",
                "pdf": "/manifestos/euro/2019/labour/manifesto-transforming.pdf",
                "cover": "/manifestos/euro/2019/labour/manifesto-transforming.png",
                "party": "labour"
            },
            {
                "title": "Liberal Democrats European Manifesto 2019",
                "pdf": "/manifestos/euro/2019/libdem/manifesto.pdf",
                "cover": "/manifestos/euro/2019/libdem/manifesto.png",
                "party": "libdem"
            },
            {
                "title": "Plaid Cymru European Manifesto 2019",
                "pdf": "/manifestos/euro/2019/plaid/manifesto.pdf",
                "cover": "/manifestos/euro/2019/plaid/manifesto.png",
                "party": "plaid"
            },
            {
                "title": "SNP European Manifesto 2019",
                "pdf": "/manifestos/euro/2019/snp/manifesto.pdf",
                "cover": "/manifestos/euro/2019/snp/manifesto.png",
                "party": "snp"
            },
            {
                "title": "Scottish Greens European Manifesto 2019",
                "pdf": "/manifestos/euro/2019/scottishgrn/manifesto.pdf",
                "cover": "/manifestos/euro/2019/scottishgrn/manifesto.png",
                "party": "scottishgrn"
            },
            {
                "title": "Sinn Féin European Manifesto 2019",
                "pdf": "/manifestos/euro/2019/sinnfein/manifesto.pdf",
                "cover": "/manifestos/euro/2019/sinnfein/manifesto.png",
                "party": "sinnfein"
            },
            {
                "title": "English Democrats European Manifesto 2019",
                "pdf": "/manifestos/euro/2019/englishdemocrats/manifesto.pdf",
                "cover": "/manifestos/euro/2019/englishdemocrats/manifesto.png",
                "party": "englishdemocrats"
            },
            {
                "title": "UKIP European Manifesto 2019",
                "pdf": "/manifestos/euro/2019/ukip/manifesto.pdf",
                "cover": "/manifestos/euro/2019/ukip/manifesto.png",
                "party": "ukip"
            },
            {
                "title": "UUP European Manifesto 2019",
                "pdf": "/manifestos/euro/2019/uup/manifesto.pdf",
                "cover": "/manifestos/euro/2019/uup/manifesto.png",
                "party": "uup"
            },
            {
                "title": "Women's Equality Party European Manifesto 2019",
                "pdf": "/manifestos/euro/2019/wep/manifesto.pdf",
                "cover": "/manifestos/euro/2019/wep/manifesto.png",
                "party": "wep"
            },
            {
                "title": "PES European Manifesto 2019",
                "pdf": "/manifestos/euro/2019/pes/manifesto.pdf",
                "cover": "/manifestos/euro/2019/pes/manifesto.png",
                "party": "pes"
            }
        ]
    }
}

def build_files():
    for year, data in ELECTIONS_DATA.items():
        filepath = os.path.join(OUT_DIR, f"{year}.json")
        out_data = {
            "id": year,
            "year": int(year),
            "displayYear": year,
            "date": data["date"],
            "title": f"{year} European Parliament election",
            "turnout": data["turnout"],
            "control": data["control"],
            "firstMinister": None,
            "majority": False,
            "summary": data["summary"],
            "highlights": data["highlights"],
            "parliament": {
                "totalSeats": data["totalSeats"],
                "majorityThreshold": data["majorityThreshold"],
                "system": data["system"],
                "results": data["results"]
            },
            "sources": [
                {
                    "label": "House of Commons Library — UK Election Statistics: 1918-2021",
                    "url": "https://commonslibrary.parliament.uk/research-briefings/cbp-7529/"
                }
            ],
            "body": "euro",
            "manifestos": data["manifestos"]
        }
        
        with open(filepath, "w", encoding="utf-8") as out:
            json.dump(out_data, out, indent=2, ensure_ascii=False)
        print(f"Wrote {filepath}")

if __name__ == "__main__":
    build_files()
