#!/usr/bin/env python3
"""
repair_manifestos_gemini.py — page-by-page visual transcription/repair.

Despite the legacy filename (kept so existing batch scripts keep working),
this script is backend-agnostic. It talks to any OpenAI-compatible
chat-completions endpoint that accepts images:

  --backend local   (DEFAULT) a local model server on this machine —
                    LM Studio (http://localhost:1234/v1) or oMLX — running a
                    document-OCR VLM such as DeepSeek-OCR. No API key, no
                    per-token cost. See LOCAL_SETUP.md.
  --backend gemini  the legacy paid path (GEMINI_API_KEY in .env).

Two prompt modes:
  --mode ocr        (default for local) sends ONLY the page image and asks
                    the model to convert it to Markdown. This is what
                    dedicated OCR VLMs (DeepSeek-OCR, dots.ocr) are trained
                    for; they ignore/are confused by "repair this draft"
                    instructions.
  --mode repair     (default for gemini) sends the image plus the ledger's
                    selected candidate text as a starting draft, with the
                    original strict repair rules. Use for general-purpose
                    VLMs (Gemini, Qwen-VL, ...).

Other useful flags:
  --reassemble-only rebuild draft.md from the ledger's selected candidates
                    without calling any model (used by the tier-2 Claude
                    skill after it writes claude-clean pages).
  --pages 0,3,5-9   explicit page list; --only-flagged uses
                    vision_audit_report.json / flagged_pages.json / ledger
                    issues.

Examples:
  python repair_manifestos_gemini.py work/<slug>/ledger.json
  python repair_manifestos_gemini.py work/<slug>/ledger.json --model deepseek-ocr-8bit
  python repair_manifestos_gemini.py work/<slug>/ledger.json --backend gemini --only-flagged
  python repair_manifestos_gemini.py work/<slug>/ledger.json --reassemble-only
"""
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

DEFAULT_LOCAL_BASE_URL = "http://localhost:1234/v1"   # LM Studio default; oMLX uses its own port
DEFAULT_LOCAL_MODEL = "deepseek-ocr"                  # check `lms ls` / server UI for the exact id
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"

# Candidate names by backend (ledger "method" field / page file suffix)
CANDIDATE_NAMES = {"local": "vlm-clean", "gemini": "gemini-clean"}
# All model-produced candidate methods (used to find deterministic baselines elsewhere)
MODEL_CANDIDATES = {"vlm-clean", "gemini-clean", "claude-clean"}


def load_env():
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                os.environ.setdefault(key.strip(), val.strip())


load_env()


def get_client(args) -> OpenAI | None:
    if args.backend == "gemini":
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("ERROR: GEMINI_API_KEY is not set in environment or .env file", file=sys.stderr)
            return None
        return OpenAI(api_key=api_key, base_url=args.base_url or GEMINI_BASE_URL)
    # local: OpenAI-compatible server, key is a placeholder
    return OpenAI(api_key=os.environ.get("LOCAL_VLM_API_KEY", "not-needed"),
                  base_url=args.base_url or DEFAULT_LOCAL_BASE_URL)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


