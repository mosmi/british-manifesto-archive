#!/usr/bin/env python3
"""
Welsh Labour 2015 manifesto extractor.

87-page PDF, single-column body text, clean text encoding (no CID issues).

Layout: A4 portrait, single-column body text.
  Body x0: 77–430pt
  Y_FOOTER = 608pt  (running footer/header at y≥608)
  X_MIN    = 0      (exclude off-screen left-page headers at x0<0)

Font hierarchy:
  sz=81.5   RobotoSlab-Thin/Light   → drop-cap letter on splash pages
  sz=28.0   RobotoSlab-Thin         → splash page title words  → # heading
  sz=30–33  RobotoSlab-Light/Regular → drop-cap on chapter intro pages
  sz=14.0   RobotoSlab-Regular      → ### subheadings (content pages)
  sz=9.5    OpenSans-Light / RobotoSlab-Regular → body text
  sz≤10     OpenSans-Light-SC700    → running footer (excluded)

Page classification (0-indexed):
  max_sz ≥ 60 → splash page (foreword or chapter title)
  max_sz ≥ 25 → chapter intro page (drop-cap first para + body)
  else        → standard content page (optional ### heading + body)

SKIP_PAGES (0-indexed):
  0  → UK Labour cover "Britain can be better"
  3  → Contents page
  86 → Back matter (max_sz=5, essentially blank)

Blank pages (e.g. 2, 4, 8, 16, 32, 44, 60, 74, 84) have no effective
body content and are automatically skipped in the processing loop.
"""

import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))
import pdfplumber

# ── Paths ─────────────────────────────────────────────────────────────────────

HERE = Path(__file__).parent
PDF  = HERE.parent.parent / 'uploads' / 'Welsh Labour 2015 manifesto.pdf'
OUT  = HERE.parent.parent / '2015-welsh-labour-manifesto.md'

# ── Constants ─────────────────────────────────────────────────────────────────

Y_FOOTER = 608   # footer/header zone: exclude y ≥ this
X_MIN    = 0     # exclude off-screen left-page chars (x0 < 0)
Y_TOL    = 4     # y-bucket tolerance for row grouping

# Pages to skip entirely (0-indexed)
SKIP_PAGES = {
    0,   # UK Labour cover
    3,   # Contents page
    86,  # Back matter (near-blank)
}


# ── Utilities ─────────────────────────────────────────────────────────────────

def clean(text: str) -> str:
    return (text
            .replace('ﬁ', 'fi').replace('ﬂ', 'fl')
            .replace('ﬃ', 'ffi').replace('ﬄ', 'ffl')
            .replace('­', '')   # soft hyphen
            .replace('​', ''))  # zero-width space


def bucket(top: float, tol: int = Y_TOL) -> int:
    return round(top / tol) * tol


def is_excluded(w) -> bool:
    """True if this word should be excluded from body extraction."""
    # Footer/header zone
    if w['top'] >= Y_FOOTER:
        return True
    # Off-screen left-page running headers (negative x0)
    if w['x0'] < X_MIN:
        return True
    # Small-caps footer font
    if 'SC700' in w.get('fontname', ''):
        return True
    return False


# ── Splash page extraction ────────────────────────────────────────────────────

def extract_splash_title(page) -> str:
    """Extract title from a splash page (drop-cap + title text).

    Structure:
      sz≥60   → single drop-cap letter (e.g. 'W', 'F')
      sz≈28   → remaining title words across multiple y-rows

    Returns the full title as a plain string (no markdown prefix).
    """
    words = page.extract_words(
        keep_blank_chars=False, y_tolerance=5, x_tolerance=5,
        extra_attrs=['size', 'fontname']
    )
    words = [w for w in words if not is_excluded(w)]

    dropcap = [w for w in words if w['size'] >= 60]
    title_ws = [w for w in words if 24 <= w['size'] < 60]

    dropcap_letter = clean(dropcap[0]['text']) if dropcap else ''
    title_ws.sort(key=lambda w: (w['top'], w['x0']))

    if not title_ws:
        return dropcap_letter

    # The first sz≈28 word is the remainder of the drop-cap word
    first = clean(title_ws[0]['text'])
    rest  = [clean(w['text']) for w in title_ws[1:]]
    title = dropcap_letter + first
    if rest:
        title += ' ' + ' '.join(rest)
    return title


def extract_splash_body(page) -> list:
    """Extract any body text (sz<12) that appears below the title on a splash page."""
    words = page.extract_words(
        keep_blank_chars=False, y_tolerance=3, x_tolerance=3,
        extra_attrs=['size', 'fontname']
    )
    words = [w for w in words if not is_excluded(w)]
    body_ws = [w for w in words if w['size'] < 12]
    return words_to_paras(body_ws)


