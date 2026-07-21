---
type: decision
title: Nations vs Beyond Westminster
description: Intentional IA split — geography/party taxonomy vs institutional elections path.
tags: [design, ia, navigation, ux]
timestamp: 2026-07-21T00:00:00Z
---

# Nations vs Beyond Westminster

## Decision (locked, UX audit I04 / I08)

Header asymmetry is **intentional**. Do **not** add Nations to the desktop or
mobile header nav to “match” the footer.

| Path | Role | Primary entry |
|------|------|----------------|
| **Beyond Westminster** (`/devolved`) | Institutions and their elections (Holyrood, Senedd, Stormont, London, EP) | Header nav |
| **The Four Nations & Europe** (`/nations`) | Geography / party taxonomy + Westminster-by-nation | Homepage + footer |

Users looking for devolved-related content should use **Beyond Westminster**.
Nations remains useful for browsing parties and results by place.

Hub pages and the homepage “Browse by Nation” lede cross-link so the two axes
are explained without merging URLs or mega-menus.
