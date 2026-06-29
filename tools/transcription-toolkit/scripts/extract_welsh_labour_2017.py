#!/usr/bin/env python3
"""
Welsh Labour 2017 manifesto extractor (English section: PDF pages 116–231).

The source PDF is bilingual — Welsh section is pages 1–114, English is 116–231.
Only the English section is extracted here.

Layout: A4 portrait, two-column body text.
  COL_SPLIT ≈ 325pt  (left col x=72–321, right col x=328–577)
  Y_FOOTER  = 830pt  (running footer at y≈835)

Font hierarchy:
  sz=69–76  OpenSans-Extrabold  → large chapter title (chapter opener pages)
  sz=12     OpenSans-Extrabold  → "CHAPTER01" label   (chapter opener pages)
  sz=36     OpenSans-Extrabold  → ## section heading  (content pages)
  sz=10     OpenSans / Bold     → body text
  sz=7      OpenSans            → running footer      (excluded)
  sz=6      Helvetica           → InDesign artifact   (excluded)

CID encoding: two body-text font subsets (RKWHQD+OpenSans-Bold and
YDQJFP+OpenSans) encode most chars as CID+29, with the exceptions in CID_MAP.

Result: 24,777 words, ~96% effective coverage (vs pdftotext English-only
content after subtracting running footers and skipped pages).
"""

import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))
import pdfplumber

# ── Paths ─────────────────────────────────────────────────────────────────────

HERE = Path(__file__).parent
PDF  = HERE.parent.parent / 'uploads' / 'Welsh_Labour_Manifesto 2017.pdf'
OUT  = HERE.parent.parent / '2017-welsh-labour-manifesto.md'

# ── Constants ─────────────────────────────────────────────────────────────────

ENGLISH_START = 115   # 0-indexed (PDF page 116)
ENGLISH_END   = 229   # 0-indexed (PDF page 230, last body page)
Y_FOOTER      = 830
COL_SPLIT     = 325
Y_TOL         = 4

# Pages to skip entirely (0-indexed)
SKIP_PAGES = {
    115,        # Welsh cover "Sefyll Cornel Cymru" (sz=58, Welsh text)
    116,        # "Standing Up for Wales" title splash (redundant with manual title)
    117, 118,   # Contents pages (11pt text)
    229,        # Back cover repeat of "Standing Up for Wales"
}

# ── CID character decoding ────────────────────────────────────────────────────
#
# Two body-text font subsets use CID-encoded characters:
#   RKWHQD+OpenSans-Bold  (some body text runs)
#   YDQJFP+OpenSans       (some body text runs, bullets)
#
# Most chars follow: chr(CID + 29).  The overrides below handle exceptions.
#
# Notes on specific mappings:
#   514 — soft punctuation mark in RKWHQD+OpenSans-Bold; pdftotext drops it.
#          Mapped to '' to avoid spurious bullet detection.
#   519 — right single quotation mark / apostrophe (e.g. "government's")
#   564 — fi ligature (e.g. "financial", "first", "fight")
#   918 — capital I; non-standard glyph ID in RKWHQD+OpenSans-Bold
#   101 — pound sign £ in YDQJFP+OpenSans
#   518 — left single quotation mark (opening quote, joins next word)
#   527 — bullet point • in YDQJFP+OpenSans
#   581 — paragraph-level marker in YDQJFP+OpenSans; pdftotext drops it.
#          Mapped to '' to avoid spurious bullet detection.

CID_MAP = {
    514: '',        # soft punctuation — drop
    519: '’',  # right single quote / apostrophe
    564: 'fi',      # fi ligature
    918: 'I',       # capital I
    101: '£',  # pound sign £
    518: '‘',  # left single quote
    527: '•',  # bullet •
    581: '',        # paragraph marker — drop
}


def decode_cid(text: str) -> str:
    """Replace (cid:N) sequences with their proper Unicode characters."""
    def _replace(m):
        n = int(m.group(1))
        if n in CID_MAP:
            return CID_MAP[n]
        shifted = n + 29
        if 32 <= shifted <= 126:
            return chr(shifted)
        return ''   # drop truly unknown CIDs

    return re.sub(r'\(cid:(\d+)\)', _replace, text)


def clean(text: str) -> str:
    return (decode_cid(text)
            .replace('ﬁ', 'fi').replace('ﬂ', 'fl')
            .replace('ﬃ', 'ffi').replace('ﬄ', 'ffl')
            .replace('­', '')    # soft hyphen
            .replace('​', ''))   # zero-width space


