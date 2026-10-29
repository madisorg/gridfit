# GridFit — design system

This file is the design language of the GridFit site: the rules and the reasons. The values live in one
place only, [`web/src/styles/tokens.css`](web/src/styles/tokens.css); the components that use them are in
[`web/src/styles/site.css`](web/src/styles/site.css). A page takes colours, sizes and fonts from tokens. It
defines no colour literal, no `font-family` and no breakpoint of its own.

Written 2026-10-29, before the Astro port, and measured after it (§11).

## 1. Character

GridFit is a **datasheet, not a brochure**. It reads like the type-approval lists and spec sheets its
users already trust: paper and ink, hairline rules, a heavy rule under a table head, numbers that line up.
Dense on purpose — a row is 34 px, the answer comes before the explanation, and every claim sits next to
its source and the date it was seen. It is technical and plain-spoken, never "premium-modern": no
gradients, no glass, no hero illustration, no motion. The one thing that is allowed to look striking is
the data itself — the register matrix and the evidence timeline (§7).

## 2. Who it is for, and the two moments

| moment | who | device | what the page must do |
|---|---|---|---|
| **1. "I have a model number"** | a prosumer after an offer, or an installer a customer just asked | phone, from a search result | answer before scrolling: local yes/no, read or control, which integration, which registers, seen date, source |
| **2. "I am still choosing"** | a buyer comparing hybrids, wallboxes, batteries | wide screen | filters on the left, a dense comparison table, the register matrix in every row |

Moment 1 is why the home page **starts with a search box that takes model codes** (`SUN-12K-SG04LP3`,
`GEN24`, `SH10RT`) and why a family page opens with the verdict block, not a paragraph. Moment 2 is why the
same table carries brand, class, HA, evcc, control, the five-register matrix and the model count in one
row, with a sticky head. Second readers are machines — search snippets (`FAQPage` schema on every family
page), other projects (CSV/JSON in the repo, linked in the footer) and LLMs (`/llms.txt`). They cost
almost nothing and need no design.

**Trust is a design element.** The audience (Home Assistant users) is allergic to ads and to confident
claims that turn out wrong. So: a source link and a seen date on every row, a correction button on every
family page, the change log one click away, and an empty cell that says "not found" — never "does not
work" or "not approved".

## 3. References, and what we take from each

