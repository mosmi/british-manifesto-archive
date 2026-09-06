#!/usr/bin/env python3
"""
build-manifesto-assets.py

Walks manifestos/ and writes data/manifesto-assets.json — per-folder flags for
whether manifesto.pdf, manifesto.md, and a cover image (`cover.png`, `cover.jpg`,
or euro-style `manifesto.png`) exist on disk.

Used by the site so text-only editions without a cover can show the
"Scan not yet archived" placeholder immediately (no broken-image flicker),
while editions that have a cover keep showing it even when the PDF is absent.

Run whenever manifesto files or covers are added/removed:
  python3 scripts/build-manifesto-assets.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFESTOS_DIR = ROOT / "manifestos"
OUT = ROOT / "data" / "manifesto-assets.json"


def folder_key(path: Path) -> str:
    """manifestos/<electionId…>/<partyId>/ → electionId/partyId (electionId may contain /)."""
    parts = path.relative_to(MANIFESTOS_DIR).parts
    party_id = parts[-1] if path.is_dir() else parts[-2]
    election_id = "/".join(parts[:-1] if path.is_dir() else parts[:-2])
    return f"{election_id}/{party_id}"


def build() -> dict[str, dict[str, bool]]:
    assets: dict[str, dict[str, bool]] = {}

    # Any directory that holds at least one of the manifesto artefacts.
    folders: set[Path] = set()
    for name in ("manifesto.pdf", "manifesto.md", "cover.png", "cover.jpg"):
        for path in MANIFESTOS_DIR.rglob(name):
            folders.add(path.parent)

    for folder in sorted(folders, key=lambda p: p.as_posix()):
        key = folder_key(folder)
        assets[key] = {
            "pdf": (folder / "manifesto.pdf").is_file(),
            "md": (folder / "manifesto.md").is_file(),
            "cover": (
                (folder / "cover.png").is_file()
                or (folder / "cover.jpg").is_file()
                or (folder / "manifesto.png").is_file()
            ),
        }

    return assets


def main() -> None:
    assets = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(assets, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    n = len(assets)
    md_only = sum(1 for v in assets.values() if v["md"] and not v["pdf"])
    no_cover = sum(1 for v in assets.values() if v["md"] and not v["pdf"] and not v["cover"])
    print(
        f"Wrote {OUT.relative_to(ROOT)} — {n} folders, "
        f"{md_only} text-only (no PDF), {no_cover} text-only without cover"
    )


if __name__ == "__main__":
    main()
