"""
extract_ssp_2005.py — Scottish Socialist Party 2005 General Election manifesto.

PDF: "Scottish Socialist 2005 manifesto.pdf"
Output: 2005-scottish-socialist-manifesto.md
Coverage: 95.0% (21,608 / 22,747 pdftotext words)

Key patterns demonstrated (see PROMPT.md for full explanations):

1. FACING-PAGES ALTERNATING COLUMN LAYOUT
   The PDF uses mirror-image margins: odd pages col_split≈260, even pages
   col_split≈345. Fixed split fails on every other page. Fix: auto_col_split()
   detects the gutter per-page from a body-font x0 histogram gap.

2. PULL-QUOTE (STANDFIRST) EXCLUSION BY FONT NAME
   Right-column italic pull-quotes (Humanist521BT-Italic, sz≥14) duplicate
   nearby body text verbatim. Classified via is_standfirst() and excluded before
   paragraph assembly. Distinct from body LightItalic (also excluded from
   standfirst classification).

3. FULL-WIDTH HEADING EXTRACTION BEFORE COLUMN SPLIT
   Large headings (ExtraBold sz≥28, Bold sz≥40) span the column gutter.
   Extracted from the full-page word list by y-bucket, merged across rows within
   90pt, then excluded from column body text — avoids split headings.

4. MID-PAGE HEADING ORDERING: THREE-ZONE EXTRACTION
   When a numbered section heading appears mid-page, body text above it belongs
   to the previous section. process_page() returns (pre_paras, headings,
   post_paras); main loop emits pre → heading → post in the correct order.
   GUARD: when heading_ys is empty, skip the pre/post split entirely and return
   all body as post_paras (avoids double-counting every word on heading-free pages).

5. HYPHEN-JOIN FIX APPLIED AFTER MERGING MULTI-ROW HEADINGS
   "barrier-" ends one y-row; "free" starts the next. After merging rows,
   re.sub(r'(\\w)- (\\w)', ...) is applied to the merged text. Applying it
   per-row before merging doesn't catch end-of-row hyphens.

6. ZAPFDINGBATS BULLET ENCODING
   Bullets encoded as ZapfDingbats font (any character); sometimes on the same
   line as bullet text, sometimes alone on a preceding line (pending_bullet flag).
   is_bullet_font() detects by font name; col_paragraphs() handles both cases.

7. CONDENSED FONT WORD-SPLIT ARTEFACT
   Humanist521BT-Light Condensed splits "part" into "par" + "t".
   Fixed with: re.sub(r'\\bpar t\\b', 'part', text, flags=re.I) applied in
   heading_to_md() and process_contents().

8. LIGATURE FIXES
   ﬁ→fi, ﬂ→fl, ﬃ→ffi, ﬄ→ffl applied via fix_lig() on every extracted word.

9. POST-PROCESSING: SENTENCE-BREAK HYPHEN JOIN
   re.sub(r'([a-z]{2,})- ([a-z])', r'\\1\\2', md) joins soft hyphens from
   PDF line-breaks in body text. Does NOT interfere with intentional compound
   hyphens (which have no trailing space after the fix-after-merge pass).

10. SPECIAL-PAGE HANDLING
    Page 55 (membership form): decorative ExtraBold logo text excluded by size
    threshold; plain body rendered as labelled form fields.
    Page 56 (notes): rendered as simple body paragraphs.

Font classification (classify()):
  ZapfDingbats          → bullet
  Humanist521BT-Bold sz≥40 → h1   (## in output)
  ExtraBold/XtraBold sz≥28 → h2   (### in output)
  Humanist521BT-Light sz≥36 → part_label
  LightItalic sz≥14     → italic_intro
  Humanist521BT-Italic (not Light) sz≥14 → standfirst (excluded)
  Minion*               → body
  Various Humanist small → body

Y-coordinate constants:
  Y_HEADER = 90   (strips running section labels at top of each page)
  Y_FOOTER = 803  (strips page numbers and party name at bottom)
"""
import sys, re, pathlib
_HERE = pathlib.Path(__file__).parent.parent  # transcription-toolkit root
sys.path.insert(0, str(_HERE / 'lib'))
import pdfplumber
from collections import defaultdict, Counter

PDF_PATH = str(_HERE / '../Scottish Socialist 2005 manifesto.pdf')
OUT_PATH = str(_HERE / '../Markdown versions/scottish-socialist-manifesto/2005-scottish-socialist-manifesto.md')

Y_HEADER = 90
Y_FOOTER = 803
PARA_INDENT = 8

