#!/usr/bin/env python3
"""
Scottish Liberal Democrat 2015 manifesto extractor.

Layout: Landscape A4 (839×595pt).
Most pages have a two-column body layout:
  Left col:  x ≈ 37–410  (split point x < 415)
  Right col: x ≈ 415–789 (split point 415 ≤ x < 790)
Decorative vertical text runs down the left edge (x < 37) and right
edge (x ≥ 790) of every page — these are filtered out entirely.

Font hierarchy:
  HelveticaNeueLTStd-Bd  sz ≥ 35      →  chapter title (# or ##)
  HelveticaNeueLTStd-Lt  sz ≥ 35      →  chapter subtitle (part of # heading)
  HelveticaNeueLTStd-Bd  sz ≈ 11.5    →  ## section heading
  HelveticaNeueLTStd-Roman sz = 9.5   →  body text
  Wingdings-Regular 'w'  sz = 9.5     →  bullet marker → "* "
  ZapfDingbatsITC '❖'   sz = 9.5     →  bullet marker → "* "
  Any font               sz < 8.0     →  artefact / decorative → skip

Special pages (0-indexed):
  0   → cover (skip — no meaningful prose)
  1   → blank / logo (skip)
  2   → Contents
  3   → Introduction chapter opener (large heading)
  5   → "Britain in 2020" chapter intro (large heading + right col body)
  7, 10, 17, 24, 27, 31, 35, 37, 43, 46, 52 … → chapter opener pages
  9, 21  → infographic / chart pages (extract available text as-is)

Usage:
  python extract_scottish_lib_dem_2015.py [pdf_path] [output_path]
"""

import re
import sys

from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))
import pdfplumber

# ── Paths ──────────────────────────────────────────────────────────────────────

PDF = (sys.argv[1] if len(sys.argv) > 1
       else '/sessions/clever-zealous-sagan/mnt/uploads/Scottish Liberal Democrat 2015 manifesto.pdf')
OUT = (sys.argv[2] if len(sys.argv) > 2
       else '/sessions/clever-zealous-sagan/mnt/outputs/2015-scottish-lib-dem-manifesto.md')

# ── Constants ──────────────────────────────────────────────────────────────────

COL_SPLIT     = 415    # x-coordinate dividing left and right columns
X_LEFT_MIN    = 37     # ignore text with x0 < this (decorative left-edge strip)
X_RIGHT_MAX   = 790    # ignore text with x0 ≥ this (decorative right-edge strip)
Y_HEADER      = 18     # ignore text with top < this
Y_FOOTER      = 575    # ignore text with top ≥ this (body text runs to ~570pt on this doc)
MIN_SIZE      = 6.8    # ignore characters smaller than this (artefacts ≤ 6.3pt; 7.0pt is legit)
PARA_GAP      = 14     # min y-gap (pt) between line groups to start a new paragraph
Y_TOL         = 4      # y-bucketing tolerance for grouping chars into lines

HEADING_SIZE  = 10.5   # bold text at or above this size → section heading
LARGE_SIZE    = 30.0   # text at or above this size → chapter/section title

SKIP_PAGES        = {0, 1}  # 0-indexed pages to skip entirely
# Pages that have large (≥30pt) decorative text but are infographic/chart pages,
# not genuine chapter openers. Treated as body pages to avoid spurious # headings.
INFOGRAPHIC_PAGES = {9, 16, 21, 51, 56}  # 0-indexed

# ── Helpers ────────────────────────────────────────────────────────────────────

def bucket(top: float, tol: int = Y_TOL) -> int:
    return round(top / tol) * tol


def base_font(fn: str) -> str:
    return fn.split('+')[-1] if '+' in fn else fn


def is_bold(fn: str) -> bool:
    b = base_font(fn)
    return 'Bd' in b or 'Bold' in b or 'Heavy' in b or 'Black' in b


def is_light(fn: str) -> bool:
    b = base_font(fn)
    return 'Lt' in b or 'Light' in b or 'Th' in b


