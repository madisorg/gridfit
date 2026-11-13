# The requirement check: model × country

Written 2026-11-01. Madis's question of that day: can the makers' product sheets be run against each country's
requirements automatically? This is that check — three layers, one state per requirement, nothing guessed.

## What it answers

For every register model and every country that has a requirement profile (`data/profiles/{cc}.yaml`: EE, ES, IT
today), every requirement of that profile gets **one state**:

| state | word on the page | meaning |
|---|---|---|
| `S` | meets by datasheet | computed from the maker's datasheet row in `data/specs/<brand>.yaml` |
| `P` | range covers; set at commissioning | the operator writes the protection values per installation (Greece: HEDNO's letter); the sheet can only show that the settable range takes them |
| `L` | over a line: other procedure | the sheet's number is over a line whose `meaning` is an RfG type, a procedure, an EMC class or where protection sits — the model is not unfit, another procedure applies (the traffic light's amber "B") |
| `X` | outside by datasheet | the sheet's number is present and breaks the rule (an 8 kW single-phase unit in Italy, a 16 kW single-phase unit in Spain) |
| `D` | meets by maker's document | a declaration or certificate in `data/evidence/<brand>.yaml` releases the model for the country **and** is a kind of document that country's operator takes (`accepts`) |
| `O` | documented for an older edition | as `D`, but this item changed in a later edition than the one the document cites (`changed_in`) |
| `R` | checked by the operator's list (the profile's own words: "checked by Elektrilevi's list") | the model is on the country's own list (listed, restricted or time-limited) **and** the profile's `list_checks.items` names the item as one the operator reads before listing — and, where `list_checks.only_where` names the item, at least one of the model's list rows carries it (the Dutch storage file, a Polish WOS 2025 row, a Czech A2 category). Tried after the datasheet and before the maker's document: the operator having read the papers outranks the maker's paper (added 2026-11-12, Estonia first). A list item whose applicability the sheet cannot decide (a kW condition, no rated power) is `R` too: the list read it whatever the power |
| `V` | within by the list's figure | a power line (`max` on `ac_kw` / `ac_kva` with a line `meaning`) on a listed model, where neither the sheet nor a document answers it: the country's own list states the type's power (and phases), and that figure is within the line — or, for a phase-bound line, the list's phases say it does not apply. Weaker than the sheet, never `S` (`list_checks.figures`, 2026-11-12: AT, SE) |
| `W` | over a line by the list's figure | as `V`, but the list's figure is over the line: another procedure applies, as with `L` |
| `N` | not shown | neither the sheet nor a document (nor the list) says it — never "fails". Where the profile has the words, the row says why: `list_checks.not_carried` on a listed model, `on_application` on one off the list |
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
evidence layer's (the family's `match` regex and its `countries`, or the `accepted_in` list that `tools/evidence/build.py` derives from `data/evidence/rules/accepts.yaml`). A document counts for a country only when its kind is one
the profile `accepts`:

| `accepts` value | a document is this kind when | taken by |
|---|---|---|
| `national-declaration` | one of its `standards` contains one of the profile's `document_must_cite` keys (CEI 0-21, RD 647 / TED 749 / NTS, TOR Erzeuger, C10/11, PPDS, VDE-AR-N 4105, WiPWC, EIFS 2018:2, Netcode, …) | all ten |
| `generic-en50549-1` | one of its `standards` contains EN 50549 or EN 50438 | EE, NL, SE (Greece in the test fixture) |
| `country-release` | its `kind` is `country-release` — the maker's own released-countries table | no country yet |

A document of a kind the country does not take proves none of the rows; the page names it and says which kinds that
operator takes.

## The profile schema (`data/profiles/{cc}.yaml`)

Two optional keys (2026-11-12) make every row of a list country answer something:

```yaml
list_checks:                       # a model on the operator's own list
  word: "checked by Elektrilevi's list"          # the state's word on the page
  what: "Elektrilevi lists a model after reading …"   # printed once in the block, with the source
  items: [freq-range, rocof, lfsm-o, …]          # must_meet ids a document can prove; the list stands in for those papers
  not_carried: "the list names the model only …"  # why a listed model's other rows (rated-power lines) stay "not shown"
on_application: "neither a datasheet nor a document GridFit holds shows it; off the list, Elektrilevi checks it on the application …"
```

