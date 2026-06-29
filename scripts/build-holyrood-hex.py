#!/usr/bin/env python3
import json
import re
import sys
import urllib.request
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "data" / "cache" / "wikipedia-html"
OUT_DIR = ROOT / "data" / "hex" / "holyrood"
GRID_PATH = ROOT / "data" / "hex" / "holyrood-grid.json"

PARTY_MAP = {
    "scottish national party": "snp",
    "snp": "snp",
    "labour": "scottishlab",
    "scottish labour": "scottishlab",
    "labour co-op": "scottishlab",
    "labour co-operative": "scottishlab",
    "scottish labour co-op": "scottishlab",
    "conservative": "scottishcon",
    "scottish conservative": "scottishcon",
    "scottish conservatives": "scottishcon",
    "conservatives": "scottishcon",
    "liberal democrats": "scottishlibdem",
    "scottish liberal democrats": "scottishlibdem",
    "green": "scottishgrn",
    "scottish green party": "scottishgrn",
    "scottish greens": "scottishgrn",
    "green party": "scottishgrn",
    "reform": "reform",
    "reform uk": "reform",
    "independent": "independent",
    "independent politician": "independent",
    "independents": "independent",
    "scottish socialist": "ssp",
    "ssp": "ssp",
    "bnp": "bnp",
    "british national party": "bnp",
    "solidarity": "solidarity",
    "christian": "scottishchristian",
    "scottish christian party": "scottishchristian",
    "alba": "alba",
    "alba party": "alba",
    "all for unity": "allforunity",
    "family": "scottishfamily",
    "scottish family party": "scottishfamily",
    "libertarian": "scottishlibertarian",
    "scottish libertarian party": "scottishlibertarian",
    "ukip": "ukip",
    "uk independence party": "ukip",
    "cooperative": "cooperative",
    "co-op": "cooperative",
    "co-operative party": "cooperative",
    "independent unionist": "independent",
    "ld": "scottishlibdem",
    "con": "scottishcon",
    "lab": "scottishlab",
}

def clean_html(text):
    text = re.sub(r'<[^>]*>', '', text)
    text = text.replace('\xa0', ' ')
    text = text.replace('&nbsp;', ' ')
    return ' '.join(text.split()).strip()

def normalize_name(name):
    """Lowercase, strip parentheticals/suffixes and punctuation, spell out '&'."""
    name = clean_html(name)
    name = re.sub(r'\([^)]*\)', '', name)          # drop "(since dd/mm/yy)", "(constituency)" etc.
    name = name.replace('&', 'and')
    name = name.lower().replace('-', ' ').replace(',', ' ')
    name = re.sub(r'\s+', ' ', name).strip()
    return name


