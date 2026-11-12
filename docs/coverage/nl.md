# Netherlands — coverage of the country view

Written 2026-11-12 by the method in `docs/coverage.md` (Estonia first). Base: `origin/main` at ca43083 (PR #9 merged;
dataset of the 2026-11-01 snapshot). Measured with:

```bash
cd web && npm run build
node tools/coverage/country.mjs --cc nl --json nl.json --brands 40
```

## Before and after

| layer | before | after |
|---|---|---|
| models in the NL view | 13 048 | 13 043 (5 CHP / wind units left for class `other`) |
| a · on Netbeheer Nederland's list | 4 409 | 4 404 |
| a · likely fit (maker's document) | 567 | 567 |
| a · possibly fit (other EU lists) | 7 387 | 7 387 |
| a · over the type-A limit (1 MW or more) | 192 | 192 |
| a · nothing known | 493 | 493 — every one legacy tier A: 453 refused on the Austrian list only, 40 expired on the Belgian list only; the page says so |
| b · "not shown" rows without a reason | 145 468 | **0** |
| b · "not shown" rows with a reason | 0 | 106 115 |
| b · rows checked by Netbeheer Nederland's list | — | 41 824 (4 404 models) |
| b · models with every row answered by a paper | 527 | 1 071 |
| b · rows by maker's document / older edition | 6 108 / 46 | 3 622 / 1 (on listed models the list now answers first; nothing was lost) |
| c · kW and phases | 7 095 | 7 095 |
| c · kW and phases, models on the list | 1 962 / 4 409 | 1 962 / 4 404 |
| c · MPPT, PV models on the list | 585 / 3 683 | 585 / 3 678 |
| d · a datasheet or a maker's document, models on the list | 1 030 | 1 030 |
| e · legacy A / B / current | 535 / 190 / 12 323 | 535 / 190 / 12 318 |

**Status re-read.** Of the 13 035 brand + model keys in both runs, **0 changed status, class, legacy tier, strongest
source or spec level**. The five that left were all "on the list" in the inverter class and are not inverters (below).

## What changed, and why

- **Every row answers** (`data/profiles/nl.yaml` `list_checks`, `on_application`). A model on either Netbeheer Nederland
  file gets "checked by Netbeheer Nederland's list" on the ten items an EN 50549-1 type certificate covers — frequency
  range, RoCoF, LFSM-O, power below 49.5 Hz, protection settings, reconnection, the logic interface to stop, power factor,
  loss of mains, storage LFSM-U. Why those: the list's own heading ("shown for the Netherlands that the RfG requirements
  are met"), Netbeheer Nederland's certification note of 2020-10-21 (an EN 50549-1 / NEN-EN 50549-1 certificate from an
  accredited body is "in any case enough") and energieleveren.nl's form for a new inverter (brand, type, firmware, rated
  active power, maximum apparent power, certificate). The three kW lines (1 MW type B, 11 kW protection, 5 kW three-phase)
  are not in the list: it names brand and type only, and the grid operator applies them to the installation from the
  maximum capacity on the installation document — that is the `not_carried` sentence. Off the list, the grid operator
  decides at registration, and the certificate is enough (`on_application`).
- **Five non-inverters out of the inverter class** (`data/registers/classes.yaml`, appended). The Dutch generation file
  has no type column. Viessmann NG-15 / NG-20 are the Vitobloc 300 NG 15 / NG 20 gas CHP units, Viessmann Vitovalor
  PA2 / PT2 are fuel-cell micro-CHP units, TWE WindStream5 is a 5 kW wind turbine with an induction generator. The EE
  session's maker list had caught the other CHP makers (2G, MTU, INNIO Jenbacher, KW Energietechnik, Remeha, …).
- **The profile's documents are the served editions** (checked 2026-11-12): the Systeemcode elektriciteit 2026
  consolidation of 2026-10-01 is still the one in force (next version 2027-01-01); Netbeheer Nederland's country settings
  are still the 2026-09 file; the requirements-generators page links the same documents. The 2027-01-01 amendment
  (ACM/UIT/668130, Stcrt. 2026, 4110), which the profile had not read, sets the group transport agreement in chapter 7
  and does not touch the type-A rules of chapter 3.
