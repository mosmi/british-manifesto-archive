#!/usr/bin/env python3
"""Check pages 7 (foreword) and understand full column structure."""

import pdfplumber
from collections import defaultdict

PDF_PATH = '/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2015/conservative/manifesto.pdf'

def strip_prefix(fontname):
    if '+' in fontname:
        return fontname.split('+', 1)[1]
    return fontname

SIDEBAR_X0 = 565
COLUMN_GAP_START = 280
COLUMN_GAP_END = 295

with pdfplumber.open(PDF_PATH) as pdf:
    # Check page 7 (foreword) - idx 6
    print("=== PAGE 7 (Foreword) - checking column structure ===")
    page = pdf.pages[6]
    chars = page.chars

    lines = defaultdict(list)
    for ch in chars:
        if ch['x0'] > SIDEBAR_X0:
            continue
        y_key = round(ch['y0'] / 2) * 2
        lines[y_key].append(ch)

    for y_key in sorted(lines.keys(), reverse=True):
        line_chars = sorted(lines[y_key], key=lambda c: c['x0'])
        text = ''.join(c['text'] for c in line_chars)
        fontname = strip_prefix(line_chars[0]['fontname'])
        size = round(line_chars[0]['size'], 1)
        y0 = line_chars[0]['y0']
        x0_min = min(c['x0'] for c in line_chars)
        x0_max = max(c['x1'] for c in line_chars)

        has_left = any(c['x0'] < COLUMN_GAP_START for c in line_chars)
        has_right = any(c['x0'] >= COLUMN_GAP_END for c in line_chars)
        col_indicator = 'BOTH' if (has_left and has_right) else ('LEFT' if has_left else 'RIGHT')

        print(f"  {col_indicator} y0={y0:.1f} x0={x0_min:.1f}-{x0_max:.1f} font={fontname} size={size}: {repr(text[:80])}")

    # Now check page 9 to understand which lines are headings vs body
    print("\n=== PAGE 9 - checking heading lines ===")
    page = pdf.pages[8]
    chars = page.chars
    lines = defaultdict(list)
    for ch in chars:
        if ch['x0'] > SIDEBAR_X0:
            continue
        y_key = round(ch['y0'] / 2) * 2
        lines[y_key].append(ch)

    for y_key in sorted(lines.keys(), reverse=True):
        line_chars = sorted(lines[y_key], key=lambda c: c['x0'])
        fontname = strip_prefix(line_chars[0]['fontname'])
        size = round(line_chars[0]['size'], 1)

        if 'Bold' in fontname or 'Italic' in fontname:
            left_chars = [c for c in line_chars if c['x0'] < COLUMN_GAP_END]
            right_chars = [c for c in line_chars if c['x0'] >= COLUMN_GAP_END]
            left_text = ''.join(c['text'] for c in sorted(left_chars, key=lambda c: c['x0']))
            right_text = ''.join(c['text'] for c in sorted(right_chars, key=lambda c: c['x0']))
            print(f"  y0={y_key} font={fontname} size={size}")
            print(f"    LEFT: {repr(left_text[:80])}")
            if right_text.strip():
                print(f"    RIGHT: {repr(right_text[:80])}")
