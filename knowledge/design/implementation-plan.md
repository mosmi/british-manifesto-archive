---
type: plan
title: Site design implementation plan
description: Phased visual and UX refresh for manifestos.org.uk — tokens, manifesto reader, cards, light mode.
tags: [design, ui, accessibility]
timestamp: 2026-07-05T21:00:00Z
---

# Implementation plan — site design amends for manifestos.org.uk

Companion to the mockups in `Site Redesign.dc.html` (ids 1a–1e) and the OG system
in `tools/og-generator/`. Ordered by impact; each phase ships independently.

---

## Phase 0 — Design tokens, typography, shared data (prerequisite for everything else)

Centralise the palette as CSS custom properties. Current problem: content text is
too dim (much of it below WCAG AA on `#090e1c`).

```css
:root {
  --field:        #090e1c;   /* page background */
  --surface:      rgba(255,255,255,0.025);  /* cards */
  --hairline:     rgba(217,183,106,0.15);   /* dividers */
  --ink:          #f4f1e8;   /* headings, emphasis (cream) */
  --ink-body:     #aeb6c4;   /* body/secondary — MINIMUM for content text */
  --ink-muted:    #8a93a3;   /* metadata, dates */
  --ink-chrome:   #6b7484;   /* footers, timestamps ONLY — never content */
  --gold:         #d9b76a;
  --paper:        #f7f3ea;   /* reading surface + light mode field */
  --texture-opacity: 0.025;  /* body noise overlay — 0 in light mode */

  /* Typography (Option A — site-wide) */
  --font-display: 'Playfair Display', Georgia, serif;
  --font-body:    'Source Serif 4', Georgia, serif;
  --font-ui:      'Public Sans', system-ui, sans-serif;
}
```

Load **Playfair Display**, **Public Sans**, and **Source Serif 4** in
`index.html` (replacing Cormorant Garamond, Lora, DM Sans). Apply across all
routes in the same phase — do not split old/new fonts by page.

**Staged token rename (compat alias layer):** introduce new names above without
a big-bang swap. Keep legacy variables as aliases until each component is migrated:

```css
:root {
  --navy:        var(--field);
  --navy-card:   var(--surface);   /* revisit per-component — not 1:1 everywhere */
  --cream:       var(--ink);
  --text:        var(--ink);
  --text-muted:  var(--ink-body);
  --text-faint:  var(--ink-muted); /* audit: some “faint” was content — bump to body */
  --gold-light:  /* derive or alias after gold shift to #d9b76a */
}
```

Remove aliases only after grep confirms no live usage. Touch call sites opportunistically
during Phases 1–4 rather than one cleanup PR.

**Contrast pass (includes former Phase 5 polish):** audit every text style; anything
users must read gets `--ink-body` or brighter (≥ 4.5:1 on the field). Known offenders:
results tables, electoral-record card metadata, party-card blurbs, breadcrumbs,
stat-row labels (≥ 13px, letter-spaced smallcaps in `--ink-muted`), Latest Additions
captions (party kicker in `kickerText(party)` above title). `--ink-chrome` is
reserved for genuinely ambient chrome.

**Shared party palette — one JSON, all consumers:** consolidate into
`data/party-colours.json` (canonical slug → hex). Generate or validate from the
existing tables in `tools/hexmaps/scripts/colour.py` / `js/data.js` / `data/seo.json`;
then wire:

| Consumer | Change |
|---|---|
| `js/data.js` | Import or embed generated colours at build time |
| `tools/og-generator/og.html` | Load `party-colours.json` instead of inline dict |
| `tools/hexmaps/scripts/colour.py` | Read JSON (or generate Python dict from it) |
| Site CSS/JS | Raw hex only via shared module — never hand-sync a fifth copy |

**Party colour derivation** — extract `derive()` (~40 lines, dependency-free) from
`tools/og-generator/og.html` into a shared module (e.g. `js/colour.js`) used by
site and OG preview. Four named functions:

- `surface(c, theme?)` — raw colour; lift to oklch L≈0.48 if too dark for the field;
  achromatic → slate `#3d4654`; light-theme pale colours clamp down for bars/dots
- `kickerText(c, theme?)` — lightness clamped ≥ 0.75, chroma capped 0.15;
  achromatic → `#aab3c0`
