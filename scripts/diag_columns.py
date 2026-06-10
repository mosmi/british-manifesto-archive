#!/usr/bin/env python3
"""Investigate two-column layout in Conservative manifesto."""

import pdfplumber
from collections import defaultdict, Counter

PDF_PATH = '/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2015/conservative/manifesto.pdf'

def strip_prefix(fontname):
    if '+' in fontname:
        return fontname.split('+', 1)[1]
    return fontname

with pdfplumber.open(PDF_PATH) as pdf:
    # Look at pages with two-column body text
    # Page 9 (idx 8) appears to be body text
    for page_idx in [8, 9, 10, 15, 20, 30]:
        page = pdf.pages[page_idx]
        chars = page.chars
        if not chars:
            continue

        print(f"\n=== Page {page_idx+1} - x0 distribution of Baskerville 11pt ===")
        body_x0 = [round(ch['x0']) for ch in chars
                   if strip_prefix(ch['fontname']) == 'Baskerville'
                   and 10 <= ch['size'] <= 12]
        x0_counter = Counter(body_x0)

        # Show histogram
        buckets = defaultdict(int)
        for x0, count in x0_counter.items():
            bucket = (x0 // 20) * 20
            buckets[bucket] += count
        for b in sorted(buckets):
            print(f"  x0 {b:3d}-{b+19:3d}: {'#' * (buckets[b] // 5)} ({buckets[b]})")

    # Look at page 9 in detail - identify column split
    print("\n\n=== Page 9 line x0 ranges (Baskerville 11pt) ===")
    page = pdf.pages[8]
    chars = page.chars
    lines = defaultdict(list)
    for ch in chars:
        y_key = round(ch['y0'] / 2) * 2
        lines[y_key].append(ch)

    for y_key in sorted(lines.keys(), reverse=True):
        line_chars = sorted(lines[y_key], key=lambda c: c['x0'])
        bask_chars = [c for c in line_chars if strip_prefix(c['fontname']) == 'Baskerville' and 10 <= c['size'] <= 12]
        if not bask_chars:
            continue

        x0_vals = [round(c['x0']) for c in bask_chars]
        x1_vals = [round(c['x1']) for c in bask_chars]
        text = ''.join(c['text'] for c in bask_chars)
        print(f"  y0={y_key} x0={min(x0_vals)}-{max(x1_vals)}: {repr(text[:80])}")
