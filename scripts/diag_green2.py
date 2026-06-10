#!/usr/bin/env python3
"""Detailed Green PDF diagnostic - understand spread layout."""
import pdfplumber
from collections import defaultdict, Counter

PDF_PATH = "/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2024/green/manifesto.pdf"

def strip_prefix(fontname):
    if '+' in fontname:
        return fontname.split('+', 1)[1]
    return fontname

with pdfplumber.open(PDF_PATH) as pdf:
    print(f"Total pages: {len(pdf.pages)}")
    
    # Detailed view of page 4 (first real content page)
    for pg_idx in [1, 3]:  # Pages 2 and 4
        page = pdf.pages[pg_idx]
        chars = page.chars
        if not chars:
            print(f"Page {pg_idx+1}: no chars")
            continue
        
        lines_dict = defaultdict(list)
        for ch in chars:
            y_key = round(ch['y0'] / 2) * 2
            lines_dict[y_key].append(ch)
        
        print(f"\n=== Page {pg_idx+1} (bbox={page.bbox[2]:.0f}x{page.bbox[3]:.0f}) ===")
        for y_key in sorted(lines_dict.keys(), reverse=True):
            line_chars = sorted(lines_dict[y_key], key=lambda c: c['x0'])
            text = ''.join(c['text'] for c in line_chars).strip()
            if not text:
                continue
            fn = strip_prefix(line_chars[0]['fontname'])
            size = round(line_chars[0]['size'], 1)
            y0 = line_chars[0]['y0']
            x0 = line_chars[0]['x0']
            print(f"  y0={y0:.0f}, x0={x0:.0f}, fn={fn}, size={size}: {repr(text[:60])}")
    
    # Understand x0 distribution on content pages
    print("\n\n=== X0 distribution on page 4 (content) ===")
    page = pdf.pages[3]
    chars = page.chars
    lines_dict = defaultdict(list)
    for ch in chars:
        y_key = round(ch['y0'] / 2) * 2
        lines_dict[y_key].append(ch)
    
    x0_vals = []
    for y_key, lchars in lines_dict.items():
        sorted_c = sorted(lchars, key=lambda c: c['x0'])
        fn = strip_prefix(sorted_c[0]['fontname'])
        size = sorted_c[0]['size']
        if y_key < 15 or y_key > 830:
            continue
        x0_vals.append(round(sorted_c[0]['x0'] / 10) * 10)
    
    buckets = Counter(x0_vals)
    for x, cnt in sorted(buckets.items()):
        print(f"  x0={x}: {cnt}")
