#!/usr/bin/env python3
"""
Fetch UK general-election constituency results and build hexmap JSON files.

Sources:
  - politicsresources.net (Wayback) — 1945–2017
  - alasdairrae/wpc CSV — 2019
  - open-innovations/constituencies — 2024

Usage: python3 scripts/fetch-constituency-data.py [--election 2015]
"""

from __future__ import annotations

import argparse
import csv
import html
import io
import json
import math
import re
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from difflib import get_close_matches
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "constituencies"
HEX_DIR = ROOT / "data" / "hex"
CACHE_DIR = ROOT / "data" / "cache" / "politicsresources"
HOC_2019_XLSX = ROOT / "data" / "sources" / "HoC-GE2019-results-by-constituency.xlsx"

HOC_2019_FIRST_PARTY = {
    "Con": ("conservative", "Conservative"),
    "Lab": ("labour", "Labour"),
    "LD": ("libdem", "Liberal Democrat"),
    "SNP": ("snp", "Scottish National Party"),
    "PC": ("plaid", "Plaid Cymru"),
    "DUP": ("dup", "DUP"),
    "SF": ("sinnfein", "Sinn Féin"),
    "SDLP": ("sdlp", "SDLP"),
    "Green": ("green", "Green"),
    "Spk": ("speaker", "Speaker"),
    "APNI": ("alliance", "Alliance"),
}


def _apply_display_name_fixes(constituencies: list[dict]) -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "import_historical_hexmaps",
        ROOT / "scripts" / "import-historical-hexmaps.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.fix_constituency_display_names(constituencies)

ARCHIVE = "https://web.archive.org/web/20170504072213"
PSR_BASE = f"{ARCHIVE}/http://www.politicsresources.net/area/uk"
# Some elections need a later snapshot — early captures miss batch pages (notably ge17).
ELECTION_ARCHIVE_OVERRIDE: dict[str, str] = {
    "2017": "https://web.archive.org/web/20190608000000",
}
UA = "Mozilla/5.0 (compatible; BritishManifestoArchive/1.0; +research)"

BATCH_ELECTIONS = {
    "1945": ("ge45", "ge45index.htm"),
    "1950": ("ge50", "ge50index.htm"),
    "1951": ("ge51", "ge51index.htm"),
    "1955": ("ge55", "ge55index.htm"),
    "1959": ("ge59", "ge59index.htm"),
    "1964": ("ge64", "ge64index.htm"),
    "1966": ("ge66", "ge66index.htm"),
    "1970": ("ge70", "ge70index.htm"),
    "feb1974": ("ge74a", "ge74aindex.htm"),
    "oct1974": ("ge74b", "ge74bindex.htm"),
    "1979": ("ge79", "ge79index.htm"),
    "1983": ("ge83", "ge83index.htm"),
    "1987": ("ge87", "ge87index.htm"),
    "1992": ("ge92", "ge92index.htm"),
    "2005": ("ge05", "ge05index.htm"),
    "2010": ("ge10", "ge10index.htm"),
    "2015": ("ge15", "ge15index.htm"),
    "2017": ("ge17", "ge17index.htm"),
}

INDIVIDUAL_ELECTIONS = {
    "1997": "mps97.htm",
    "2001": "mps01.htm",
}

