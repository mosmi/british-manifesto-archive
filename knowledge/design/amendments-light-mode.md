# Amendments — light mode QA fixes for manifestos.org.uk

Follow-up to [implementation-plan](./implementation-plan.md) (Phase 4), based on QA of the
implemented light mode (screenshots in `uploads/light-mode-*.png`). Ordered by
priority. Owner decision already made where noted.

---

## A1 — Stranded dark components (bugs, fix first)

Components that stayed dark-styled while inheriting light-mode text tokens,
producing navy-on-dark text:

1. **Homepage hemicycle card + timeline strip** (`light-mode-01/02`)
   → **Theme both LIGHT** (owner decision). White/`--surface` card on the cream
   field, hairline border, soft shadow — same treatment as the sidebar election
   cards. Card title, winner line, and "View election →" button move to light
   tokens. Timeline strip: light track, hairline border, year pill stays red.
   The seat-dot arc itself keeps party colours on the light panel (see A6 for
   glow removal).
2. **Constituency hover tooltip** (`light-mode-22`, East Antrim) — navy heading
   on navy panel. Theme light: white panel, `--ink` heading, hairline border,
   `0 4px 16px rgba(20,32,58,0.15)` shadow. Ensure tooltip tokens are theme-aware,
   not hardcoded.
3. **Parliament / Constituencies segmented control** (`light-mode-10/21`) — dark
   grey pill on light page. Restyle: hairline-bordered track in `--surface`,
   active segment white with `--ink` text + gold underline or border; inactive
   `--ink-muted`.
4. Audit for any other hardcoded dark panels (video embed placeholder block on
   election pages is dark — acceptable as a media frame, but give it a light
   caption bar so its text never mixes tokens). Include devolved portal timeline
   cards (`.london-timeline-card`) in the audit.

## A2 — Pale-colour clamp-down (light-mode derivation)

The dark-mode `derive()` rules were ported, but the light-mode flip is missing in
call sites. `deriveColour(hex, 'light')` and `kickerTextColour(hex, theme)` already
exist in `js/colour.js`; wire them everywhere via a shared `getCurrentTheme()`
helper. Add a new **`dotColour(c, theme)`** helper (pale fill + 1px outline).

- **Small text in party colour** on cream: clamp oklch lightness DOWN to ≤ 0.55,
  keep hue (OMRLP `#FFF000 → ~#8a7a00`; SNP `#FDF38E → ~#8f7f1a`; gold links
  `#d9b76a → #8a6d2c`). Fixes the unreadable OMRLP hero stats (`light-mode-25`).
  Use `kickerTextColour(c, getCurrentTheme())` — not raw party hex or dark-mode
  derivation. Unify on 0.55 (matches `kickerOnPaper()`; `deriveColour` light
  kicker currently uses 0.42 — pick one constant).
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
- **Theme toggle must re-derive**: on `applyTheme()`, re-run
  `updateHomeDashboard()`, refresh card inline styles (or CSS vars from derived
  colours), and redraw hemicycle charts so mid-session toggles don't leave stale
  inline colours.

## A3 — Remove/re-tone the pink hero glow

Still present on homepage, election-page, and party-page heroes; reads as a
smudge on cream (`light-mode-01/03/04/11`). Replace with a barely-there gold
radial (`rgba(138,109,44,0.05)` light / `rgba(217,183,106,0.06)` dark) or remove
entirely. Stop setting `--party-glow` from raw winner colour in
`updateHomeDashboard()`. One accent world.

## A4 — Manifesto reading page (paper + empty states)

`light-mode-06`:
- Paper panel is the same cream as the field — no object. On light theme, paper
  = `#ffffff` with `1px rgba(20,32,58,0.12)` border + softer shadow
  (`0 12px 32px rgba(20,32,58,0.10)`). Dark theme unchanged (`#f7f3ea` paper).
