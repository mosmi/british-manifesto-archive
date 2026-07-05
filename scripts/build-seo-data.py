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
PARTY_LINKS = ROOT / "data" / "party-links.json"
DEVOLVED_DIR = ROOT / "data" / "devolved"
MANIFESTOS_DIR = ROOT / "manifestos"
OUT = ROOT / "data" / "seo.json"
CATALOG_OUT = ROOT / "data" / "catalog.jsonld"

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


OBJECT_KEY_RE = re.compile(r"^  (?:'([^']+)'|([a-z][a-z0-9-]*)):\s*\{", re.M)


def object_key(match: re.Match) -> str:
    return match.group(1) or match.group(2)


def parse_named_map(block: str, name_field: str) -> dict:
    """Extract {top-level-id: <name_field value>} from a simple object block."""
    field_re = re.compile(rf"{name_field}:\s*'((?:\\'|[^'])*)'")
    matches = list(OBJECT_KEY_RE.finditer(block))
    out = {}
    for i, m in enumerate(matches):
        seg_end = matches[i + 1].start() if i + 1 < len(matches) else len(block)
        seg = block[m.end():seg_end]
        fm = field_re.search(seg)
        out[object_key(m)] = fm.group(1).replace("\\'", "'") if fm else None
    return out


def parse_nations(block: str) -> dict:
    """Extract {id: {name, description}} from the NATIONS block."""
    desc_re = re.compile(r"description:\s*'((?:\\'|[^'])*)'")
    matches = list(OBJECT_KEY_RE.finditer(block))
    out = {}
    for i, m in enumerate(matches):
        seg_end = matches[i + 1].start() if i + 1 < len(matches) else len(block)
        seg = block[m.end():seg_end]
        name_m = re.search(r"name:\s*'((?:\\'|[^'])*)'", seg)
        desc_m = desc_re.search(seg)
        out[object_key(m)] = {
            "name": name_m.group(1).replace("\\'", "'") if name_m else object_key(m),
            "description": desc_m.group(1).replace("\\'", "'") if desc_m else None,
        }
    return out


def parse_parties(text: str) -> dict:
    """Extract {id: {name, shortName, color, description}} from the PARTIES block."""
    block = slice_block(text, "const PARTIES", "const NATIONS")
    # id, name and shortName appear together (same line) per entry.
    entry_re = re.compile(
        r"id:\s*'([^']+)',\s*name:\s*'([^']*)',\s*shortName:\s*'([^']*)'"
    )
    color_re = re.compile(r"color:\s*'([^']*)'")
    desc_re = re.compile(r"description:\s*'((?:\\'|[^'])*)'")
    matches = list(entry_re.finditer(block))
    parties = {}
    for i, m in enumerate(matches):
        pid, name, short = m.group(1), m.group(2), m.group(3)
        # Scope the colour search to this entry only.
        seg_end = matches[i + 1].start() if i + 1 < len(matches) else len(block)
        seg = block[m.end():seg_end]
        cm = color_re.search(seg)
        dm = desc_re.search(seg)
        parties[pid] = {
            "name": name,
            "shortName": short,
            "color": cm.group(1) if cm else None,
            "description": dm.group(1).replace("\\'", "'") if dm else None,
        }
    return parties


def parties_in_westminster_segment(seg: str) -> set[str]:
    """Unique party ids that contested a general election."""
    parties = {m.group(1) for m in re.finditer(r"party:\s*'([^']+)'", seg)}
    pr = re.search(r"partyResults:\s*\{([\s\S]*?)\n\s*\},?\s*\n", seg)
    if pr:
        parties.update(
            km.group(1)
            for km in re.finditer(r"^\s{6}([a-z][a-z0-9]*):\s*\{", pr.group(1), re.M)
        )
    em = re.search(r"extraManifestoParties:\s*\[([\s\S]*?)\]", seg)
    if em:
        parties.update(re.findall(r"'([^']+)'", em.group(1)))
    return parties


