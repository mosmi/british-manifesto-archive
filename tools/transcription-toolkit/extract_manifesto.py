#!/usr/bin/env python3
"""
extract_manifesto.py — Generalised manifesto PDF → Markdown extractor.

Handles:
  - Single-column and two-column PDF layouts (auto-detected)
  - Font-aware inline styling: bold (**...**) and italic (_..._)
  - Paragraph reconstruction from y-gap detection (gap ≥ PARA_GAP)
  - Running header stripping (top zone < HEADER_CUT pt)
  - Bullet point detection via Symbol font or bullet-character glyphs
  - Post-processing cleanup of style-marker artefacts
  - Merging of sentence continuation fragments split across columns
  - Per-page column split detection for mixed-layout PDFs

Usage:
    python extract_manifesto.py input.pdf [output.md]

    If output.md is omitted, the script writes to input-extracted.md
    in the same directory as the PDF.

Options (edit the CONFIG section below, or pass as arguments — see --help):
    --col-split N        Column split x-coordinate (default: auto-detect)
    --para-gap N         Min y-gap to start new paragraph (default: 18)
    --header-cut N       Strip text with top < N pt (default: 65)
    --skip-pages N,N     Comma-separated 0-indexed page numbers to skip
    --single-col         Force single-column mode (disable auto-detect)
    --title TITLE        Manifesto title for the H1 heading
    --no-dedup           Disable duplicate-paragraph removal (default: on)
    --strip-toc-numbers  Strip trailing page numbers from TOC lines (default: off)
    --no-colon-merge     Disable joining of trailing-colon intro lines to bullets (default: on)

For PDFs with mixed column layouts (different page types use different
gutter positions), use detect_page_col_split() as a col_split_fn:

    from extract_manifesto import extract_pdf, detect_page_col_split

    col_fn = lambda p: detect_page_col_split(
        p, standfirst_split=148, normal_split=202)
    paras = extract_pdf("manifesto.pdf", col_split_fn=col_fn)

See PROMPT.md → "Mixed-layout pages: per-page column detection" for
calibration guidance.

Developed through Alliance manifesto transcription work, 2025.
Draws on patterns from convert_manifesto.py (2005 Conservative),
extract_manifesto.py (2024 Labour), and Scottish Labour 2019 work.
"""

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber is not installed. Run: pip install pdfplumber --break-system-packages", file=sys.stderr)
    sys.exit(1)

try:
    import yaml as _yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


# ── Configuration defaults ──────────────────────────────────────────────────

Y_TOL       = 4     # y-bucket tolerance (pt) — groups chars on the same line
PARA_GAP    = 18    # min y-gap (pt) between bottom of one line-group and top of next
                    # to trigger a new paragraph. Within-para gaps are ~12–16pt,
                    # between-para gaps are ~20pt; 18 catches the latter cleanly.
HEADER_CUT  = 65    # strip chars with top < this value (pt) — removes running headers
COL_SPLIT   = None  # x-coordinate of column split; None = auto-detect
MIN_CHARS   = 2     # suppress lone chars / ligature artefacts shorter than this

DECO_CHARS = set('""″\u201c\u201d\u2018\u2019\'`')

BOLD_KEYWORDS   = ('Bold', 'Extra', 'Heavy', 'Black', 'SemiBold', 'Demi')
ITALIC_KEYWORDS = ('Italic', 'Oblique', 'Slanted')


# ── Utility ─────────────────────────────────────────────────────────────────

def bucket(top, tol=Y_TOL):
    return round(top / tol) * tol


def is_bold_font(fontname):
    return any(k in fontname for k in BOLD_KEYWORDS)


def is_italic_font(fontname):
    return any(k in fontname for k in ITALIC_KEYWORDS)


def is_symbol_font(fontname):
    return 'Symbol' in fontname or 'Wingding' in fontname or 'Zapf' in fontname


def is_meaningful(text):
    t = text.strip()
    if len(t) < MIN_CHARS:
        return False
    if all(ch in DECO_CHARS or ch.isspace() for ch in t):
        return False
    return True


def clean_ligatures(text):
    """Replace common PDF ligature characters with their plain equivalents."""
    return (text
            .replace('\ufb01', 'fi')
            .replace('\ufb02', 'fl')
            .replace('\ufb03', 'ffi')
            .replace('\ufb04', 'ffl')
            .replace('\u00ad', '')    # soft hyphen
            .replace('\u200b', ''))   # zero-width space


# ── Colored-box detection (page.rects) ──────────────────────────────────────

def get_colored_boxes(page, min_dim: float = 60) -> list:
    """
    Return a list of (x0, y_top, x1, y_bot) bounding boxes for every
    significant *colored* fill rectangle on the page, in screen coordinates
    (y measured from the top of the page).

    Why this matters
    ----------------
    PDFs with callout boxes, sidebars, or highlighted regions store their
    colored backgrounds as fill rectangles accessible via page.rects.  Words
    inside these boxes belong to the box, not the main body column flow.  If
    they remain in the main word pool they corrupt the x0 distribution that
    column-gap detection relies on — collapsing visible gutters and causing
    columns to interleave in the output.

    The fix is to call this function *before* column detection, partition the
    word list with separate_box_words(), run column detection only on the
    clean main-body pool, then process each box's words independently and
    append the results (separated by a horizontal rule or similar marker).

    Ordering note
    -------------
    Box separation must happen on the *raw* word list, before header/footer
    filtering.  Colored boxes can start near the very top of the page, so
    their opening lines would otherwise be incorrectly discarded by the
    running-header filter.  Filter main-body words and box words separately
    after partitioning:

        raw  = page.extract_words(extra_attrs=['fontname', 'size'], ...)
        boxes          = get_colored_boxes(page)
        main_raw, pools = separate_box_words(raw, boxes)
        main_body      = [w for w in main_raw  if passes_header_footer_filter(w)]
        box_pools      = [[w for w in pool if passes_footer_filter(w)]
                          for pool in pools]

    Color filtering rules
    ---------------------
    - Skip white / near-white fills (all RGB channels ≥ 0.95).
    - Skip very dark fills (RGB mean < 0.10) — decorative borders.
    - Skip rectangles smaller than min_dim pt in either dimension.
    - Accept everything else as a content box.

    Coordinate conversion
    ---------------------
    PDF rect coordinates use PDF space (y=0 at bottom).  This function
    converts them to screen space (y=0 at top) so they are directly
    comparable to word['top'] values from extract_words().

    Parameters
    ----------
    page    : pdfplumber Page object
    min_dim : minimum width *and* height (pt) to qualify as a content box
              (default 60 — filters out decorative rules and thin borders)

    Returns
    -------
    List of (x0, y_top, x1, y_bot) tuples in screen coordinates.
    Empty list if the page has no significant colored rects.

    Reference implementation
    ------------------------
    See scripts/extract_scot_libdem_2005.py for the worked example that
    motivated this utility: the 2005 Scottish Lib Dem manifesto has a
    full-page blue foreword box and a yellow "how we'll pay" box that
    together occupy the x-range of all three body columns on page 2,
    collapsing the 14 pt column gutters unless removed first.
    """
    page_h = float(page.height)
    boxes  = []

    for r in page.rects:
        fill = r.get('non_stroking_color')
        if not fill:
            continue

        # Normalise fill colour to (R, G, B) in [0, 1]
        if isinstance(fill, (int, float)):
            rv = gv = bv = float(fill)
        elif len(fill) == 3:
            rv, gv, bv = (float(c) for c in fill)
        elif len(fill) == 4:                    # CMYK → RGB
            c_, m_, y_, k_ = (float(c) for c in fill)
            rv = (1 - c_) * (1 - k_)
            gv = (1 - m_) * (1 - k_)
            bv = (1 - y_) * (1 - k_)
        else:
            continue

        if rv >= 0.95 and gv >= 0.95 and bv >= 0.95:   # white / near-white
            continue
        if (rv + gv + bv) / 3.0 < 0.10:                # near-black border
            continue

        # Convert PDF y-coords (bottom=0) → screen y-coords (top=0)
        y_top  = page_h - float(r['y1'])
        y_bot  = page_h - float(r['y0'])
        rect_w = float(r['x1']) - float(r['x0'])
        rect_h = y_bot - y_top

        if rect_w < min_dim or rect_h < min_dim:        # tiny decorative rule
            continue

        boxes.append((float(r['x0']), y_top, float(r['x1']), y_bot))

    return boxes