def is_bullet(w: dict) -> bool:
    """True for Wingdings 'w' or ZapfDingbats bullet characters."""
    fn = base_font(w.get('fontname', ''))
    text = w.get('text', '')
    return (('Wing' in fn or 'Zapf' in fn or 'Ding' in fn)
            and text.strip() in ('w', '❖', '•', 'n', 'l'))


def clean(text: str) -> str:
    """Fix common PDF ligature/encoding artefacts."""
    return (text
            .replace('ﬁ', 'fi').replace('ﬂ', 'fl')
            .replace('ﬃ', 'ffi').replace('ﬄ', 'ffl')
            .replace('­', '')   # soft hyphen
            .replace('​', '')   # zero-width space
            .replace('‘', "'").replace('’', "'")
            .replace('“', '"').replace('”', '"')
            .replace('–', '–').replace('—', '—')
            .replace('…', '...')
            )


def filter_word(w: dict) -> bool:
    """Return True if this word should be kept."""
    x0   = w.get('x0', 0)
    top  = w.get('top', 0)
    size = w.get('size', 0)
    text = w.get('text', '').strip()
    if not text:
        return False
    if x0 < X_LEFT_MIN or x0 >= X_RIGHT_MAX:
        return False
    if top < Y_HEADER or top >= Y_FOOTER:
        return False
    if size < MIN_SIZE and not is_bullet(w):
        return False
    return True


# ── Line / paragraph assembly ──────────────────────────────────────────────────

