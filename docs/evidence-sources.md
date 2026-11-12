# Where the makers say which countries a product is for — the map of evidence sources

Read 2026-11-01. The question behind it: a model that is not on a country's list (Estonia: 11 678 of the models GridFit
knows) — does its maker publish a document a grid operator would take? For Estonia that is what Elektrilevi asks for a
model off its list: an RfG / EN 50549-1 certificate plus the Estonian settings (`data/profiles/ee.yaml`). Three kinds of
document answer it, from the strongest:

| kind (`kind:` in `data/evidence/`) | what it says | what GridFit makes of it |
|---|---|---|
| `country-release` | the maker releases the family for the country (Kostal's X table, Sungrow's overview) | the country, by the maker's name for it |
| `grid-code-setting` | the firmware has a setting for the country's grid code (a manual's safety-code table) | the country; `confidence: general` when the table is for the maker's whole range, not per model |
| `certificate` | a test lab certifies a standard for listed models (EN 50549-1, CEI 0-21, NTS, VDE-AR-N 4105) | a national standard names its country; EN 50549-1 names none, so the country comes from `data/evidence/rules/accepts.yaml` as `accepted_in` (Estonia only, from Elektrilevi's own words) |

How it runs: `tools/evidence/sources.yaml` lists every file below that a script can fetch; `fetch.py` downloads them to
`cache/evidence/<brand>/` (robots.txt, 2 s apart, a manifest with sha256 and the seen date), `parse.py` reads them
(`python -I`), `build.py` writes `data/evidence/<brand>.yaml` and keeps every hand-written document, `coverage.py` counts.

## Brand by brand

EE gap = models of the brand not on Elektrilevi's list (inverters, hybrids, batteries, plug-in units). ✓ = in
`sources.yaml`; ✎ = transcribed by hand earlier (2026-10-31, Spain/Italy/Germany certificates); ✗ = found, not usable by
script; — = nothing found.

| brand | EE gap | country / grid-code table | EN 50549-1 certificates | where, and why not more |
|---|---:|---|---|---|
| SAJ | 705 | — (the download centre's search for "Estonia" finds nothing; manuals point to the app) | ✓ H3-LS2 (DEKRA, 2026), CHS2 (TÜV Rheinland, 2025) | `saj-electric.com/services-support-download?search_value=…` is server-rendered and searchable. The 308 EK70/EK90 HS5 kits and HS2/HS3/AS2 hybrids have no EN 50549-1 certificate in the centre — Spain (NTS/RD 647) and Italy (CEI 0-16) only |
| SolaX | 461 | ✓ "Actual Safety Code Display" (75 codes, EN50549_Estonia; not per model) | X1/X3-Hybrid G4 (TÜV) exist, not added — the code table already covers them | `solaxpower.com/uploads/file/…` static; the downloads page is JavaScript |
| Fox ESS | 433 | — (KH, H3-Smart manuals: "set by default", no table) | ✗ several are scans without text (A3-50591574-0001-extsigned) | `fox-ess.com/download/certificates`, 266 entries, server-rendered; titles carry report numbers, not standards — worth one more pass |
| Solis | 259 | ✗ older manuals' appendix 11.1 "Grid standard selection guide" (files over 10 MB, Estonia not verified); a reseller-hosted declaration says countries without a code use "EN50549L" | ✓ S6-EH3P3–10K-H-EU (Bureau Veritas, 2022); S6-GR1P, S6-EH1P-L-PLUS, 5G-PRO exist under `solisinverters.com/uploads/file/` | no public listing page (`/download` is 404) |
| Sigenergy | 243 | — | ✗ Intertek EN 50549-1 (SigenStor, Hybrid, PV Max) only on a distributor's server | `sigenergy.com/en/support/download` is a Nuxt app over an API; 403 to scripts |
| GoodWe | 227 | ✓ ET 12–30 kW manual, 10.5 "Safety Standards Countries" (EE = code 60, FI-A…D); the SDT G3, XS G3, DNS, EH, ES-LD manuals have no table | ✎ Spain/Italy/Germany (earlier) | series pages load page 2+ by JavaScript; files via `admin.goodwe.com/En/Api/downloadFile?id=…`. The ET 5–10, EH and BH manuals in the same new style are the next look |
| Growatt | 214 | — (MOD manuals show only examples of the Country/Area menu) | ✓ MODA all-in-one (Intertek, 2026); ~60 more EN 50549 entries | `en.growatt.com/support/download/certificate?keyword=50549` is plain HTML, 6 pages — the largest untapped certificate set |
| Sofar | 200 | ✓ HYD 5–20KTL-3PH manual, country-code table (109-000 Estonia) | — (the centre has an EN 50549 filter, JavaScript) | `sofarsolar.com/download.html` is JavaScript; the KTLX-G3 manuals were not found outside it |
| Afore | 197 | — (the 3-phase hybrid manual's safety menu ends in "……") | ✓ 8 current Intertek certificates: SL/ASL, SL-0, HNS, BNT 3–110, MTH/ATH, TH/THP/THA (5 superseded ones left out) | `aforenergy.com/download/` WordPress, links in the HTML |
| Hoymiles | 185 | — (grid profiles live in the S-Miles cloud, login) | ✎ MIT VDE 4105 (earlier) | download centre is JavaScript |
| Fronius | 169 | ✗ "Conformity with requirements from Estonia" (2017; Galvo/Primo/Symo/Eco with setup "PT", from search snippets) | — | old `/~/downloads/…` paths are 404, `downloads.fronius.com` resets scripted TLS (WAF); manual only, in a browser |
| SMA | 152 | — (the country data set manuals say the generic EN 50549 set is for countries without their own) | ✗ "EN50549-HK-en-16" is SMA's own declaration (2022), not a lab certificate — left out | `files.sma.de/downloads/…` static; product download lists are JavaScript |
| Sinexcel | 136 | ✗ PWS2 manual: the country list is a screenshot | ✓ PWS2-29P/30P-EX (TÜV SÜD) | `en.sinexcel.com/uploads/soft/…` static; no certificate listing |
| Kstar | 132 | E(4–12)KT-D22 manual table 7-1: 27 codes, no EE (generic "50549") — not added: it names no Estonian setting | ✓ BluE-G, BluE-S, KAC50DP, E8–12KT, KAC20–125DP2 (TÜV SÜD); 4 more are scans without text | `kstarnewenergy.com/support.html` server-rendered |
| Deye | 130 | — (SG04LP3 manual's grid modes: no EE) | ✓ SUN-18–36K-G04 (Bureau Veritas); ✎ ES/IT/DE (earlier) | `deyeinverter.com/download/Declaration_of_Conformity/` plain HTML, 988 entries: PL, ES, IT, FR, NL, IE, NO certificates |
| Enphase | 129 | — (profiles chosen in Enlighten at activation) | — | documentation centre is JavaScript; IQ8 ships to Estonia (press release, Aug 2024) — not a document of the kind |
| INVT | 127 | — | XG3–15KTR (TÜV SÜD) and PL/IT certificates exist under `/userfiles/files/download/Certificates/` | not added this round |
| KACO | 123 | — | ✗ only third-party mirrors | JavaScript centre |
| Pylontech | 121 | — (batteries; the compatibility list is per inverter, not per country) | — | |
| ZCS Azzurro | 118 | ✓ "Safety Standard Table" 2024-08-13 (109-000 Estonia; brand-wide) | per-family EN 50549 attestations on the documentation page | `zcsazzurro.com/documentation`, static, 344 PDFs |
| Sungrow | 106 | ✎ "Product Certification and Country Code Overview (Europe)" v3.5 (still the newest; EE = "EN50549-1 Manual settings / Elektrilevi") | — | the per-hardware-version availability glyph is an image |
| Anker SOLIX | 105 | — | ✗ third-party copies only | JavaScript product pages |
| TSUN | 102 | — | ✓ TSOL-MS1600/2000, MS600–800 (Bureau Veritas) | `tsun-ess.com/downloads.html` static |
| Victron | 91 | — (grid codes only in VEConfigure) | ✓ MultiPlus-II 48/8000–15000 (SGS, 2026) | product pages list certificates in static HTML |
| Hypontech | 83 | — | ✗ only third-party copies; hypontech.com's TLS certificate is for another host (not bypassed) | |
| SolarEdge | 83 | ✗ "Countries supported by SolarEdge inverters" v1.1 (Aug 2024; Estonia listed per snippets, the 2018 edition maps Estonia to the "Portugal" setting) | — | Cloudflare 403 to scripts; manual only, in a browser |
| Kostal | 81 | ✓ "Released countries" 10/2026 (DOC01962673-041); the shortlink /released_countries points to a stale 2025 copy | ✎ IT (earlier) | static PDF |
| EcoFlow | 77 | — (grid norm chosen in the app) | ✗ one EN 50549-10 certificate on the UK portal | Next.js documentation portal |
| Sunsynk | 76 | — | ✗ resellers only | everything behind a login |
| Sunways | 75 | — | — | `sunways-tech.com/downloads/` (not sunwaypv.com, another company) has no certificates |
| Autarco | 74 | — | — | the company is bankrupt; every download is 404 |
| AEG | 73 | — (the menu has a "50Hz Grid Default") | ✓ AS-ICH02, AS-IC02-2, AS-IR02-2, AS-IR02 | `aeg-solar.com/service/downloads/` static |
| Solplanet | 50 | — (the App manual UM0041 is over 10 MB, unread) | ✓ ASW-LT-G2 Pro, ASW kH-T2 (Bureau Veritas) | certificate list loads through admin-ajax |
| Huawei | — | Grid codes appendix of the SUN2000 MAP0 manual (public copy): no Estonia code | — | excluded: the terms forbid automated access |
| WSTECH | 96 | — | — | MW-scale central inverters, downloads behind a login |

Gensets (CAT, MWM, Caterpillar, MTU, INNIO Jenbacher: ~810 EE "models") and EVW are synchronous machines or combined
heat-and-power units: no inverter maker's document will ever cover them.

## What is deliberately not a source

- Third-party copies (resellers, distributors' CDNs): the maker's own URL or nothing, so a reader can check the source.
- A maker's general declaration that "all our inverters comply with EN 50549-1" (Solis via a reseller, SMA's EN50549-HK)
  without a lab: kept in this map, not in the data.
- Zero-export certificates (UNE 217001 / ITC-BT-40) and parameter guides — as before (README).
- Huawei (terms), Reddit, Facebook, enfsolar, zerez, Geizhals (closed or forbidden).

## Next sources, by what they would add for Estonia

1. Growatt's ~60 EN 50549 certificates (plain HTML listing): MIN/MOD/MID/MIC families, ~150 EE models.
2. GoodWe ET 5–10, EH, BH manuals in the 2026 style — if they carry the same "Safety Standards Countries" table, the
   ET/EH/BT/BH hybrids (74 EE models).
3. Fox ESS certificates (266 entries, server-rendered): read the titles' report numbers against the certificates.
4. Fronius and SolarEdge country documents by hand in a browser (WAF / Cloudflare), transcribed with the seen date.
5. SAJ HS2/HS3/AS2 and EK70/EK90 kits: no EN 50549-1 certificate published — ask nothing, wait for the centre.

## Country documents, ten countries (2026-11-01)

69 hand-written documents from the country research of 2026-11-01 (ids start with the country: `at-`, `be-`, `cz-`,
`de-`, `nl-`, `pl-`, `se-`; generic `en50549-*`), 11 brands. Each `standards` string is copied as the document prints it,
so the country's `document_must_cite` key matches (TOR Erzeuger / OVE-Richtlinie R 25, C10/11, PPDS, VDE-AR-N 4105,
WiPWC / WOS, EIFS 2018:2, Netcode / NEN-EN 50549). Where only a wholesaler's copy could be read, `url` is the copy and
`copy_of` says who hosts it. Belgian entries are Synergrid GLV declarations (one per brand, opened) plus the makers' own
C10/11 certificates (Deye U22-0136, Victron 2622/0478); Czech entries say in the family note whether the document is the
accredited SZÚ certificate the operators take (only Deye B-00337-26) or background.

Left out, and why: Huawei in every country (its terms forbid automated access); Fronius P26-0320 (VDE-AR-N 4105:2026-03,
an NA-protection certificate with remote voltage measurement for plants above 30 kVA — not a unit certificate; the
evidence schema cannot show that narrow scope yet); Deye U22-0643 (replaced by U24-0950); Fox ESS A3 50555469 (expired
2025-08-17); Fox ESS's Dutch CE self-declaration (names no country); GoodWe's ET G2 GLV (a scan, model codes
unreadable); GoodWe's SZÚ certificate (only on an aggregator site); Kostal's TOR, NL and CZ files and Fronius Tauro / CZ
files (dead links or block pages on 2026-11-01). SolaX's Czech declaration names X3-FTH-…K-O; the register has no `-O`
suffix, so those rows are not joined. Two families join no register model and keep a note (Deye SG06LP1 for DE, Fronius
Primo GEN24 8.0/10.0 U25-0878).
