#!/usr/bin/env python3
"""Convert Green Party Manifesto 2024 PDF to Markdown.

The PDF uses two-page spreads (1190.55pt wide = 2x A4).
Each spread has two pages, each with up to two text columns.
Left spread page: x0 0-595, Right spread page: x0 595-1190.
Within each page, columns may be at different x offsets.
"""
import pdfplumber
from collections import defaultdict, Counter
import re

PDF_PATH = "/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2024/green/manifesto.pdf"
OUTPUT_PATH = "/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2024/green/manifesto.md"

# Pages to skip (0-indexed)
# Page 0 = cover, Page 1 = intro/foreword (include but label), Page 2 = contents (skip)
# Page 26 = mostly blank/notes header, Page 27 = vote page, Page 28 = back cover
SKIP_PAGES = {2, 25, 26, 27}  # Contents, mostly-blank notes, vote page, back cover

# Decorative watermark text patterns to skip
WATERMARK_PATTERNS = re.compile(r'^[RHeaolCng\s\.\!]+$')

def strip_prefix(fontname):
    if '+' in fontname:
        return fontname.split('+', 1)[1]
    return fontname

def classify_font(fontname, size):
    fn = strip_prefix(fontname)
    
    # Skip watermark/decorative large text
    if 'BebasNeueBold' in fn and size >= 17:
        return 'watermark'
    
    # Skip running headers/footers
    if 'BebasNeueBold' in fn and size <= 13:
        return 'skip'
    
    # Skip page numbers
    if 'Manrope-Medium' in fn and size <= 11:
        return 'skip'
    
    # Skip small footnote text
    if size <= 7:
        return 'skip'
    
    # Chapter headings (BebasNeueBold at 36pt)
    if 'BebasNeueBold' in fn and size >= 30:
        return 'h1'
    
    # Section subheadings (BebasNeueBold at 60pt = special)
    if 'BebasNeueBold' in fn and size >= 50:
        return 'h1'
    
    # Section headings (Manrope-Bold at 16pt, 18pt)
    if 'Manrope-Bold' in fn and size >= 15:
        return 'h2'
    
    # Bullet markers (• at 13pt Manrope-Regular)
    if size >= 12.5 and size <= 13.5:
        return 'bullet_or_body'  # Could be bullet or header-level text
    
    # Small footnote (8.5pt)
    if size <= 9:
        return 'footnote'
    
    # Subheading medium (Manrope-Medium at 12pt = TOC items)
    if 'Manrope-Medium' in fn and size >= 11.5:
        return 'toc'
    
    # Body text
    return 'body'


def is_watermark_text(text):
    """Check if text is part of the decorative watermark."""
    # The watermark is doubled chars like 'RReeaall  HHooppee..'
    if re.match(r'^([A-Za-z\s\.\!\,]+)\1$', text.strip()):
        return True
    # Just doubled letters pattern
    if re.match(r'^([A-Z][a-z]){1,}', text):
        doubled = True
        for i in range(0, len(text)-1, 2):
            if text[i] != text[i+1] and text[i:i+2] not in ('  ', '..', '!!', ',,'):
                doubled = False
                break
        if doubled and len(text) > 2:
            return True
    return False


def chars_to_words(chars):
    """Group chars into words."""
    if not chars:
        return []
    sorted_chars = sorted(chars, key=lambda c: c['x0'])
    words = []
    current_word = [sorted_chars[0]]
    for ch in sorted_chars[1:]:
        prev_ch = current_word[-1]
        gap = ch['x0'] - (prev_ch['x0'] + prev_ch.get('width', prev_ch['size'] * 0.5))
        if gap > 3:
            words.append(current_word)
            current_word = [ch]
        else:
            current_word.append(ch)
    words.append(current_word)
    return words


def find_column_split(chars, page_min_x, page_max_x):
    """Find column split within a half-page of the spread."""
    lines_dict = defaultdict(list)
    for ch in chars:
        if ch['x0'] < page_min_x or ch['x0'] >= page_max_x:
            continue
        y_key = round(ch['y0'] / 2) * 2
        lines_dict[y_key].append(ch)
    
    line_starts = []
    for y_key, lchars in lines_dict.items():
        if y_key < 15 or y_key > 810:
            continue
        sorted_c = sorted(lchars, key=lambda c: c['x0'])
        fn = strip_prefix(sorted_c[0]['fontname'])
        cls = classify_font(fn, sorted_c[0]['size'])
        if cls in ('skip', 'watermark'):
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


def extract_lines_from_column(chars, min_x, max_x):
    """Extract text lines from a column x range."""
    lines_dict = defaultdict(list)
    for ch in chars:
        if ch['x0'] < min_x or ch['x0'] >= max_x:
            continue
        y_key = round(ch['y0'] / 2) * 2
        lines_dict[y_key].append(ch)
    
    lines = []
    for y_key in sorted(lines_dict.keys(), reverse=True):
        line_chars = sorted(lines_dict[y_key], key=lambda c: c['x0'])
        
        if y_key < 15 or y_key > 810:
            continue
        
        fn = strip_prefix(line_chars[0]['fontname'])
        size = line_chars[0]['size']
        cls = classify_font(fn, size)
        
        if cls in ('skip',):
            continue
        
        text = ''.join(c['text'] for c in line_chars).strip()
        
        # Skip watermark text
        if cls == 'watermark':
            continue
        
        if not text:
            continue
        
        lines.append({
            'y0': line_chars[0]['y0'],
            'x0': line_chars[0]['x0'],
            'text': text,
            'cls': cls,
            'size': size,
        })
    
    return lines


