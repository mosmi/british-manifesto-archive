#!/usr/bin/env python3
"""Build Greater London Council HexJSON files (1964–1981).

Two eras:
  1973–1981  92 single-member divisions (grid: data/hex/glc-grid.json)
  1964–1970  32 multi-member boroughs  (grid: data/hex/glc-borough-grid.json)

Results are parsed from the official GLC Intelligence Unit PDFs under
  ~/Claude/Projects/Manifestos/Original documents/Devolved Elections/London/
  1964-1981 Greater London Council Election Materials/

Usage:
  python3 scripts/build-glc-hex.py           # all years
  python3 scripts/build-glc-hex.py --era 92  # 1973–81 only
  python3 scripts/build-glc-hex.py --era 32  # 1964–70 only
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from difflib import get_close_matches
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "hex" / "glc"
GRID_92 = ROOT / "data" / "hex" / "glc-grid.json"
GRID_32 = ROOT / "data" / "hex" / "glc-borough-grid.json"
PDF_DIR = Path.home() / (
    "Claude/Projects/Manifestos/Original documents/Devolved Elections/London/"
    "1964-1981 Greater London Council Election Materials"
)
CACHE_DIR = ROOT / "data" / "cache" / "glc-pdf-text"

PDFS = {
    1964: "GLC_1964-4-9.pdf",
    1967: "GLC_1967-4-13.pdf",
    1970: "GLCE_1970-4-9.pdf",
    1973: "GLCE_1973-4-12.pdf",
    1977: "GLCE_1977-5-5.pdf",
    1981: "GLCE_1981-5-7.pdf",
}

PARTY_MAP = {
    "lab": "labour",
    "labour": "labour",
    "labcp": "labour",  # Labour Co-operative (OCR)
    "con": "conservative",
    "can": "conservative",  # OCR
    "conservative": "conservative",
    "lib": "libdem",
    "liberal": "libdem",
    "ld": "libdem",
}

# Expected councillor seat totals from archive JSON
EXPECTED = {
    1964: {"labour": 64, "conservative": 36},
    1967: {"conservative": 82, "labour": 18},
    1970: {"conservative": 65, "labour": 35},
    1973: {"labour": 58, "conservative": 32, "libdem": 2},
    1977: {"conservative": 64, "labour": 28},
    1981: {"labour": 50, "conservative": 41, "libdem": 1},
}

# OCR / wrapping aliases → canonical grid key (normalized)
NAME_ALIASES = {
    "stocknewington": "hackneynorthandstokenewington",
    "hackneynorthandstocknewington": "hackneynorthandstokenewington",
    "shoreditch": "hackneysouthandshoreditch",
    "hackneysouthandshoreditch": "hackneysouthandshoreditch",
    "cityoflondonandwestmistersouth": "cityoflondonandwestminstersouth",
    "cityoflondonandwestminstersouth": "cityoflondonandwestminstersouth",
    "ravensbourne": "ravensbourne",
    "ravensboume": "ravensbourne",
    "ruislipnorthwood": "ruislipnorthwood",
    "kingstonuponthames": "kingstonuponthames",
    "bethnalgreenbow": "bethnalgreenandbow",
    "holbornandstpancrassouth": "holbornandstpancrassouth",
    "islingtonsouthfinsbury": "islingtonsouthandfinsbury",
    "wansteadwoodford": "wansteadandwoodford",
    "brentfordisleworth": "brentfordandisleworth",
    "hayesharlington": "hayesandharlington",
    "felthamheston": "felthamandheston",
    "mitchammorden": "mitchamandmorden",
    "suttoncheam": "suttonandcheam",
    "stepneypoplar": "stepneyandpoplar",
    "erithcrayford": "erithandcrayford",
    "westminsterandthecityoflondon": "westminsterandthecityoflondon",
    "kensingtonandchelsea": "kensingtonandchelsea",
    "richmonduponthames": "richmonduponthames",
}


def norm(s: str) -> str:
    s = s.lower().replace("&", "and").replace("st.", "st ")
    s = s.replace("westmister", "westminster")
    # Common OCR confusions in GLCE booklets
    s = s.replace("pancrols", "pancras").replace("chea~", "cheam").replace("cheah", "cheam")
    s = s.replace("lewishclm", "lewisham").replace("newhclim", "newham").replace("newhclm", "newham")
    s = s.replace("newhclill", "newham").replace("mitchalll", "mitcham").replace("horden", "morden")
    s = s.replace("mi tchalll", "mitcham").replace("and horden", "and morden")
    s = re.sub(r"\s+", " ", s)
    key = re.sub(r"[^a-z0-9]+", "", s)
    return NAME_ALIASES.get(key, key)


def lookup_party(parties: dict[str, str], nk: str) -> str | None:
    if nk in parties:
        return parties[nk]
    for pk, pv in parties.items():
        if pk in nk or nk in pk:
            return pv
    hits = get_close_matches(nk, parties.keys(), n=1, cutoff=0.75)
    return parties[hits[0]] if hits else None


def pdf_text(year: int) -> str:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache = CACHE_DIR / f"{year}.txt"
    if cache.exists():
        return cache.read_text(encoding="utf-8", errors="replace")
    pdf = PDF_DIR / PDFS[year]
    if not pdf.exists():
        raise FileNotFoundError(pdf)
    print(f"Extracting text from {pdf.name}...")
    text = subprocess.check_output(
        ["pdftotext", "-layout", str(pdf), "-"],
        text=True,
        errors="replace",
    )
    cache.write_text(text, encoding="utf-8")
    return text


def join_wrapped_lines(text: str) -> list[str]:
    """Join constituency name wraps (e.g. 'Holborn and' + '  St Pancras South … Lab')."""
    lines = text.splitlines()
    out = []
    i = 0
    party_end = re.compile(r"(Lab|Con|Lib|Can|LAB|CON|LIB|LABCP)\.?\s*$", re.I)
    while i < len(lines):
        line = lines[i].rstrip()
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        # Name wrap: "Holborn and" / "City of London and" then continuation with figures
        if (
            line.strip()
            and not re.search(r"\d", line)
            and (
                line.strip().lower().endswith(" and")
                or line.strip().lower().endswith(" and the")
                or len(line.strip().split()) >= 2
            )
            and party_end.search(nxt)
            and re.search(r"\d", nxt)
        ):
            out.append(line.strip() + " " + nxt.strip())
            i += 2
            continue
        # Indented continuation after a name-only previous line
        if (
            out
            and (line.startswith(" ") or line.startswith("\t"))
            and out[-1].strip()
            and not re.search(r"\d", out[-1])
            and re.search(r"\d", line)
            and party_end.search(line)
        ):
            out[-1] = out[-1].rstrip() + " " + line.strip()
            i += 1
            continue
        out.append(line)
        i += 1
    return out


def parse_fptp_summary(text: str) -> dict[str, str]:
    """Return {norm_name: party_id} from the constituency summary table."""
    lines = join_wrapped_lines(text)
    body = "\n".join(lines)
    # Prefer the last Barking data row (summary tables sit late in the booklet)
    matches = list(re.finditer(r"(?m)^Barking\s+[\d,\.]+", body))
    chunk = body[matches[-1].start() :] if matches else body

    winners: dict[str, str] = {}
    # Name ends at whitespace before a digit column; party is the final token.
    row_re = re.compile(
        r"^(?P<name>[A-Za-z][A-Za-z0-9\s\.\-\'&/~]*?[A-Za-z~])\s+\d.*\s+(?P<party>Lab|Con|Lib|Can|LAB|CON|LIB|LABCP)\.?\s*$",
        re.I,
    )
    for line in chunk.splitlines():
        line = line.strip()
        if not line or not re.search(r"\d", line):
            continue
        m = row_re.match(line)
        if not m:
            continue
        name = re.sub(r"\s+", " ", m.group("name")).strip().rstrip("*")
        # Borough totals are usually ALL CAPS short labels
        if name.isupper() and not any(c.islower() for c in name):
            continue
        if "constituency" in name.lower() or name.lower().startswith("borough"):
            continue
        if name.lower().startswith("notes") or "population" in name.lower():
            continue
        ptok = m.group("party").lower().rstrip(".")
        party = PARTY_MAP.get(ptok)
        if not party:
            continue
        winners[norm(name)] = party
    return winners


def parse_fptp_candidate_names(text: str) -> dict[str, tuple[str, str]]:
    """Best-effort {norm_name: (winner_person, party)} from candidate listings."""
    # Match CONSTITUENCY NAME (electorate) headers — may be OCR-spaced
    header_re = re.compile(
        r"(?m)^([A-Z][A-Z\s\.\-\'&/]{2,60}?)\s*\(([\d,\.]+)\)\s*"
    )
    # Candidate line: Name  Party  votes
    cand_re = re.compile(
        r"^([A-Za-z][A-Za-z\s\.\-\'\(\),]+?)\s{2,}(Lab|Con|Can|Lib|Comm|Ind|Act|SPGB|Nat\.?\s*Fr|NIP|RR|ICP|NPC)\s+([\d,\.]+)\s*$",
        re.I,
    )

    results: dict[str, list[tuple[str, str, int]]] = {}
    current = None
    for raw in text.splitlines():
        line = raw.rstrip()
        # Two-column pages: split on large gaps
        parts = re.split(r"\s{6,}", line.strip()) if line.strip() else [""]
        for part in parts:
            part = part.strip()
            if not part:
                continue
            hm = header_re.match(part) or header_re.match(part.upper() if part[:3].isupper() else "")
            # Broader header: ALL CAPS name with (digits)
            hm2 = re.match(r"^([A-Z][A-Z\s\.\-\'&/]+?)\s*\(([\d,\.]+)\)\s*$", part)
            if hm2:
                current = norm(hm2.group(1))
                results.setdefault(current, [])
                continue
            if not current:
                continue
            cm = cand_re.match(part)
            if not cm:
                continue
            person = re.sub(r"\s+", " ", cm.group(1)).strip(" ,.")
            # Drop trailing titles noise
            person = re.sub(r",?\s*J\.?P\.?\s*$", "", person, flags=re.I).strip(" ,.")
            party_tok = cm.group(2).lower().replace(" ", "").rstrip(".")
            party = PARTY_MAP.get(party_tok)
            if not party:
                continue
            votes = int(re.sub(r"[^\d]", "", cm.group(3)) or "0")
            results[current].append((person, party, votes))

    winners: dict[str, tuple[str, str]] = {}
    for key, cands in results.items():
        if not cands:
            continue
        person, party, _ = max(cands, key=lambda x: x[2])
        winners[key] = (person, party)
    return winners


def build_fptp(year: int) -> dict:
    grid = json.loads(GRID_92.read_text(encoding="utf-8"))
    text = pdf_text(year)
    parties = parse_fptp_summary(text)
    names = parse_fptp_candidate_names(text)

    # Manual party overrides when OCR summary still misses a seat
    MANUAL_PARTY = {
        (1973, "croydonnortheast"): "labour",
        (1973, "croydonnorthwest"): "labour",
        (1973, "hackneynorthandstokenewington"): "labour",
        (1977, "cityoflondonandwestminstersouth"): "conservative",
        (1981, "lewishameast"): "labour",
        (1981, "mitchamandmorden"): "labour",
        (1981, "newhamnortheast"): "labour",
        (1981, "newhamsouth"): "labour",
        (1981, "suttonandcheam"): "conservative",
        (1981, "holbornandstpancrassouth"): "labour",
    }

    hexes = {}
    problems = []
    for key, cell in grid["hexes"].items():
        nk = norm(cell["n"])
        party = MANUAL_PARTY.get((year, nk)) or lookup_party(parties, nk)
        person_party = names.get(nk)
        if not person_party:
            hits = get_close_matches(nk, names.keys(), n=1, cutoff=0.75)
            if hits:
                person_party = names[hits[0]]

        if not party:
            problems.append(f"{year}: no party for {cell['n']}")
            party = "others"

        winner = person_party[0] if person_party else "Unknown"
        # Prefer summary party if candidate OCR disagrees on rare OCR errors
        if person_party and person_party[1] != party:
            # keep summary party, keep name if votes look plausible
            pass

        code = f"glc-{year}-{key.replace(' ', '-')}"
        hexes[code] = {
            "n": cell["n"],
            "q": cell["q"],
            "r": cell["r"],
            "winner": winner,
            "party": party,
        }

    counts = Counter(h["party"] for h in hexes.values())
    expected = EXPECTED[year]
    for pid, n in expected.items():
        if counts.get(pid, 0) != n:
            problems.append(f"{year}: {pid} seats hex={counts.get(pid, 0)} expected={n}")

    if len(hexes) != 92:
        problems.append(f"{year}: expected 92 hexes, got {len(hexes)}")

    return {"layout": "odd-r", "hexes": hexes}, problems, counts


# ── Borough multi-member era (1964–1970) ──────────────────────────

BOROUGH_MAGNITUDE = {
    "barking": 2,
    "barnet": 4,
    "bexley": 3,
    "brent": 4,
    "bromley": 4,
    "camden": 3,
    "croydon": 4,
    "ealing": 4,
    "enfield": 3,
    "greenwich": 3,
    "hackney": 3,
    "hammersmith": 3,
    "haringey": 3,
    "harrow": 3,
    "havering": 3,
    "hillingdon": 3,
    "hounslow": 3,
    "islington": 3,
    "kensington and chelsea": 3,
    "kingston upon thames": 2,
    "lambeth": 4,
    "lewisham": 4,
    "merton": 2,
    "newham": 3,
    "redbridge": 3,
    "richmond upon thames": 2,
    "southwark": 4,
    "sutton": 2,
    "tower hamlets": 2,
    "waltham forest": 3,
    "wandsworth": 4,
    "westminster and the city of london": 4,
}

def _all_con_except(lab_boroughs: dict[str, int | list[str]]) -> dict[str, list[str]]:
    """Build seats_list parties for every borough; lab_boroughs maps name→mag or explicit list."""
    out: dict[str, list[str]] = {}
    for b, mag in BOROUGH_MAGNITUDE.items():
        if b in lab_boroughs:
            spec = lab_boroughs[b]
            out[b] = list(spec) if isinstance(spec, list) else ["labour"] * int(spec)
        else:
            out[b] = ["conservative"] * mag
        assert len(out[b]) == mag, (b, out[b], mag)
    return out


# Per-borough elected parties (bloc vote; rare splits listed explicitly).
# 1964: Wikipedia borough results. 1967/1970: Wikipedia narrative + official seat totals
# (Greenwich 1967 split; Lambeth 1970 one Labour gain). PDF text supplies names when OCR allows.
BOROUGH_SEAT_PARTIES: dict[int, dict[str, list[str]]] = {
    1964: _all_con_except({
        "barking": 2, "bexley": 3, "brent": 4, "camden": 3, "ealing": 4,
        "greenwich": 3, "hackney": 3, "hammersmith": 3, "haringey": 3,
        "havering": 3, "hillingdon": 3, "hounslow": 3, "islington": 3,
        "lambeth": 4, "lewisham": 4, "newham": 3, "southwark": 4,
        "tower hamlets": 2, "waltham forest": 3, "wandsworth": 4,
    }),
    1967: _all_con_except({
        "barking": 2, "hackney": 3, "islington": 3, "newham": 3,
        "southwark": 4, "tower hamlets": 2,
        # Official diagram / by-election note: 1 Lab + 2 Con, then Lab gained one in by-election
        "greenwich": ["labour", "conservative", "conservative"],
    }),
    1970: _all_con_except({
        "barking": 2, "hackney": 3, "islington": 3, "newham": 3,
        "southwark": 4, "tower hamlets": 2, "greenwich": 3, "camden": 3,
        "hammersmith": 3, "lewisham": 4, "wandsworth": 4,
        # Labour won back one seat in Lambeth
        "lambeth": ["labour", "conservative", "conservative", "conservative"],
    }),
}


def _borough_header_map() -> dict[str, str]:
    """Map normalized header tokens → BOROUGH_MAGNITUDE key (normalized)."""
    aliases = {
        "westminstercityof": "westminsterandthecityoflondon",
        "westminsterwiththecityoflondonandthetemples": "westminsterandthecityoflondon",
        "westminstercityofwiththecityoflondonandthetemples": "westminsterandthecityoflondon",
        "westminstereetc": "westminsterandthecityoflondon",
        "westminster": "westminsterandthecityoflondon",
        "kensingtonchelsea": "kensingtonandchelsea",
        "richmondthames": "richmonduponthames",
        "kingstonthames": "kingstonuponthames",
        "towerhamlets": "towerhamlets",
        "walthamforest": "walthamforest",
        "croy don": "croydon",  # unused; OCR spaces stripped by norm
    }
    out = {norm(b): norm(b) for b in BOROUGH_MAGNITUDE}
    out.update(aliases)
    return out


def _match_borough_header(cell: str, header_map: dict[str, str]) -> str | None:
    """Return norm borough key if cell is a section header (not a candidate)."""
    raw = cell.strip()
    if not raw:
        return None
    # Skip continuation/by-election notes that aren't new borough starts for totals
    if re.search(r"by[\-\s]?election", raw, re.I):
        return None
    cleaned = re.sub(r"\s*[-–]\s*Continued.*$", "", raw, flags=re.I)
    cleaned = re.sub(r"\s*\(.*?\)\s*$", "", cleaned).strip()
    if not cleaned:
        return None
    # Headers are short-ish and mostly alphabetic
    if re.search(r"\d{2,}", cleaned):
        return None
    nk = norm(cleaned)
    if nk in header_map:
        return header_map[nk]
    # OCR: "CRO YDON", "WA LTHAM FOREST"
    nk2 = norm(re.sub(r"\s+", "", cleaned))
    if nk2 in header_map:
        return header_map[nk2]
    for key, canon in header_map.items():
        if len(key) >= 8 and (key == nk or key in nk or nk in key):
            return canon
    return None


def _parse_borough_candidate(cell: str) -> tuple[str, str, int] | None:
    """Parse one candidate cell → (name, party_id, votes) or None."""
    cell = cell.strip()
    if not cell or len(cell) < 6:
        return None
    # Strip leading/trailing leader dots used as leaders in 1964/67 tables
    cell = re.sub(r"\s*\.\.\s*", " ", cell)
    cell = re.sub(r"\s+", " ", cell).strip()

    # 1964/67: Name (Lab.) 25,380   — Can. is OCR for Con.
    m = re.search(
        r"^(?P<name>.+?)\s*\((?P<party>Lab|Con|Can|Lib|Li\s*b|Comm|Ind)[^)]*\)\s*(?P<votes>[\d,]+)\s*$",
        cell,
        re.I,
    )
    if not m:
        # 1970: Name   Lab    20,236
        m = re.search(
            r"^(?P<name>.+?)\s+(?P<party>Lab|Con|Can|Lib|Comm|HBR|UM|SPGB|O\.?)\s+(?P<votes>[\d,]+)\s*$",
            cell,
            re.I,
        )
    if not m:
        return None
    person = m.group("name").strip(" ,.-")
    person = re.sub(r",?\s*(J\.?P\.?|O\.?B\.?E\.?|C\.?B\.?E\.?)\s*$", "", person, flags=re.I)
    person = re.sub(r"\s+", " ", person).strip(" ,.")
    if len(person) < 2 or person.lower() in {"table", "number", "successful"}:
        return None
    ptok = re.sub(r"\s+", "", m.group("party").lower()).rstrip(".")
    party = PARTY_MAP.get(ptok)
    if not party:
        return None  # ignore Comm/HBR/etc. for slate selection (still need Lab/Con)
    votes = int(re.sub(r"[^\d]", "", m.group("votes") or "0") or "0")
    if votes <= 0:
        return None
    return person, party, votes


def _split_two_columns(line: str, mid: int = 52) -> tuple[str, str]:
    """Split a layout line into left/right columns (GLC booklets are dual-column)."""
    if len(line) < mid:
        return line.rstrip(), ""
    # Prefer a wide whitespace gap near the midpoint
    window = line[mid - 12 : mid + 16]
    gap = re.search(r"\s{3,}", window)
    if gap:
        cut = mid - 12 + gap.start() + gap.end() // 2
        # find actual gap start for cleaner cut
        cut = mid - 12 + gap.start()
        return line[:cut].rstrip(), line[cut:].strip()
    return line[:mid].rstrip(), line[mid:].strip()


def parse_borough_results(text: str, year: int) -> dict[str, list[tuple[str, str]]]:
    """
    Parse multi-member borough results into {norm_borough: [(name, party), ...]}.

    Booklets use a two-column layout. Successful candidates are listed first (heavy
    type in the printed PDF); we therefore take the first `magnitude` candidates in
    document order for each borough. Line-wrapped names are rejoined within a column.
    """
    header_map = _borough_header_map()
    buckets: dict[str, list[tuple[str, str, int]]] = {norm(b): [] for b in BOROUGH_MAGNITUDE}

    left_b: str | None = None
    right_b: str | None = None
    pending: dict[str, str] = {"left": "", "right": ""}
    in_table = False

    def flush_pending(setter: str, borough: str | None) -> None:
        buf = pending[setter].strip()
        pending[setter] = ""
        if not buf or not borough:
            return
        parsed = _parse_borough_candidate(buf)
        if parsed:
            buckets[borough].append(parsed)

    def handle_cell(setter: str, cell: str) -> None:
        nonlocal left_b, right_b
        cell = cell.strip()
        if not cell:
            return
        hdr = _match_borough_header(cell, header_map)
        if hdr:
            flush_pending(setter, left_b if setter == "left" else right_b)
            if setter == "left":
                left_b = hdr
            else:
                right_b = hdr
            return
        emb = re.match(r"^([A-Z][A-Z\s&\-]{2,40}?)\s{2,}(.+)$", cell)
        if emb:
            hdr2 = _match_borough_header(emb.group(1), header_map)
            if hdr2:
                flush_pending(setter, left_b if setter == "left" else right_b)
                if setter == "left":
                    left_b = hdr2
                else:
                    right_b = hdr2
                cell = emb.group(2).strip()

        cur = left_b if setter == "left" else right_b
        if not cur:
            return

        # Continuation of a wrapped name (no party/votes yet)
        combined = (pending[setter] + " " + cell).strip() if pending[setter] else cell
        parsed = _parse_borough_candidate(combined)
        if parsed:
            pending[setter] = ""
            buckets[cur].append(parsed)
            return
        # Start/continue wrap buffer if this looks like a name fragment
        if not re.search(r"\d{3,}", cell) and re.search(r"[A-Za-z]{2,}", cell):
            pending[setter] = combined
        else:
            pending[setter] = ""

    for raw in text.splitlines():
        if re.search(r"\bTABLE\s*I\b", raw, re.I) or (
            not in_table and re.match(r"^BARKING\b", raw.strip())
        ):
            in_table = True
        if not in_table:
            continue
        if re.search(
            r"^(Number of electors|Summary of Election Results by Boroughs|"
            r"PERCENTAGE OF ELECTORS|Political Representation|TABLE\s*II\b)",
            raw.strip(),
            re.I,
        ):
            break
        if not raw.strip():
            continue

        left, right = _split_two_columns(raw)
        handle_cell("left", left)
        handle_cell("right", right)

    flush_pending("left", left_b)
    flush_pending("right", right_b)

    out: dict[str, list[tuple[str, str]]] = {}
    for bname, mag in BOROUGH_MAGNITUDE.items():
        bn = norm(bname)
        cands = buckets.get(bn, [])
        if not cands:
            continue
        seen: set[tuple[str, str, int]] = set()
        uniq: list[tuple[str, str, int]] = []
        for c in cands:
            if c in seen:
                continue
            seen.add(c)
            uniq.append(c)
        # Booklets list successful candidates first
        slate = uniq[:mag]
        out[bn] = [(p, party) for p, party, _ in slate]
    return out


def _names_for_parties(
    parsed: dict[str, list[tuple[str, str]]],
    borough_key: str,
    parties: list[str],
) -> list[str]:
    """Pick councillor names from OCR parse matching each seat's party."""
    pool = list(parsed.get(norm(borough_key), []))
    names: list[str] = []
    used: set[int] = set()
    for party in parties:
        found = None
        for i, (person, p) in enumerate(pool):
            if i in used or p != party:
                continue
            found = person
            used.add(i)
            break
        names.append(found or f"{party.title()} councillor")
    return names