def separate_box_words(raw_words: list, boxes: list) -> tuple:
    """
    Partition a raw word list into main-body words and per-box word pools.

    Must be called on the RAW word list (before header/footer filtering) so
    that box content near the top of the page is not lost to the header-zone
    filter.  See get_colored_boxes() for the full rationale and usage pattern.

    Parameters
    ----------
    raw_words : list of word dicts from page.extract_words()
    boxes     : list of (x0, y_top, x1, y_bot) tuples from get_colored_boxes()

    Returns
    -------
    (main_words, box_pools) where:
      main_words : words not inside any colored box
      box_pools  : list[list], one word list per box (parallel to `boxes`)
    """
    box_pools  = [[] for _ in boxes]
    main_words = []

    for w in raw_words:
        wx, wy = float(w['x0']), float(w['top'])
        placed = False
        for i, (bx0, by0, bx1, by1) in enumerate(boxes):
            if bx0 <= wx <= bx1 and by0 <= wy <= by1:
                box_pools[i].append(w)
                placed = True
                break
        if not placed:
            main_words.append(w)

    return main_words, box_pools


# ── Layout detection ─────────────────────────────────────────────────────────

def detect_column_split(pages, sample_pages=5):
    """
    Auto-detect whether the PDF is two-column by analysing word x0 distribution.
    Returns a split x-coordinate if two-column is detected, or None for single-column.

    Method: collect x0 values of all words on sample pages; if there is a clear
    gap (bimodal distribution) in the x0 histogram, it's two-column.

    Note: this function searches the full page width for a gap, not just the central
    region. This handles asymmetric layouts where the gutter is well to one side of
    the page centre (e.g. a narrow decorative left column with gutter at x≈150 on an
    A4 page that is 595pt wide). A gap of ≥20pt anywhere in the x=50–(width-50) range
    is treated as a column boundary.

    Limitation: when the PDF has *mixed* layout types (some pages with gutter at x=148,
    others at x=202), the global histogram blends the two populations and the detected
    split may be wrong. Use detect_page_col_split() for per-page refinement in that case.
    """
    x0_values = []
    for page in pages[:sample_pages]:
        words = page.extract_words(keep_blank_chars=False)
        for w in words:
            if w['top'] > HEADER_CUT:
                x0_values.append(w['x0'])

    if not x0_values:
        return None

    # Build histogram with 10pt bins
    page_width = float(pages[0].width) if pages else 600
    bins = defaultdict(int)
    for x in x0_values:
        bins[round(x / 10) * 10] += 1

    # Search the full inner width (excluding 50pt margins) for a gap zone of ≥20pt
    # where word density drops to near zero. The first (leftmost) gap found wins,
    # since for two-column layouts the inter-column gutter is the dominant gap.
    search_range = range(50, int(page_width - 50), 10)
    gap_bins = [b for b in search_range if bins.get(b, 0) <= 2]

    # Require at least 20pt of continuous gap (2 consecutive 10pt bins)
    if len(gap_bins) >= 2:
        # Find the first contiguous run of gap bins
        run_start = gap_bins[0]
        run_bins  = [gap_bins[0]]
        for b in gap_bins[1:]:
            if b - run_bins[-1] <= 10:
                run_bins.append(b)
            else:
                if len(run_bins) >= 2:
                    break
                run_bins = [b]
        if len(run_bins) >= 2:
            split_x = round(sum(run_bins) / len(run_bins))
            return split_x

    return None  # single-column