def extract_lines_from_column_with_word_split(chars, col_min_x, col_max_x):
    """Extract lines from column, splitting by word-start position."""
    lines_dict = defaultdict(list)
    for ch in chars:
        y_key = round(ch['y0'] / 2) * 2
        lines_dict[y_key].append(ch)
    
    lines = []
    for y_key in sorted(lines_dict.keys(), reverse=True):
        all_line_chars = sorted(lines_dict[y_key], key=lambda c: c['x0'])
        
        if y_key < 15 or y_key > 810:
            continue
        
        fn = strip_prefix(all_line_chars[0]['fontname'])
        size = all_line_chars[0]['size']
        cls = classify_font(fn, size)
        
        if cls in ('skip', 'watermark'):
            continue
        
        # Split words by column
        words = chars_to_words(all_line_chars)
        col_chars = [c for word in words if word[0]['x0'] >= col_min_x and word[0]['x0'] < col_max_x
                     for c in word]
        
        if not col_chars:
            continue
        
        col_sorted = sorted(col_chars, key=lambda c: c['x0'])
        text = ''.join(c['text'] for c in col_sorted).strip()
        
        if not text:
            continue
        
        fn2 = strip_prefix(col_sorted[0]['fontname'])
        size2 = col_sorted[0]['size']
        cls2 = classify_font(fn2, size2)
        
        if cls2 in ('skip', 'watermark'):
            continue
        
        lines.append({
            'y0': col_sorted[0]['y0'],
            'x0': col_sorted[0]['x0'],
            'text': text,
            'cls': cls2,
            'size': size2,
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
        size = line['size']
        
        # Clean text
        clean = text.replace('\xa0', ' ').replace('\t', ' ').strip()
        
        gap = (prev_y0 - y0) if prev_y0 is not None else 999
        
        if not clean:
            prev_y0 = y0
            continue
        
        # Bullet markers
        if cls == 'bullet_or_body':
            if clean == '•' or clean.startswith('• '):
                if current_para:
                    blocks.append(current_para)
                    current_para = None
                if clean == '•':
                    bullet_pending = True
                else:
                    # Bullet with text
                    bullet_text = clean[2:].strip()
                    blocks.append({'type': 'bullet', 'text': bullet_text})
                prev_y0 = y0
                prev_cls = 'bullet_marker'
                continue
            else:
                # Regular text at 13pt - treat as larger body
                cls = 'body'
        
        if cls in ('h1', 'h2'):
            if current_para:
                blocks.append(current_para)
                current_para = None
            bullet_pending = False
            # Merge adjacent same headings
            if blocks and blocks[-1]['type'] == cls and gap <= 60:
                blocks[-1]['text'] += ' ' + clean
            else:
                blocks.append({'type': cls, 'text': clean})
            prev_y0 = y0
            prev_cls = cls
            continue
        
        if bullet_pending:
            if current_para:
                blocks.append(current_para)
                current_para = None
            blocks.append({'type': 'bullet', 'text': clean})
            bullet_pending = False
            prev_y0 = y0
            prev_cls = 'bullet'
            continue
        
        if blocks and blocks[-1]['type'] == 'bullet' and gap <= 16:
            blocks[-1]['text'] += ' ' + clean
            prev_y0 = y0
            prev_cls = cls
            continue
        
        if cls in ('toc', 'footnote'):
            if current_para:
                blocks.append(current_para)
                current_para = None
            if gap <= 14 and blocks and blocks[-1]['type'] == cls:
                blocks[-1]['text'] += ' ' + clean
            else:
                blocks.append({'type': cls, 'text': clean})
            prev_y0 = y0
            prev_cls = cls
            continue
        
        # Body text
        if current_para is None:
            current_para = {'type': 'para', 'text': clean}
        elif gap <= 14:
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
        elif bt == 'bullet':
            md.append(f'*   {text}')
        elif bt == 'footnote':
            md.extend(['', f'*{text}*'])
        elif bt == 'toc':
            pass  # Skip TOC items
        elif bt == 'para':
            md.extend(['', text])
    return md


def process_spread(page):
    """Process a two-page spread PDF page."""
    chars = page.chars
    if not chars:
        return []
    
    bbox_w = page.bbox[2]
    
    if bbox_w < 600:
        # Single page (cover or back cover)
        mid_x = bbox_w
    else:
        mid_x = bbox_w / 2  # ~595.28
    
    # Process left half-page
    left_chars = [c for c in chars if c['x0'] < mid_x]
    # Process right half-page
    right_chars = [c for c in chars if c['x0'] >= mid_x]
    
    all_md = []
    
    for half_chars, page_min_x, page_max_x in [(left_chars, 0, mid_x), (right_chars, mid_x, bbox_w)]:
        if not half_chars:
            continue
        
        # Find if this half has two columns
        split_x = find_column_split(half_chars, page_min_x, page_max_x)
        
        if split_x:
            # Two columns within this half-page
            col1_lines = extract_lines_from_column_with_word_split(half_chars, page_min_x, split_x)
            col2_lines = extract_lines_from_column_with_word_split(half_chars, split_x, page_max_x)
            
            blocks1 = lines_to_blocks(col1_lines)
            blocks2 = lines_to_blocks(col2_lines)
            
            md1 = blocks_to_md(blocks1)
            md2 = blocks_to_md(blocks2)
            
            all_md.extend(md1)
            if md2:
                all_md.extend(md2)
        else:
            # Single column in this half-page
            lines = extract_lines_from_column_with_word_split(half_chars, page_min_x, page_max_x)
            blocks = lines_to_blocks(lines)
            md = blocks_to_md(blocks)
            all_md.extend(md)
    
    return all_md


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
            page_md = process_spread(page)
            
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