def words_to_paragraphs(words: list, is_right_col: bool = False) -> list:
    """
    Given a list of word dicts (already filtered and column-separated),
    group them into lines (by y-bucket), then into paragraphs.

    Paragraph break detection uses three complementary signals:
      1. y-gap ≥ PARA_GAP  (large vertical space)
      2. Short line: the previous line's last word ends significantly before
         the column's right margin → it was the last line of a paragraph.
      3. Indented first line: the current line's first word starts further
         right than the column's typical left margin → a new paragraph starts
         here. (Suppressed when the current block already contains a bullet,
         to avoid falsely splitting hanging-indent bullet continuations.)
      4. Bullet marker: a line whose first word is a bullet character always
         starts a new paragraph block.

    Returns a list of paragraph dicts:
        {'type': 'heading'|'bullet'|'body', 'text': str, 'level': int}
    """
    if not words:
        return []

    # Group into lines
    lines_map = defaultdict(list)
    for w in words:
        lines_map[bucket(w['top'])].append(w)

    sorted_y = sorted(lines_map.keys())
    if not sorted_y:
        return []

    # ── Column geometry for paragraph-break heuristics ────────────────────
    line_meta = {}
    for y in sorted_y:
        ws_sorted = sorted(lines_map[y], key=lambda w: w['x0'])
        line_meta[y] = {
            'last_x1':   max(w.get('x1', w['x0']) for w in ws_sorted),
            'first_x0':  ws_sorted[0]['x0'],
            'is_bullet': is_bullet(ws_sorted[0]),
        }

    right_margin = max(m['last_x1']  for m in line_meta.values())
    left_margin  = min(m['first_x0'] for m in line_meta.values())
    SHORT_LINE   = right_margin * 0.90   # lines ending here or shorter → para break follows
    INDENT_START = left_margin  + 8      # lines starting here or further right → new para

    # ── Dynamic PARA_GAP: adapt to the font size of this word set ─────────
    # Body text (9.5pt) has 12pt line spacing; 14pt intro text has 16pt.
    # PARA_GAP must exceed normal line spacing to avoid splitting at every
    # line, but must be smaller than actual paragraph gaps (20-24pt).
    # Strategy: find the most common (modal) y-gap between consecutive lines;
    # set PARA_GAP = modal_gap * 1.5, floored at the global PARA_GAP constant.
    if len(sorted_y) >= 3:
        raw_gaps = [sorted_y[i] - sorted_y[i - 1] for i in range(1, len(sorted_y))]
        modal_gap = Counter(round(g) for g in raw_gaps).most_common(1)[0][0]
        dyn_para_gap = max(modal_gap * 1.5, PARA_GAP)
    else:
        dyn_para_gap = PARA_GAP

    # ── Group lines into paragraph blocks ─────────────────────────────────
    para_blocks = []
    cur_block = [sorted_y[0]]
    cur_block_has_bullet = line_meta[sorted_y[0]]['is_bullet']

    for i in range(1, len(sorted_y)):
        prev_y = sorted_y[i - 1]
        cur_y  = sorted_y[i]
        gap    = cur_y - prev_y

        prev_short          = line_meta[prev_y]['last_x1'] < SHORT_LINE
        cur_starts_with_blt = line_meta[cur_y]['is_bullet']
        # Indent detection: don't fire inside a hanging-indent bullet block
        cur_indented = (
            line_meta[cur_y]['first_x0'] > INDENT_START
            and not cur_starts_with_blt
            and not cur_block_has_bullet
        )

        if gap >= dyn_para_gap or prev_short or cur_indented or cur_starts_with_blt:
            para_blocks.append(cur_block)
            cur_block = [cur_y]
            cur_block_has_bullet = cur_starts_with_blt
        else:
            cur_block.append(cur_y)
            if cur_starts_with_blt:
                cur_block_has_bullet = True

    para_blocks.append(cur_block)

    paragraphs = []
    for block in para_blocks:
        # Collect all words in this block, sorted by x within each line
        block_words = []
        for y in block:
            line_words = sorted(lines_map[y], key=lambda w: w['x0'])
            block_words.append(line_words)

        # Determine paragraph type from the first word
        first_word = block_words[0][0] if block_words and block_words[0] else None
        if first_word is None:
            continue

        fn   = first_word.get('fontname', '')
        size = first_word.get('size', 0)

        if is_bullet(first_word):
            para_type = 'bullet'
        elif is_bold(fn) and size >= HEADING_SIZE:
            # Only treat as ## heading if it looks like a numbered section heading
            # (e.g. "1.1", "2.3", "5.") — prevents infographic bold text becoming headings
            first_text = first_word.get('text', '').strip()
            # Section numbers are 1–19 followed by a period and optional digits
            # (e.g. "1.1", "5.", "10.3") — excludes chart values like "30.9"
            is_numbered = bool(re.match(r'^(?:[1-9]|1[0-9])\.\d{0,2}$', first_text))
            para_type = 'heading' if is_numbered else 'body'
        else:
            para_type = 'body'

        # Build text: for each line, join words, checking for style changes
        lines_text = []
        for line_words in block_words:
            line_parts = []
            in_bold = False
            for w in line_words:
                wtext = clean(w['text'])
                if not wtext.strip():
                    continue
                if is_bullet(w):
                    # Bullet marker — handled at paragraph level
                    continue
                wfn   = w.get('fontname', '')
                wsize = w.get('size', 0)
                word_bold = is_bold(wfn) and wsize < HEADING_SIZE  # inline bold
                # For heading paragraphs, don't wrap in ** again
                if para_type == 'heading':
                    line_parts.append(wtext)
                else:
                    if word_bold and not in_bold:
                        line_parts.append('**' + wtext)
                        in_bold = True
                    elif not word_bold and in_bold:
                        # Close the bold marker on previous word
                        if line_parts:
                            line_parts[-1] = line_parts[-1] + '**'
                        in_bold = False
                        line_parts.append(wtext)
                    else:
                        line_parts.append(wtext)

            if in_bold and line_parts:
                line_parts[-1] = line_parts[-1] + '**'

            lines_text.append(' '.join(line_parts))

        full_text = ' '.join(t for t in lines_text if t).strip()
        if not full_text:
            continue

        # Determine heading level
        level = 2  # default ## for section headings
        if para_type == 'heading' and size >= 20:
            level = 1

        paragraphs.append({
            'type':  para_type,
            'text':  full_text,
            'level': level,
        })

    return paragraphs


# ── Chapter opener page handling ───────────────────────────────────────────────

