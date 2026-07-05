#!/usr/bin/env python3
"""
extract_compare.py — Extraction strategy runner for manifesto PDFs.

Tries all available extraction methods, scores each one for common
artefacts, and recommends the best starting point for a clean conversion.

Usage:
    python extract_compare.py manifesto.pdf
    python extract_compare.py manifesto.pdf --out-dir /tmp/manifesto-extracts
    python extract_compare.py manifesto.pdf --out-dir /tmp/extracts --fixed-widths 60,80,100
    python extract_compare.py manifesto.pdf --json

Methods tried (where available):
    pdftotext           Plain text, no layout preservation
    pdftotext-layout    Attempt to preserve visual layout with spaces
    pdftotext-raw       Raw character order (can help with reading-order PDFs)
    pdftotext-fixed-N   Fixed column width (several widths)
    pdftotext-bbox      Bounding-box layout (poppler ≥ 0.72)
    markitdown          Microsoft MarkItDown library (optional)
    ocr                 Tesseract OCR via pytesseract + pdf2image (optional)

Output includes:
    - Word counts by method
    - Page / form-feed counts
    - Raw bullet glyph counts
    - Repeated-word artefact counts (to to, and and, …)
    - Mid-sentence bullet counts
    - Likely vertical running-header fragments
    - Sample snippets (first body, middle, last)
    - Recommended starting method
    - Extracted text files saved to --out-dir (if given)
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent / "lib"))

# ── Patterns ──────────────────────────────────────────────────────────────────

RE_BULLET_GLYPH  = re.compile(r"[•●◆◉▪▸►]")
RE_DOUBLE_WORD   = re.compile(r"\b(\w{2,})\s+\1\b", re.IGNORECASE)
RE_MID_BULLET    = re.compile(r"\S.+[•●◆◉▪▸►]")  # bullet not at line start
RE_VERT_FRAG     = re.compile(r"^[A-Za-z]\s[A-Za-z](\s[A-Za-z])*\s*$")  # "P y W b"
RE_SINGLE_CHAR   = re.compile(r"^\s*[A-Za-z]\s*$")


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class MethodResult:
    method:           str
    available:        bool        = True
    error:            str         = ""
    word_count:       int         = 0
    page_count:       int         = 0      # form-feed count + 1
    bullet_glyphs:    int         = 0
    double_words:     int         = 0      # repeated adjacent words
    mid_bullets:      int         = 0
    vert_fragments:   int         = 0      # likely vertical-header lines
    short_paras:      int         = 0      # very short isolated paragraphs
    artefact_score:   float       = 0.0   # lower is better
    snippet_first:    str         = ""
    snippet_middle:   str         = ""
    snippet_last:     str         = ""
    output_file:      str         = ""
    recommended:      bool        = False


# ── Utilities ─────────────────────────────────────────────────────────────────

def _run(cmd: list[str], timeout: int = 120) -> tuple[bool, str, str]:
    """Run a command. Returns (ok, stdout, stderr)."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, r.stdout, r.stderr
    except FileNotFoundError:
        return False, "", f"command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return False, "", "timeout"
    except Exception as e:
        return False, "", str(e)


