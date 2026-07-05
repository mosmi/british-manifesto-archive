#!/usr/bin/env python3
"""
Welsh Labour 2010 manifesto extractor.

54-page PDF, three-column body text, clean encoding (no CID issues).
Uses NeoSansPro and Baskerville fonts.

Layout: A4 portrait, three-column body text.
  Left col:   x0 = 57–214
  Middle col: x0 = 215–381
  Right col:  x0 = 382–530
  Y_HEADER = 70   (running header "WelshLabourManifesto2010" at top≈56)
  Y_FOOTER = 790  (page number glyph at top≈801)

Words must be extracted with x_tolerance=2 (inter-word gaps are ~3pt at 12pt
font size; default x_tolerance=5 merges words into runs).

Font hierarchy:
  NeoSansPro-Medium  sz=40  → # heading  (chapter splash title)
  NeoSansPro-*       sz=24  → ## heading  (chapter subtitle on intro pages)
  NeoSansPro-Bold    sz=18  → ## heading  (section heading on special pages)
  NeoSansPro-Bold    sz=12  → ### heading (subheading within columns)
  NeoSansPro-Medium  sz=12  → body (intro lead-in paragraph)
  Baskerville        sz=12  → body (regular body text, also bullet text)
  NeoSansPro-MediumItalic sz=12 → body (quoted/callout text)
  Baskerville-SemiBold    sz=12 → body (emphasized text)
  NeoSansPro-Regular sz=8   → running header (excluded)
  NeoSansPro-Bold    sz=10  → page number (excluded)

Page types:
  Splash (max_sz≥40, few body words): chapter title only → # heading
  Mixed  (max_sz≥40, has body text):  large title + body (e.g. Foreword page)
  Intro  (max_sz=24): chapter subtitle + 3-column body
  Sz18   (max_sz=18): section heading + 3-column body
  Body   (max_sz≤12): 3-column body with ### subheading detection

SKIP_PAGES (0-indexed):
  0 → cover
  1 → near-blank back-of-cover (max_sz=6)
  2 → contents page
  5 → empty page
"""

import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))
import pdfplumber

# ── Paths ─────────────────────────────────────────────────────────────────────

HERE = Path(__file__).parent
PDF  = HERE.parent.parent / 'uploads' / 'Welsh Labour 2010 manifesto.pdf'
OUT  = HERE.parent.parent / '2010-welsh-labour-manifesto.md'

# ── Constants ─────────────────────────────────────────────────────────────────

Y_HEADER  = 70    # exclude top ≤ this (running header at top≈56)
Y_FOOTER  = 790   # exclude top ≥ this (page number at top≈801)
Y_TOL     = 4     # y-bucket tolerance
X_TOL     = 2     # x_tolerance for extract_words (needed to split words)

COL1_END  = 215   # left column  : x0 < 215
COL2_END  = 382   # middle column: 215 ≤ x0 < 382
                  # right column : x0 ≥ 382

SKIP_PAGES = {0, 1, 2, 5}   # 0-indexed: cover, back-cover, contents, blank

BULLET_CHARS = {'•', '*'}

# Regex for numbered promise items: "14)", "100)" etc.
RE_NUMBERED = re.compile(r'^\d{1,3}\)$')


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
    """True if word should be excluded (header/footer zone or non-printing glyph)."""
    if w['top'] <= Y_HEADER or w['top'] >= Y_FOOTER:
        return True
    text = w['text']
    if not text.strip() or '\x04' in text or '\x02' in text:
        return True
    return False


def is_subheading(w) -> bool:
    """True if word is a ### subheading (NeoSansPro-Bold at sz=12)."""
    fn = w.get('fontname', '')
    return 'Bold' in fn and 11 <= w['size'] <= 13


# ── Word extraction ───────────────────────────────────────────────────────────

def get_body_words(page) -> list:
    """Extract all valid body words using x_tolerance=2."""
    words = page.extract_words(
        keep_blank_chars=False,
        y_tolerance=3,
        x_tolerance=X_TOL,
        extra_attrs=['size', 'fontname'],
    )
    return [w for w in words if not is_excluded(w)]


