#!/usr/bin/env python3
import sys
import os
import re
import json
import base64
import argparse
from pathlib import Path

TOOLKIT_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLKIT_DIR.parents[1]

sys.path.insert(0, str(TOOLKIT_DIR / "lib"))
try:
    from openai import OpenAI
except ImportError:
    print("ERROR: openai package not found. Run pip install openai --break-system-packages", file=sys.stderr)
    sys.exit(1)

def load_env():
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                os.environ.setdefault(key.strip(), val.strip())

load_env()

def get_gemini_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY is not set in environment or .env file", file=sys.stderr)
        return None
    return OpenAI(
        api_key=api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""

def write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

PROMPT_TEMPLATE = """You are a meticulous archivist transcribing political manifestos into clean, structured Markdown.
Your goal is to output a perfect, human-readable transcription of the attached page image, using the provided raw machine transcription as a starting draft.

Raw starting draft:
---
{candidate_text}
---

Follow these strict rules:
1. READING ORDER: Transcribe multi-column layouts linearly (left column first in its entirety, then right column). Never interleave sentences or lines between columns. Ensure sentences that split across columns flow logically and completely.
2. HEADINGS: Format distinct section headings with proper markdown levels:
   - Use `#` only for the document's main title (if present on the page).
   - Use `##` for main section headings.
   - Use `###` for sub-headings.
   - Never format running text paragraphs as headings.
3. BOILERPLATE: Strip out running headers, running footers, social media links/buttons, and page numbers from the top and bottom of the page.
4. TEXT FIDELITY: Keep every single word, number, and policy from the original page. Do not summarize, shorten, paraphrase, or take shortcuts.
5. FORMATTING: Use bold, italics, lists, and tables exactly as they appear visually in the image.

Output ONLY the clean Markdown text for this page. Do not include any introductory comments, notes, or backticks."""

def clean_page(client: OpenAI, image_path: Path, candidate_text: str) -> str:
    with open(image_path, "rb") as f:
        img_bytes = f.read()
    b64 = base64.b64encode(img_bytes).decode("ascii")

    # Determine media type
    suffix = image_path.suffix.lower()
    media_type = "image/jpeg" if suffix in (".jpg", ".jpeg") else "image/png"

    prompt = PROMPT_TEMPLATE.format(candidate_text=candidate_text)

    response = client.chat.completions.create(
        model="gemini-2.5-flash",
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{media_type};base64,{b64}"
                    }
                },
                {"type": "text", "text": prompt},
            ],
        }]
    )
    return response.choices[0].message.content.strip()