REPAIR_PROMPT_TEMPLATE = """You are a meticulous archivist transcribing political manifestos into clean, structured Markdown.
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

# Dedicated OCR VLMs are trained on short conversion instructions; keep it simple.
OCR_PROMPT = "Convert the document to markdown."


def postprocess_model_output(text: str) -> str:
    """Strip wrappers/artefacts local OCR models commonly emit."""
    text = text.strip()
    # Fenced whole-output: ```markdown ... ```
    m = re.match(r"^```(?:markdown|md)?\s*\n(.*)\n```$", text, re.DOTALL)
    if m:
        text = m.group(1).strip()
    # DeepSeek-OCR grounding tokens: <|ref|>...<|/ref|><|det|>[[..]]<|/det|>, <|grounding|>
    text = re.sub(r"<\|/?(?:ref|det|grounding)\|>", "", text)
    text = re.sub(r"\[\[\d+(?:,\s*\d+)*\]\](?:,?\s*\[\[\d+(?:,\s*\d+)*\]\])*", "", text)
    # Image placeholders some OCR models emit for figures
    text = re.sub(r"^!\[[^\]]*\]\(\s*\)$", "", text, flags=re.MULTILINE)
    # Collapse 3+ blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_page(client: OpenAI, args, image_path: Path, candidate_text: str) -> str:
    with open(image_path, "rb") as f:
        img_bytes = f.read()
    b64 = base64.b64encode(img_bytes).decode("ascii")

    suffix = image_path.suffix.lower()
    media_type = "image/jpeg" if suffix in (".jpg", ".jpeg") else "image/png"

    if args.mode == "ocr":
        prompt = args.ocr_prompt or OCR_PROMPT
    else:
        prompt = REPAIR_PROMPT_TEMPLATE.format(candidate_text=candidate_text)

    response = client.chat.completions.create(
        model=args.model,
        temperature=0.0,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{b64}"}},
                {"type": "text", "text": prompt},
            ],
        }],
    )
    return postprocess_model_output(response.choices[0].message.content or "")


def collect_flagged_pages(work_dir: Path) -> set[int]:
    """Union of pages flagged by the vision audit report (legacy) and
    flagged_pages.json (Layer A gate, flag_pages.py)."""
    flagged: set[int] = set()
    report_json = work_dir / "vision_audit_report.json"
    if report_json.exists():
        try:
            with open(report_json, encoding="utf-8") as f:
                report = json.load(f)
            for res in report.get("results", []):
                if res.get("findings"):
                    real = [f for f in res["findings"]
                            if f.get("type") != "spurious_text" or "footer" not in str(f.get("locator")).lower()]
                    if real:
                        flagged.add(res["page_index"])
        except Exception as e:
            print(f"WARNING: failed to parse vision_audit_report.json: {e}")
    gate_json = work_dir / "flagged_pages.json"
    if gate_json.exists():
        try:
            with open(gate_json, encoding="utf-8") as f:
                gate = json.load(f)
            for entry in gate.get("flagged", []):
                flagged.add(entry["page_index"])
        except Exception as e:
            print(f"WARNING: failed to parse flagged_pages.json: {e}")
    return flagged


def reassemble_draft(ledger: dict, work_dir: Path):
    print("\nAssembling draft.md from selected candidates...")
    draft_parts = []
    sorted_pages = sorted(ledger.get("pages", []), key=lambda p: p.get("page_index", 0))
    for page_rec in sorted_pages:
        best_candidate = page_rec.get("selected_candidate")
        page_text = ""
        if best_candidate:
            cand = next((c for c in page_rec.get("candidates", []) if c.get("method") == best_candidate), None)
            if cand and cand.get("output_file"):
                page_text = read_text(REPO_ROOT / cand["output_file"])
        page_text = page_text.strip()
        if page_text:
            draft_parts.append(page_text)
    final_draft = "\n\n".join(draft_parts) + "\n"
    write_text(work_dir / "draft.md", final_draft)
    print(f"Successfully assembled and wrote to {work_dir / 'draft.md'}")


def register_candidate(page_rec: dict, cand_name: str, out_file: Path, text: str):
    words = len(text.split())
    rel_out = str(out_file.relative_to(REPO_ROOT))
    cand = next((c for c in page_rec.get("candidates", []) if c.get("method") == cand_name), None)
    if cand:
        cand["available"] = True
        cand["word_count"] = words
        cand["output_file"] = rel_out
    else:
        page_rec.setdefault("candidates", []).append({
            "method": cand_name,
            "available": True,
            "word_count": words,
            "artifact_score": 0.0,
            "output_file": rel_out,
            "error": None,
        })
    page_rec["selected_candidate"] = cand_name
    page_rec["status"] = "reviewed"
    page_rec["issues"] = []


def main():
    parser = argparse.ArgumentParser(description="Transcribe/repair manifesto pages via a local or cloud vision model.")
    parser.add_argument("ledger", help="Path to ledger.json (e.g. tools/transcription-toolkit/work/<slug>/ledger.json)")
    parser.add_argument("--backend", choices=["local", "gemini"], default="local",
                        help="local = OpenAI-compatible server on this machine (default); gemini = legacy paid API")
    parser.add_argument("--base-url", help="Override endpoint base URL (default: LM Studio localhost:1234/v1 or Gemini)")
    parser.add_argument("--model", help="Model id (default: deepseek-ocr for local, gemini-2.5-flash for gemini)")
    parser.add_argument("--mode", choices=["ocr", "repair"],
                        help="ocr = image-only transcription (default for local); repair = image + draft (default for gemini)")
    parser.add_argument("--ocr-prompt", help="Override the OCR-mode prompt")
    parser.add_argument("--candidate-name", help="Ledger candidate name (default: vlm-clean for local, gemini-clean for gemini)")
    parser.add_argument("--pages", help="Comma-separated pages to clean (0-indexed). If omitted, processes all pages.")
    parser.add_argument("--only-flagged", action="store_true",
                        help="Only process pages flagged in flagged_pages.json / vision_audit_report.json.")
    parser.add_argument("--force", action="store_true", help="Re-process pages even if already cleaned by this candidate.")
    parser.add_argument("--reassemble-only", action="store_true",
                        help="Just rebuild draft.md from selected candidates; no model calls.")
    args = parser.parse_args()

    if not args.model:
        args.model = DEFAULT_LOCAL_MODEL if args.backend == "local" else DEFAULT_GEMINI_MODEL
    if not args.mode:
        args.mode = "ocr" if args.backend == "local" else "repair"
    cand_name = args.candidate_name or CANDIDATE_NAMES[args.backend]

    ledger_path = Path(args.ledger).resolve()
    if not ledger_path.exists():
        print(f"ERROR: ledger not found at {ledger_path}", file=sys.stderr)
        sys.exit(1)

    work_dir = ledger_path.parent
    with open(ledger_path, encoding="utf-8") as f:
        ledger = json.load(f)

    if args.reassemble_only:
        reassemble_draft(ledger, work_dir)
        return

    client = get_client(args)
    if not client:
        sys.exit(1)

    flagged_pages = collect_flagged_pages(work_dir)

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

    print(f"Backend: {args.backend}  model: {args.model}  mode: {args.mode}  candidate: {cand_name}")
    print(f"Selected {len(pages_to_process)} page(s) to visually clean...")

    pages_dir = work_dir / "pages"
    images_dir = work_dir / "images"

    for idx in pages_to_process:
        print(f"\nProcessing page {idx}...")
        page_rec = next((p for p in ledger.get("pages", []) if p.get("page_index") == idx), None)
        if not page_rec:
            print(f"  WARNING: Page record {idx} not found in ledger. Skipping.")
            continue

        # Skip already-cleaned pages only on a plain full run; explicit --pages,
        # --only-flagged (the gate says this page is bad) or --force always re-process.
        if (page_rec.get("selected_candidate") == cand_name
                and not args.pages and not args.force and not args.only_flagged):
            print(f"  Page {idx} already cleaned ({cand_name} selected). Skipping.")
            continue

        image_path = None
        for fmt in [f"page-{idx+1}.png", f"page-{idx+1:02d}.png", f"page-{idx+1:03d}.png"]:
            cand_img = images_dir / fmt
            if cand_img.exists():
                image_path = cand_img
                break

        if not image_path:
            print(f"  ERROR: Page image not found for index {idx}. Skipping.")
            continue

        # Starting text only needed for repair mode
        start_text = ""
        if args.mode == "repair":
            best_candidate = page_rec.get("selected_candidate")
            if best_candidate:
                cand = next((c for c in page_rec.get("candidates", []) if c.get("method") == best_candidate), None)
                if cand and cand.get("output_file"):
                    start_text = read_text(REPO_ROOT / cand["output_file"])
            if not start_text:
                for cand in page_rec.get("candidates", []):
                    if cand.get("output_file") and cand.get("available"):
                        start_text = read_text(REPO_ROOT / cand["output_file"])
                        if start_text:
                            break

        print(f"  Image: {image_path.name}")
        if args.mode == "repair":
            print(f"  Starting draft: {len(start_text)} chars")

        try:
            cleaned_text = clean_page(client, args, image_path, start_text)
            out_file = pages_dir / f"page-{idx:03d}.{cand_name}.txt"
            write_text(out_file, cleaned_text)
            print(f"  Cleaned text saved: {out_file.name} ({len(cleaned_text)} chars)")
            register_candidate(page_rec, cand_name, out_file, cleaned_text)
        except Exception as e:
            print(f"  ERROR cleaning page {idx}: {e}")

    with open(ledger_path, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2, ensure_ascii=False)
        f.write("\n")

    reassemble_draft(ledger, work_dir)


if __name__ == "__main__":
    main()
