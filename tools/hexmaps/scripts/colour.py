#!/usr/bin/env python3
"""
colour.py — Join election results to a packed hexjson and add party colour.

Usage:
    python3 colour.py --year 1983            # uses output/1983.hexjson
    python3 colour.py --year 1974 --election 1974F
    python3 colour.py --year 2010

Outputs:
    output/<year>.hexjson  (updated in-place with colour + party fields)
    output/<year>_join_report.txt  (which seats matched / didn't)

Key decisions:
- Name normalisation: NFKD accent strip, lowercase, & → and, -/. → space, strip punct,
  collapse spaces.
- Compass expansion: N→north, NE→north east, etc. as whole-word substitutions.
- Five-tier lookup: exact → expanded → crosswalk → sorted-words → expanded-suffix.
- Sorted-word fallback handles prefix/suffix reordering (Aberdeenshire W → West Aberdeenshire).
- Suffix fallback handles county-prefixed old CSV names (Glamorganshire Aberavon → Aberavon).
- Crosswalk handles typos in hexjson/CSV and multi-year name form differences.
  Crosswalk values may be a list; all alternatives are tried in order.
- Richmond (A)/(B) pairs disambiguated by r-coord (lower r = further north = Yorkshire).
- Winner determined by highest non-blank share column.
- natSW → SNP (Scotland) or Plaid (Wales) based on region.
- NI 1945–1970: CSV usually has votes in con → colour Conservative (UUP whip era).
- NI 1974+: oth-only bucket → look up actual winner from ni_results.json (CAIN/Parliament data).
- Speaker seats: looked up from speaker_seats.json.
- lib/lib_share: Liberal (pre-1983), Alliance (1983/87), Liberal Democrats (1992+).
"""

import csv
import json
import re
import unicodedata
import argparse
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
REFERENCE = BASE / "reference"
OUTPUT = BASE / "output"

CSV_PATH = REFERENCE / "1918-2019election_results.csv"
CSV_2024_PATH = REFERENCE / "HoC-GE2024-results-by-constituency.csv"

PARTY_2024_MAP = {
    "Lab":   "Labour",
    "Con":   "Conservative",
    "LD":    "Liberal Democrats",
    "SNP":   "SNP",
    "PC":    "Plaid Cymru",
    "RUK":   "Reform UK",
    "Green": "Green",
    "DUP":   "DUP",
    "SF":    "Sinn Féin",
    "SDLP":  "SDLP",
    "UUP":   "UUP",
    "APNI":  "Alliance NI",
    "TUV":   "TUV",
    "Ind":   "Independent",
    "Spk":   "Speaker",
}

YEAR_TO_CSV_ELECTION = {
    1945: "1945", 1950: "1950", 1951: "1951",
    1955: "1955", 1959: "1959", 1964: "1964", 1966: "1966",
    1970: "1970",
    1974:  "1974F",
    19741: "1974O",   # October 1974 — same boundaries as Feb 1974
    1979: "1979",
    1983: "1983", 1987: "1987", 1992: "1992",
    1997: "1997", 2001: "2001", 2005: "2005",
    2010: "2010", 2015: "2015", 2017: "2017", 2019: "2019",
    2024: "2024",
}

REPO_ROOT = Path(__file__).resolve().parents[3]
_DATA = REPO_ROOT / "data"


def load_party_colours() -> dict:
    """Build hexmap lookup from shared JSON (slug palette + display aliases + overrides)."""
    slugs = json.loads((_DATA / "party-colours.json").read_text(encoding="utf-8"))
    aliases = json.loads((_DATA / "party-colour-aliases.json").read_text(encoding="utf-8"))
    overrides = json.loads((_DATA / "party-colour-overrides.json").read_text(encoding="utf-8"))
    colours = dict(slugs)
    for name, slug in aliases.items():
        colours[name] = slugs.get(slug, slugs.get("others", "#6b7280"))
    colours.update(overrides)
    return colours


PARTY_COLOURS = load_party_colours()


