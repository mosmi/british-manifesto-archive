#!/usr/bin/env python3
"""Convert Conservative Party Manifesto 2024 PDF to Markdown - v2 with proper column handling."""
import pdfplumber
from collections import defaultdict
import re

PDF_PATH = "/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2024/conservative/manifesto.pdf"
OUTPUT_PATH = "/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2024/conservative/manifesto.md"

# Pages to skip entirely (0-indexed)
SKIP_PAGES = {0, 1, 2, 3}  # Pages 1-4: cover, image-only, contents, image-only

def strip_prefix(fontname):
    if '+' in fontname:
        return fontname.split('+', 1)[1]
    return fontname

def classify_line(fontname, size):
    fn = strip_prefix(fontname)
    if 'ZapfDingbats' in fn:
        return 'bullet_marker'
    if 'ProximaNovaCond-SemiboldIt' in fn:
        return 'skip'
    if size <= 8.5 and fn in ('ProximaNova-Regular', 'ProximaNova-Semibold'):
        return 'skip'
    if 'M&SLeeds-Bold' in fn and size >= 30:
        return 'h1'
    if 'M&SLeeds-Bold' in fn and size >= 18:
        return 'h2_sub'
    if 'Extrabld' in fn and size >= 15:
        return 'h2'
    if 'Extrabld' in fn and size >= 11:
        return 'h3'
    if 'M&SLeeds' in fn:
        return 'sidebar_body'
    if 'Extrabld' in fn:
        return 'bold_body'
    if fn == 'ProximaNova-Bold' and size <= 10.5:
        return 'author_name'
    if 'Semibold' in fn:
        return 'body'
    return 'body'


def get_page_lines(page):
    """Extract all text lines from a page with metadata."""
    chars = page.chars
    if not chars:
        return []
    
    lines_dict = defaultdict(list)
    for ch in chars:
        y_key = round(ch['y0'] / 2) * 2
        lines_dict[y_key].append(ch)
    
    result = []
    for y_key in sorted(lines_dict.keys(), reverse=True):
        line_chars = sorted(lines_dict[y_key], key=lambda c: c['x0'])
        text = ''.join(c['text'] for c in line_chars).strip()
        if not text:
            continue
        
        fontname = strip_prefix(line_chars[0]['fontname'])
        size = line_chars[0]['size']
        y0 = line_chars[0]['y0']
        x0 = line_chars[0]['x0']
        
        if y0 < 30:
            continue
        
        cls = classify_line(fontname, size)
        if cls == 'skip':
            continue
        
        result.append({
            'y0': y0,
            'x0': x0,
            'text': text,
            'fontname': fontname,
            'size': size,
            'cls': cls,
        })
    
    return result


def detect_columns(lines):
    """Detect if page has two text columns and return column split x."""
    if not lines:
        return None
    
    # Get non-header x positions
    body_lines = [l for l in lines if l['cls'] in ('body', 'bold_body', 'sidebar_body', 'bullet_marker')]
    if not body_lines:
        return None
    
    # Look at x0 distribution
    x0_vals = [l['x0'] for l in body_lines]
    
    # Find the gap between columns
    # Left column typically starts at ~40-70
    # Right column typically starts at ~265-360
    left = [x for x in x0_vals if x < 230]
    right = [x for x in x0_vals if x > 240]
    
    if len(left) >= 3 and len(right) >= 3:
        # Two-column layout detected
        # Find split point
        split = 240
        return split
    
    return None


def split_into_columns(lines, split_x):
    """Split lines into left and right columns."""
    left = []
    right = []
    
    for line in lines:
        if line['x0'] < split_x:
            left.append(line)
        else:
            right.append(line)
    
    return left, right


