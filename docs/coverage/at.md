# Coverage of the Austrian view

Written 2026-11-12, by the method of `docs/coverage.md` (Estonia first). Command: `cd web && npm run build`, then
`node tools/coverage/country.mjs --cc at --json …`. Base: `origin/main` at ca43083 (Estonia #9 merged, dataset
2026-11-09).

## Sources re-read

- **E-Control's TOR page, 2026-11-12**: TOR Stromerzeugungsanlagen Typ A **V1.4** (the profile's file, same URL) and TOR
  Verteilernetzanschluss Niederspannung **V1.3.1** are still the current parts; no new consultation for either. The profile
  stands as written on 2026-11-01.
- **The Wechselrichterliste was not fetched.** `www.wechselrichterliste.at/robots.txt` is `User-agent: *` / `Disallow: /`
  (read 2026-11-12). The list rows are the 2026-10-30 file in the 2026-11-01 snapshot; the admission page was read on
  2026-11-01. The monthly register run fetches the file anyway — that is a choice for the owner (below), not changed here.

## Before and after

| layer | before | after |
|---|---|---|
| models in the AT view | 13 048 | 13 048 (the 17 wind-turbine inverters leave at the next register refresh, see below) |
| a · on the list (`Ja`) | 664 | 664 |
| a · on the list with a condition | 2 634 | 2 634 |
| a · refused / not allowed (`Nein …`) | 743 | 743 |
| a · likely fit (maker's document) | 413 | **516** |
| a · possibly fit (other EU lists) | 8 138 | 8 035 |
| a · over the type-A limit (250 kW) | 416 | 416 |
| a · nothing known | 40 | 40 — every one legacy tier A (expired on another list only); the page says so |
| b · "not shown" rows without a reason | 200 291 | **0** |
| b · rows checked by the Wechselrichterliste | — | 35 490 (2 730 models) |
| b · rows met by a maker's document (`D` + `O`) | 1 391 | 3 768 |
| b · models with every row answered by a paper | 35 | 344 |
| c · kW and phases | 7 095 | 7 095 — every listed model 4 041 / 4 041 (the list states kVA and phases) |
| c · MPPT, PV models on the list | 436 / 3 036 | 436 / 3 036 |
| d · a datasheet or a maker's document, models on the list | 676 | 881 |
| d · models with an accepted Austrian document (check) | 93 | 657 |
| e · legacy A / B / current | 535 / 190 / 12 323 | 535 / 190 / 12 323 |

**Status re-read**, model by model over the 13 040 distinct (brand, model) keys of both runs: **103 changed status, 0
changed class**. All 103 are "possibly fit" → "likely fit (maker's document)", each joined by one of the new documents:
Sofar 44, Sigenergy 13, Deye 12, Kstar 12, SMA 10, Anker SOLIX 6, Kostal 4, SolarEdge 2. No listed model changed (the
list is read first), and no other country's line in the check changed (`tools/check/run.py` stats, before and after).

## What changed, and why

- **Every row answers** (`data/profiles/at.yaml` `list_checks`, `on_application`). A model admitted by the list gets
  "checked by the Wechselrichterliste" on the 13 TOR Typ A items a document can prove (frequency and voltage ranges,
  RoCoF, LFSM-O, under-frequency, FRT, protection settings, loss of mains, reconnection, reactive power, P(U), remote stop,
  locked settings / parameter export): the list reads the R 25 report with the Austria setting before listing, and TOR
  Typ A V1.4 8.1 note 37 counts the proof as given. Left out on purpose: **storage**, a TOR Verteilernetzanschluss rule the
  list's own words ("all TOR Typ A requirements") do not name, and the **rated-power lines**, which GridFit judges on the
  maker's sheet — on a listed model they say the list states the figures (on the row) and the operator applies the line.
  A model off the list, or with a "Nein" row, says the operator checks it on the application against an R 25 report, the
  Austria-setup confirmation and a machine-readable parameter export.
- **66 Austrian documents, 15 brands** (`data/evidence/*.yaml`, ids `at-tor-…`, append only): Sofar 13, ZCS Azzurro 14,
  Kostal 12, Deye 3, Growatt 4, Kstar 3, Fox ESS 3, Afore 1, GoodWe 1, SolaX 2, SMA 2, SolarEdge 2, Hoymiles 2, Anker
  SOLIX 2 (new file, register brand `Anker`), Sigenergy 2 (new file). Each is a certificate citing TOR Erzeuger /
  Stromerzeugungsanlagen Typ A and (all but two) OVE R 25, transcribed from the PDF; 573 register models join one.
  Where only a wholesaler's copy could be read, `copy_of` says who hosts it. Every one cites an edition older than V1.4
  (2026-06): the page counts the items changed since (`reactive`, `settings-protection`, both 2024-07).
- **Wind turbine inverters are not PV inverters** (`tools/registers/parse.py` `read_at`). The list's
  „Windenergie-Wechselrichter“ rows (16 Solarinvert WIN, 1 Schachner generator) were read as class `inverter` ("PV
  inverter") because the word contains „wechselrichter“; they are class `other` now, which the site does not show. Tested
  on the local 2026-10-23 file (17 rows → `other`); it lands with the next `refresh` run (snapshots are not committed here).

Not added, on purpose: **Type B-only certificates** (GoodWe GW75–100K-ET-G10 DEKRA 6235591.02, SMA STP 15–25000TL-30
U21-0478 and STP 50-40/41 U21-0477, SolarEdge SE50–120K U21-0828; Kostal and KACO Type B files) — they are not Type A
evidence, though they would match the profile's "TOR Erzeuger" key (see the engine wish); superseded editions (Sofar
CN-PV-210152, Sigenergy CN-PV-230566, Kostal 1671 declaration); Kostal's settings declaration 1675 (names families, not
models); Sofar's Typ B-only 25–50 / 60–80KTLX-G3 files.

