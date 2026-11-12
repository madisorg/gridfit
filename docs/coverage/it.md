# Italy — coverage of the country view

Written 2026-11-12, the method of `docs/coverage.md`. Base: `origin/main` at ca43083 (Estonia #9 merged, dataset
2026-11-09). Branch `riik-it`. Measured with `cd web && npm run build` then
`node tools/coverage/country.mjs --cc it --json …` on the base and on the branch.

## Before and after

| layer | before | after |
|---|---|---|
| models in the IT view | 13 048 | 13 048 |
| a · likely fit (maker's document) | 916 | **2 297** |
| a · possibly fit (other EU lists) | 8 109 | 7 223 |
| a · over the type-A limit (11.08 kW) | 3 699 | 3 219 |
| a · nothing known | 324 | 309 — every one legacy tier A (refused or expired on every list that carries it); the page says so |
| b · "not shown" rows without a reason | 194 968 | **0** |
| b · "not shown" rows with a reason (`on_application`) | 0 | 172 868 |
| b · rows met by the maker's document (`D`) / for an older edition (`O`) | 4 024 / 638 | 23 250 / 3 512 |
| b · models with every row answered by a paper | 319 | **1 774** |
| c · kW and phases | 7 095 | 7 095 (no datasheet work in this round, see below) |
| d · strongest source a maker's document | 904 | 2 285 |
| e · legacy A / B / current | 535 / 190 / 12 323 | unchanged |

Of the 1 774 models with a CEI 0-21 document, the newest edition cited: CEI 0-21:2026-07 18 (Fox ESS H3-Pro / AC3-Pro,
TÜV Rheinland A3 50749480 0001, 2026-10-16 — the first 2026-07 certificate GridFit has), V3:2025-10 107,
V2/EC2:2025-02 309, V2:2024-01 419, V1:2022-11 437, older 484. Every one but the 18 is "documented for an older edition":
`spi-settings` (59.S2) and `p-of-u` (P(U)_115) changed in 2026-07 and stay unverified on those models.

## Status re-read, model by model

13 040 model keys in both runs (8 keys repeat in the index); **0 changed class**, none left or appeared. **1 378 changed
status, all to "likely fit (maker's document)"**, each through one of the documents below:

| change | models | brands |
|---|---|---|
| possibly fit → likely fit | 884 | Sigenergy 91, SAJ 86, Growatt 85, Afore 77, Solis 71, GoodWe 66, Fox ESS 60, Fronius 48, Kstar 43, SMA 43, Solplanet 40, Enphase 35, SolarEdge 33, ABB / FIMER 32, INVT 24, Hypontech 23, Deye 13, KACO 12, SolaX 2 |
| over the type-A limit → likely fit | 479 | Solis 78, INVT 48, GoodWe 41, KACO 40, Kstar 36, Solplanet 32, Fronius 26, SAJ 27, Fox ESS 24, Sigenergy 24, Afore 23, Deye 21, ABB / FIMER 18, SMA 13, Hypontech 9, SolaX 9, SolarEdge 5, Growatt 5 |
| nothing known → likely fit | 15 | KACO 8, SolarEdge 3, Victron 3, SMA 1 |

"Over the type-A limit → likely fit" is the ladder's order (`web/src/lib/grid-filter.js`: the maker's document before
the 11.08 kW line); the model's rows still say "over 11.08 kW: type B, a procedure of its own" by its datasheet where
there is one.

## What changed, and why

- **Every row answers** (`data/profiles/it.yaml` `on_application`). Italy has no list, so `list_checks` does not apply;
  a row no datasheet or document shows now says that the maker's CEI 0-21 declaration (Allegato C), named in the
  operating rules, is what the grid operator reads at activation, with the on-site autotest.
- **The editions are still the profile's** (re-read 2026-11-12): CEI's catalogue entry for CEI 0-21 is the 2026-07
  edition (in force 2026-08-01) with V1:2026-08 (Allegato X); no later variant or errata was found. The full 2026-07 text
  is served by CEI (`static.ceinorme.it/strumenti-online/doc/26363.pdf`, 338 pages, file dated 2026-07-31) and is now a
  source of the profile. e-distribuzione's connection guide section B is still edition 8.0, May 2026 (Last-Modified
  2026-05-29).
