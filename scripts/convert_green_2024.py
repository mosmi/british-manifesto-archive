#!/usr/bin/env python3
"""
Convert Green Party 2024 manifesto PDF to clean markdown.

Layout (per spread page, width=1190):
  LEFT half (x=0-600): two side-by-side columns LA and LB
    LA: x=0-300
    LB: x=300-600
  RIGHT half (x=600-1200): two side-by-side columns RA and RB
    RA: x=600-900
    RB: x=900-1200

Reading order: LA → LB → RA → RB (each column top-to-bottom independently)

SPECIAL: Chapter headings (size 36) span across LA+LB or RA+RB.
         They must be assembled by combining chars from both columns at same y.

Font sizes:
  60  = Large decorative → SKIP
  36  = Chapter heading → ##
  27  = Decorative → SKIP
  17  = Watermark → SKIP
  16  = Section heading → ###
  13  = Bullet markers (•) or running footer → handle carefully
  12  = Contents entries (page 2 only)
  11  = Body text or page numbers (skip if top > 800)
  10  = Body text
  9   = Body text (small)
  8   = Legal disclaimer
  6   = Tiny decorative → SKIP

Contents page (page 2) has size-12 entries like:
  'Building a Fairer, Healthier Country2' (chapter name + page number embedded)
  These span x=718-1090 (crosses RA-RB boundary). Strip trailing digits.
"""

import pdfplumber
from collections import defaultdict
import re

PDF_PATH = '/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2024/green/manifesto.pdf'
OUT_PATH = '/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2024/green/manifesto.md'

FOOTER_TOP = 800  # y above this is footer/page number area

# Column boundaries (x_min, x_max)
# Note: Some chars appear at x=899.9975 (just below 900) but belong to RB column.
# Use x=895 as the RA/RB split to correctly place these boundary chars in RB.
COL_LA = (0, 300)
COL_LB = (300, 600)
COL_RA = (600, 895)
COL_RB = (895, 1200)

# Sizes to skip completely
NOISE_SIZES = {6, 17, 27, 60}


def is_noise(c):
    sz = round(c['size'])
    return sz in NOISE_SIZES or sz < 6 or c['top'] >= FOOTER_TOP


def group_by_top(chars, y_tol=3):
    """Group chars into lines, return sorted list of (bucket, [chars sorted by x0])."""
    buckets = defaultdict(list)
    for c in chars:
        b = round(c['top'] / y_tol) * y_tol
        buckets[b].append(c)
    return [(b, sorted(cs, key=lambda c: c['x0'])) for b, cs in sorted(buckets.items())]


def dominant_size(chars_list):
    sizes = [round(c['size']) for c in chars_list]
    return max(set(sizes), key=sizes.count)


def chars_text(chars_list):
    return ''.join(c['text'] for c in chars_list)


def clean(text):
    text = text.replace('\xa0', ' ')
    text = re.sub(r'  +', ' ', text)
    return text.strip()


def strip_trailing_pagenum(text):
    """Remove trailing page number like 'Country2' -> 'Country'."""
    return re.sub(r'\d+$', '', text).strip()


def build_word_index(page, x_min, x_max):
    """
    Build a dict mapping approx-top-bucket -> word-line-text for a column.
    Uses extract_words for proper spacing.
    """
    all_words = page.extract_words(keep_blank_chars=False, x_tolerance=3, y_tolerance=3)
    col_words = [w for w in all_words if x_min <= w['x0'] < x_max and w['top'] < FOOTER_TOP]
    buckets = defaultdict(list)
    for w in col_words:
        b = round(w['top'] / 4) * 4
        buckets[b].append(w)
    result = {}
    for b, wlist in buckets.items():
        wlist.sort(key=lambda w: w['x0'])
        result[b] = ' '.join(w['text'] for w in wlist)
    return result


def get_word_text(word_index, char_top, fallback):
    """Find word text closest to char_top bucket.
    When two buckets are equally close, prefer the one with more content (longer text).
    """
    best_text = fallback
    best_diff = 999
    for wb, wtext in word_index.items():
        diff = abs(wb - char_top)
        if diff > 8:
            continue
        # Prefer closer bucket; on tie, prefer longer/more-content text
        if diff < best_diff or (diff == best_diff and len(wtext) > len(best_text)):
            best_diff = diff
            best_text = wtext
    return best_text


