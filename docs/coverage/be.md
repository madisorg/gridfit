# Coverage of the Belgian view

Written 2026-11-12, on the method of `docs/coverage.md` (Estonia first). Belgium's view is `/grid/be/` and every model's
BE row; its list is Synergrid's C10/26, which GridFit shows only as "listed / expired" with a link, because Synergrid's
terms allow personal use only (`docs/register-check.md`, Belgium). Completeness here comes from the profile, the makers'
datasheets and the parser — not from more of the list's columns.

## The measurement

```bash
cd web && npm run build
node tools/coverage/country.mjs --cc be --json be.json --brands 30
```

Base: `origin/main` at ca43083 (Estonia, PR #9, merged). Three runs:

- **before** — ca43083 as it is;
- **after** — this branch as committed (profile + datasheets; the register snapshot is the shared 2026-11-01 one);
- **after the refresh** — the same, with the BE rows of that snapshot re-parsed from the same 2026-10-30 file by this
  branch's parser, swapped into a local copy that was never committed. The parser fix reaches the site only with the
  shared `refresh` run. Its effect is measured against the same swap made with `origin/main`'s parser, so drift between
  the snapshot and today's parser (see "Found on the way") is not counted as this work.

## Before and after

| layer | before | after | after the refresh |
|---|---|---|---|
| models in the BE view | 13 048 | 13 048 | 13 008 (58 bare-number devices dissolve into existing models and 18 new named ones) |
| a · on Synergrid's list | 6 674 | 6 674 | **6 719** (+45 net: 84 existing models newly joined, 18 new named ones, 57 bare-number devices gone) |
| a · likely fit (maker's document) | 267 | 267 | 243 (23 Kostal models now on the list instead) |
| a · possibly fit (other EU lists) | 5 595 | 5 595 | 5 534 |
| a · nothing known | 454 | 454 | 454 — every one legacy tier A: 446 expired or refused on every list that carries them, 8 with a datasheet but no positive list; the page says so |
| a · refused / not allowed | 53 | 53 | 53 — expired homologations on Synergrid's own expired sheet ("expired" on the page) |
| a · over the type-A limit | 5 | 5 | 5 (four NR Electric PCS-9567TU and a Vacon NXI, all ≥ 1 MW) |
| b · "not shown" rows without a reason | 143 799 | **0** | 0 |
| b · models with a reasonless "not shown" row | 12 384 | **0** | 0 |
| b · rows checked by Synergrid's list (`R`) | — | 53 413 | 53 732 |
| b · rows met by datasheet (`S`) | 4 806 | 5 171 | 5 171 |
| c · kW and phases, all models | 7 095 | 7 166 | 7 166 |
| c · kW and phases, listed models | 3 115 / 6 674 | 3 186 / 6 674 | 3 255 / 6 719 |
| c · MPPT, listed PV models | 1 216 / 5 517 | 1 282 / 5 517 | 1 294 / 5 609 |
| d · a datasheet or a maker's document, listed models | 1 631 | 1 720 | 1 766 |
| e · legacy A / B / current | 535 / 190 / 12 323 | the same | the same |

Every listed model already has a rated power (the list's own figure, which the grid has used since the start); what the
listed models lack is **phases** — 3 488 of them, because Synergrid's phase column is not reproduced.

## Status re-read, model by model

- **before → after**: of 13 040 models in both runs (keyed brand + model), **0 changed status and 0 changed class**. 88
  models gained phases or MPPT (HYXi 52, TSUN 36), nothing else moved. No row became "outside by datasheet"; 11 more rows
  are "over a line" (HYXi string and hybrid units above the 5 kVA single-phase / 10 kVA small-installation lines).
- **the parser fix alone** (main's parser vs this branch's, same file, same snapshot): **84 status changes, each with the
  same reason** — the model is on Synergrid's list under a bare number in the model cell, which until now formed a device
  of its own ("KOSTAL 10") and joined nothing: Fronius 40 (Primo, Primo/Symo GEN24, Verto, Argeno), Ampere Energy 14,
  Kostal 6 and Solis 1 ("Solis 30K") go from "possibly fit" to "on the list"; Kostal PIKO, PIKO IQ, PIKO CI, PLENTICORE
  plus / plus G2 / BI 23 go from "likely fit (maker's document)" to "on the list". 20 class changes, same cause: the 14 Ampere systems become hybrids (the Belgian
  rows tick solar and storage), and six Fronius Symo GEN24 without "Plus" become inverters (the Belgian rows tick solar
  only; Austria's "hybrid" is now one vote of four). 18 new named models (Kostal G3 range, Ampere Tower M PRO 6.3) are new
  on the grid, all "on the list".

## What changed, and why

- **Every row answers** (`data/profiles/be.yaml` `list_checks`, `on_application`). A listed model gets "checked by
  Synergrid's list" on the ten Annex D items Synergrid reads against accredited test reports before listing: frequency and
  voltage ranges, power at under-frequency, RoCoF, LFSM-O, LFSM-U on storage, reconnection, reactive power, the logic
  interface and, on storage, the homologated power control system. In the 2026-10-30 file every storage-only row ticks
  LFSM-U (1 249 / 1 249) and names its control system (1 248 / 1 249). **Left out on purpose**: separation settings and loss
  of mains — 29 of the 5 519 listed PV / storage units up to 30 kVA use an external relay instead of a built-in separation
  system, and GridFit does not carry that column. The size lines (type A, 5 kVA single-phase, 10 kVA small installation,
  30 kVA integrated separation) read Smax, which GridFit does not carry either; on a listed model they say so ("its Smax,
  phases and whether the separation system is built in are on Synergrid's list"). Off the list: "there is no application
  to check it on — only the maker or importer can file the homologation".
- **Editions re-read 2026-11-12**: C10/11 ed. 2.4 (Last-Modified 2025-10-14, the file the profile cites), C10/26 template
  ed. 2.4.1 (2026-04-09), FAQ (2025-10-14), plug&play extract (2026-10-10), list file (2026-10-30, 1 555 983 bytes — the
  same as the 2026-11-01 snapshot, so no new snapshot). The "Grid Update" amendment is still in consultation until
  2026-12-01. Nothing to change in `tools/reports/country_values.yaml`.
- **Bare-number models** (`tools/registers/parse.py` `be_model`, test `tools/registers/test_be.py`). Synergrid writes 152
  rows with the name in the series column and only a number in the model cell; they now read as the other lists write
  them ("PLENTICORE plus 10 G2", "Primo 3.0-1", "SYMO GEN24 10.0 Plus SC"). Five-digit article numbers (Perceval, as the
  Dutch list has them too) stay. Takes effect with the next `refresh`.
- **Gensets** were already fixed by the Estonian pass (`data/registers/classes.yaml`); re-checked against the
  2026-10-30 file: of the 2 002 rows flagged CHP / wind / backup only or "Generator (…)", two still sat in a PV class —
  Viessmann Vitobloc 300 NG-15 / NG-20, through the Dutch generation list — and the Dutch pass fixes those (riik-nl).
- **Datasheets**: TSUN (new, 19 rows, 37 register models: Gen3 microinverters, MSU2000, MAU5000) and HYXi POWER (new, 33
  rows, 52 of its 71 models: micro, string, hybrid, MS3000 balcony storage), both BE-heavy brands with 0 % / 31 % phases.

## What is left, and why

- **Phases on 3 488 listed models.** The figure is on Synergrid's list; GridFit may not reproduce it until Synergrid
  answers the permission letter (drafted, not sent — homelab `kataloogid/reference/gridreg-avaldamine.md` § 4). 1 123 of
  them are brands the model-code level of PR madisorg/gridfit#11 reads (Afore 121, Autarco 95, SolaX 95, Fox ESS 93,
  Sigenergy 85, Sungrow 59, GoodWe 55 …). The rest, by size: WSTECH 96 and Vacon 63 / Danfoss 57 (industrial storage PCS
  and regenerative drives — no consumer datasheets), SAJ 94 and Solis 76 (older generations and "-BE" variants the current
  sheets do not print), Fronius 85 (bare numbers — fixed by the refresh, which joins them to the Austrian rows), Hypontech
  82 (site unreachable, below), INVT 58.
- **"Possibly fit" (5 534 after the refresh)**: accepted on other EU lists, not on Synergrid's. In Belgium that means "not
  connectable until homologated", which the page's `not_listed` text says. A level with its reason.
- **"Nothing known" (454)** and **"refused" (53)**: legacy tier A and expired homologations, with the reason on the page.

## Mootori soovid (for one engine session; not done here)

1. **Run `tools/registers/test_be.py` in `npm test`** (`web/package.json` `test`: add `python ../tools/registers/test_be.py`).
   11 cases, under a second; proves the bare-number names and the genset class. Touches nothing else.
2. **The `refresh` run** brings the parser fix to the site: +84 models "on the list", 20 class corrections, 58 bare-number
   devices gone (numbers above). Test: `node tools/coverage/country.mjs --cc be` after the refresh should show 6 719 on the
   list on the same file.
3. **Snapshot drift** (found on the way): re-parsing the 2026-10-30 file with `origin/main`'s own parser changes the 2026-11-01
   snapshot's BE view in 119 classes (84 battery → hybrid, 35 hybrid → battery, e.g. CONOW — the Estonian `cls_of` fix of
   "Backup power system") and 39 spellings ("AF4K-SL" / "AF4k-SL", "H2.5_210" / "H2.5 210", RCT Power, Socomec …), with 0
   status changes. None of it is this branch's; the refresh brings it too, so its re-read should expect it.
4. **Model-code rules for BE-only brands** once #11 is merged (`data/specs/naming/codes.yaml`): Hypontech HBS / HHS, Q
   CELLS "… 3P", Sunsynk "-SG01HP3", SolarEast "…KL1 / KH3", Megarevo "…L1", Rahvolt "…-S2". They need three agreeing
   figures from AT / SE or a datasheet each; Synergrid's phase column must not be used for it until the permission.

## Documents for Madis to fetch by hand

- **Hypontech** datasheets (HBS / HHS / HMS series; 82 listed models without phases): hypontech.com answers with a TLS
  certificate for another host (`docs/evidence-sources.md`), not bypassed — https://www.hypontech.com/
- **HYXi "-HS" hybrids** (HYX-H3K…H8K-HS, 7 listed): the site serves only the "-HS1" revision —
  https://www.hyxipower.com/en/ProductsDetail/hybrid-inverter-3-6k ; ask HYXi or its Belgian importer for the HS sheet.
- **TSUN** ACU / HSU 3–6 kW, MAU1000 / MAU2000, MSU1000, MP2250 / MP3000, MS3000, MX800Lite, ESK kits (52 listed models without phases): no sheet on
  https://www.tsun-ess.com/downloads.html on 2026-11-12; ask TSUN.
- **Synergrid's permission** for the phase and Smax columns (the drafted letter) — the single document that closes most
  of what is left.
