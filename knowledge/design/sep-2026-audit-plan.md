---
type: plan
title: September 2026 forensic audit — implementation plan
description: Batch-by-batch work order for the 6 Sep 2026 live-site audit, with this repo’s URL, cover, nav and deploy constraints applied.
tags: [design, a11y, performance, ia, plan]
timestamp: 2026-09-06T00:00:00Z
---

# September 2026 forensic audit — implementation plan

Work order for the 61 findings in the 6 Sep 2026 live-site audit. Finding IDs
(`1.1`, `4.2`, …) match that document. **Do not use the audit’s plural URL
table.** The audit header (Nations in the nav, Elections as one slot) **is**
in scope — see [nations-vs-devolved](./nations-vs-devolved.md).

July visual refresh: [implementation-plan](./implementation-plan.md) (tokens,
reader, light mode). This file sequences the forensic batches; if the two
conflict, **this file wins** for a11y, performance, IA and copy.

## Hard constraints

- No bundler, transpiler, framework, or `package.json` build step.
- Deploy is **Cloudflare Workers** static assets, not Pages. `_headers` and
  `_redirects` still apply.
- New covers stay **transparent A4 PNG** ([covers](../pipelines/covers.md)).
  WebP thumbs are **derivatives** beside those PNGs (confirmed 6 Sep 2026),
  never replacements. Two sizes per cover still fits the ~20k file cap.
- Cache-bust `?v=` / `ASSETS_VERSION` when JS/CSS/covers change
  ([cache-busting](../architecture/cache-busting.md)).
- `python3 scripts/check-cloudflare-limits.py` after adding files (20k file
  cap, 25 MiB/file). ~7.5k deployable files today; two WebP sizes per cover
  still fits.
- [Co-operative Party](../page-rules/cooperative-party.md) and
  [party-names](../data-model/party-names.md) (`getPartyName(id, year)`) still
  apply.
- Ship each batch as **one PR** that can go to `main` on its own.

## Decisions already taken

| Topic | Decision | Source |
|---|---|---|
| URL pillars | Singular: `/election`, `/party`, `/nation`, `/manifesto` | [url-scheme](../architecture/url-scheme.md) |
| Westminster items | Stay `/election/1997`, not `/election/westminster/1997` | same |
| Filesystem | `/manifestos/` stays plural | same |
| Header IA | Four slots: Elections, Parties, Nations, About. Retire Beyond Westminster | [nations-vs-devolved](./nations-vs-devolved.md) |
| Cover thumbs | WebP `cover-356` / `cover-712` **beside** canonical A4 PNG | Batch 1; 20k-file budget OK |
| `/parties` vs `/party/all` | Keep both this round (audit **2.9** deferred) | audit WON’T |
| Semantic HTML sweep (**4.9**) | Opportunistic inside other work, not a batch | audit WON’T |
| Full CSP | Out of scope | audit WON’T |

## Suggested order

```
0  quick wins
1  performance          (biggest user-visible wait)
2  accessibility        (WCAG A/AA on tested pages)
3  design tokens        (makes later CSS cheap)
4  URLs + IA            (one redirect release)
5  archive value        (titles, provenance, search, rails)
6  growth               (RSS, /wanted, PDF copies)
```

Do **not** start 4 until 0–3 are on `main`: every `href` in the SPA and
middleware has to move together. Do **not** start 5.2-scale content edits
before 4 if they hard-code old paths.

## Batch 0 — Quick wins (~one evening)

**Goal:** Level A contrast/ARIA nits, honest archive size, fewer 304s.