# ── Column-aware paragraph assembly ──────────────────────────────────────────

def words_to_paras(words: list, para_gap: int = 20) -> list:
    """Assemble word list into paragraph strings, detecting bullets and numbered items.

    A new paragraph starts when:
      - the y-gap between rows exceeds para_gap, OR
      - the next word starts with a bullet char (•, *), OR
      - the next word is a numbered-list marker (e.g. "14)", "100)").

    Bullet-started paragraphs are converted to '* text'.
    """
    if not words:
        return []
    words = sorted(words, key=lambda w: (bucket(w['top']), w['x0']))

    paras    = []
    buf      = []
    prev_top = None

    def flush():
        if not buf:
            return
        text = clean(' '.join(w['text'] for w in buf)).strip()
        if not text:
            return
        if text[0] in BULLET_CHARS:
            text = '* ' + text[1:].lstrip(' ').strip()
        paras.append(text)
        buf.clear()

    for w in words:
        top     = bucket(w['top'])
        raw     = clean(w['text'])
        if not raw.strip():
            continue
        gap        = (top - prev_top) if prev_top is not None else 0
        is_bul     = raw[0] in BULLET_CHARS
        is_numitem = bool(RE_NUMBERED.match(raw))

        if prev_top is not None and (gap >= para_gap or is_bul or is_numitem):
            flush()

        buf.append(w)
        prev_top = top

    flush()
    return [p for p in paras if p.strip()]


def process_column(words: list) -> list:
    """Process one column's words: detect ### subheadings, assemble paragraphs.

    Returns a list of markdown strings (### headings and paragraph text),
    in reading order for this column.
    """
    if not words:
        return []

    words = sorted(words, key=lambda w: (bucket(w['top']), w['x0']))

    result   = []
    body_buf = []
    prev_top = None

    def flush_body():
        if body_buf:
            result.extend(words_to_paras(body_buf))
            body_buf.clear()

    # Group consecutive subheading words at the same y into heading rows
    # then flush into result as ### headings
    sh_buf    = []
    sh_top    = None

    def flush_sh():
        if sh_buf:
            heading = '### ' + ' '.join(clean(w['text']) for w in sh_buf)
            result.append(heading)
            sh_buf.clear()

    PARA_GAP = 20  # points before a new paragraph starts

    for w in words:
        top = bucket(w['top'])

        if is_subheading(w):
            # Could be continuation of same subheading row or a new one
            if sh_top is not None and abs(top - sh_top) < 20:
                sh_buf.append(w)
            else:
                flush_body()
                flush_sh()
                sh_buf.append(w)
                sh_top = top
        else:
            flush_sh()
            sh_top = None

            if prev_top is not None and (top - prev_top) >= PARA_GAP:
                flush_body()

            body_buf.append(w)
            prev_top = top

    flush_body()
    flush_sh()
    return result


def extract_3col(words: list) -> list:
    """Split words into three columns and process each in reading order."""
    left  = [w for w in words if w['x0'] < COL1_END]
    mid   = [w for w in words if COL1_END <= w['x0'] < COL2_END]
    right = [w for w in words if w['x0'] >= COL2_END]

    result = []
    result.extend(process_column(left))
    result.extend(process_column(mid))
    result.extend(process_column(right))
    return result


# ── Splash title extraction ───────────────────────────────────────────────────

def extract_splash_title(page) -> str:
    """Extract the sz=40 chapter title from a splash page."""
    words = page.extract_words(
        keep_blank_chars=False, y_tolerance=5, x_tolerance=5,
        extra_attrs=['size', 'fontname'],
    )
    large = [w for w in words if w['size'] >= 40 and not is_excluded(w)]
    large.sort(key=lambda w: (w['top'], w['x0']))
    return ' '.join(clean(w['text']) for w in large)


# ── Main ──────────────────────────────────────────────────────────────────────

all_paras = ['# Welsh Labour Manifesto 2010']
chapter_num = 0

