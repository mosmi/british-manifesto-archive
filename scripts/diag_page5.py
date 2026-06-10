#!/usr/bin/env python3
"""Detailed look at page 5 layout."""

import pdfplumber
from collections import defaultdict

PDF_PATH = '/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2015/conservative/manifesto.pdf'

def strip_prefix(fontname):
    if '+' in fontname:
        return fontname.split('+', 1)[1]
    return fontname

with pdfplumber.open(PDF_PATH) as pdf:
    # Page 5 (idx 4) - the intro page
    print("=== PAGE 5 (intro page) ===")
    page = pdf.pages[4]
    chars = page.chars

    lines = defaultdict(list)
    for ch in chars:
        y_key = round(ch['y0'] / 2) * 2
        lines[y_key].append(ch)

    for y_key in sorted(lines.keys(), reverse=True):
        line_chars = sorted(lines[y_key], key=lambda c: c['x0'])
        text = ''.join(c['text'] for c in line_chars)
        fontname = strip_prefix(line_chars[0]['fontname'])
        size = round(line_chars[0]['size'], 1)
        y0 = line_chars[0]['y0']
        x0_min = min(c['x0'] for c in line_chars)
        x0_max = max(c['x1'] for c in line_chars)
        print(f"  y0={y0:.1f} x0={x0_min:.1f}-{x0_max:.1f} font={fontname} size={size}: {repr(text[:100])}")

    # Now look at page 9 (first body page) to understand its full layout
    print("\n=== PAGE 9 (first body page) ALL lines ===")
    page = pdf.pages[8]
    chars = page.chars

    lines = defaultdict(list)
    for ch in chars:
        y_key = round(ch['y0'] / 2) * 2
        lines[y_key].append(ch)

    for y_key in sorted(lines.keys(), reverse=True):
        line_chars = sorted(lines[y_key], key=lambda c: c['x0'])
        text = ''.join(c['text'] for c in line_chars)
        fontname = strip_prefix(line_chars[0]['fontname'])
        size = round(line_chars[0]['size'], 1)
        y0 = line_chars[0]['y0']
        x0_min = min(c['x0'] for c in line_chars)
        x0_max = max(c['x1'] for c in line_chars)
        print(f"  y0={y0:.1f} x0={x0_min:.1f}-{x0_max:.1f} font={fontname} size={size}: {repr(text[:120])}")

    # Check if page 9 lines ever have chars spanning col gap (x0 < 280 AND chars x1 > 300)
    print("\n=== PAGE 9: checking which lines span both columns ===")
    for y_key in sorted(lines.keys(), reverse=True):
        line_chars = sorted(lines[y_key], key=lambda c: c['x0'])
        has_left = any(c['x0'] < 280 for c in line_chars)
        has_right = any(c['x0'] > 295 for c in line_chars)
        if has_left and has_right:
            text = ''.join(c['text'] for c in line_chars)
            fontname = strip_prefix(line_chars[0]['fontname'])
            x0_min = min(c['x0'] for c in line_chars)
            x0_max = max(c['x1'] for c in line_chars)
            print(f"  BOTH y0={y_key} x0={x0_min:.1f}-{x0_max:.1f} font={fontname}: {repr(text[:80])}")
