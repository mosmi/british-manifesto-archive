---
type: log
title: Project log
description: Reverse-chronological history of notable changes and decisions.
tags: [log, history]
timestamp: 2026-07-05T00:00:00Z
---

# Project log

Newest first. Add a dated entry when you make a notable change. Keep deep technical
detail in the relevant `knowledge/` concept; this is the timeline.

## 2026-09-06 — Elections menu height

Desktop `#elections-dropdown` is not height-capped; six chamber rows plus the
hub link must all show without a scrollbar. Assets `?v=2026090628`. See
[nations-vs-devolved](./design/nations-vs-devolved.md).

## 2026-09-06 — Manifesto cover wall

Canonical `/manifesto` is a filterable cover index from `manifesto-assets.json`
(route-loaded `js/manifestos-hub.js`). Not a fifth header slot — footer, homepage Manifestos count, and the guessable URL. `/manifestos` 301s here. Gap tiles say “No
cover scan”. Density axis is calendar decades (including 1950 and 2020) plus hover year/count. **1945** and **2026** are centred on their bars. Homepage hero stats are the ways in (Ways in row removed). Hero and catalogue count **619 unique folders** (London once). Assets
`?v=2026090627`. See [manifesto-hub](./design/manifesto-hub.md).

## 2026-09-06 — Drawer accordion and footer IA

Hamburger menu starts on the four slots. Elections / Parties expand one at a
time instead of dumping both megas. Footer links: Home / Elections / Parties /
Nations / About. Assets `?v=2026090617`. The Elections / Parties **label**
goes to the hub; the chevron opens the submenu.

## 2026-09-06 — Batch 5 archive value

Published manifesto titles (Wikipedia slogans for Lab/Con/LD; cover or
document H1 otherwise) in H1, cards, catalogue, and citations. Fallback is
`{Party} manifesto {Year}`, not “Published without a distinct title”. Page
`<title>` leads with party and year. Per-document provenance and copyright on
the reader. Home hero uses the title, four ways in, and the stat row (no
1945–2024 span; Holyrood and Senedd 2026 are in the archive). Trust copy lives
on manifesto pages and `/about`, not the homepage. Crawlable `/search?q=` with
original-case snippets and `SearchAction`.
Sticky on-this-page rails on election and party pages. Assets `?v=2026090614`.
See [manifesto-titles](./pipelines/manifesto-titles.md) and
[sep-2026-audit-plan](./design/sep-2026-audit-plan.md).

## 2026-09-06 — Batch 4 singular URLs and four-slot header

Public hubs are singular: `/election`, `/election/westminster`, `/party`,
`/party/all`, `/party/other`, `/party/european-groups`, `/nation`. Legacy
`/elections`, `/devolved/…`, `/parties/…`, `/others`, `/nations`, `/nation/europe`
301 once. Header is Elections / Parties / Nations / About; mobile drawer matches
desktop. Assets `?v=2026090608`. See [url-scheme](./architecture/url-scheme.md)
and [nations-vs-devolved](./design/nations-vs-devolved.md).

## 2026-09-06 — Batch 3 design tokens and polish

`--fs-*` (11px floor), `--space-*`, `--radius-*`, `--shadow-*` in `styles.css`.
Tracked uppercase uses `--font-ui`. Mega menu inset to the 1200px grid. Homepage
nations are 2×2 / 4-col, not 3-col. Latest Additions leads with covers. Four ways
in are underlined links. Party holdings keep “manifestos” with the last chamber.
Mobile stats are a 2×2. Light gold is AA `#7a5f24`. Assets `?v=2026090607`. See
[tokens](./design/tokens.md) and [sep-2026-audit-plan](./design/sep-2026-audit-plan.md)
Batch 3.

## 2026-09-06 — Batch 2 accessibility (WCAG 2.1 AA on tested pages)

Party tags and winner badges use ink + kicker border, not party-on-party tint.
Election results keep Votes and Vote % at 375px via `.results-scroll`. A–Z
parties use letter `h2`s and real lists. Search trap re-tested (`inert` + Tab
cycle; skip-link included). Chrome hit targets 44px; `forced-colors`; hemicycle
`<desc>` seat summary; one cover+label link on manifesto cards. Assets
`?v=2026090606`. See [a11y-programme](./design/a11y-programme.md) and
[sep-2026-audit-plan](./design/sep-2026-audit-plan.md) Batch 2.

## 2026-09-06 — Batch 1 performance (covers, fonts, JS)

Homepage no longer requests missing covers, Google Fonts, jsDelivr, or unused
devolved indexes. Cards use WebP `cover-356`/`cover-712` beside canonical PNGs.
Chamber JS and `marked.min.js` load on the routes that need them. Latin fonts are
self-hosted under `/fonts/`. Assets `?v=2026090605`. File count 8736. See
[sep-2026-audit-plan](./design/sep-2026-audit-plan.md) Batch 1 (**4.1–4.7**).

## 2026-09-06 — Header wordmark no longer overlaps nav

Wordmark is a locked two-line stack (never a squeezed four-line column). Desktop
nav collapses to the hamburger at **1100px** (JS hover matches). Assets
`?v=2026090604`.

## 2026-09-06 — Header wordmark wraps below 1400px

Full name **The British Manifesto Archive** was `nowrap` and collided with
desktop nav at mid widths. Below 1400px it stacks as “The British” /
“Manifesto Archive”; domain hides; nav links no longer shrink. Assets
`?v=2026090603`.

## 2026-09-06 — Batch 0 of the forensic audit

Shipped cache `immutable` on versioned JS/CSS; hero manifesto count from
`data/archive-counts.json` (659 / 71); brand wordmark; underlined prose links;
removed `role="menu"`; “Not yet digitised”; `aria-current` on crumbs and nav.
Assets `?v=2026090602`. Parties hub `/parties/all` now marks the Parties nav current. See [sep-2026-audit-plan](./design/sep-2026-audit-plan.md).

## 2026-09-06 — Header lock reopened (I04/I08)

Four-slot nav: Elections, Parties, Nations, About. Beyond Westminster retired as
a header label. WebP thumbnail derivatives confirmed beside canonical A4 PNGs.
See [nations-vs-devolved](./design/nations-vs-devolved.md) and
[sep-2026-audit-plan](./design/sep-2026-audit-plan.md). Not implemented.

## 2026-09-06 — Forensic audit implementation plan

Wrote [design/sep-2026-audit-plan](./design/sep-2026-audit-plan.md) (batches 0–6)
and backlog task-008. Applies singular URLs and the locked Nations header split
on top of the 6 Sep 2026 live-site audit.

## 2026-09-06 — Singular URL scheme (decided, not shipped)

Recorded [architecture/url-scheme](./architecture/url-scheme.md) after the Sep 2026
forensic audit. Public pillars are singular (`/election`, `/party`, `/nation`,
`/manifesto`). Westminster **items** stay `/election/1997` (optional alias
`/election/westminster/1997`); chamber items become `/election/holyrood/2021`.
Filesystem `/manifestos/` stays plural. Not implemented.

## 2026-08-10 — Natural Law spectrum + manifesto list formatting (Cursor Grok)

Assets `?v=2026081002`.

- Natural Law Party spectrum → *Syncretic / New Age (Natural Law and Transcendental Meditation)*.
- Batch manifesto.md list-formatting / trailing-newline cleanup across the archive.

## 2026-08-09 — Natural Law Party (1997 GE + 1999 EP) (Cursor Grok)

Assets `?v=2026080914`.

- Added party slug `naturallaw` (`PARTIES`, `OTHERS_PARTIES`, `EURO_OTHER_PARTIES`,
  `data/party-colours.json` navy `#000080`).
- Ingested **1997** UK manifesto from the party’s archived multi-page site
  (108 HTML pages → `manifestos/1997/naturallaw/` PDF + `manifesto.md` + transparent
  A4 `cover.png`); wired via `extraManifestoParties` / `manifestos-index.json`.
- Ingested **1999** European manifesto (`manifestos/euro/1999/naturallaw/` PDF +
  text + `manifesto.png`); registered in `data/devolved/euro/1999.json`.
- Sources: archived HTML dumps + derived PDFs under the local Original documents
  tree; Wayback originals at `natural-law-party.org.uk/UKmanifesto/` and
  `…/euromanifesto/`.
- 1997 PDF shipped as a ~20 MiB JPEG rebuild (under Cloudflare’s 25 MiB file
  limit); full-text remains in `manifesto.md`. Dark-mode party hero meta now
  uses `--party-kicker` for legibility on dark brand colours.

## 2026-08-09 — Compact EP FPTP hexmaps (contiguous UK outline) (Cursor Grok)

Assets `?v=2026080912`.

- Centroid-only placement left ~80 hexes sparse on the Westminster frame.
- `scripts/build-euro-fptp-hex.py` now nation-packs (scale → Hungarian snap →
  merge → hole-fill) and assembles England/Scotland/Wales into one mainland;
  Highlands & Islands and NI stay detached. Mainland touch 100% for all four
  years. Cross-nation hole-fill disabled (it was scattering Wales into England).
  See [pipelines/euro-region-map](./pipelines/euro-region-map.md).

## 2026-08-09 — FPTP EP constituency hexmaps 1979–1994 (Cursor Grok)

Assets `?v=2026080910`.

- Built `data/hex/euro/{1979,1984,1989,1994}.hexjson` via
  `scripts/build-euro-fptp-hex.py` from constituency winners + Westminster→EP
  centroids (colliding `q,r` nudged; NI `seats_list` of 3 MEPs).
- UI: `euroHasConstituencyMap` + **Constituencies** tab in `js/euro.js`
  (reuses `hexmap.js`; does not widen `euroHasRegionMap`).
- Docs: [pipelines/euro-region-map](./pipelines/euro-region-map.md).

## 2026-08-09 — FPTP EP election constituency dataset & Westminster crosswalks 1979–1994 (Antigravity)

- Generated `data/sources/european-parliament-elections/constituency-winners-1979-1994.json` containing structured constituency-level winners, MEP names, party IDs, and EP political groups across all four FPTP elections (1979, 1984, 1989, 1994).
- Built Westminster-to-EP constituency crosswalk datasets under `data/sources/european-parliament-elections/westminster-to-ep/{1979,1984,1994}.json` mapping 100% of FPTP-era EP constituencies to their constituent Westminster hex keys from `data/hex/elections/{1979,1983,1997}.hexjson` (0 empty EP lists across all eras).
- Computed averaged `(q, r)` centroid coordinates for every EP constituency to enable direct hex map rendering and spatial aggregation.
- Updated European Parliament FPTP hexmaps to generate manifesto detail links using the `/devolved/euro/{year}/{partyId}` route format:
  1. Added `options.manifestoPrefix` support to `drawHexmap` in `js/hexmap.js`.
  2. Passed `manifestoPrefix: \`/devolved/euro/\${election.year}\`` in `js/euro.js`.
  3. Bumped `?v=2026080913` cache-busting query strings for `hexmap.js` and `euro.js` in `index.html`.
