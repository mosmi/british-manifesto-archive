#!/usr/bin/env python3
"""Convert Green Party Manifesto 2024 PDF to Markdown - v2.

Two-page spreads: each PDF page is 1190pt wide (2x A4).
Left half: x 0-595, Right half: x 595-1190.
Each half may have 2 columns.
"""
import pdfplumber
from collections import defaultdict, Counter
import re

PDF_PATH = "/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2024/green/manifesto.pdf"
OUTPUT_PATH = "/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2024/green/manifesto.md"

SKIP_PAGES = {2, 25, 26, 27}  # Contents, blank, vote page, back cover

def strip_prefix(fontname):
    if '+' in fontname:
        return fontname.split('+', 1)[1]
    return fontname

def classify_font(fontname, size):
    fn = strip_prefix(fontname)
    if 'BebasNeueBold' in fn and size >= 17:
        return 'watermark'
    if 'BebasNeueBold' in fn:
        return 'skip'
    if 'Manrope-Medium' in fn and size <= 11.5:
        return 'skip'
    if size <= 7:
        return 'skip'
    if 'BebasNeueBold' in fn and size >= 30:
        return 'h1'
    if 'BebasNeueBold' in fn and size >= 50:
        return 'h1'
    if 'Manrope-Bold' in fn and size >= 14:
        return 'h2'
    if 'Manrope-Bold' in fn and size >= 11:
        return 'bold_body'
    if size >= 12.5 and size <= 13.5:
        return 'bullet_line'  # Bullet points are at 13pt
    if size <= 9:
        return 'footnote'
    return 'body'


def chars_to_words(chars):
    """Group chars into words based on x gaps."""
    if not chars:
        return []
    sorted_chars = sorted(chars, key=lambda c: c['x0'])
    words = []
    current_word = [sorted_chars[0]]
    for ch in sorted_chars[1:]:
        prev_ch = current_word[-1]
        gap = ch['x0'] - (prev_ch['x0'] + prev_ch.get('width', prev_ch['size'] * 0.45))
        if gap > 2:
            words.append(current_word)
            current_word = [ch]
        else:
            current_word.append(ch)
    words.append(current_word)
    return words


def find_column_split(chars, min_x, max_x):
    """Find column split x in a page half."""
    lines_dict = defaultdict(list)
    for ch in chars:
        if ch['x0'] < min_x or ch['x0'] >= max_x:
            continue
        if ch['y0'] < 15 or ch['y0'] > 810:
            continue
        y_key = round(ch['y0'] / 2) * 2
        lines_dict[y_key].append(ch)
    
    line_starts = []
    for y_key, lchars in lines_dict.items():
        sorted_c = sorted(lchars, key=lambda c: c['x0'])
        fn = strip_prefix(sorted_c[0]['fontname'])
        cls = classify_font(fn, sorted_c[0]['size'])
        if cls in ('skip', 'watermark'):
            continue
        # Only count line starts for lines with substantial content (>1 char)
        text = ''.join(c['text'] for c in sorted_c).strip()
        if len(text) < 2:
            continue
        line_starts.append(round(sorted_c[0]['x0'] / 5) * 5)
    
    if not line_starts:
        return None
    
    buckets = Counter(line_starts)
    sorted_xs = sorted(buckets.keys())
    
    for i in range(len(sorted_xs) - 1):
        gap = sorted_xs[i+1] - sorted_xs[i]
        if gap > 80:
            split = (sorted_xs[i] + sorted_xs[i+1]) / 2
            left_count = sum(cnt for x, cnt in buckets.items() if x < split)
            right_count = sum(cnt for x, cnt in buckets.items() if x >= split)
            if left_count >= 3 and right_count >= 3:
                return split
    
    return None


def extract_column_lines(chars, col_min_x, col_max_x):
    """Extract text lines from a column, using word-start x for assignment."""
    # Group all chars by y
    lines_dict = defaultdict(list)
    for ch in chars:
        if ch['y0'] < 15 or ch['y0'] > 810:
            continue
        y_key = round(ch['y0'] / 2) * 2
        lines_dict[y_key].append(ch)
    
    lines = []
    for y_key in sorted(lines_dict.keys(), reverse=True):
        all_lchars = sorted(lines_dict[y_key], key=lambda c: c['x0'])
        
        # Split into words and assign to column
        words = chars_to_words(all_lchars)
        col_chars = [c for word in words 
                     if word[0]['x0'] >= col_min_x and word[0]['x0'] < col_max_x
                     for c in word]
        
        if not col_chars:
            continue
        
        col_sorted = sorted(col_chars, key=lambda c: c['x0'])
        text = ''.join(c['text'] for c in col_sorted).strip()
        
        if not text:
            continue
        
        fn = strip_prefix(col_sorted[0]['fontname'])
        size = col_sorted[0]['size']
        cls = classify_font(fn, size)
        
        if cls in ('skip', 'watermark'):
            continue
        
        lines.append({
            'y0': col_sorted[0]['y0'],
            'x0': col_sorted[0]['x0'],
            'text': text,
            'cls': cls,
            'size': size,
        })
    
    return lines


