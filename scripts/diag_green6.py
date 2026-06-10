#!/usr/bin/env python3
"""Check body text line spacing in Green PDF content pages."""
import pdfplumber
from collections import defaultdict, Counter

PDF_PATH = "/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2024/green/manifesto.pdf"

def strip_prefix(fontname):
    if '+' in fontname:
        return fontname.split('+', 1)[1]
    return fontname

with pdfplumber.open(PDF_PATH) as pdf:
    # Look at page 5 (idx 4) body text
    page = pdf.pages[4]
    chars = page.chars
    mid_x = page.bbox[2] / 2
    
    # Left half, left column (x=43-305)
    left_chars = [c for c in chars if c['x0'] < mid_x]
    
    lines_dict = defaultdict(list)
    for ch in left_chars:
        y_key = round(ch['y0'] / 2) * 2
        lines_dict[y_key].append(ch)
    
    print("Page 5 left-half left-column body text line y0 and gaps:")
    y_keys = sorted([y for y in lines_dict.keys() if 15 < y < 810], reverse=True)
    
    body_ys = []
    for y_key in y_keys:
        line_chars = sorted(lines_dict[y_key], key=lambda c: c['x0'])
        fn = strip_prefix(line_chars[0]['fontname'])
        size = line_chars[0]['size']
        if 'Bebas' in fn or size < 9 or size > 12:
            continue
        # Only col1 (x < 305)
        col1 = [c for c in line_chars if c['x0'] < 305]
        if col1:
            text = ''.join(c['text'] for c in col1).strip()[:40]
            body_ys.append((y_key, line_chars[0]['y0'], fn, size, text))
    
    gaps = []
    for i in range(len(body_ys)-1):
        gap = body_ys[i][0] - body_ys[i+1][0]
        gaps.append(gap)
        print(f"  y0={body_ys[i][0]}, gap={gap}: {body_ys[i][4]}")
    if body_ys:
        print(f"  y0={body_ys[-1][0]}: {body_ys[-1][4]}")
    
    print(f"\nGap distribution: {Counter(gaps)}")
