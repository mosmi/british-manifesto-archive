#!/usr/bin/env python3
"""
Import processed manifesto Markdown from the source archive into this site.

Copies source .md files to manifestos/{electionId}/{partyId}/manifesto.md
(including YAML frontmatter), maps source party/election IDs to site conventions,
and regenerates data/manifestos-index.json.

Usage:
  python scripts/import-manifestos.py
  python scripts/import-manifestos.py --dry-run
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = Path("/Users/mosmi/Cursor/Projects/Manifestos/Markdown versions")
PROCESS_SCRIPT = SOURCE_ROOT / "process_manifestos.py"
MANIFESTOS_DIR = ROOT / "manifestos"
INDEX_PATH = ROOT / "data" / "manifestos-index.json"
DATA_JS = ROOT / "js" / "data.js"

# Site election IDs (1945 general elections onward)
SITE_ELECTIONS: set[str] = {
    "1945", "1950", "1951", "1955", "1959", "1964", "1966", "1970",
    "feb1974", "oct1974", "1979", "1983", "1987", "1992", "1997",
    "2001", "2005", "2010", "2015", "2017", "2019", "2024",
}

SOURCE_ELECTION_TO_SITE = {
    "1974-february": "feb1974",
    "1974-october": "oct1974",
}

# Source party_id (from process_manifestos.py) → site party_id (js/data.js)
SOURCE_PARTY_TO_SITE: dict[str, str] = {
    "conservative": "conservative",
    "labour": "labour",
    "liberal": "libdem",
    "green": "green",
    "loony": "omrlp",
    "bnp": "bnp",
    "brexit-party": "reform",
    "co-operative": "cooperative",
    "reform": "reform",
    "respect": "respect",
    "ukip": "ukip",
    "pirate": "pirate",
    "nha": "nha",
    "womens-equality": "wep",
    "workers-party": "workersparty",
    "snp": "snp",
    "scottish-conservative": "scottishcon",
    "scottish-labour": "scottishlab",
    "scottish-lib-dem": "scottishlibdem",
    "scottish-greens": "scottishgrn",
    "scottish-socialist": "ssp",
    "plaid": "plaid",
    "welsh-conservative": "welshcon",
    "welsh-labour": "welshlab",
    "welsh-lib-dem": "welshlibdem",
    "alliance": "alliance",
    "dup": "dup",
    "green-ni": "gpni",
    "sdlp": "sdlp",
    "sinn-fein": "sinnfein",
    "tuv": "tuv",
    "uup": "uup",
    "alba": "alba",
}

SKIP_SOURCE_PARTIES = {"gwlad-gwlad", "conservative-ni"}

ELECTION_DISPLAY_YEAR: dict[str, str] = {
    "feb1974": "Feb 1974",
    "oct1974": "Oct 1974",
}

# Historical source party names for carousel labels (when site id differs)
SOURCE_PARTY_LABELS: dict[str, str] = {
    "brexit-party": "Brexit Party",
    "loony": "Monster Raving Loony Party",
    "scottish-socialist": "Scottish Socialist Party",
}

LIBERAL_LINEAGE = {
    "libdem": ("Liberal", "Alliance", "Liberal Democrats"),
    "welshlibdem": ("Liberal", "Alliance", "Welsh Liberal Democrats"),
    "scottishlibdem": ("Liberal", "Alliance", "Scottish Liberal Democrats"),
}

PRIMARY_PARTIES = ("conservative", "labour", "libdem")


def load_process_manifestos():
    spec = importlib.util.spec_from_file_location("process_manifestos", PROCESS_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {PROCESS_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_parties_from_data_js() -> dict[str, dict]:
    """Extract party shortName and isPrimary from js/data.js."""
    text = DATA_JS.read_text(encoding="utf-8")
    start = text.index("const PARTIES = {")
    end = text.index("const NATIONS", start)
    block = text[start:end]
    parties: dict[str, dict] = {}
    for key, short_single, short_double, is_primary in re.findall(
        r"^\s{2}(\w+):\s*\{[^}]*?shortName:\s*(?:'([^']*)'|\"([^\"]*)\")[^}]*?isPrimary:\s*(true|false)",
        block,
        re.MULTILINE | re.DOTALL,
    ):
        short_name = short_single or short_double
        parties[key] = {
            "shortName": short_name,
            "isPrimary": is_primary == "true",
        }
    return parties


def party_label(source_party_id: str, site_party_id: str, election_year: int, parties: dict) -> str:
    if source_party_id in SOURCE_PARTY_LABELS:
        name = SOURCE_PARTY_LABELS[source_party_id]
    elif site_party_id in LIBERAL_LINEAGE:
        liberal, alliance, modern = LIBERAL_LINEAGE[site_party_id]
        if election_year < 1983:
            name = liberal
        elif election_year in (1983, 1987):
            name = alliance
        else:
            name = modern
    else:
        name = parties.get(site_party_id, {}).get("shortName", site_party_id)

    display_year = str(election_year)
    return f"{name} Manifesto {display_year}"


def election_sort_key(election_id: str) -> tuple[int, int]:
    if election_id == "feb1974":
        return (1974, 1)
    if election_id == "oct1974":
        return (1974, 2)
    return (int(election_id), 0)


def index_sort_key(entry: dict, parties: dict) -> tuple:
    eid = entry["electionId"]
    pid = entry["partyId"]
    year_key = election_sort_key(eid)
    is_primary = 0 if pid in PRIMARY_PARTIES else 1
    short = parties.get(pid, {}).get("shortName", pid)
    return (-year_key[0], -year_key[1], is_primary, short)


def discover_source_files(pm) -> list[Path]:
    return sorted(
        p
        for p in SOURCE_ROOT.rglob("*.md")
        if p.parent.name in pm.FOLDER_TO_PARTY_ID
        and not pm.is_excluded(p)
        and not any(part.startswith(".") for part in p.relative_to(SOURCE_ROOT).parts)
    )


def import_manifestos(dry_run: bool = False) -> dict:
    pm = load_process_manifestos()
    parties = parse_parties_from_data_js()

    imported: list[dict] = []
    skipped: list[dict] = []
    errors: list[dict] = []

    for path in discover_source_files(pm):
        rel = str(path.relative_to(SOURCE_ROOT))
        try:
            source_election_id, source_party_id = pm.parse_filename(path)
        except ValueError as exc:
            errors.append({"file": rel, "reason": str(exc)})
            continue

        year = int(source_election_id.split("-")[0])
        if year < 1945:
            skipped.append({"file": rel, "reason": "pre-1945"})
            continue

        if source_party_id in SKIP_SOURCE_PARTIES:
            skipped.append({"file": rel, "reason": f"no site party ({source_party_id})"})
            continue

        site_election_id = SOURCE_ELECTION_TO_SITE.get(source_election_id, source_election_id)
        if site_election_id not in SITE_ELECTIONS:
            skipped.append({"file": rel, "reason": f"election not on site ({site_election_id})"})
            continue

        site_party_id = SOURCE_PARTY_TO_SITE.get(source_party_id)
        if not site_party_id:
            skipped.append({"file": rel, "reason": f"unmapped party ({source_party_id})"})
            continue

        if site_party_id not in parties:
            skipped.append({"file": rel, "reason": f"party id missing from data.js ({site_party_id})"})
            continue

        content = path.read_text(encoding="utf-8")
        dest = MANIFESTOS_DIR / site_election_id / site_party_id / "manifesto.md"

        if not dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")

        imported.append({
            "source": rel,
            "electionId": site_election_id,
            "partyId": site_party_id,
            "sourcePartyId": source_party_id,
            "year": year,
            "dest": str(dest.relative_to(ROOT)),
            "label": party_label(source_party_id, site_party_id, year, parties),
        })

    index_entries = [
        {
            "electionId": item["electionId"],
            "partyId": item["partyId"],
            "label": item["label"],
        }
        for item in sorted(imported, key=lambda x: index_sort_key(x, parties))
    ]

    # Preserve devolved election entries from the existing index
    if INDEX_PATH.exists():
        try:
            existing = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
            devolved_entries = [
                entry for entry in existing
                if entry.get("electionId") not in SITE_ELECTIONS
            ]
            # Merge and avoid duplicates
            seen = {(e["electionId"], e["partyId"]) for e in index_entries}
            for entry in devolved_entries:
                key = (entry["electionId"], entry["partyId"])
                if key not in seen:
                    index_entries.append(entry)
                    seen.add(key)
        except Exception as e:
            print(f"WARN: Failed to parse existing index: {e}", file=sys.stderr)

    if not dry_run:
        INDEX_PATH.write_text(
            json.dumps(index_entries, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    return {
        "imported": imported,
        "skipped": skipped,
        "errors": errors,
        "index_entries": index_entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Import manifesto Markdown into the site.")
    parser.add_argument("--dry-run", action="store_true", help="Analyse only; do not write files.")
    args = parser.parse_args()

    if not SOURCE_ROOT.is_dir():
        print(f"ERROR: source directory not found: {SOURCE_ROOT}", file=sys.stderr)
        return 1
    if not PROCESS_SCRIPT.is_file():
        print(f"ERROR: process_manifestos.py not found: {PROCESS_SCRIPT}", file=sys.stderr)
        return 1

    result = import_manifestos(dry_run=args.dry_run)

    print(f"Imported: {len(result['imported'])} manifestos")
    print(f"Unique election/party pairs: {len({(i['electionId'], i['partyId']) for i in result['imported']})}")
    print(f"Skipped: {len(result['skipped'])}")
    print(f"Errors: {len(result['errors'])}")

    if result["skipped"]:
        print("\nSkipped files:")
        for item in result["skipped"]:
            print(f"  {item['file']}: {item['reason']}")

    if result["errors"]:
        print("\nErrors:")
        for item in result["errors"]:
            print(f"  {item['file']}: {item['reason']}")

    if args.dry_run:
        print("\n(dry-run — no files written)")
    else:
        print(f"\nWrote index: {INDEX_PATH.relative_to(ROOT)} ({len(result['index_entries'])} entries)")

    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
