#!/usr/bin/env python3
import json
import os
import re
import urllib.request
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parent.parent
HEX_DIR = ROOT / "data" / "hex" / "senedd"
CACHE_DIR = ROOT / "data" / "cache" / "wikipedia"

# Custom layout for 2026 (16 constituencies in a 4x6 grid)
LAYOUT_2026 = {
    "Bangor Conwy Môn": {"q": 0, "r": 5},
    "Clwyd": {"q": 1, "r": 5},
    "Fflint Wrecsam": {"q": 2, "r": 5},
    "Gwynedd Maldwyn": {"q": 2, "r": 4},
    "Ceredigion Penfro": {"q": 0, "r": 3},
    "Sir Gaerfyrddin": {"q": 1, "r": 3},
    "Gŵyr Abertawe": {"q": 2, "r": 3},
    "Brycheiniog Tawe Nedd": {"q": 3, "r": 3},
    "Afan Ogwr Rhondda": {"q": 0, "r": 2},
    "Pontypridd Cynon Merthyr": {"q": 1, "r": 2},
    "Blaenau Gwent Caerffili Rhymni": {"q": 2, "r": 2},
    "Sir Fynwy Torfaen": {"q": 3, "r": 2},
    "Pen-y-bont Bro Morgannwg": {"q": 0, "r": 1},
    "Caerdydd Penarth": {"q": 1, "r": 1},
    "Caerdydd Ffynnon Taf": {"q": 2, "r": 1},
    "Casnewydd Islwyn": {"q": 3, "r": 1}
}

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
    "ld": "welshlibdem",
    "con": "welshcon",
    "lab": "welshlab",
    "pc": "plaid",
}

def clean_html(text):
    text = re.sub(r'<[^>]*>', '', text)
    text = text.replace('\xa0', ' ')
    text = text.replace('&nbsp;', ' ')
    return ' '.join(text.split()).strip()

def normalize_name(name):
    name = clean_html(name)
    name = name.replace('&', 'and')
    # Remove constituency/region suffix if any
    name = re.sub(r'\s*\((Assembly|Senedd)\s*constituency\)', '', name, flags=re.I)
    name = re.sub(r'\s*\((National\s+Assembly\s+for\s+Wales\s+|Senedd\s+|Senedd\s+Cymru\s+)?electoral\s+region\)', '', name, flags=re.I)
    # Common replacements to align naming
    name = name.replace('Carmarthen West and South Pembrokeshire', 'Carmarthen West and South Pembrokeshire')
    name = name.replace('Carmarthen West & South Pembrokeshire', 'Carmarthen West and South Pembrokeshire')
    name = name.replace('Ynys Mon', 'Ynys Môn')
    
    name_str = ' '.join(name.split()).strip().lower()
    
    # Map spacing-error variants (from 1997 hexjson) to standard names
    mappings = {
        "alynand deeside": "alyn and deeside",
        "breconand radnorshire": "brecon and radnorshire",
        "carmarthen eastand dinefwr": "carmarthen east and dinefwr",
        "carmarthen westand south pembrokeshire": "carmarthen west and south pembrokeshire",
        "merthyr tydfiland rhymney": "merthyr tydfil and rhymney",
        "valeof clwyd": "vale of clwyd",
        "valeof glamorgan": "vale of glamorgan",
        "cardiff southand penarth": "cardiff south and penarth",
    }
    return mappings.get(name_str, name_str)


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

def load_grid_coords_1997():
    path = ROOT / "data" / "hex" / "uk-constituencies-1997.hexjson"
    data = json.loads(path.read_text(encoding="utf-8"))
    coords = {}
    for k, cell in data["hexes"].items():
        name = normalize_name(cell["n"])
        q = cell["q"]
        r = cell["r"]
        if name in ["caernarfon", "conwy", "vale of clwyd", "clwyd west"]:
            q += 1
        coords[name] = {"q": q, "r": r}
    # Add manual fallback/override for Welsh specific differences
    coords["meirionnydd nant conwy"] = {"q": 6, "r": 11} # In uk-1997, Meirionnydd Nant Conwy is WIKI-meirionnydd-nant-conwy
    return coords