def bucket(top, tol=Y_TOL):
    return round(top / tol) * tol


# ── Section heading extraction ────────────────────────────────────────────────

def extract_heading(page):
    """Return (y_bucket, text) for the sz≥30 section heading, or None.

    Headings are full-width (parts appear in both column x-ranges at the same y),
    so we collect all sz≥30 words on that y-row regardless of column.
    """
    heading_chars = [
        c for c in page.chars
        if c['text'].strip() and c.get('size', 0) >= 30 and c['top'] < Y_FOOTER
    ]
    if not heading_chars:
        return None

    by_y = defaultdict(list)
    for c in heading_chars:
        by_y[bucket(c['top'])].append(c)

    all_words = page.extract_words(
        keep_blank_chars=False, y_tolerance=3, x_tolerance=5,
        extra_attrs=['size']
    )

    heading_lines = []
    for y_bkt in sorted(by_y.keys()):
        chars = by_y[y_bkt]
        y_min = min(c['top'] for c in chars) - 2
        y_max = max(c['top'] for c in chars) + 5
        row_words = [
            w for w in all_words
            if y_min <= w['top'] <= y_max and w.get('size', 0) >= 30
        ]
        if row_words:
            row_words.sort(key=lambda w: w['x0'])
            heading_lines.append(
                ' '.join(clean(w['text']) for w in row_words)
            )

    if not heading_lines:
        return None
    return (min(by_y.keys()), ' '.join(heading_lines))


# ── Chapter opener extraction ─────────────────────────────────────────────────

def extract_chapter_opener(page):
    """Extract the large-title chapter opener pages.

    Structure:
      sz=12  → "CHAPTER01" label at top (y≈92)
      sz=69+ → chapter title words in large type spread across y≈587–741

    Output: ['# Chapter N: Title Case Title']
    """
    words = page.extract_words(
        keep_blank_chars=False, y_tolerance=5, x_tolerance=10,
        extra_attrs=['size']
    )
    words = [w for w in words if w['top'] < Y_FOOTER]

    label_words = [w for w in words if 11 <= w.get('size', 0) <= 13]
    title_words = [w for w in words if w.get('size', 0) >= 60]

    label_words.sort(key=lambda w: w['x0'])
    title_words.sort(key=lambda w: (w['top'], w['x0']))

    if not title_words:
        return []

    label_text = ' '.join(clean(w['text']) for w in label_words)
    m = re.search(r'(\d+)', label_text)
    chapter_num = int(m.group(1)) if m else 0

    title_text = ' '.join(clean(w['text']) for w in title_words)
    title_cased = title_text.title()

    if chapter_num:
        return [f'# Chapter {chapter_num}: {title_cased}']
    return [f'# {title_cased}']


# ── Body text → paragraph assembly ───────────────────────────────────────────

BULLET_CHARS = {'•', '*'}   # • and *


def words_to_paras(words, para_gap=15):
    """Assemble a column's word list into paragraph strings.

    Bullets (• or CID-decoded •) are converted to '* '.
    A new paragraph starts when the y-gap exceeds para_gap points.
    Empty words (CID chars that decoded to '') are skipped.
    """
    if not words:
        return []
    words = sorted(words, key=lambda w: (bucket(w['top']), w['x0']))

    paras = []
    buf = []
    prev_top = None

    def flush():
        if not buf:
            return
        text = clean(' '.join(w['text'] for w in buf)).strip()
        if not text:
            return
        if text[0] in BULLET_CHARS:
            text = '* ' + text[1:].lstrip('. ').strip()
        paras.append(text)
        buf.clear()

    for w in words:
        top = bucket(w['top'])
        raw = clean(w['text'])
        if not raw.strip():
            continue   # skip empty (dropped CID chars)

        gap = (top - prev_top) if prev_top is not None else 0
        is_bullet = raw[0] in BULLET_CHARS

        if prev_top is not None and (gap >= para_gap or is_bullet):
            flush()

        buf.append(w)
        prev_top = top

    flush()
    return [p for p in paras if p.strip()]


# ── Standard page extractor ───────────────────────────────────────────────────

