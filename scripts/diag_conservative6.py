#!/usr/bin/env python3
"""Check word-start x positions for column detection."""
import pdfplumber
from collections import defaultdict

PDF_PATH = "/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2024/conservative/manifesto.pdf"

def strip_prefix(fontname):
    if '+' in fontname:
        return fontname.split('+', 1)[1]
    return fontname

with pdfplumber.open(PDF_PATH) as pdf:
    for pg_idx in [4, 5, 7]:  # Pages 5, 6, 8
        page = pdf.pages[pg_idx]
        chars = page.chars
        if not chars:
            continue
        
        # Group chars by y position
        lines_dict = defaultdict(list)
        for ch in chars:
            y_key = round(ch['y0'] / 2) * 2
            lines_dict[y_key].append(ch)
        
        # For each line, find all "word start" x positions (chars preceded by space or start of line)
        word_starts = []
        for y_key in sorted(lines_dict.keys(), reverse=True):
            line_chars = sorted(lines_dict[y_key], key=lambda c: c['x0'])
            if y_key < 30:
                continue
            fn = strip_prefix(line_chars[0]['fontname'])
            if 'Cond' in fn or line_chars[0]['size'] <= 8.5 or 'Zapf' in fn:
                continue
            
            # First char of line is a word start
            word_starts.append(round(line_chars[0]['x0'], 0))
            
            # Find word starts within line (chars with big x gap from previous)
            prev_x = line_chars[0]['x0'] + line_chars[0].get('width', 6)
            for ch in line_chars[1:]:
                if ch['x0'] - prev_x > 3:  # Gap suggests new word/column
                    word_starts.append(round(ch['x0'], 0))
                prev_x = ch['x0'] + ch.get('width', 6)
        
        # Show distribution
        from collections import Counter
        buckets = Counter(round(x/10)*10 for x in word_starts)
        print(f"\nPage {pg_idx+1} word-start x distribution (10pt buckets):")
        for x, cnt in sorted(buckets.items()):
            print(f"  x={x}: {cnt}")
        
        # Try finding the line-start x positions only
        line_starts = []
        for y_key in sorted(lines_dict.keys(), reverse=True):
            line_chars = sorted(lines_dict[y_key], key=lambda c: c['x0'])
            if y_key < 30:
                continue
            fn = strip_prefix(line_chars[0]['fontname'])
            if 'Cond' in fn or line_chars[0]['size'] <= 8.5 or 'Zapf' in fn:
                continue
            line_starts.append(round(line_chars[0]['x0'], 0))
        
        buckets2 = Counter(round(x/10)*10 for x in line_starts)
        print(f"  Line-start x distribution:")
        for x, cnt in sorted(buckets2.items()):
            print(f"    x={x}: {cnt}")