def extract_chapter_headings(page):
    """
    Extract chapter headings (size 36) which span across a full half (LA+LB or RA+RB).
    Returns dict: approx_top -> heading_text for each side (left or right).
    """
    chars = page.chars
    s36 = [c for c in chars if round(c['size']) == 36 and c['top'] < FOOTER_TOP]
    if not s36:
        return {}

    # Group by top (within 5pt) across all x positions
    buckets = defaultdict(list)
    for c in s36:
        b = round(c['top'] / 5) * 5
        buckets[b].append(c)

    headings = {}
    # Collect consecutive top buckets that belong to same heading (within 50pt)
    sorted_tops = sorted(buckets.keys())
    i = 0
    while i < len(sorted_tops):
        # Collect all parts of this heading (can span 2-3 lines)
        heading_chars = list(buckets[sorted_tops[i]])
        j = i + 1
        while j < len(sorted_tops) and (sorted_tops[j] - sorted_tops[j-1]) <= 50:
            heading_chars.extend(buckets[sorted_tops[j]])
            j += 1

        # Determine which side (left or right)
        avg_x = sum(c['x0'] for c in heading_chars) / len(heading_chars)
        side = 'left' if avg_x < 600 else 'right'

        # Build text line by line, sorted by top then x
        line_buckets = defaultdict(list)
        for c in heading_chars:
            b = round(c['top'] / 3) * 3
            line_buckets[b].append(c)

        text_parts = []
        for tb in sorted(line_buckets.keys()):
            lc = sorted(line_buckets[tb], key=lambda c: c['x0'])
            text_parts.append(chars_text(lc).strip())

        full_text = ' '.join(p for p in text_parts if p).strip()
        # Use the min top of this heading group as key
        min_top = sorted_tops[i]
        headings[min_top] = (side, full_text)
        i = j

    return headings


def process_column(page, col_x_min, col_x_max, chapter_headings_set, word_index, all_page_words=None):
    """
    Extract all content blocks from a single column.
    Returns list of dicts: {top, size, text, block_type}
    block_type: 'chapter', 'section', 'body', 'skip'
    all_page_words: pre-extracted list from page.extract_words(), optional cache
    """
    chars = page.chars
    col_chars = [c for c in chars
                 if col_x_min <= c['x0'] < col_x_max and not is_noise(c)]

    # Group into lines
    lines = group_by_top(col_chars, y_tol=3)

    blocks = []
    for top_b, lc in lines:
        if not lc:
            continue
        sz = dominant_size(lc)
        char_txt = chars_text(lc).strip()

        if not char_txt:
            continue

        # Skip size-36 (chapter headings) - handled separately
        if sz == 36:
            continue

        # Handle size-13 bare bullet markers
        # (inline bullets where dominant_size=13 rarely occur since the text portion is size 10)
        if sz == 13:
            stripped13 = char_txt.strip()
            if stripped13 in ('•', '• ', ' •'):
                # Bare bullet marker preceding body text
                blocks.append({'top': top_b, 'size': sz, 'text': '•', 'block_type': 'bullet_marker'})
            # If it's a non-bullet size-13 line (running headers etc), skip it
            # Note: inline bullet lines have dominant_size=10 (most chars), handled below
            continue

        # Detect lines that contain an inline bullet marker at the start.
        # The '•' is a size-13 char but most text on this line is size-10,
        # so dominant_size=10. Check char_txt for leading '•'.
        stripped_char = char_txt.strip()
        if stripped_char.startswith('•'):
            # Inline bullet line: assemble word text from extract_words (excludes '•' word)
            if all_page_words is None:
                all_page_words = page.extract_words(keep_blank_chars=False, x_tolerance=3, y_tolerance=3)
            line_words = [w for w in all_page_words
                          if col_x_min <= w['x0'] < col_x_max
                          and abs(w['top'] - top_b) <= 12
                          and w['text'] != '•']
            if line_words:
                line_words.sort(key=lambda w: w['x0'])
                word_txt = '• ' + ' '.join(w['text'] for w in line_words)
            else:
                word_txt = stripped_char  # fallback to char text
            word_txt = clean(word_txt)
            if word_txt:
                blocks.append({'top': top_b, 'size': sz, 'text': word_txt, 'block_type': 'body'})
            continue

        # Classify
        if sz == 16:
            btype = 'section'
        elif sz in (8, 9, 10, 11, 12):
            btype = 'body'
        else:
            btype = 'skip'

        if btype == 'skip':
            continue

        # Get word-level text for better spacing
        word_txt = clean(get_word_text(word_index, top_b, char_txt))
        if not word_txt:
            continue

        blocks.append({'top': top_b, 'size': sz, 'text': word_txt, 'block_type': btype})

    return blocks


