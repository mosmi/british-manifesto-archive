#!/usr/bin/env python3
"""
build-seo-data.py

Derives data/seo.json from the site's existing sources of truth:
  - js/data.js                  -> PARTIES, ELECTIONS (parsed, not duplicated)
  - data/manifestos-index.json  -> per-manifesto `label`

The edge middleware (functions/_middleware.js) fetches the resulting
data/seo.json to build per-page titles, descriptions, canonical URLs and
JSON-LD, and to validate dynamic route IDs so unknown pages return a true 404.

Run after any change to parties, elections, or the manifesto index:
  python3 scripts/build-seo-data.py

Note: this parses the literal field values out of data.js with targeted
regexes (data.js is the single source of truth). It deliberately does NOT
execute the JS. If the formatting of data.js changes substantially, re-check
the regexes below.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_JS = ROOT / "js" / "data.js"
MANIFESTOS_INDEX = ROOT / "data" / "manifestos-index.json"
OUT = ROOT / "data" / "seo.json"

SITE_URL = "https://www.manifestos.org.uk"
SITE_NAME = "The British Manifesto Archive"

MONTHS = {
    "january": "01", "february": "02", "march": "03", "april": "04",
    "may": "05", "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
}


def to_iso_date(human: str | None) -> str | None:
    """'5 July 1945' -> '1945-07-05' (for schema.org Event.startDate)."""
    if not human:
        return None
    m = re.match(r"^\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})\s*$", human)
    if not m:
        return None
    month = MONTHS.get(m.group(2).lower())
    if not month:
        return None
    return f"{m.group(3)}-{month}-{int(m.group(1)):02d}"


def slice_block(text: str, start_marker: str, end_marker: str) -> str:
    start = text.find(start_marker)
    if start == -1:
        raise ValueError(f"marker not found: {start_marker!r}")
    end = text.find(end_marker, start + len(start_marker))
    if end == -1:
        end = len(text)
    return text[start:end]


def parse_named_map(block: str, name_field: str) -> dict:
    """Extract {top-level-id: <name_field value>} from a simple object block."""
    key_re = re.compile(r"^  ([a-z][a-z0-9-]*):\s*\{", re.M)
    field_re = re.compile(rf"{name_field}:\s*'([^']*)'")
    matches = list(key_re.finditer(block))
    out = {}
    for i, m in enumerate(matches):
        seg_end = matches[i + 1].start() if i + 1 < len(matches) else len(block)
        seg = block[m.end():seg_end]
        fm = field_re.search(seg)
        out[m.group(1)] = fm.group(1) if fm else None
    return out


def parse_parties(text: str) -> dict:
    """Extract {id: {name, shortName, color}} from the PARTIES block."""
    block = slice_block(text, "const PARTIES", "const NATIONS")
    # id, name and shortName appear together (same line) per entry.
    entry_re = re.compile(
        r"id:\s*'([^']+)',\s*name:\s*'([^']*)',\s*shortName:\s*'([^']*)'"
    )
    color_re = re.compile(r"color:\s*'([^']*)'")
    matches = list(entry_re.finditer(block))
    parties = {}
    for i, m in enumerate(matches):
        pid, name, short = m.group(1), m.group(2), m.group(3)
        # Scope the colour search to this entry only.
        seg_end = matches[i + 1].start() if i + 1 < len(matches) else len(block)
        seg = block[m.end():seg_end]
        cm = color_re.search(seg)
        parties[pid] = {
            "name": name,
            "shortName": short,
            "color": cm.group(1) if cm else None,
        }
    return parties


def parse_elections(text: str) -> dict:
    """Extract {id: {displayYear, year, date, isoDate, winner}}."""
    block = slice_block(text, "const ELECTIONS", "\n];")
    entry_re = re.compile(
        r"id:\s*'([^']+)',\s*year:\s*(\d+),\s*displayYear:\s*'([^']*)',"
        r"\s*date:\s*'([^']*)'"
    )
    winner_re = re.compile(r"winner:\s*'([^']*)'")
    matches = list(entry_re.finditer(block))
    elections = {}
    for i, m in enumerate(matches):
        eid, year, display, date = m.groups()
        seg_end = matches[i + 1].start() if i + 1 < len(matches) else len(block)
        seg = block[m.end():seg_end]
        wm = winner_re.search(seg)
        elections[eid] = {
            "displayYear": display,
            "year": int(year),
            "date": date or None,
            "isoDate": to_iso_date(date),
            "winner": wm.group(1) if wm else None,
        }
    return elections


def main() -> None:
    text = DATA_JS.read_text(encoding="utf-8")

    parties = parse_parties(text)
    # `others` is a catch-all bucket, not a standalone page (mirrors the
    # sitemap, which excludes /party/others).
    parties.pop("others", None)
    elections = parse_elections(text)
    nations = parse_named_map(
        slice_block(text, "const NATIONS", "const ELECTIONS"), "name")
    devolved = parse_named_map(
        slice_block(text, "const DEVOLVED_PORTALS", "\n};"), "label")

    if not parties or not elections:
        print("ERROR: failed to parse parties/elections from data.js "
              f"(parties={len(parties)}, elections={len(elections)}). "
              "Check the regexes in build-seo-data.py.", file=sys.stderr)
        sys.exit(1)

    manifestos = json.loads(MANIFESTOS_INDEX.read_text(encoding="utf-8"))
    manifesto_map = {
        f"{item['electionId']}/{item['partyId']}": {
            "label": item.get("label"),
            "electionId": item["electionId"],
            "partyId": item["partyId"],
        }
        for item in manifestos
    }

    seo = {
        "site": {"url": SITE_URL, "name": SITE_NAME},
        "parties": parties,
        "elections": elections,
        "nations": nations,
        "devolved": devolved,
        "manifestos": manifesto_map,
    }

    OUT.write_text(json.dumps(seo, ensure_ascii=False, separators=(",", ":")),
                   encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"  parties:    {len(parties)}")
    print(f"  elections:  {len(elections)}")
    print(f"  nations:    {len(nations)}")
    print(f"  devolved:   {len(devolved)}")
    print(f"  manifestos: {len(manifesto_map)}")


if __name__ == "__main__":
    main()
