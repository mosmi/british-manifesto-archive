#!/usr/bin/env python3
"""
Import London election assets (candidate booklets + party/candidate manifestos)
from the local source archive into manifestos/london/{id}/...

For each PDF it:
  • copies (or, if larger than the Cloudflare 24 MiB ceiling, Ghostscript-compresses)
    the file to its destination,
  • renders the first page to cover.png via pdftoppm.

Driven by scripts/london-assets.json:
[
  {
    "id": "gla-2016",
    "booklet": "<absolute source path or null>",
    "manifestos": [ {"party": "labour", "src": "<absolute source path>"} ]
  }
]

Usage:
  python3 scripts/import-london-assets.py            # process everything
  python3 scripts/import-london-assets.py gla-2016   # one election only
  python3 scripts/import-london-assets.py --dry-run
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path(__file__).resolve().parent / "london-assets.json"
DEST_ROOT = ROOT / "manifestos" / "london"
MAX_BYTES = 24 * 1024 * 1024  # Cloudflare free-plan per-file ceiling (25 MiB), with headroom
COVER_WIDTH = 640


def make_cover(pdf: Path, out_png: Path) -> None:
    tmp = out_png.with_suffix("")  # pdftoppm appends -1.png etc.
    subprocess.run(
        ["pdftoppm", "-png", "-f", "1", "-l", "1",
         "-scale-to-x", str(COVER_WIDTH), "-scale-to-y", "-1", str(pdf), str(tmp)],
        check=True,
    )
    produced = sorted(out_png.parent.glob(out_png.stem + "-*.png"))
    if produced:
        produced[0].replace(out_png)


def place_pdf(src: Path, dest: Path, dry: bool) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    size = src.stat().st_size
    if dry:
        action = "compress" if size > MAX_BYTES else "copy"
        print(f"  [{action}] {src.name} -> {dest.relative_to(ROOT)} ({size/1048576:.1f}MB)")
        return
    if size > MAX_BYTES:
        print(f"  compressing {src.name} ({size/1048576:.1f}MB)…")
        subprocess.run(
            ["gs", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.5",
             "-dPDFSETTINGS=/ebook", "-dNOPAUSE", "-dQUIET", "-dBATCH",
             f"-sOutputFile={dest}", str(src)],
            check=True,
        )
        new = dest.stat().st_size
        print(f"    -> {new/1048576:.1f}MB")
        if new > MAX_BYTES:
            print(f"    WARNING: {dest.name} still over limit ({new/1048576:.1f}MB)")
    else:
        shutil.copy2(src, dest)
    make_cover(dest, dest.parent / "cover.png")


def process(entry: dict, dry: bool) -> None:
    eid = entry["id"]
    print(f"== {eid} ==")
    booklet = entry.get("booklet")
    if booklet:
        src = Path(booklet)
        if not src.exists():
            print(f"  MISSING booklet: {src}")
        else:
            place_pdf(src, DEST_ROOT / eid / "booklet" / "booklet.pdf", dry)
    for m in entry.get("manifestos", []):
        src = Path(m["src"])
        if not src.exists():
            print(f"  MISSING {m['party']}: {src}")
            continue
        place_pdf(src, DEST_ROOT / eid / m["party"] / "manifesto.pdf", dry)


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    data = json.loads(MANIFEST.read_text())
    only = set(args)
    for entry in data:
        if only and entry["id"] not in only:
            continue
        process(entry, dry)
    print("Done.")


if __name__ == "__main__":
    main()
