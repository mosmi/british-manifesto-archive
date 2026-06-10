#!/usr/bin/env python3
"""
Convert 2015 Green Party manifesto PDF to markdown.

Layout:
- Single A4 page (595x842pt)
- Mostly single-column, x0 ~50-540
- Foreword (pages 6-7) has two-column body text: left col x0~54-280, right col x0~301-540
- Decorative stacked chars: BebasNeueBold 41pt (chapter openers, skip them)
- Running footer: BebasNeueRegular 8pt at y0=24 -> skip
- BebasNeueBook 40pt: chapter headings -> ##
- BebasNeueBold 16pt: section headings -> ###
- HelveticaNeueLTPro-Cn 12pt: lead-in body text -> body
- HelveticaNeueLTPro-Cn 10pt: body text -> body
- HelveticaNeueLTPro-CnO 10pt: italic body -> body
- HelveticaNeueLTPro-BdCn 10pt: bold body -> bold body
- SymbolMT 10pt: bullet markers (bullet + tab + text, or bullet alone) -> bullet
- BebasNeueRegular 14pt: author name -> author
- BebasNeueRegular 18pt: TOC entries (with leader dots) -> skip
- HelveticaNeueLTPro-LtCn 10pt: TOC sub-entries -> skip

SKIP_PAGES: 0 (cover), 1 (copyright), 2 (TOC p1), 3 (TOC p2), 4 (TOC p3),
            5 (Foreword chapter opener decorative), 6 (policy on a page chapter opener)
            83 (last page - just footer)
Note: pages 5 and 6 (0-indexed) have body content below the decorative stacked chars,
so we include them but skip the decorative chars by size filter.

TABLE_PAGES: 79, 80, 81, 82 (0-indexed) contain financial tables which are rendered
with a special handler that produces clean tabular markdown.

INLINE ITALIC LABEL FIX: Some bullet items use an inline design pattern where italic
"keyword" text appears at the same visual y-position as the bullet but in a separate PDF
text run at a slightly different y0. The fix merges these into the adjacent body-text
y-bucket at the correct x-position.
"""

import pdfplumber
from collections import defaultdict
import re

PDF_PATH = '/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2015/green/manifesto.pdf'
OUT_PATH = '/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2015/green/manifesto.md'

# Column layout for two-column pages (Foreword, Policy on a page)
RIGHT_COL_START = 295  # right column starts at x0 >= 295

# Pages to skip entirely (0-indexed)
SKIP_PAGES = {0, 1, 2, 3, 4, 83}

# Pages with financial tables - handled separately
TABLE_PAGES = {79, 80, 81, 82}


def strip_prefix(fontname):
    if '+' in fontname:
        return fontname.split('+', 1)[1]
    return fontname


def is_leader_line(text):
    """Detect TOC leader dot lines."""
    s = text.strip()
    if len(s) < 4:
        return False
    dots = sum(1 for c in s if c in '.\u00b7\u2026')
    return dots / len(s) > 0.3


