#!/usr/bin/env python3
"""
Welsh Conservative 2019 manifesto extractor.
595×595pt square pages, two-column layout.

Layout:
  - Chapter opener pages (max char size >= 50): large title → # heading,
    intro text (Intelo-Regular sz=13) → full-width body paragraphs,
    body text (sz=9) → two-column
  - Standard body pages: two-column at col_split = 207
    Left col: x ≈ 40–195, Right col: x ≈ 215–555
  - Candidate profile pages/inserts: InteloAlt-SemiBold/Intelo-Bold sz=18
    followed by Intelo-Bold sz=12 "Candidate for" → handled as bold bylines
    in post-processing

Font hierarchy:
  InteloAlt-SemiBold sz ≥ 50  → # chapter title
  Intelo-Bold / InteloAlt-SemiBold sz ≥ 35  → ## major heading
  Intelo-Bold / InteloAlt-SemiBold sz ∈ [15, 35)  → ## section heading (or candidate name)
  Intelo-Bold sz ∈ [12.5, 15)  → ### subsection heading
  Intelo-Regular sz ≥ 11        → intro / full-width body text
  Intelo-Regular / Intelo-Bold sz ≤ 10  → body text (two-column)
  Wingdings3 any size           → bullet marker (→ "* ")
  • (U+2022) in any font        → bullet marker (→ "* ")
  ProximaNovaCond-Bold sz ≤ 9   → footer (skip)

Usage:
  python extract_welsh_conservative_2019.py [pdf_path] [output_path]
"""

import re
import sys
from collections import defaultdict
from pathlib import Path

import pdfplumber

# ── Paths ──────────────────────────────────────────────────────────────────────

PDF = (sys.argv[1] if len(sys.argv) > 1
       else '/sessions/clever-zealous-lamport/mnt/uploads/Welsh Conservative Manifesto 2019.pdf')
OUT = (sys.argv[2] if len(sys.argv) > 2
       else '/sessions/clever-zealous-lamport/mnt/outputs/2019-welsh-conservative-manifesto.md')

# ── Constants ──────────────────────────────────────────────────────────────────

COL_SPLIT  = 207    # x-boundary between left and right body columns
Y_HEADER   = 35     # ignore chars above this y
Y_FOOTER   = 556    # ignore chars at/below this y (page-number footer at y≈560)
PARA_GAP   = 14     # minimum y-gap (pt) that signals a new paragraph
Y_TOL      = 4      # y-bucketing tolerance

# ── Helpers ────────────────────────────────────────────────────────────────────

def bucket(top: float, tol: int = Y_TOL) -> int:
    return round(top / tol) * tol


def base_font(fn: str) -> str:
    return fn.split('+')[-1]


def clean(text: str) -> str:
    """Fix common PDF ligature/encoding artefacts."""
    return (text
            .replace('ﬁ', 'fi').replace('ﬂ', 'fl')
            .replace('ﬃ', 'ffi').replace('ﬄ', 'ffl')
            .replace('­', '')    # soft hyphen
            .replace('​', '')    # zero-width space
            )


def is_footer_char(c: dict) -> bool:
    return 'ProximaNovaCond' in base_font(c['fontname']) and c['size'] <= 9


def is_wingdings_bullet(c: dict) -> bool:
    return 'Wingdings3' in base_font(c['fontname'])


def is_chapter_title_char(c: dict) -> bool:
    fn = base_font(c['fontname'])
    return 'InteloAlt-SemiBold' in fn and c['size'] >= 50


def is_heading_char(c: dict, min_sz: float = 12.5) -> bool:
    """True for any bold/semibold heading-level char (sz ≥ min_sz)."""
    fn = base_font(c['fontname'])
    return (('Intelo-Bold' in fn or 'InteloAlt-SemiBold' in fn)
            and c['size'] >= min_sz
            and c['text'].strip())


def is_body_char(c: dict) -> bool:
    fn = base_font(c['fontname'])
    return (('Intelo-Regular' in fn or 'Intelo-Bold' in fn
             or 'InteloAlt-ExtraBold' in fn)
            and c['size'] <= 13
            and c['text'].strip())


# ── Chapter title extraction ───────────────────────────────────────────────────

