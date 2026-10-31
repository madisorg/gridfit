// Proves the grid view's counts add up: for every filter, in every state tried, the "Any" count equals the sum
// of its options, and the status group's counts sum to the base — every model lands in exactly one category,
// never a silent gap. Runs over the built index (web/dist/grid/index.json) with the page's own logic
// (web/src/lib/grid-filter.js), so what is proved is what is shown.
//
//     node web/test/facets.mjs            (after `npm run build` in web/)
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { IDS, ORDER, predicates, select, facet, cellCode } from "../src/lib/grid-filter.js";

const here = dirname(fileURLToPath(import.meta.url));
const data = JSON.parse(readFileSync(resolve(here, "../dist/grid/index.json"), "utf-8"));
const OPTIONS = {
  ph: ["1", "2", "3", "-"], kva: ["0-3.7", "3.7-6", "6-12", "12-30", "30-", "-"], mppt: ["1", "2", "3", "4", "0", "-"],
  n: ["0", "1", "2", "3"], lo: ["W", "L", "C", "B", "-"], ha: ["W", "L", "C", "B", "-"], ev: ["W", "L", "C", "B", "-"], st: ORDER, legacy: ["0", "1"],
};
const empty = Object.fromEntries(IDS.map((id) => [id, ""]));
// the states a reader reaches: no country, one list country, one no-list country, several, the kinds, a brand, a search
const STATES = [
  { name: "no country", cs: [], g: "" }, { name: "EE", cs: ["EE"], g: "inv" }, { name: "ES", cs: ["ES"], g: "inv" }, { name: "AT", cs: ["AT"], g: "inv" },
  { name: "DE (list, not read)", cs: ["DE"], g: "inv" }, { name: "FI wallboxes", cs: ["FI"], g: "ev" }, { name: "AT+EE", cs: ["AT", "EE"], g: "inv" },
  { name: "AT+EE every", cs: ["AT", "EE"], g: "inv", every: true }, { name: "ES+FR+IT every", cs: ["ES", "FR", "IT"], g: "inv", every: true },
  { name: "SE wallboxes", cs: ["SE"], g: "ev" }, { name: "EE, Deye", cs: ["EE"], g: "inv", cur: { brand: "Deye" } },
  { name: "ES, status D", cs: ["ES"], g: "inv", cur: { st: "D" } }, { name: "ES, 3-phase 6-12 kVA, search sun", cs: ["ES"], g: "inv", cur: { ph: "3", kva: "6-12", q: "sun" } },
  { name: "no country, status X, HA local control", cs: [], g: "", cur: { st: "X", ha: "W" } }, { name: "EE wallboxes (nothing to check)", cs: ["EE"], g: "ev" },
  { name: "AT with legacy included", cs: ["AT"], g: "inv", cur: { legacy: "1" } }, { name: "AT, search 'symo' (legacy shown by search)", cs: ["AT"], g: "inv", cur: { q: "symo" } },
];
let fails = 0, checks = 0;
const fail = (m) => { fails++; console.log("FAIL", m); };
for (const s of STATES) {
  const ccs = s.cs.length ? s.cs : data.read, readSel = s.cs.filter((c) => data.read.includes(c)), every = !!s.every && s.cs.length >= 2;
  const cur = { ...empty, ...(s.cur ?? {}) }, ctx = { ccs, every, readSel, q: cur.q }, T = predicates(data, ctx);
  const hits = select(data, cur, s.g, T);
  for (const id of IDS) {
    if (id === "q" || id === "brand") continue;
    const base = select(data, cur, s.g, T, id), counts = facet(id, base, data, ctx);
    const sum = OPTIONS[id].reduce((a, v) => a + (counts.get(v) ?? 0), 0);
    checks++;
    if (sum !== base.length) fail(`${s.name} · ${id}: any ${base.length} ≠ sum ${sum} (${[...counts].map(([k, v]) => `${k}:${v}`).join(" ")})`);
    for (const k of counts.keys()) if (!OPTIONS[id].includes(k)) fail(`${s.name} · ${id}: category "${k}" has no option`);
    if (id === "legacy") {
      // a toggle, not a partition of choices: off leaves the current rows (unless a search text shows everything), on leaves them all
      checks++; const off = select(data, { ...cur, legacy: "" }, s.g, T).length, on = select(data, { ...cur, legacy: "1" }, s.g, T).length;
      if (on !== base.length) fail(`${s.name} · legacy on: ${on} ≠ base ${base.length}`);
      if (off !== (cur.q ? base.length : counts.get("0") ?? 0)) fail(`${s.name} · legacy off: ${off} ≠ ${cur.q ? base.length : counts.get("0")}`);
      continue;
    }
    // and each option really is the filter: choosing it leaves exactly its count
    for (const v of OPTIONS[id]) { checks++; const n = select(data, { ...cur, [id]: v }, s.g, T).length; if (n !== (counts.get(v) ?? 0)) fail(`${s.name} · ${id}=${v}: option says ${counts.get(v) ?? 0}, choosing it gives ${n}`); }
  }
  // brands: one count per brand, the sum is the base
  { const base = select(data, cur, s.g, T, "brand"), counts = facet("brand", base, data, ctx); checks++;
    const sum = [...counts.values()].reduce((a, b) => a + b, 0); if (sum !== base.length) fail(`${s.name} · brand: any ${base.length} ≠ sum ${sum}`); }
  console.log(`ok  ${s.name}: ${hits.length} models`);
}
// every cell has a code the legend names
const CODES = new Set(ORDER);
for (const r of data.rows) for (const cc of Object.keys(data.names)) { const c = cellCode(r, cc, data); if (!CODES.has(c)) fail(`cell code "${c}" for ${data.brands[r[0]]} ${r[1]} in ${cc}`); }
checks++;
// the no-list story: in Spain most inverters get a better answer than "nothing known"
const es = data.rows.filter((r) => r[2] !== "wallbox").map((r) => cellCode(r, "ES", data));
const tally = Object.fromEntries(ORDER.map((k) => [k, es.filter((c) => c === k).length]));
console.log("ES inverters by status:", tally);
const leg = data.rows.filter((r) => r[11]).length, legX = data.rows.filter((r) => r[11] === "A" && [...r[4]].some((ch) => "LORT".includes(ch))).length;
console.log(`legacy rows: ${leg} (A ${data.rows.filter((r) => r[11] === "A").length}, B ${data.rows.filter((r) => r[11] === "B").length}, C ${data.rows.filter((r) => r[11] === "C").length})`);
if (legX) fail(`${legX} tier-A legacy rows still have a positive list entry`);
if ((tally["-"] ?? 0) > es.length * 0.1) fail(`ES: ${tally["-"]} of ${es.length} inverters are "nothing known"`);
console.log(`${checks} checks, ${fails} failures`);
process.exit(fails ? 1 : 0);
