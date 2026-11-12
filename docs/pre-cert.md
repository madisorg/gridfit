# Pre-certification: a maker's settable ranges against each country's values

Written 2026-11-01 (pilot). Madis's question of that day: can every EU country's grid requirements be gathered in one
database and used to "pre-certify" inverter models? The requirement check (`docs/checks.md`) already proves what a
datasheet can (power class, phases, frequency and voltage range, cos φ, DC injection — 2 to 7 items a country) and
takes the rest from a maker's declaration as a whole. This pilot asks about the step between: **does a public
EN 50549-1 document give, per function, the range the unit can be set to — so that "the country's value is inside
it" can be checked mechanically, for every country at once, without a national declaration?**

The answer: **yes for one kind of document — the certificate that carries the EN 50549-1:2019+A1 Annex C parameter
table — which covers 8–9 of Estonia's and Spain's 10 document-level requirements, 4–6 of Italy's, and every Greek one
the operator does not set; no for the rest (two-page certificates, country-preset lists, national grid-code
certificates), which give no range at all. Only 5 of the evidence layer's 29 EN 50549 documents carry such a
table.** Details and reasons below.

## The layer

`data/test-reports/<brand>.yaml` — one file per brand, one entry per document, beside `data/evidence/` and joined the
same way (`families[].match` over the register code). Facts only: the document's own numbers and the PDF page; no
PDF, no copied text. Downloads are in `cache/reports/<brand>/` (git-ignored; read with `python -I`).

```yaml
brand: Deye
documents:
- id: tuvr-a3-50714707-sg06lp3
  title: "..."                       # issuer, number, standard, families
  url: https://...                    # the maker's file (or a distributor's copy: copy_of)
  kind: certificate-annex-c           # see the kinds below
  issuer: TÜV Rheinland LGA Products GmbH
  cert_no: A3 50714707 0001
  report_no: CN269EL4 001
  issued: '2026-02-05'
  standards: [EN 50549-1:2019+A1, EN 50549-10:2022]
  firmware: 2207-1175-1809
  pages: 12
  text_layer: true                    # false = a scan; nothing to parse
  seen: '2026-11-01'
  families: [{name: "...", match: ^SUN-[3-8]K-SG06LP3-EU-[BC]M2$}]
  functions:                          # EN 50549-1 functions — Annex C's rows
    ov2: {page: 5, threshold_un: {range: [1.0, 1.3]}, time_s: {range: [0.1, 5]}}
    rocof: {page: 3, immunity_hz_s: {max: 3.5, default: 2}}
    lfsm_o: {page: 3, f1_hz: {range: [50.2, 52], default: 50.2}, droop_pct: {range: [2, 12], default: 5}}
  tested: [p_u]                       # functions the document says were assessed, with no value printed
  presets: {EE: "...", IT: "..."}     # a presets list: the preset's name per country, no value
  note: "..."
```