- **The list was re-issued on 11 November 2026** (`last-modified` endpoint and the sheet's A3 "Versie 11 november 2026"):
  7 031 rows against the snapshot's 7 021 — five new GONEO models (EUE2-PB30, -PB36, -PB46, -PB50, -PB60, on both files)
  and the brand cell now spelled "GONEO". `read_nl()` reads the new files unchanged (7 031 rows, source date 2026-11-11,
  maker normalised to Goneo, no error line). No snapshot is committed here; the shared refresh run brings it in.

## What is left in the Netherlands, and why

- **kW and phases on 2 442 listed models** (and ~3 500 off the list). The largest gaps on the list, with the reason:

  | brand | listed, no kW + phases | why |
  |---|---|---|
  | SolaX | 106 | older X1-Fit / X1-3K-S / AELIO units; PR #11's model-code layer reads SolaX codes |
  | Autarco | 75 | autarco.com now redirects to invrida.com (installer software) — no datasheets served; PR #11 reads Autarco codes |
  | Anker SOLIX | 71 | codes (A17C1, A17E23Z1-35, AE1113Z1-8 …) carry no rating; ankersolix.com disallows `/downloads` in robots.txt — owner's list |
  | SAJ | 70 | AS1 / AS2 all-in-one units not in the cached sheets; SAJ's hand table lives in `tools/specs/draft.py`, which PR #11 also edits — for one brand pass after the country PRs |
  | Afore | 61 | PR #11 reads Afore codes |
  | Solis | 53 | RHI-…-48ES and `-BE` variants of older sheets; hand table in `draft.py` (brand pass) |
  | Sungrow | 52 | RT / RS / CX sheets not harvested (Estonia found the same); PR #11 reads Sungrow codes |
  | INVT, SMA, Kstar, SolarEdge, GoodWe, Fox ESS, Growatt | 47, 46, 38, 35, 29, 32, 28 | PR #11's code layer reads these brands |
  | Danfoss + Vacon | 64 | VACON NX active front ends rated by current, not by kW; no sheet |
  | Sinexcel, KACO, Felicity Solar, AMPERE ENERGY, HYXi, CONOW | 43, 39, 33, 33, 29, 28 | no sheets cached; not in the code layer |
  | EcoFlow | 34 | the PowerOcean sheets found are reseller copies, not EcoFlow's own — owner's list |
  | Pylontech | 30 | the download centre renders from a script API, no PDF link in the page — owner's list |
  | joined brand cells | 98 | "Solarwatt / Fronius" 30, "ILumen / SMA" 28, "Solarwatt / Kostal" 21, "Solarwatt / SMA" 14, "Solarwatt / Steka" 5: mostly the second brand's hardware, whose sheet rows exist — engine wish 2 |

- **"Possibly fit" (7 387)**: accepted on other EU lists, nothing read in the Netherlands. It is a level, with its reason.
- **"Nothing known" (493)**: legacy tier A, hidden by default, the reason on the page (refused or expired elsewhere).
- **106 115 "not shown" rows with a reason**: on a listed model the three kW lines without a sheet (`not_carried`); off the
  list every document item without a document (`on_application`).

## Mootori soovid (for the engine session)

1. **The storage item from the storage file only.** `list_checks` treats both Dutch files alike, so the `storage` row
   (LFSM-U) reads "checked by the list" on 33 hybrids that are on the generation file only (Anker X1-H5K-T … X1-H12K-T and
   others). Wanted: `list_checks.items_by_file` (or a `storage_file_only` flag) reading the entry's `extra.list`
   (`generation` / `storage`) that `read_nl()` already stores; touches `tools/check/run.py` (`listed`) and the profile
   schema. Test: Anker X1-H5K-T × NL `storage` → "not shown" with the `not_carried` reason; Afore AF3K-TH (both files) → R.
2. **Rebrand join for the spec layer.** 98 listed NL models sit under a joined brand cell whose type names the second
   brand's hardware: "ILumen / SMA" "2.5 / SB3.0-1AV-41" (battery size first), "Solarwatt / SMA" "Command 25 /
   SB3.0-1VL-41 (GLV006-01-0004)", "Solarwatt / Fronius" "Command 25 / Primo 3.0-1 (…)" (later rows drop "Primo"),
   "Solarwatt / Steka" "Command 25 / StecaGrid 1511 (…)"; "Solarwatt / Kostal" writes "Command 25 / 3.0 (GLV016-01-0012)"
   and needs Solarwatt's own table. Matching the code between "/" and "(" against the second brand's
   `data/specs/<brand>.yaml` would give most of them kW, phases and MPPT. Touches `tools/specs/build.py` or the alias
   layer. Test: "ILumen / SMA" "2.5 / SB3.0-1AV-41" gets SMA SB3.0-1AV-41's row.
3. **V2G units have no class of their own.** Kia EV9 / Hyundai IONIQ9 with the IoTecha EVEE V2X charger (3, inverter) and
   Venema E-Mobility V2G chargers (5, inverter / battery) are on the Dutch list as generating / storage units. They show
   as inverters or batteries; a `v2g` class (or wallbox with a bidirectional flag) is a decision for the class model.
4. **Freshness from the endpoint.** `GET https://api.energieleveren.nl/api/v2/files/homologation-file/last-modified`
   returns the list date as JSON (`2026-11-11T00:00:00Z` today); the refresh job could compare it with the snapshot's
   `source_date` instead of downloading both files every run.

## Documents for Madis (a browser, not a script)

- **Anker SOLIX** — datasheets for A17C1 / A17C2 / A17C3 / A17C53Z1 / A17C6, A17E23Z1 / A17E2GZ1, AE1033Z1, AE1113Z1 / AE111GZ1
  and the X1-H / X1-P6K hybrids: <https://www.ankersolix.com/nl> (the `/downloads` path is disallowed to robots).
- **EcoFlow** — the maker's own PowerOcean single-phase (EF HD-P1-…-S1 / -S2), three-phase (EF HD-P3-…) and STREAM
  (EF-ST5K-…) datasheets: <https://www.ecoflow.com/eu/> (installer downloads). Reseller copy seen, not used:
  <https://midsummer.ie/pdfs/ecoflow-powerocean--single-phase--datasheet-en-20241022.pdf>.
- **Pylontech** — Force H3X (FH3X-…-HY-1P / -3P), Force H3 (FHM-…-HY-3P) and NECS datasheets:
  <https://en.pylontech.com.cn/service/downloads>.
- **Autarco** — the S2 / S3 datasheets: the maker's site no longer serves them (autarco.com → invrida.com); a Dutch
  wholesaler or Autarco's installer portal is the only source left.
- Shared with Estonia: Fronius, SolarEdge, Sigenergy, Huawei (see `docs/coverage.md`).