def lines_to_blocks(lines):
    """Convert lines to paragraph blocks with smart merging."""
    blocks = []
    prev_y0 = None
    prev_cls = None
    current_para = None
    bullet_pending = False
    
    for line in lines:
        y0 = line['y0']
        text = line['text']
        cls = line['cls']
        
        clean = text.replace('\xa0', ' ').replace('\t', ' ').strip()
        gap = (prev_y0 - y0) if prev_y0 is not None else 999
        
        if not clean:
            prev_y0 = y0
            continue
        
        # Handle bullet lines
        if cls == 'bullet_line':
            if clean == '•' or clean.startswith('•'):
                if current_para:
                    blocks.append(current_para)
                    current_para = None
                if clean == '•':
                    bullet_pending = True
                else:
                    bullet_text = clean[1:].strip()
                    if bullet_text:
                        blocks.append({'type': 'bullet', 'text': bullet_text})
                    else:
                        bullet_pending = True
                prev_y0 = y0
                prev_cls = 'bullet_marker'
                continue
            else:
                # Regular text at 13pt
                cls = 'body'
        
        # Headings
        if cls in ('h1', 'h2'):
            if current_para:
                blocks.append(current_para)
                current_para = None
            bullet_pending = False
            if blocks and blocks[-1]['type'] == cls and gap <= 60:
                blocks[-1]['text'] += ' ' + clean
            else:
                blocks.append({'type': cls, 'text': clean})
            prev_y0 = y0
            prev_cls = cls
            continue
        
        # Bold body (subheadings within sections)
        if cls == 'bold_body':
            if current_para:
                blocks.append(current_para)
                current_para = None
            bullet_pending = False
            if blocks and blocks[-1]['type'] == 'bold_body' and gap <= 20:
                blocks[-1]['text'] += ' ' + clean
            else:
                blocks.append({'type': 'bold_body', 'text': clean})
            prev_y0 = y0
            prev_cls = cls
            continue
        
        # Bullet pending
        if bullet_pending:
            if current_para:
                blocks.append(current_para)
                current_para = None
            blocks.append({'type': 'bullet', 'text': clean})
            bullet_pending = False
            prev_y0 = y0
            prev_cls = 'bullet'
            continue
        
        # Continue previous bullet
        if blocks and blocks[-1]['type'] == 'bullet' and gap <= 18 and prev_cls == 'bullet':
            blocks[-1]['text'] += ' ' + clean
            prev_y0 = y0
            prev_cls = cls
            continue
        
        # Footnote
        if cls == 'footnote':
            if current_para:
                blocks.append(current_para)
                current_para = None
            if blocks and blocks[-1]['type'] == 'footnote' and gap <= 18:
                blocks[-1]['text'] += ' ' + clean
            else:
                blocks.append({'type': 'footnote', 'text': clean})
            prev_y0 = y0
            prev_cls = cls
            continue
        
        # Regular body paragraph
        if current_para is None:
            current_para = {'type': 'para', 'text': clean}
        elif gap <= 18:
            # Same paragraph (Green PDF uses ~15pt line spacing)
            current_para['text'] += ' ' + clean
        else:
            blocks.append(current_para)
            current_para = {'type': 'para', 'text': clean}
        
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
        elif bt == 'h2':
            md.extend(['', f'## {text}', ''])
        elif bt == 'bold_body':
            md.extend(['', f'**{text}**'])
        elif bt == 'bullet':
            md.append(f'*   {text}')
        elif bt == 'footnote':
            md.extend(['', f'*{text}*'])
        elif bt == 'para':
            md.extend(['', text])
    return md


def process_spread_half(chars, page_min_x, page_max_x):
    """Process one half of a two-page spread."""
    half_chars = [c for c in chars if c['x0'] >= page_min_x and c['x0'] < page_max_x]
    if not half_chars:
        return []
    
    split_x = find_column_split(half_chars, page_min_x, page_max_x)
    
    if split_x:
        col1_lines = extract_column_lines(half_chars, page_min_x, split_x)
        col2_lines = extract_column_lines(half_chars, split_x, page_max_x)
        
        blocks1 = lines_to_blocks(col1_lines)
        blocks2 = lines_to_blocks(col2_lines)
        
        md = blocks_to_md(blocks1)
        md2 = blocks_to_md(blocks2)
        if md2:
            md.extend(md2)
        return md
    else:
        lines = extract_column_lines(half_chars, page_min_x, page_max_x)
        blocks = lines_to_blocks(lines)
        return blocks_to_md(blocks)


def process_page(page):
    """Process a PDF page (may be a single page or two-page spread)."""
    chars = page.chars
    if not chars:
        return []
    
    bbox_w = page.bbox[2]
    
    if bbox_w < 700:
        # Single A4 page
        return process_spread_half(chars, 0, bbox_w)
    else:
        # Two-page spread
        mid_x = bbox_w / 2
        left_md = process_spread_half(chars, 0, mid_x)
        right_md = process_spread_half(chars, mid_x, bbox_w)
        
        md = left_md
        if right_md:
            md.extend(right_md)
        return md


def main():
    output = ['# Green Party Manifesto 2024', '']
    
    with pdfplumber.open(PDF_PATH) as pdf:
        print(f"Total pages: {len(pdf.pages)}")
        
        for page_num, page in enumerate(pdf.pages):
            if page_num in SKIP_PAGES:
                print(f"  Skipping page {page_num+1}")
                continue
            
            if not page.chars:
                print(f"  Page {page_num+1}: no chars")
                continue
            
            print(f"  Processing page {page_num+1}...")
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