def bkt(v, tol=4):
    return round(v / tol) * tol

def base_font(fn):
    return fn.split('+')[-1]

def fix_lig(t):
    return (t.replace('ﬁ','fi').replace('ﬂ','fl').replace('ﬃ','ffi')
             .replace('ﬄ','ffl').replace('­','').replace('​',''))

def is_standfirst(fn, sz):
    bf = base_font(fn)
    return 'Humanist521BT-Italic' in bf and 'Light' not in bf and sz >= 14

def is_bullet_font(fn):
    return 'ZapfDingbats' in base_font(fn)

def classify(fn, sz):
    bf = base_font(fn)
    if 'ZapfDingbats' in bf:                                    return 'bullet'
    if 'Humanist521BT-Bold' in bf and sz >= 40:                 return 'h1'
    if ('ExtraBold' in bf or 'XtraBold' in bf) and sz >= 28:    return 'h2'
    if 'Humanist521BT-Light' in bf and sz >= 36:                return 'part_label'
    if 'LightItalic' in bf and sz >= 14:                        return 'italic_intro'
    if is_standfirst(fn, sz):                                   return 'standfirst'
    if 'Minion' in bf:                                          return 'body'
    if 'Humanist521BT-Roman' in bf and sz >= 9:                 return 'body'
    if 'Humanist521BT-Bold' in bf and sz <= 14:                 return 'body'
    if 'Humanist521BT-Light' in bf and sz <= 14:                return 'body'
    if 'Humanist521BT-BoldItalic' in bf and sz <= 11:           return 'body'
    if 'LightItalic' in bf and sz <= 10:                        return 'body'
    if 'Impact' in bf and sz <= 16:                             return 'body'
    return 'other'

def auto_col_split(page):
    chars = [c for c in page.chars
             if 'Minion' in c['fontname'] and c['text'].strip()
             and Y_HEADER <= c['top'] <= Y_FOOTER]
    if len(chars) < 30:
        return 330
    x_counts = Counter(round(c['x0'] / 10) * 10 for c in chars)
    occupied = sorted(k for k, v in x_counts.items() if v >= 2)
    best_gap, best_split = 0, 330
    for i in range(1, len(occupied)):
        gap = occupied[i] - occupied[i-1]
        if gap > best_gap and occupied[i-1] > 60:
            best_gap = gap
            best_split = (occupied[i-1] + occupied[i]) // 2
    return best_split if best_gap > 25 else 330

def words_of(page, x_lo=0, x_hi=999, y_lo=Y_HEADER, y_hi=Y_FOOTER):
    ws = page.extract_words(keep_blank_chars=False, extra_attrs=['fontname','size'],
                            x_tolerance=2, y_tolerance=3)
    result = []
    for w in ws:
        if x_lo <= w['x0'] < x_hi and y_lo <= w['top'] <= y_hi:
            w = dict(w)
            w['text'] = fix_lig(w['text'])
            result.append(w)
    return result

def find_heading_ys(words):
    hys = set()
    for w in words:
        fn, sz = w.get('fontname',''), w.get('size',0)
        cl = classify(fn, sz)
        if cl in ('h1','h2','part_label'):
            hys.add(bkt(w['top']))
    return hys

def extract_headings(words, heading_ys):
    by_y = defaultdict(list)
    for w in words:
        y = bkt(w['top'])
        if y in heading_ys:
            cl = classify(w.get('fontname',''), w.get('size',0))
            if cl in ('h1','h2','part_label'):
                by_y[y].append(w)
    raw = []
    for y in sorted(by_y.keys()):
        ws = sorted(by_y[y], key=lambda w: w['x0'])
        text = ' '.join(w['text'] for w in ws if w['text'].strip())
        cl = classify(ws[0]['fontname'], ws[0]['size']) if ws else 'body'
        raw.append((y, cl, text))
    # Merge consecutive same-type headings within 90pt
    merged = []
    for y, cl, text in raw:
        if merged and merged[-1][1] == cl and abs(y - merged[-1][0]) < 90:
            merged[-1] = [y, cl, merged[-1][2] + ' ' + text]
        else:
            merged.append([y, cl, text])
    # Fix "barrier- free" type hyphen-space AFTER merging (hyphen at end of row)
    for item in merged:
        item[2] = re.sub(r'(\w)- (\w)', r'\1-\2', item[2])
    return merged

