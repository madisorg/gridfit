# GridFit

**Does this solar inverter, home battery or wallbox work locally with Home Assistant and evcc — and which EU grid registers list it?**

A static site and an open dataset, built only from open sources. For each product family it shows the
Home Assistant core and HACS integrations and the evcc templates that support it, whether they talk to the
device on your network or through a cloud, whether they can *control* it or only read it, and which of five
national grid registers (AT, NL, CZ, SE, PL) list its models. Every row links to its source and carries the
date it was last seen.

Home Assistant core devices are already covered model by model by the
[Open Home Foundation Device Database](https://device-database-preview.openhomefoundation.org/) (preview);
GridFit links there instead of copying it, and adds what it does not cover yet: HACS custom integrations,
evcc, read-vs-control, and register listings.

## Build

```bash
pip install -r requirements.txt
python build.py              # downloads what is older than 6 days into cache/, then builds
python build.py --refresh    # downloads everything again
python build.py --offline    # builds from cache/ only
python -m http.server 8390 -d site   # preview at http://localhost:8390
```

One command builds from nothing: `cache/` and `site/` are git-ignored and recreated. The build makes about
1 000 small requests to `raw.githubusercontent.com` (manifests and HEAD probes) and never uses the
rate-limited GitHub REST API, so it needs no token.

Environment variables (both optional):

| variable | effect |
|---|---|
| `GRIDFIT_BASE_URL` | e.g. `https://example.eu` — canonical links, `sitemap.xml`, `robots.txt` sitemap line |
| `GRIDFIT_ANALYTICS` | `plausible:<domain>` or `cloudflare:<beacon token>` — cookie-free analytics tag; empty = none |

## What is in the repo

| path | what |
|---|---|
| `build.py` | the one command |
| `gridfit/` | fetch, assemble, render |
| `templates/`, `static/` | Jinja2 templates, CSS, a small vanilla-JS filter |
| `data/curated/brands.yaml` | brand spellings → one canonical name |
| `data/curated/ha_core.yaml` | which HA core integrations are energy devices, and their brand/class |
| `data/curated/hacs.yaml` | which HACS repos are energy device integrations, what their README says they cover |
| `data/curated/families.yaml` | product families of the main brands: model-code pattern + evcc templates |
| `data/registers/listing.json` | register membership snapshot (see below) |
| `data/dataset/` | **the dataset** (generated, committed): `rows.json` / `rows.csv`, `families.json`, `changelog.json` |
| `tools/import_registers.py` | refreshes `listing.json` from the register parser's output |

## Sources and licences

| source | used for | licence / terms |
|---|---|---|
| [home-assistant/core](https://github.com/home-assistant/core) `generated/integrations.json`, component `manifest.json`, platform files | name, `iot_class`, quality scale, settable platforms | Apache-2.0 |
| [HACS](https://hacs.xyz/) store data (`data-v2.hacs.xyz/integration/data.json`) | repo name, domain, stars, last update | facts about public repos |
| each listed HACS repo's `manifest.json`, platform files, README | `iot_class`, settable platforms; the curated "covers" text | facts only; each repo has its own licence |
| [evcc-io/evcc](https://github.com/evcc-io/evcc) `templates/definition/{meter,charger}` | brand, product, connection params, capabilities, sponsor flag | MIT; components needing an evcc sponsorship are excluded from MIT (`LICENSES/exclusions.md`) — the exclusion header sits only in Go driver files, not in the YAML templates. GridFit copies no template content, only the fact of support, and marks sponsor-only templates |
| grid registers AT, NL, CZ, SE, PL | "this register lists this model" + the register's own status word | the registers publish the lists; GridFit keeps the membership fact only, never firmware strings, certificate numbers or other columns, and links back |
| Belgium, Synergrid C10/26 | **not used** | its terms allow personal use only |

The register snapshot comes from a separate parser (six xlsx/csv/pdf downloads, 2026-08-21 … 2026-10-28).
`python tools/import_registers.py <parser-output-dir>` rewrites `data/registers/listing.json`; it drops
Belgium, drops Austria's "Nein" rows (an empty cell, never a negative) and keeps no other column.

**Dataset licence:** [CC BY 4.0](LICENSE-DATA.md) — attribute "GridFit" and keep the per-row source links.
**Code licence:** [MIT](LICENSE).

## How a row is decided

- **local** — `iot_class` starts with `local_` (HA core, HACS); for evcc, the template takes a Modbus
  connection, a host/URI, or is an OCPP template. A template that only takes account credentials is cloud.
- **control** — HA: the integration has `number.py`, `select.py`, `switch.py` or `button.py` (settable
  entities; can be anything from a charge limit to a restart button). evcc: chargers always; meters when
  the template has `battery-control` or `curtail`.
- **families** — a HACS or core row without `families:` applies to every curated family of the same kind
  (wallbox / meter / everything else) of that brand. evcc rows join a family by template name.
  Register models join a family by a regex over the normalised model code — a pattern, not a confirmation;
  the site shows each model's brand-match trust (exact / alias).
- The site never says "does not work" or "not approved": an empty cell is an empty cell.

## Hand check, 2026-10-29

Three brands were checked against the sources themselves (READMEs, HA docs, evcc template files, register rows):

**Deye**
- evcc `deye-hybrid-3p`: Modbus RS485/TCP, capabilities `battery-control` + `curtail` → LP3/HP3 rows "control" ✔.
  `deye-storage`: no capabilities → "metering only" ✔. `deye-evse`: Solarman Wi-Fi logger (port 8899), sponsorship → sponsor flag ✔.
- HACS *Deye Local* README: single-phase LP1 supported (verified on SUN-6K-SG05LP1), LP3/HP3 experimental,
  string/micro "recognised, not mapped yet" → limited to the three hybrid families, README caveat added as a note.
- Same README: newer WiBLE loggers (firmware `DYDA_WiBLE_*`) close ports 8899 and 502 → note added to the
  *Solarman* row, which relies on port 8899 or a Modbus TCP gateway.
- Register spot check: SUN-12K-SG04LP3-EU — AT "listed with restrictions", CZ, NL, SE listed in the raw
  parser rows; BE also listed there but excluded on purpose ✔.

**SolaX**
- HACS *SolaX Inverter Modbus* README: Gen2–Gen5 hybrids, Gen3 AC/RetroFit, X1 Air/Boost/Mini, X3 MEGA/FORTH,
  X3 MIC/PRO, Qcells Q.VOLT HYB-G3-3P; no EV charger → applies to all SolaX inverter families, not the wallbox family ✔.
- HA core `solax`: `local_polling`, no settable platforms → "read" ✔.
- evcc `solax`: `battery-control` ✔; `solax-g2` X3-MIC/PRO G2 metering ✔; X3-EVC / X3-HAC chargers RS485 + sponsorship ✔.
- **Fixed:** the *SolaX Local X1 Micro* repo had spread to every SolaX family; now its own family.

**Fronius**
- HA core `fronius` docs: Solar API (HTTP) for GEN24, IG Plus, Primo, Symo, Symo Hybrid, Tauro, Verto (Plus),
  plus a "Controlling the inverter over Modbus" section; platforms `number`, `switch` → "control".
  **Fixed:** connection now HTTP + Modbus TCP (was HTTP only).
- HACS *Fronius Modbus* README: GEN24 only, needs "Allow control" → **fixed:** was also attached to the
  string-inverter family; now GEN24 only, with the README caveat as a note.
- HACS *Fronius Wattpilot* README: Wattpilot, V2 and flex, "via local LAN or via Cloud" → connection fixed.
- evcc `fronius-gen24`: Modbus TCP, `battery-control` + `curtail` ✔. `fronius-wattpilot` is deprecated in evcc;
  the live route is `ocpp-goe` "Wattpilot (OCPP)", which needs sponsorship → the FAQ says so ✔.
- Register spot check: Symo GEN24 10.0 Plus — AT, CZ, NL, SE ✔.

## Corrections

Open an issue or a pull request. Most corrections are one line in `data/curated/*.yaml`; the dataset and the
change log are regenerated by the build. "My Deye does Modbus TCP from firmware X" is exactly what is needed.

## Publish (first time — done by hand)

1. Create the GitHub repo and push (from this directory):

   ```bash
   gh repo create madisorg/gridfit --public --source . --remote origin --push --description "Which solar inverters, batteries and wallboxes work locally with Home Assistant and evcc"
   ```

2. Cloudflare Pages → *Connect to Git* → this repo. Build command
   `pip install -r requirements.txt && python build.py`, output directory `site`, environment variables
   `PYTHON_VERSION=3.12`, `GRIDFIT_BASE_URL=https://<domain>`, `GRIDFIT_ANALYTICS=plausible:<domain>`.
3. Point the domain at Pages; add it in Plausible (or use Cloudflare Web Analytics and `cloudflare:<token>`).
4. The weekly refresh (`.github/workflows/refresh.yml`) commits `data/dataset/` when a source changed; each
   push rebuilds the site.

## Not affiliated

Home Assistant is a trademark of the Open Home Foundation. evcc, HACS and all product and company names are
trademarks of their owners and are used only to say what works with what. GridFit is not affiliated with any of them.
