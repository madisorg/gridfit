# Germany — coverage of `/grid/de/` (2026-11-12)

The method and the measure are `docs/coverage.md`. This file is Germany's before and after, what changed and why, what is
left, and what the engine would need next. Base: `origin/main` at ca43083 (Estonia #9 merged, dataset 2026-11-09).

```bash
cd web && npm run build && cd .. && node tools/coverage/country.mjs --cc de --json de.json
```

## What Germany is

There is no list to be on. The grid operator takes the model's VDE-AR-N 4105 unit and NA-protection certificates, and
since 1 February 2025 only through the ZEREZ-ID (NELEV § 4(9)–(10)). ZEREZ is the register of those certificates. GridFit
does not read it: there is no reuse licence and no API account yet (`docs/zerez.md`). So the profile gets no `list_checks`.
It gets `on_application`, and the evidence is the makers' own certificates.

## Before and after

| layer | before | after |
|---|---|---|
| models in the DE view | 13 048 | 13 048 |
| a · likely fit (maker's document) | 797 | **1 831** |
| a · possibly fit (other EU lists) | 11 070 | 10 041 |
| a · over the type-A limit (135 kW) | 706 | 701 |
| a · nothing known | 475 | 475 — every one legacy tier A (refused or expired on another country's list only); the page says so and hides them by default |
| b · "not shown" rows without a reason | 135 115 | **0** |
| b · "not shown" rows with a reason | 10 570 | 133 950 |
| b · rows by the maker's document (D + O) | 1 179 | 12 778 |
| b · models with every row answered by a paper | 50 | 452 |
| c · kW and phases | 7 095 | 7 126 |
| c · MPPT, PV models | 1 757 / 10 419 | 1 799 / 10 419 |
| d · a datasheet or a maker's document | 2 362 | 3 100 |
| d · strongest source a maker's document | 785 | 1 819 |
| e · legacy A / B / current | 535 / 190 / 12 323 | the same |

Every Germany document so far cites VDE-AR-N 4105:2018-11, so every documented row is "documented for an older edition"
against the profile's 2026-03. That is right until **1 March 2027**, when the transition ends (see the profile below).

## Status re-read, model by model

Of the 13 040 (brand, model) pairs in both runs, **1 034 changed status and 0 changed class**:

- **possibly fit → likely fit, 1 029.** By brand: Solis 210, Sofar 166, Deye 154, Fronius 118, Enphase 81, GoodWe 70, Anker 58,
  Victron 49, Fox ESS 36, Solplanet 22, EcoFlow 13, APsystems 13, RCT Power 10, Zendure 10, Kostal 9, SAJ 5, SMA 5. In each case
  a new VDE-AR-N 4105 certificate names the unit. Victron's 49 include 31 that the three German certificates already in the
  repo should have reached: they never joined (silent bug 1 below).
- **over the type-A limit → likely fit, 5.** GoodWe GW125K-GT and GW150K-GT-G10, Solis S6-GC125K-HV, S6-GC3P150K07-NV-ND and
  S6-GC3P200K07-HV-ND. The maker's VDE-AR-N 4105 certificate names each of them, and VDE-AR-N 4105:2026-03 reaches 500 kW
  cumulative. The ladder (`grid-filter.js`) puts the maker's document before the 135 kW line. The `power-class` row still
  says "over a line: other procedure".
- Nothing went the other way, and no model left the view or changed class. The SMA datasheet rows added kW or phases to 31
  models, and none of them crossed 135 kW.

### Two silent bugs, found by this re-read

1. **Victron's evidence never joined.** `data/evidence/victron.yaml` said `brand: Victron Energy`, which is the display name;
   the register's brand is `Victron`, and the loaders key on `brand` lowercased. Ten documents in five countries, three of them
   German, joined no model. The fix is one line (commit f15c6bc). Spain's branch (#17) found and fixed the same line and carries
   the test that every brand file names a register brand, so this branch does not repeat the test. A new Anker file was
   about to make the same mistake (`Anker SOLIX`) and is `brand: Anker` in `anker.yaml`, the file name Austria's branch (#16)
   uses.
2. **A 2018-edition certificate issued after March 2026 would pass as the 2026-03 edition.** `tools/check/run.py`
   `edition_of` reads an edition only as `YYYY-MM`. TÜV Rheinland prints "VDE-AR-N 4105/11.18", others "VDE-AR-N 4105:2018".
   Neither matches, so the engine falls back to the issue month, and a certificate issued in July 2026 to the 2018 edition
   would count as current. That is the case for Anker Solarbank Max (2026-07-10), Solis S6-EH1P-L-PLUS (2026-07-13) and
   Deye's SUN-BK AM2 (2026-07-22). The engine is left alone. Each new document keeps the standard as printed and adds the edition
   beside it ("VDE-AR-N 4105/11.18 (2018-11)"). The engine fix is under "Engine requests". One document already on main has the
   bare print: Deye `de-vde4105-sg06lp1-2026`, which joins no register model, so it changes nothing today.

## What changed, and why

- **Every row answers** (`data/profiles/de.yaml` `on_application`). A row that neither a datasheet nor a certificate shows says
  that Germany has no list, that the grid operator reads it from the model's unit and NA-protection certificates in ZEREZ
  through the ZEREZ-ID, and that GridFit does not read ZEREZ yet.
- **The profile is the one VDE FNN serves today.** VDE-AR-N 4105:2026-03 is still the edition in force; no correction and no
  amendment have been published. VDE FNN's FAQ to section 9.2 now names **01.03.2027** as the end of the transition: until then
  2018-11 unit certificates are accepted, and a maker's declaration in ZEREZ or a 2018 PAV,E-monitoring certificate is enough
  for the PAV,E protection. The profile had assumed "about 1 March 2028", which is the § 9 EEG 60 % deadline (FAQ to 5.7.4.1),
  not the certificate one. Corrected in `edition`, `unit-certificate`, `changes` and `sources`. The EEG 2027 line now says
  "cabinet draft 29 July 2026, not adopted" (press reports, not confirmed).
- **159 makers' certificates**, VDE-AR-N 4105 unit certificates (Einheitenzertifikat) and NA-protection certificates, from 21
  brands, each read from the maker's own file, appended to `data/evidence/<brand>.yaml` (6 new files: `anker`, `apsystems`,
  `ecoflow`, `enphase`, `rctpower`, `zendure`). By brand: Fronius 20 (GEN24, Symo, Primo, Eco, Tauro, Verto / Verto Plus),
  Deye 22, Sofar 22, Solis 19, GoodWe 14, Zendure 12, Enphase 8, EcoFlow 7, Anker 6, Kostal 5, Fox ESS 5, APsystems 4,
  Solplanet 4, Victron 4, SolaX 3, RCT Power 2, SMA 1, SAJ 1. Where the register spells a unit two ways, both spellings are
  joined. A certificate that covers a unit only in a combination joins only that combination (Enphase IQ Balcony: the bare
  IQ8PLUS-72-M-INT is left out).
- **SMA datasheets** (`data/specs/sma.yaml`, 13 → 67 register models): Sunny Boy 1.5–2.5 VL-40 and 3.0–6.0 AV-41, Sunny Boy
  Storage 2.5 / 3.7–6.0, Sunny Tripower 15000–25000TL-30 and CORE2, and rows for the register's long spellings of STP xx-50.
  The sheets were already in `cache/specs/sma/`, read 2026-11-12, and their URLs are live.

## What is left in Germany, and why

- **"Possibly fit" (10 041).** These are accepted on other EU lists, but GridFit holds no German document for them. It is a
  level, and the page gives the reason. The largest German gaps are the brands whose certificates a script may not fetch, or
  that are not published at all:
  - **Not published:** SAJ 705 (the maker publishes a German certificate only for CHS2), Sigenergy 313, Huawei 134, SolarEdge 113,
    KACO 115, Afore 247, Kstar 126, Pylontech 121.
  - **Not fetched:** Growatt 367 (61 certificates sit under `/upload/`, which robots.txt disallows), Hoymiles 234.
- **"Nothing known" (475).** Legacy tier A: refused or expired on another list only. The page says so and hides them by default.
  All 12 SENEC.Home rows are among them. SENEC publishes no certificate (its "Zertifikate" ZIP holds EDI X.509 certificates).
- **kW and phases (7 126 of 13 048).** Sigenergy 214 and SolaX 197 are missing most. Sigenergy refuses scripts. SolaX's sheets
  are mostly cached but not transcribed. Next comes the long tail of Chinese brands with no sheets in the cache. A
  certificate's E.4 table prints the unit's rated power and phases; reading that table is an engine request below.
- **§ 14a EnWG controllability** is the consumer's largest question in Germany. It is not a grid-approval property of the
  model, and it stays a note in the profile.

## Documents only a browser gets (Madis's list)

Each of these would turn a brand's "possibly fit" rows into "likely fit". Save the PDF and give it to a session. The session
then transcribes the PDF, as with the other 159. The row counts are estimates made from the family names.

| brand | what | where | DE rows |
|---|---|---|---:|
| Growatt | 61 VDE-AR-N 4105 unit and NA certificates (MIN, MOD, MID, MIC, MAX, SPH/SPA, WIT, NEO, NEXA, MODA). A script may not take them: robots.txt `Allow: /` then `Disallow: /upload/`, and the longest match wins (RFC 9309) | https://en.growatt.com/support/download/certificate?keyword=4105 (7 pages) | ~250 |
| GoodWe | 22 certificate titles whose file is only behind `admin.goodwe.com` (robots `Disallow: /`): SDT G2, MT, XS / XS PLUS+, ET PLUS+ / BT, EH / BH, ES / ESA, ETC / BTC, ETR, PCS, SMT 25–60K, DNS 2022; plus two scans (HT 1100V, SDT G2 17–25K) | the series pages on https://de.goodwe.com (filter Zertifikat) | ~120 |
| Huawei | SUN2000-3–10KTL-M0/M1 (BV U20-0249, U21-0458/0459), SUN2000-2–6KTL-L1 (U21-0557/0558), SUN2000-30–40KTL-M3 (U21-0103), SUN2000-8–20KTL-M0 NA (U21-0556); still to find: MAP0, MB0, LB0, MC0, LUNA2000. Not by script: Huawei's terms forbid automated access | https://solar.huawei.com/de/download (certificates) | ~130 |
| SMA | the residential VDE-AR-N 4105 unit and NA certificates: Sunny Boy AV-41 (lead BV U21-0056) and VL-40 (U21-0054), Tripower Smart Energy (A3 50540179 0001), Sunny Boy Smart Energy, Tripower X, Tripower AV-40 NA, Sunny Boy Storage / Sunny Island (U20-0254), Tripower Storage (U23-0295), Tripower Hybrid X. The download centre is JavaScript and its search is disallowed | https://www.sma.de/service/downloads (filter Zertifikate, Deutschland) | ~90 |
| Sungrow | SH-RT / SH-RT-20 (lead A3 50564350 0001), SH-T (also the 2026-03 certificate Sungrow announced), SG-RT / RT-P2, SH-RS / SG-RS | https://support.sungrowpower.com → Download → product → Certificate | ~60 |
| SolaX | X1-Hybrid G4, X3-Ultra, X1/X3-IES, X3-Pro G2, X1-Mini G4, X3-Forth (`/ysecm_api` is disallowed) | https://de.solaxpower.com/downloads.html | ~90 |
| SolarEdge | Home Wave / Home Hub 1-phase and 3-phase, StorEdge (Cloudflare) | https://www.solaredge.com/de/download-center | ~110 |
| Sigenergy | SigenStor / Sigen Hybrid / PV Max unit certificate (a reseller copy names CN-PV-230539) | https://www.sigenergy.com/de/support/download | ~310 |
| Fox ESS | scans with no text layer: T-G3 (COCPVP11004…), H1-G2 / AC1-G2 (COCPVP0210323E-03/-04), M series | the `www.fox-ess.com/Public/Uploads/…` files named in the notes | ~45 |
| Kostal | NA certificates for PLENTICORE plus G2, PIKO IQ / plus G1, BI G1; PIKO MP plus; MP M G3 5.0–7.0 | https://www.kostal-solar-electric.com/de/download/ (Land Deutschland, Zertifikate) | ~25 |
| Solplanet | ASW5–12KH-T2/T3: on the maker's site, but the pages are image tiles | https://solplanet.net/wp-content/uploads/2024/01/Cer_VDE-4105_ASW5-12KH-T3_de_V0116.pdf | ~25 |
| Enphase | IQ8 / IQ8PLUS / IQ8A / IQ8H with IQ Relay; IQ8 with System Controller 3; IQ Battery 5P FlexPhase | https://enphase.com/de-de/installers/resources/documentation | ~40 |
| APsystems | DS3D, EZ1D, QT2 / QT2D, QS1 / QS2, YC600 / YC1000, APstorage (FileCloud, robots `Disallow: /`) | the FileCloud folders linked from https://emea.apsystems.com/document-library/ | ~20 |
| Anker | X1 hybrid 1-phase and 3-phase (Salesforce support pages), Solarbank 4 unit certificate | https://support.ankersolix.com/de | ~45 |
| KACO, Alpha ESS | blueplanet NX3 / TL3 / gridsave; SMILE-G3 / SMILE5 / STORION (script-only centres) | kaco-newenergy.com/downloads; osc.alphaess.com | ~120 |
| ask the maker | Hoymiles (HMS/HMT/HYS/MS-A2), sonnen, SENEC, E3/DC, TSUN, Marstek, EcoFlow STREAM, Deye SG05LP1 (the listed file is gone) | — | ~330 |

## Engine requests

These are left for one engine session. None of them is done here.

1. **Read the edition in every print** (`tools/check/run.py` `edition_of`). Read "4105/11.18" (MM.YY after a slash) and a bare
   year where the norm has one edition that year ("VDE-AR-N 4105:2018" → 2018-11, "DIN VDE V 0124-100:2020" → 2020-06). Today
   such a document falls back to its issue month, so a 2026 certificate to the 2018 edition counts as the 2026-03 edition.
   - Affects every German document issued after 2026-03 that does not print a YYYY-MM. The new ones carry the edition beside
     the print. One on main (Deye SG06LP1) joins nothing.
   - Test: a document with `standards: ["VDE-AR-N 4105/11.18"]` and `issued: 2026-07-01` × DE gives O, not D.
2. **A transition end in the profile.** `edition.transition_until: 2027-03-01` would let the page say "accepted until 1 March
   2027" on every O row, and turn O into "documented for a withdrawn edition" after that date. Germany is the first profile with
   a dated end, and every one of its 1 819 documented models has one.
3. **ZEREZ as Germany's list**, once Madis has the account and FGW's reuse permission (`docs/zerez.md`, the letter draft on the
   homelab branch). A unit registered and valid in ZEREZ would be Germany's "on the list". The `list_checks` items would be the 4105
   items the unit certificate proves. A pull at 250 requests/hour is enough. It would touch every DE model.
4. **Certificate kind.** A unit certificate and an NA-protection certificate prove different rows (NA settings and islanding
   come from the NA certificate). Today both are "a certificate citing VDE-AR-N 4105". A `cert_scope: [unit, na, pave]` field
   on the document would let `unit-certificate` require both. Of the 159 new documents, 24 are NA-protection certificates and
   68 are titled unit certificates; the other titles do not say which.
5. **Ratings from the certificate.** The E.4 / "Netzanschlusswerte" table prints rated active and apparent power and the phases
   per model. Reading it as a spec source of its own (lower than the datasheet) would close kW and phases for most documented
   German models. This pass read the table for Fronius, Kostal and RCT Power but kept the values out of the data, because
   no field takes them yet.
6. **robots.txt, read as RFC 9309 reads it.** `tools/evidence/fetch.py` uses Python's `urllib.robotparser`, which takes the first
   matching line. On en.growatt.com (`Allow: /`, then `Disallow: /upload/`) it says yes where the longest-match rule says no. The
   file behind `en50549-moda-2026` (main) came through that gap. Use a longest-match parser, and check that one file by hand.

## Notes on how the documents were fetched

- **Solis.** `www.solisinverters.com` disallows `/uploads/file/*` and `*.pdf`. Every Solis URL here is the same file on
  `cmsdata.solisinverters.com`, the maker's own CDN host, whose robots.txt allows everything. The file was found through the
  download centre's JSON (`/api/Form/getForm/…`, not disallowed). This is the maker's own file on a host that allows it, which
  fits D130's frame (robots.txt is per host). Madis may still prefer to rule on it.
- **Anker and Zendure** files are on `cdn.shopify.com`, linked from the makers' own product and download pages, so they count as
  the makers' own.
- **Deye.** Two requests went to `hqcdn.hqsmartcloud.com` (Deye's download mirror) before its robots.txt was read, and that file
  disallows everything. Both answered "Document not found", and nothing from that host is used.
- **Scans** (six Fronius GEN24, six Zendure) were read from page images rendered locally, not with pdftotext.
- **Left out on purpose:** SMA's 2011 self-declaration and its VDE-AR-N 4110 certificate, Fox ESS's R75–R110 4110 certificate,
  SAJ C6 (4110), Deye's NA certificate for an external relay box (SUN-M60/80/100G3), Sofar 75–136KTL-HV (expired 2024-07-27), and
  certificates for -PRO variants the register does not have. Fox ESS H3-E / AC3-E's TÜV NORD Hangzhou certificate is in, with a
  note that it names no German accreditation.

## Other countries

The brand files are shared, so this branch also moves other countries' views. Each country was measured on main (ca43083)
and on this branch with the same command, model by model. There are 13 040 (brand, model) pairs in each run, no class
changes, and no model went down a level without a stated line:

| country | status changes | why |
|---|---|---|
| AT, BE, EE, NL, SE | 9, 4, 7, 5, 6 · possibly fit → likely fit | Victron: that country's own documents join again (bug 1) |
| PL | 37 possibly fit and 1 nothing known → likely fit | Victron, the same |
| CZ, ES | 1 · possibly fit → over the type-A limit | SMA Sunny Tripower CORE2 STP 110-60: the sheet's 110 kW is over the 100 kW type-A line |
| IT | 8 · possibly fit → over the type-A limit | the "Sunny Tripower STP …" spellings of STP 12–25-50, 15000–25000TL-30 and CORE2 now carry the sheet's kW, which is over Italy's 11.08 kW line. The short spellings were already there |

"Not shown" rows without a reason fall in every country that has no `on_application` yet, because more models now have a
document or a sheet. For example, AT goes from 200 291 to 199 963.
