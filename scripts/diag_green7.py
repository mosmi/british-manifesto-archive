#!/usr/bin/env python3
"""Check bullet text on page 4 of Green PDF."""
import pdfplumber
from collections import defaultdict

PDF_PATH = "/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2024/green/manifesto.pdf"

def strip_prefix(fontname):
    if '+' in fontname:
        return fontname.split('+', 1)[1]
    return fontname

with pdfplumber.open(PDF_PATH) as pdf:
    page = pdf.pages[3]  # Page 4
    chars = page.chars
    mid_x = page.bbox[2] / 2
    
    # Left half
    left_chars = [c for c in chars if c['x0'] < mid_x]
    
    lines_dict = defaultdict(list)
    for ch in left_chars:
        y_key = round(ch['y0'] / 2) * 2
        lines_dict[y_key].append(ch)
    
    print("Page 4 left half - y0 range 60-200:")
    for y_key in sorted(lines_dict.keys(), reverse=True):
        if y_key < 60 or y_key > 200:
            continue
        line_chars = sorted(lines_dict[y_key], key=lambda c: c['x0'])
        text = ''.join(c['text'] for c in line_chars).strip()
        if not text:
            continue
        fn = strip_prefix(line_chars[0]['fontname'])
        size = round(line_chars[0]['size'], 1)
        y0 = line_chars[0]['y0']
        x0 = line_chars[0]['x0']
        print(f"  y0={y0:.0f}, x0={x0:.0f}, fn={fn}, size={size}: {repr(text[:60])}")
