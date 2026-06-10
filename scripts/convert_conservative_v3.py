#!/usr/bin/env python3
"""Convert Conservative Party Manifesto 2024 PDF to Markdown - v3."""
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

def classify_line(fontname, size):
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
        return 'intro_text'  # Large semibold intro (page 8 pullquote)
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


def detect_column_split(lines):
    """Detect column split x position. Returns None if single column."""
    if not lines:
        return None
    
    body_lines = [l for l in lines if l['cls'] not in ('skip', 'bullet_marker', 'h1', 'h2', 'h2_sub', 'h3')]
    if not body_lines:
        return None
    
    x0_vals = sorted(set(round(l['x0'] / 5) * 5 for l in body_lines))
    
    # Check if there's a bimodal distribution
    # Find a gap in x0 values that indicates two columns
    for i in range(len(x0_vals) - 1):
        gap = x0_vals[i+1] - x0_vals[i]
        if gap > 80:  # Large gap indicates column boundary
            split = (x0_vals[i] + x0_vals[i+1]) / 2
            left_count = sum(1 for l in body_lines if l['x0'] < split)
            right_count = sum(1 for l in body_lines if l['x0'] >= split)
            if left_count >= 2 and right_count >= 2:
                return split
    
    return None


def extract_column(lines, min_x=None, max_x=None):
    """Extract lines within a column x range."""
    result = []
    for l in lines:
        x0 = l['x0']
        if min_x is not None and x0 < min_x:
            continue
        if max_x is not None and x0 >= max_x:
            continue
        result.append(l)
    return result


def lines_to_paragraphs(lines):
    """Convert sorted lines into paragraph blocks."""
    if not lines:
        return []
    
    # Sort by y0 descending (top to bottom)
    sorted_lines = sorted(lines, key=lambda l: -l['y0'])
    
    blocks = []
    prev_y0 = None
    prev_cls = None
    current_para = None
    is_bullet_next = False
    
    for line in sorted_lines:
        y0 = line['y0']
        x0 = line['x0']
        text = line['text']
        cls = line['cls']
        
        # Remove ZapfDingbats characters from text
        clean = re.sub(r'[❱\u27f6❯❮►◄▶◀→←]', '', text).replace('\t', ' ').strip()
        
        gap = (prev_y0 - y0) if prev_y0 is not None else 999
        
        if cls == 'bullet_marker':
            if current_para:
                blocks.append(current_para)
                current_para = None
            is_bullet_next = True
            # If marker has text alongside it, use it
            if clean:
                blocks.append({'type': 'bullet', 'text': clean, 'bold': False})
                is_bullet_next = False
            prev_y0 = y0
            prev_cls = cls
            continue
        
        if not clean:
            prev_y0 = y0
            continue
        
        # Headings are always standalone
        if cls in ('h1', 'h2', 'h2_sub', 'h3'):
            if current_para:
                blocks.append(current_para)
                current_para = None
            is_bullet_next = False
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
        
        # Handle bullet items
        if is_bullet_next:
            if current_para:
                blocks.append(current_para)
                current_para = None
            blocks.append({'type': 'bullet', 'text': clean, 'bold': cls == 'bold_body'})
            is_bullet_next = False
            prev_y0 = y0
            prev_cls = cls
            continue
        
        # Continuation of previous bullet item (small gap, same indentation)
        if blocks and blocks[-1]['type'] == 'bullet' and gap <= 16 and prev_cls in ('body', 'bold_body', 'sidebar_body', 'bullet'):
            blocks[-1]['text'] += ' ' + clean
            prev_y0 = y0
            prev_cls = cls
            continue
        
        # Regular body text
        if current_para is None:
            current_para = {'type': 'para', 'text': clean, 'bold': cls == 'bold_body',
                           'is_sidebar': cls == 'sidebar_body', 'is_intro': cls == 'intro_text'}
        elif gap <= 14:
            # Continuation of same paragraph
            current_para['text'] += ' ' + clean
        else:
            # New paragraph
            blocks.append(current_para)
            current_para = {'type': 'para', 'text': clean, 'bold': cls == 'bold_body',
                           'is_sidebar': cls == 'sidebar_body', 'is_intro': cls == 'intro_text'}
        
        prev_y0 = y0
        prev_cls = cls
    
    if current_para:
        blocks.append(current_para)
    
    return blocks


def blocks_to_md(blocks):
    """Convert blocks to markdown lines."""
    md = []
    for b in blocks:
        bt = b['type']
        text = b.get('text', '').strip()
        if not text and bt != 'bullet_pending':
            continue
        
        if bt == 'h1':
            md.append('')
            md.append(f'# {text}')
            md.append('')
        elif bt == 'h2':
            md.append('')
            md.append(f'## {text}')
            md.append('')
        elif bt == 'h2_sub':
            md.append('')
            md.append(f'## {text}')
            md.append('')
        elif bt == 'h3':
            md.append('')
            md.append(f'### {text}')
            md.append('')
        elif bt == 'author':
            md.append(f'*{text}*')
            md.append('')
        elif bt == 'bullet':
            if b.get('bold', False):
                md.append(f'*   **{text}**')
            else:
                md.append(f'*   {text}')
        elif bt == 'para':
            md.append('')
            if b.get('bold', False):
                md.append(f'**{text}**')
            elif b.get('is_intro', False):
                md.append(f'> {text}')  # Use blockquote for intro/pullquote text
            else:
                md.append(text)
    
    return md


def process_page(page, page_num):
    """Process a single page and return markdown lines."""
    lines = get_page_lines(page)
    if not lines:
        return []
    
    split_x = detect_column_split(lines)
    
    if split_x:
        # Process left column, then right column
        left = extract_column(lines, max_x=split_x)
        right = extract_column(lines, min_x=split_x)
        
        left_blocks = lines_to_paragraphs(left)
        right_blocks = lines_to_paragraphs(right)
        
        md = blocks_to_md(left_blocks)
        right_md = blocks_to_md(right_blocks)
        
        if right_md:
            md.append('')
            md.extend(right_md)
        return md
    else:
        blocks = lines_to_paragraphs(lines)
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
                print(f"  Page {page_num+1}: image-only")
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