def blocks_to_md(blocks):
    """
    Convert a list of blocks to markdown lines.
    Handles section heading multi-line merging, body text continuation, and bullets.
    """
    md = []
    prev_size = None
    prev_top = None
    prev_btype = None
    pending_bullet = False

    i = 0
    while i < len(blocks):
        b = blocks[i]
        btype = b['block_type']
        text = b['text']
        sz = b['size']
        top = b['top']

        if btype == 'section':
            # Collect multi-line section heading
            parts = [text.strip()]
            j = i + 1
            while j < len(blocks):
                nb = blocks[j]
                if nb['block_type'] == 'section' and (nb['top'] - blocks[j-1]['top']) <= 30:
                    parts.append(nb['text'].strip())
                    j += 1
                else:
                    break
            heading = ' '.join(p for p in parts if p).strip()
            # Remove any trailing/extra whitespace
            heading = re.sub(r'  +', ' ', heading).strip()
            md.append('')
            md.append(f'### {heading}')
            md.append('')
            prev_btype = 'section'
            prev_size = sz
            prev_top = top
            pending_bullet = False
            i = j
            continue

        elif btype == 'bullet_marker':
            pending_bullet = True
            i += 1
            continue

        elif btype == 'body':
            stripped_text = text.strip()
            # Only bold "Elected Greens will..." lines when they end with ':'
            # (i.e., they introduce a bullet list, not body text that happens to start with this phrase)
            if re.match(r'^Elected Greens will\b', stripped_text) and stripped_text.endswith(':'):
                if md and md[-1] != '':
                    md.append('')
                md.append(f'**{stripped_text}**')
                md.append('')
                pending_bullet = False
            elif stripped_text.startswith('•'):
                bullet_text = text.strip()[1:].strip()
                if bullet_text:
                    md.append(f'*   {bullet_text}')
                pending_bullet = False
            elif pending_bullet:
                md.append(f'*   {text.strip()}')
                pending_bullet = False
            else:
                # Regular body text
                # Lines within a paragraph: ~15pt apart
                # Between paragraphs: ~21pt
                # Between bullet items: ~18pt
                # Threshold <= 19 merges 15pt/18pt line wraps, breaks at 21pt
                gap = top - prev_top if prev_top is not None else 999

                # Can we append to the previous line?
                # For bullet items: only append if gap <= 15 (tight line wrap)
                # For body paragraphs: append if gap <= 19
                prev_is_bullet = md and md[-1].startswith('*   ')
                prev_is_heading = md and (md[-1].startswith('#') or md[-1].startswith('**'))

                if prev_is_bullet and gap <= 15 and md and md[-1] != '':
                    # Continuation of a bullet item line wrap
                    last = md[-1]
                    if last.endswith('-'):
                        # Keep hyphen (compound words and prefixes like re-establish)
                        md[-1] = last + text.strip()
                    else:
                        md[-1] = last + ' ' + text.strip()
                elif (prev_btype == 'body'
                      and prev_top is not None
                      and gap <= 19
                      and md
                      and md[-1]
                      and not prev_is_bullet
                      and not prev_is_heading
                      and md[-1] != ''):
                    # Continuation of body paragraph
                    last = md[-1]
                    if last.endswith('-'):
                        # Keep hyphen (compound words and prefixes)
                        md[-1] = last + text.strip()
                    else:
                        md[-1] = last + ' ' + text.strip()
                else:
                    # New paragraph: add blank line if previous was body or bullet
                    if prev_btype == 'body' and md and md[-1] != '':
                        md.append('')
                    md.append(text.strip())

            prev_btype = 'body'
            prev_size = sz
            prev_top = top

        i += 1

    return md