# Aliases mapping each historical / future constituency name onto the canonical
# 2011-2021 cell in data/hex/holyrood-grid.json. The 2011/2016/2021 names already
# match the grid directly, so only the 1999-2007 (Westminster 1997-boundary) names
# and the 2026 (new-boundary) names need aliasing. A value may be a canonical grid
# key (str) or an explicit (q, r) for a seat with no modern equivalent ("overflow",
# placed in a free cell near its true geography so nothing overlaps).
ALIASES = {
    # --- 1999 / 2003 / 2007 (Westminster 1997 boundaries) -> canonical ---
    "aberdeen north": "aberdeen donside",
    "aberdeen south": "aberdeen south and north kincardine",
    "gordon": "aberdeenshire east",
    "west aberdeenshire and kincardine": "aberdeenshire west",
    "livingston": "almond valley",
    "angus": "angus north and mearns",
    "north tayside": "angus south",
    "banff and buchan": "banffshire and buchan coast",
    "caithness sutherland and easter ross": "caithness sutherland and ross",
    "central fife": "mid fife and glenrothes",
    "fife central": "mid fife and glenrothes",
    "ochil": "clackmannanshire and dunblane",
    "dunfermline east": "cowdenbeath",
    "dunfermline west": "dunfermline",
    "dumfries": "dumfriesshire",
    "dundee east": "dundee city east",
    "dundee west": "dundee city west",
    "edinburgh east and musselburgh": "edinburgh eastern",
    "edinburgh north and leith": "edinburgh northern and leith",
    "edinburgh south": "edinburgh southern",
    "edinburgh west": "edinburgh western",
    "roxburgh and berwickshire": "ettrick roxburgh and berwickshire",
    "galloway and upper nithsdale": "galloway and west dumfries",
    "glasgow govan": "glasgow southside",
    "glasgow baillieston": "glasgow provan",
    "glasgow rutherglen": "rutherglen",
    "glasgow maryhill": "glasgow maryhill and springburn",
    "glasgow springburn": (1, 8),          # overflow: old Glasgow had Maryhill + Springburn separately
    "hamilton south": "hamilton larkhall and stonehouse",
    "hamilton north and bellshill": "uddingston and bellshill",
    "inverness east nairn and lochaber": "inverness and nairn",
    "kilmarnock and loudoun": "kilmarnock and irvine valley",
    "midlothian": "midlothian north and musselburgh",
    "tweeddale ettrick and lauderdale": "midlothian south tweeddale and lauderdale",
    "fife north east": "north east fife",
    "paisley south": "paisley",
    "paisley north": "renfrewshire south",
    "perth": "perthshire north",
    "west renfrewshire": "renfrewshire north and west",
    "ross skye and inverness west": "skye lochaber and badenoch",
    "western isles": "na h eileanan an iar",

    # --- 2026 (new boundaries) -> canonical ---
    "orkney islands": "orkney",
    "shetland islands": "shetland",
    "aberdeen deeside and north kincardine": "aberdeen south and north kincardine",
    "airdrie": "airdrie and shotts",
    "bathgate": "linlithgow",
    "east lothian coast and lammermuirs": "east lothian",
    "inverclyde": "greenock and inverclyde",
    "midlothian north": "midlothian north and musselburgh",
    "falkirk east and linlithgow": "falkirk east",
    "renfrewshire north and cardonald": "renfrewshire south",
    "renfrewshire west and levern valley": "renfrewshire north and west",
    "rutherglen and cambuslang": "rutherglen",
    "glasgow central": "glasgow kelvin",
    "glasgow cathcart and pollok": "glasgow cathcart",
    "glasgow baillieston and shettleston": "glasgow shettleston",
    "glasgow easterhouse and springburn": "glasgow provan",
    "glasgow kelvin and maryhill": "glasgow maryhill and springburn",
    "edinburgh eastern musselburgh and tranent": "edinburgh eastern",
    "edinburgh north eastern and leith": "edinburgh northern and leith",
    "edinburgh north western": "edinburgh western",
    "edinburgh south western": "edinburgh pentlands",
    "edinburgh northern": (6, 4),          # 2026-only seat (DDE "Edinburgh Northern" cell)
}

def get_party_id(party_str):
    party_clean = clean_html(party_str).lower().strip()
    for k, v in PARTY_MAP.items():
        if k in party_clean:
            return v
    return "others"

MEMBER_PARTY_OVERRIDES = {
    # 1999
    ("David Steel", "1999"): "scottishlibdem",
    ("Dorothy Grace Elder", "1999"): "snp",
    ("Margo MacDonald", "1999"): "snp",
    # 2003
    ("George Reid", "2003"): "snp",
    ("Brian Monteith", "2003"): "scottishcon",
    ("Campbell Martin", "2003"): "snp",
    # 2007
    ("Alex Fergusson", "2007"): "scottishcon",
    # 2011
    ("Tricia Marwick", "2011"): "snp",
    ("John Wilson", "2011"): "snp",
    ("John Finnie", "2011"): "snp",
    ("Jean Urquhart", "2011"): "snp",
    # 2016
    ("Derek Mackay", "2016"): "snp",
    ("Mark McDonald", "2016"): "snp",
    ("Andy Wightman", "2016"): "scottishgrn",
    ("Michelle Ballantyne", "2016"): "scottishcon",
    ("Ken Macintosh", "2016"): "scottishlab",
    # 2021
    ("Fergus Ewing", "2021"): "snp",
    ("John Mason", "2021"): "snp",
    ("Ash Regan", "2021"): "snp",
    ("Graham Simpson", "2021"): "scottishcon",
    ("Pam Duncan-Glancy", "2021"): "scottishlab",
    ("Jeremy Balfour", "2021"): "scottishcon",
    ("Foysol Choudhury", "2021"): "scottishlab",
    ("Alison Johnstone", "2021"): "scottishgrn",
    ("Colin Smyth", "2021"): "scottishlab",
    # 2026
    ("Kenneth Gibson", "2026"): "snp",
}