def classify(text, font, size, x0, y0):
    """
    Classify a line. Returns (type, cleaned_text) or None to skip.
    Types: h2, h3, body, bold_body, bullet, author
    """
    fn = font.lower()

    # Skip running footer
    if y0 < 30:
        return None

    # Skip footnote superscripts
    if size < 7:
        return None

    # Skip decorative stacked chars (BebasNeueBold 41pt+)
    if 'bebasneuebold' in fn and size >= 30:
        return None

    # Skip TOC entries: BebasNeueRegular 18pt (with leader dots)
    if 'bebasneue' not in fn or 'book' not in fn:
        if 'bebasneueregular' in fn and size >= 14 and is_leader_line(text):
            return None
    if 'bebasneueregular' in fn and size >= 18:
        return None

    # Skip TOC sub-entries: HelveticaNeueLTPro-LtCn
    if 'ltcn' in fn:
        return None

    # Skip leader dot lines
    if is_leader_line(text):
        return None

    # Clean text
    cleaned = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)
    cleaned = re.sub(r' {2,}', ' ', cleaned).strip()
    if not cleaned:
        return None

    # BebasNeueBook 40pt: chapter heading
    if 'bebasneue' in fn and 'book' in fn and size >= 35:
        return ('h2', cleaned)

    # BebasNeueBold 16pt: section heading
    if 'bebasneuebold' in fn and 14 <= size < 30:
        return ('h3', cleaned)

    # BebasNeueRegular 14pt: author attribution
    if 'bebasneueregular' in fn and 12 <= size < 18:
        return ('author', cleaned)

    # SymbolMT 10pt: bullet markers
    if 'symbolmt' in fn:
        # Strip the bullet char and tab, get the text part
        bullet_text = re.sub(r'^[•\t\s]+', '', cleaned).strip()
        if bullet_text:
            return ('bullet', bullet_text)
        else:
            return ('bullet_marker', '')

    # HelveticaNeueLTPro-BdCn: bold body
    if 'helveticaneultp' in fn and ('bdcn' in fn or 'bold' in fn.split('helveticaneultp')[-1]):
        return ('bold_body', cleaned)

    # HelveticaNeueLTPro-CnO or italic: italic body (treat as regular body)
    if 'helveticaneultp' in fn and ('cno' in fn or 'italic' in fn):
        return ('body', cleaned)

    # HelveticaNeueLTPro-Cn 12pt: lead-in body
    if 'helveticaneultp' in fn and 'cn' in fn and size >= 11:
        return ('body', cleaned)

    # HelveticaNeueLTPro-Cn 10pt: regular body
    if 'helveticaneultp' in fn and 'cn' in fn:
        return ('body', cleaned)

    # Continuation text indented under a bullet (x0 ~67-70)
    if 'helveticaneultp' in fn:
        return ('body', cleaned)

    return None


def is_two_col_line(all_chars):
    """Check if this y-bucket has chars in both left and right columns with a gap."""
    right_chars = [c for c in all_chars if c['x0'] >= RIGHT_COL_START]
    if not right_chars:
        return False
    left_chars = [c for c in all_chars if c['x0'] < RIGHT_COL_START]
    if not left_chars:
        return False
    max_x1_left = max(c['x1'] for c in left_chars)
    min_x0_right = min(c['x0'] for c in right_chars)
    gap = min_x0_right - max_x1_left
    return gap >= 8


def is_inline_label_bucket(all_chars):
    """
    Detect the 'inline italic label' pattern. Two sub-types:

    Type 1: A y-bucket with SymbolMT bullet marker + short italic text only
    (no regular Cn body text). The italic keyword belongs in an adjacent body line.

    Type 2: A y-bucket with ONLY italic/bold text (no bullet marker, no regular text).
    The italic keyword belongs inline within an adjacent bullet line.

    Returns True if this bucket matches either pattern.
    """
    non_footer = [c for c in all_chars if c['y0'] > 30]
    if not non_footer:
        return False

    has_symbol = any('SymbolMT' in c['fontname'] for c in non_footer)
    non_symbol_chars = [c for c in non_footer if 'SymbolMT' not in c['fontname']]

    if not non_symbol_chars:
        return False  # pure bullet marker only, not a label bucket

    all_italic_or_bold = all(
        'CnO' in c['fontname'] or 'BdCn' in c['fontname'] or 'bold' in c['fontname'].lower()
        for c in non_symbol_chars
    )

    if not all_italic_or_bold:
        return False

    # Check that the italic text is short (a keyword, not a full line)
    italic_text = ''.join(c['text'] for c in non_symbol_chars).strip()
    italic_text = italic_text.replace('\t', '').strip()

    if len(italic_text) >= 60:
        return False

    # Type 1: has bullet marker + short italic (the bullet marker will be transferred)
    # Type 2: no bullet marker, just short italic (will be merged into adjacent bullet)
    return True