Two more `list_checks` keys (2026-11-12, engine round 2) read the list **row**, not only the fact of listing. The row's
fields come from the parser's `extra` (`tools/registers/parse.py`) through `tools/site_data.py` (`EXTRA`, which now
carries `wos`) into `web/.data/registers.json`, where the engine reads them:

```yaml
list_checks:
  only_where:                      # an item the list checks only on some rows
    storage: { field: list, match: "^storage$", else: "the type is on the file of generating units only …" }
  figures: { power: kw, phases: true, phases_not_if: "trefas" }   # the list's own power (kw | kva) and phases column
```

- `only_where.<item>`: `R` only where one of the model's admitting rows has `extra.<field>` matching the regex; otherwise
  the row is "not shown" with the `else` sentence (or the maker's document answers it). NL `storage` (the storage file),
  PL `rocof` (a WOS 2025 row; WOS 2018 confirms 2.0 Hz/s, not 2.5), CZ `power-recovery` and `power-reduction-input`
  (a "Kategorie VM" with A2).
- `figures`: the row's `kva` (the parser's power column: AT the Nennscheinleistung in kVA, SE Effekt in kW) and
  `extra.phases`, taken only where every admitting row of the model gives the same value. A kVA figure bounds the active
  power from above and a kW figure bounds the apparent power from below, so a kVA figure within a kW line is `V`, a kW
  figure over a kVA line is `W`, and the two undecidable cases stay "not shown" with that reason. The phases column is
  skipped on a row whose comment matches `phases_not_if` (a Swedish single-phase unit listed for a three-phase set) and
  where a model named "230 V" is listed with more than one phase (Victron's 2022 Swedish rows); the row then says so.
  Belgium has the figures but Synergrid's terms allow personal use only, so `be.yaml` has no `figures` until it agrees.

The engine stores `listed: true` per model × country; the reader (`web/src/lib/checks.ts`) words a plain "not shown" row
from `not_carried` or `on_application`, so the sentence is not repeated 150 000 times in `checks.json`. `--validate`
refuses a `list_checks.items` entry that is not a document-provable item. The stats line counts `listed` (models with a
row checked by the list) and `bare` ("not shown" rows with no reason at all; 0 for a profile with both keys, and the test
holds it there).

Two top-level keys next to the existing prose:

```yaml
edition:
  norm: "CEI 0-21"                 # the rule's name, as the summary line prints it
  id: "2026-07"                    # the edition every requirement below is written against
  date: "2026-07"                  # YYYY-MM, compared with the document's edition
  in_force: "2026-08-01"           # optional
  label: "CEI 0-21:2026-07"
  transition_until: "2027-03-01"   # optional (DE): until this day a document to an older edition is accepted
document_must_cite: ["CEI 0-21"]   # what makes a document a declaration against this country's own rule
accepts: [national-declaration]    # the kinds of maker's document the operator takes (table above)
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
| `kind` | `range` · `max` · `min` · `cosphi` · `phases` · `stated` · `settable` · `document` · `none` | how the sheet is judged; `stated` = the operator wants the sheet to state the value (any value); `settable` = the operator sets the values, the sheet shows the range (`P`); `document` = type tests only; `none` = no check, with a `why` |
| `field` | `ac_kw` · `ac_kva` · `ac_a` · `phases` · `freq_hz` · `vac_v` · `vac_pct` · `cosphi` · `idc_pct` · `thdi_pct` · `fsw_khz` · `isc_a` | the sheet value a kind reads (`ac_kw` falls back to `ac_kva`; `vac_pct` is computed from `vac_v` and `vac_un`, or 400 V / 230 V by phases) |
| `meaning` | `rfg-type` · `procedure` · `phases` · `emc-class` · `protection` | what a line means — required on a `max` over `ac_kw` / `ac_kva` / `ac_a`. A country has as many lines as it has meanings (Italy: 11.08 kW is the RfG type and where protection sits; Greece: 1 MW RfG type, 10 kW three-phase / 5 kW single-phase notification, 16 A per phase EMC class). Over an `rfg-type` / `procedure` / `emc-class` / `protection` line the state is `L`, never `X` |
| `range: [lo, hi]` | numbers | the sheet's range must cover it |
| `limit` + `over` / `under` | number + text | `max`: value ≤ limit, else outside with the `over` text; `min` likewise with `under`; `cosphi`: adjustable to ≤ limit |
| `three_phase_above_kw` | number | `phases`: above it the sheet must say three-phase; up to it either is allowed |
| `provable_by` | subset of `[datasheet, document, operator]` | the sheet is tried first where it is allowed; a `document` kind is `[document]` only; `operator` goes with `settable` and only with it |
| `applies` | `classes: [...]`, `below_kw`, `above_kw`, `phases: [1, 3]` | when the item applies; outside it the item is "not applicable". A kW condition with no rated power on the sheet gives "not shown" with the reason. `classes: [wallbox]` makes the item a charging point's: a wallbox is checked against such items only (every other item is not applicable for it), and only in a country that has one — Italy's `charging-controller` |
| `from` + `before` | YYYY-MM-DD + text | the day the item starts to apply; until then a row no document covers says "required from 1 January 2027; until then <before>" (`--today` sets the day for the fixture) |
| `cite` | list of strings | a covering document must also cite one of these for this item (Italy: "Allegato X") |
| `changed_in` + `changed` | YYYY-MM + text | the edition in which this item changed; a document citing an older edition gets `O` here, with the text |
| `source` | text | the clause, printed under the requirement |

Optional datasheet fields the check reads (`data/specs/<brand>.yaml`, only where the sheet states them; otherwise
absent and the row is "not shown"): `freq_hz: [lo, hi]` and `vac_v: [lo, hi]` (the output ranges, which are also the
settable ranges), `vac_un` (the nominal the voltage range is given against: 400 line-to-line, or 230 when the sheet
gives phase voltage), `cosphi: 0.9` (adjustable down to), `idc_pct` (DC injection), `thdi_pct` (current THD, the
sheet's upper bound), `fsw_khz` (switching frequency), `isc_a` (the contribution to the short-circuit current).
`tools/specs/build.py` ignores them; only the check reads them. HEDNO's document list (2026-02-20, § 11) asks the
inverter datasheet for exactly these; a two-page datasheet often leaves DC injection, switching frequency and
short-circuit current out (GoodWe ET G2 does), while the user manual's technical table has them — the spec harvester
should read that table too.

## The document's edition

The newest edition the document's `standards` strings cite: a `YYYY-MM` (CEI 0-21;V2:2024-01 → 2024-01), an `MM.YY`
after a slash (OVE-Richtlinie R25/03.20 → 2020-03, VDE-AR-N 4105/11.18 → 2018-11), or a bare year of a norm that had one
edition that year, from the profile's `edition_years` (per norm: `"VDE-AR-N 4105": {"2018": "2018-11"}`); only then the
month it was issued, which is not an edition (a 2026 certificate to the 2018 edition must not count as 2026-03). Compared
with the profile's `edition.date`: older → the summary says "documented for <standards>; n items of <edition>
unverified", and each item whose `changed_in` is later than the document's edition is `O`. Where several documents
cover a model in a country, the newest edition is the one shown; the others are counted.

Where the profile's `edition.transition_until` is set (Germany: 2027-03-01, the end of the VDE-AR-N 4105:2026-03
transition), a document to an older edition carries `until` and the page says "accepted until 1 March 2027" on the
edition line and on every `O` row. From that day (`withdrawn: true`) every row the document covers is `O` — not only
the changed ones — and the state reads "documented for a withdrawn edition".

A key of `document_must_cite` (and the generic EN 50549 / EN 50438) counts where a term starts in the standards text:
Spain's "NTS" is not the end of "requirements", while a key may run on ("OVE-Richtlinie R" names "OVE-Richtlinie R25").
Brands are keyed through `data/curated/brands.yaml` on both sides (evidence, datasheets, registers), and two files of one
brand are joined, never last-wins.

**One rule for "likely fit".** `checks.json` carries `doc_accepted`: per maker's document, the countries whose
`accepts` take its kind. The site's grid cell, the model page's list tiers and this check read the same answer
(`web/src/lib/evidence.ts` `fitsIn`): a firmware grid-code list or a released-countries table that names a country
is shown on the model page ("named", with its kind), but it is not "likely fit" there.

## The worked example (the test)

ABB/FIMER TRIO-8.5-TL-OUTD × Italy — datasheet FIMER TRIO-5.8/7.5/8.5-TL-OUTD, IT Rev. B
(`data/specs/abb.yaml`); declaration of conformity attached to TÜV Rheinland certificate AK 60176937 0001,
2024-07-01, citing CEI 0-21:2022-03; V1:2022-11; V2:2024-01 (`data/evidence/abb.yaml`):

- **7 by datasheet**: 8.5 kW within the 11.08 kW type-A line (`power-class`) and so the interface protection may be
  built in (`spi-integrated`), and within the 20 kW back-up interface switch line (`backup-ddi`, added 2026-11-01); three-phase, required over 6 kW (`phases`); 47–53 Hz covers 47.5–51.5 (`freq-range`);
  320–480 V at 400 V = 80–120 % covers 85–110 % (`voltage-range`); cos φ adjustable to 0.9 (`reactive`).
- **9 by the maker's document**: RoCoF, LFSM-O, interface protection settings, IEC 61850, reconnection, fitness above
  11.08 kW / FRT, P(U), DC injection, power at under-frequency (`under-frequency`, added 2026-11-01) — of which two are `O`: table 13's 59.S2 time and P(U)_115 changed in the
  2026-07 edition, which the declaration does not cite.
- `storage` not applicable; `sli` no check. Nothing not shown.

The register has this unit under the brand ABB (Estonia's list); the Belgian and Dutch spellings sit under
"Fimer" and are not joined yet, so the model has no page of its own — the check exists for it, the test proves it,
and the page will follow the join.

## The second example (the fixture)

Greece has no site profile yet. `tools/check/fixtures/gr/` holds a test-only profile with the Greek hand example of
2026-11-01 (the owner session's reading of RAE 1165/2020, ΥΠΕΝ/ΔΑΠΕΕΚ/93976/2772 and HEDNO's document list), the real
GoodWe ET G2 datasheet row and the real TÜV Rheinland EN 50549-1 certificate A3 50588989 0001 (2023-06-16, firmware
000006), plus one invented single-phase 6 kW unit. `npm test` runs the engine over it
(`--fixture tools/check/fixtures/gr --out .data/checks-fixture.json`) and proves: GW10K-ET-20 × GR = 5 by datasheet
(RfG type, the 10 kW three-phase notification line, the 16 A EMC line, the frequency range, a stated THDi), 2 set at
commissioning (frequency and voltage protection), 3 by the generic certificate (RoCoF, LFSM-O, reconnection), 3 not
shown (DC injection, switching frequency, short-circuit current — not on the two-page sheet); the 6 kW single-phase
unit is over two lines (5 kW notification, 16 A EMC), never "outside". Write `data/profiles/gr.yaml` from the sources
before Greece goes on the site; the fixture's values are not re-read.

Beside it, `profiles/qa.yaml` is an invented "Testland" for the rules no real profile can show on any given day, and the
fixture runs with `--today 2027-06-01`: the list's figures (`V` within, `W` over, a kVA figure over a kW line left "not
shown", a sheet that wins over the list, a three-phase-set row and a "230 V" name whose phases column is not used),
`only_where` (storage from the storage file only), a list item whose kW condition the sheet cannot decide (`R`), the
charging-point items (`from` before and after the day, `cite` deciding which certificate covers Allegato X, no block in a
country without such an item) and an edition whose transition has ended (every document row `O`, `withdrawn`).

## Coverage on 2026-11-01 (origin/main after the evidence PR #4)

13 892 models × 3 countries. Models with at least one datasheet row: 670 per country (the spec layer's reach; 9
brands). Every applicable item covered: EE 352 (EN 50549-1 certificates, accepted through `data/evidence/rules/accepts.yaml`
→ the families' derived `accepted_in`), IT 319, ES 146. Over a line by datasheet: IT 260 (over 11.08 kW), ES 21
(over 100 kW). Outside by datasheet: IT 16 (single-phase units over 6 kW), ES 1 (a 16 kW single-phase unit), EE 0. Every Italian and Spanish document read so far cites an
edition older than the profile's (IT: before 2026-07; ES: before Orden TED/82/2026), so every documented model there
carries the "unverified" count honestly; 39 Estonian certificates predate the 2023 conditions, with no item changed since.

## What it does not do

- It does not read the datasheet or the declaration itself; both layers are transcribed by hand or by the spec
  harvester, and the check only joins them to the rule.
- The list's own kVA and phases (AT, SE) are never "datasheet" evidence — the sheet is the maker's figure. They answer
  a power line only as `V` / `W`, below the sheet and the document; Belgium's are not used at all (terms). Otherwise a
  list counts only as the operator's own check, through `list_checks`, and only for the items named there.
- A document covers an item only through the standard it cites; it does not read the declaration's tick boxes
  ("fit for plants above 11.08 kW", "SPI integrated") as separate facts yet. That is the next field to add to the
  evidence schema.
- The family pages do not carry the check yet (models that a product family claims have no page of their own).
