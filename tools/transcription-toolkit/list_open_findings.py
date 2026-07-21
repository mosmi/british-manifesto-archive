#!/usr/bin/env python3
"""
list_open_findings.py — one place to see every open tier-2 finding across all
work directories, instead of hand-compiling them from chat/agent summaries.

Scans every tools/transcription-toolkit/work/<slug>/ledger.json and reports,
per page:
  - any recorded page_rec["vision_audit"]["discrepancies"] (from the
    manifesto-page-repair skill's in-session audit, or qa_audit_vision.py) —
    these persist across flag_pages.py re-runs by design (see flag_pages.py's
    "VISION-AUDIT CARRY-FORWARD" step), so this is the authoritative list of
    genuine structural findings still awaiting a human decision.
  - any page still at status == "needs-review" for another reason (coverage
    heuristic, qa_check warnings) — these are usually, but not always,
    false positives; skimming them here beats re-deriving them per-ledger.

This script only reads ledgers; it never writes anything.

Usage:
    python list_open_findings.py
    python list_open_findings.py --work-root tools/transcription-toolkit/work
    python list_open_findings.py --slug-filter stormont
    python list_open_findings.py --json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TOOLKIT_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLKIT_DIR.parents[1]
DEFAULT_WORK_ROOT = TOOLKIT_DIR / "work"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--work-root", default=str(DEFAULT_WORK_ROOT), help="Directory containing <slug>/ledger.json dirs.")
    parser.add_argument("--slug-filter", default=None, help="Only report slugs containing this substring.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of a text report.")
    args = parser.parse_args()

    work_root = Path(args.work_root)
    if not work_root.exists():
        print(f"ERROR: work root not found: {work_root}", file=sys.stderr)
        return 2

    results = []
    for ledger_path in sorted(work_root.glob("*/ledger.json")):
        slug = ledger_path.parent.name
        if args.slug_filter and args.slug_filter not in slug:
            continue
        try:
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"WARNING: could not read {ledger_path}: {e}", file=sys.stderr)
            continue

        for page in ledger.get("pages", []):
            idx = page.get("page_index")
            vision_audit = page.get("vision_audit") or {}
            discrepancies = vision_audit.get("discrepancies") or []
            status = page.get("status")
            issues = page.get("issues") or []

            if not discrepancies and status != "needs-review":
                continue

            results.append({
                "slug": slug,
                "page_index": idx,
                "status": status,
                "vision_audit_discrepancies": discrepancies,
                "gate_issues": issues,
            })

    if args.json:
        print(json.dumps({"work_root": str(work_root), "open_findings": results}, indent=2, ensure_ascii=False))
        return 0

    if not results:
        print("No open findings.")
        return 0

    genuine = [r for r in results if r["vision_audit_discrepancies"]]
    gate_only = [r for r in results if not r["vision_audit_discrepancies"]]

    if genuine:
        print(f"=== {len(genuine)} page(s) with a recorded vision-audit discrepancy (needs a human decision) ===\n")
        for r in genuine:
            print(f"{r['slug']}  page {r['page_index']}")
            for d in r["vision_audit_discrepancies"]:
                locator = d.get("locator") or ""
                note = d.get("note") or ""
                print(f"    {d.get('type', 'unknown')} — {locator} — {note}")
            print()

    if gate_only:
        print(f"=== {len(gate_only)} page(s) flagged by the deterministic gate only (often false positives, unverified) ===\n")
        for r in gate_only:
            print(f"{r['slug']}  page {r['page_index']}: {'; '.join(r['gate_issues'])}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