def extract_chapter_title(page) -> list[str]:
    """Return ['# Title Text'] for chapter-opener pages (max char size ≥ 50).
    Uses extract_words() with y_tolerance=1 to get clean word spacing.
    """
    title_ys: set[int] = set()
    for c in page.chars:
        if (c['text'].strip() and is_chapter_title_char(c)
                and Y_HEADER < c['top'] < Y_FOOTER):
            title_ys.add(bucket(c['top']))   # standard tol=4

    if not title_ys:
        return []

    words = page.extract_words(keep_blank_chars=False,
                               y_tolerance=1, x_tolerance=3,
                               extra_attrs=['fontname', 'size'])
    words_by_y: dict[int, list] = defaultdict(list)
    for w in words:
        y = bucket(w['top'])
        fn = base_font(w.get('fontname', ''))
        sz = w.get('size', 0)
        if y in title_ys and sz >= 50 and 'InteloAlt-SemiBold' in fn:
            words_by_y[y].append(w)

    lines = []
    for y in sorted(words_by_y):
        row = sorted(words_by_y[y], key=lambda w: w['x0'])
        line = clean(' '.join(w['text'] for w in row)).strip()
        if line:
            lines.append(line)

    merged = ' '.join(lines)
    merged = re.sub(r'(\w)- (\w)', r'\1-\2', merged)
    return [f'# {merged}'] if merged else []


# ── Heading extraction ─────────────────────────────────────────────────────────

