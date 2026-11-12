# Register check, 10 countries (2026-11-01)
Is each parsed list complete and current, how many operators publish one, and what its columns mean. One section per
country, written by the country research of 2026-11-01 against `gridfit/registers.py` and the snapshots in
`data/registers/`. Parser suggestions are listed, not applied (they belong to `gridfit/registers.py`). Estonia, Spain and
Italy: see `data/profiles/{ee,es,it}.yaml` (`list`, `changes`); Estonia's list was row-for-row unchanged on 2026-11-01
(2 239 rows, 105 makers); Spain has no de facto list; Italy has only ANIE's members' list (76 rows, 5 makers, 2025-10-29,
all rights reserved) and a storage list n. 8 (2020).

## Austria (AT)
### Verdict

**Our parsed lists are complete and current.** The newest files on wechselrichterliste.at on 2026-11-01 are the ones the
2026-10-31 and 2026-11-01 snapshots hold:

| list | newest file on the site (seen 2026-11-01) | `registers.py` / snapshot | rows in file | rows parsed |
|---|---|---|---|---|
| TOR SEA Typ A (`AT`) | `2026-10-30_Liste_TYP_A_TOR_ERZ.xlsx`, 181 866 B, Last-Modified 2026-10-30 10:59 GMT, sheet `Export` | `at_typ_a__2026-10-30_…xlsx`, source_date 2026-10-30, seen 2026-11-01 | 3 520 | 3 520 (7 unmatched: "model is a pattern") |
| Ladeeinrichtungen (`AT-EV`) | `2026_10_30_Liste_TOR_VNA_Ladeeinrichtungen.xlsx`, sheet `data` | `at_laden__2026_10_30_…xlsx`, source_date 2026-10-30 | 614 | 614 |

`registers.py` finds the file through the page's link pattern, not a guessed URL, so a new date in the file name is
picked up automatically. Earlier files were 2026-10-23 (pass-3 report): the list moves several times a month.

### Who runs it, and how many lists

- **One national list per kind**, not per DSO. Publisher (Impressum): Verein „Österreichs E-Wirtschaft“ (Oesterreichs
  Energie), Vienna. Run by the project group „Qualitätssicherung dezentrale Erzeugungsanlagen“: 13 distribution grid
  operators — Energie Klagenfurt, Energienetze Steiermark, Innsbrucker Kommunalbetriebe, KNG-Kärnten Netz, LINZ NETZ,
  Netz Burgenland, Netz Niederösterreich, Netz Oberösterreich, Salzburg Netz, Stromnetz Graz, TINETZ, Vorarlberger
  Energienetze, Wiener Netze — plus the association VÖEW and Österreichs E-Wirtschaft Service GmbH. The members fund
  independent laboratory tests to OVE R 25 (page „Über“).
  - **Correction for `registers.py`**: "a project group of 14 grid operators" → 13 grid operators + VÖEW (an association
    of smaller utilities). The home page says all **122** Austrian DSOs read the same database.
- **Is every DSO bound?** Yes in effect: E-Control's TOR Stromerzeugungsanlagen Typ A V1.4, 8.1 note 37, says a PV
  inverter listed as admissible has its conformity proof "as given" — and the TOR is part of every grid connection
  contract. The same holds for chargers (TOR VNA NS V1.3.1 8.1 note 39). The list is not the only way in: TOR 8.1 lets
  the operator take an OVE R 25 report instead. Note 37 still links the old URL
  `oesterreichsenergie.at/publikationen/…/wechselrichterliste-tor-erzeuger-typ-a`, which now redirects (307) to
  wechselrichterliste.at; the old English whitelist page on oesterreichsenergie.at is 404.
- Other pages on the same site, not parsed: **TOR SEA Typ B** (no list — type B goes through RKS-AT certification; foreign
  unit certificates such as VDE-AR-N 4110 are recognised), **Umschaltboxen** (backup transfer boxes).

### Columns and status words (TOR SEA Typ A, file 2026-10-30)

Columns: `Marke`, `Type`, `Nennwirkleistung (Maximalleistung) bei cosPhi = 1 [kW]`, `Nennscheinleistung (Maximalleistung) [kVA]`,
`Phasenzahl` (3: 2 605, 1: 911, 2: 4), `Art Betriebsmittel` (Hybrid 1 792, PV 1 240, AC-Batterie 466, Windenergie 17, USV 2,
Frequenzumformer 2, universelle Batterieerweiterung 1), `Zulässig`, `EINSCHRÄNKUNG ab Firmware` (1 613 rows),
`Datum befristet bis` (275 rows), `Deaktivierbare USV-Fähigkeit?` (22 × Ja).

The list's own legend (FAQ on the page, paraphrased):
- **Einschränkung** refers to the firmware column: only from that firmware version on is conformity ensured.
- **Befristung**: documents are still outstanding or minor software faults without direct effect on grid integration
  were found; not a rejection. For users: a plant ordered or built within the period may be commissioned up to 6 months
  after the end date (since 2024-01-01); a required update is the contractor's duty.

`Zulässig` has **16 distinct values**, not four:

| value | rows | parser → |
|---|---|---|
| Ja - mit Einschränkung | 1 424 | restricted |
| Ja | 613 | listed |
| Nein | 607 | nein |
| Ja - <= 800W Anlage | 261 | restricted |
| Ja - <= 16A Anlage | 167 | restricted |
| Nein - Befristung abgelaufen | 122 | nein |
| Ja, befristet | 89 | limited |
| Ja - <= 16A Anlage, mit Einschränkung | 67 | restricted |
| Ja - nur für Eigenverbrauch | 55 (54 AC batteries) | restricted |
| Ja - mit Einschränkung, befristet | 42 | limited |
| Nein - Typ B | 28 | nein |
| Ja - bis 30kVA Rückspeisung, befristet | 21 (all Victron) | limited |
| Ja - <= 800W Anlage - mit Einschränkung | 10 | restricted |
| Nein - In Prüfung | 10 | nein |
| Ja - mit Einschränkung und ext. Entkupplungsschutz | 3 | restricted |
| Ja - <= 800W Anlage, befristet | 1 | limited |

Dates: 2026-12-31 (118 rows), 2027-01-31 (34), others 2023–2026; every past date sits on a „Nein - Befristung
abgelaufen“ (121) or „Nein“ (2) row — no "Ja" row is past its date. Firmware strings are free text
("Software-Version: V1.09, ARM Version:V1.18B, DSP1 …").

