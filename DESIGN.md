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

Since 2026-10-29 the site answers **two questions for two audiences at once** (Madis: hybrid target groups — local Home Assistant/evcc users and grid-connection compatibility): the home page's heading, lede, facts line and OG card carry both, the register cross-view is the front door for the grid side, and the kind switch (§6) splits inverters from wallboxes. Moment 1 is why the home page **starts with a search box that takes model codes** (`SUN-12K-SG04LP3`,
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
| **Kind switch** (`.kind`, `.hero` on the home page) | home, the first thing on the page, before the search | two 44 px toggles with a line icon, the word and the count: **Inverters** (string, hybrid, battery and plug-in units — everything that feeds the grid) and **Wallboxes**. Pressed = the `--signal` edge, like an active filter; pressing again shows every kind (meters included). State in the URL (`g=inv` / `g=ev`); the class select narrows further. Madis, 2026-10-29: "all inverters under one icon, a second for wallboxes, that is enough for now" and "the question does not need to be there, just two icons" — the h1 is visually hidden, the two 64 px toggles open the page. |
| **Filter bar** | home | plain `<select>`s that name themselves ("All brands"); labels above them on wide screens, visually hidden on a phone so the filters take three rows, not a screen. The active filter gets the `--signal` edge; state lives in the URL. Sticky sidebar from 80 rem. |
| **Family table** (`FamilyTable.astro`) | home, brand pages | sticky head with 2 px rule; 34 px rows; brand in `--ink-2` before the family name; one status per column; matrix; model count right-aligned with tabular numbers. **Under 48 rem it stacks**: one block per family, the name as a 44 px link, the statuses on one line with their column name as a prefix, the matrix on its own line. |
| **Register matrix cell** (`Matrix.astro`) | every table, verdict | six fixed cells in fixed order (AT CZ EE NL PL SE). Filled = listed; outlined + `*` = listed with the register's own restriction word; faint outline = the list covers this class but no model was found; **dotted `--ok` outline on `--ok-bg` = the country has no listing for this class** (a wallbox is a load; only AT lists chargers), nothing to check; **dotted `--cloud` on `--cloud-bg` = no list, but a rule applies** (a notification, a registration, a ban), the note under the verdict says which; faint + `?` = coverage not confirmed (`SCOPE` in `gridfit/registers.py`, from the EU+ table of 2026-10-29). Shape first, colour second: dotted vs solid, `*` vs `?`. One accessible label reads all six. |
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

## 8b. One database, two lenses (2026-10-30)

