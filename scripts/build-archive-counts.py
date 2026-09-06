#!/usr/bin/env python3
"""Write data/archive-counts.json from catalog.jsonld + election indexes.

Counts unique manifesto folder keys, not raw DigitalDocument nodes (London
editions must not be counted twice). Hero stats read this file. Run after
scripts/build-seo-data.py (catalog rebuild).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "data" / "catalog.jsonld"
OUT = ROOT / "data" / "archive-counts.json"
ELECTIONS_INDEX = ROOT / "data" / "elections" / "index.json"
DEVOLVED_DIR = ROOT / "data" / "devolved"
SITE_URL = "https://www.manifestos.org.uk"
CHAMBER_SLUGS = {"london", "holyrood", "senedd", "stormont", "euro"}
ARTEFACT_STEMS = {"manifesto", "cover", "booklet"}


def iter_typed(obj, type_name: str):
    if isinstance(obj, dict):
        typ = obj.get("@type")
        types = typ if isinstance(typ, list) else [typ]
        if type_name in types:
            yield obj
        for value in obj.values():
            yield from iter_typed(value, type_name)
    elif isinstance(obj, list):
        for item in obj:
            yield from iter_typed(item, type_name)


def document_key(url: str) -> str | None:
    """Folder key (`1997/labour`, `london/2024/green`) from a catalogue URL."""
    path = (url or "").replace(SITE_URL, "").strip("/")
    parts = [p for p in path.split("/") if p]
    if len(parts) < 2 or parts[0] not in ("manifesto", "manifestos"):
        return None
    rest = parts[1:]
    if parts[0] == "manifestos" and rest:
        stem = rest[-1].rsplit(".", 1)[0]
        if stem in ARTEFACT_STEMS:
            rest = rest[:-1]
    key = "/".join(rest)
    return key or None


def classify_document_key(key: str) -> str:
    folder = (key or "").split("/", 1)[0]
    if folder in CHAMBER_SLUGS:
        return "devolved"
    return "westminster"


def count_elections() -> int:
    n = 0
    if ELECTIONS_INDEX.is_file():
        n += len(json.loads(ELECTIONS_INDEX.read_text(encoding="utf-8")))
    for index in sorted(DEVOLVED_DIR.glob("*/index.json")):
        data = json.loads(index.read_text(encoding="utf-8"))
        if isinstance(data, list):
            n += len(data)
        elif isinstance(data, dict) and isinstance(data.get("elections"), list):
            n += len(data["elections"])
    return n


def unique_document_keys(catalog: dict) -> set[str]:
    keys: set[str] = set()
    for doc in iter_typed(catalog, "DigitalDocument"):
        key = document_key(doc.get("url") or "")
        if key:
            keys.add(key)
    return keys


def build_archive_counts(catalog: dict | None = None) -> dict:
    if catalog is None:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    keys = unique_document_keys(catalog)
    westminster = sum(1 for k in keys if classify_document_key(k) == "westminster")
    devolved = sum(1 for k in keys if classify_document_key(k) == "devolved")
    return {
        "manifestos": len(keys),
        "westminsterManifestos": westminster,
        "devolvedManifestos": devolved,
        "elections": count_elections(),
        "nations": 4,
    }


def write_archive_counts(catalog: dict | None = None) -> dict:
    counts = build_archive_counts(catalog)
    OUT.write_text(json.dumps(counts, indent=2) + "\n", encoding="utf-8")
    return counts


if __name__ == "__main__":
    if not CATALOG.is_file():
        print(f"ERROR: missing {CATALOG}", file=sys.stderr)
        sys.exit(1)
    counts = write_archive_counts()
    print(f"Wrote {OUT.relative_to(ROOT)}")
    for key, value in counts.items():
        print(f"  {key}: {value}")
