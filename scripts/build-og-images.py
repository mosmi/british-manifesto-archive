#!/usr/bin/env python3
"""
build-og-images.py

Generates branded 1200×630 Open Graph / Twitter share cards for every route
that exposes og:image, written to /og/… (and og-image.jpg for the homepage).

Uses the HTML renderer in tools/og-generator/og.html (Puppeteer) with specs
built from site data by tools/og-generator/build-manifest.mjs. Run
build-seo-data.py first.

Usage:
  python3 scripts/build-og-images.py                 # all cards
  python3 scripts/build-og-images.py --only manifesto # one type
  python3 scripts/build-og-images.py --sample         # a handful, for preview
  python3 scripts/build-og-images.py --force          # ignore hash cache

Requires: Node.js, npm install (puppeteer).
"""

import argparse
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GENERATOR = ROOT / "tools" / "og-generator"
MANIFEST = GENERATOR / "pages.json"
NODE_MODULES = ROOT / "node_modules"


def node_install_hint() -> str:
    return (
        "Node.js is required for the OG image pipeline (Puppeteer).\n\n"
        "Install on macOS (pick one):\n"
        "  brew install node              # Homebrew (recommended if you have brew)\n"
        "  https://nodejs.org/en/download # official installer\n\n"
        "Then from the repo root:\n"
        "  npm install\n"
        "  python3 scripts/build-og-images.py --sample"
    )


def ensure_deps() -> None:
    if shutil.which("node") is None:
        print(f"ERROR: node not found.\n\n{node_install_hint()}", file=sys.stderr)
        sys.exit(1)
    if not (NODE_MODULES / "puppeteer").is_dir():
        npm = shutil.which("npm")
        if npm is None:
            print(
                f"ERROR: npm not found (node is installed but npm is missing).\n\n"
                f"{node_install_hint()}",
                file=sys.stderr,
            )
            sys.exit(1)
        print("Installing puppeteer (npm install)…")
        subprocess.run([npm, "install"], cwd=ROOT, check=True)
    ensure_puppeteer_browser()


def chrome_framework_path(extract_dir: Path) -> Path | None:
    matches = list(extract_dir.glob(
        "chrome-mac-arm64/Google Chrome for Testing.app/Contents/Frameworks/"
        "Google Chrome for Testing Framework.framework/Versions/*/"
        "Google Chrome for Testing Framework"
    ))
    return matches[0] if matches and matches[0].is_file() else None


def repair_chrome_cache(cache: Path) -> bool:
    """Extract Puppeteer Chrome zips when npm blocked the postinstall script."""
    ok = False
    for zip_path in sorted(cache.glob("*-chrome-mac-arm64.zip")):
        version = zip_path.name.removesuffix("-chrome-mac-arm64.zip")
        extract_dir = cache / f"mac_arm-{version}"
        if chrome_framework_path(extract_dir):
            ok = True
            continue
        print(f"Extracting Puppeteer Chrome from {zip_path.name}…")
        extract_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(extract_dir)
        if chrome_framework_path(extract_dir):
            ok = True
    return ok


def ensure_puppeteer_browser() -> None:
    """Download and extract the headless Chrome Puppeteer needs."""
    install_mjs = NODE_MODULES / "puppeteer" / "install.mjs"
    if install_mjs.is_file():
        print("Ensuring Puppeteer browser (install.mjs)…")
        subprocess.run(["node", str(install_mjs)], cwd=ROOT, check=False)

    npx = shutil.which("npx")
    if npx:
        subprocess.run(
            [npx, "puppeteer", "browsers", "install", "chrome"],
            cwd=ROOT,
            check=False,
        )

    cache = Path.home() / ".cache" / "puppeteer" / "chrome"
    if cache.is_dir() and repair_chrome_cache(cache):
        return

    mac_chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    if sys.platform == "darwin" and mac_chrome.is_file():
        print("Warning: bundled Puppeteer Chrome unavailable; will try system Google Chrome.")
        return

    print(
        "ERROR: Puppeteer Chrome is missing or incomplete.\n\n"
        "npm may have blocked Puppeteer's install script. Try:\n"
        "  npm approve-scripts          # allow puppeteer → install.mjs\n"
        "  npm install\n"
        "  npx puppeteer browsers install chrome\n\n"
        "Or install Google Chrome and rerun — the renderer will fall back to it.\n"
        "  brew install --cask google-chrome",
        file=sys.stderr,
    )
    sys.exit(1)


def run_node(script: str, *args: str) -> None:
    subprocess.run(["node", str(GENERATOR / script), *args], cwd=ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--only",
        help="comma-separated: home,hub,election,party,manifesto,nation,devolved",
    )
    parser.add_argument(
        "--sample", action="store_true",
        help="render a small representative sample only",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="re-render all cards, ignoring the hash cache",
    )
    args = parser.parse_args()

    seo = ROOT / "data" / "seo.json"
    if not seo.is_file():
        print("ERROR: data/seo.json not found — run python3 scripts/build-seo-data.py first",
              file=sys.stderr)
        sys.exit(1)

    ensure_deps()

    subprocess.run(["node", str(ROOT / "scripts" / "build-party-colours.mjs")], cwd=ROOT, check=True)

    manifest_args = ["--out", str(MANIFEST)]
    if args.only:
        manifest_args.extend(["--only", args.only])
    if args.sample:
        manifest_args.append("--sample")

    run_node("build-manifest.mjs", *manifest_args)

    render_args = [str(MANIFEST), str(ROOT)]
    if args.force:
        render_args.append("--force")

    run_node("generate-og.mjs", *render_args)

    count = len(__import__("json").loads(MANIFEST.read_text(encoding="utf-8")))
    print(f"OG pipeline complete — {count} cards → {ROOT / 'og'}/")


if __name__ == "__main__":
    main()