def col_paragraphs(words, col_margin):
    by_y = defaultdict(list)
    for w in words:
        by_y[bkt(w['top'])].append(w)
    paras, cur, cur_type, pending_bullet = [], [], 'body', False
    def flush():
        if cur:
            text = ' '.join(cur).strip()
            if text: paras.append((cur_type, text))
            cur.clear()
    for y in sorted(by_y.keys()):
        row = sorted(by_y[y], key=lambda w: w['x0'])
        bullet_ws = [w for w in row if is_bullet_font(w.get('fontname',''))]
        body_ws   = [w for w in row if not is_bullet_font(w.get('fontname',''))
                     and classify(w.get('fontname',''), w.get('size',0)) in ('body','italic_intro')]
        intro_ws  = [w for w in body_ws if classify(w.get('fontname',''), w.get('size',0)) == 'italic_intro']
        line_text = ' '.join(w['text'] for w in body_ws if w['text'].strip())
        
        if intro_ws:
            flush()
            intro_text = ' '.join(w['text'] for w in intro_ws if w['text'].strip())
            if paras and paras[-1][0] == 'italic_intro':
                paras[-1] = ('italic_intro', paras[-1][1] + ' ' + intro_text)
            else:
                paras.append(('italic_intro', intro_text))
            pending_bullet = False
        elif bullet_ws:
            flush()
            if line_text:
                paras.append(('bullet', line_text))
                pending_bullet = False
            else:
                pending_bullet = True
            cur_type = 'body'
        elif pending_bullet and line_text:
            paras.append(('bullet', line_text))
            pending_bullet = False
        elif not line_text:
            pass
        else:
            first_x = row[0]['x0']
            is_indent = first_x > col_margin + PARA_INDENT
            if is_indent and cur:
                flush()
            cur.append(line_text)
            cur_type = 'body'
    flush()
    return paras

def process_page(page):
    all_words = words_of(page)
    col_split = auto_col_split(page)

    left_xs = [w['x0'] for w in all_words if w['x0'] < col_split and classify(w.get('fontname',''), w.get('size',0)) == 'body']
    right_xs = [w['x0'] for w in all_words if w['x0'] >= col_split and classify(w.get('fontname',''), w.get('size',0)) == 'body']
    left_margin  = min(left_xs)  if left_xs  else 30
    right_margin = min(right_xs) if right_xs else col_split

    heading_ys = find_heading_ys(all_words)
    headings = extract_headings(all_words, heading_ys)

    def filter_body(ws, x_lo, x_hi, y_lo, y_hi):
        return [w for w in ws
                if x_lo <= w['x0'] < x_hi
                and y_lo <= bkt(w['top']) <= y_hi
                and bkt(w['top']) not in heading_ys
                and not is_standfirst(w.get('fontname',''), w.get('size',0))
                and classify(w.get('fontname',''), w.get('size',0)) not in ('other','h1','h2','part_label')]

    # No headings on this page — all body as a single block (no pre/post split)
    if not heading_ys:
        all_left  = filter_body(all_words, 0,        col_split, Y_HEADER, Y_FOOTER)
        all_right = filter_body(all_words, col_split, 9999,     Y_HEADER, Y_FOOTER)
        return [], [], col_paragraphs(all_left, left_margin) + col_paragraphs(all_right, right_margin)

    min_h_y = min(heading_ys)
    max_h_y = max(heading_ys)

    # Pre-heading body (continuation from previous section)
    pre_left  = filter_body(all_words, 0,         col_split, Y_HEADER, min_h_y - 1)
    pre_right = filter_body(all_words, col_split,  9999,     Y_HEADER, min_h_y - 1)
    pre_paras = col_paragraphs(pre_left, left_margin) + col_paragraphs(pre_right, right_margin)

    # Post-heading body (start of this section)
    post_left  = filter_body(all_words, 0,        col_split, max_h_y + 1, Y_FOOTER)
    post_right = filter_body(all_words, col_split, 9999,     max_h_y + 1, Y_FOOTER)
    post_paras = col_paragraphs(post_left, left_margin) + col_paragraphs(post_right, right_margin)

    return pre_paras, headings, post_paras

def heading_to_md(cl, text):
    text = re.sub(r'\bpar t\b', 'part', text, flags=re.I)
    if cl == 'h1':       return f'\n## {text}\n'
    elif cl == 'h2':     return f'\n### {text}\n'
    elif cl == 'part_label': return f'\n_**{text.lower()}**_\n'
    return f'\n{text}\n'

def paras_to_md(paras):
    lines = []
    for ptype, text in paras:
        text = text.strip()
        if not text: continue
        if ptype == 'italic_intro':
            lines.append(f'\n_{text}_\n')
        elif ptype == 'bullet':
            lines.append(f'* {text}')
        else:
            lines.append(f'\n{text}\n')
    return '\n'.join(lines)

