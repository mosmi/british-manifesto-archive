#!/usr/bin/env python3
"""
flag_pages.py — deterministic per-page QA gate (Layer A) for the two-tier
local pipeline. No model calls, no API key.

For every page whose selected candidate is model-produced (vlm-clean /
gemini-clean / claude-clean), it:

  1. WORD-COVERAGE CHECK — compares the candidate's word count against the
     best deterministic extraction for the page (pdftotext/pdfplumber/etc.).
     A big deviation means the model dropped or hallucinated text.
     Pages with no deterministic text (image-only/scanned) are exempt.
     Two further exemptions guard against a source PDF where the
     deterministic extractors themselves can't be trusted (seen repeatedly
     across the Stormont/Holyrood batches):
       a. SPREAD CHECK (automatic) — if the deterministic candidates disagree
          with each other by more than --spread-threshold (default 3x), the
          "baseline" is probably a broken extractor, not a real measurement,
          so the coverage check is skipped for that page. This catches a
          PDF where some extractors (e.g. pdftotext-raw/pdfplumber) badly
          undercount while others (pdftotext) are fine — the classic pattern
          from Stormont 2007 DUP.
       b. COVERAGE ALLOWLIST (manual, git-tracked) — for the harder case
          where ALL deterministic extractors agree with each other but are
          still collectively wrong (e.g. a corrupted/non-standard font
          encoding, seen in Holyrood 2003 ScottishGrn and Holyrood 2016 SNP),
          there's no statistical signal to detect this automatically. A
          human has to verify it against the page images once; after that,
          `coverage_baseline_allowlist.yaml` (same spirit as qa_check.py's
          `qa_allowlist.yaml`) lets that verified exemption persist instead
          of re-flagging forever or being silently "fixed" by tweaking
          numbers no one remembers the reason for.
  2. ARTEFACT CHECK — runs qa_check.py --json on the page's text file and
     counts errors/warnings (encoding junk, heading problems, column-join
     symptoms, spacing artefacts, ...).
  3. VISION-AUDIT CARRY-FORWARD — folds in any discrepancies already
     recorded under page_rec["vision_audit"]["discrepancies"] (written by
     the manifesto-page-repair skill's in-session audit, or
     qa_audit_vision.py). This script only reads that field; it never
     clears it, so a real structural finding keeps showing up here on every
     re-gate instead of vanishing the moment the deterministic checks pass.

Pages that fail any check are written to work/<slug>/flagged_pages.json
and marked status="needs-review" with reasons in the ledger. Downstream:

  - repair_manifestos_gemini.py --only-flagged reads flagged_pages.json
  - the tier-2 Claude skill (.claude/skills/manifesto-page-repair) repairs
    exactly these pages from the page images.

Usage:
    python flag_pages.py work/<slug>/ledger.json
    python flag_pages.py work/<slug>/ledger.json --coverage-low 0.85 --coverage-high 1.25 --max-warnings 2
    python flag_pages.py work/<slug>/ledger.json --spread-threshold 4.0
    python flag_pages.py work/<slug>/ledger.json --no-allowlist
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from statistics import median
from typing import Optional

TOOLKIT_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLKIT_DIR.parents[1]
DEFAULT_ALLOWLIST_PATH = TOOLKIT_DIR / "coverage_baseline_allowlist.yaml"

MODEL_CANDIDATES = {"vlm-clean", "gemini-clean", "claude-clean"}
# Deterministic baseline = any candidate that is not model-produced.
MIN_BASELINE_WORDS = 15  # below this the page is effectively image-only; coverage check is meaningless
DEFAULT_SPREAD_THRESHOLD = 3.0  # max/min ratio among deterministic word counts before the baseline is distrusted


def run_qa_check(page_file: Path) -> list[dict]:
    """Run qa_check.py --json on one page file; return the issue list."""
    try:
        proc = subprocess.run(
            [sys.executable, str(TOOLKIT_DIR / "qa_check.py"), str(page_file), "--json"],
            capture_output=True, text=True, timeout=60,
        )
        return json.loads(proc.stdout) if proc.stdout.strip() else []
    except Exception as e:
        return [{"code": "X0", "severity": "warning", "line": 0,
                 "excerpt": "", "detail": f"qa_check failed to run: {e}"}]


def load_coverage_allowlist(path: Optional[Path]) -> dict[str, dict]:
    """
    Load coverage_baseline_allowlist.yaml -> {slug: {"pages": set[int] | None, "reason": str}}.
    A None "pages" value means the whole document is exempt from the coverage
    check (used when every deterministic extractor agrees with every other
    one but all are wrong, e.g. a corrupted font encoding across the whole
    PDF - a per-page spread check can't catch that since there's no internal
    disagreement to detect). Returns {} if the file is missing, empty, or
    PyYAML isn't installed (degrades to "no allowlist", never an error).
    """
    if path is None or not path.exists():
        return {}
    try:
        import yaml  # type: ignore
        entries = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    except ImportError:
        return {}
    except Exception as e:
        print(f"WARNING: could not parse {path}: {e}", file=sys.stderr)
        return {}

    result: dict[str, dict] = {}
    for entry in entries or []:
        slug = entry.get("slug")
        if not slug:
            continue
        pages = entry.get("pages")
        result[slug] = {
            "pages": set(pages) if pages is not None else None,
            "reason": entry.get("reason", "(no reason given)"),
        }
    return result


def main():
    parser = argparse.ArgumentParser(description="Flag model-transcribed pages that need tier-2 (frontier model) review.")
    parser.add_argument("ledger", help="Path to work/<slug>/ledger.json")
    parser.add_argument("--coverage-low", type=float, default=0.85,
                        help="Flag if candidate words / baseline words < this (default 0.85)")
    parser.add_argument("--coverage-high", type=float, default=1.30,
                        help="Flag if candidate words / baseline words > this (default 1.30)")
    parser.add_argument("--max-warnings", type=int, default=3,
                        help="Flag if qa_check reports more than this many warnings (default 3); any error always flags")
    parser.add_argument("--spread-threshold", type=float, default=DEFAULT_SPREAD_THRESHOLD,
                        help=f"Skip the coverage check on a page when deterministic candidates' word counts "
                             f"disagree by more than this max/min ratio - the baseline is probably a broken "
                             f"extractor, not a real measurement (default {DEFAULT_SPREAD_THRESHOLD})")
    parser.add_argument("--allowlist", default=str(DEFAULT_ALLOWLIST_PATH),
                        help=f"Path to coverage_baseline_allowlist.yaml (default: {DEFAULT_ALLOWLIST_PATH.name} next to this script)")
    parser.add_argument("--no-allowlist", action="store_true", help="Disable coverage allowlist loading entirely")
    parser.add_argument("--json", action="store_true", help="Print the flag report JSON to stdout too")
    args = parser.parse_args()

    ledger_path = Path(args.ledger).resolve()
    if not ledger_path.exists():
        print(f"ERROR: ledger not found at {ledger_path}", file=sys.stderr)
        sys.exit(1)
    work_dir = ledger_path.parent
    with open(ledger_path, encoding="utf-8") as f:
        ledger = json.load(f)

    allowlist = {} if args.no_allowlist else load_coverage_allowlist(Path(args.allowlist))
    doc_allowlist = allowlist.get(work_dir.name)

    flagged: list[dict] = []
    checked = 0

    for page_rec in sorted(ledger.get("pages", []), key=lambda p: p.get("page_index", 0)):
        idx = page_rec.get("page_index")
        selected = page_rec.get("selected_candidate")
        if selected not in MODEL_CANDIDATES:
            continue  # deterministic pages are handled by the existing full-document QA
        cand = next((c for c in page_rec.get("candidates", []) if c.get("method") == selected), None)
        if not cand or not cand.get("output_file"):
            flagged.append({"page_index": idx, "reasons": ["selected candidate file missing"]})
            continue
        out_ref = Path(cand["output_file"])
        page_file = out_ref if out_ref.is_absolute() else REPO_ROOT / out_ref
        if not page_file.exists():  # fall back to path relative to the work dir
            page_file = (work_dir / out_ref).resolve()
        if not page_file.exists():
            flagged.append({"page_index": idx, "reasons": ["selected candidate file missing on disk"]})
            continue

        checked += 1
        reasons: list[str] = []

        # 1. Word coverage vs deterministic baseline.
        # Use the MEDIAN of the deterministic extractors, not the max: some
        # extractors (notably pdfplumber on multi-column pages) fragment
        # positioned text and roughly double the word count, so max() picks
        # that outlier and makes every clean page look like it dropped text.
        baseline_counts = sorted(
            (c.get("word_count") or 0)
            for c in page_rec.get("candidates", [])
            if c.get("method") not in MODEL_CANDIDATES
        )
        baseline = int(round(median(baseline_counts))) if baseline_counts else 0
        cand_words = cand.get("word_count") or len(page_file.read_text(encoding="utf-8").split())

        # 1a. Manual, git-tracked exemption for whole-document/whole-page
        # extractor failures a human has already verified against the images
        # (e.g. a corrupted font encoding every extractor reads the same
        # wrong way, so there's no internal disagreement to detect automatically).
        allowlisted = doc_allowlist is not None and (
            doc_allowlist["pages"] is None or idx in doc_allowlist["pages"]
        )
        # 1b. Automatic exemption when the deterministic extractors disagree
        # with each other too widely to trust any single point estimate -
        # the "baseline" is probably a broken extractor, not signal.
        nonzero = [c for c in baseline_counts if c > 0]
        spread = (max(nonzero) / min(nonzero)) if len(nonzero) >= 2 else 1.0
        spread_unreliable = spread > args.spread_threshold

        if allowlisted:
            print(f"  page {idx}: coverage check skipped (allowlisted: {doc_allowlist['reason']})", file=sys.stderr)
        elif spread_unreliable:
            print(f"  page {idx}: coverage check skipped (deterministic extractors disagree "
                  f"{spread:.1f}x, min {min(nonzero)}/max {max(nonzero)} words — baseline unreliable)", file=sys.stderr)
        elif baseline >= MIN_BASELINE_WORDS:
            ratio = cand_words / baseline if baseline else 0.0
            if ratio < args.coverage_low:
                reasons.append(f"coverage low: {cand_words}/{baseline} words (ratio {ratio:.2f})")
            elif ratio > args.coverage_high:
                reasons.append(f"coverage high: {cand_words}/{baseline} words (ratio {ratio:.2f}) — possible hallucination/duplication")

        # 2. qa_check artefact scan on the page text
        issues = run_qa_check(page_file)
        errors = [i for i in issues if i.get("severity") == "error"]
        warnings = [i for i in issues if i.get("severity") == "warning"]
        if errors:
            reasons.append(f"qa_check errors: {', '.join(sorted({i['code'] for i in errors}))}")
        if len(warnings) > args.max_warnings:
            reasons.append(f"qa_check warnings ({len(warnings)}): {', '.join(sorted({i['code'] for i in warnings}))}")

        # 3. Vision-audit discrepancies (written by the manifesto-page-repair
        # skill's in-session structural audit, or qa_audit_vision.py). This
        # script only reads this field, never writes it, so a discrepancy
        # recorded here survives every future re-gate instead of being
        # silently overwritten the moment the deterministic checks pass.
        # Clearing it is the auditor's job (re-run the audit clean), not
        # this gate's.
        vision_discrepancies = (page_rec.get("vision_audit") or {}).get("discrepancies") or []
        for d in vision_discrepancies:
            note = d.get("note") or ""
            reasons.append(f"vision_audit: {d.get('type', 'unknown')} — {note}".rstrip(" —"))

        if reasons:
            flagged.append({"page_index": idx, "reasons": reasons})
            page_rec["status"] = "needs-review"
            page_rec["issues"] = reasons
        else:
            page_rec["status"] = "reviewed"
            page_rec["issues"] = []

    report = {
        "ledger": str(ledger_path.relative_to(REPO_ROOT)) if ledger_path.is_relative_to(REPO_ROOT) else str(ledger_path),
        "pages_checked": checked,
        "flagged_count": len(flagged),
        "thresholds": {"coverage_low": args.coverage_low, "coverage_high": args.coverage_high,
                       "max_warnings": args.max_warnings},
        "flagged": flagged,
    }
    out_path = work_dir / "flagged_pages.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        f.write("\n")
    with open(ledger_path, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Checked {checked} model-transcribed page(s); flagged {len(flagged)} for tier-2 review.")
    for entry in flagged:
        print(f"  page {entry['page_index']}: {'; '.join(entry['reasons'])}")
    print(f"Report: {out_path}")
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
