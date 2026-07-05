#!/usr/bin/env python3
"""
resolve_output.py — Output path and naming convention helper.

Infers or validates the canonical destination path for a converted manifesto
Markdown file, following the project convention:

    Markdown versions/<party-slug>/<year>-<party-slug>.md

Usage:
    # Infer everything from PDF filename and party name
    python resolve_output.py --pdf "Original documents/2001 General election/Scottish Labour 2001 manifesto.pdf" --party "Scottish Labour"

    # Override the year explicitly
    python resolve_output.py --pdf manifesto.pdf --party "Green Party" --year 2019

    # Check whether a file already exists at the resolved path
    python resolve_output.py --pdf manifesto.pdf --party "SNP" --check

    # Output JSON (useful in scripts)
    python resolve_output.py --pdf manifesto.pdf --party "Plaid Cymru" --json

    # Print only the output path (useful in shell pipelines)
    python resolve_output.py --pdf manifesto.pdf --party "Liberal Democrats" --path-only

Resolution rules:
    party slug   : party name lowercased, spaces → hyphens, punctuation stripped
    year         : first 4-digit year found in the PDF filename (or --year override)
    output folder: <manifesto-root>/Markdown versions/<party-slug>/
    output file  : <year>-<party-slug>.md

The manifesto root is searched upward from the PDF location, then from the
script location, looking for a directory containing a "Markdown versions" folder.
"""

import argparse
import json
import re
import sys
from pathlib import Path


# ── Slug helpers ──────────────────────────────────────────────────────────────

def make_slug(party: str) -> str:
    """
    Convert a party name to a kebab-case slug.

    'Scottish Labour'         → 'scottish-labour'
    'Green Party (NI)'        → 'green-party-ni'
    'Plaid Cymru'             → 'plaid-cymru'
    "Alliance Party"          → 'alliance-party'
    """
    s = party.lower().strip()
    # Replace parentheses content cleanly
    s = re.sub(r'[()]', ' ', s)
    # Replace non-alphanumeric with hyphens
    s = re.sub(r'[^a-z0-9]+', '-', s)
    # Collapse multiple hyphens, strip leading/trailing
    s = re.sub(r'-+', '-', s).strip('-')
    return s


def extract_year_from_name(name: str) -> str | None:
    """Return the first 4-digit year found in a filename or path string."""
    m = re.search(r'\b(1[89]\d{2}|20[0-2]\d)\b', name)
    return m.group(1) if m else None


# ── Root finder ───────────────────────────────────────────────────────────────

def find_manifesto_root(start: Path) -> Path | None:
    """
    Walk upward from start looking for a directory that contains
    a 'Markdown versions' subdirectory.  Returns that directory or None.
    """
    candidate = start.resolve()
    for _ in range(10):  # limit search depth
        if (candidate / "Markdown versions").is_dir():
            return candidate
        parent = candidate.parent
        if parent == candidate:
            break
        candidate = parent
    return None


# ── Core resolution ───────────────────────────────────────────────────────────