# ── Contents page ─────────────────────────────────────────────────────────────
def process_contents(page):
    ws = words_of(page, y_lo=30, y_hi=840)
    by_y = defaultdict(list)
    for w in ws:
        by_y[bkt(w['top'])].append(w)
    lines_out = ['\n## Contents\n']
    for y in sorted(by_y.keys()):
        row = sorted(by_y[y], key=lambda w: w['x0'])
        text = ' '.join(w['text'] for w in row if w['text'].strip())
        if not text: continue
        fn, sz = row[0]['fontname'], row[0]['size']
        bf = base_font(fn)
        if 'XtraBoldCondensed' in bf or ('ExtraBold' in bf and sz > 40): continue
        if 'UltraBold' in bf: continue
        cl = classify(fn, sz)
        if cl == 'part_label':
            t2 = re.sub(r'\bpar t\b','part', text, flags=re.I)
            lines_out.append(f'\n### {t2.title()}\n')
        elif cl == 'italic_intro':
            lines_out.append(f'\n_{text}_\n')
        elif cl == 'body':
            lines_out.append(f'\n{text}\n')
    return '\n'.join(lines_out)

# ── Form page (p.55) — plain text extraction ──────────────────────────────────
def process_form_page(page):
    ws = words_of(page, y_lo=90, y_hi=803)
    # Extract as simple body text, avoiding decorative large font
    out = ['\n---\n\n## Join the SSP / Scottish Socialist Voice\n']
    by_y = defaultdict(list)
    for w in ws:
        fn, sz = w.get('fontname',''), w.get('size',0)
        # Skip decorative large ExtraBold (the "voice" logo)
        if ('ExtraBold' in base_font(fn) or 'XtraBold' in base_font(fn)) and sz > 20:
            continue
        if 'UltraBold' in base_font(fn): continue
        by_y[bkt(w['top'])].append(w)
    for y in sorted(by_y.keys()):
        row = sorted(by_y[y], key=lambda w: w['x0'])
        fn0, sz0 = row[0]['fontname'], row[0]['size']
        text = ' '.join(w['text'] for w in row if w['text'].strip())
        if not text: continue
        if 'Humanist521BT-Bold' in base_font(fn0) and sz0 >= 30:
            out.append(f'\n**{text}**\n')
        elif is_bullet_font(fn0):
            body = ' '.join(w['text'] for w in row if not is_bullet_font(w.get('fontname',''))).strip()
            if body: out.append(f'* {body}')
        else:
            out.append(f'\n{text}\n')
    return '\n'.join(out)

# ── Main ──────────────────────────────────────────────────────────────────────
with pdfplumber.open(PDF_PATH) as pdf:
    parts = ['# Scottish Socialist Party Manifesto 2005\n']
    parts.append(process_contents(pdf.pages[0]))

    for i, page in enumerate(pdf.pages[1:], start=1):
        if i == 55:  # Join form page
            parts.append(process_form_page(page))
            continue
        if i == 56:  # Notes page — include as plain body
            ws = words_of(page)
            all_paras = col_paragraphs(ws, 30)
            parts.append('\n---\n')
            parts.append(paras_to_md(all_paras))
            continue

        pre_paras, headings, post_paras = process_page(page)
        parts.append(paras_to_md(pre_paras))
        for _, cl, text in headings:
            parts.append(heading_to_md(cl, text))
        parts.append(paras_to_md(post_paras))

md = '\n'.join(parts)

# ── Post-processing ───────────────────────────────────────────────────────────
md = re.sub(r'\n{3,}', '\n\n', md)

# Join hyphenated line-breaks (soft hyphen from line-break: lowercase-hyphen-SPACE-lowercase)
# This catches PDF line-break hyphens; intentional compound hyphens have no trailing space
# after the heading-fix pass already removed spaces from "word- word" → "word-word" in headings
md = re.sub(r'([a-z]{2,})- ([a-z])', r'\1\2', md)

# Fix missing space after comma/period within words (condensed font artifact)
md = re.sub(r'([a-z]),([A-Z])', r'\1, \2', md)
md = re.sub(r'([a-z])\.([A-Z][a-z])', r'\1. \2', md)

out = pathlib.Path(OUT_PATH).resolve()
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(md, encoding='utf-8')

print("Done.")
print(f"Word count: {len(md.split())}")
print(f"Saved to: {out}")