def build_borough(year: int) -> tuple[dict, list[str], Counter]:
    if not GRID_32.exists():
        raise FileNotFoundError(f"Missing {GRID_32} — author borough grid first")
    if year not in BOROUGH_SEAT_PARTIES:
        raise KeyError(f"No curated borough seat parties for {year}")
    grid = json.loads(GRID_32.read_text(encoding="utf-8"))
    text = pdf_text(year)
    parsed = parse_borough_results(text, year)
    seat_parties = BOROUGH_SEAT_PARTIES[year]

    hexes = {}
    problems = []
    for key, cell in grid["hexes"].items():
        nk = norm(cell["n"])
        bname = None
        for name in BOROUGH_MAGNITUDE:
            if norm(name) == nk:
                bname = name
                break
        if not bname:
            problems.append(f"{year}: unknown borough {cell['n']}")
            continue
        parties = seat_parties[bname]
        names = _names_for_parties(parsed, bname, parties)
        party = Counter(parties).most_common(1)[0][0]
        code = f"glc-{year}-{key.replace(' ', '-')}"
        hexes[code] = {
            "n": cell["n"],
            "q": cell["q"],
            "r": cell["r"],
            "party": party,
            "winner": ", ".join(names),
            # Party-id strings for hexmap.js multi-seat dots (Stormont-style)
            "seats_list": list(parties),
        }

    counts = Counter()
    for h in hexes.values():
        for pid in h["seats_list"]:
            counts[pid] += 1

    expected = EXPECTED[year]
    for pid, n in expected.items():
        if counts.get(pid, 0) != n:
            problems.append(f"{year}: {pid} seats hex={counts.get(pid, 0)} expected={n}")

    total = sum(counts.values())
    if total != 100:
        problems.append(f"{year}: total seats {total}, expected 100")
    if len(hexes) != 32:
        problems.append(f"{year}: expected 32 boroughs, got {len(hexes)}")

    return {"layout": "odd-r", "hexes": hexes}, problems, counts


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--era", choices=["92", "32", "all"], default="all")
    args = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    all_problems: list[str] = []

    if args.era in ("92", "all"):
        if not GRID_92.exists():
            raise SystemExit(f"Missing {GRID_92}")
        for year in (1973, 1977, 1981):
            doc, problems, counts = build_fptp(year)
            path = OUT_DIR / f"{year}.hexjson"
            path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"{year}: wrote {path} ({len(doc['hexes'])} seats) {dict(counts)}")
            all_problems.extend(problems)

    if args.era in ("32", "all"):
        if not GRID_32.exists():
            print(f"Skip borough era — {GRID_32.name} not present yet", file=sys.stderr)
        else:
            for year in (1964, 1967, 1970):
                doc, problems, counts = build_borough(year)
                path = OUT_DIR / f"{year}.hexjson"
                path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                print(f"{year}: wrote {path} ({len(doc['hexes'])} boroughs, {sum(counts.values())} seats) {dict(counts)}")
                all_problems.extend(problems)

    if all_problems:
        print("\n=== PROBLEMS ===", file=sys.stderr)
        for p in all_problems:
            print("  " + p, file=sys.stderr)
        # Soft-fail on name OCR unknowns; hard-fail on seat total mismatches
        hard = [p for p in all_problems if "expected=" in p or "expected 92" in p or "expected 100" in p]
        if hard:
            raise SystemExit(f"\n{len(hard)} hard problem(s).")
        print(f"\n{len(all_problems)} soft warning(s) (names/OCR).", file=sys.stderr)
    print("\nDone. ✓")


if __name__ == "__main__":
    main()
