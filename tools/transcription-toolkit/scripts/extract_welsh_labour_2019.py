#!/usr/bin/env python3
"""
Welsh Labour 2019 manifesto extractor.
420×595pt A5 portrait, two-column facing-pages layout.
Result: 31,060 words, 98.3% coverage.

Two layout variants per page:
  - FOREWORD pages  (min body x ≈ 34):  col_split = 200, right col starts x ≈ 210
  - MAIN pages      (min body x ≈ 51):  col_split = 217, right col starts x ≈ 227

Fonts:
  - AcuminProCond-Black sz=36-54 → ## chapter title  (chapter opener pages)
  - AcuminProCond-Black sz=24    → ### section heading
  - AcuminProCond-Black sz=16    → SKIP (page-number sub-section list in chapter opener)
  - AcuminProCond-Black sz=6     → SKIP (footer: "SECTION NAME  PAGE_NUM")
  - LotaGrotesqueAlt3-SemiBold   → **bold** body text (standfirst or emphasis)
  - LotaGrotesqueAlt3-Light      → regular body text
  - bullet char '•' at word start → '* '

Key techniques used (see PROMPT.md for detailed explanations):
  - col_split_for_page(): auto-detects MAIN vs FOREWORD layout from min body x
  - standfirst_info(): detects narrow-strip standfirst rows using:
      (a) SemiBold chars must START and END within the narrow strip (x1 < sb_edge)
      (b) Light body text must start ≤30px past sf_split (full-width standfirst
          detected when Light text starts far to the right — use regular_split)
  - extract_standard_page(): dual col_split per y-row — standfirst rows use
      sf_split, non-standfirst rows use regular_split
  - words_to_paras(): effective_gap=20 for SemiBold (wider line-gap than body)
  - merge_unfinished_paras(): terminal-punctuation-based paragraph merging
"""

import re, sys
from collections import defaultdict
from pathlib import Path

import pdfplumber

PDF         = 'Welsh-Labour-Manifesto-2019.pdf'  # adjust to your PDF path
OUT         = '2019-welsh-labour-manifesto.md'      # adjust to your output path
HEADER_CUT  = 27    # content starts at y≈32; nothing above 27 to keep
FOOTER_CUT  = 562   # footer at y=576; exclude
PARA_GAP    = 14    # A5 tight body leading; within-para gaps ≈8-12, between ≈16+
SKIP_PAGES  = {0, 1, 2, 3, 107}
Y_TOL       = 4

# ── Helpers ────────────────────────────────────────────────────────────────────

def bucket(top, tol=Y_TOL):
    return round(top / tol) * tol

def base_font(fn):
    return fn.split('+')[-1]

def clean(text):
    return (text.replace('\ufb01', 'fi').replace('\ufb02', 'fl')
                .replace('\ufb03', 'ffi').replace('\ufb04', 'ffl')
                .replace('\u00ad', '').replace('\u200b', ''))

def col_split_for_page(page):
    """Return the regular (non-standfirst) column split for a page.
      MAIN pages    (body min_x ≈ 51): 217
      FOREWORD pages (body min_x ≈ 34): 200
    Standfirst handling is done per-row in extract_standard_page().
    """
    body_chars = [c for c in page.chars
                  if (c['text'].strip()
                      and HEADER_CUT < c['top'] < FOOTER_CUT
                      and 'AcuminProCond' not in base_font(c['fontname']))]
    if not body_chars:
        return 217
    min_x = min(c['x0'] for c in body_chars)
    return 217 if min_x >= 48 else 200

