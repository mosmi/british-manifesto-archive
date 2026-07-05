#!/usr/bin/env python3
"""
check_headings.py — Extract and verify headings from a manifesto PDF.

Two modes:

  1. EXTRACT mode (no markdown file given):
     Prints every heading found in the PDF, one per line, so you can
     check them against your markdown manually.

  2. VERIFY mode (markdown file given):
     Compares every PDF heading against the markdown and reports any
     that are missing or appear to have been altered.

Usage:
    python check_headings.py input.pdf
    python check_headings.py input.pdf output.md
    python check_headings.py input.pdf output.md --size-threshold 8

Options:
    --size-threshold N    Minimum font size (pt) to treat as a heading
                          (default: 7.5). Lower = more headings included;
                          raise if you're getting too much body text.
    --skip-pages N,N      Comma-separated 0-indexed page numbers to skip
                          (e.g. cover, contents pages).
    --header-cut N        Ignore text with top < N pt (strips running headers).
                          Default: 30.
    --footer-cut N        Ignore text with top > N pt from page bottom.
                          Default: 30.

How headings are extracted:
    The script buckets characters by y-coordinate and groups them into
    lines. A line is classified as a heading if its maximum character
    font size is >= size-threshold AND it is not a running header/footer.
    Characters at the same y-bucket across multiple columns are kept
    separate by x-position clustering, so that side-by-side headings
    (common in multi-column landscape PDFs) are reported individually.

Exit codes:
    0  All PDF headings found in markdown (verify mode), or extract done.
    1  One or more PDF headings missing or altered in markdown (verify mode).
"""

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber not installed. Run: pip install pdfplumber --break-system-packages",
          file=sys.stderr)
    sys.exit(1)


# ── Utilities ────────────────────────────────────────────────────────────────

def bucket(val, tol=3):
    return round(val / tol) * tol


def normalise(text):
    """Lowercase and collapse whitespace for fuzzy matching."""
    return re.sub(r'\s+', ' ', text).strip().lower()


def strip_markdown(text):
    """Remove markdown heading markers, bold, italic, bullet markers."""
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    text = re.sub(r'^[-*]\s+', '', text, flags=re.MULTILINE)
    return text


# ── Column splitting ─────────────────────────────────────────────────────────

def split_into_columns(chars, min_gap=15, bucket_size=5):
    """
    Given a list of chars on the same y-row, split them into per-column
    groups by detecting horizontal gaps >= min_gap pt.

    Returns a list of lists (one per column), each sorted by x0.
    """
    if not chars:
        return []
    chars_sorted = sorted(chars, key=lambda c: c['x0'])

    groups = [[chars_sorted[0]]]
    for c in chars_sorted[1:]:
        gap = c['x0'] - groups[-1][-1]['x1']
        if gap >= min_gap:
            groups.append([])
        groups[-1].append(c)
    return groups


# ── Heading extraction ───────────────────────────────────────────────────────