**Meaning not documented by the list:** „<= 16A Anlage“ (most rows are single-phase units ≤ 3.68 kVA, but 20 are
single-phase > 3.68 kVA), „nur für Eigenverbrauch“ (presumably AC batteries that do not export — TOR 6.1.2 / 6.3.1 notes
exclude non-exporting AC storage from the 30 kVA sum), „bis 30kVA Rückspeisung“, „ext. Entkupplungsschutz“. GridFit
should show the word as written.

#### Charger list (`AT-EV`, file 2026-10-30)

Columns: `Marke`, `Type`, `Nennleistung [kVA]`, `Phasenzahl`, `Art Betriebsmittel` (AC 458, DC 142, AC-Bidirektional 8,
DC-Bidirektional 6), `Anschlussart` (Fest 581, Mobil 33), `Nachweis OVE R37 (Laden)` (Ja - befristet mit Einschränkung 245,
Ja - befristet 240, Ja 54, Ja - mit Einschränkung 48, Ja - befristet & <= 16A 23, Ja - <= 16 A 4), `Nachweis OVE R25
(Einspeisen)` (all „Nein“ — no bidirectional charger is cleared for feed-in), `EINSCHRÄNKUNGEN ab Firmware`,
`Datum befristet` (508 × 2026-12-14), `Herstellererklärung`, `OVE R37 Prüfbericht` (106 Vorhanden), `OVE R25 Prüfbericht`.
**508 of 614 rows rest on a maker's declaration and are time-limited to 2026-12-14**; from 2026-12-15 an OVE R 37 test
report is required (page text and TOR VNA NS V1.3.1 note 39). The next file after 2026-12-14 should show whether they
turn into „Nein“ or disappear.

### Suggestions for `registers.py` / `tools/registers/parse.py`

1. `contains` text: list the real words (above), not "Ja / Ja - mit Einschränkung / Ja - befristet / Nein".
2. `Nein - Befristung abgelaufen` → map to `expired` (GridFit already has the state) instead of `nein`; `Nein - Typ B` is
   not a failure but "type B, not covered" — consider `other` or a note.
3. `Art Betriebsmittel` „Windenergie-Wechselrichter“ (17) becomes class `inverter` because the word contains
   „wechselrichter“ — should be `other`.
4. Not parsed yet: `Deaktivierbare USV-Fähigkeit?`; on AT-EV `Herstellererklärung` / `OVE R37 Prüfbericht` /
   `OVE R25 Prüfbericht` (the last three say what the entry rests on — useful after 2026-12-15).
5. `kva=num(ps) or num(pw)` is right (kVA column first); the kW column is also there.

### Reuse terms

None stated. The site has an Impressum (publisher, ZVR 064107101) and a privacy page only; the list page says
„Sie erhebt keinen Anspruch auf Vollständigkeit. Fehler vorbehalten.“ No licence, no prohibition. GridFit's current use
(status word, firmware note, end date per row, with a link) is unchanged by this check; asking the publisher remains the
clean route for anything more.

Sources: https://www.wechselrichterliste.at/tor-sea-typ-a, /ladeeinrichtungen, /ueber, /impressum, /information-in-english,
/tor-sea-typ-b (all seen 2026-11-01); TOR Stromerzeugungsanlagen Typ A V1.4 (2026-06-01) 8.1; TOR Verteilernetzanschluss NS
V1.3.1 (2026-03-30) 8.1; `C:\Users\madis\projects\gridfit-riigid\gridfit\registers.py`, `tools/registers/parse.py`,
`data/registers/snapshots/2026-11-01.json.gz`.

## Belgium (BE)
### One list, one publisher

There is one list for the whole country: Synergrid vzw/asbl publishes it for all Belgian distribution grid operators
(Fluvius, ORES, RESA, AIEG, AIESH, REW, Sibelga). No grid operator keeps its own. Next to it Synergrid publishes a
**plug&play extract** (PDF, ed. 09.10.2026, 444 GLV references) — a subset of the same list, not a second register.
The relay lists (C10/21 interface relays, C10/23, C10/24 synchrocheck, C10/25 export-limit relays) are separate
Synergrid lists for installation components; GridFit does not need them for inverters.

### File and date

| | value |
|---|---|
| page | https://www.synergrid.be/nl/homologatie/elektriciteit/decentrale-productie-eenheden (seen 2026-11-01) |
| file on the page | `/images/downloads/c10_26_list_of_pgu_compliant_with_c10_11_ed2_1_12_2019.xlsx` — **still the current file**: the page links exactly this name (NL page; the plug&play page links it with a cache-buster `?1760452883141`) |
| what `registers.py` fetches | the same URL — correct |
| HTTP Last-Modified on 2026-11-01 | Fri, 30 Oct 2026 10:48:44 GMT, 1 555 983 bytes |
| "LAST UPDATE" cell (sheet 1, B7) | 2026-10-30 |
| our snapshot `2026-11-01.json.gz` meta | `source_date 2026-10-30`, 9 067 rows (8 995 listed + 72 expired) — **complete and current** |
| newest approval date in the file | 2026-10-29; newest "publication date update/correction" 2026-09-22 |
| sheet title | "C10/26-LIST OF POWER-GENERATING UNITS HOMOLOGATED ACCORDING TO THE REQUIREMENTS OF ANNEX D OF THE TECHNICAL PRESCRIPTION C10/11 ed. 2.4 (15/10/2025)" — the file name still says "ed2_1_12_2019" (a fixed name kept since 2019; not stale) |

`listing.json` has **no BE key** on purpose: `registers.listing()` skips BE (personal-use terms), so BE appears on
the site only as "listed / expired" + link. That is consistent with the terms below.

Counts in the 2026-10-30 file (my own read, openpyxl): 8 995 listed rows, 302 brand spellings, 469 rows marked
"Plug&play" in column AB, 17 "Suitable for V2G", 53 "Generator (diesel)"; 72 rows on the expired sheet (31 "expired
since 01/09/2020", 18 "since 11/12/2020" — the 2020 transition — plus later ones; Growatt 18, Vestas 14, Omnik 13,
Sofar 10, Solis 4 …).

### Sheets and columns (the list's own words, shortened)