def extract_headings(page) -> list[tuple]:
    """
    Extract section (##) and subsection (###) headings.
    Returns list of (y_float, col, text, level) tuples sorted by y.

    Key design decisions:
    - h_info is keyed by y_bkt only (not x_bkt) so that a single heading whose
      words span a wide x-range (e.g. "FOREWORD FROM BORIS JOHNSON") is always
      collected as one unit.
    - Left and right column chars are tracked SEPARATELY in left_h_info /
      right_h_info to avoid the bucket collision where a left-col heading row
      and a right-col heading row share the same y-bucket but have different
      font sizes (the max_sz would be wrong if merged).
    - Full-width headings are detected by checking the x-gap between the
      rightmost left-side char and the leftmost right-side char in the same
      y-bucket.  Gap < FULLWIDTH_GAP (50 pt) → one heading spanning both cols.
    - Within a column, two separate headings may share the same y-bucket if
      they are at different x-positions (e.g. pg23: "Fix our immigration" at
      x≈219 and "Attracting the best and brightest" at x≈399, both right-col
      at y≈87).  These are separated in Step 3 by splitting collected words on
      any inter-word x-gap > SUBCOL_GAP (40 pt) — much larger than normal word
      spacing but much smaller than the ~80 pt gap between sub-columns.
    - The merge step groups rows by (col, level, x_bucket) and measures y gaps
      from the LAST merged row, so 3+ line headings merge correctly.
    """
    FULLWIDTH_GAP = 50   # pt; below this the L+R chars form one full-width heading
    SUBCOL_GAP    = 40   # pt; x-gap between words that signals different sub-columns

    # Step 1: track heading chars separately per left/right column, keyed by y_bkt.
    # Also track min_x / max_x for full-width detection.
    left_h_info:  dict[int, dict] = {}
    right_h_info: dict[int, dict] = {}

    def _update(info_dict: dict, y_bkt: int, c: dict):
        c_width = c.get('width', c['size'] * 0.5)
        if y_bkt not in info_dict:
            info_dict[y_bkt] = {
                'min_y': c['top'], 'max_y': c['top'], 'max_sz': c['size'],
                'min_x': c['x0'], 'max_x': c['x0'] + c_width,
            }
        else:
            info = info_dict[y_bkt]
            info['min_y']  = min(info['min_y'],  c['top'])
            info['max_y']  = max(info['max_y'],  c['top'])
            info['max_sz'] = max(info['max_sz'], c['size'])
            info['min_x']  = min(info['min_x'],  c['x0'])
            info['max_x']  = max(info['max_x'],  c['x0'] + c_width)

    for c in page.chars:
        if not (c['text'].strip() and Y_HEADER < c['top'] < Y_FOOTER):
            continue
        if is_chapter_title_char(c):
            continue
        if not is_heading_char(c, min_sz=12.5):
            continue
        y_bkt = bucket(c['top'])
        if c['x0'] < COL_SPLIT:
            _update(left_h_info,  y_bkt, c)
        else:
            _update(right_h_info, y_bkt, c)

    if not left_h_info and not right_h_info:
        return []

    # Step 1b: detect full-width heading rows (same y_bkt in both L and R,
    # tiny x-gap between them).  Merge into a single 'full' entry.
    common_ybkts = set(left_h_info.keys()) & set(right_h_info.keys())
    full_h_info: dict[int, dict] = {}
    for y_bkt in common_ybkts:
        gap = right_h_info[y_bkt]['min_x'] - left_h_info[y_bkt]['max_x']
        if gap < FULLWIDTH_GAP:
            l, r = left_h_info.pop(y_bkt), right_h_info.pop(y_bkt)
            full_h_info[y_bkt] = {
                'min_y':  min(l['min_y'],  r['min_y']),
                'max_y':  max(l['max_y'],  r['max_y']),
                'max_sz': max(l['max_sz'], r['max_sz']),
            }

    # Step 2: extract_words with y_tolerance=1
    all_words = page.extract_words(keep_blank_chars=False,
                                   y_tolerance=1, x_tolerance=3,
                                   extra_attrs=['fontname', 'size'])

    def _heading_word(w) -> bool:
        fn = base_font(w.get('fontname', ''))
        sz = w.get('size', 0)
        return (('Intelo-Bold' in fn or 'InteloAlt-SemiBold' in fn) and sz >= 12.5)

    def _split_by_x_gap(words):
        """Split x-sorted words into sub-groups when either:
        - the inter-word x-gap exceeds SUBCOL_GAP, OR
        - the font size changes by more than 2pt (two separate heading levels
          sharing the same y-bucket, e.g. sz=18 '## Fix our immigration' and
          sz=14 '### Attracting the best and brightest' at y≈87 on pg 23).
        """
        if not words:
            return []
        groups = [[words[0]]]
        for w in words[1:]:
            gap        = w['x0'] - groups[-1][-1]['x1']
            prev_sz    = groups[-1][-1].get('size', 0)
            curr_sz    = w.get('size', 0)
            size_jump  = abs(curr_sz - prev_sz) > 2
            if gap > SUBCOL_GAP or size_jump:
                groups.append([w])
            else:
                groups[-1].append(w)
        return groups

    # Step 3: for each heading y-group collect words, then split into sub-column
    # groups if multiple headings share the same y-row in the same column.
    # Rows tuple: (y_mean, col, text, level, x_start)
    rows: list[tuple] = []

    def _add_rows(h_info: dict, col: str):
        for y_bkt, info in h_info.items():
            y_min  = info['min_y'] - 1.5
            y_max  = info['max_y'] + 3.0
            level  = '##' if info['max_sz'] >= 15 else '###'
            y_mean = (info['min_y'] + info['max_y']) / 2

            row_words = [w for w in all_words
                         if y_min <= w['top'] <= y_max and _heading_word(w)]
            if col == 'left':
                row_words = [w for w in row_words if w['x0'] <  COL_SPLIT]
            elif col == 'right':
                row_words = [w for w in row_words if w['x0'] >= COL_SPLIT]
            # 'full': keep all (full-width heading)

            if not row_words:
                continue
            row_words.sort(key=lambda w: w['x0'])
            actual_col = 'left' if col == 'full' else col

            # Split into sub-groups when two separate headings share a y-row.
            # Re-derive the heading level from each sub-group's own font sizes
            # so that mixed-level rows (e.g. sz=18 '##' and sz=14 '###' at the
            # same y) get the correct level for each sub-group.
            for word_group in _split_by_x_gap(row_words):
                grp_max_sz = max(w.get('size', 0) for w in word_group)
                grp_level  = '##' if grp_max_sz >= 15 else '###'
                text = clean(' '.join(w['text'] for w in word_group)).strip()
                text = re.sub(r'(\w)- (\w)', r'\1-\2', text)
                if text:
                    rows.append((y_mean, actual_col, text, grp_level,
                                 word_group[0]['x0']))

    _add_rows(left_h_info,  'left')
    _add_rows(right_h_info, 'right')
    _add_rows(full_h_info,  'full')

    rows.sort(key=lambda r: r[0])

    # Step 4: merge heading rows that belong to the same logical heading.
    #
    # Strategy: group rows by (col, level, x_bucket) where x_bucket quantises
    # x_start at 80pt granularity.  This keeps sub-columns in the same page
    # column separate — e.g. "Investing across" (x=219) and "Investing in Wales"
    # (x=399) fall in different x-buckets (240 vs 400) and are never merged,
    # while multi-line headings like "Make Wales the / best place to / …" all
    # start at x≈40 and land in the same bucket.
    #
    # Within each group, merge consecutive rows whose y gap (from the LAST
    # merged row, not the first) is ≤ 28pt.  Using last_y avoids the problem
    # where a 3-line heading incorrectly appears to span > 28pt from its anchor.

    X_BUCKET_SIZE = 80

    from collections import defaultdict as _dd
    groups: dict = _dd(list)
    for y, col, text, level, x_start in rows:
        x_bkt = round(x_start / X_BUCKET_SIZE) * X_BUCKET_SIZE
        groups[(col, level, x_bkt)].append((y, text))

    group_entries: list[tuple] = []   # (y_first, col, text, level)
    for (col, level, x_bkt), group_rows in groups.items():
        group_rows.sort(key=lambda r: r[0])
        merged_text: str | None = None
        y_first: float | None = None
        y_last: float | None = None
        for y, text in group_rows:
            if y_last is not None and (y - y_last) <= 28:
                merged_text = merged_text + ' ' + text   # type: ignore[operator]
                y_last = y
            else:
                if merged_text is not None:
                    group_entries.append((y_first, col, merged_text, level))
                merged_text = text
                y_first = y
                y_last = y
        if merged_text:
            group_entries.append((y_first, col, merged_text, level))

    group_entries.sort(key=lambda r: r[0])

    result = []
    for y, col, text, level in group_entries:
        text = re.sub(r'(\w)- (\w)', r'\1-\2', text)
        result.append((y, col, text, level))

    return result


