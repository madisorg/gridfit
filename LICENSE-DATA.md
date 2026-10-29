# Dataset licence

The GridFit dataset — everything under `data/curated/` and `data/dataset/`, plus `data/registers/alias.json` — is licensed under the
**Creative Commons Attribution 4.0 International** licence (CC BY 4.0):
https://creativecommons.org/licenses/by/4.0/legalcode

Attribution: "GridFit (https://github.com/madisorg/gridfit)". Keep the per-row `source_url` and `seen`
fields when you redistribute rows; they are how a reader checks a claim.

## Third-party facts in the dataset

The dataset states facts about third-party sources and links to them; it does not reproduce their content.

- Home Assistant core metadata (integration names, `iot_class`, quality scale): Apache License 2.0,
  © Home Assistant contributors / Open Home Foundation.
- evcc template facts (brand, product name, capabilities, sponsorship flag): MIT, © evcc.io. Components that
  require an evcc sponsorship are excluded from evcc's MIT licence; no part of them is copied here.
- HACS store data and individual repositories: facts about public repositories (names, stars, last update,
  manifest `iot_class`). Each repository keeps its own licence.
- `data/registers/` (snapshots, change log, listing): rows of public grid-connection lists (AT, CZ, EE, NL, PL, SE):
  maker, model, status word, firmware, row or document number and dates, each with a link to its register.
  These are the registers' facts. They are **not** licensed by GridFit; the registers state no reuse terms, and
  the register is the authority. For Belgium's Synergrid list only "listed / expired" is kept (its terms allow
  personal use only).

The CC BY 4.0 grant covers the selection, arrangement and curated text that are GridFit's own work.
