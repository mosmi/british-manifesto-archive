#!/usr/bin/env python3
"""
Convert 2015 Conservative manifesto PDF to markdown.

Two-column layout: left col x0~34-267, right col x0~299-553.
Gap between columns: x~267-299.
Sidebar vertical text: x0 > 565 (skip).

Key insight: Full-width elements (headings, pull quotes) start at x0<50 and
their chars span into the right column. We detect full-width lines by checking
if the leftmost char starts at x0 < 50 AND chars span across the column gap.
For body text lines spanning both columns, split at the gap.
"""

import pdfplumber
from collections import defaultdict
import re

PDF_PATH = '/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2015/conservative/manifesto.pdf'
OUT_PATH = '/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2015/conservative/manifesto.md'

LEFT_COL_END  = 270  # Left column clearly in left if x0 < this
RIGHT_COL_START = 299  # Right column clearly in right if x0 >= this
SIDEBAR_CUT   = 565  # Sidebar vertical text starts here

def strip_prefix(fontname):
    if '+' in fontname:
        return fontname.split('+', 1)[1]
    return fontname

def clean_text(text):
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)
    text = text.replace('\u00b7', '')
    text = re.sub(r'\.{3,}', '', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()

def is_leader_line(text):
    s = text.strip()
    if len(s) < 4:
        return False
    dots = sum(1 for c in s if c in '.\u00b7\u2026')
    return dots / len(s) > 0.4

def majority_font_size(chars):
    counts = defaultdict(int)
    for ch in chars:
        fn = strip_prefix(ch['fontname'])
        sz = round(ch['size'], 1)
        counts[(fn, sz)] += 1
    return max(counts, key=counts.get) if counts else ('', 0)

def process_page(page):
    """
    Returns two ordered lists:
      left_lines: [(y_key, text, font, size, x0), ...] top-to-bottom
      right_lines: [(y_key, text, font, size, x0), ...] top-to-bottom

    For each y-bucket:
    - If chars appear BOTH at x<LEFT_COL_END AND at x>=RIGHT_COL_START, it's two-column.
      Split the chars at the gap and add to left_lines and right_lines.
    - Otherwise, it's a single element (heading, centered, single-column).
      Assign to left or right based on majority x0.
    """
    chars = page.chars
    if not chars:
        return [], []

    # Bucket chars by y (2pt buckets), excluding sidebar
    buckets = defaultdict(list)
    for ch in chars:
        if ch['x0'] > SIDEBAR_CUT:
            continue
        y_key = round(ch['y0'] / 2) * 2
        buckets[y_key].append(ch)

    left_lines = []
    right_lines = []

    for y_key in sorted(buckets.keys(), reverse=True):
        all_chars = sorted(buckets[y_key], key=lambda c: c['x0'])
        if not all_chars:
            continue

        font, size = majority_font_size(all_chars)

        # Determine if this is truly two-column:
        # Strategy: detect the gap between the last char of the left-ish group
        # and the first char of the right-ish group.
        # Body text: gap of ~14pt between left col end (~285) and right col start (299)
        # Headings crossing the gap: continuous text, no gap
        right_col_chars = [c for c in all_chars if c['x0'] >= RIGHT_COL_START]

        if right_col_chars:
            # Find the last char before the right column starts
            left_side_chars = [c for c in all_chars if c['x0'] < RIGHT_COL_START]
            if left_side_chars:
                max_x1_left = max(c['x1'] for c in left_side_chars)
                min_x0_right = min(c['x0'] for c in right_col_chars)
                gap_width = min_x0_right - max_x1_left
                # Two-column: there's a gap of at least 8pt between the columns
                is_two_col = gap_width >= 8
            else:
                is_two_col = False
        else:
            is_two_col = False

        # Also split chars
        left_col_chars = [c for c in all_chars if c['x0'] < RIGHT_COL_START]
        gap_chars = []  # No longer needed separately

        if is_two_col:
            # Split at RIGHT_COL_START (x=299)
            left_chars = left_col_chars
            right_chars = right_col_chars

            if left_chars:
                text = ''.join(c['text'] for c in sorted(left_chars, key=lambda c: c['x0'])).strip()
                if text and not is_leader_line(text):
                    f, s = majority_font_size(left_chars)
                    x0 = min(c['x0'] for c in left_chars)
                    left_lines.append((y_key, text, f, s, x0))

            if right_chars:
                text = ''.join(c['text'] for c in sorted(right_chars, key=lambda c: c['x0'])).strip()
                if text and not is_leader_line(text):
                    f, s = majority_font_size(right_chars)
                    x0 = min(c['x0'] for c in right_chars)
                    right_lines.append((y_key, text, f, s, x0))
        else:
            # Single element - take all chars as-is
            text = ''.join(c['text'] for c in all_chars).strip()
            if not text or is_leader_line(text):
                continue
            x0 = all_chars[0]['x0']
            # Assign based on starting x0
            if x0 >= RIGHT_COL_START:
                right_lines.append((y_key, text, font, size, x0))
            else:
                left_lines.append((y_key, text, font, size, x0))

    left_lines.sort(key=lambda e: -e[0])
    right_lines.sort(key=lambda e: -e[0])
    return left_lines, right_lines


def classify(text, font, size, x0, y_key):
    """
    Classify and return (type, cleaned_text) or None to skip.
    """
    fn = font.lower()

    # Skip running headers at top: OpenSans-Semibold ~8pt (y_key > 785)
    if y_key > 784 and 'opensans-semibold' in fn and size <= 9:
        return None

    # Skip footers (y_key < 38)
    if y_key < 38:
        return None

    if is_leader_line(text):
        return None
    if size < 7:
        return None

    cleaned = clean_text(text)
    if not cleaned:
        return None

    # Chapter heading: OpenSans-Bold 20pt+
    if 'opensans-bold' in fn and size >= 20:
        cleaned = re.sub(r'\s+[A-Z]$', '', cleaned).strip()
        return ('h2', cleaned) if cleaned else None

    # Sub-heading: OpenSans-Bold 14-19pt
    if 'opensans-bold' in fn and 14 <= size < 20:
        cleaned = re.sub(r'\s+[A-Z]$', '', cleaned).strip()
        return ('h3', cleaned) if cleaned else None

    # Sub-sub heading: OpenSans-Bold 11-13pt
    if 'opensans-bold' in fn and size >= 11:
        return ('h4', cleaned)

    # Pull quote: OpenSans-BoldItalic (any size here it's 16pt or 12pt)
    if 'opensans-bolditalic' in fn:
        cleaned = re.sub(r'\s+[A-Z]$', '', cleaned).strip()
        return ('pullquote', cleaned) if cleaned else None

    # Pull quote: OpenSans-SemiboldItalic 15pt+
    if 'opensans-semibolditalic' in fn and size >= 15:
        cleaned = re.sub(r'\s+[A-Z]$', '', cleaned).strip()
        return ('pullquote', cleaned) if cleaned else None

    # Bullet/commitment items: OpenSans-Italic 11pt+
    if 'opensans-italic' in fn and size >= 11:
        # Strip trailing stray chars
        cleaned = re.sub(r'\s+[A-Z]{1,2}$', '', cleaned).strip()
        return ('bullet', cleaned) if cleaned else None

    # Stats/callouts: OpenSans regular 14pt+ - skip (design elements)
    if fn == 'opensans' and size >= 14:
        return None

    # Body text: Baskerville 10pt+
    if 'baskerville' in fn and size >= 10:
        cleaned = re.sub(r'\s+[A-Z]$', '', cleaned).strip()
        return ('body', cleaned) if cleaned else None

    if 'baskerville' in fn:
        return ('body', cleaned) if cleaned else None

    return None


def lines_to_markdown(entries):
    """
    Convert classified (type, text) tuples to markdown lines.
    """
    md = []
    prev_type = None
    bullet_buffer = []

    def flush_bullets():
        nonlocal bullet_buffer
        if not bullet_buffer:
            return
        # Merge continuation lines
        merged = []
        cur = None
        for bt in bullet_buffer:
            if cur is None:
                cur = bt
            elif bt and (bt[0].islower() or bt[0] in '£0123456789–-—('):
                cur = cur + ' ' + bt
            else:
                merged.append(cur)
                cur = bt
        if cur:
            merged.append(cur)
        for b in merged:
            md.append(f'* {b}')
        bullet_buffer.clear()

    for item_type, text in entries:
        if item_type == 'h2':
            flush_bullets()
            if md and md[-1] != '':
                md.append('')
            md.append(f'## {text}')
            md.append('')
            prev_type = 'h2'

        elif item_type == 'h3':
            flush_bullets()
            if md and md[-1] != '':
                md.append('')
            md.append(f'### {text}')
            md.append('')
            prev_type = 'h3'

        elif item_type == 'h4':
            flush_bullets()
            if md and md[-1] != '':
                md.append('')
            md.append(f'#### {text}')
            md.append('')
            prev_type = 'h4'

        elif item_type == 'pullquote':
            flush_bullets()
            if md and md[-1] != '':
                md.append('')
            md.append(f'> *{text}*')
            md.append('')
            prev_type = 'pullquote'

        elif item_type == 'bullet':
            bullet_buffer.append(text)
            prev_type = 'bullet'

        elif item_type == 'col_break':
            # Column break - force paragraph break
            flush_bullets()
            prev_type = 'col_break'

        elif item_type == 'body':
            flush_bullets()
            if prev_type == 'body':
                md[-1] = md[-1] + ' ' + text
            else:
                if md and md[-1] != '':
                    md.append('')
                md.append(text)
            prev_type = 'body'

    flush_bullets()
    return md


def main():
    SKIP_PAGES = {0, 2, 3}  # cover spread, image, contents

    output = ['# Conservative Party Manifesto 2015', '']

    with pdfplumber.open(PDF_PATH) as pdf:
        total = len(pdf.pages)
        print(f"Processing {total} pages...")

        for idx in range(total):
            page = pdf.pages[idx]

            if idx in SKIP_PAGES:
                print(f"  Skipping page {idx+1}")
                continue

            if not page.chars:
                print(f"  Page {idx+1}: image-only")
                continue

            print(f"  Processing page {idx+1}...")

            left_lines, right_lines = process_page(page)

            if not left_lines and not right_lines:
                continue

            # Classify
            left_cl = []
            for y_key, text, font, size, x0 in left_lines:
                r = classify(text, font, size, x0, y_key)
                if r:
                    left_cl.append(r)

            right_cl = []
            for y_key, text, font, size, x0 in right_lines:
                r = classify(text, font, size, x0, y_key)
                if r:
                    right_cl.append(r)

            if not left_cl and not right_cl:
                continue

            # Output left column, then right column
            # Insert a sentinel 'col_break' between them so body paragraphs
            # don't bleed across columns
            all_cl = left_cl
            if right_cl:
                all_cl = left_cl + [('col_break', '')] + right_cl

            page_md = lines_to_markdown(all_cl)
            output.extend(page_md)

    # Cleanup
    cleaned = []
    blanks = 0
    for line in output:
        if line == '':
            blanks += 1
            if blanks <= 1:
                cleaned.append(line)
        else:
            blanks = 0
            cleaned.append(line)

    while cleaned and cleaned[-1] == '':
        cleaned.pop()

    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(cleaned))
        f.write('\n')

    print(f"\nDone! Written to {OUT_PATH}")
    print(f"Total lines: {len(cleaned)}")


if __name__ == '__main__':
    main()
