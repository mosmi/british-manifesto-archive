#!/usr/bin/env python3
"""
Convert 2015 Green Party manifesto PDF to markdown.

Key insights from diagnostic:
- Pages are mostly single-column (x0 50-543)
- Pages 6-7 (foreword) and possibly page 80 have two-column layout
  * Left col: x0 ~54-289, Right col: x0 ~301-537
  * Gap is at ~290-300
- SymbolMT bullet lines: bullet char (•) + tab + body text, all on same line
  * Continuation lines have x0=67 (indented) and use regular body font
  * Gap between bullet line and continuation: ~12pt
- Font families:
  * QVHEBS+HelveticaNeueLTPro-Cn 10pt: main body text
  * QVHEBS+HelveticaNeueLTPro-Cn 12pt: lead-in body text (larger intro paragraphs)
  * WUFJHG+HelveticaNeueLTPro-CnO 10pt: italic body
  * EYIKPQ+HelveticaNeueLTPro-BdCn 10pt: bold body (sidebars/callouts)
  * BESNZW+BebasNeueBold 16pt: section headings
  * JQTJHG+BebasNeueBook 40pt: chapter headings
  * BESNZW+BebasNeueBold 41pt+: decorative stacked chars (skip)
  * VNXTKN+BebasNeueRegular 8pt at y0=24: running footer (skip)
  * XYUPVE+SymbolMT 10pt: bullet markers
"""

import pdfplumber
from collections import defaultdict, Counter
import re
import sys

PDF_PATH = '/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2015/green/manifesto.pdf'
OUT_PATH = '/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2015/green/manifesto.md'

# Pages to skip entirely (0-indexed)
SKIP_PAGES = {0, 1, 2, 3, 4, 83}

# Two-column pages (0-indexed): foreword pages (5, 6)
# These have left col x0 < ~295 and right col x0 >= ~295
TWO_COL_PAGES = {5, 6}
COL_SPLIT = 295  # x0 < 295 = left col, x0 >= 295 = right col

# Font classification helpers
def strip_prefix(fontname):
    if '+' in fontname:
        return fontname.split('+', 1)[1]
    return fontname

def classify_font(fontname, size):
    """Return font category."""
    fn = fontname.lower()
    if 'symbolmt' in fn or 'symbol' in fn:
        return 'bullet_marker'
    if 'bebasneuebold' in fn and size >= 30:
        return 'decorative'
    if 'bebasneuebook' in fn and size >= 30:
        return 'chapter_heading'
    if 'bebasneuebold' in fn and 14 <= size <= 25:
        return 'section_heading'
    if 'bebasneuebold' in fn and 10 <= size <= 13:
        return 'subsection_heading'
    if 'bebasneueregular' in fn and size <= 8:
        return 'footer'
    if 'bebasneueregular' in fn and size >= 14:
        return 'toc_entry'
    if 'ltcn' in fn:
        return 'toc_sub'
    if 'helveticaneultpro-bdcn' in fn or 'bdcn' in fn:
        return 'bold_body'
    if 'helveticaneultpro-cno' in fn or 'cno' in fn:
        return 'italic_body'
    if 'helveticaneultpro-cn' in fn or '-cn' in fn:
        if size >= 11:
            return 'lead_body'
        return 'body'
    return 'body'

def is_leader_line(text):
    """Detect TOC leader dot lines."""
    s = text.strip()
    if len(s) < 4:
        return False
    dots = sum(1 for c in s if c in '.\u00b7\u2026')
    return dots / len(s) > 0.25

def clean_text(text):
    """Clean up extracted text."""
    # Replace tab with space
    text = text.replace('\t', ' ')
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_bullet_text(text):
    """Strip the bullet marker from a SymbolMT line."""
    # Lines start with • and then a tab
    text = text.strip()
    # Remove the bullet char (may be \xe2\x80\xa2 or •)
    if text.startswith('•'):
        text = text[1:]
    # Remove leading tab
    text = text.lstrip('\t').strip()
    return text

