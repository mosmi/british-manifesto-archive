#!/usr/bin/env python3
"""
profile_pdf.py — Preflight layout profiler for manifesto PDFs.

Run this BEFORE writing an extraction script.  It analyses the PDF and
prints a per-page report covering:

  • Page count, dimensions, and rotation
  • Word-count baseline from pdftotext (if available)
  • Per-page word count from pdfplumber and a suggested reading mode
    (single-col, two-col, full-width, or manual-review)
  • Likely blank / logo-only pages
  • Repeated text near page edges → probable running header / footer strings
  • x-coordinate histogram (25pt buckets) of left-word-edges on body pages,
    to help identify column split positions
  • Suggested Y_HEADER and Y_FOOTER constants
  • Font inventory: distinct font names and their size range

Usage:
    python profile_pdf.py manifesto.pdf
    python profile_pdf.py manifesto.pdf --sample-pages 5,10,15
    python profile_pdf.py manifesto.pdf --json > profile.json

Options:
    --sample-pages N,N,...   Comma-separated 0-indexed page numbers used for
                             x-histogram and font inventory (default: auto,
                             picks 3 evenly-spaced body pages)
    --header-cut N           Initial guess for header zone top (default: 80)
    --footer-cut N           Initial guess for footer zone top (default: 760)
    --json                   Output machine-readable JSON instead of text
    --quiet                  Suppress per-page table; only print summary + hints
"""

import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'lib'))

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber not installed.  Run: pip install pdfplumber --break-system-packages",
          file=sys.stderr)
    sys.exit(1)


# ── Constants ─────────────────────────────────────────────────────────────────

BUCKET_SIZE   = 25      # pt — x-histogram bucket width
MIN_WORD_LEN  = 1       # minimum text length to count as a word
BLANK_THRESH  = 5       # pages with ≤ this many words are "blank/logo"
REPEAT_THRESH = 0.60    # fraction of pages a string must appear on to be "repeated"
COL_GAP_MIN   = 30      # minimum gap (pt) between x-clusters to call it multi-column


# ── Utilities ─────────────────────────────────────────────────────────────────

def pdftotext_wc(pdf_path: str) -> int | None:
    """Return word count from pdftotext, or None if unavailable."""
    try:
        res = subprocess.run(
            ['pdftotext', pdf_path, '-'],
            capture_output=True, text=True, timeout=60
        )
        if res.returncode == 0:
            return len(res.stdout.split())
    except Exception:
        pass
    return None


def get_words(page, header_cut: float, footer_cut: float) -> list:
    """Extract non-header/footer words with size and fontname."""
    try:
        words = page.extract_words(
            keep_blank_chars=False,
            y_tolerance=3,
            x_tolerance=3,
            extra_attrs=['size', 'fontname'],
        )
    except Exception:
        return []
    return [
        w for w in words
        if w['top'] > header_cut
        and w['top'] < footer_cut
        and len(w['text'].strip()) >= MIN_WORD_LEN
        and '\x04' not in w['text']
    ]


def get_colored_rect_count(page, min_dim: float = 60) -> int:
    """
    Count significant colored fill rectangles on a page.

    Returns the number of rects that are non-white, non-black, and large
    enough to be content boxes (width and height both ≥ min_dim pt).
    A non-zero count is a strong signal that rect-based box separation
    (get_colored_boxes / separate_box_words in extract_manifesto.py) will
    be needed to prevent box words from corrupting column detection.
    """
    page_h = float(page.height)
    count  = 0
    for r in page.rects:
        fill = r.get('non_stroking_color')
        if not fill:
            continue
        if isinstance(fill, (int, float)):
            rv = gv = bv = float(fill)
        elif len(fill) == 3:
            rv, gv, bv = (float(c) for c in fill)
        elif len(fill) == 4:
            c_, m_, y_, k_ = (float(c) for c in fill)
            rv = (1 - c_) * (1 - k_); gv = (1 - m_) * (1 - k_); bv = (1 - y_) * (1 - k_)
        else:
            continue
        if rv >= 0.95 and gv >= 0.95 and bv >= 0.95:
            continue
        if (rv + gv + bv) / 3.0 < 0.10:
            continue
        y_top  = page_h - float(r['y1'])
        y_bot  = page_h - float(r['y0'])
        if (float(r['x1']) - float(r['x0'])) >= min_dim and (y_bot - y_top) >= min_dim:
            count += 1
    return count


