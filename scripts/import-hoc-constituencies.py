#!/usr/bin/env python3
"""
Import constituency results from House of Commons Research Paper PDFs.

Usage:
  python3 scripts/import-hoc-constituencies.py --election 2017 --pdf /path/to/report.pdf --pages 83-93
  python3 scripts/import-hoc-constituencies.py --all-defaults
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import unicodedata
from difflib import get_close_matches
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parent.parent
HEX_DIR = ROOT / "data" / "hex"
OUT_DIR = ROOT / "data" / "constituencies"

DEFAULT_PDFS = {
    "1997": (
        Path(
            "/Users/mosmi/Claude/Projects/Manifestos/Original documents/"
            "1997 General election/z House of Commons 1997 election report.pdf"
        ),
        (23, 36),
    ),
    "2001": (
        Path(
            "/Users/mosmi/Claude/Projects/Manifestos/Original documents/"
            "2001 General election/z House of Commons 2001 election report.pdf"
        ),
        (42, 110),
    ),
    "2017": (
        Path(
            "/Users/mosmi/Claude/Projects/Manifestos/Original documents/"
            "2017 General election/z House of Commons 2017 election report.pdf"
        ),
        (83, 93),
    ),
}

HOC_PARTIES = (
    r"Con|Lab|LDem|SNP|PC|Ind|UKIP|Green|DUP|UUP|SDLP|SF|Spk|Speaker|Comm|SLP|BNP|SSP|SA|"
    r"MRLP|NMBP|UKUP|UPUP|Other|SPK|IKHHC|LD|Ind Lab|Ind Con"
)

HOC_PARTY_MAP = {
    "con": "conservative",
    "lab": "labour",
    "ldem": "libdem",
    "ld": "libdem",
    "snp": "snp",
    "pc": "plaid",
    "green": "green",
    "ukip": "ukip",
    "dup": "dup",
    "uup": "uup",
    "sdlp": "sdlp",
    "sf": "sinnfein",
    "spk": "others",
    "speaker": "others",
    "ikhhc": "others",
    "other": "others",
    "ind": "others",
    "ind lab": "labour",
    "ind con": "conservative",
    "comm": "others",
    "slp": "others",
    "bnp": "bnp",
    "ssp": "others",
    "sa": "others",
    "mrlp": "others",
    "nmbp": "others",
    "ukup": "others",
    "upup": "others",
}


def load_fetch_module():
    spec = importlib.util.spec_from_file_location(
        "fetch_constituency_data",
        ROOT / "scripts" / "fetch-constituency-data.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def clean_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\u2019", "'").replace("\u2018", "'").replace("\u2013", "-")
    text = text.replace("\u2014", "-")
    return text


def norm_name(name: str) -> str:
    name = clean_text(name)
    name = name.replace(" and ", " & ")
    name = re.sub(r"[^a-z0-9]+", " ", name.lower())
    return re.sub(r"\s+", " ", name).strip()


def map_hoc_party(raw: str) -> tuple[str, str]:
    key = clean_text(raw).strip()
    label = key
    pid = HOC_PARTY_MAP.get(key.lower(), "others")
    if pid == "others" and key.lower().startswith("ind"):
        pid = "others"
    display = {
        "conservative": "Conservative",
        "labour": "Labour",
        "libdem": "Liberal Democrat",
        "snp": "SNP",
        "plaid": "Plaid Cymru",
        "green": "Green",
        "ukip": "UKIP",
        "dup": "DUP",
        "uup": "UUP",
        "sdlp": "SDLP",
        "sinnfein": "Sinn Féin",
        "others": label,
    }.get(pid, label)
    return pid, display


def parse_pages_arg(value: str) -> tuple[int, int]:
    if "-" in value:
        start, end = value.split("-", 1)
        return int(start), int(end)
    page = int(value)
    return page, page


def build_gazetteer_from_1997(pdf_path: Path, pages: tuple[int, int]) -> list[str]:
    line_re = re.compile(
        rf"^(.+)\s+({HOC_PARTIES})\s+"
        r"(hold|gain from \w+(?:\s+\w+)?)\s+([\d,]+)\s+([\d.]+%)\s+([\d.]+%)\s*$"
    )
    names: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for pn in range(pages[0] - 1, pages[1]):
            for line in (pdf.pages[pn].extract_text() or "").splitlines():
                line = clean_text(line.strip())
                m = line_re.match(line)
                if not m:
                    m = re.match(
                        r"^(.+)\s+Other\s+(hold|gain from \w+)\s+([\d,]+)\s+([\d.]+%)\s+([\d.]+%)\s*$",
                        line,
                    )
                if not m:
                    continue
                words = m.group(1).split()
                names.append(" ".join(words[:-2]))
    return names


def resolve_constituency_name(raw: str, gazetteer: list[str]) -> str | None:
    raw = re.sub(r"^xx", "", clean_text(raw).strip())
    raw = re.sub(r"\s+", " ", raw)
    if not raw:
        return None

    gaz_norm = {norm_name(g): g for g in gazetteer}
    key = norm_name(raw)
    if key in gaz_norm:
        return gaz_norm[key]

    prefix = [g for g in gazetteer if key.startswith(norm_name(g)) or norm_name(g).startswith(key)]
    if prefix:
        return max(prefix, key=lambda g: len(norm_name(g)))

    close = get_close_matches(key, list(gaz_norm.keys()), n=1, cutoff=0.86)
    if close:
        return gaz_norm[close[0]]
    return None


def parse_1997(pdf_path: Path, pages: tuple[int, int]) -> list[dict]:
    line_re = re.compile(
        rf"^(.+)\s+({HOC_PARTIES})\s+"
        r"(hold|gain from \w+(?:\s+\w+)?)\s+([\d,]+)\s+([\d.]+%)\s+([\d.]+%)\s*$"
    )
    results: list[dict] = []
    with pdfplumber.open(pdf_path) as pdf:
        for pn in range(pages[0] - 1, pages[1]):
            for line in (pdf.pages[pn].extract_text() or "").splitlines():
                line = clean_text(line.strip())
                if line in {"England", "Wales", "Scotland", "Northern Ireland"}:
                    continue
                m = line_re.match(line)
                party_raw = None
                if m:
                    before, party_raw = m.group(1), m.group(2)
                else:
                    m2 = re.match(
                        r"^(.+)\s+Other\s+(hold|gain from \w+)\s+([\d,]+)\s+([\d.]+%)\s+([\d.]+%)\s*$",
                        line,
                    )
                    if m2:
                        before, party_raw = m2.group(1), "Other"
                if not party_raw:
                    continue
                words = before.split()
                if len(words) < 3:
                    continue
                const = " ".join(words[:-2])
                mp = " ".join(words[-2:])
                pid, label = map_hoc_party(party_raw)
                results.append(
                    {
                        "name": const,
                        "mp": mp,
                        "party": pid,
                        "partyLabel": label,
                        "nation": None,
                    }
                )
    return results


def parse_2001_block(text: str, gazetteer: list[str]) -> dict[str, dict]:
    header_re = re.compile(
        rf"(?:xx)?([A-Z][A-Za-z'&,.\- ]{{2,60}}?)\s+({HOC_PARTIES})\s+"
        r"(hold|gain(?:\s+from\s+\w+)?)"
    )
    win_re = re.compile(rf"([A-Za-z][A-Za-z' \-\.]{{1,45}}?)\s+\*\s+({HOC_PARTIES})")
    cand_re = re.compile(
        rf"^([A-Za-z][A-Za-z' \-\.]{{1,45}}?)\s+(?:\*\s+)?({HOC_PARTIES})\s+([\d,]+)",
        re.M,
    )

    def winner_from_block(block: str, header_party: str) -> tuple[str, str] | None:
        stars = list(win_re.finditer(block))
        for wm in stars:
            if wm.group(2) == header_party:
                return wm.group(1).strip(), wm.group(2)
        best: tuple[str, str] | None = None
        best_votes = -1
        for cm in cand_re.finditer(block):
            if cm.group(2) != header_party:
                continue
            votes = int(cm.group(3).replace(",", ""))
            if votes > best_votes:
                best_votes = votes
                best = (cm.group(1).strip(), cm.group(2))
        if best:
            return best
        if stars:
            wm = stars[0]
            return wm.group(1).strip(), wm.group(2)
        return None

    results: dict[str, dict] = {}
    headers = list(header_re.finditer(text))
    for i, m in enumerate(headers):
        raw = m.group(1).strip()
        if any(x in raw for x in ("Candidate Party", "Party Votes", "Share Change")):
            continue
        if re.search(r"\b(hold|gain)\b", raw):
            continue
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        block = text[m.end() : end]
        won = winner_from_block(block, m.group(2))
        if not won:
            continue
        name = resolve_constituency_name(raw, gazetteer)
        if not name:
            continue
        pid, label = map_hoc_party(won[1])
        results[name] = {
            "name": name,
            "mp": won[0],
            "party": pid,
            "partyLabel": label,
            "nation": None,
        }
    return results


def parse_2001(pdf_path: Path, pages: tuple[int, int], gazetteer: list[str]) -> list[dict]:
    all_results: dict[str, dict] = {}
    with pdfplumber.open(pdf_path) as pdf:
        for pn in range(pages[0] - 1, pages[1]):
            page = pdf.pages[pn]
            full = clean_text(page.extract_text() or "")
            all_results.update(parse_2001_block(full, gazetteer))
            mid = page.width / 2
            for bbox in ((0, 0, mid, page.height), (mid, 0, page.width, page.height)):
                col = clean_text(page.within_bbox(bbox).extract_text() or "")
                all_results.update(parse_2001_block(col, gazetteer))
    return list(all_results.values())


def parse_2017(pdf_path: Path, pages: tuple[int, int]) -> list[dict]:
    detail_re = re.compile(r"^([\d,]+)\s+([\d.]+%)\s+(.+?)\s+(No|Yes)$")
    rows: list[list] = []
    with pdfplumber.open(pdf_path) as pdf:
        for pn in range(pages[0] - 1, pages[1]):
            for table in pdf.pages[pn].extract_tables() or []:
                for row in table:
                    if not row or not row[0]:
                        continue
                    if str(row[0]).startswith("Constituency"):
                        continue
                    rows.append(row)

    results: list[dict] = []
    for row in rows:
        names = clean_text(str(row[0])).split("\n")
        parties1 = clean_text(str(row[1] or "")).split("\n")
        parties2 = clean_text(str(row[2] or "")).split("\n")
        details = clean_text(str(row[3] or "")).split("\n")
        count = max(len(names), len(parties1), len(parties2), len(details))
        while len(parties1) < count:
            parties1.append(parties1[-1] if parties1 else "")
        while len(parties2) < count:
            parties2.append(parties2[-1] if parties2 else "")
        while len(details) < count:
            details.append(details[-1] if details else "")

        for i in range(count):
            name = names[i] if i < len(names) else names[-1]
            dm = detail_re.match(details[i].strip())
            if not dm:
                continue
            mp = dm.group(3).strip()
            pid, label = map_hoc_party(parties1[i].strip())
            results.append(
                {
                    "name": name.strip(),
                    "mp": mp,
                    "party": pid,
                    "partyLabel": label,
                    "nation": None,
                }
            )
    return results


def rebuild_index(all_ids: list[str]) -> None:
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


def import_election(
    fetch_mod,
    election_id: str,
    pdf_path: Path,
    pages: tuple[int, int],
    gazetteer: list[str] | None = None,
) -> int:
    print(f"Importing {election_id} from {pdf_path.name} (pages {pages[0]}-{pages[1]})…")

    if election_id == "1997":
        constituencies = parse_1997(pdf_path, pages)
        hex_file = None
    elif election_id == "2001":
        if not gazetteer:
            raise ValueError("2001 import requires a constituency gazetteer")
        constituencies = parse_2001(pdf_path, pages, gazetteer)
        hex_file = None
    elif election_id == "2017":
        constituencies = parse_2017(pdf_path, pages)
        hex_file = "uk-constituencies-2010.hexjson"
    else:
        raise ValueError(f"Unsupported election {election_id}")

    if not constituencies:
        raise RuntimeError(f"No constituencies parsed for {election_id}")

    out_path = OUT_DIR / f"{election_id}.json"
    if out_path.exists():
        prev = json.loads(out_path.read_text(encoding="utf-8"))
        if prev.get("totalSeats", 0) > len(constituencies):
            print(
                f"  → kept existing {prev['totalSeats']} constituencies "
                f"(new import only {len(constituencies)})"
            )
            return prev["totalSeats"]

    source = f"House of Commons Research Paper PDF ({pdf_path.name}, pp. {pages[0]}-{pages[1]})"
    payload = fetch_mod.build_election_json(election_id, constituencies, hex_file, source)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        f"  → {len(constituencies)} constituencies "
        f"({payload['matchedHexes']} hex-matched)"
    )
    return len(constituencies)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import HoC PDF constituency results")
    parser.add_argument("--election", choices=["1997", "2001", "2017"])
    parser.add_argument("--pdf", type=Path)
    parser.add_argument("--pages", help="Page range, e.g. 83-93")
    parser.add_argument("--all-defaults", action="store_true")
    args = parser.parse_args()

    fetch_mod = load_fetch_module()
    fetch_mod.download_hex_layouts()

    gazetteer: list[str] | None = None
    if args.all_defaults or args.election in (None, "1997", "2001"):
        pdf97, pages97 = DEFAULT_PDFS["1997"]
        if pdf97.exists():
            gazetteer = build_gazetteer_from_1997(pdf97, pages97)
        else:
            print(f"Warning: 1997 PDF not found at {pdf97}")

    targets: list[tuple[str, Path, tuple[int, int]]] = []
    if args.all_defaults:
        for eid, (pdf_path, pages) in DEFAULT_PDFS.items():
            targets.append((eid, pdf_path, pages))
    elif args.election:
        if not args.pdf or not args.pages:
            if args.election in DEFAULT_PDFS:
                pdf_path, pages = DEFAULT_PDFS[args.election]
            else:
                parser.error("--pdf and --pages required for custom import")
                return
        else:
            pdf_path = args.pdf
            pages = parse_pages_arg(args.pages)
        targets.append((args.election, pdf_path, pages))
    else:
        parser.error("Specify --election or --all-defaults")
        return

    for election_id, pdf_path, pages in targets:
        if not pdf_path.exists():
            print(f"  ! Skipping {election_id}: PDF not found at {pdf_path}")
            continue
        try:
            import_election(fetch_mod, election_id, pdf_path, pages, gazetteer)
        except Exception as exc:
            print(f"  ! Failed {election_id}: {exc}")

    # Apply Wikipedia / ODI hex layouts when available (1997/2001/2005/2010)
    try:
        spec = importlib.util.spec_from_file_location(
            "build_wikipedia_hex_layout",
            ROOT / "scripts" / "build-wikipedia-hex-layout.py",
        )
        hex_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(hex_mod)
        for election_id, boundary in hex_mod.ELECTION_LAYOUT.items():
            if (HEX_DIR / f"uk-constituencies-{boundary}.hexjson").exists():
                hex_mod.apply_layout_to_election(election_id, boundary)
        for election_id in ("2015", "2017", "2019"):
            if (HEX_DIR / "uk-constituencies-2010.hexjson").exists():
                hex_mod.apply_layout_to_election(election_id, "2010")
    except Exception as exc:
        print(f"  ! Hex layout apply skipped: {exc}")

    all_ids = (
        list(fetch_mod.BATCH_ELECTIONS.keys())
        + list(fetch_mod.INDIVIDUAL_ELECTIONS.keys())
        + ["2019", "2024"]
    )
    rebuild_index(all_ids)
    print("Done.")


if __name__ == "__main__":
    main()
