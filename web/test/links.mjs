// Proves a crawler that does not run JavaScript reaches every page the sitemap lists: a breadth-first walk over the
// built HTML from the home page, following only <a href> to the site's own pages. An orphan (a sitemap URL no static
// link reaches) is a failure, and so is a model page more than three clicks from the home page. It also holds the sitemap
// shape: /sitemap.xml is an index of one child per kind, every child under 50 000 URLs, robots.txt names the index, and
// every URL has a lastmod.
//
//     node web/test/links.mjs            (after `GRIDFIT_BASE_URL=… npm run build` in web/)
import { readFileSync, existsSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const dist = resolve(here, "../dist");
let fails = 0, checks = 0;
const fail = (m) => { fails++; console.log("FAIL", m); };
const ok = (c, m) => { checks++; if (!c) fail(m); };

const index = existsSync(resolve(dist, "sitemap.xml")) ? readFileSync(resolve(dist, "sitemap.xml"), "utf-8") : "";
if (!index.trim()) {
  console.log("FAIL dist/sitemap.xml is empty: build with GRIDFIT_BASE_URL set (e.g. https://gridfit.eu)");
  process.exit(1);
}
ok(/<sitemapindex\b/.test(index), "sitemap.xml is a sitemap index");
const robots = readFileSync(resolve(dist, "robots.txt"), "utf-8");
ok(/^Sitemap: \S+\/sitemap\.xml$/m.test(robots), "robots.txt names the index");
const locs = (xml) => [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1]);
const sitemap = new Map();   // path -> child kind
for (const child of locs(index)) {
  const name = child.split("/").pop();
  const xml = readFileSync(resolve(dist, name), "utf-8");
  const urls = locs(xml);
  ok(urls.length > 0 && urls.length <= 50000, `${name}: ${urls.length} URLs (1 to 50 000)`);
  ok((xml.match(/<lastmod>\d{4}-\d{2}-\d{2}<\/lastmod>/g) ?? []).length === urls.length, `${name}: every URL has a lastmod`);
  for (const u of urls) {
    const p = u.replace(/^https?:\/\/[^/]+/, "");
    ok(!sitemap.has(p), `${p} is in one child sitemap only`);
    sitemap.set(p, name.replace(/^sitemap-|\.xml$/g, ""));
  }
}

// the walk: only the site's own page paths (ending in /), query and fragment dropped
const fileOf = (p) => resolve(dist, p === "/" ? "index.html" : p.replace(/^\/|\/$/g, "") + "/index.html");
const HREF = /<a\b[^>]*?\shref="(\/[^"#?]*)/g;
const depth = new Map([["/", 0]]);
const queue = ["/"];
while (queue.length) {
  const p = queue.shift();
  const f = fileOf(p);
  if (!existsSync(f)) continue;
  for (const m of readFileSync(f, "utf-8").matchAll(HREF)) {
    const h = decodeURI(m[1]);
    if (!h.endsWith("/") || h.startsWith("/_astro/") || depth.has(h)) continue;
    depth.set(h, depth.get(p) + 1);
    queue.push(h);
  }
}
const orphans = [...sitemap.keys()].filter((p) => !depth.has(p));
ok(orphans.length === 0, `${orphans.length} sitemap pages no static link reaches, e.g. ${orphans.slice(0, 5).join(", ")}`);
for (const [p, kind] of sitemap) {
  ok(existsSync(fileOf(p)), `${p}: a built page`);
  if (kind === "models" && depth.has(p)) ok(depth.get(p) <= 3, `${p}: ${depth.get(p)} clicks from the home page (at most 3)`);
}
const byKind = {};
for (const [p, kind] of sitemap) { const d = depth.get(p) ?? "orphan"; (byKind[kind] ??= {})[d] = (byKind[kind][d] ?? 0) + 1; }
console.log(`${checks} checks, ${fails} failures · ${sitemap.size} sitemap URLs, ${depth.size} pages reached · clicks from home by kind ${JSON.stringify(byKind)}`);
process.exit(fails ? 1 : 0);