def detect_page_col_split(page, header_cut=HEADER_CUT, footer_cut=None,
                          mid_lo=100, mid_hi=200,
                          standfirst_threshold=4,
                          standfirst_split=148, normal_split=202):
    """
    Per-page column split detection for PDFs with mixed layout types.

    Some PDFs use two distinct column layouts on different pages:
    - 'Standfirst' pages: narrow decorative left column (bold pull-quote, x≈34–140)
      + wide right body column starting at x≈150–167.  Gutter ≈ x=148.
    - Normal body pages: wide left body column (x≈34–190, often fully justified)
      + right column starting at x≈210.  Gutter ≈ x=202.

    Detection: count y-lines where the minimum text x falls in the band
    (mid_lo, mid_hi).  Standfirst pages score high (right body col starts at x≈153);
    normal pages score low (right col starts at x≥210).

    Parameters
    ----------
    page                : pdfplumber page object
    header_cut          : exclude chars with top < this value (pt)
    footer_cut          : exclude chars with top > this value (pt); defaults to
                          page.height - 30 if None
    mid_lo, mid_hi      : band for detecting standfirst-page right-column starts
                          (default 100–200pt, suitable for A4 two-column layouts)
    standfirst_threshold: min line count in band to classify as standfirst page
    standfirst_split    : col_split to use for standfirst pages
    normal_split        : col_split to use for normal body pages

    Returns
    -------
    int col_split value

    Usage
    -----
    Pass as col_split_fn to extract_page() to override the global split per-page:

        col_split_fn = lambda p: detect_page_col_split(
            p, standfirst_split=148, normal_split=202)
        paras = extract_page(page, col_split=None, col_split_fn=col_split_fn, ...)

    Calibration
    -----------
    1. Run the Step 0b x0 histogram on a standfirst page and a normal page
       separately to read off gutter positions.
    2. Call detect_page_col_split() on 10–15 pages and print results alongside
       a visual description to verify classification is correct.
    3. Adjust mid_lo/mid_hi and standfirst_threshold until all pages classify
       correctly.
    """
    if footer_cut is None:
        footer_cut = float(page.height) - 30

    chars_by_y = defaultdict(list)
    for c in page.chars:
        if c['text'].strip() and header_cut < c['top'] < footer_cut:
            chars_by_y[bucket(c['top'])].append(c)

    count = 0
    for chars in chars_by_y.values():
        min_x = min(c['x0'] for c in chars if c['text'].strip())
        if mid_lo < min_x < mid_hi:
            count += 1

    return standfirst_split if count >= standfirst_threshold else normal_split


# ── Font-aware word styling ──────────────────────────────────────────────────

def word_style(word, char_lookup):
    """
    Determine the dominant inline style of a word by examining its characters.
    char_lookup: dict keyed by y-bucket → list of char dicts for that line.
    Returns: 'bold', 'italic', 'bolditalic', or 'regular'.
    """
    wx0, wx1, wy = word['x0'], word['x1'], word['top']
    b = bucket(wy)
    matching = [c for c in char_lookup.get(b, [])
                if c['x0'] >= wx0 - 2 and c['x1'] <= wx1 + 2]
    # Fallback: check adjacent buckets if no match found
    if not matching:
        for delta in (-Y_TOL, Y_TOL):
            matching = [c for c in char_lookup.get(b + delta, [])
                        if c['x0'] >= wx0 - 2 and c['x1'] <= wx1 + 2]
            if matching:
                break

    if not matching:
        return 'regular'

    bold_count   = sum(1 for c in matching if is_bold_font(c.get('fontname', '')))
    italic_count = sum(1 for c in matching if is_italic_font(c.get('fontname', '')))
    n = len(matching)

    if bold_count >= n / 2 and italic_count >= n / 2:
        return 'bolditalic'
    if bold_count >= n / 2:
        return 'bold'
    if italic_count >= n / 2:
        return 'italic'
    return 'regular'


# ── Line extraction ──────────────────────────────────────────────────────────

def get_styled_lines(page, x0_min, x0_max, header_cut=HEADER_CUT, footer_cut=None):
    """
    Extract styled lines from a column region of a page.

    Returns a list of (top, line_text) tuples, where line_text contains
    inline **bold** and _italic_ markers as appropriate.

    x0_min, x0_max: column boundaries (x0_max can be float('inf') for full width)
    footer_cut: exclude words with top >= this value (pt); defaults to page height - 20
    """
    if footer_cut is None:
        footer_cut = float(page.height) - 20

    words = page.extract_words(keep_blank_chars=False)
    chars = page.chars

    # Build char lookup by y-bucket for style detection
    char_lookup = defaultdict(list)
    for c in chars:
        char_lookup[bucket(c['top'])].append(c)

    # Filter words to this column region, excluding header and footer zones
    col_words = [w for w in words
                 if w['top'] > header_cut
                 and w['top'] < footer_cut
                 and w['x0'] >= x0_min
                 and w['x0'] < x0_max]

    # Group words into lines by y-bucket
    line_map = defaultdict(list)
    for w in col_words:
        line_map[bucket(w['top'])].append(w)

    result = []
    for top in sorted(line_map.keys()):
        line_words = sorted(line_map[top], key=lambda w: w['x0'])

        # Detect bullet: Symbol font character at this y-level within the column
        has_bullet = any(
            is_symbol_font(c.get('fontname', ''))
            for c in char_lookup.get(top, [])
            if c['x0'] >= x0_min and c['x0'] < x0_max
        )

        # Build styled segments
        segments = []
        if has_bullet:
            segments.append(('bullet', '·'))

        current_style = None
        current_text  = ''

        for w in line_words:
            style = word_style(w, char_lookup)
            text  = clean_ligatures(w['text'])
            if style == current_style:
                current_text = (current_text + ' ' + text) if current_text else text
            else:
                if current_text:
                    segments.append((current_style, current_text))
                current_style = style
                current_text  = text

        if current_text:
            segments.append((current_style, current_text))

        # Render segments to line text
        line_text = ''
        for seg_style, seg_text in segments:
            if seg_style == 'bullet':
                line_text += '·'
            elif seg_style == 'bold':
                line_text += f'**{seg_text}**'
            elif seg_style == 'italic':
                line_text += f'_{seg_text}_'
            elif seg_style == 'bolditalic':
                line_text += f'**_{seg_text}_**'
            else:
                line_text += seg_text

        if line_text.strip():
            result.append((top, line_text.strip()))

    return result


# ── Paragraph assembly ───────────────────────────────────────────────────────

def merge_inline_markers(text):
    """
    Fix common inline marker artefacts produced by word-by-word processing:
    - Missing spaces at style boundaries: **word**next → **word** next
    - Trailing space inside markers: **word ** → **word**
    - Leading space inside markers: _ word_ → _word_
    - Adjacent same-style markers: **a** **b** → **a b**
    """
    # Fix trailing space in bold: **word **
    text = re.sub(r'\*\*([^*]+?)\s+\*\*', lambda m: f'**{m.group(1).rstrip()}**', text)
    # Fix leading space in italic: _ word_
    text = re.sub(r'_\s+([^_\n]+)_', r'_\1_', text)
    # Fix trailing space in italic: _word _
    text = re.sub(r'_([^_\n]+?)\s+_', lambda m: f'_{m.group(1).rstrip()}_', text)
    # Merge adjacent bold: **a** **b** → **a b**
    text = re.sub(r'\*\*([^*]+)\*\* \*\*([^*]+)\*\*', r'**\1 \2**', text)
    # Merge adjacent italic: _a_ _b_ → _a b_
    text = re.sub(r'_([^_]+)_ _([^_]+)_', r'_\1 \2_', text)
    # Add missing space: **word**NextWord → **word** NextWord
    text = re.sub(r'\*\*([^*]+)\*\*([^\s*_\n])', r'**\1** \2', text)
    # Add missing space: PrevWord**word** → PrevWord **word**
    text = re.sub(r'([^\s*_\n])\*\*([^*]+)\*\*', r'\1 **\2**', text)
    # Add missing space: _word_NextWord → _word_ NextWord
    text = re.sub(r'_([^_]+)_([^\s_*\n.,;:!?])', r'_\1_ \2', text)
    return text