# ── Paragraph assembly ─────────────────────────────────────────────────────────

def words_to_paras(words: list, para_gap: int = PARA_GAP) -> list[str]:
    """
    Assemble a list of word-dicts (from extract_words) into Markdown paragraphs.
    Handles: regular body, bold body, bullets (Wingdings3 or •).
    """
    if not words:
        return []

    words = sorted(words, key=lambda w: (bucket(w['top']), w['x0']))

    paras: list[str] = []
    buf: list[dict] = []
    buf_type: str | None = None
    prev_top: int | None = None

    def flush():
        nonlocal buf, buf_type
        if not buf:
            return
        tokens = []
        for w in buf:
            t = clean(w['text'])
            # Strip Wingdings bullet chars from text tokens
            t = t.replace('', '').replace('•', '').strip()
            if t:
                tokens.append(t)
        text = ' '.join(tokens).strip()
        if not text:
            buf = []; buf_type = None; return

        if buf_type == 'bullet':
            paras.append(f'* {text}')
        elif buf_type == 'bold':
            paras.append(f'**{text}**')
        else:
            paras.append(text)
        buf = []; buf_type = None

    for w in words:
        top   = bucket(w['top'])
        fn    = base_font(w.get('fontname', ''))
        text  = w.get('text', '')
        gap   = (top - prev_top) if prev_top is not None else 0

        is_bullet_word = ('Wingdings3' in fn) or text.startswith('•')
        is_bold_word   = ('Intelo-Bold' in fn or 'InteloAlt-ExtraBold' in fn)

        if is_bullet_word:
            flush()
            buf_type = 'bullet'
            prev_top = top
            continue

        new_type = 'bold' if is_bold_word else 'body'

        force_break = (
            gap >= para_gap
            or (buf_type is not None
                and buf_type != 'bullet'
                and buf_type != new_type)
        )
        if prev_top is not None and force_break:
            flush()

        buf.append(w)
        buf_type = new_type if buf_type != 'bullet' else 'bullet'
        prev_top = top

    flush()
    return [p for p in paras if p.strip()]


# ── Page processors ────────────────────────────────────────────────────────────