def standfirst_info(page):
    """Detect rows that have a NARROW SemiBold standfirst column.

    A true standfirst column occupies a narrow left strip: the SemiBold text
    both starts AND ends within the strip (x1 < sb_strip + 20).  Bold text
    that is just the regular left-column body content will have x1 >> sb_strip.

    Returns (sf_y_rows, sf_split):
      sf_y_rows  – set of y-buckets where a narrow standfirst was detected
      sf_split   – x-boundary separating standfirst from body on those rows
                   (None if no narrow standfirst detected)

    Boundaries (derived from actual char positions):
      FOREWORD standfirst: SemiBold ends at x≈133, body starts at x≈153 → split 148
      MAIN standfirst:     SemiBold ends at x≈154, body starts at x≈167 → split 161
    """
    body_chars = [c for c in page.chars
                  if (c['text'].strip()
                      and HEADER_CUT < c['top'] < FOOTER_CUT
                      and 'AcuminProCond' not in base_font(c['fontname']))]
    if not body_chars:
        return set(), None

    min_x = min(c['x0'] for c in body_chars)
    is_main  = (min_x >= 48)
    sb_strip = 160 if is_main else 140   # SemiBold STARTS within this x
    sb_edge  = sb_strip + 20             # SemiBold must also END within this x
    sf_split = 161 if is_main else 148   # col boundary for standfirst rows

    # Group by y-row
    by_y = defaultdict(list)
    for c in body_chars:
        by_y[bucket(c['top'])].append(c)

    # A narrow-standfirst row has SemiBold chars that both start AND end within
    # the narrow left strip (x0 < sb_strip, x1 < sb_edge).
    sf_rows = set()
    for y, chars in by_y.items():
        sb_chars = [c for c in chars
                    if 'SemiBold' in base_font(c['fontname']) and c['x0'] < sb_strip]
        if sb_chars and max(c['x1'] for c in sb_chars) < sb_edge:
            sf_rows.add(y)

    if not sf_rows:
        return set(), None

    # Sanity-check: if the Light (non-SemiBold) body text on standfirst rows
    # starts significantly further right than sf_split, the standfirst fills the
    # full left column rather than a narrow strip. Fall back to regular_split.
    light_on_sf_rows = [c for c in body_chars
                        if ('SemiBold' not in base_font(c['fontname'])
                            and bucket(c['top']) in sf_rows)]
    if light_on_sf_rows:
        body_start_x = min(c['x0'] for c in light_on_sf_rows)
        if body_start_x > sf_split + 30:   # large gap → full-width left standfirst
            return set(), None

    return sf_rows, sf_split

# ── Heading extraction ────────────────────────────────────────────────────────

def extract_headings(page):
    """Return sorted list of (top, col, text) for AcuminProCond-Black sz=24 headings.
    Uses extract_words() for text reconstruction (proper word spacing).
    col = 'left' if x0 < col_split, else 'right'."""
    col_split = col_split_for_page(page)

    # Step 1: find y-rows containing sz=24 AcuminProCond-Black chars
    heading_y_rows = set()
    for c in page.chars:
        fn = base_font(c['fontname'])
        if (c['text'].strip()
                and 'AcuminProCond-Black' in fn
                and round(c['size']) == 24
                and HEADER_CUT < c['top'] < FOOTER_CUT):
            heading_y_rows.add(bucket(c['top']))

    if not heading_y_rows:
        return []

    # Step 2: get extract_words() tokens on those y-rows
    all_words = page.extract_words(keep_blank_chars=False)
    words_by_y = defaultdict(list)
    for w in all_words:
        y = bucket(w['top'])
        if y in heading_y_rows and HEADER_CUT < w['top'] < FOOTER_CUT:
            words_by_y[y].append(w)

    # Step 3: assemble text per row
    result = []
    for y in sorted(words_by_y.keys()):
        words = sorted(words_by_y[y], key=lambda w: w['x0'])
        text = clean(' '.join(w['text'] for w in words)).strip()
        col = 'left' if words[0]['x0'] < col_split else 'right'
        result.append((y, col, text))
    return result

# ── Word → paragraph assembly ─────────────────────────────────────────────────

def words_to_paras(words, para_gap=PARA_GAP):
    """
    Assemble extract_words() results into paragraph strings.

    SemiBold text is emitted as **...**. Font-stream changes force a paragraph
    break (prevents interleaving of standfirst and body text being merged together).
    Bullet paragraphs are always split on the bullet char.
    """
    if not words:
        return []
    words = sorted(words, key=lambda w: (bucket(w['top']), w['x0']))

    paras = []
    buf   = []
    buf_stream = None
    prev_top   = None

    def flush():
        nonlocal buf, buf_stream
        if not buf:
            return
        text = clean(' '.join(w['text'] for w in buf))
        text = text.strip()
        if not text:
            buf = []; buf_stream = None; return
        if text.startswith('•'):
            text = '* ' + text[1:].strip()
            paras.append(text)
        elif buf_stream == 'semibold':
            paras.append(f'**{text}**')
        else:
            paras.append(text)
        buf = []
        buf_stream = None

    for w in words:
        top    = bucket(w['top'])
        fn     = base_font(w.get('fontname', ''))
        stream = 'semibold' if 'SemiBold' in fn else 'light'
        text   = w['text']

        is_bullet = text.startswith('•')
        gap = (top - prev_top) if prev_top is not None else 0

        # New paragraph on: y-gap (larger threshold for SemiBold to keep
        # standfirst lines joined), font-stream change, or bullet
        effective_gap = 20 if stream == 'semibold' else para_gap
        if prev_top is not None and (gap >= effective_gap or stream != buf_stream or is_bullet):
            flush()

        buf.append(w)
        buf_stream = stream
        prev_top   = top

    flush()
    return [p for p in paras if p.strip()]