| ID | Work | Files | Notes |
|---|---|---|---|
| **4.4** | Versioned `/js/*` and `/styles.css` → long-cache `immutable` | `_headers` | Live audit saw `max-age=14400`; repo is already `300`. Do **not** mark unversioned PDFs `immutable` if we still replace in place. Covers with `?v=` may use a long max-age. Keep HTML `max-age=0, must-revalidate`. |
| **5.1** | Hero states manifesto **count**, not “650 Commons seats” | `js/app.js`, `js/data.js` or generated count | Derive from `catalog.jsonld` / index at build or runtime. **650 is the current Commons size**, not a typo; move seats elsewhere if kept. Do not hard-code `659`. |
| **3.1** | Inline prose links: underline + ≥3:1 vs surrounding text | `styles.css` | Site-wide. |
| **3.2** | Remove `role="menu"` (and related) from nav that has no `menuitem`s | `js/app.js` | Deleting the role is the fix. |
| **5.9** / **2.14** | One placeholder string: **Not yet digitised** | `js/app.js` and any carousel copy | Sentence case, every surface. |
| **3.8** | `aria-current="page"` on breadcrumbs and current nav item | `js/app.js` | |
| **1.1** | Header/footer wordmark = **The British Manifesto Archive**; domain secondary | `index.html`, `js/app.js`, `js/meta.js`, `functions/_middleware.js` | Title template `Page — The British Manifesto Archive`. Unblocks **4.10a**. |

**Verify:** curl `Cache-Control` on `/js/app.js?v=…` and `/`; axe homepage (link contrast, no `role="menu"`); homepage stat row; one interior `<title>` and header.

## Batch 1 — Performance

**Goal:** homepage weight ~4.7 MB → ~0.6 MB. No visual redesign.

Order: **4.2 → 4.1+4.7 → 4.3 → 4.5 → 4.6**.

| ID | Work | Files | Notes |
|---|---|---|---|
| **4.2** | Never request a cover when `manifesto-assets.json` says `cover: false`. Fix double-`?v=` on the png fallback | `js/app.js` | Inventory already exists ([manifesto-assets](../pipelines/manifesto-assets.md)). |
| **4.1** | Emit `cover-356.webp` + `cover-712.webp` beside each `cover.png`; `<picture>` + `srcset` for thumbnails | new `scripts/build-cover-thumbs.py`, `js/app.js`, [covers](../pipelines/covers.md) | Keep canonical transparent A4 PNG. JPEG is fallback only. Run limits script. Homepage six thumbs are the 4.28 MB headline; generate those first if splitting the PR. |
| **4.7** | `width`/`height` (or CSS `aspect-ratio` already on A4) on every `<img>` | `js/app.js` | Ships with 4.1. |
| **4.3** | One fetch per JSON URL per session; don’t pull five unused devolved indexes on `/` | `js/app.js`, `js/data-loader.js`, chamber JS | |
| **4.5** | `defer` the homepage set; route-load chamber JS + `marked` | `index.html`, `js/app.js` | Scripts are **classic globals**, not ES modules — use a memoised `loadScript`, not `import()`. Self-host `marked` under `/js/` (drop jsDelivr). Prefetch chamber modules on nav hover. |
| **4.6** | Self-host **subset** woff2 (Latin) for Playfair, Public Sans, Source Serif | `index.html`, `styles.css`, `fonts/` | Kill render-blocking Google Fonts CSS. Subset with `pyftsubset` / similar; no bundler required. |

**Verify:** DevTools network on cold homepage (image bytes, JS count, font origin); CLS; missing-cover election does not 404 a `.png`/`.jpg`; `check-cloudflare-limits.py`.

## Batch 2 — Accessibility completion

**Goal:** WCAG 2.1 AA on homepage, `/election/1997`, `/party/all` (today `/parties/all`), both themes.

| ID | Work | Files | Notes |
|---|---|---|---|
| **3.4** | Party-colour **text** on party-colour tint: ink/border pattern that passes AA in both themes | `styles.css`, `js/colour.js` | After **1.2** is nicer; can ship a one-component fix now if 3 is delayed. |
| **3.5** | Results table: Votes + Vote % reachable at 375 px | `styles.css`, election renderers | **Actual data loss.** Card-stack / column priority / horizontal scroll with visible cue — pick one and test. |
| **3.3** | Real list markup; `h2` groups on the A–Z parties page | `js/app.js` | Remove illegal `role="listitem"` on anchors. |
| **3.7** | Confirm search focus trap | `js/search.js` | [a11y-programme](./a11y-programme.md) already claims `inert`. Re-test; only add a trap if the dialog still leaks. |
| **3.6** | Hit targets ≥24 px (AA 2.5.8); aim 44 px where it doesn’t wreck the header | `styles.css` | Easier after **1.2**. |
| **3.9** | `forced-colors` / Windows High Contrast | `styles.css` | |
| **3.10** | Hemicycle: expose seat/party summary beyond one `aria-label` | `js/parliament.js` | Don’t claim a fully keyboard-operable SVG this round unless cheap. |
| **3.11** | One link wrapping cover+label; `aria-hidden` on decorative emoji | `js/app.js` | Overlaps **2.13**. |

