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

cache_path = CACHE_DIR / "2026_assembly.html"
html = cache_path.read_text(encoding="utf-8")
parser = TableParser()
parser.feed(html)

const_winners_2026 = {}
current_const = ""

# Table 5 (index 4) has constituency results
for row in parser.tables[4][1][1:]:
    if len(row) < 3:
        continue
    
    val_0 = clean_html(row[0])
    if "Blaenau Gwent" in val_0 or current_const == "Blaenau Gwent Caerffili Rhymni":
        print(f"RAW ROW: {row}")

    if val_0 != "":
        current_const = val_0
        if current_const not in const_winners_2026:
            const_winners_2026[current_const] = []
        
        # First row of constituency: constituency is row[0], member is row[2], party is row[4]
        if len(row) >= 5:
            member = clean_html(row[2])
            party = clean_html(row[4])
        else:
            member = ""
            party = ""
    else:
        # Subsequent rows of constituency: member is row[1], party is row[3]
        if len(row) >= 4:
            member = clean_html(row[1])
            party = clean_html(row[3])
        else:
            member = ""
            party = ""

    if current_const and member and party:
        party_clean = party.lower()
        # Simple local party resolution for testing
        party_id = "others"
        if "plaid" in party_clean: party_id = "plaid"
        elif "labour" in party_clean: party_id = "welshlab"
        elif "reform" in party_clean: party_id = "reform"
        elif "conservative" in party_clean: party_id = "welshcon"
        elif "green" in party_clean: party_id = "walesgrn"
        elif "liberal democrat" in party_clean: party_id = "welshlibdem"
        
        const_winners_2026[current_const].append((member, party_id))


print(f"Total constituencies parsed: {len(const_winners_2026)}")
for const, members in const_winners_2026.items():
    print(f"  {const} ({len(members)} members):")
    for m, p in members:
        print(f"    - {m}: {p}")