- **59.S2, read from the text**: table 13 (p. 98) prints 1.15 Vn **0.5 s**, and so does table 14 (below 800 W); the
  settings form of the operating rules above 11.08 kW, Allegato G (p. 269), still prints **0.2 s**; the 2025-10
  consolidated text had 0.2 s in table 13. The profile's sentence now says exactly that, and the pre-certification
  pilot (`tools/reports/country_values.yaml`, IT block) accepts 0.2–0.5 s with the note (no document's result changed).
- **152 makers' documents for 21 brands**, appended to `data/evidence/<brand>.yaml` (ids `it-…`, `countries: [IT]`),
  six new brand files (Enphase, Fimer, Hypontech, INVT, Kaco, Sigenergy). All from the makers' own sites, each
  `match` tested against the register codes; a code with a hardware suffix the document does not name is not joined.

| brand | documents | of which the maker's own declaration | editions cited |
|---|---|---|---|
| GoodWe | 18 | 4 | 2019-04 – V3:2025-10 |
| Solis | 17 | 3 | 2022-03 – 2025-09 |
| SolaX | 10 | 0 | 2022-03 – V2/EC2:2025-02 |
| Fimer (new file) | 9 | 1 | V2:2024-01 – V3:2025-10 |
| Fox ESS | 9 | 0 | 2019-04 – **2026-07** |
| Fronius | 8 | 1 | 2019-04 – V2/EC2:2025-02 |
| Growatt | 8 | 0 | 2019-04 – V3:2025-10 |
| SMA | 8 | 0 | V1:2022-11 – V3:2025-10 |
| Solplanet | 8 | 0 | 2022-03 – V2:2024-01 |
| Afore | 6 | 0 | 2022-03 – V2:2024-01 |
| Deye | 6 | 1 | 2019-04 – V2:2024-01 |
| Hypontech (new) | 6 | 0 | 2021 – 2024 |
| Kaco (new) | 6 | 0 | 2019-04 – V3:2025-10 |
| Kstar | 6 | 0 | 2021 – 2023 |
| SAJ | 6 | 0 | 2022-03 – V2:2024-01 |
| ABB | 5 | 0 | V2:2024-01 |
| Enphase (new) | 5 | 3 | 2022-03 – V2/EC2:2025-02 |
| SolarEdge | 4 | 0 | 2022-03 – 2024 |
| INVT (new) | 3 | 0 | 2022 |
| Sigenergy (new) | 3 | 0 | V1:2022-11 – 2023 |
| Victron | 1 | 0 | 2014 (MultiPlus 3 kVA, both -16 and -50 named) |

- **Victron's documents now join** (separate commit, test in `web/test/checks.mjs`): `data/evidence/victron.yaml` said
  `brand: Victron Energy` while the register's brand is `Victron`, so its AT, BE, PL and DE documents reached no model in
  any country (AT 93 → 105, BE 96 → 108 documented models with the fix alone). A test now holds every evidence file's
  brand to a register brand.

## What is left in Italy, and why

- **"Possibly fit" 7 223**: accepted on other EU lists, no Italian document found. The largest: SAJ 417 (the EK70/EK90
  HS5 kits, HS2/AS2 — only a CEI 0-16 certificate, which is medium voltage; SAJ's EU declarations print "CEI 0-21:2022-03"
  for every family alike and were not taken as a CEI 0-21 declaration), Fox ESS 231 (PQ3/P3 series, nothing published),
  Hoymiles 216 (1 940 files in the download centre, none a CEI document), Deye 195 (SG05LP1/SG04LP1/SG02LP1, SG05LP3,
  G05/G06, micro: nothing in the download centre), Growatt 171 (see the owner's list), Sofar 150 (1 094 certificates and
  every EU declaration read: none cites CEI 0-21; Sofar sells in Italy as ZCS Azzurro, another company's documents),
  Sigenergy 145 (Neo, TP2/SP2, LV/BE, C&I), TSUN 106 (a press release only), Anker 104, Enphase 112 (rows that pair an
  inverter with a non-Italian relay or a balcony kit), Huawei 83 (its terms forbid automated access).
- **"Likely fit" on a document of another kind, 523 models**: SolaX 333 (the safety-code list), ZCS 78 (the safety
  standard table), Sungrow 52 (the country-code overview v3.5, still the newest), Kostal 38 (released countries), Sofar
  14, GoodWe 8 — the maker's document names Italy, but it is not a CEI 0-21 declaration, so the rows say "not shown" with
  the reason and the page names the kind of document the operator takes.
- **"Nothing known" 309**: legacy tier A, hidden by default, the reason on the page.
- **Specs (layer c)**: unchanged; the datasheet work is shared by every country and the brands sold in Italy were
  covered for Estonia already (ZCS 81 %, SAJ 80 %, Solis 73 %, Sofar 73 %). The widest Italian gaps are Sigenergy 34 %,
  Hypontech 20 %, Autarco 5 % (no sheets cached; Sigenergy's centre answered scripts this time) — a datasheet round, not
  an Italian one.
- **Medium-voltage documents found and not used**: CEI 0-16 certificates for Fronius Eco, Tauro Eco and Argeno 125, SMA
  SHP-21, SolarEdge TerraMax, Fimer PVS-60/120/175, Kaco 87–165 TL3 and 360 NX3, GoodWe ET 15–30 kW, SAJ HS2/AS2,
  Solis GU3P. The Italian view is the low-voltage rule (CEI 0-21); see the engine wishes.
- **Joins left for one session after the parallel round** (existing entries in shared brand files, not rewritten
  here): SMA's STP xx-50, 3AV, 3SE and Smart Energy regexes miss the `SUNNYTRIPOWER…` spellings of their own codes; the
  SolarEdge Home Hub regex misses the `HOMEHUB…` prefix; Fox ESS S22/MQ2200 expects `MQ-2200` (2 codes); Sungrow's overview
  misses `SH5.0T` / `SH10.0RT(-20)` / `SG7.0RT(-P2)` spellings (5–7 rows). Each subagent report has the corrected regex.
- **Not joined on purpose**: Kaco blueplanet 3.0–10.0 and 15.0/20.0 TL3 (the register writes the name without the M2
  the certificates name), Kaco 25–33 NX3 (bare "25.0" rows that could be a Powador), Fronius Primo "3.0-1 M" (the register
  has no M), Fox ESS GM241 (the register says TM241) and GM215 `-2HF` (the certificate names `-2h`).

## Engine wishes (for one engine session)

1. **Wallboxes in the check** — from 2027-01-01 every new non-public charging point must be certified to CEI 0-21
   Allegato X (`changes` in the profile). `tools/check/run.py` checks no wallbox (568 Italian models are "no model-level
   requirement"). Needed: wallboxes in the engine and a must_meet item with a start date (`from: 2027-01-01`) so the row
   says "required from 1 January 2027" until then. Test: a wallbox × IT gets the Allegato X row, N with the reason before
   any document.
2. **A document the operator does not take should not make the cell "likely fit"** — the ladder takes any maker's
   document naming the country (`row[10]`), the checks only the kinds in `accepts`. In Italy 523 models are amber "likely
   fit" on a firmware grid-code list or a released-countries table. Either a separate cell word ("the maker names Italy;
   no CEI 0-21 declaration found") or `doc` in the index only for accepted kinds. Test: SolaX X3-HYB-10.0-P × IT (amber on the safety-code list, every row "not shown").
3. **Medium-voltage documents** — a CEI 0-16 certificate is the right paper for a unit connected at MV (above ~100 kW),
   and makers publish them beside CEI 0-21. An evidence `scope: mv` (shown, never counted for the LV profile) would let
   GridFit carry the ten documents above. Test: Fronius Tauro Eco 100 × IT shows the CEI 0-16 certificate and keeps its
   rows "not shown".
4. **Declaration tick boxes** (`docs/checks.md` already names it): "SPI integrated" and "fit for plants above
   11.08 kW" are printed in most of the 152 documents and noted in the family `note`; as fields they would answer
   `spi-integrated` and `frt` without the datasheet.

## Documents for the owner to download by hand

- **Growatt** (en.growatt.com, robots.txt `Disallow: /upload/`): MOD 3–15KTL3-X
  `https://en.growatt.com/upload/file/MOD_3-15KTL3-X_CEI_0-21.pdf` (17 codes); MOD 3–15KTL3-HU
  `https://en.growatt.com/upload/file/MOD_3-15KTL3-HU_IEC_0-21_Certificate.pdf` (12); MID 11–30KTL3-XH
  `https://en.growatt.com/upload/file/MID_11-30KTL3-XH_CEI0-21.pdf` (8); MID 30–50KTL3-X2
  `https://en.growatt.com/upload/file/MID_30-50KTL3-X2_CEI_021.pdf`; MAX 50–80KTL3 LV
  `https://en.growatt.com/upload/file/MAX_50-80KTL3_LV_CEI_0-21.pdf` (8). growatt.it is not linked from growatt.com and
  was not used.
- **GoodWe** (en.goodwe.com, robots.txt `Disallow: /download`): the English download centre `https://en.goodwe.com/download`
  → Certificate, for SDT G2 / DT, NS, ET G1 5–10 kW, ET 15–30 kW, ETC/BTC, ET 75–100 kW G10, HT, ES, SBP, GT-G30.
- **SolarEdge** (403): `https://knowledge-center.solaredge.com/sites/kc/files/se-three-phase-inverter-with-synergy-technology-cei021-certificate-it.pdf`
  (Synergy SE50K–SE100K), `https://knowledge-center.solaredge.com/sites/kc/files/se-solaredge-css-od-battery-inverter-grid-certificate-italy.pdf`.
- **SolaX**: `https://www.solaxpower.com/downloads.html` filtered to Italy / certificates (the list comes from an API
  robots.txt disallows) — X1-Smart G2, X1-Lite LV, X1-Vast, X3-NEO-LV, X3-GRD, Retrofit G4.
- **APsystems** (robots.txt `Disallow: /` on the file host): the CEI 0-21 certificate in each share — DS3
  `https://apsystems.filecloudonline.com/url/xfwedtvhhmneahs4`, EZ1 `https://apsystems.filecloudonline.com/url/dssucipqn2ru4bpk`,
  QT2 `https://apsystems.filecloudonline.com/url/nzaz2axrewsxndmb` (the other twelve shares are in the run's notes).
- **Sungrow**: `https://support.sungrowpower.com/` (login) — a newer Country Code Overview than v3.5 and the CEI 0-21
  declarations for SH-RS/-RT, SG-RS/-RT, SBR.
- **Huawei**: the SUN2000 CEI 0-21 declarations, by hand only (its terms).
- **TSUN**, **Hoymiles**, **Pylontech**, **Victron (MultiPlus-II)**: nothing public; only on request from the makers.
- Afore's `https://enjiu.aforenergy.com/service/download` did not answer; worth one look for 2026 certificates.
