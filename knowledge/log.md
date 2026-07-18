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
