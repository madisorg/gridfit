# GridFit

**Does this solar inverter, home battery or wallbox work locally with Home Assistant and evcc — and which EU grid registers list it?**

A static site and an open dataset, built only from open sources. For each product family it shows the
Home Assistant core and HACS integrations and the evcc templates that support it, whether they talk to the
device on your network or through a cloud, whether they can *control* it or only read it, and which national
grid registers list its models. Every row links to its source and carries the date it was last seen.

A second section, **[/registers/](#grid-register-cross-view)**, is a cross-view of seven national grid-connection
lists (AT, BE, CZ, EE, NL, PL, SE): for each inverter, hybrid, battery, plug-in unit and wallbox, every list's own
status word, firmware, certificate or row number and dates side by side, plus a change log of what each refresh
added, dropped or changed. It is a hobby section and does not depend on the rest.

Home Assistant core devices are already covered model by model by the
[Open Home Foundation Device Database](https://device-database-preview.openhomefoundation.org/) (preview);
GridFit links there instead of copying it, and adds what it does not cover yet: HACS custom integrations,
evcc, read-vs-control, and register listings.

## Build

```bash
pip install -r requirements.txt
python build.py              # downloads what is older than 6 days into cache/, then builds
python build.py --refresh    # downloads everything again
python build.py --offline    # builds from cache/ only
python build.py --registers-refresh      # also downloads the seven grid registers, parses, snapshots, diffs (monthly)
python build.py --registers-from DIR     # same, from register files already downloaded into DIR
python -m http.server 8390 -d site   # preview at http://localhost:8390
```

One command builds from nothing: `cache/` and `site/` are git-ignored and recreated. The build makes about
1 000 small requests to `raw.githubusercontent.com` (manifests and HEAD probes) and never uses the
rate-limited GitHub REST API, so it needs no token.

Environment variables (both optional):

| variable | effect |
|---|---|
| `GRIDFIT_BASE_URL` | e.g. `https://example.eu` — canonical links, `sitemap.xml`, `robots.txt` sitemap line |
| `GRIDFIT_ANALYTICS` | `plausible:<domain>` or `cloudflare:<beacon token>` — cookie-free analytics tag; empty = none |

## What is in the repo

| path | what |
|---|---|
| `build.py` | the one command |
| `gridfit/` | fetch, assemble, render |
| `templates/`, `static/` | Jinja2 templates, CSS, a small vanilla-JS filter |
| `data/curated/brands.yaml` | brand spellings → one canonical name |
| `data/curated/ha_core.yaml` | which HA core integrations are energy devices, and their brand/class |
| `data/curated/hacs.yaml` | which HACS repos are energy device integrations, what their README says they cover |
| `data/curated/families.yaml` | product families of the main brands: model-code pattern + evcc templates |
| `data/dataset/` | **the dataset** (generated, committed): `rows.json` / `rows.csv`, `families.json`, `changelog.json` |
| `gridfit/registers.py` | register cross-view: download, snapshot, diff, device join, `listing.json` for the family pages |
| `tools/registers/parse.py` | the register parser (runs as `python -I`, never inside the download directory) |
| `data/registers/alias.json` | maker spellings in the registers → one canonical maker |
| `data/registers/snapshots/<date>.json.gz` | one parsed snapshot per refresh (generated, committed) |
| `data/registers/changelog.json` | added / removed / changed rows between snapshots (generated, committed) |
| `data/registers/listing.json` | membership only, read by the family pages (generated, committed) |
| `tools/watch/`, `data/watch/` | the freshness watch: `python tools/watch/run.py` looks for new models in maker sitemaps, the grid lists between refreshes, evcc / Home Assistant / HACS and the trade press, checks each code against the lists and families, and writes `docs/watch-report.md` (weekly in `refresh.yml`; JavaScript pages with `--edge` on madis-pc). Sources, rhythm and what is deliberately not read: [`docs/freshness.md`](docs/freshness.md); a missing model can be reported with the "Missing model" issue form |
| `data/countries.yaml` | one row per EU+ country (43): public list yes / partial / no, and what applies per device class (list / rule / free / banned / unknown) — from the EU+ grid-connection table of 2026-10-29 |
| `data/profiles/<cc>.yaml` | country requirement profile: who decides, the basis, what a type A model must meet, the documents, thresholds, what counts as “fit by the maker's document” — each fact with its source; rendered as “How it works in …” on `/grid/{cc}/`. 2026-10-31: EE (Elektrilevi list) and ES (no list; the maker's equipment certificate under RD 647/2020, TED/749/2020 and the NTS, carried by the installer) |
| `data/specs/<brand>.yaml` | datasheet layer: MPPT count, rated kW/kVA, max AC current, phases, max PV per model code, each row with the maker's sheet (URL, version where the sheet has one, seen date). Drafted by `tools/specs/draft.py` from `tools/specs/table.py` / `fronius_pages.py` readings of the sheets in `cache/specs/`, corrected by hand in the drafter; `tools/specs/build.py` exports `web/.data/specs.json` and prints coverage. 2026-10-31: Deye (41 sheets, 198 rows), Fronius GEN24 (28 help-center pages), GoodWe (12 sheets, 64 rows), Kostal (3 sheets, 19 rows), SMA (4 sheets, 13 rows), Fox ESS (18 sheets, 127 rows), Growatt (31 sheets, 159 rows), Solis (28 flyers, 133 rows); 741 rows, 670 register models get one. `mppt: 0` is a sheet that states no PV input (AC-coupled units: Fox ESS AC1 G2, Growatt SPA, Solis S6-EA1P); a battery, AC inverter or wallbox has no MPPT by its class. `tools/specs/dom.py` renders a JavaScript download centre through headless Edge (the homelab's ui-kontroll launcher) to find the links; SolaX and Hoymiles have an API route found but not harvested, Sungrow, Sofar, Sigenergy and SolarEdge hide their files behind scripts or 403, SAJ not started, Huawei excluded (its terms forbid automated access). No list carries MPPT counts; a model without a row shows "not collected" |
| `data/evidence/<brand>.yaml` | evidence layer: the maker's own released-countries or certificate document, family by family — document URL, version, seen date, the countries it names, and a `match` regex over the register model code. A model in a country without a list (or whose list is not read) shows “fit by the maker's document” from this and nothing else. 2026-10-31: Kostal (“Released countries” 10/2026, 11 families × 21 countries), Sungrow (“Product Certification and Country Code Overview (Europe)” v3.5, six residential families — the per-hardware-version availability glyph is an image and is not read), and Spain (RD 647/2020, UNE 217002, NTS), Italy (CEI 0-21) and Germany (VDE-AR-N 4105) certificates for Deye, Fox ESS, Fronius GEN24, GoodWe, Hoymiles MIT, SMA STP X, SolaX and Solis — 392 register models. Zero-export certificates (UNE 217001 / ITC-BT-40), generic EN 50549-1 and parameter guides are not evidence and are left out; Huawei is excluded, SolarEdge, Sigenergy, Enphase, Growatt and Sofar keep their certificates behind scripts or 403 |
| `web/src/lib/grid-filter.js`, `web/test/facets.mjs` | the grid view's filter logic, shared by the page and the count test: every filter is a partition (the “Any” count equals the sum of its options; a missing value is its own option — “not specified”, “not collected”, “no MPPT”) and a model has exactly one status per country. `cd web && npm test` runs it over the built `dist/grid/index.json` |
| `functions/api/cc.js` | Cloudflare Pages Function: the visitor's country from `CF-IPCountry`, for the home page's "open the … view" offer; nothing stored |
| `web/` | the site (Astro, static): `src/lib/devices.ts` is the one resolver over both halves; pages `/local/`, `/grid/`, `/grid/{cc}/`, `/{brand}/`, `/{brand}/{family}/`, `/{brand}/model/{code}/`, `/changes/` (DESIGN.md §8b) |