def extract_standard_page(page):
    """Extract a content page: optional ## heading + two-column body text.

    Column split: x < COL_SPLIT → left, x ≥ COL_SPLIT → right.
    Heading y-row is excluded from body extraction.
    """
    heading = extract_heading(page)
    heading_y = heading[0] if heading else None

    all_words = page.extract_words(
        keep_blank_chars=False, y_tolerance=3, x_tolerance=3,
        extra_attrs=['fontname', 'size']
    )

    body_words = []
    for w in all_words:
        sz = w.get('size', 0)
        if sz < 9 or sz > 11:
            continue
        if w['top'] >= Y_FOOTER:
            continue
        if heading_y is not None and abs(bucket(w['top']) - heading_y) < 8:
            continue
        body_words.append(w)

    left_words  = [w for w in body_words if w['x0'] <  COL_SPLIT]
    right_words = [w for w in body_words if w['x0'] >= COL_SPLIT]

    result = []
    if heading:
        result.append(f'## {heading[1]}')
    result.extend(words_to_paras(left_words))
    result.extend(words_to_paras(right_words))
    return result


# ── Main ──────────────────────────────────────────────────────────────────────

all_paras = [
    '# Standing Up for Wales: Welsh Labour Manifesto 2017',
    '_Note: This document covers the English-language version of the bilingual manifesto._',
]

with pdfplumber.open(str(PDF)) as pdf:
    total = len(pdf.pages)
    print(f"Total pages: {total}")
    for pg_num in range(ENGLISH_START, ENGLISH_END + 1):
        if pg_num in SKIP_PAGES:
            print(f"  pg {pg_num+1:3d}: SKIP")
            continue

        page = pdf.pages[pg_num]
        chars = [c for c in page.chars if c['text'].strip()]
        if not chars:
            print(f"  pg {pg_num+1:3d}: (empty)")
            continue

        max_sz = max(c['size'] for c in chars)

        if max_sz < 8:
            print(f"  pg {pg_num+1:3d}: (footer only, skip)")
            continue

        if max_sz >= 60:
            paras = extract_chapter_opener(page)
            label = 'CHAPTER OPENER'
        else:
            paras = extract_standard_page(page)
            label = 'standard'

        all_paras.extend(paras)
        print(f"  pg {pg_num+1:3d}: {label:20s}  {len(paras):3d} paras")

# ── Post-processing ───────────────────────────────────────────────────────────

md = '\n\n'.join(p for p in all_paras if p.strip()) + '\n'

# Merge paragraphs where the previous line ends without terminal punctuation.
# Single quotes (', ') are excluded from TERMINAL_PUNCT because they appear
# in possessives (e.g. "workers'") that continue on the next line.
TERMINAL_PUNCT = set('.!?:;"»')


def merge_unfinished_paras(text):
    paras = text.split('\n\n')
    result = []
    for para in paras:
        stripped = para.strip()
        if result and stripped:
            prev = result[-1].rstrip()
            structural_prefixes = ('# ', '## ', '### ', '* ', '_')
            prev_structural = any(prev.startswith(p) for p in structural_prefixes)
            curr_structural = any(stripped.startswith(p) for p in structural_prefixes)
            if (not prev_structural and not curr_structural
                    and prev and prev[-1] not in TERMINAL_PUNCT):
                result[-1] = prev + ' ' + stripped
                continue
        result.append(para)
    return '\n\n'.join(result)


md = merge_unfinished_paras(md)

# Fix headings where "AND" is a visual design gap with no text char in the PDF
md = md.replace('## ENGLAND SCOTLAND\n', '## ENGLAND AND SCOTLAND\n')
md = md.replace('## WALES NORTHERN IRELAND\n', '## WALES AND NORTHERN IRELAND\n')

md = re.sub(r'(\w)- (\w)', r'\1-\2', md)   # fix hyphen-space
md = re.sub(r'\n{4,}', '\n\n\n', md)        # collapse excess blank lines

OUT.write_text(md, encoding='utf-8')

import subprocess
wc_md = len(md.split())
print(f"\nMarkdown word count: {wc_md:,}")
try:
    res = subprocess.run(
        ['pdftotext', '-f', '116', '-l', '230', str(PDF), '-'],
        capture_output=True, text=True, timeout=60
    )
    if res.returncode == 0:
        wc_pdf = len(res.stdout.split())
        print(f"PDF English section (pdftotext): {wc_pdf:,}")
        print(f"Coverage (md/pdf): {wc_md / wc_pdf * 100:.1f}%")
        print("Note: pdftotext count includes ~800 running footer words and ~400")
        print("      words from skipped pages. Effective content coverage ~96%.")
except Exception as e:
    print(f"pdftotext check skipped: {e}")
print(f"\nWritten: {OUT}")