def reconstruct_line_with_inline_labels(body_chars, label_chars_by_x):
    """
    Given body chars and a dict of {x_start: label_text} for inline labels,
    reconstruct the full line by inserting label text at the appropriate x positions.

    Returns the full reconstructed text string.
    """
    if not label_chars_by_x:
        return ''.join(c['text'] for c in sorted(body_chars, key=lambda c: c['x0']))

    # Build a combined list of (x0, text_fragment, is_label)
    fragments = []

    # Add body chars as individual chars
    for c in body_chars:
        fragments.append((c['x0'], c['text'], False))

    # Add label fragments
    for x_start, label_text in label_chars_by_x.items():
        fragments.append((x_start, label_text, True))

    # Sort by x0
    fragments.sort(key=lambda f: f[0])

    # Build text, inserting a space before labels if the previous char isn't whitespace
    result = []
    prev_x1 = None
    for x0, text, is_label in fragments:
        if prev_x1 is not None and x0 > prev_x1 + 3:
            # There's a gap - add a space if not already there
            if result and result[-1] != ' ':
                result.append(' ')
        result.append(text)
        prev_x1 = x0 + len(text) * 5  # approximate
    return ''.join(result).strip()


def merge_inline_labels(buckets):
    """
    Find inline label buckets and merge them into the adjacent body-text bucket.

    For each y-key that matches is_inline_label_bucket:
    1. Find the adjacent y-key (within +/-6) that has actual body text (no bullet marker)
    2. If found, remove the label bucket and augment the body bucket's chars
       by inserting the label chars (including any SymbolMT bullet marker) at their x positions

    The bullet marker from the label bucket is transferred to the body bucket so that
    the body line is correctly classified as a bullet item.

    Returns a new buckets dict with labels merged.
    """
    sorted_keys = sorted(buckets.keys(), reverse=True)
    label_buckets = {}  # y_key -> (all_label_chars, italic_text, has_symbol)
    body_y_keys = set()

    # First pass: identify label buckets and body buckets
    for y_key in sorted_keys:
        all_chars = sorted(buckets[y_key], key=lambda c: c['x0'])
        if is_inline_label_bucket(all_chars):
            non_symbol = [c for c in all_chars if 'SymbolMT' not in c['fontname']]
            italic_text = ''.join(c['text'] for c in non_symbol).strip().replace('\t', '').strip()
            if italic_text:
                has_symbol = any('SymbolMT' in c['fontname'] for c in all_chars)
                # For Type 1 (has_symbol=True): keep ALL chars including bullet marker
                # For Type 2 (has_symbol=False): keep only the italic chars
                label_buckets[y_key] = (all_chars, italic_text, has_symbol)
        else:
            body_y_keys.add(y_key)

    if not label_buckets:
        return buckets

    new_buckets = dict(buckets)

    for label_y, (label_chars, italic_text, has_symbol) in label_buckets.items():
        # Find the nearest body y-key within tolerance of 6
        best_body_y = None
        best_dist = 999
        for body_y in body_y_keys:
            dist = abs(body_y - label_y)
            if dist <= 6 and dist < best_dist:
                best_dist = dist
                best_body_y = body_y

        if best_body_y is not None:
            # Type 1 (has_symbol=True): merge ALL chars including SymbolMT bullet marker.
            #   The bullet marker in the label bucket becomes the bullet marker for the body line.
            # Type 2 (has_symbol=False): only merge italic chars into adjacent BULLET lines.
            #   Check that the target bucket has a SymbolMT marker (it's a bullet).
            if has_symbol:
                # Transfer all chars (including SymbolMT) to body bucket
                merged = list(new_buckets[best_body_y]) + label_chars
                new_buckets[best_body_y] = merged
                del new_buckets[label_y]
            else:
                # For Type 2: only merge if the adjacent bucket is a bullet (has SymbolMT)
                target_chars = new_buckets[best_body_y]
                target_has_bullet = any('SymbolMT' in c['fontname'] for c in target_chars)
                if target_has_bullet:
                    italic_chars = [c for c in label_chars if 'SymbolMT' not in c['fontname']]
                    merged = list(target_chars) + italic_chars
                    new_buckets[best_body_y] = merged
                    del new_buckets[label_y]
                # Otherwise leave the label bucket as-is
        # If no adjacent body found, leave the label bucket as-is (will be handled normally)

    return new_buckets


