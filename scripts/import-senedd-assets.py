#!/usr/bin/env python3
"""
Import Senedd election manifesto PDFs from the local source archive into
manifestos/senedd/{id}/{party}/...

Driven by scripts/senedd-assets.json (same schema as london-assets.json).

Usage:
  python3 scripts/import-senedd-assets.py
  python3 scripts/import-senedd-assets.py 2026
  python3 scripts/import-senedd-assets.py --dry-run
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path(__file__).resolve().parent / "senedd-assets.json"
DEST_ROOT = ROOT / "manifestos" / "senedd"
MAX_BYTES = 24 * 1024 * 1024
COVER_WIDTH = 640


def preprocess_pdf(src: Path, dest: Path, opts: dict) -> None:
    """Copy or transform *src* into *dest* before cover generation."""
    rotate = opts.get("rotate")
    skip_first = opts.get("skip_first_page")
    if not rotate and not skip_first:
        shutil.copy2(src, dest)
        return

    gs_args = [
        "gs", "-sDEVICE=pdfwrite", "-dNOPAUSE", "-dBATCH", "-dQUIET",
        f"-sOutputFile={dest}",
    ]
    if skip_first:
        gs_args.append("-dFirstPage=2")
    if rotate:
        gs_args.extend(["-c", f"<</Rotate {int(rotate)}>> setpagedevice"])
    gs_args.extend(["-f", str(src)])
    subprocess.run(gs_args, check=True)


def make_cover(pdf: Path, out_png: Path, mode: str = "page") -> None:
    """Render a cover thumbnail from page 1 of *pdf*.

    mode="page"           : full first page, scaled to COVER_WIDTH (default).
    mode="top-a4"         : top slice cropped to A4 portrait proportions.
    mode="landscape"      : landscape page letterboxed on portrait A4 canvas.
    mode="contain"        : any aspect ratio fitted inside portrait A4 canvas.
    mode="spread-right"   : two-up spread; keep the right-hand page as the cover.
    mode="spread-left"    : two-up spread; keep the left-hand page as the cover.
    mode="spread-right-trim" : right-hand cover from a spread, then trim crop marks.
    mode="spread-left-trim"  : left-hand cover from a spread, then trim crop marks.
    mode="trifold-right"  : printer cover spread; keep the right third (English cover).
    mode="trim-landscape" : crop to printer trim marks, then letterbox as landscape.
    mode="trim"           : crop to printer trim marks, then fit on portrait A4 canvas.
    """
    tmp = out_png.with_suffix("")
    is_spread = mode in ("spread-right", "spread-left", "spread-left-trim", "spread-right-trim", "trifold-right")
    render_w = COVER_WIDTH * 2 if is_spread else COVER_WIDTH
    subprocess.run(
        ["pdftoppm", "-png", "-f", "1", "-l", "1",
         "-scale-to-x", str(render_w), "-scale-to-y", "-1", str(pdf), str(tmp)],
        check=True,
    )
    produced = sorted(out_png.parent.glob(out_png.stem + "-*.png"))
    if not produced:
        return
    produced[0].replace(out_png)
    portrait_h = round(COVER_WIDTH * 297 / 210)

    if mode == "spread-right":
        info = subprocess.run(
            ["magick", "identify", "-format", "%w %h", str(out_png)],
            check=True, capture_output=True, text=True,
        )
        w, h = map(int, info.stdout.split())
        half_w = w // 2
        subprocess.run(
            ["magick", str(out_png), "-crop", f"{half_w}x{h}+{half_w}+0",
             "+repage", "-resize", f"{COVER_WIDTH}x", str(out_png)],
            check=True,
        )
    elif mode == "spread-left":
        info = subprocess.run(
            ["magick", "identify", "-format", "%w %h", str(out_png)],
            check=True, capture_output=True, text=True,
        )
        w, h = map(int, info.stdout.split())
        half_w = w // 2
        subprocess.run(
            ["magick", str(out_png), "-crop", f"{half_w}x{h}+0+0",
             "+repage", "-resize", f"{COVER_WIDTH}x", str(out_png)],
            check=True,
        )
    elif mode == "spread-right-trim":
        info = subprocess.run(
            ["magick", "identify", "-format", "%w %h", str(out_png)],
            check=True, capture_output=True, text=True,
        )
        w, h = map(int, info.stdout.split())
        half_w = w // 2
        subprocess.run(
            ["magick", str(out_png), "-crop", f"{half_w}x{h}+{half_w}+0", "+repage",
             "-fuzz", "2%", "-trim", "+repage",
             "-resize", f"{COVER_WIDTH}x{portrait_h}",
             "-background", "none", "-gravity", "center",
             "-extent", f"{COVER_WIDTH}x{portrait_h}", str(out_png)],
            check=True,
        )
    elif mode == "spread-left-trim":
        info = subprocess.run(
            ["magick", "identify", "-format", "%w %h", str(out_png)],
            check=True, capture_output=True, text=True,
        )
        w, h = map(int, info.stdout.split())
        half_w = w // 2
        subprocess.run(
            ["magick", str(out_png), "-crop", f"{half_w}x{h}+0+0", "+repage",
             "-fuzz", "2%", "-trim", "+repage",
             "-resize", f"{COVER_WIDTH}x{portrait_h}",
             "-background", "none", "-gravity", "center",
             "-extent", f"{COVER_WIDTH}x{portrait_h}", str(out_png)],
            check=True,
        )
    elif mode == "trifold-right":
        info = subprocess.run(
            ["magick", "identify", "-format", "%w %h", str(out_png)],
            check=True, capture_output=True, text=True,
        )
        w, h = map(int, info.stdout.split())
        third_w = w // 3
        crop_x = w - third_w
        subprocess.run(
            ["magick", str(out_png), "-crop", f"{third_w}x{h}+{crop_x}+0",
             "+repage", "-resize", f"{COVER_WIDTH}x{portrait_h}",
             "-background", "none", "-gravity", "center",
             "-extent", f"{COVER_WIDTH}x{portrait_h}", str(out_png)],
            check=True,
        )
    elif mode == "trim-landscape":
        subprocess.run(
            ["magick", str(out_png), "-fuzz", "2%", "-trim", "+repage",
             "-resize", f"{COVER_WIDTH}x", str(out_png)],
            check=True,
        )
        subprocess.run(
            ["magick", "-size", f"{COVER_WIDTH}x{portrait_h}", "xc:none",
             str(out_png), "-gravity", "center", "-composite", str(out_png)],
            check=True,
        )
    elif mode == "trim":
        subprocess.run(
            ["magick", str(out_png), "-fuzz", "2%", "-trim", "+repage",
             "-resize", f"{COVER_WIDTH}x{portrait_h}",
             "-background", "none", "-gravity", "center",
             "-extent", f"{COVER_WIDTH}x{portrait_h}", str(out_png)],
            check=True,
        )
    elif mode == "top-a4":
        subprocess.run(
            ["magick", str(out_png), "-crop", f"{COVER_WIDTH}x{portrait_h}+0+0",
             "+repage", str(out_png)],
            check=True,
        )
    elif mode == "landscape":
        subprocess.run(
            ["magick", "-size", f"{COVER_WIDTH}x{portrait_h}", "xc:none",
             str(out_png), "-gravity", "center", "-composite", str(out_png)],
            check=True,
        )
    elif mode == "contain":
        subprocess.run(
            ["magick", str(out_png), "-resize", f"{COVER_WIDTH}x{portrait_h}",
             "-background", "none", "-gravity", "center",
             "-extent", f"{COVER_WIDTH}x{portrait_h}", str(out_png)],
            check=True,
        )


def place_pdf(src: Path, dest: Path, dry: bool, cover_mode: str = "page",
              preprocess: dict | None = None) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    size = src.stat().st_size
    preprocess = preprocess or {}
    if dry:
        action = "compress" if size > MAX_BYTES else "copy"
        extras = []
        if preprocess.get("skip_first_page"):
            extras.append("drop page 1")
        if preprocess.get("rotate"):
            extras.append(f"rotate {preprocess['rotate']}°")
        suffix = f" ({', '.join(extras)})" if extras else ""
        print(f"  [{action}] {src.name} -> {dest.relative_to(ROOT)}{suffix}")
        return

    tmp = dest
    if preprocess.get("skip_first_page") or preprocess.get("rotate"):
        tmp = dest.with_suffix(".src.pdf")
        preprocess_pdf(src, tmp, preprocess)
        src_for_copy = tmp
    else:
        src_for_copy = src

    if size > MAX_BYTES and not preprocess:
        print(f"  compressing {src.name} ({size/1048576:.1f}MB)…")
        subprocess.run(
            ["gs", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.5",
             "-dPDFSETTINGS=/ebook", "-dNOPAUSE", "-dQUIET", "-dBATCH",
             f"-sOutputFile={dest}", str(src_for_copy)],
            check=True,
        )
    elif preprocess.get("skip_first_page") or preprocess.get("rotate"):
        if size > MAX_BYTES:
            print(f"  compressing {src.name} ({size/1048576:.1f}MB) after preprocess…")
            subprocess.run(
                ["gs", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.5",
                 "-dPDFSETTINGS=/ebook", "-dNOPAUSE", "-dQUIET", "-dBATCH",
                 f"-sOutputFile={dest}", str(tmp)],
                check=True,
            )
            tmp.unlink(missing_ok=True)
        else:
            shutil.move(str(tmp), str(dest))
    else:
        shutil.copy2(src, dest)

    make_cover(dest, dest.parent / "cover.png", cover_mode)


def process(entry: dict, dry: bool) -> None:
    eid = entry["id"]
    print(f"== {eid} ==")
    for m in entry.get("manifestos", []):
        src = Path(m["src"])
        party = m["party"]
        if not src.exists():
            print(f"  MISSING {party}: {src}")
            continue
        preprocess = {}
        if m.get("skip_first_page"):
            preprocess["skip_first_page"] = True
        if m.get("rotate"):
            preprocess["rotate"] = m["rotate"]
        place_pdf(
            src,
            DEST_ROOT / eid / party / "manifesto.pdf",
            dry,
            m.get("cover", "page"),
            preprocess,
        )


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
