# Amendments — light mode QA fixes for manifestos.org.uk

Follow-up to `site-redesign/IMPLEMENTATION_PLAN.md` (Phase 4), based on QA of the
implemented light mode (screenshots in `uploads/light-mode-*.png`). Ordered by
priority. Owner decision already made where noted.

> **Mockups:** corrected light-mode designs for A1, A2, A3, A4, A5 and A6 are in
> `Light Mode Fixes.dc.html` — 1a homepage hemicycle card + timeline slider,
> 1b OMRLP hero + placeholder covers, 1c manifesto reading page, 2a hover
> tooltip, 2b segmented control, 2c Four Nations cards. Build to those specs.

---

## A1 — Stranded dark components (bugs, fix first)

Components that stayed dark-styled while inheriting light-mode text tokens,
producing navy-on-dark text:

1. **Homepage hemicycle card + timeline strip** (`light-mode-01/02`)
   → **Theme both LIGHT** (owner decision). White/`--surface` card on the cream
   field, hairline border, soft shadow — same treatment as the sidebar election
   cards. Card title, winner line, and "View election →" button move to light
   tokens. The seat-dot arc itself keeps party colours on the light panel (see
   A6 for glow removal); keep the chunky ~11px seat dots from the current site.
   Timeline: NOT a strip of evenly spaced years — it is a **continuous
   1945–2024 slider** (elections are irregularly spaced). Light treatment: white
   panel, hairline track, a tick at every election (incl. both 1974s) at its
   true proportional position, red year-flag thumb, prev/next buttons, sparse
   year labels (1945 / 1955 / 1966 / 1974 / 1987 / 2001 / 2015 / 2024) at
   proportional positions. Mocked as `1a`.
2. **Constituency hover tooltip** (`light-mode-22`, East Antrim) — navy heading
   on navy panel. Theme light: white panel, `--ink` heading, hairline border,
   `0 4px 16px rgba(20,32,58,0.15)` shadow. Ensure tooltip tokens are theme-aware,
   not hardcoded. Mocked as `2a`.
3. **Parliament / Constituencies segmented control** (`light-mode-10/21`) — dark
   grey pill on light page. Restyle: hairline-bordered track in `--surface`,
   active segment white with `--ink` text + gold underline or border; inactive
   `--ink-muted`. Mocked as `2b` (both states).
4. Audit for any other hardcoded dark panels (video embed placeholder block on
   election pages is dark — acceptable as a media frame, but give it a light
   caption bar so its text never mixes tokens).

## A2 — Pale-colour clamp-down (light-mode derivation)

The dark-mode `derive()` rules were ported, but the light-mode flip is missing.
Implement `kickerText(c, 'light')` and `dot(c, 'light')`:

- **Small text in party colour** on cream: clamp oklch lightness DOWN to ≤ 0.55,
  keep hue (OMRLP `#FFF000 → ~#8a7a00`; SNP `#FDF38E → ~#8f7f1a`; gold links
  `#d9b76a → #8a6d2c`). Fixes the unreadable OMRLP hero stats (`light-mode-25`).
- **Legend/menu dots**: pale dots (L ≥ 0.7) get a 1px `rgba(20,32,58,0.25)`
  outline everywhere (mega-menu, hub sidebars, hemicycle legends) — currently
  applied inconsistently; SNP is a white speck in the Parties menu
  (`light-mode-07`).
- **Ghost numerals / large tint surfaces** (placeholder covers): pale colours
  need a darker tint base — use the clamped variant at 12–15% opacity instead of
  the raw colour at 7% (fixes invisible "2015/2005/2001" on OMRLP placeholder
  covers).
- Bars/edge bars/top rules: raw colour is fine on light EXCEPT L ≥ 0.85
  (OMRLP, SNP, Ulster Popular Unionist) → use clamped variant.

OMRLP hero + placeholder covers mocked as `1b`.

## A3 — Remove/re-tone the pink hero glow

Still present on homepage, election-page, and party-page heroes; reads as a
smudge on cream (`light-mode-01/03/04/11`). Replace with a barely-there gold
radial (`rgba(138,109,44,0.05)` light / `rgba(217,183,106,0.06)` dark) or remove
entirely. One accent world. Gold radial shown on the `1b` hero mock (tweakable).

## A4 — Manifesto reading page (paper + empty states)

`light-mode-06`:
- Paper panel is the same cream as the field — no object. On light theme, paper
  = `#ffffff` with `1px rgba(20,32,58,0.12)` border + softer shadow
  (`0 12px 32px rgba(20,32,58,0.10)`). Dark theme unchanged (`#f7f3ea` paper).
- **Metadata fallbacks**: header currently prints "8 June 2017 · … ·" — omit
  missing fields and their separators entirely. Never render placeholder dots.
- **Empty document state**: designed, centred block on the paper — small-caps
  kicker `TEXT VERSION NOT YET ARCHIVED`, one-line explanation, primary button
  "View original PDF", ghost button "How to contribute" (links to About). Hide
  the empty CONTENTS rail when there are no sections (currently an empty label
  + divider). Mocked as `1c`.

## A5 — Nation card motif containment (`light-mode-18`)

- Motifs overlap text (England cross, Scotland saltire sit behind the kicker
  line). Reserve a corner zone: motif absolutely positioned top-right within a
  ~120×120px area, card text max-width leaves that zone clear; drop motif
  opacity to ~12–18% on light.
- **Europe card uses an emoji flag** — replace with the gold ring motif (ghost
  circle, border-only), consistent with the OG card system.

All five cards mocked as `2c`.

## A6 — Hemicycle rendering on light

Disable the glow/bloom filter on seat arcs when theme=light (`light-mode-21`
NI Assembly shows halo artefacts). Flat dots + thin arc stroke on light; keep
bloom on dark. Flat-dot treatment shown on the `1a` hemicycle mock.

## A7 — Small sweep

- Replace any remaining bright-gold small text/links on cream with `--gold`
  light-token `#8a6d2c` (breadcrumb current page, "View portal →", card links).
- Beyond Westminster menu: London dot is purple — use gold (City Hall) or the
  body's assigned accent; keep dot assignments consistent between menu, hub
  sidebar, and portal cards.
- Party-page cover grids (`light-mode-11`): missing scans show washed-out pink
  blocks — reuse the OMRLP-style placeholder (party-tint field + clamped ghost
  year + party dot caption) as the single missing-cover pattern.
- Election-page kickers in party red on cream are fine, but check every party's
  kicker goes through `kickerText(c, 'light')` rather than raw colour.

## QA checklist (after fixes)

- [ ] Homepage: hemicycle card + timeline fully light-themed, no navy-on-dark
- [ ] Tooltip + segmented control light-themed
- [ ] OMRLP party page: all hero stats legible; placeholder covers show ghost years
- [ ] Parties mega-menu: every dot visible incl. SNP/Alliance yellows
- [ ] Manifesto page: white paper distinct from field; no "· … ·"; designed empty state
- [ ] Four Nations: no motif/text overlap; Europe ring not emoji
- [ ] No pink glow anywhere
- [ ] Contrast scan (axe) passes on: home, election 2024, manifesto, OMRLP, Holyrood
