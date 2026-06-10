#!/usr/bin/env python3
"""Understand ZapfDingbats as bullet markers and how to handle bullet text."""
import pdfplumber
from collections import defaultdict

PDF_PATH = "/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2024/conservative/manifesto.pdf"

def strip_prefix(fontname):
    if '+' in fontname:
        return fontname.split('+', 1)[1]
    return fontname

with pdfplumber.open(PDF_PATH) as pdf:
    # Look at page 10 and 11 in detail - where ZapfDingbats appear alongside text
    for pg in [9, 10]:  # 0-indexed
        page = pdf.pages[pg]
        chars = page.chars
        if not chars:
            continue

        lines = defaultdict(list)
        for ch in chars:
            y_key = round(ch['y0'] / 2) * 2
            lines[y_key].append(ch)

        print(f"\n=== Page {pg+1} all lines ===")
        for y_key in sorted(lines.keys(), reverse=True):
            line_chars = sorted(lines[y_key], key=lambda c: c['x0'])
            # Group by font
            fonts_in_line = []
            for ch in line_chars:
                fn = strip_prefix(ch['fontname'])
                fonts_in_line.append(fn)
            unique_fonts = list(dict.fromkeys(fonts_in_line))
            text = ''.join(c['text'] for c in line_chars).strip()
            if not text:
                continue
            fontname = strip_prefix(line_chars[0]['fontname'])
            size = round(line_chars[0]['size'], 1)
            x0 = line_chars[0]['x0']
            print(f"  y0={y_key}, x0={x0:.0f}, font={fontname}/{unique_fonts[:3]}, size={size}: {repr(text[:70])}")
