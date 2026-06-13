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

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path(__file__).resolve().parent / "senedd-assets.json"
DEST_ROOT = ROOT / "manifestos" / "senedd"
MAX_BYTES = 24 * 1024 * 1024
COVER_WIDTH = 640
PORTRAIT_H = round(COVER_WIDTH * 297 / 210)
LANDSCAPE_H = round(COVER_WIDTH * 210 / 297)


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


def _is_dark(rgb: tuple[int, int, int], threshold: int = 240) -> bool:
    return all(c < threshold for c in rgb)


def crop_to_trim_marks(
    img: Image.Image,
    *,
    threshold: int = 240,
    margin: float = 0.05,
    inset_frac: float = 0.015,
) -> Image.Image:
    """Crop to the trim box inside printer crop marks."""
    img = img.convert("RGB")
    w, h = img.size
    px = img.load()
    x0, x1 = int(w * margin), int(w * (1 - margin))
    y0, y1 = int(h * margin), int(h * (1 - margin))
    left_band = int(w * 0.25)
    right_band = w - left_band

    def is_dark(x: int, y: int) -> bool:
        return _is_dark(px[x, y], threshold)

    def row_center(y: int) -> float:
        return sum(is_dark(x, y) for x in range(x0, x1)) / (x1 - x0)

    def row_full(y: int) -> float:
        return sum(is_dark(x, y) for x in range(w)) / w

    def row_sides(y: int) -> tuple[float, float]:
        left = sum(is_dark(x, y) for x in range(left_band)) / left_band
        right = sum(is_dark(x, y) for x in range(right_band, w)) / (w - right_band)
        return left, right

    def col_center(x: int) -> float:
        return sum(is_dark(x, y) for y in range(y0, y1)) / (y1 - y0)

    top = next((y for y in range(h) if row_center(y) >= 0.05), 0)
    bottom = 0
    for y in range(h - 1, -1, -1):
        full = row_full(y)
        left, right = row_sides(y)
        if full >= 0.1 or (full >= 0.15 and (left >= 0.1 or right >= 0.1)):
            bottom = y + 1
            break
    else:
        bottom = h

    left = next((x for x in range(w) if col_center(x) >= 0.05), 0)
    right = next((x + 1 for x in range(w - 1, -1, -1) if col_center(x) >= 0.05), w)

    inset = max(2, int(min(right - left, bottom - top) * inset_frac))
    bottom_inset = max(1, inset // 4)
    left += inset
    top += inset
    right -= inset
    bottom -= bottom_inset
    if right <= left or bottom <= top:
        return img
    return img.crop((left, top, right, bottom))


def fit_portrait(img: Image.Image) -> Image.Image:
    img = img.copy().convert("RGBA")
    img.thumbnail((COVER_WIDTH, PORTRAIT_H), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (COVER_WIDTH, PORTRAIT_H), (0, 0, 0, 0))
    canvas.paste(img, ((COVER_WIDTH - img.width) // 2, (PORTRAIT_H - img.height) // 2))
    return canvas


def fit_landscape(img: Image.Image) -> Image.Image:
    img = img.copy().convert("RGBA")
    img.thumbnail((COVER_WIDTH, LANDSCAPE_H), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (COVER_WIDTH, PORTRAIT_H), (0, 0, 0, 0))
    canvas.paste(img, ((COVER_WIDTH - img.width) // 2, (PORTRAIT_H - img.height) // 2))
    return canvas


def fit_contain(img: Image.Image) -> Image.Image:
    return fit_portrait(img)


def find_spread_right_panel_left(img: Image.Image, start_frac: float = 0.5) -> int:
    """Locate the left edge of the right-hand cover on a printer spread."""
    rgb = img.convert("RGB")
    w, h = rgb.size
    px = rgb.load()
    mid = int(w * start_frac)
    top_band = int(h * 0.45)

    for x in range(mid, w):
        dark = sum(_is_dark(px[x, y]) for y in range(top_band)) / top_band
        if dark >= 0.15:
            return x

    in_spine = False
    spine_end = mid
    for x in range(mid, w):
        r, g, b = px[x, h // 2]
        if r > 200 and g < 80 and b < 120:
            in_spine = True
            spine_end = x
        elif in_spine:
            return x
    if in_spine:
        return min(spine_end + 8, w - 1)
    return mid


def postprocess_cover(src_png: Path, out_png: Path, mode: str) -> None:
    img = Image.open(src_png)

    if mode == "cropmarks":
        result = fit_portrait(crop_to_trim_marks(img, inset_frac=0.022))
    elif mode == "cropmarks-landscape":
        result = fit_landscape(crop_to_trim_marks(img, inset_frac=0.035))
    elif mode == "spread-right-cropmarks":
        left = find_spread_right_panel_left(img)
        panel = img.crop((left, 0, img.width, img.height))
        result = fit_portrait(crop_to_trim_marks(panel, inset_frac=0.022))
    elif mode == "spread-two-thirds-cropmarks":
        third = img.width // 3
        panel = img.crop((third, 0, img.width, img.height))
        result = fit_portrait(crop_to_trim_marks(panel, inset_frac=0.022))
    elif mode == "spread-right":
        half_w = img.width // 2
        panel = img.crop((half_w, 0, img.width, img.height))
        panel = panel.resize((COVER_WIDTH, PORTRAIT_H), Image.Resampling.LANCZOS)
        result = panel.convert("RGBA")
    elif mode == "spread-left":
        half_w = img.width // 2
        panel = img.crop((0, 0, half_w, img.height))
        panel = panel.resize((COVER_WIDTH, PORTRAIT_H), Image.Resampling.LANCZOS)
        result = panel.convert("RGBA")
    elif mode == "landscape":
        result = fit_landscape(img)
    elif mode == "contain":
        result = fit_contain(img)
    elif mode == "top-a4":
        result = img.crop((0, 0, min(img.width, COVER_WIDTH), min(img.height, PORTRAIT_H)))
        result = fit_portrait(result)
    else:
        panel = img.resize((COVER_WIDTH, PORTRAIT_H), Image.Resampling.LANCZOS)
        result = panel.convert("RGBA")

    result.save(out_png)


def make_cover(pdf: Path, out_png: Path, mode: str = "page") -> None:
    """Render a cover thumbnail from page 1 of *pdf*.

    mode="page"                       : full first page, scaled to COVER_WIDTH.
    mode="top-a4"                     : top slice cropped to A4 portrait proportions.
    mode="landscape"                  : landscape page letterboxed on portrait canvas.
    mode="contain"                    : any aspect ratio fitted inside portrait canvas.
    mode="spread-right"               : two-up spread; keep the right-hand page.
    mode="spread-left"                : two-up spread; keep the left-hand page.
    mode="spread-right-cropmarks"     : right-hand cover from a spread, cropped to trim marks.
    mode="spread-two-thirds-cropmarks": printer cover spread; keep right two-thirds.
    mode="cropmarks-landscape"        : crop to printer trim marks, then letterbox landscape.
    mode="cropmarks"                  : crop to printer trim marks, then fit portrait canvas.
    """
    tmp = out_png.with_suffix("")
    spread_modes = {
        "spread-right",
        "spread-left",
        "spread-right-cropmarks",
        "spread-two-thirds-cropmarks",
    }
    landscape_modes = {"landscape", "cropmarks-landscape"}
    render_w = COVER_WIDTH * 3 if mode == "spread-two-thirds-cropmarks" else (
        COVER_WIDTH * 2 if mode in spread_modes else COVER_WIDTH
    )
    ppm_args = ["pdftoppm", "-png", "-f", "1", "-l", "1"]
    if mode in landscape_modes:
        ppm_args.extend(["-scale-to-y", str(COVER_WIDTH), "-scale-to-x", "-1"])
    else:
        ppm_args.extend(["-scale-to-x", str(render_w), "-scale-to-y", "-1"])
    ppm_args.extend([str(pdf), str(tmp)])
    subprocess.run(ppm_args, check=True)
    produced = sorted(out_png.parent.glob(out_png.stem + "-*.png"))
    if not produced:
        return
    produced[0].replace(out_png)
    postprocess_cover(out_png, out_png, mode)


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
