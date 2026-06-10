#!/usr/bin/env python3
"""Diagnostic script for Conservative manifesto PDF."""
import pdfplumber
from collections import defaultdict

PDF_PATH = "/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2024/conservative/manifesto.pdf"

def strip_prefix(fontname):
    """Strip font prefixes like CAGUPY+ or TLUSTQ+."""
    if '+' in fontname:
        return fontname.split('+', 1)[1]
    return fontname

with pdfplumber.open(PDF_PATH) as pdf:
    print(f"Total pages: {len(pdf.pages)}")

    # Collect font stats across pages 5-20
    font_stats = defaultdict(lambda: {'count': 0, 'samples': []})

    for page_num in range(4, 20):  # 0-indexed, so pages 5-20
        if page_num >= len(pdf.pages):
            break
        page = pdf.pages[page_num]
        chars = page.chars
        if not chars:
            print(f"Page {page_num+1}: IMAGE ONLY (no chars)")
            continue

        lines = defaultdict(list)
        for ch in chars:
            y_key = round(ch['y0'] / 2) * 2
            lines[y_key].append(ch)

        for y_key in sorted(lines.keys(), reverse=True):
            line_chars = sorted(lines[y_key], key=lambda c: c['x0'])
            text = ''.join(c['text'] for c in line_chars).strip()
            if not text:
                continue

            fontname = strip_prefix(line_chars[0]['fontname'])
            size = round(line_chars[0]['size'], 1)
            y0 = line_chars[0]['y0']

            key = (fontname, size)
            font_stats[key]['count'] += 1
            if len(font_stats[key]['samples']) < 3:
                font_stats[key]['samples'].append(f"[p{page_num+1}, y={y0:.0f}] {text[:60]}")

    print("\n=== Font Statistics (pages 5-20) ===")
    for (font, size), stats in sorted(font_stats.items(), key=lambda x: -x[1]['count']):
        print(f"\nFont: {font}, Size: {size}, Count: {stats['count']}")
        for sample in stats['samples']:
            print(f"  Sample: {sample}")

    # Also check y0 ranges for running headers and footers
    print("\n\n=== Y0 ranges for page 5 (foreword) ===")
    page = pdf.pages[4]  # Page 5, 0-indexed
    chars = page.chars
    lines = defaultdict(list)
    for ch in chars:
        y_key = round(ch['y0'] / 2) * 2
        lines[y_key].append(ch)

    for y_key in sorted(lines.keys(), reverse=True):
        line_chars = sorted(lines[y_key], key=lambda c: c['x0'])
        text = ''.join(c['text'] for c in line_chars).strip()
        if not text:
            continue
        fontname = strip_prefix(line_chars[0]['fontname'])
        size = round(line_chars[0]['size'], 1)
        print(f"  y0={y_key}, font={fontname}, size={size}: {text[:60]}")
