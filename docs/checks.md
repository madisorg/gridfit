# The requirement check: model × country

Written 2026-11-01. Madis's question of that day: can the makers' product sheets be run against each country's
requirements automatically? This is that check — three layers, one state per requirement, nothing guessed.

## What it answers

For every register model and every country that has a requirement profile (`data/profiles/{cc}.yaml`: EE, ES, IT
today), every requirement of that profile gets **one state**:

| state | word on the page | meaning |
|---|---|---|
| `S` | meets by datasheet | computed from the maker's datasheet row in `data/specs/<brand>.yaml` |
| `X` | outside by datasheet | the sheet's number is present and clearly outside the rule (an 8 kW single-phase unit in Italy; a unit over the type-A line) |
| `D` | meets by maker's document | a declaration or certificate in `data/evidence/<brand>.yaml` releases the model for the country **and** cites the profile's norm |
| `O` | documented for an older edition | as `D`, but this item changed in a later edition than the one the document cites (`changed_in`) |
| `N` | not shown | neither the sheet nor a document says it — never "fails" |
| `I` | no check | the requirement is optional or sits at the installation's level (`kind: none`) |

A requirement that does not apply to the model (storage rules on a PV inverter; a rule for plants above a kW line)
is listed as not applicable and counted nowhere. The grid operator decides; the page says so on every block.

## Where it runs

`python tools/check/run.py` — a build step in `web/package.json`, after `tools/site_data.py` and
`tools/specs/build.py` — reads the three inputs and writes `web/.data/checks.json` (git-ignored, ~2.6 MB). The
model page (`web/src/pages/[brand]/model/[code]/index.astro`) includes `Checklist.astro`, which reads the file
through `web/src/lib/checks.ts`. `python tools/check/run.py --validate` checks the profiles' `check` blocks only.
`node web/test/checks.mjs` (part of `npm test`) proves the sums and the worked example below.

The datasheet match is the spec layer's (normalised code, or the row's `match` regex); the document match is the
evidence layer's (the family's `match` regex and its `countries`). A document counts for a country only when one of
its `standards` strings contains one of the profile's `document_must_cite` keys — a released-countries table that
names the country but cites no standard proves none of the rows, and the page says so.

## The profile schema (`data/profiles/{cc}.yaml`)

Two top-level keys next to the existing prose:

```yaml
edition:
  norm: "CEI 0-21"                 # the rule's name, as the summary line prints it
  id: "2026-07"                    # the edition every requirement below is written against
  date: "2026-07"                  # YYYY-MM, compared with the document's edition
  in_force: "2026-08-01"           # optional
  label: "CEI 0-21:2026-07"
document_must_cite: ["CEI 0-21"]   # a document's `standards` must contain one of these to count
```

Every `must_meet` entry keeps its `rule` and `value` sentences (the country page prints them) and adds `id`
(kebab-case, unique in the file) and a `check` block:

```yaml
- id: freq-range
  rule: "Frequency range (CEI 0-21 8.4.4, table 9)"
  value: "an inverter stays connected without time limit from 47.5 to 51.5 Hz"
  check: { kind: range, field: freq_hz, range: [47.5, 51.5], provable_by: [datasheet, document], source: "CEI 0-21:2026-07 8.4.4, table 9" }
```

| key | values | meaning |
|---|---|---|
| `kind` | `range` · `max` · `min` · `cosphi` · `phases` · `document` · `none` | how the sheet is judged; `document` = type tests only; `none` = no check, with a `why` |
| `field` | `ac_kw` · `ac_kva` · `phases` · `freq_hz` · `vac_pct` · `cosphi` · `idc_pct` | the sheet value a numeric kind reads (`ac_kw` falls back to `ac_kva`; `vac_pct` is computed from `vac_v` and `vac_un`, or 400 V / 230 V by phases) |
| `range: [lo, hi]` | numbers | the sheet's range must cover it |
| `limit` + `over` / `under` | number + text | `max`: value ≤ limit, else outside with the `over` text; `min` likewise with `under`; `cosphi`: adjustable to ≤ limit |
| `three_phase_above_kw` | number | `phases`: above it the sheet must say three-phase; up to it either is allowed |
| `provable_by` | subset of `[datasheet, document]` | the sheet is tried first where it is allowed; a `document` kind is `[document]` only |
| `applies` | `classes: [...]`, `below_kw`, `above_kw` | when the item applies; outside it the item is "not applicable". A kW condition with no rated power on the sheet gives "not shown" with the reason |
| `changed_in` + `changed` | YYYY-MM + text | the edition in which this item changed; a document citing an older edition gets `O` here, with the text |
| `source` | text | the clause, printed under the requirement |