def process_chapter_opener(page) -> list[str]:
    """
    Chapter opener pages (max char size ≥ 50).
    1. Extract # title.
    2. Extract any ## / ### section headings.
    3. Extract intro paragraphs (Intelo-Regular sz ≥ 11) full-width.
    4. Extract two-column body (sz ≤ 10).
    """
    result: list[str] = []

    # 1. Chapter title
    result.extend(extract_chapter_title(page))

    # 2. Section/subsection headings
    headings = extract_headings(page)
    heading_ys = {bucket(y, tol=2) for y, _, _, _ in headings}
    # We'll emit headings inline with content below, but for chapter openers
    # they typically appear before body text, so emit them all first.
    for _, col, text, level in sorted(headings, key=lambda x: x[0]):
        result.append(f'{level} {text}')

    # Collect heading char y-buckets to exclude from body extraction
    h_char_ys: set[int] = set()
    for c in page.chars:
        if (c['text'].strip() and Y_HEADER < c['top'] < Y_FOOTER
                and is_heading_char(c, min_sz=12.5)
                and not is_chapter_title_char(c)):
            h_char_ys.add(bucket(c['top'], tol=2))

    all_words = page.extract_words(keep_blank_chars=False, extra_attrs=['fontname', 'size'])

    # 3. Intro text (Intelo-Regular sz ≥ 11) — full-width
    intro_words = [w for w in all_words
                   if Y_HEADER < w['top'] < Y_FOOTER
                   and bucket(w['top'], tol=2) not in h_char_ys
                   and 'Intelo-Regular' in base_font(w.get('fontname', ''))
                   and w.get('size', 0) >= 11]
    result.extend(words_to_paras(intro_words, para_gap=18))

    # 4. Two-column body (sz ≤ 10)
    body_words = [w for w in all_words
                  if Y_HEADER < w['top'] < Y_FOOTER
                  and bucket(w['top'], tol=2) not in h_char_ys
                  and (('Intelo-Regular' in base_font(w.get('fontname', ''))
                        or 'Intelo-Bold' in base_font(w.get('fontname', ''))
                        or 'Wingdings3' in base_font(w.get('fontname', '')))
                       and w.get('size', 0) <= 10)]

    left_words  = [w for w in body_words if w['x0'] <  COL_SPLIT]
    right_words = [w for w in body_words if w['x0'] >= COL_SPLIT]
    result.extend(words_to_paras(left_words))
    result.extend(words_to_paras(right_words))

    return result


def process_standard_page(page) -> list[str]:
    """
    Standard two-column body page.
    1. Extract headings (char-level, per-column).
    2. Collect body words per column (exclude heading-char y-rows).
    3. Interleave headings into each column's word stream.
    """
    headings = extract_headings(page)

    # Build set of y-buckets (tol=2) that belong to heading chars
    h_char_ys: set[int] = set()
    for c in page.chars:
        if (c['text'].strip() and Y_HEADER < c['top'] < Y_FOOTER
                and is_heading_char(c, min_sz=12.5)
                and not is_chapter_title_char(c)):
            h_char_ys.add(bucket(c['top'], tol=2))

    all_words = page.extract_words(keep_blank_chars=False, extra_attrs=['fontname', 'size'])

    # Body words: exclude heading-char y-rows, include sz ≤ 13 body fonts
    body_words = []
    for w in all_words:
        if not (Y_HEADER < w['top'] < Y_FOOTER):
            continue
        if bucket(w['top'], tol=2) in h_char_ys:
            continue
        fn  = base_font(w.get('fontname', ''))
        sz  = w.get('size', 0)
        if 'ProximaNovaCond' in fn:
            continue
        if 'Wingdings3' in fn:
            body_words.append(w)
        elif ('Intelo-Regular' in fn or 'Intelo-Bold' in fn
              or 'InteloAlt-ExtraBold' in fn) and sz <= 13:
            body_words.append(w)

    left_body  = [w for w in body_words if w['x0'] <  COL_SPLIT]
    right_body = [w for w in body_words if w['x0'] >= COL_SPLIT]

    left_heads  = sorted([(y, t, lv) for y, col, t, lv in headings if col == 'left'],
                         key=lambda x: x[0])
    right_heads = sorted([(y, t, lv) for y, col, t, lv in headings if col == 'right'],
                         key=lambda x: x[0])

    result: list[str] = []
    result.extend(_interleave(left_body,  left_heads))
    result.extend(_interleave(right_body, right_heads))
    return result