def get_edge_words(page, zone_height: float = 50) -> tuple[list, list]:
    """Return words in the top and bottom edge zones (possible headers/footers)."""
    try:
        all_words = page.extract_words(keep_blank_chars=False, y_tolerance=3, x_tolerance=3)
    except Exception:
        return [], []
    h = page.height
    top_words  = [w for w in all_words if w['top'] <= zone_height]
    bot_words  = [w for w in all_words if w['top'] >= h - zone_height]
    return top_words, bot_words


def x_histogram(words: list) -> dict[int, int]:
    """Build a histogram of left-word-edge x0 values in BUCKET_SIZE pt buckets."""
    hist: dict[int, int] = defaultdict(int)
    for w in words:
        bucket = int(w['x0'] // BUCKET_SIZE) * BUCKET_SIZE
        hist[bucket] += 1
    return dict(hist)


def detect_col_split(words: list, page_width: float) -> str:
    """
    Guess the reading mode from the x0 distribution of body words.

    Returns one of: 'single-col', 'two-col', 'three-col', 'full-width', 'sparse'
    """
    if len(words) < 10:
        return 'sparse'

    # Build a density histogram in 10pt buckets
    hist: Counter = Counter()
    for w in words:
        b = int(w['x0'] // 10) * 10
        hist[b] += 1

    # Find the leftmost x0 of any word
    x0_min = min(w['x0'] for w in words)
    x0_max = max(w['x1'] for w in words)
    span   = x0_max - x0_min

    # Count how many words start in the left vs right half
    mid = page_width / 2
    left_count  = sum(1 for w in words if w['x0'] < mid)
    right_count = sum(1 for w in words if w['x0'] >= mid)

    if right_count < 0.15 * left_count:
        return 'single-col'

    # Look for a gap in the x0 histogram between the two columns
    # Scan for a contiguous run of empty 10pt buckets in the middle region
    low  = int(page_width * 0.3 // 10) * 10
    high = int(page_width * 0.7 // 10) * 10
    gap_start = gap_len = best_gap = best_gap_x = 0

    for x in range(low, high, 10):
        if hist.get(x, 0) == 0:
            if gap_len == 0:
                gap_start = x
            gap_len += 10
            if gap_len > best_gap:
                best_gap   = gap_len
                best_gap_x = gap_start + gap_len // 2
        else:
            gap_len = 0

    if best_gap >= COL_GAP_MIN:
        # Look for a second gap (three-col)
        gap2_len = gap2_x = 0
        scan_from = best_gap_x + int(page_width * 0.2)
        for x in range(scan_from, high + int(page_width * 0.1), 10):
            if hist.get(x, 0) == 0:
                gap2_len += 10
                if gap2_len == 10:
                    gap2_x = x
                if gap2_len >= COL_GAP_MIN:
                    return f'three-col  (splits≈{best_gap_x:.0f}, {gap2_x + gap2_len//2:.0f})'
            else:
                gap2_len = 0
        return f'two-col  (split≈{best_gap_x:.0f})'

    return 'single-col'


# ── Layout class detection ────────────────────────────────────────────────────

# A3 landscape: ≈ 1190×842pt.  Allow ±20pt tolerance.
A3_W_MIN, A3_W_MAX = 1150, 1220
A3_H_MIN, A3_H_MAX = 800,  880

# Standard rotations that indicate a landscape-printed spread
SPREAD_ROTATIONS = {90, 270}


def classify_layout(pages_data: list[dict]) -> dict:
    """
    Classify the overall PDF layout class.

    Returns a dict with keys:
        layout_class          : str  — e.g. 'rotated_spread', 'standard', 'landscape'
        physical_pages        : int
        logical_pages_estimate: int
        rotation              : int | None   — dominant rotation angle (0/90/180/270)
        page_size_class       : str  — 'A4', 'A3', 'letter', 'other'
        warnings              : list[str]
    """
    if not pages_data:
        return {
            'layout_class': 'unknown',
            'physical_pages': 0,
            'logical_pages_estimate': 0,
            'rotation': None,
            'page_size_class': 'unknown',
            'warnings': [],
        }

    physical = len(pages_data)
    rotations: Counter = Counter()
    size_classes: Counter = Counter()

    for rec in pages_data:
        w = rec.get('width', 0)
        h = rec.get('height', 0)
        rot = rec.get('rotation', 0) or 0
        rotations[rot] += 1

        # Classify page size — check both orientations (w may be swapped with h)
        w_norm, h_norm = (min(w, h), max(w, h))
        if A3_W_MIN <= h_norm <= A3_W_MAX and A3_H_MIN <= w_norm <= A3_H_MAX:
            size_classes['A3'] += 1
        elif 570 <= h_norm <= 620 and 390 <= w_norm <= 430:
            # A4 portrait: ~595×842pt — but rotated A4 appears as landscape
            size_classes['A4'] += 1
        elif 770 <= h_norm <= 800 and 590 <= w_norm <= 620:
            size_classes['A4'] += 1
        elif 770 <= h_norm <= 800 and 590 <= w_norm <= 620:
            size_classes['letter'] += 1
        else:
            size_classes['other'] += 1

    dominant_rotation = rotations.most_common(1)[0][0] if rotations else 0
    dominant_size = size_classes.most_common(1)[0][0] if size_classes else 'other'

    warnings: list[str] = []
    layout_class = 'standard'
    logical_pages = physical

    # rotated_spread: A3 pages with 90/270° rotation — two A4 logical pages per physical page
    if dominant_size == 'A3' and dominant_rotation in SPREAD_ROTATIONS:
        layout_class = 'rotated_spread'
        logical_pages = physical * 2
        warnings += [
            "rotated_spread detected: each physical PDF page contains two A4 logical pages.",
            "Do NOT use coordinate-based column splitting to reconstruct reading order — "
            "x-coordinate splits cannot reliably distinguish left and right logical pages.",
            "pdftotext -layout will likely interleave both pages; try MarkItDown or -raw first.",
            "Word coverage near 100% is not sufficient QA — reading order may still be interleaved.",
            "Vertical running titles are likely present; add strip patterns before conversion.",
        ]
    elif dominant_rotation in SPREAD_ROTATIONS and dominant_size != 'A3':
        layout_class = 'landscape'
        warnings.append(
            "Landscape rotation detected — check whether pages are single-column landscape "
            "or two-page spreads."
        )
    elif dominant_size == 'A3':
        layout_class = 'a3_portrait'
        logical_pages = physical * 2
        warnings.append(
            "A3 portrait pages detected — may contain two A4 logical pages per physical page "
            "(verify visually before assuming reading order)."
        )

    return {
        'layout_class':           layout_class,
        'physical_pages':         physical,
        'logical_pages_estimate': logical_pages,
        'rotation':               dominant_rotation,
        'page_size_class':        dominant_size,
        'warnings':               warnings,
    }


def find_repeated_strings(edge_text_by_page: dict[int, list[str]], total_pages: int,
                           threshold: float = REPEAT_THRESH) -> list[str]:
    """Return strings that appear on more than threshold fraction of pages."""
    counter: Counter = Counter()
    for strings in edge_text_by_page.values():
        for s in set(strings):   # deduplicate within one page
            counter[s] += 1
    return [s for s, n in counter.most_common() if n >= threshold * total_pages and s.strip()]


def suggest_y_cuts(top_words_by_page: dict, bot_words_by_page: dict,
                   page_height: float) -> tuple[float, float]:
    """
    Suggest Y_HEADER (top cut) and Y_FOOTER (bottom cut) based on where
    edge-zone words cluster.
    """
    top_bottoms = []  # bottom edge of top-zone words
    bot_tops    = []  # top edge of bottom-zone words

    for words in top_words_by_page.values():
        for w in words:
            top_bottoms.append(w['bottom'])

    for words in bot_words_by_page.values():
        for w in words:
            bot_tops.append(w['top'])

    y_header = max(top_bottoms) + 5  if top_bottoms else 65
    y_footer = min(bot_tops)   - 5  if bot_tops    else page_height - 50
    return round(y_header), round(y_footer)


# ── Main ──────────────────────────────────────────────────────────────────────

def profile(pdf_path: str, sample_pages: list[int] | None = None,
            header_cut: float = 80, footer_cut: float = 760,
            as_json: bool = False, quiet: bool = False) -> dict:

    path = Path(pdf_path)
    if not path.exists():
        print(f"ERROR: file not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    result = {
        'pdf': str(path),
        'pages': [],
        'summary': {},
        'hints': [],
    }

    # ── pdftotext baseline ────────────────────────────────────────────────────
    pdftotext_words = pdftotext_wc(pdf_path)

    # ── Per-page analysis ─────────────────────────────────────────────────────
    top_words_by_page: dict[int, list] = {}
    bot_words_by_page: dict[int, list] = {}
    top_text_by_page:  dict[int, list[str]] = {}
    bot_text_by_page:  dict[int, list[str]] = {}

    page_modes: list[str] = []
    body_word_counts: list[tuple[int, int]] = []   # (pg_num, count)
    blank_pages: list[int] = []
    page_height = 842   # A4 default; overwritten per page

    font_inventory: dict[str, list[float]] = defaultdict(list)   # fontname → sizes

    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)
        result['summary']['total_pages'] = total

        # Auto-select sample pages if not given
        if sample_pages is None:
            step = max(1, total // 4)
            sample_pages = [min(i * step + step // 2, total - 1) for i in range(3)]
            # Filter out first and last pages (likely cover/back)
            sample_pages = [p for p in sample_pages if 0 < p < total - 1]

        page_records: list[dict] = []

        for pg_num, page in enumerate(pdf.pages):
            page_height = page.height
            pw = page.width
            page_rotation = getattr(page, 'rotation', 0) or 0

            # Effective footer cut: scale if page height differs from assumed 842
            eff_footer = footer_cut if footer_cut < page_height else page_height - 40

            body_words = get_words(page, header_cut, eff_footer)
            tw, bw = get_edge_words(page, zone_height=50)

            top_words_by_page[pg_num] = tw
            bot_words_by_page[pg_num] = bw
            top_text_by_page[pg_num]  = [w['text'].strip() for w in tw if w['text'].strip()]
            bot_text_by_page[pg_num]  = [w['text'].strip() for w in bw if w['text'].strip()]

            wc   = len(body_words)
            mode = detect_col_split(body_words, pw)

            # Font inventory for sample pages
            if pg_num in sample_pages:
                for w in body_words:
                    fn = w.get('fontname', 'unknown')
                    sz = round(w.get('size', 0), 1)
                    font_inventory[fn].append(sz)

            flags = []
            if wc <= BLANK_THRESH:
                flags.append('blank/logo')
                blank_pages.append(pg_num)

            colored_rects = get_colored_rect_count(page)
            if colored_rects:
                flags.append(f'{colored_rects} colored box{"es" if colored_rects > 1 else ""}')

            rec = {
                'page':         pg_num,
                'page_1':       pg_num + 1,
                'width':        round(pw, 1),
                'height':       round(page_height, 1),
                'rotation':     page_rotation,
                'words':        wc,
                'mode':         mode,
                'colored_rects': colored_rects,
                'flags':        flags,
            }
            page_records.append(rec)
            page_modes.append(mode)
            body_word_counts.append((pg_num, wc))

        result['pages'] = page_records

        # ── Repeated edge strings ─────────────────────────────────────────────
        repeated_top = find_repeated_strings(top_text_by_page, total)
        repeated_bot = find_repeated_strings(bot_text_by_page, total)

        # ── Suggested Y cuts ─────────────────────────────────────────────────
        sugg_header, sugg_footer = suggest_y_cuts(
            top_words_by_page, bot_words_by_page, page_height
        )

        # ── x-histogram from sample pages ─────────────────────────────────────
        sample_words = []
        with pdfplumber.open(pdf_path) as pdf2:
            for pg_num in sample_pages:
                if pg_num < len(pdf2.pages):
                    sample_words.extend(
                        get_words(pdf2.pages[pg_num], header_cut, footer_cut)
                    )
        xhist = x_histogram(sample_words)

        # ── Font inventory summary ─────────────────────────────────────────────
        font_summary = {}
        for fn, sizes in sorted(font_inventory.items()):
            font_summary[fn] = {
                'min_size': round(min(sizes), 1),
                'max_size': round(max(sizes), 1),
                'count':    len(sizes),
            }

        # ── Total word count ──────────────────────────────────────────────────
        total_body_words = sum(wc for _, wc in body_word_counts)

        # ── Layout class classification ───────────────────────────────────────
        layout_info = classify_layout(page_records)

        result['summary'].update({
            'page_size':         f"{round(page_height, 0):.0f}×{round(page_records[-1]['width'] if page_records else 595, 0):.0f}pt  (H×W)",
            'pdftotext_words':   pdftotext_words,
            'pdfplumber_words':  total_body_words,
            'blank_pages_0idx':  blank_pages,
            'repeated_top_strings': repeated_top[:8],
            'repeated_bot_strings': repeated_bot[:8],
            'suggested_Y_HEADER':   sugg_header,
            'suggested_Y_FOOTER':   sugg_footer,
            'sample_pages_used':    sample_pages,
            'x_histogram_25pt':     {str(k): v for k, v in sorted(xhist.items())},
            'font_inventory':        font_summary,
            'layout_class':          layout_info,
        })

        # ── Hints ─────────────────────────────────────────────────────────────
        hints = []

        # Layout class warnings take top priority
        for w in layout_info.get('warnings', []):
            hints.append(f"[layout] {w}")

        if blank_pages:
            hints.append(f"SKIP_PAGES candidates (0-indexed, low word count): {blank_pages}")

        if repeated_top:
            hints.append(f"Likely running header strings: {repeated_top[:4]}")
            hints.append(f"  → Suggest Y_HEADER ≈ {sugg_header}  (currently guessing from edge-word positions)")

        if repeated_bot:
            hints.append(f"Likely running footer strings: {repeated_bot[:4]}")
            hints.append(f"  → Suggest Y_FOOTER ≈ {sugg_footer}")

        # Dominant reading mode
        mode_counts: Counter = Counter(
            m.split()[0] for m in page_modes if m not in ('sparse', 'blank/logo')
        )
        if mode_counts:
            dominant = mode_counts.most_common(1)[0][0]
            hints.append(f"Dominant reading mode: {dominant}")

        # Column split hint
        two_col_modes = [m for m in page_modes if 'two-col' in m]
        if two_col_modes:
            splits = []
            for m in two_col_modes:
                match = re.search(r'split≈(\d+)', m)
                if match:
                    splits.append(int(match.group(1)))
            if splits:
                median_split = sorted(splits)[len(splits)//2]
                hints.append(f"Two-column split x ≈ {median_split}pt  (median across {len(splits)} pages)")

        # x_tolerance hint
        if sample_words:
            gaps = []
            by_line: dict[int, list] = defaultdict(list)
            for w in sample_words:
                by_line[round(w['top'] / 3) * 3].append(w)
            for line_words in by_line.values():
                line_words.sort(key=lambda w: w['x0'])
                for a, b in zip(line_words, line_words[1:]):
                    gap = b['x0'] - a['x1']
                    if 0 < gap < 20:
                        gaps.append(gap)
            if gaps:
                min_gap = min(gaps)
                hints.append(
                    f"Min inter-word gap on sample pages: {min_gap:.1f}pt  "
                    f"(if < 4pt, use x_tolerance=2 in extract_words)"
                )

        # ── Colored box hint ──────────────────────────────────────────────────
        pages_with_boxes = [r['page_1'] for r in page_records if r['colored_rects'] > 0]
        if pages_with_boxes:
            hints.append(
                f"Colored fill rectangles detected on {len(pages_with_boxes)} page(s): "
                f"{pages_with_boxes[:10]}{'…' if len(pages_with_boxes) > 10 else ''}"
            )
            hints.append(
                "  → Use get_colored_boxes() + separate_box_words() from extract_manifesto.py "
                "BEFORE column detection.  Box words pollute the x0 distribution and collapse "
                "column gutters if left in the main word pool.  Partition on the RAW word list "
                "(before Y_HEADER filter) so box content near the page top is not discarded."
            )

        # ── PARA_GAP suggestion ───────────────────────────────────────────────
        # Estimate dominant body font size from the font inventory (most frequent
        # non-bold, non-symbol font at a plausible body-text size range).
        body_font_sizes = []
        for fn, info in font_summary.items():
            fn_upper = fn.upper()
            if any(k in fn_upper for k in ('BOLD', 'BLACK', 'HEAVY', 'SYMBOL',
                                            'WINGDING', 'ZAPF', 'DINGBAT')):
                continue
            min_sz, max_sz = info['min_size'], info['max_size']
            # Plausible body text: 8–16pt
            if 8 <= min_sz <= 16:
                body_font_sizes.extend([min_sz] * info['count'])
        if body_font_sizes:
            median_body = sorted(body_font_sizes)[len(body_font_sizes) // 2]
            # Rule: for very small body text the paragraph gap is much smaller
            # than the default 18 pt.  Derive from font size:
            #   typical line spacing ≈ font_size × 1.2
            #   effective row height ≈ font_size × 0.85  (pdfplumber word top)
            #   effective line gap   ≈ font_size × 0.35
            #   paragraph gap       ≈ font_size × 0.5  (slightly wider than line)
            # Clamp between 3 and 18.
            suggested_para_gap = max(3, min(18, round(median_body * 0.5)))
            if suggested_para_gap < 14:
                hints.append(
                    f"Body font ≈ {median_body:.1f}pt → suggest PARA_GAP = {suggested_para_gap}  "
                    f"(default 18 will miss paragraph breaks at this font size; "
                    f"at {median_body:.0f}pt the gap between paragraphs is only "
                    f"~{median_body * 0.5:.0f}pt)"
                )
            result['summary']['suggested_PARA_GAP'] = suggested_para_gap

        result['hints'] = hints

    # ── Output ────────────────────────────────────────────────────────────────
    if as_json:
        print(json.dumps(result, indent=2))
        return result

    # Human-readable text output
    print(f"\n{'─'*70}")
    print(f"  PDF profile: {path.name}")
    print(f"{'─'*70}")
    print(f"  Pages       : {total}")
    print(f"  Page size   : {result['summary']['page_size']}")
    lc = layout_info['layout_class']
    lc_str = lc.upper() if lc not in ('standard',) else lc
    print(f"  Layout class: {lc_str}  (rotation={layout_info['rotation']}°, "
          f"size={layout_info['page_size_class']})")
    if lc == 'rotated_spread':
        print(f"  Logical pages (est): {layout_info['logical_pages_estimate']}  "
              f"(2 × {layout_info['physical_pages']} physical pages)")
    if pdftotext_words:
        print(f"  pdftotext wc: {pdftotext_words:,} words")
    print(f"  pdfplumber  : {total_body_words:,} body words  (header_cut={header_cut}, footer_cut={footer_cut})")
    print()

    if not quiet:
        # Per-page table
        show_rot = any(rec.get('rotation', 0) for rec in page_records)
        if show_rot:
            print(f"  {'pg':>4}  {'w':>5}  {'h':>5}  {'rot':>4}  {'words':>6}  mode")
            print(f"  {'──':>4}  {'─':>5}  {'─':>5}  {'───':>4}  {'─────':>6}  ────")
        else:
            print(f"  {'pg':>4}  {'w':>5}  {'h':>5}  {'words':>6}  mode")
            print(f"  {'──':>4}  {'─':>5}  {'─':>5}  {'─────':>6}  ────")
        for rec in page_records:
            flag_str = f"  [{', '.join(rec['flags'])}]" if rec['flags'] else ''
            if show_rot:
                print(f"  {rec['page_1']:>4}  {rec['width']:>5.0f}  {rec['height']:>5.0f}  "
                      f"{rec.get('rotation',0):>4}  {rec['words']:>6}  {rec['mode']}{flag_str}")
            else:
                print(f"  {rec['page_1']:>4}  {rec['width']:>5.0f}  {rec['height']:>5.0f}  "
                      f"{rec['words']:>6}  {rec['mode']}{flag_str}")
        print()

    # Repeated strings
    if repeated_top:
        print(f"  Running header text (appears on ≥{REPEAT_THRESH*100:.0f}% of pages):")
        for s in repeated_top[:6]:
            print(f"    {s!r}")
        print()
    if repeated_bot:
        print(f"  Running footer text (appears on ≥{REPEAT_THRESH*100:.0f}% of pages):")
        for s in repeated_bot[:6]:
            print(f"    {s!r}")
        print()

    # x-histogram
    if xhist:
        print(f"  x0 histogram (sample pages {[p+1 for p in sample_pages]}, 25pt buckets):")
        max_count = max(xhist.values())
        for x in sorted(xhist):
            bar = '█' * int(xhist[x] / max_count * 30)
            print(f"    {x:>4}–{x+BUCKET_SIZE-1:<4}  {xhist[x]:>4}  {bar}")
        print()

    # Font inventory
    if font_summary:
        print(f"  Font inventory (sample pages {[p+1 for p in sample_pages]}):")
        for fn, info in sorted(font_summary.items(), key=lambda x: -x[1]['max_size']):
            print(f"    {info['max_size']:>5.1f}pt max  {fn}  ({info['count']} words)")
        print()

    # Suggested constants
    print(f"  Suggested constants:")
    print(f"    Y_HEADER = {sugg_header}")
    print(f"    Y_FOOTER = {sugg_footer}")
    if blank_pages:
        print(f"    SKIP_PAGES = {set(blank_pages)}  # 0-indexed")
    print()

    # Hints
    if hints:
        print(f"  Hints:")
        for h in hints:
            print(f"    • {h}")
        print()

    print(f"{'─'*70}\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('pdf', help='Path to PDF file')
    parser.add_argument('--sample-pages', metavar='N,N,...',
                        help='Comma-separated 0-indexed page numbers for x-histogram/font inventory')
    parser.add_argument('--header-cut', type=float, default=80,
                        help='Initial header zone bottom (default: 80)')
    parser.add_argument('--footer-cut', type=float, default=760,
                        help='Initial footer zone top (default: 760)')
    parser.add_argument('--json', dest='as_json', action='store_true',
                        help='Output JSON instead of text')
    parser.add_argument('--quiet', action='store_true',
                        help='Suppress per-page table')
    args = parser.parse_args()

    sample_pages = None
    if args.sample_pages:
        sample_pages = [int(p.strip()) for p in args.sample_pages.split(',')]

    profile(
        args.pdf,
        sample_pages=sample_pages,
        header_cut=args.header_cut,
        footer_cut=args.footer_cut,
        as_json=args.as_json,
        quiet=args.quiet,
    )


if __name__ == '__main__':
    main()