PARTY_MAP = {
    "labour": "labour",
    "labour & co-op": "labour",
    "labour and co-op": "labour",
    "conservative": "conservative",
    "liberal democrat": "libdem",
    "liberal democrats": "libdem",
    "libdem": "libdem",
    "liberal": "libdem",
    "liberal party": "libdem",
    "social and liberal democrats": "libdem",
    "sdp-liberal alliance": "libdem",
    "sdp - liberal alliance": "libdem",
    "snp": "snp",
    "scottish national party": "snp",
    "plaid cymru": "plaid",
    "pcymru": "plaid",
    "green": "green",
    "green party": "green",
    "ukip": "ukip",
    "uk independence party": "ukip",
    "united kingdom independence party": "ukip",
    "reform uk": "reform",
    "brexit party": "reform",
    "reform": "reform",
    "dup": "dup",
    "democratic unionist": "dup",
    "democratic unionist party": "dup",
    "sinn fein": "sinnfein",
    "sinn fein": "sinnfein",
    "sdlp": "sdlp",
    "social democratic & labour party": "sdlp",
    "social democratic and labour party": "sdlp",
    "alliance (lib)": "libdem",
    "alliance (sdp)": "libdem",
    "alliance (liberal)": "libdem",
    "alliance (social democratic)": "libdem",
    "uup": "uup",
    "ulster unionist": "uup",
    "ulster unionist party": "uup",
    "official unionist": "uup",
    "official unionist party": "uup",
    "official ulster unionist": "uup",
    "united uu council": "uup",
    "united ulster unionist council": "uup",
    "uuuc": "uup",
    "vanguard": "vanguard",
    "vanguard unionist progressive party": "vanguard",
    "tuv": "tuv",
    "traditional unionist voice": "tuv",
    "liberal national": "nationalliberal",
    "national liberal": "nationalliberal",
    "nat liberal": "nationalliberal",
    "nat lib conservative": "natlibconservative",
    "nat lib and conservative": "natlibconservative",
    "lib and conservative": "natlibconservative",
    "lib conservative": "natlibconservative",
    "common wealth": "commonwealth",
    "common wealth party": "commonwealth",
    "ind labour party": "ilp",
    "independent labour party": "ilp",
    "ind conservative": "indconservative",
    "independent conservative": "indconservative",
    "ind liberal": "indliberal",
    "independent liberal": "indliberal",
    "ind progressive": "indprogressive",
    "independent progressive": "indprogressive",
    "ind ulster unionist": "indunionist",
    "independent unionist": "indunionist",
    "irish nationalist": "irishnationalist",
    "national": "national",
    "national independent": "nationalindependent",
    "speaker": "speaker",
    "spk": "speaker",
    "speaker seeking re election": "speaker",
    "irish labour": "irishlabour",
    "irish republican": "irishrepublican",
    "anti partition": "antipartition",
    "republican labour": "republicanlabour",
    "protestant unionist": "protestantunionist",
    "unity": "unity",
    "ind unity": "unity",
    "united ulster unionist": "uuuc",
    "ukup": "ukup",
    "ulster popular unionist": "ulsterpopularunionist",
    "social democratic labour": "sdlp",
    "social democratic and labour party": "sdlp",
    "social democratic & labour party": "sdlp",
    "provisional sinn fein": "sinnfein",
    "sinn fein": "sinnfein",
    "social democrat": "libdem",
    "ikhc": "healthconcern",
    "nat lib & conservative": "conservative",
    "nat lib and conservative": "conservative",
    "welsh nationalist": "plaid",
    "scottish nationalist": "snp",
    "ulster unionist": "uup",
    "official unionist": "uup",
    "official conservative": "conservative",
    "independent conservative": "conservative",
    "independent unionist": "others",
    "independent conservative": "conservative",
    "independent labour": "indlabour",
    "ind lab": "indlabour",
    "ind labour": "indlabour",
    "independent liberal": "libdem",
    "independent social democrat": "libdem",
    "independent social democratic": "libdem",
    "independent republican": "sinnfein",
    "nationalist": "others",
    "unionist": "uup",
    "communist": "communist",
    "communist party of great britain": "communist",
    "national front": "others",
    "bnp": "bnp",
    "british national party": "bnp",
    "referendum party": "referendumparty",
    "co-op": "cooperative",
    "co-operative": "cooperative",
    "co-operative party": "cooperative",
    "lab": "labour",
    "con": "conservative",
    "ld": "libdem",
    "pc": "plaid",
    "sf": "sinnfein",
    "apni": "alliance",
    "ref": "reform",
    "spk": "others",
    "xspk": "others",
    "speaker": "others",
    "speakers": "others",
    "independent": "others",
    "ind": "others",
}

NATION_MAP = {"E": "england", "W": "wales", "S": "scotland", "N": "northern-ireland"}


def fetch_url(url: str, cache_path: Path | None = None, retries: int = 5) -> str:
    if cache_path and cache_path.exists():
        return cache_path.read_text(encoding="utf-8", errors="replace")

    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = resp.read().decode("utf-8", errors="replace")
            if cache_path:
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(data, encoding="utf-8")
            return data
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last_err = exc
            time.sleep(1.25 * (attempt + 1))
    raise last_err  # type: ignore[misc]


def norm_name(name: str) -> str:
    name = html.unescape(name)
    name = name.replace("&", " and ").replace("—", "-").replace("–", "-")
    name = re.sub(r"\s+", " ", name).strip().lower()
    name = name.replace(" upon ", "-upon-").replace(" under ", "-under-")
    name = re.sub(r"[^\w\s-]", "", name)
    return name


