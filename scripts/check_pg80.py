import pdfplumber
from collections import defaultdict

def strip_prefix(fontname):
    if '+' in fontname:
        return fontname.split('+', 1)[1]
    return fontname

with pdfplumber.open("/Users/mosmi/Claude/claude-code/british-manifesto-archive/manifestos/2024/conservative/manifesto.pdf") as pdf:
    page = pdf.pages[79]  # page 80
    chars = page.chars
    lines_dict = defaultdict(list)
    for ch in chars:
        y_key = round(ch['y0'] / 2) * 2
        lines_dict[y_key].append(ch)
    
    print("Page 80 all lines:")
    for y_key in sorted(lines_dict.keys(), reverse=True):
        line_chars = sorted(lines_dict[y_key], key=lambda c: c['x0'])
        text = ''.join(c['text'] for c in line_chars).strip()
        if not text:
            continue
        fn = strip_prefix(line_chars[0]['fontname'])
        size = line_chars[0]['size']
        y0 = line_chars[0]['y0']
        print(f"  y0={y0:.0f}, fn={fn}, size={size:.0f}: {text[:60]}")
