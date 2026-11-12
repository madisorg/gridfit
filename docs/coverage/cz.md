# Czechia — coverage of the country view

Written 2026-11-12, by the method in `docs/coverage.md` (Estonia first). Command:

```bash
cd web && npm run build
node tools/coverage/country.mjs --cc cz --json cz.json --brands 30
```

Base: `origin/main` at ca43083 (Estonia PR #9 merged). Both runs on the same register data (snapshot 2026-11-01; ČEZ
Distribuce's list "Stav k" 2026-08-21, re-downloaded 2026-11-12: same 113 093 bytes, same dates, so no new snapshot).

## Before and after

| layer | before | after |
|---|---|---|
| models in the CZ view | 13 048 | 13 048 |
| a · on ČEZ Distribuce's list | 784 | 784 |
| a · likely fit (maker's document) | 572 | 572 |
| a · possibly fit (other EU lists) | 10 206 | 10 206 |
| a · over the type-A limit (100 kW) | 1 031 | 1 031 |
| a · nothing known | 455 | 455 — every one legacy tier A (refused or expired on another list only); the page says so |
| b · "not shown" rows without a reason | 223 689 | **0** |
| b · rows checked by ČEZ Distribuce's list (`R`) | — | 9 408 (784 models) |
| b · rows met by the maker's document (`D` / `O`) | 610 / 72 | 16 / 0 — see "the accepted kind of document" below |
| b · rows met by datasheet (`S`) / over a line (`L`) | 6 434 / 2 576 | 6 587 / 2 657 |
| c · kW and phases, all models | 7 095 | 7 139 |
| c · kW and phases, models on the list | 531 / 784 | 575 / 784 |
| c · MPPT, PV models on the list | 244 / 782 | 289 / 782 |
| d · a datasheet or a maker's document, models on the list | 273 | 321 |
| e · legacy A / B / current | 535 / 190 / 12 323 | unchanged |

**Status re-read** (`--json` of both runs, model by model, 13 040 brand+model keys): **0 changed status, 0 changed
class.** 48 changed only their spec layer (44 Dražice from "none" to kW + phases, 41 of them with MPPT; 4 GoodWe ET
gained an MPPT count). 36 lost their document rows, each for the reason below.

## What changed, and why

- **Every row answers** (`data/profiles/cz.yaml` `list_checks`, `on_application`). The items come from ČEZ Distribuce's
  own installation documents A1 and A2 (revised 2026-03-19), whose table "on the basis of equipment certificates" names
  what a certificate or protocol proves: frequency stability, RoCoF, LFSM-O, under-frequency reduction and constant power,
  the logic module, reconnection, voltage stability, UVRT/OVRT, reactive power, Q(U), P(U), protection settings — and the
  RfG page says a listed type's protocol must show that the module "including the firmware and settings used meets every
  requirement of Příloha 4". So a listed model gets "checked by ČEZ Distribuce's list" on twelve items. Left out on
  purpose: the two A2-only items (power-reduction interface, power recovery), because three LEDVANCE rows of 15–25 kW are
  approved for category **A1 only** and the engine cannot read the category per row (an engine wish below); and the
  grid-monitoring switch and the storage response, which are not in the form's certificate table. Those rows on a listed
  model say why (`not_carried`); every row off the list says who checks it and on what papers (`on_application`).
- **The accepted kind of document** (PR #8 hand-over, point 2). The profile took any document citing "PPDS" as a national
  declaration. The A1/A2 forms take only a PPDS Příloha 4 certificate from a body accredited by **ČIA** (or a DSO
  laboratory protocol), and the certificate must name the methodology it was made by. The engine reads a document's
  `standards`, not its issuer, so `document_must_cite` is now the Czech test methodology: SZÚ's procedure
  `Metodika 0100 M 043` (what the SZÚ certificate cites), `MPO 2023` / `Metodika ověřování a prokazování souladu` (the
  operators' methodology for laboratory protocols). Effect: the SZÚ certificate B-00337-26 (Deye SG02HP3 60–80 kW, 4
  models) still proves its rows; Bureau Veritas U22-0790 / U23-0156 (DAkkS, Deye SG04LP3 and SG01HP3, 10 models), the
  SolaX declaration of 2022-12-20 (3 models) and the Sungrow declaration of 2021-01-22 (23 models) are shown by name as
  the kind they are and prove no row. Their grid cell is unchanged ("likely fit (maker's document)": the maker's document
  names Czechia) — see the engine wishes.
- **ČEZ Distribuce now names an end for laboratory proofs.** The RfG page (seen 2026-11-12) adds: from 2027-01-01 no
  certificate or protocol "valid until 2026-12-31" is accepted, and the revised A1/A2 forms name DSO protocols "issued by
  2025-12-31". The profile said ČEZd stated no end date; `list.gate`, `not_listed` and `changes` now carry it. The list
  prints no validity per row, so GridFit cannot yet say which of the 784 listed models are affected (an engine/parser wish).
- **Editions re-read 2026-11-12**: PPDS Příloha 4 2025 is still the current annex on ČEZd's PPDS page (no 2026 PPDS);
  Připojovací podmínky nn "Platnost od 1. 9. 2025" (file re-saved 2026-04-27, same 3.7 kVA / 10.8 kW / 16 A lines); VP_05 and
  VP_08 same sizes; the ČEZ list unchanged; no national list of certified devices found; the plug-in (800 VA) amendment
  still not confirmed passed.
- **Datasheets**: Dražice (new brand file, 47 rows from 7 product sheets and the 2025-10 catalogue on dzd.cz — 44 of its
  45 listed models; `IN.COMPACT 9.0K` is on no sheet). The list's typos are joined by `match` ("IN.HYBDRID COMPACT S/M",
  "IN.HYBRID COMPACT 5K-D/M" for 5.0K-D/M, "IN.Hybrid-One 3.0" for IN.HYBRID ONE 3.0K-D/M). GoodWe ET 5–10 kW (+4 rows from
  GW_ET_Datasheet-EN V2.0, read 2026-11-12).

## What is left in Czechia, and why

- **kW and phases on 209 listed models.** Largest: Sigenergy 46 (download centre refuses scripts — owner's list),
  Vonsch UNIRU 13 (no public sheet; vonsch.cz did not answer), Wattsonic G3 13 (wattsonic.com serves only the newer
  WattMatic/WattCision sheets), SolarEdge 11 (listed as wildcard patterns `SE3K-XXXTXBXX4`, deliberately not joined),
  Atmoce 11, BENEKOV ESCO 10 (Deye OEM: `BEN-…-SG04LP3-EU`, `ŘÍDÍCÍ MODUL BD …`), Turbo Energy 10, Chisage 8, Fronius 8,
  Vitron Energy 8 (MultiPlus II / Quattro codes, no sheet under that maker name). PR #11's model-code level will read many of them
  (Sigenergy, Wattsonic `WTS-10KW-…-3P`) at the "≈" level once merged.
- **MPPT on 493 listed PV models** — Fronius 52, GoodWe 34 (ET-20, ETA-G20, SDT-20 and KN-ET sheets not served at the
  usual Ftp path), Solinteg 29, Huawei 19 (terms forbid automated access), Kstar 15.
- **"Possibly fit" (10 206)**: accepted on other EU lists, nothing read in Czechia. A level, with its reason on the page.
- **"Nothing known" (455)**: legacy tier A, hidden by default, reason on the page.
- **The "ZUE" (storage) sheet has two rows**; hybrids on the inverter sheet are parsed as class `inverter` (Dražice IN.HYBRID,
  Turbo Energy Hybrid Series, BENEKOV). Their `storage` item is then not applicable. A class rule by model name is a parser
  change for the next register refresh (below).

## Engine wishes (not done here — `tools/check/**`, `web/src/**`, `tools/registers/**` belong to the engine session)

1. **Accept a document by issuer, not only by what it cites.** Add a profile key such as
   `document_issuer: ["SZÚ", "Strojírenský zkušební ústav", "ČEZ Distribuce", "EG.D"]` (or an `accredited_by: ČIA` field on the
   document) and have `classes_of` give `national-declaration` only to a document whose issuer matches. Today
   `document_must_cite` stands in for it (the Czech methodology), which a maker's declaration could also cite. Touches CZ only
   (4 models with the SZÚ certificate; 36 named-only). Test: `tools/check/run.py`, Deye `SUN-80K-SG02HP3-EU-EM6` × CZ keeps
   `D` rows; Sungrow `SG5KTL-MT` × CZ has `named`, no `doc`.
2. **The grid cell should follow `accepts`.** `ladder` gives "likely fit (maker's document)" (`D`) to any model whose document
   *names* the country (`row[10]`), even where the check engine says the operator does not take that kind of document. In
   CZ that is 36 off-list models (Sungrow 23, Deye 10, SolaX 3). Either build `row[10]` from the documents `check_model` takes
   for that country, or add a muted state "maker's document, not the kind the operator takes". Changes 36 CZ statuses
   (D → K); re-read model by model.
3. **Read the list's VM category per row.** ČEZ's "Kategorie VM" (A1, A1/A2, B1/B2 …) says whether the A2 items were
   tested. With it, `power-recovery` and `power-reduction-input` can be `R` on 734 rows of category A1/A2 and "not shown —
   approved for A1 only" on the 53 A1-only rows (3 of which, LEDVANCE LHT-HV-15/20/25K F1, are above 11 kW). Needs the
   category carried from `listing.json` into `checks.json` and a per-item condition in `list_checks`.
4. **Carry `cert_date` and the 2026-12-31 end.** The snapshot has `extra.cert_date` per CZ row; `web/.data/registers.json`
   drops it. With it the page can say "proof issued 2024-11-14; EG.D and PREdi take DSO protocols issued by 2025-12-31 until
   2026-12-31, ČEZd none valid only to 2026-12-31 from 2027-01-01". 700 of 819 inverter rows rest on a protocol.
5. **Class from the model name on the CZ inverter sheet** (`tools/registers/parse.py` `read_cz`): a row whose model says
   `HYBRID` / `HYB` (Dražice, Turbo Energy, OIG Power "Battery Box … se střídačem") is a hybrid. Changes class for about 40
   models; re-read on the next `refresh`.

## Documents only a browser (or the owner) gets

- Sigenergy datasheets for the 46 listed models — Sigenergy's download centre on sigenergy.com (refuses scripts; the Estonian pass found the same).
- EG.D's own laboratory list — https://www.egd.cz/laborator (403 to scripts, "maintenance" to headless Edge).
- Wattsonic G3 (WTS-…-3P-G3) datasheet — not on wattsonic.com/download.html; a Czech distributor (elfetex.cz) links one, not fetched.
- Vonsch UNIRU 400 sheet — https://www.vonsch.cz/ (no answer to scripts on 2026-11-12).
- Huawei SUN2000 datasheets (19 listed) — by hand only, under its terms.
