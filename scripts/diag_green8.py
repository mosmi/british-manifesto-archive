#!/usr/bin/env python3
"""Check exact y0 values for bullet markers on page 4."""
import pdfplumber

PDF_PATH = "/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2024/green/manifesto.pdf"

def strip_prefix(fontname):
    if '+' in fontname:
        return fontname.split('+', 1)[1]
    return fontname

with pdfplumber.open(PDF_PATH) as pdf:
    page = pdf.pages[3]  # Page 4
    chars = page.chars
    mid_x = page.bbox[2] / 2
    
    # Find all chars near y=161 in the left half
    print("Page 4: chars near y=161 in left half (x < 305):")
    for ch in sorted(chars, key=lambda c: c['y0']):
        if ch['x0'] >= 305 or ch['x0'] < mid_x:
            pass
        if ch['x0'] >= 305:
            continue
        if 155 < ch['y0'] < 170:
            fn = strip_prefix(ch['fontname'])
            print(f"  y0={ch['y0']:.3f}, x0={ch['x0']:.3f}, size={ch['size']:.1f}, fn={fn}: {repr(ch['text'])}")
    
    # Also show the • markers and nearby text
    print("\nAll bullet markers (size ≈ 13pt) in left half of page 4:")
    for ch in sorted(chars, key=lambda c: c['y0'], reverse=True):
        if ch['x0'] >= 305:
            continue
        if abs(ch['size'] - 13.0) < 1 and ch['text'] in ('•',):
            y0 = ch['y0']
            # Find nearby chars at same y
            nearby = [c for c in chars if c['x0'] < 305 and abs(c['y0'] - y0) < 3]
            nearby.sort(key=lambda c: c['x0'])
            text = ''.join(c['text'] for c in nearby)
            print(f"  Bullet at y0={y0:.3f}: nearby text = {repr(text[:50])}")
