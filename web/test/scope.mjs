// Proves the site covers exactly the countries data/countries.yaml marks `scope: in`, everywhere it names countries:
// the grid index's columns and names, one built /grid/{cc}/ page each, the front door's country set (functions/index.js),
// and for every `scope: out` row a 301 in web/public/_redirects, no built page and no link from any built page.
//
//     node web/test/scope.mjs            (after `npm run build`; npm test runs it)
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { resolve, dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { parse } from "yaml";

const here = dirname(fileURLToPath(import.meta.url)), root = resolve(here, "../.."), dist = resolve(here, "../dist");
const rows = parse(readFileSync(join(root, "data/countries.yaml"), "utf-8"));
const IN = rows.filter((r) => r.scope === "in").map((r) => r.cc).sort(), OUT = rows.filter((r) => r.scope === "out").map((r) => r.cc).sort();
let fails = 0, checks = 0;
const fail = (m) => { fails++; console.log("FAIL", m); };
const eq = (a, b, m) => { checks++; if (JSON.stringify(a) !== JSON.stringify(b)) fail(`${m}: ${JSON.stringify(a)} ≠ ${JSON.stringify(b)}`); };
const ok = (c, m) => { checks++; if (!c) fail(m); };

eq(IN.length + OUT.length, rows.length, "every row is in or out");
const idx = JSON.parse(readFileSync(join(dist, "grid/index.json"), "utf-8"));
eq(idx.countries, IN, "index.json countries");
eq(Object.keys(idx.names).sort(), IN, "index.json names");
eq(Object.keys(idx.scope).sort(), IN, "index.json scope");
ok(idx.read.every((c) => IN.includes(c)), "every list read is in scope");
ok(idx.rows.every((r) => !r[10] || r[10].split(",").every((c) => IN.includes(c))), "maker's-document countries are in scope");

const door = /new Set\(\[([^\]]*)\]\)/.exec(readFileSync(join(root, "functions/index.js"), "utf-8"));
eq(door ? [...door[1].matchAll(/"([A-Z]{2})"/g)].map((m) => m[1]).sort() : null, IN, "front door country set");

const redir = readFileSync(join(here, "../public/_redirects"), "utf-8").split("\n").filter((l) => /^\/grid\/[a-z]{2}\/? /.test(l));
const want = OUT.flatMap((c) => [`/grid/${c.toLowerCase()}/ /grid/ 301`, `/grid/${c.toLowerCase()} /grid/ 301`]);
eq(redir.slice().sort(), want.slice().sort(), "_redirects block");

for (const c of IN) ok(existsSync(join(dist, "grid", c.toLowerCase(), "index.html")), `page /grid/${c.toLowerCase()}/ built`);
for (const c of OUT) ok(!existsSync(join(dist, "grid", c.toLowerCase())), `no page for /grid/${c.toLowerCase()}/`);

// no built page or sitemap entry points at a country the site no longer covers
const outRx = new RegExp(`(?:href="|<loc>[^<]*)/grid/(${OUT.map((c) => c.toLowerCase()).join("|")})/`);
let pages = 0;
const walk = (d) => { for (const e of readdirSync(d, { withFileTypes: true })) {
  const p = join(d, e.name);
  if (e.isDirectory()) walk(p);
  else if (e.name.endsWith(".html") || e.name.endsWith(".xml") || e.name.endsWith(".txt")) { pages++; const m = outRx.exec(readFileSync(p, "utf-8")); if (m) fail(`${p.slice(dist.length)} links to /grid/${m[1]}/`); }
} };
walk(dist);
checks++;
console.log(`${checks} checks over ${IN.length} countries in scope, ${OUT.length} out, ${pages} built files, ${fails} failures`);
process.exit(fails ? 1 : 0);