def extract_chapter_opener(page) -> list:
    """
    For chapter/section opener pages (large decorative text).
    Extracts the large title as a heading, then processes the remaining
    body text using the same two-column left→right logic as body pages.
    """
    words = page.extract_words(x_tolerance=3, y_tolerance=3,
                               extra_attrs=['fontname', 'size'])
    title_words = []
    left_words  = []
    right_words = []

    for w in words:
        x0   = w.get('x0', 0)
        top  = w.get('top', 0)
        size = w.get('size', 0)
        text = w.get('text', '').strip()
        if not text:
            continue
        if x0 < X_LEFT_MIN or x0 >= X_RIGHT_MAX:
            continue
        if top < Y_HEADER or top >= Y_FOOTER:
            continue
        if size >= LARGE_SIZE:
            title_words.append(w)
        elif size >= MIN_SIZE:
            if x0 < COL_SPLIT:
                left_words.append(w)
            else:
                right_words.append(w)

    # Reconstruct title from large words, grouped by y-line
    title_lines = defaultdict(list)
    for w in title_words:
        title_lines[bucket(w['top'], tol=8)].append(w)

    title_parts_bold  = []
    title_parts_light = []
    for y in sorted(title_lines.keys()):
        line_ws   = sorted(title_lines[y], key=lambda w: w['x0'])
        line_text = ' '.join(clean(w['text']) for w in line_ws if w['text'].strip())
        if not line_text.strip():
            continue
        fn_first = line_ws[0].get('fontname', '')
        if is_bold(fn_first):
            title_parts_bold.append(line_text)
        else:
            title_parts_light.append(line_text)

    result     = []
    bold_text  = ' '.join(title_parts_bold).strip()
    light_text = ' '.join(title_parts_light).strip()

    # Bold large text → H1 (chapter title); light large text → H2 (subtitle).
    # If only one font weight present, always emit as H1.
    if bold_text:
        result.append({'type': 'heading', 'text': bold_text, 'level': 1})
        if light_text:
            result.append({'type': 'heading', 'text': light_text, 'level': 2})
    elif light_text:
        result.append({'type': 'heading', 'text': light_text, 'level': 1})

    # Body text: left column first, then right column
    result.extend(words_to_paragraphs(left_words))
    result.extend(words_to_paragraphs(right_words))

    return result


# ── Contents page ──────────────────────────────────────────────────────────────

def extract_contents_page(page) -> list:
    """Extract the table of contents page."""
    words = page.extract_words(x_tolerance=3, y_tolerance=3,
                               extra_attrs=['fontname', 'size'])

    result = [{'type': 'heading', 'text': 'Contents', 'level': 1}]
    entries = []

    # Group by line
    lines_map = defaultdict(list)
    for w in words:
        x0   = w.get('x0', 0)
        top  = w.get('top', 0)
        size = w.get('size', 0)
        text = w.get('text', '').strip()
        if not text:
            continue
        if x0 < X_LEFT_MIN or x0 >= X_RIGHT_MAX:
            continue
        if top < 40 or top >= Y_FOOTER:
            continue
        if size < 7:
            continue
        # Skip the large "Contents" heading itself
        if size >= 40:
            continue
        lines_map[bucket(top, tol=6)].append(w)

    for y in sorted(lines_map.keys()):
        line_ws = sorted(lines_map[y], key=lambda w: w['x0'])
        line_text = ' '.join(clean(w['text']) for w in line_ws).strip()
        if line_text:
            entries.append(line_text)

    # Output as a body block (join lines that clearly continue)
    # Separate page-number-only lines and rejoin
    toc_lines = []
    for entry in entries:
        toc_lines.append(entry)

    if toc_lines:
        result.append({'type': 'body', 'text': '\n'.join(toc_lines), 'level': 0})

    return result


# ── Main page extractor ────────────────────────────────────────────────────────