A parameter is `{range: [lo, hi]}` (settable), `{fixed: x}` (not configurable), `{default: x}`, `{max: x}` (a
capability "up to x", or a limit the unit stays under), or `{tested_at: x}` (a full test report's one test point).

| function | EN 50549-1 clause | parameters |
|---|---|---|
| `freq_bands` | 4.4.2 | `band_47_5_48_5_min`, `band_51_51_5_min` (how long it stays connected; `.inf` = unlimited) |
| `uf_power` | 4.4.3 | `threshold_hz`, `reduction_pct_hz` |
| `rocof` | 4.5.2 | `immunity_hz_s` |
| `uvrt` | 4.5.3 | `curve` (text) |
| `lfsm_o` / `lfsm_u` | 4.6.1 / 4.6.2 | `f1_hz`, `droop_pct` |
| `cosphi` / `q_modes` | 4.7.2 | `min_cosphi`; `modes`: `q_setpoint`, `q_u`, `q_p`, `cosphi_setpoint`, `cosphi_p` |
| `p_u` | 4.7.3 (optional in the standard) | `start_un`, `zero_un`, `gradient_pct_per_pct` |
| `dc_injection` | 4.8 | `max_pct` |
| `uv1` `uv2` `ov1` `ov2` | 4.9.3.2–3 | `threshold_un`, `time_s` (stage 1 = U< / U>, stage 2 = U<< / U>>) |
| `ov10` | 4.9.3.4 | `threshold_un` (10-minute mean) |
| `uf1` `uf2` `of1` `of2` | 4.9.3.5–6 | `threshold_hz`, `time_s` |
| `islanding` | 4.9.4 | `method` (text) |
| `reconnect` / `start` | 4.10.2 / 4.10.3 | `f_low_hz`, `f_high_hz`, `u_low_un`, `u_high_un`, `observation_s`, `ramp_pct_min` |

Kinds: `certificate-annex-c` (a certificate with the standard's parameter table: clause, parameter, settable range,
default), `certificate-table` (a certificate with a table of the maker's own form), `test-report` (the full TRF),
`certificate` (names, standard, report number — no values), `grid-code-certificate` (a national RfG certificate that
names the functions assessed), `country-presets` (the firmware's country presets by name).

## The comparison

`python tools/reports/compare.py [--md] [--registers web/.data/registers.json] [--json out.json]` puts every document
beside every country's setting values. The profiles carry those values as sentences, so the pilot reads them into
numbers in `tools/reports/country_values.yaml` (EE, ES, IT — each requirement names the profile item it reads) and
`tools/reports/gr_draft.yaml` (Greece, the owner session's hand reading; not a profile). A requirement is a list of
`[function, parameter, value]`; a value is a number, an interval `[lo, hi]` (any value in it is acceptable),
`{cover: [lo, hi]}` (the whole interval must be settable — Italy's LFSM-O threshold 50–52 Hz), `{modes: [...]}`,
`present`, or `operator`.

Per parameter, then per requirement (the worst of its parameters):

| state | meaning |
|---|---|
| ✓ covers | the country's value is in the printed settable range (or equals the fixed value; a capability is at least the country's) |
| ✗ outside | the document prints a range or a fixed value, and the country's value is not in it |
| ? not tested | the document names the function (a clause list, a single test point, a mode without settings) but prints no range that answers |
| – not in document | the document says nothing about the function |
| op operator | the country leaves the value to the grid operator per installation (Greece's protection settings) |

Nothing is inferred from a standard a document cites. That reading is a row of its own, the **EN 50549-1 floor**
(`tools/reports/floor.yaml`): the minimum settable ranges a pass requires, as a full test report reproduces the
requirement text. It is what a bare EN 50549-1 certificate would imply if every lab held every unit to the floor —
and the EAST report shows one that did not (reconnection upper frequency settable only 50.0–50.2 Hz, passed).

## Results (2026-11-01: 14 documents from 9 brands, 4 countries)

Regenerate with `python tools/reports/compare.py --md --registers web/.data/registers.json`. "models" = register
models (inverter, hybrid, battery, plug-in) the document's families join. A document that says nothing anywhere
is left out of the per-country tables.

| document | kind | models | EE ✓/✗/?/–/op | ES ✓/✗/?/–/op | IT ✓/✗/?/–/op | GR ✓/✗/?/–/op |
|---|---|---|---|---|---|---|
| Deye — tuvr-a3-50714707-sg06lp3 | certificate-annex-c | 0 | 9/0/0/1/0 of 10 | 8/0/0/2/0 of 10 | 5/3/0/2/0 of 10 | 4/0/0/0/3 of 7 |
| Deye — tuvr-a3-50717844-sg06lp1 | certificate-annex-c | 0 | 9/0/0/1/0 of 10 | 8/0/0/2/0 of 10 | 5/3/0/2/0 of 10 | 4/0/0/0/3 of 7 |
| Deye — bv-u24-0954-g04 | certificate | 7 | 0/0/10/0/0 of 10 | 0/0/10/0/0 of 10 | 0/0/10/0/0 of 10 | 0/0/4/0/3 of 7 |
| EAST — dekra-6052106-53-ea-ktsi | test-report | 0 | 7/0/3/0/0 of 10 | 10/0/0/0/0 of 10 | 5/1/4/0/0 of 10 | 2/1/1/0/3 of 7 |
| GoodWe — tuvr-a3-50588989-et-g2 | certificate | 14 | 0/0/0/10/0 of 10 | 0/0/0/10/0 of 10 | 0/0/0/10/0 of 10 | 0/0/0/4/3 of 7 |
| GoodWe — goodwe-et-12-30-manual-presets | country-presets | 5 | 0/0/0/10/0 of 10 | 0/0/0/10/0 of 10 | 0/0/0/10/0 of 10 | 0/0/0/4/3 of 7 |
| GoodWe — tuvr-a3-50561246-et | certificate | 8 | 0/0/0/10/0 of 10 | 0/0/0/10/0 of 10 | 0/0/0/10/0 of 10 | 0/0/0/4/3 of 7 |
| Growatt — intertek-cn-pves-260337-moda | certificate-table | 49 | 4/0/0/6/0 of 10 | 6/0/0/4/0 of 10 | 3/2/0/5/0 of 10 | 1/0/0/3/3 of 7 |
| Kostal — kostal-plenticore-g3-country-setting-2024 | country-presets | 21 | 0/0/0/10/0 of 10 | 0/0/0/10/0 of 10 | 0/0/0/10/0 of 10 | 0/0/0/4/3 of 7 |
| SMA — tuvsud-d070122-0013-stp110-60 | certificate-annex-c | 4 | 9/0/0/1/0 of 10 | 8/0/0/2/0 of 10 | 6/2/0/2/0 of 10 | 4/0/0/0/3 of 7 |
| Solplanet — bv-u22-0354-asw-lt-g2-pro | certificate-annex-c | 12 | 9/0/1/0/0 of 10 | 8/0/0/2/0 of 10 | 4/4/1/1/0 of 10 | 4/0/0/0/3 of 7 |
| Sungrow — dnv-tc-gcc-0124-07602-sg-rt-pl | grid-code-certificate | 11 | 0/0/3/7/0 of 10 | 0/0/3/7/0 of 10 | 0/0/3/7/0 of 10 | 0/0/3/1/3 of 7 |
| Sungrow — sungrow-country-code-overview-2025-04 | country-presets | 0 | 0/0/0/10/0 of 10 | 0/0/0/10/0 of 10 | 0/0/0/10/0 of 10 | 0/0/0/4/3 of 7 |
| Victron — sgs-2622-0478-multiplus-ii | certificate-annex-c | 9 | 8/1/1/0/0 of 10 | 8/0/0/2/0 of 10 | 4/4/1/1/0 of 10 | 4/0/0/0/3 of 7 |
| EN 50549-1 — en50549-1-floor | standard-floor | — | 6/1/3/0/0 of 10 | 8/0/2/0/0 of 10 | 5/3/2/0/0 of 10 | 3/0/1/0/3 of 7 |

**EE** — Elektrilevi A-type conditions 2023-06-01; protection settings recommended 2019-04-27

| requirement | Deye sg06lp3 | Deye sg06lp1 | Deye g04 | EAST ktsi | Growatt moda | SMA 60 | Solplanet pro | Sungrow pl | Victron ii | EN 50549-1 floor |
|---|---|---|---|---|---|---|---|---|---|---|
| Frequency bands 47.5–49.0 and 51.0–51.5 Hz for 30 min | ✓ | ✓ | ? | ✓ | – | ✓ | ✓ | ? | ✓ | ? |
| RoCoF withstand 2.5 Hz/s | ✓ | ✓ | ? | ? | – | ✓ | ✓ | ? | ✗ | ✗ |
| LFSM-O from 50.2 Hz, droop 5 % | ✓ | ✓ | ? | ✓ | – | ✓ | ✓ | ? | ✓ | ✓ |
| Below 49 Hz output falls at most 2 % Pmax per Hz | ✓ | ✓ | ? | ? | – | ✓ | ✓ | – | ✓ | ? |
| U>> 1.15 Un 0.1–0.2 s; U> 1.11 Un ≥ 3 s | ✓ | ✓ | ? | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ |
| U< 0.85 Un 1.2–1.5 s | ✓ | ✓ | ? | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ |
| f> ≥ 51.6 Hz; f< ≤ 47.4 Hz | ✓ | ✓ | ? | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ |
| Reconnect within 49.0–50.1 Hz after 60 s, ramp ≤ 10 %/min | ✓ | ✓ | ? | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ |
| P(U) from 110 % Un, zero at 112 % | – | – | ? | ? | – | – | ? | – | ? | ? |
| cos φ = 1; fixed cos φ, cos φ(P), fixed Q or Q(U) on request | ✓ | ✓ | ? | ✓ | – | ✓ | ✓ | – | ✓ | ✓ |

**ES** — Orden TED/749/2020 as amended by TED/82/2026; RD 1699/2011 table 1

| requirement | Deye sg06lp3 | Deye sg06lp1 | Deye g04 | EAST ktsi | Growatt moda | SMA 60 | Solplanet pro | Sungrow pl | Victron ii | EN 50549-1 floor |
|---|---|---|---|---|---|---|---|---|---|---|
| Frequency bands 47.5–48.5 and 51.0–51.5 Hz for 30 min | ✓ | ✓ | ? | ✓ | – | ✓ | ✓ | ? | ✓ | ? |
| RoCoF withstand 2 Hz/s (500 ms window) | ✓ | ✓ | ? | ✓ | – | ✓ | ✓ | ? | ✓ | ✓ |
| LFSM-O from 50.2 Hz, droop 5 % | ✓ | ✓ | ? | ✓ | – | ✓ | ✓ | ? | ✓ | ✓ |
| Settable connection window and ramp; after an over-frequency trip reconnect only at ≤ 50 Hz | ✓ | ✓ | ? | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ |
| Fault ride-through (figure 14) for type A since 2026-05 | ✓ | ✓ | ? | ✓ | – | ✓ | – | – | ✓ | ? |
| DC injection ≤ 0.5 % of rated current | – | – | ? | ✓ | ✓ | – | – | – | – | ✓ |
| 1.10 Un 1.5 s; 1.15 Un 0.2 s | ✓ | ✓ | ? | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ |
| 0.85 Un 1.5 s | ✓ | ✓ | ? | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ |
| 51 Hz 0.5 s; 48 Hz 3 s | ✓ | ✓ | ? | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ |
| Active anti-islanding (UNE-EN 62116) | – | – | ? | ✓ | ✓ | – | ✓ | – | – | ✓ |

**IT** — CEI 0-21:2026-07

| requirement | Deye sg06lp3 | Deye sg06lp1 | Deye g04 | EAST ktsi | Growatt moda | SMA 60 | Solplanet pro | Sungrow pl | Victron ii | EN 50549-1 floor |
|---|---|---|---|---|---|---|---|---|---|---|
| 47.5–51.5 Hz without time limit | ✗ | ✗ | ? | ? | – | ✓ | ✗ | ? | ✗ | ? |
| RoCoF withstand 2.5 Hz/s | ✓ | ✓ | ? | ? | – | ✓ | ✓ | ? | ✗ | ✗ |
| LFSM-O 50.2 Hz settable 50–52 Hz; droop 2.6 %, settable 2–12 % | ✗ | ✗ | ? | ? | – | ✗ | ✗ | ? | ✗ | ✗ |
| 59.S1 1.10 Un 10-min mean; 59.S2 1.15 Un 0.2 s | ✓ | ✓ | ? | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ |
| 27.S1 0.85 Un 1.5 s; 27.S2 0.15 Un 0.2 s | ✗ | ✗ | ? | ✗ | ✗ | ✗ | ✗ | – | ✗ | ✗ |
| 81>.S2 51.5 Hz / 81<.S2 47.5 Hz 0.1 s; narrow 81.S1 50.2 / 49.8 Hz 0.1 s | ✓ | ✓ | ? | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ |
| 49.90–50.10 Hz, 85–110 % Un; 30 s at start, 300 s after a trip; ramp ≤ 20 %/min | ✓ | ✓ | ? | ✓ | ✗ | ✓ | ✗ | – | ✓ | ✓ |
| P(U)_115: from 110 % Un at ≥ 20 % Pn per 1 % U, zero at 115 % | – | – | ? | ? | – | – | ? | – | ? | ? |
| cos φ down to 0.9; cos φ(P) curve on request | ✓ | ✓ | ? | ✓ | – | ✓ | ✓ | – | ✓ | ✓ |
| DC injection ≤ 0.5 % of rated current | – | – | ? | ✓ | ✓ | – | – | – | – | ✓ |

**GR** — RAE 1165/2020 (RfG type A below 1 MW); protection settings in HEDNO's letter per installation

| requirement | Deye sg06lp3 | Deye sg06lp1 | Deye g04 | EAST ktsi | Growatt moda | SMA 60 | Solplanet pro | Sungrow pl | Victron ii | EN 50549-1 floor |
|---|---|---|---|---|---|---|---|---|---|---|
| 47.5–48.5 and 51.0–51.5 Hz for 30 min | ✓ | ✓ | ? | ✓ | – | ✓ | ✓ | ? | ✓ | ? |
| RoCoF withstand 2 Hz/s over 500 ms | ✓ | ✓ | ? | ✓ | – | ✓ | ✓ | ? | ✓ | ✓ |
| LFSM-O 50.2 Hz, droop settable 2–12 %, 5 % by default | ✓ | ✓ | ? | ? | – | ✓ | ✓ | ? | ✓ | ✓ |
| Reconnect within 49.5–50.5 Hz | ✓ | ✓ | ? | ✗ | ✓ | ✓ | ✓ | – | ✓ | ✓ |
| U>, U>> — HEDNO's letter per installation | op | op | op | op | op | op | op | op | op | op |
| U<, U<< — HEDNO's letter per installation | op | op | op | op | op | op | op | op | op | op |
| f>, f< — HEDNO's letter per installation | op | op | op | op | op | op | op | op | op | op |

**Outside, by document and country** (the country's value is not in the printed settable range)

- Deye tuvr-a3-50714707-sg06lp3 × IT — freq-bands: freq_bands.band_47_5_48_5_min withstands 90, needs unlimited, p. 3
- Deye tuvr-a3-50714707-sg06lp3 × IT — freq-bands: freq_bands.band_51_51_5_min withstands 90, needs unlimited, p. 3
- Deye tuvr-a3-50714707-sg06lp3 × IT — lfsm-o: lfsm_o.f1_hz settable 50.2–52, does not take the whole 50.0–52.0, p. 3
- Deye tuvr-a3-50714707-sg06lp3 × IT — protection-voltage-low: uv2.threshold_un settable 0.2–1, needs 0.15, p. 5
- Deye tuvr-a3-50717844-sg06lp1 × IT — freq-bands: freq_bands.band_47_5_48_5_min withstands 90, needs unlimited, p. 3
- Deye tuvr-a3-50717844-sg06lp1 × IT — freq-bands: freq_bands.band_51_51_5_min withstands 90, needs unlimited, p. 3
- Deye tuvr-a3-50717844-sg06lp1 × IT — lfsm-o: lfsm_o.f1_hz settable 50.2–52, does not take the whole 50.0–52.0, p. 3
- Deye tuvr-a3-50717844-sg06lp1 × IT — protection-voltage-low: uv2.threshold_un settable 0.2–1, needs 0.15, p. 5
- EAST dekra-6052106-53-ea-ktsi × IT — protection-voltage-low: uv2.threshold_un settable 0.2–1, needs 0.15, p. 136
- EAST dekra-6052106-53-ea-ktsi × GR — reconnection: reconnect.f_high_hz settable 50–50.2, needs 50.5, p. 171
- Growatt intertek-cn-pves-260337-moda × IT — protection-voltage-low: uv2.threshold_un settable 0.2–1, needs 0.15, p. 4
- Growatt intertek-cn-pves-260337-moda × IT — reconnection: reconnect.observation_s settable 10–60, needs 300, p. 4
- SMA tuvsud-d070122-0013-stp110-60 × IT — lfsm-o: lfsm_o.f1_hz settable 50.2–52, does not take the whole 50.0–52.0, p. 4
- SMA tuvsud-d070122-0013-stp110-60 × IT — protection-voltage-low: uv2.threshold_un settable 0.2–1, needs 0.15, p. 5
- Solplanet bv-u22-0354-asw-lt-g2-pro × IT — freq-bands: freq_bands.band_47_5_48_5_min withstands 90, needs unlimited, p. 4
- Solplanet bv-u22-0354-asw-lt-g2-pro × IT — freq-bands: freq_bands.band_51_51_5_min withstands 90, needs unlimited, p. 4
- Solplanet bv-u22-0354-asw-lt-g2-pro × IT — lfsm-o: lfsm_o.f1_hz settable 50.2–52, does not take the whole 50.0–52.0, p. 4
- Solplanet bv-u22-0354-asw-lt-g2-pro × IT — protection-voltage-low: uv2.threshold_un settable 0.2–1, needs 0.15, p. 5
- Solplanet bv-u22-0354-asw-lt-g2-pro × IT — reconnection: start.observation_s settable 60–600, needs 30, p. 6
- Victron sgs-2622-0478-multiplus-ii × EE — rocof: rocof.immunity_hz_s withstands 2, needs 2.5, p. 2
- Victron sgs-2622-0478-multiplus-ii × IT — freq-bands: freq_bands.band_47_5_48_5_min withstands 90, needs unlimited, p. 2
- Victron sgs-2622-0478-multiplus-ii × IT — freq-bands: freq_bands.band_51_51_5_min withstands 90, needs unlimited, p. 2
- Victron sgs-2622-0478-multiplus-ii × IT — rocof: rocof.immunity_hz_s withstands 2, needs 2.5, p. 2
- Victron sgs-2622-0478-multiplus-ii × IT — lfsm-o: lfsm_o.f1_hz settable 50.2–52, does not take the whole 50.0–52.0, p. 4
- Victron sgs-2622-0478-multiplus-ii × IT — protection-voltage-low: uv2.threshold_un settable 0.78–1, needs 0.15, p. 6
- EN 50549-1 en50549-1-floor × EE — rocof: rocof.immunity_hz_s withstands 2, needs 2.5, p. 12
- EN 50549-1 en50549-1-floor × IT — rocof: rocof.immunity_hz_s withstands 2, needs 2.5, p. 12
- EN 50549-1 en50549-1-floor × IT — lfsm-o: lfsm_o.f1_hz settable 50.2–52, does not take the whole 50.0–52.0, p. 16
- EN 50549-1 en50549-1-floor × IT — protection-voltage-low: uv2.threshold_un settable 0.2–1, needs 0.15, p. 37

### What the pilot shows

1. **The best document is the certificate with the Annex C parameter table** (5 here: Deye SG06LP3 and SG06LP1, SMA
   STP 110-60, Solplanet ASW LT-G2 Pro, Victron MultiPlus-II). It covers **9 of Estonia's 10** document-level
   requirements (8 for Victron, whose RoCoF withstand is fixed at 2 Hz/s against Estonia's 2.5), **8 of Spain's 10**,
   **4–6 of Italy's 10** and **all 4 Greek ones the operator does not set**. What it never has: P(U) (optional in
   EN 50549-1, not an Annex C row), DC injection and anti-islanding (Spain).
2. **The full test report is close, not better**: EAST's 188-page DEKRA TRF covers Spain 10 of 10 (it has DC injection
   and anti-islanding) and Estonia 7 — LFSM-O, RoCoF, cos φ and P(U) are tested at one point only, so a country value
   off that point is "not tested". The settable protection ranges are in the appended tables (default and three
   points per stage). Full reports are rare in public (one of 14 here, and not a register brand).
3. **The maker's "table of country settings" is not a settings table.** Kostal's PLENTICORE G3 list, GoodWe's manual
   (109 European presets) and Sungrow's overview give the preset's name, the grid code it is written against and the
   month — no value. The hypothesis "country-settings table > full report > certificate" does not hold: these lists
   answer "is there a preset for EE", which `data/evidence` already reads as `country-release`.
4. **A two-page certificate gives nothing to compare** (GoodWe ET G2 and first-generation ET, TÜV Rheinland 2023);
   Bureau Veritas's Deye G04 certificate lists the clauses assessed (every row "not tested").
5. **Italy is not reachable through EN 50549-1 documents alone.** Its values sit outside the standard's floor in four
   places: 27.S2 at 0.15 Un (the floor and every table start at 0.2 Un, Victron at 0.78 Un), the LFSM-O threshold
   settable from 50.0 Hz (tables start at 50.2), 47.5–51.5 Hz without time limit (tables offer 30–90 min; only SMA's
   default is "unlimited"), and P(U)_115. Plus IEC 61850 and FRT above 11.08 kW, which are not EN 50549-1 functions.
   The CEI 0-21 declaration stays the evidence; a table can only flag a unit that would fail (Growatt MODA's
   observation time settable 10–60 s against Italy's 300 s; Solplanet's 60–600 s against Italy's 30 s at start).
6. **The table catches what a bare certificate hides.** Victron's RoCoF 2 Hz/s "not configurable" fails Estonia's and
   Italy's 2.5; Deye SG06 (up to 3.5 Hz/s), SMA (5) and Solplanet (0.5–10) pass. The floor is 2 Hz/s — a generic
   certificate proves nothing for 2.5.
7. **Automatic reading works for Annex C, not for the rest.** One generic parser (`python -I -X utf8
   tools/reports/extract.py score cache/reports`) reads 15–18 of 20 ranges right from the Annex C forms of TÜV
   Rheinland, TÜV SÜD, SGS and BV, 5 of 15 from Intertek's own form, 0 of 14 from the full TRF (its appended tables
   are per test point). One BV range was read wrong (stage-1 under-voltage took the over-voltage range): a hand check
   stays in the loop.
8. **Reach.** Of the evidence layer's 29 EN 50549 documents, 5 carry a parameter table (`extract.py corpus
   ../gridfit/cache/evidence cache/reports --registers web/.data/registers.json`); they join 83 register models,
   against 278 joined only by a document without one. The newest certificates (2026, against EN 50549-1:2019+A1 with
   EN 50549-10:2022) carry Annex C — Deye SG06, Growatt MODA, Victron — but the newest families are often not on any
   list yet (Deye SG06LP3/LP1: 0 register models).

## Ten countries (2026-11-01, second pass)

`tools/reports/country_values.yaml` now carries AT, BE, CZ, DE, NL, PL and SE beside EE, ES and IT (each block names its
profile item; the EE and IT blocks gained the gap check's lines). Run `python tools/reports/compare.py --md --registers
web/.data/registers.json` for every table; the documents with a settable-range table:

| document | kind | models | EE ✓/✗/?/–/op | ES ✓/✗/?/–/op | IT ✓/✗/?/–/op | AT ✓/✗/?/–/op | BE ✓/✗/?/–/op | NL ✓/✗/?/–/op | PL ✓/✗/?/–/op | SE ✓/✗/?/–/op | CZ ✓/✗/?/–/op | DE ✓/✗/?/–/op | GR ✓/✗/?/–/op |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Deye — tuvr-a3-50714707-sg06lp3 | certificate-annex-c | 0 | 10/0/0/1/0 of 11 | 8/0/0/2/0 of 10 | 6/4/0/2/0 of 12 | 10/1/0/2/0 of 13 | 10/0/0/1/0 of 11 | 10/0/0/1/0 of 11 | 9/0/0/2/0 of 11 | 8/0/0/1/0 of 9 | 10/1/0/2/0 of 13 | 4/3/0/1/0 of 8 | 4/0/0/0/3 of 7 |
| Deye — tuvr-a3-50717844-sg06lp1 | certificate-annex-c | 0 | 10/0/0/1/0 of 11 | 8/0/0/2/0 of 10 | 6/4/0/2/0 of 12 | 10/1/0/2/0 of 13 | 10/0/0/1/0 of 11 | 10/0/0/1/0 of 11 | 9/0/0/2/0 of 11 | 8/0/0/1/0 of 9 | 10/1/0/2/0 of 13 | 4/3/0/1/0 of 8 | 4/0/0/0/3 of 7 |
| EAST — dekra-6052106-53-ea-ktsi | test-report | 0 | 8/0/3/0/0 of 11 | 10/0/0/0/0 of 10 | 6/1/5/0/0 of 12 | 8/0/5/0/0 of 13 | 8/0/3/0/0 of 11 | 8/0/3/0/0 of 11 | 7/0/4/0/0 of 11 | 7/0/2/0/0 of 9 | 9/0/4/0/0 of 13 | 5/1/2/0/0 of 8 | 2/1/1/0/3 of 7 |
| Growatt — intertek-cn-pves-260337-moda | certificate-table | 49 | 5/0/0/6/0 of 11 | 6/0/0/4/0 of 10 | 4/2/0/6/0 of 12 | 4/1/0/8/0 of 13 | 5/0/0/6/0 of 11 | 5/0/0/6/0 of 11 | 5/0/0/6/0 of 11 | 4/1/0/4/0 of 9 | 4/1/0/8/0 of 13 | 3/1/0/4/0 of 8 | 1/0/0/3/3 of 7 |
| SMA — tuvsud-d070122-0013-stp110-60 | certificate-annex-c | 4 | 10/0/0/1/0 of 11 | 8/0/0/2/0 of 10 | 7/3/0/2/0 of 12 | 10/1/0/2/0 of 13 | 10/0/0/1/0 of 11 | 10/0/0/1/0 of 11 | 9/0/0/2/0 of 11 | 8/0/0/1/0 of 9 | 10/1/0/2/0 of 13 | 5/2/0/1/0 of 8 | 4/0/0/0/3 of 7 |
| Solplanet — bv-u22-0354-asw-lt-g2-pro | certificate-annex-c | 12 | 10/0/1/0/0 of 11 | 8/0/0/2/0 of 10 | 5/5/1/1/0 of 12 | 10/1/1/1/0 of 13 | 11/0/0/0/0 of 11 | 11/0/0/0/0 of 11 | 10/0/1/0/0 of 11 | 9/0/0/0/0 of 9 | 10/1/1/1/0 of 13 | 7/1/0/0/0 of 8 | 4/0/0/0/3 of 7 |
| Victron — sgs-2622-0478-multiplus-ii | certificate-annex-c | 9 | 9/1/1/0/0 of 11 | 8/0/0/2/0 of 10 | 5/5/1/1/0 of 12 | 9/2/1/1/0 of 13 | 10/0/0/1/0 of 11 | 9/1/0/1/0 of 11 | 8/1/1/1/0 of 11 | 8/0/0/1/0 of 9 | 8/3/1/1/0 of 13 | 3/4/0/1/0 of 8 | 4/0/0/0/3 of 7 |
| EN 50549-1 — en50549-1-floor | standard-floor | — | 7/1/3/0/0 of 11 | 8/0/2/0/0 of 10 | 6/4/2/0/0 of 12 | 8/1/4/0/0 of 13 | 9/0/2/0/0 of 11 | 9/0/2/0/0 of 11 | 7/1/3/0/0 of 11 | 7/0/2/0/0 of 9 | 8/1/4/0/0 of 13 | 5/3/0/0/0 of 8 | 3/0/1/0/3 of 7 |

What it shows:

- **An Annex C table covers most of a country's document-level numbers everywhere except Italy and Germany**: EE 10/11,
  BE 10–11/11, NL 10–11/11, SE 8–9/9, PL 9–10/11, AT 10/13, CZ 10/13, ES 8/10 (the rest is untested or absent, not
  outside). Italy stays at 5–7/12 (27.S2 0.15 Un below the floor, LFSM-O 50.0 Hz), Germany at 3–7/8.
- **Germany's 2026-03 edition breaks the 2018 tables**: f< 2 s / f> 5 s / f>> 52.6 Hz and the 4 Hz/s RoCoF ride-through are
  outside most documents' printed ranges, which were written for 2018-11 (0.1 s trips). Until about 2028-03 a 2018-11
  certificate is still sufficient, so this is "documented for an older edition", not unfit.
- **Storage LFSM-U droop below 2 %** (AT 1 %, settable 1–2 %; DE 1.6 %; CZ settable from 0.1 %) is under the EN 50549-1
  floor of 2–12 %: no generic document proves it. NL's 2 % sits on the floor.
- **AT reconnection**: the TOR's "wait settable 0–300 s" is not compared as a cover (the floor starts at 10 s); the two
  recommended values (60 s, 300 s) are.
- The national-only items (no Annex C function exists: certificate under WiPWC / PPDS / ZEREZ, Bank Nastaw profile name,
  storage power control, logic interface, controllability) are counted per country in the homelab report
  `kataloogid/reference/gridfit-10-riiki.md`; the grammar extensions the gap check asks for (FRT curve points, LFSM-O
  response times, the operating power factor, the RoCoF loss-of-mains trip) are listed in "What the profile needs".

## What the profile needs (handoff — not changed here)

- **Setting values as data.** Each `kind: document` item whose `value` sentence holds numbers gets a `settings` list
  in the grammar of `tools/reports/country_values.yaml` (`[function, parameter, value]`). Greece's protection rows
  are `operator`. Then `country_values.yaml` goes away.
- **Tolerances.** EN 50549-1 sets the protection accuracy at ±1 % Un and ±0.05 Hz (the TRF's appended tables, p. 136);
  a value on the edge of a range (Victron's U>> 1.15 Un, the top of 1.0–1.15) covers, but a profile may want a margin.
- **A state between D and S** in `tools/check/run.py`: "range covers, by the maker's table" — stronger than a
  certificate's general cover, weaker than a national declaration; and "outside the maker's table" as a real ✗ for a
  document-level item (today only a datasheet number can say ✗).
- **The evidence entry and the test-report entry are the same document** (Solplanet U22-0354, Victron 2622/0478,
  Growatt CN-PVES-260337 are in both): when this is adopted, `functions` becomes a field of the `data/evidence`
  entry and `data/test-reports/` folds into it.
- **Grammar extensions from the 10-country pass**: FRT curve points (`uvrt`: u_ret_pu, t_clear_s, u_clear_pu, u_rec2_pu,
  t_rec3_s — ES figure 14, IT table 12, AT figure 5, CZ), LFSM-O response and settling times, the 48.5–49.0 Hz band
  duration (AT 90 min, CZ 90 min), a time for `ov10` (IT 603 s), the RoCoF loss-of-mains trip (PL, SE 2.5 Hz/s 0.5 s), the
  start-up ramp (BE 20 %/min) and a region condition (ES non-peninsular systems).
- **Italy keeps `national-declaration`**; the table is a pre-check there, not evidence. Spain's FRT item needs
  figure 14's points before a curve can be compared.