- Updated dataset index in `data/sources/european-parliament-elections/README.md`.

## 2026-08-09 — European Parliament regional maps 1999–2014 (Cursor Grok)

Assets `?v=2026080909`.

- Extended **Electoral regions** tab to all PR-era EP elections:
  `/devolved/euro/{1999,2004,2009,2014,2019}`.
- Built `data/devolved/euro/regions/{1999,2004,2009,2014}.json` from Commons
  Library RP PDFs via `scripts/build-euro-regions-pr.py` (MEP lists + regional
  vote shares; seat totals validated against election JSON).
- Year-aware waffle grids in `js/euro-map.js` for changing seat magnitudes
  (87 → 78 → 72 → 73).
- Source bundle: `data/sources/european-parliament-elections/`.
- **1979–1994 FPTP maps deferred** (wrong geography for waffle renderer); phase-2
  lead documented in [pipelines/euro-region-map](./pipelines/euro-region-map.md)
  — EUI constituency-level dataset (Cadmus 1814/75475), not RP99-57 alone.

## 2026-08-09 — European Parliament regional seat map (2019) (Cursor Grok)

Assets `?v=2026080901`.

- Added interactive **Electoral regions** tab on `/devolved/euro/2019`: geographic
  EER outlines with seat-square clusters and MEP detail panel.
- Data from Commons Library CBP 8600 (`data/sources/commons-library/`); geography
  from ONS EER Dec 2018 UGCB, simplified to `data/maps/euro-regions.json`.
- Builders: `scripts/build-euro-regions.py`, `scripts/build-euro-region-map.py`.
- Docs: [pipelines/euro-region-map](./pipelines/euro-region-map.md).

## 2026-08-08 — Fix Holyrood 1999 parliament chart + Ayr hex (Cursor Grok)

Assets `?v=2026080801`.

- 1999 results summed to 130 seats (Others: 3) vs 129 — crashed
  `drawParliamentChart` (`allPositions[i].t` undefined). Split into SSP (1) +
  Dennis Canavan Independent (1); index updated.
- Hex map Ayr was John Scott/Con (2000 by-election); restored Ian Welsh/Labour.
- Chart now truncates over-allocated seat colours so bad rows cannot blank the SVG.

## 2026-08-08 — Mobile results folds stay closed on hash jump (Cursor Grok)

Assets `?v=2026080704`. `#party-*` chip links scroll to the section but no longer
auto-open the results `<details>` on narrow screens (that left London’s 19-row
list expanded on Labour).

## 2026-08-07 — Mobile party hero densify + results folds (Cursor Grok)

Assets `?v=2026080703`.

- Compact ≤900px `.party-hero-stats` panel (Founded / Spectrum / Contested / Wins)
  matching `sandbox/party-hero-mobile-stats-mockup.html`.
- Wins numeral uses `--party-color` / `--party-kicker` (same as Founded); removed
  inline `partyTextColour` wash.
- Party results lists wrap in `<details class="party-results-fold">` — closed on
  mobile, open on desktop; `#party-*` chips scroll to the section.

## 2026-08-07 — Wins badge left-align when stacked (Cursor Grok)

Assets `?v=2026080702`. On ≤900px the wins aside stacks under the hero; year and
chamber chips now `flex-start` with the numeral (they had stayed `flex-end`
between 641–900px).

## 2026-08-07 — Ken Livingstone party page + multi-chamber wins badge (Cursor Grok)

Assets `?v=2026080701`.

- Added `PARTIES.livingstone`; 2000 London `mayorWinner` → `livingstone` (ballot
  label Independent). Party history also matches 2004–12 Labour-banner runs by
  candidate name.
- Party-hero wins aside: Westminster majors keep a Westminster total + chamber
  *count* chips (no year pills); single-chamber leads (UKIP/Plaid/SNP/…) get
  year chips when ≤5. Mock-ups remain under `sandbox/`.
- Regenerated `data/seo.json` / `catalog.jsonld` so `/party/livingstone` is a
  valid edge route. `scripts/build-seo-data.py` now has
  `from __future__ import annotations` so it runs on system Python 3.9.
- Smoke-checked locally: Livingstone 2 mayoral wins + year chips + 4 rows;
  Labour/Con Westminster + Europe/London counts; UKIP Europe 2014; SNP Holyrood
  years; contested chips still present.

## 2026-08-07 — Party “Elections contested” chamber chips (Cursor Grok)

Assets `?v=2026072107`.

- Replaced the middot sentence in the party hero with chamber chips when a party
  has 2+ contested chambers (scalar kept for one chamber). Short label
  `Europe`; chips link to `#party-*` results sections.
- Mock-up retained at `sandbox/party-elections-contested-mockup.html`.

## 2026-07-21 — London mayoral result rows link to party pages (Cursor Grok)

Assets `?v=2026072106`.

- Added missing `party` ids on 2024 (and 2016) mayoral candidates that already
  have dedicated pages — Binface, London Real, Britain First, SDP, Animal
  Welfare, One Love, Independents.
- `londonPartyCell` now uses `resolvePartyId` + `devolvedPartyLink` so result
  labels link to `/party/<id>`.

## 2026-07-21 — Pirate Party UK 2010 Westminster manifesto added (Cursor Grok)

Assets `?v=2026072105`.

- Added `manifestos/2010/pirate/` (PDF, transparent A4 cover, transcribed
  `manifesto.md`; leader Andrew Robinson).
- Wired `manifestos-index.json`, `extraManifestoParties` in `js/data.js` and
  `data/elections/2010.json`; rebuilt pdf-sizes, latest-additions, SEO, sitemap,
  fulltext, manifesto-assets, and party/manifesto OG cards.

## 2026-07-21 — Brexit→Reform alias restored; euro election loading skeleton (Cursor Grok)

Assets `?v=2026072104`.

- Restored `PARTY_ALIASES.brexit → reform`; removed standalone `PARTIES.brexit`.
  `/party/brexit` now canonicalises to Reform UK (client `replaceState` +
  `_redirects` 301). EP folder `manifestos/euro/2019/brexit/` kept.
- Euro index `control` for 2019 corrected to `reform`; winner helper resolves aliases.
- `renderEuroElection` shows a loading skeleton (same pattern as Senedd) so hard
  navigations are not a blank page while JSON loads.

## 2026-07-21 — Home ways-in polish, UK-wide breadcrumbs, OG rebuild hook (Cursor Grok)

Assets `?v=2026072103`.

- **Home:** Replaced the inline “Four ways in: A · B · C · D” line with a four-column
  label + hint nav under the hero subtitle.
- **Breadcrumbs:** `partyBreadcrumbItems` skips the nation crumb for
  `nation: 'england'` (UK-wide bucket) so Reform UK etc. read
  `Home › Parties › Reform UK`. Documented in
  [`party-names.md`](./data-model/party-names.md).
- **OG cards:** Stale `/og/party/*.jpg` (last mass build ~5 Jul) did not reflect new
  holdings. Regenerated party cards from current `seo.json`; added
  `build-og-images.py --only party` to transcription Phase 5 and clarified in
  [`og-generator.md`](./pipelines/og-generator.md) that cards are static JPGs, not
  edge-dynamic.

## 2026-07-21 — UX audit follow-on I11–I18, L1, L3, research notes (Cursor Grok)

Assets `?v=2026072102`. Plan waves A–D (L2 compare mode out of scope).

- **I11:** `minmax(min(280px,100%),1fr)` grids; election-body `overflow-x: clip`.
- **I12:** Verified platform-aware ⌘K / Ctrl+K in `search.js` — no change.
- **I13:** Nation headings use `aria-hidden` flags via `nationHeadingLabelHtml`.
- **I14:** Richer edge noscript hubs (elections years, parties A–Z, About, portals).
- **I15:** “England seats” badge + stronger Documents seat note.
- **I16:** Richer 404 with hub links + Search button.
- **I17:** Mega-menu Reform UK / Reform UK Scotland / Reform UK Wales → `/party/reform`.
- **I18:** Light `--gold` → `#7a5f24` (~5.4:1 on cream).
- **L1:** Home “Four ways in”; About organisation section; election/portal type chips.
- **L3:** [`design/a11y-programme.md`](./design/a11y-programme.md) + results table caption.
- **Research:** [`design/ux-research-backlog.md`](./design/ux-research-backlog.md).
- **I01 live:** Still verify `GET /elections` → 200 after this middleware ships to `main`.

## 2026-07-21 — H4-H6 Heading Level Depth Preservation Fix (Gemini 3.5 Flash)
- Updated `tools/transcription-toolkit/format_manifesto_headings.py` to preserve arbitrary heading depths (`####` H4, `#####` H5, `######` H6) without collapsing them to H3, maintaining deep document hierarchies.
- Restored `#### The Facts` and `#### What Will We Do?` (H4) under `### British People Are Worried About [Topic]` (H3) across all pages of Veritas 2005 (`work/manifestos__2005__veritas__manifesto`).

## 2026-07-21 — UX audit I01–I10 highest-priority fixes (Cursor Grok)

Closed the July 2026 UX audit top issues. Assets `?v=2026072101`.

- **I01:** Middleware short-circuits `/elections` (+ `/elections/`) to the SPA shell;
  recovery kept as fallback. Live still 308s until this deploys.
- **I02/I03:** Verified catalogue/full-text honesty and primary-party ranking
  (`SEARCH_LIMIT` 24, exact-name boost) — no further product change.
- **I05:** Catalogue “Did you mean…?” fuzzy suggestions on empty results.
- **I06:** Shared `pdfCtaHtml` — **Original PDF** (+ size) on cards and reader.
- **I07:** Chrome H1 is sole landmark; first markdown H1 → `.manifesto-doc-masthead`;
  `document.title` includes Manifesto + year (sandbox kept as reference).
- **I08/I04:** Nations stays footer/homepage (not header); hub + home copy clarify
  geography vs institutions — see [nations-vs-devolved](./design/nations-vs-devolved.md).
- **I09/I10:** In-document find in TOC; citation strip with copy actions on reader.

