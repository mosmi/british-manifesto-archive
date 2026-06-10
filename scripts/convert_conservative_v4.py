#!/usr/bin/env python3
"""Convert Conservative Party Manifesto 2024 PDF to Markdown - v4.
Key insight: Characters from both columns are at the same y0 coordinates.
We must split chars by x position BEFORE grouping into lines.
"""
import pdfplumber
from collections import defaultdict
import re

PDF_PATH = "/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2024/conservative/manifesto.pdf"
OUTPUT_PATH = "/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2024/conservative/manifesto.md"

SKIP_PAGES = {0, 1, 2, 3}  # Pages 1-4: cover, image-only, contents, image-only

def strip_prefix(fontname):
    if '+' in fontname:
        return fontname.split('+', 1)[1]
    return fontname

def classify_font(fontname, size):
    fn = strip_prefix(fontname)
    if 'ZapfDingbats' in fn:
        return 'bullet_marker'
    if 'ProximaNovaCond-SemiboldIt' in fn:
        return 'skip'
    if size <= 8.5:
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
    if fn == 'ProximaNova-Bold':
        return 'author_name'
    if 'Semibold' in fn and size >= 13:
        return 'pullquote'
    return 'body'


def find_column_split(chars):
    """Find x-coordinate that splits content into two columns."""
    # Get unique x-start positions for non-trivial content
    x0_vals = []
    for ch in chars:
        fn = strip_prefix(ch['fontname'])
        cls = classify_font(fn, ch['size'])
        if cls in ('skip', 'bullet_marker'):
            continue
        if ch['y0'] < 30:
            continue
        x0_vals.append(ch['x0'])
    
    if not x0_vals:
        return None
    
    # Find gaps in x distribution
    x_sorted = sorted(set(round(x/2)*2 for x in x0_vals))
    
    # Look for a gap > 60pt that separates two column regions
    for i in range(len(x_sorted)-1):
        gap = x_sorted[i+1] - x_sorted[i]
        if gap > 60:
            split = (x_sorted[i] + x_sorted[i+1]) / 2
            left = sum(1 for x in x0_vals if x < split)
            right = sum(1 for x in x0_vals if x >= split)
            if left >= 5 and right >= 5:
                return split
    
    return None


def get_column_chars(chars, split_x=None, col='left'):
    """Filter chars for a specific column."""
    if split_x is None:
        return chars
    if col == 'left':
        return [c for c in chars if c['x0'] < split_x]
    else:
        return [c for c in chars if c['x0'] >= split_x]


def chars_to_lines(chars):
    """Group chars into lines by y0 position."""
    lines_dict = defaultdict(list)
    for ch in chars:
        y_key = round(ch['y0'] / 2) * 2
        lines_dict[y_key].append(ch)
    
    lines = []
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
        
        cls = classify_font(fontname, size)
        if cls == 'skip':
            continue
        
        lines.append({
            'y0': y0,
            'x0': x0,
            'text': text,
            'cls': cls,
        })
    
    return lines


