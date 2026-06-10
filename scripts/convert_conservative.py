#!/usr/bin/env python3
"""Convert Conservative Party Manifesto 2024 PDF to Markdown."""
import pdfplumber
from collections import defaultdict
import re

PDF_PATH = "/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2024/conservative/manifesto.pdf"
OUTPUT_PATH = "/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2024/conservative/manifesto.md"

# Pages to skip entirely (0-indexed)
SKIP_PAGES = {0, 1, 2, 3}  # Pages 1-4: cover, image-only, contents, image-only

def strip_prefix(fontname):
    """Strip font prefixes like CAGUPY+ or TLUSTQ+."""
    if '+' in fontname:
        return fontname.split('+', 1)[1]
    return fontname

def classify_line(fontname, size):
    """Classify a line based on font and size."""
    fn = strip_prefix(fontname)
    
    # Skip decorative/navigation elements
    if 'ZapfDingbats' in fn:
        return 'bullet_marker'
    if 'ProximaNovaCond-SemiboldIt' in fn:
        return 'skip'  # Running header
    if fn == 'ProximaNova-Regular' and size <= 8.5:
        return 'skip'  # Page numbers
    if fn == 'ProximaNova-Semibold' and size <= 8.5:
        return 'skip'
    
    # Chapter headings
    if 'M&SLeeds-Bold' in fn and size >= 30:
        return 'h1'
    
    # Sub-headings within chapters (M&SLeeds-Bold at 20pt)
    if 'M&SLeeds-Bold' in fn and size >= 18:
        return 'h2_sub'
    
    # Section headers (ProximaNova-Extrabld at 16pt)
    if 'Extrabld' in fn and size >= 15:
        return 'h2'
    
    # Section intros (ProximaNova-Extrabld at 12pt)
    if 'Extrabld' in fn and size >= 11:
        return 'h3'
    
    # Callout text in sidebars (M&SLeeds-Light and M&SLeeds-Bold at 10pt)
    if 'M&SLeeds' in fn and size <= 11:
        return 'sidebar'
    
    # Bold body text (callouts)
    if 'Extrabld' in fn and size <= 10.5:
        return 'bold_body'
    
    # Semi-bold body
    if 'Semibold' in fn or 'Semibold' in fn:
        return 'body'
    
    # ProximaNova-Bold (Rishi Sunak's name)
    if fn == 'ProximaNova-Bold' and size <= 10.5:
        return 'author_name'
    
    # Regular body
    return 'body'

def group_lines_by_column(lines_dict, page_width=595.28):
    """Group lines into left and right columns based on x0 position."""
    # Determine if page has two columns by checking x0 distribution
    all_x0 = []
    for y_key, chars in lines_dict.items():
        sorted_chars = sorted(chars, key=lambda c: c['x0'])
        x0 = sorted_chars[0]['x0']
        fontname = strip_prefix(sorted_chars[0]['fontname'])
        size = sorted_chars[0]['size']
        cls = classify_line(fontname, size)
        if cls not in ('skip', 'bullet_marker'):
            all_x0.append(x0)
    
    if not all_x0:
        return None
    
    # Check if there's a bimodal distribution suggesting two columns
    # Roughly: left column x0 < 200, right column x0 > 250
    left_count = sum(1 for x in all_x0 if x < 200)
    right_count = sum(1 for x in all_x0 if x > 250)
    
    # If significant right-column content, it's two-column
    if right_count > 3 and left_count > 3:
        return True  # Two-column page
    return False

def process_page(page, page_num):
    """Process a single page and return markdown lines."""
    chars = page.chars
    if not chars:
        return []
    
    # Group chars by y position
    lines_dict = defaultdict(list)
    for ch in chars:
        y_key = round(ch['y0'] / 2) * 2
        lines_dict[y_key].append(ch)
    
    # Collect all lines with their properties
    all_lines = []
    for y_key in sorted(lines_dict.keys(), reverse=True):
        line_chars = sorted(lines_dict[y_key], key=lambda c: c['x0'])
        text_parts = []
        for c in line_chars:
            text_parts.append(c['text'])
        text = ''.join(text_parts).strip()
        
        if not text:
            continue
        
        fontname = strip_prefix(line_chars[0]['fontname'])
        size = line_chars[0]['size']
        y0 = line_chars[0]['y0']
        x0 = line_chars[0]['x0']
        
        # Filter running headers and page numbers (very bottom of page)
        if y0 < 30:
            continue
        
        cls = classify_line(fontname, size)
        
        # Skip running headers and page numbers
        if cls == 'skip':
            continue
        
        # Skip pure bullet markers with no text
        if cls == 'bullet_marker' and len(text.replace('❱', '').strip()) == 0:
            continue
        
        all_lines.append({
            'y0': y0,
            'x0': x0,
            'text': text,
            'fontname': fontname,
            'size': size,
            'cls': cls,
        })
    
    return all_lines

