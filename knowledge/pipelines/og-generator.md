---
type: pipeline
title: OG image generator
description: How 1200×630 Open Graph / Twitter cards are built from site data via Puppeteer.
tags: [pipeline, og, seo, social]
timestamp: 2026-07-05T00:00:00Z
---

# OG image generator

Generates branded **1200×630** social/meta images for every route that exposes
`og:image`, written to `/og/…` plus `og-image.jpg` for the homepage.

**Project home:** `tools/og-generator/`

## Regenerating all OG images (runbook)

Use this whenever party/election/manifesto content changes, or after editing
`tools/og-generator/og.html` or `build-manifest.mjs`.

### Prerequisites (first time only)

1. **Node.js 18+** — `brew install node` if `node` / `npm` are not found.
2. From the repo root:
   ```bash
   npm install
   ```
3. If npm warns that it blocked Puppeteer's install script, run `npm approve-scripts`,
   approve **puppeteer**, then `npm install` again. If bundled Chrome still fails to
   launch, install Google Chrome — the renderer falls back to it automatically.

### Full regeneration (~395 cards)

Run commands **one per line** (do not paste inline `#` comments — zsh treats `~` and
`#` specially).

```bash
cd ~/Cursor/british-manifesto-archive

python3 scripts/build-seo-data.py      # refresh data/seo.json first if content changed
python3 scripts/build-og-images.py     # writes og/**.jpg + og-image.jpg
```

Takes a few minutes. Incremental runs skip unchanged cards via `og/.og-hashes.json`.
To re-render everything regardless of cache:

```bash
python3 scripts/build-og-images.py --force
```

### Partial rebuilds

```bash
python3 scripts/build-og-images.py --sample              # ~24 cards, for a quick eyeball
python3 scripts/build-og-images.py --only hub --force     # hub pages only (about, elections, …)
python3 scripts/build-og-images.py --only party           # party cards only
python3 scripts/build-og-images.py --only manifesto       # manifesto cards only
```

`--only` accepts: `home`, `hub`, `election`, `party`, `manifesto`, `nation`, `devolved`
(comma-separated for multiple).

### Visual QA

Open `tools/og-generator/og.html` in a browser (no query params) to preview every
card type in the design gallery before running a full batch.

### Deploy

Commit the updated `/og/` tree and `og-image.jpg`. No JS/CSS bump needed unless you
also changed routing or meta helpers. Social platforms cache `og:image` aggressively —
expect a delay before link previews update on Twitter/Slack/etc.

See also: [structured-data](../architecture/structured-data.md) for how routes map to
OG paths.

## Pipeline

```
data/seo.json + election results + manifestos/
        │
        ▼
build-manifest.mjs  →  pages.json  ({ path, spec } per card)
        │
        ▼
generate-og.mjs (Puppeteer + og.html)  →  og/**.jpg, og-image.jpg
```

1. **`build-manifest.mjs`** — reads `data/seo.json` (run `build-seo-data.py` first),
   Westminster results (`data/elections/`), devolved results (`data/devolved/`), and
   manifesto holdings. Derives subtitles from actual archive content (party chamber
   counts, manifesto document titles from `manifesto.md`, election seat strips).
   See [Party manifesto holdings](../data-model/party-holdings.md) for how counts are
   derived and when to regenerate them.
2. **`og.html`** — self-contained HTML/CSS renderer. Design truth: motifs per page
   type, party palette, OKLCH colour derivation, title auto-shrink. Open with no
   params for a QA gallery of every card type.
3. **`generate-og.mjs`** — Puppeteer batch capture. Skips unchanged cards using
   SHA-1 hashes in `og/.og-hashes.json`.

## Quick reference

Same commands as the runbook above:

```bash
python3 scripts/build-og-images.py             # full build
python3 scripts/build-og-images.py --sample      # preview
python3 scripts/build-og-images.py --force       # ignore hash cache
```

Or via npm: `npm run og:build`, `npm run og:sample`.

## Output paths (mirror site URLs)

| Route | Image path |
|---|---|
| `/` | `og-image.jpg` |
| `/about`, `/elections`, … | `og/hub/{slug}.jpg` |
| `/party/:id` | `og/party/{id}.jpg` |
| `/election/:id` | `og/election/{id}.jpg` |
| `/manifesto/:eid/:pid` | `og/manifesto/{eid}/{pid}.jpg` |
| `/nation/:id` | `og/nation/{id}.jpg` |
| `/devolved/:portal` | `og/devolved/{portal}.jpg` |
| `/devolved/:portal/:year` | `og/devolved/{portal}/{year}.jpg` |
| `/devolved/:portal/other-parties` | `og/devolved/{portal}/other-parties.jpg` |

Edge middleware and `js/meta.js` both resolve `og:image` to these paths. See
[structured-data](../architecture/structured-data.md).

## Party colours

The renderer loads `party-colours.embed.js` (generated from
[`data/party-colours.json`](../data/party-colours.json) by
`scripts/build-party-colours.mjs`). Keep slugs aligned with
`js/data.js` / `data/seo.json`. See [party-colours](../data-model/party-colours.md).

## Party manifesto holdings (`buildHoldings`)

`buildHoldings(seo)` in `build-manifest.mjs` counts manifestos per party slug and
chamber. It walks `seo.manifestos` (Westminster) and `seo.devolvedManifestos`
(Holyrood, Senedd, Stormont, euro, london). A new manifesto in the catalogue
increments the right slug on the next build — no manual party-card edits.

**Regenerate** whenever `data/seo.json` or devolved manifest indexes change, in the
same pass as this pipeline (after `build-seo-data.py` if content changed).

Today holdings feed OG party-card subtitles via `partySubtitle()`. The
[design refresh](../design/implementation-plan.md) will also export them to
`data/party-holdings.json` for site party browse cards; both surfaces read one file.

Full reference: [party-holdings](../data-model/party-holdings.md).

## When to re-run

After any change to parties, elections, manifesto holdings, or card copy rules —
typically alongside `build-seo-data.py` and `build-sitemap.py`.

**This is not automatic on deploy.** Cards are static JPGs committed under `/og/`.
Adding a manifesto updates `data/seo.json` / party pages immediately after the
usual rebuild scripts, but **share previews stay stale until**
`python3 scripts/build-og-images.py` runs (party-only is enough when only
holdings change). Phase 5 of the [transcription pipeline](./transcription.md)
includes `--only party` for that reason.

True per-request OG rendering (Cloudflare Worker + HTML canvas) is out of scope
for the static archive; regenerate from data instead.
