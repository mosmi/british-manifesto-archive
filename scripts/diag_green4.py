#!/usr/bin/env python3
"""Debug Green PDF page 2 column detection."""
import pdfplumber
from collections import defaultdict, Counter

PDF_PATH = "/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2024/green/manifesto.pdf"

def strip_prefix(fontname):
    if '+' in fontname:
        return fontname.split('+', 1)[1]
    return fontname

def classify_font(fontname, size):
    fn = strip_prefix(fontname)
    if 'BebasNeueBold' in fn and size >= 17:
        return 'watermark'
    if 'BebasNeueBold' in fn and size <= 13:
        return 'skip'
    if 'Manrope-Medium' in fn and size <= 11:
        return 'skip'
    if size <= 7:
        return 'skip'
    return 'body'

with pdfplumber.open(PDF_PATH) as pdf:
    # Page 2 (idx 1) - foreword with two columns
    page = pdf.pages[1]
    chars = page.chars
    mid_x = page.bbox[2] / 2  # ~595
    
    # Check right half (should have two columns)
    right_chars = [c for c in chars if c['x0'] >= mid_x]
    
    lines_dict = defaultdict(list)
    for ch in right_chars:
        y_key = round(ch['y0'] / 2) * 2
        lines_dict[y_key].append(ch)
    
    line_starts = []
    for y_key, lchars in lines_dict.items():
        if y_key < 15 or y_key > 810:
            continue
        sorted_c = sorted(lchars, key=lambda c: c['x0'])
        fn = strip_prefix(sorted_c[0]['fontname'])
        cls = classify_font(fn, sorted_c[0]['size'])
        if cls in ('skip', 'watermark'):
            continue
        line_starts.append(round(sorted_c[0]['x0'] / 5) * 5)
    
    buckets = Counter(line_starts)
    print(f"Page 2 right half (x >= {mid_x:.0f}) line-start x distribution:")
    for x, cnt in sorted(buckets.items()):
        print(f"  x={x}: {cnt}")
    
    # Check left half
    left_chars = [c for c in chars if c['x0'] < mid_x]
    lines_dict = defaultdict(list)
    for ch in left_chars:
        y_key = round(ch['y0'] / 2) * 2
        lines_dict[y_key].append(ch)
    
    line_starts = []
    for y_key, lchars in lines_dict.items():
        if y_key < 15 or y_key > 810:
            continue
        sorted_c = sorted(lchars, key=lambda c: c['x0'])
        fn = strip_prefix(sorted_c[0]['fontname'])
        cls = classify_font(fn, sorted_c[0]['size'])
        if cls in ('skip', 'watermark'):
            continue
        line_starts.append(round(sorted_c[0]['x0'] / 5) * 5)
    
    buckets = Counter(line_starts)
    print(f"\nPage 2 left half (x < {mid_x:.0f}) line-start x distribution:")
    for x, cnt in sorted(buckets.items()):
        print(f"  x={x}: {cnt}")
    
    # Check page 4 (first content page)
    page = pdf.pages[3]
    chars = page.chars
    mid_x = page.bbox[2] / 2
    
    for half in ['left', 'right']:
        if half == 'left':
            half_chars = [c for c in chars if c['x0'] < mid_x]
            mn, mx = 0, mid_x
        else:
            half_chars = [c for c in chars if c['x0'] >= mid_x]
            mn, mx = mid_x, page.bbox[2]
        
        lines_dict = defaultdict(list)
        for ch in half_chars:
            y_key = round(ch['y0'] / 2) * 2
            lines_dict[y_key].append(ch)
        
        line_starts = []
        for y_key, lchars in lines_dict.items():
            if y_key < 15 or y_key > 810:
                continue
            sorted_c = sorted(lchars, key=lambda c: c['x0'])
            fn = strip_prefix(sorted_c[0]['fontname'])
            cls = classify_font(fn, sorted_c[0]['size'])
            if cls in ('skip', 'watermark'):
                continue
            line_starts.append(round(sorted_c[0]['x0'] / 5) * 5)
        
        buckets = Counter(line_starts)
        print(f"\nPage 4 {half} half line-start x distribution:")
        for x, cnt in sorted(buckets.items()):
            print(f"  x={x}: {cnt}")