def lines_to_text_blocks(lines):
    """Convert a sequence of lines into text blocks for markdown."""
    blocks = []
    
    i = 0
    prev_y0 = None
    prev_cls = None
    current_block = None
    
    while i < len(lines):
        line = lines[i]
        y0 = line['y0']
        text = line['text']
        cls = line['cls']
        
        # Clean up text
        clean = text.replace('❱', '').replace('\t', ' ').strip()
        
        # Handle bullet marker - next line is bullet content
        if cls == 'bullet_marker':
            if current_block:
                blocks.append(current_block)
                current_block = None
            # Look at bullet text from the marker line itself (if any)
            bullet_text = clean
            if bullet_text:
                # Marker has text attached - treat as bullet
                blocks.append({'type': 'bullet', 'text': bullet_text, 'y0': y0})
            else:
                # Pure marker - flag next line as bullet
                blocks.append({'type': 'bullet_pending', 'y0': y0})
            prev_y0 = y0
            prev_cls = 'bullet_marker'
            i += 1
            continue
        
        if not clean:
            prev_y0 = y0
            i += 1
            continue
        
        gap = (prev_y0 - y0) if prev_y0 is not None else 999
        
        # Heading types always standalone
        if cls in ('h1', 'h2', 'h2_sub', 'h3', 'author_name'):
            if current_block:
                blocks.append(current_block)
                current_block = None
            blocks.append({'type': cls, 'text': clean, 'y0': y0})
            prev_y0 = y0
            prev_cls = cls
            i += 1
            continue
        
        # Check if this should be a bullet (previous was bullet_pending or bullet_marker)
        if blocks and blocks[-1]['type'] == 'bullet_pending':
            blocks[-1] = {'type': 'bullet', 'text': clean, 'y0': y0, 'bold': cls == 'bold_body'}
            prev_y0 = y0
            prev_cls = cls
            i += 1
            continue
        
        # Continuation of bullet text?
        if blocks and blocks[-1]['type'] == 'bullet' and gap <= 16 and prev_cls in ('bold_body', 'body', 'sidebar_body'):
            blocks[-1]['text'] += ' ' + clean
            prev_y0 = y0
            prev_cls = cls
            i += 1
            continue
        
        # Regular body text
        if current_block is None:
            current_block = {'type': 'para', 'text': clean, 'y0': y0, 'bold': cls == 'bold_body'}
        elif gap <= 14:
            # Same paragraph - join
            current_block['text'] += ' ' + clean
        else:
            # New paragraph
            blocks.append(current_block)
            current_block = {'type': 'para', 'text': clean, 'y0': y0, 'bold': cls == 'bold_body'}
        
        prev_y0 = y0
        prev_cls = cls
        i += 1
    
    if current_block:
        blocks.append(current_block)
    
    return blocks


def blocks_to_markdown(blocks):
    """Convert text blocks to markdown lines."""
    md = []
    for block in blocks:
        btype = block['type']
        text = block.get('text', '').strip()
        
        if not text and btype not in ('bullet_pending',):
            continue
        
        if btype == 'h1':
            md.append('')
            md.append(f'# {text}')
            md.append('')
        elif btype == 'h2':
            md.append('')
            md.append(f'## {text}')
            md.append('')
        elif btype == 'h2_sub':
            md.append('')
            md.append(f'## {text}')
            md.append('')
        elif btype == 'h3':
            md.append('')
            md.append(f'### {text}')
            md.append('')
        elif btype == 'author_name':
            md.append('')
            md.append(f'*{text}*')
        elif btype == 'bullet':
            bold = block.get('bold', False)
            if bold:
                md.append(f'*   **{text}**')
            else:
                md.append(f'*   {text}')
        elif btype == 'bullet_pending':
            pass  # Skip orphaned bullet markers
        elif btype == 'para':
            bold = block.get('bold', False)
            md.append('')
            if bold:
                md.append(f'**{text}**')
            else:
                md.append(text)
    
    return md


def process_page_to_markdown(page, page_num):
    """Process a page and return markdown lines."""
    lines = get_page_lines(page)
    if not lines:
        return []
    
    split_x = detect_columns(lines)
    
    if split_x:
        # Two-column layout: process each column separately
        left_lines, right_lines = split_into_columns(lines, split_x)
        
        # Sort each column by y0 descending (top to bottom)
        left_lines.sort(key=lambda l: -l['y0'])
        right_lines.sort(key=lambda l: -l['y0'])
        
        # Convert each column
        left_blocks = lines_to_text_blocks(left_lines)
        right_blocks = lines_to_text_blocks(right_lines)
        
        left_md = blocks_to_markdown(left_blocks)
        right_md = blocks_to_markdown(right_blocks)
        
        # Combine: left column first, then right column
        result = left_md
        if right_md:
            result.append('')
            result.extend(right_md)
        return result
    else:
        # Single column
        lines.sort(key=lambda l: -l['y0'])
        blocks = lines_to_text_blocks(lines)
        return blocks_to_markdown(blocks)


def main():
    output_lines = ['# Conservative Party Manifesto 2024', '']
    
    with pdfplumber.open(PDF_PATH) as pdf:
        print(f"Processing {len(pdf.pages)} pages...")
        
        for page_num, page in enumerate(pdf.pages):
            if page_num in SKIP_PAGES:
                print(f"  Skipping page {page_num+1}")
                continue
            
            chars = page.chars
            if not chars:
                print(f"  Page {page_num+1}: image-only, skipping")
                continue
            
            print(f"  Processing page {page_num+1}...")
            page_md = process_page_to_markdown(page, page_num)
            
            if page_md:
                output_lines.extend(page_md)
                output_lines.append('')
    
    # Post-process: clean up multiple blank lines
    final_lines = []
    blank_count = 0
    for line in output_lines:
        if line == '':
            blank_count += 1
            if blank_count <= 2:
                final_lines.append(line)
        else:
            blank_count = 0
            final_lines.append(line)
    
    # Write output
    text = '\n'.join(final_lines)
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(text)
    
    print(f"\nDone! Written to {OUTPUT_PATH}")
    print(f"Total lines: {len(final_lines)}")


if __name__ == '__main__':
    main()
