import json
from pathlib import Path
from html.parser import HTMLParser
import re

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "data" / "cache" / "wikipedia"

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

# Load 2010 coordinates
path_2010 = ROOT / "data" / "hex" / "uk-constituencies-2010.hexjson"
data_2010 = json.loads(path_2010.read_text(encoding="utf-8"))
coords_2010 = {}
for k, cell in data_2010["hexes"].items():
    if cell.get("region") == "W92000004" or k.startswith("W"):
        coords_2010[normalize_name(cell["n"])] = True

# Parse 1999 constituency winners
html_1999 = (CACHE_DIR / "1999_election.html").read_text(encoding="utf-8")
parser = TableParser()
parser.feed(html_1999)
consts_1999 = []
for title, rows in parser.tables:
    if "Constituency" in title:
        for row in rows[1:]:
            if len(row) < 3: continue
            const_cell = clean_html(row[1] if len(row) >= 4 else row[0])
            const_norm = normalize_name(const_cell)
            if const_norm and const_norm.lower() != "constituency":
                consts_1999.append(const_norm)

print("Parsed 1999 constituency count:", len(consts_1999))
print("Missing in 2010:")
for c in consts_1999:
    if c not in coords_2010:
        print(f"  {c}")