def map_party(raw: str) -> str:
    key = html.unescape(raw).strip().lower()
    key = re.sub(r"\s+", " ", key)
    key = key.replace("&", " and ")
    if key in PARTY_MAP:
        return PARTY_MAP[key]
    for prefix, pid in (
        ("labour", "labour"),
        ("conservative", "conservative"),
        ("liberal democrat", "libdem"),
        ("liberal", "libdem"),
        ("sinn fein", "sinnfein"),
        ("sinn fein", "sinnfein"),
        ("plaid cymru", "plaid"),
        ("green", "green"),
        ("ukip", "ukip"),
        ("reform", "reform"),
        ("brexit", "reform"),
    ):
        if key.startswith(prefix):
            return pid
    return "others"


def parse_batch_page(text: str) -> list[dict]:
    text = html.unescape(text)
    results = []

    # Modern pages: <b>Name</b><a name="C001">
    blocks = re.split(r"<b>([^<]+)</b>\s*<a\s+name=", text, flags=re.I)
    if len(blocks) >= 3:
        iterable = [(blocks[i], blocks[i + 1]) for i in range(1, len(blocks), 2)]
    else:
        # Older pages: <b>Name</b><br>[W] Labour win
        parts = re.split(r"<b>([^<]+)</b>", text, flags=re.I)
        iterable = [(parts[i], parts[i + 1]) for i in range(1, len(parts), 2)]

    for name_raw, body in iterable:
        name = re.sub(r"\s+", " ", name_raw.strip())
        if not name or len(name) > 90 or name.lower().startswith("index"):
            continue

        nat = None
        nat_m = re.search(r"\[([EWNS])\]", body)
        if nat_m:
            nat = NATION_MAP.get(nat_m.group(1))

        row_m = re.search(
            r"<tr><td>([^<]*)</td><td>([^<]+)</td><td[^>]*>([^<]*)</td>",
            body,
            re.I,
        )
        if not row_m:
            continue
        mp = re.sub(
            r"\s+",
            " ",
            html.unescape(row_m.group(1).replace("&dagger;", "").strip()),
        )
        party_raw = row_m.group(2).strip()
        results.append(
            {
                "name": name,
                "mp": mp,
                "party": map_party(party_raw),
                "partyLabel": html.unescape(party_raw),
                "nation": nat,
            }
        )
    return results


def parse_individual_page(text: str) -> dict | None:
    text = html.unescape(text)
    title_m = re.search(r"<title>([^<\[]+)", text, re.I)
    h1_m = re.search(r"<h1>[^<]*>([^<]+)</h1>", text, re.I)
    name = (h1_m.group(1) if h1_m else title_m.group(1) if title_m else "").strip()
    if not name:
        return None

    rows = re.findall(
        r"<tr><td>([^<]*)</td><td>\s*([^<]+)</td><td[^>]*>\s*([^<]*)</td>",
        text,
        re.I,
    )
    if not rows:
        return None
    mp, party_raw, _votes = rows[0]
    mp = re.sub(r"\s+", " ", mp.strip())
    return {
        "name": name,
        "mp": mp,
        "party": map_party(party_raw),
        "partyLabel": party_raw.strip(),
        "nation": None,
    }


def archive_base_from_html(html: str) -> str:
    ts_m = re.search(
        r"/web/(\d+)/http://www\.politicsresources\.net/area/uk",
        html,
    )
    if ts_m:
        return f"https://web.archive.org/web/{ts_m.group(1)}/http://www.politicsresources.net/area/uk"
    return PSR_BASE


def psr_base_for_election(election_id: str) -> str:
    override = ELECTION_ARCHIVE_OVERRIDE.get(election_id)
    if override:
        return f"{override}/http://www.politicsresources.net/area/uk"
    return PSR_BASE


def scrape_batch_election(election_id: str, folder: str, index_file: str) -> list[dict]:
    base = psr_base_for_election(election_id)
    index_url = f"{base}/{folder}/{index_file}"
    cache = CACHE_DIR / election_id / "index.htm"
    index_html = fetch_url(index_url, cache)
    if election_id not in ELECTION_ARCHIVE_OVERRIDE:
        base = archive_base_from_html(index_html)
    pages = sorted(set(re.findall(r'href="(i\d+\.htm)"', index_html, re.I)))
    if not pages:
        raise RuntimeError(f"No batch pages found for {election_id}")

    all_results: list[dict] = []
    for page in pages:
        url = f"{base}/{folder}/{page}"
        page_cache = CACHE_DIR / election_id / page
        time.sleep(0.35)
        try:
            all_results.extend(parse_batch_page(fetch_url(url, page_cache)))
        except Exception as exc:
            print(f"    warning: {page}: {exc}")
    return all_results