def join_to_paragraphs(line_tops, para_gap=PARA_GAP, semibold_gap=None):
    """
    Join (top, text) lines into paragraphs using y-gap detection.
    Bullet lines and numbered lines always start a new paragraph.
    Returns a list of paragraph strings.

    semibold_gap: if set, use this larger gap threshold for **bold** lines.
    SemiBold/bold text often has wider inter-line spacing than body text
    (e.g. 16pt vs 12pt on A5 layouts), causing standfirst lines to fragment
    into separate bold paragraphs.  Set semibold_gap ≈ max_SemiBold_line_gap + 2pt.
    If None, body para_gap is used for all lines.
    """
    paras = []
    buf   = []
    prev_top = None

    def flush():
        if buf:
            combined = merge_inline_markers(' '.join(buf))
            paras.append(combined)
            buf.clear()

    for top, text in line_tops:
        s = text.strip()
        if not s:
            flush()
            continue

        is_bullet   = s.startswith('·')
        is_numbered = bool(re.match(r'^\d+\.', s))
        is_bold_line = s.startswith('**') and s.endswith('**')
        gap = (top - prev_top) if prev_top is not None else 0

        effective_gap = (semibold_gap if semibold_gap is not None and is_bold_line
                         else para_gap)

        if prev_top is not None and (gap >= effective_gap or is_bullet or is_numbered):
            flush()

        # Convert bullet glyph to markdown bullet prefix
        if is_bullet:
            s = '* ' + s[1:].strip()

        buf.append(s)
        prev_top = top

    flush()
    return paras


# ── Heading detection ─────────────────────────────────────────────────────────

def detect_headings(paragraphs, bold_only_threshold=10):
    """
    Convert paragraphs that are entirely bold (and short enough to be headings)
    into ### headings. Paragraphs that start with '## ' or '# ' are left as-is.

    bold_only_threshold: max word count for a bold-only paragraph to be treated
    as a heading (rather than a bold introductory paragraph).
    """
    result = []
    for p in paragraphs:
        # Skip if already a heading
        if p.startswith('#'):
            result.append(p)
            continue

        # Check if the entire paragraph is wrapped in **...**
        m = re.match(r'^\*\*(.+)\*\*$', p.strip())
        if m:
            inner = m.group(1).strip()
            word_count = len(inner.split())
            if word_count <= bold_only_threshold and not inner[0].islower():
                # Looks like a heading
                result.append(f'### {inner}')
                continue

        # Check for bullet starting with bold: * **Heading.** body text
        # — leave these as bullets, do not convert to headings
        result.append(p)

    return result


# ── Post-processing ──────────────────────────────────────────────────────────

def post_process(text):
    """
    Global post-processing passes on the full markdown text.
    Fixes artefacts that can only be caught at document level.
    """
    # Fix doubled bullet from Symbol detection + glyph conversion: "* · " → "* "
    text = text.replace('* · ', '* ')

    # Fix cross-page paragraph splits: word followed by stray page number
    # e.g. "strongly advocate a move 3\n\naway from..." → "strongly advocate a move away..."
    text = re.sub(r'(\w) (\d{1,2})\n\n([a-z])', r'\1 \3', text)

    # Fix hyphen-space artefacts from column-wrap line endings: "self- government" → "self-government"
    text = re.sub(r'(\w)- (\w)', r'\1-\2', text)

    # Collapse 3+ consecutive blank lines to 2
    text = re.sub(r'\n{4,}', '\n\n\n', text)

    # Clean up stray single characters on their own line (artefacts)
    text = re.sub(r'\n([a-zA-Z])\n', '\n', text)

    return text


def deduplicate_paragraphs(paragraphs: list, window: int = 20) -> list:
    """
    Remove duplicate paragraphs that appear within a sliding window.

    Catches the chapter-opener + body-page repetition pattern: when a chapter
    title page contains introductory body text that is then repeated verbatim
    on the next page, the same paragraph appears twice in quick succession.

    Headings are never deduplicated (a chapter title appearing at the top of
    multiple sections is intentional).  Short paragraphs (< 8 words) are also
    exempt, since brief phrases like "Dear friend," are legitimately repeated.

    Parameters
    ----------
    paragraphs : list of paragraph strings
    window     : number of recent paragraphs to check against (default 20)

    Returns a new list with within-window duplicates removed.
    Duplicate removal is reported to stdout.
    """
    if not paragraphs:
        return paragraphs

    result = []
    # ring buffer of recent (fingerprint, display_text) pairs
    recent_fps: list[str] = []
    removed = 0

    for para in paragraphs:
        stripped = para.strip()

        # Never deduplicate headings or very short paragraphs
        if stripped.startswith('#') or len(stripped.split()) < 8:
            result.append(para)
            continue

        # Fingerprint: first 100 chars, lowercase, whitespace-normalised,
        # markdown markers stripped so "**text**" and "text" match.
        fp_text = re.sub(r'[*_`]', '', stripped[:100])
        fp = re.sub(r'\s+', ' ', fp_text.lower().strip())

        if fp in recent_fps:
            removed += 1
            preview = stripped[:72].replace('\n', ' ')
            print(f"  [dedup] Removed duplicate paragraph: {preview!r}")
            continue

        result.append(para)
        recent_fps.append(fp)
        if len(recent_fps) > window:
            recent_fps.pop(0)

    if removed:
        print(f"  [dedup] {removed} duplicate paragraph(s) removed.")
    return result


