import urllib.request
import re
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "data" / "cache" / "wikipedia"

PARTY_MAP = {
    "labour": "welshlab",
    "welsh labour": "welshlab",
    "labour co-op": "welshlab",
    "labour co-operative": "welshlab",
    "welsh labour and co-operative": "welshlab",
    "welsh labour co-op": "welshlab",
    "conservative": "welshcon",
    "welsh conservative": "welshcon",
    "welsh conservatives": "welshcon",
    "conservatives": "welshcon",
    "plaid cymru": "plaid",
    "liberal democrats": "welshlibdem",
    "welsh liberal democrats": "welshlibdem",
    "ukip": "ukip",
    "uk independence party": "ukip",
    "green": "walesgrn",
    "wales green party": "walesgrn",
    "green party": "walesgrn",
    "reform": "reform",
    "reform uk": "reform",
    "reform uk wales": "reform",
    "independent": "independent",
    "independent politician": "independent",
    "independents": "independent",
    "gwlad": "gwlad",
    "gwlad gwlad": "gwlad",
    "propel": "propel",
    "heritage party": "heritage",
    "communist party of britain": "communist",
    "communist": "communist",
    "welsh tusc": "tusc",
    "tusc": "tusc",
    "co-operative party": "cooperative",
    "co-op": "cooperative",
    "cooperative": "cooperative",
    "abolish the welsh assembly": "abolish",
    "abolish": "abolish",
    "abolish the welsh assembly party": "abolish",
    "independent unionist": "independent",
}

def get_party_id(party_str):
    party_clean = clean_html(party_str).lower()
    for k, v in PARTY_MAP.items():
        if k in party_clean:
            return v
    return "others"

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

def clean_html(text):
    text = re.sub(r'<[^>]*>', '', text)
    text = text.replace('\xa0', ' ')
    text = text.replace('&nbsp;', ' ')
    return ' '.join(text.split()).strip()

def normalize_name(name):
    n = clean_html(name)
    n = n.replace("Eastand", "East and").replace("of Clwyd", "of Clwyd").replace("Valeof", "Vale of")
    return n

def get_parsed_data(year):
    if year == 2021:
        html = (CACHE_DIR / "2021_assembly.html").read_text(encoding="utf-8")
        tables = parse_tables(html)
        consts = {}
        for row in tables[4][1][1:]:
            if len(row) < 4: continue
            consts[normalize_name(row[0])] = get_party_id(row[4])
        
        reg_list = []
        current_region = ""
        for row in tables[5][1][1:]:
            val_0 = clean_html(row[0])
            if val_0 in ["Mid and West Wales", "North Wales", "South Wales Central", "South Wales East", "South Wales West"]:
                current_region = val_0
            member = row[1] if row[0] == "" or val_0 == current_region else row[0]
            party = row[4]
            pid = get_party_id(party)
            reg_list.append((current_region, clean_html(member), party, pid))
        return consts, reg_list

    elif year == 2011:
        html_el = (CACHE_DIR / "2011_election.html").read_text(encoding="utf-8")
        tables_el = parse_tables(html_el)
        consts = {}
        for row in tables_el[9][1][1:]:
            if len(row) < 7: continue
            c_name = normalize_name(row[0])
            if "Brecon" in c_name:
                print(f"RAW BRECON ROW: {row}")
            consts[c_name] = get_party_id(row[6])
            
        html_mem = (CACHE_DIR / "2011_assembly.html").read_text(encoding="utf-8")
        tables_mem = parse_tables(html_mem)
        reg_list = []
        regions = ["North Wales", "Mid and West Wales", "South Wales West", "South Wales Central", "South Wales East"]
        for idx, reg_name in enumerate(regions):
            rows = tables_mem[4 + idx][1]
            for row in rows[2:]:
                if len(row) < 3: continue
                member = row[1] if row[0] == "" or row[0] == reg_name else row[0]
                party = row[2] if row[0] == "" or row[0] == reg_name else row[1]
                pid = get_party_id(party)
                reg_list.append((reg_name, clean_html(member), party, pid))
        return consts, reg_list

    elif year == 2007:
        html = (CACHE_DIR / "2007_assembly.html").read_text(encoding="utf-8")
        tables = parse_tables(html)
        consts = {}
        for row in tables[5][1][2:]:
            if len(row) < 3: continue
            consts[normalize_name(row[0])] = get_party_id(row[3])
            
        reg_list = []
        current_region = ""
        for row in tables[6][1][2:]:
            val_0 = clean_html(row[0])
            if "region" in val_0.lower() or "member" in val_0.lower(): continue
            if val_0 != "" and val_0 in ["Mid and West Wales", "North Wales", "South Wales Central", "South Wales East", "South Wales West"]:
                current_region = val_0
            member = row[1] if row[0] == "" or val_0 == current_region else row[0]
            party = row[2] if row[0] == "" or val_0 == current_region else row[1]
            pid = get_party_id(party)
            reg_list.append((current_region, clean_html(member), party, pid))
        return consts, reg_list

def parse_tables(html):
    parser = TableParser()
    parser.feed(html)
    return parser.tables

for y in [2007, 2011, 2021]:
    consts, regs = get_parsed_data(y)
    print(f"\n=================== Year {y} constituencies ===================")
    for c, p in sorted(consts.items()):
        if p == "others":
            print(f"  Constituency '{c}' has others: {p}")
            
    print(f"\n=================== Year {y} regional members ===================")
    for r, m, party, pid in regs:
        if pid == "others":
            print(f"  Region '{r}', member '{m}': party_str='{party}' -> resolved to: {pid}")
