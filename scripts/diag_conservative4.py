#!/usr/bin/env python3
"""Understand column layout better."""
import pdfplumber
from collections import defaultdict

PDF_PATH = "/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2024/conservative/manifesto.pdf"

def strip_prefix(fontname):
    if '+' in fontname:
        return fontname.split('+', 1)[1]
    return fontname

with pdfplumber.open(PDF_PATH) as pdf:
    # Page 5 is foreword - what's the column structure?
    for pg_idx in [4, 5, 6, 7]:
        page = pdf.pages[pg_idx]
        chars = page.chars
        if not chars:
            print(f"Page {pg_idx+1}: image only")
            continue
        
        lines_dict = defaultdict(list)
        for ch in chars:
            y_key = round(ch['y0'] / 2) * 2
            lines_dict[y_key].append(ch)
        
        print(f"\n=== Page {pg_idx+1} x0 distribution ===")
        x0_vals = []
        for y_key in sorted(lines_dict.keys(), reverse=True):
            line_chars = sorted(lines_dict[y_key], key=lambda c: c['x0'])
            text = ''.join(c['text'] for c in line_chars).strip()
            if not text:
                continue
            fn = strip_prefix(line_chars[0]['fontname'])
            size = line_chars[0]['size']
            y0 = line_chars[0]['y0']
            x0 = line_chars[0]['x0']
            if y0 < 30:
                continue
            if 'Zapf' in fn or 'Cond' in fn or size <= 8.5:
                continue
            x0_vals.append((x0, y0, fn, size, text[:40]))
        
        # Show x0 distribution
        xs = [v[0] for v in x0_vals]
        if xs:
            print(f"  x0 range: {min(xs):.0f} - {max(xs):.0f}")
            # Show unique x0 start positions
            unique_starts = sorted(set(round(x/10)*10 for x in xs))
            print(f"  Unique x0 buckets (10pt): {unique_starts}")
        
        # Show first 10 lines with x0
        print(f"  First 15 content lines:")
        for x0, y0, fn, size, text in x0_vals[:15]:
            print(f"    x0={x0:.0f} y0={y0:.0f} {fn[:25]} {size:.0f}pt: {text}")