def strip_toc_page_numbers(text: str) -> str:
    """
    Remove trailing page numbers from table-of-contents lines.

    TOC entries often extract with their PDF page numbers intact, e.g.:
      "Introduction by Nick Clegg & Willie Rennie 6"
      "1 Responsible finances: 14"
      "Economic policy ............. 42"

    This function strips the trailing number when the line is short enough
    to be a TOC entry (≤ 14 words of content) and ends with a 1–3 digit number
    optionally preceded by dots or spaces.

    Conservative by design: lines of 15+ words or ending in other content
    are never touched, so legitimate page references in body text are safe.
    """
    lines = text.split('\n')
    result = []
    # Match: non-greedy content ending on a non-digit char, then optional
    # dots/whitespace, then a 1-3 digit page number at end of line.
    # Using (.*?[^\d\s]) ensures the content group cannot absorb leading
    # digits of the trailing page number (e.g. stops "vision 1" absorbing
    # the leading "1" of page number "10").
    _toc_re = re.compile(r'^(.*?[^\d\s])\s*\.{0,10}\s+(\d{1,3})\s*$')
    for line in lines:
        m = _toc_re.match(line.rstrip())
        if m:
            content = m.group(1).strip()
            word_count = len(content.split())
            if 1 <= word_count <= 14:
                # Preserve original leading whitespace
                leading = line[:len(line) - len(line.lstrip())]
                result.append(leading + content)
                continue
        result.append(line)
    return '\n'.join(result)


def merge_colon_intro_paras(text: str) -> str:
    """
    Attach short trailing-colon intro paragraphs to the bullet list that follows.

    Manifestos frequently use the pattern:

        We will:

        * Invest in public services
        * Reform the tax system

    The extractor treats "We will:" as a standalone paragraph, which QA flags as
    a P4 orphan (< 4 words).  This function removes the blank line between a short
    trailing-colon paragraph (≤ 8 words) and an immediately following bullet list,
    producing:

        We will:
        * Invest in public services
        * Reform the tax system

    This keeps the colon intro as the natural lead-in sentence while eliminating
    the false-positive P4 warning.  Headings ending in ":" are left untouched.

    CLI: --no-colon-merge to disable.
    """
    # Pattern: paragraph ending in ":" (≤ 8 words, not a heading), blank line, bullet
    _colon_re = re.compile(
        r'(?m)^(?!#)'          # not a heading
        r'([^\n]{1,80}:)'      # trailing-colon line
        r'\n\n'                # blank separator
        r'(?=\* )',            # followed immediately by a bullet
    )
    return _colon_re.sub(r'\1\n', text)


_TERMINAL_PUNCT = set('.!?:;"\'»')


def merge_unfinished_paras(text):
    """
    Merge consecutive paragraphs where the preceding paragraph ends without
    terminal punctuation — indicating a sentence split at a column or line boundary.

    This complements merge_lowercase_orphans(): that function catches fragments
    starting with a lowercase word; this function catches fragments starting with
    an uppercase word (proper nouns, mid-sentence first-caps, and continuation
    phrases like "And" or "The").

    Guards:
    - Never merge after a heading (# / ## / ###)
    - Never merge after a bold block (ending with **) — standalone standfirst/
      pull-quote paragraphs must not absorb the body text that follows them
    - Never merge into a heading (# / ## / ###) or bullet (* )

    Typical usage: run after merge_lowercase_orphans, then run
    merge_lowercase_orphans again. The two are complementary.

    Example:
        "The First Minister has confirmed that the Welsh Government"  ← ends mid-sentence
        "will invest £1bn in green energy over the next decade."     ← continuation

    becomes:
        "The First Minister has confirmed that the Welsh Government will invest
         £1bn in green energy over the next decade."
    """
    paras = text.split('\n\n')
    result = []
    for para in paras:
        stripped = para.strip()
        if result and stripped:
            prev = result[-1].rstrip()
            prev_structural = (any(prev.startswith(p) for p in ('# ', '## ', '### '))
                               or prev.endswith('**'))
            curr_structural = any(stripped.startswith(p) for p in ('# ', '## ', '### ', '* '))
            if (not prev_structural
                    and not curr_structural
                    and prev
                    and prev[-1] not in _TERMINAL_PUNCT):
                result[-1] = prev + ' ' + stripped
                continue
        result.append(para)
    return '\n\n'.join(result)


def merge_lowercase_orphans(text):
    """
    Merge right-column sentence continuation fragments into the preceding paragraph.

    When a two-column layout splits a sentence at the column boundary, the right
    column begins a new "paragraph" with a lowercase word — but it is really a
    continuation of the sentence that ended in the left column.

    Detection: the preceding paragraph ends without terminal punctuation (.!?:;"')
    AND the next paragraph starts with a lowercase letter AND is not a heading,
    bullet, or italic/bold block.

    This is a conservative merge: it requires the absence of sentence-ending
    punctuation on the left side, so it will not accidentally join two separate
    sentences that happen to have an unusual paragraph break between them.

    Run twice to catch cases where the right-column fragment itself ends without
    terminal punctuation and is followed by a further continuation.

    Example:
        "the four-hour waiting time target in A&E"     ← left col, ends mid-sentence
        "has not been met for two years."               ← right col continuation

    becomes:
        "the four-hour waiting time target in A&E has not been met for two years."
    """
    TERMINAL = set('.!?:;\'"')
    paras = text.split('\n\n')
    result = []
    for para in paras:
        stripped = para.strip()
        if (result
                and stripped
                and stripped[0].islower()
                and not stripped.startswith('#')
                and not stripped.startswith('*')
                and not stripped.startswith('_')
                and not stripped.startswith('**')):
            prev = result[-1].rstrip()
            if prev and prev[-1] not in TERMINAL:
                result[-1] = prev + ' ' + stripped
                continue
        result.append(para)
    return '\n\n'.join(result)


# ── Heading classification by font size ─────────────────────────────────────

def get_line_max_size(page, top_bucket, x0_min, x0_max):
    """Return the maximum font size for characters on the given line."""
    chars_on_line = [
        c for c in page.chars
        if bucket(c['top']) == top_bucket
        and c['x0'] >= x0_min and c['x0'] < x0_max
    ]
    if not chars_on_line:
        return 0
    return max(c.get('size', 0) for c in chars_on_line)


# ── Page manifest ────────────────────────────────────────────────────────────

