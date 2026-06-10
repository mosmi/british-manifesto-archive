#!/usr/bin/env python3
"""Check line spacing in Green PDF."""
import pdfplumber
from collections import defaultdict

PDF_PATH = "/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2024/green/manifesto.pdf"

def strip_prefix(fontname):
    if '+' in fontname:
        return fontname.split('+', 1)[1]
    return fontname

with pdfplumber.open(PDF_PATH) as pdf:
    page = pdf.pages[1]  # Page 2 - foreword
    chars = page.chars
    mid_x = page.bbox[2] / 2  # ~595
    
    # Check right-half left column only (x=638-785)
    right_chars = [c for c in chars if c['x0'] >= mid_x]
    
    lines_dict = defaultdict(list)
    for ch in right_chars:
        y_key = round(ch['y0'] / 2) * 2
        lines_dict[y_key].append(ch)
    
    print("Page 2 right half content - checking line y0 and gaps:")
    y_keys = sorted(lines_dict.keys(), reverse=True)
    
    # Show first 20 lines with gaps
    prev_y = None
    for y_key in y_keys:
        line_chars = sorted(lines_dict[y_key], key=lambda c: c['x0'])
        fn = strip_prefix(line_chars[0]['fontname'])
        size = line_chars[0]['size']
        y0 = line_chars[0]['y0']
        if y0 < 15 or y0 > 810:
            continue
        if 'Bebas' in fn:
            continue
        
        # Only show col1 (x < 785)
        col1_chars = [c for c in line_chars if c['x0'] < 785]
        col2_chars = [c for c in line_chars if c['x0'] >= 785]
        
        gap_str = f" (gap={prev_y-y0:.0f})" if prev_y else ""
        if col1_chars:
            text1 = ''.join(c['text'] for c in col1_chars).strip()[:30]
            print(f"  y0={y0:.0f}{gap_str}, col1: {text1}")
        if col2_chars:
            text2 = ''.join(c['text'] for c in col2_chars).strip()[:30]
            print(f"  y0={y0:.0f}{gap_str}, col2: {text2}")
        
        prev_y = y0
        
        if y0 < 500:
            break