def lines_to_markdown(all_lines):
    """Convert processed lines to markdown text."""
    md_lines = []
    prev_y0 = None
    prev_cls = None
    in_bullet_list = False
    pending_bullet_text = None
    
    # Check for two-column layout
    # Separate left and right column content based on x0 cutoff
    left_lines = [l for l in all_lines if l['x0'] < 230]
    right_lines = [l for l in all_lines if l['x0'] >= 230]
    
    # If we have significant content in both columns, process left then right
    # But first check if there's a sidebar box (M&SLeeds fonts at 10pt)
    has_sidebar = any(l['cls'] == 'sidebar' for l in all_lines)
    has_left = len([l for l in left_lines if l['cls'] not in ('bullet_marker',)]) > 2
    has_right = len([l for l in right_lines if l['cls'] not in ('bullet_marker',)]) > 2
    
    if has_left and has_right and not has_sidebar:
        # Two-column layout without sidebar: interleave by y position (they're already sorted by y)
        # Process as single stream (already sorted by y0 descending)
        lines_to_process = sorted(all_lines, key=lambda l: -l['y0'])
    elif has_sidebar:
        # Sidebar present: process left column (sidebar) then right column (body)
        # Identify sidebar column (typically x0 < 200 and M&SLeeds font)
        sidebar_lines = [l for l in all_lines if l['cls'] == 'sidebar']
        body_lines = [l for l in all_lines if l['cls'] != 'sidebar']
        lines_to_process = sorted(body_lines, key=lambda l: -l['y0'])
    else:
        lines_to_process = sorted(all_lines, key=lambda l: -l['y0'])
    
    i = 0
    while i < len(lines_to_process):
        line = lines_to_process[i]
        y0 = line['y0']
        x0 = line['x0']
        text = line['text']
        cls = line['cls']
        
        # Check gap from previous line for paragraph breaks
        gap = (prev_y0 - y0) if prev_y0 is not None else 0
        
        # Handle bullet marker
        if cls == 'bullet_marker':
            # The bullet text should be on the next line(s)
            pending_bullet_text = ''
            prev_y0 = y0
            prev_cls = cls
            i += 1
            continue
        
        # Clean text - remove ZapfDingbats chars
        clean_text = text.replace('❱', '').replace('\t', ' ').strip()
        if not clean_text:
            prev_y0 = y0
            i += 1
            continue
        
        # Format based on classification
        if cls == 'h1':
            if in_bullet_list:
                md_lines.append('')
                in_bullet_list = False
            md_lines.append('')
            md_lines.append(f'# {clean_text}')
            pending_bullet_text = None
        elif cls == 'h2_sub':
            if in_bullet_list:
                md_lines.append('')
                in_bullet_list = False
            md_lines.append('')
            md_lines.append(f'## {clean_text}')
            pending_bullet_text = None
        elif cls == 'h2':
            if in_bullet_list:
                md_lines.append('')
                in_bullet_list = False
            md_lines.append('')
            md_lines.append(f'## {clean_text}')
            pending_bullet_text = None
        elif cls == 'h3':
            if in_bullet_list:
                md_lines.append('')
                in_bullet_list = False
            md_lines.append('')
            md_lines.append(f'### {clean_text}')
            pending_bullet_text = None
        elif cls == 'author_name':
            md_lines.append('')
            md_lines.append(f'*{clean_text}*')
            pending_bullet_text = None
        elif cls == 'bold_body':
            # Check if previous line was a bullet_marker - then this is a bullet item
            if prev_cls == 'bullet_marker' or pending_bullet_text is not None:
                in_bullet_list = True
                md_lines.append(f'*   **{clean_text}**')
                pending_bullet_text = None
            else:
                # Check gap - if large gap, new paragraph
                if gap > 16 and prev_cls not in ('h1', 'h2', 'h2_sub', 'h3', 'bullet_marker'):
                    md_lines.append('')
                md_lines.append(f'**{clean_text}**')
                pending_bullet_text = None
        else:  # body, sidebar, etc.
            if prev_cls == 'bullet_marker' or pending_bullet_text is not None:
                in_bullet_list = True
                md_lines.append(f'*   {clean_text}')
                pending_bullet_text = None
            elif in_bullet_list and gap <= 14 and prev_cls in ('bold_body', 'body', 'sidebar'):
                # Continuation of bullet item
                if md_lines and md_lines[-1].startswith('*   '):
                    md_lines[-1] = md_lines[-1] + ' ' + clean_text
                else:
                    md_lines.append(f'    {clean_text}')
            else:
                # Regular body paragraph
                if gap > 16 and prev_cls not in ('h1', 'h2', 'h2_sub', 'h3', 'author_name', 'bullet_marker'):
                    if in_bullet_list:
                        md_lines.append('')
                        in_bullet_list = False
                    md_lines.append('')
                
                if md_lines and not md_lines[-1].startswith('#') and not md_lines[-1] == '' and gap <= 14:
                    # Continuation of previous body line
                    if not md_lines[-1].startswith('*   ') and not md_lines[-1].startswith('**'):
                        md_lines[-1] = md_lines[-1] + ' ' + clean_text
                    else:
                        md_lines.append(clean_text)
                else:
                    md_lines.append(clean_text)
        
        prev_y0 = y0
        prev_cls = cls
        i += 1
    
    return md_lines


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
            
            all_lines = process_page(page, page_num)
            page_md = lines_to_markdown(all_lines)
            
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
    
    # Fix word-join artifacts: ensure space before capital letters after lowercase
    # but preserve headers and markdown syntax
    text = '\n'.join(final_lines)
    
    # Write output
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(text)
    
    print(f"\nDone! Written to {OUTPUT_PATH}")
    print(f"Total lines: {len(final_lines)}")

if __name__ == '__main__':
    main()
