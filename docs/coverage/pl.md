# Coverage of the Polish view

Written 2026-11-12 by the method in `docs/coverage.md` (Estonia first). Command:
`cd web && npm run build && node tools/coverage/country.mjs --cc pl --json out.json --brands 40`.

Base: `origin/main` ca43083 (EE #9 merged; dataset of the committed snapshot 2026-11-01, whose PL rows are the
2026-10-26 list read by the old layout-mode parser). Three measurements:

- **before** — ca43083 as it is;
- **after** — this branch on the same committed snapshot: what the PR changes the day it is merged;
- **refresh preview** — this branch with a local, uncommitted snapshot whose PL rows are the 2026-11-06 list read by the
  new parser: what the next `refresh` run will add. Snapshots are not committed here (one refresh after all countries).

| layer | before | after | refresh preview |
|---|---|---|---|
| models in the PL view | 13 048 | 13 048 | 13 331 (+283: rows the old parser lost or misread, and the new file) |
| a · on PTPiREE's list | 1 522 | 1 522 | 1 902 |
| a · likely fit (maker's document) | 653 | 653 | 653 |
| a · possibly fit (other EU lists) | 9 943 | 9 943 | 9 850 |
| a · over the type-A limit | 442 | 442 | 438 |
| a · nothing known | 488 | 488 — every one legacy tier A (refused or expired on another list only); the page says so | 488 |
| b · "not shown" rows without a reason | 177 863 (12 435 models) | **0** | **0** |
| b · rows checked by PTPiREE's list | — | 15 022 | 18 759 |
| c · kW and phases, all models | 7 095 | 7 112 | 7 134 |
| c · kW and phases, models on the list | 642 / 1 522 | 659 / 1 522 | 764 / 1 902 |
| c · MPPT, PV models on the list | 208 / 1 070 | 225 / 1 070 | 251 / 1 191 |
| d · a datasheet or a maker's document, models on the list | 307 | 324 | 350 |
| e · legacy A / B / current | 535 / 190 / 12 323 | same | same |

## Status re-read, model by model

**before → after**: of the 13 040 (brand, model) keys in both runs, **0 changed status and 0 changed class**. The
profile and the Lux Power sheet change rows (b) and specs (c) only.

**after → refresh preview** (the parser fix and the new file; 12 937 keys in both, 103 only before, 386 only after).
Every change has a reason:

| change | models | why |
|---|---|---|
| possibly fit → on the list | 32 | rows the old parser misread on the 2026-10-26 file: EcoFlow `EF-EA-…-600 A` (the PPM scope "A" glued to the model), Sinexcel Isuna `… A`, Enjoy EPCS (model read as "A, B, C, D"), Bytewatt BW-INV-TPH (maker read as its street address), Kstar KAC (maker read as "… 2025 …"), Cubenergy, Sigenergy SigenMate (30 rows read as one model "A") |
| possibly fit → on the list | 63 | new on the 2026-11-06 file: Sigenergy Hybrid / PV Max / SigenStor AC / SigenMicro, Growatt MAX …KTL3-X LV, APsystems EZ2 / QS2 / ELT, Pixii, Voltdeer |
| over the type-A limit → on the list | 4 | Kehua BCS1000K, Megarevo MEGA0500 / 0500TS / 0630 (old parser bleed); the grid cell puts the country's own list before the type-A line, as in Estonia |
| class changes (inverter ↔ hybrid ↔ battery) | 10 | the "type of device" cell is now read whole: Sinexcel Isuna D…K-TL "Falownik hybrydowy", Sineng EH-…-UD, Elecod Monet-125AC-H4, Zendure ZDA2502 |
| only before / only after, same device | 101 / 101 | the display spelling of the model: the old parser left a space inside wrapped codes (`SUN-25K-SG02HP3-EU- AM3`, `SH100CX + Logger1000A- EU`, `INPPCS-74/0.4-W-14-A2- OS`); same normalised key |
| only after, new | 285 | ENEL-PC EW (187 rows on pages 17–34 read with the street address as the maker), the rest of the misread rows above, and the file's new rows |
| only before, gone | 2 | Clou (`CO.,LTD.` became `CO., LTD.` in the new file) |

## What changed, and why

- **The list is read right** (`tools/registers/parse.py` `read_pl`; first commit; the error that made PL data wrong).
  PTPiREE's file is an Excel sheet printed with every cell ruled, but the parser read it in pypdf layout mode by character
  columns. On the 2026-10-26 file 307 of 2 491 rows had a column bled into another and 30 Lp numbers were unread. Now
  pdfplumber reads the ruled cells: 2 491 / 2 491 and 2 681 / 2 681 rows, bleed 0. `tools/registers/test_pl.py` runs the
  parser on a downloaded file and fails on an unread Lp or a bleed; `parse.py` writes both into `errors.txt` on every refresh.
- **Every row answers** (`data/profiles/pl.yaml`). `list_checks`: a model on the WiPWC 1.3 list is "checked by
  PTPiREE's list" on ten items — certificate, frequency range, LFSM-O, under-frequency, protection settings,
  reconnection, P(U), reactive power, anti-islanding, storage. WiPWC 1.3 §6 makes a certificate mandatory for a type-A
  PPM on LFSM-O, the frequency range and RoCoF (items 6.1, 6.14, 6.15), and §3 makes it confirm the Bank Nastaw
  settings set (protection, under-frequency, Q(U), P(U), reconnection). Left with the OSD: RoCoF (360 rows are WOS 2018
  certificates, 2.0 Hz/s), the remote stop (6.16, optional), the voltage band and RS-485 / SunSpec (micro-installation
  regulation and IRiESD — the list page says the OSD checks them even for a listed device). `not_carried` and
  `on_application` word the rest.
- **The profile is current**: the list page serves the 1.3 list of 2026-11-06 (2 681 rows; 2 321 WOS 2025, 360 WOS 2018,
  355 of them accepted until 2026-12-31 and 5 ElectraTherm rows until 2026-07-26 — past, class other); the 1.2 list is
  still the 2026-10-26 file. WiPWC 1.3 and Bank Nastaw 1.1 (files of 2024-10-01), the notice of 2026-10-05, PSE's WOS
  2025 page and Dz.U. 2023 poz. 1098 (ELI register: in force, no amending act) are unchanged.
- **The date column reads "accepted until"** (`gridfit/registers.py`, PL `date_label`), as PTPiREE's notice says.
- **Datasheets**: Lux Power (new, `data/specs/luxpower.yaml`, 17 rows from the maker's EU catalogue 2026.04.10) — 17 of
  its 19 models on the PL list.

## What is left in Poland, and why

- **kW and phases on 863 listed models** (refresh preview: 1 138 of 1 902). By brand on the list:
  - Power Electronics España HEMK FS…K (88), Sinexcel PWS1-…KTL (≈75), Ingeteam INGECON SUN …TL (44), Kehua, Hopewind,
    4en, Golen, Weiheng: MW-class PCS and central inverters, mostly type B–D; their codes carry the kVA (`FS1910K`,
    `PWS1-1725KTL`, `3825TL`). The model-code level (PR #11) is the route — rules proposed below.
  - Must PH11 / EU118 (46): no datasheet is served — the maker's product pages give a "Rated Power" line and leave out
    7KL3, 7.5KL3, 9KL3 and 11.2KL3; the sheets come by quote request (owner's list).
  - Sunsynk SM…kW / LIFE…HYB (40), Poweroad PRP (28), SRNE HESP (20), Felicity IVGM …LP3 (19), Sunplus (16),
    Chisage (14): not attempted in this session; the codes carry kW and phases for Felicity (`LP3`/`HP3` three-phase,
    `LP1` single) and SRNE (`…H3`).
  - Sigenergy (53 on the 2026-10-26 file): covered by PR #11's model-code rule (`SP` / `TP`); the download centre
    refuses scripts (Estonia's list).
  - Sungrow 42, GoodWe 35, SAJ 45 (CH3 / AS2), Deye 23, Sofar 21: older or commercial lines whose sheets are not in
    `cache/specs/`; shared brands, left for one harvest run rather than nine.
- **"Possibly fit" (9 850)**: accepted on other EU lists, nothing read in Poland. Fronius (236), SMA (136 of 184),
  Growatt (≈365), Victron (58) are in it although the **WiPWC 1.2 list** (not read) still names many of them until
  31 December 2026 — see the decision below.
- **"Nothing known" (488)**: legacy tier A, hidden by default, the reason on the page.

## Decision for the owner: the WiPWC 1.2 list

The 1.2 file (851 pages, 8 531 rows, 2026-10-26) counts for connections until 31 December 2026 (WiPWC 1.3 §10;
PTPiREE's notice of 2026-10-05); after it, for no new type-A connection. Reading it would move Fronius, most of SMA,
Growatt and Victron from "possibly fit" to a time-limited listing for seven weeks, then they fall back. The pdfplumber
reader would take it (~10 min per run). Not done here: it needs a second PL file in `gridfit/registers.py`, a
`limited` status with `valid: 2026-12-31`, and a removal on 2027-01-01.

## Engine wishes (for one engine session; nothing here changed them)

1. **R by the row's WOS edition** (`tools/check/run.py` `check_model`). The engine marks a listed model R on every
   `list_checks.items` entry; PL's rows each name their WOS edition (`extra.wos`, "WOS 2018" / "WOS 2025"). With a
   per-item `needs_edition` (or `list_checks.items_by: {rocof: "WOS 2025", remote-stop: "WOS 2025"}`) a WOS 2025 row
   could prove RoCoF as R and a WOS 2018-only model show O. On the 2026-11-06 file: 1 630 listed models have a WOS 2025
   row, 245 only WOS 2018 rows.
   Test: a model with a WOS 2025 row → `rocof` R; one with only WOS 2018 rows → `rocof` not R.
2. **PL acceptance date as status** (`tools/registers/parse.py` + `gridfit/registers.py` `devices`). Every PL row has an
   "accepted until" date; 360 rows end on 2026-12-31. Writing PL rows as `limited` with `valid` = that date would make
   them turn `limited-past` on 2027-01-01 by themselves. It changes the word on ≈ 1 900 models ("time-limited"), so it
   is a UI decision. Test: a row with a past date → `limited-past`, not POSITIVE in `run.py`.
3. **Aliases** (`data/registers/alias.json`, not touched — `data/registers/**` stays with the refresh): "Huizhou
   Sinexcel Electric Co., Ltd." → Sinexcel (6 models); "SHEN ZHEN CLOU ELECTRONICS CO., LTD." and "…CO.,LTD." → one
   brand (Clou); "Power Electronics Espańa, S.L." (the list's own typo) → Power Electronics; "ENEL-PC Spółka z o.o." →
   "ENEL-PC" (the cleaner turns Spółka into "Ka"). Test: `parse.py` on the 2026-11-06 file gives one brand each.
4. **Model-code rules for the PL list's PCS brands** (for `data/specs/naming/codes.yaml` after PR #11, each proven by
   its agreement rule there): Power Electronics `^HEMKFS(?P<kva>\d{4})K` (three-phase), Sinexcel `^PWS1-(?P<kw>\d+)KTL`
   (three-phase), Ingeteam `^INGECONSUN(?:STORAGE)?(?P<kw>\d+)TL` (three-phase), Must `^PH11-(?P<kw>[\d.]+)KL(?P<ph>1|3)`,
   Felicity `^IVGM(?P<kw>\d+)K(?P<frac>\d)?[LH]P(?P<ph>1|3)`, Luxpower `TRIP2?-[LH]B-3P(?P<kw>\d+)K` (three-phase).

## Documents only the owner can get

- **Must** PH11-…KL3-EU / PH11-…KL1-EU-G2 / EU118 datasheets: not served for download; `mustpower.com` product pages
  carry a "Request A Quote" button only.
  https://www.mustpower.com/product/ph1100-eu-series-516kw/ · https://www.mustpower.com/product/ph1100-eu-g2-series-310kw/
- **Lux Power** GEN3-LB-EU 6.5K and 7K: on the PL list (Lp of 2026-11-06), on no sheet of the maker's site or catalogue.
- (From Estonia, still open) Sigenergy datasheets and Intertek certificates — the download centre refuses scripts.