# Crosswalk: expanded+normalised hex name → expanded+normalised CSV name (or list of fallbacks).
# Fires only after direct/expansion/sorted-words lookups all fail.
# List values are tried in order; first match wins.
CROSSWALK = {
    # 2010 boundary (2010, 2015, 2017, 2019) — typos and name differences
    "aidrie and shotts":            "airdrie and shotts",
    "canbridgeshire south east":    "south east cambridgeshire",
    "great grimsbby":               "great grimsby",
    "kilmarnock and loudon":        "kilmarnock and loudoun",
    "morcambe and lunesdale":       "morecambe and lunesdale",
    "northamapton south":           "northampton south",
    "suufolk west":                 "west suffolk",
    # Hull: 2010+ CSV uses 'Kingston Upon Hull'; 1974F CSV uses plain 'Hull'
    "hull east":                    "kingston upon hull east",
    "hull north":                   "kingston upon hull north",
    "hull west and hessle":         "kingston upon hull west and hessle",
    "kingston upon hull central":   "hull central",
    "kingston upon hull east":      "hull east",
    "kingston upon hull west":      "hull west",
    # Richmond: coord-based disambiguation sets norm to 'richmond yorkshire'/'richmond surrey'
    # then these crosswalks handle years with different CSV forms
    "richmond yorkshire":           "yorkshire north riding richmond",      # 1945/1950 county-prefix form
    "richmond surrey":              ["richmond upon thames", "richmond"],   # 1974F then 1950 plain
    "richmond":                     "richmond yorkshire",                   # unambiguous hex 'Richmond' = Yorks
    # 1955 boundary (1955, 1959, 1964, 1966, 1970) — typos and older forms
    "cities of london and westmister": "cities of london and westminster",
    "flint east":                   "east flintshire",
    "flint west":                   "west flintshire",
    "holborn and st pancras south": "holborn and st pancras",
    "kirkcaldy":                    ["kirkcaldy burghs", "kirkaldy"],  # 1955 burghs, 1974F typo
    "leicester south east":         "leicestersouth east",
    "leicester south west":         "leicestersouth west",
    "llanelly":                     "llanelli",
    "londonderry":                  "londonderry county",
    "mansfiield":                   "mansfield",
    "middleton and prestwich":      "middleton and prestwick",
    "newcastle upon tyne west":     "newcastle upontyne west",
    "orkney and shetland":          "orkney and zetland",
    "penrith and the border":       "penrith and the borders",
    "portsmouth langstone":         "portsmouth langston",
    "saffron walden":               "saffron waldon",
    "southampton itchen":           "southamptonitchen",
    "wolverhamton north east":      "wolverhampton north east",
    "wolverhamton south west":      "wolverhampton south west",
    # 1974 boundary (1974, 1979)
    "ashton under line":            "ashton under lyne",
    "banff":                        "banffshire",
    "bethnal green and bow":        ["bethnall green and bow", "bethnal green"],
    "birmingha selly oak":          "birmingham selly oak",
    "bishop auckland":              "bishop aukland",
    "city of chester":              "chester",
    "city of london and westmister south": ["city of london and westminster south",
                                            "cities of london and westminster"],
    "gasgow shettleston":           "glasgow shettleston",
    "montgomery":                   "montgomeryshire",
    "nottinghsm west":              "nottingham west",
    "oxon mid":                     "oxfordshire mid",
    "royal tunbridge wells":        "tunbridge wells",
    "wanstead and woodford":        "wanstead and woodfod",
    # 1983 boundary (1983, 1987, 1992)
    "birkendhead":                  "birkenhead",
    "chertsey and walton":          "chertsy and walton",
    "gllingham":                    "gillingham",
    "sheffield hillborough":        "sheffield hillsborough",
    "wolverhmapton north east":     "wolverhampton north east",
    # 1997 boundary (1997, 2001, 2005)
    "sheffiled brightside":         "sheffield brightside",
    "sheffiled central":            "sheffield central",
    "sheffiled heeley":             "sheffield heeley",
    "southhampton itchin":          "southampton itchen",
    # 1945/1950 pre-redistribution: shire suffixes, county prefixes, District of Burghs
    "abrerdeenshire east":          "aberdeenshire east",                   # hex typo (1950)
    "aberdeenshire central":        "aberdeenshire and kincardineshire central",
    "aberdeenshire east":           "aberdeenshire and kincardineshire eastern",  # 1945 county form
    "angus north and mearns":       "angus and kincardinshire north angus and mearns",
    "angus south":                  "angus and kincardinshire south angus",
    "ayr district":                 "ayr district of burghs",
    "ayrshire central":             "ayrshire and bute central ayrshire",
    "ayrshire south":               "ayrshire and bute south ayrshire",
    "bermondsey west":              "bermondsey west bermondsey",
    "berwick and east lothian":     "berwickshire and east lothian",
    "berwick and haddington":       "berwickshire and haddingtonshire",
    "birmingham handsworth":        "birmingham hansworth",                 # CSV typo (1950)
    "birmingham sparkbrook":        "birmingham sparbrook",                 # CSV typo (1950)
    "birmingham stechford":         "birmingham strechford",                # CSV typo (1950)
    "birmingham west":              "birmingham west birmingham",
    "bolsover":                     "derbyshire bolsolver",                 # CSV typo (1950)
    "brecon and radnor":            "breconshire and radnorshire",
    "bute and ayrshire north":      ["ayrshire and bute bute and north ayrshire",
                                     "ayrshire and bute bute and northern"],
    "caernarvon":                   ["caernarvonshire caernarvon", "caernarvonshire"],
    "caernarvon district":          "caernarvon district of boroughs",
    "cardigan":                     "cardiganshire",
    "city of london 2":             "city of london",
    "clackmannan and east stirlingshire": ["stirlingshire and clackmannanshire clackmannan and east stirlingshire",
                                           "stirlingshire and clackmannanshire clackmannan and eastern"],
    "dumbarton district":           "dumbarton district of burghs",
    "dumfries":                     "dumfriesshire",
    "dunfermline district":         ["dunfermline district of burghs", "dunfermline burghs"],
    "flint":                        "flintshire",
    "forfar":                       "forfarshire",
    "fylde north":                  "lancashire north fylde",
    "fylde south":                  "lancashire south fylde",
    "glagow pollok":                "glasgow pollok",                       # hex typo (1950)
    "kincardine and aberdeenshire west": "aberdeenshire and kincardineshire kincardine and western",
    "kingston upon hull cenrtral":  "kingston upon hull central",           # hex typo (1950)
    "kinross and west perthshire":  ["perthshire and kinross shire kinross and west perthshire",
                                     "perthshire and kinross shire kinross and western"],
    "kirkcaldy district":           ["kirkcaldy district of burghs", "kirkcaldy burghs"],
    "leomisnter":                   "leominster",                           # hex typo (1945)
    "linlithgow":                   "linlithgowshire",
    "merioneth":                    "merionethshire",
    "merthyr tyfil aberdare":       "merthyr tydfil aberdare",              # hex typo (1945)
    "middlesbrough east":           "middlesborough east",                  # CSV typo (1950)
    "midlothian and peebles":       "midlothian and peeblesshire",
    "midlothian north":             "midlothian and peeblesshire northern",
    "montrose district":            "montrose district of burghs",
    "moray and nairn":              "moray and nairnshire",
    "morecambe and lonsdale":       "lancashire morecombe and lonsdale",    # CSV typo (1950)
    "northamptonshire south":       "northamptonshire and the soke of peterborough south",
    "peebles and midlothian south": "midlothian and peeblesshire peebles and southern",
    "pembroke":                     "pembrokeshire",
    "ponterfract":                  "pontefract",                           # hex typo (1945)
    "poplar south":                 "poplar south poplar",
    "roxburgh and selkirk":         "roxburghshire and selkirkshire",
    "stirling and falkirk":         "stirling and falkirk district of burghs",
    "stirling and falkirk district": "stirling and falkirk district of burghs",
    "stirlingshire west":           ["stirlingshire and clackmannanshire western",
                                     "stirlingshire and clackmannanshire west stirlingshire"],
    "stoke on tent stoke":          "stoke on trent stoke",                 # hex typo (1945)
    "westhoughton":                 "lancashire west houghton",
    "bridgwater":                   "somerset bridgewater",                 # CSV spelling differs (1950)
    # 1979: constituency name changes between 1974F and 1979 (same 1974 boundary)
    "aldridge brownhills":          "aldridge brownhill",                   # CSV missing 's' (1979)
    "bexleyheath":                  "bexley heath",
    "christchurch and lymington":   "christchurch",
    "cleveland and whitby":         "cleveland",
    "derbyshire south east":        "south east derbyshie",                 # CSV typo (1979)
    "dover and deal":               "dover",
    "epping forest":                "epping",
    "epsom and ewell":              "epsom",
    "hartlepool":                   "the hartlepools",
    "hertford and stevenage":       "hertford stevenage",
    "horsham and crawley":          "horsham",
    "liverpool scotland exchange":  "liverpool scotland",
    "middlesbrough":                "middlesborough",                        # CSV typo (1979)
    "pontefract and castleford":    "pontefract",
    "scarborough":                  "scarborough and whitby",
    "stratford on avon":            "stratford",
}