def process_column(column_chars, page_width=543):
    """
    Process chars from a single column into a list of (type, text) tuples.

    Steps:
    1. Group chars into lines by y0 (bucket ±2pt)
    2. Sort lines top-to-bottom
    3. Join consecutive continuation lines
    4. Classify each resulting block
    """
    if not column_chars:
        return []

    # Step 1: Group into lines by y0
    lines = defaultdict(list)
    for c in column_chars:
        y_key = round(c['y0'] / 2) * 2  # bucket by 2pt
        lines[y_key].append(c)

    # Step 2: Sort lines top-to-bottom (higher y0 = higher on page in PDF coords)
    sorted_y_keys = sorted(lines.keys(), reverse=True)

    # Step 3: Build structured line list
    structured_lines = []
    for y_key in sorted_y_keys:
        line_chars = sorted(lines[y_key], key=lambda c: c['x0'])
        text = ''.join(c['text'] for c in line_chars)
        if not text.strip():
            continue

        font = line_chars[0]['fontname']
        size = round(line_chars[0]['size'])
        y0 = line_chars[0]['y0']
        x0 = line_chars[0]['x0']
        category = classify_font(font, size)

        structured_lines.append({
            'text': text,
            'font': font,
            'size': size,
            'y0': y0,
            'x0': x0,
            'category': category,
        })

    # Step 4: Join continuation lines
    # A continuation line is: same font category, close y0, and NOT a new heading/bullet
    paragraphs = []
    current = None
    is_bullet_continuation = False

    for line in structured_lines:
        cat = line['category']

        # Skip decorative, footer, toc entries
        if cat in ('decorative', 'footer', 'toc_entry', 'toc_sub'):
            if is_leader_line(line['text']):
                continue
            if cat in ('footer', 'decorative', 'toc_sub'):
                continue
            if cat == 'toc_entry' and is_leader_line(line['text']):
                continue

        # Skip footnote superscripts (very small)
        if line['size'] < 7:
            continue

        # Skip running footer (y0 < 30)
        if line['y0'] < 30:
            continue

        # Is this line a continuation of the previous paragraph?
        is_continuation = False
        if current is not None:
            gap = current['y0'] - line['y0']  # positive = going down
            prev_cat = current['category']

            # A continuation if:
            # - gap is small (same paragraph line spacing)
            # - same or compatible font category
            # - not a new heading
            if cat not in ('chapter_heading', 'section_heading', 'subsection_heading', 'bullet_marker', 'decorative', 'footer'):
                if prev_cat not in ('chapter_heading', 'section_heading', 'subsection_heading'):
                    if 0 < gap <= 20:  # line spacing for 10-12pt text
                        # Check font compatibility
                        same_category = (cat == current['category'])
                        compatible = same_category or (
                            cat in ('body', 'lead_body', 'italic_body', 'bold_body') and
                            prev_cat in ('body', 'lead_body', 'italic_body', 'bold_body')
                        )
                        # Special case: bullet continuation has x0 ~67 (indented)
                        if prev_cat == 'bullet_marker' or is_bullet_continuation:
                            if line['x0'] >= 65:  # indented text = continuation
                                compatible = True
                                is_continuation = True
                                is_bullet_continuation = True
                        elif compatible:
                            is_continuation = True

        if is_continuation and current is not None:
            # Append to current paragraph
            current['text'] = current['text'] + ' ' + clean_text(line['text'])
            current['y0'] = line['y0']  # update y0 to last line
        else:
            # Start new paragraph
            if current is not None:
                paragraphs.append(current)
            is_bullet_continuation = (cat == 'bullet_marker')
            current = dict(line)
            current['text'] = line['text']

    if current is not None:
        paragraphs.append(current)

    return paragraphs

