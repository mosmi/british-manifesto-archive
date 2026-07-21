#!/usr/bin/env python3
"""
serve_viewer.py — Lightweight HTTP server for the Manifesto Side-by-Side QA Reader.

Usage:
    python3 serve_viewer.py
    python3 serve_viewer.py --port 8500
"""
import argparse
import json
import mimetypes
import os
import subprocess
import sys
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

TOOLKIT_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLKIT_DIR.parents[1]
WORK_DIR = TOOLKIT_DIR / "work"
VIEWER_DIR = TOOLKIT_DIR / "viewer"

class QAViewerHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress routine GET logging unless error
        if " 40" in format % args or " 50" in format % args:
            super().log_message(format, *args)

    def send_json(self, data, status=200):
        body = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message, status=400):
        self.send_json({"error": message}, status=status)

    def serve_file(self, file_path: Path):
        if not file_path.exists() or not file_path.is_file():
            self.send_error(404, "File Not Found")
            return
        
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = "application/octet-stream"
        
        content = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        # API Routes
        if path == "/api/manifestos":
            self.handle_list_manifestos()
            return
        elif path.startswith("/api/manifesto/"):
            parts = path.split("/")[3:] # ['<slug>', ...]
            if len(parts) == 1:
                self.handle_get_manifesto(parts[0])
                return
            elif len(parts) == 3 and parts[1] == "page":
                try:
                    page_index = int(parts[2])
                    self.handle_get_page(parts[0], page_index)
                    return
                except ValueError:
                    pass

        # Static file routing for work/ directory (images, text files)
        if path.startswith("/work/"):
            rel_path = path[6:]
            target = WORK_DIR / rel_path
            self.serve_file(target)
            return

        # Static file routing for viewer UI (index.html, styles.css, app.js)
        if path.startswith("/viewer/"):
            rel_name = path[8:]
            target = VIEWER_DIR / rel_name if rel_name else (VIEWER_DIR / "index.html")
        elif not path or path == "/index.html":
            target = VIEWER_DIR / "index.html"
        else:
            target = VIEWER_DIR / path.lstrip("/")

        self.serve_file(target)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        content_len = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_len) if content_len > 0 else b""
        payload = {}
        if post_data:
            try:
                payload = json.loads(post_data.decode("utf-8"))
            except Exception as e:
                self.send_error_json(f"Invalid JSON payload: {e}")
                return

        if path.startswith("/api/manifesto/"):
            parts = path.split("/")[3:] # ['<slug>', ...]
            if len(parts) == 4 and parts[1] == "page" and parts[3] == "save":
                try:
                    page_index = int(parts[2])
                    self.handle_save_page(parts[0], page_index, payload)
                    return
                except ValueError:
                    pass
            elif len(parts) == 4 and parts[1] == "page" and parts[3] == "accept":
                try:
                    page_index = int(parts[2])
                    self.handle_accept_flag(parts[0], page_index)
                    return
                except ValueError:
                    pass

        self.send_error_json("Endpoint not found", 404)

    def handle_list_manifestos(self):
        manifestos = []
        for d in sorted(WORK_DIR.glob("manifestos__*")):
            if not d.is_dir():
                continue
            ledger_path = d / "ledger.json"
            flagged_path = d / "flagged_pages.json"
            
            if not ledger_path.exists():
                continue

            try:
                ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            except Exception:
                continue

            pages_count = len(ledger.get("pages", []))
            reviewed_count = sum(1 for p in ledger.get("pages", []) if p.get("status") == "reviewed")
            needs_review_count = sum(1 for p in ledger.get("pages", []) if p.get("status") == "needs-review")
            
            flagged_count = 0
            flagged_indices = []
            if flagged_path.exists():
                try:
                    flagged_data = json.loads(flagged_path.read_text(encoding="utf-8"))
                    flagged_count = flagged_data.get("flagged_count", 0)
                    flagged_indices = [item["page_index"] for item in flagged_data.get("flagged", [])]
                except Exception:
                    pass

            manifestos.append({
                "slug": d.name,
                "display_name": d.name.replace("manifestos__", "").replace("__", " / "),
                "total_pages": pages_count,
                "reviewed_count": reviewed_count,
                "needs_review_count": needs_review_count,
                "flagged_count": flagged_count,
                "flagged_indices": flagged_indices,
            })

        self.send_json({"manifestos": manifestos})

    def handle_get_manifesto(self, slug: str):
        manifesto_dir = WORK_DIR / slug
        ledger_path = manifesto_dir / "ledger.json"
        flagged_path = manifesto_dir / "flagged_pages.json"

        if not ledger_path.exists():
            self.send_error_json(f"Manifesto ledger not found for slug: {slug}", 404)
            return

        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        flagged_data = {}
        if flagged_path.exists():
            flagged_data = json.loads(flagged_path.read_text(encoding="utf-8"))

        pages_summary = []
        for p in ledger.get("pages", []):
            idx = p.get("page_index")
            pages_summary.append({
                "page_index": idx,
                "status": p.get("status"),
                "selected_candidate": p.get("selected_candidate"),
                "issues": p.get("issues", []),
                "vision_audit": p.get("vision_audit"),
            })

        self.send_json({
            "slug": slug,
            "display_name": slug.replace("manifestos__", "").replace("__", " / "),
            "total_pages": len(pages_summary),
            "flagged_pages": flagged_data.get("flagged", []),
            "pages": pages_summary,
        })

    def find_image_url(self, manifesto_dir: Path, page_index: int) -> str:
        images_dir = manifesto_dir / "images"
        if not images_dir.exists():
            return ""

        candidates = [
            f"page-{page_index + 1:03d}.png",
            f"page-{page_index + 1:02d}.png",
            f"page-{page_index + 1}.png",
            f"page-{page_index:03d}.png",
        ]
        for name in candidates:
            if (images_dir / name).exists():
                return f"/work/{manifesto_dir.name}/images/{name}"
        return ""

    def handle_get_page(self, slug: str, page_index: int):
        manifesto_dir = WORK_DIR / slug
        ledger_path = manifesto_dir / "ledger.json"

        if not ledger_path.exists():
            self.send_error_json(f"Manifesto ledger not found for slug: {slug}", 404)
            return

        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        pages = ledger.get("pages", [])
        if page_index < 0 or page_index >= len(pages):
            self.send_error_json(f"Page index {page_index} out of bounds (0..{len(pages)-1})", 404)
            return

        p_rec = pages[page_index]
        selected = p_rec.get("selected_candidate")
        
        # Read text content for selected candidate
        selected_text = ""
        cand_info = next((c for c in p_rec.get("candidates", []) if c.get("method") == selected), None)
        if cand_info and cand_info.get("output_file"):
            out_path = REPO_ROOT / cand_info["output_file"]
            if not out_path.exists():
                out_path = manifesto_dir / "pages" / Path(cand_info["output_file"]).name
            if out_path.exists():
                selected_text = out_path.read_text(encoding="utf-8")

        # Read baseline pdftotext content if available
        baseline_text = ""
        pdf_cand = next((c for c in p_rec.get("candidates", []) if c.get("method") in {"pdftotext", "pdftotext-layout"}), None)
        if pdf_cand and pdf_cand.get("output_file"):
            b_path = REPO_ROOT / pdf_cand["output_file"]
            if not b_path.exists():
                b_path = manifesto_dir / "pages" / Path(pdf_cand["output_file"]).name
            if b_path.exists():
                baseline_text = b_path.read_text(encoding="utf-8")

        image_url = self.find_image_url(manifesto_dir, page_index)

        self.send_json({
            "slug": slug,
            "page_index": page_index,
            "total_pages": len(pages),
            "status": p_rec.get("status"),
            "selected_candidate": selected,
            "selected_text": selected_text,
            "baseline_text": baseline_text,
            "image_url": image_url,
            "issues": p_rec.get("issues", []),
            "vision_audit": p_rec.get("vision_audit"),
            "candidates": p_rec.get("candidates", []),
        })

    def handle_save_page(self, slug: str, page_index: int, payload: dict):
        manifesto_dir = WORK_DIR / slug
        ledger_path = manifesto_dir / "ledger.json"

        if not ledger_path.exists():
            self.send_error_json(f"Ledger not found for slug: {slug}", 404)
            return

        content = payload.get("content", "").strip() + "\n"
        mark_reviewed = payload.get("mark_reviewed", True)

        # Write text file
        claude_rel = f"tools/transcription-toolkit/work/{slug}/pages/page-{page_index:03d}.claude-clean.txt"
        claude_file = manifesto_dir / "pages" / f"page-{page_index:03d}.claude-clean.txt"
        claude_file.parent.mkdir(parents=True, exist_ok=True)
        claude_file.write_text(content, encoding="utf-8")

        # Update ledger
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        p_rec = ledger["pages"][page_index]
        
        # Replace or add claude-clean candidate
        cands = [c for c in p_rec.get("candidates", []) if c.get("method") != "claude-clean"]
        wc = len(content.split())
        cands.append({
            "method": "claude-clean",
            "available": True,
            "word_count": wc,
            "artifact_score": 0.0,
            "output_file": claude_rel,
            "error": None
        })
        p_rec["candidates"] = cands
        p_rec["selected_candidate"] = "claude-clean"
        p_rec["vision_audit"] = {
            "audited_at": datetime.now(timezone.utc).isoformat(),
            "method": "human-editor",
            "checked_candidate": "claude-clean",
            "discrepancies": []
        }
        if mark_reviewed:
            p_rec["status"] = "reviewed"
            p_rec["issues"] = []

        ledger_path.write_text(json.dumps(ledger, indent=2, ensure_ascii=False), encoding="utf-8")

        # Reassemble draft.md & re-run flag_pages.py
        try:
            subprocess.run([sys.executable, str(TOOLKIT_DIR / "repair_manifestos_gemini.py"), str(ledger_path), "--reassemble-only"], check=True, capture_output=True)
            subprocess.run([sys.executable, str(TOOLKIT_DIR / "flag_pages.py"), str(ledger_path)], check=True, capture_output=True)
        except Exception as e:
            print(f"WARNING: reassemble/re-gate post-save error: {e}", file=sys.stderr)

        self.send_json({"success": True, "message": "Saved page, reassembled draft, and refreshed gate."})

    def handle_accept_flag(self, slug: str, page_index: int):
        manifesto_dir = WORK_DIR / slug
        ledger_path = manifesto_dir / "ledger.json"

        if not ledger_path.exists():
            self.send_error_json(f"Ledger not found for slug: {slug}", 404)
            return

        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        p_rec = ledger["pages"][page_index]
        sel = p_rec.get("selected_candidate", "vlm-clean")
        
        p_rec["vision_audit"] = {
            "audited_at": datetime.now(timezone.utc).isoformat(),
            "method": "human-accepted",
            "checked_candidate": sel,
            "discrepancies": []
        }
        p_rec["status"] = "reviewed"
        p_rec["issues"] = []

        ledger_path.write_text(json.dumps(ledger, indent=2, ensure_ascii=False), encoding="utf-8")

        try:
            subprocess.run([sys.executable, str(TOOLKIT_DIR / "flag_pages.py"), str(ledger_path)], check=True, capture_output=True)
        except Exception as e:
            print(f"WARNING: re-gate error: {e}", file=sys.stderr)

        self.send_json({"success": True, "message": "Accepted flag as reviewed."})


def main():
    parser = argparse.ArgumentParser(description="Serve Manifesto QA Viewer local HTTP server.")
    parser.add_argument("--port", type=int, default=8500, help="Port to listen on (default 8500)")
    args = parser.parse_args()

    server = HTTPServer(("0.0.0.0", args.port), QAViewerHandler)
    print(f"\n========================================================")
    print(f" Manifesto QA Reader & Editor is live at:")
    print(f"   http://localhost:{args.port}")
    print(f"========================================================\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        server.server_close()

if __name__ == "__main__":
    main()
