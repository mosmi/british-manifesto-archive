#!/usr/bin/env python3
"""More detailed diagnostic for Conservative PDF - check ZapfDingbats y0 values and page structure."""
import pdfplumber
from collections import defaultdict

PDF_PATH = "/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2024/conservative/manifesto.pdf"

def strip_prefix(fontname):
    if '+' in fontname:
        return fontname.split('+', 1)[1]
    return fontname

with pdfplumber.open(PDF_PATH) as pdf:
    # Check ZapfDingbats on pages 6, 8, 9 to understand y0 range
    for pg in [5, 7, 8, 9, 10]:  # 0-indexed
        page = pdf.pages[pg]
        chars = page.chars
        if not chars:
            continue

        lines = defaultdict(list)
        for ch in chars:
            y_key = round(ch['y0'] / 2) * 2
            lines[y_key].append(ch)

        print(f"\n=== Page {pg+1} ZapfDingbats and low y0 elements ===")
        for y_key in sorted(lines.keys(), reverse=True):
            line_chars = sorted(lines[y_key], key=lambda c: c['x0'])
            text = ''.join(c['text'] for c in line_chars).strip()
            if not text:
                continue
            fontname = strip_prefix(line_chars[0]['fontname'])
            size = round(line_chars[0]['size'], 1)

            if 'Zapf' in fontname or y_key < 100 or y_key > 800:
                print(f"  y0={y_key}, font={fontname}, size={size}: {repr(text[:40])}")

    # Also check what's at the top of pages (running header y0)
    print("\n\n=== Running headers (ProximaNovaCond-SemiboldIt) across multiple pages ===")
    for pg in range(4, 15):
        page = pdf.pages[pg]
        chars = page.chars
        if not chars:
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
            if 'Cond' in fontname or y_key < 30:
                print(f"  Page {pg+1}, y0={y_key}, font={fontname}: {text[:60]}")