def extract_table_columns_by_x(all_chars):
    """
    Extract table column values using x-position ranges.
    The 5 data columns (years 2015-2019) are at fixed x ranges:
      col0: x ~ 330-372  (2015)
      col1: x ~ 374-416  (2016)
      col2: x ~ 418-462  (2017)
      col3: x ~ 462-506  (2018)
      col4: x ~ 502-548  (2019)  -- slightly overlapping to capture wider percentage values

    Returns a tuple (row_label, [col0, col1, col2, col3, col4]) or None if not a data row.
    """
    COL_RANGES = [
        (330, 374),   # 2015
        (374, 418),   # 2016
        (418, 462),   # 2017
        (460, 503),   # 2018 - end before 504 to avoid capturing 2019 chars
        (503, 548),   # 2019
    ]

    # Skip footer chars
    non_footer = [c for c in all_chars if c['y0'] > 30]

    # Split chars into label chars and column chars
    label_chars = [c for c in non_footer if c['x0'] < 330 and 'SymbolMT' not in c['fontname']]
    if not label_chars:
        return None

    # Build each column's text
    cols = []
    for x_start, x_end in COL_RANGES:
        col_chars = sorted([c for c in non_footer if x_start <= c['x0'] < x_end], key=lambda c: c['x0'])
        col_text = ''.join(c['text'] for c in col_chars).strip()
        cols.append(col_text)

    # Check that at least 3 of the 5 columns have numeric content
    # (this is the strict check that filters out body text paragraphs)
    numeric_cols = sum(1 for col in cols if re.search(r'\d', col))
    if numeric_cols < 3:
        return None

    # Additional check: columns must start with a digit, minus, or decimal
    cols_starting_numeric = sum(1 for col in cols if col and col[0] in '0123456789−-')
    if cols_starting_numeric < 2:
        return None

    # Build row label text
    label_chars_sorted = sorted(label_chars, key=lambda c: c['x0'])
    row_label = ''.join(c['text'] for c in label_chars_sorted).strip()
    row_label = re.sub(r' {2,}', ' ', row_label).strip()

    return (row_label, cols)