def paragraphs_to_markdown(paragraphs, in_two_col=False):
    """Convert list of paragraph dicts to markdown lines."""
    output_lines = []
    prev_was_bullet = False

    for para in paragraphs:
        cat = para['category']
        text = para['text']
        size = para['size']

        # Skip empties
        if not text.strip():
            continue

        # Skip decorative, footer, etc.
        if cat in ('decorative', 'footer'):
            continue

        if cat == 'toc_entry' and is_leader_line(text):
            continue

        if cat == 'toc_sub':
            continue

        # Clean up text
        clean = clean_text(text)
        if not clean:
            continue

        # Chapter heading (large BebasNeueBold/Book)
        if cat == 'chapter_heading':
            if output_lines and output_lines[-1] != '':
                output_lines.append('')
            output_lines.append(f'## {clean}')
            output_lines.append('')
            prev_was_bullet = False
            continue

        # Section heading
        if cat == 'section_heading':
            if output_lines and output_lines[-1] != '':
                output_lines.append('')
            output_lines.append(f'### {clean}')
            output_lines.append('')
            prev_was_bullet = False
            continue

        # Subsection heading
        if cat == 'subsection_heading':
            if output_lines and output_lines[-1] != '':
                output_lines.append('')
            output_lines.append(f'#### {clean}')
            output_lines.append('')
            prev_was_bullet = False
            continue

        # Bullet marker line
        if cat == 'bullet_marker':
            bullet_text = extract_bullet_text(clean)
            if bullet_text:
                output_lines.append(f'*   {bullet_text}')
            prev_was_bullet = True
            continue

        # Bold body (callout/sidebar)
        if cat == 'bold_body':
            if not prev_was_bullet and output_lines and output_lines[-1] != '':
                output_lines.append('')
            output_lines.append(f'> **{clean}**')
            output_lines.append('')
            prev_was_bullet = False
            continue

        # Italic body
        if cat == 'italic_body':
            if output_lines and output_lines[-1] != '':
                output_lines.append('')
            output_lines.append(f'> *{clean}*')
            output_lines.append('')
            prev_was_bullet = False
            continue

        # Lead body (larger intro text) or regular body
        if cat in ('lead_body', 'body'):
            if output_lines and output_lines[-1] != '':
                output_lines.append('')
            output_lines.append(clean)
            output_lines.append('')
            prev_was_bullet = False
            continue

        # Fallback: treat as body
        if output_lines and output_lines[-1] != '':
            output_lines.append('')
        output_lines.append(clean)
        output_lines.append('')
        prev_was_bullet = False

    return output_lines

def process_page(page, page_num):
    """Process a single page and return markdown lines."""
    chars = page.chars
    if not chars:
        return []

    # Check for two-column layout
    is_two_col = page_num in TWO_COL_PAGES

    # Also auto-detect two-column for other pages
    if not is_two_col:
        body_chars = [c for c in chars if c['text'].strip() and c['y0'] > 30 and c['y0'] < 800]
        if body_chars:
            x0s = [round(c['x0']) for c in body_chars]
            x0_hist = Counter(x0s)
            # Check for gap in 260-330 range
            gap_range = range(260, 330)
            gap_count = sum(1 for x in gap_range if x0_hist.get(x, 0) == 0)
            # Need right-column content (x0 >= 295)
            right_count = sum(1 for x in x0s if x >= 295)
            if gap_count > 40 and right_count > 20:
                is_two_col = True

    output_lines = []

    if is_two_col:
        # Split chars into left and right columns
        left_chars = [c for c in chars if c['x0'] < COL_SPLIT]
        right_chars = [c for c in chars if c['x0'] >= COL_SPLIT]

        # Process each column independently
        left_paragraphs = process_column(left_chars)
        right_paragraphs = process_column(right_chars)

        # Output left column then right column
        left_lines = paragraphs_to_markdown(left_paragraphs, in_two_col=True)
        right_lines = paragraphs_to_markdown(right_paragraphs, in_two_col=True)

        output_lines.extend(left_lines)
        if left_lines and right_lines:
            output_lines.append('')
        output_lines.extend(right_lines)
    else:
        # Single column
        paragraphs = process_column(chars)
        output_lines = paragraphs_to_markdown(paragraphs)

    return output_lines


def main():
    all_lines = ['# Green Party Manifesto 2015', '']

    with pdfplumber.open(PDF_PATH) as pdf:
        print(f'Total pages: {len(pdf.pages)}')

        for page_num in range(len(pdf.pages)):
            if page_num in SKIP_PAGES:
                continue

            page = pdf.pages[page_num]

            try:
                page_lines = process_page(page, page_num)
            except Exception as e:
                print(f'Error on page {page_num+1}: {e}', file=sys.stderr)
                continue

            if page_lines:
                # Add a separator between pages only if content follows
                all_lines.extend(page_lines)

    # Clean up: collapse multiple blank lines into single blank lines
    output = []
    prev_blank = True  # start as True to avoid leading blank lines
    for line in all_lines:
        is_blank = (line.strip() == '')
        if is_blank and prev_blank:
            continue  # skip consecutive blank lines
        output.append(line)
        prev_blank = is_blank

    # Remove trailing blank lines
    while output and output[-1].strip() == '':
        output.pop()

    # Write output
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))
        f.write('\n')

    print(f'Written to {OUT_PATH}')
    print(f'Total lines: {len(output)}')

    # Count bullets
    bullet_lines = [l for l in output if l.startswith('*   ')]
    print(f'Bullet items: {len(bullet_lines)}')

    # Show first few bullets to check
    print('\nFirst 10 bullets:')
    for b in bullet_lines[:10]:
        print(f'  {b[:100]}')

if __name__ == '__main__':
    main()