def load_manifest(manifest_path: str) -> dict:
    """
    Load a YAML page manifest and return a normalised dict.

    Manifest schema (all keys optional):

        title:       "Manifesto Title"          # overrides --title / PDF filename
        header_cut:  65                          # global Y_HEADER default
        footer_cut:  760                         # global Y_FOOTER default
        col_split:   304                         # global column split x
        skip_pages:  [0, 1, 5]                   # 0-indexed pages to skip
        pages:                                   # per-page overrides
          0:
            mode: full-width                     # 'full-width', 'single-col', 'skip',
                                                 # 'two-col', 'summary-box'
            footer_cut: null                     # null = page height - 20
            header_cut: 80
          18:
            mode: summary-box
          21:
            mode: full-width
            heading_level: 2                     # reserved; not yet used by extractor

    Recognised page modes:
      skip        — page is silently skipped
      full-width  — single-column extraction regardless of global col_split
      single-col  — alias for full-width
      summary-box — alias for full-width (sidebar detection is future work)
      two-col     — force two-column extraction using global col_split
    """
    if not _YAML_AVAILABLE:
        print("ERROR: PyYAML is not installed.  Run: pip install pyyaml --break-system-packages",
              file=sys.stderr)
        sys.exit(1)

    path = Path(manifest_path)
    if not path.exists():
        print(f"ERROR: manifest file not found: {manifest_path}", file=sys.stderr)
        sys.exit(1)

    with path.open(encoding='utf-8') as fh:
        raw = _yaml.safe_load(fh) or {}

    # Normalise pages dict: keys may be ints or strings
    raw_pages = raw.get('pages', {}) or {}
    pages = {}
    for k, v in raw_pages.items():
        pg_num = int(k)
        pages[pg_num] = v or {}

    # Normalise skip_pages: merge manifest list with any in pages dict
    skip_from_pages = {pg for pg, cfg in pages.items()
                       if (cfg.get('mode') or '').strip().lower() == 'skip'}
    skip_from_list  = set(raw.get('skip_pages', []) or [])
    skip_pages      = skip_from_pages | skip_from_list

    return {
        'title':      raw.get('title'),
        'header_cut': raw.get('header_cut'),
        'footer_cut': raw.get('footer_cut'),
        'col_split':  raw.get('col_split'),
        'skip_pages': skip_pages,
        'pages':      pages,
    }


def _page_overrides(manifest: dict | None, pg_num: int,
                    global_col_split, global_header_cut: float,
                    global_footer_cut: float | None) -> dict:
    """
    Return per-page extraction parameters after applying manifest overrides.

    Returns a dict with keys:
      skip        : bool
      col_split   : float or None  (None = single-column)
      header_cut  : float
      footer_cut  : float or None
    """
    defaults = {
        'skip':       False,
        'col_split':  global_col_split,
        'header_cut': global_header_cut,
        'footer_cut': global_footer_cut,
    }
    if manifest is None:
        return defaults

    cfg = manifest.get('pages', {}).get(pg_num, {}) or {}
    mode = (cfg.get('mode') or '').strip().lower()

    overrides = dict(defaults)

    if mode == 'skip':
        overrides['skip'] = True
        return overrides

    if mode in ('full-width', 'single-col', 'summary-box'):
        overrides['col_split'] = None   # force single-column

    if mode == 'two-col':
        # Keep whatever the global split is; just ensure it's used
        # (no change to col_split — the global value already applies)
        pass

    if 'header_cut' in cfg:
        v = cfg['header_cut']
        if v is not None:
            overrides['header_cut'] = float(v)

    if 'footer_cut' in cfg:
        v = cfg['footer_cut']
        overrides['footer_cut'] = float(v) if v is not None else None

    return overrides


# ── Main extraction ──────────────────────────────────────────────────────────

def extract_page(page, col_split, header_cut, para_gap, col_split_fn=None,
                 footer_cut=None):
    """
    Extract all styled paragraphs from a single page.
    Returns a list of paragraph strings.

    Parameters
    ----------
    col_split    : global column split x-coordinate, or None for single-column
    col_split_fn : optional callable(page) → int that overrides col_split for
                   this specific page.  Use detect_page_col_split() (with your
                   calibrated parameters) when the PDF has mixed layout types
                   (different pages use different gutter positions).

                   Example:
                       col_split_fn = lambda p: detect_page_col_split(
                           p, standfirst_split=148, normal_split=202)
    footer_cut   : exclude words with top >= this value (pt); defaults to
                   page height - 20 if None.  Per-page override from manifest.
    """
    page_width = float(page.width)

    # Per-page detection overrides the global split when provided
    effective_split = col_split_fn(page) if col_split_fn is not None else col_split

    if effective_split is None:
        # Single column: full page width
        lines = get_styled_lines(page, 0, page_width, header_cut, footer_cut)
        return join_to_paragraphs(lines, para_gap)
    else:
        # Two columns: process left then right
        left_lines  = get_styled_lines(page, 0,               effective_split, header_cut, footer_cut)
        right_lines = get_styled_lines(page, effective_split,  page_width,     header_cut, footer_cut)
        left_paras  = join_to_paragraphs(left_lines,  para_gap)
        right_paras = join_to_paragraphs(right_lines, para_gap)
        return left_paras + right_paras