def process_contents_page(page):
    """Special handling for the contents page (page 2)."""
    md = []
    md.append('')
    md.append('## Contents')
    md.append('')

    chars = page.chars
    # Contents entries are size 12, spanning x=718-1090
    s12 = sorted([c for c in chars if round(c['size']) == 12 and c['top'] < FOOTER_TOP],
                 key=lambda c: (c['top'], c['x0']))

    lines = group_by_top(s12, y_tol=5)
    for top_b, lc in lines:
        text = chars_text(lc).strip()
        # Remove trailing page number
        text = strip_trailing_pagenum(text)
        text = clean(text)
        if text:
            md.append(f'*   {text}')

    # Add small print from size 8/9 (disclaimer)
    s89 = sorted([c for c in chars if round(c['size']) in (8, 9) and c['top'] < FOOTER_TOP],
                 key=lambda c: (c['top'], c['x0']))
    if s89:
        md.append('')
        lines89 = group_by_top(s89, y_tol=5)
        disclaimer_parts = []
        for top_b, lc in lines89:
            text = chars_text(lc).strip()
            if text:
                disclaimer_parts.append(text)
        if disclaimer_parts:
            md.append('*Note: ' + ' '.join(disclaimer_parts) + '*')

    return md


def process_foreword_page(page):
    """Special handling for the foreword page (page 1)."""
    md = []

    chars = page.chars

    # Build word index for the right side (all columns)
    word_index_ra = build_word_index(page, COL_RA[0], COL_RA[1])
    word_index_rb = build_word_index(page, COL_RB[0], COL_RB[1])

    # The title (size 16) - spans across RA+RB (x=671-1100)
    # Assemble from all chars at this size, sorted by top then x
    s16 = sorted([c for c in chars if round(c['size']) == 16 and c['top'] < FOOTER_TOP
                  and c['x0'] >= 600],  # only right half
                 key=lambda c: (c['top'], c['x0']))
    if s16:
        # Combine all s16 chars across the full width into lines
        lines16 = group_by_top(s16, y_tol=5)
        title_parts = []
        for top_b, lc in lines16:
            # Use word-level text for this line across full width
            w = page.extract_words(keep_blank_chars=False, x_tolerance=3, y_tolerance=3)
            wline = [word for word in w if abs(word['top'] - top_b) <= 8
                     and word['x0'] >= 600 and word['x0'] < 1200]
            if wline:
                wline.sort(key=lambda word: word['x0'])
                text = ' '.join(word['text'] for word in wline)
            else:
                text = chars_text(lc)
            text = clean(text)
            if text:
                title_parts.append(text)
        if title_parts:
            md.append('')
            md.append(f'### {" ".join(title_parts)}')
            md.append('')

    # Process RA column body text (size 10, 11)
    for col_x_min, col_x_max, word_idx in [
            (COL_RA[0], COL_RA[1], word_index_ra),
            (COL_RB[0], COL_RB[1], word_index_rb)]:
        col_chars = sorted([c for c in chars
                            if col_x_min <= c['x0'] < col_x_max
                            and c['top'] < FOOTER_TOP
                            and round(c['size']) in (10, 11)
                            and not is_noise(c)],
                           key=lambda c: c['top'])

        lines_body = group_by_top(col_chars, y_tol=3)
        col_blocks = []
        for top_b, lc in lines_body:
            if not lc:
                continue
            word_txt = clean(get_word_text(word_idx, top_b, chars_text(lc)))
            if word_txt:
                col_blocks.append({'top': top_b, 'size': 10, 'text': word_txt, 'block_type': 'body'})

        col_md = blocks_to_md(col_blocks)
        md.extend(col_md)
        if md and md[-1] != '':
            md.append('')

    # Add the signature/attribution
    s13 = sorted([c for c in chars if round(c['size']) == 13 and c['top'] < FOOTER_TOP],
                 key=lambda c: (c['top'], c['x0']))
    if s13:
        lines13 = group_by_top(s13, y_tol=5)
        for top_b, lc in lines13:
            text = chars_text(lc).strip()
            if text and text not in ('•', '• '):
                md.append(f'*{text}*')

    return md