# Manual overrides: seats absent from the results CSV, sourced separately.
# Keyed by (election_key, hex_name). Applied after the main join loop.
MANUAL_OVERRIDES = {
    # Derby South not listed in 1918-2019election_results.csv for either year.
    # Results from api.parliament.uk/uk-general-elections/elections/15044 (1950)
    # and /15669 (1951): Labour hold, Philip Noel-Baker.
    ("1950", "Derby S"): ("Labour",    "#E4003B"),
    ("1951", "Derby S"): ("Labour",    "#E4003B"),
    # Brighton Pavilion 2010-2019: Caroline Lucas (Green) won each time.
    # The CSV lumps all "other" party votes into oth_share so her wins appear as "Other".
    ("2010", "Brighton Pavilion"): ("Green",  "#02A95B"),
    ("2015", "Brighton Pavilion"): ("Green",  "#02A95B"),
    ("2017", "Brighton Pavilion"): ("Green",  "#02A95B"),
    ("2019", "Brighton Pavilion"): ("Green",  "#02A95B"),
    # Clacton 2015: Douglas Carswell (UKIP), the only UKIP seat ever won.
    # UKIP votes are in the oth column, inflating oth_share above con_share.
    ("2015", "Clacton"):           ("UKIP",   "#6D3177"),
    # Hartlepool 2015: Iain Wright (Labour) won with 35.6%.
    # UKIP's 24.7% + minor parties inflate oth_share to 41.5%, exceeding lab_share.
    ("2015", "Hartlepool"):        ("Labour", "#E4003B"),
    # --- 1945 ---
    # Communist Party of Great Britain
    ("1945", "Fife W"):            ("Communist",    "#EF0000"),  # Willie Gallacher
    ("1945", "Stepney Mile End"):  ("Communist",    "#EF0000"),  # Phil Piratin
    # Common Wealth Party
    ("1945", "Chelmsford"):        ("Common Wealth","#7A1F2E"),  # Ernest Millington
    ("1945", "Bridgwater"):        ("Independent",  "#DCDCDC"),  # Vernon Bartlett (Progressive)
    # Independent Labour Party (last ILP MPs; party dissolved 1946)
    ("1945", "Glasgow Bridgeton"): ("ILP",          "#BF0000"),  # James Maxton
    ("1945", "Glasgow Camlachie"): ("ILP",          "#BF0000"),  # Campbell Stephen
    ("1945", "Glasgow Shettleston"):("ILP",         "#BF0000"),  # John McGovern
    # Northern Ireland seats with all-zero CSV data or oth_share wins
    ("1945", "Belfast W"):         ("Irish Labour", "#E4003B"),  # Jack Beattie, NILP
    ("1945", "Armagh"):            ("Nationalist",  "#009A44"),  # James McSparran, APL
    ("1945", "Liverpool Scotland"):("Nationalist",  "#009A44"),  # T.J. Burke, Irish Nationalist
    # Labour seats with all-zero CSV data
    ("1945", "Rhondda W"):         ("Labour",       "#E4003B"),  # D.H. Thomas; all-zero CSV row
    # Rhondda East: Labour (Mainwaring) won; oth_share inflated by Communist+PC votes in oth bucket
    ("1945", "Rhondda E"):         ("Labour",       "#E4003B"),  # William Mainwaring; data artefact
    # National Liberal seats (Liberal Nationals who supported National Government; oth_share in CSV)
    ("1945", "Denbigh"):           ("National Liberal", "#C8B400"),  # Henry Morris-Jones
    ("1945", "Dumfries"):          ("National Liberal", "#C8B400"),  # Niall Macpherson
    ("1945", "Eddisbury"):         ("National Liberal", "#C8B400"),  # Sir John Barlow
    ("1945", "Fife E"):            ("National Liberal", "#C8B400"),  # James Henderson-Stewart
    ("1945", "Harwich"):           ("National Liberal", "#C8B400"),  # Stanley Holmes
    ("1945", "Holland with Boston"):("National Liberal","#C8B400"),  # Herbert Butcher
    ("1945", "Huntingdonshire"):   ("National Liberal", "#C8B400"),  # David Renton
    ("1945", "Montrose District"): ("National Liberal", "#C8B400"),  # John Maclay
    ("1945", "Norfolk E"):         ("National Liberal", "#C8B400"),  # Frank Medlicott
    ("1945", "South Molton"):      ("National Liberal", "#C8B400"),  # George Lambert (2nd Viscount)
    ("1945", "St Ives"):           ("National Liberal", "#C8B400"),  # N.A. Beechman
    # Independent Liberal seats (broke from National Liberal group; closer to Liberal Party)
    ("1945", "Inverness"):         ("Liberal",      "#FFD700"),  # Murdoch Macdonald (Ind. Liberal)
    ("1945", "Ross & Cromarty"):   ("Liberal",      "#FFD700"),  # John MacLeod (Ind. Liberal)
    # Independent seats
    ("1945", "Cheltenham"):        ("Independent",  "#DCDCDC"),  # Daniel Lipson (National Independent)
    ("1945", "Galloway"):          ("Independent",  "#DCDCDC"),  # John Mackie (Ind. Unionist; denied official nomination)
    ("1945", "Grantham"):          ("Independent",  "#DCDCDC"),  # Denis Kendall (no party affiliation)
    ("1945", "Rugby"):             ("Independent",  "#DCDCDC"),  # W.J. Brown (trade unionist)
    # Independent Labour: Denis Pritt (expelled from Labour 1940; ran as Independent Labour)
    ("1945", "Hammersmith N"):     ("Independent Labour", "#E4003B"),  # D.N. Pritt
    # --- 1950 ---
    ("1950", "Antrim N"):          ("Conservative", "#0087DC"),  # Sir Henry Mulholland, UUP; all-zero CSV
    ("1950", "Fermanagh & S Tyrone"):("Nationalist","#009A44"),  # Cahir Healy, APL
    ("1950", "Ulster Mid"):        ("Nationalist",  "#009A44"),  # Anthony Mulvey, APL
    ("1950", "Belfast W"):         ("Irish Labour", "#E4003B"),  # Jack Beattie, NILP (won again)
    # --- 1951 ---
    ("1951", "Antrim N"):          ("Conservative", "#0087DC"),  # UUP; oth_share CSV error
    ("1951", "Belfast W"):         ("Irish Labour", "#E4003B"),  # Jack Beattie, NILP
    ("1951", "Fermanagh & S Tyrone"):("Nationalist","#009A44"),  # APL
    ("1951", "Ulster Mid"):        ("Conservative", "#0087DC"),  # UUP; oth_share CSV error
    ("1951", "Londonderry"):       ("Conservative", "#0087DC"),  # UUP; oth_share CSV error
    ("1951", "Glasgow Shettleston"):("ILP",         "#BF0000"),  # John McGovern (still ILP 1951)
    ("1951", "Merthyr Tydfil"):    ("Independent Labour","#E4003B"),  # S.O. Davies, deselected
    ("1951", "Ebbw Vale"):         ("Labour",       "#E4003B"),  # Aneurin Bevan; all-zero CSV row
    # --- 1955 ---
    ("1955", "Fermanagh & S Tyrone"):("Sinn Féin",  "#326760"),  # Philip Clarke (abstentionist, won from prison)
    ("1955", "Ulster Mid"):        ("Sinn Féin",    "#326760"),  # Tom Mitchell (abstentionist, won from prison)
    # --- 1966 ---
    ("1966", "Belfast W"):         ("Republican Labour","#CC0000"),  # Gerry Fitt
    # --- 1970 ---
    ("1970", "Antrim N"):          ("Protestant Unionist","#003366"),  # Ian Paisley (pre-DUP)
    ("1970", "Belfast W"):         ("Republican Labour","#CC0000"),    # Gerry Fitt
    ("1970", "Fermanagh & S Tyrone"):("Nationalist","#009A44"),  # Frank McManus, Unity
    ("1970", "Ulster Mid"):        ("Nationalist",  "#009A44"),  # Bernadette Devlin, People's Democracy
    ("1970", "Merthyr Tydfil"):    ("Independent Labour","#E4003B"),  # S.O. Davies (deselected, won again)
    # --- Feb 1974 ---
    ("1974F", "Blyth"):            ("Independent Labour","#E4003B"),  # Eddie Milne (deselected, won)
    ("1974F", "Lincoln"):          ("Democratic Labour","#B05080"),   # Dick Taverne (Lab rebel, won as Democratic Labour)
    # Bodmin: Paul Tyler (Liberal) won by 9 votes (20283 vs 20274 Con).
    # Both round to 0.44 share; tie-break incorrectly favours "con" bucket.
    ("1974F", "Bodmin"):           ("Liberal",      "#FFD700"),
    # --- Oct 1974 ---
    # Dunbartonshire East: SNP's Margaret Bain won by 22 votes (15551 vs 15529 Con).
    # Both round to 0.312 share; tie-break in max() incorrectly favours "con" bucket.
    ("1974O", "Dunbartonshire E"): ("SNP",          "#FDF38E"),
    # --- 1997 ---
    # Martin Bell (Independent anti-sleaze candidate, Tatton vs Neil Hamilton)
    ("1997", "Tatton"):            ("Independent",  "#DCDCDC"),
    # --- 2001 ---
    # Richard Taylor, Health Concern (KHHC — Kidderminster Hospital)
    ("2001", "Wyre Forest"):       ("Independent",  "#DCDCDC"),
    # --- 2005 ---
    ("2005", "Bethnal Green & Bow"):("Respect",     "#FF4500"),  # George Galloway
    ("2005", "Blaenau Gwent"):     ("Independent",  "#DCDCDC"),  # Peter Law (Labour rebel)
    ("2005", "Wyre Forest"):       ("Independent",  "#DCDCDC"),  # Richard Taylor (KHHC, 2nd term)
}