def _interleave(body_words: list, headings: list[tuple]) -> list[str]:
    """Emit headings at the right position within the body word stream."""
    if not body_words and not headings:
        return []
    if not headings:
        return words_to_paras(body_words)

    result: list[str] = []
    head_idx = 0
    segment: list[dict] = []

    sorted_body = sorted(body_words, key=lambda w: (bucket(w['top']), w['x0']))

    for w in sorted_body:
        w_y = w['top']
        while head_idx < len(headings) and headings[head_idx][0] <= w_y:
            if segment:
                result.extend(words_to_paras(segment))
                segment = []
            hy, htxt, hlv = headings[head_idx]
            result.append(f'{hlv} {htxt}')
            head_idx += 1
        segment.append(w)

    if segment:
        result.extend(words_to_paras(segment))
    while head_idx < len(headings):
        hy, htxt, hlv = headings[head_idx]
        result.append(f'{hlv} {htxt}')
        head_idx += 1

    return result


def process_single_column_page(page) -> list[str]:
    """
    Single-column pages (My Guarantee, Contents — max_sz ≥ 35 < 50).
    Extract major headings (sz ≥ 35) as # headings, then body text.
    """
    # Major headings (sz ≥ 35)
    major_chars: dict[int, list] = defaultdict(list)
    for c in page.chars:
        if (c['text'].strip() and Y_HEADER < c['top'] < Y_FOOTER
                and is_heading_char(c, min_sz=35)):
            major_chars[bucket(c['top'], tol=8)].append(c)

    major_headings = []
    major_ys: set[int] = set()
    # Use extract_words with y_tolerance=1 to avoid mixing adjacent rows
    page_words_major = page.extract_words(keep_blank_chars=False,
                                          y_tolerance=1, x_tolerance=3,
                                          extra_attrs=['fontname', 'size'])
    for y_key in sorted(major_chars):
        chars = major_chars[y_key]
        y_tops = [c['top'] for c in chars]
        y_min = min(y_tops) - 1.5
        y_max = max(y_tops) + 3.0
        for c in chars:
            major_ys.add(bucket(c['top'], tol=2))
        row_words = [w for w in page_words_major
                     if y_min <= w['top'] <= y_max
                     and w.get('size', 0) >= 35]
        row_words.sort(key=lambda w: w['x0'])
        text = clean(' '.join(w['text'] for w in row_words)).strip()
        text = re.sub(r'(\w)- (\w)', r'\1-\2', text)
        if text:
            major_headings.append((y_key, text, '#'))

    # Section/subsection headings — filter out rows that overlap with major
    # heading y-rows (to avoid emitting the same text twice) and filter out
    # the decorative "Welsh Conservative Party Manifesto 2019" banner that
    # appears at the bottom of a few pages.
    _BANNER_RE = re.compile(r'Welsh Conservative|Manifesto\s+20\d\d', re.I)
    sub_headings_raw = extract_headings(page)
    sub_headings = [(y, col, t, lv) for y, col, t, lv in sub_headings_raw
                    if bucket(y, tol=2) not in major_ys
                    and not _BANNER_RE.search(t)]
    h_char_ys: set[int] = set()
    for c in page.chars:
        if (c['text'].strip() and Y_HEADER < c['top'] < Y_FOOTER
                and is_heading_char(c, min_sz=12.5)):
            h_char_ys.add(bucket(c['top'], tol=2))
    h_char_ys |= major_ys

    all_words = page.extract_words(keep_blank_chars=False, extra_attrs=['fontname', 'size'])
    body_words = []
    for w in all_words:
        if not (Y_HEADER < w['top'] < Y_FOOTER):
            continue
        if bucket(w['top'], tol=2) in h_char_ys:
            continue
        fn = base_font(w.get('fontname', ''))
        sz = w.get('size', 0)
        if 'ProximaNovaCond' in fn:
            continue
        if sz <= 25:
            body_words.append(w)

    all_heads = ([(float(y), t, lv) for y, t, lv in major_headings]
                 + [(y, t, lv) for y, col, t, lv in sub_headings])
    all_heads.sort(key=lambda x: x[0])

    return _interleave(body_words, [(y, t, lv) for y, t, lv in all_heads])


# ── Main ──────────────────────────────────────────────────────────────────────

all_paras: list[str] = [
    '# Welsh Conservative Party Manifesto 2019'
]