def extract_headings(pdf_path, size_threshold, skip_pages, header_cut, footer_cut):
    """
    Return a list of (page_num, heading_text) tuples for every heading
    found in the PDF.
    """
    headings = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            if page_num in skip_pages:
                continue

            page_height = page.height
            y_footer = page_height - footer_cut

            # Bucket chars by y
            chars_by_y = defaultdict(list)
            for c in page.chars:
                if not c['text'].strip():
                    continue
                top = c['top']
                if top < header_cut or top > y_footer:
                    continue
                chars_by_y[bucket(top)].append(c)

            for y in sorted(chars_by_y.keys()):
                row_chars = chars_by_y[y]
                max_size = max(c.get('size', 0) for c in row_chars)
                if max_size < size_threshold:
                    continue

                # Only keep the heading-size characters (filter out body
                # text that happens to share a y-row with a heading)
                heading_chars = [c for c in row_chars if c.get('size', 0) >= size_threshold]
                if not heading_chars:
                    continue

                # Split into column groups to avoid merging side-by-side headings
                col_groups = split_into_columns(heading_chars)
                for group in col_groups:
                    text = ''.join(c['text'] for c in sorted(group, key=lambda c: c['x0'])).strip()
                    if text and len(text) > 1:
                        headings.append((page_num, text))

    # Merge consecutive heading fragments from the same page that are
    # clearly part of the same heading (same column position, small y gap).
    # We do a simple pass: if two consecutive entries share the same page
    # and the text looks like a continuation (no punctuation end on first,
    # or first ends with a hyphen), merge them.
    merged = []
    i = 0
    while i < len(headings):
        pg, txt = headings[i]
        # Look ahead for continuation lines on the same page
        while (i + 1 < len(headings)
               and headings[i + 1][0] == pg
               and not re.search(r'[.!?]$', txt.rstrip())):
            next_txt = headings[i + 1][1]
            # Only merge if the next fragment also looks like a heading
            # (short and no sentence-ending punctuation)
            if len(next_txt.split()) <= 8 and not re.search(r'^[a-z]', next_txt):
                txt = txt.rstrip('-').rstrip() + ' ' + next_txt
                i += 1
            else:
                break
        merged.append((pg, txt))
        i += 1

    return merged


# ── Markdown heading extraction ───────────────────────────────────────────────

def extract_md_headings(md_path):
    """Return a list of heading texts from a markdown file (stripped of # markers)."""
    headings = []
    with open(md_path, encoding='utf-8') as f:
        for line in f:
            m = re.match(r'^#{1,6}\s+(.+)', line.rstrip())
            if m:
                headings.append(m.group(1).strip())
    return headings


# ── Verification ─────────────────────────────────────────────────────────────

def verify_headings(pdf_headings, md_headings):
    """
    For each PDF heading, check whether it appears (verbatim or close match)
    in the markdown headings list.

    Returns (ok_list, problem_list) where each item is a dict with keys:
        pdf_text, md_match (or None), issue
    """
    md_norms = [(normalise(h), h) for h in md_headings]
    # Also build a flat normalised string of all markdown heading text for
    # substring searches (catches headings that have been partially merged)
    md_flat = ' | '.join(normalise(h) for h in md_headings)

    ok = []
    problems = []

    for page_num, pdf_text in pdf_headings:
        pdf_norm = normalise(pdf_text)

        # 1. Exact normalised match
        exact = [orig for norm, orig in md_norms if norm == pdf_norm]
        if exact:
            ok.append({'page': page_num, 'pdf_text': pdf_text,
                       'md_match': exact[0], 'issue': None})
            continue

        # 2. PDF heading is a substring of a markdown heading (e.g. multi-line merge)
        sub_match = [orig for norm, orig in md_norms if pdf_norm in norm]
        if sub_match:
            ok.append({'page': page_num, 'pdf_text': pdf_text,
                       'md_match': sub_match[0], 'issue': None})
            continue

        # 3. Markdown heading contains the PDF heading
        super_match = [orig for norm, orig in md_norms if norm in pdf_norm]
        if super_match:
            # The markdown heading is a truncation of the PDF heading — flag it
            problems.append({'page': page_num, 'pdf_text': pdf_text,
                              'md_match': super_match[0],
                              'issue': 'TRUNCATED in markdown'})
            continue

        # 4. Fuzzy: check if key words from the PDF heading appear in md headings
        words = [w for w in pdf_norm.split() if len(w) > 3]
        if words:
            best_score = 0
            best_orig = None
            for norm, orig in md_norms:
                score = sum(1 for w in words if w in norm) / len(words)
                if score > best_score:
                    best_score, best_orig = score, orig
            if best_score >= 0.6:
                problems.append({'page': page_num, 'pdf_text': pdf_text,
                                  'md_match': best_orig,
                                  'issue': f'ALTERED (word overlap {best_score:.0%})'})
                continue

        # 5. No match at all
        problems.append({'page': page_num, 'pdf_text': pdf_text,
                          'md_match': None, 'issue': 'NOT FOUND in markdown'})

    return ok, problems


