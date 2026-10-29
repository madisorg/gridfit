# Dataset licence

The GridReg dataset — everything under `data/curated/` and `data/dataset/` — is licensed under the
**Creative Commons Attribution 4.0 International** licence (CC BY 4.0):
https://creativecommons.org/licenses/by/4.0/legalcode

Attribution: "GridReg (https://github.com/madisorg/gridreg)". Keep the per-row `source_url` and `seen`
fields when you redistribute rows; they are how a reader checks a claim.

## Third-party facts in the dataset

The dataset states facts about third-party sources and links to them; it does not reproduce their content.

- Home Assistant core metadata (integration names, `iot_class`, quality scale): Apache License 2.0,
  © Home Assistant contributors / Open Home Foundation.
- evcc template facts (brand, product name, capabilities, sponsorship flag): MIT, © evcc.io. Components that
  require an evcc sponsorship are excluded from evcc's MIT licence; no part of them is copied here.
- HACS store data and individual repositories: facts about public repositories (names, stars, last update,
  manifest `iot_class`). Each repository keeps its own licence.
- `data/registers/listing.json`: which public grid-register list names which model, with the register's own
  status word, and a link to the register. No other column of any register is included. Belgium's
  Synergrid list is not used.

The CC BY 4.0 grant covers the selection, arrangement and curated text that are GridReg's own work.