Sheets: **"C10-26 power-generating units"** (the list), **"explanation"** (column legend, still headed with
ed2.1 text), **"C10-26 expired homologations"**. Header in rows 5–10, data from row 11.

| col | header | meaning (legend) |
|---|---|---|
| B (1) | Synergrid reference number GLVxxx-yy-zzzz | xxx = manufacturer, yy = the manufacturer's file number, zzzz = unit; "GLV" = gelijkvormigheidsverklaring (declaration of conformity). **The model cell (E) hyperlinks the signed GLV PDF** |
| C (2) | Brand name | "under which the unit is marketed on the Belgian market" |
| D (3) | Name of the product series | |
| E (4) | Reference of the model / type | must distinguish units of a series unequivocally |
| F (5) | Firmware version | "reference of the firmware version of the unit" (often "x.y or higher") |
| G (6) | Small storage: power control system type EnFluRi (name) and/or "P1" | storage units only |
| H (7) | Other (bigger) storage: other power control system | storage units only |
| I (8) | Pac,r rated active power (W) | from datasheet/nameplate — informative only |
| J (9) | Smax maximum apparent power (VA) | the value that counts for every limit; firmware limits ignored; **pink** if single-phase > 5 000 VA |
| K (10) | 1-phase or 3-phase | the unit itself, not the connection |
| L–Q (11–16) | Additional characteristics: integrated automatic separation system (≤ 30 kVA) [D.3]; RfG type B / "type B ready" (usable in installations ≥ 1 MW); additional frequency range 51.5–52.5 Hz [D.4.1]; power response to under-frequency [D.6.2]; P(U) [D.7.2]; compliant power control system provided | "optional additional characteristics … following the information in checklist annex D" |
| R–U (17–20) | Limitations: only for "small" installations [D.7.1]; only for HV connection [D.4.3]; only for modules < 800 W [D.9.1]; only as backup power system §2.2.1 | X = limitation applies |
| V–AA (21–26) | Application: solar, wind, CHP, energy storage, **backup power system**, other | "the applications for which the unit is suitable" |
| AB (27) | Additional information | Plug&play / Suitable for V2G / Generator (diesel, gas …) |
| AC (28) | Synergrid homologation approval date | final approval; validity conditions: no change to the units, **no new edition of C10/11**, test reports not past their validity, and procedure S1/01 |
| AD–AE (29–30) | Publication date of update/correction; summary of correction | e.g. "P1 port added" (46), "Plug&play option removed" (40) / "added" (37), "SmaX … corrected (firmware power limitation removed)" (since INFO 02.2023) |

The expired sheet keeps the older layout (temporary + final homologation columns) and ends each row with the reason
("homologation eXpired since 01/09/2020", …).

### Findings for our parser (`tools/registers/parse.py`, `read_be`)

1. **Gensets are classed as batteries.** `cls_of` reads column 25 ("Backup power system", application) as storage
   (`sto or bak → battery`). 1 047 listed rows have backup ticked without storage — CAT, MWM, MTU, EVW, Caterpillar,
   2G … diesel/gas gensets and CHP — and our snapshot shows them as `battery` (CAT 227, MWM 225, MTU 125 …). Fix:
   `bak` alone (no storage, no solar) → `other`; or use column AB "Generator (…)". 3 559 storage rows also tick
   backup; those are hybrids/batteries with a backup output and are classed correctly.
2. **Plug&play is in column AB** ("Plug&play", 469 rows). The parser derives plug-in only from kVA; the snapshot has
   0 BE rows with class `plug-in`. Column AB (or the "only for modules < 800 W" limitation, col 19) is the list's own
   flag.
3. **GLV links point to two hosts.** 6 881 rows link `https://www.synergrid.be/images/downloads/…`, **2 111 rows
   (the newer, signed ones) link `https://dev.synergrid.be/images/downloads/…`** and 3 link `http://www.synergrid.be`.
   The dev-host links work (HTTP 200 on 2026-11-01), the same path on www returns 404. If GridFit ever links the GLV,
   it must take the hyperlink from the cell as-is. (We only link the list page now — fine.)
4. Brand spellings vary (e.g. "Growatt" / "Growatt ", "CAT" / "Caterpillar" / "CATERPILLAR", "FOXESS" / "Fox ESS");
   the alias table handles makers, not trailing spaces — check `_collapse` covers it (it does strip whitespace).
5. Two "empty maker/model" errors in the snapshot come from rows below the data (a link to
   `https://www.synergrid.be/images/downloads/.pdf` and an empty row) — harmless, can be skipped by requiring a GLV id.

### Reuse terms (Synergrid website, seen 2026-11-01)