# ── Main ─────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(
        description='Extract and verify manifesto headings from a PDF.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    p.add_argument('input_pdf', help='Path to the PDF file')
    p.add_argument('output_md', nargs='?', help='Path to the Markdown file to verify against')
    p.add_argument('--size-threshold', type=float, default=7.5,
                   help='Minimum font size (pt) to treat as a heading (default: 7.5)')
    p.add_argument('--skip-pages', default='',
                   help='Comma-separated 0-indexed page numbers to skip')
    p.add_argument('--header-cut', type=float, default=30,
                   help='Ignore text with top < N pt (default: 30)')
    p.add_argument('--footer-cut', type=float, default=30,
                   help='Ignore text in the bottom N pt of each page (default: 30)')
    return p.parse_args()


def main():
    args = parse_args()

    pdf_path = Path(args.input_pdf)
    if not pdf_path.exists():
        print(f"ERROR: File not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    skip_pages = set()
    if args.skip_pages:
        for s in args.skip_pages.split(','):
            s = s.strip()
            if s.isdigit():
                skip_pages.add(int(s))

    print(f"Extracting headings from: {pdf_path}")
    print(f"  Size threshold : {args.size_threshold} pt")
    print(f"  Skip pages     : {sorted(skip_pages) or 'none'}")
    print()

    pdf_headings = extract_headings(
        pdf_path,
        size_threshold=args.size_threshold,
        skip_pages=skip_pages,
        header_cut=args.header_cut,
        footer_cut=args.footer_cut,
    )

    if not args.output_md:
        # EXTRACT mode: just print the headings
        print("=== Headings found in PDF ===")
        print()
        for page_num, text in pdf_headings:
            print(f"  [p{page_num}] {text}")
        print()
        print(f"Total: {len(pdf_headings)} heading(s) found.")
        print()
        print("To verify against a markdown file, run:")
        print(f"  python check_headings.py {pdf_path} your_output.md")
        return

    # VERIFY mode
    md_path = Path(args.output_md)
    if not md_path.exists():
        print(f"ERROR: Markdown file not found: {md_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Verifying against  : {md_path}")
    print()

    md_headings = extract_md_headings(md_path)
    ok, problems = verify_headings(pdf_headings, md_headings)

    # Print problems grouped by page
    if problems:
        # Collect unique pages with issues, in order
        pages_with_issues = []
        seen_pages = set()
        for item in problems:
            if item['page'] not in seen_pages:
                pages_with_issues.append(item['page'])
                seen_pages.add(item['page'])

        print(f"{'='*60}")
        print(f"  ⚠️  {len(problems)} heading(s) with issues on {len(pages_with_issues)} page(s)")
        print(f"{'='*60}")
        print()

        # Group problems by page
        from collections import defaultdict
        by_page = defaultdict(list)
        for item in problems:
            by_page[item['page']].append(item)

        for pg in sorted(by_page.keys()):
            page_items = by_page[pg]
            print(f"  ── Page {pg} ({len(page_items)} issue(s)) ──")
            for item in page_items:
                print(f"    PDF text : {item['pdf_text']}")
                print(f"    Issue    : {item['issue']}")
                if item['md_match']:
                    print(f"    MD match : {item['md_match']}")
                print()

    # Summary of OK headings
    print(f"{'='*60}")
    print(f"  ✓  {len(ok)} heading(s) matched correctly")
    if ok:
        for item in ok:
            print(f"  [p{item['page']}] {item['pdf_text']}")
    print()

    if problems:
        print("ACTION REQUIRED: Fix the headings listed above before committing.")
        sys.exit(1)
    else:
        print("All headings verified. ✓")
        sys.exit(0)


if __name__ == '__main__':
    main()
