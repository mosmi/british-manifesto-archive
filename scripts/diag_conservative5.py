#!/usr/bin/env python3
"""Debug column detection on page 5."""
import pdfplumber
from collections import defaultdict

PDF_PATH = "/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2024/conservative/manifesto.pdf"

def strip_prefix(fontname):
    if '+' in fontname:
        return fontname.split('+', 1)[1]
    return fontname

with pdfplumber.open(PDF_PATH) as pdf:
    # Page 5 (idx 4)
    page = pdf.pages[4]
    chars = page.chars
    
    lines_dict = defaultdict(list)
    for ch in chars:
        y_key = round(ch['y0'] / 2) * 2
        lines_dict[y_key].append(ch)
    
    print("Page 5 - all chars at same y_key showing potential column overlap:")
    for y_key in sorted(lines_dict.keys(), reverse=True):
        line_chars = sorted(lines_dict[y_key], key=lambda c: c['x0'])
        if y_key < 30:
            continue
        
        fn = strip_prefix(line_chars[0]['fontname'])
        if 'Cond' in fn or line_chars[0]['size'] <= 8.5:
            continue
        
        # Show x0 ranges within same y bucket
        x0s = [round(c['x0'], 0) for c in line_chars]
        text_by_x = {}
        for c in line_chars:
            col = 'left' if c['x0'] < 240 else 'right'
            if col not in text_by_x:
                text_by_x[col] = ''
            text_by_x[col] += c['text']
        
        if 'right' in text_by_x and 'left' in text_by_x:
            print(f"  y={y_key}: LEFT='{text_by_x['left'][:30]}' RIGHT='{text_by_x['right'][:30]}'")
        elif 'right' in text_by_x:
            print(f"  y={y_key}: RIGHT='{text_by_x['right'][:50]}'")
        else:
            print(f"  y={y_key}: LEFT='{text_by_x.get('left', '')[:50]}'")
    
    # Also check page width and bbox
    print(f"\nPage 5 bbox: {page.bbox}")
    
    # Check which pages have overlapping columns (same y, different x)
    print("\n\nPages with interleaved column content:")
    for pg_idx in range(4, 20):
        page = pdf.pages[pg_idx]
        chars = page.chars
        if not chars:
            continue
        
        lines_dict = defaultdict(list)
        for ch in chars:
            y_key = round(ch['y0'] / 2) * 2
            lines_dict[y_key].append(ch)
        
        overlap_count = 0
        for y_key, line_chars in lines_dict.items():
            if y_key < 30:
                continue
            fn = strip_prefix(line_chars[0]['fontname'])
            if 'Cond' in fn or line_chars[0]['size'] <= 8.5:
                continue
            x0s = [c['x0'] for c in line_chars]
            if min(x0s) < 200 and max(x0s) > 250:
                overlap_count += 1
        
        if overlap_count > 2:
            print(f"  Page {pg_idx+1}: {overlap_count} lines with overlapping x0")
