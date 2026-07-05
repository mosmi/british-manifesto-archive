#!/usr/bin/env python3
"""Generate sitemap.xml from js/data.js and data/manifestos-index.json."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://www.manifestos.org.uk"
OBJECT_KEY_RE = re.compile(r"^  (?:'([^']+)'|([a-z][a-z0-9-]*)):\s*\{", re.M)


def section(text: str, start: str, end: str) -> str:
    part = text.split(start, 1)[1]
    return part.split(end, 1)[0]


def object_keys(block: str) -> list[str]:
    return [m.group(1) or m.group(2) for m in OBJECT_KEY_RE.finditer(block)]


def load_index_ids(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [e["id"] for e in json.loads(path.read_text(encoding="utf-8"))]


def iso_date(path: Path | None) -> str:
    if path and path.is_file():
        ts = path.stat().st_mtime
        return datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()
    return datetime.now(tz=timezone.utc).date().isoformat()


def lastmod_for_path(path: str) -> str:
    if path == "/":
        return iso_date(ROOT / "index.html")
    if path == "/about":
        return iso_date(ROOT / "js" / "app.js")
    if path.startswith("/manifesto/"):
        parts = path.strip("/").split("/")
        if len(parts) == 3:
            folder = ROOT / "manifestos" / parts[1] / parts[2]
            for candidate in (folder / "manifesto.md", folder / "manifesto.pdf"):
                if candidate.is_file():
                    return iso_date(candidate)
    if path.startswith("/devolved/"):
        parts = path.strip("/").split("/")
        if len(parts) == 3 and parts[2] != "other-parties":
            jf = ROOT / "data" / "devolved" / parts[1] / f"{parts[2]}.json"
            return iso_date(jf)
        if len(parts) == 2:
            return iso_date(ROOT / "data" / "devolved" / parts[1] / "index.json")
    if path.startswith("/election/"):
        return iso_date(ROOT / "js" / "data.js")
    if path.startswith("/party/"):
        return iso_date(ROOT / "js" / "data.js")
    if path.startswith("/nation/"):
        return iso_date(ROOT / "js" / "data.js")
    return iso_date(ROOT / "data" / "seo.json")


def main() -> None:
    data_js = (ROOT / "js/data.js").read_text(encoding="utf-8")

    election_ids = re.findall(r"id: '([^']+)',\s*year:", data_js)
    party_ids = object_keys(section(data_js, "const PARTIES = {", "const NATIONS"))
    nation_ids = object_keys(section(data_js, "const NATIONS = {", "const ELECTIONS"))
    devolved_ids = object_keys(section(data_js, "const DEVOLVED_PORTALS = {", ";\n"))

    manifestos = json.loads(
        (ROOT / "data/manifestos-index.json").read_text(encoding="utf-8")
    )

    london_ids = load_index_ids(ROOT / "data/devolved/london/index.json")
    holyrood_ids = load_index_ids(ROOT / "data/devolved/holyrood/index.json")
    senedd_ids = load_index_ids(ROOT / "data/devolved/senedd/index.json")
    stormont_ids = load_index_ids(ROOT / "data/devolved/stormont/index.json")
    euro_ids = load_index_ids(ROOT / "data/devolved/euro/index.json")

    urls: list[str] = ["/", "/about", "/others", "/elections", "/devolved", "/parties", "/nations"]
    urls.extend(f"/election/{eid}" for eid in election_ids)
    urls.extend(f"/party/{pid}" for pid in party_ids if pid != "others")
    urls.extend(f"/nation/{nid}" for nid in nation_ids)
    urls.extend(f"/devolved/{did}" for did in devolved_ids)
    urls.extend(f"/devolved/london/{lid}" for lid in london_ids)
    urls.extend(f"/devolved/holyrood/{hid}" for hid in holyrood_ids)
    urls.append("/devolved/holyrood/other-parties")
    urls.extend(f"/devolved/senedd/{sid}" for sid in senedd_ids)
    urls.append("/devolved/senedd/other-parties")
    urls.extend(f"/devolved/stormont/{sid}" for sid in stormont_ids)
    urls.append("/devolved/stormont/other-parties")
    urls.extend(f"/devolved/euro/{eid}" for eid in euro_ids)
    urls.append("/devolved/euro/other-parties")
    urls.extend(
        f"/manifesto/{m['electionId']}/{m['partyId']}" for m in manifestos
    )

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for path in urls:
        loc = f"{BASE}/" if path == "/" else f"{BASE}{path}"
        lines.append("  <url>")
        lines.append(f"    <loc>{loc}</loc>")
        lines.append(f"    <lastmod>{lastmod_for_path(path)}</lastmod>")
        lines.append("  </url>")
    lines.append("</urlset>")

    out = ROOT / "sitemap.xml"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(urls)} URLs to {out}")


if __name__ == "__main__":
    main()
