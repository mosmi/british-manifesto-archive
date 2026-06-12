#!/usr/bin/env python3
"""Generate sitemap.xml from js/data.js and data/manifestos-index.json."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://www.manifestos.org.uk"


def section(text: str, start: str, end: str) -> str:
    part = text.split(start, 1)[1]
    return part.split(end, 1)[0]


def main() -> None:
    data_js = (ROOT / "js/data.js").read_text(encoding="utf-8")

    election_ids = re.findall(r"id: '([^']+)',\s*year:", data_js)
    party_ids = re.findall(
        r"^\s{2}([a-z][a-z0-9]*):\s*\{",
        section(data_js, "const PARTIES = {", "const NATIONS"),
        re.M,
    )
    nation_ids = re.findall(
        r"^\s{2}([a-z-]+):\s*\{",
        section(data_js, "const NATIONS = {", "const ELECTIONS"),
        re.M,
    )
    devolved_ids = re.findall(
        r"^\s{2}([a-z-]+):\s*\{",
        section(data_js, "const DEVOLVED_PORTALS = {", ";\n"),
        re.M,
    )

    manifestos = json.loads(
        (ROOT / "data/manifestos-index.json").read_text(encoding="utf-8")
    )

    london_index_path = ROOT / "data/devolved/london/index.json"
    london_ids = (
        [e["id"] for e in json.loads(london_index_path.read_text(encoding="utf-8"))]
        if london_index_path.exists()
        else []
    )

    urls: list[str] = ["/", "/about", "/others", "/elections", "/devolved", "/parties", "/nations"]
    urls.extend(f"/election/{eid}" for eid in election_ids)
    urls.extend(f"/party/{pid}" for pid in party_ids if pid != "others")
    urls.extend(f"/nation/{nid}" for nid in nation_ids)
    urls.extend(f"/devolved/{did}" for did in devolved_ids)
    urls.extend(f"/devolved/london/{lid}" for lid in london_ids)
    urls.extend(
        f"/manifesto/{m['electionId']}/{m['partyId']}" for m in manifestos
    )

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for path in urls:
        loc = BASE if path == "/" else f"{BASE}{path}"
        lines.append("  <url>")
        lines.append(f"    <loc>{loc}</loc>")
        lines.append("  </url>")
    lines.append("</urlset>")

    out = ROOT / "sitemap.xml"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(urls)} URLs to {out}")


if __name__ == "__main__":
    main()