_RICHMOND_AMBIG_RE = re.compile(r"^Richmond \([A-Z]\)$")
_RICHMOND_YORKSHIRE_TARGETS = [
    "richmond yorkshire",
    "yorkshire north riding richmond",
    "richmond",
]
_RICHMOND_SURREY_TARGETS = [
    "richmond surrey",
    "richmond upon thames",
    "richmond",
]


def liberal_party_for_year(year):
    # 19741 = October 1974 (same era as 1974F = February 1974)
    era = 1974 if year == 19741 else year
    if era <= 1987:
        return "Liberal" if era < 1983 else "Alliance"
    return "Liberal Democrats"


# ---------------------------------------------------------------------------
# Name normalisation
# ---------------------------------------------------------------------------

_NORMALIZE_RE = re.compile(r"[^a-z0-9 ]")
_SPACE_RE = re.compile(r"\s+")
_COMPASS = [
    ("nw", "north west"), ("ne", "north east"),
    ("sw", "south west"), ("se", "south east"),
    ("n", "north"), ("s", "south"), ("e", "east"), ("w", "west"),
]


def normalise(name: str) -> str:
    """NFKD accent-strip, lowercase, &/-/. → space, strip non-alphanumeric, collapse whitespace."""
    s = unicodedata.normalize("NFKD", name.lower().strip())
    s = s.replace("&", " and ").replace("/", " ").replace("-", " ").replace(".", " ").replace(",", " ")
    s = _NORMALIZE_RE.sub("", s)
    s = _SPACE_RE.sub(" ", s).strip()
    return s


