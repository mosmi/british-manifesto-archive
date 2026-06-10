#!/usr/bin/env python3
"""Fetch Wikipedia 'Replaced by' for 1974-only constituencies (abolished at 1983)."""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "hex" / "1974-abolished-wikipedia-replaced-by.json"
UA = "BritishManifestoArchive/1.0 (research; local script)"
BATCH = 1
SLEEP_S = 2.5


def load_1974_only_names() -> list[str]:
    c83 = {
        c["name"]
        for c in json.loads((ROOT / "data/constituencies/1983.json").read_text())[
            "constituencies"
        ]
    }
    feb = [
        c["name"]
        for c in json.loads((ROOT / "data/constituencies/feb1974.json").read_text())[
            "constituencies"
        ]
    ]
    return sorted(set(feb) - c83)


def wiki_title(name: str) -> str:
    return f"{name} (UK Parliament constituency)"


def wiki_title_variants(name: str) -> list[str]:
    base = name.replace(" & ", " and ").replace("&", "and")
    titles = [wiki_title(name)]
    if base != name:
        titles.append(wiki_title(base))
    return titles


def fetch_wikitext_batch(titles: list[str]) -> tuple[dict[str, str], dict[str, str]]:
    """Return (requested_title -> wikitext, resolved_title -> requested_title)."""
    url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(
        {
            "action": "query",
            "format": "json",
            "redirects": 1,
            "prop": "revisions",
            "rvprop": "content",
            "rvslots": "main",
            "titles": "|".join(titles),
        }
    )
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read())
            break
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < 8:
                time.sleep(30 * (attempt + 1))
                continue
            raise
    else:
        raise RuntimeError(f"Wikipedia rate limit persisted for batch: {titles[:3]}")
    redirect_to_from = {
        redir["to"]: redir["from"] for redir in data.get("query", {}).get("redirects", [])
    }
    resolved_text: dict[str, str] = {}
    for page in data.get("query", {}).get("pages", {}).values():
        if "missing" in page:
            continue
        title = page.get("title", "")
        revs = page.get("revisions") or []
        if revs:
            content = revs[0].get("slots", {}).get("main", {}).get("*", "")
            if content:
                resolved_text[title] = content
    by_requested: dict[str, str] = {}
    for resolved_title, content in resolved_text.items():
        requested = redirect_to_from.get(resolved_title, resolved_title)
        by_requested[requested] = content
    return by_requested, redirect_to_from


def clean_wiki_value(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return ""
    parts = []
    for chunk in re.split(r"\s*,\s*|\s+and\s+", raw):
        chunk = chunk.strip()
        chunk = re.sub(r"\[\[([^|\]]+)\|([^\]]+)\]\]", r"\2", chunk)
        chunk = re.sub(r"\[\[([^\]]+)\]\]", r"\1", chunk)
        chunk = chunk.replace("''", "").strip()
        if chunk:
            parts.append(chunk)
    return "; ".join(parts)


def parse_replaced_by(wikitext: str) -> tuple[str, str]:
    blocks: list[dict[str, str]] = []
    current: dict[str, str] = {}
    in_infobox = False
    for line in wikitext.splitlines():
        if line.strip().startswith("{{Infobox UK constituency"):
            in_infobox = True
            current = {}
            continue
        if in_infobox:
            if line.strip() == "}}":
                if current:
                    blocks.append(current)
                in_infobox = False
                current = {}
                continue
            m = re.match(r"\|\s*([a-zA-Z0-9_]+)\s*=\s*(.*)", line.strip())
            if m:
                key, val = m.group(1).lower(), m.group(2).strip()
                if re.match(r"next\d?$", key) or key.startswith("abolished"):
                    current[key] = val

    chosen = None
    for block in blocks:
        abol = " ".join(block.get(k, "") for k in block if k.startswith("abolished"))
        if "1983" in abol:
            chosen = block
            break
    if chosen is None and blocks:
        chosen = blocks[-1]

    if not chosen:
        next_m = re.search(r"\|\s*next\s*=\s*(.+)", wikitext, re.I)
        abol_m = re.search(r"\|\s*abolished\s*=\s*(.+)", wikitext, re.I)
        return (
            clean_wiki_value(next_m.group(1)) if next_m else "",
            clean_wiki_value(abol_m.group(1)) if abol_m else "",
        )

    abol = clean_wiki_value(
        chosen.get("abolished")
        or chosen.get("abolished2")
        or chosen.get("abolished3")
        or chosen.get("abolished4")
        or ""
    )
    next_keys = sorted(k for k in chosen if re.fullmatch(r"next\d?", k))
    replaced = "; ".join(
        p
        for k in next_keys
        if chosen.get(k)
        for p in [clean_wiki_value(chosen[k])]
        if p
    )
    return replaced, abol


def main() -> None:
    names = load_1974_only_names()
    title_by_name = {n: wiki_title(n) for n in names}
    results: list[dict] = []
    done_names: set[str] = set()
    if OUT.exists():
        results = json.loads(OUT.read_text())
        done_names = {r["name1974"] for r in results}

    titles = [title_by_name[n] for n in names if n not in done_names]
    pending_names = [n for n in names if n not in done_names]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if not pending_names:
        print(f"Already complete: {len(results)} rows in {OUT}")
        return

    for start in range(0, len(pending_names)):
        name = pending_names[start]
        wikitext = None
        used_title = title_by_name[name]
        for title in wiki_title_variants(name):
            page_text, _ = fetch_wikitext_batch([title])
            wikitext = page_text.get(title)
            if wikitext:
                used_title = title
                break
        if not wikitext:
            results.append(
                {
                    "name1974": name,
                    "wikipediaTitle": used_title,
                    "replacedBy": "",
                    "abolished": "",
                    "status": "page_not_found",
                }
            )
        else:
            replaced, abol = parse_replaced_by(wikitext)
            results.append(
                {
                    "name1974": name,
                    "wikipediaTitle": used_title,
                    "replacedBy": replaced,
                    "abolished": abol,
                    "status": "ok" if replaced else "missing_replaced_by",
                }
            )
        if (start + 1) % 5 == 0 or start + 1 == len(pending_names):
            print(f"  {len(done_names) + start + 1}/{len(names)}")
            results.sort(key=lambda r: r["name1974"].lower())
            OUT.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
        time.sleep(SLEEP_S)

    results.sort(key=lambda r: r["name1974"].lower())
    OUT.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    ok = sum(1 for r in results if r["replacedBy"])
    print(f"Wrote {len(results)} rows ({ok} with Replaced by) -> {OUT}")


if __name__ == "__main__":
    main()
