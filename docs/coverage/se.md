# Coverage of the Swedish view, 2026-11-12

The method and the measure are `docs/coverage.md`; this file is Sweden's run of it. Base: `origin/main` at ca43083
(Estonia #9 merged; dataset of 2026-11-09; the committed register snapshot carries Rikta Rätt of 2026-10-23).

```bash
cd web && npm run build
node tools/coverage/country.mjs --cc se --json se.json --brands 30
```

## Before and after

| layer | before | after |
|---|---|---|
| models in the SE view | 13 048 | 13 048 |
| a · on Rikta Rätt | 3 427 | 3 427 |
| a · likely fit (maker's document) | 849 | 849 |
| a · possibly fit (other EU lists) | 8 112 | 8 112 |
| a · over the type-A limit (1.5 MW) | 167 | 167 |
| a · nothing known | 493 | 493 — every one legacy tier A (refused on the Austrian list or expired on the Belgian list only); the page says so |
| b · "not shown" rows without a reason | 154 446 | **0** |
| b · rows checked by Rikta Rätt (`R`) | — | 30 798 (3 422 models) |
| b · rows meeting by datasheet (`S`) | 5 977 | 6 096 |
| b · models with every row answered by a paper | 201 | 398 |
| c · kW and phases | 7 095 | 7 100 |
| c · kW and phases, models on the list | 3 406 / 3 427 | 3 406 / 3 427 (the 21 without: see below) |
| c · MPPT, PV models on the list | 853 / 2 937 | 885 / 2 937 |
| d · a datasheet or a maker's document, models on the list | 1 120 | 1 152 |
| e · legacy A / B / current | 535 / 190 / 12 323 | 535 / 190 / 12 323 |

**Status re-read**: of the 13 040 model keys in both runs, **0 changed status and 0 changed class**. What moved: 37 models
gained an MPPT count and 5 off-list models a datasheet as their strongest source (all Sunways, below). The profile adds
words to rows, never a state to the grid.

The parser fixes below change the grid only when the next `refresh` brings a new snapshot; their effect, measured on a
temporary snapshot of the same 2026-10-23 file read by the fixed reader, is in "After the next refresh".

## What changed, and why

- **Every row answers** (`data/profiles/se.yaml` `list_checks`, `on_application`). A model on Rikta Rätt gets "checked by
  Rikta Rätt" on the nine items the application form (version 2025 EN) has the applicant tick one by one and Energiföretagen
  checks against the RfG / EN 50549-1, EMC and LVD certificates: frequency range, the voltage window between the ALP trips,
  RoCoF, LFSM-O, under-frequency, reconnection, the ALP protection settings, island detection and the RfG 13.6 logic
  interface. The `what` sentence carries the page's own limits (papers only, no test report verified, nothing tested, not
  binding). Left out on purpose: the two EMC lines (they hang on the unit's rated current, which the list does not state,
  and about 100 list comments qualify the EMC papers: no third-party EMC, industrial-environment EMC only, harmonics shown only to
  the 40th order), storage (Rikta Rätt 1.0 "is not fully adapted" to it) and the power lines. Those rows,
  on a listed model without a sheet, say that the list states kW and phases but no current and no datasheet and that the
  local grid operator applies the line on the föranmälan. A model off the list says the operator checks it on the
  föranmälan: the protection-settings and power-quality tables of its type-A form, filled from the type-test protocol,
  with the RfG / EN 50549-1, EMC and LVD certificates (Ellevio's form, Vattenfall's conditions).
- **The profile is current** (re-read 2026-11-12). EIFS 2018:2 is still in force: Ei's 2026 regulations page lists amending
  regulations only, and the replacement drafted on 2026-02-19 (planned for 1 July 2026) is still not adopted. Rikta Rätt's
  page and list are of 2026-11-09; the 2.0 application and XML formats are still announced for "November 2026". The
  application form (Last-Modified 2025-02-25), Ellevio's type-A form (2025-09-15), Vattenfall's conditions (2026-09-02)
  and Nätkraft Borås's instructions (2026-02-05) are the same files the profile cites. The register's name and gate text
  (`gridfit/registers.py`) follow the page's new title and the 2.0 timetable.
- **The list changed code page** (`tools/registers/parse.py` `read_se`, test `tools/registers/test_read_se.py`). The CSV of
  2026-10-23 was cp1252, the one of 2026-11-09 is cp850. Read as cp1252 the next refresh would have written "f†r enbart"
  into 397 comments and changed 11 model codes. The reader now takes the code page whose header spells "Löp-nummer" and
  "Energikälla" (UTF-8 too).
- **Three-phase-only units are "listed with restrictions"** (same commit). 119 rows say "får enbart / endast anslutas /
  monteras i trefaskoppling": single-phase units listed only as a three-phase set. They were plain "listed"; now
  `restricted` with the list's own words, which the grid shows as "with a condition".
- **A lost dash** (same file). 40 Pylontech FH3X rows (3313–3362) read `FH3X?8K?HY?3P?10D`: a dash the export could not
  encode, as the family's other rows (`FH3X-8K-HY-3P-10`) show. With the `?` they got no model page.
- **Smaller reader fixes**: four Growatt review dates in dd/mm/yyyy become ISO (they were dropped); row 3377 (Solplanet
  ASW150K-LT, the maker's company name in the energy-source cell) is read as PV and reported instead of falling into
  class `other`.
- **Datasheets**: Sunways (new, `data/specs/sunways.yaml`, five sheets, 40 rows, 37 of 77 register models; Rikta Rätt lists
  56 Sunways models). The sheets' own suffixes are kept: STH-…-HSS is not the list's STH-…-HS. Rikta Rätt states 45 kW for
  STT-40KTL, the sheet 40 kW rated / 44 kVA max; the sheet is the maker's figure.

## After the next refresh (preview)

Measured on two temporary snapshots (never committed): the committed 2026-11-01 snapshot with its Rikta Rätt rows
(file of 2026-10-23) re-read by main's reader, and by the fixed one. Same file, same date, so the difference is the reader:

| | main's reader | fixed reader |
|---|---|---|
| a · on Rikta Rätt (`Y`) | 3 427 | 3 314 |
| a · with a condition (`C`) | 0 | 114 |
| a · possibly fit (`K`) | 8 112 | 8 096 |
| models in the SE view | 13 048 | 13 033 |

Every change, model by model:

- **98 `Y` → `C`**: the three-phase-only rows (Afore 21, Hoymiles 14, SolaX 8, Victron 7, Sunways 7, ZCS 6, Enphase 5,
  GoodWe, AEG, Sineng, WHES 4 each, others 1–3).
- **16 `K` → `C`**: Pylontech FH3X single-phase units. With the lost dash restored, the list's row joins the model the
  other EU lists already carry (`FH3X-5K-HY-1P-10`), and the row says three-phase only.
- **24 renamed, same status `Y`**: the Pylontech FH3X three-phase rows (`FH3X?8K?HY?3P?10D` → `FH3X-8K-HY-3P-10D`), now
  with a model page of their own; 21 of them carry no kW on the list itself.
- **1 new `Y`**: Solplanet ASW150K-LT, class `other` (hidden) before, now an inverter.
- No class change otherwise, no other status change. "Not shown" without a reason stays 0.

The refresh run will also bring the 2026-11-09 list (+25 / −15 rows) on top of this.

## What is left in Sweden, and why

- **kW and phases on 21 listed models**: Pylontech FH3X three-phase rows whose kW cell is empty on Rikta Rätt itself (and
  three more where the list's kW is the battery's kWh: 10 / 15 / 20 for an 8 kW unit). Pylontech publishes no FH3X sheet
  GridFit has read.
- **MPPT on 2 052 listed PV models.** The largest gaps: SAJ, Fox ESS, Growatt, SolaX, GoodWe, Hoymiles — brands with spec
  files whose older generations are not in the download centres, and Sigenergy, Huawei, Sineng, Solinteg, SolarEdge,
  Megarevo, EcoFlow, Enphase, KACO with no sheet read. Solinteg's download centre renders by script only (its sheets are
  on distributors' sites, which the spec rule does not take); Huawei's terms forbid automated access; Sigenergy's centre
  refuses scripts.
- **"Possibly fit" (8 112)**: accepted on other EU lists, nothing read in Sweden. A level, with its reason on the page.
  Sweden takes a generic EN 50549-1 certificate (`data/evidence/rules/accepts.yaml`), so every such certificate any
  country session adds also lifts Sweden.
- **"Nothing known" (493)**: legacy tier A, hidden by default, the reason on the page.
- **The list update** of 2026-11-09 (+25 / −15 rows against 2026-10-23, `docs/watch-report.md`) waits for the one
  `refresh` run after all countries; the new reader is what that run should use.

## Documents only a browser gets (owner's list)

| document | why a script cannot | what it would add |
|---|---|---|
| [SolarEdge — single-phase inverter with HD-Wave, EN 50549-1 certificate (Sweden)](https://knowledge-center.solaredge.com/sites/kc/files/se-single-phase-inverter-with-hd-wave-en50549-1-certificate-swe.pdf) | 403 (Cloudflare) | a Swedish document for SolarEdge's single-phase range (36 listed, 85 off the list, none documented) |
| [SolarEdge — Home Hub three-phase, grid certificate (Sweden)](https://knowledge-center.solaredge.com/sites/kc/files/se-solaredge-home-hub-inverter-three-phase-grid-certificate-swe.pdf) | 403 (Cloudflare) | the same for the Home Hub three-phase range |
| Kostal Swedish EN 50549-1 declarations (`1821_Z-EN50549-1_PIKO-10-20_sv.pdf`, `1799_Z-EN50549-1_PLENTICORE-BI-XX-26_sv.pdf`, kostal-solar-electric.com download centre) | 404 at the old address; the download centre has to be searched by hand | Kostal is already covered by its released-countries table; these would add the Swedish settings |
| Solinteg datasheets (MHT, M2HT, OGT) from solinteg.com's download centre | the centre renders by script | kW / MPPT for 50 listed Solinteg models |
| Sigenergy datasheets and Intertek EN 50549-1 certificates | 403 to scripts | 64 listed, 262 off the list |

## Engine wishes (for the engine session; not changed here)

- **Use the list's kW and phases for the power lines on a listed model without a sheet** (`tools/check/run.py`,
  `web/src/lib/checks.ts`). Rikta Rätt states kW and phases on 3 406 of 3 427 rows; today a listed model without a sheet
  shows the RfG-type, micro-producer, single-phase and EMC rows as "not shown" with the `not_carried` reason, although the
  list's figure would place it. As a distinct state ("by the list's figure", below "by datasheet"), never as `S`; the list's
  phases column is not the maker's phase count (Victron 230 V units listed with 3), so for `phases` only where the comment
  does not say three-phase set. Affects ≈ 3 400 SE models (and AT, BE where terms allow). Test: a listed Sunways
  STT-40KTL (list 45 kW, sheet 40 kW) must keep the sheet.
- **Wire `tools/registers/test_read_se.py` into `npm test`** (`web/package.json`). Today no register reader has a test.
- **A per-row restriction text** on the model page for `restricted` SE rows (the comment, e.g. "only in a three-phase
  connection") if the page does not already print the `word` for a restricted cell — check after the refresh.