- `kickerOnPaper(c)` — **opposite direction** for section kickers on `--paper`:
  clamp lightness ≤ 0.55 for AA (e.g. Lib Dem `#FAA61A → #b07708`); achromatic → `#5b6478`
- `onSurface(c)` — navy `#090e1c` when surface L ≥ 0.7, else `rgba(255,255,255,0.85)`

Apply in Phase 0 to every existing party-coloured surface (victory pills, legend
dots, seat bars, map keys) **before** Phase 2 record-card work — so election cards
ship with derived colours, not raw hex. Fixes TUV/Speaker (vanishing) and keeps
SNP/OMRLP (pale) legible.

**Holdings precompute:** export `buildHoldings()` from
`tools/og-generator/build-manifest.mjs` to `data/party-holdings.json` (slug →
`{ westminster, holyrood, senedd, stormont, euro, london }` counts). Run this step
whenever `data/seo.json` or devolved manifest indexes change — same cadence as the OG
manifest build. New manifestos added to the catalogue therefore update holdings on
the next build/deploy without manual edits. Site reads the JSON at runtime (or
inlines via build into `data.js`); OG subtitles and party-card holdings lines both
use the same file. See [party-holdings](../data-model/party-holdings.md).

**Homepage hero background:** retire the secondary corner radials (red/blue party
tints at 5% opacity in `.home-hero-bg`) — keep a single gold/navy accent world
(e.g. centre radial `rgba(217,183,106,0.06)` only).

---

## Phase 1a — Manifesto reading page: structure & typography (mockup 1a)

Route: `/manifesto/{electionId}/{partyId}`. Rebuild the document body as an archival
object: light paper document framed by dark chrome.

**Ship in 1a (no scroll JS):**

- **Document header** (dark): breadcrumb → party-colour kicker rule +
  `GENERAL ELECTION {YEAR}` (in `kickerText(party)`) → 52px Playfair title →
  metadata row (date · leader · page count · *document title* in italic cream) →
  actions right: "Original PDF · {size}" (ghost button) + "Download ↓" (gold solid).
- **Paper panel:** `--paper` background, max-width 820px, `border-radius: 2px`,
  heavy shadow (`0 24px 64px rgba(0,0,0,0.5)`), 72–88px padding (24px side padding
  on mobile, full-bleed). Static 4px top edge in party colour (progress animation
  deferred to 1b).
- **Document typography** (on paper): Source Serif 4 body 19px/1.7, ink `#3a3d45`;
  lede 20px `#26282e`; section kickers 13px Public Sans smallcaps in
  `kickerOnPaper(party)`; Playfair headings 38px `#191b20`; list bullets = 7px
  party-colour squares.
- Mobile: paper layout only; TOC placeholder or simple in-document heading list
  (anchor links, no sticky/collapsible yet).

**Acceptance (1a):** 70ch max measure; all paper text ≥ 4.5:1; print stylesheet
(hide dark chrome, white paper); `:focus-visible` on header actions; reduced-motion
safe (no motion required).

---

## Phase 1b — Manifesto reading page: TOC & scroll (mockup 1a completion)

**Ship in 1b:**

- **Two-column body** (desktop ≥ 1200px): sticky TOC (264px) + paper panel from 1a.
- TOC: `CONTENTS` label, section links derived from markdown headings; active item =
  party-colour left rule + 10% party-colour background + cream text. Below a divider:
  reading time + position ("Section n of m").
- Scroll-linked progress bar on paper top edge (read fraction vs 15% tint remainder).
- Mobile: collapsible TOC bar above paper.
- Keyboard/anchor navigation per section; TOC scroll-spy.

**Acceptance (1b):** TOC tracks scroll; anchor jumps land correctly; scroll-spy and
progress respect `prefers-reduced-motion` (instant updates, no animated bar if reduced).

---

## Phase 2 — Electoral record cards (mockup 1b)

Homepage + election index. Uses `kickerText(winner)` and `surface(party)` from Phase 0.

Per card:

