#!/usr/bin/env python3
"""Regenerate 2004 EU manifesto PDFs and covers."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'manifestos/euro/2004'
SRC = Path(
    '/Users/mosmi/Claude/Projects/Manifestos/Original documents/European Elections/2004 European Parliament election'
)
GROUPS = SRC / 'zEuropean Parliamentary groups'

CW, CH = 1240, 1754
DPI = 300

# (source, slug, cover mode, dest pdf name, skip_cover)
JOBS: list[tuple[Path, str, str, str, bool]] = [
    (SRC / 'Conservative 2004 manifesto.pdf', 'conservative', 'portrait_contain', 'manifesto.pdf', False),
    (SRC / 'Labour 2004 manifesto.pdf', 'labour', 'square_contain', 'manifesto.pdf', False),
    (SRC / 'Liberal Democrats 2004 manifesto.pdf', 'libdem', 'portrait_contain', 'manifesto.pdf', False),
    (SRC / 'Green 2004 manifesto.pdf', 'green', 'spread_left_contain', 'manifesto.pdf', False),
    (SRC / 'SNP 2004 manifesto.pdf', 'snp', 'portrait_contain', 'manifesto.pdf', False),
    (SRC / 'Plaid Cymru 2004 manifesto.pdf', 'plaid', 'portrait_contain', 'manifesto.pdf', False),
    (SRC / 'UKIP 2004 manifesto.pdf', 'ukip', 'spread_right_purple_contain', 'manifesto.pdf', False),
    (SRC / 'Sinn Fein 2004 manifesto.pdf', 'sinnfein', 'portrait_contain', 'manifesto.pdf', False),
    (SRC / 'DUP 2004 manifesto.pdf', 'dup', 'spread_right_red_contain', 'manifesto.pdf', False),
    (SRC / 'UUP 2004 manifesto.pdf', 'uup', 'spread_right_contain', 'manifesto.pdf', False),
    (SRC / 'Greens NI 2004 manifesto.pdf', 'gpni', 'portrait_contain', 'manifesto.pdf', False),
    (SRC / 'Scottish Socialist Party 2004 manifesto.pdf', 'ssp', 'portrait_contain', 'manifesto.pdf', False),
    (SRC / 'Socialist Environmental Alliance 2004 manifesto.pdf', 'sea', 'portrait_contain', 'manifesto.pdf', True),
    (SRC / 'Independent Gilliland 2004 manifesto.pdf', 'gilliland', 'portrait_contain', 'manifesto.pdf', False),
    (GROUPS / 'PES 2004 manifesto.pdf', 'pes', 'square_contain', 'manifesto.pdf', False),
]


def crop_to_red_border(img: Image.Image) -> Image.Image:
    img = img.convert('RGB')
    w, h = img.size
    px = img.load()
    xs: list[int] = []
    ys: list[int] = []
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if r > 150 and g < 100 and b < 120:
                xs.append(x)
                ys.append(y)
    if not xs:
        return img.convert('RGBA')
    left, top, right, bottom = min(xs), min(ys), max(xs), max(ys)
    pad = max(8, int((right - left) * 0.02))
    left = max(0, left - pad)
    top = max(0, top - pad)
    right = min(w, right + pad)
    bottom = min(h, bottom + pad)
    return img.crop((left, top, right, bottom)).convert('RGBA')


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
    return fit_portrait_contain(panel)


def spread_right_contain(img: Image.Image) -> Image.Image:
    half = img.width // 2
    panel = img.crop((half, 0, img.width, img.height))
    return fit_portrait_contain(panel)


def crop_to_purple_border(img: Image.Image) -> Image.Image:
    img = img.convert('RGB')
    w, h = img.size
    px = img.load()
    xs: list[int] = []
    ys: list[int] = []
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if min(r, g, b) > 210:
                continue
            if r > 60 and b > 80 and g < 130 and b > r * 0.55:
                xs.append(x)
                ys.append(y)
    if not xs:
        return img.convert('RGBA')
    left, top, right, bottom = min(xs), min(ys), max(xs), max(ys)
    pad = max(3, int((right - left) * 0.008))
    return img.crop((left - pad, top - pad, right + pad, bottom + pad))


def shave_white_borders(img: Image.Image, thresh: int = 235) -> Image.Image:
    img = img.convert('RGB')
    w, h = img.size
    px = img.load()

    def col_white_frac(x: int) -> float:
        return sum(1 for y in range(0, h, 4) if min(px[x, y]) > thresh) / ((h + 3) // 4)

    def row_white_frac(y: int) -> float:
        return sum(1 for x in range(0, w, 4) if min(px[x, y]) > thresh) / ((w + 3) // 4)

    left = 0
    while left < w - 1 and col_white_frac(left) > 0.9:
        left += 1
    right = w
    while right > left + 1 and col_white_frac(right - 1) > 0.9:
        right -= 1
    top = 0
    while top < h - 1 and row_white_frac(top) > 0.9:
        top += 1
    bottom = h
    while bottom > top + 1 and row_white_frac(bottom - 1) > 0.9:
        bottom -= 1
    return img.crop((left, top, right, bottom))


def spread_right_purple_contain(img: Image.Image) -> Image.Image:
    half = img.width // 2
    panel = img.crop((half, 0, img.width, img.height))
    panel = shave_white_borders(crop_to_purple_border(panel))
    return fit_portrait_contain(panel.convert('RGBA'))


def spread_right_red_contain(img: Image.Image) -> Image.Image:
    half = img.width // 2
    panel = img.crop((half, 0, img.width, img.height))
    return fit_portrait_contain(crop_to_red_border(panel))


def cover_from_page(page: Image.Image, mode: str) -> Image.Image:
    if mode == 'portrait_contain':
        return fit_portrait_contain(page)
    if mode == 'square_contain':
        return fit_portrait_contain(page)
    if mode == 'spread_left_contain':
        return spread_left_contain(page)
    if mode == 'spread_right_contain':
        return spread_right_contain(page)
    if mode == 'spread_right_purple_contain':
        return spread_right_purple_contain(page)
    if mode == 'spread_right_red_contain':
        return spread_right_red_contain(page)
    raise ValueError(mode)


def merge_sdlp() -> None:
    pt1 = SRC / 'SDLP 2004 manifesto - pt 1.pdf'
    pt2 = SRC / 'SDLP 2004 manifesto - pt 2.pdf'
    dest_dir = DEST / 'sdlp'
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_pdf = dest_dir / 'manifesto.pdf'
    subprocess.run(['pdfunite', str(pt1), str(pt2), str(dest_pdf)], check=True)

    for old in ['manifesto-pt1.pdf', 'manifesto-pt2.pdf', 'manifesto-pt1.png', 'manifesto-pt2.png']:
        p = dest_dir / old
        if p.exists():
            p.unlink()

    page = render_page(dest_pdf)
    cover = fit_portrait_contain(page)
    cover.save(dest_dir / 'manifesto.png', optimize=True)
    print(f'sdlp: merged -> {dest_pdf} ({dest_pdf.stat().st_size // 1024} KB)')


def process_job(src: Path, slug: str, mode: str, pdf_name: str, skip_cover: bool) -> None:
    dest_dir = DEST / slug
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_pdf = dest_dir / pdf_name
    dest_png = dest_dir / 'manifesto.png'

    shutil.copy2(src, dest_pdf)
    if skip_cover:
        print(f'{slug}: copied PDF only (cover unchanged)')
        return

    page = render_page(dest_pdf)
    cover = cover_from_page(page, mode)
    cover.save(dest_png, optimize=True)
    print(f'{slug}: {page.size} -> {cover.size}')


def main() -> None:
    merge_sdlp()
    for src, slug, mode, pdf_name, skip_cover in JOBS:
        process_job(src, slug, mode, pdf_name, skip_cover)


if __name__ == '__main__':
    main()