# The "Nth Scottish Parliament" Wikipedia pages list each seat's *current* member,
# so mid-term constituency by-elections contaminate the election-night result
# (the row shows a "(since dd/mm/yy)" by-election winner, sometimes from another
# party). Restore the original election winner for those seats here, keyed by
# (normalized constituency, year). Any "(since ...)" constituency row WITHOUT an
# entry here is reported as a problem by the build so it can be added.
CONSTITUENCY_RESULT_OVERRIDES = {
    # 4th Parliament (2011) by-elections during 2013-2014
    ("dunfermline", "2011"):       {"winner": "Bill Walker", "party": "snp"},          # by-elec 25/10/13 -> Cara Hilton (Lab)
    ("aberdeen donside", "2011"):  {"winner": "Brian Adam", "party": "snp"},           # by-elec 20/06/13 -> Mark McDonald (SNP)
    ("cowdenbeath", "2011"):       {"winner": "Helen Eadie", "party": "scottishlab"},  # by-elec 23/01/14 -> Alex Rowley (Lab)
    # 6th Parliament (2021) by-election during 2025
    ("hamilton larkhall and stonehouse", "2021"): {"winner": "Christina McKelvie", "party": "snp"},  # by-elec 06/06/25 -> Davy Russell (Lab)
}

class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self.current_table = []
        self.current_row = []
        self.current_cell = ""
        self.in_table = False
        self.in_tr = False
        self.in_cell = False
        self.caption = ""
        self.in_caption = False

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.in_table = True
            self.current_table = []
            self.caption = ""
        elif tag == "caption" and self.in_table:
            self.in_caption = True
        elif tag == "tr" and self.in_table:
            self.in_tr = True
            self.current_row = []
        elif tag in ("th", "td") and self.in_tr:
            self.in_cell = True
            self.current_cell = ""

    def handle_endtag(self, tag):
        if tag == "table":
            self.in_table = False
            self.tables.append((self.caption.strip(), self.current_table))
        elif tag == "caption" and self.in_caption:
            self.in_caption = False
        elif tag == "tr" and self.in_tr:
            self.in_tr = False
            self.current_table.append(self.current_row)
        elif tag in ("th", "td") and self.in_cell:
            self.in_cell = False
            self.current_row.append(self.current_cell.strip())

    def handle_data(self, data):
        if self.in_caption:
            self.caption += data
        elif self.in_cell:
            self.current_cell += data

