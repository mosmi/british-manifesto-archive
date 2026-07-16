#!/usr/bin/env python3
"""
qa_audit_vision.py - Layer B vision-model audit (classify, never transcribe).

Sends each requested page's rendered image, alongside the ledger's selected
candidate text for that page, to a Claude vision model with a prompt
constrained to structural classification. The model is asked to return a
short list of discrepancy types (missing_block, column_join_error,
style_mismatch, spurious_text, ordering_error) with locators - never
corrected or rewritten text. See TRANSCRIPTION_PIPELINE.md Sec.4 Layer B for
the design rationale: deterministic checks (qa_check.py, Layer A) run on
everything; this is reserved for pages Layer A/the ledger already flagged,
or an explicit page list, since it costs real API calls.

IMPORTANT: this audits the ledger's *selected candidate file* for each page
(pages/page-NNN.<method>.txt), not the current manifesto.md/draft.md. If
draft.md was hand-edited since the ledger was built, this script won't see
those edits - re-run 'transcribe_pipeline.py new/audit' to refresh the
ledger first, or accept that a page's report may be stale relative to the
current draft.

Usage:
    python qa_audit_vision.py work/<slug>/ledger.json --pages 0,3,5-10
    python qa_audit_vision.py work/<slug>/ledger.json --from-checklist
    python qa_audit_vision.py work/<slug>/ledger.json --pages 0-2 --dry-run
    python qa_audit_vision.py work/<slug>/ledger.json --from-checklist --model claude-haiku-4-5

Reruns MERGE into the existing vision_audit_report.json by page index -
auditing a subset of pages again updates just those entries and leaves the
rest of a prior full run intact.

Requires ANTHROPIC_API_KEY in the environment for real runs. --dry-run
builds and prints the request for each page without calling the API, so the
page/image/text resolution logic can be checked without credentials.
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import sys
from pathlib import Path
from typing import Any

TOOLKIT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLKIT_DIR))

from transcribe_pipeline import (  # type: ignore  # noqa: E402
    REPO_ROOT,
    now_iso,
    read_text,
    rel,
    write_json,
)

DISCREPANCY_TYPES = [
    "missing_block",
    "column_join_error",
    "style_mismatch",
    "spurious_text",
    "ordering_error",
]

DEFAULT_MODEL = "claude-sonnet-5"
DEFAULT_MAX_TOKENS = 2048
RETRY_MAX_TOKENS = 4096
DEFAULT_MAX_IMAGE_DIM = 1568  # long edge, px; Claude's own useful-detail ceiling for most vision tasks

# USD per 1M tokens. Classification only needs to be roughly right for
# cost estimates, not billing-accurate - update if pricing changes.
PRICING_PER_MTOK = {
    "claude-opus-4-8": {"input": 5.00, "output": 25.00},
    "claude-sonnet-5": {"input": 3.00, "output": 15.00},
    "claude-haiku-4-5": {"input": 1.00, "output": 5.00},
}

PROMPT_TEMPLATE = """You are auditing a machine-generated Markdown transcription of one scanned \
manifesto page against a photo of the original page.

Your job is to CLASSIFY structural discrepancies between the image and the \
Markdown below. You are not a transcriber: never rewrite, correct, or \
reproduce the page's text yourself, even partially, even to illustrate a \
point. Quote at most a few words at a time, only as a locator.

Compare the image to this Markdown chunk:
---
{markdown_chunk}
---

For each discrepancy you find, classify it as exactly one of:
- missing_block: text visible in the image that is entirely absent from the Markdown
- column_join_error: two columns/blocks were merged in the wrong reading order
- style_mismatch: heading level, bold/italic, or list formatting doesn't match the image
- spurious_text: the Markdown contains text that isn't in the image at all
- ordering_error: content is present but appears in the wrong order