**Verify:** axe-core both themes on the three pages; keyboard-only search open/close; 375×812 results table shows vote data; VoiceOver/NVDA sample per [a11y-programme](./a11y-programme.md).

## Batch 3 — Design system

**Goal:** tokens so later CSS is find-and-replace. Extends July colour tokens; does not replace them.

Order: **1.2 → 1.3 → 1.6 → 1.5 → 1.4 → 1.7, 1.8, 1.11–1.14**. Skip **1.9** glyph redesign; do light-mode glyph contrast with **1.14**.

| ID | Work |
|---|---|
| **1.2** | `--fs-*` 8-step scale + `--lh-*`; map every `font-size` in `styles.css` |
| **1.3** | Floor 11 px; tracked uppercase uses `--font-ui`, not Source Serif |
| **1.6** | Radius + elevation tokens; dark-mode shadows that actually lift |
| **1.5** | Spacing scale; retire the 20 ad-hoc gaps |
| **1.4** | Display / body / UI contract; one arrow glyph |
| **1.7** | Mega menu inside the 1200 px grid |
| **1.8** | Four nation cards: 2×2 or a fourth track, not a 3-col leftover |
| **1.10** | Latest Additions: don’t lead with three empty scans (filter via assets JSON) |
| **1.11** | “Four ways in” looks like links |
| **1.12** | Party-card meta doesn’t orphan “manifestos” |
| **1.13** | Mobile header + stat row |
| **1.14** | Light-theme gold/contrast |

**Verify:** visual pass home / election / party / manifesto, light and dark, 375 and 1200+; grep `styles.css` for raw `font-size:` / `gap:` stragglers.

## Batch 4 — URLs and IA (one release)

**Goal:** singular hubs, `/devolved` under `/election`, audit four-slot header, one nav model on mobile. **Not** the audit’s plural REST tree.

Implement [url-scheme](../architecture/url-scheme.md) in this batch. 301s **above** SPA 200s. Same commit: sitemap, `seo.json`, middleware, in-app `href`s, London one-hop legacy lines.

### 4A — Redirects and router (must)

`_redirects`, `js/app.js` `route()`, `functions/_middleware.js`, `scripts/build-sitemap.py`, `scripts/build-seo-data.py`, every `href` in `js/*.js`.

Canonical recap: `/election` merged hub; `/election/westminster` GE timeline; `/election/1997` unmarked GE; `/election/holyrood/2021` etc.; `/party`, `/party/all`, `/party/other`; `/nation`; `/nation/europe` → `/party/european-groups`.

### 4B — IA on the new paths (must)

| ID | Work | Constraint |
|---|---|---|
| **2.2** | One **Elections** slot (Westminster + chambers). Retire Beyond Westminster as a nav label | Same release as 4C |
| **2.4** | Mobile drawer = desktop IA (groups, not a flat 9-link alternative); opaque overlay; in-drawer close | Same four slots as desktop |
| **2.5** / **4.10b** | Europe is not a nation; `/party/european-groups`; nations H1 drops “& Europe” | |
| **2.6** | No 🇮🇪 for Northern Ireland; drop “England & UK-wide” conflation | SVG/plain text; flax flower optional |
| **2.10** | `/others` → `/party/other` + breadcrumb | |
| **2.11** | `party.related` cross-links (e.g. Labour ↔ Scottish/Welsh Labour) | |
| **2.12** | Guessable 404s for `/election/:year` and `/party/:slug` | |
| **2.13** | Single manifesto card link; unambiguous jump chips | |
| **2.3** | One label per node (`meta.js` `NODES`) for nav/breadcrumb/hero | Byte-identical labels |
| **5.11** | Delete “use Beyond Westminster” disclaimers once URLs don’t need them | |
| **4.10** | Edge `<h1>` / titles follow **1.1** | |

