#!/usr/bin/env python3
"""Further Green PDF diagnostic - understand all pages."""
import pdfplumber
from collections import defaultdict

PDF_PATH = "/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2024/green/manifesto.pdf"

def strip_prefix(fontname):
    if '+' in fontname:
        return fontname.split('+', 1)[1]
    return fontname

with pdfplumber.open(PDF_PATH) as pdf:
    print(f"Total pages: {len(pdf.pages)}")
    
    for pg_idx in range(len(pdf.pages)):
        page = pdf.pages[pg_idx]
        chars = page.chars
        bbox_w = page.bbox[2]
        n_chars = len(chars) if chars else 0
        print(f"Page {pg_idx+1}: w={bbox_w:.0f}, chars={n_chars}")
    
    # Check where x=595 split is for the two-page spreads
    # Left page: x0 < 595, right page: x0 >= 595
    # But looking at data: left ~43-305, right ~638-920
    # The actual midpoint seems to be around 595 (half of 1190)
    
    # Check what's near the center of the spread
    print("\n\n=== Checking page 4 x0 around midpoint ===")
    page = pdf.pages[3]
    chars = page.chars
    if chars:
        lines_dict = defaultdict(list)
        for ch in chars:
            y_key = round(ch['y0'] / 2) * 2
            lines_dict[y_key].append(ch)
        
        for y_key in sorted(lines_dict.keys(), reverse=True)[:20]:
            line_chars = sorted(lines_dict[y_key], key=lambda c: c['x0'])
            if y_key < 15:
                continue
            fn = strip_prefix(line_chars[0]['fontname'])
            x0s = [c['x0'] for c in line_chars]
            text = ''.join(c['text'] for c in line_chars).strip()
            if text and (min(x0s) > 590 or max(x0s) > 590):
                print(f"  y={y_key}, x0_range={min(x0s):.0f}-{max(x0s):.0f}: {text[:40]}")
    
    # Check the last few pages to understand structure
    print("\n\n=== Last pages structure ===")
    for pg_idx in range(max(0, len(pdf.pages)-5), len(pdf.pages)):
        page = pdf.pages[pg_idx]
        chars = page.chars
        if not chars:
            print(f"Page {pg_idx+1}: no chars")
            continue
        
        lines_dict = defaultdict(list)
        for ch in chars:
            y_key = round(ch['y0'] / 2) * 2
            lines_dict[y_key].append(ch)
        
        print(f"\nPage {pg_idx+1}:")
        for y_key in sorted(lines_dict.keys(), reverse=True)[:10]:
            line_chars = sorted(lines_dict[y_key], key=lambda c: c['x0'])
            text = ''.join(c['text'] for c in line_chars).strip()
            if not text:
                continue
            fn = strip_prefix(line_chars[0]['fontname'])
            size = line_chars[0]['size']
            y0 = line_chars[0]['y0']
            x0 = line_chars[0]['x0']
            print(f"  y0={y0:.0f}, x0={x0:.0f}, {fn}: {text[:50]}")