Respond with ONLY a JSON array (no markdown fences, no other text). Each \
element: {{"type": one of the five types above, "locator": a short quote \
(<=8 words) or plain-English location description, "note": one sentence}}. \
If there are no discrepancies, respond with exactly: []
"""


def parse_page_spec(spec: str) -> list[int]:
    indices: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            indices.extend(range(int(a), int(b) + 1))
        else:
            indices.append(int(part))
    return sorted(set(indices))


def load_ledger(ledger_path: Path) -> dict[str, Any]:
    return json.loads(read_text(ledger_path))


def resolve_page(ledger: dict[str, Any], page_index: int) -> dict[str, Any] | None:
    for p in ledger.get("pages", []):
        if p["page_index"] == page_index:
            return p
    return None


def candidate_text_for(page: dict[str, Any]) -> tuple[str, str]:
    """Return (markdown_chunk, source_label) for a page's selected candidate."""
    selected = page.get("selected_candidate")
    if not selected:
        return "[No text was extracted for this page - the ledger has no selected candidate.]", "none"
    for c in page.get("candidates", []):
        if c.get("method") == selected and c.get("output_file"):
            candidate_path = REPO_ROOT / c["output_file"]
            if candidate_path.exists():
                return read_text(candidate_path).strip(), f"candidate:{selected}"
    return "[Selected candidate text file could not be located.]", f"candidate:{selected} (missing file)"


def load_image_bytes(image_path: Path, max_dim: int | None) -> tuple[bytes, str]:
    """Read an image, optionally downsampling to cut vision-token cost. Returns (bytes, media_type)."""
    raw = image_path.read_bytes()
    media_type = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"
    if not max_dim:
        return raw, media_type
    try:
        from PIL import Image
    except ImportError:
        return raw, media_type
    with Image.open(io.BytesIO(raw)) as img:
        if max(img.size) <= max_dim:
            return raw, media_type
        scale = max_dim / max(img.size)
        new_size = (round(img.size[0] * scale), round(img.size[1] * scale))
        resized = img.convert("RGB").resize(new_size, Image.LANCZOS)
        buf = io.BytesIO()
        resized.save(buf, format="JPEG", quality=85)
        return buf.getvalue(), "image/jpeg"


def build_request(ledger: dict[str, Any], page_index: int, max_image_dim: int | None) -> dict[str, Any] | None:
    page = resolve_page(ledger, page_index)
    if page is None:
        return None
    image_rel = page.get("image_path")
    if not image_rel:
        return None
    image_path = REPO_ROOT / image_rel
    if not image_path.exists():
        return None
    markdown_chunk, source_label = candidate_text_for(page)
    prompt = PROMPT_TEMPLATE.format(markdown_chunk=markdown_chunk or "[empty]")
    return {
        "page_index": page_index,
        "image_path": image_path,
        "markdown_chunk": markdown_chunk,
        "source_label": source_label,
        "prompt": prompt,
        "max_image_dim": max_image_dim,
    }


def estimate_cost(model: str, usage: dict[str, int]) -> float:
    pricing = PRICING_PER_MTOK.get(model)
    if not pricing:
        return 0.0
    return (
        usage.get("input_tokens", 0) * pricing["input"]
        + usage.get("output_tokens", 0) * pricing["output"]
    ) / 1_000_000


def call_claude_once(request: dict[str, Any], model: str, client: Any, max_tokens: int) -> tuple[str, dict[str, int]]:
    image_bytes, media_type = load_image_bytes(request["image_path"], request["max_image_dim"])
    b64 = base64.standard_b64encode(image_bytes).decode("ascii")

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
                {"type": "text", "text": request["prompt"]},
            ],
        }],
    )
    text = "".join(block.text for block in response.content if getattr(block, "type", None) == "text").strip()
    usage = {
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }
    return text, usage


def parse_findings(text: str) -> list[dict[str, Any]] | None:
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        findings = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(findings, list):
        return None
    for f in findings:
        if f.get("type") not in DISCREPANCY_TYPES:
            f["type"] = f.get("type") or "unknown"
    return findings