| site | what we take | what we leave |
|---|---|---|
| [caniuse.com](https://caniuse.com/) | the dense support matrix that reads at a glance: fixed column order, filled vs outlined cells, a footnote marker instead of a colour shade for "partial" | its legacy chrome and ad slots |
| [diskprices.com](https://diskprices.com/) | honesty and plainness: one table, filters as plain selects, no marketing copy between the user and the data | the unsorted wall-of-links feel |
| [zigbee2mqtt.io supported devices](https://www.zigbee2mqtt.io/supported-devices/) | one page per device that lists *capabilities* ("exposes") and a visible community correction path | the docs-site sidebar on a device page |
| [ev-database.org](https://ev-database.org/) | moment 2: filters beside a results table, spec rows you can compare | its ad blocks and image-heavy cards |
| [Starlight](https://starlight.astro.build/) (Astro docs theme) | that a static Astro site can be fast, accessible and readable with a small CSS layer | its default look — GridFit does not use the theme |

openalternative.co and nomadlist.com were looked at as examples of a site with a character of its own;
GridFit's character is a different one (§1).

### What not to do

- **Inter (or any default UI font) as the body face.** Every AI-generated site uses it; it says nothing.
- **Violet-to-indigo gradients**, or any gradient, as background or on buttons.
- **Glass cards** — `backdrop-filter: blur` over a coloured background.
- **Three equal cards in a row** ("Fast · Open · Free") — the page has data to show instead.
- **One 16 px radius on everything.** GridFit is square by default; radius is the exception (§5).
- **Decorative animation** — fade-ins on scroll, hover lifts, animated counters, skeleton shimmer.
- **Colour that carries meaning alone.** Every status is a shape and a word first (§4).
- **Stock photos and illustrations.** No images; icons only where a word cannot do it, as line SVG.
- **Anything that looks like the Home Assistant brand** — its blue, its house logo, the "Works with Home
  Assistant" badge. Those are Open Home Foundation / Nabu Casa marks; GridFit names them in text only.

## 4. Type and colour

### Two faces, chosen with real data

Trial: [`docs/moodud/kirjaproov.html`](docs/moodud/kirjaproov.html) renders the same fragment of the Deye
SUN-SG LP3 page — 12 register model codes, the five-register matrix and the five integration rows — in
three pairings, at 390 px. Measured in the page itself
([`kirjaproov.json`](docs/moodud/kirjaproov.json) is the ui-kontroll pass of the same page):

| pairing (heading / table) | `tnum` works | digits proportional without it | x-height | widest model code at 13 px | fits 366 px | I l 1 · O 0 distinct |
|---|---|---|---|---|---|---|
| **A. Barlow Semi Condensed / IBM Plex Sans** | yes | no (already equal) | 0.52 | 206 px | yes | **yes** — Plex has a serifed `I`, a tailed `l`, and a slashed zero via `zero` |
| B. IBM Plex Sans Condensed / Source Sans 3 | yes | no | 0.49 | 200 px | yes | `I` and `l` alike |
| C. Archivo Narrow / Public Sans | yes | **yes** (18 px drift over 7 digits) | 0.52 | 209 px | yes | `I` and `l` alike |

**Chosen: A.** The table face carries model codes all day — `SUN-10K-SG04LP3-EU`, `X1-IES`, `IQ8`,
`SH10RT` — where `I`/`l`/`1` and `O`/`0` must not be confused; only Plex Sans separates all of them, and
its x-height keeps 13 px cells readable on a phone. The heading face is **Barlow Semi Condensed**, a
DIN-like grotesque from road and industrial signage: it fits the grid/electrical subject, it is visibly
different from the body face (B would be one family in two widths), and its narrow width keeps long
family names to two lines at 390 px.

| token | value | use |
|---|---|---|
| `--font-head` | Barlow Semi Condensed 600 | h1–h3, the wordmark, register keys |
| `--font-text` | IBM Plex Sans 400 / 600 | everything else |
| `--num` | `tabular-nums slashed-zero` | set on `body`: every number, date and code lines up |

Licence: both SIL Open Font License 1.1 (copies in [`web/src/fonts/`](web/src/fonts/)). Files are
**self-hosted woff2** from the Fontsource packages — Latin (~23 KB each, three files) plus a Latin-Extended
subset that loads only for a character that needs it. No font CDN. Sizes: 13 / 14 / 16 / 20 / 28 / 40 px;
**12 px is the floor**, and a text input on a phone is 16 px (no zoom on focus).

### Palette

Paper and ink, one accent, four status tones. Defined once for light and once for dark; the site follows
the OS (`prefers-color-scheme`), there is no toggle. Contrast was computed (WCAG 2.x) before any code and
measured again on the built pages (§11).

| token | light | dark | role | lowest contrast |
|---|---|---|---|---|
| `--paper` / `--surface` / `--sunk` | `#f5f4ef` / `#fdfcf9` / `#ecebe4` | `#111315` / `#181b1e` / `#0c0e0f` | page, table/panel, hover row | — |
| `--ink` | `#16191c` | `#e8e6df` | text | 13.9:1 |
| `--ink-2` / `--ink-3` | `#4d545a` / `#5f666c` | `#a9aeb1` / `#959b9f` | secondary text / faint matrix key | 6.4 / 4.9:1 |
| `--rule` | `#d5d2c8` | `#2c3135` | hairlines (decorative, not a control edge) | — |
| `--link` | `#0a4f86` | `#8ebff0` | links | 7.1:1 |
| `--signal` | `#a8430a` | `#f2a463` | the one accent: focus ring, active filter, caveat bar | 5.1:1 |
| `--ok` on `--ok-bg` | `#1c6337` / `#e2efe4` | `#82d39e` / `#16301f` | local, control | 6.1:1 |
| `--cloud` on `--cloud-bg` | `#7c4a00` / `#f8ecd6` | `#f0c470` / `#36290f` | cloud, sponsor token | 6.3:1 |
| `--reg` on `--reg-bg` | `#1f3f6e` / `#e4eaf3` | `#aec7ee` / `#1b293d` | register matrix | 8.5:1 |
| `--unk` on `--unk-bg` | `#4d545a` / `#e9e8e2` | `#a9aeb1` / `#23272a` | read only, not found | 6.3:1 |

No violet, no indigo, no gradient. Form controls take a 1 px `--ink-2` edge (≥ 3:1 against the surface,
WCAG 1.4.11); hairline rules are decoration and need not.

### Status = shape + word (colour only repeats it)

| mark | shape | word | meaning |
|---|---|---|---|
| `.st.local` | ■ filled square | local | an integration talks to the device on your network |
| `.st.cloud` | ○ ring | cloud | only through a vendor cloud |
| `.st.write` | ◆ filled diamond | control | settable entities (HA) / evcc drives it |
| `.st.read` | ◇ outlined diamond | read only | sensors only |
| `.st.none` | — dash | not found | no source found — never "does not work" |
| `.st.sponsor` | + | sponsor token | evcc needs a sponsor token |

The shapes are CSS (`::before`), not SVG, so a 731-row table carries no markup per mark. A printout in
greyscale, or a reader who cannot tell green from amber, loses nothing.

## 5. Space, shape, density

- **Space:** 4 px steps — `--s1` 4 · `--s2` 8 · `--s3` 12 · `--s4` 16 · `--s5` 24 · `--s6` 32 · `--s7` 48 · `--s8` 64.
  Nothing in between. Side gutter 16 px on a phone, 32 px from 48 rem.
- **Width:** prose stops at `--measure` 42 rem; tables use `--page` 110 rem (1 760 px). At 3 440 px the
  page does not stretch further — a 7-column table wider than that stops being comparable row by row.
- **Radius:** `--r0` 0 for tables, panels and matrix cells; `--r1` 2 px for status marks; `--r2` 4 px
  for inputs and buttons. Nothing rounder.
- **Rules:** 1 px `--rule` between rows; 2 px `--ink` under a table head, under a page head and above the
  footer — the datasheet rhythm.
- **Density:** table rows **34 px** (`--row-h`), not 56. Touch targets **44 px** (`--hit`): on a phone
  every link and control is at least that tall, and the tables stack (§6) so their links become 44 px
  rows. The matrix cells are not links, so they can stay small.

## 6. Components

| component | where | rules |
|---|---|---|
| **Shell** (`Base.astro`) | every page | text wordmark (no logo — GridFit is a working name, no new marks), four nav links at 44 px, footer with sources, the empty-cell rule, the not-affiliated line, dataset links and licences |
| **Search** (`index.astro`) | home | one 48 px input, 2 px ink edge. Brand and family names filter the table; a query with a digit is looked up in `/models.json` (every register model code, normalised like the register parser), fetched on first use. Results list family pages with the matching codes. |
| **Filter bar** | home | plain `<select>`s that name themselves ("All brands"); labels above them on wide screens, visually hidden on a phone so the filters take three rows, not a screen. The active filter gets the `--signal` edge; state lives in the URL. Sticky sidebar from 80 rem. |
| **Family table** (`FamilyTable.astro`) | home, brand pages | sticky head with 2 px rule; 34 px rows; brand in `--ink-2` before the family name; one status per column; matrix; model count right-aligned with tabular numbers. **Under 48 rem it stacks**: one block per family, the name as a 44 px link, the statuses on one line with their column name as a prefix, the matrix on its own line. |
| **Register matrix cell** (`Matrix.astro`) | every table, verdict | six fixed cells in fixed order (AT CZ EE NL PL SE). Filled = listed; outlined + `*` = listed with the register's own restriction word; faint outline = the list covers this class but no model was found; **dotted `--ok` outline on `--ok-bg` = the country has no listing for this class** (a wallbox is a load; only AT lists chargers), nothing to check; faint + `?` = coverage not confirmed (`SCOPE` in `gridfit/registers.py`, 2026-10-29). Shape first, colour second: dotted vs solid, `*` vs `?`. One accessible label reads all six. |
| **Status mark** (`Status.astro`) | everywhere | §4 |
| **Verdict block** | family page, first | a definition list — Home Assistant, evcc, Grid registers, Register match, Checked — that answers moment 1 above the fold on a phone. On wide screens it sits right of the FAQ answer. |
| **FAQ block** | family page | the question as h2, the one-line answer from the dataset (also the `FAQPage` JSON-LD), and the firmware/grid caveat with a `--signal` bar |
| **Evidence table** | family page | one row per integration route: name (+ repo, + the curated note), source, local/cloud, read/control with the reason, connection, HACS stars and last update, seen date linking to the source file |
| **Evidence timeline** (`Timeline.astro`) | family page, home | §7 |
| **Correction button** | family page | a bordered 44 px link to a pre-filled GitHub issue — the one call to action on the site |
| **Register cross-view table** (`.xv`, `RegCell.astro`) | `/registers/` hub and brand pages | one fixed column per country (AT BE CZ EE NL PL SE), always in that order; the cell carries the list's own status as a symbol — ✓ listed, ✓* with restrictions, ⏱ time-limited, ⏱! date passed, exp expired, Nein — filled `--reg` for listed, outlined for restricted/limited, amber outline for passed/expired/Nein; empty = no matching entry. The words are in the title and the legend. On a phone the country columns narrow to 28 px and the brand moves above the model so the name keeps ~160 px. |
| **List panels** (`.panel`, `.facts-dl`) | register model and country pages | one panel per country: the list's name and date, its status in its own words, "as written", firmware, row/document number, end date, match trust. A country with no entry is an empty panel that says "not a no". |
| **Footer disclaimer** | every page | sources, "an empty cell is not a no", firmware and grid caveat, not affiliated with OHF / Nabu Casa / evcc / HACS / manufacturers / grid operators |

## 7. The one distinctive shape: the data itself

GridFit has no illustration. What gives the page its face is two pieces of data drawn plainly:

1. **The register matrix** — the same five cells in every row of every table, so a column of filled `NL`
   cells is a pattern the eye picks up across 700 rows. It is the only place with strong fills.
2. **The evidence timeline** — "how old is what we know". One row per source on one shared axis (12
   months on a family page, 6 on the home page): every HACS repo's last release, every register snapshot
   that lists the family, and the day GridFit read the sources. A repo last updated 2026-05 next to
   registers read last week *shows* that the local-control claim is the one that can rot. Older than the
   axis = an open ring at the left edge and `◂` after the date. On a phone the track moves under the label.

The change log (`/changelog/`) is where "who fell off a list" will show once there is more than one
rebuild; the timeline is the per-page view of the same idea.

## 8. Stack, and why

- **Astro 7.4.0, fully static** (`output: "static"`). Astro 7 has been stable since 2026-06 (7.0.0,
  2026-06-22); 7.4.0 is pinned as the newest release at least two weeks old. Every page is HTML at build
  time; **7 265 pages build in ~20 s** (731 families, 297 brands, and the `/registers/` cross-view:
  hub, 503 brand pages, 5 722 model pages, 7 country pages, change log). The pages read the same committed
  dataset `build.py` writes (`data/dataset/*.json`, `data/registers/listing.json`, `data/curated/*.yaml`)
  and change none of it. The register cross-view needs the grouping in `gridfit/registers.py`
  (devices from the latest snapshot), so `npm run build` first runs `tools/site_data.py`, which calls
  that same code and writes `web/.data/registers.json` (git-ignored) — the parser and the data stay
  untouched. URLs use the same slug rules as `gridfit/assemble.py` and `gridfit/registers.py`; the URL set
  is identical to the Python site (7 265 = 7 265, checked by diff).
- **No Tailwind.** The system is ~25 tokens and a dozen components. Tailwind would move those decisions
  into class strings on every element of 1 000 pages, add a build dependency, and its default scale and
  palette are exactly the "standard AI" look this file exists to avoid. Tokens + one ~250-line stylesheet
  is less to read and less to break.
- **No Pagefind.** Tested on the built site: its facets (`data-pagefind-filter`) work, but its word
  splitter breaks model codes — `GEN24` and `X3-Ultra` returned nothing and `SG04LP3` ranked Sungrow SG
  above the Deye LP3 page. A 57 KB (gzip) `/models.json` with the register parser's own normalisation
  finds every one of them by substring, and the 731-row facet filter is cheaper in the DOM than an index.
- **JavaScript:** two islands, both inline modules — the home page (filters + model-code lookup, 2.4 KB)
  and the `/registers/` hub (filter and page through `/registers/index.json`, 2.3 KB). **0 bytes on every
  other page.** The home table works without JS; the hub says so in a `<noscript>` and every model is on
  its brand page.

## 9. Adding a page

A new page is an `.astro` file under `web/src/pages/` wrapped in `Base.astro`, built from the components
above. If it needs something new, add a token or a component class to the two CSS files and a row in §6
— never a local colour, font or breakpoint.

## 10. Measuring a change

Every visual change is measured before and after with the same tool, the homelab's
`scripts/ui-kontroll.py pildid` (headless Edge): **3440×1440 and 390×844, light and dark**, at least the
home page, one family page (top and the register table) and one brand page
([`docs/moodud/routes.json`](docs/moodud/routes.json)). Pass means:

1. no console errors or failed requests;
2. **0 px horizontal overflow** at 390 px;
3. every text **≥ 4.5:1** against its background;
4. on a phone every tappable thing **≥ 44 px** tall (a link inside a sentence excepted);
5. no text under **12 px**;
6. colours and fonts only from tokens.

The numbers do not see a table that collapsed to zero width — look at the pictures too.

## 11. Measured, 2026-10-29

Same tool, same 14 routes ([`routes.json`](docs/moodud/routes.json): home, home table, a model-code
search, a filter state, the Deye LP3 family page at three scroll positions, two brand pages, How we know,
the register hub with a search, a register brand page, a register model page and a country page), each at
3440×1440 and 390×844, light and dark = 56 pictures per site. **Before** = the Python/Jinja site of `main`
at `da80cc8` (v1 + the register cross-view); **after** = this Astro build of the same commit's data.
Reports: [`enne.json`](docs/moodud/enne.json) / [`parast.json`](docs/moodud/parast.json), logs beside
them, pictures as `enne--<route>--<lai|tel>-<hele|tume>.webp` and `parast--…` (wide views stored at half size).

| check | before (Python site) | after (Astro) |
|---|---|---|
| console errors / failed requests | 1 (favicon 404) | **0** |
| horizontal overflow at 390 px | 0 of 56 | **0 of 56** |
| texts under 4.5:1 | 0 (lowest 5.47) | **0** (lowest 5.29) |
| tap targets under 44 px on a phone | **204 of 210** | **0 of 254** |
| smallest text | 12.5 px | 13 px |
| fonts | system-ui | Barlow Semi Condensed + IBM Plex Sans, self-hosted, 70 KB |
| JS on the home page | 1.6 KB | 2.5 KB (filters + model-code lookup) |
| JS on family, brand, register model and country pages | 0 | 0 |
| JS on the register hub | 3.5 KB | 2.3 KB |
| home HTML, gzip | 23 KB | 33 KB (6 register cells per row, CSS inlined) |
| family page HTML, gzip | 2.6 KB | 8.7 KB (CSS inlined, evidence table, timeline) |

Lighthouse 13.5 (mobile preset, simulated slow 4G, Edge headless), performance / accessibility /
best practices / SEO:

| page | before | after |
|---|---|---|
| home | 79 / 100 / 96 / 100 (LCP 2.8 s, TBT 530 ms) | 79 / 100 / 100 / 100 (LCP 3.9 s, TBT 120 ms, CLS 0.001) |
| Deye LP3 family page | 100 / 100 / 96 / 100 | 100 / 100 / 100 / 100 (LCP 1.5 s) |
| register model page | 100 / 100 / 96 / 100 | 100 / 100 / 100 / 100 (LCP 1.5 s) |

What it took to get there, so the next change does not undo it: the first Astro home scored 44 (TBT 1.4 s,
CLS 0.09). Fixed by preloading the two faces every page paints first, `content-visibility: auto` on the
stacked rows of a phone table, building the search text only on the first search, a short accessible
label per matrix (what *is* listed, not six "no listing found" phrases per row), and inlining the CSS.
The home page's LCP stays above the old one because its HTML is twice as large; the next lever is to
render the long tail (649 uncurated families) on demand instead of in the page.

Not done yet: the change log and the evidence timeline show one rebuild only (the first dataset and the
register baseline are the same day), so the "who fell off a list" view has nothing to show until the
second register refresh.

## 12. Measured, 2026-10-29 — pre-publish pass

Same tool and routes as §11 plus the new `/404.html` ([`routes-etapp0.json`](docs/moodud/routes-etapp0.json)), 60 pictures:
[`etapp0.json`](docs/moodud/etapp0.json). The 14 §11 routes are unchanged (0 console errors, 0 overflow, 0 texts
under 4.5:1, 0 tap targets under 44 px, smallest text 13 px). The 404 page first measured 3 of 9 tap targets under
44 px on a phone (plain links in a `.facts` line); they became `.crumbs` links and the re-measure
([`etapp0-404.json`](docs/moodud/etapp0-404.json), pictures `etapp0--404--*.webp`) is 0 of 9. The OG card
(`web/public/og.png`, 1200×630) is rendered by headless Edge from the same fonts and tokens: paper, ink, the
signal rule, the three status marks and the seven register cells — no illustration.

## 13. Measured, 2026-10-29 — register scope states

Two new matrix states (§6): dotted `--ok` = the country has no listing for this class, faint + `?` = coverage not
confirmed. Routes: home table, the legend, a wallbox family (Deye SUN-EVSE) and a meter family (Sungrow DTSU666)
([`routes-scope.json`](docs/moodud/routes-scope.json)): [`scope.json`](docs/moodud/scope.json), 16 pictures, 0 errors,
0 overflow, 0 texts under 4.5:1 (lowest 5.29). The legend route found 5 of 5 tap targets under 44 px on a phone: the
home timeline's "register snapshot" links (17 px), which earlier routes never scrolled to. Timeline labels are now
44 px links on a phone; re-measure [`scope-parast.json`](docs/moodud/scope-parast.json) 0 of 4 and 0 of 7.

