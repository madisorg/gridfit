// Coverage of one country's view, model by model: how much of what a reader needs is there for every model the grid
// shows for that country. Five layers, each with one value per model (docs/coverage.md has the method):
//   a status    the grid cell (web/src/lib/grid-filter.js cellCode over dist/grid/index.json — what the page shows)
//   b checks    the country profile's must_meet rows (web/.data/checks.json, rebuilt as web/src/lib/checks.ts does)
//   c specs     rated kW (or kVA), phases, and the MPPT count on a model that takes PV (the grid index row)
//   d source    the strongest document behind the model: own list row, maker's document, datasheet, other list only
//   e legacy    tier A / B / C (web/src/lib/legacy.ts) or current
//
//     cd web && npm run build                      # writes dist/grid/index.json and .data/*.json
//     node tools/coverage/country.mjs --cc ee      # tables to stdout (markdown)
//     node tools/coverage/country.mjs --cc ee --json out.json --brands 30
//
// Reads only build outputs; changes nothing. The next country is the same command with another code.
import { readFileSync, writeFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { cellCode } from "../../web/src/lib/grid-filter.js";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
const CC = String(arg("--cc", "ee")).toUpperCase();
const NBR = Number(arg("--brands", 25));
const read = (p) => JSON.parse(readFileSync(resolve(ROOT, p), "utf-8"));
const index = read("web/dist/grid/index.json");
const reg = read("web/.data/registers.json");
const checks = read("web/.data/checks.json");

// ---- the index rows in the order web/src/pages/grid/index.json.ts writes them, joined back to the register device
const lc = (s) => s.toLowerCase();
const cmp = (a, b) => (a < b ? -1 : a > b ? 1 : 0);
const devs = reg.devices.filter((d) => !d.unmatched).sort((a, b) => b.n - a.n || cmp(lc(a.brand), lc(b.brand)) || cmp(lc(a.model), lc(b.model)));
if (devs.length !== index.rows.length) throw new Error(`index has ${index.rows.length} rows, registers ${devs.length} devices — rebuild web/ first`);
devs.forEach((d, i) => { if (index.rows[i][1] !== d.model) throw new Error(`row ${i}: ${index.rows[i][1]} != ${d.model}`); });

const STATUS = { Y: "on the list", C: "on the list with a condition", D: "likely fit (maker's document)", K: "possibly fit (other EU lists)",
  B: "over the type-A limit", "-": "nothing known", "?": "not confirmed", F: "nothing to approve", X: "refused / not allowed" };
const ownList = index.read.includes(CC);
const prof = checks.profiles[CC];
if (!prof) console.error(`no profile for ${CC}: layer b is empty`);
const PV = new Set(["inverter", "hybrid", "plug-in"]);
const POS = new Set(["listed", "restricted", "limited"]);

// ---- one record per model
const recs = devs.map((d, i) => {
  const row = index.rows[i];
  const status = cellCode(row, CC, index);
  // b: the check rows, as checks.ts rebuilds them
  let b = "no model-level requirement", rows = {}, nNote = 0, nBare = 0;
  const m = checks.models[d.brand + "|" + d.model];
  const r = m?.cc?.[CC];
  if (prof && r) {
    const na = new Set(r.na ?? []);
    const why = (r.listed ? prof.list?.not_carried : prof.on_application) ?? "";   // as web/src/lib/checks.ts words a plain row
    prof.items.forEach((it, k) => {
      if (na.has(k)) return;
      let st = "I", note = it.why ?? "";
      if (it.kind !== "none") { const x = r.rows?.[String(k)]; st = x ? x[0] : "N"; note = x ? (x[2] ?? "") : why; }
      rows[st] = (rows[st] ?? 0) + 1;
      if (st === "N") { if (note) nNote++; else nBare++; }
    });
    b = nBare ? "rows not shown, no reason" : nNote ? "every row answered or with a reason" : "every row answered";
  }
  // c: what the grid row carries (the lists' kVA and phases where a list states them, else the sheet)
  const kw = row[8] !== null, ph = !!row[7], pv = PV.has(d.cls), mppt = row[9] !== null;
  const c = kw && ph && (!pv || mppt) ? "kW, phases" + (pv ? ", MPPT" : "") : kw && ph ? "kW, phases; no MPPT" : kw ? "kW only" : ph ? "phases only" : "none";
  // the model-code level (row[12]), only where the list / datasheet level has no figure
  const ckw = !kw && row[12] && row[12][0] !== null, cph = !ph && row[12] && !!row[12][1];
  const cAny = (kw || ckw) && (ph || cph) ? (ckw || cph ? "kW and phases, some from the model code" : "kW and phases from a list or datasheet")
    : (kw || ckw) ? "kW only" + (ckw ? " (model code)" : "") : (ph || cph) ? "phases only" : "none";
  // d: the strongest source behind the model
  const own = (d.cells[CC] ?? []).length > 0;
  const doc = !!(r?.doc || r?.named?.length);
  const sheet = !!m?.sheet;
  const anyPos = Object.values(d.cells).flat().some((e) => POS.has(e.show));
  const dsrc = own ? "own list row" : doc ? "maker's document" : sheet ? "datasheet" : anyPos ? "other list (positive)" : "other list (expired / refused only)";
  const legacy = row[11] || "current";
  return { brand: index.brands[row[0]], model: d.model, cls: d.cls, status, b, rows, nBare, nNote, c, cAny, kw, ph, ckw, cph, pv, mppt, dsrc, sheet, doc, own, legacy };
});

// ---- tables
const by = (key, list = recs) => { const m = new Map(); for (const x of list) { const k = typeof key === "function" ? key(x) : x[key]; m.set(k, (m.get(k) ?? 0) + 1); } return m; };
const pct = (n, t) => (t ? `${Math.round((100 * n) / t)} %` : "–");
const out = [];
const h = (s) => out.push("", `### ${s}`, "");
const table = (head, rows) => { out.push(`| ${head.join(" | ")} |`, `|${head.map(() => "---").join("|")}|`); for (const r of rows) out.push(`| ${r.join(" | ")} |`); };
const N = recs.length;
out.push(`## ${CC} — ${N} models in the grid view (index of ${index.rows.length}; checks built ${checks.built})`);

h("a · status");
table(["status", "models", "share"], [...by("status")].sort((a, b) => b[1] - a[1]).map(([k, v]) => [`${STATUS[k] ?? k} (\`${k}\`)`, v, pct(v, N)]));
const none = recs.filter((x) => x.status === "-");
if (none.length) { out.push("", `"nothing known", by legacy tier and lists: ${[...by((x) => `${x.legacy}`, none)].map(([k, v]) => `${k} ${v}`).join(", ")}`); }

h("b · must_meet rows" + (prof ? ` (${prof.norm}, ${prof.items.length} items)` : ""));
const allRows = {}; let bare = 0, noted = 0;
for (const x of recs) { for (const [k, v] of Object.entries(x.rows)) allRows[k] = (allRows[k] ?? 0) + v; bare += x.nBare; noted += x.nNote; }
const tot = Object.values(allRows).reduce((a, b) => a + b, 0);
const SW = { S: "meets by datasheet", P: "range covers; set at commissioning", D: "meets by maker's document", O: "documented for an older edition", R: "checked by the operator's list",
  V: "within by the list's figure", W: "over a line by the list's figure", N: "not shown", L: "over a line: other procedure", X: "outside by datasheet", I: "no check" };
table(["row state", "rows", "share"], Object.entries(allRows).sort((a, b) => b[1] - a[1]).map(([k, v]) => [`${SW[k] ?? k} (\`${k}\`)`, v, pct(v, tot)]));
out.push("", `not shown: ${noted} with a reason, ${bare} without`, "");
table(["model", "models", "share"], [...by("b")].sort((a, b) => b[1] - a[1]).map(([k, v]) => [k, v, pct(v, N)]));

h("c · specs");
table(["what the row carries", "models", "share"], [...by("c")].sort((a, b) => b[1] - a[1]).map(([k, v]) => [k, v, pct(v, N)]));
out.push("", "with the model-code level (≈, display only):", "");
table(["kW and phases at some level", "models", "share"], [...by("cAny")].sort((a, b) => b[1] - a[1]).map(([k, v]) => [k, v, pct(v, N)]));
h("d · source");
table(["strongest source", "models", "share"], [...by("dsrc")].sort((a, b) => b[1] - a[1]).map(([k, v]) => [k, v, pct(v, N)]));
h("e · legacy");
table(["tier", "models", "share"], [...by("legacy")].sort((a, b) => b[1] - a[1]).map(([k, v]) => [k, v, pct(v, N)]));

// one line per group: the share of models that have each layer "at some level"
const atLevel = (x) => ({
  a: x.status !== "-" && x.status !== "?",
  b: x.b !== "rows not shown, no reason",
  c: x.kw && x.ph,
  cc: (x.kw || x.ckw) && (x.ph || x.cph),
  d: true, // every model in the view comes from at least one list row with its link; the column above says which
  e: true, // the tier is computed for every model; "current" is the default without a dated entry
  all: x.status !== "-" && x.status !== "?" && x.b !== "rows not shown, no reason" && x.kw && x.ph,
});
const groupTable = (title, keyFn, limit) => {
  h(title);
  const g = new Map();
  for (const x of recs) { const k = keyFn(x); if (!g.has(k)) g.set(k, []); g.get(k).push(x); }
  const rows = [...g].sort((a, b) => b[1].length - a[1].length).slice(0, limit ?? 999).map(([k, xs]) => {
    const n = xs.length, s = (f) => xs.filter((x) => atLevel(x)[f]).length;
    const st = by("status", xs);
    return [k, n, xs.filter((x) => x.own).length, ["Y", "C", "D", "K", "B", "-"].map((c) => st.get(c) ?? 0).join(" / "), pct(s("b"), n), pct(xs.filter((x) => x.b === "every row answered").length, n),
      pct(s("c"), n), pct(s("cc"), n), pct(xs.filter((x) => x.pv && x.mppt).length, xs.filter((x) => x.pv).length), pct(xs.filter((x) => x.sheet || x.doc).length, n), pct(s("all"), n)];
  });
  table(["group", "models", "on own list", "Y / C / D / K / B / –", "b: no bare row", "b: all answered", "c: kW + phases", "c: … with model code", "c: MPPT (PV)", "d: sheet or document", "a+b+c"], rows);
};
groupTable("by class", (x) => x.cls);
groupTable(`by brand (largest ${NBR})`, (x) => x.brand, NBR);
if (ownList) groupTable(`brands on the ${CC} list (largest ${NBR}, models on the list only)`, (x) => (x.own ? x.brand : "(not on the list)"), NBR + 1);

console.log(out.join("\n"));
const jsonOut = arg("--json");
if (jsonOut) {
  const summary = { cc: CC, built: checks.built, models: N, status: Object.fromEntries(by("status")), rows: allRows, notShown: { reason: noted, bare },
    b: Object.fromEntries(by("b")), c: Object.fromEntries(by("c")), cAny: Object.fromEntries(by("cAny")), d: Object.fromEntries(by("dsrc")), e: Object.fromEntries(by("legacy")) };
  writeFileSync(jsonOut, JSON.stringify({ summary, models: recs }, null, 0));
}
