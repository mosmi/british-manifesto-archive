#!/usr/bin/env python3
"""
finalize_manifesto.py — Copy, verify, and QA a converted manifesto Markdown file.

Run this as the last step of every manifesto conversion to confirm the file
landed correctly and passes QA before committing.

Usage:
    python finalize_manifesto.py working.md destination.md
    python finalize_manifesto.py working.md destination.md --pdf source.pdf
    python finalize_manifesto.py working.md destination.md --pdf source.pdf --strict

What it does:
    1. Checks that the working file exists
    2. Creates the destination folder if needed
    3. Copies working.md → destination.md
    4. Prints file size for both
    5. Prints SHA-256 hashes for both and confirms they match
    6. Runs qa_check.py on the DESTINATION file (not the working copy)
    7. Exits non-zero if:
         - SHA-256 hashes don't match (copy was corrupted)
         - QA reports errors or warnings (when --strict is set)
         - QA reports any errors (always)

Options:
    --pdf FILE      Original PDF — passed through to qa_check for coverage check
    --strict        Exit non-zero if QA has any warnings (default: only on errors)
    --no-qa         Skip QA step (copy and hash only)
    --overwrite     Allow overwriting an existing destination file
    --json          Output machine-readable JSON summary
    --no-colour     Disable ANSI colour output

Exit codes:
    0   All checks passed
    1   QA errors/warnings
    2   File system error (missing file, copy failure, hash mismatch)
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


# ── Colours ───────────────────────────────────────────────────────────────────

USE_COLOUR = True

def _c(code: str, s: str) -> str:
    return f"\033[{code}m{s}\033[0m" if USE_COLOUR else s

def green(s):  return _c("32", s)
def yellow(s): return _c("33", s)
def red(s):    return _c("31", s)
def bold(s):   return _c("1",  s)
def dim(s):    return _c("2",  s)
def tick():    return green("✓")
def cross():   return red("✗")


# ── Utilities ─────────────────────────────────────────────────────────────────

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def human_size(n: int) -> str:
    for unit in ('B', 'KB', 'MB'):
        if n < 1024:
            return f"{n:.0f} {unit}"
        n /= 1024
    return f"{n:.1f} MB"


def find_qa_script() -> Path | None:
    """Locate qa_check.py relative to this script."""
    candidates = [
        Path(__file__).parent / "qa_check.py",
        Path("qa_check.py"),
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


# ── Main logic ────────────────────────────────────────────────────────────────

def finalize(working: str, destination: str,
             pdf: str | None = None,
             strict: bool = False,
             no_qa: bool = False,
             overwrite: bool = False,
             as_json: bool = False) -> int:
    """
    Copy, verify, and QA.  Returns exit code.
    """
    results: dict = {
        'working':     working,
        'destination': destination,
        'pdf':         pdf,
        'steps':       {},
        'qa':          None,
        'ok':          False,
    }

    def step(name: str, ok: bool, detail: str = ""):
        results['steps'][name] = {'ok': ok, 'detail': detail}
        if not as_json:
            sym = tick() if ok else cross()
            print(f"  {sym}  {name}" + (f"  {dim(detail)}" if detail else ""))

    if not as_json:
        print(f"\n{bold('finalize_manifesto')}")
        print("─" * 60)

    # ── Step 1: working file exists ───────────────────────────────────────────
    working_path = Path(working)
    if not working_path.exists():
        step("Working file exists", False, f"not found: {working}")
        if as_json:
            print(json.dumps(results, indent=2))
        return 2

    working_size = working_path.stat().st_size
    step("Working file exists", True,
         f"{human_size(working_size)}  ({working_path.name})")

    # ── Step 2: destination safety check ─────────────────────────────────────
    dest_path = Path(destination)
    if dest_path.exists() and not overwrite:
        step("Destination safety check", False,
             f"file already exists: {destination}  (use --overwrite to replace)")
        if as_json:
            print(json.dumps(results, indent=2))
        return 2

    # ── Step 3: create destination folder ────────────────────────────────────
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        step("Create destination folder", True, str(dest_path.parent))
    except Exception as e:
        step("Create destination folder", False, str(e))
        if as_json:
            print(json.dumps(results, indent=2))
        return 2

    # ── Step 4: copy file ─────────────────────────────────────────────────────
    try:
        shutil.copy2(str(working_path), str(dest_path))
        dest_size = dest_path.stat().st_size
        step("Copy to destination", True,
             f"{human_size(dest_size)}  ({dest_path.name})")
    except Exception as e:
        step("Copy to destination", False, str(e))
        if as_json:
            print(json.dumps(results, indent=2))
        return 2

    # ── Step 5: SHA-256 verification ─────────────────────────────────────────
    working_hash = sha256(working_path)
    dest_hash    = sha256(dest_path)
    hash_ok      = working_hash == dest_hash

    results['steps']['sha256'] = {
        'ok':      hash_ok,
        'working': working_hash,
        'dest':    dest_hash,
    }

    if not as_json:
        sym = tick() if hash_ok else cross()
        print(f"  {sym}  SHA-256 verification")
        print(f"       working : {dim(working_hash[:16])}…")
        print(f"       dest    : {dim(dest_hash[:16])}…  "
              f"[{green('match') if hash_ok else red('MISMATCH')}]")

    if not hash_ok:
        if not as_json:
            print(f"\n  {red('ERROR: hash mismatch — destination file may be corrupted.')}")
        if as_json:
            print(json.dumps(results, indent=2))
        return 2

    # ── Step 6: QA ────────────────────────────────────────────────────────────
    qa_exit = 0
    if not no_qa:
        qa_script = find_qa_script()
        if qa_script is None:
            step("QA check", False, "qa_check.py not found alongside this script")
        else:
            cmd = [sys.executable, str(qa_script), str(dest_path)]
            if pdf:
                cmd += ['--pdf', pdf]
            if strict:
                cmd += ['--strict']
            if not as_json:
                print(f"\n  Running QA on destination file…\n")

            try:
                proc = subprocess.run(cmd, capture_output=as_json)
                qa_exit = proc.returncode

                if as_json:
                    # Re-run in JSON mode to capture structured output
                    cmd_json = [sys.executable, str(qa_script), str(dest_path), '--json']
                    if pdf:
                        cmd_json += ['--pdf', pdf]
                    proc_j = subprocess.run(cmd_json, capture_output=True, text=True)
                    try:
                        results['qa'] = json.loads(proc_j.stdout)
                    except Exception:
                        results['qa'] = {'raw': proc_j.stdout}
                else:
                    # Already printed to stdout by qa_check
                    results['qa'] = {'exit_code': qa_exit}

            except Exception as e:
                step("QA check", False, str(e))
                qa_exit = 2
    else:
        if not as_json:
            print(f"  {dim('QA skipped (--no-qa)')}")

    # ── Summary ───────────────────────────────────────────────────────────────
    results['ok'] = (qa_exit == 0)

    if not as_json:
        print("─" * 60)
        if results['ok']:
            print(f"  {green(bold('OK'))}  {dest_path}")
        else:
            print(f"  {yellow(bold('DONE with issues'))}  {dest_path}")
            if qa_exit != 0:
                print(f"  QA exit code: {qa_exit}  "
                      f"(run qa_check.py manually to review)")
        print()

    if as_json:
        print(json.dumps(results, indent=2))

    return qa_exit if qa_exit != 0 else 0


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    global USE_COLOUR

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("working",     help="Working Markdown file (source)")
    parser.add_argument("destination", help="Final destination path for the Markdown file")
    parser.add_argument("--pdf",       metavar="FILE",
                        help="Original PDF (passed to QA for coverage check)")
    parser.add_argument("--strict",    action="store_true",
                        help="Fail on QA warnings as well as errors")
    parser.add_argument("--no-qa",     dest="no_qa", action="store_true",
                        help="Skip QA step")
    parser.add_argument("--overwrite", action="store_true",
                        help="Allow overwriting an existing destination file")
    parser.add_argument("--json",      dest="as_json", action="store_true",
                        help="Output machine-readable JSON")
    parser.add_argument("--no-colour", dest="no_colour", action="store_true",
                        help="Disable ANSI colour")
    args = parser.parse_args()

    if args.no_colour or args.as_json:
        USE_COLOUR = False

    sys.exit(finalize(
        args.working,
        args.destination,
        pdf=args.pdf,
        strict=args.strict,
        no_qa=args.no_qa,
        overwrite=args.overwrite,
        as_json=args.as_json,
    ))


if __name__ == "__main__":
    main()
