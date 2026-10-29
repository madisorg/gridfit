# GridFit site (Astro)

The static site, built from the dataset that `../build.py` writes. Design rules: [`../DESIGN.md`](../DESIGN.md).

```bash
cd web
npm ci
npm run build                       # -> web/dist/ (1 032 pages, ~5 s)
python -m http.server 8396 -d dist  # preview at http://localhost:8396
```

- Reads `../data/dataset/{families,rows,changelog}.json`, `../data/registers/listing.json` and
  `../data/curated/{hacs,families}.yaml`; writes nothing outside `dist/`. Run `python build.py` first when
  the dataset should be fresh.
- Same environment variables as the Python build: `GRIDFIT_BASE_URL` (canonical links, `sitemap.xml`,
  robots sitemap line) and `GRIDFIT_ANALYTICS` (`plausible:<domain>` or `cloudflare:<token>`).
- Cloudflare Pages: build command `pip install -r requirements.txt && python build.py && cd web && npm ci && npm run build`,
  output `web/dist`.
- Fonts are self-hosted from `src/fonts/` (IBM Plex Sans, Barlow Semi Condensed — SIL OFL 1.1, licences beside them).