with pdfplumber.open(str(PDF)) as pdf:
    total = len(pdf.pages)
    print(f"Total pages: {total}")

    for pg_num in range(total):
        if pg_num in SKIP_PAGES:
            print(f"  pg {pg_num+1:3d}: SKIP")
            continue

        page  = pdf.pages[pg_num]
        chars = [c for c in page.chars if c['text'].strip() and '\x04' not in c['text']]
        eff   = [c for c in chars if Y_HEADER < c['top'] < Y_FOOTER]

        if not eff:
            print(f"  pg {pg_num+1:3d}: (blank, skip)")
            continue

        max_sz = max(c['size'] for c in eff)

        words     = get_body_words(page)
        sz40_ws   = [w for w in words if w['size'] >= 40]
        sz24_ws   = [w for w in words if 22 <= w['size'] < 40]
        sz18_ws   = [w for w in words if 16 <= w['size'] < 22]
        body_ws   = [w for w in words if w['size'] < 16]

        # ── Splash page (chapter/section title) ────────────────────────────
        if sz40_ws and len(body_ws) < 10:
            chapter_num += 1
            title   = extract_splash_title(page)
            heading = f'# Chapter {chapter_num}: {title}'
            all_paras.append(heading)
            print(f"  pg {pg_num+1:3d}: SPLASH  {heading!r}")

        # ── Mixed page: large title + body (e.g. Foreword) ────────────────
        elif sz40_ws and body_ws:
            title   = ' '.join(clean(w['text']) for w in sorted(sz40_ws, key=lambda w: (w['top'], w['x0'])))
            heading = f'# {title}'
            all_paras.append(heading)
            # Also output the sz=24 subtitle if present
            if sz24_ws:
                subtitle = ' '.join(clean(w['text']) for w in sorted(sz24_ws, key=lambda w: (w['top'], w['x0'])))
                all_paras.append(f'## {subtitle}')
            paras = extract_3col(body_ws)
            all_paras.extend(paras)
            print(f"  pg {pg_num+1:3d}: MIXED   {heading!r}  +{len(paras)} paras")

        # ── Intro page: sz=24 subtitle + body ─────────────────────────────
        elif sz24_ws and body_ws:
            subtitle = ' '.join(clean(w['text']) for w in sorted(sz24_ws, key=lambda w: (w['top'], w['x0'])))
            all_paras.append(f'## {subtitle}')
            paras = extract_3col(body_ws)
            all_paras.extend(paras)
            print(f"  pg {pg_num+1:3d}: INTRO   ## {subtitle!r}  +{len(paras)} paras")

        # ── Sz=18 section heading page ─────────────────────────────────────
        elif sz18_ws:
            # Group heading words by y-bucket, then merge consecutive rows
            by_y = defaultdict(list)
            for w in sz18_ws:
                by_y[bucket(w['top'])].append(w)
            ys = sorted(by_y.keys())
            # Merge consecutive rows within 25pt of the previous row
            # Each entry: [last_y_added, [words...]]
            merged = []
            for y in ys:
                if merged and (y - merged[-1][0]) < 25:
                    merged[-1][0] = y          # advance the high-water y
                    merged[-1][1].extend(by_y[y])
                else:
                    merged.append([y, list(by_y[y])])
            for rep_y, ws in merged:
                ws_sorted = sorted(ws, key=lambda w: (bucket(w['top']), w['x0']))
                heading = '## ' + ' '.join(clean(w['text']) for w in ws_sorted)
                all_paras.append(heading)
            paras = extract_3col(body_ws)
            all_paras.extend(paras)
            print(f"  pg {pg_num+1:3d}: SZ18    {[h for h in all_paras if h.startswith('## ')][-1]!r}  +{len(paras)} paras")

        # ── Standard content page ──────────────────────────────────────────
        else:
            paras = extract_3col(words)
            all_paras.extend(paras)
            print(f"  pg {pg_num+1:3d}: content  {len(paras):3d} paras")

# ── Post-processing ───────────────────────────────────────────────────────────

md = '\n\n'.join(p for p in all_paras if p.strip()) + '\n'

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

# Fix hyphen-space from line-breaking
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
        print("Note: pdftotext includes running headers, contents page, cover,")
        print("      and blank pages. Effective content coverage will be higher.")
except Exception as e:
    print(f"pdftotext check skipped: {e}")

print(f"\nWritten: {OUT}")
