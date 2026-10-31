// The grid view's filter logic, shared by the page script (GridView.astro) and the count test
// (web/test/facets.mjs), so what the page shows is what the test proves: every filter is a partition —
// the "Any" count equals the sum of its options, always — and a model's status in a country is one
// category, never a silent gap. Plain JS so Node runs it without a build.
//
// Row shape (web/src/pages/grid/index.json.ts): [brandIdx, model, cls, url, cells, marks, family, phases, kva, mppt, doc]
//   cells: one letter per read list — L listed, R restricted, T time-limited, O other, P end date passed,
//          E expired, N refused, - not on the list;  marks: Home Assistant + evcc, W/L/C/B/-;
//   phases: "1" | "2" | "3" | "";  kva: number | null;  mppt: number | null (0 = the sheet says none);
//   doc: country codes the maker's own document releases the model for, comma-joined, or "".

// ---- one status per model × country. Best → worst; "every chosen country" takes the worst.
export const ORDER = ["Y", "C", "F", "D", "K", "B", "?", "-", "X"];
const LIST_GROUP = { L: "Y", O: "Y", R: "C", T: "C", P: "X", E: "X", N: "X" };
const POSITIVE = "LORT";
export const KIND_OF = { inverter: "inv", hybrid: "inv", battery: "inv", "plug-in": "inv", wallbox: "ev" };

export function cellCode(row, cc, data) {
  const i = data.read.indexOf(cc);
  if (i >= 0) { const s = row[4][i]; return s === "-" ? "-" : LIST_GROUP[s]; }
  const st = data.scope[cc]?.[row[2]] ?? "unknown";
  if (st === "banned") return "X";
  if (st === "free") return "F";
  // the maker's document first (it outranks "not confirmed"), then the type-A limit, then what other EU lists say
  if (row[10] && row[10].split(",").includes(cc)) return "D";
  if (st === "unknown") return "?";
  const lim = data.limits?.[cc]?.max_kw;
  if (lim && row[8] !== null && row[8] > lim) return "B";
  if ([...row[4]].some((ch) => POSITIVE.includes(ch))) return "K";
  return "-";
}
export const rank = (code) => ORDER.indexOf(code);
export function rowStatus(row, ccs, every, data) {
  let out = every ? "Y" : "X";
  for (const cc of ccs) {
    const c = cellCode(row, cc, data);
    if (every ? rank(c) > rank(out) : rank(c) < rank(out)) out = c;
  }
  return out;
}
// the lists a model has an entry on, besides the chosen read lists (any status: it is a listing, not an approval)
export const otherLists = (row, readSel, data) => [...row[4]].filter((ch, i) => ch !== "-" && !readSel.includes(data.read[i])).length;
export const positiveLists = (row, data) => data.read.filter((c, i) => POSITIVE.includes(row[4][i]));

// ---- the partitions behind the selects. Each option value maps a row to exactly one value.
export const BUCKETS = [["0-3.7", 0, 3.7], ["3.7-6", 3.7, 6], ["6-12", 6, 12], ["12-30", 12, 30], ["30-", 30, Infinity]];
export const kvaCat = (row) => row[8] === null ? "-" : (BUCKETS.find(([, lo, hi]) => row[8] > lo && row[8] <= hi) ?? ["-"])[0];
export const mpptCat = (row) => row[9] !== null ? (row[9] === 0 ? "0" : row[9] >= 4 ? "4" : String(row[9])) : (row[2] === "battery" || row[2] === "wallbox" ? "0" : "-");
export const phCat = (row) => row[7] || "-";
const best = (a, b) => "WLCB-".indexOf(a) <= "WLCB-".indexOf(b) ? a : b;
export const loCat = (row) => best(row[5][0], row[5][1]);
export const nCat = (row, readSel, data) => { const n = otherLists(row, readSel, data); return n >= 3 ? "3" : String(n); };

// ---- the filters: one predicate per id, over the current values
export const IDS = ["st", "ph", "kva", "mppt", "brand", "n", "lo", "ha", "ev", "q"];
export function predicates(data, ctx) {
  const { ccs, every, readSel } = ctx;
  return {
    st: (r, v) => !v || v.includes(rowStatus(r, ccs, every, data)),
    ph: (r, v) => !v || phCat(r) === v,
    kva: (r, v) => !v || kvaCat(r) === v,
    mppt: (r, v) => !v || mpptCat(r) === v,
    brand: (r, v) => !v || data.brands[r[0]] === v,
    n: (r, v) => !v || nCat(r, readSel, data) === v,
    lo: (r, v) => !v || loCat(r) === v,
    ha: (r, v) => !v || r[5][0] === v,
    ev: (r, v) => !v || r[5][1] === v,
    q: (r, v) => !v || (data.brands[r[0]] + " " + r[1] + " " + r[6]).toLowerCase().includes(v),
  };
}
export const kindOk = (r, g) => !g || KIND_OF[r[2]] === g;

// the rows that pass every filter but `skip` (the facet base), and the full result when skip is ""
export function select(data, cur, g, T, skip = "") {
  return data.rows.filter((r) => kindOk(r, g) && IDS.every((id) => id === skip || T[id](r, cur[id])));
}
// counts per option value of one filter over its base — one pass, keyed by category
export function facet(id, base, data, ctx) {
  const m = new Map();
  const cat = id === "st" ? (r) => rowStatus(r, ctx.ccs, ctx.every, data) : id === "ph" ? phCat : id === "kva" ? kvaCat : id === "mppt" ? mpptCat
    : id === "brand" ? (r) => data.brands[r[0]] : id === "n" ? (r) => nCat(r, ctx.readSel, data) : id === "lo" ? loCat : id === "ha" ? (r) => r[5][0] : (r) => r[5][1];
  for (const r of base) { const k = cat(r); m.set(k, (m.get(k) ?? 0) + 1); }
  return m;
}