def lines_to_blocks(lines):
    """Convert lines to paragraph/heading blocks."""
    blocks = []
    prev_y0 = None
    prev_cls = None
    current_para = None
    bullet_pending = False
    
    for line in lines:
        y0 = line['y0']
        text = line['text']
        cls = line['cls']
        
        # Clean decorative chars
        clean = re.sub(r'[❱\u27f6❯❮►◄▶◀→←]', '', text).replace('\t', ' ').strip()
        
        gap = (prev_y0 - y0) if prev_y0 is not None else 999
        
        if cls == 'bullet_marker':
            if current_para:
                blocks.append(current_para)
                current_para = None
            if clean:
                # Marker has attached text
                blocks.append({'type': 'bullet', 'text': clean, 'bold': False})
            else:
                bullet_pending = True
            prev_y0 = y0
            prev_cls = cls
            continue
        
        if not clean:
            prev_y0 = y0
            continue
        
        # Standalone headings
        if cls in ('h1', 'h2', 'h2_sub', 'h3'):
            if current_para:
                blocks.append(current_para)
                current_para = None
            bullet_pending = False
            blocks.append({'type': cls, 'text': clean})
            prev_y0 = y0
            prev_cls = cls
            continue
        
        if cls == 'author_name':
            if current_para:
                blocks.append(current_para)
                current_para = None
            blocks.append({'type': 'author', 'text': clean})
            prev_y0 = y0
            prev_cls = cls
            continue
        
        # Handle bullet pending
        if bullet_pending:
            if current_para:
                blocks.append(current_para)
                current_para = None
            blocks.append({'type': 'bullet', 'text': clean, 'bold': cls == 'bold_body'})
            bullet_pending = False
            prev_y0 = y0
            prev_cls = cls
            continue
        
        # Continuation of bullet
        if blocks and blocks[-1]['type'] == 'bullet' and gap <= 16 and prev_cls in ('body', 'bold_body', 'sidebar_body', 'pullquote', 'bullet'):
            blocks[-1]['text'] += ' ' + clean
            prev_y0 = y0
            prev_cls = cls
            continue
        
        # Regular paragraph
        if current_para is None:
            current_para = {
                'type': 'para',
                'text': clean,
                'bold': cls == 'bold_body',
                'pullquote': cls == 'pullquote',
            }
        elif gap <= 14:
            current_para['text'] += ' ' + clean
        else:
            blocks.append(current_para)
            current_para = {
                'type': 'para',
                'text': clean,
                'bold': cls == 'bold_body',
                'pullquote': cls == 'pullquote',
            }
        
        prev_y0 = y0
        prev_cls = cls
    
    if current_para:
        blocks.append(current_para)
    
    return blocks


def blocks_to_md(blocks):
    """Convert blocks to markdown."""
    md = []
    for b in blocks:
        bt = b['type']
        text = b.get('text', '').strip()
        if not text:
            continue
        
        if bt == 'h1':
            md.extend(['', f'# {text}', ''])
        elif bt in ('h2', 'h2_sub'):
            md.extend(['', f'## {text}', ''])
        elif bt == 'h3':
            md.extend(['', f'### {text}', ''])
        elif bt == 'author':
            md.extend([f'*{text}*', ''])
        elif bt == 'bullet':
            if b.get('bold'):
                md.append(f'*   **{text}**')
            else:
                md.append(f'*   {text}')
        elif bt == 'para':
            if b.get('bold'):
                md.extend(['', f'**{text}**'])
            elif b.get('pullquote'):
                md.extend(['', f'> {text}'])
            else:
                md.extend(['', text])
    return md


def process_page(page, page_num):
    """Process page with proper column splitting."""
    chars = page.chars
    if not chars:
        return []
    
    # Find column split based on all characters
    split_x = find_column_split(chars)
    
    if split_x:
        # Split characters into two columns
        left_chars = get_column_chars(chars, split_x, 'left')
        right_chars = get_column_chars(chars, split_x, 'right')
        
        left_lines = chars_to_lines(left_chars)
        right_lines = chars_to_lines(right_chars)
        
        left_blocks = lines_to_blocks(left_lines)
        right_blocks = lines_to_blocks(right_lines)
        
        md = blocks_to_md(left_blocks)
        right_md = blocks_to_md(right_blocks)
        if right_md:
            md.extend(['', ''])
            md.extend(right_md)
        return md
    else:
        all_lines = chars_to_lines(chars)
        blocks = lines_to_blocks(all_lines)
        return blocks_to_md(blocks)


def main():
    output = ['# Conservative Party Manifesto 2024', '']
    
    with pdfplumber.open(PDF_PATH) as pdf:
        print(f"Total pages: {len(pdf.pages)}")
        
        for page_num, page in enumerate(pdf.pages):
            if page_num in SKIP_PAGES:
                continue
            
            chars = page.chars
            if not chars:
                continue
            
            page_md = process_page(page, page_num)
            if page_md:
                output.extend(page_md)
                output.append('')
    
    # Clean up multiple blank lines
    final = []
    blanks = 0
    for line in output:
        if line == '':
            blanks += 1
            if blanks <= 2:
                final.append(line)
        else:
            blanks = 0
            final.append(line)
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(final))
    
    print(f"Written {len(final)} lines to {OUTPUT_PATH}")


if __name__ == '__main__':
    main()