def expand_compass(s: str) -> str:
    for abbr, full in _COMPASS:
        s = re.sub(r"\b" + abbr + r"\b", full, s)
    return _SPACE_RE.sub(" ", s).strip()


_COLLAPSE = [
    ("western", "west"), ("northern", "north"),
    ("eastern", "east"), ("southern", "south"),
]


def collapse_directionals(s: str) -> str:
    """Convert '-ern' directional forms to short form: 'eastern'→'east', etc."""
    for long, short in _COLLAPSE:
        s = re.sub(r"\b" + long + r"\b", short, s)
    return _SPACE_RE.sub(" ", s).strip()


def sorted_words(s: str) -> str:
    return " ".join(sorted(s.split()))


# ---------------------------------------------------------------------------
# NI results lookup
# ---------------------------------------------------------------------------

def load_ni_results():
    with open(REFERENCE / "ni_results.json") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Speaker lookup
# ---------------------------------------------------------------------------

def load_speaker_seats():
    with open(REFERENCE / "speaker_seats.json") as f:
        raw = json.load(f)
    speaker_map = {}
    party_not_speaker = {"1951", "1983", "1992"}
    for election_key, info in raw.items():
        if election_key in party_not_speaker:
            continue
        seat = info.get("seat", "")
        if seat:
            speaker_map[election_key] = expand_compass(normalise(seat))
    return speaker_map


