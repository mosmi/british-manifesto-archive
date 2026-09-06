---
type: decision
title: Header navigation — Elections, Parties, Nations, About
description: September 2026 — Nations is a header item; Beyond Westminster is retired as a nav label. Supersedes the July I04/I08 lock.
tags: [design, ia, navigation, ux]
timestamp: 2026-09-06T00:00:00Z
---

# Header navigation

## Decision (6 September 2026)

**Status:** implemented 6 September 2026 with the
[singular URL scheme](../architecture/url-scheme.md).

Reopened July UX audit **I04 / I08**. Adopt the 6 Sep 2026 forensic audit header
(**2.1**, **2.2**): four slots, one axis each.

```
Elections ▾                         Parties ▾                 Nations    About    [⌘K]
├ General elections (1945–2024)     ├ England                 → /nation
├ Scottish Parliament               ├ Wales
├ Welsh Parliament                  ├ Scotland
├ Northern Ireland Assembly         ├ Northern Ireland
├ London Mayor & Assembly           ├ European groups
├ European Parliament               ├ Other parties
└ All elections →                   └ All parties A–Z →
```

Desktop Elections rows use a chamber subtitle (Westminster, Holyrood, Senedd
Cymru, Stormont, City Hall, Strasbourg & Brussels). The panel is a closed list
of six chambers plus the hub link, so it is not height-capped (a 420px cap
scrolled once General elections gained a subtitle). The Parties mega has a
left rule on the England column as well as rules between columns.

| Slot | Canonical hub | Children |
|---|---|---|
| **Elections** | `/election` | `/election/westminster`, `/election/holyrood`, `/election/senedd`, `/election/stormont`, `/election/london`, `/election/euro` |
| **Parties** | `/party` | nation columns; `/party/european-groups`; `/party/other`; `/party/all` |
| **Nations** | `/nation` | plain link (not a dropdown) |
| **About** | `/about` | |

Retire the **Beyond Westminster** nav label and the `/devolved` public path
(301 onto `/election/…`). Desktop and mobile render the **same** tree (**2.4**). The hamburger drawer
starts with the four slots collapsed; Elections and Parties expand one at a
time. The **label** is a link to the hub (`/election`, `/party`, `/nation`,
`/about`); a separate chevron opens the submenu. Footer site links: Home /
Elections / Parties / Nations / Manifestos / About. Manifestos is **not** a
fifth header slot — see [manifesto-hub](./manifesto-hub.md).

Europe is **not** a nation: `/nation/europe` → `/party/european-groups`; the
nations H1 is “The Four Nations” (**2.5**).

The two organising axes remain real (institution vs geography). They no longer
split the header. Elections = chambers; Nations = place; Parties = organisations.

## Superseded (21 July 2026, I04 / I08)

Header asymmetry was locked: Nations footer/home only; Beyond Westminster in
the header for Holyrood, Senedd, Stormont, London and EP. That lock is
**revoked**. Do not restore it without a new explicit decision.
