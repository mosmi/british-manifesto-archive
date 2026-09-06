#!/usr/bin/env python3
"""
build-latest-additions.py

Generate data/latest-additions.json for the homepage carousel — newest archive
additions first — from:

  1. data/manifestos-index.json  (Westminster / SPA catalogue)
  2. data/devolved/*/*.json      (euro, holyrood, senedd, stormont, london)

"Recently added" = first git commit that introduced that folder's manifesto.pdf
(or manifesto.md / cover if no PDF). Falls back to filesystem mtime when git
history is unavailable.

Run after adding manifesto files (same cadence as build-pdf-sizes.py):

    python3 scripts/build-latest-additions.py
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFESTOS_DIR = ROOT / "manifestos"
INDEX_PATH = ROOT / "data" / "manifestos-index.json"
TITLES_PATH = ROOT / "data" / "manifesto-titles.json"
DEVOLVED_DIR = ROOT / "data" / "devolved"
OUT = ROOT / "data" / "latest-additions.json"

# How many cards on the homepage carousel
LIMIT = 12

PORTAL_PREFIXES = ("euro", "holyrood", "senedd", "stormont", "london")


def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def cover_for(folder: Path) -> str | None:
    for name in ("cover.png", "manifesto.png", "cover.jpg"):
        if (folder / name).is_file():
            rel = (folder / name).relative_to(ROOT)
            return "/" + str(rel).replace("\\", "/")
    return None


def folder_for(election_id: str, party_id: str) -> Path:
    return MANIFESTOS_DIR / election_id / party_id


def is_westminster(election_id: str) -> bool:
    head = election_id.split("/", 1)[0]
    return head not in PORTAL_PREFIXES


def year_from_election_id(election_id: str) -> str:
    # "2024", "feb1974", "euro/2019", "senedd/2026"
    tail = election_id.rsplit("/", 1)[-1]
    digits = "".join(ch for ch in tail if ch.isdigit())
    if len(digits) >= 4:
        return digits[-4:]
    return tail


def git_first_added_map() -> dict[str, str]:
    """Map repo-relative path → ISO date of first Add commit (oldest A)."""
    try:
        proc = subprocess.run(
            [
                "git",
                "-C",
                str(ROOT),
                "log",
                "--diff-filter=A",
                "--reverse",
                "--pretty=format:%aI",
                "--name-only",
                "--",
                "manifestos/",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return {}

    added: dict[str, str] = {}
    current_date: str | None = None
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        if line[0].isdigit() and "T" in line and len(line) >= 19:
            current_date = line
            continue
        if current_date and line.startswith("manifestos/"):
            # Keep the earliest Add only
            added.setdefault(line.replace("\\", "/"), current_date)
    return added


def best_added_date(folder: Path, git_added: dict[str, str]) -> str:
    """Prefer git first-add of manifesto.pdf, then .md, then cover; else mtime."""
    candidates = [
        folder / "manifesto.pdf",
        folder / "manifesto.md",
        folder / "cover.png",
        folder / "manifesto.png",
        folder / "cover.jpg",
    ]
    for path in candidates:
        if not path.is_file():
            continue
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        if rel in git_added:
            return git_added[rel]
    # mtime fallback
    for path in candidates:
        if path.is_file():
            ts = path.stat().st_mtime
            return datetime.fromtimestamp(ts, tz=timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
    return iso_now()


def load_published_titles() -> dict:
    if not TITLES_PATH.is_file():
        return {}
    try:
        return json.loads(TITLES_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def load_index_entries() -> list[dict]:
    if not INDEX_PATH.is_file():
        return []
    titles = load_published_titles()
    raw = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    out = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        eid = item.get("electionId")
        pid = item.get("partyId")
        if not eid or not pid:
            continue
        rec = titles.get(f"{eid}/{pid}") or {}
        out.append(
            {
                "electionId": eid,
                "partyId": pid,
                "title": rec.get("title") or "",
                "source": "index",
            }
        )
    return out


def load_devolved_entries() -> list[dict]:
    """Supplement with devolved/euro manifesto rows not always in the flat index."""
    out = []
    if not DEVOLVED_DIR.is_dir():
        return out
    titles = load_published_titles()
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
            election_id = f"{portal_dir.name}/{jf.stem}"
            for m in data.get("manifestos") or []:
                if not isinstance(m, dict):
                    continue
                pid = m.get("party")
                pdf = m.get("pdf") or ""
                if not pid:
                    continue
                # Derive folder from pdf path when present
                folder = folder_for(election_id, pid)
                if pdf.startswith("/manifestos/"):
                    # /manifestos/euro/2019/green/manifesto.pdf → euro/2019/green
                    parts = pdf.strip("/").split("/")
                    if len(parts) >= 4:
                        folder = ROOT / "/".join(parts[:-1])
                rec = titles.get(f"{election_id}/{pid}") or {}
                out.append(
                    {
                        "electionId": election_id,
                        "partyId": pid,
                        "title": rec.get("title") or m.get("title") or "",
                        "cover_override": m.get("cover"),
                        "pdf_override": pdf or None,
                        "folder": folder,
                        "source": "devolved",
                    }
                )
    return out


def build_card(entry: dict, git_added: dict[str, str]) -> dict | None:
    eid = entry["electionId"]
    pid = entry["partyId"]
    folder = entry.get("folder") or folder_for(eid, pid)
    if not folder.is_dir():
        return None

    has_pdf = (folder / "manifesto.pdf").is_file()
    has_md = (folder / "manifesto.md").is_file()
    if not has_pdf and not has_md:
        return None

    cover = entry.get("cover_override") or cover_for(folder)
    year = year_from_election_id(eid)
    westminster = is_westminster(eid)

    if westminster and (has_md or has_pdf):
        # SPA manifesto reader (PDF-only pages still work with empty-state + download)
        url = f"/manifesto/{eid}/{pid}"
        is_pdf = False
    else:
        pdf_url = entry.get("pdf_override") or (
            f"/manifestos/{eid}/{pid}/manifesto.pdf" if has_pdf else None
        )
        if not pdf_url:
            return None
        url = pdf_url
        is_pdf = True

    card = {
        "electionId": eid,
        "partyId": pid,
        "title": entry["title"],
        "year": year,
        "url": url,
        "isPdf": is_pdf,
        "added": best_added_date(folder, git_added),
    }
    if cover:
        card["cover"] = cover
    return card


def build_latest(limit: int = LIMIT) -> list[dict]:
    git_added = git_first_added_map()

    # Index first; devolved fills gaps (same electionId/partyId wins for index)
    seen: set[tuple[str, str]] = set()
    merged: list[dict] = []
    for entry in load_index_entries():
        key = (entry["electionId"], entry["partyId"])
        if key in seen:
            continue
        seen.add(key)
        merged.append(entry)
    for entry in load_devolved_entries():
        key = (entry["electionId"], entry["partyId"])
        if key in seen:
            continue
        seen.add(key)
        merged.append(entry)

    cards = []
    for entry in merged:
        card = build_card(entry, git_added)
        if card:
            cards.append(card)

    cards.sort(key=lambda c: c["added"], reverse=True)
    # Strip internal-only fields if any; keep `added` for transparency/debug
    return cards[:limit]


def main() -> None:
    items = build_latest()
    OUT.write_text(
        json.dumps(items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"✅  Wrote {len(items)} entries to {OUT.relative_to(ROOT)}")
    for it in items[:5]:
        print(f"   {it['added'][:10]}  {it['title']}")
    if len(items) > 5:
        print(f"   … and {len(items) - 5} more")


if __name__ == "__main__":
    main()