def _snippet(text: str, position: str = "first", lines: int = 6) -> str:
    """Extract a short snippet from the text."""
    all_lines = [l for l in text.splitlines() if l.strip()]
    if not all_lines:
        return ""
    if position == "first":
        # Skip very short lines at the start (likely cover/title)
        start = 0
        for i, l in enumerate(all_lines):
            if len(l.split()) >= 5:
                start = i
                break
        chunk = all_lines[start: start + lines]
    elif position == "middle":
        mid = len(all_lines) // 2
        chunk = all_lines[max(0, mid - lines // 2): mid + lines // 2]
    else:  # last
        chunk = all_lines[max(0, len(all_lines) - lines):]
    return " | ".join(chunk)[:300]


def _score(r: MethodResult) -> float:
    """
    Compute an artefact score (lower = cleaner).
    Weights are heuristic but validated against real manifesto PDFs.
    """
    if not r.available or r.word_count == 0:
        return 9999.0
    wc = max(r.word_count, 1)
    score = (
        (r.double_words  / wc) * 1000 * 5   +
        (r.vert_fragments / wc) * 1000 * 3  +
        (r.mid_bullets   / wc) * 1000 * 2   +
        (r.bullet_glyphs / wc) * 1000 * 1   +
        (r.short_paras   / wc) * 1000 * 0.5
    )
    return round(score, 2)


def _analyse(text: str) -> dict:
    """Count artefacts in extracted text. Returns dict for MethodResult fields."""
    lines = text.splitlines()
    paragraphs = []
    current: list[str] = []
    for ln in lines:
        if ln.strip():
            current.append(ln)
        else:
            if current:
                paragraphs.append("\n".join(current))
                current = []
    if current:
        paragraphs.append("\n".join(current))

    double_words = sum(len(RE_DOUBLE_WORD.findall(p)) for p in paragraphs)
    bullet_glyphs = sum(1 for p in paragraphs if RE_BULLET_GLYPH.search(p))
    mid_bullets   = sum(1 for ln in lines if RE_MID_BULLET.search(ln))
    vert_frags    = sum(1 for ln in lines if RE_VERT_FRAG.match(ln) or RE_SINGLE_CHAR.match(ln))
    short_paras   = sum(1 for p in paragraphs
                        if 1 <= len(p.split()) <= 3 and not p.strip().endswith(':'))

    pages = text.count('\f') + 1
    words = len(text.split())

    return dict(
        word_count=words,
        page_count=pages,
        bullet_glyphs=bullet_glyphs,
        double_words=double_words,
        mid_bullets=mid_bullets,
        vert_fragments=vert_frags,
        short_paras=short_paras,
        snippet_first=_snippet(text, "first"),
        snippet_middle=_snippet(text, "middle"),
        snippet_last=_snippet(text, "last"),
    )


def _save(text: str, out_dir: Optional[Path], method: str) -> str:
    """Save extracted text to out_dir if given. Returns file path or ''."""
    if not out_dir:
        return ""
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = method.replace(" ", "-").replace("/", "-")
    path = out_dir / f"{slug}.txt"
    path.write_text(text, encoding="utf-8")
    return str(path)


# ── Extractors ────────────────────────────────────────────────────────────────

def try_pdftotext(pdf: str, flag: str = "", fixed_width: int = 0,
                  out_dir: Optional[Path] = None) -> MethodResult:
    """Run pdftotext with various flags."""
    if shutil.which("pdftotext") is None:
        return MethodResult(method="pdftotext", available=False,
                            error="pdftotext not found (install poppler-utils)")

    if fixed_width:
        method = f"pdftotext-fixed-{fixed_width}"
        cmd = ["pdftotext", f"-fixed", str(fixed_width), pdf, "-"]
    elif flag:
        method = f"pdftotext-{flag.lstrip('-')}"
        cmd = ["pdftotext", flag, pdf, "-"]
    else:
        method = "pdftotext"
        cmd = ["pdftotext", pdf, "-"]

    ok, stdout, stderr = _run(cmd)
    if not ok:
        return MethodResult(method=method, available=True,
                            error=stderr[:200] if stderr else "pdftotext failed")

    stats = _analyse(stdout)
    saved = _save(stdout, out_dir, method)
    r = MethodResult(method=method, **stats, output_file=saved)
    r.artefact_score = _score(r)
    return r


def try_markitdown(pdf: str, out_dir: Optional[Path] = None) -> MethodResult:
    """Try extraction via MarkItDown (microsoft/markitdown)."""
    try:
        from markitdown import MarkItDown  # type: ignore
    except ImportError:
        return MethodResult(method="markitdown", available=False,
                            error="markitdown not installed "
                                  "(pip install markitdown --break-system-packages)")

    try:
        md = MarkItDown()
        result = md.convert(pdf)
        text = result.text_content or ""
    except Exception as e:
        return MethodResult(method="markitdown", available=True,
                            error=f"MarkItDown failed: {e}")

    stats = _analyse(text)
    saved = _save(text, out_dir, "markitdown")
    r = MethodResult(method="markitdown", **stats, output_file=saved)
    r.artefact_score = _score(r)
    return r


def try_ocr(pdf: str, out_dir: Optional[Path] = None) -> MethodResult:
    """Try OCR via pytesseract + pdf2image."""
    try:
        import pytesseract  # type: ignore
        from pdf2image import convert_from_path  # type: ignore
    except ImportError:
        return MethodResult(method="ocr", available=False,
                            error="OCR dependencies not installed "
                                  "(pip install pytesseract pdf2image --break-system-packages; "
                                  "also requires tesseract and poppler system packages)")

    try:
        images = convert_from_path(pdf, dpi=200)
        pages_text = []
        for img in images:
            pages_text.append(pytesseract.image_to_string(img, lang="eng"))
        text = "\f".join(pages_text)
    except Exception as e:
        return MethodResult(method="ocr", available=True,
                            error=f"OCR failed: {e}")

    stats = _analyse(text)
    saved = _save(text, out_dir, "ocr")
    r = MethodResult(method="ocr", **stats, output_file=saved)
    r.artefact_score = _score(r)
    return r


# ── Runner ────────────────────────────────────────────────────────────────────

def run_compare(pdf: str,
                out_dir: Optional[Path] = None,
                fixed_widths: list[int] = None,
                include_ocr: bool = False) -> list[MethodResult]:
    """Run all available methods and return results sorted by artefact score."""
    if fixed_widths is None:
        fixed_widths = [60, 80, 100]

    results: list[MethodResult] = []

    # pdftotext variants
    results.append(try_pdftotext(pdf, out_dir=out_dir))
    results.append(try_pdftotext(pdf, flag="-layout", out_dir=out_dir))
    results.append(try_pdftotext(pdf, flag="-raw", out_dir=out_dir))
    results.append(try_pdftotext(pdf, flag="-bbox-layout", out_dir=out_dir))
    for w in fixed_widths:
        results.append(try_pdftotext(pdf, fixed_width=w, out_dir=out_dir))

    # MarkItDown
    results.append(try_markitdown(pdf, out_dir=out_dir))

    # OCR (slow — opt-in)
    if include_ocr:
        results.append(try_ocr(pdf, out_dir=out_dir))

    # Sort available methods by score; unavailable last
    available = sorted([r for r in results if r.available and not r.error],
                       key=lambda r: r.artefact_score)
    unavailable = [r for r in results if not r.available or r.error]

    if available:
        available[0].recommended = True

    return available + unavailable


# ── Output ────────────────────────────────────────────────────────────────────

USE_COLOUR = True

def _c(code: str, s: str) -> str:
    if not USE_COLOUR:
        return s
    return f"\033[{code}m{s}\033[0m"

def green(s):  return _c("32", s)
def yellow(s): return _c("33", s)
def red(s):    return _c("31", s)
def bold(s):   return _c("1",  s)
def dim(s):    return _c("2",  s)
def cyan(s):   return _c("36", s)


def print_results(results: list[MethodResult], pdf_name: str):
    print(f"\n{bold('Extraction comparison:')} {pdf_name}")
    print("─" * 72)

    available = [r for r in results if r.available and not r.error]
    unavailable = [r for r in results if not r.available]
    errored = [r for r in results if r.available and r.error]

    if not available:
        print(red("  No methods succeeded."))
        if unavailable:
            print(dim(f"  Not available: {', '.join(r.method for r in unavailable)}"))
        return

    # ── Summary table ─────────────────────────────────────────────────────────
    col_w = [22, 8, 6, 8, 8, 7, 7, 9]
    headers = ["Method", "Words", "Pages", "DblWord", "BulGlyph",
               "MidBul", "VertFrg", "Score"]
    row_fmt = " {:<22} {:>8} {:>6} {:>8} {:>8} {:>7} {:>7} {:>9}"
    print(row_fmt.format(*headers))
    print("  " + "─" * 70)

    for r in available:
        tag = green(" ★ RECOMMENDED") if r.recommended else ""
        score_str = green(f"{r.artefact_score:.2f}") if r.recommended else f"{r.artefact_score:.2f}"
        print(row_fmt.format(
            r.method, f"{r.word_count:,}", r.page_count,
            r.double_words, r.bullet_glyphs, r.mid_bullets,
            r.vert_fragments, score_str
        ) + tag)

    # ── Recommendation ────────────────────────────────────────────────────────
    rec = next((r for r in available if r.recommended), None)
    if rec:
        print(f"\n{bold('Recommendation:')} {green(rec.method)}")
        print(f"  Artefact score {rec.artefact_score:.2f} "
              f"(lower is cleaner; weighted: double-words ×5, vert-frags ×3, "
              f"mid-bullets ×2, bullet-glyphs ×1)")

    # ── Snippets for top 2 methods ────────────────────────────────────────────
    for r in available[:2]:
        print(f"\n{bold('Snippets —')} {cyan(r.method)}")
        for label, snippet in [("first body", r.snippet_first),
                                ("middle",     r.snippet_middle),
                                ("last",       r.snippet_last)]:
            print(f"  {dim(label+':')} {snippet[:200]}")

    # ── Output files ──────────────────────────────────────────────────────────
    saved = [r for r in available if r.output_file]
    if saved:
        print(f"\n{bold('Saved extracts:')}")
        for r in saved:
            tag = green(" (recommended)") if r.recommended else ""
            print(f"  {r.output_file}{tag}")

    # ── Unavailable / errored ─────────────────────────────────────────────────
    if unavailable:
        print(f"\n{dim('Not available:')} "
              f"{dim(', '.join(r.method + ': ' + r.error for r in unavailable))}")
    if errored:
        print(f"\n{yellow('Errors:')}")
        for r in errored:
            print(f"  {r.method}: {r.error}")

    print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    global USE_COLOUR

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("pdf", help="Path to manifesto PDF")
    parser.add_argument(
        "--out-dir", metavar="DIR",
        help="Directory to save extracted text files (optional)"
    )
    parser.add_argument(
        "--fixed-widths", metavar="N,N,...", default="60,80,100",
        help="Comma-separated fixed widths for pdftotext -fixed (default: 60,80,100)"
    )
    parser.add_argument(
        "--ocr", action="store_true",
        help="Include OCR (slow; requires tesseract, pytesseract, pdf2image)"
    )
    parser.add_argument(
        "--json", dest="as_json", action="store_true",
        help="Output machine-readable JSON"
    )
    parser.add_argument(
        "--no-colour", dest="no_colour", action="store_true",
        help="Disable ANSI colour output"
    )
    args = parser.parse_args()

    if args.no_colour or args.as_json:
        USE_COLOUR = False

    pdf_path = args.pdf
    if not Path(pdf_path).exists():
        print(f"ERROR: PDF not found: {pdf_path}", file=sys.stderr)
        sys.exit(2)

    out_dir = Path(args.out_dir) if args.out_dir else None
    fixed_widths = [int(w.strip()) for w in args.fixed_widths.split(",") if w.strip()]

    results = run_compare(
        pdf_path,
        out_dir=out_dir,
        fixed_widths=fixed_widths,
        include_ocr=args.ocr,
    )

    if args.as_json:
        print(json.dumps([asdict(r) for r in results], indent=2))
    else:
        print_results(results, Path(pdf_path).name)


if __name__ == "__main__":
    main()
