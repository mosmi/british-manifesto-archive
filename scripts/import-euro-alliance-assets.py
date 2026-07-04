#!/usr/bin/env python3
"""Import zEuropean Parliamentary groups manifestos into the archive."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DEST_ROOT = ROOT / 'manifestos/euro'
DATA_DIR = ROOT / 'data/devolved/euro'
SRC_ROOT = Path(
    '/Users/mosmi/Claude/Projects/Manifestos/Original documents/European Elections'
)

CW, CH = 1240, 1754
DPI = 300

# (filename prefix regex, slug, display name)
PARTY_RULES: list[tuple[str, str, str]] = [
    (r'^PES ', 'pes', 'PES'),
    (r'^ELDR ', 'eldr', 'ELDR'),
    (r'^ALDE ', 'alde', 'ALDE'),
    (r'^EPP ', 'epp', 'EPP'),
    (r'^ECR ', 'ecr', 'ECR'),
    (r'^Green Group ', 'greengroup', 'Green Group'),
    (r'^Greens-EFA - European Green Party ', 'eurengreens', 'Greens-EFA European Green Party'),
    (r'^Greens-EFA - European Free Alliance ', 'eurefa', 'Greens-EFA European Free Alliance'),
    (r'^GUE-NGL - European Left ', 'eurleft', 'GUE-NGL European Left'),
    (r'^Independence-Democracy ', 'inddem', 'Independence & Democracy'),
    (r'^Union for Europe of the Nations ', 'uen', 'Union for Europe of the Nations'),
    (r'^European Alliance for Freedom ', 'eaf', 'European Alliance for Freedom'),
    (r'^Democracy in Europe Movement ', 'diem25', 'Democracy in Europe Movement (DiEM25)'),
    (r'^European Christian Political Movement ', 'ecpm', 'European Christian Political Movement'),
    (r'^European Conservatives and Reformists Party ', 'ecrp', 'European Conservatives and Reformists Party'),
    (r'^European Pirates Party ', 'eurpirates', 'European Pirates Party'),
    (r'^Volt ', 'volt', 'Volt'),
]


def parse_source(pdf: Path) -> tuple[str, str, str, str] | None:
    name = pdf.name
    if 'flyer' in name.lower():
        return None
    year = pdf.parent.parent.name.split()[0]
    # ALDE 2009 duplicates the ELDR 2009 manifesto in this collection.
    if year == '2009' and name.startswith('ALDE '):
        return None
    for pattern, slug, label in PARTY_RULES:
        if re.match(pattern, name):
            doc = 'Platform' if 'platform' in name.lower() else 'Manifesto'
            title = f'{label} European {doc} {year}'
            return year, slug, title, doc
    return None


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


def spread_right_contain(img: Image.Image) -> Image.Image:
    half = img.width // 2
    panel = img.crop((half, 0, img.width, img.height))
    return fit_portrait_contain(panel)


def cover_mode_for_page(page: Image.Image, slug: str, year: str) -> str:
    return 'spread_right_contain' if page.width > page.height * 1.25 else 'portrait_contain'


def cover_from_page(page: Image.Image, mode: str) -> Image.Image:
    if mode == 'portrait_contain':
        return fit_portrait_contain(page)
    if mode == 'spread_right_contain':
        return spread_right_contain(page)
    raise ValueError(mode)


def process_pdf(pdf: Path) -> dict | None:
    parsed = parse_source(pdf)
    if not parsed:
        print(f'skip: {pdf.name}')
        return None
    year, slug, title, _doc = parsed
    dest_dir = DEST_ROOT / year / slug
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_pdf = dest_dir / 'manifesto.pdf'
    dest_png = dest_dir / 'manifesto.png'

    shutil.copy2(pdf, dest_pdf)
    custom_cover = dest_dir / 'cover-source.png'
    if year == '2009' and slug == 'pes' and custom_cover.exists():
        cover = fit_portrait_contain(Image.open(custom_cover).convert('RGBA'))
        cover.save(dest_png, optimize=True)
        print(f'{year}/{slug}: custom cover-source {custom_cover.name} -> {cover.size}')
    else:
        page = render_page(dest_pdf)
        mode = cover_mode_for_page(page, slug, year)
        cover = cover_from_page(page, mode)
        cover.save(dest_png, optimize=True)
        print(f'{year}/{slug}: {mode} {page.size} -> {cover.size}')
    return {
        'title': title,
        'pdf': f'/manifestos/euro/{year}/{slug}/manifesto.pdf',
        'cover': f'/manifestos/euro/{year}/{slug}/manifesto.png',
        'party': slug,
        'group': 'alliances',
    }


def update_json(entries_by_year: dict[str, list[dict]]) -> None:
    for year, new_entries in sorted(entries_by_year.items()):
        json_path = DATA_DIR / f'{year}.json'
        if not json_path.exists():
            print(f'warn: missing {json_path}')
            continue
        data = json.loads(json_path.read_text())
        manifestos = data.get('manifestos', [])
        alliance_parties = {e['party'] for e in new_entries}
        manifestos = [m for m in manifestos if m.get('party') not in alliance_parties]
        manifestos.extend(new_entries)
        data['manifestos'] = manifestos
        json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
        print(f'updated {json_path.name}: +{len(new_entries)} alliance manifestos')


def main() -> None:
    entries_by_year: dict[str, list[dict]] = {}
    groups_dirs = sorted(SRC_ROOT.glob('* European Parliament election/zEuropean Parliamentary groups'))
    for groups_dir in groups_dirs:
        for pdf in sorted(groups_dir.glob('*.pdf')):
            entry = process_pdf(pdf)
            if not entry:
                continue
            year = pdf.parent.parent.name.split()[0]
            entries_by_year.setdefault(year, []).append(entry)

    for entries in entries_by_year.values():
        entries.sort(key=lambda e: e['party'])

    update_json(entries_by_year)


if __name__ == '__main__':
    main()