def extract_pdf(pdf_path, col_split=None, para_gap=PARA_GAP, header_cut=HEADER_CUT,
                footer_cut=None, skip_pages=None, title=None, force_single_col=False,
                col_split_fn=None, collect_stats=False, manifest=None):
    """
    Extract a manifesto PDF to a list of markdown paragraph strings.

    Parameters
    ----------
    pdf_path        : path to the PDF file
    col_split       : x-coordinate of column split (None = auto-detect)
    para_gap        : minimum y-gap (pt) to trigger a new paragraph
    header_cut      : exclude chars with top < this value (pt)
    footer_cut      : exclude chars with top >= this value (pt); None = page
                      height - 20 (applied per page automatically)
    skip_pages      : set of 0-indexed page numbers to skip
    title           : manifesto title for the H1 heading
    force_single_col: if True, skip auto-detection and treat as single-column
    col_split_fn    : optional callable(page) → int for per-page column split
                      detection (overrides col_split when provided).
                      Use when the PDF has mixed layout types (different pages
                      use different gutter positions).  See detect_page_col_split().
    collect_stats   : if True, also return a list of per-page stat dicts suitable
                      for passing to anomaly_report().
    manifest        : optional dict returned by load_manifest().  Provides
                      per-page mode, header_cut, footer_cut overrides and an
                      additional skip_pages set.  CLI: --manifest path/to/manifest.yaml

    Returns
    -------
    If collect_stats is False (default): list of paragraph strings.
    If collect_stats is True: (list of paragraph strings, list of page stat dicts).
    """
    if skip_pages is None:
        skip_pages = set()

    # Merge skip_pages from manifest
    if manifest:
        skip_pages = skip_pages | manifest.get('skip_pages', set())
        # Manifest top-level values override only if the caller did not set them
        if manifest.get('col_split') is not None and col_split is None and not force_single_col:
            col_split = manifest['col_split']
        if manifest.get('header_cut') is not None:
            header_cut = manifest['header_cut']
        if manifest.get('footer_cut') is not None and footer_cut is None:
            footer_cut = manifest['footer_cut']

    with pdfplumber.open(pdf_path) as pdf:
        pages = pdf.pages
        print(f"PDF: {pdf_path}")
        print(f"Pages: {len(pages)}")
        if manifest:
            print(f"Manifest loaded  ({len(manifest.get('pages', {}))} per-page overrides, "
                  f"{len(skip_pages)} skip pages)")

        # Auto-detect column layout if not specified and no per-page fn given
        if col_split_fn is not None:
            print("Per-page column split detection enabled")
        elif not force_single_col and col_split is None:
            detected = detect_column_split(pages)
            if detected is not None:
                print(f"Auto-detected two-column layout; split at x={detected}")
                col_split = detected
            else:
                print("Auto-detected single-column layout")
        elif force_single_col:
            col_split = None
            print("Single-column mode (forced)")
        else:
            print(f"Column split: x={col_split}")

        all_paragraphs = []
        page_stats = []
        if title:
            all_paragraphs.append(f'# {title}')

        for page_num, page in enumerate(pages):
            if page_num in skip_pages:
                print(f"  Page {page_num:3d}: SKIPPED")
                continue

            # Resolve per-page overrides from manifest
            pg_overrides = _page_overrides(
                manifest, page_num,
                global_col_split  = col_split,
                global_header_cut = header_cut,
                global_footer_cut = footer_cut,
            )

            if pg_overrides['skip']:
                print(f"  Page {page_num:3d}: SKIPPED (manifest)")
                continue

            # col_split_fn takes priority over manifest mode override
            effective_split = pg_overrides['col_split'] if col_split_fn is None else None

            mode_label = ''
            if manifest and page_num in manifest.get('pages', {}):
                cfg  = manifest['pages'][page_num]
                mode = (cfg.get('mode') or '').lower()
                mode_label = f' [{mode}]'

            print(f"  Page {page_num:3d}: extracting...{mode_label}")
            paras = extract_page(
                page,
                col_split  = effective_split,
                header_cut = pg_overrides['header_cut'],
                para_gap   = para_gap,
                col_split_fn = col_split_fn if effective_split == col_split else None,
                footer_cut = pg_overrides['footer_cut'],
            )
            all_paragraphs.extend(paras)

            if collect_stats:
                wc = sum(len(p.split()) for p in paras)
                frag_count = sum(1 for p in paras if len(p.split()) <= 2)
                b_issues = bullet_sanity_check(paras)
                page_stats.append({
                    'page_num':      page_num,
                    'word_count':    wc,
                    'para_count':    len(paras),
                    'frag_count':    frag_count,
                    'bullet_issues': [(j, t) for j, t in b_issues],
                })

    if collect_stats:
        return all_paragraphs, page_stats
    return all_paragraphs


def paragraphs_to_markdown(paragraphs):
    """Join paragraphs into a markdown document string."""
    return '\n\n'.join(p for p in paragraphs if p.strip()) + '\n'


# ── Anomaly detection ────────────────────────────────────────────────────────