def scrape_individual_election(election_id: str, index_file: str) -> list[dict]:
    base = psr_base_for_election(election_id)
    index_url = f"{base}/{index_file}"
    cache = CACHE_DIR / election_id / "index.htm"
    index_html = fetch_url(index_url, cache)
    if election_id not in ELECTION_ARCHIVE_OVERRIDE:
        base = archive_base_from_html(index_html)
    links = sorted(set(re.findall(r'href="constit/(\d+)\.htm"', index_html)))

    results = []
    for num in links:
        url = f"{base}/constit/{num}.htm"
        page_cache = CACHE_DIR / election_id / f"constit_{num}.htm"
        time.sleep(0.25)
        try:
            item = parse_individual_page(fetch_url(url, page_cache))
            if item:
                results.append(item)
        except Exception as exc:
            print(f"    warning: constit/{num}.htm: {exc}")
    return results


def load_hex_layout(path: Path) -> tuple[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    layout = data.get("layout", "odd-q")
    lookup: dict[str, dict] = {}
    for _code, hex_def in data.get("hexes", {}).items():
        name = hex_def.get("n", "")
        lookup[norm_name(name)] = {
            "q": hex_def["q"],
            "r": hex_def["r"],
            "code": _code,
            "layoutName": name,
        }
    return layout, lookup


def auto_layout(count: int) -> list[dict]:
    width = max(1, int(math.ceil(math.sqrt(count * 1.4))))
    positions = []
    for i in range(count):
        row, col = divmod(i, width)
        q = col
        r = row
        positions.append({"q": q, "r": r})
    return positions


def assign_hex_positions(
    constituencies: list[dict],
    hex_lookup: dict[str, dict] | None,
    layout: str,
) -> tuple[str, int]:
    if constituencies and all(c.get("q") is not None and c.get("r") is not None for c in constituencies):
        return layout, len(constituencies)

    if hex_lookup:
        names = list(hex_lookup.keys())
        matched = 0
        for c in constituencies:
            key = norm_name(c["name"])
            pos = hex_lookup.get(key)
            if not pos:
                close = get_close_matches(key, names, n=1, cutoff=0.88)
                if close:
                    pos = hex_lookup[close[0]]
            if pos:
                c["q"] = pos["q"]
                c["r"] = pos["r"]
                c["code"] = pos.get("code")
                matched += 1
        if matched >= len(constituencies) * 0.75:
            return layout, matched

    positions = auto_layout(len(constituencies))
    for c, pos in zip(sorted(constituencies, key=lambda x: norm_name(x["name"])), positions):
        c["q"] = pos["q"]
        c["r"] = pos["r"]
    return "odd-q", 0


def build_election_json(
    election_id: str,
    constituencies: list[dict],
    hex_file: str | None,
    source: str,
) -> dict:
    layout = "odd-q"
    matched = 0
    hex_lookup = None
    if hex_file:
        hex_path = HEX_DIR / hex_file
        if hex_path.exists():
            layout, hex_lookup = load_hex_layout(hex_path)

    layout, matched = assign_hex_positions(constituencies, hex_lookup, layout)

    return {
        "electionId": election_id,
        "source": source,
        "layout": layout,
        "hexLayout": hex_file,
        "totalSeats": len(constituencies),
        "matchedHexes": matched,
        "constituencies": constituencies,
    }


def read_xlsx_sheet_rows(path: Path, sheet: str = "sheet1.xml") -> list[list[str]]:
    """Read first worksheet rows from an .xlsx without external dependencies."""
    with zipfile.ZipFile(path) as zf:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
            for si in root.findall(".//m:si", ns):
                texts = [t.text or "" for t in si.findall(".//m:t", ns)]
                shared.append("".join(texts))
        sheet_xml = f"xl/worksheets/{sheet}"
        if sheet_xml not in zf.namelist():
            sheet_xml = "xl/worksheets/sheet1.xml"
        root = ET.fromstring(zf.read(sheet_xml))
        ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        rows: list[list[str]] = []
        for row in root.findall(".//m:sheetData/m:row", ns):
            vals: list[str] = []
            for cell in row.findall("m:c", ns):
                cell_type = cell.get("t")
                value = cell.find("m:v", ns)
                if value is None:
                    vals.append("")
                elif cell_type == "s":
                    vals.append(shared[int(value.text)])
                else:
                    vals.append(value.text or "")
            rows.append(vals)
        return rows


def fetch_hoc_xlsx_2019(path: Path = HOC_2019_XLSX) -> list[dict]:
    """House of Commons GE2019 constituency results (First party column)."""
    if not path.is_file():
        raise FileNotFoundError(path)

    rows = read_xlsx_sheet_rows(path)
    header_idx = next(
        (i for i, row in enumerate(rows) if row and row[0] == "ONS ID"),
        None,
    )
    if header_idx is None:
        raise RuntimeError(f"Could not find header row in {path}")

    header = rows[header_idx]
    col = {name: header.index(name) for name in header if name}

    nation_by_country = {
        "England": "england",
        "Wales": "wales",
        "Scotland": "scotland",
        "Northern Ireland": "northern-ireland",
    }

    out: list[dict] = []
    for row in rows[header_idx + 1 :]:
        if len(row) <= col["Constituency name"]:
            continue
        name = row[col["Constituency name"]].strip()
        if not name:
            continue
        first_party = row[col["First party"]].strip()
        if first_party not in HOC_2019_FIRST_PARTY:
            raise RuntimeError(f"Unmapped 2019 party code: {first_party!r} ({name})")
        party_id, party_label = HOC_2019_FIRST_PARTY[first_party]
        mp = f"{row[col['Member first name']].strip()} {row[col['Member surname']].strip()}".strip()
        country = row[col["Country name"]].strip()
        item = {
            "name": name,
            "mp": mp,
            "party": party_id,
            "partyLabel": party_label,
            "nation": nation_by_country.get(country),
            "code": row[col["ONS ID"]].strip(),
            "region": row[col["ONS region ID"]].strip()
            if "ONS region ID" in col
            else None,
        }
        out.append(item)

    if len(out) != 650:
        raise RuntimeError(f"Expected 650 constituencies in {path}, got {len(out)}")
    return out


def fetch_wpc_2019() -> list[dict]:
    url = "https://raw.githubusercontent.com/alasdairrae/wpc/master/files/wpc_2019_flat_file_v9.csv"
    text = fetch_url(url)
    rows = list(csv.DictReader(io.StringIO(text)))
    out = []
    for row in rows:
        out.append(
            {
                "name": row["cname1"],
                "mp": f"{row['firstname']} {row['lastname']}".strip(),
                "party": map_party(row["partynow"]),
                "partyLabel": row["partynow"],
                "nation": {
                    "England": "england",
                    "Wales": "wales",
                    "Scotland": "scotland",
                    "Northern Ireland": "northern-ireland",
                }.get(row.get("ukcountry", ""), None),
                "code": row.get("ons_id2") or row.get("ccode1"),
            }
        )
    return out


def fetch_2024() -> list[dict]:
    csv_url = (
        "https://raw.githubusercontent.com/open-innovations/constituencies/main/"
        "src/_data/sources/society/general-elections-2024.csv"
    )
    text = fetch_url(csv_url)
    rows = list(csv.DictReader(io.StringIO(text)))
    hex_path = HEX_DIR / "uk-constituencies-2024.hexjson"
    _, hex_lookup = load_hex_layout(hex_path)

    out = []
    for row in rows:
        name = row["PCON24NM"]
        item = {
            "name": name,
            "mp": row["MP"],
            "party": map_party(row["Party"]),
            "partyLabel": row.get("Party name") or row["Party"],
            "code": row["PCON24CD"],
        }
        key = norm_name(name)
        pos = hex_lookup.get(key)
        if pos:
            item["q"] = pos["q"]
            item["r"] = pos["r"]
        out.append(item)
    return out


def download_hex_layouts() -> None:
    HEX_DIR.mkdir(parents=True, exist_ok=True)
    sources = {
        "uk-constituencies-2010.hexjson": (
            "https://raw.githubusercontent.com/odileeds/hexmaps/gh-pages/maps/"
            "uk-constituencies-2019-BBC.hexjson"
        ),
        "uk-constituencies-2024.hexjson": (
            "https://raw.githubusercontent.com/open-innovations/constituencies/main/"
            "src/_data/hexjson/uk-constituencies-2024.hexjson"
        ),
    }
    for filename, url in sources.items():
        dest = HEX_DIR / filename
        if not dest.exists():
            print(f"Downloading {filename}…")
            dest.write_text(fetch_url(url), encoding="utf-8")


def process_election(election_id: str) -> None:
    print(f"Processing {election_id}…")
    hex_file = None
    source = ""

    if election_id == "2019":
        if HOC_2019_XLSX.is_file():
            constituencies = fetch_hoc_xlsx_2019()
            source = "House of Commons Library (HoC-GE2019-results-by-constituency.xlsx)"
        else:
            constituencies = fetch_wpc_2019()
            source = "alasdairrae/wpc (2019 flat file)"
        hex_file = "uk-constituencies-2010.hexjson"
        hex_data = json.loads((HEX_DIR / hex_file).read_text(encoding="utf-8"))
        hexes = hex_data["hexes"]
        _, hex_lookup = load_hex_layout(HEX_DIR / hex_file)
        for c in constituencies:
            code = c.get("code")
            if code and code in hexes:
                c["q"] = hexes[code]["q"]
                c["r"] = hexes[code]["r"]
            else:
                key = norm_name(c["name"])
                pos = hex_lookup.get(key)
                if not pos:
                    close = get_close_matches(key, list(hex_lookup.keys()), n=1, cutoff=0.88)
                    if close:
                        pos = hex_lookup[close[0]]
                if pos:
                    c["q"] = pos["q"]
                    c["r"] = pos["r"]
    elif election_id == "2024":
        constituencies = fetch_2024()
        hex_file = "uk-constituencies-2024.hexjson"
        source = "open-innovations/constituencies (2024)"
        _apply_display_name_fixes(constituencies)
        payload = build_election_json(election_id, constituencies, hex_file, source)
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / f"{election_id}.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"  → {len(constituencies)} constituencies")
        return
    elif election_id in BATCH_ELECTIONS:
        folder, index = BATCH_ELECTIONS[election_id]
        constituencies = scrape_batch_election(election_id, folder, index)
        source = f"politicsresources.net ({folder})"
        if election_id in {"2010", "2015", "2017"}:
            hex_file = "uk-constituencies-2010.hexjson"
    elif election_id in INDIVIDUAL_ELECTIONS:
        constituencies = scrape_individual_election(election_id, INDIVIDUAL_ELECTIONS[election_id])
        source = f"politicsresources.net ({INDIVIDUAL_ELECTIONS[election_id]})"
    else:
        raise ValueError(f"Unknown election {election_id}")

    if not constituencies:
        existing = OUT_DIR / f"{election_id}.json"
        if existing.exists():
            prev = json.loads(existing.read_text(encoding="utf-8"))
            if prev.get("totalSeats", 0) > 0:
                print(f"  → kept existing {prev['totalSeats']} constituencies")
                return
        raise RuntimeError("No constituencies parsed")

    _apply_display_name_fixes(constituencies)

    payload = build_election_json(election_id, constituencies, hex_file, source)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{election_id}.json"
    if out_path.exists():
        prev = json.loads(out_path.read_text(encoding="utf-8"))
        prev_seats = prev.get("totalSeats", 0)
        if prev_seats > len(constituencies) and election_id != "2019":
            print(
                f"  → kept existing {prev_seats} constituencies "
                f"(new fetch only {len(constituencies)})"
            )
            return
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"  → {len(constituencies)} constituencies ({payload['matchedHexes']} hex-matched)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--election", action="append", dest="elections")
    args = parser.parse_args()

    download_hex_layouts()

    all_ids = (
        list(BATCH_ELECTIONS.keys())
        + list(INDIVIDUAL_ELECTIONS.keys())
        + ["2019", "2024"]
    )
    targets = args.elections or all_ids

    for eid in targets:
        try:
            process_election(eid)
        except Exception as exc:
            print(f"  ! Failed {eid}: {exc}")

    index = []
    for eid in all_ids:
        path = OUT_DIR / f"{eid}.json"
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            seats = data.get("totalSeats", 0)
            index.append(
                {
                    "id": eid,
                    "available": seats > 0,
                    "seats": seats,
                    "matchedHexes": data.get("matchedHexes", 0),
                    "source": data.get("source"),
                }
            )
        else:
            index.append({"id": eid, "available": False})

    (OUT_DIR / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print("Done.")


if __name__ == "__main__":
    main()