### 4C — Header restructure (in scope)

Audit **2.1** + **2.2**: four slots — **Elections** ▾, **Parties** ▾, **Nations** → `/nation`, **About**. Spec and hrefs: [nations-vs-devolved](./nations-vs-devolved.md). Ship **in the same PR as 4A/4B**.

**Verify:** curl 301s (`/elections`, `/devolved/holyrood/2021`, `/parties`, `/others`, `/nation/europe`); 200 on new hubs; no redirect chains; sitemap + a handful of JSON-LD paths; desktop mega-menu and mobile drawer show the same tree including Nations; NI headings.

## Batch 5 — Archive value

**Goal:** citable documents. Longest batch; most of it is data + copy.

| ID | Work | Notes |
|---|---|---|
| **5.2** | Real manifesto titles in H1, cards, catalogue, `llms.txt` | Wikipedia slogans for Lab/Con/LD; cover or document H1 otherwise. Fallback is `{Party} manifesto {Year}`, not “Published without a distinct title”. `<title>` leads with party + year. Unlocks **5.5**, search, **1.10** labels. |
| **5.4** | Per-item provenance (source, digitisation, licence) | On the manifesto page, not only `/about`. |
| **5.3** | Surface `/about` trust copy on document pages | Not on the homepage (user: too long). Short, not a paste of About. |
| **5.5** | Citation styles + access date + real title; consider BibTeX | After **5.2**. |
| **5.10** | Hero stat row shows counts | No 1945–2024 span in prose (Holyrood/Senedd 2026). |
| **5.12** | Copyright/licence **per document** | Ties to **5.4**. |
| **2.7** | Crawlable `/search?q=` (+ mode); original-case snippets | Add SPA 200 + middleware. Then `SearchAction` in JSON-LD is allowed ([structured-data](../architecture/structured-data.md), task-007). |
| **2.8** | Sticky on-this-page rail on long election/party pages; jump-to-documents on election pages | Manifesto TOC is the template. |

**Verify:** `/manifesto/1997/labour` title + cite + provenance; `/search?q=thatcher` shareable; election page rail; Schema.org still valid.

## Batch 6 — Growth

| ID | Work | Notes |
|---|---|---|
| **5.7** | RSS (or Atom) of new digitised items | Generate from [latest-additions](../content/latest-additions.md) or git-first-add dates. |
| **5.6** | Date each Latest Additions card (not one bulk stamp) | Same generator. |
| **5.8** | `/wanted` + in-situ “help us digitise this” where scans are missing | After **4.2** / assets JSON. |
| **4.8** | Smaller reading-copy PDF (or “read online” emphasis) for the ~23 MB files | Do not replace the archival PDF. Optional derivative; watch 25 MiB and honesty about scans. |

**Verify:** feed in a reader; carousel dates; `/wanted` 200; a large-PDF page offers a sane path on a phone.

## WON’T (this programme)

| ID | Why |
|---|---|
| **2.9** | Curated `/party` hub vs `/party/all` — revisit after 4 |
| **1.9** | Wales glyph metaphor; contrast is **1.14** |
| **4.9** | Full `article`/`figure` sweep — opportunistic |
| Plural URLs | Replaced by [url-scheme](../architecture/url-scheme.md) |
| CSP beyond `frame-ancestors` | Low benefit, easy to break `marked` / fonts |

## Per-PR checklist

1. Finding IDs in the commit message.
2. Bump `?v=` / `ASSETS_VERSION` if JS/CSS/covers changed.
3. `python3 scripts/check-cloudflare-limits.py` if files were added.
4. Update this plan’s batch checkboxes in the task handoff, plus [log](../log.md).
5. UI batches: exercise the changed flow in a browser (home, one election, one manifesto, one party), light and dark where CSS changed.

## Measurement replay (from the audit)

After 1: homepage images ≪ 4.3 MB, JS request count down on `/`. After 2: axe clean on the three sample URLs. After 4: ~1,100 sitemap URLs rewritten, 301s single-hop. After 5: citation uses the real title.