See [manifesto-viewer](./page-rules/manifesto-viewer.md),
[search-browse](./design/search-browse.md).

## 2026-07-20 — Batch Heading Level & Casing Standardisation Pass (Gemini 3.5 Flash)
- Created `tools/transcription-toolkit/format_manifesto_headings.py` to automate heading hierarchy and Title/Sentence casing rules across all draft files (`#` H1 for single manifesto title, `##` H2 for major sections & contents, `###` H3 for sub-questions & policy sub-topics).
- Ran automated pass across all 325 work directories in `tools/transcription-toolkit/work/`; successfully refactored and standardized heading formatting in 281 `draft.md` files while preserving all domain acronyms (EU, NHS, UK, DUP, SNP, etc.).

## 2026-07-20 — Session: empty manifesto UX + `/parties/all` redesign + CPB split (Cursor Grok)

Session work (evening), current assets `?v=2026072016`. Related notes:
[page-rules/manifesto-viewer](./page-rules/manifesto-viewer.md),
[design/search-browse](./design/search-browse.md),
[data-model/party-contests](./data-model/party-contests.md),
[content/about-page](./content/about-page.md).

### Missing manifesto reader (e.g. `/manifesto/1955/nationalliberal`)
- When `manifesto-assets` shows no PDF, cover, or Markdown, the reader now shows
  **“Not yet in the archive”** (honest copy, election/party links, `noindex`) instead
  of a broken cover and a false “connection failed / Try again” state.
- Solid CTA contrast: `.manifesto-content a` was overriding `.manifesto-btn-solid`
  (gold-on-gold in light mode). Fixed with higher-specificity selectors keeping
  `color: var(--field)`.
- Ghost CTA copy **Contact and corrections** → `/about#contact-and-corrections`
  (`id` on the About `<h2>`); SPA `route()` scrolls to in-page hashes after render.

### `/parties/all` browse redesign (Storied Colors–inspired)
- Hero search box (“Search the archive” / “Search by party”; Try: Reform, Labour,
  SNP, Plaid) plus live party count from `PARTIES` (same source as the homepage
  hero stat).
- Hue spectrum strip (“Party colour”): thin bars per party, hover expands and
  names the party; click opens the party page.
- Left sidebar filters: **Colour family** (OKLCH hue buckets; teal range widened so
  Reform UK `#12B6CF` is teal not blue; brown family added), **Nation / Europe**
  (Others removed from that control), **Party founded** dual-handle decade range
  (`1890s and earlier` → present; drag no longer rebuilds the sidebar mid-gesture;
  thumbs vertically centred on the track), **Status** (respects curated
  `status` / dissolved description; SPGB marked active), **Tags** (spectrum
  keywords + nation labels, with filter box and counts), **Contested** (curated
  `contests[]` + Westminster results + archive docs; Holyrood/Senedd/Stormont/
  London/Europe chips), **Documents**.
- Inline “nation-grouped hub” link uses About-style gold link CSS.
- Search modal kicker: “Search the catalogue” → “Search the archive”.

### Communist Party of Britain split
- New party id `cpb` (Communist Party of Britain); CPGB remains `communist`.
- Moved folders/index wiring: 2024 GE, Holyrood 2011/2016, Senedd 2021/2026
  (1955/1966 stay on CPGB). Updated elections/devolved JSON, party colours/links/
  aliases, `js/data.js`, and rebuilt pdf-sizes, manifesto-assets, seo, fulltext,
  sitemap, party-colours embed.

## 2026-07-20 — Graceful empty manifesto reader (Cursor Grok)
- `/manifesto/…` with no PDF, cover, or Markdown now shows “Not yet in the archive”
  (links to election/party, `noindex`) instead of a broken cover + false
  “connection failed / Try again” state. Assets `?v=2026072008`.

## 2026-07-20 — Scan-not-archived placeholder via manifesto-assets (Cursor Grok)
- Added `scripts/build-manifesto-assets.py` → `data/manifesto-assets.json`
  (pdf/md/cover flags). Cards + reader show “Scan not yet archived” immediately
  when `cover` is false (11 text-only folders today). Covers still show when
  present even without a PDF. Clarified catalogue-label fallbacks in
  [fulltext-index](./pipelines/fulltext-index.md). Assets `?v=2026072007`.

## 2026-07-20 — BNP 1992 on party/election pages (Cursor Grok)
- 1992 BNP had `manifesto.md` + catalogue row but was missing from
  `extraManifestoParties` (BNP won no seats, so no results row). Added to
  `js/data.js` + `data/elections/1992.json`. Party pages now also fall back to
  `manifestos-index.json` so text-only editions aren’t dropped if wiring lags.
  Assets `?v=2026072006`.

## 2026-07-20 — Full-text index future-proofing (Cursor Grok)
- `build-fulltext-index.py` now writes `data/fulltext-meta.json` and supports
  `--check` (fingerprint of every `manifesto.md`). Search loads meta → index
  with `?v=<generated>` so rebuilds do not need an ASSETS_VERSION bump.
- Wired into transcription Phase 5 + manifesto add checklist.

## 2026-07-20 — Full-text search Phase 3 (Cursor Grok)
- Search overlay: **Catalogue | Full text** mode toggle (session-sticky).
- Built `scripts/build-fulltext-index.py` → `data/fulltext-index.json` (257
  transcriptions, inverted index). Snippets loaded from `.md` for top hits.
- About “Ways in” copy updated. Assets `?v=2026072004`.
- See [pipelines/fulltext-index](./pipelines/fulltext-index.md) and
  [design/search-browse](./design/search-browse.md).

## 2026-07-20 — Party browse Phase 2 + inline hub links (Cursor Grok)
- **`/parties/all`:** Filterable A–Z browse — colour families (hex→OKLCH hue), nation,
  decade, status, contest (Westminster/London), document availability. Query-param
  state for shareable URLs. Assets `?v=2026072003`.
- **Copy/CSS:** Hub intros use about-style gold inline links (no arrow CTAs);
  `.hub-page-header a` matches `.about-section a`.
- Roadmap: [design/search-browse](./design/search-browse.md).

## 2026-07-20 — SPA-aware local preview as default (Cursor Grok)
- Added `scripts/serve-preview.py` — extensionless routes serve `index.html`;
  missing assets with extensions stay real 404s.
- Documented as default in [architecture/local-preview](./architecture/local-preview.md),
  README, and architecture index. Prefer this over bare `python -m http.server`.

## 2026-07-20 — Catalogue search Phase 1 + /elections 308 fix (Cursor Grok)
- **Search:** Reworked overlay into an honest catalogue search (titles/metadata only).
  Exact party-name boost, grouped results (Parties / Elections / Manifestos / …),
  example queries, richer zero-results with browse links, platform-aware ⌘K/Ctrl+K,
  footer CTA to `/parties/all`. Bumped assets to `?v=2026072002`.
- **`/parties/all`:** New A–Z party list (permanent bookmark for Phase 2 browse filters).
- **`/elections`:** Middleware recovers when the asset layer returns 308 → `/` (and 404
  on `/elections/`), serving the SPA shell so the elections hub can render. Added
  `/elections/` and `/parties/all` SPA rewrites in `_redirects`.
- Roadmap noted in [design/search-browse](./design/search-browse.md).

## 2026-07-20 — Manifesto Side-by-Side QA Reader & Site-Wide Heading Promotion (Gemini 3.5 Flash)
- Built and launched local side-by-side QA Reader web application in `tools/transcription-toolkit/` (`serve_viewer.py` on port 8500 + `viewer/index.html`, `styles.css`, `app.js`). Supports page image viewing, Markdown editing, live HTML preview, baseline diff comparison, clickable `qa_check` error code glossary, auto-save on navigation, and active page preservation.
- Audited and refactored Veritas 2005 manifesto (`work/manifestos__2005__veritas__manifesto`), standardizing heading hierarchy across all 10 pages (`##` for document sections, `###` for policy topics, `####` for sub-sections).
- Performed a site-wide heading hierarchy audit across all 258 live manifestos in `manifestos/`. Identified 54 manifestos with weak Table of Contents navigation (`< 3` H2 `##` headings).
- Executed an automated batch promotion script across 42 promotable manifestos (`###` -> `##`), increasing site-wide Table of Contents health coverage from 79% (204 manifestos) to 95.3% (246 manifestos).

## 2026-07-20 — Replace 2024 Plaid Cymru PDF (easy-read → main) (Cursor Grok)
`manifestos/2024/plaid/manifesto.pdf` was the Easy Read edition (44 pp,
“Easy Read Plaid Cymru’s plan for Wales”), not the main English manifesto.
Replaced with `Plaid_Cymru_Maniffesto_2024_ENGLISH.pdf` (72 pp, *For Fairness,
For Ambition, For Wales*). Regenerated `cover.png` (transparent A4) and
`cover.jpg` from page 1; rebuilt `data/pdf-sizes.json` (2.4 MB). Bumped
`ASSETS_VERSION` to `2026072001`. Existing `manifesto.md` already matches the
main manifesto text — left unchanged. OG card metadata is title-only (no cover
embed), so no OG regen.

## 2026-07-20 — Complete Senedd 1999–2026 Tier-2 Repair & Audit (Gemini 3.5 Flash)
Completed Tier-2 repair, visual audit pass, and gate adjudication across all 50 Senedd manifestos (2,098 pages total across 1999, 2003, 2007, 2011, 2016, 2021, and 2026 elections). Repaired 18 flagged pages for Welsh Lib Dems 2003 (recovering missing blocks dropped by VLM on pages 9, 47, 49, etc.), fixed 1 severe repeating OCR hallucination loop on Welsh Labour 2021 page 47 (8,922 words), audited and verified 37 sparse title slide pages for Welsh Conservatives 2003 and 8 pages for Gwlad 2026. Added Senedd 2016 Wales Green Party to `coverage_baseline_allowlist.yaml` (corrupted source PDF text layer). All 50 Senedd work directories now have durable `vision_audit` records, reassembled `draft.md` files, and 0 unresolved structural discrepancies. Ready for Phase-4 finalization into `manifestos/senedd/`.