def load_grid_coords_2010():
    path = ROOT / "data" / "hex" / "uk-constituencies-2010.hexjson"
    data = json.loads(path.read_text(encoding="utf-8"))
    coords = {}
    for k, cell in data["hexes"].items():
        if cell.get("region") == "W92000004" or k.startswith("W"):
            name = normalize_name(cell["n"])
            q = cell["q"]
            r = cell["r"]
            if name in ["arfon", "aberconwy", "vale of clwyd", "clwyd west"]:
                q += 1
            coords[name] = {"q": q, "r": r}
    return coords

def main():
    HEX_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load coordinates
    coords_1997 = load_grid_coords_1997()
    coords_2010 = load_grid_coords_2010()
    
    print(f"Loaded {len(coords_1997)} coordinates for 1997 grid, {len(coords_2010)} for 2010 grid.")
    
    # -------------------------------------------------------------
    # 1999 Election
    # -------------------------------------------------------------
    html_1999 = fetch_wikipedia_html(
        "https://en.wikipedia.org/wiki/1999_National_Assembly_for_Wales_election",
        "1999_election.html"
    )
    tables_1999 = parse_tables(html_1999)
    const_winners_1999 = {}
    regional_list_1999 = {}
    
    # Parse constituencies and regional lists from the regional tables on the election page
    for caption, rows in tables_1999:
        cap_clean = clean_html(caption)
        if "Mid and West Wales" in cap_clean or "North Wales" in cap_clean or "South Wales Central" in cap_clean or "South Wales East" in cap_clean or "South Wales West" in cap_clean:
            # Check if this is the constituency results table or the list seats table
            # Table of constituency results has header: ['Constituency', 'Elected member', 'Result'] or similar
            is_const = any("constituency" in clean_html(cell).lower() for cell in rows[0])
            is_list = any("elected candidates" in clean_html(cell).lower() or "elected member" in clean_html(cell).lower() for cell in rows[0]) and not is_const
            
            region_match = re.search(r'(Mid and West Wales|North Wales|South Wales Central|South Wales East|South Wales West)', cap_clean)
            if not region_match:
                continue
            region_name = region_match.group(1)
            
            if is_const:
                # Constituency results
                for row in rows[1:]:
                    if len(row) < 3:
                        continue
                    const_cell = clean_html(row[1] if len(row) >= 4 else row[0]) # if column 0 is a swatch
                    member_cell = clean_html(row[2] if len(row) >= 4 else row[1])
                    result_cell = clean_html(row[3] if len(row) >= 4 else row[2])
                    
                    const_norm = normalize_name(const_cell)
                    if not const_norm or const_norm == "constituency":
                        continue
                    
                    # Extract winning party from result string (e.g. "Plaid Cymru win")
                    party_id = get_party_id(result_cell)
                    const_winners_1999[const_norm] = {
                        "winner": member_cell,
                        "party": party_id
                    }
            elif "elected candidates" in [clean_html(c).lower() for c in rows[0]]:
                # Regional list seats
                if region_name not in regional_list_1999:
                    regional_list_1999[region_name] = []
                for row in rows[1:]:
                    if len(row) < 3:
                        continue
                    party_cell = clean_html(row[1] if len(row) >= 4 else row[0])
                    candidates_cell = clean_html(row[2] if len(row) >= 4 else row[1])
                    seats_cell = clean_html(row[3] if len(row) >= 4 else row[2])
                    
                    party_id = get_party_id(party_cell)
                    if not party_id or party_id == "others":
                        continue
                    
                    try:
                        seats_count = int(re.sub(r'\D', '', seats_cell))
                    except ValueError:
                        seats_count = 0
                    
                    if seats_count > 0:
                        cands = []
                        if party_id == "welshcon":
                            if "Nick Bourne" in candidates_cell: cands.append("Nick Bourne")
                            if "Glyn Davies" in candidates_cell or "Edward Glyn Davies" in candidates_cell: cands.append("Glyn Davies")
                            if "Alun Cairns" in candidates_cell: cands.append("Alun Cairns")
                            if "Jonathan Morgan" in candidates_cell: cands.append("Jonathan Morgan")
                            if "David Melding" in candidates_cell: cands.append("David Melding")
                            if "William Graham" in candidates_cell: cands.append("William Graham")
                            if "Peter Rogers" in candidates_cell: cands.append("Peter Rogers")
                            if "Owen John Thomas" in candidates_cell: cands.append("Owen John Thomas")
                        elif party_id == "plaid":
                            if "Cynog Dafis" in candidates_cell: cands.append("Cynog Dafis")
                            if "Jocelyn Davies" in candidates_cell: cands.append("Jocelyn Davies")
                            if "Janet Ryder" in candidates_cell: cands.append("Janet Ryder")
                            if "Gareth Jones" in candidates_cell: cands.append("Gareth Jones")
                            if "Helen Mary Jones" in candidates_cell: cands.append("Helen Mary Jones")
                            if "Rhodri Glyn Thomas" in candidates_cell: cands.append("Rhodri Glyn Thomas")
                            if "Pauline Jarman" in candidates_cell: cands.append("Pauline Jarman")
                            if "Geraint Davies" in candidates_cell: cands.append("Geraint Davies")
                        
                        raw_cands = [c.strip() for c in re.split(r'(?=[A-Z][a-z]+ [A-Z][a-z]+)', candidates_cell) if c.strip()]
                        for rc in raw_cands[:seats_count]:
                            if rc not in cands:
                                cands.append(rc)
                        while len(cands) < seats_count:
                            cands.append(f"{party_cell} List Member")
                        
                        for cname in cands[:seats_count]:
                            regional_list_1999[region_name].append({
                                "name": cname,
                                "party": party_id
                            })
                            
    # -------------------------------------------------------------
    # 2003 Election (2nd Assembly)
    # -------------------------------------------------------------
    html_2003 = fetch_wikipedia_html(
        "https://en.wikipedia.org/wiki/2nd_National_Assembly_for_Wales",
        "2003_assembly.html"
    )
    tables_2003 = parse_tables(html_2003)
    const_winners_2003 = {}
    regional_list_2003 = {}
    
    # Table 7: constituency members
    for row in tables_2003[6][1][2:]: # Table index 6 is the 7th table
        if len(row) < 3:
            continue
        const_name = row[0]
        member = row[2]
        party = row[3]
        const_winners_2003[normalize_name(const_name)] = {
            "winner": member,
            "party": get_party_id(party)
        }
    
    # Table 8: regional members
    current_region = ""
    for row in tables_2003[7][1][2:]:
        if len(row) == 1:
            current_region = clean_html(row[0])
            if current_region not in regional_list_2003:
                regional_list_2003[current_region] = []
        elif len(row) >= 2:
            member = row[1] if row[0] == "" else row[0]
            party = row[2] if row[0] == "" else row[1]
            if current_region:
                regional_list_2003[current_region].append({
                    "name": member,
                    "party": get_party_id(party)
                })

    # -------------------------------------------------------------
    # 2007 Election (3rd Assembly)
    # -------------------------------------------------------------
    html_2007 = fetch_wikipedia_html(
        "https://en.wikipedia.org/wiki/3rd_National_Assembly_for_Wales",
        "2007_assembly.html"
    )
    tables_2007 = parse_tables(html_2007)
    const_winners_2007 = {}
    regional_list_2007 = {}
    
    # Table 6: constituency members
    for row in tables_2007[5][1][2:]:
        if len(row) < 3:
            continue
        const_name = row[0]
        member = row[2]
        party = row[3]
        const_winners_2007[normalize_name(const_name)] = {
            "winner": member,
            "party": "others" if normalize_name(const_name).lower() == "blaenau gwent" else get_party_id(party)
        }
        
    # Table 7: regional members
    current_region = ""
    for row in tables_2007[6][1][2:]:
        val_0 = clean_html(row[0])
        if "region" in val_0.lower() or "member" in val_0.lower():
            continue
        if val_0 != "" and val_0 in ["Mid and West Wales", "North Wales", "South Wales Central", "South Wales East", "South Wales West"]:
            current_region = val_0
            if current_region not in regional_list_2007:
                regional_list_2007[current_region] = []
        
        if len(row) >= 4:
            member = row[2]
            party = row[3]
        else:
            member = row[1]
            party = row[2]
        
        if current_region and member and party:
            m_name = clean_html(member)
            p_id = get_party_id(party)
            if m_name == "Mohammad Asghar":
                p_id = "plaid"
            regional_list_2007[current_region].append({
                "name": m_name,
                "party": p_id
            })

    # -------------------------------------------------------------
    # 2011 Election (4th Assembly)
    # -------------------------------------------------------------
    html_2011_el = fetch_wikipedia_html(
        "https://en.wikipedia.org/wiki/2011_National_Assembly_for_Wales_election",
        "2011_election.html"
    )
    tables_2011_el = parse_tables(html_2011_el)
    const_winners_2011 = {}
    
    # Parse constituency winners from Table 10 of election page
    for row in tables_2011_el[9][1][1:]: # Table 10 is index 9
        if len(row) < 7:
            continue
        const_name = row[0]
        result_cell = row[6]
        
        party_id = get_party_id(result_cell)
        const_winners_2011[normalize_name(const_name)] = {
            "winner": "",
            "party": party_id
        }
        
    html_2011_mem = fetch_wikipedia_html(
        "https://en.wikipedia.org/wiki/4th_National_Assembly_for_Wales",
        "2011_assembly.html"
    )
    tables_2011_mem = parse_tables(html_2011_mem)
    
    for row in tables_2011_mem[3][1][1:]: # Table 4 is index 3
        if len(row) < 2:
            continue
        const_name = row[0]
        member = row[1]
        norm = normalize_name(const_name)
        if norm in const_winners_2011:
            const_winners_2011[norm]["winner"] = member
            
    regional_list_2011 = {}
    regions_2011 = ["North Wales", "Mid and West Wales", "South Wales West", "South Wales Central", "South Wales East"]
    for idx, reg_name in enumerate(regions_2011):
        table_rows = tables_2011_mem[4 + idx][1]
        regional_list_2011[reg_name] = []
        for row in table_rows[1:]:
            if len(row) == 1 or "members" in [x.lower() for x in row]:
                continue
            if len(row) < 3:
                continue
            if row[0] == reg_name:
                member = row[1]
                party = row[2]
            else:
                member = row[0]
                party = row[1]
            regional_list_2011[reg_name].append({
                "name": clean_html(member),
                "party": get_party_id(party)
            })

    # -------------------------------------------------------------
    # 2016 Election (5th Assembly)
    # -------------------------------------------------------------
    html_2016 = fetch_wikipedia_html(
        "https://en.wikipedia.org/wiki/5th_National_Assembly_for_Wales",
        "2016_assembly.html"
    )
    tables_2016 = parse_tables(html_2016)
    const_winners_2016 = {}
    regional_list_2016 = {}
    
    # Table 6 (index 5) is Constituency members
    for row in tables_2016[5][1][1:]:
        if len(row) < 4:
            continue
        const_name = row[0]
        member = row[1]
        party = row[4] if len(row) >= 5 else row[3]
        const_winners_2016[normalize_name(const_name)] = {
            "winner": member,
            "party": get_party_id(party)
        }
        
    # Table 7 (index 6) is Regional members
    current_region = ""
    for row in tables_2016[6][1][1:]:
        val_0 = clean_html(row[0])
        if val_0 in ["Mid and West Wales", "North Wales", "South Wales Central", "South Wales East", "South Wales West"]:
            current_region = val_0
            if current_region not in regional_list_2016:
                regional_list_2016[current_region] = []
        
        member = row[1] if row[0] == "" or val_0 == current_region else row[0]
        party = row[4] if len(row) >= 5 and (row[0] == "" or val_0 == current_region) else row[3]
        
        if current_region and member and party:
            regional_list_2016[current_region].append({
                "name": clean_html(member),
                "party": get_party_id(party)
            })

    # -------------------------------------------------------------
    # 2021 Election (6th Senedd)
    # -------------------------------------------------------------
    html_2021 = fetch_wikipedia_html(
        "https://en.wikipedia.org/wiki/Members_of_the_6th_Senedd",
        "2021_assembly.html"
    )
    tables_2021 = parse_tables(html_2021)
    const_winners_2021 = {}
    regional_list_2021 = {}
    
    # Table 5 (index 4) is Constituency members
    for row in tables_2021[4][1][1:]:
        if len(row) < 4:
            continue
        const_name = row[0]
        member = row[1]
        party = row[4]
        c_norm = normalize_name(const_name)
        if c_norm.lower() == "caerphilly":
            winner = "Hefin David"
            party_id = "welshlab"
        else:
            winner = member
            party_id = get_party_id(party)
        const_winners_2021[c_norm] = {
            "winner": winner,
            "party": party_id
        }
        
    # Table 6 (index 5) is Regional members
    current_region = ""
    for row in tables_2021[5][1][1:]:
        val_0 = clean_html(row[0])
        if val_0 in ["Mid and West Wales", "North Wales", "South Wales Central", "South Wales East", "South Wales West"]:
            current_region = val_0
            if current_region not in regional_list_2021:
                regional_list_2021[current_region] = []
        
        if len(row) >= 6:
            member = row[1]
            party = row[4]
        else:
            member = row[0]
            party = row[3]
        
        if current_region and member and party:
            regional_list_2021[current_region].append({
                "name": clean_html(member),
                "party": get_party_id(party)
            })

    # -------------------------------------------------------------
    # 2026 Election (7th Senedd)
    # -------------------------------------------------------------
    html_2026 = fetch_wikipedia_html(
        "https://en.wikipedia.org/wiki/7th_Senedd",
        "2026_assembly.html"
    )
    tables_2026 = parse_tables(html_2026)
    const_winners_2026 = {}
    
    # Table 5 (index 4) is Constituency members
    current_const = ""
    for row in tables_2026[4][1][1:]:
        if len(row) < 3:
            continue
        val_0 = clean_html(row[0])
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
            const_winners_2026[current_const].append(get_party_id(party))


    # -------------------------------------------------------------
    # Output Files Generation
    # -------------------------------------------------------------
    build_ams_json("1999", const_winners_1999, regional_list_1999, coords_1997)
    build_ams_json("2003", const_winners_2003, regional_list_2003, coords_1997)
    build_ams_json("2007", const_winners_2007, regional_list_2007, coords_2010)
    build_ams_json("2011", const_winners_2011, regional_list_2011, coords_2010)
    build_ams_json("2016", const_winners_2016, regional_list_2016, coords_2010)
    build_ams_json("2021", const_winners_2021, regional_list_2021, coords_2010)
    build_pr_json("2026", const_winners_2026)

