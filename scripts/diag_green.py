#!/usr/bin/env python3
"""Diagnostic script for Green Party manifesto PDF."""
import pdfplumber
from collections import defaultdict, Counter

PDF_PATH = "/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2024/green/manifesto.pdf"

def strip_prefix(fontname):
    if '+' in fontname:
        return fontname.split('+', 1)[1]
    return fontname

with pdfplumber.open(PDF_PATH) as pdf:
    print(f"Total pages: {len(pdf.pages)}")
    
    # Check first few pages for structure
    for pg_idx in range(min(10, len(pdf.pages))):
        page = pdf.pages[pg_idx]
        chars = page.chars
        if not chars:
            print(f"Page {pg_idx+1}: IMAGE ONLY")
            continue
        print(f"Page {pg_idx+1}: {len(chars)} chars, bbox={page.bbox}")
    
    print("\n=== Font Statistics (pages 1-15) ===")
    font_stats = defaultdict(lambda: {'count': 0, 'samples': []})
    
    for pg_idx in range(min(15, len(pdf.pages))):
        page = pdf.pages[pg_idx]
        chars = page.chars
        if not chars:
            continue
        
        lines_dict = defaultdict(list)
        for ch in chars:
            y_key = round(ch['y0'] / 2) * 2
            lines_dict[y_key].append(ch)
        
        for y_key in sorted(lines_dict.keys(), reverse=True):
            line_chars = sorted(lines_dict[y_key], key=lambda c: c['x0'])
            text = ''.join(c['text'] for c in line_chars).strip()
            if not text:
                continue
            
            fontname = strip_prefix(line_chars[0]['fontname'])
            size = round(line_chars[0]['size'], 1)
            y0 = line_chars[0]['y0']
            
            key = (fontname, size)
            font_stats[key]['count'] += 1
            if len(font_stats[key]['samples']) < 2:
                font_stats[key]['samples'].append(f"[p{pg_idx+1}, y={y0:.0f}] {text[:50]}")
    
    for (font, size), stats in sorted(font_stats.items(), key=lambda x: -x[1]['count']):
        print(f"\nFont: {font}, Size: {size}, Count: {stats['count']}")
        for sample in stats['samples']:
            print(f"  Sample: {sample}")
    
    # Detailed look at page 3 (likely body text)
    print("\n\n=== Page 3 all lines ===")
    page = pdf.pages[2]
    chars = page.chars
    if chars:
        lines_dict = defaultdict(list)
        for ch in chars:
            y_key = round(ch['y0'] / 2) * 2
            lines_dict[y_key].append(ch)
        
        for y_key in sorted(lines_dict.keys(), reverse=True):
            line_chars = sorted(lines_dict[y_key], key=lambda c: c['x0'])
            text = ''.join(c['text'] for c in line_chars).strip()
            if not text:
                continue
            fontname = strip_prefix(line_chars[0]['fontname'])
            size = round(line_chars[0]['size'], 1)
            y0 = line_chars[0]['y0']
            x0 = line_chars[0]['x0']
            print(f"  y0={y0:.0f}, x0={x0:.0f}, fn={fontname}, size={size}: {text[:60]}")