# ---------------------------------------------------------------------------
# CSV loading
# ---------------------------------------------------------------------------

def load_results(election_key: str):
    """
    Return five lookup dicts for the requested election:
      by_norm       — {normalised_name: row}
      by_expanded   — {expand_compass(normalised_name): row}
      by_collapsed  — {collapse_directionals(expanded_name): row}
      by_sorted     — {sorted_words(expanded_name): row}
      by_exp_suffix — {suffix_of_expanded_name: row}  (unambiguous suffixes only)
    """
    by_norm: dict = {}
    by_expanded: dict = {}
    by_collapsed: dict = {}
    by_sorted: dict = {}
    suffix_count: Counter = Counter()
    suffix_rows: dict = {}

    with open(CSV_PATH, encoding="latin-1", newline="") as f:
        reader = csv.DictReader(f)
        reader.fieldnames = [h.strip() for h in reader.fieldnames]
        for row in reader:
            row = {k: v.strip() for k, v in row.items()}
            if row.get("election") != election_key:
                continue
            name = row.get("constituency_name", "")
            if not name:
                continue
            norm = normalise(name)
            exp = expand_compass(norm)
            col = collapse_directionals(exp)
            srt = sorted_words(exp)
            by_norm[norm] = row
            by_expanded[exp] = row
            by_collapsed[col] = row
            by_sorted[srt] = row
            words = exp.split()
            for i in range(len(words)):
                suffix = " ".join(words[i:])
                suffix_count[suffix] += 1
                suffix_rows[suffix] = row

    by_exp_suffix = {s: r for s, r in suffix_rows.items() if suffix_count[s] == 1}
    return by_norm, by_expanded, by_collapsed, by_sorted, by_exp_suffix