def process_table_page(page):
    """
    Process pages 79-82 which contain financial tables.
    Extracts the table data and formats it as markdown tables using x-position-based
    column extraction to correctly split the 5 year columns.
    """
    chars = page.chars
    if not chars:
        return []

    buckets = defaultdict(list)
    for ch in chars:
        y_key = round(ch['y0'] / 2) * 2
        buckets[y_key].append(ch)

    entries = []
    in_table = False  # Track if we're inside a table

    for y_key in sorted(buckets.keys(), reverse=True):
        all_chars = sorted(buckets[y_key], key=lambda c: c['x0'])
        if not all_chars:
            continue

        # Skip footer
        if all_chars[0]['y0'] < 30:
            continue

        text = ''.join(c['text'] for c in all_chars).strip()
        if not text:
            continue

        font = strip_prefix(all_chars[0]['fontname'])
        size = all_chars[0]['size']
        x0 = all_chars[0]['x0']
        fn = font.lower()

        # Skip decorative stacked chars
        if 'bebasneuebold' in fn and size >= 30:
            continue

        # Skip footnote superscripts
        if size < 7:
            continue

        # Clean text
        cleaned = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)
        cleaned = re.sub(r' {2,}', ' ', cleaned).strip()
        if not cleaned:
            continue

        # Detect the table header row (contains year columns like 2015 2016 ...)
        if re.search(r'20\d\d.*20\d\d', cleaned):
            # Table header row - extract title and year columns
            match = re.search(r'^(.*?)(\d{4}(?:\s*\d{4})+)\s*$', cleaned)
            if match:
                title = match.group(1).strip()
                years_raw = match.group(2).strip()
                years = re.findall(r'\d{4}', years_raw)
                if title:
                    entries.append(('body', title))
                entries.append(('table_row', '| Item | ' + ' | '.join(years) + ' |'))
                entries.append(('table_row', '| --- | ' + ' | '.join(['---'] * len(years)) + ' |'))
                in_table = True
            else:
                entries.append(('body', cleaned))
            continue

        # Try x-position-based column extraction for data rows
        col_result = extract_table_columns_by_x(all_chars)
        if col_result is not None:
            row_label, cols = col_result
            if row_label:
                col_str = ' | '.join(col if col else '' for col in cols)
                entries.append(('table_row', f'| {row_label} | {col_str} |'))
            else:
                # Section subheading row (no label, just a category name on the left)
                label_chars = [c for c in all_chars if c['x0'] < 330]
                label_text = ''.join(c['text'] for c in sorted(label_chars, key=lambda c: c['x0'])).strip()
                if label_text:
                    entries.append(('bold_body', label_text))
            continue

        # Section subheadings within the table (bold, no number columns)
        if 'bdcn' in fn or ('helveticaneultp' in fn and 'bd' in fn):
            if len(cleaned) < 80:
                in_table = False
                entries.append(('bold_body', cleaned))
                continue

        if 'bebasneue' in fn and 'book' in fn and size >= 35:
            in_table = False
            entries.append(('h2', cleaned))
            continue

        if 'bebasneuebold' in fn and 14 <= size < 30:
            in_table = False
            entries.append(('h3', cleaned))
            continue

        # Regular body text (headings, explanatory paragraphs)
        if 'bebasneue' in fn:
            in_table = False
            entries.append(('h3', cleaned))
        elif 'helveticaneultp' in fn:
            # Check if this looks like a section category label in a table
            # (short text, no numbers, indented slightly)
            if in_table and x0 < 100 and not re.search(r'\d', cleaned) and len(cleaned) < 50:
                entries.append(('bold_body', cleaned))
            else:
                entries.append(('body', cleaned))
        else:
            entries.append(('body', cleaned))

    return entries


