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

def inspect_year(year, filename, table_indices):
    cache_path = CACHE_DIR / filename
    if not cache_path.exists():
        print(f"File missing: {filename}")
        return
    html = cache_path.read_text(encoding="utf-8")
    parser = TableParser()
    parser.feed(html)
    
    print(f"\n===== Inspecting {year} ({filename}) =====")
    for idx in table_indices:
        if idx >= len(parser.tables):
            print(f"Table index {idx} out of range (total tables: {len(parser.tables)})")
            continue
        caption, rows = parser.tables[idx]
        print(f"Table {idx}: caption='{caption}', rows={len(rows)}")
        if len(rows) > 0:
            print(f"  Header: {rows[0]}")
            print("  All data rows:")
            for r in rows[1:]:
                print(f"    {r}")

# 2021
inspect_year(2021, "2021_assembly.html", [5])
# 2011
inspect_year(2011, "2011_election.html", [9])
# 2007
inspect_year(2007, "2007_assembly.html", [5, 6])