def build_ams_json(year, const_winners, regional_list, coords_grid):
    hexes = {}
    for const_name, data in const_winners.items():
        coords = None
        for name, pt in coords_grid.items():
            if normalize_name(name) == const_name:
                coords = pt
                break
        
        if not coords:
            print(f"WARNING: No coordinates found for constituency {const_name} in {year}")
            continue
            
        hexes[clean_html(const_name).title()] = {
            "q": coords["q"],
            "r": coords["r"],
            "n": clean_html(const_name).title(),
            "party": data["party"],
            "winner": data["winner"],
        }
        
    regional_list_clean = []
    for reg, members in regional_list.items():
        regional_list_clean.append({
            "region": clean_html(reg).title(),
            "members": [{"name": clean_html(m["name"]), "party": m["party"]} for m in members]
        })
        
    out_data = {
        "layout": "odd-r",
        "hexes": hexes,
        "regional_list": regional_list_clean
    }
    
    out_path = HEX_DIR / f"{year}.hexjson"
    out_path.write_text(json.dumps(out_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Written {out_path} with {len(hexes)} hexes and {len(regional_list_clean)} regional list seats.")

def build_pr_json(year, const_winners):
    hexes = {}
    for const_name, seats in const_winners.items():
        coords = LAYOUT_2026.get(clean_html(const_name))
        if not coords:
            for name, pt in LAYOUT_2026.items():
                if normalize_name(name) == normalize_name(const_name):
                    coords = pt
                    break
        
        if not coords:
            print(f"WARNING: No coordinates found for constituency {const_name} in 2026")
            continue
            
        counts = {}
        for s in seats:
            counts[s] = counts.get(s, 0) + 1
        plurality = max(counts, key=counts.get) if counts else "others"
        
        hexes[clean_html(const_name)] = {
            "q": coords["q"],
            "r": coords["r"],
            "n": clean_html(const_name),
            "party": plurality,
            "seats_list": seats
        }
        
    out_data = {
        "layout": "odd-r",
        "hexes": hexes
    }
    
    out_path = HEX_DIR / f"{year}.hexjson"
    out_path.write_text(json.dumps(out_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Written {out_path} with {len(hexes)} hexes.")

if __name__ == "__main__":
    main()