## What is left, and why

- **"Possibly fit" (8 035)** — accepted on other EU lists, nothing Austrian read. Largest: SAJ 661, Fox ESS 408, Growatt
  251, Afore 228, Deye 227, Sigenergy 203, Solis 201, GoodWe 189, Sofar 152, INVT 150. SAJ, INVT, Solplanet, Sinexcel,
  Hypontech and Sunsynk publish no TOR / R 25 document anywhere a script may read (their download centres were listed
  in full); the rest are other model series than the ones documented.
- **MPPT on listed PV models (436 / 3 036)**: the list carries no MPPT count and the datasheets are not harvested for
  most listed series (Hoymiles, GoodWe, Solis, Enphase, Huawei). It is not part of "at some level" (kW and phases are).
- **"Not shown" with a reason (172 994 rows)**: mostly off-list models (`on_application`) and the rated-power lines of
  listed models without a sheet (10 249 rows on 2 482 models, `not_carried`).
- **Register spellings not joined** (a suffix is another model): Sofar `…KTLX-G3P` vs the certificate's `-G3-PRO`,
  Growatt `MOD…-XH(OPTIONAL MIT SYN100-XH-30)`, Anker `AE1038Z1(HB:SOLARBANK4)`, ZCS `3PH15000KTL-V3` and `3PH125KTL-V4`,
  SolaX `X3PROG2…`, `-LV`, `-T-DG2`, Deye `-AM2` 30–50 kW and `-DM2`.

## Documents only a browser (or the owner) can get

