#!/usr/bin/env python3
"""
Convert 2024 Green Party manifesto PDF to Markdown.

Key facts about this PDF:
- 28 pages, each a TWO-PAGE SPREAD (width ≈ 1190.55pt = 2 × A4)
- Each half-page spread uses TWO TEXT COLUMNS
- So each PDF page has FOUR text columns total
- Column layout:
    Left half:  col0 x≈40-285,  col1 x≈300-575
    Right half: col2 x≈638-885, col3 x≈900-1170
- Reading order: col0 → col1 → col2 → col3

Font classification:
- BebasNeueBold @36pt  = chapter heading  → # (h1)
- Manrope-Bold  @16pt  = section heading  → ## (h2)
- Manrope-Bold  @10pt  = subsection       → ### (h3)
- Manrope-Regular @10pt = body text       → paragraph
- Manrope-Regular @11pt = body text       → paragraph (slight size variant)
- Manrope-Regular @13pt = bullet marker • → skip (bullet text is in adjacent spans)
- BebasNeueBold @17pt  = "Real Hope. Real Change." watermark → SKIP
- BebasNeueBold @13pt  = running header   → SKIP
- Manrope-Medium @11pt = page numbers     → SKIP
"""

import pdfplumber
from collections import defaultdict
import re
import sys

PDF_PATH = "/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2024/green/manifesto.pdf"
OUTPUT_PATH = "/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2024/green/manifesto.md"

# Column boundaries (x0 ranges) - determined from diagnostic
# Each PDF page is a two-page spread ≈ 1190.55pt wide
HALF = 595.0

# Column boundaries (start, end)
COLUMNS = [
    (36, 286),    # col0: left half, left column
    (296, 580),   # col1: left half, right column
    (634, 888),   # col2: right half, left column
    (896, 1175),  # col3: right half, right column
]

# Y-range for content (skip headers/footers)
Y_MIN = 22   # below this = footer/page number
Y_MAX = 830  # above this = header

# Line grouping tolerance in pt
Y_BUCKET = 4

# Max vertical gap to consider lines as part of the same block (in pt)
# Body text at 10pt has line spacing ~13-15pt; headings ~20-30pt
CONTINUATION_GAP = 20  # pt - if gap <= this AND same font+size, join lines


def classify_font(fontname, size):
    """Classify a font/size combination."""
    # Strip PDF subset prefix like NVYNNC+
    fname = fontname.split('+')[-1] if '+' in fontname else fontname

    if 'BebasNeue' in fname:
        if size >= 30:
            return 'chapter_heading'
        elif size >= 15:
            return 'watermark'   # "Real Hope. Real Change."
        else:
            return 'running_header'  # chapter name repeated in header
    elif 'Manrope-Bold' in fname:
        if size >= 14:
            return 'section_heading'
        else:
            return 'subsection_heading'
    elif 'Manrope-Medium' in fname:
        if size >= 11:
            return 'page_number'
        else:
            return 'body'
    elif 'Manrope-Regular' in fname:
        if size >= 12:
            return 'bullet_marker'  # • bullets at 13pt
        else:
            return 'body'
    else:
        return 'body'


def extract_column_blocks(chars, col_x_start, col_x_end):
    """
    Extract and return text blocks from one column.

    Returns a list of (font_class, fontname, size, text) tuples,
    where multi-line wrapped text has been joined into single blocks.
    """
    # Filter chars to this column and valid y range
    col_chars = [
        c for c in chars
        if c['x0'] >= col_x_start - 2 and c['x0'] < col_x_end + 2
        and c['top'] >= Y_MIN and c['top'] <= Y_MAX
        and c['text'].strip()
    ]

    if not col_chars:
        return []

    # Group chars into lines by y (top) position with 4pt buckets
    lines_dict = defaultdict(list)
    for c in col_chars:
        # Use 'top' (distance from top of page) for y-ordering
        y_key = round(c['top'] / Y_BUCKET) * Y_BUCKET
        lines_dict[y_key].append(c)

    # Sort lines top-to-bottom
    raw_lines = []
    for y_key in sorted(lines_dict.keys()):
        line_chars = sorted(lines_dict[y_key], key=lambda c: c['x0'])
        text = ''.join(c['text'] for c in line_chars).strip()
        if not text:
            continue
        # Use first char for font classification
        first_char = line_chars[0]
        fontname = first_char['fontname']
        size = round(first_char['size'])
        font_class = classify_font(fontname, size)
        raw_lines.append((y_key, fontname, size, font_class, text))

    # Now join continuation lines (wrapped text)
    # Two lines are continuations if:
    # 1. Same fontname and size (or both 'body' class)
    # 2. Vertical gap <= CONTINUATION_GAP
    # 3. The first line doesn't end a heading (headings don't wrap in same way)
    blocks = []
    i = 0
    while i < len(raw_lines):
        y0, fontname, size, font_class, text = raw_lines[i]

        # Headings: try to join if they are wrapped
        # Body text: join wrapped lines
        if font_class in ('watermark', 'running_header', 'page_number', 'bullet_marker'):
            # Skip these entirely
            i += 1
            continue

        # Accumulate continuation lines
        while i + 1 < len(raw_lines):
            ny0, nfontname, nsize, nfont_class, ntext = raw_lines[i + 1]

            # Skip watermark/header/pagenumber lines
            if nfont_class in ('watermark', 'running_header', 'page_number', 'bullet_marker'):
                i += 1
                continue

            gap = ny0 - y0  # positive = moving down

            # Join if same font+size and within gap threshold
            same_font = (nfontname == fontname and nsize == size)

            if same_font and gap <= CONTINUATION_GAP:
                # Join with space, but handle bullet continuation carefully
                if text.endswith('-'):
                    # Hyphenated word wrap - join without space
                    text = text[:-1] + ntext
                else:
                    text = text + ' ' + ntext
                i += 1
                y0 = ny0
            else:
                break

        blocks.append((font_class, fontname, size, text))
        i += 1

    return blocks


