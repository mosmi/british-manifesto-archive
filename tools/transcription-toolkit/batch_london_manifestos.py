#!/usr/bin/env python3
import sys
import os
import subprocess
from pathlib import Path

TOOLKIT_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLKIT_DIR.parents[1]

# Mappings of election -> candidates
BATCHES = {
    "1": [
        "manifestos/london/gla-2024/sdp/manifesto.pdf",
        "manifestos/london/gla-2024/londonreal/manifesto.pdf",
        "manifestos/london/gla-2024/binface/manifesto.pdf",
        "manifestos/london/gla-2024/awp/manifesto.pdf",
        "manifestos/london/gla-2024/reform/manifesto.pdf",
        "manifestos/london/gla-2024/conservative/manifesto.pdf"
    ],
    "2": [
        "manifestos/london/gla-2024/michli/manifesto.pdf",
        "manifestos/london/gla-2024/campbell/manifesto.pdf",
        "manifestos/london/gla-2024/britainfirst/manifesto.pdf",
        "manifestos/london/gla-2024/libdem/manifesto.pdf",
        "manifestos/london/gla-2024/labour/manifesto.pdf",
        "manifestos/london/gla-2024/ghulati/manifesto.pdf",
        "manifestos/london/gla-2024/green/manifesto.pdf"
    ],
    "3": [
        "manifestos/london/gla-2021/labour/manifesto.pdf",
        "manifestos/london/gla-2021/conservative/manifesto.pdf",
        "manifestos/london/gla-2021/libdem/manifesto.pdf",
        "manifestos/london/gla-2021/green/manifesto.pdf",
        "manifestos/london/gla-2021/londonreal/manifesto.pdf",
        "manifestos/london/gla-2021/reclaim/manifesto.pdf",
        "manifestos/london/gla-2021/binface/manifesto.pdf",
        "manifestos/london/gla-2021/pierscorbyn/manifesto.pdf",
        "manifestos/london/gla-2021/burningpink/manifesto.pdf",
        "manifestos/london/gla-2021/maxfosh/manifesto.pdf"
    ],
    "4": [
        "manifestos/london/gla-2004/libdem/manifesto.pdf",
        "manifestos/london/gla-2004/green/manifesto.pdf",
        "manifestos/london/gla-2004/cpa/manifesto.pdf"
    ],
    "5": [
        "manifestos/london/gla-2016/labour/manifesto.pdf",
        "manifestos/london/gla-2016/conservative/manifesto.pdf",
        "manifestos/london/gla-2016/libdem/manifesto.pdf",
        "manifestos/london/gla-2016/green/manifesto.pdf",
        "manifestos/london/gla-2016/ukip/manifesto.pdf",
        "manifestos/london/gla-2016/respect/manifesto.pdf",
        "manifestos/london/gla-2016/wep/manifesto.pdf",
        "manifestos/london/gla-2016/bnp/manifesto.pdf",
        "manifestos/london/gla-2016/onelove/manifesto.pdf"
    ],
    "6": [
        "manifestos/london/gla-2012/labour/manifesto.pdf",
        "manifestos/london/gla-2012/conservative/manifesto.pdf",
        "manifestos/london/gla-2012/libdem/manifesto.pdf",
        "manifestos/london/gla-2012/green/manifesto.pdf",
        "manifestos/london/gla-2012/bnp/manifesto.pdf",
        "manifestos/london/gla-2012/benita/manifesto.pdf"
    ],
    "7": [
        "manifestos/london/gla-2008/conservative/manifesto.pdf",
        "manifestos/london/gla-2008/libdem/manifesto.pdf",
        "manifestos/london/gla-2008/cooperative/manifesto.pdf",
        "manifestos/london/gla-2008/green/manifesto.pdf",
        "manifestos/london/gla-2008/englishdemocrats/manifesto.pdf"
    ],
    "8": [
        "manifestos/london/gla-2000/livingstone/manifesto.pdf"
    ]
}

def run_cmd(args):
    print(f"Running: {' '.join(args)}")
    res = subprocess.run(args, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"ERROR running command. Stdout:\n{res.stdout}\nStderr:\n{res.stderr}")
    return res.returncode == 0

def slug_for_pdf(pdf_path: str) -> str:
    # Matches work dir naming convention: manifestos__london__gla-2024__sdp__manifesto
    slug = pdf_path.replace(".pdf", "").replace("/", "__").replace("\\", "__")
    return slug

def process_pdf(pdf_rel_path: str):
    pdf_path = REPO_ROOT / pdf_rel_path
    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}")
        return False

    slug = slug_for_pdf(pdf_rel_path)
    work_dir = TOOLKIT_DIR / "work" / slug
    ledger_json = work_dir / "ledger.json"

    print(f"\n==================================================")
    print(f"Processing {pdf_rel_path}...")
    print(f"==================================================")

    # 1. Run transcribe_pipeline.py new
    ok = run_cmd([
        sys.executable,
        str(TOOLKIT_DIR / "transcribe_pipeline.py"),
        "new",
        str(pdf_path)
    ])
    if not ok:
        return False

    # Get page count from ledger
    if not ledger_json.exists():
        print(f"Error: ledger.json not created at {ledger_json}")
        return False

    import json
    with open(ledger_json, encoding="utf-8") as f:
        ledger_data = json.load(f)
    page_count = len(ledger_data.get("pages", []))
    print(f"Found {page_count} page(s) in ledger.")

    if page_count == 0:
        print("No pages to process.")
        return True

    # 2. Run vision audit on all pages
    page_range = f"0-{page_count - 1}"
    print(f"Running vision audit on pages: {page_range}...")
    ok = run_cmd([
        sys.executable,
        str(TOOLKIT_DIR / "qa_audit_vision.py"),
        str(ledger_json),
        "--pages", page_range,
        "--force",
        "--model", "gemini-2.5-flash"
    ])
    if not ok:
        print("Vision audit failed (continuing anyway).")

    # 3. Generate checklist
    print("Generating review checklist...")
    ok = run_cmd([
        sys.executable,
        str(TOOLKIT_DIR / "transcribe_pipeline.py"),
        "checklist",
        str(ledger_json)
    ])
    
    return ok

def main():
    if len(sys.argv) < 2:
        print("Usage: python batch_london_manifestos.py <batch_number>")
        print("Available batches: 1, 2, 3, 4, 5, 6, 7, 8")
        sys.exit(1)

    batch_num = sys.argv[1]
    if batch_num not in BATCHES:
        print(f"Unknown batch number: {batch_num}")
        sys.exit(1)

    pdf_list = BATCHES[batch_num]
    print(f"Starting Batch {batch_num} ({len(pdf_list)} manifestos)...")

    success_count = 0
    for pdf in pdf_list:
        if process_pdf(pdf):
            success_count += 1

    print(f"\nBatch {batch_num} complete! Successfully processed {success_count}/{len(pdf_list)} manifestos.")

if __name__ == "__main__":
    main()
