# Freshness: how a new model reaches GridFit

*2026-10-31. The watch is `tools/watch/`; its latest output is [`watch-report.md`](watch-report.md).*

A new inverter, battery or wallbox becomes visible in public in roughly this order:

1. **The maker announces it** — a product page, a press release, a trade-fair launch (Intersolar in June is the
   big one). The page often names a range ("SUN-5-12K-SG05LP3") before every single model has a datasheet.
2. **The trade press repeats it**, sometimes the same day.
3. **A certification body tests it** against EN 50549-1 / VDE-AR-N 4105 and the national rules. These certificates
   are not published in bulk anywhere that may be read automatically (see "Not watched").
4. **A national grid list adds it** — the event GridFit exists for. Lists move weekly (AT, BE, NL) to monthly (PL,
   SE) to rarely (CZ).
5. **Open-source support follows** — an evcc template, a Home Assistant or HACS integration — usually after the
   device is sold, sometimes long after.

GridFit's core question ("which lists carry it, does it work locally") is answered from step 4 and 5. Steps 1–2
are the early warning: a model GridFit should expect, so a family pattern or a datasheet row can be ready when the
list catches up.

## What the watch does

`python tools/watch/run.py` fetches every source below once, politely: robots.txt is checked for the user agent
`GridFit watch (+https://gridfit.eu)` before every URL, one request per second per host (or the site's
Crawl-delay), ETag / Last-Modified where the server sends them. Each source's items — product URLs, feed entries,
model codes, integration keys — are compared with the previous run (`data/watch/seen/<id>.txt`); every model code
is checked against the latest register snapshot, `data/curated/families.yaml` and `data/specs/`. The verdicts:

| verdict | meaning | what to do |
|---|---|---|
| in a list, not yet in GridFit | a grid list gained the row after the last register refresh | run the register refresh (or wait for the monthly one) |
| new to GridFit | no list row, no family pattern | a model to expect; a family pattern if it is a new series |
| family known, in no list yet | a curated family matches, no list carries the model | nothing — it appears when a list does |
| close to a listed model | a listed code starts with it (a range page, a missing suffix) | usually nothing |
| in GridFit | the exact code is in a list GridFit reads | nothing |

`data/watch/codes.json` keeps the date each code was first seen and the date a list first carried it, so after a
few months the report states the real lead time (maker page → list) instead of the estimates below. The first run
of each source is a baseline: everything it lists is counted, nothing is called new.

**First run, 2026-10-31** (HTTP sources plus the Edge page; baseline, so these are inventory numbers, not news):
697 distinct product codes or product-page names from 13 makers, the Kostal country list, evcc and the press,
in 64 HTTP requests plus one Edge page. 25 are exact list models, 76 are close to one (mostly range pages such as
"S6-EH3P(15-20)K-ND-H"), 162 match a curated family but no list, and 434 match neither — a mix of models no list
carries yet, series names and accessories. The six grid lists the watch may read matched the 2026-10-31 snapshot:
nothing pending.

## Sources

"Lead" is how early the source shows a new model compared with the first grid list. It is an estimate until
`codes.json` has measured it.

| source | URL | format | updates | robots / terms | Edge? | lead |
|---|---|---|---|---|---|---|
| **Grid lists** BE, CZ, NL, EE, SE, PL | as in `gridfit/registers.py` | xlsx, html, csv, pdf | BE, NL weekly or faster (file dated 2026-10-23 → 10-30; NL 10-28 → 10-30); PL file 2026-10-26; SE 2026-10-23; CZ 2026-08-21; EE undated | allowed | no | 0 — this is the event |
| Grid list AT, AT-EV | wechselrichterliste.at | xlsx | weekly (10-23 → 10-30) | **robots.txt: `Disallow: /` for every agent** | — | 0, **not watched** |
| Ireland, ESB Networks register | esbnetworks.ie low-carbon-technology-register | dated xlsx link | monthly (file of 2026-10-02) | allowed | no | 0 (not read by GridFit yet; the watch notes a new file) |
| Kostal released countries | kostal-solar-electric.com/…/Released-countries-inverter.pdf | PDF, "Version: 10 / 2026" | monthly | allowed | no | ≈ 0 to weeks before the lists |
| Deye products | deye.com/sitemaps.xml → product-sitemap1–4 | sitemap | on publication | allowed | no | weeks to months before |
| GoodWe | en.goodwe.com/sitemap.xml | sitemap; every lastmod rewritten daily, so only new URLs count | daily | allowed (`/download` disallowed, not used) | no | weeks to months |
| SolaX | solaxpower.com/sitemap.xml (`/our-products/`) | sitemap | Last-Modified 2026-10-30 | allowed | no | weeks to months |
| Fox ESS | fox-ess.com/sitemap.xml (`/products/`) | sitemap | 2026-10-30 | allowed | no | weeks to months |
| Solis | solisinverters.com/sitemap.xml (one `/global/<range>_gl.html` page per model range) | sitemap, 3 MB | daily | allowed | no | weeks to months |
| Hoymiles | hoymiles.com/sitemap.xml (`/product-release/`) | sitemap of press releases | 2026-08-19 | no robots.txt | no | launch day |
| SMA | sma.de/en/sitemap.xml → pages | sitemap | — | allowed | no | weeks to months |
| Fronius | fronius.com/sitemap-groups.xml?country=home (help-center model pages) | sitemap | — | allowed | no | weeks |
| Kostal pages | kostal-solar-electric.com/en/sitemap.xml | sitemap | — | allowed (`cHash` disallowed, not used) | no | weeks |
| Victron | victronenergy.com/sitemap.xml | sitemap | daily | allowed | no | weeks |
| Sofar | sofarsolar.com product list pages (storage and PV inverters) | plain HTML; the codes printed on the page | — | no robots.txt | no | weeks to months |
| Growatt | en.growatt.com/products | JavaScript; its sitemap.xml is from 2024-04 | — | allowed | **yes** | weeks to months |
| evcc templates | github.com/evcc-io/evcc/commits/master/templates/definition.atom | Atom, last 20 commits | several a week | allowed | no | after market launch; can be before a list in a country without one |
| evcc releases | github.com/evcc-io/evcc/releases.atom | Atom | weekly to biweekly | allowed | no | as above |
| Home Assistant core | raw.githubusercontent.com/home-assistant/core/dev/…/integrations.json | JSON keys | daily (dev) | allowed | no | months after |
| HACS | data-v2.hacs.xyz/integration/data.json | JSON keys | daily | allowed | no | after launch |
| pv magazine (int., DE), Solarserver, PV Tech | `/feed/` | RSS; only entries naming a known brand and a model code | daily | allowed | no | launch day; weakest signal (a code is often missing) |