def fetch_wikipedia_html(url, filename):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / filename
    if cache_path.exists():
        return cache_path.read_text(encoding="utf-8")
    
    print(f"Fetching {url}...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8')
    cache_path.write_text(html, encoding="utf-8")
    return html

def parse_tables(html):
    parser = TableParser()
    parser.feed(html)
    return parser.tables

def load_grid():
    """Load the canonical geographically-coherent Holyrood hex grid (odd-r),
    keyed by normalized 2011-2021 constituency names. See build-holyrood-grid.py."""
    hex_data = json.loads(GRID_PATH.read_text(encoding="utf-8"))
    return {name: (cell["q"], cell["r"]) for name, cell in hex_data["hexes"].items()}


def resolve_cell(member_for, grid):
    """Return (norm_key, (q, r)) for a constituency name, or (norm_key, None) if unmapped."""
    norm = normalize_name(member_for)
    if norm in grid:
        return norm, grid[norm]
    if norm in ALIASES:
        target = ALIASES[norm]
        if isinstance(target, tuple):
            return norm, target
        return norm, grid.get(target)
    return norm, None

def build_holyrood_hex():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    grid = load_grid()
    problems = []
    
    elections = [
        ("1999", "1st_Scottish_Parliament", "1999_holyrood.html"),
        ("2003", "2nd_Scottish_Parliament", "2003_holyrood.html"),
        ("2007", "3rd_Scottish_Parliament", "2007_holyrood.html"),
        ("2011", "4th_Scottish_Parliament", "2011_holyrood.html"),
        ("2016", "5th_Scottish_Parliament", "2016_holyrood.html"),
        ("2021", "6th_Scottish_Parliament", "2021_holyrood.html"),
        ("2026", "7th_Scottish_Parliament", "2026_holyrood.html"),
    ]
    
    for year, wiki_slug, cache_file in elections:
        url = f"https://en.wikipedia.org/wiki/{wiki_slug}"
        html = fetch_wikipedia_html(url, cache_file)
        tables = parse_tables(html)
        
        # Find the main member list table (typically rows around 130 representing 129 MSPs + header)
        member_table = None
        for idx, (caption, rows) in enumerate(tables):
            if 120 <= len(rows) <= 135:
                member_table = rows
                break
        
        if not member_table:
            # Try to find any large table
            for idx, (caption, rows) in enumerate(tables):
                if len(rows) > 100:
                    member_table = rows
                    break
        
        if not member_table:
            print(f"Error: Could not find member list table for {year} / {wiki_slug}!")
            continue
        
        print(f"Parsing {year}... Found member list table with {len(member_table)} rows.")
        
        hexes = {}
        regional_list = {}
        
        # Parse all rows (excluding header at index 0)
        for row in member_table[1:]:
            if "Constituency" in row:
                type_idx = row.index("Constituency")
                is_const = True
            elif "Regional" in row:
                type_idx = row.index("Regional")
                is_const = False
            else:
                continue
            
            # Robust extraction relative to Type cell index
            name = clean_html(row[type_idx - 3]) if type_idx >= 3 else clean_html(row[0])
            member_for = clean_html(row[type_idx - 1])
            party_str = clean_html(row[type_idx + 1])
            party_id = MEMBER_PARTY_OVERRIDES.get((name, year), get_party_id(party_str))
            
            if is_const:
                norm_const, pos = resolve_cell(member_for, grid)
                if pos is None:
                    problems.append(f"{year}: UNMAPPED '{member_for}' (norm: '{norm_const}')")
                    q, r = 0, 0
                else:
                    q, r = pos

                # Restore the election-night winner for seats that changed hands at
                # a mid-term by-election (the source page shows the current member).
                override = CONSTITUENCY_RESULT_OVERRIDES.get((norm_const, year))
                if override:
                    name = override["winner"]
                    party_id = override["party"]
                elif "(since" in member_for.replace(" ", ""):
                    problems.append(
                        f"{year}: BY-ELECTION ROW without result override: "
                        f"'{member_for}' (norm: '{norm_const}', shows '{name}') — "
                        f"add to CONSTITUENCY_RESULT_OVERRIDES"
                    )

                # Strip any "(since dd/mm/yy)" by-election suffix from the display name.
                display_name = re.sub(r'\s*\([^)]*\)', '', member_for).strip()

                # Build unique code
                code = f"holyrood-{year}-{norm_const.replace(' ', '-')}"
                hexes[code] = {
                    "n": display_name,
                    "q": q,
                    "r": r,
                    "winner": name,
                    "party": party_id
                }
            else:
                # Regional List Seat — strip "(since dd/mm/yy)" so by-election
                # replacements merge back into their parent region.
                region_name = re.sub(r'\s*\([^)]*\)', '', member_for).strip()
                if region_name not in regional_list:
                    regional_list[region_name] = []
                regional_list[region_name].append({
                    "name": name,
                    "party": party_id
                })

        # Detect overlapping constituency hexes within this election
        seen_pos = {}
        for code, cell in hexes.items():
            key = (cell["q"], cell["r"])
            if key == (0, 0):
                continue
            if key in seen_pos:
                problems.append(f"{year}: OVERLAP at {key} — '{cell['n']}' and '{seen_pos[key]}'")
            else:
                seen_pos[key] = cell["n"]

        # Format the output HexJSON document
        out_doc = {
            "layout": "odd-r",
            "hexes": hexes,
            "regional_list": []
        }
        
        # Build the regional lists section in a structured format
        # Region Name -> members list
        for reg_name, members in sorted(regional_list.items()):
            out_doc["regional_list"].append({
                "region": reg_name,
                "members": members
            })
            
        # Write to JSON file
        out_path = OUT_DIR / f"{year}.hexjson"
        out_path.write_text(json.dumps(out_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote constituency layout to {out_path} ({len(hexes)} constituency seats, {sum(len(m['members']) for m in out_doc['regional_list'])} regional list seats).")

    if problems:
        print("\n=== PROBLEMS ===", file=sys.stderr)
        for p in problems:
            print("  " + p, file=sys.stderr)
        raise SystemExit(f"\n{len(problems)} mapping problem(s) — fix ALIASES/grid and re-run.")
    print("\nAll constituencies mapped to unique cells across every election. ✓")

if __name__ == "__main__":
    build_holyrood_hex()