# ── Chapter intro page extraction ─────────────────────────────────────────────

def extract_intro_page(page) -> list:
    """Extract a chapter intro page: drop-cap (sz≥25) + body (sz<12).

    The large drop-cap letter is merged with the first body word at the
    same y position.  All body text is then assembled into paragraphs.
    """
    words = page.extract_words(
        keep_blank_chars=False, y_tolerance=3, x_tolerance=3,
        extra_attrs=['size', 'fontname']
    )
    words = [w for w in words if not is_excluded(w)]

    dropcap_ws = [w for w in words if w['size'] >= 25]
    body_ws    = [w for w in words if w['size'] < 12]

    if not body_ws:
        return []

    body_ws = sorted(body_ws, key=lambda w: (bucket(w['top']), w['x0']))

    if dropcap_ws:
        dropcap_letter = clean(dropcap_ws[0]['text'])
        dropcap_y = bucket(dropcap_ws[0]['top'])
        # Find first body word at same y-bucket as drop-cap
        for i, w in enumerate(body_ws):
            if abs(bucket(w['top']) - dropcap_y) < 8:
                merged = dict(w, text=dropcap_letter + w['text'])
                body_ws[i] = merged
                break

    return words_to_paras(body_ws)


# ── Body paragraph assembly ───────────────────────────────────────────────────

def words_to_paras(words: list, para_gap: int = 12) -> list:
    """Assemble a sorted word list into paragraph strings.

    A new paragraph starts when the y-gap between successive rows
    exceeds para_gap points.
    """
    if not words:
        return []
    words = sorted(words, key=lambda w: (bucket(w['top']), w['x0']))

    paras   = []
    buf     = []
    prev_top = None

    def flush():
        if not buf:
            return
        text = clean(' '.join(w['text'] for w in buf)).strip()
        if text:
            paras.append(text)
        buf.clear()

    for w in words:
        top = bucket(w['top'])
        gap = (top - prev_top) if prev_top is not None else 0
        if prev_top is not None and gap >= para_gap:
            flush()
        buf.append(w)
        prev_top = top

    flush()
    return [p for p in paras if p.strip()]


# ── Standard content page extraction ─────────────────────────────────────────

def extract_standard_page(page) -> list:
    """Extract a content page: ### subheadings (sz≥12) + body text (sz<12).

    Headings and body paragraphs are interleaved in reading order
    (sorted by y position).
    """
    words = page.extract_words(
        keep_blank_chars=False, y_tolerance=3, x_tolerance=3,
        extra_attrs=['size', 'fontname']
    )
    words = [w for w in words if not is_excluded(w)]

    heading_ws = [w for w in words if w['size'] >= 12]
    body_ws    = [w for w in words if w['size'] <  12]

    # Build a map of y-bucket → heading text, merging consecutive heading lines
    # (e.g. a long subheading that wraps to two lines in the PDF).
    heading_rows = {}
    if heading_ws:
        by_y = defaultdict(list)
        for w in heading_ws:
            by_y[bucket(w['top'])].append(w)
        # Merge consecutive y-rows that are within 20pt of each other
        ys_sorted = sorted(by_y.keys())
        merged_ys  = []   # list of (representative_y, [words...])
        for y in ys_sorted:
            if merged_ys and (y - merged_ys[-1][0]) < 20:
                merged_ys[-1][1].extend(by_y[y])
            else:
                merged_ys.append([y, list(by_y[y])])
        for rep_y, ws in merged_ys:
            ws_sorted = sorted(ws, key=lambda w: (bucket(w['top']), w['x0']))
            heading_rows[rep_y] = '### ' + ' '.join(clean(w['text']) for w in ws_sorted)

    if not heading_rows:
        return words_to_paras(body_ws)

    # Interleave headings with body paragraphs in y-order
    result      = []
    body_sorted = sorted(body_ws, key=lambda w: (bucket(w['top']), w['x0']))
    hy_sorted   = sorted(heading_rows.keys())
    hi          = 0   # heading index
    buf         = []

    def flush_buf():
        if buf:
            result.extend(words_to_paras(buf))
            buf.clear()

    for w in body_sorted:
        top = bucket(w['top'])
        # Emit all headings that precede this body word
        while hi < len(hy_sorted) and hy_sorted[hi] < top:
            flush_buf()
            result.append(heading_rows[hy_sorted[hi]])
            hi += 1
        buf.append(w)

    flush_buf()

    # Emit any headings that follow all body text
    while hi < len(hy_sorted):
        result.append(heading_rows[hy_sorted[hi]])
        hi += 1

    return result