with pdfplumber.open(PDF) as pdf:
    total = len(pdf.pages)
    print(f'Total pages: {total}')

    for pg_num, page in enumerate(pdf.pages):
        content_chars = [c for c in page.chars
                         if c['text'].strip()
                         and Y_HEADER < c['top'] < Y_FOOTER
                         and not is_footer_char(c)]
        if not content_chars:
            print(f'  pg {pg_num:3d}: BLANK — skip')
            continue

        max_sz = max(c['size'] for c in content_chars)

        if pg_num == 0:
            print(f'  pg {pg_num:3d}: COVER — skip')
            continue

        if max_sz >= 50:
            paras = process_chapter_opener(page)
            label = f'CHAPTER OPENER (max_sz={max_sz:.0f})'
        elif max_sz >= 35:
            paras = process_single_column_page(page)
            label = f'MAJOR HEADING PAGE (max_sz={max_sz:.0f})'
        else:
            paras = process_standard_page(page)
            label = f'std (max_sz={max_sz:.0f})'

        all_paras.extend(paras)
        print(f'  pg {pg_num:3d}: {label:40s}  {len(paras):3d} paras')


# ── Post-processing ───────────────────────────────────────────────────────────

md = '\n\n'.join(p for p in all_paras if p.strip()) + '\n'

# 1. Merge paragraphs ending without terminal punctuation
TERMINAL_PUNCT = set('.!?:;"\'»')

def merge_unfinished_paras(text: str) -> str:
    paras = text.split('\n\n')
    result: list[str] = []
    for para in paras:
        stripped = para.strip()
        if result and stripped:
            prev = result[-1].rstrip()
            prev_structural = (any(prev.startswith(p) for p in ('# ', '## ', '### '))
                               or prev.endswith('**'))
            curr_structural = any(stripped.startswith(p) for p in ('# ', '## ', '### ', '* '))
            if (not prev_structural and not curr_structural
                    and prev and prev[-1] not in TERMINAL_PUNCT):
                result[-1] = prev + ' ' + stripped
                continue
        result.append(para)
    return '\n\n'.join(result)

md = merge_unfinished_paras(md)
md = merge_unfinished_paras(md)

# 2. Fix hyphen-space: "self- government" → "self-government"
md = re.sub(r'(\w)- (\w)', r'\1-\2', md)

# 3. Collapse 3+ blank lines to 2
md = re.sub(r'\n{4,}', '\n\n\n', md)

# 4. Fix adjacent bold blocks
md = re.sub(r'\*\*([^*\n]+)\*\* \*\*([^*\n]+)\*\*', r'**\1 \2**', md)

# 5. Fix specific heading artefacts:
#    "Fix our immigration" and "system" are two rows of a left-col heading,
#    but "Attracting the best and brightest" is a separate right-col heading.
#    These should already be separated by the char-level extractor, but add
#    manual fixes for any residual issues found in review.
HEADING_FIXES = {
    # No manual fixes needed if char-level extractor works correctly.
}
for old, new in HEADING_FIXES.items():
    md = md.replace(old, new)

# 6. Convert candidate-profile headings to bold bylines.
#    Pattern: ## Name\n\nparagraph containing "Candidate for"
def fix_candidate_headings(text: str) -> str:
    paras = text.split('\n\n')
    result: list[str] = []
    i = 0
    while i < len(paras):
        p = paras[i]
        if (p.startswith('## ') and i + 1 < len(paras)
                and 'Candidate for' in paras[i + 1]
                and not paras[i + 1].startswith('#')):
            name = p[3:].strip()
            result.append(f'**{name}**')
            result.append(paras[i + 1])
            i += 2
        else:
            result.append(p)
            i += 1
    return '\n\n'.join(result)

md = fix_candidate_headings(md)

# ── Write output ──────────────────────────────────────────────────────────────

Path(OUT).write_text(md, encoding='utf-8')

import subprocess
wc_md = len(md.split())
print(f'\nMarkdown word count: {wc_md:,}')

res = subprocess.run(['pdftotext', PDF, '-'], capture_output=True, text=True, timeout=60)
if res.returncode == 0:
    wc_pdf = len(res.stdout.split())
    print(f'PDF word count (pdftotext): {wc_pdf:,}')
    print(f'Coverage: {wc_md / wc_pdf * 100:.1f}%')
else:
    print('(pdftotext not available for word-count check)')

print(f'\nWritten: {OUT}')