| maker | what | why a script did not |
|---|---|---|
| Solis | TOR / R 25 certificates S6-EH3P(12-20)K-H, S6-EH3P(29.9-50)K-H, S6-GC3P(25-36)K, S6-GC(50-75)K-LV / (80-125)K — `solisinverters.com/uploads/file/Solis_certificate_TOR_R25_…_Austria_V0x.pdf` | robots.txt disallows `*.pdf` and `/uploads/file/*` |
| KACO | 14 TOR Typ A / R 25 certificates (blueplanet NX1, NX3 3–125, TL3 3–165, hybrid NH3 and 10.0 TL3, gridsave 50–137): TÜV Rheinland A3 50629843 / A3 50616329, TÜV SÜD ESY 064946 0009 / 0005 / 0022, BV U22-0562 / U21-0890 / U21-0411 / U21-0248 / U24-0001, Kiwa 22-098-00, CERE 21252 / 21014-15 | found through the site search, whose URL robots.txt disallows; confirm from the product pages' download tabs (JavaScript) before they are added |
| SolarEdge | `se-single-phase-inverter-certificate-austria.pdf`, `se-extended-power-three-phase-inverter-certificate-austria.pdf`, `se-inverters-manufacturer-parameter-declaration.pdf` (knowledge-center.solaredge.com) | Cloudflare |
| Enphase | IQ8MC / IQ8AC / IQ8HC + IQ Battery TOR Erzeuger V1.2 declaration (2023-08), IQ8X TOR declaration (2024-07), IQ7 A3 60166810 0001 (enphase.com/de-de/download/…); EnTEST COCP2024102501 on creaton.de has its model table as an image | 403 to scripts; the image table needs a person's reading |
| SolaX | X3-ULTRA TÜV Rheinland A3 50651311 0001 | the download list is behind `/ysecm_api`, which robots.txt disallows |
| GoodWe | the TOR certificates on `en.goodwe.com/download` | robots.txt disallows `/download` |
| Sungrow | SH5.0–10RT „UNBED TOR Erzeuger Typ A R25“ U22-0105 (sungrowpower.com/de) | the download list loads by JavaScript |
| Sigenergy | the maker's own copies of CN-PVES-230566R1 and VHC2407160090GC01-R1 (sigenergy.com download centre) | 403 to scripts |
| SMA | Type A certificates U20-1016 (STP TL-30) and U21-0206 (STP 50-4x), cited in the Type B ones | not found |
| Hypontech / Sunsynk | any TOR document | a signed, encrypted download API / an installer login |

## The owner's choice: the Wechselrichterliste and robots.txt

`www.wechselrichterliste.at/robots.txt` disallows every path for every agent, and the site states no reuse terms. The
monthly register run downloads the xlsx regardless. Options: ask Oesterreichs Energie for permission (the clean route);
keep the run as it is; or stop the script and download the file by hand when it changes (it moves several times a month).

## Engine wishes (not done here: engine files belong to the engine session)

1. **The list's own figures for the rated-power lines** (`tools/check/run.py`, `web/src/lib/checks.ts`). AT (and SE) lists
   state kVA and phases; on a listed model without a sheet, `power-class`, `phases`, `protection-place` and
   `simplified-procedure` stay "not shown" (10 249 AT rows, 2 482 models). A state "by the list's figure" (weaker than a
   sheet) would answer them. Test: a listed model without a sheet gets that state on the four rows, and a sheet still wins.
2. **Grid "likely fit" and the check disagree for 345 AT models** (`web/src/lib/grid-filter.js` `ladder` vs the check's
   `accepts`): the grid marks D for any maker's document naming AT, including grid-code-setting tables (SolaX 290, ZCS 40,
   Kostal's released-countries 12, GoodWe 3), while the check's block says the document is not a kind the Austrian
   operator takes. Either the grid word or the check should name the kind. Test: the 345 models show the same reading in
   both places.
3. **Type A is not explicit in `document_must_cite`** (`tools/check/run.py` `classes_of`): "TOR Erzeuger" also matches a
   Type B-only certificate, so adding one would wrongly cover Type A rows. A profile key for a required pattern (e.g. "Typ
   A|Type A") or an exclusion would close it; no Type B-only document is in the data today.
4. **A settings declaration as evidence** (`data/evidence` schema): Kostal 1675 lists the Austrian trip values per family —
   the `lom-protection` / `lfsm-o` rows could read it, but the schema has no field for a settings table.