def load_results_2024():
    """Return lookup dicts for 2024 from the HoC constituency-level CSV.
    Each row dict has 'first_party' and 'country/region' instead of share columns.
    """
    by_norm: dict = {}
    by_expanded: dict = {}
    by_collapsed: dict = {}
    by_sorted: dict = {}
    suffix_count: Counter = Counter()
    suffix_rows: dict = {}

    with open(CSV_2024_PATH, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row = {k: v.strip() for k, v in row.items()}
            name = row.get("Constituency name", "")
            if not name:
                continue
            unified = {
                "constituency_name": name,
                "first_party": row.get("First party", ""),
                "country/region": row.get("Country name", ""),
            }
            norm = normalise(name)
            exp = expand_compass(norm)
            col = collapse_directionals(exp)
            srt = sorted_words(exp)
            by_norm[norm] = unified
            by_expanded[exp] = unified
            by_collapsed[col] = unified
            by_sorted[srt] = unified
            words = exp.split()
            for i in range(len(words)):
                suffix = " ".join(words[i:])
                suffix_count[suffix] += 1
                suffix_rows[suffix] = unified

    by_exp_suffix = {s: r for s, r in suffix_rows.items() if suffix_count[s] == 1}
    return by_norm, by_expanded, by_collapsed, by_sorted, by_exp_suffix


# ---------------------------------------------------------------------------
# Row lookup
# ---------------------------------------------------------------------------

def _try_targets(targets, by_norm, by_expanded, by_collapsed, by_sorted, by_exp_suffix):
    """Try a list of normalised target names against all lookup dicts."""
    for t in targets:
        row = (by_norm.get(t) or by_expanded.get(t) or
               by_sorted.get(sorted_words(t)) or by_exp_suffix.get(t))
        if row is not None:
            return row
    return None


def _lookup_row(hex_norm, by_norm, by_expanded, by_collapsed, by_sorted, by_exp_suffix):
    """Six-tier lookup: exact → expanded → collapsed → crosswalk → sorted-words → suffix."""
    row = by_norm.get(hex_norm)
    if row is not None:
        return row

    exp = expand_compass(hex_norm)

    row = by_expanded.get(exp)
    if row is not None:
        return row

    row = by_collapsed.get(collapse_directionals(exp))
    if row is not None:
        return row

    cw = CROSSWALK.get(exp)
    if cw is not None:
        cw_targets = [cw] if isinstance(cw, str) else cw
        row = _try_targets(cw_targets, by_norm, by_expanded, by_collapsed, by_sorted, by_exp_suffix)
        if row is not None:
            return row

    row = by_sorted.get(sorted_words(exp))
    if row is not None:
        return row

    return by_exp_suffix.get(exp)


# ---------------------------------------------------------------------------
# Winner + colour determination
# ---------------------------------------------------------------------------

def determine_winner(row, year, region, speaker_norm_name, hex_norm_name, ni_election_data=None):
    if speaker_norm_name:
        hex_exp = expand_compass(hex_norm_name)
        cw = CROSSWALK.get(hex_exp)
        cw_targets = ([cw] if isinstance(cw, str) else cw) if cw else []
        is_speaker = (
            hex_exp == speaker_norm_name or
            any(t == speaker_norm_name for t in cw_targets)
        )
    else:
        is_speaker = False
    if is_speaker:
        return "Speaker", PARTY_COLOURS["Speaker"]

    # 2024 HoC format: 'first_party' abbreviation available directly
    if "first_party" in row:
        abbr = row["first_party"]
        party = PARTY_2024_MAP.get(abbr, "Other")
        colour = PARTY_COLOURS.get(party, PARTY_COLOURS["Other"])
        return party, colour

    def _share(col):
        v = row.get(col, "").strip()
        try:
            return float(v) if v else 0.0
        except ValueError:
            return 0.0

    shares = {
        "con":   _share("con_share"),
        "lib":   _share("lib_share"),
        "lab":   _share("lab_share"),
        "natSW": _share("natSW_share"),
        "oth":   _share("oth_share"),
    }

    if not any(shares.values()):
        return "Other", PARTY_COLOURS["Other"]

    winner_bucket = max(shares, key=shares.get)

    is_ni = ("northern ireland" in region.lower()) if region else False
    era = 1974 if year == 19741 else year
    if is_ni and era >= 1974 and winner_bucket == "oth":
        if ni_election_data:
            hex_exp = expand_compass(hex_norm_name)
            ni_party = ni_election_data.get(hex_exp)
            if ni_party:
                colour = PARTY_COLOURS.get(ni_party, PARTY_COLOURS["Other"])
                return ni_party, colour
        return "UUP", PARTY_COLOURS["UUP"]  # fallback if no NI data

    if winner_bucket == "con":
        return "Conservative", PARTY_COLOURS["Conservative"]
    if winner_bucket == "lab":
        return "Labour", PARTY_COLOURS["Labour"]
    if winner_bucket == "lib":
        party = liberal_party_for_year(year)
        return party, PARTY_COLOURS[party]
    if winner_bucket == "natSW":
        if "scotland" in region.lower():
            return "SNP", PARTY_COLOURS["SNP"]
        if "wales" in region.lower():
            return "Plaid Cymru", PARTY_COLOURS["Plaid Cymru"]
        return "Nationalist", "#888888"
    return "Other", PARTY_COLOURS["Other"]


# ---------------------------------------------------------------------------
# Main colouring routine
# ---------------------------------------------------------------------------

def colour_year(year, election_key=None, hexjson_path=None, verbose=True):
    def log(*args):
        if verbose:
            print(*args)

    election_key = election_key or YEAR_TO_CSV_ELECTION.get(year)
    if not election_key:
        raise ValueError(f"No CSV election key for year {year}")

    hex_path = hexjson_path or OUTPUT / f"{year}.hexjson"
    if not hex_path.exists():
        raise FileNotFoundError(f"Hexjson not found: {hex_path}. Run pack.py first.")

    log(f"=== Colouring {year} (election={election_key}) ===")

    with open(hex_path) as f:
        hexjson = json.load(f)
    hexes = hexjson["hexes"]

    if year == 2024:
        log("Loading 2024 HoC results…")
        by_norm, by_expanded, by_collapsed, by_sorted, by_exp_suffix = load_results_2024()
    else:
        log(f"Loading results for election {election_key}…")
        by_norm, by_expanded, by_collapsed, by_sorted, by_exp_suffix = load_results(election_key)
    log(f"  {len(by_norm)} constituencies loaded")

    log("Loading NI results…")
    ni_results = load_ni_results()
    ni_election_data = ni_results.get(election_key, {})
    log(f"  {len(ni_election_data)} NI constituencies for {election_key}")

    log("Loading speaker seats…")
    speaker_map = load_speaker_seats()
    speaker_norm = speaker_map.get(election_key, "")
    if speaker_norm:
        log(f"  Speaker seat: {speaker_norm!r}")

    # Disambiguate Richmond (A)/(B) pairs by r-coordinate (lower r = further north = Yorkshire)
    richmond_hexes = [(n, d) for n, d in hexes.items() if _RICHMOND_AMBIG_RE.match(n)]
    richmond_override: dict[str, list] = {}
    if len(richmond_hexes) == 2:
        richmond_hexes.sort(key=lambda x: x[1].get("r", 0))
        richmond_override[richmond_hexes[0][0]] = _RICHMOND_YORKSHIRE_TARGETS
        richmond_override[richmond_hexes[1][0]] = _RICHMOND_SURREY_TARGETS
        log(f"  Disambiguated Richmond: {richmond_hexes[0][0]} → Yorkshire, "
            f"{richmond_hexes[1][0]} → Surrey")

    # Main join loop
    matched = unmatched = 0
    unmatched_names = []

    for hex_name, hex_data in hexes.items():
        if hex_name in richmond_override:
            row = _try_targets(richmond_override[hex_name],
                               by_norm, by_expanded, by_collapsed, by_sorted, by_exp_suffix)
        else:
            hex_norm = normalise(hex_name)
            row = _lookup_row(hex_norm, by_norm, by_expanded, by_collapsed, by_sorted, by_exp_suffix)

        if row is None:
            unmatched += 1
            unmatched_names.append(hex_name)
            hex_data["colour"] = "#CCCCCC"
            hex_data["party"] = "UNMATCHED"
            continue

        hex_norm_for_speaker = normalise(hex_name)
        region = row.get("country/region", "")
        party, colour = determine_winner(row, year, region, speaker_norm, hex_norm_for_speaker, ni_election_data)
        hex_data["colour"] = colour
        hex_data["party"] = party
        matched += 1

    # Apply manual overrides for seats absent from the results CSV
    for (ek, hname), (party, colour) in MANUAL_OVERRIDES.items():
        if ek == election_key and hname in hexes:
            hexes[hname]["colour"] = colour
            hexes[hname]["party"] = party
            if hname in unmatched_names:
                unmatched_names.remove(hname)
                unmatched -= 1
                matched += 1
            log(f"  Manual override: {hname!r} → {party}")

    match_pct = 100 * matched / len(hexes) if hexes else 0
    log(f"\nMatch: {matched}/{len(hexes)} ({match_pct:.1f}%)")

    if unmatched_names:
        log(f"Unmatched ({len(unmatched_names)}):")
        for n in sorted(unmatched_names)[:30]:
            log(f"  {n!r}")
        if len(unmatched_names) > 30:
            log(f"  ... and {len(unmatched_names)-30} more")

    report_path = OUTPUT / f"{year}_join_report.txt"
    with open(report_path, "w") as f:
        f.write(f"Join report: {year} (election={election_key})\n")
        f.write(f"Matched: {matched}/{len(hexes)} ({match_pct:.1f}%)\n\n")
        if unmatched_names:
            f.write("Unmatched hex names:\n")
            for n in sorted(unmatched_names):
                f.write(f"  {n}\n")

    with open(hex_path, "w") as f:
        json.dump(hexjson, f, indent=2)

    log(f"Wrote coloured hexjson → {hex_path}")
    log(f"Wrote join report     → {report_path}")

    return matched, len(hexes), unmatched_names


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Colour a packed hexjson with election results")
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--election", default=None,
                        help="CSV election key (e.g. 1974F, 1974O). Defaults to year's primary.")
    parser.add_argument("--hexjson", type=Path, default=None)
    args = parser.parse_args()
    colour_year(args.year, election_key=args.election, hexjson_path=args.hexjson)


if __name__ == "__main__":
    main()
