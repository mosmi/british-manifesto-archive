#!/usr/bin/env python3
"""SPA-aware local preview for the British Manifesto Archive.

Serves the repo root on http://127.0.0.1:8888/ by default. Applies `_redirects`
301s then 200 SPA rewrites (same order as Cloudflare). Real files — including
PDFs under /manifestos/ — are served as-is; missing files with extensions stay 404.

Usage:
    python3 scripts/serve-preview.py
    python3 scripts/serve-preview.py --port 8890
"""

from __future__ import annotations

import argparse
import re
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def parse_redirects(text: str) -> list[tuple[re.Pattern[str], str, int]]:
    """Parse Cloudflare `_redirects` (first match wins). `*` → splat."""
    rules: list[tuple[re.Pattern[str], str, int]] = []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        src, dest, status_s = parts[0], parts[1], parts[2]
        try:
            status = int(status_s)
        except ValueError:
            continue
        if "*" in src:
            prefix = src.split("*", 1)[0]
            regex = re.compile("^" + re.escape(prefix) + "(.*)$")
        else:
            regex = re.compile("^" + re.escape(src) + "$")
        rules.append((regex, dest, status))
    return rules


REDIRECT_RULES = parse_redirects((ROOT / "_redirects").read_text(encoding="utf-8"))


def apply_redirects(path: str) -> tuple[int, str] | None:
    for regex, dest, status in REDIRECT_RULES:
        m = regex.match(path)
        if not m:
            continue
        target = dest.replace(":splat", m.group(1) if m.lastindex else "")
        return status, target
    return None


class SpaHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def _apply_path(self):
        """Rewrite self.path for SPA 200s, or return a redirect/error tuple."""
        raw = self.path
        path = raw.split("?", 1)[0]
        qs = raw[len(path) :]

        hit = apply_redirects(path)
        if hit and hit[0] in (301, 302, 303, 307, 308):
            return hit[0], hit[1] + qs

        local = (ROOT / path.lstrip("/")).resolve()
        try:
            local.relative_to(ROOT)
        except ValueError:
            return 403, None

        if path == "/" or local.is_file() or (
            local.is_dir() and (local / "index.html").is_file()
        ):
            return None, None

        if (hit and hit[0] == 200) or not re.search(r"\.[a-z0-9]{2,8}$", path, re.I):
            self.path = "/index.html" + qs
        return None, None

    def do_GET(self):
        status, dest = self._apply_path()
        if status in (301, 302, 303, 307, 308) and dest:
            self.send_response(status)
            self.send_header("Location", dest)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if status == 403:
            self.send_error(403)
            return
        return super().do_GET()

    def do_HEAD(self):
        status, dest = self._apply_path()
        if status in (301, 302, 303, 307, 308) and dest:
            self.send_response(status)
            self.send_header("Location", dest)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if status == 403:
            self.send_error(403)
            return
        return super().do_HEAD()

    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8888)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), SpaHandler)
    print(
        f"Serving SPA preview at http://{args.host}:{args.port}/  (root={ROOT})",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.", flush=True)


if __name__ == "__main__":
    main()