def block_to_markdown(font_class, fontname, size, text):
    """Convert a block to markdown text."""
    # Clean up text
    text = text.strip()
    # Remove double spaces
    text = re.sub(r'  +', ' ', text)

    if font_class == 'chapter_heading':
        return f'# {text}\n'
    elif font_class == 'section_heading':
        return f'## {text}\n'
    elif font_class == 'subsection_heading':
        return f'### {text}\n'
    elif font_class == 'body':
        # Check if this is a bullet item
        if text.startswith('•'):
            bullet_text = text.lstrip('• ').strip()
            return f'*   {bullet_text}\n'
        else:
            return f'{text}\n'
    else:
        return None


def process_pdf():
    """Main processing function."""
    output_lines = ['# Green Party Manifesto 2024\n', '\n']

    with pdfplumber.open(PDF_PATH) as pdf:
        total_pages = len(pdf.pages)
        print(f"Processing {total_pages} pages...")

        for page_idx, page in enumerate(pdf.pages):
            chars = page.chars

            if not chars:
                continue

            print(f"  Page {page_idx + 1}/{total_pages}...", end='', flush=True)

            page_blocks = []

            # Process all 4 columns in reading order
            for col_idx, (col_start, col_end) in enumerate(COLUMNS):
                col_blocks = extract_column_blocks(chars, col_start, col_end)
                page_blocks.extend(col_blocks)

            # Convert blocks to markdown
            prev_class = None
            for font_class, fontname, size, text in page_blocks:
                md = block_to_markdown(font_class, fontname, size, text)
                if md is None:
                    continue

                # Add blank line before headings
                if font_class in ('chapter_heading', 'section_heading', 'subsection_heading'):
                    if output_lines and output_lines[-1] != '\n':
                        output_lines.append('\n')

                output_lines.append(md)

                # Add blank line after headings
                if font_class in ('chapter_heading', 'section_heading', 'subsection_heading'):
                    output_lines.append('\n')
                elif font_class == 'body' and not text.startswith('•'):
                    # Add blank line after body paragraphs (not bullets)
                    output_lines.append('\n')

                prev_class = font_class

            print(f" {len(page_blocks)} blocks")

    return output_lines


def quality_check(output_lines):
    """Perform quality checks on the output."""
    print("\nQuality check:")

    full_text = ''.join(output_lines)

    # Count bullets
    bullet_lines = [l for l in output_lines if l.strip().startswith('*   ')]
    print(f"  Total bullet items: {len(bullet_lines)}")

    # Check for truncated bullets (ending without punctuation or common endings)
    punctuation_endings = {'.', ',', ';', ':', '!', '?', ')', '"', "'", '%', '£', '$'}
    # Also allow lines ending with common words that might not have punctuation
    ok_endings = punctuation_endings | {'and', 'the', 'a', 'of', 'in', 'to', 'for', 'with', 'by', 'at'}

    truncated = []
    for line in bullet_lines:
        text = line.strip().lstrip('*   ').strip()
        if text and text[-1] not in punctuation_endings:
            last_word = text.split()[-1].lower() if text.split() else ''
            if last_word not in ok_endings:
                truncated.append(text[-60:])  # last 60 chars

    truncated_pct = len(truncated) / len(bullet_lines) * 100 if bullet_lines else 0
    print(f"  Bullets without punctuation: {len(truncated)} ({truncated_pct:.1f}%)")

    if truncated[:5]:
        print("  Sample truncated bullets:")
        for t in truncated[:5]:
            print(f"    ...{t}")

    # Check headings
    h1_lines = [l for l in output_lines if l.startswith('# ')]
    h2_lines = [l for l in output_lines if l.startswith('## ')]
    print(f"  H1 headings: {len(h1_lines)}")
    print(f"  H2 headings: {len(h2_lines)}")

    # Check for garbled text (very long lines that might be column mix)
    long_lines = [l for l in output_lines if len(l) > 500]
    print(f"  Lines > 500 chars: {len(long_lines)}")

    return truncated_pct < 20  # Pass if less than 20% truncated


def main():
    print(f"Converting: {PDF_PATH}")
    print(f"Output: {OUTPUT_PATH}")

    output_lines = process_pdf()

    # Quality check
    passed = quality_check(output_lines)

    if passed:
        print("\nQuality check PASSED. Writing output...")
    else:
        print("\nQuality check results shown above. Writing output anyway...")

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)

    print(f"Done. Written {len(output_lines)} lines to {OUTPUT_PATH}")


if __name__ == '__main__':
    main()
