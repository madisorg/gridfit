# Coverage of a country's view

Written 2026-11-12, Estonia first. Before the launch, Madis asked that every country view (`/grid/{cc}/` and every model's
row for that country) have **every layer of information at some level, with its source and its reason**. This file is the
method and the measure. The next country runs the same command with another code.

## The command

```bash
cd web && npm run build                      # dist/grid/index.json, .data/registers.json, .data/checks.json
node tools/coverage/country.mjs --cc ee      # markdown tables to stdout
node tools/coverage/country.mjs --cc ee --json out.json --brands 30
```

`tools/coverage/country.mjs` reads only build outputs and changes nothing. It walks the grid index's rows in the order the
page writes them, joins each row back to its register device (and stops if the two disagree), and gives every model one
value per layer:

| layer | what is measured | "at some level" means |
|---|---|---|
| a · status | the grid cell, from `web/src/lib/grid-filter.js` `cellCode` (exactly what the page shows): on the list / with a condition / likely fit (maker's document) / possibly fit (other EU lists) / over the type-A limit / nothing known | not "nothing known", or a named reason for it |
| b · `must_meet` rows | the profile's rows for that model, rebuilt as `web/src/lib/checks.ts` does: by datasheet, by the maker's document, checked by the operator's list, not shown, no check | no "not shown" row without a reason |
| c · specs | rated kW (or kVA), phases, and the MPPT count on a model that takes PV — what the grid row carries (the list's figure where a list states it, else the maker's datasheet) | kW and phases |
| d · source | the strongest document behind the model: its own list row, a maker's document, a datasheet, another country's list | every model comes from at least one list row with its link, so this is always met; the column says how strong |
| e · legacy | tier A / B / C (`web/src/lib/legacy.ts`) or current | always computed; "current" is the default without a dated entry |

The tables come by class, by brand, and (in a list country) by brand among the models on the list, with the share of each
layer met. The status re-read (step 4 of the method) is the `--json` output of two runs compared model by model.

## The method, per country

1. **Measure before**, on the merged tree, and keep the JSON.
2. **Make every row answer**: a profile with a list gets `list_checks` (which items the operator reads before listing) and
   every profile gets `on_application` (who decides a row nothing shows, and on what papers) — `docs/checks.md`.
3. **Close gaps by impact**: the largest brands on the country's own list first, then the brands sold there. Datasheets
   through `tools/specs/` (hand tables in `draft.py`), makers' country documents through `tools/evidence/`. A document
   that needs a browser goes on the owner's list, never through a scraper.
4. **Re-read the operator's own documents**: is the profile's edition still the one served? (Estonia: three of them had
   been re-issued since the profile was written.)
5. **Measure after** with the same command, and **compare the statuses model by model**: a model that changes status
   without a reason is a silent bug (Italy found two this way).
6. **UI**: a new state or a new kind of row is measured by DESIGN.md §10.

## Estonia, 2026-11-12

Base: `origin/riigid` (PR #8) merged with `origin/main` (dataset 2026-11-09). The Elektrilevi list was downloaded again
on 2026-11-12: 2 239 rows, identical to the 2026-11-01 snapshot, so no new snapshot.

| layer | before | after |
|---|---|---|
| models in the EE view | 14 460 | 13 048 (1 417 CHP / generator / wind units left for their own class, 5 split apart) |
| a · on Elektrilevi's list | 2 214 | 2 216 |
| a · likely fit (maker's document) | 932 | 933 |
| a · possibly fit (other EU lists) | 9 569 | 9 134 |
| a · over the type-A limit | 1 252 | 272 |
| a · nothing known | 493 | 493 — every one legacy tier A: 453 refused on the Austrian list only, 40 expired on the Belgian list only; the page says so |
| b · "not shown" rows without a reason | 152 300 | **0** |
| b · rows checked by Elektrilevi's list | — | 21 060 (2 216 models) |
| b · models with every row answered by a paper | 182 | 598 |
| c · kW and phases | 6 915 | 7 095 |
| c · kW and phases, models on the list | 1 292 / 2 214 | 1 370 / 2 216 |
| c · MPPT, PV models on the list | 365 / 2 081 | 467 / 2 083 |
| d · a datasheet or a maker's document, models on the list | 507 | 602 |
| e · legacy A / B / current | 535 / 190 / 13 735 | 535 / 190 / 12 323 |

Status re-read: of the 13 043 models in both runs, **0 changed status and 0 changed class**. The 1 417 that left were all
"over the type-A limit" (980) or "possibly fit" (437) — none was on Elektrilevi's list.

What changed, and why:

- **Every row answers** (`data/profiles/ee.yaml` `list_checks`, `on_application`; `tools/check/run.py`). A model on the list
  gets "checked by Elektrilevi's list" on the ten items the listing guide names; a rated-power line on a listed model
  without a sheet says the list names the model only; a model off the list says Elektrilevi checks it on the application
  against an EN 50549-1 / EN 50438 certificate and a type-test protocol.
- **Gensets are not batteries** (`data/registers/classes.yaml`, `gridfit/registers.py`, `tools/registers/parse.py`). The
  Belgian "Backup power system" flag was read as storage, and the Dutch generation file has no type column: CAT, MWM,
  MTU, Caterpillar, EVW, INNIO Jenbacher, 2G and 50 other makers' engines sat in the battery and inverter classes and made
  up four in five of Estonia's "over the type-A limit". They are class `other` now, which the site does not show.
- **3.3 kW is not 33 kW** (`gridfit/registers.py` `_decimals`). The register's model key drops the decimal point, so nine
  devices had merged two units (Sofar 3,3KTLX-G3 / 33KTLX-G3, Sineng SN3.0PT / SN30PT, Deye SUN-3.6K-G04 / SUN-36K-G04,
  ZCS 3PH 3.3KTL-V3 / 33KTL-V3, Pixii). The device key now carries where the digits' decimal point sits; nothing else
  splits (16 188 → 16 197 devices).
- **The profile is the 2026 one**: listing guide re-issued (served 2026-09-14, same items, any generating unit), connection
  conditions valid from 29.09.2026 (micro-producer 2.32.1; the €38 000/MW security is no longer in them; the 2023 file the
  profile cited is no longer served), producer application form 2026-01, and a new item: the **nano-producer line**
  (under 0.8 kW per connection point, Elektrilevi self-service) for plug-in units.
- **Datasheets**: Sofar (new, 103 rows from 20 sheets — 43 of its 93 listed models), Sungrow (new, 15 rows — 10 of 78),
  Growatt (+109 rows from 20 sheets — 43 more of 165), all read from the sheets already in `cache/specs/`.

## What is left in Estonia, and why

- **kW and phases on 846 listed models** (and ~5 900 off the list). The largest gaps on the list: Sigenergy 70 (the
  download centre refuses scripts), Deye 61 (the list writes the codes without the hardware suffix the sheets carry —
  `SUN-10K-SG01HP3-EU` vs `…-EU-AM2` — and the rule says a suffix is another model), Autarco 47 and Livoltek 34 (no sheets
  cached), Sofar 50 and Growatt 67 (older generations whose sheets are not in the download centres, `-A` variants no sheet
  prints), Sungrow 68 (the RT / RT-P2 / RS / SH-RT / CX sheets were not harvested — a harvest recipe gap, not a block),
  Huawei 22 (terms forbid automated access). The kW a list states (BE, AT, SE) is used; Belgium's phase column is not,
  because its terms allow personal use only.
- **"Possibly fit" (9 134)**: accepted on other EU lists, nothing read in Estonia. It is a level, with its reason on the page.
- **"Nothing known" (493)**: legacy tier A, hidden by default, the reason on the page (refused or expired elsewhere).
- **Documents only a browser gets** (owner's list): Fronius "Conformity with requirements from Estonia" (downloads.fronius.com,
  WAF), SolarEdge "Countries supported by SolarEdge inverters" v1.1 (Cloudflare), Sigenergy's Intertek EN 50549-1
  certificates and datasheets (403 to scripts), Huawei SUN2000 datasheets (by hand only, its terms).

## Estonia, the model-code level (2026-11-12, second pass)

The 846 listed models without kW and phases, after the makers' download centres refused scripts and the owner could not open
the PDFs either: `data/specs/naming/codes.yaml` reads the maker's naming, and `tools/specs/codes.py` keeps a rule only where it
agrees with stated figures (68 rules over 28 brands, 56 kept in some part; every kept part agrees on at least 3 and at least 90 % of the models a list or
sheet states, most on all of them — SolaX 163/163 and 175/175, GoodWe 104/104, Sofar 100/100, Sigenergy 62/62).
Listed models with kW and phases at some level: **1 370 → 1 746 of 2 214**; all models: 7 095 + 757 with some part from the
code. Status re-read: 0 changed (display only). Left: 470 listed models — 294 with neither figure, 176 with kW but no phases.
They are brands whose naming no stated figure can check (ABB / FIMER's Estonian spellings, Kehua SPI, Elecod, Kstar KSG, INVT
BD, Fox ESS AC, Renac KR3, Huawei SUN2000L) and the industrial converters (Tecloman, Elecod, Kehua BCS, Weiheng). For those the
route is ZEREZ, the German unit register (`docs/zerez.md`): a registered account and FGW's permission, which the owner has a
draft letter for.

The check paid for itself once: Deye's `…-SM2` / `…-BM2` three-phase hybrids had been written into `data/specs/deye.yaml` as
single-phase (the drafter's microinverter test `M\d` matched the hardware suffix). Eleven rows were corrected, and four
Italian "outside by datasheet" verdicts went with them (27 → 23).