## Not watched, and why

| source | why |
|---|---|
| Austrian lists (TOR Erzeuger Typ A, Ladeeinrichtungen) | robots.txt disallows all crawlers. **GridFit's monthly register refresh reads them anyway** (`gridfit/registers.py`, browser user agent). That is a decision for the owner: ask Oesterreichs Energie for permission, or let the refresh skip AT and carry its previous rows over. Until it is settled the register refresh stays monthly. |
| Huawei | the site's terms forbid automated access. Huawei models arrive through the lists. |
| SolarEdge, Sigenergy | bot walls (a Cloudflare challenge; a "Blocked" page). Not bypassed. |
| Sungrow | the product pages render without the product list in headless Edge (a consent or region gate, not clicked through), and `/sitemap.xml` is an HTML page. |
| energy-storage.news | robots.txt answers 403, which counts as "disallowed". |
| Certification bodies (TÜV Rheinland Certipedia, TÜV SÜD, DEKRA, Bureau Veritas, Intertek) | no bulk or machine-readable list. Certipedia's robots.txt disallows its search pages; the others are search forms. Read by hand only. |
| ZEREZ (DE), ENA Type Test Register (UK) | ZEREZ is closed to this project; ENA's register is a web app whose public API is unverified. |
| Reddit, Facebook, ENF Solar, Geizhals | closed, or a database right GridFit does not take. |

## The rhythm

| when | what | where |
|---|---|---|
| Monday 04:17 UTC | `refresh` workflow: integrations and templates rebuilt, then the watch (all HTTP sources, ~60 requests, ~4 min); report committed with the weekly stamp, and kept as a run artifact | GitHub Actions |
| 1st of the month | the same run also reads every grid list (`--registers-refresh`) | GitHub Actions |
| weekly, any Monday | grid lists too, once the repository variable `REGISTERS_WEEKLY` is `true` | GitHub Actions |
| Sunday evening | the watch's Edge pages (`--edge`), committed so Monday's report folds them in | madis-pc, scheduled task |
| Monday, after the watch | the datasheet harvester's HTTP recipes (`tools/specs/harvest.py --http`): new maker sheets -> manifest + review drafts + `docs/harvest-report.md` | GitHub Actions |
| Sunday evening, after the watch | the harvester's Edge recipes (`--edge`: SMA, Kostal, SolaX), manifest `harvest-edge.json` committed, folded into Monday's report | madis-pc, the same task |

Weekly is enough because the lists themselves move weekly: AT and BE published their latest files on a Thursday
and a Friday, so a Monday run sees them within four days. Daily runs would add requests without moving GridFit,
which is rebuilt on every push anyway. The step that would make GridFit itself fresher is **reading the lists
weekly instead of monthly** — today a new list row waits on average two weeks. The watch already reads every
list except Austria each week and says which rows are pending; flipping `REGISTERS_WEEKLY` (Settings → Secrets and
variables → Actions → Variables) brings them in, after the Austria question above is answered.

## Datasheets

The spec layer (`data/specs/`, README) is fed by `tools/specs/harvest.py`, recipes in `tools/specs/harvest.yaml`.

