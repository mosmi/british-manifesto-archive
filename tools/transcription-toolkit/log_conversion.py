#!/usr/bin/env python3
"""
log_conversion.py — Sidecar JSON metadata logger for manifesto conversions.

Writes a small .conversion.json record alongside each converted Markdown file
so future sessions can audit which extractor was used, what the QA results
were, and any notes about the conversion.

Sidecar file convention:
    <output>.md  →  <output>.conversion.json

Usage:
    # Write a new sidecar record
    python log_conversion.py write output.md \\
        --pdf "Original documents/2001 General election/Scottish Labour 2001 manifesto.pdf" \\
        --extractor markitdown \\
        --coverage 99.6 \\
        --qa-errors 0 --qa-warnings 0 --qa-info 94 \\
        --notes "Rotated A3 spread PDF; MarkItDown gave cleaner reading order than pdftotext."

    # Auto-populate QA counts by running qa_check on the file
    python log_conversion.py write output.md --pdf source.pdf --extractor pdftotext-layout --run-qa

    # Read and display an existing sidecar
    python log_conversion.py read output.md

    # List all conversion sidecars under a directory
    python log_conversion.py list "Markdown versions/"

    # Output as JSON
    python log_conversion.py read output.md --json

Record schema:
    {
      "source_pdf":    "relative or absolute path to source PDF",
      "output_md":     "path to output Markdown file",
      "extractor":     "markitdown | pdftotext | pdftotext-layout | pdftotext-raw | ocr | ...",
      "coverage":      99.6,      // word coverage %, null if not measured
      "qa_errors":     0,
      "qa_warnings":   0,
      "qa_info":       94,
      "notes":         "free-text notes",
      "written_at":    "2026-05-03T14:22:00"   // ISO 8601 UTC
    }
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


# ── Sidecar path convention ───────────────────────────────────────────────────

def sidecar_path(md_path: str | Path) -> Path:
    p = Path(md_path)
    return p.with_suffix('.conversion.json')


# ── QA count extraction ───────────────────────────────────────────────────────

def _run_qa_counts(md_path: str, pdf_path: str | None = None) -> dict:
    """
    Run qa_check.py in JSON mode and extract error/warning/info counts.
    Returns {'qa_errors': N, 'qa_warnings': N, 'qa_info': N, 'coverage': float|None}.
    """
    qa_script = Path(__file__).parent / 'qa_check.py'
    if not qa_script.exists():
        return {'qa_errors': None, 'qa_warnings': None, 'qa_info': None, 'coverage': None}

    cmd = [sys.executable, str(qa_script), md_path, '--json']
    if pdf_path:
        cmd += ['--pdf', pdf_path]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        issues = json.loads(proc.stdout)
    except Exception:
        return {'qa_errors': None, 'qa_warnings': None, 'qa_info': None, 'coverage': None}

    errors   = sum(1 for i in issues if i.get('severity') == 'error'   and i.get('code') != 'C1')
    warnings = sum(1 for i in issues if i.get('severity') == 'warning')
    infos    = sum(1 for i in issues if i.get('severity') == 'info'     and i.get('code') != 'C1')

    # Extract coverage from C1 issue if present
    coverage = None
    for i in issues:
        if i.get('code') == 'C1':
            m = __import__('re').search(r'coverage=([\d.]+)%', i.get('detail', ''))
            if m:
                coverage = float(m.group(1))
            break

    return {
        'qa_errors':   errors,
        'qa_warnings': warnings,
        'qa_info':     infos,
        'coverage':    coverage,
    }


# ── Write ─────────────────────────────────────────────────────────────────────

def write_record(md_path: str,
                 pdf_path: str | None = None,
                 extractor: str | None = None,
                 coverage: float | None = None,
                 qa_errors: int | None = None,
                 qa_warnings: int | None = None,
                 qa_info: int | None = None,
                 notes: str = "",
                 run_qa: bool = False) -> dict:
    """
    Write a sidecar JSON record next to the Markdown file.
    Returns the record dict.
    """
    md = Path(md_path).resolve()
    sc = sidecar_path(md)

    record: dict = {}

    # Load existing record if present (preserve any fields not being updated)
    if sc.exists():
        try:
            record = json.loads(sc.read_text(encoding='utf-8'))
        except Exception:
            record = {}

    # Auto-run QA if requested
    if run_qa:
        qa_counts = _run_qa_counts(str(md), pdf_path)
        if qa_errors   is None: qa_errors   = qa_counts['qa_errors']
        if qa_warnings is None: qa_warnings = qa_counts['qa_warnings']
        if qa_info     is None: qa_info     = qa_counts['qa_info']
        if coverage    is None: coverage    = qa_counts['coverage']

    # Update record fields
    record.update({
        k: v for k, v in {
            'source_pdf':  str(Path(pdf_path).resolve()) if pdf_path else record.get('source_pdf'),
            'output_md':   str(md),
            'extractor':   extractor or record.get('extractor'),
            'coverage':    coverage  if coverage  is not None else record.get('coverage'),
            'qa_errors':   qa_errors   if qa_errors   is not None else record.get('qa_errors'),
            'qa_warnings': qa_warnings if qa_warnings is not None else record.get('qa_warnings'),
            'qa_info':     qa_info     if qa_info     is not None else record.get('qa_info'),
            'notes':       notes or record.get('notes', ''),
            'written_at':  datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S'),
        }.items() if v is not None or k in ('notes', 'written_at')
    })

    sc.write_text(json.dumps(record, indent=2), encoding='utf-8')
    return record


# ── Read ──────────────────────────────────────────────────────────────────────

def read_record(md_path: str) -> dict | None:
    sc = sidecar_path(md_path)
    if not sc.exists():
        return None
    try:
        return json.loads(sc.read_text(encoding='utf-8'))
    except Exception:
        return None


# ── List ──────────────────────────────────────────────────────────────────────

def list_records(directory: str) -> list[dict]:
    """Find all .conversion.json sidecars under a directory."""
    records = []
    for p in sorted(Path(directory).rglob('*.conversion.json')):
        try:
            records.append(json.loads(p.read_text(encoding='utf-8')))
        except Exception:
            pass
    return records


# ── Output ────────────────────────────────────────────────────────────────────

USE_COLOUR = True

def _c(code: str, s: str) -> str:
    return f"\033[{code}m{s}\033[0m" if USE_COLOUR else s

def green(s):  return _c("32", s)
def yellow(s): return _c("33", s)
def bold(s):   return _c("1",  s)
def dim(s):    return _c("2",  s)


def _qa_summary(r: dict) -> str:
    e = r.get('qa_errors')
    w = r.get('qa_warnings')
    i = r.get('qa_info')
    if e is None:
        return dim("QA not run")
    parts = []
    if e:  parts.append(yellow(f"{e}E"))
    else:  parts.append(green("0E"))
    if w:  parts.append(yellow(f"{w}W"))
    else:  parts.append(green("0W"))
    parts.append(f"{i or 0}I")
    return " ".join(parts)


def print_record(r: dict):
    print()
    print(bold("Conversion record"))
    print("─" * 60)
    cov = r.get('coverage')
    print(f"  Output     : {r.get('output_md', '?')}")
    print(f"  Source PDF : {r.get('source_pdf', dim('(not recorded)'))}")
    print(f"  Extractor  : {r.get('extractor', dim('(not recorded)'))}")
    print(f"  Coverage   : {f'{cov:.1f}%' if cov is not None else dim('(not measured)')}")
    print(f"  QA         : {_qa_summary(r)}")
    if r.get('notes'):
        print(f"  Notes      : {r['notes']}")
    print(f"  Written at : {r.get('written_at', '?')}")
    print()


def print_list(records: list[dict]):
    if not records:
        print(dim("  No conversion records found."))
        return
    print()
    print(f"  {'File':<50}  {'Extractor':<20}  {'Cov':>6}  QA")
    print(f"  {'────':<50}  {'─────────':<20}  {'───':>6}  ──")
    for r in records:
        name = Path(r.get('output_md', '?')).name
        ext  = r.get('extractor') or dim('?')
        cov  = r.get('coverage')
        cov_s = f"{cov:.1f}%" if cov is not None else dim("   ?")
        print(f"  {name:<50}  {ext:<20}  {cov_s:>6}  {_qa_summary(r)}")
    print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    global USE_COLOUR

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest='command', required=True)

    # write
    wp = sub.add_parser('write', help='Write or update a conversion sidecar')
    wp.add_argument('markdown', help='Path to converted Markdown file')
    wp.add_argument('--pdf',          metavar='FILE', help='Source PDF path')
    wp.add_argument('--extractor',    metavar='NAME',
                    help='Extraction method used (e.g. markitdown, pdftotext-layout)')
    wp.add_argument('--coverage',     type=float, metavar='PCT',
                    help='Word coverage percentage')
    wp.add_argument('--qa-errors',    type=int,   dest='qa_errors',   metavar='N')
    wp.add_argument('--qa-warnings',  type=int,   dest='qa_warnings', metavar='N')
    wp.add_argument('--qa-info',      type=int,   dest='qa_info',     metavar='N')
    wp.add_argument('--notes',        default='', help='Free-text notes')
    wp.add_argument('--run-qa',       dest='run_qa', action='store_true',
                    help='Auto-run qa_check to populate QA counts and coverage')
    wp.add_argument('--json',         dest='as_json', action='store_true')
    wp.add_argument('--no-colour',    dest='no_colour', action='store_true')

    # read
    rp = sub.add_parser('read', help='Display a conversion sidecar')
    rp.add_argument('markdown', help='Path to Markdown file (or its .conversion.json)')
    rp.add_argument('--json',      dest='as_json',  action='store_true')
    rp.add_argument('--no-colour', dest='no_colour', action='store_true')

    # list
    lp = sub.add_parser('list', help='List all conversion records under a directory')
    lp.add_argument('directory', help='Directory to search')
    lp.add_argument('--json',      dest='as_json',  action='store_true')
    lp.add_argument('--no-colour', dest='no_colour', action='store_true')

    args = parser.parse_args()

    if getattr(args, 'no_colour', False) or getattr(args, 'as_json', False):
        USE_COLOUR = False

    if args.command == 'write':
        record = write_record(
            args.markdown,
            pdf_path=args.pdf,
            extractor=args.extractor,
            coverage=args.coverage,
            qa_errors=args.qa_errors,
            qa_warnings=args.qa_warnings,
            qa_info=args.qa_info,
            notes=args.notes,
            run_qa=args.run_qa,
        )
        if args.as_json:
            print(json.dumps(record, indent=2))
        else:
            print_record(record)
            sc = sidecar_path(args.markdown)
            print(f"  Saved → {sc}")
            print()

    elif args.command == 'read':
        record = read_record(args.markdown)
        if record is None:
            print(f"No conversion record found for {args.markdown}", file=sys.stderr)
            sys.exit(1)
        if args.as_json:
            print(json.dumps(record, indent=2))
        else:
            print_record(record)

    elif args.command == 'list':
        records = list_records(args.directory)
        if args.as_json:
            print(json.dumps(records, indent=2))
        else:
            print_list(records)


if __name__ == '__main__':
    main()
