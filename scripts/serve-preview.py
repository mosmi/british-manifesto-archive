#!/usr/bin/env python3
"""SPA-aware local preview for the British Manifesto Archive.

Serves the repo root on http://127.0.0.1:8888/ by default. Extensionless client
routes fall back to index.html (same idea as Cloudflare `_redirects` 200 rules
and `not_found_handling = "single-page-application"`). Real files — including
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

# Exact paths from `_redirects` (200 → index.html), plus trailing-slash variants.
EXACT = {
    "/elections",
    "/elections/",
    "/parties",
    "/parties/all",
    "/devolved",
    "/nations",
    "/others",
    "/about",
}

# Prefix patterns from `_redirects`.
PREFIXES = (
    "/election/",
    "/manifesto/",
    "/party/",
    "/nation/",
    "/devolved/",
)


class SpaHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        raw = self.path
        path = raw.split("?", 1)[0]
        qs = raw[len(path) :]

        local = (ROOT / path.lstrip("/")).resolve()
        try:
            local.relative_to(ROOT)
        except ValueError:
            self.send_error(403)
            return

        if path == "/" or local.is_file() or (
            local.is_dir() and (local / "index.html").is_file()
        ):
            return super().do_GET()

        bare = path.rstrip("/") or "/"
        if path in EXACT or bare in EXACT or any(path.startswith(p) for p in PREFIXES):
            self.path = "/index.html" + qs
            return super().do_GET()

        # Other extensionless paths → SPA shell (client renders 404).
        if not re.search(r"\.[a-z0-9]{2,8}$", path, re.I):
            self.path = "/index.html" + qs
            return super().do_GET()

        return super().do_GET()

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
