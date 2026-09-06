#!/usr/bin/env python3
"""
Emit cover-356.webp and cover-712.webp (or manifesto-356/712.webp) beside each
canonical cover raster. Does not replace cover.png.

  python3 scripts/build-cover-thumbs.py
  python3 scripts/build-cover-thumbs.py --force
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFESTOS = ROOT / "manifestos"
MAGICK = shutil.which("magick") or shutil.which("convert")
SIZES = (356, 712)
A4 = 297 / 210  # height / width
QUALITY = "82"

SOURCES = ("cover.png", "cover.jpg", "manifesto.png")


def thumbs_for(src: Path) -> list[tuple[int, Path]]:
    return [(w, src.with_name(f"{src.stem}-{w}.webp")) for w in SIZES]


def needs_build(src: Path, dest: Path, force: bool) -> bool:
    if force or not dest.is_file():
        return True
    return dest.stat().st_mtime < src.stat().st_mtime


def render_one(src: Path, width: int, dest: Path) -> str:
    height = round(width * A4)
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        MAGICK,
        str(src),
        "-auto-orient",
        "-resize",
        f"{width}x{height}",
        "-quality",
        QUALITY,
        str(dest),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return f"{src.relative_to(ROOT)} → {dest.name} ({width}w)"


def collect_sources() -> list[Path]:
    found: list[Path] = []
    seen_dirs: set[Path] = set()
    for name in SOURCES:
        for path in MANIFESTOS.rglob(name):
            if name == "cover.jpg" and (path.parent / "cover.png").is_file():
                continue
            if name == "manifesto.png" and (path.parent / "cover.png").is_file():
                # PNG cover is canonical; manifesto.png still used by some euro JSON.
                # Generate thumbs for manifesto.png too when it is a distinct file.
                pass
            found.append(path)
            seen_dirs.add(path.parent)
    return sorted(set(found))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--jobs", type=int, default=8)
    args = parser.parse_args()

    if not MAGICK:
        print("ERROR: ImageMagick `magick` (or `convert`) is required.", file=sys.stderr)
        return 1

    jobs: list[tuple[Path, int, Path]] = []
    for src in collect_sources():
        for width, dest in thumbs_for(src):
            if needs_build(src, dest, args.force):
                jobs.append((src, width, dest))

    if not jobs:
        print("Cover thumbs up to date.")
        return 0

    print(f"Building {len(jobs)} WebP thumbs from {len(collect_sources())} covers…")
    ok = 0
    failed = 0
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        futs = {pool.submit(render_one, src, w, dest): (src, dest) for src, w, dest in jobs}
        for fut in as_completed(futs):
            src, dest = futs[fut]
            try:
                fut.result()
                ok += 1
            except subprocess.CalledProcessError as err:
                failed += 1
                stderr = (err.stderr or b"").decode("utf-8", "replace")[-300:]
                print(f"FAIL {src}: {stderr}", file=sys.stderr)
            except Exception as err:  # noqa: BLE001
                failed += 1
                print(f"FAIL {src}: {err}", file=sys.stderr)
    print(f"Done: {ok} written, {failed} failed.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