def anomaly_report(page_stats, threshold_low=0.4, threshold_frags=0.5):
    """
    Print a per-page anomaly report from stats collected during extraction.

    page_stats: list of dicts, one per extracted page, each with keys:
        page_num    : 0-indexed page number
        word_count  : number of words extracted from the page
        para_count  : number of paragraphs extracted from the page
        frag_count  : number of single-word paragraphs (fragment indicator)
        bullet_issues: list of (para_index, text) for suspicious bullet lines

    threshold_low  : flag pages whose word count is below this fraction of the
                     median page word count (default: 40%)
    threshold_frags: flag pages where the fraction of single-word paragraphs
                     exceeds this value (default: 50%)
    """
    if not page_stats:
        print("No per-page stats collected.")
        return

    counts = [s['word_count'] for s in page_stats if s['word_count'] > 0]
    if not counts:
        print("No word counts available.")
        return

    counts_sorted = sorted(counts)
    median_wc = counts_sorted[len(counts_sorted) // 2]
    low_cutoff = max(5, median_wc * threshold_low)

    print("\n" + "=" * 64)
    print("  Per-page anomaly report")
    print("=" * 64)
    print(f"  Median page word count : {median_wc}")
    print(f"  Low-count flag at      : < {low_cutoff:.0f} words")
    print()

    any_issues = False
    for s in page_stats:
        issues = []
        wc = s['word_count']
        pc = s['para_count']

        if 0 < wc < low_cutoff:
            issues.append(f"low word count ({wc})")

        if pc > 0:
            frag_count = s.get('frag_count', 0)
            if frag_count / pc > threshold_frags:
                issues.append(f"high fragment ratio ({frag_count}/{pc} paras are short)")

        bullet_issues = s.get('bullet_issues', [])
        if bullet_issues:
            issues.append(f"{len(bullet_issues)} bullet(s) may have clipped opening")

        if issues:
            any_issues = True
            print(f"  [p{s['page_num']:3d}]  ⚠  {'; '.join(issues)}")
            for _, btext in bullet_issues[:3]:  # show up to 3 examples per page
                preview = btext[:72].replace('\n', ' ')
                print(f"           → {preview!r}")

    if not any_issues:
        print("  No anomalies detected.")
    print("=" * 64 + "\n")


def bullet_sanity_check(paragraphs):
    """
    Scan paragraphs for bullet items that appear to start mid-sentence —
    a common sign that the opening phrase was clipped during extraction.

    A bullet is flagged if its body text (after stripping the '* ' prefix and
    any bold lead phrase) starts with a lowercase letter, suggesting it is a
    continuation rather than a fresh list item.

    Returns a list of (index, text) tuples for suspicious bullet paragraphs.
    """
    issues = []
    for i, para in enumerate(paragraphs):
        if not para.startswith('* '):
            continue
        body = para[2:].lstrip()
        # Strip a bold lead phrase if present: **Bold phrase.** rest of text
        body_stripped = re.sub(r'^\*\*[^*]+\*\*\s*', '', body)
        if body_stripped and body_stripped[0].islower():
            issues.append((i, para))
    return issues


# ── Verification ─────────────────────────────────────────────────────────────

def word_count(text):
    return len(text.split())


def verify(md_text, pdf_path):
    """Print word-count verification stats."""
    import subprocess
    md_words = word_count(md_text)
    print(f"\nMarkdown word count: {md_words:,}")

    try:
        result = subprocess.run(
            ['pdftotext', str(pdf_path), '-'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            pdf_words = word_count(result.stdout)
            print(f"PDF text word count: {pdf_words:,}")
            if pdf_words > 0:
                coverage = md_words / pdf_words * 100
                print(f"Coverage:            {coverage:.1f}%")
                if coverage < 95:
                    print("⚠️  WARNING: Coverage below 95% — some content may be missing.")
                elif coverage > 103:
                    print("ℹ️  Note: Slight overcount due to Markdown syntax tokens is normal.")
                else:
                    print("✓  Coverage looks good.")
        else:
            print("(pdftotext not available — install poppler-utils for PDF word count)")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("(pdftotext not available — install poppler-utils for PDF word count)")


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description='Extract a political party manifesto PDF to Markdown.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('input_pdf', help='Path to the input PDF file')
    parser.add_argument('output_md', nargs='?', help='Path to the output Markdown file (optional)')
    parser.add_argument('--col-split', type=float, default=None,
                        help='Column split x-coordinate (default: auto-detect)')
    parser.add_argument('--para-gap', type=float, default=PARA_GAP,
                        help=f'Min y-gap to start a new paragraph (default: {PARA_GAP})')
    parser.add_argument('--header-cut', type=float, default=HEADER_CUT,
                        help=f'Strip text with top < N pt (default: {HEADER_CUT})')
    parser.add_argument('--skip-pages', default='',
                        help='Comma-separated 0-indexed page numbers to skip (e.g. 0,1,5)')
    parser.add_argument('--single-col', action='store_true',
                        help='Force single-column mode')
    parser.add_argument('--title', default='',
                        help='Manifesto title for the H1 heading')
    parser.add_argument('--manifest', metavar='FILE',
                        help='YAML page manifest for per-page mode/footer/header overrides '
                             '(see load_manifest() docstring for schema)')
    parser.add_argument('--footer-cut', type=float, default=None,
                        help='Strip text with top >= N pt (default: page height - 20)')
    parser.add_argument('--no-verify', action='store_true',
                        help='Skip word-count verification')
    parser.add_argument('--anomaly-report', action='store_true',
                        help='Print a per-page anomaly report (low word counts, '
                             'high fragment ratios, bullets that may have clipped openings)')
    parser.add_argument('--no-dedup', action='store_true',
                        help='Disable automatic removal of duplicate paragraphs within a '
                             'sliding window (deduplication is on by default to catch '
                             'chapter-opener + body-page repetition)')
    parser.add_argument('--strip-toc-numbers', action='store_true',
                        help='Strip trailing page numbers from table-of-contents lines '
                             '(e.g. "Introduction 6" → "Introduction"). Safe for most '
                             'manifestos; off by default to avoid touching body text.')
    parser.add_argument('--no-colon-merge', action='store_true',
                        help='Disable automatic joining of short trailing-colon intro '
                             'paragraphs ("We will:") to the bullet list that follows. '
                             'Colon merging is on by default to suppress P4 false positives.')
    return parser.parse_args()


def main():
    args = parse_args()

    pdf_path = Path(args.input_pdf)
    if not pdf_path.exists():
        print(f"ERROR: File not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    if args.output_md:
        out_path = Path(args.output_md)
    else:
        out_path = pdf_path.with_name(pdf_path.stem + '-extracted.md')

    skip_pages = set()
    if args.skip_pages:
        for s in args.skip_pages.split(','):
            s = s.strip()
            if s.isdigit():
                skip_pages.add(int(s))

    # Load manifest (if provided); it may supply title, skip_pages, and per-page overrides
    manifest = None
    if args.manifest:
        manifest = load_manifest(args.manifest)

    # Manifest title takes precedence over --title; then fall back to filename
    title = (args.title
             or (manifest.get('title') if manifest else None)
             or pdf_path.stem.replace('-', ' ').replace('_', ' ').title())

    result = extract_pdf(
        pdf_path         = str(pdf_path),
        col_split        = args.col_split,
        para_gap         = args.para_gap,
        header_cut       = args.header_cut,
        footer_cut       = getattr(args, 'footer_cut', None),
        skip_pages       = skip_pages,
        title            = title,
        force_single_col = args.single_col,
        collect_stats    = args.anomaly_report,
        manifest         = manifest,
    )

    if args.anomaly_report:
        paragraphs, page_stats = result
    else:
        paragraphs = result
        page_stats = []

    # Apply heading detection heuristics
    paragraphs = detect_headings(paragraphs)

    # Remove duplicate paragraphs (chapter-opener + body-page repetition pattern).
    # Use --no-dedup to skip this step if legitimate repetition is expected.
    if not args.no_dedup:
        paragraphs = deduplicate_paragraphs(paragraphs)

    # Join to markdown and post-process
    md_text = paragraphs_to_markdown(paragraphs)
    md_text = post_process(md_text)

    # Optionally strip trailing page numbers from TOC lines
    if args.strip_toc_numbers:
        md_text = strip_toc_page_numbers(md_text)

    # Merge sentence continuation fragments (two complementary passes):
    #   merge_lowercase_orphans: catches fragments starting with a lowercase word
    #   merge_unfinished_paras:  catches any fragment where the previous para
    #                            ends without terminal punctuation
    md_text = merge_lowercase_orphans(md_text)
    md_text = merge_unfinished_paras(md_text)
    md_text = merge_lowercase_orphans(md_text)

    # Attach short trailing-colon intro paragraphs ("We will:") to the bullet
    # list that follows, eliminating spurious P4 orphan warnings.
    if not args.no_colon_merge:
        md_text = merge_colon_intro_paras(md_text)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md_text, encoding='utf-8')
    print(f"\nWritten: {out_path}")

    if not args.no_verify:
        verify(md_text, pdf_path)

    if args.anomaly_report:
        anomaly_report(page_stats)

    # Document-level bullet sanity check (always run — cheap and high-value)
    final_paras = md_text.split('\n\n')
    clipped = bullet_sanity_check(final_paras)
    if clipped:
        print(f"\n⚠  Bullet sanity check: {len(clipped)} bullet(s) may have clipped openings")
        print("   (body text starts with a lowercase letter — check the PDF page image)")
        for _, btext in clipped[:5]:
            preview = btext[:80].replace('\n', ' ')
            print(f"   → {preview!r}")
        if len(clipped) > 5:
            print(f"   ... and {len(clipped) - 5} more. Run --anomaly-report for page-level detail.")
    else:
        print("\n✓  Bullet sanity check passed.")

    print("\nDone.")
    print("Review the output and correct any missed sections, heading levels, or styling.")
    print("Aim for ≥95% word coverage vs. the PDF.")


if __name__ == '__main__':
    main()
