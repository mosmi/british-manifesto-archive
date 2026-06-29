#!/usr/bin/env python3
"""
spot_check.py — Known-good snippet spot checker for manifesto conversions.

For long manifestos, full manual review is slow.  This tool extracts a handful
of key passages from both the source PDF (via pdftotext) and the converted
Markdown file, then prints them side-by-side so you can verify reading order
and content fidelity at a glance.

Snippets extracted:
    1. First body paragraph        (skips short cover/title lines)
    2. First heading after contents (first heading at least 30 lines in)
    3. One middle-section paragraph
    4. First bullet list (up to 6 items)
    5. Last substantive paragraph

Usage:
    python spot_check.py output.md
    python spot_check.py output.md --pdf manifesto.pdf
    python spot_check.py output.md --pdf manifesto.pdf --lines 8
    python spot_check.py output.md --json

Options:
    --pdf FILE      Original PDF for pdftotext comparison (optional)
    --lines N       Lines per snippet (default: 6)
    --json          Output machine-readable JSON
    --no-colour     Disable ANSI colour
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


# ── Colours ───────────────────────────────────────────────────────────────────

USE_COLOUR = True

def _c(code: str, s: str) -> str:
    return f"\033[{code}m{s}\033[0m" if USE_COLOUR else s

def cyan(s):   return _c("36", s)
def yellow(s): return _c("33", s)
def bold(s):   return _c("1",  s)
def dim(s):    return _c("2",  s)
def green(s):  return _c("32", s)


# ── Snippet extraction from Markdown ─────────────────────────────────────────

def _meaningful_lines(text: str) -> list[tuple[int, str]]:
    """Return (lineno, text) for non-blank lines, 1-indexed."""
    return [(i + 1, l) for i, l in enumerate(text.splitlines()) if l.strip()]


def extract_md_snippets(text: str, lines_per: int = 6) -> dict[str, str]:
    """Extract key snippets from a Markdown string."""
    mlines = _meaningful_lines(text)
    total  = len(mlines)

    def _chunk(start_idx: int, n: int = lines_per) -> str:
        return "\n".join(l for _, l in mlines[start_idx: start_idx + n])

    snippets: dict[str, str] = {}

    # ── 1. First body paragraph ───────────────────────────────────────────────
    first_body_idx = 0
    for i, (_, l) in enumerate(mlines):
        stripped = l.strip()
        # Skip headings, very short lines, and lines that look like title/cover
        if (not stripped.startswith('#')
                and len(stripped.split()) >= 8
                and not re.match(r'^\d{1,4}$', stripped)):
            first_body_idx = i
            break
    snippets['first_body'] = _chunk(first_body_idx)

    # ── 2. First heading after the first 30 meaningful lines ─────────────────
    heading_idx = None
    for i, (_, l) in enumerate(mlines):
        if i < 30:
            continue
        if l.strip().startswith('#'):
            heading_idx = i
            break
    if heading_idx is not None:
        snippets['first_post_contents_heading'] = _chunk(heading_idx)
    else:
        snippets['first_post_contents_heading'] = "(no heading found after line 30)"

    # ── 3. Middle paragraph ───────────────────────────────────────────────────
    mid = total // 2
    # Walk backward from mid to find a paragraph start
    for i in range(mid, max(0, mid - 20), -1):
        if mlines[i][1].strip() and not mlines[i][1].strip().startswith(('#', '*', '-')):
            mid = i
            break
    snippets['middle_paragraph'] = _chunk(mid)

    # ── 4. First bullet list ──────────────────────────────────────────────────
    bullet_start = None
    for i, (_, l) in enumerate(mlines):
        if l.strip().startswith(('* ', '- ')):
            bullet_start = i
            break
    if bullet_start is not None:
        # Collect up to lines_per bullets
        bullet_lines = []
        j = bullet_start
        while j < total and len(bullet_lines) < lines_per:
            l = mlines[j][1].strip()
            if l.startswith(('* ', '- ')) or (bullet_lines and l and not l.startswith('#')):
                bullet_lines.append(mlines[j][1])
            elif bullet_lines and not l:
                break  # end of list block
            j += 1
        snippets['first_bullet_list'] = "\n".join(bullet_lines)
    else:
        snippets['first_bullet_list'] = "(no bullet list found)"

    # ── 5. Last substantive paragraph ────────────────────────────────────────
    last_body_idx = total - 1
    for i in range(total - 1, max(0, total - 40), -1):
        stripped = mlines[i][1].strip()
        if (stripped
                and not stripped.startswith('#')
                and len(stripped.split()) >= 5
                and not re.match(r'^\d{1,4}$', stripped)):
            last_body_idx = i
            break
    snippets['last_paragraph'] = _chunk(max(0, last_body_idx - lines_per // 2), lines_per)

    return snippets


# ── Snippet extraction from pdftotext ────────────────────────────────────────

def extract_pdf_snippets(pdf_path: str, lines_per: int = 6) -> dict[str, str]:
    """
    Extract matching snippets from pdftotext output.
    Uses the same positional heuristics as the Markdown extractor.
    """
    try:
        res = subprocess.run(
            ['pdftotext', pdf_path, '-'],
            capture_output=True, text=True, timeout=120
        )
        if res.returncode != 0:
            return {}
        text = res.stdout
    except Exception:
        return {}

    # Strip form feeds and normalise
    pages = text.split('\f')
    all_text = '\n'.join(p for p in pages)
    return extract_md_snippets(all_text, lines_per=lines_per)


# ── Output ────────────────────────────────────────────────────────────────────

LABELS = {
    'first_body':                   'First body paragraph',
    'first_post_contents_heading':  'First heading after contents',
    'middle_paragraph':             'Middle paragraph',
    'first_bullet_list':            'First bullet list',
    'last_paragraph':               'Last paragraph',
}

SNIPPET_ORDER = list(LABELS.keys())


def print_comparison(md_snips: dict[str, str], pdf_snips: dict[str, str]):
    w = 72
    print()
    for key in SNIPPET_ORDER:
        label = LABELS.get(key, key)
        print(f"{bold(label)}")
        print("─" * w)

        md_text  = md_snips.get(key, "(not found)")
        pdf_text = pdf_snips.get(key, "(PDF not provided)")

        if pdf_snips:
            print(f"  {cyan(bold('PDF (pdftotext):'))}")
            for l in pdf_text.splitlines():
                print(f"    {dim(l)}")
            print()
            print(f"  {yellow(bold('Markdown:'))}")
        else:
            print(f"  {yellow(bold('Markdown:'))}")

        for l in md_text.splitlines():
            print(f"    {l}")
        print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    global USE_COLOUR

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("markdown", help="Path to converted Markdown file")
    parser.add_argument("--pdf",    metavar="FILE",
                        help="Original PDF for pdftotext comparison")
    parser.add_argument("--lines",  type=int, default=6, metavar="N",
                        help="Lines per snippet (default: 6)")
    parser.add_argument("--json",   dest="as_json", action="store_true",
                        help="Output JSON")
    parser.add_argument("--no-colour", dest="no_colour", action="store_true",
                        help="Disable ANSI colour")
    args = parser.parse_args()

    if args.no_colour or args.as_json:
        USE_COLOUR = False

    md_path = Path(args.markdown)
    if not md_path.exists():
        print(f"ERROR: Markdown file not found: {args.markdown}", file=sys.stderr)
        sys.exit(2)

    md_text   = md_path.read_text(encoding='utf-8', errors='replace')
    md_snips  = extract_md_snippets(md_text, lines_per=args.lines)
    pdf_snips = {}
    if args.pdf:
        pdf_snips = extract_pdf_snippets(args.pdf, lines_per=args.lines)
        if not pdf_snips:
            print(f"  {yellow('Warning:')} could not extract from PDF "
                  f"(is pdftotext installed?)", file=sys.stderr)

    if args.as_json:
        print(json.dumps({
            'markdown': md_snips,
            'pdf':      pdf_snips,
        }, indent=2))
    else:
        print(f"\n{bold('Spot check:')} {md_path.name}")
        print_comparison(md_snips, pdf_snips)


if __name__ == "__main__":
    main()