Optional datasheet fields the check reads (`data/specs/<brand>.yaml`, only where the sheet states them; otherwise
absent and the row is "not shown"): `freq_hz: [lo, hi]`, `vac_v: [lo, hi]`, `vac_un: 400`, `cosphi: 0.9`
(adjustable down to), `idc_pct: 0.5`. `tools/specs/build.py` ignores them; only the check reads them.

## The document's edition

The newest `YYYY-MM` in the document's `standards` strings (CEI 0-21;V2:2024-01 → 2024-01), else the month it was
issued. Compared with the profile's `edition.date`: older → the summary says "documented for <standards>; n items
of <edition> unverified", and each item whose `changed_in` is later than the document's edition is `O`. Where
several documents cover a model in a country, the newest edition is the one shown; the others are counted.

## The worked example (the test)

ABB/FIMER TRIO-8.5-TL-OUTD × Italy — datasheet FIMER TRIO-5.8/7.5/8.5-TL-OUTD, IT Rev. B
(`data/specs/abb.yaml`); declaration of conformity attached to TÜV Rheinland certificate AK 60176937 0001,
2024-07-01, citing CEI 0-21:2022-03; V1:2022-11; V2:2024-01 (`data/evidence/abb.yaml`):

- **6 by datasheet**: 8.5 kW within the 11.08 kW type-A line (`power-class`) and so the interface protection may be
  built in (`spi-integrated`); three-phase, required over 6 kW (`phases`); 47–53 Hz covers 47.5–51.5 (`freq-range`);
  320–480 V at 400 V = 80–120 % covers 85–110 % (`voltage-range`); cos φ adjustable to 0.9 (`reactive`).
- **8 by the maker's document**: RoCoF, LFSM-O, interface protection settings, IEC 61850, reconnection, fitness above
  11.08 kW / FRT, P(U), DC injection — of which two are `O`: table 13's 59.S2 time and P(U)_115 changed in the
  2026-07 edition, which the declaration does not cite.
- `storage` not applicable; `sli` no check. Nothing not shown.

The register has this unit under the brand ABB (Estonia's list); the Belgian and Dutch spellings sit under
"Fimer" and are not joined yet, so the model has no page of its own — the check exists for it, the test proves it,
and the page will follow the join.

## Coverage on 2026-11-01 (origin/main datasheets and documents)

13 892 models × 3 countries. Models with at least one datasheet row: 670 per country (the spec layer's reach).
Every applicable item covered: IT 319, ES 146, EE 0 (no EN 50549-1 certificate read for Estonia yet; the
released-countries tables cite no standard). Outside by datasheet: IT 272 (units over 11.08 kW, single-phase units
over 6 kW), ES 22 (over 100 kW). Every document read so far cites an edition older than the profile's (IT: before
2026-07; ES: before Orden TED/82/2026), so every documented model carries the "unverified" count honestly.

## What it does not do

- It does not read the datasheet or the declaration itself; both layers are transcribed by hand or by the spec
  harvester, and the check only joins them to the rule.
- The list's own kVA and phases (AT, BE, SE) are not used as "datasheet" evidence — the sheet is the maker's figure.
- A document covers an item only through the standard it cites; it does not read the declaration's tick boxes
  ("fit for plants above 11.08 kW", "SPI integrated") as separate facts yet. That is the next field to add to the
  evidence schema.
- The family pages do not carry the check yet (models that a product family claims have no page of their own).