def call_claude(request: dict[str, Any], model: str, client: Any) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Call the model, retrying once with a larger max_tokens if the response wasn't valid JSON
    (usually means it got cut off mid-object). Returns (findings, cumulative_usage)."""
    text, usage = call_claude_once(request, model, client, DEFAULT_MAX_TOKENS)
    findings = parse_findings(text)
    if findings is not None:
        return findings, usage

    retry_text, retry_usage = call_claude_once(request, model, client, RETRY_MAX_TOKENS)
    usage = {k: usage[k] + retry_usage[k] for k in usage}
    findings = parse_findings(retry_text)
    if findings is not None:
        return findings, usage

    return [{
        "type": "audit_error",
        "locator": None,
        "note": f"Model response was not valid JSON after retry with max_tokens={RETRY_MAX_TOKENS}: {retry_text[:200]!r}",
    }], usage


def render_report_markdown(ledger_path: Path, results: list[dict[str, Any]], total_cost: float) -> str:
    lines = [
        "# Vision audit report (Layer B)",
        "",
        f"Source ledger: `{rel(ledger_path)}`",
        f"Generated: {now_iso()}",
        "",
        "Classification only - the model was never asked to transcribe or",
        "correct text, only to flag structural discrepancies against the",
        "page image. Verify findings against the image before acting on them.",
        "",
        "Each page is audited against the ledger's *selected candidate file*,",
        "not the current draft.md/manifesto.md - if a page was hand-edited",
        "since the ledger was built, this report may be stale for it. The",
        "`source` field on each page result below names the exact candidate",
        "file that was actually compared against the image.",
        "",
    ]
    total_findings = sum(len(r["findings"]) for r in results)
    lines.append(
        f"Pages audited: {len(results)}  |  Total findings: {total_findings}  |  "
        f"Cumulative cost: ${total_cost:.4f}"
    )
    lines.append("")
    for r in sorted(results, key=lambda x: x["page_index"]):
        lines.append(f"## Page {r['page_index']} ({r.get('model', '?')}, source: {r.get('source', '?')})")
        if not r["findings"]:
            lines.append("")
            lines.append("No discrepancies flagged.")
            lines.append("")
            continue
        for f in r["findings"]:
            locator = f.get("locator") or ""
            note = f.get("note") or ""
            lines.append(f"- **{f.get('type', 'unknown')}** — {locator} — {note}")
        lines.append("")
    return "\n".join(lines)


def load_existing_report(report_json_path: Path) -> dict[int, dict[str, Any]]:
    """Load a prior report (if any) as {page_index: result}, so reruns merge instead of clobbering."""
    if not report_json_path.exists():
        return {}
    try:
        data = json.loads(read_text(report_json_path))
    except Exception:
        return {}
    return {r["page_index"]: r for r in data.get("results", [])}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ledger", help="Path to a ledger.json produced by transcribe_pipeline.py new/audit.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pages", help="Comma/range page spec, 0-indexed, e.g. 0,5-10,20.")
    group.add_argument("--from-checklist", action="store_true", help="Audit exactly the pages listed in the sibling checklist.json (run 'transcribe_pipeline.py checklist' first).")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Claude model to use (default: {DEFAULT_MODEL}). claude-haiku-4-5 is ~3x cheaper for this classification-only task.")
    parser.add_argument("--max-image-dim", type=int, default=DEFAULT_MAX_IMAGE_DIM, help=f"Downsample page images so the long edge is at most this many pixels before sending, to cut vision-token cost (default {DEFAULT_MAX_IMAGE_DIM}; pass 0 to disable and send full-resolution images).")
    parser.add_argument("--max-pages", type=int, default=25, help="Refuse to run against more pages than this without --force (default 25, since each page is a real API call).")
    parser.add_argument("--force", action="store_true", help="Bypass --max-pages.")
    parser.add_argument("--dry-run", action="store_true", help="Build requests and print them without calling the API.")
    args = parser.parse_args()

    ledger_path = Path(args.ledger).resolve()
    ledger = load_ledger(ledger_path)
    max_image_dim = args.max_image_dim or None

    if args.from_checklist:
        checklist_path = ledger_path.with_name("checklist.json")
        if not checklist_path.exists():
            print(f"ERROR: no checklist.json next to {ledger_path}; run 'transcribe_pipeline.py checklist' first.", file=sys.stderr)
            return 2
        checklist = json.loads(read_text(checklist_path))
        page_indices = [e["page_index"] for e in checklist["entries"]]
    else:
        page_indices = parse_page_spec(args.pages)

    if len(page_indices) > args.max_pages and not args.force:
        print(
            f"ERROR: {len(page_indices)} pages requested, exceeds --max-pages {args.max_pages} "
            f"(each page is a real, billed API call). Pass --force to proceed anyway.",
            file=sys.stderr,
        )
        return 2

    requests = []
    for idx in page_indices:
        req = build_request(ledger, idx, max_image_dim)
        if req is None:
            print(f"WARNING: page {idx} not found in ledger or has no image; skipping.", file=sys.stderr)
            continue
        requests.append(req)

    if args.dry_run:
        for req in requests:
            print(f"--- page {req['page_index']} ({req['source_label']}) ---")
            print(f"image: {req['image_path']}")
            print(f"markdown_chunk ({len(req['markdown_chunk'])} chars): {req['markdown_chunk'][:200]!r}")
            print()
        print(f"[dry-run] {len(requests)} page(s) would be sent to {args.model}. No API calls made.")
        return 0

    try:
        import anthropic  # type: ignore
    except ImportError:
        print("ERROR: the 'anthropic' package is not installed. pip install anthropic --break-system-packages", file=sys.stderr)
        return 2

    try:
        client = anthropic.Anthropic()
    except Exception as e:
        print(f"ERROR: could not create Anthropic client (is ANTHROPIC_API_KEY set?): {e}", file=sys.stderr)
        return 2

    report_json_path = ledger_path.with_name("vision_audit_report.json")
    report_md_path = ledger_path.with_name("vision_audit_report.md")
    merged = load_existing_report(report_json_path)

    run_cost = 0.0
    for req in requests:
        print(f"Auditing page {req['page_index']} ({req['source_label']})...", file=sys.stderr)
        try:
            findings, usage = call_claude(req, args.model, client)
        except Exception as e:
            findings, usage = [{"type": "audit_error", "locator": None, "note": f"API call failed: {e}"}], {"input_tokens": 0, "output_tokens": 0}
        page_cost = estimate_cost(args.model, usage)
        run_cost += page_cost
        print(f"  {len(findings)} finding(s), ~${page_cost:.4f}", file=sys.stderr)
        merged[req["page_index"]] = {
            "page_index": req["page_index"],
            "source": req["source_label"],
            "model": args.model,
            "usage": usage,
            "estimated_cost_usd": round(page_cost, 6),
            "findings": findings,
        }

    results = sorted(merged.values(), key=lambda r: r["page_index"])
    total_cost = sum(r.get("estimated_cost_usd", 0.0) for r in results)

    report_json = {
        "schema_version": 2,
        "mode": "vision-audit",
        "created_at": now_iso(),
        "source_ledger": rel(ledger_path),
        "pages_audited": len(results),
        "total_findings": sum(len(r["findings"]) for r in results),
        "total_estimated_cost_usd": round(total_cost, 4),
        "results": results,
    }
    write_json(report_json_path, report_json)
    report_md_path.write_text(render_report_markdown(ledger_path, results, total_cost), encoding="utf-8")

    print(json.dumps({
        "mode": "vision-audit",
        "pages_audited_this_run": len(requests),
        "pages_in_report": len(results),
        "total_findings": report_json["total_findings"],
        "this_run_cost_usd": round(run_cost, 4),
        "report_total_cost_usd": round(total_cost, 4),
        "report_json": rel(report_json_path),
        "report_md": rel(report_md_path),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