def main():
    parser = argparse.ArgumentParser(description="Repair audited markdown files page-by-page using Gemini Vision API.")
    parser.add_argument("ledger", help="Path to ledger.json (e.g. tools/transcription-toolkit/work/<slug>/ledger.json)")
    parser.add_argument("--pages", help="Comma-separated pages to clean (0-indexed). If omitted, processes all pages.")
    parser.add_argument("--only-flagged", action="store_true", help="Only process pages flagged in vision_audit_report.json or having ledger issues.")
    args = parser.parse_args()

    ledger_path = Path(args.ledger).resolve()
    if not ledger_path.exists():
        print(f"ERROR: ledger not found at {ledger_path}", file=sys.stderr)
        sys.exit(1)

    client = get_gemini_client()
    if not client:
        sys.exit(1)

    work_dir = ledger_path.parent
    with open(ledger_path, encoding="utf-8") as f:
        ledger = json.load(f)

    # Load vision audit report to check for flagged pages
    flagged_pages = set()
    report_json = work_dir / "vision_audit_report.json"
    if report_json.exists():
        try:
            with open(report_json, encoding="utf-8") as f:
                report = json.load(f)
            for res in report.get("results", []):
                if res.get("findings"):
                    # Check if findings are real issues (exclude empty lists or harmless ones)
                    real_findings = [f for f in res["findings"] if f.get("type") != "spurious_text" or "footer" not in str(f.get("locator")).lower()]
                    if real_findings:
                        flagged_pages.add(res["page_index"])
        except Exception as e:
            print(f"WARNING: failed to parse vision_audit_report.json: {e}")

    # Determine pages to process
    if args.pages:
        pages_to_process = []
        for part in args.pages.split(","):
            if "-" in part:
                start, end = map(int, part.split("-"))
                pages_to_process.extend(range(start, end + 1))
            else:
                pages_to_process.append(int(part))
    else:
        pages_to_process = list(range(len(ledger.get("pages", []))))

    if args.only_flagged:
        pages_to_process = [idx for idx in pages_to_process if idx in flagged_pages]

    print(f"Selected {len(pages_to_process)} page(s) to visually clean using Gemini...")

    pages_dir = work_dir / "pages"
    images_dir = work_dir / "images"

    for idx in pages_to_process:
        print(f"\nProcessing page {idx}...")
        page_rec = next((p for p in ledger.get("pages", []) if p.get("page_index") == idx), None)
        if not page_rec:
            print(f"  WARNING: Page record {idx} not found in ledger. Skipping.")
            continue

        if page_rec.get("selected_candidate") == "gemini-clean" and not args.pages:
            print(f"  Page {idx} already cleaned (gemini-clean selected). Skipping.")
            continue

        # Find image path
        image_path = None
        for fmt in [f"page-{idx+1}.png", f"page-{idx+1:02d}.png", f"page-{idx+1:03d}.png"]:
            cand = images_dir / fmt
            if cand.exists():
                image_path = cand
                break
        
        if not image_path:
            print(f"  ERROR: Page image not found for index {idx}. Skipping.")
            continue

        # Find starting text
        # Try best candidate output file, falling back to any candidate
        best_candidate = page_rec.get("selected_candidate")
        start_text = ""
        if best_candidate:
            cand = next((c for c in page_rec.get("candidates", []) if c.get("method") == best_candidate), None)
            if cand and cand.get("output_file"):
                start_text = read_text(REPO_ROOT / cand["output_file"])
        
        if not start_text:
            # Fallback to first available candidate text
            for cand in page_rec.get("candidates", []):
                if cand.get("output_file") and cand.get("available"):
                    start_text = read_text(REPO_ROOT / cand["output_file"])
                    if start_text:
                        break

        print(f"  Image: {image_path.name}")
        print(f"  Starting draft: {len(start_text)} chars")

        try:
            cleaned_text = clean_page(client, image_path, start_text)
            
            # Save cleaned page text
            out_file = pages_dir / f"page-{idx:03d}.gemini-clean.txt"
            write_text(out_file, cleaned_text)
            print(f"  Cleaned text saved: {out_file.name} ({len(cleaned_text)} chars)")

            # Update page_rec in ledger
            # Add or update gemini-clean candidate
            cand_name = "gemini-clean"
            gemini_cand = next((c for c in page_rec.get("candidates", []) if c.get("method") == cand_name), None)
            
            words = len(cleaned_text.split())
            rel_out = str(out_file.relative_to(REPO_ROOT))
            
            if gemini_cand:
                gemini_cand["available"] = True
                gemini_cand["word_count"] = words
                gemini_cand["output_file"] = rel_out
            else:
                page_rec.get("candidates", []).append({
                    "method": cand_name,
                    "available": True,
                    "word_count": words,
                    "artifact_score": 0.0,
                    "output_file": rel_out,
                    "error": None
                })
            
            page_rec["selected_candidate"] = cand_name
            page_rec["status"] = "reviewed"
            page_rec["issues"] = []
            
        except Exception as e:
            print(f"  ERROR cleaning page {idx}: {e}")

    # Write updated ledger.json
    with open(ledger_path, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # Assemble new draft.md
    print("\nAssembling draft.md from selected candidates...")
    draft_parts = []
    
    # Sort pages by index
    sorted_pages = sorted(ledger.get("pages", []), key=lambda p: p.get("page_index", 0))
    for page_rec in sorted_pages:
        best_candidate = page_rec.get("selected_candidate")
        page_text = ""
        if best_candidate:
            cand = next((c for c in page_rec.get("candidates", []) if c.get("method") == best_candidate), None)
            if cand and cand.get("output_file"):
                page_text = read_text(REPO_ROOT / cand["output_file"])
        
        # Clean page title placeholder or simple H1 from prompt if model output it
        page_text = page_text.strip()
        if page_text:
            draft_parts.append(page_text)

    # Join pages with double newline
    final_draft = "\n\n".join(draft_parts) + "\n"
    write_text(work_dir / "draft.md", final_draft)
    print(f"Successfully assembled and wrote to {work_dir / 'draft.md'}")

if __name__ == "__main__":
    main()
