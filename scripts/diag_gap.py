#!/usr/bin/env python3
"""Check the gap between columns more precisely."""

import pdfplumber
from collections import defaultdict

PDF_PATH = '/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2015/conservative/manifesto.pdf'

def strip_prefix(fontname):
    if '+' in fontname:
        return fontname.split('+', 1)[1]
    return fontname

with pdfplumber.open(PDF_PATH) as pdf:
    # Page 9 (idx 8) - examine the exact char positions in the gap zone
    page = pdf.pages[8]
    chars = page.chars

    lines = defaultdict(list)
    for ch in chars:
        if ch['x0'] > 565:
            continue
        y_key = round(ch['y0'] / 2) * 2
        lines[y_key].append(ch)

    print("=== Page 9 - chars in gap zone (x0 between 260 and 310) ===")
    for y_key in sorted(lines.keys(), reverse=True):
        line_chars = sorted(lines[y_key], key=lambda c: c['x0'])
        font = strip_prefix(line_chars[0]['fontname'])
        size = round(line_chars[0]['size'], 1)

        # Get chars in the gap zone
        gap_chars = [c for c in line_chars if 260 <= c['x0'] <= 310]
        if gap_chars:
            gap_text = ''.join(c['text'] for c in gap_chars)
            gap_x0 = [round(c['x0'], 1) for c in gap_chars]
            print(f"  y0={y_key} font={font} size={size}: gap chars x0={gap_x0[:10]}: {repr(gap_text[:30])}")

    # Check specifically at y0=436
    print("\n=== Page 9 y0=436 - all chars with x0 positions ===")
    y_key = 436
    if y_key in lines:
        for ch in sorted(lines[y_key], key=lambda c: c['x0']):
            print(f"  x0={ch['x0']:.1f} x1={ch['x1']:.1f} char={repr(ch['text'])}")
    else:
        # Try nearby
        for yk in range(430, 445):
            if yk in lines:
                print(f"\nFound at y_key={yk}:")
                for ch in sorted(lines[yk], key=lambda c: c['x0']):
                    print(f"  x0={ch['x0']:.1f} x1={ch['x1']:.1f} char={repr(ch['text'])}")