- Year = hero: 58px Playfair (long labels "Feb 1974" drop to 46px, two lines OK)
- Ghost numeral bottom-right: last 2 digits, ~190px Playfair at 7% winner colour
- Border: 1px winner colour at 35% (replaces the thin top rule)
- Winner line: 12px colour square + `kickerText(winner)` text — "Labour victory · 411 seats"
- `New PM:` value in cream; drop any other repeated labels
- Footer: 6px seat-share bar, flex-weighted by seats, top 3 parties + slate remainder
- Mobile: same data as a compact list row (year · winner dot · PM · mini bar),
  not stacked cards — kills the endless scroll.

Hub election cards (Holyrood etc.): drop the repeated "Scottish Parliament
election" line — page context covers it; year + FM + winner-colour top bar remain
(intentionally different from Westminster full-border cards — see mockup 1e).

---

## Phase 3 — Nation & party browse cards (mockups 1c, 1d)

**Nation cards:** remove flag icons. Top-right geometric motif per nation, in the
nation accent at 25–35% opacity: England cross, Wales layered peaks, Scotland
saltire, NI Causeway hexagons (deliberately apolitical). Border = nation accent
at 30%. Motifs are 3–6 positioned divs each — copy from `Site Redesign.dc.html` 1c.
Homepage nation cards + `/nations` share the same motif components.

**Party cards:** 8px full-height edge bar in `surface(party)`; `EST. {year}` kicker
in `kickerText(party)`; blurb at `--ink-body`; holdings line from
`data/party-holdings.json` (e.g. "21 Westminster · 7 Holyrood manifestos").

---

## Phase 4 — Light mode (mockup 1e)

A token swap, not a redesign — every component reads tokens from Phase 0.

```css
[data-theme="light"] {
  --field:           #f7f3ea;
  --surface:         #ffffff;
  --hairline:        rgba(20,32,58,0.12);
  --ink:             #14203a;
  --ink-body:        #3a4256;
  --ink-muted:       #5b6478;
  --ink-chrome:      #5b6478;
  --gold:            #8a6d2c;   /* darkened for AA on cream */
  --texture-opacity: 0;        /* disable body noise overlay */
}
```

**Body noise texture:** today `body::before` applies a fixed SVG noise overlay. Drive
it from `--texture-opacity` (0.025 dark, 0 light) so cream field stays clean. Do not
remove the pseudo-element — set `opacity: var(--texture-opacity)` (or equivalent) so
dark mode keeps subtle grain and light mode has none.

- Cards: white on cream with 1px hairline + soft shadow (`0 2px 10px rgba(20,32,58,0.06)`)
- Party colours: `surface(c, theme)` / `kickerText(c, theme)` — PALE colours clamp
  down on light (SNP `#FDF38E → #d4b40a` for bars; outline on legend dots); dark
  colours mostly pass through raw.
- Toggle in nav (☾ Dark / ☀ Light); persist in `localStorage`; default to
  `prefers-color-scheme`; set `meta[name=theme-color]` per theme.
- The manifesto paper panel is identical in both themes — it IS the light surface.
- **Hexmaps:** separate light palette — map field, seat fills, labels, and legend
  must not reuse dark-navy assumptions. Audit `hexmap` / preview CSS and SVG label
  colours; add `[data-theme="light"]` overrides or a dedicated `--map-*` token set
  derived from the same party JSON + `surface(..., 'light')`.

---

## Phase 5 — Residual polish

Only items not absorbed into Phase 0:

- Any breadcrumb/metadata chip sizes missed in the Phase 0 contrast pass.
- Screenshot diff checklist automation (optional).

---

## Sequencing & effort

| phase | scope | size |
|---|---|---|
| 0 | tokens, aliases, fonts, contrast pass, shared JSON, derive() + holdings export, hero bg, party UI recolour | M |
| 1a | manifesto paper panel + header + typography | M |
| 1b | TOC, scroll spy, progress bar, mobile collapsible | M |
| 2 | record cards (uses Phase 0 derive) | S |
| 3 | browse cards + holdings line | S |
| 4 | light mode + hexmap palette + texture toggle | M |
| 5 | residual polish | S |

Ship **0 → 1a → 1b** first.

**QA checklist per phase:** axe/contrast scan; TUV + SNP + Speaker spot-checks on
every party-coloured component; mobile pass; screenshot diff of homepage before/after;
after 1b — manifesto print preview and reduced-motion TOC behaviour; after 4 — hexmap
page in both themes.