# ── Main ──────────────────────────────────────────────────────────────────────

all_paras = [
    '# Welsh Labour Manifesto 2015',
]

chapter_num  = 0
foreword_num = 0

with pdfplumber.open(str(PDF)) as pdf:
    total = len(pdf.pages)
    print(f"Total pages: {total}")

    for pg_num in range(total):
        if pg_num in SKIP_PAGES:
            print(f"  pg {pg_num+1:3d}: SKIP")
            continue

        page  = pdf.pages[pg_num]
        chars = [c for c in page.chars if c['text'].strip()]

        # Exclude footer/off-screen chars for classification
        eff_chars = [
            c for c in chars
            if c['top'] < Y_FOOTER and c['x0'] >= X_MIN
            and 'SC700' not in c.get('fontname', '')
        ]

        if not eff_chars:
            print(f"  pg {pg_num+1:3d}: (blank/footer-only, skip)")
            continue

        max_sz = max(c['size'] for c in eff_chars)

        # ── Splash page ────────────────────────────────────────────────────
        if max_sz >= 60:
            title = extract_splash_title(page)
            lower = title.lower()
            if lower.startswith('foreword'):
                foreword_num += 1
                heading = f'# {title}'
                label = 'FOREWORD SPLASH'
            elif lower.startswith('time for change'):
                heading = f'# {title}'
                label = 'CLOSING SPLASH'
            else:
                chapter_num += 1
                heading = f'# Chapter {chapter_num}: {title}'
                label = 'CHAPTER SPLASH'
            all_paras.append(heading)
            # Also capture any body text below the splash title
            body_paras = extract_splash_body(page)
            all_paras.extend(body_paras)
            print(f"  pg {pg_num+1:3d}: {label:20s}  {heading!r}  +{len(body_paras)} body paras")

        # ── Chapter intro page (drop-cap ~30pt + body) ─────────────────────
        elif max_sz >= 25:
            paras = extract_intro_page(page)
            all_paras.extend(paras)
            print(f"  pg {pg_num+1:3d}: {'CHAPTER INTRO':20s}  {len(paras):3d} paras")

        # ── Standard content page ──────────────────────────────────────────
        else:
            paras = extract_standard_page(page)
            all_paras.extend(paras)
            print(f"  pg {pg_num+1:3d}: {'standard':20s}  {len(paras):3d} paras")

# ── Post-processing ───────────────────────────────────────────────────────────

md = '\n\n'.join(p for p in all_paras if p.strip()) + '\n'

# Merge paragraphs where previous line ends without terminal punctuation.
# Single quotes excluded to preserve possessives (e.g. "workers'").
TERMINAL_PUNCT = set('.!?:;"»')


def merge_unfinished_paras(text: str) -> str:
    paras  = text.split('\n\n')
    result = []
    for para in paras:
        stripped = para.strip()
        if result and stripped:
            prev = result[-1].rstrip()
            structural = ('# ', '## ', '### ', '* ', '_')
            prev_struct = any(prev.startswith(p) for p in structural)
            curr_struct = any(stripped.startswith(p) for p in structural)
            if (not prev_struct and not curr_struct
                    and prev and prev[-1] not in TERMINAL_PUNCT):
                result[-1] = prev + ' ' + stripped
                continue
        result.append(para)
    return '\n\n'.join(result)


md = merge_unfinished_paras(md)

# Fix hyphen-space artefacts from line-breaking in the source PDF
md = re.sub(r'(\w)- (\w)', r'\1-\2', md)

# Collapse excess blank lines
md = re.sub(r'\n{4,}', '\n\n\n', md)

OUT.write_text(md, encoding='utf-8')

# ── Coverage report ───────────────────────────────────────────────────────────

import subprocess

wc_md = len(md.split())
print(f"\nMarkdown word count: {wc_md:,}")
try:
    res = subprocess.run(
        ['pdftotext', str(PDF), '-'],
        capture_output=True, text=True, timeout=60
    )
    if res.returncode == 0:
        wc_pdf = len(res.stdout.split())
        print(f"PDF full text (pdftotext): {wc_pdf:,}")
        print(f"Raw coverage (md/pdf): {wc_md / wc_pdf * 100:.1f}%")
        print("Note: pdftotext includes running footers, contents page, cover,")
        print("      and back matter. Effective content coverage will be higher.")
except Exception as e:
    print(f"pdftotext check skipped: {e}")

print(f"\nWritten: {OUT}")
