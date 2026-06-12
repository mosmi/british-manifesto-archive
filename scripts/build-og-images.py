#!/usr/bin/env python3
"""
build-og-images.py

Generates branded 1200x630 Open Graph / Twitter share cards for every
manifesto, party and election page, written to /og/... as JPEGs. The edge
middleware (functions/_middleware.js) points each page's og:image and
twitter:image at the matching card.

Cards are derived from data/seo.json (run build-seo-data.py first) and use the
site's own brand palette + fonts (assets/og/fonts).

Usage:
  python3 scripts/build-og-images.py                 # all cards
  python3 scripts/build-og-images.py --only manifesto # one type
  python3 scripts/build-og-images.py --sample         # a handful, for preview
"""

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SEO = ROOT / "data" / "seo.json"
OG_DIR = ROOT / "og"
FONT_SERIF = ROOT / "assets/og/fonts/CormorantGaramond.ttf"
FONT_SANS = ROOT / "assets/og/fonts/DMSans.ttf"

W, H = 1200, 630
MARGIN = 90

# Brand palette (from styles.css :root).
NAVY = (9, 14, 28)
NAVY2 = (18, 30, 56)
CREAM = (242, 232, 204)
CREAM_DIM = (200, 192, 168)
GOLD = (201, 168, 76)


def hex_to_rgb(value, fallback=GOLD):
    if not value:
        return fallback
    value = value.lstrip("#")
    if len(value) != 6:
        return fallback
    try:
        return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return fallback


def load_font(path, size, variation=None):
    font = ImageFont.truetype(str(path), size)
    if variation:
        try:
            font.set_variation_by_name(variation)
        except Exception:
            pass
    return font


def background():
    """Vertical navy gradient with a thin inset gold frame."""
    img = Image.new("RGB", (W, H), NAVY)
    px = img.load()
    for y in range(H):
        t = y / (H - 1)
        r = round(NAVY[0] + (NAVY2[0] - NAVY[0]) * t)
        g = round(NAVY[1] + (NAVY2[1] - NAVY[1]) * t)
        b = round(NAVY[2] + (NAVY2[2] - NAVY[2]) * t)
        for x in range(W):
            px[x, y] = (r, g, b)
    draw = ImageDraw.Draw(img)
    inset = 38
    draw.rectangle([inset, inset, W - inset, H - inset],
                   outline=(201, 168, 76), width=2)
    return img, draw


def wrap_lines(draw, text, font, max_width):
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def fit_title(draw, text, max_width, start, minimum, variation, max_lines=2):
    size = start
    while size >= minimum:
        font = load_font(FONT_SERIF, size, variation)
        lines = wrap_lines(draw, text, font, max_width)
        if len(lines) <= max_lines:
            return font, lines, size
        size -= 4
    font = load_font(FONT_SERIF, minimum, variation)
    return font, wrap_lines(draw, text, font, max_width)[:max_lines], minimum


def draw_card(out_path, kicker, title, subtitle, accent):
    img, draw = background()

    bar_x = MARGIN
    text_x = bar_x + 40
    text_w = (W - MARGIN) - text_x

    # Kicker (uppercase, letter-spaced sans), fixed near the top.
    kfont = load_font(FONT_SANS, 30, "SemiBold")
    draw.text((text_x, 150), spaced(kicker.upper(), 4), font=kfont, fill=accent)

    # Footer position (fixed at the bottom).
    fy = H - 122

    # Title + subtitle are vertically centred in the region between the kicker
    # and the footer, so 1- and 2-line titles both stay clear of the footer.
    region_top, region_bottom = 206, fy - 40
    region_h = region_bottom - region_top

    tfont, lines, tsize = fit_title(draw, title, text_w, 100, 52, "Bold", 2)
    line_h = int(tsize * 1.06)
    title_h = len(lines) * line_h

    sfont = load_font(FONT_SANS, 34, "Regular")
    sub_lines = wrap_lines(draw, subtitle, sfont, text_w)[:1] if subtitle else []
    sub_gap, sub_line_h = 18, 44
    sub_h = (sub_gap + sub_line_h) if sub_lines else 0

    block_h = title_h + sub_h
    y = region_top + max(0, (region_h - block_h) // 2)

    # Accent bar spans the centred text block.
    draw.rectangle([bar_x, y + 6, bar_x + 8, y + block_h - 6], fill=accent)

    for line in lines:
        draw.text((text_x, y), line, font=tfont, fill=CREAM)
        y += line_h
    if sub_lines:
        y += sub_gap
        draw.text((text_x, y), sub_lines[0], font=sfont, fill=CREAM_DIM)

    # Footer: hairline + wordmark.
    draw.line([(text_x, fy), (W - MARGIN, fy)], fill=GOLD, width=1)
    ffont = load_font(FONT_SANS, 27, "Medium")
    draw.text((text_x, fy + 26), spaced("THE BRITISH MANIFESTO ARCHIVE", 2),
              font=ffont, fill=CREAM)
    dfont = load_font(FONT_SANS, 27, "Regular")
    domain = "manifestos.org.uk"
    dw = draw.textlength(domain, font=dfont)
    draw.text((W - MARGIN - dw, fy + 26), domain, font=dfont, fill=GOLD)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "JPEG", quality=86, optimize=True, progressive=True)


def spaced(text, px):
    """Cheap letter-spacing via hair spaces between characters."""
    if px <= 0:
        return text
    return ("\u200a" * max(1, px // 2)).join(list(text))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", help="comma-separated: manifesto,party,election")
    parser.add_argument("--sample", action="store_true",
                        help="render a small representative sample only")
    args = parser.parse_args()

    seo = json.loads(SEO.read_text(encoding="utf-8"))
    parties = seo["parties"]
    elections = seo["elections"]
    manifestos = seo["manifestos"]

    types = set((args.only or "manifesto,party,election").split(","))
    count = 0

    if "election" in types:
        items = list(elections.items())
        if args.sample:
            items = items[:3]
        for eid, e in items:
            accent = hex_to_rgb(parties.get(e.get("winner"), {}).get("color"))
            draw_card(
                OG_DIR / "election" / f"{eid}.jpg",
                "General Election",
                f"{e['displayYear']} General Election",
                "Results, maps & party manifestos",
                accent,
            )
            count += 1

    if "party" in types:
        items = list(parties.items())
        if args.sample:
            items = items[:3]
        for pid, p in items:
            draw_card(
                OG_DIR / "party" / f"{pid}.jpg",
                "Party Archive",
                p["name"],
                "General election manifestos & history",
                hex_to_rgb(p.get("color")),
            )
            count += 1

    if "manifesto" in types:
        items = list(manifestos.items())
        if args.sample:
            items = items[:5]
        for key, m in items:
            eid, pid = m["electionId"], m["partyId"]
            party = parties.get(pid, {})
            election = elections.get(eid, {})
            name = party.get("name") or m.get("label") or pid
            year = election.get("displayYear", eid)
            draw_card(
                OG_DIR / "manifesto" / eid / f"{pid}.jpg",
                "Manifesto",
                name,
                f"{year} General Election Manifesto",
                hex_to_rgb(party.get("color")),
            )
            count += 1

    print(f"Wrote {count} OG cards to {OG_DIR.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
