#!/usr/bin/env python3
"""Regenerate 2009 EU manifesto PDFs and covers."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'manifestos/euro/2009'
SRC = Path(
    '/Users/mosmi/Claude/Projects/Manifestos/Original documents/European Elections/2009 European Parliament election'
)
GROUPS = SRC / 'zEuropean Parliamentary groups'
UKIP_SRC = Path(
    '/Users/mosmi/Downloads/Campaign policies Euro elections 2009 - UK Independence Party · 12.20am · 07-04.pdf'
)
PLAID_SRC = Path('/Users/mosmi/Downloads/Manifestos/Great Britain/PC_09.pdf')

CW, CH = 1240, 1754
DPI = 300

# (source path relative to SRC or GROUPS, slug, cover mode, dest pdf filename)
JOBS: list[tuple[Path, str, str, str]] = [
    (SRC / 'Alliance Party 2009 manifesto.pdf', 'alliance', 'portrait_contain', 'manifesto.pdf'),
    (SRC / 'BNP 2009 manifesto.pdf', 'bnp', 'spread_right_contain', 'manifesto.pdf'),
    (SRC / 'Christian Party Christian People\'s Alliance 2009 leaflet.pdf', 'christian', 'portrait_contain', 'manifesto.pdf'),
    (SRC / 'Conservative 2009 manifesto.pdf', 'conservative', 'portrait_contain', 'manifesto.pdf'),
    (SRC / 'DUP 2009 manifesto.pdf', 'dup', 'spread_left_contain', 'manifesto.pdf'),
    (SRC / 'English Democrats 2009 manifesto.pdf', 'englishdemocrats', 'portrait_contain', 'manifesto.pdf'),
    (SRC / 'Green Party 2009 manifesto.pdf', 'green', 'portrait_contain', 'manifesto.pdf'),
    (SRC / 'Greens NI 2009 manifesto.pdf', 'gpni', 'portrait_contain', 'manifesto.pdf'),
    (SRC / 'Labour 2009 manifesto.pdf', 'labour', 'portrait_contain', 'manifesto.pdf'),
    (SRC / 'Liberal Democrat 2009 manifesto.pdf', 'libdem', 'portrait_contain', 'manifesto.pdf'),
    (SRC / 'SDLP 2009 manifesto.pdf', 'sdlp', 'square_trim_contain', 'manifesto.pdf'),
    (SRC / 'Scottish Greens 2009 manifesto.pdf', 'scottishgrn', 'portrait_contain', 'manifesto.pdf'),
    (SRC / 'Scottish Labour 2009 manifesto.pdf', 'scottishlab', 'portrait_contain', 'manifesto.pdf'),
    (SRC / 'Sinn Fein 2009 manifesto.pdf', 'sinnfein', 'spread_right_contain', 'manifesto.pdf'),
    (SRC / 'TUV 2009 manifesto.pdf', 'tuv', 'portrait_contain', 'manifesto.pdf'),
    (SRC / 'UUP 2009 manifesto.pdf', 'uup', 'portrait_contain', 'manifesto.pdf'),
    (SRC / 'Scottish Liberal Democrats 2009 manifesto.pdf', 'scottishlibdem', 'portrait_contain', 'manifesto.pdf'),
    (UKIP_SRC, 'ukip', 'portrait_contain', 'manifesto.pdf'),
    (PLAID_SRC, 'plaid', 'portrait_contain', 'manifesto.pdf'),
    (GROUPS / 'PES 2009 manifesto.pdf', 'pes', 'portrait_contain', 'manifesto.pdf'),
    (GROUPS / 'ELDR 2009 manifesto.pdf', 'eldr', 'portrait_contain', 'manifesto.pdf'),
]


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
    img = img.convert('RGB')
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


def crop_sdlp_square(img: Image.Image) -> Image.Image:
    """Crop SDLP square cover, dropping bottom printer metadata."""
    img = crop_to_trim_marks(img, inset_frac=0.025)
    w, h = img.size
    px = img.load()
    content_bottom = h
    for y in range(h - 1, int(h * 0.55), -1):
        whites = sum(1 for x in range(0, w, 12) if min(px[x, y]) > 230)
        if whites > (w // 12) * 0.85 and y > h * 0.78:
            content_bottom = y
        else:
            break
    side = min(w, content_bottom)
    return img.crop((0, 0, side, side))


def render_page(pdf: Path, page: int = 1) -> Image.Image:
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / 'page'
        subprocess.run(
            [
                'pdftocairo', '-png', '-f', str(page), '-l', str(page),
                '-r', str(DPI), '-singlefile', str(pdf), str(out),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return Image.open(out.with_suffix('.png')).convert('RGBA')


def fit_portrait_contain(img: Image.Image) -> Image.Image:
    w, h = img.size
    scale = min(CW / w, CH / h)
    nw, nh = round(w * scale), round(h * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
    canvas.paste(img, ((CW - nw) // 2, (CH - nh) // 2), img)
    return canvas


def spread_left_contain(img: Image.Image) -> Image.Image:
    half = img.width // 2
    panel = img.crop((0, 0, half, img.height))
    panel = crop_to_trim_marks(panel, inset_frac=0.02).convert('RGBA')
    return fit_portrait_contain(panel)


def spread_right_contain(img: Image.Image) -> Image.Image:
    half = img.width // 2
    panel = img.crop((half, 0, img.width, img.height))
    return fit_portrait_contain(panel)


def cover_from_page(page: Image.Image, mode: str) -> Image.Image:
    if mode == 'portrait_contain':
        return fit_portrait_contain(page)
    if mode == 'spread_right_contain':
        return spread_right_contain(page)
    if mode == 'spread_left_contain':
        return spread_left_contain(page)
    if mode == 'square_trim_contain':
        trimmed = crop_sdlp_square(page).convert('RGBA')
        return fit_portrait_contain(trimmed)
    raise ValueError(mode)


def process_job(src: Path, slug: str, mode: str, pdf_name: str) -> None:
    dest_dir = DEST / slug
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_pdf = dest_dir / pdf_name
    dest_png = dest_dir / 'manifesto.png'

    shutil.copy2(src, dest_pdf)
    page = render_page(dest_pdf)
    cover = cover_from_page(page, mode)
    cover.save(dest_png, optimize=True)
    print(f'{slug}: {page.size} -> {cover.size}')


def crop_snp_page(img: Image.Image) -> Image.Image:
    """Remove printer crop marks and filename metadata from an SNP imposition page."""
    img = crop_to_trim_marks(img, inset_frac=0.035)
    w, h = img.size
    px = img.load()
    top = 0
    for y in range(min(h, int(h * 0.1))):
        dark = sum(1 for x in range(0, w, 20) if sum(px[x, y]) < 600)
        if dark < (w // 20) * 0.12:
            top = y + 1
        else:
            break
    if top:
        img = img.crop((0, top, w, h))
        w, h = img.size
    side = max(35, int(w * 0.018))
    return img.crop((side, 0, w - side, h))


def strip_stitch_gutter(img: Image.Image, edge: str) -> Image.Image:
    w, h = img.size
    strip = max(50, int(h * 0.05))
    if edge == 'bottom':
        return img.crop((0, 0, w, h - strip))
    return img.crop((0, strip, w, h))


def stitch_vertical(top: Image.Image, bottom: Image.Image) -> Image.Image:
    top = top.convert('RGB')
    bottom = bottom.convert('RGB')
    w = max(top.width, bottom.width)
    h = top.height + bottom.height
    out = Image.new('RGB', (w, h), (255, 255, 255))
    out.paste(top, ((w - top.width) // 2, 0))
    out.paste(bottom, ((w - bottom.width) // 2, top.height))
    return out


def export_snp_assets() -> None:
    """Copy the original SNP imposition PDF; cover is maintained separately."""
    src = SRC / 'SNP 2009 manifesto.pdf'
    dest_dir = DEST / 'snp'
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest_dir / 'manifesto.pdf')
    print(f'snp: copied original PDF ({src.stat().st_size // 1024} KB)')


def main() -> None:
    for src, slug, mode, pdf_name in JOBS:
        process_job(src, slug, mode, pdf_name)
    export_snp_assets()


if __name__ == '__main__':
    main()