## Sources and licences

| source | used for | licence / terms |
|---|---|---|
| [home-assistant/core](https://github.com/home-assistant/core) `generated/integrations.json`, component `manifest.json`, platform files | name, `iot_class`, quality scale, settable platforms | Apache-2.0 |
| [HACS](https://hacs.xyz/) store data (`data-v2.hacs.xyz/integration/data.json`) | repo name, domain, stars, last update | facts about public repos |
| each listed HACS repo's `manifest.json`, platform files, README | `iot_class`, settable platforms; the curated "covers" text | facts only; each repo has its own licence |
| [evcc-io/evcc](https://github.com/evcc-io/evcc) `templates/definition/{meter,charger}` | brand, product, connection params, capabilities, sponsor flag | MIT; components needing an evcc sponsorship are excluded from MIT (`LICENSES/exclusions.md`) — the exclusion header sits only in Go driver files, not in the YAML templates. GridFit copies no template content, only the fact of support, and marks sponsor-only templates |
| grid registers AT, CZ, EE, NL, PL, SE | family pages: "this register lists this model". `/registers/`: also each row's status word, firmware, row/document number and dates | the registers publish the lists but **none states reuse terms**; GridFit links every row back and says the register is the authority. These columns are the registers' facts, not GridFit's work, and are not under GridFit's CC BY |
| Belgium, Synergrid C10/26 | `/registers/` only: "listed" / "expired" + link; nothing else of a row is stored | its terms allow personal use only; a permission letter is drafted. Family pages do not use it |

Database right: copying most of a list's columns is the kind of extraction a database maker can object to.
GridFit is a non-commercial cross-reference with a link on every row; if a register asks, its columns go
back to membership only (one switch in `gridfit/registers.py`, as Belgium already is).

**Dataset licence:** [CC BY 4.0](LICENSE-DATA.md) — attribute "GridFit" and keep the per-row source links.
**Code licence:** [MIT](LICENSE).

## How a row is decided

- **local** — `iot_class` starts with `local_` (HA core, HACS); for evcc, the template takes a Modbus
  connection, a host/URI, or is an OCPP template. A template that only takes account credentials is cloud.
- **control** — HA: the integration has `number.py`, `select.py`, `switch.py` or `button.py` (settable
  entities; can be anything from a charge limit to a restart button). evcc: chargers always; meters when
  the template has `battery-control` or `curtail`.
- **families** — a HACS or core row without `families:` applies to every curated family of the same kind
  (wallbox / meter / everything else) of that brand. evcc rows join a family by template name.
  Register models join a family by a regex over the normalised model code — a pattern, not a confirmation;
  the site shows each model's brand-match trust (exact / alias).
- The site never says "does not work" or "not approved": an empty cell is an empty cell.
- **grid status, one per model and country** — with a list read: on the list / with a condition or end date / refused or expired / not on
  the list. Without a list (or with one not read), in this order: *fit by the maker's document* (`data/evidence/`), *over the type-A limit*
  (the country profile's ceiling; type B is another procedure), *accepted on other EU lists* (a positive entry on at least one list read —
  a hint about the maker, never an approval there), *nothing known*. A banned class is *not fit*, a class with nothing to check
  *nothing to check*, an unconfirmed one *not confirmed*. Several countries chosen: the best answer among them, or the worst with
  “in every chosen country” ticked.

## Grid register cross-view

**Refresh, once a month:** the 1st-of-the-month run of `refresh.yml` does `python build.py --registers-refresh` and commits `data/registers/`; by hand it is the same command plus the commit.

1. `gridfit/registers.py` finds each list's current file on its page (the file names carry dates) and downloads
   it with `curl` and a browser user agent into a new, empty `cache/registers/raw/<date>/`. A file that is not
   a real xlsx/PDF/CSV is rejected.
2. `tools/registers/parse.py` reads them, isolated (`python -I`), into `cache/registers/parsed/<date>/`:
   one entry per register row, the list's source date, and the rows it could not read.
3. The entries become `data/registers/snapshots/<date>.json.gz`. The build compares that file with the previous
   snapshot and writes `changelog.json`: rows added, rows removed, and changes to a row's status word,
   firmware or end date, per register. A list that cannot be downloaded or comes back empty keeps its
   previous rows. It never shows up as "every model removed".
4. The site reads only the committed files, so a plain `python build.py` never contacts the registers.

**Matching.** A device = canonical maker (`alias.json`, then legal suffixes removed) + a normalised model code
(upper case; separators, a trailing `-EU`/`-SM2` and notes such as "(Connected in Delta)" removed; `10.0` = `10`;
a power in brackets, e.g. "(5.0 kW)", is kept because it names a different unit). Every cell says how it was
matched: **exact** (the same maker and model spelling as the page title), **alias** (joined after
normalising) or **unmatched** (kept apart, never joined). Rows are marked unmatched when a PL row's maker cell
holds an address (the PDF columns shifted; 251 rows, nearly all generators and CHP), when a word crosses a PDF
column (29) or when the "model" is a pattern such as `IPES-3A-XXXX-H2-10K` (135). An empty cell means no
matching entry was found. It never means "not approved".

**Pages.** Classes with pages: PV inverter, hybrid, battery / AC inverter, plug-in (≤ 800 VA, from the lists' own
power columns; PL "mikro"), wallbox (the Austrian charger list). CHP, generators, wind, relays and EZA controllers
stay in the snapshot without pages. Every brand gets a page. A model gets its own page when it is in two or
more countries' lists; the brand table carries the rest.

**Baseline 2026-10-29:** 29,184 rows (AT 3,517 + 610 chargers, BE 9,013, NL 7,021, SE 3,502, PL 2,461, EE 2,239,
CZ 821) → 14,550 devices in the page classes from 503 makers. 5,722 devices are in ≥ 2 countries' lists and get a
model page; 2,429 are in ≥ 3. Cells: exact 18,767, alias 8,425, unmatched 145. Of the 2,215 Estonian devices,
1,483 are also in another country's list.

**Known gaps.**
- PL: 30 of 2,491 rows are unread (Lp 176–181, 1127–1136, 2051–2056, 2078–2086: generators, turbines, and
  8 Sigenergy SigenMate rows where the address column runs into the model column). They are listed on the PL
  country page.
- Names that pack several models into one cell (`SUN2000-17KTL-M0/M2/M3`, 472 single-list devices) are not split,
  so they do not join the same model in another list.
- NL lists brand and type only. CZ gives the kind of evidence (protocol/certificate and issuer), not a number.
  Only PL prints a document number. EE gives maker, model and a battery column only, and its page carries no
  date, so "list dated" stays empty for EE and a change shows up only as rows added or removed.
- PL's date column is headed "Document acceptance date", but its dates lie mostly in 2029–2031. The page shows
  the date with that caveat and does not call it an expiry.

## Hand check, 2026-10-29 — Sungrow, Huawei, Victron

Every integration and template row of the three brands was read against its source (evcc template YAML on
`master`, Home Assistant core manifests and platform files on `dev`, HACS READMEs). The capability words
match: `sungrow-hybrid`, `huawei-sun2000-hybrid`, `huawei-smartlogger` and `victron-energy` carry
`battery-control`; `sungrow-ihm`, `sungrow-inverter` and `huawei-emma` carry `curtail`; the `sungrow` and
`victron-evcs` chargers carry `1p3p`; `ocpp-sungrow` and `ocpp-huawei` require a sponsor token (flagged);
`victron_gx` (core) is `local_push` with number/select/switch/button platforms, `victron_remote_monitoring`
and `victron_ble` are sensor-only. One fix: **Sungrow Local** talks Sungrow's encrypted Modbus TCP, not HTTP,
and covers only SG5K-D with a WiFi V31 module. Curated pattern fixes found by reading the matched model codes of
all 82 curated families: Deye `SUN300G3…SUN2000G3-EU-230` are microinverters (now in the SUN-M / SUN-G3 family,
the string pattern requires the kW `K`); Hoymiles `MIT-4000…6000` are three-phase string inverters (own family);
Anker `AE103x` is Solarbank 4 (the AT list says so). Left as doubts: Fox ESS `AC-10.0-E` / `AC-12.0-E` sit in the
single-phase H1/AC1 family by their prefix. 652 of 731 families have no register listing — that is expected
(the registers list PV/storage units, the families include meters and wallboxes from evcc) and is shown as
"not found", never "not approved".

## Hand check, 2026-10-29 — registers

Deye, SolaX and Huawei against the raw AT, CZ and SE files, read by a separate script that does not use the parser.
For each brand and register, three random raw rows were compared with the snapshot: the model spelling, AT's
status word and the firmware text. **27 / 27 matched**, and the row counts per brand and register are identical
(AT: Deye 48, SolaX 183, Huawei 61; CZ: 50, 74, 19; SE: 108, 148, 59). Join check: Deye SUN-12K-SG04LP3-EU is on
one page with AT "Ja - mit Einschränkung" (firmware 1150 note), BE listed, CZ (firmware 2005/2006-1160-1807), NL
(generation and storage lists), SE (Ver >= 1090) and EE (battery: yes). It has no PL entry, which matches the PDF.
In the three brands: Deye 296 devices (167 in ≥ 2 lists), SolaX 605 (257), Huawei 144 (81).
SolaX cells all show "alias" because every list writes the maker differently ("SolaX Power", "SolaX Power
Network Technology (Zhejiang) Co., Ltd.").

## Hand check, 2026-10-29 — HA / evcc

Three brands were checked against the sources themselves (READMEs, HA docs, evcc template files, register rows):

**Deye**
- evcc `deye-hybrid-3p`: Modbus RS485/TCP, capabilities `battery-control` + `curtail` → LP3/HP3 rows "control" ✔.
  `deye-storage`: no capabilities → "metering only" ✔. `deye-evse`: Solarman Wi-Fi logger (port 8899), sponsorship → sponsor flag ✔.
- HACS *Deye Local* README: single-phase LP1 supported (verified on SUN-6K-SG05LP1), LP3/HP3 experimental,
  string/micro "recognised, not mapped yet" → limited to the three hybrid families, README caveat added as a note.
- Same README: newer WiBLE loggers (firmware `DYDA_WiBLE_*`) close ports 8899 and 502 → note added to the
  *Solarman* row, which relies on port 8899 or a Modbus TCP gateway.
- Register spot check: SUN-12K-SG04LP3-EU — AT "listed with restrictions", CZ, NL, SE listed in the raw
  parser rows; BE also listed there but excluded on purpose ✔.

**SolaX**
- HACS *SolaX Inverter Modbus* README: Gen2–Gen5 hybrids, Gen3 AC/RetroFit, X1 Air/Boost/Mini, X3 MEGA/FORTH,
  X3 MIC/PRO, Qcells Q.VOLT HYB-G3-3P; no EV charger → applies to all SolaX inverter families, not the wallbox family ✔.
- HA core `solax`: `local_polling`, no settable platforms → "read" ✔.
- evcc `solax`: `battery-control` ✔; `solax-g2` X3-MIC/PRO G2 metering ✔; X3-EVC / X3-HAC chargers RS485 + sponsorship ✔.
- **Fixed:** the *SolaX Local X1 Micro* repo had spread to every SolaX family; now its own family.

**Fronius**
- HA core `fronius` docs: Solar API (HTTP) for GEN24, IG Plus, Primo, Symo, Symo Hybrid, Tauro, Verto (Plus),
  plus a "Controlling the inverter over Modbus" section; platforms `number`, `switch` → "control".
  **Fixed:** connection now HTTP + Modbus TCP (was HTTP only).
- HACS *Fronius Modbus* README: GEN24 only, needs "Allow control" → **fixed:** was also attached to the
  string-inverter family; now GEN24 only, with the README caveat as a note.
- HACS *Fronius Wattpilot* README: Wattpilot, V2 and flex, "via local LAN or via Cloud" → connection fixed.
- evcc `fronius-gen24`: Modbus TCP, `battery-control` + `curtail` ✔. `fronius-wattpilot` is deprecated in evcc;
  the live route is `ocpp-goe` "Wattpilot (OCPP)", which needs sponsorship → the FAQ says so ✔.
- Register spot check: Symo GEN24 10.0 Plus — AT, CZ, NL, SE ✔.

## Corrections

Open an issue or a pull request. Most corrections are one line in `data/curated/*.yaml`; the dataset and the
change log are regenerated by the build. "My Deye does Modbus TCP from firmware X" is exactly what is needed.

## Publish (first time — done by hand)

1. Create the GitHub repo and push (from this directory):

   ```bash
   gh repo create madisorg/gridfit --public --source . --remote origin --push --description "Which solar inverters, batteries and wallboxes work locally with Home Assistant and evcc"
   ```

2. Cloudflare Pages → *Connect to Git* → this repo. The public site is the Astro build in `web/`
   (the Python site in `site/` stays as the reference renderer and is git-ignored). Build command
   `pip install -r requirements.txt && cd web && npm ci && npm run build`, output directory `web/dist`,
   environment variables `NODE_VERSION=22` (Astro 7 needs ≥ 22.22), `PYTHON_VERSION=3.12`,
   `GRIDFIT_BASE_URL=https://<domain>`, `GRIDFIT_ANALYTICS=cloudflare:<token>` (or `plausible:<domain>`).
   `python build.py` is **not** part of the Pages build: it would re-download the sources on every deploy,
   and the site reads the committed `data/` as it is (`npm run build` only runs `tools/site_data.py`,
   which reads the committed register snapshot, and `tools/specs/build.py`, which reads `data/specs/`). `404.html` and `og.png` are served from `web/public/`.
3. Point the domain at Pages; add it in Plausible (or use Cloudflare Web Analytics and `cloudflare:<token>`).
4. The refresh workflow (`.github/workflows/refresh.yml`) runs every Monday: sources (`--refresh`), and on the
   1st of each month the grid registers too (`--registers-refresh`, commits `data/registers/`). It
   rewrites `data/dataset/REFRESHED` and commits every run, so the public repository never goes 60 days
   without activity (GitHub would then disable the schedule). Add a repository secret `HEALTHCHECKS_URL`
   (a healthchecks.io check's ping URL, period 7 days, grace 2 days) and the run pings it at the end, `/fail`
   on failure; without the secret the step is skipped. `Actions → refresh → Run workflow` runs it by hand,
   with a checkbox for the registers. Each push rebuilds the site on Pages.

## Not affiliated

Home Assistant is a trademark of the Open Home Foundation. evcc, HACS and all product and company names are
trademarks of their owners and are used only to say what works with what. GridFit is not affiliated with any of them.