- **What runs where.** `--http` runs on GitHub Actions right after the watch: maker sitemaps -> product pages
  (Deye, GoodWe, Sungrow's `www.sungrowpower.com/eu/en/products/`, whose pages embed the "Datasheet" button's
  info-support URL as JSON), download centres with plain pages (Fox ESS `/Index/getRes`, Growatt
  `/support/download/datasheet?page=N`, Sofar's European centre `downloads.sofarsolar.eu` with its FacetWP query
  string), and two APIs (Hoymiles `ysecm_api` type -> series -> product -> file list; Solis `getDownloadcenterNavbar`).
  `--edge` runs on madis-pc in the Sunday task: SMA product pages (their download list is script-rendered), the Kostal
  download centre and SolaX's `downloads.html` (its listing API `/ysecm_api` is disallowed by robots.txt; the page
  itself is allowed and is rendered the way a visitor's browser renders it, the `/downloads-NNNN.html` links then
  answer a meta refresh to the file). Same politeness as the watch - the watch's own `Net` class: robots.txt per host,
  one request per second per host, browser-honest user agent, `If-None-Match` / `If-Modified-Since` from the manifest,
  no retries.
- **What it writes.** PDFs into `cache/specs/<brand>/` (git-ignored; on Actions they live for the run only, the
  manifest's sha256 and ETag make the next week's run a set of 304s). `data/specs/harvest.json` (`harvest-edge.json`
  from madis-pc): per PDF the URL, sha256, size, first/last seen, maker, route (`ok`, `edge`, `robots` = listed but the
  file host's robots.txt disallows, `failed`) and the model columns `table.py` read. A new or changed sheet becomes
  rows in **`data/specs/_drafts/<brand>.yaml`** - raw strings kept, `status: draft`, never read by the site.
  `docs/harvest-report.md`: new, changed, unreadable sheets, failed routes, blocked makers, and how many register
  models each maker's sheets could cover.
- **What stays by hand.** The live `data/specs/<brand>.yaml`: a draft row is reviewed against the sheet, the
  correction is written into `tools/specs/draft.py` (named, with the reason) and that script writes the brand file,
  as before. Growatt's and Hoymiles' files: their listings are read, their file hosts (`/upload/`, `w3oss.hoymiles.com`)
  are disallowed or answer 403 to robots.txt, so the manifest names the sheets and they are fetched by hand. Huawei
  (terms), SolarEdge (Cloudflare 403 on everything) and Sigenergy (download centre is a script app; its PDF links
  answer HTML) are recorded in the report and never fetched.

## The incoming channel

- **Missing model** (`.github/ISSUE_TEMPLATE/missing-model.yml`): for installers and makers — brand, model code,
  class, the lists that carry it, a datasheet link, integration links. It shows in GitHub's template chooser, which
  is where the site's header link "Fix a row" already leads. It asks for no contact details.
- **Planned, in the site (not built here):** an Atom feed of `/changes/` and a "new models this month" section, so an
  installer can subscribe to a country's list changes. That is also the growth lever: an installer who subscribes
  comes back every month. The hand-over to the site is in the pull request that added this file.

## Running it

```bash
python tools/watch/run.py                       # all HTTP sources; writes data/watch/ and docs/watch-report.md
python tools/watch/run.py --only deye-products  # one source
python tools/watch/run.py --dry-run             # fetch and print, write nothing
python tools/watch/run.py --edge                # the JavaScript pages (madis-pc: needs Edge and the homelab's ui-kontroll.py)
```

Adding a source is one line in `tools/watch/sources.yaml`; check its robots.txt and terms first and add a row to
the tables above. Downloads go into new directories under `cache/` and are only read, never executed; the register
files are parsed by `tools/registers/parse.py` with `python -I`, as in the refresh.

**Known limits.** A product URL's last segment is read as a code ("sun-12k-sg04lp3-eu" → SUN-12K-SG04LP3-EU), so a
series page ("et-plus-series-…") gives a series name, not a model. A list in the same dated file as the snapshot
cannot hold new models; any difference there is the parser's and is logged, not reported (PL on 2026-10-31: pypdf
6.13 on madis-pc and 6.21 on GitHub Actions read the PDF's columns differently).

### The Edge task on madis-pc (once, by hand)

1. Clone a copy of its own, never a checkout somebody works in (the task resets it to `origin/main` every run):
   `git clone https://github.com/madisorg/gridfit C:\Users\madis\projects\gridfit-watch-edge`
2. Check that it runs: `python C:\Users\madis\projects\gridfit-watch-edge\tools\watch\run.py --edge --dry-run`
   (it finds the homelab's `scripts\ui-kontroll.py` next to the clone).
3. Create the task in PowerShell (full path to python.exe: Task Scheduler cannot resolve a bare `python`):

   ```powershell
   $a = New-ScheduledTaskAction -Execute "powershell.exe" -Argument '-NoProfile -ExecutionPolicy Bypass -File C:\Users\madis\projects\gridfit-watch-edge\tools\watch\edge-task.ps1'
   $t = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 19:00
   Register-ScheduledTask -TaskName "GridFit watch (Edge)" -Action $a -Trigger $t -Description "tools/watch/run.py --edge, commit data/watch/*-edge.json"
   ```

4. Run it once: `Start-ScheduledTask -TaskName "GridFit watch (Edge)"`, then read
   `C:\Users\madis\projects\gridfit-watch-edge.log`. The task pushes to `main`; it only ever commits
   `data/watch/*-edge.json` and the Edge sources' `data/watch/seen/` files, so it never meets the Monday run's files.