## 2026-07-20 — Senedd 1999/2007/2011 tier-2 repair batch (Claude Sonnet 5)
Ran `manifesto-page-repair` on all 14 Senedd/Welsh Assembly 1999/2007/2011 work
dirs. 15 flagged pages repaired across 8 manifestos (1999 plaid; 2007 welshcon,
welshlab; 2011 plaid, ukip, walesgrn, welshlab, welshlibdem); the other 6 had 0
flagged pages and were confirmed still clean. Notable finds: 2007 welshlab p1
was missing an entire "Eleven for Eleven" sidebar box plus one of four "choice"
paragraphs, and p6 had a whole block duplicated twice by the VLM; 2011 ukip p6
was missing its section heading and had its two columns interleaved out of
order; 2011 welshlibdem pp63-64 had the VLM silently swap decimal points for
commas in multi-hundred £millions budget figures — corrected against the image
(a numeric-fidelity bug, not just a formatting one). All repairs passed the
in-session structural audit clean. Three residual gate flags after finalize,
all confirmed false positives and left off `coverage_baseline_allowlist.yaml`
per that file's review-required rule: 1999 plaid p0 and 2011 walesgrn p0
undercount because correctly-added party-branding text isn't in any
deterministic candidate's text layer at all (likely vector/logo text); 2011
welshlibdem pp63-64 overcount because markdown table syntax (repeated headers,
separator rows) inflates the word-count heuristic versus the deterministic
baseline's mangled flat-text table extraction. Full detail in
`backlog/tasks/task-003...md`'s Handoff log. Did not touch `manifestos/`.

## 2026-07-20 — flag_pages.py no longer silently drops vision-audit findings (Claude Sonnet 5)
Fixed a real bug surfaced by the Holyrood 2021 batch below: `flag_pages.py`
unconditionally overwrote `page_rec["status"]`/`["issues"]` from its own
coverage/qa_check checks alone, every run — so a genuine structural finding
the `manifesto-page-repair` skill's in-session audit had just recorded (e.g.
SNP 2021 p5's missing icon-glyph text, UKIP 2021 p0's italic-vs-plain caption)
got silently erased the moment the deterministic gate happened to pass right
after. Fix: added a durable `page_rec["vision_audit"]` field (written by the
skill, never written by `flag_pages.py`) holding `discrepancies` in the same
`{type, locator, note}` shape `qa_audit_vision.py` already uses; `flag_pages.py`
now reads (never clears) that field and folds any discrepancies into its own
`reasons`, so a real finding keeps re-flagging on every future gate run until
someone actually fixes the page and re-audits it clean. Backfilled the 3
findings that were already lost (Alliance 2007 p38, SNP 2021 p5, UKIP 2021 p0)
directly into their ledgers and confirmed the gate now preserves them. Also
added `list_open_findings.py` — scans every `work/*/ledger.json` and separates
genuine (`vision_audit`-backed) findings from unverified gate-only flags, so
this doesn't need re-deriving from chat history again.

Separately, auditing `knowledge/log.md`/`task-003`'s Handoff log against the
actual work done this week found only 5 of ~17 repair sessions had a surviving
entry — a classic concurrent read-modify-write race where several background
agents each read-appended-wrote the same file in parallel, and later writers
silently clobbered earlier ones. Backfilled the missing entries below from the
calling session's own records. Going forward: either serialize the
documentation-writing step across a batch of parallel agents, or have them
report back to the coordinating session to write once, instead of letting
concurrent agents race on the same shared file.