def process_page(page, page_idx=None):
    """
    Extract lines from page. Returns list of (type, text) tuples in reading order.
    Handles two-column layout for pages where it occurs.
    Handles inline italic label merging.
    """
    # Delegate table pages to special handler
    if page_idx in TABLE_PAGES:
        return process_table_page(page)

    chars = page.chars
    if not chars:
        return []

    # Group chars into y-buckets
    raw_buckets = defaultdict(list)
    for ch in chars:
        y_key = round(ch['y0'] / 2) * 2
        raw_buckets[y_key].append(ch)

    # Merge inline italic labels into adjacent body-text lines
    buckets = merge_inline_labels(raw_buckets)

    left_lines = []   # (y_key, text, font, size, x0)
    right_lines = []  # (y_key, text, font, size, x0)
    single_lines = []  # (y_key, text, font, size, x0)

    has_two_col = False

    for y_key in sorted(buckets.keys(), reverse=True):
        all_chars = sorted(buckets[y_key], key=lambda c: c['x0'])
        if not all_chars:
            continue

        font = strip_prefix(all_chars[0]['fontname'])
        size = all_chars[0]['size']
        x0 = all_chars[0]['x0']

        if is_two_col_line(all_chars):
            has_two_col = True
            left_chars = [c for c in all_chars if c['x0'] < RIGHT_COL_START]
            right_chars = [c for c in all_chars if c['x0'] >= RIGHT_COL_START]

            if left_chars:
                lc_sorted = sorted(left_chars, key=lambda c: c['x0'])
                text = ''.join(c['text'] for c in lc_sorted).strip()
                if text:
                    lf = strip_prefix(lc_sorted[0]['fontname'])
                    ls = lc_sorted[0]['size']
                    lx = lc_sorted[0]['x0']
                    left_lines.append((y_key, text, lf, ls, lx))

            if right_chars:
                rc_sorted = sorted(right_chars, key=lambda c: c['x0'])
                text = ''.join(c['text'] for c in rc_sorted).strip()
                if text:
                    rf = strip_prefix(rc_sorted[0]['fontname'])
                    rs = rc_sorted[0]['size']
                    rx = rc_sorted[0]['x0']
                    right_lines.append((y_key, text, rf, rs, rx))
        else:
            text = ''.join(c['text'] for c in all_chars).strip()
            if text:
                single_lines.append((y_key, text, font, size, x0))

    if has_two_col:
        # Sort each column top-to-bottom (descending y_key = top to bottom)
        left_lines.sort(key=lambda e: -e[0])
        right_lines.sort(key=lambda e: -e[0])
        # Single lines: some are chapter headings that appear above both columns
        single_lines.sort(key=lambda e: -e[0])

        # Find the y range of two-col content
        if left_lines and right_lines:
            two_col_max_y = max(left_lines[0][0], right_lines[0][0])
            two_col_min_y = min(left_lines[-1][0], right_lines[-1][0])
        elif left_lines:
            two_col_max_y = left_lines[0][0]
            two_col_min_y = left_lines[-1][0]
        elif right_lines:
            two_col_max_y = right_lines[0][0]
            two_col_min_y = right_lines[-1][0]
        else:
            two_col_max_y = 0
            two_col_min_y = 0

        above_singles = [(y, t, f, s, x) for y, t, f, s, x in single_lines if y > two_col_max_y]
        below_singles = [(y, t, f, s, x) for y, t, f, s, x in single_lines if y <= two_col_min_y]
        mid_singles = [(y, t, f, s, x) for y, t, f, s, x in single_lines
                       if two_col_min_y < y <= two_col_max_y]

        # Mid singles: assign to left or right based on x0
        for entry in mid_singles:
            y, t, f, s, x = entry
            if x >= RIGHT_COL_START:
                right_lines.append(entry)
            else:
                left_lines.append(entry)
        left_lines.sort(key=lambda e: -e[0])
        right_lines.sort(key=lambda e: -e[0])

        # Build classified entries
        all_entries = []

        # Above singles
        for y, text, font, size, x0 in above_singles:
            r = classify(text, font, size, x0, y)
            if r:
                all_entries.append(r)

        # Left column
        left_cl = []
        for y, text, font, size, x0 in left_lines:
            r = classify(text, font, size, x0, y)
            if r:
                left_cl.append(r)

        # Right column
        right_cl = []
        for y, text, font, size, x0 in right_lines:
            r = classify(text, font, size, x0, y)
            if r:
                right_cl.append(r)

        if left_cl:
            all_entries.extend(left_cl)
        if right_cl:
            all_entries.append(('col_break', ''))
            all_entries.extend(right_cl)

        # Below singles
        for y, text, font, size, x0 in below_singles:
            r = classify(text, font, size, x0, y)
            if r:
                all_entries.append(r)

        return all_entries
    else:
        # Single-column page
        single_lines.sort(key=lambda e: -e[0])
        entries = []
        for y, text, font, size, x0 in single_lines:
            r = classify(text, font, size, x0, y)
            if r:
                entries.append(r)
        return entries