def build_party_chamber_counts(text: str) -> dict[str, dict[str, int]]:
    """{partyId: {westminster, holyrood, senedd, stormont, euro}} election counts."""
    counts: dict[str, dict[str, int]] = {}

    block = slice_block(text, "const ELECTIONS", "\n];")
    entry_starts = list(re.finditer(r"\{\s*\n\s*id: '([^']+)'", block))
    for i, m in enumerate(entry_starts):
        seg_end = entry_starts[i + 1].start() if i + 1 < len(entry_starts) else len(block)
        seg = block[m.start():seg_end]
        for pid in parties_in_westminster_segment(seg):
            counts.setdefault(pid, {})
            counts[pid]["westminster"] = counts[pid].get("westminster", 0) + 1

    portal_keys = {
        "holyrood": "holyrood",
        "senedd": "senedd",
        "stormont": "stormont",
        "euro": "euro",
    }
    for portal, key in portal_keys.items():
        portal_dir = DEVOLVED_DIR / portal
        if not portal_dir.is_dir():
            continue
        for jf in sorted(portal_dir.glob("*.json")):
            if jf.stem == "index":
                continue
            try:
                data = json.loads(jf.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            results = (
                (data.get("parliament") or {}).get("results")
                or data.get("results")
                or []
            )
            seen = {r.get("party") for r in results if r.get("party")}
            for pid in seen:
                counts.setdefault(pid, {})
                counts[pid][key] = counts[pid].get(key, 0) + 1

    return counts


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


def humanize(slug: str) -> str:
    """'foreign-policy' -> 'foreign policy' (for schema.org keywords)."""
    return slug.replace("-", " ").replace("_", " ").strip()


def manifesto_sections(md_path: Path) -> list:
    """Pull the `sections:` list out of a manifesto.md YAML frontmatter block.

    Hand-parsed (no YAML dependency): read the block between the first two
    `---` fences, find `sections:`, then collect the following `  - item` lines.
    """
    if not md_path.is_file():
        return []
    try:
        text = md_path.read_text(encoding="utf-8")
    except OSError:
        return []
    if not text.startswith("---"):
        return []
    end = text.find("\n---", 3)
    block = text[3:end] if end != -1 else text[3:]
    lines = block.splitlines()
    sections = []
    capturing = False
    for line in lines:
        if re.match(r"^\s*sections:\s*$", line):
            capturing = True
            continue
        if capturing:
            m = re.match(r"^\s*-\s+(.+?)\s*$", line)
            if m:
                sections.append(m.group(1).strip().strip("'\""))
            elif line.strip() and not line.startswith((" ", "\t")):
                break
    return sections


def enrich_manifesto(item: dict) -> dict:
    """Add asset flags (pdf/markdown/cover) and topic keywords to a manifesto."""
    eid, pid = item["electionId"], item["partyId"]
    folder = MANIFESTOS_DIR / eid / pid
    out = {
        "label": item.get("label"),
        "electionId": eid,
        "partyId": pid,
        "hasPdf": (folder / "manifesto.pdf").is_file(),
        "hasMarkdown": (folder / "manifesto.md").is_file(),
        "hasCover": (folder / "cover.jpg").is_file(),
    }
    keywords = [humanize(s) for s in manifesto_sections(folder / "manifesto.md")]
    if keywords:
        out["keywords"] = keywords
    return out


def parse_devolved_portals(text: str) -> dict:
    """{portal: {label, subtitle, nation, body}} from DEVOLVED_PORTALS."""
    block = slice_block(text, "const DEVOLVED_PORTALS", "\n};")
    fields = ("label", "subtitle", "nation", "body")
    matches = list(OBJECT_KEY_RE.finditer(block))
    out = {}
    for i, m in enumerate(matches):
        seg_end = matches[i + 1].start() if i + 1 < len(matches) else len(block)
        seg = block[m.end():seg_end]
        entry = {}
        for f in fields:
            fm = re.search(rf"{f}:\s*'([^']*)'", seg)
            if fm:
                entry[f] = fm.group(1)
        out[object_key(m)] = entry
    return out


def build_devolved_manifestos() -> dict:
    """{`portal/year`: [{party, title, pdf, cover}]} from data/devolved/*/*.json."""
    out = {}
    if not DEVOLVED_DIR.is_dir():
        return out
    for portal_dir in sorted(DEVOLVED_DIR.iterdir()):
        if not portal_dir.is_dir():
            continue
        for jf in sorted(portal_dir.glob("*.json")):
            if jf.stem == "index":
                continue
            try:
                data = json.loads(jf.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            mans = data.get("manifestos") or []
            items = []
            for m in mans:
                if not isinstance(m, dict):
                    continue
                items.append({
                    "party": m.get("party"),
                    "title": m.get("title"),
                    "pdf": m.get("pdf"),
                    "cover": m.get("cover"),
                })
            if items:
                out[f"{portal_dir.name}/{jf.stem}"] = items
    return out


def build_catalog(seo: dict) -> dict:
    """A DataCatalog feed enumerating the archive's manifesto corpus + datasets."""
    publisher = {
        "@type": "Organization",
        "@id": f"{SITE_URL}/#organization",
        "name": SITE_NAME,
        "url": f"{SITE_URL}/",
    }

    def doc_node(key, rec):
        node = {
            "@type": "DigitalDocument",
            "@id": f"{SITE_URL}/manifesto/{key}#document",
            "name": rec.get("label") or key,
            "url": f"{SITE_URL}/manifesto/{key}",
        }
        if rec.get("keywords"):
            node["keywords"] = rec["keywords"]
        return node

    general_parts = [doc_node(k, r) for k, r in sorted(seo["manifestos"].items())]

    devolved_parts = []
    for ekey, items in sorted(seo.get("devolvedManifestos", {}).items()):
        for it in items:
            if not it.get("pdf"):
                continue
            devolved_parts.append({
                "@type": "DigitalDocument",
                "name": it.get("title") or f"{it.get('party')} {ekey}",
                "url": f"{SITE_URL}{it['pdf']}",
                "encodingFormat": "application/pdf",
            })

    datasets = [
        {
            "@type": "Dataset",
            "@id": f"{SITE_URL}/#dataset-general-manifestos",
            "name": "UK general election party manifestos (1945–2024)",
            "description": "Full-text party manifestos published for UK general "
                           "elections, with original PDFs and transcribed text.",
            "url": f"{SITE_URL}/elections",
            "inLanguage": "en-GB",
            "isAccessibleForFree": True,
            "creativeWorkStatus": "Published",
            "publisher": publisher,
            "hasPart": general_parts,
        },
        {
            "@type": "Dataset",
            "@id": f"{SITE_URL}/#dataset-devolved-manifestos",
            "name": "Devolved, regional and mayoral election manifestos",
            "description": "Manifestos from Scottish Parliament (Holyrood), Senedd "
                           "Cymru, Northern Ireland Assembly (Stormont) and London "
                           "elections.",
            "url": f"{SITE_URL}/devolved",
            "inLanguage": "en-GB",
            "isAccessibleForFree": True,
            "creativeWorkStatus": "Published",
            "publisher": publisher,
            "hasPart": devolved_parts,
        },
        {
            "@type": "Dataset",
            "@id": f"{SITE_URL}/#dataset-election-results",
            "name": "UK election results and seat maps",
            "description": "Party seat totals, vote shares and constituency hex "
                           "maps for UK general and devolved elections.",
            "url": f"{SITE_URL}/elections",
            "inLanguage": "en-GB",
            "isAccessibleForFree": True,
            "creativeWorkStatus": "Published",
            "publisher": publisher,
        },
    ]

    return {
        "@context": "https://schema.org",
        "@type": "DataCatalog",
        "@id": f"{SITE_URL}/#catalog",
        "name": f"{SITE_NAME} — Catalogue",
        "url": f"{SITE_URL}/",
        "description": "Machine-readable catalogue of UK election manifestos, "
                       "results and maps held in The British Manifesto Archive.",
        "inLanguage": "en-GB",
        "isAccessibleForFree": True,
        "publisher": publisher,
        "dataset": datasets,
    }


def main() -> None:
    text = DATA_JS.read_text(encoding="utf-8")

    parties = parse_parties(text)
    # `others` is a catch-all bucket, not a standalone page (mirrors the
    # sitemap, which excludes /party/others).
    parties.pop("others", None)
    elections = parse_elections(text)
    nations = parse_nations(slice_block(text, "const NATIONS", "const ELECTIONS"))
    devolved = parse_named_map(
        slice_block(text, "const DEVOLVED_PORTALS", "\n};"), "label")
    chamber_counts = build_party_chamber_counts(text)
    for pid, counts in chamber_counts.items():
        if pid in parties and counts:
            parties[pid]["chamberCounts"] = counts

    if not parties or not elections:
        print("ERROR: failed to parse parties/elections from data.js "
              f"(parties={len(parties)}, elections={len(elections)}). "
              "Check the regexes in build-seo-data.py.", file=sys.stderr)
        sys.exit(1)

    devolved_portals = parse_devolved_portals(text)

    # Merge curated external identity URLs (schema.org sameAs) into parties.
    same_as = 0
    if PARTY_LINKS.is_file():
        links = json.loads(PARTY_LINKS.read_text(encoding="utf-8"))
        for pid, urls in links.items():
            if pid.startswith("_") or pid not in parties:
                continue
            clean = [u for u in urls if isinstance(u, str) and u.startswith("http")]
            if clean:
                parties[pid]["sameAs"] = clean
                same_as += 1

    manifestos = json.loads(MANIFESTOS_INDEX.read_text(encoding="utf-8"))
    manifesto_map = {
        f"{item['electionId']}/{item['partyId']}": enrich_manifesto(item)
        for item in manifestos
    }

    devolved_manifestos = build_devolved_manifestos()

    seo = {
        "site": {"url": SITE_URL, "name": SITE_NAME},
        "parties": parties,
        "elections": elections,
        "nations": nations,
        "devolved": devolved,
        "devolvedPortals": devolved_portals,
        "manifestos": manifesto_map,
        "devolvedManifestos": devolved_manifestos,
        "counts": {
            "parties": len(parties),
            "elections": len(elections),
            "manifestos": len(manifesto_map),
            "devolvedElections": len(devolved_manifestos),
        },
    }

    OUT.write_text(json.dumps(seo, ensure_ascii=False, separators=(",", ":")),
                   encoding="utf-8")

    catalog = build_catalog(seo)
    CATALOG_OUT.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"  parties:    {len(parties)} ({same_as} with sameAs)")
    print(f"  elections:  {len(elections)}")
    print(f"  nations:    {len(nations)}")
    print(f"  devolved:   {len(devolved)} portals, "
          f"{len(devolved_manifestos)} elections with manifestos")
    print(f"  manifestos: {len(manifesto_map)}")
    print(f"Wrote {CATALOG_OUT.relative_to(ROOT)}")
    print(f"  datasets:   {len(catalog['dataset'])}")


if __name__ == "__main__":
    main()