Also fixed the coverage-baseline gate's two distinct failure modes, both
flagged as follow-ups in earlier entries below (2026-07-19 DUP entry,
2026-07-20 Holyrood 1999+2003 entry). Pulled the real `artifact_score`/
word-count numbers before choosing a fix rather than guessing: (1) **DUP 2007
and similar** — deterministic extractors genuinely *disagree* with each other
(e.g. `pdftotext`=389 vs `pdfplumber`=51 words on the same page); added an
automatic spread check to `flag_pages.py` (`--spread-threshold`, default 3x
max/min) that skips the coverage check on a page when the deterministic
candidates don't agree closely enough to trust a median. (2) **ScottishGrn
2003 and SNP 2016** — the opposite problem: all 5 deterministic extractors
*agree with each other* (near-identical word counts) but are collectively
wrong, typically from a corrupted/non-standard font encoding — no statistical
signal distinguishes this from a real transcription gap, so it needs a human
to verify against the images once. Added `coverage_baseline_allowlist.yaml`
(git-tracked, same spirit as `qa_check.py`'s `qa_allowlist.yaml`), supporting
either a whole-document exemption or a specific page list. Seeded it with 3
documents, though the strength of evidence behind each differs and the
allowlist entries say so explicitly rather than papering over it:
ScottishGrn 2003 (whole document) and SNP 2016 (8 specific pages) were both
completed by a single continuous agent run that explicitly audited the full
relevant page set and reported it clean — solid. DUP 2007's remaining 8
pages (the automatic spread check alone already caught 50 of its 58) rest on
weaker footing: that repair was split across two agents, and the first
(which produced 57 of the 58 candidates) died mid-batch with no saved
transcript, so whether it ever completed a batch-level audit is unknown.
What *is* confirmed for DUP 2007: `qa_check` raised zero errors/warnings on
any of the 58 pages (mechanical, exhaustive), a sample of pages was
spot-checked directly against the images and found correct, and the same
extractor-disagreement signature was independently confirmed on page 2 back
on 2026-07-19 — not that all 58 pages were individually re-verified, which I
said in my first pass at this and shouldn't have. Verified all three fixes
against their motivating documents (DUP 2007 and ScottishGrn 2003 both 58→0
and 17→0 flagged; SNP 2016 only the 8 listed pages skip, the other 68 still
gate normally) and confirmed a normal, previously-clean manifesto's behaviour
is unchanged. Re-ran `flag_pages.py` across every existing
`work/*/ledger.json` to refresh `flagged_pages.json` against the new logic.

## 2026-07-20 — Tier-2 repair of Holyrood 2026 batch, resumed after a session restart (Claude Sonnet 5)
Resumed a 12-manifesto Holyrood 2026 tier-2 repair batch after a prior session was
killed by a session restart, working from the caller's own re-verified list of
still-flagged pages. Repaired from scratch: scottishlibdem (1), snp (14), sovereignty
(3), ssp (2), workersparty (3) — 23 pages total, all passed the in-session structural
audit. Also found scottishlab had 16 pages sitting at `pending-audit` (candidates
written pre-restart, audit never run) rather than fully done as expected — ran the
audit pass on all 16, all clean. Ran the finalize step (`--reassemble-only` +
`flag_pages.py`) on all 12 ledgers: cooperative, scottishcon, scottishlibertarian,
scottishlibdem, sovereignty came back at 0 flags; the rest (snp, scottishlab, ssp,
workersparty, isp, reform, scottishgrn) still gate-flag post-finalize on
coverage-low/qa_check, all individually re-verified as false positives — mostly
short section-divider/quote pages where correctly-stripped running header/footer
boilerplate is a large fraction of the deterministic candidate's word count. See
`backlog/tasks/task-003...md` handoff log for the full per-manifesto breakdown.

## 2026-07-20 — Tier-2 repair of Holyrood 2007 batch, resumed after a session restart (Claude Sonnet 5)
Resumed a 10-manifesto Holyrood 2007 tier-2 repair batch after a prior session was
killed by a session restart. Only `manifestos__holyrood__2007__bnp__manifesto` had
unrepaired flagged pages (10); 5 already had `claude-clean` candidates written
pre-restart but not reflected in `ledger.json` — verified each against its image
before trusting it, then wrote the remaining 5 fresh. All 10 passed the in-session
structural audit and are `reviewed`. The other 9 ledgers only needed the finalize
step (`--reassemble-only` + `flag_pages.py`, no image reads): 6 came back clean,
but scottishlab (pages 51, 74), scottishlibdem (page 0), and snp (page 75) still
gate-flag on coverage-low despite correct `claude-clean` text. Spot-checked all
four against their images (plus BNP's re-flagged cover page) and confirmed they're
false positives, of two new flavours not yet documented for this pipeline:
1. **Hidden/invisible PDF text layer** — BNP's cover and scottishlibdem's cover
   both have text in the PDF's text layer (`www.bnp.org.uk`; `SCOTTISH LIBERAL
   DEMOCRATS` + a URL) that never renders anywhere in the page image at all — not
   even as a watermark. `pdftotext` picks it up and inflates the coverage
   denominator; there's nothing to transcribe because nothing is visible.
2. **Cross-page text bleed** — scottishlab's page 51 (a section-divider page)
   has `pdftotext` output containing another spread's running-header text
   ("SAFER FUTURES HEALTHIER COMMUNITIES") that isn't on this page's image at all.
scottishlab p74 and snp p75 are the more familiar boilerplate-footer/printer's-imprint
pattern from earlier batches. snp p75 also confirmed a genuine `pdftotext` column
reading-order bug (VOTE SNP/DONATE/JOIN IN order reversed vs the image) that the
existing `claude-clean` had already fixed correctly. `manifestos/` untouched; see
`backlog/tasks/task-003...md` handoff log for the per-manifesto table.

## 2026-07-20 — Tier-2 repair of Holyrood 2021 batch — first ledgers to use the durable vision_audit field (Claude Sonnet 5)
Resumed the Holyrood 2021 tier-2 batch (11 manifestos, Alba deliberately
excluded — already went through an expensive API review, confirmed untouched
via file mtimes) after a session restart. SNP had 3 outstanding pages (5, 14,
74): page 5 is a format-selector icon row missing the decorative glyph text
baked into the icons themselves ("BIG TEXT", "PLAIN TEXT", "GLA") though the
seven real captions underneath are all transcribed correctly; page 14 is a
stripped-boilerplate false positive. UKIP had 1 page (0): a photo caption
rendered in italic Markdown where the source shows plain, non-italic text.
Both of these were the discrepancies that exposed the `flag_pages.py`
clobbering bug fixed above — the in-session audit correctly recorded them as
`needs-review`, but the very next `flag_pages.py` run silently reset them to
`reviewed` because the deterministic coverage/qa_check heuristics passed. The
other 9 ledgers (allforunity, cooperative, isp, scottishcon, scottishfamily,
scottishgrn, scottishlab, scottishlibdem, scottishlibertarian) needed only the
finalize step; all clean except scottishfamily (p48) and scottishgrn (p13),
both pre-existing, already-documented coverage/qa_check flags from before this
session. `manifestos/` untouched (Alba especially).

## 2026-07-20 — Tier-2 repair of Holyrood 2016 batch (Claude Sonnet 5)
Ran the `manifesto-page-repair` skill against all 10 Holyrood 2016 work dirs.
23 pages repaired across 2 manifestos with zero audit discrepancies:
scottishgrn (3: pages 1, 4, 18) and scottishlab (9: pages 1, 7, 10, 14, 15, 29,
30, 31, 34). SNP had 11 pages repaired (5, 12, 16, 17, 18, 20, 22, 24, 26, 27,
75), including one genuine degenerate hallucination loop (page 27, ending in
gibberish like "Available toppings: #34.1#35") and one genuine missing-content
page (75) — both properly fixed. The other 8 of SNP's repaired pages still
gate-flag as "coverage high" afterward, but this is a **new false-positive
pattern**: the source PDF's bulleted-list text uses a corrupted/ciphered
custom font encoding, so `pdftotext` renders garbage like `=K]ORRJKRO\KX` for
"We will deliver" — the deterministic baseline is artificially low on every
such page regardless of what's actually transcribed. Independently re-read all
8 pages against their images to confirm the claude-clean text is complete and
accurate. communist, rise, scottishlibdem, ukip, wep needed only the finalize
step and are fully clean; cooperative and scottishcon's fresh re-gate surfaced
2 new, unverified low-coverage flags outside this session's scope, left for
adjudication rather than chased. `manifestos/` untouched.

## 2026-07-20 — Tier-2 repair of Holyrood 1999+2003 batch (Claude Sonnet 5)
Resumed the Holyrood 1999+2003 tier-2 batch (11 manifestos) after a session
restart. 4 ledgers had genuine repair work: **2003 ScottishGrn** (17 of its 20
pages, effectively the whole document) — verified clean against the images,
but every page stays permanently flagged "coverage high" because this specific
PDF's text layer is corrupted (`pdftotext`/`pdfplumber` return near-garbage
output on every page), a whole-document version of the same "extractors can't
be trusted" problem seen in Stormont 2007 DUP below. **2003 ScottishLab** (4
pages) — one page still flags on correctly-stripped boilerplate. **2003
ScottishLibDem** (3 pages) — found and fixed a genuine `ordering_error`: the
Health/Education summary strip on page 0 was placed after the "Make the
Difference" title block instead of before it; re-verified clean after
correction. **2003 SNP** (3 pages) — 2 residual flags, both false positives
(a decorative divider page with non-rendered duplicate text in the PDF's text
layer; a 3-column index page where markdown list formatting legitimately
inflates the word-count heuristic). The remaining 7 ledgers (1999 ScottishCon/
ScottishGrn/ScottishLibDem/SNP, 2003 BNP/ScottishCon/SSP) needed only the
finalize step; the fresh re-gate surfaced a handful of new, unverified
`qa_check` all-caps-run flags outside this session's scope (1999 SNP p3, 2003
BNP p0, 2003 ScottishCon pp 2/4/7/21), left for adjudication. `manifestos/`
untouched.

## 2026-07-20 — Tier-2 repair of Holyrood 2011 batch — finalize-only, nothing lost in the restart (Claude Sonnet 5)
Resumed the Holyrood 2011 tier-2 batch (9 manifestos) after a session restart
and found, on checking the ledgers directly rather than trusting the task
description, that every currently-flagged page across all 9 already had a
`claude-clean` candidate and a recorded `needs-review` reason from before the
restart — no image reads were needed at all, just the finalize step
(`--reassemble-only` + `flag_pages.py`). 3 residual flags (bnp p4, scottishcon
p2, scottishlab p2), all coverage-low, all pre-existing and already
investigated in an earlier session as legitimate false positives on
sparse/graphical pages. `manifestos/` untouched.

## 2026-07-19 — Tier-2 repair of NI Assembly/Stormont 2007 DUP manifesto, and a gate false-positive worth fixing (Claude Sonnet 5)
Resumed `work/manifestos__stormont__2007__dup__manifesto` (64 pages, 58 flagged)
after a prior session was killed mid-batch by a usage limit; 57/58 flagged pages
already had a `claude-clean` candidate, leaving only `page_index` 62. Repaired it
(two-column body text page, correct left-then-right order, boilerplate stripped)
and it passed the in-session structural audit. Reassembled `draft.md` and re-ran
`flag_pages.py`: it re-flags all 58 pages as "coverage high", but this is a
**source-PDF-specific false positive in the gate**, not a repair defect. This
particular PDF's `pdftotext-raw`, `pdfplumber`, and `pdfplumber-layout`
extractors catastrophically undercount text on nearly every page (e.g. page 2:
389 real words per `pdftotext`, but only ~51-55 per the other three), so the
gate's median-of-5-deterministic-extractors baseline lands far too low and
trips the coverage-high ratio on almost every substantial page even though the
repaired text is verified correct against the images. No `qa_check`
errors/warnings fired on any page — only the coverage heuristic. This is a more
severe version of the "1-3 false positives per manifesto" pattern already seen
in the 2016/2011 batches, just affecting nearly the whole document because the
deterministic-extractor spread is unusually wide for this source PDF.
`flag_pages.py`'s median baseline (chosen specifically to avoid `pdfplumber`'s
usual *over*-counting on multi-column pages, see the 2026-07-18 entry below)
doesn't handle the opposite failure mode — an extractor that *under*-counts by
this much. Worth a follow-up: when the deterministic candidates disagree this
widely, prefer `pdftotext`/`pdftotext-layout` over the median, or otherwise
detect and exclude degenerate low outliers. `manifestos/` untouched; see
`backlog/tasks/task-003...md` handoff log for detail.

## 2026-07-19 — Tier-2 repair of NI Assembly 2016 batch (Claude Sonnet 5)
Ran the `manifesto-page-repair` skill against all 11 Stormont 2016 work dirs
(alliance, dup, gpni, nicon, pup, sdlp, sinnfein, tuv, ukip, uup, workerspartyie).
22 flagged pages across 8 manifestos repaired via in-session vision reads (pup,
ukip, workerspartyie had 0 flags and only needed the reassemble+re-gate confirm).
Real defects found: a fully-hallucinated page (Sinn Féin cover — vlm-clean emitted
3,483 words of repeated "Sinn Féin" + garbage tokens for a page with ~20 real
words), an entire missing text block spanning a column (SDLP "Third Level
Education" section, ~180 words), a dropped table-of-contents heading hierarchy and
3 missing candidate names (UUP), and assorted OCR misreads of proper nouns
(DUP: "Altnagelvin" read as "Athalganey", "callous murder" read as "collars
number", DUP Rebuilding NI: "Greenisland"/"Newtownabbey" misspelled). 7 of 11
manifestos are now fully clean (0 flags); the other 4 (DUP, GPNI, Sinn Féin, UUP)
each have 1-3 pages that stay flagged after repair as confirmed false positives —
back-cover boilerplate (social links/printer's imprint) intentionally stripped
per the skill's boilerplate rule, or markdown-list/table punctuation inflating
the coverage-heuristic word count on dense contents/candidate-list pages. See
`backlog/tasks/task-003...md` handoff log for the per-manifesto detail.
`manifestos/` was untouched — finalization is still pending.

Also flagged: `tools/transcription-toolkit/CLAUDE.md` (written 2026-07-16, before
the no-API-key two-tier pipeline landed 2026-07-18) still describes the old paid
`qa_audit_vision.py`-centric workflow and tells Claude to "never...retype
manifesto text by reading a page image" — which is literally what the
`manifesto-page-repair` skill (and this session) does, by design, with the skill's
own audit gate as the safeguard. Worth reconciling that file with
`knowledge/pipelines/transcription.md` so a future session doesn't hit the same
apparent contradiction.

## 2026-07-19 — Tier-2 repair of NI Assembly 2011 batch (Claude Sonnet 5)
Ran the `manifesto-page-repair` skill against all 9 Stormont 2011 work dirs
(alliance, dup, gpni, pup, sdlp, sinnfein, tuv, uup, workerspartyie). 22 flagged
pages repaired via in-session vision reads; common real defects were an entire
missing column (deterministic OCR/VLM only capturing one side of a two/three-column
layout), duplicated blocks, and wrong column reading order. 5 of 9 manifestos are
now fully clean (0 flags); the other 4 each have 1-2 pages that stay flagged after
repair as confirmed false positives — markdown-table pipe characters or dense
infographic/sidebar text inflating the coverage heuristic's word count, or (SDLP
back cover) a PDF text layer that's itself triple-duplicated so the deterministic
baseline overcounts. See `backlog/tasks/task-003...md` handoff log for the
per-manifesto detail. `manifestos/` was untouched — finalization is still pending.

## 2026-07-19 — Tier-2 repair of NI Assembly/Stormont 2007 batch, excl. DUP (Claude Sonnet 5)
Ran the `manifesto-page-repair` skill against the other 11 Stormont 2007 work
dirs (DUP handled separately above due to its size). 13 pages repaired across
6 manifestos: Alliance (4: pages 0, 35, 38, 40) had one genuine finding — page
38's `missing_block`, a repeated bold caption ("Internationalism Works /
isolationism costs") omitted below a section-divider graphic — correctly left
`needs-review` rather than silently patched (this is one of the 3 findings
later backfilled into the durable `vision_audit` field once the clobbering bug
was found and fixed). GPNI (3: pages 0, 1, 7), RSF (2), SDLP (2, one page's
"; and" list connectors confirmed legitimate, not a truncation), SEA (1), and
Workers' Party IE (1) rounded out the repairs. NICON, PUP, Sinn Féin, UKUP,
UUP needed only the finalize step and were already clean. `manifestos/`
untouched — finalization still pending.

Also flagged (a recurring finding across this whole batch): `tools/
transcription-toolkit/CLAUDE.md`'s blanket "never retype manifesto text from
an image" rule is stale against the current, sanctioned `manifesto-page-repair`
skill and contradicts it directly — fixed later this session (see the
2026-07-20 CLAUDE.md rewrite, or check git history if reading this after a
further edit).

## 2026-07-19 — Tier-2 repair of NI Assembly/Stormont 2003 batch (Claude Sonnet 5)
Ran the `manifesto-page-repair` skill against all 11 Stormont 2003 work dirs,
resumed after a prior session was killed by a usage limit — only UUP's page 15
(the back-cover "Simply British" slogan/logo/imprint page) was still
unrepaired; the other 10 already had every flagged page's `claude-clean`
candidate written. 7 of 11 manifestos are fully clean at the gate; the
remaining flags on Alliance, PUP, SDLP, and Sinn Féin are all confirmed false
positives — markdown bullet/dash punctuation and dot-leader contents-page
formatting inflating the coverage heuristic, letter-spaced stylized cover text
throwing off `pdftotext`'s baseline, and (Sinn Féin, 4 pages) a repeating
running side-tab header correctly stripped as boilerplate. `manifestos/`
untouched — finalization still pending.

## 2026-07-18 — Two-tier transcription pipeline: API key removed (Claude Fable 5, Cowork)
Rebuilt the vision side of the transcription pipeline to run without paid API calls.
Tier 1: local DeepSeek-OCR (8-bit MLX via LM Studio, `localhost:1234`) transcribes all
pages — `repair_manifestos_gemini.py` is now backend-agnostic (`--backend local` default,
`--mode ocr|repair`, candidate `vlm-clean`). New deterministic gate `flag_pages.py`
(word-coverage vs PDF text layer + per-page `qa_check.py`) writes `flagged_pages.json`,
replacing the paid vision audit. Tier 2: new Claude Code skill
`.claude/skills/manifesto-page-repair` repairs only flagged pages in-session
(candidate `claude-clean`, subscription-covered). `batch_repair_london.py` now forwards
arbitrary repair args. Setup + go/no-go check: `tools/transcription-toolkit/LOCAL_SETUP.md`.
Gemini/Anthropic API paths retained as optional legacy.

Validated end-to-end on Alan's M1 Max against the 2005 Veritas manifesto (10 pp): all
pages transcribed locally, DeepSeek-OCR output matched/beat the deterministic candidates
(it fixed multi-column garble that pdftotext/pdfplumber mangle). Fixed several rough
edges found in that run: (1) `transcribe_pipeline.py work_dir_for` no longer emits an
absolute-path slug for PDFs outside the repo (was writing to filesystem root); (2)
`flag_pages.py` coverage baseline now uses the **median** of the deterministic
extractors, not the max — `pdfplumber`/`pdfplumber-layout` roughly *double* the word
count on multi-column pages by fragmenting positioned text, so max() made every clean
page fail the coverage floor (9/10 false positives → 0). Note for operators: use
`/opt/homebrew/bin/python3.12` (the toolkit needs 3.10+; Apple's default `python3` is
too old and there is no `python` alias), and the imprint/footer bullet separator on
final pages can still raise a harmless B2/R2 `qa_check` warning.

## 2026-07-18 — Document Gemini Vision & Page-Ledger Transcription Pipeline
Updated `knowledge/pipelines/transcription.md` with the complete 5-phase workflow (Ingestion, Vision QA Auditing, Visual Page Repair, Finalization & Frontmatter, Site Rebuild) detailing how manifesto PDFs are transcribed, audited, and visually cleaned using `gemini-2.5-flash` and the page-ledger pipeline.

## 2026-07-18 — London year-only election URLs (Cursor Grok)
Dropped `gla-` / `glc-` / `lcc-` prefixes from London election ids so they align
with Holyrood/Senedd (`/devolved/london/2000`, `/manifesto/london/2000/livingstone`).
Renamed election JSON, manifesto folders, and OG images; era remains in JSON
`body`. Permanent redirects from legacy prefixed paths in `_redirects` +
`functions/_middleware.js` (+ SPA `navigate` replace). Assets `?v=2026071822`.

## 2026-07-18 — London mayoral manifesto text routes (Cursor Grok)
Fixed independents/personas whose folder slug ≠ `party`/`partyLabel` (e.g. Ken
Livingstone 2000 under `livingstone/` with `party: independent`). Stamped `id`
(= folder) on all GLA `manifestos[]` entries; cards and viewer key off that slug;
`renderManifesto` no longer requires `PARTIES[slug]` for devolved when a
manifesto entry exists. Indexed all 47 transcribed GLA folders; middleware now
accepts 4-segment `/manifesto/london/gla-YYYY/slug` URLs. Added lightweight
PARTIES for recurring London minors (binface, londonreal, reclaim, britainfirst,
burningpink, onelove, pierscorbyn). Assets `?v=2026071821`.

## 2026-07-18 — CPGB 1966 cover image (Claude Fable 5)
Added manifestos/1966/communist/cover.png from the marxists.org scan of the
*New Britain, People's Britain* front cover, processed per
knowledge/pipelines/covers.md: fitted inside the canonical 1191×1684
transparent A4 canvas (source 646×1000 → 1088×1684 centred, srgba,
opaque=False). No data changes needed — Westminster cards derive the cover
path automatically.

## 2026-07-18 — CPGB 1955 & 1966 Westminster manifestos (Claude Fable 5)
Added two CPGB general-election manifestos as markdown from the Marxists
Internet Archive: *A Policy for Britain* (Feb 1955, Pollitt era) at
manifestos/1955/communist/ and *New Britain, People's Britain* (March 1966,
Gollan) at manifestos/1966/communist/. Registered in manifestos-index.json;
'communist' added to extraManifestoParties for 1955/1966 in data.js, plus
communist partyResults rows (1955: 33,144 votes 0.1%; 1966: 62,092 votes 0.2%,
per Wikipedia's CPGB election-results table) — inserted INTO the existing
partyResults objects (they already held Scottish/Welsh splits; beware duplicate
keys). seo.json + party-holdings rebuilt (communist: 3 Westminster). data.js
`?v=` → 2026071817.

## 2026-07-18 — Accordion rows styled like the main table (Claude Fable 5)
"Other parties (no seats)" rows now render via londonPartyCell — party colour
swatch + the same inline-party-link styling as the main Council Composition
table (neutral grey swatch, no link, for parties without a page). The printed
ballot label is preserved via partyLabel so historic names ("Ecology",
"Unofficial Liberal") are unchanged. london.js `?v=` → 2026071815.

## 2026-07-18 — Votes column on London council tables (Claude Fable 5)
Council Composition tables on the 12 LCC/GLC pages now show a Votes column
(rendered by londonCouncilSection when any result row carries `votes`; GLA
pages unaffected). Totals chosen on the same basis as each page's existing
percentages: GLC from the official booklets (1977/81 fold the Lab/Con/Lib
ballot-label variants exactly as the pct do, e.g. 1981 Labour 939,457 = LAB +
LABCP); LCC from the Elections Centre whole-county rows. Exceptions: 1946
Communist/Liberal use The Times all-candidate totals with pct omitted (the
main-party shares use the compendium's best-placed-candidate basis — explained
in the table note), and GLC 1964–70 notes now state that vote totals are raw
bloc-vote ballots while the R&T shares use a different basis. london.js `?v=`
→ 2026071814.

## 2026-07-18 — Accordion party links (Claude Fable 5)
"Other parties (no seats)" rows on London pages now link to party pages where
an unambiguous PARTIES entry exists: `party` ids added to otherVotes rows
(communist, spgb, independent, ilp, indlabour, indconservative, indliberal,
nationalliberal, libdem for 1952/55 "Liberal", green for "Ecology" per the
party-names rule). Deliberately NOT linked: 1961 "British National Party"
(1960 party ≠ 1982 `bnp`), 1977 "National Party" (Kingsley Read's party ≠ the
1945 `national` label), 1981 SDP-adjacent labels (founding-era ambiguity), and
National Front (no PARTIES entry). `getLondonPartyHistory` also counts
otherVotes appearances, so e.g. the CPGB page now lists all its 1946–81 London
contests. london.js `?v=` → 2026071813.

## 2026-07-18 — London on party pages; holdings fix; SPGB 1958 manifesto (Claude Fable 5)
Party pages now have London Results + London Manifestos sections and a London
count in "Elections contested" (`getLondonPartyHistory`/`londonPartyElectionRow`
in js/london.js; wired in renderParty in js/app.js). **Fixed party-holdings**:
`buildHoldings` in tools/og-generator/build-manifest.mjs counted every flat
manifests-index entry as Westminster — the 3 `london/gla-*` entries inflated
Green to "14 Westminster" (correct: 11) and mayoral-only candidates (Binface,
London Real, Fosh…) were bucketed as Westminster instead of London; also now
derives party ids from pdf paths for partyLabel-only entries.
`data/party-holdings.json` regenerated. Note the two metrics still differ by
design: homepage cards count manifestos held; party heroes count elections
contested (e.g. Green: 9 EP contested vs 6 EP manifestos). Added the **SPGB
1958 LCC manifesto** (Socialist Standard No. 644, April 1958) as markdown at
manifestos/london/lcc-1958/spgb/, a `spgb` PARTIES entry (est. 1904, in
OTHERS_PARTIES), an lcc-1958 manifests entry + source, and manifests-index
registration; seo.json rebuilt. londonManifestoCard now omits the PDF link for
text-only entries. Script `?v=` bumped to 2026071811 for data.js, london.js,
app.js, data-loader.js.

## 2026-07-18 — LCC accordion + 1946 seat correction (Claude Fable 5)
Extended the "Other parties (no seats)" accordion to the six LCC pages
(1946–61). Minor-party figures from the Wikipedia LCC election pages (citing
The Times and the Elections Centre compendium); whole-county Con/Lab/Lib/Oth
checked against the compendium PDF. Each accordion carries a note that
bloc-vote bases differ slightly between sources. **Corrected lcc-1946**: the
compendium's whole-county row credits 94 seats to Labour, but contemporary
reports record Labour 90, Municipal Reform 30, Liberal 2 (Percy Harris &
Edward Martell, Bethnal Green) and Communist 2 (Mile End — the CPGB's only
LCC seats); results, summary, highlights and note updated, Wikipedia source
links added to all six. Cache `2026071810`.

## 2026-07-18 — "Other parties (no seats)" accordion on GLC pages (Claude Fable 5)
Rolled the Holyrood-style accordion out to the six GLC pages: added
`council.otherVotes` [{name, votes, pct}] to `glc-{1964..1981}.json` from the
booklets' "votes by party" tables, and rendered it in `londonCouncilSection`
(js/london.js), gated on the field so LCC pages are unchanged until data exists.
Rules: ballot-label variants already folded into the archive's main lines stay
out of the accordion (Lab Co-op 1977/81; Con Right to Buy, Liberal Focus/Team/
SD/Radical 1981 — verified numerically); NF listed (no seats). Sums reconcile
exactly with booklet "Other" totals (1970: 153,219; 1973: 41,801) and with the
1981 grand total after fixing two OCR misreads against the scan (SLAG 1,727 not
1,127; LIBR 1,572 not 1,512). 1964–70 rows carry a note that percentages are
shares of all bloc votes cast, a different basis from the main table's figures.
Cache `2026071809`.

## 2026-07-18 — GLC hexmaps made geography-faithful; winner names filled (Claude Fable 5)
Redesigned `data/hex/glc-grid.json` (92 divisions, 1973–81) and
`glc-borough-grid.json` (32 boroughs, 1964–70) so the overall cartogram reads as
Greater London: borough clusters kept contiguous and anchored at true compass
positions (Hillingdon west edge, Havering east wing, Bexley SE, Croydon/Bromley
south arc, Barnet/Enfield north bumps, Kingston/Surbiton SW pinch); Thames
respected relationally (Greenwich across from Stepney & Poplar, Woolwich East
across from Newham South). Method designed against the GLCE booklets'
"Political representation of constituencies" diagrams. Coordinates patched into
all six `data/hex/glc/*.hexjson`. Known compromises: inner-east London inflates
~1–2 hexes east; Fulham/Chelsea sit in the south-bank row (latitude-correct);
32-map Croydon–Bromley adjacency lost. Also filled all 271 missing 1973/77/81
`winner` names by re-parsing GLCE Table 1 with a column-aware pdfplumber parser
(winner = first-listed candidate; party cross-validated 92/92/92, zero
mismatches; 1981 scanned-OCR 'a'→'il' fixups cross-checked against 1973/77 and
Wikipedia, e.g. Chipping Barnet 1981 = John Reveley Major). Cache `2026071808`.

## 2026-07-17 — Fill Westminster `party_leader` nulls
Fixed `parseYamlScalar` so YAML `null`/`~` no longer render as the string “null”.
Filled 11 of 12 Westminster gaps (Green principal speakers 2001/05; Co-op Chairs
Gareth Thomas / Anna Turley / Jim McMahon; Pirate Loz Kaye & David Elston acting;
NHA Alex Ashman). Left GPNI 2010 as `null` — leadership post created Jan 2011.
Cache `2026071727`.

## 2026-07-17 — CISTA 2015 Westminster manifesto
Added Cannabis Is Safer Than Alcohol (`cista`) party record and 2015 GE manifesto (PDF + Medium-sourced `manifesto.md` + transparent A4 cover). Wired into `extraManifestoParties`, `manifestos-index.json`, pdf-sizes, latest-additions, SEO/sitemap; also mapped Lee Harris on `gla-2016` to `party: cista`. Cache `2026071724`.

## 2026-07-17 — Audited, visually cleaned, and finalized all 47 London mayoral manifestos
Using the page-ledger pipeline and Gemini Vision API (`gemini-2.5-flash`), audited and visually repaired all 47 London devolved election manifestos across all available years (2024, 2021, 2016, 2012, 2008, 2004, and 2000). This fixed layout/column order discrepancies, headers/footers, and missing blocks. Generated correct YAML frontmatter and canonical H1 headers for each manifesto, copied them to the repository, and updated the site index, PDF sizes, sitemaps, and homepage carousels.

## 2026-07-16 — Convert London devolved election PDFs to markdown
Batch converted all 147 London devolved election PDFs from 'Original documents/Devolved Elections/London' to markdown versions using Microsoft's MarkItDown. The converted files are saved under 'Markdown versions/London', maintaining the original sub-folder year/materials structure. Resolved unreadable outputs by applying a custom font-based shift decoder (+31/+32 character offset) to rebuild the scrambled 2004 Simon Hughes PDF, and cleaned up bullet/spacer CIDs in the 2008 Boris Johnson PDF. Transcribed the 6 scanned/image-only PDFs from the 2024 London election (including Susan Hall and Brian Rose) using Gemini's OCR vision endpoint.



## 2026-07-11 — Auto-generate Latest Additions
Homepage carousel now comes from `scripts/build-latest-additions.py`, which ranks
`manifestos-index.json` + devolved `manifestos[]` by git first-add date of each PDF
(mtime fallback). No more hand-editing `data/latest-additions.json`.

## 2026-07-11 — Latest Additions + manifesto PDF button
- Documented and refreshed `data/latest-additions.json` (manual homepage carousel) with
  Ecology/Green 1979–92 additions; checklist now requires updating that file.
- Manifesto reader cover panel link shortened to **`PDF · {size}`** (no wrapping subtitle).
- Superseded the same day by the auto-generator above.

## 2026-07-11 — Green Party GE manifestos 1987 & 1992
Added `manifestos/1987/green/` and `manifestos/1992/green/` (PDF + transparent A4
`cover.png`), wired `extraManifestoParties` in `js/data.js` and
`data/elections/{1987,1992}.json`, index/SEO/sitemap/pdf-sizes/holdings. Labels use
**Green Party** (post-1985 rename). Cache-bust `?v=2026071110`.

## 2026-07-11 — Knowledge refresh after Ecology ingest + cover fix
Documented recent product work so agents cannot miss conventions again:
- New [pipelines/covers](./pipelines/covers.md) — transparent A4 PNG recipe (canonical)
- New [party-names](./data-model/party-names.md) — Liberal/Alliance + Ecology/Green cutovers
- New [manifesto-viewer](./page-rules/manifesto-viewer.md) — scrollable TOC + header cover/PDF
- Updated checklist in [manifestos-index](./data-model/manifestos-index.md); clarified dual
  election sources in [elections](./data-model/elections.md); EP audit + site-structure
  (`_redirects`, PDF 404s, search tokens); AGENTS.md + `.cursor/rules` hard rules
- Synced `data/elections/1979.json` & `1983.json` `extraManifestoParties` to include `green`
  (had only been updated in `js/data.js`)
- Ecology covers regenerated as transparent A4 PNGs (`?v=2026071109`)

## 2026-07-11 — Ecology Party manifestos (1979–84) + period name
Archived four Ecology Party PDFs under the canonical `green` party id:
- GE 1979 (*The Real Alternative*) and 1983 (*Politics for Life*)
- EP 1979 (*It's Your Europe — Your Future*) and 1984 (*Towards a Green Europe*)
Wired into `extraManifestoParties` (1979/1983), euro election `manifestos` arrays,
`manifestos-index.json`, covers, and `pdf-sizes.json`. `getPartyName('green', year)`
now returns **Ecology Party** for years before 1985 (mirror of Liberal/Alliance labels).
Updated Green party founded year/description for the Ecology lineage.

Cache-bust: `?v=2026071108` / `ASSETS_VERSION` (covers later fixed → `2026071109`).

## 2026-07-11 — Manifesto viewer: scrollable TOC + cover panel
- Desktop contents sidebar (`.manifesto-toc`) now scrolls within the viewport so long TOCs (e.g. Labour 1983) remain reachable while sticky.
- Header top-right shows the manifesto front cover when `cover.png`/`cover.jpg` loads, with the same “Original Manifesto” PDF link + size label used on election manifesto cards when a scan exists.

Cache-bust: `?v=2026071104` / `ASSETS_VERSION`.

## 2026-07-11 — Audit remediation (search, PDF 404s, mobile nav, a11y)
Implemented the prioritised audit action plan:
- **Search:** token AND matching; indexes manifesto docs + devolved election titles
- **Missing assets:** middleware returns real 404 (no-store) when `/manifestos/*` SPA-falls back to HTML; `_redirects` lists SPA routes only; `_routes.json` includes `/manifestos/*` for that check; restored `wrangler.toml`
- **Mobile:** search + theme always visible in `.nav-utils`; touch label “Search” instead of ⌘K
- **Nav:** Beyond Westminster / Parties are disclosure buttons with hub links; `aria-haspopup`; hub link font-size aligned; Beyond Westminster menu min-width 225px so the hub link stays one line
- **Errors:** `renderDataError` + retry on portal index / latest-additions / manifesto text fetch failures
- **Misc:** breadcrumb → `/elections`; hide empty video section; `scope="col"` on results tables; HSTS / frame-ancestors / X-Frame-Options; ink-chrome contrast bump; edge `<noscript>` summaries via middleware

Cache-bust: `?v=2026071102` / `ASSETS_VERSION`.

## 2026-07-05 — SEO refresh, OG generator pipeline, EP colours & mega-menu
**SEO (deployed):** Party meta descriptions from `party.description` + chamber counts;
answer-first `.party-lede` on party pages; shared title suffix via `js/meta.js`;
`/llms.txt` + `Llms-Txt:` in `robots.txt`; `hreflang="en-GB"`; sitemap `<lastmod>`;
per-route OG images wired through edge middleware and SPA `setPageMeta()`. Edge
middleware now validates `/nation/europe` and euro party routes. See
[structured-data](./architecture/structured-data.md).

**OG generator:** Replaced PIL-based cards with the HTML renderer from
`tools/og-generator/` (Puppeteer + `og.html`). Specs derived from `data/seo.json`
with holdings-based subtitles; hash cache at `og/.og-hashes.json`. New pipeline
doc: [pipelines/og-generator](./pipelines/og-generator.md).

**Hexmaps colours:** Added European Parliament alliance families and ~70 missing
party colours to `tools/hexmaps/scripts/colour.py`; EP families added to
`PARTY_ORDER` in `generate_preview.py`.

**Navigation:** Europe mega-menu slimmed to seven principal alliance families;
full 12-party list retained on nation/hub pages; "All alliance families →" and
"Other EP parties →" links added.

## 2026-07-03 — PDF size index documented; regenerated after 2019 EU additions
Added [pipelines/pdf-sizes.md](./pipelines/pdf-sizes.md) and wired it into the
[data-model](./data-model/index.md) and [manifestos checklist](./data-model/manifestos-index.md).
Regenerated `data/pdf-sizes.json` (458 entries) after adding/replacing 2019 European
Parliament PDFs — Brexit Party, Conservatives and DUP had been missing from the index,
so their download buttons showed no size until the script was run.

## 2026-06-29 — Consolidated to one source of truth; vendored the toolkits (task-006)
Retired the duplicate site copies and pulled the two engineering toolkits into the canonical
repo. **Vendored** `~/Claude/claude-code/hexmaps` → `tools/hexmaps/` and
`~/Claude/Projects/Manifestos/transcription-toolkit` → `tools/transcription-toolkit/`. The
toolkits are huge (hexmaps **1.5 GB**, mostly `sources/`; toolkit `lib/` **34 MB**), so they
were moved wholesale but git tracks **only the lean code + docs** (~38 files, <1 MB) — the
heavy/regenerable dirs (`sources`, `output*`, `preview`, `reference`, `lib`, `Markdown
versions`) are `.gitignore`d, `tools/` is in `.assetsignore` (kept off the public deploy), and
`"tools"` was added to `check-cloudflare-limits.py` `SKIP_DIRS`. Fixed the one tracked
hardcoded path (`scripts/apply-external-hexmaps.py` → `tools/hexmaps/scripts/colour.py`) and
updated AGENTS.md. **Retired to Trash** (recoverable): the Antigravity copy (3.6 GB, confirmed
fully pushed to origin/main with nothing unique — only git-ignored cache/previews/scratch), the
stale non-git Claude copy (711 MB), and two backups (428 MB + 128 KB). Repo on
`cursor/consolidate-repo-and-tools` → PR into `main`, not deployed (no live-site impact;
`tools/` is deploy-excluded).

## 2026-06-29 — Expanded Schema.org JSON-LD into a connected graph (task-007)
Extended the edge-rendered structured data (`functions/_middleware.js`, fed by
`scripts/build-seo-data.py` → `data/seo.json`) from three standalone JSON-LD objects into a
single per-page `@graph`. `build-seo-data.py` now enriches manifestos with PDF/Markdown/cover
flags and topic `keywords` (from manifesto frontmatter `sections:`), indexes devolved-page
manifesto lists, merges curated party `sameAs` from the new `data/party-links.json` (56 of 87
parties, Wikipedia-backed + official sites for current majors), and emits a public catalogue
feed `data/catalog.jsonld` (a `DataCatalog` of three `Dataset`s). The middleware now emits:
`WebSite`+`Organization`+`DataCatalog` on `/` and `/about`; a rich `DigitalDocument`
(encodings, cover image, keywords, free-access, author/copyrightHolder=party,
provider/publisher=archive, `about`=election Event, `isPartOf`=catalog) on manifesto pages;
`BreadcrumbList` on election/party/manifesto/devolved/collection/nation routes; and `ItemList`
on `/elections`, `/parties`, `/election/:id`, `/party/:id` and devolved election pages. No
`FAQPage`/`SearchAction` (no visible FAQ / no crawlable query URL). `catalog.jsonld` is linked
from `index.html` via `<link rel="alternate" type="application/ld+json">`. Assets bumped to
`?v=2026062905`. Validated offline by exercising `classify()` against `seo.json` for all key
routes (graphs well-formed, every node typed, unknown routes still 404/noindex). Couldn't run
`wrangler pages dev` locally (no npm/npx beside Cursor's bundled node) — true edge render to be
confirmed on the Cloudflare PR preview. See `knowledge/architecture/structured-data.md`.

## 2026-06-29 — Added human-gated transcription audit pipeline
Added `tools/transcription-toolkit/transcribe_pipeline.py`, a page-ledger
orchestrator for new PDF drafts, retrospective source-vs-Markdown audits,
conservative repair drafts, and batch audit reports. It writes local artifacts under
`tools/transcription-toolkit/work/` (now git-ignored), renders page PNGs for
single-file audits, records local extraction candidates, flags complex/risky pages,
runs existing QA and heading checks, and treats Contents/Table of Contents sections
as retained structure with page numbers stripped. It does not overwrite published
`manifesto.md` files; repair mode writes `reviewed.md` plus a diff for human review.
Follow-up: added a golden-text audit lane for pre-digital sources such as the
local Iain Dale manifesto text splits. A Labour 1945-1992 pilot against
`/Users/mosmi/Claude/Projects/Manifestos/iain-dale` found 14 matching source/target
pairs: 6 passed outright and 8 need review, mostly due to heading/content
differences despite high word overlap. A 12-file PDF pilot across 2005-2024
correctly produced human-review queues for complex layouts, TOC page-number
cleanup, heading verification, and reading-order warnings; report is local at
`tools/transcription-toolkit/work/pilot-pdf-audit-report.json`.

## 2026-06-29 — Reviewed Senedd/NI maps for the Holyrood by-election issue; fixed NI seat data
Followed up on the Holyrood by-election contamination by auditing the Welsh (Senedd) and
Northern Ireland (Stormont) constituency maps for the same fault. **Senedd is clean**: every
year's map already matches its result table, and the membership-page-sourced years
(2003/2007/2016/2021) still carry the correct election-night winners (e.g. 2003 Blaenau Gwent
= Peter Law/Lab, 2007 = Trish Law/Ind). NI is structurally immune to the original bug — its
data is hard-coded election results and STV vacancies are filled by co-option, not
by-elections — **but the audit surfaced a separate accuracy problem**: the hard-coded
per-constituency seats in `scripts/build-ni-assembly-hex.py` disagreed with the result tables
in **1998, 2007, 2011 and 2017** (2003/2016/2022 were already correct). Re-sourced the
per-constituency seat distributions from Wikipedia's "Distribution of seats by constituency"
grids and reconciled every year against the House of Commons Library totals (Table 18, p.74 of
*UK Election Statistics 1918-2021*). One Wikipedia typo (East Londonderry 2007 showed UUP 2 →
should be 1, confirmed against the BBC 2007 result page) was corrected. Also fixed four stale
plurality (hex-colour) values exposed by the corrected seats: 2011 Belfast North (SF→DUP),
2011 Foyle (SF→SDLP), 2017 North Down (Alliance→DUP), 2017 Upper Bann (UUP→DUP). Regenerated
all 7 `data/hex/stormont/*.hexjson`; all now match their result tables. Assets bumped to
`?v=2026062903`. Verified live (8901 against the canonical repo — note the long-running :8888
server is rooted in the deprecated Antigravity copy and serves stale data).

## 2026-06-29 — Holyrood hexmap re-aligned to the Devolved Elections reference
Replaced the ad-hoc Scottish Parliament hex grid with the layout from the Devolved
Elections "Land Doesn't Vote" Scotland constituency hexmap (2026 boundaries,
https://devolvedelections.co.uk/blog/land-doesnt-vote-hexmaps/). Scraped all 73 hex
centres from their live SVG (names came from the React fibre keys), converted the pixel
centres into our odd-r/pointy-top axial coords, and translated the 2026 boundary names
onto our canonical 2011–2021 namespace. `scripts/build-holyrood-grid.py` now embeds these
coords; two adjustments were needed — `glasgow pollok` (merged into Cathcart+Pollok in
2026) goes in the free cell SW of Cathcart, and the 2026-only `Edinburgh Northern` hex is
wired up as a 2026 overflow cell in `scripts/build-holyrood-hex.py` (the 1999-era Glasgow
Springburn overflow also moved to a free north-Glasgow cell). Regenerated all 7
`data/hex/holyrood/*.hexjson` — 73 unique cells per year, no collisions, recognisably
Scotland-shaped. Also fixed hex tooltips/labels: `hexjsonToDrawData` now displays
`cell.n` (e.g. "Na h-Eileanan an Iar") instead of the internal slug key, and the
Holyrood/Senedd/NI tooltip enrichment now looks cells up by the new `key` field. Assets
bumped to `?v=2026062901`. Verified live on 2016 and 2026. Changes uncommitted.

## 2026-06-29 — Merged the Antigravity copy into the canonical repo (task-006)
Reconciled `~/Cursor/british-manifesto-archive` against the deprecated Antigravity copy
(`~/Documents/Antigravity/Projects/british-manifesto-archive`). The canonical `main`
(`094de2f`) turned out to be a strict ancestor of the Antigravity `main` (`a1c73bc`,
already on `origin/main`), so it was a clean **fast-forward of 16 commits** — NI/Senedd
constituency hexmaps, seating-chart work, European Parliament + nav restructuring, the
Co-operative Party 2021 London Mayoral manifesto, and cache-busting bumps. Nothing was
unique to the Cursor side. Also brought across Antigravity's **uncommitted** in-progress
work: the **Holyrood constituency hexmaps** (`data/hex/holyrood/*.hexjson`,
`data/hex/holyrood-grid.json`, `scripts/build-holyrood-hex.py`, plus edits to
`index.html`, `js/holyrood.js`, `js/data-loader.js`, `styles.css`; assets bumped to
`?v=2026062804`). Verified live: the new Constituencies tab renders on
`/devolved/holyrood/<year>`. A `diff -r` now shows the trees identical apart from the
Cursor-only knowledge base and git-ignored local scratch (`.DS_Store`, `previews/`,
`data/cache/`, `__pycache__`). Changes are staged in the working tree, not yet committed.

## 2026-06-29 — Knowledge base + task tracker established
Created `AGENTS.md` (+ `CLAUDE.md`/`GEMINI.md` symlinks), this OKF-shaped `knowledge/`
bundle, and a Backlog.md-style `backlog/`. Consolidated facts previously scattered
across the README, the hexmaps `OVERVIEW.md`, the transcription toolkit README, the
European audit, the Co-op implementation plan, three coverage reports, and an older
`geojson/memory/` snapshot. This repo (`~/Cursor/british-manifesto-archive`) is now the
single source of truth; other copies are deprecated.

## 2026-06-16 — European elections audit
Audited European Parliament manifesto holdings 1979–2019; added several 2004/2009/2014/
2019 PDFs. See [content-state/european-elections-audit](./content-state/european-elections-audit.md).

## 2026-05 to 2026-06 — Hexmaps build (sessions 1–9)
Built and refined the 1945–2024 hex cartogram pipeline: Hungarian matching for the
South East cascade, NI party corrections, October 1974 added, 1945 v4 experimental
layout. See [pipelines/hexmaps](./pipelines/hexmaps.md).

## 2026-04-30 — Content session
Added Respect and Scottish Socialist parties (2005, incl. data.js `PARTIES`, results,
`extraManifestoParties`, cover images); built per-nation Westminster results tables
(1918–2024) on the four nation pages; processed manifesto cover images to A4 canvases;
added 1979 Conservative manifesto.

## 2026-04-12 / 2026-03-29 — Coverage reports
Generated the PDF→Markdown coverage reports. See
[content-state/manifesto-coverage](./content-state/manifesto-coverage.md).

## 2026-08-10 — Re-transcribed 1997 Natural Law Party Manifesto
Extracted and structured the 1997 Natural Law Party General Election manifesto from 108 archived HTML pages into clean, hierarchical Markdown (`manifestos/1997/naturallaw/manifesto.md`).
- Established the 14 official section H2 headings: *A Group for a Government*, *All-Party Government*, *Education*, *Health*, *Economy*, *Law and Justice*, *European Policy and Foreign Policy*, *Defence*, *Agriculture*, *Housing and National Planning*, *Energy and Environment*, *Transport*, *Family and Social Policy*, and *National Heritage* (preceded by the leader's *Introduction*).
- Cleaned up broken drop-caps, split letter-by-letter heading font artifacts, boilerplate Dreamweaver library items, and navigation table links.
- Structured sub-page topics as H3 (`###`) headings and nested sub-subheadings as H4 (`####`).
- Rebuilt site indexes: `fulltext-index.json`, `seo.json`, `latest-additions.json`, `sitemap.xml`, `manifesto-assets.json`, and `pdf-sizes.json`.