def resolve(pdf: str, party: str, year: str | None = None,
            manifesto_root: str | None = None) -> dict:
    """
    Resolve the canonical output path for a manifesto conversion.

    Returns a dict with keys:
        slug              : str
        year              : str | None
        party_folder      : str (absolute path)
        output_path       : str (absolute path to .md file)
        folder_exists     : bool
        file_exists       : bool
        root_found        : bool
        warnings          : list[str]
    """
    pdf_path  = Path(pdf)
    slug      = make_slug(party)
    warnings: list[str] = []

    # Year resolution
    resolved_year = year or extract_year_from_name(pdf_path.name)
    if not resolved_year:
        resolved_year = extract_year_from_name(str(pdf_path))
    if not resolved_year:
        warnings.append(
            f"Could not infer year from filename '{pdf_path.name}'. "
            "Pass --year YYYY explicitly."
        )

    # Root resolution
    root = None
    if manifesto_root:
        root = Path(manifesto_root)
    else:
        # Try upward from PDF location
        root = find_manifesto_root(pdf_path.parent if pdf_path.parent != Path('.') else Path.cwd())
        if not root:
            # Try upward from script location
            root = find_manifesto_root(Path(__file__).parent)

    root_found = root is not None
    if not root_found:
        warnings.append(
            "Could not locate the manifesto project root (no 'Markdown versions' folder found "
            "in parent directories). Pass --root to specify the project root explicitly."
        )
        # Fall back to relative path
        root = Path(".")

    md_root     = root / "Markdown versions"
    party_folder = md_root / f"{slug}-manifesto" if not (md_root / slug).exists() else md_root / slug

    # Prefer the simpler slug-only folder if it already exists; otherwise use slug-manifesto
    # to match the project's existing convention (e.g. scottish-labour-manifesto/)
    simple_folder   = md_root / slug
    manifest_folder = md_root / f"{slug}-manifesto"

    if simple_folder.exists():
        party_folder = simple_folder
    elif manifest_folder.exists():
        party_folder = manifest_folder
    else:
        # Neither exists yet — use slug-manifesto to match existing convention
        party_folder = manifest_folder

    if resolved_year:
        output_file = party_folder / f"{resolved_year}-{slug}-manifesto.md"
    else:
        output_file = party_folder / f"XXXX-{slug}-manifesto.md"

    return {
        'slug':          slug,
        'year':          resolved_year,
        'party_folder':  str(party_folder),
        'output_path':   str(output_file),
        'folder_exists': party_folder.exists(),
        'file_exists':   output_file.exists(),
        'root_found':    root_found,
        'manifesto_root': str(root),
        'warnings':      warnings,
    }


# ── Output ────────────────────────────────────────────────────────────────────

USE_COLOUR = True

def _c(code: str, s: str) -> str:
    return f"\033[{code}m{s}\033[0m" if USE_COLOUR else s

def green(s):  return _c("32", s)
def yellow(s): return _c("33", s)
def red(s):    return _c("31", s)
def bold(s):   return _c("1",  s)
def dim(s):    return _c("2",  s)


def print_resolution(r: dict):
    print()
    print(bold("Resolved output path"))
    print("─" * 56)
    print(f"  Slug         : {r['slug']}")
    print(f"  Year         : {r['year'] or dim('(unknown)')}")
    print(f"  Party folder : {r['party_folder']}  "
          f"[{green('exists') if r['folder_exists'] else yellow('will be created')}]")
    print(f"  Output file  : {r['output_path']}")
    if r['file_exists']:
        print(f"               {yellow('  ⚠ file already exists at this path')}")
    else:
        print(f"                  [{dim('not yet written')}]")
    if r['warnings']:
        print()
        for w in r['warnings']:
            print(f"  {yellow('⚠')} {w}")
    print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    global USE_COLOUR

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--pdf",   required=True, metavar="FILE",
                        help="Path to source PDF (used to infer year)")
    parser.add_argument("--party", required=True, metavar="NAME",
                        help="Party name (e.g. 'Scottish Labour')")
    parser.add_argument("--year",  metavar="YYYY",
                        help="Election year (overrides auto-detection)")
    parser.add_argument("--root",  metavar="DIR",
                        help="Manifesto project root (folder containing 'Markdown versions/')")
    parser.add_argument("--check", action="store_true",
                        help="Exit with code 1 if the output file already exists")
    parser.add_argument("--json",  dest="as_json", action="store_true",
                        help="Output JSON")
    parser.add_argument("--path-only", dest="path_only", action="store_true",
                        help="Print only the resolved output path (useful in pipelines)")
    parser.add_argument("--no-colour", dest="no_colour", action="store_true",
                        help="Disable ANSI colour")
    args = parser.parse_args()

    if args.no_colour or args.as_json:
        USE_COLOUR = False

    r = resolve(args.pdf, args.party, year=args.year, manifesto_root=args.root)

    if args.path_only:
        print(r['output_path'])
        sys.exit(0)

    if args.as_json:
        print(json.dumps(r, indent=2))
        sys.exit(1 if (args.check and r['file_exists']) else 0)

    print_resolution(r)

    if args.check and r['file_exists']:
        print(red(f"ERROR: output file already exists: {r['output_path']}"), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