- **Metadata fallbacks**: header currently prints "8 June 2017 · … ·" — build the
  meta row from present fields and `join(' · ')`; omit missing fields and their
  separators entirely. Never render placeholder dots.
- **Empty document state**: designed, centred block on the paper — small-caps
  kicker `TEXT VERSION NOT YET ARCHIVED`, one-line explanation, primary button
  "View original PDF", ghost button "How to contribute" (links to About). Hide
  the empty CONTENTS rail when there are no sections (currently an empty label
  + divider).

## A5 — Nation card motif containment (`light-mode-18`)

- Motifs overlap text (England cross, Scotland saltire sit behind the kicker
  line). Reserve a corner zone: motif absolutely positioned top-right within a
  ~120×120px area, card text max-width leaves that zone clear; drop motif
  opacity to ~12–18% on light.
- **Europe card uses an emoji flag** — replace with the gold ring motif (ghost
  circle, border-only), consistent with the OG card system.

## A6 — Hemicycle rendering on light

Disable the glow/bloom filter on seat arcs when theme=light (`light-mode-21`
NI Assembly shows halo artefacts). Flat dots + thin arc stroke on light; keep
bloom on dark. Pass theme into `drawParliamentChart()` or read `data-theme`
inside `js/parliament.js`.

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
  kicker goes through `kickerTextColour(c, theme)` rather than raw colour.

## A8 — Manifesto text fetch + PDF download (functional bugs)

Reported on `/manifesto/2019/labour`: markdown file and PDF both exist on disk,
but the page shows the fetch-error placeholder and "Download ↓" does nothing.

**Root causes (confirmed in code review):**

1. **Markdown not loading** — `fetchTyped()` in `js/data-loader.js` rejects
   responses unless `Content-Type` includes `markdown` or `text/plain`.
   Python `http.server` (and some static hosts) serve `.md` as
   `application/octet-stream`, so the fetch throws even though the file returns
   200. Fix: for `expected === 'markdown'`, also accept `octet-stream`, or
   validate by URL suffix when status is 200.
2. **Download button intercepted by SPA router** — `setupRouter()` in
   `js/app.js` calls `preventDefault()` + `navigate()` on all same-origin
   links without `target="_blank"`. The Download link uses `<a download>` with
   no `target`, so the router navigates to `/manifestos/…/manifesto.pdf` as an
   SPA route → `renderNotFound()`. Fix: skip interception when
   `a.hasAttribute('download')` or when `href` matches static asset extensions
   (`.pdf`, `.jpg`, `.png`, etc.). "Original PDF" works because it uses
   `target="_blank"`.
3. **Local dev note**: direct browser navigation to `/manifesto/…` on bare
   `python -m http.server` returns 404 (no SPA fallback to `index.html`). In-app
   navigation works; production (Cloudflare Pages) should serve `index.html` for
   unknown paths — verify separately from the two JS bugs above.

**QA after fix:**
- [ ] `/manifesto/2019/labour` renders full markdown body + populated TOC
- [ ] Download ↓ saves `manifesto.pdf` (does not SPA-navigate to 404)
- [ ] Original PDF still opens in new tab

## QA checklist (after fixes)

- [ ] Homepage: hemicycle card + timeline fully light-themed, no navy-on-dark
- [ ] Tooltip + segmented control light-themed
- [ ] OMRLP party page: all hero stats legible; placeholder covers show ghost years
- [ ] Parties mega-menu: every dot visible incl. SNP/Alliance yellows
- [ ] Manifesto page: white paper distinct from field; no "· … ·"; designed empty state
- [ ] Four Nations: no motif/text overlap; Europe ring not emoji
- [ ] No pink glow anywhere
- [ ] Theme toggle mid-page: switch light ↔ dark on homepage slider without stale inline colours
- [ ] Contrast scan (axe) passes on: home, election 2024, manifesto, OMRLP, Holyrood
- [ ] Manifesto text loads and PDF download works (A8)