The site answers two questions about one set of devices, so it has **one resolver** and **two views**, not two
sections. `web/src/lib/devices.ts` joins the integration families (`data.ts`) with the register devices
(`registers.ts`) and is the only place that decides a device's local state (`control / read / cloud / brand route /
not found`) and its grid cell per country (`listed / restricted / expired / not found / rule / free / banned /
unknown`; the last five come from `data/countries.yaml`, the EU+ grid-connection table). Every page reads through it.

| path | what | why |
|---|---|---|
| `/` | the two kinds, the search (submits to `/local/`), the two doors, the latest changes; no JS | the reader picks a lens or types a code |
| `/local/` | one row per family: HA, evcc, control, connection, the 7-list matrix | the smart-home lens; the grid lens is a column |
| `/grid/` | one row per register model (14 411), the 7 lists as cells, the local lens as a column; `index.json` + 100-row paging | the grid lens; the smart-home lens is a column |
| `/grid/{cc}/` | one page per EU+ country (43): what applies per device class; the 7 parsed lists also get the list's facts, rows by class, status words, changes | "what does my country do?"; unparsed countries are `noindex` until their notes exist |
| `/{brand}/` | both lenses on one page: `#local` families, `#grid` every list model with an anchor `#m-{code}` | one brand, one URL; 672 brands across both halves (the family slug wins) |
| `/{brand}/{family}/` | the device page: glance bar, `#local` (verdict, evidence), `#grid` (one row per parsed list with the list's own words, the other 36 countries grouped, the model codes with every cell) | one page per device, both answers |
| `/{brand}/model/{code}/` | a register model no family claims, in two or more lists (3 595): grid first, local = brand route or not found | the same skeleton, the other way round |
| `/changes/` | both logs | — |

**Arrival decides the order, not a cookie.** The device page renders the local block first; CSS
`.device:has(#grid:target, #grid-sec :target)` puts the grid block first when the reader arrives at `#grid`,
`#grid-{cc}` or `#m-{code}` (`/grid/`, country and brand pages link that way). A model page is grid-first and flips
on `#local`. The target row or country gets the signal edge. No JavaScript, no referrer sniffing.

**Grid first (2026-10-31).** The home page asks "is it fit for the grid in …?": a country select (the 7 lists read first, then
public / partial / none), a model-code search that submits to `/grid/`, the two kinds, and the smart-home view as the second
door. `/grid/` is a query: countries are a multi-select with AND logic ("on every selected list"), the columns are the selected
countries (or the 7 read when none is selected), a country without a list shows what applies to the class there, and phases
and rated power (from the AT, SE and BE lists; no list carries MPPT counts) are filter columns. `/grid/{cc}/` is the same view
with that country preselected, under the country's class table. A tiny Pages Function (`functions/api/cc.js`) returns
Cloudflare's `CF-IPCountry` so the home page can *offer* the visitor's country (never redirect; nothing stored server-side;
the user's own choice is kept in `localStorage`); elsewhere the browser language is the guess.

**One vocabulary for 43 countries.** A register's own word ("Nein", "befristet") is detail, not a category. Per model × country
the site uses: `listed` · `listed, conditions` · `expired` · `not accepted` · `not found` (on a list that covers the class) ·
`no list, a requirement applies` · `nothing to check` · `not allowed` · `unknown`; the evidence layer will add `documented`
(the maker publishes a document against the country's named standard and version — the grid operator decides) and
`general certificate` (EN 50549-1 without a country profile). The register's word stays in the cell's title and on the device page.

**Partial data has words.** A family with no list match shows, per country, what the table says: no list for the class
(dotted green), a rule without a list (dotted amber), not allowed (struck), not confirmed (`?`) — never a bare
"not found" when the country has nothing to find. A register model with no integration row shows "brand route, model
unconfirmed" when the brand has a local family, else "not found", and says which sources were read.

**Reserved first segments** (`local grid changes about model search data devices sitemap 404 llms robots models`): the
build throws when a brand slug collides, or a family slug is `model`.

## 8c. The grid cell: three answers, detail on hover (2026-10-31)

Madis: "too many categories; think of them together with the visual side; mark, background, and a hover with the
detail". The cell now answers one question — *fit for the grid here?* — with three answers, and nothing else is a
category:

| answer | cell | means |
|---|---|---|
| **✓** filled `--reg` | fit | a model of the family (or the model) is on the country's official list, with or without a condition |
| **✓** outlined, dashed | fit by the maker's document | no list row, but the maker publishes a document against the country's named standard — the grid operator decides (evidence layer, later) |
| **✕** `--cloud` outline | not fit | the list says no, the entry expired or its end date passed, or the class is not allowed |
| empty, faint rule | nothing known | not found on the list, no document found, the rule not confirmed, or nothing to check for this class |

Everything that used to be a category is now in the hover (`Cell.astro`): the list's own word ("Ja - befristet bis
2027-03-31", "Nein"), the end date, firmware, the certificate or document number, the row as written, and a link to the
list or the country page. On device pages the hover is a CSS tooltip that also opens on keyboard focus (`rich`); in
the dense tables (732 families, brand pages with hundreds of models, the grid view) it is the `title` attribute, so a
page carries 5 000 cells without 5 000 tooltips. The country's rule for the class — list / certificate / — — sits in the
grid view's column head, not in every cell. `GRID_WORD` and the register words stay for the aria-labels and the
device page's list rows. Colour repeats the shape: filled vs dashed vs outlined vs empty read in greyscale.

## 8d. A country without a list: one answer per model, and the counts add up (2026-10-31)

Madis, after the first evening with the filters: "many problems … a product that actually is free of rookie mistakes".
Two rules came out of the walkthrough, and the grid view is built on them now.

**Every filter is a partition.** The "Any … (N)" count equals the sum of its options, always, because a missing value is
an option of its own — *Phases not specified*, *Power not specified*, *MPPT not collected* — and a value the class cannot
have is named, not blank: *No MPPT: battery, AC inverter or wallbox*. The overlapping options went (Local "read or control"
⊇ "control"; "Other lists: 1 or more" ⊇ "3 or more"; the Smart home select that mixed Home Assistant and evcc): Local,
Home Assistant and evcc are three selects of five disjoint routes each, Other lists is none / 1 / 2 / 3 or more. The logic
lives once, in `web/src/lib/grid-filter.js`, imported by the page and by `web/test/facets.mjs`, which proves the sums over
the built index in fifteen states (`npm test`). An option that would leave nothing is hidden, so the 47 wallbox-only brands
no longer sit as "(0)" in the inverter view.

**One status per model and country.** The status group used to count "any cell with that status" over the seven lists,
so its counts overlapped and in Spain — no list — every model was "Not on the list". Now a model has exactly one status
in each chosen country, and the group filters by the best of them (or the worst, with "in every chosen country"). In a
country whose list we read: on the list · with a condition · refused or expired · not on the list. In a country without a
list, or whose list is not read, in this order:

| answer | cell | from |
|---|---|---|
| fit by the maker's document | ✓ dashed (`--reg`) | `data/evidence/<brand>.yaml`: the maker's released-countries document names the country |
| over the type-A limit | **B**, outlined, muted | the country profile's `type_a_max_kw` (Spain: 100 kW, RD 647/2020 art. 8) and the model's kVA |
| accepted on other EU lists | ○ dotted, muted | a positive entry on at least one list read; the hover names them |
| nothing known | empty | its only listings are expired or refused |

plus *not fit* (a banned class), *nothing to check* (—) and *not confirmed* (?). Words, not percentages; the hover says
why ("accepted on 5 other EU lists (AT, EE, NL, PL, SE) — nothing checked here; Spain has no list: the grid operator
checks the maker's certificate"). The device pages group the 36 other countries by the same answer, with the reason and the
document under each group (`GridBlock.astro`), so a model page can justify what the grid cell only states. The status group
moved to the top of the filters, under the countries, because status is the question. The "Smart home" column head is
the two words, nothing else (Madis: the icons wrapped and looked messy); the icons stay in the cells and the legend.

A side effect of the walkthrough: the family join re-normalised model codes locally ("3.0" kept its zero, the parser
drops it), so 400 models that belong to a family had pages of their own; `data.ts` now joins by the parser's `norm`.

## 8e. The traffic light (2026-10-31, late)

Madis, after seeing §8d live: the status categories should all be shown all the time, ordered from highest to lowest
confidence, "nothing to check for this class" says nothing to a reader, and a traffic light would make sense. So the cell
and the status group are now one ladder in three colours, shape repeating colour so it reads in greyscale:

| | cell | status word |
|---|---|---|
| green — fit | `--ok` filled ✓ · outlined ✓ · dotted ✓ | on the list · with a condition or end date · nothing to approve for this kind of device |
| amber — the operator decides | `--cloud` filled ✓ · outlined ○ · dotted B | likely fit: the maker's document names the country · possibly fit: accepted on other EU lists · other procedure: over the type-A limit |
| red — not fit | `--no` filled ✕ (new token, light `#8f1d1d` / dark `#f2a8a8`) | refused, expired or not allowed |
| grey — unknown | `--unk` outlined ? · empty | not confirmed · not on the list / nothing known |

Green moved from `--reg` (blue, the register colour) to `--ok`; the amber that used to say "not fit" now says "likely /
possibly", and red says "not fit" — the one place colour semantics changed, so every cell, the device pages' list words
(`.rs-*`) and the About page moved together. "Nothing to check for this class" became "nothing to approve for this kind of
device" and sits in green: a wallbox in Estonia is a load, nothing gates it, so it is fit as far as a list goes. The status
group shows all nine categories always, in this order, zero counts in lighter ink, so the reader sees the whole ladder
and where the chosen country's models fall on it.

## 8f. Legacy models (2026-11-01)

Madis: old models nobody searches for any more are noise in the table — hide them by default, with a way to include them.
The flag is evidence, never an age guess (`web/src/lib/legacy.ts`), in three tiers, each carrying its reason in words:

| tier | means | reason on the model page |
|---|---|---|
| A, sure | every entry the model has is expired, past its end date or refused | "expired or refused on every list that carries it (AT: time-limited until 2023-03-31; BE: expired)" |
| B, sure | the maker's own archive or end-of-life page names it (`data/legacy/<brand>.yaml`) | "Kostal lists it as discontinued — “…” (archive page, seen …)" |
| C, probable | the oldest list date (SE reviewed, CZ added) is more than six years old, no list has changed the entry since, and the brand has a newer generation of the family on the lists (`data/legacy/generations.yaml`) | "the SE entry dates from … and no list has changed it since; Deye has a newer generation on the lists (SG04LP3 → SG05LP3; e.g. …)" |

No date (AT, BE, EE, NL carry none; PL's are end dates) means current. On 2026-11-01 the lists' oldest dates are 2021, so
tier C marks nothing yet and will start to as the data ages; tier B waits for the archive pages. The grid view hides
legacy rows unless "Include legacy models (N)" is ticked (`legacy=1`); the count line says how many are hidden with a
one-click "include"; **a search by model code ignores the hiding**, because the owner of a 2017 inverter and the
second-hand buyer must always find it. Legacy rows carry a grey `legacy` tag (`legacy?` for tier C); the model page
states the reason under the header; the brand page lists them in a section of their own at the end; the family page
tags them in the model-codes table. The count test treats the toggle as a toggle: off leaves the current rows (or
everything when there is a search text), on leaves them all.

## 8g. A list country's second level (2026-11-01)

Madis: Estonia showed 11 678 models as "not on the list", although every one of them is on some other list and
Elektrilevi takes a model that is not on its list with extra documents. So a cell in a country whose list we read now has
two levels. The first is the list's own word — green on the list, green outlined with a condition, red refused or
expired. A model **off the list** gets the second level by the same amber ladder as a country without a list
(`grid-filter.js ladder()`, `devices.ts subTiers()`): likely fit when the maker's document names the country, over the
type-A limit when the profile's ceiling says so (Estonia 500 kW), possibly fit when it is accepted on other EU lists
(this one excluded), else nothing known. The words of what the country does with such a model come from the profile's
`not_listed_short` ("Elektrilevi takes a model that is not on the list with extra documents …"; Spain: the maker's
certificate at the operational notification) and sit in the hover, in the note under the count line and on the device
page's list row ("Not on the list — likely fit: the maker's document names Estonia · Elektrilevi takes …"). The status
group's labels say "Not on the list — likely fit …" when every chosen country has a list, so the ladder reads as the
second level it is. Estonia on 2026-11-01: 2 214 on the list; off the list 41 likely, 9 850 possibly, 1 252 over the
type-A limit, 535 nothing known (all of them legacy, hidden by default). "Type A fits" was asked for and not added: under
the ceiling is the normal case, so it would mark everything and say nothing.

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

Same day, a fourth state from the EU+ grid-connection table: dotted `--cloud` = no list, but a rule applies (CZ and PL
plug-in notifications, the EE AC-battery application, the SE plug-in ban), with the note under the verdict.
Legend, plug-in family (APsystems EZ1) and wallbox family ([`routes-scope-rule.json`](docs/moodud/routes-scope-rule.json)):
[`scope-rule.json`](docs/moodud/scope-rule.json), 12 pictures, 0 errors, 0 overflow, 0 under 4.5:1, 0 tap targets under 44 px.

## 14. Measured, 2026-10-29 — kind switch first, the question for machines

Home page with the two toggles (Inverters 250 / Wallboxes 343) as the first thing before the search, the h1 visually
hidden ([`routes-kind.json`](docs/moodud/routes-kind.json): home, and home with `?g=ev` scrolled to the count):
[`kind.json`](docs/moodud/kind.json) (switch above the table, first version) and [`positsioon.json`](docs/moodud/positsioon.json)
(final), 8 pictures each, 0 errors, 0 overflow, 0 texts under 4.5:1 (lowest 5.68), 0 tap targets under 44 px
(0 of 14 / 0 of 5). The OG card carries the two-question heading.

## 15. Measured, 2026-10-30 — one database, two lenses

13 routes ([`routes-arh.json`](docs/moodud/routes-arh.json): home, `/local/` top and table, `/grid/` top and table filtered to EE,
`/grid/ee/`, `/grid/fr/`, the Deye LP3 device page top and at `#grid-ee`, the Sungrow brand page top and at `#grid`, a register
model page, 404) × 3440/390 × light/dark = 52 pictures: [`arh.json`](docs/moodud/arh.json). 0 console errors, 0 overflow,
0 texts under 4.5:1 (lowest 5.68). Two findings on the device page's grid block: the "36 more countries" links were
sentence links under 44 px on a phone (36 of 48) and the confidence marks were 11.7 px `<sup>`s; both fixed
(44 px inline-flex links, 13 px marks), re-measure [`arh-parast.json`](docs/moodud/arh-parast.json) 0 of 40 and 0 of 13.
Pages: 5 048 (732 families, 3 595 model pages, 672 brands, 43 countries) — down from 7 267; `/registers/**` is gone.

## 16. Measured, 2026-10-31 — grid first

Home (country select, search, kinds), `/grid/` top and the table, `/grid/?c=FI,ES,PL&ph=3` (three countries, two without a
list), `/grid/ee/` top and table, `/grid/fr/`, the open country picker ([`routes-0c.json`](docs/moodud/routes-0c.json)) ×
3440/390 × light/dark: [`c0.json`](docs/moodud/c0.json) 28 pictures. Findings: the home page logged a 404 for `/api/cc` outside
Cloudflare (now guarded by hostname), the grid table overflowed 14 px on a phone (the Lists column is hidden there now, legend
keys wrap, the "Show more" button wraps), phases were empty in the index (`tools/site_data.py` now exports `phases`), and
three list links in the panels were 21 px (44 px now). Re-measure [`c0-parast.json`](docs/moodud/c0-parast.json): 0 errors,
0 overflow, 0 under 4.5:1 (lowest 5.89), 0 tap targets under 44 px. Phases known for 6 229 of 14 411 models, kVA for 11 501.

## 17. Measured, 2026-10-31 — three-answer cells

`/local/` table, `/grid/?c=FI,ES,PL&ph=3`, the Deye LP3 device page top, at `#grid-ee` and with a glance cell focused
(tooltip open), the Sungrow brand page at `#grid`, a register model page ([`routes-cell.json`](docs/moodud/routes-cell.json))
× 3440/390 × light/dark: [`cell.json`](docs/moodud/cell.json), 28 pictures, 0 console errors, 0 under 4.5:1 (lowest 5.68).
Findings: the column-head rule word overflowed 15 px on a phone (hidden there now), the row-count `<sup>` was 10.8 px
(13 px now), a focusable cell was 26 px on a phone (44 px there now). Re-measure [`cell-parast.json`](docs/moodud/cell-parast.json):
0 overflow, 0 under 12 px, 0 tap targets under 44 px. Page weight: `/local/` 43 KB gz (33 KB before the titles), a
brand page with 412 models 13 KB gz, a device page 12 KB gz.

## 18. Measured, 2026-10-31 — datasheet specs (MPPT, kW)

`/grid/` table, `/grid/?c=EE&mppt=2`, the Deye LP3 and GoodWe ET family pages at `#codes` (MPPT and kW columns, datasheet
footnote), the Deye SUN-10K-SG04LP3-EU model page at `#grid` (Datasheet block) ([`routes-spec.json`](docs/moodud/routes-spec.json))
× 3440/390 × light/dark: [`spec.json`](docs/moodud/spec.json), 20 pictures, 0 console errors, 0 overflow, 0 texts under 12 px,
0 under 4.5:1 (lowest 5.68), 0 tap targets under 44 px. The MPPT column and filter sit beside phases and kVA; on a phone
the `.sp` columns stay hidden as before and the model page's Datasheet block carries the figures. Rows: 290 for three brands;
on the EE list 51 models answer "2 MPPT".

## 19. Measured, 2026-10-31 — Spain profile

`/grid/es/` top and at `#how` ([`routes-es.json`](docs/moodud/routes-es.json)) × 3440/390 × light/dark: [`es.json`](docs/moodud/es.json),
8 pictures, 0 console errors, 0 overflow, 0 under 12 px, 0 under 4.5:1 (lowest 6.98), 0 tap targets under 44 px. The profile block's
headings now follow the country: “How a model is accepted” / “If the model has no certificate” where there is no list.

## 20. Measured, 2026-10-31 — the front door

The country page and `/local/` open on one question (“Is my inverter fit for the grid operator's list in Estonia?” /
“Does my inverter work locally with Home Assistant and evcc?”), the other question as a small link under it, and the two
kinds as one-line icons — the active one ringed and a step larger; the wallbox icon swaps the question. The site nav moved
to the foot; the device-class select is gone (the kind is the class). `/` is a Pages Function: the gf-cc cookie (set when
a country is picked on the home page) or CF-IPCountry sends the visitor to `/grid/{cc}/`; crawlers and `/?all` get the
neutral home. `/grid/ee/`, `/grid/ee/?g=ev`, `/grid/es/`, `/local/`, `/local/?g=ev`, `/` ([`routes-uks.json`](docs/moodud/routes-uks.json))
× 3440/390 × light/dark: [`uks.json`](docs/moodud/uks.json), 24 pictures, 0 console errors, 0 overflow, 0 under 12 px,
0 under 4.5:1 (lowest 5.68), 0 tap targets under 44 px.

## 21. Measured, 2026-10-31 — Local and Smart home columns, /local/ retired

The smart-home lens is two columns in the grid table: **Local** is the best route on the visitor's network (control / read /
cloud / brand route, the `.st` chips) and **Smart home** is who talks to it — one glyph each for Home Assistant and evcc
(GridFit's own one-line glyphs, not the projects' logos), filled green for local control, green outline for local read,
amber for cloud only, dotted grey for a brand route, empty when nothing was found; the title carries the words. `/local/`
is gone (301 to `/grid/`); the family pages keep the local detail. `/grid/ee/`, `/grid/ee/?lo=W`, the legend, a family
page and the 404 ([`routes-sh.json`](docs/moodud/routes-sh.json)) × 3440/390 × light/dark: [`sh.json`](docs/moodud/sh.json),
20 pictures, 0 overflow, 0 under 12 px, 0 under 4.5:1 (lowest 5.68), 0 tap targets under 44 px; the only logged errors are
the preview server's plain 404 for the 404 route (Pages serves `404.html`).

## 22. Measured, 2026-10-31 — the country picker

The 43 checkboxes left the sidebar. The picker is: chips for the chosen countries (each with a 44 px remove button), a
typeahead that matches code and name and shows the group word beside each hit (keyboard: arrows, Enter, Escape; combobox
roles), the 7 read lists as quick toggles, and “All 43 countries…” opening a `<dialog>` with the grouped list, live.
Pattern after Baymard's truncation findings (≤ 10 visible values, a clearly visible “more” right under them) and the
GOV.UK / Agriculture DS accessible autocomplete. `/grid/ee/` closed, typeahead open (“sp”), dialog open, and
`/grid/?c=FI,ES,PL&ph=3` ([`routes-cc.json`](docs/moodud/routes-cc.json)) × 3440/390 × light/dark: [`cc.json`](docs/moodud/cc.json),
16 pictures, 0 console errors, 0 overflow, 0 under 12 px, 0 under 4.5:1 (lowest 5.68), 0 tap targets under 44 px. One
finding by eye: the column-head rule word “certificate” clipped in a narrow column at 3440 — now “cert.”.

## 23. Measured, 2026-10-31 — countries are columns, status is the filter

Six asks in one sitting, the same evening. Countries no longer filter: a chosen country is a column, and a model off
its list stays with an empty cell, which is the answer the first question needs (the model that is not on the list used
to vanish, and seven lists at once kept 8 models — AND logic nobody asked for). The rows the chosen lists carry sort
first. **Status** is a checkbox group in the cells' own words — fit / fit with a condition or end date / not fit / not on
the list — ticked together they add up (OR), and “in every chosen country” (shown from two list countries on) is the
installer's AND. **Other lists** replaces “Lists”: the read lists a model is on *besides* the chosen countries, a hint of
what the maker has had certified where there is no list to check, never an approval. The smart-home filter is two, like
the columns: **Local** (best route) and **Smart home** (Home Assistant, evcc). Every option carries in brackets the number
of models it would leave with the other filters as they stand (facet counts: one pass keyed by brand for the 500 brand
options, the search debounced 120 ms; one apply ≈ 0.2 s over 13.9 k rows). The filters follow the kind: wallboxes have no
MPPT, so that filter and column go. The HA/evcc link under the country question is gone. `/grid/ee/`, `/grid/at/?st=CX`,
`/grid/ee/?st=-&brand=Deye`, `/grid/es/?n=3&lo=W&sh=HW`, `/grid/ee/?g=ev`, `/grid/?c=AT,EE&st=Y&every=1`
([`routes-filters.json`](docs/moodud/routes-filters.json)) × 3440/390 × light/dark: [`filters.json`](docs/moodud/filters.json),
24 pictures, 0 console errors, 0 overflow, 0 under 12 px, 0 under 4.5:1 (lowest 5.29), 0 tap targets under 44 px. One
finding on the way: an `<option>` without a `value` takes its text as value, so the count in the text broke the brand
filter — every option now has an explicit value.

## 24. Measured, 2026-10-31 — the user's walk, counts that add up, a country without a list

Madis's brief for the evening: walk the site as a user and do not stop before it is a viable product; three named faults
(the counts, Spain, the small things). Fifteen routes ([`routes-toode.json`](docs/moodud/routes-toode.json): the home page,
`/grid/es/` open and with "fit by the maker's document" ticked, `/grid/ee/`, `/grid/?c=AT,EE,ES&every=1&st=YCD`, the wallbox
view, `/grid/ee/?mppt=0`, the Kostal PLENTICORE family page at the grid block and at "the other 36 countries", the Elecod
Monet-100AC model page at the top and at the same block, the Kostal brand page, How we know, Changes, 404) × 3440/390 ×
light/dark, three rounds, the last on the final build with the evidence layer and the three new datasheet brands:
[`toode.json`](docs/moodud/toode.json), 60 pictures, 0 console errors, 0 failed requests, 0 px overflow, 0 texts under 12 px
(smallest 13 px), 0 under 4.5:1 (lowest 5.29), 0 tap targets under 44 px of 1 596 (round 2 found one: the model search box in the filters was 21 px tall on a phone — it had no rule of its own, the selects had; now 44 px like them). Proved by script, not by eye:
`web/test/facets.mjs` over the built index — 796 checks in fifteen filter states, 0 failures: every "Any" equals the sum of
its options, every category has an option, choosing an option leaves exactly its count, every cell has a legend word. Two
findings by eye between the rounds as well: the sidebar's status counts floated away from a wrapped label (now inline after the
words), and a device page listed the same Kostal document once per family (now once, naming the families). Spain after the
round: 13 892 inverters, 245 fit by the maker's document, 2 174 over the type-A limit, 10 977 accepted on other EU lists,
496 nothing known.

## 25. Measured, 2026-10-31 — the traffic light

The same fifteen routes as §24 × 3440/390 × light/dark on the §8e build: [`toode.json`](docs/moodud/toode.json), 60 pictures,
0 console errors, 0 failed requests, 0 px overflow, 0 texts under 12 px, 0 under 4.5:1 (lowest 5.29 — the new `--no` red on
`--surface`, the amber `--cloud` fill and the green `--ok` fill all clear it in both themes), 0 tap targets under 44 px.
One regression caught in the browser before the round, not by the numbers: the status labels start hidden in the HTML for
the no-JavaScript case and the "always show all" change had dropped the line that un-hides them, so the group showed its
heading alone. The count test is unchanged (796 checks, 0 failures): colour moved, the partition did not.

## 26. Measured, 2026-11-01 — legacy models

Five routes ([`routes-legacy.json`](docs/moodud/routes-legacy.json): `/grid/at/` with its "535 legacy models hidden — include"
line, `/grid/at/?legacy=1&st=X`, `/grid/at/?q=symo+3.0` (an old code found despite the hiding), the SolaX brand page at its
"Legacy models" section, a family page at its first tagged row) × 3440/390 × light/dark: [`legacy.json`](docs/moodud/legacy.json),
20 pictures, 0 console errors, 0 overflow, 0 under 12 px, 0 under 4.5:1 (lowest 5.29), 0 tap targets under 44 px. The count
test grew to 936 checks (two legacy states), 0 failures; it also asserts that no tier-A row still has a positive list entry.
On this date: 535 legacy (all tier A: 495 refused on the Austrian list only, 40 expired on the Belgian list only), 0 tier B,
0 tier C, 13 925 current.

## 27. Measured, 2026-11-01 — the second level

Five routes ([`routes-kaks-taset.json`](docs/moodud/routes-kaks-taset.json): `/grid/ee/`, `/grid/ee/?st=D`, `/grid/ee/?st=K&brand=Fox ESS`,
the Sungrow SH family page at its grid block and at its Estonia row) × 3440/390 × light/dark: [`kaks-taset.json`](docs/moodud/kaks-taset.json),
20 pictures, 0 console errors, 0 overflow, 0 under 12 px, 0 under 4.5:1 (lowest 5.29), 0 tap targets under 44 px. The count
test is unchanged at 936 checks, 0 failures — the second level only moved rows between categories of the same partition.