# ── Page extractors ───────────────────────────────────────────────────────────

def extract_chapter_opener(page):
    """Chapter opener pages (max sz ≥ 36): merge large title lines → ## heading.
    Uses extract_words() for text reconstruction (proper word spacing).
    Skip the sz=16 sub-section page-number list and sz=6 footer."""
    # Step 1: find y-rows with sz≥36 AcuminProCond-Black chars
    title_y_rows = set()
    for c in page.chars:
        fn = base_font(c['fontname'])
        if (c['text'].strip()
                and 'AcuminProCond-Black' in fn
                and c['size'] >= 36
                and HEADER_CUT < c['top'] < FOOTER_CUT):
            title_y_rows.add(bucket(c['top']))

    if not title_y_rows:
        return []

    # Step 2: get words on those y-rows
    all_words = page.extract_words(keep_blank_chars=False)
    words_by_y = defaultdict(list)
    for w in all_words:
        y = bucket(w['top'])
        if y in title_y_rows and HEADER_CUT < w['top'] < FOOTER_CUT:
            words_by_y[y].append(w)

    # Step 3: assemble title lines in y-order
    title_lines = []
    for y in sorted(words_by_y.keys()):
        words = sorted(words_by_y[y], key=lambda w: w['x0'])
        text = clean(' '.join(w['text'] for w in words)).strip()
        if text:
            title_lines.append(text)

    if title_lines:
        return [f'## {" ".join(title_lines)}']
    return []

def extract_standard_page(page):
    """Normal two-column body page, with per-row standfirst handling.

    Strategy:
    1. Extract sz=24 headings (as ### anchors).
    2. Detect standfirst rows (y-rows with dense SemiBold in narrow left strip).
    3. Standfirst rows → split at the narrow standfirst boundary (148/161):
         left  → bold standfirst paragraphs
         right → body text alongside standfirst
    4. Non-standfirst rows → split at the regular boundary (200/217):
         left  → left body column
         right → right body column
    """
    regular_split = col_split_for_page(page)
    sf_rows, sf_split = standfirst_info(page)
    page_width = float(page.width)

    headings   = extract_headings(page)
    heading_ys = {bucket(y) for y, _, _ in headings}

    all_words = page.extract_words(keep_blank_chars=False, extra_attrs=['fontname'])
    body_words = [w for w in all_words
                  if HEADER_CUT < w['top'] < FOOTER_CUT
                  and bucket(w['top']) not in heading_ys]

    result = []
    for _, col, text in sorted(headings, key=lambda x: x[0]):
        result.append(f'### {text}')

    if sf_rows and sf_split is not None:
        # Rows that contain standfirst: use narrow split
        sf_words  = [w for w in body_words if bucket(w['top']) in sf_rows]
        reg_words = [w for w in body_words if bucket(w['top']) not in sf_rows]

        sf_left  = words_to_paras([w for w in sf_words if w['x0'] <  sf_split])
        sf_right = words_to_paras([w for w in sf_words if w['x0'] >= sf_split])
        result.extend(sf_left)
        result.extend(sf_right)
    else:
        reg_words = body_words

    # Regular rows: use standard two-column split
    reg_left  = words_to_paras([w for w in reg_words if w['x0'] <  regular_split])
    reg_right = words_to_paras([w for w in reg_words if w['x0'] >= regular_split])
    result.extend(reg_left)
    result.extend(reg_right)
    return result

# ── Main ──────────────────────────────────────────────────────────────────────