General terms of use of the website, "Intellectuele eigendomsrechten": you may consult, download and reproduce the
information on the site **for personal use, with the source stated**, under the Belgian Code of Economic Law on
copyright; this does not apply to texts that restrict it; multimedia needs prior permission; for reproduction of
information contact Synergrid by e-mail. (https://www.synergrid.be/nl/algemene-voorwaarden/algemene-voorwaarden-voor-het-gebruik-van-de-website)
So the earlier reading stands: commercial republication of the list's contents (firmware, GLV ids, dates) needs
Synergrid's permission; GridFit's "listed / expired + link" shape is the safe form until then.

### What the statuses mean for GridFit

- **listed** — on sheet 1: homologated against C10/11 ed. 2.4 Annex D (older GLVs were filed under ed. 2.1 / 2.3 and
  remain listed; the legend's rule that a new C10/11 edition ends a final homologation has evidently not been applied
  to ed. 2.2–2.4, which did not touch Annex D's unit requirements).
- **expired** — on the expired sheet: may not be newly installed (Synergrid FAQ: old inverters "no longer conform …
  may no longer be newly installed").
- Pink Smax (single-phase > 5 kVA) is a usage restriction, not a status — not parsed now; worth a flag later.

## Czechia (CZ)
### Is our parsed list complete and current?

**Yes — the file has not changed since our snapshot.**

- I fetched the file again on 2026-11-01 from the URL that `gridfit/registers.py` uses:
  `https://www.cezdistribuce.cz/file/edee/distribuce/legislativa/seznam_schvalenych_stridacu.xlsx`
  (HTTP 200, 113 093 bytes).
  - Sheet 1 still says "Stav k 2026-08-21".
  - The ZUE sheet says "Stav k 2026-08-06".
  - These match `listing.json` → `registers.CZ.snapshot` 2026-08-21 and the snapshot 2026-11-01 meta (`source_date` 2026-08-21, 821 rows).
- The RfG page (https://www.cezdistribuce.cz/cs/pro-vyrobce/overeni-souladu-s-rfg) links only this one xlsx. The file has no dated name, so the in-file "Stav k" date is the only version marker. **No newer version was found.**
- The file has not changed for 10 weeks.
  - The earlier research (EU table) already noted that "Stav k" had stood for two months.
  - The update rhythm is irregular. By month of entry: 212 rows in 2024-10, 89 in 2026-03, 89 in 2026-08.

### What the file contains, and what we parse

The file has four sheets.

| sheet | "Stav k" | rows | parsed by `read_cz()` |
|---|---|---|---|
| Schválené střídače | 2026-08-21 | 819 data rows, 46 makers | yes, `cls: inverter`; multi-model cells are split on newlines |
| Schválené střídače - ZUE (storage) | 2026-08-06 | 2 (Atmoce MS-7K-U, Emaldo EM-INV-03-B) | yes, `cls: battery` |
| Síťové ochrany (protection relays) | 2026-08-21 | 2 (ESIT UF300, Schrack URNA0345) | no — external protection relays are outside GridFit's scope (fine) |
| Již neplatné (expired) | — | 0 ("Sem budou přesunuty již neplatné Protokoly/Certifikáty") | no — empty; watch it: the first expired rows will appear here |

**Total in our snapshot: 821 entries** (819 + 2). This matches the meta.

Footer notes in sheet 1 that the parser skips:
- For category B, compliance can be proven with a certificate or protocol only where the supply point has a single active element. One generating unit or one storage unit is meant. In that case no simulation is needed, but the on-site tests stay.
- One note is a naming rule. Any Fronius Verto type name may carry the suffix "SPD 1+2" or "SPD 2".

#### Columns (the list's own header words) and how `read_cz()` maps them

| column | meaning | parser field |
|---|---|---|
| Výrobce | maker | `maker_raw` |
| Typ střídače | model; one cell may hold several models, one per line | `model_raw` |
| FW | the approved firmware, often several components ("DSP: …; ARM: …") | `fw` |
| Nastavení/Setup | the settings profile to select on the unit (e.g. "Czech 2023", "EN50549_CZ-PPDS(>16A)", "PPDS_CR", "Česko(CZ)", or an SMA .bck file name) | `extra.setup` |
| certifikát/protokol | kind of proof and issuer | `cert` |
| Datum vydání Certifikátu/Protokolu | issue date of that certificate or protocol | `extra.cert_date` |
| Datum zápisu do tabulky | date of entry in the list | `date` |
| Kategorie VM | VM category the entry is approved for | `extra.category` |
| Poznámka | note | `extra.note` (first 200 chars) |

**"certifikát/protokol" values.** Counts are from the 819 inverter rows:

| value | rows |
|---|---|
| Protokol (EGD) | 529 |
| Protokol (ČEZd) | 171 |
| Certifikát (SZÚ) | 100 |
| Protokol (ČEZd) nebo Certifikát (SZÚ) | 13 |
| Protokol (EGD) nebo Protokol (ČEZd) | 6 |

The ZUE rows are spelled "Protokol(EGD)".

There are no certificate numbers and no validity dates. The SZÚ certificates themselves carry a "Platnost do" date, e.g. B-00337-26 is valid until 2029-03-11.

**"Kategorie VM" values:**

| value | rows |
|---|---|
| A1/A2 | 734 |
| A1 | 53 |
| B1/B2 | 15 |
| A1/A2 (A2 pouze s baterií) | 5 |
| A1/A2/B1/B2 | 5 |
| A1/A2 a A1 | 4 |
| A1/A2/B1 | 3 |

Two of these need explaining:
- "A1" alone means the type is not approved for A2 plants above 11 kW.
- "A2 pouze s baterií" means approved for A2 only with a battery.

**There is no status word.** Every row means "approved". The parser writes `status: listed`, which is correct. The list has no "restricted" or "expired" state yet; that is what the "Již neplatné" sheet is for.

### Suggested parser and registers.py notes

1. **`registers.py` wording.**
   - `"gate": "Yes at ČEZ Distribuce for A1/A2 units since 2025-01-01."` is right.
   - Suggest adding: "Protocols from the DSO laboratories: EG.D and PREdi accept only those issued by 2025-12-31 and only until 2026-12-31; ČEZd states no end date."
   - `"contains"` is right. Also add: "four sheets incl. tested protection relays and an (empty) expired sheet".
2. **Firmware.** The FW column often holds several versions joined with "nebo" ("or"), e.g. Deye "Inv5612-a341 (nebo Inv5622-a341); LcdC30". The text is shown verbatim, which is fine.
3. **2026 protocols.** 88 rows (ČEZd 57, EG.D 31) carry a laboratory protocol issued in 2026. The makers are Atmoce, Deye, GoodWe, Sigenergy, EcoFlow, RCT Power, Kstar, Dražice, Huawei and Emaldo.
   - ČEZd lists them, so ČEZd accepts them.
   - EG.D's and PREdi's notices accept only protocols issued by 2025-12-31.
   - So "listed at ČEZd" does not imply "accepted at EG.D / PREdi". If GridFit says the list speaks for the whole country, it overstates.
4. **Mixed rows.** Rows "Protokol (ČEZd) nebo Certifikát (SZÚ)" (13) show the type has both kinds of proof. They could be counted as "certificate".

### How many operators publish lists

- **ČEZ Distribuce publishes a list:** the xlsx above.
  - It is the only machine-readable list.
  - It draws on both DSO labs and on SZÚ.
- **EG.D has a list of its own lab, but it is not reachable.**
  - In search results EG.D's lab page (https://www.egd.cz/laborator) describes a list of inverters its lab tested against PPDS Příloha 4. Their correct function is assumed only with the listed firmware and the Czech setting selected.
  - egd.cz answers 403 to curl and WebFetch, and shows a "maintenance" page to headless Edge. **The list could not be read on 2026-11-01.**
  - A third-party copy (cefas.cz, "20240809seznam-doporucenych-stridacu.pdf") is from 2024-08-09 and stale.
  - EG.D lab protocols appear on ČEZd's list (529 rows), so the EG.D-tested types are largely covered there. Whether every EG.D-tested type is on ČEZd's list is **not confirmed**.
- **PREdistribuce publishes no list.**
  - Its installation document (2026-02) refers to "the list of certified devices … for the Czech Republic".
  - Footnote 1 of that document says "PDS ještě upřesní, kde a v jaké podobě budou jednotlivé seznamy zveřejněny" — the operators will still say where and in what form.
- **There is no national list yet.** Searches on 2026-11-01 found nothing published under that name.
  - When it appears, it should replace or join the ČEZd xlsx as GridFit's CZ source.
  - SZÚ publishes no public register of its PPDS certificates (not found).

### Terms of use

The ČEZ Distribuce page footer says "Copyright 2026 ČEZ, a. s. – Všechna práva vyhrazena" ("all rights reserved"). No reuse terms are stated for the xlsx. This is unchanged from `registers.py`.

The current use is the status per model with a link, plus the firmware, the kind of proof and the entry date. That is facts per model, not a copy of the table, and it stays reasonable. Do not republish the whole sheet.

### Reuse in GridFit

The list has these columns per model that GridFit can show:
- the firmware
- the settings profile name
- the kind of proof and its issuer
- the proof's issue date
- the entry date
- the VM category

The settings profile name is useful to installers: it is the menu item to pick on the unit. It is not shown on GridFit yet (`extra.setup` is parsed).

Evidence-type counts per GridFit brand on the list:

| brand | rows | proof |
|---|---|---|
| Fronius | 75 | all Protokol (EGD) |
| SolaX | 74 | EGD 63, SZÚ 6, ČEZd 5 |
| Growatt | 52 | EGD 30, ČEZd 22 |
| Deye | 50 | EGD 32, SZÚ 18 |
| GoodWe | 46 | EGD 27, ČEZd 15, SZÚ 4 |
| Fox ESS | 42 | SZÚ 33, ČEZd 9 |
| Huawei | 19 | EGD 15, ČEZd 4 |
| Solis | 17 | all EGD |
| Sungrow | 11 | all EGD |
| Kostal | 6 | all EGD; setting "CZ PPDS 2018 <16A", tested 2023-03-17 |
| SMA | 5 | all EGD |
| Victron | 0 | — |

Brands that rely only on laboratory protocols are exposed to the end of protocol acceptance at EG.D and PREdi on 2026-12-31: Fronius, Sungrow, Solis, Kostal, SMA, Growatt and Huawei.

## Netherlands (NL)
### Is our parse complete and current?

**Yes, both files, row for row.**

| | operator's newest | registers.py fetches | snapshot 2026-11-01 |
|---|---|---|---|
| generation (opwek) type A | xlsx "Versie 31 oktober 2026", 4 359 data rows, 188 brands; served as "Goedgekeurde opwek omvormers type A 01-11-2026.xlsx" (101 423 B) | `api.energieleveren.nl/api/v2/files/homologation-file/POWER_GENERATING` | source_date 2026-10-31, part of 7 021 rows |
| storage (opslag) type A | xlsx "Versie 31 oktober 2026", 2 662 data rows, 178 brands ("…opslag omvormers type A 01-11-2026.xlsx", 69 986 B) | `…/homologation-file/ELECTRICAL_STORAGE` | same |
| API's own date | `GET …/homologation-file/last-modified` → `{"lastModified":"2026-10-31T00:00:00Z"}` | not used | — |

- I downloaded both files today and compared them with `data/registers/snapshots/2026-11-01.json.gz` (NL rows):
  7 021 = 4 359 + 2 662; the 57 apparent differences are whitespace only (the parser collapses double spaces and
  line breaks inside a type cell, e.g. "Tower PRO  M 6.3", "EUE2-\nPDL36G2"). The 2026-10-29 snapshot (list
  version 28 Oct) had the same 7 021 rows; no row was added or removed between versions 28 and 31 October.
- The file name carries **the request date**, the sheet carries the **list version** in A3 ("Versie 31 oktober 2026");
  `read_nl()` reads the version from row 3 — correct. The `last-modified` endpoint (found in energieleveren.nl's own
  front-end code) gives the same date as JSON and could replace the regex if the sheet text changes.
- The old route — dated PDFs on netbeheernederland.nl ("goedgekeurde_omvormers_type_a_dd_23-04-2024.pdf") — is gone
  (the URL now returns an HTML page). There is **no second type-A source**: no per-DSO list (Liander, Stedin, Enexis
  publish none; they all use Netbeheer Nederland's) and no PDF.

### What is not parsed

- **Type B lists** (PDF, "Versie 8 oktober 2026"): generation 284 lines (columns Merk / Model / Type, Type = PPM-PV,
  PPM-WT, SPGM …) and storage 197 lines (Merk / Type), linked from netbeheernederland.nl/publicatie/goedgekeurde-omvormers-opwek-type-B
  and …-opslag-type-B. Type B = 1 MW and above, outside GridFit's home scope; worth a line on the country page.
- energieleveren.nl's registration status per installation (Conform / Niet-conform / Onbekend) is private data.

### How many operators, what the list means

- **One list for the whole country**, kept by Netbeheer Nederland (the association of all Dutch grid operators) and
  served through energieleveren.nl, the operators' joint registration site. It started on 2021-04-21 as a derivative of
  Synergrid's Belgian C10/26 list, updated with DNV GL (Solar Magazine 2021-02-24 / 2021-04-21).
- **Columns:** only `Merk` (brand) and `Type`. No firmware, no certificate, no date, no status word, no phase or power.
  Every row has the same meaning; our status word "listed" is right.
- **Legend (row 1–2, paraphrased):** a list of RfG type-A inverters for which it has been shown for the Netherlands that
  they meet the RfG requirements; not exhaustive by definition, updated regularly; if your inverter is missing, ask
  the supplier, and the supplier contacts Netbeheer Nederland by e-mail.
- **Generation vs storage:** 2 048 brand/type pairs sit on both lists (hybrids). The storage file's sheet is also called
  "Goedgekeurde omvormers Type A" and its header text is word-for-word the generation header.

### Data-quality notes for the parser / join

- The generation list is **not only inverters**: about 224 rows are CHP gas engines and gensets (INNIO Jenbacher 106,
  Caterpillar 27, Viessmann 24, 2G Energy 23, Remeha 15, MTU 13, Vaillant 9, EC Power 5, Cummins 2), some with long
  "+ Stamford generator … refer to 18-EZE-…" type strings; `read_nl()` classes every generation row `inverter`.
- Storage rows are classed `battery`, but most are hybrid or AC-coupled inverters (the list is of *omvormers*).
- Brand cells joining two names: "ILumen / SMA", "Solarwatt / Fronius", "Solarwatt / Kostal", "Solarwatt / SMA",
  "Centrica / MTU", "E3/DC", "Voltronic/ Vision" … — the maker join should split on "/" or treat these as rebrands.
- Brand spellings on the NL list: "SolaX Power", "FoxESS", "KOSTAL", "Victron Energy", "Solis" (+ 1 row "Ginlong").
- 18 type cells contain line breaks (several types in one cell).

### Reuse terms

- None stated: no licence or terms on the xlsx, the API or netbeheernederland.nl/requirements-generators (cookie notice
  only); energieleveren.nl links a privacy page only. Same finding as the pass-3 table ("none stated"). The list is a
  public download linked by Netbeheer Nederland for exactly this purpose (checking a type).

## Poland (PL)
### What exists

One list, kept by PTPiREE (Polskie Towarzystwo Przesyłu i Rozdziału Energii Elektrycznej) for the five OSDs that
are its members and verify certificates together: ENEA Operator, ENERGA-OPERATOR, Stoen Operator, PGE Dystrybucja,
TAURON Dystrybucja (WiPWC 1.3 introduction; PTPiREE "Warunki i procedury" page). No OSD publishes a list of its own
(none found). The list page https://ptpiree.pl/kodeksy-sieci/wykaz-certyfikatow/ (seen 2026-11-01) carries **two**
PDF files, both exports of an Excel workbook (PDF title "2026-10-26 Tablica robocza-Certyfikaty_1.x.xlsx"; no xlsx
is published):

| file | heading on the file | pages | rows (Lp.) | Last-Modified | size |
|---|---|---|---|---|---|
| `2026-10-26-Wykaz-urzadzen_1.3.pdf` | "Wykaz urządzeń akceptowany od dnia 01.11.2024 / List of devices accepted from 01.11.2024" (WiPWC 1.3) | 225 | 1–2491 | 2026-10-26 13:20:53 GMT | 914 753 B |
| `2026-10-26-Wykaz-urzadzen_1.2.pdf` | "Wykaz urządzeń akceptowany do dnia 31.12.2026 / List of devices accepted until 31.12.2026" (WiPWC 1.2) | 851 | 1–8531 | 2026-10-26 13:20:55 GMT | 3 332 594 B |

Both are dated "Data publikacji 26.10.2026" in the footer of every page. The page says the list is updated "nie
rzadziej niż raz w miesiącu" (at least once a month); the next file is therefore expected by about 2026-11-26.

### Is our parse complete and current?

- `gridfit/registers.py` PL fetches only the **1.3** file (regex `Wykaz-urzadzen_1\.3\.pdf`); `listing.json`
  `registers.PL.snapshot` = 2026-10-26 — **current** (no newer file on 2026-11-01). 1 009 models carry a PL status
  (`listed`), from 2 491 rows (rows repeat per model, firmware and certificate; non-inverter rows such as CHP gensets
  are class "other").
- The **1.2 file is not read.** It is 3.7× larger and still counts for connections until 31 December 2026 (WiPWC 1.3
  §10.2; PTPiREE notice 2026-10-05). Several big brands are **only** on 1.2 on 2026-10-26: Fronius (16 certificates;
  72 rows already past their acceptance date, 40 until 2026-12-31), Growatt (9 certificates, 99 rows), Victron
  (2 certificates, 20 rows); SMA has 12 rows on 1.3 against ~116 on 1.2. For two months GridFit therefore says
  "not listed" for models an OSD still accepts. Options: (a) parse 1.2 as a second file with status "listed until
  31.12.2026" and drop it on 2027-01-01; (b) keep 1.3 only and say on the PL page that the 1.2 list still counts until
  31.12.2026. After 2027-01-01 the 1.2 file stops mattering for new type-A connections (the page will presumably
  remove it — not announced).
- Within 1.3, **369 rows are "WOS 2018"** and all carry 31.12.2026 in the date column (counted from the text; 2 122
  "WOS 2025" mentions). For type A after 2026-12-31 WOS 2025 applies (PSE 2025-05-30), so these rows will likely
  stop counting on 2027-01-01 as well — the list itself does not say so for type A; it says it only for B/C/D.
- 5 rows on 1.3 carry 26.07.2026 (already past) and are still on the list; on 1.2, about 373 rows carry a date
  before 2026-11-01. "Listed" therefore does not mean "accepted today": the date column must be compared with today.

### Columns and what they mean (list's own words, abridged)

`Lp.` · `Certyfikat / Certificate`: `Nr dokumentu / Document number`, `Data akceptacji dokumentu / Document Acceptance
Date`, `Wersja WOS` (1.3 only: "WOS 2018" / "WOS 2025") · `Urządzenie / Device`: `Nazwa producenta / Manufacturer's
name`, `Adres producenta`, `Rodzaj Urządzenia / Type of device` (free text: "Falownik fotowoltaiczny", "Falownik
hybrydowy", "przekształtnik do współpracy z magazynem energii", "Mikroinwerter", "Zespół prądotwórczy" …), `Typ model`,
`Zakres wymagań PPM: (A,B,C,D) / Scope of requirements PPM`, `Wersja oprogramowania / Firmware version`.

**The date column** ("Data akceptacji dokumentu") is the date **until which** the certificate is accepted in the
connection process — not the date PTPiREE accepted it:
- the page: for type B, C, D devices struck off but named in connection conditions issued before 2025-12-01, "certyfikat
  będzie akceptowany w okresie do dnia wskazanego w kolumnie „Data akceptacji dokumentu”";
- the 1.2 heading "akceptowany do dnia 31.12.2026" and its rows: 31.12.2026, or an earlier date where the certificate
  itself expires earlier (e.g. Fronius COCPVP04029/24B-01_R4 → 19.10.2026);
- WOS 2025 rows on 1.3: dates 2028–2031, matching the certificate's expiry (WiPWC 1.3 §9: validity at most 5 years;
  e.g. GoodWe A3 50697928 0001 issued 2026-04-09, expiry 2031-04-09, list date 09.04.2031).
The notice of 2026-10-05: the 31.12.2026 cut "pozostaje niezależny od wskazanego w nich okresu ważności" and buyers
should "sprawdzić datę akceptacji jego certyfikatu w wykazie w wersji 1.3". `registers.py` `date_label` should read
"accepted until" (it now says "mostly in the future — read it as the certificate's end date"), which is right in
substance.

**Status words:** none — presence on the list is the status. Struck-off devices disappear; PTPiREE publishes no list of
removals (the page: reasons are available from the maker). A struck-off device may be refused "od dnia wykreślenia".

**Usage rules the list states:** search the current file only; get the certificate from the maker (OSDs and PTPiREE
do not hand certificates out — `przewodnik.pdf`); the device name in the notification must be identical to the
certificate; a listed device can still be refused if it misses the micro-installation regulation or the IRiESD
(RS-485 + SunSpec named explicitly).

### Reuse terms

None stated. The page footer is "© PTPiREE 2015 - 2026"; no licence, no terms for the list files; the PDFs carry no
notice. Same as recorded in `registers.py` ("No reuse terms are stated (© footer)"). Asking PTPiREE for permission
(as for Synergrid / FGW) is the clean route; the data are facts (certificate numbers, dates), the PDF layout is theirs.

### Parser notes

- 1.3 rows are multi-line blocks; the header block repeats on every page; page footers "Data publikacji 26.10.2026
  Str. N". Certificate numbers have spaces ("A3 50697928 0001", "44 799 26 406749 - 343") and split across lines
  ("TC-GCC-DNV-SE-0124-\n13587-0").
- Certificate-number prefixes seen and their issuers (from the certificates read): `A3 5…` TÜV Rheinland LGA
  Products; `U2x-…` Bureau Veritas Consumer Products Services Germany (DAkkS D-ZE-12024-01-00); `LS2…GCC-…` Lyns-tci
  Technology Guangdong; `6xxxxxx.01 COC` DEKRA (not confirmed); `ESY …` TÜV SÜD (from a search snippet, not confirmed);
  `CN-PVES-…` unknown; `25-042-03` / `26-226-00` style (Kostal) unknown.

## Sweden (SE)
### Is our parse complete and current?

- **Newest file on the operator's page (seen 2026-11-01, page dated 29 Oct 2026):** `rikta-ratt-26-10-23.csv` and
  `rikta-ratt-26-10-23.pdf`, both labelled "23 okt 2026". `gridfit/registers.py` takes the CSV by the regex
  `href="([^"]*rikta-ratt-[\d-]+\.csv)"` off the page — it matches the current link
  `/4aa4f3/globalassets/medlemsportalen-oppet/rikta-ratt/rikta-ratt-26-10-23.csv`. Snapshot in `data/registers/listing.json`:
  `"snapshot": "2026-10-23"`. **Current.** Energiföretagen aims at a new list every second Friday, so the next one would be
  6 Nov 2026 (target, not a promise).
- **Size:** the CSV (cp1252, `;`) has 3,560 lines after the header, of which **3,502 data rows** (the rest empty `;;;;`),
  164 makes, Löpnummer 1–3679 (not contiguous: removed entries leave gaps). `listing.json` has 2,514 models with an SE status —
  fewer because GridFit joins rows to normalised models (duplicates, unmatched makes); not a loss by itself, but the parent
  should compare the parser's row count with 3,502.
- **Only one operator publishes a list.** Energiföretagen Sverige runs it for the whole country; none of Ellevio, Vattenfall
  Eldistribution or E.ON Energidistribution publishes a list of its own — Ellevio's type-A form asks "Är valda växelriktare
  listade på Rikta Rätt?" and Vattenfall's 2026 conditions do not mention a list. (E.ON's site returned 403 to the fetch; not
  checked from its own pages.)
- **Page title changed:** now "Rikta Rätt – information om omriktare för anslutning till det svenska lågspänningsnätet"
  (registers.py `name` says "Rikta Rätt — växelriktare för solceller"). URL unchanged.

### Columns and their meaning (the CSV's own header)

| # | header | meaning |
|---|---|---|
| 0 | Löp-nummer | running number of the entry (not a certificate number) |
| 1 | Fabrikat | make (trailing spaces occur: "Growatt ", "Solplanet ") |
| 2 | Typbeteckning/ Modellnummer | type designation |
| 3 | Programvara (versionsnummer) | firmware reviewed; empty in 6 rows |
| 4 | Effekt (kW) | power, decimal comma; empty in 21 rows |
| 5 | Antal faser | 1 or 3 (316 single-phase rows, 3,186 three-phase) — see quirks |
| 6 | Energikälla | Sol / Sol/Batteri / Batteri / Sol/Batteri/DC-laddare / Sol/Vind … |
| 7 | Granskad (Datum) | date reviewed, ISO except 4 rows in dd/mm/yyyy and 1 empty |
| 8 | Kommentarer | free text: Hybrid, restrictions, EMC notes |

The page's own words on what a row means (paraphrased): only equipment that passed the pre-review is listed; the review checks
submitted documents and certificates and that the unit *can* be set right, not that it *is*; Energiföretagen does not verify
test reports or test anything; listing is "not a formal approval"; the list "has no legal status and is not mandatory"; it does
not carry Elsäkerhetsverket's sales bans, though Energiföretagen tries to remove banned products.

### Parser findings (tools/registers/parse.py `read_se`)

1. **Restrictions are read as plain "listed".** 119 rows say the unit may only be connected in a three-phase arrangement
   ("får enbart anslutas i trefaskoppling", also misspelt "anlsutas", "får endast monteras i trefaskoppling") — 118 of them
   single-phase units. 15 rows say "EMC från tredje part saknas" (no third-party EMC), 75 "EMC-cert för industriell miljö",
   9 "EMC bara upp till 40:e överton redovisad". The parser keeps the comment (first 200 chars) but sets status `listed`;
   `restricted` ("listed with restrictions") would be truer for the three-phase-only rows.
2. **Energy source misplaced:** row 3377 Solplanet ASW150K-LT has "Aiswei B.V." in Energikälla → classed `other`.
3. **Dates:** 4 Growatt WIT-HU rows (3395–3398) carry `25/09/2026`; Victron row 2118 has no date. The parser passes the string
   through.
4. **Duplicate running numbers:** 2839 (FOXESS TM241kWh-100kW-H and Hoymiles HIT-6L-G3S) and 2849 (FOXESS TM241kWh-125kW-AC and
   Megarevo MPS0500). If `rid` is used as a key, two rows collide.
5. **Phases quirk:** some 230 V single-phase units carry "3" (e.g. Victron MultiPlus-II 230 V 24/3000 listed 2022 with 3 phases;
   the 2023 rows for the same units say 1) — probably "three units in a three-phase set". GridFit should not use this column as the
   maker's phase count (docs/checks.md already says the list's kVA and phases are not datasheet evidence).
6. **DC chargers:** 49 rows are "Sol/Batteri/DC-laddare" (classed hybrid — fine); 3 rows are a bidirectional AC wallbox
   (comment "AC Laddbox elbil … bidirektionell laddning", whitelisted EV combination) and land in class by energy source.

### Rikta Rätt 2.0 — what changes for the parser

- Format, application form, **XML** data format and a test data set: "presented during November 2026" (not yet out on 2026-11-01).
- Listing in 2.0 opens at the turn of 2026/2027; from **Q2 2027** a 1.0 listing also needs a 2.0 listing; from **September 2027**
  no new 1.0 listings; the **1.0 CSV is unpublished at the turn of 2027/2028**.
- 2.0 is no longer a pass list: every product with a make and type designation is included, with the certificates, declarations
  and data the maker chose to submit; each operator judges, guided by an Energiföretagen industry guideline on which data are
  necessary. GridFit's status word "listed" will not mean the same thing in 2.0 — the parser should carry what is documented
  (certificates present / missing) rather than a pass.
- registers.py `gate` text ("listing in Rikta Rätt 2.0 is expected from Q2 2027") is right; add the September 2027 stop and the
  2027/28 CSV removal.

### Reuse terms

No terms of use or copyright notice on the page or in the CSV (seen 2026-11-01). The service is free; application, review and
listing are financed by the grid operators through their Energiföretagen membership fee. A courtesy notice to Energiföretagen
before publishing remains sensible, as for the other lists.

### Sources

- https://www.energiforetagen.se/energifakta/elsystemet/produktion/solceller/rikta-ratt--vaxelriktare-for-solceller — page dated 2026-10-29, seen 2026-11-01
- https://www.energiforetagen.se/4aa4f3/globalassets/medlemsportalen-oppet/rikta-ratt/rikta-ratt-26-10-23.csv — 2026-10-23, 294,917 bytes
- https://www.ellevio.se/globalassets/content/ovrigt/ellevio-anmalan-av-produktionsanlaggning-typ-a.pdf — 2025-09-12
- https://www.vattenfalleldistribution.se/globalassets/1.-privat/elnatsanslutning/anslut-elproduktion/tekniska-villkor-egen-produktion-vattenfall-eldistribution-ab-2026.pdf — 2026-09-02

## Germany (DE)
### Short answer

- **No approved-model list exists in Germany.** No grid operator, BNetzA or VDE FNN publishes approved models.
- **The de facto list is ZEREZ**, the statutory register of unit and component certificates run by FGW e.V.
  (entrusted under § 49d(3) EnWG). It is a *certificate* register, not an approval: a ZEREZ-ID proves that a
  certificate (or a maker's declaration / prototype entry — field 1.12 says which) was registered, and its
  status says whether it is valid. Since 1 February 2025 it is the gate: the operator takes only the ZEREZ-ID
  and may not ask for certificate data any other way (NELEV § 4(9)-(10), § 7(4)).
- **One register for the whole country** (not per operator). Each of the several hundred DSOs uses it; none
  publishes a list of its own (none found).
- **GridFit parses nothing for DE today.** `gridfit/registers.py` lists DE only as a planned register
  ("ZEREZ (FGW)", `https://zerez.net/`, note "a web app; the public view needs checking and it holds no
  wallboxes"); `data/registers/listing.json` has no `DE` key (registers present: AT, CZ, EE, NL, PL, SE).

### Newest published version vs what GridFit has

| | ZEREZ | GridFit |
|---|---|---|
| form | live web app (React + GraphQL), public view without login per FAQ; REST API v1 for registered users | — |
| newest change | client bundle Last-Modified 2026-10-21; user manual Rev. 5 of 2026-03-13; FAQ page modified 2025-12-10; "other documents" page 2026-06-18; value-list templates Rev. 1 (2024-12; 4110 inertia variant 2026-06) | no snapshot |
| size | not obtained this pass (pv magazine counted 827 certificates on 2025-01-02; the live count was not queried) | 0 |

### What the fields and statuses mean (ZEREZ's own words, briefly)

- Validity (FAQ): a certificate with status „ungültig" "darf nicht verwendet werden und die entsprechenden
  Einheiten sind vom Netz zu trennen". For 4105 the rule gives only an issue date, so "Grundsätzlich gelten
  ausgestellte Zertifikate daher als gültig"; a predecessor may be marked „Abgelaufen" when a newer
  certificate exists for the same unit (manual § 4.6). NELEV § 5(5): an expired validity does not invalidate
  installed plants, but a first connection must not rest on an expired certificate.
- Verification (API enum): Verified / Verification Pending / Ongoing Feedback Process.
- "Nachweisdokument" (1.12): certificate, maker's declaration or prototype.
- "replaced by": the successor certificate.
- No firmware field in the public overview or the 4105 value list; firmware is in the certificate PDF
  (the API carries `software_environment_version_number` per certificate).
- No wallbox/charger category; plug-in batteries (Marstek, Anker Solarbank) appear per the 2026-10 pass.

### Reuse terms

The terms of use (2025-02-06) govern accounts, uploads and corrections; they are silent on copying or
republishing register data, and the CMS pages carry "Alle Rechte vorbehalten". Registration and use are
free of charge. **Republishing needs FGW's permission** — see `zerez.md`, steps 2 and 8.

### What GridFit can show without the register

- The maker's own certificate (evidence layer): VDE-AR-N 4105 unit certificate + NA-protection certificate,
  issuer, number, date, edition (2018-11 vs 2026-03), firmware — see `evidence.md`.
- A link to zerez.net per model, not a status. The status word ("in ZEREZ, valid") needs either the
  public view (if it works without login and FGW allows reuse) or the API.