def process_spread_page(page, page_idx):
    """Process a double-spread page."""
    page_width = page.width
    md = []

    chars = page.chars

    # Extract chapter headings (size 36) - these span full halves
    chapter_headings = extract_chapter_headings(page)

    # Emit chapter headings in the correct reading order:
    # Left half headings before right half content, right half headings before right content
    left_headings = {top: (side, text) for top, (side, text) in chapter_headings.items() if side == 'left'}
    right_headings = {top: (side, text) for top, (side, text) in chapter_headings.items() if side == 'right'}

    # Build word indices for all columns using defined boundaries
    la_x1, lb_x0, lb_x1, ra_x0, ra_x1, rb_x0, rb_x1 = (
        COL_LA[1], COL_LB[0], COL_LB[1], COL_RA[0], COL_RA[1], COL_RB[0], COL_RB[1]
    )
    word_indices = {
        'LA': build_word_index(page, COL_LA[0], COL_LA[1]),
        'LB': build_word_index(page, COL_LB[0], COL_LB[1]),
        'RA': build_word_index(page, COL_RA[0], COL_RA[1]),
        'RB': build_word_index(page, COL_RB[0], COL_RB[1]),
    }

    # Cache extract_words for inline bullet text assembly
    all_page_words = page.extract_words(keep_blank_chars=False, x_tolerance=3, y_tolerance=3)

    # Process LEFT half (LA + LB)
    if left_headings:
        for top, (side, heading_text) in sorted(left_headings.items()):
            md.append('')
            md.append(f'## {heading_text}')
            md.append('')

    la_blocks = process_column(page, COL_LA[0], COL_LA[1], chapter_headings, word_indices['LA'], all_page_words)
    lb_blocks = process_column(page, COL_LB[0], COL_LB[1], chapter_headings, word_indices['LB'], all_page_words)

    left_md = blocks_to_md(la_blocks)
    md.extend(left_md)
    if md and md[-1] != '':
        md.append('')

    left_md_lb = blocks_to_md(lb_blocks)
    md.extend(left_md_lb)
    if md and md[-1] != '':
        md.append('')

    # Process RIGHT half (RA + RB)
    if right_headings:
        for top, (side, heading_text) in sorted(right_headings.items()):
            md.append('')
            md.append(f'## {heading_text}')
            md.append('')

    ra_blocks = process_column(page, COL_RA[0], COL_RA[1], chapter_headings, word_indices['RA'], all_page_words)
    rb_blocks = process_column(page, COL_RB[0], COL_RB[1], chapter_headings, word_indices['RB'], all_page_words)

    right_md = blocks_to_md(ra_blocks)
    md.extend(right_md)
    if md and md[-1] != '':
        md.append('')

    right_md_rb = blocks_to_md(rb_blocks)
    md.extend(right_md_rb)

    return md