all_paras = ['# Standing Up for Wales: The Welsh Labour Manifesto 2019']

with pdfplumber.open(PDF) as pdf:
    print(f"Total pages: {len(pdf.pages)}")
    for pg_num, page in enumerate(pdf.pages):
        if pg_num in SKIP_PAGES:
            print(f"  pg {pg_num:3d}: SKIP")
            continue

        max_sz = max((c['size'] for c in page.chars if c['text'].strip()), default=0)
        if max_sz >= 36:
            paras = extract_chapter_opener(page)
            label = 'CHAPTER OPENER'
        else:
            paras = extract_standard_page(page)
            label = f'std col={col_split_for_page(page)}'

        all_paras.extend(paras)
        print(f"  pg {pg_num:3d}: {label:20s}  {len(paras):3d} paras")

# ── Post-processing ────────────────────────────────────────────────────────────

md = '\n\n'.join(p for p in all_paras if p.strip()) + '\n'

# Merge paragraphs where the previous paragraph ends without terminal punctuation
# (line-break artefacts where a sentence was split across PDF lines)
TERMINAL_PUNCT = set('.!?:;"\'»')

def merge_unfinished_paras(text):
    paras = text.split('\n\n')
    result = []
    for para in paras:
        stripped = para.strip()
        if result and stripped:
            prev = result[-1].rstrip()
            prev_is_structural = (any(prev.startswith(p) for p in ('# ', '## ', '### '))
                                  or prev.endswith('**'))   # don't merge after bold block
            curr_is_structural = any(stripped.startswith(p) for p in ('# ', '## ', '### ', '* '))
            if (not prev_is_structural
                    and not curr_is_structural
                    and prev and prev[-1] not in TERMINAL_PUNCT):
                result[-1] = prev + ' ' + stripped
                continue
        result.append(para)
    return '\n\n'.join(result)

md = merge_unfinished_paras(md)

# ── Heading fixes ─────────────────────────────────────────────────────────────
# Merge cross-column split headings (heading spans both columns → two ### lines)
md = md.replace('### COMMUNITIES AND\n\n### LOCAL GOVERNMENT\n\n',
                '### COMMUNITIES AND LOCAL GOVERNMENT\n\n')
md = md.replace('### DIGITAL, CULTURE,\n\n### MEDIA AND SPORT\n\n',
                '### DIGITAL, CULTURE, MEDIA AND SPORT\n\n')
md = md.replace('### INTERNATIONAL SOLIDARITY\n\n### AND SOCIAL JUSTICE\n\n',
                '### INTERNATIONAL SOLIDARITY AND SOCIAL JUSTICE\n\n')
# Remove duplicate sub-heading immediately following the ## version
md = md.replace('## THE FINAL SAY ON BREXIT\n\n### THE FINAL SAY ON BREXIT\n\n',
                '## THE FINAL SAY ON BREXIT\n\n')
md = md.replace('## A NEW INTERNATIONALISM\n\n### A NEW INTERNATIONALISM\n\n',
                '## A NEW INTERNATIONALISM\n\n')

# Fix bold artefacts: **word  **  →  **word**  (no newline crossing)
md = re.sub(r'\*\*([^*\n]+?)\s+\*\*', lambda m: f'**{m.group(1).rstrip()}**', md)
# Merge adjacent bold: **a** **b** → **a b**
md = re.sub(r'\*\*([^*\n]+)\*\* \*\*([^*\n]+)\*\*', r'**\1 \2**', md)
# Fix hyphen-space: "self- government" → "self-government"
md = re.sub(r'(\w)- (\w)', r'\1-\2', md)
# Collapse 3+ blank lines
md = re.sub(r'\n{4,}', '\n\n\n', md)

Path(OUT).write_text(md, encoding='utf-8')

import subprocess
wc_md = len(md.split())
print(f"\nMarkdown word count: {wc_md:,}")
res = subprocess.run(['pdftotext', PDF, '-'], capture_output=True, text=True, timeout=30)
if res.returncode == 0:
    wc_pdf = len(res.stdout.split())
    print(f"PDF word count (pdftotext): {wc_pdf:,}")
    print(f"Coverage: {wc_md / wc_pdf * 100:.1f}%")
print(f"\nWritten: {OUT}")