def entries_to_markdown(entries):
    """Convert classified entries to markdown lines."""
    md = []
    prev_type = None
    bullet_buffer = []
    h2_buffer = []  # Accumulate multi-line chapter headings

    def flush_bullets():
        nonlocal bullet_buffer
        if not bullet_buffer:
            return
        # Merge continuation lines (lines starting lowercase are continuations)
        merged = []
        cur = None
        for bt, bold in bullet_buffer:
            if cur is None:
                cur = (bt, bold)
            elif bt and (bt[0].islower() or bt[0] in '£0123456789–-—('):
                cur = (cur[0] + ' ' + bt, cur[1])
            else:
                merged.append(cur)
                cur = (bt, bold)
        if cur:
            merged.append(cur)
        for bt, bold in merged:
            if not bt:
                continue  # skip empty bullets
            if bold:
                md.append(f'* **{bt}**')
            else:
                md.append(f'* {bt}')
        bullet_buffer.clear()

    def flush_h2():
        nonlocal h2_buffer
        if not h2_buffer:
            return
        text = ' '.join(h2_buffer)
        if md and md[-1] != '':
            md.append('')
        md.append(f'## {text}')
        md.append('')
        h2_buffer.clear()

    for item_type, text in entries:
        if item_type == 'h2':
            flush_bullets()
            # Chapter headings come in 3 lines: number, title line1, title line2
            # Accumulate and flush on non-h2
            h2_buffer.append(text)
            prev_type = 'h2'
            continue

        if h2_buffer and item_type != 'h2':
            flush_h2()

        if item_type == 'h3':
            flush_bullets()
            if md and md[-1] != '':
                md.append('')
            md.append(f'### {text}')
            md.append('')
            prev_type = 'h3'

        elif item_type == 'author':
            flush_bullets()
            if md and md[-1] != '':
                md.append('')
            md.append(f'*{text}*')
            md.append('')
            prev_type = 'author'

        elif item_type == 'bullet':
            bullet_buffer.append((text, False))
            prev_type = 'bullet'

        elif item_type == 'bullet_marker':
            # A bullet marker with no text on this line - next line is the text
            bullet_buffer.append(('', False))
            prev_type = 'bullet_marker'

        elif item_type == 'bold_body':
            # If we have a pending empty bullet, this text is the bullet content
            if bullet_buffer and bullet_buffer[-1][0] == '':
                bullet_buffer[-1] = (text, True)
                prev_type = 'bullet'
            else:
                flush_bullets()
                if prev_type == 'body' or prev_type == 'bold_body':
                    md[-1] = md[-1] + ' ' + text
                else:
                    if md and md[-1] != '':
                        md.append('')
                    md.append(f'**{text}**')
                prev_type = 'bold_body'

        elif item_type == 'col_break':
            flush_bullets()
            prev_type = 'col_break'

        elif item_type == 'table_row':
            flush_bullets()
            # Table rows always go on their own line - never merged with previous
            md.append(text)
            prev_type = 'table_row'

        elif item_type == 'body':
            # If we have a pending empty bullet, this text is the bullet content
            if bullet_buffer and bullet_buffer[-1][0] == '':
                bullet_buffer[-1] = (text, False)
                prev_type = 'bullet'
            elif bullet_buffer and prev_type == 'bullet' and text and (
                    text[0].islower() or text[0] in '£0123456789–-—(|'):
                # Continuation of last bullet (starts lowercase or is a table row)
                last_bt, last_bold = bullet_buffer[-1]
                bullet_buffer[-1] = (last_bt + ' ' + text if last_bt else text, last_bold)
                prev_type = 'bullet'
            else:
                flush_bullets()
                if prev_type == 'body':
                    md[-1] = md[-1] + ' ' + text
                else:
                    if md and md[-1] != '':
                        md.append('')
                    md.append(text)
                prev_type = 'body'

    flush_h2()
    flush_bullets()
    return md


def main():
    output = ['# Green Party Manifesto 2015', '']

    with pdfplumber.open(PDF_PATH) as pdf:
        total = len(pdf.pages)
        print(f'Processing {total} pages...')

        for idx in range(total):
            if idx in SKIP_PAGES:
                print(f'  Skipping page {idx+1}')
                continue

            page = pdf.pages[idx]
            if not page.chars:
                print(f'  Page {idx+1}: image-only')
                continue

            print(f'  Processing page {idx+1}...')
            entries = process_page(page, page_idx=idx)

            if not entries:
                continue

            page_md = entries_to_markdown(entries)
            output.extend(page_md)

    # Cleanup: collapse multiple blank lines
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

    print(f'\nDone! Written to {OUT_PATH}')
    print(f'Total lines: {len(cleaned)}')


if __name__ == '__main__':
    main()
