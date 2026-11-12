# Coverage of the Spanish view

Written 2026-11-12 by the method in [`docs/coverage.md`](../coverage.md) (Estonia first). Spain has **no list**: the grid
operator takes the maker's Spanish equipment certificate (RD 647/2020, Orden TED/749/2020, NTS 2.1; UNE 217002 for the
inverter) at the operational notification. So for Spain "at some level" means: the maker's Spanish certificate where one
exists, otherwise what other EU lists say, and on every check row a reason when nothing shows it.

## The command and the base

```bash
cd web && npm run build
node tools/coverage/country.mjs --cc es --json es.json --brands 30
```

Before: `origin/main` at ca43083 (Estonia #9 merged; dataset 2026-11-09). After: branch `riik-es` (52b81a3 profile,
c5e378f certificates, 519d272 Victron fix). Both runs on the same register: 13 048 models in the ES view.

## Before and after

| layer | before (ca43083) | after (`riik-es`) |
|---|---|---|
| a · likely fit (maker's document) | 821 | **1 886** |
| a · possibly fit (other EU lists) | 10 169 | 9 162 |
| a · over the type-A limit (100 kW) | 1 035 | 1 007 |
| a · nothing known | 455 | 425 — every one legacy tier A (refused or expired on another list only); the page says so |
| a · nothing to approve (wallboxes) | 568 | 568 |
| b · "not shown" rows without a reason | 199 355 | **0** |
| b · rows met by a maker's Spanish document (`D`) | 1 807 | 17 493 |
| b · rows documented for an older edition (`O`) | 380 | 3 236 |
| b · models with every row answered by a paper | 146 | 1 359 |
| c · kW and phases | 7 095 | 7 095 (no datasheet work in this round, see below) |
| d · strongest source a maker's document | 821 | 1 886 |
| e · legacy A / B / current | 535 / 190 / 12 323 | unchanged |

The "older edition" count is honest, not a gap: of the 1 359 documented models, 1 307 hold certificates issued before
Orden TED/82/2026 (in force 12 May 2026), so fault ride-through, storage and the non-peninsular rule are "documented for
an older edition" on them. No NTS edition with type A fault ride-through tests exists yet (below).

## Status re-read, model by model

Of 13 040 models in both runs (the eight duplicate brand + model keys in the index are counted once), **1 065 changed
status, all to "likely fit (maker's document)"**; 0 changed class, 0 changed specs. Every change has a document behind it:

| from → to | models | reason |
|---|---|---|
| possibly fit → likely fit | 1 007 | a Spanish certificate on the maker's own site now names the model |
| nothing known → likely fit | 30 | legacy tier A elsewhere (refused / expired), but a Spanish certificate names it: Kstar KSG-25…40KT-M0…M5 (28, the NTS certificate lists all 28 suffixes), SMA Sunny Island 4.4M-13, Solplanet ASW13K-LT-G2 Pro |
| over the type-A limit → likely fit | 28 | 100–250 kW units with a Spanish certificate (Deye G03 100/110K, Fox R100/R110, GoodWe GT 100–125K and HT 225/250K, Kstar KAC100–125, SAJ C6 100–125K, SMA STP 125-70, Sofar 110/125KTLX-G4, Solplanet ASW100/110K-LT). The ladder puts the maker's document before the type-A limit (`web/src/lib/grid-filter.js` `ladder`); their `power-class` row still says "over 100 kW: type B, a procedure of its own". See engine wish 2 |

By brand (models that became "likely fit"): SAJ 244, Sofar 139, Deye 128, Kstar 96, Enphase 86, SMA 86, GoodWe 62,
Solplanet 60, Afore 53, Fox ESS 48, Kostal 18, INVT 18, SolaX 15, Victron 12. SolaX, Kostal and ZCS Azzurro also moved
models that were already "likely fit" by a document Spain does not take (a safety-code table, a released-countries table)
onto an accepted certificate, so their rows now answer.

Other countries: the check engine's per-country stats are unchanged except through the Victron fix (below).

## What changed, and why

- **Every row answers** (`data/profiles/es.yaml` `on_application`): a row neither a datasheet nor a Spanish certificate
  GridFit holds shows now says that in Spain there is no list, the installer proves it at the operational notification
  with the maker's equipment certificate (RD 647/2020, TED/749/2020, NTS), and the grid operator decides; storage is
  exempt from presenting it (TED/749 additional provision 1). No new row state, no new kind of row: `on_application` is
  the Estonian mechanism (docs/checks.md), so no new UI measurement under DESIGN.md §10.
- **The profile's documents are still the current editions** (re-read 2026-11-12): RD 647/2020 and TED/749/2020
  consolidated texts last changed 12.02.2026 (TED/82/2026, in force 12.05.2026 — its end of the self-consumption
  exemption is confirmed in RD 647's transitional provision 3); RD 1699/2011 last changed 2022-10-19; RD 244/2019 last
  changed 2026-03-21 (RDL 7/2026, already in the profile); the NTS is still SEPE 2.1 (2021-07-09) with its 2021-10-08
  errata — REE's grid-code page lists only a June 2025 annex on inertia emulation and oscillation damping since, not a type A
  matter; e-distribución's guide is still v12 (v13 is 404). The draft royal decree on self-consumption and distributed
  storage is not adopted. The profile's "changes" lines say so.
- **139 Spanish certificates from 15 makers' own sites** (the commit message of c5e378f says 131; the count is 139), all
  `kind: certificate`, ids starting `es-`, appended only, every `match` checked against the register's codes:
  SAJ 12, GoodWe 14, Sofar 13, Kostal 13, Deye 12, Fox ESS 12, SMA 12, Kstar 11, SolaX 10, Solplanet 8, Victron 7,
  Afore 6, Enphase 4 (new file), INVT 4 (new file; the maker serves these as .rar archives), ZCS Azzurro 1.
  Left out on purpose: zero-export certificates (UNE 217001), parameter guides, companion certificates that add no model
  (an RD 647 beside the NTS one for the same family), superseded issues, NTS SENP-only certificates (non-peninsular;
  the mainland NTS covers the same models), an expired ZCS 50–70 kW certificate (2024-04-26), and SAJ's H2-S2 TÜV NORD
  certificate, which says the unit complies "with restrictions" listed in an annex the posted file does not carry.
- **Victron's documents never joined, anywhere** (519d272, a fix with a test): `data/evidence/victron.yaml` carried
  `brand: Victron Energy`, the register's brand is `Victron`, and every loader joins evidence by `brand:` lowercased. The
  brand line now says `Victron` (the same in `tools/evidence/sources.yaml`, where `build.py` would take it for a new file);
  `web/test/checks.mjs` now checks that every `data/evidence/*.yaml` brand is a register brand, and that the Spanish NTS
  certificate joins MultiPlus-II 48/8000/110-100/100. Effect outside Spain: Victron models with a document in AT, BE, DE,
  EE, NL, PL, SE move to "likely fit" (NL 527 → 536 and EE 527 → 536 documented models in the engine's stats). The
  country page's document list says "Victron" instead of "Victron Energy".

## What is left in Spain, and why

- **"Possibly fit" (9 162)**: accepted on other EU lists, no Spanish certificate read. The largest gaps by brand are the
  ones whose Spanish certificates a script may not fetch (the list below) — Growatt 362, Solis 254, Huawei 124, SolarEdge
  110, Fronius 204 — and those without one on the maker's site: SAJ's EK70/EK90 HS5 kits (~300; the brief expected them,
  the site has none), Sigenergy 290 (403 to scripts), Hoymiles 240 (login), Sungrow 100 (JavaScript download centre;
  only reseller copies found), KACO 105, Pylontech 121 (batteries, no grid certificate), Anker SOLIX, TSUN, Hypontech.
  Ingeteam (44, the Spanish maker) links only datasheets and a zero-export guide on its product pages; its NTS
  certificates appear only on distributor sites. Power Electronics (88) publishes none.
- **527 models are "likely fit" by a document Spain does not take** (SolaX 369 and ZCS Azzurro 91 by the makers'
  safety-code tables, Sungrow 52 by its country overview, Kostal 7, GoodWe 8): the cell says likely fit, the rows say
  "not shown" with the Spanish reason. See engine wish 3.
- **kW and phases (7 095 of 13 048)** are not changed in this round: the datasheet layer is shared by every country, and
  eight country sessions harvesting the same brands' sheets at once would collide in `data/specs/<brand>.yaml`. The largest
  ES gaps: Sigenergy (34 %), Autarco (5 %), Anker SOLIX (25 %), Hypontech (20 %), TSUN (32 %), INVT (33 %) — one spec
  session after the country PRs is the right place.
- **Fox ESS `une217002-h3-pro-ac3-pro-2025`** (250061RECO11-A, already in the data) also lists the P3-PRO aliases; its
  regex leaves them out. Widening an existing entry is outside this session's append-only rule.
- **"Nothing known" (425)**: legacy tier A, hidden by default, the reason on the page.

## Documents only a browser gets (for Madis)

| maker | what | where | why a script stopped |
|---|---|---|---|
| Growatt | 3 RD 647, 7 UNE 217002, 9 NTS type A certificates (MOD, MID, MIN, MIC, NEO, SPE, MAX) | `https://en.growatt.com/upload/file/` — e.g. `MIN_2500-6000TL-X_NTS_TypeA.pdf`, `MOD_3-15KTL3-X_RD_647.pdf`; listed by `https://en.growatt.com/support/download/certificate?keyword=NTS` | robots.txt `Disallow: /upload/` |
| Solis | 11 NTS / RD 647 certificates (S6-EH3P 5–20K, S5-GR3P, S5/S6-GR1P, mini, S5-GC 25–110K, EHV 215–255K, RHI / S5-EH1P) | `https://www.solisinverters.com/uploads/file/Solis_certificate_NTS_631…_Spain_V01….pdf`; page `https://www.solisinverters.com/es/certificates42.html` | robots.txt disallows `/uploads/file/*` and `/*.pdf`; the same files on ginlong.com were not used |
| Fronius | NTS: Primo 3.0-1–8.2-1, Symo 3.0-3-M–8.2-3-M, Symo GEN24 3–5, Eco (SEPE and SENP), Tauro; UNE 217002: Symo GEN24 Plus 3–5, Tauro/Eco; RD 647 / TED 749 declaration for the SnapINverters | `https://www.fronius.com/~/downloads/Solar%20Energy/Certificates/SE_CER_NTS_631_…_ES.pdf`; index `https://www.fronius.com/es-es/spain/energia-solar/instaladores-y-socios/servicio-y-soporte/tech-support/certificates-datasheets` | WAF |
| SolarEdge | Home Hub three-phase (U23-0334, NTS + UNE 217002), commercial three-phase incl. Synergy (2623/0095-CER), its UNE certificate, PCS050 NTS and UNE 217002; single-phase Home Wave and SE5–10K-RWS by search | `https://knowledge-center.solaredge.com/sites/kc/files/se-solaredge-home-hub-inverter-three-phase-grid-certificate-sp.pdf` and siblings | Cloudflare 403 |
| Huawei | SUN2000 NTS / RD 647 / UNE 217002 certificates, if any | `https://solar.huawei.com/-/media/Solar/attachment/pdf/es/certificate/residential/`; one lead `https://solar.huawei.com/admin/asset/v1/pro/view/1088897b22334639836579fe3f4b2545.pdf` | terms forbid automated access |
| APsystems | Spanish certificates for DS3, DS3D, EZ1, EZ1D, EZHI, QT2, QT2D, QS1, QS2, YC600, YC1000, APstorage | linked from `https://emea.apsystems.com/document-library` to `apsystems.filecloudonline.com/url/…` | robots.txt `Disallow: /` |
| Hoymiles | Spanish certificates | `https://www.hoymiles.com/downloads.html` | certificates need a login |
| SolaX | X3-IES, X1-IES, X3-Ultra, X3-MIC G2, X1-SMART | `https://www.solaxpower.com/downloads.html` | its API is robots-disallowed |
| SMA | NTS for STP 50-80 / 60-80 (a scan, no text layer); STP-3SE-40, SBSE, Tripower X hybrid, SHP Peak3, CORE2, Sunny Boy Storage not found | `https://files.sma.de/downloads/ZE_STPxx-80_TED749-NTS_es_11.pdf`; sma.de download centre | scan; the centre's search is robots-disallowed |
| SAJ | R6 5–10K S2/S3 NTS and RD certificates, H2-T2 5–10K UNE + RD, R5 0.7–3K (scans); H2-S2 TÜV NORD annex | `https://www.saj-electric.com/hubfs/South%20East%20Europe%20document/Certification/Spain%20certification/` | scans without text; the annex is not posted |
| i-DE (Iberdrola) | commissioning guide for generation modules (what the FON asks for) | `https://www.i-de.es/documents/d/guest/guia-puesta-en-servicio-para-mge-conectados-a-la-red` | 503 to scripts |

## Mootori soovid (engine wishes)

1. **Cite keys as words, not substrings** (`tools/check/run.py` `cites`). It lowercases and tests `key in text`, so
   Spain's `NTS` also hits "requirem**ents**". Today it changes nothing (a document applies only where a family names the
   country; the one loose hit is a Polish PTPiREE document for PL), but the next generic key will. Test: a document whose
   standards say "requirements for type A" and whose family names ES must not be `national-declaration`.
2. **Document and type B together** (`web/src/lib/grid-filter.js` `ladder`). A 100–250 kW unit with a Spanish certificate
   shows "likely fit" in the cell; the check row says type B. 28 models in Spain. Wish: the cell says both ("maker's
   document · over the type-A limit") or the B wins when the certificate is type A only. Test: GoodWe GW125K-GT × ES.
3. **"Likely fit" only for a kind the country takes.** 527 Spanish models are "likely fit" from a safety-code table or a
   released-countries table, while Spain's `accepts` is `national-declaration` only. Wish: the cell takes the profile's
   `accepts` into account (or a weaker word for a document of another kind). Test: SolaX X1-Micro 800 × ES (covered only by the
   safety-code table).
4. **Evidence keyed by the curated brand aliases** (`web/src/lib/evidence.ts`, `tools/check/run.py`,
   `tools/evidence/coverage.py`): `data/curated/brands.yaml` already maps `Victron Energy: [victron, victron energy]`;
   the loaders should use it so a display-name key cannot silently join nothing again. The test added in 519d272 guards it
   meanwhile.