def post_process(lines):
    """Clean up the output."""
    def has_doubled(line):
        """
        Detect watermark lines like 'RReeaall HHooppee..' where every char is doubled.
        Normal English has occasional doubled chars (ss, ll, ee) but not most chars doubled.
        """
        no_space = line.replace(' ', '').replace('.', '').replace(',', '')
        if len(no_space) < 6:
            return False
        # Count doubled pairs
        doubles = sum(1 for i in range(0, len(no_space) - 1, 2)
                      if i + 1 < len(no_space) and no_space[i] == no_space[i + 1])
        # Watermark has MOST chars doubled (ratio >= 0.7 of total pairs)
        total_pairs = len(no_space) // 2
        if total_pairs == 0:
            return False
        ratio = doubles / total_pairs
        return ratio >= 0.6 and doubles >= 3

    def is_page_num(line):
        stripped = line.strip()
        # Standalone digits (page numbers that leaked through)
        if re.match(r'^\d{1,4}$', stripped):
            return True
        # Fragments like 'and Dignity 5', 'for All 7' (table of contents fragments)
        if re.match(r'^(and Dignity|for All|Deal|Public Finances|System|for All|World)\s+\d+$', stripped):
            return True
        return False

    cleaned = []
    prev_blank = False
    for line in lines:
        if has_doubled(line):
            continue
        if is_page_num(line):
            continue
        if line == '':
            if not prev_blank:
                cleaned.append('')
            prev_blank = True
        else:
            cleaned.append(line)
            prev_blank = False

    # Merge cross-column sentence fragments:
    # If a line ends without terminal punctuation and is followed by
    # a blank line and then a continuation line starting with a lowercase letter,
    # merge the continuation onto the preceding line.
    # This handles both body paragraphs and bullet items that split across columns.
    TERMINAL_PUNCT = set('.!?:')
    merged = []
    i = 0
    while i < len(cleaned):
        line = cleaned[i]
        # Check if this is a mergeable fragment:
        # - non-blank line (not a heading)
        # - ends without terminal punctuation
        # - next is a blank line
        # - then a lowercase-starting continuation (not a heading or bullet marker)
        stripped_line = line.rstrip()
        if (stripped_line
                and not stripped_line.startswith('#')
                and stripped_line[-1] not in TERMINAL_PUNCT
                and i + 2 < len(cleaned)
                and cleaned[i + 1] == ''
                and cleaned[i + 2]
                and not cleaned[i + 2].startswith('#')
                and not cleaned[i + 2].startswith('*   ')
                and cleaned[i + 2][0].islower()):
            # Merge continuation
            cont = cleaned[i + 2].strip()
            if stripped_line.endswith('-'):
                merged.append(stripped_line + cont)
            else:
                merged.append(stripped_line + ' ' + cont)
            i += 3  # skip the blank and continuation
        else:
            merged.append(line)
            i += 1

    return merged


def main():
    print(f"Processing: {PDF_PATH}")

    output_lines = ['# Green Party Manifesto 2024', '']

    with pdfplumber.open(PDF_PATH) as pdf:
        total_pages = len(pdf.pages)
        print(f"Total pages: {total_pages}")

        for page_idx in range(total_pages):
            page = pdf.pages[page_idx]
            page_width = page.width
            print(f"  Page {page_idx} (w={page_width:.0f})...", end='', flush=True)

            if page_width < 700:
                # Single A4 page (cover page 0 or back page 27)
                if page_idx == 0:
                    output_lines.append('*Cover page*')
                    output_lines.append('')
                    print(" cover")
                else:
                    # Back page - extract any text
                    words = page.extract_words(keep_blank_chars=False, x_tolerance=3, y_tolerance=3)
                    content = [w for w in words if w['top'] < FOOTER_TOP]
                    if content:
                        text = ' '.join(w['text'] for w in content)
                        output_lines.append(clean(text))
                        output_lines.append('')
                    print(f" back ({len(content)} words)")
                continue

            # Special pages
            if page_idx == 1:
                # Foreword page
                page_lines = process_foreword_page(page)
                print(f" foreword ({len(page_lines)} lines)")
            elif page_idx == 2:
                # Contents page
                page_lines = process_contents_page(page)
                print(f" contents ({len(page_lines)} lines)")
            else:
                # Normal spread page
                page_lines = process_spread_page(page, page_idx)
                print(f" {len(page_lines)} lines")

            output_lines.extend(page_lines)
            if output_lines and output_lines[-1] != '':
                output_lines.append('')

    # Post-process
    output_lines = post_process(output_lines)

    output = '\n'.join(output_lines)
    # Collapse 3+ blank lines
    output = re.sub(r'\n{3,}', '\n\n', output)

    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        f.write(output)

    line_count = output.count('\n') + 1
    print(f"\nWritten: {OUT_PATH}")
    print(f"Size: {len(output):,} chars, ~{line_count} lines")


if __name__ == '__main__':
    main()