def extract_body_page(page) -> list:
    """
    Standard two-column body page extraction.
    Left column (x < COL_SPLIT) is read top-to-bottom first,
    then right column (COL_SPLIT ≤ x < X_RIGHT_MAX).
    """
    words = page.extract_words(x_tolerance=3, y_tolerance=3,
                               extra_attrs=['fontname', 'size'])

    left_words  = []
    right_words = []

    for w in words:
        if not filter_word(w):
            continue
        if w['x0'] < COL_SPLIT:
            left_words.append(w)
        else:
            right_words.append(w)

    paras = []
    paras.extend(words_to_paragraphs(left_words))
    paras.extend(words_to_paragraphs(right_words))
    return paras


# ── Markdown formatter ─────────────────────────────────────────────────────────

def paras_to_markdown(paras: list) -> str:
    chunks = []
    for p in paras:
        ptype = p['type']
        text  = p['text'].strip()
        level = p.get('level', 2)
        if not text:
            continue
        if ptype == 'heading':
            prefix = '#' * level
            chunks.append(f'{prefix} {text}')
        elif ptype == 'bullet':
            chunks.append(f'* {text}')
        else:
            chunks.append(text)
    return '\n\n'.join(chunks)


# ── Page-type detection ────────────────────────────────────────────────────────

def page_has_large_text(page) -> bool:
    """True if the page contains large decorative chapter-title text."""
    for c in page.chars:
        if (c['text'].strip() and c['size'] >= LARGE_SIZE
                and c.get('x0', 0) >= X_LEFT_MIN
                and c.get('x0', 0) < X_RIGHT_MAX
                and c.get('top', 0) >= Y_HEADER
                and c.get('top', 0) < Y_FOOTER):
            return True
    return False


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print(f'Extracting: {PDF}')
    print(f'Output:     {OUT}\n')

    Path(OUT).parent.mkdir(parents=True, exist_ok=True)

    all_sections = []

    # Title block
    all_sections.append([{
        'type': 'heading',
        'text': 'Scottish Liberal Democrat General Election Manifesto 2015',
        'level': 1,
    }])

    with pdfplumber.open(PDF) as pdf:
        total = len(pdf.pages)
        print(f'Total pages: {total}')

        for i, page in enumerate(pdf.pages):
            pg_num = i + 1
            print(f'  Page {pg_num:3d}/{total}', end=' ')

            if i in SKIP_PAGES:
                print('(skipped)')
                continue

            # Contents page
            if i == 2:
                print('(contents)')
                paras = extract_contents_page(page)
                all_sections.append(paras)
                continue

            # Infographic/chart pages — have large text but are NOT chapter openers
            if i in INFOGRAPHIC_PAGES:
                print('(infographic — body extraction)')
                paras = extract_body_page(page)
                word_count = sum(len(p['text'].split()) for p in paras)
                print(f'  → {word_count} words')
                if paras:
                    all_sections.append(paras)
                continue

            # Chapter opener / intro pages with large decorative text
            if page_has_large_text(page):
                print('(chapter opener)')
                paras = extract_chapter_opener(page)
                all_sections.append(paras)
                continue

            # Standard body page
            paras = extract_body_page(page)
            word_count = sum(len(p['text'].split()) for p in paras)
            print(f'({word_count} words)')
            if paras:
                all_sections.append(paras)

    # Write output
    md_parts = []
    for section_paras in all_sections:
        md_text = paras_to_markdown(section_paras)
        if md_text.strip():
            md_parts.append(md_text)

    full_md = '\n\n---\n\n'.join(md_parts)

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(full_md)
        f.write('\n')

    # Word-count summary
    md_words = len(full_md.split())
    print(f'\nMarkdown word count: {md_words:,}')

    # pdftotext comparison if available
    import subprocess
    try:
        result = subprocess.run(
            ['pdftotext', PDF, '-'],
            capture_output=True, text=True, timeout=30
        )
        pdf_words = len(result.stdout.split())
        coverage = md_words / pdf_words * 100 if pdf_words else 0
        print(f'pdftotext word count: {pdf_words:,}')
        print(f'Coverage: {coverage:.1f}%')
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print('(pdftotext not available for coverage check)')

    print(f'\nDone → {OUT}')


if __name__ == '__main__':
    main()
