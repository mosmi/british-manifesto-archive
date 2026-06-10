#!/usr/bin/env python3
"""Convert Conservative Party Manifesto 2024 PDF to Markdown - v5.
Uses line-start x positions for accurate column detection.
"""
import pdfplumber
from collections import defaultdict, Counter
import re

PDF_PATH = "/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2024/conservative/manifesto.pdf"
OUTPUT_PATH = "/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2024/conservative/manifesto.md"

SKIP_PAGES = {0, 1, 2, 3}  # 0-indexed

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
    """Find column split x using line-start positions."""
    lines_dict = defaultdict(list)
    for ch in chars:
        y_key = round(ch['y0'] / 2) * 2
        lines_dict[y_key].append(ch)
    
    line_starts = []
    for y_key, lchars in lines_dict.items():
        if y_key < 30:
            continue
        sorted_c = sorted(lchars, key=lambda c: c['x0'])
        fn = strip_prefix(sorted_c[0]['fontname'])
        cls = classify_font(fn, sorted_c[0]['size'])
        if cls in ('skip',):
            continue
        line_starts.append(round(sorted_c[0]['x0'] / 5) * 5)
    
    if not line_starts:
        return None
    
    # Find gaps
    buckets = Counter(line_starts)
    sorted_xs = sorted(buckets.keys())
    
    for i in range(len(sorted_xs) - 1):
        gap = sorted_xs[i+1] - sorted_xs[i]
        if gap > 80:
            split = (sorted_xs[i] + sorted_xs[i+1]) / 2
            left_count = sum(cnt for x, cnt in buckets.items() if x < split)
            right_count = sum(cnt for x, cnt in buckets.items() if x >= split)
            if left_count >= 5 and right_count >= 5:
                return split
    
    return None


def chars_to_lines(chars, split_x=None, col='all'):
    """Group chars into lines, optionally filtering by column."""
    # First split chars by column if needed
    if split_x is not None:
        if col == 'left':
            chars = [c for c in chars if c['x0'] < split_x]
        elif col == 'right':
            chars = [c for c in chars if c['x0'] >= split_x]
    
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
    """Convert lines to paragraph blocks."""
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
                blocks.append({'type': 'bullet', 'text': clean, 'bold': False})
            else:
                bullet_pending = True
            prev_y0 = y0
            prev_cls = cls
            continue
        
        if not clean:
            prev_y0 = y0
            continue
        
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
        
        if bullet_pending:
            if current_para:
                blocks.append(current_para)
                current_para = None
            blocks.append({'type': 'bullet', 'text': clean, 'bold': cls == 'bold_body'})
            bullet_pending = False
            prev_y0 = y0
            prev_cls = cls
            continue
        
        if blocks and blocks[-1]['type'] == 'bullet' and gap <= 16:
            blocks[-1]['text'] += ' ' + clean
            prev_y0 = y0
            prev_cls = cls
            continue
        
        if current_para is None:
            current_para = {
                'type': 'para', 'text': clean,
                'bold': cls == 'bold_body',
                'pullquote': cls == 'pullquote',
            }
        elif gap <= 14:
            current_para['text'] += ' ' + clean
        else:
            blocks.append(current_para)
            current_para = {
                'type': 'para', 'text': clean,
                'bold': cls == 'bold_body',
                'pullquote': cls == 'pullquote',
            }
        
        prev_y0 = y0
        prev_cls = cls
    
    if current_para:
        blocks.append(current_para)
    
    return blocks


def blocks_to_md(blocks):
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


def process_page(page):
    chars = page.chars
    if not chars:
        return []
    
    split_x = find_column_split(chars)
    
    if split_x:
        left_lines = chars_to_lines(chars, split_x, 'left')
        right_lines = chars_to_lines(chars, split_x, 'right')
        
        left_blocks = lines_to_blocks(left_lines)
        right_blocks = lines_to_blocks(right_lines)
        
        md = blocks_to_md(left_blocks)
        right_md = blocks_to_md(right_blocks)
        if right_md:
            md.extend(['', ''])
            md.extend(right_md)
        return md
    else:
        lines = chars_to_lines(chars)
        blocks = lines_to_blocks(lines)
        return blocks_to_md(blocks)


def main():
    output = ['# Conservative Party Manifesto 2024', '']
    
    with pdfplumber.open(PDF_PATH) as pdf:
        print(f"Total pages: {len(pdf.pages)}")
        
        for page_num, page in enumerate(pdf.pages):
            if page_num in SKIP_PAGES:
                continue
            
            if not page.chars:
                continue
            
            page_md = process_page(page)
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
