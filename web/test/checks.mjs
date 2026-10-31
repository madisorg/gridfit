// Proves the requirement check adds up (web/.data/checks.json, written by tools/check/run.py): for every model and
// country the states sum to the applicable items, every "meets / outside by datasheet" row carries the number it was
// judged on, "outside" never appears without a datasheet row, and the worked example holds — ABB/FIMER TRIO-8.5-TL-OUTD
// in Italy: 6 rows by the datasheet, 8 by the maker's declaration, which cites CEI 0-21:2022-03 + V1 + V2 against the
// profile's 2026-07 edition, so the items changed in 2026-07 are unverified.
//
//     node web/test/checks.mjs            (after `npm run build` in web/, or `python tools/check/run.py`)
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const C = JSON.parse(readFileSync(resolve(here, "../.data/checks.json"), "utf-8"));
let fails = 0, checks = 0;
const fail = (m) => { fails++; console.log("FAIL", m); };
const eq = (a, b, m) => { checks++; if (a !== b) fail(`${m}: ${JSON.stringify(a)} ≠ ${JSON.stringify(b)}`); };
const ok = (c, m) => { checks++; if (!c) fail(m); };

const ccs = Object.keys(C.profiles);
ok(ccs.length >= 3, "at least three profiles");
for (const cc of ccs) {
  const p = C.profiles[cc];
  ok(/^20\d\d-\d\d$/.test(p.edition.date), `${cc}: edition date`);
  const ids = p.items.map((x) => x.id);
  eq(new Set(ids).size, ids.length, `${cc}: item ids unique`);
}
let models = 0, sheetAny = {}, covered = {}, outside = {};
for (const [key, m] of Object.entries(C.models)) {
  models++;
  for (const cc of ccs) {
    const r = m.cc[cc];
    ok(r, `${key} ${cc}: entry`);
    if (!r) continue;
    const items = C.profiles[cc].items;
    const na = new Set(r.na ?? []);
    const applicable = items.filter((_, i) => !na.has(i)).length;
    const sum = Object.values(r.sum).reduce((a, b) => a + b, 0);
    eq(sum, applicable, `${key} ${cc}: states sum to the applicable items`);
    for (const [i, row] of Object.entries(r.rows ?? {})) {
      ok(!na.has(Number(i)), `${key} ${cc}: row ${i} is applicable`);
      ok(items[i].kind !== "none", `${key} ${cc}: a kind-none item has no stored row`);
      if (row[0] === "S" || row[0] === "X") ok(row[1] && m.sheet, `${key} ${cc}: ${items[i].id} ${row[0]} carries the sheet's number`);
      if (row[0] === "D" || row[0] === "O") ok(r.doc, `${key} ${cc}: ${items[i].id} ${row[0]} has a document`);
      if (row[0] === "O") ok(items[i].changed_in && r.doc.edition < items[i].changed_in, `${key} ${cc}: ${items[i].id} is older than the change`);
    }
    if (r.sum.X) ok(m.sheet, `${key} ${cc}: outside only with a datasheet`);
    if (r.sum.S || r.sum.X) sheetAny[cc] = (sheetAny[cc] ?? 0) + 1;
    if (!r.sum.N) covered[cc] = (covered[cc] ?? 0) + 1;
    if (r.sum.X) outside[cc] = (outside[cc] ?? 0) + 1;
  }
}
for (const cc of ccs) {
  eq(sheetAny[cc] ?? 0, C.stats[cc].sheet_any, `${cc}: sheet_any stat`);
  eq(covered[cc] ?? 0, C.stats[cc].covered, `${cc}: covered stat`);
  eq(outside[cc] ?? 0, C.stats[cc].outside, `${cc}: outside stat`);
}

// the worked example
const trio = C.models["ABB|TRIO-8.5-TL-OUTD"];
ok(trio, "ABB TRIO-8.5-TL-OUTD is a register model with checks");
if (trio) {
  const it = trio.cc.IT, items = C.profiles.IT.items, id = (i) => items[i].id;
  eq(it.sum.S ?? 0, 6, "TRIO × IT: by datasheet");
  eq((it.sum.D ?? 0) + (it.sum.O ?? 0), 8, "TRIO × IT: by the maker's document");
  eq(it.sum.N ?? 0, 0, "TRIO × IT: nothing not shown");
  eq(it.sum.X ?? 0, 0, "TRIO × IT: nothing outside");
  eq(it.doc?.edition, "2024-01", "TRIO × IT: the declaration's newest cited variant is V2:2024-01");
  eq(C.profiles.IT.edition.id, "2026-07", "IT profile edition");
  eq(it.doc?.older, true, "TRIO × IT: documented for an older edition");
  const old = Object.entries(it.rows).filter(([, r]) => r[0] === "O").map(([i]) => id(i)).sort();
  eq(old.join(","), "p-of-u,spi-settings", "TRIO × IT: the two 2026-07 items are unverified");
  const sheet = Object.entries(it.rows).filter(([, r]) => r[0] === "S").map(([i]) => id(i)).sort();
  eq(sheet.join(","), "freq-range,phases,power-class,reactive,spi-integrated,voltage-range", "TRIO × IT: the six datasheet rows");
  eq((it.na ?? []).map(id).join(","), "storage", "TRIO × IT: storage does not apply to a PV inverter");
  eq(trio.cc.ES.doc, undefined, "TRIO × ES: no Spanish document");
  ok((trio.cc.ES.sum.S ?? 0) >= 2, "TRIO × ES: the datasheet still answers the numeric rows");
}
// an honest "outside": a single-phase unit over 6 kW in Italy, judged on its sheet
const one = Object.entries(C.models).find(([, m]) => m.cc.IT.rows && Object.values(m.cc.IT.rows).some((r) => r[0] === "X" && /1-phase/.test(r[1])));
ok(one, "an 8 kW single-phase unit is outside the Italian phase rule by its datasheet");

console.log(`${checks} checks, ${fails} failures · ${models} models × ${ccs.length} countries`);
for (const cc of ccs) console.log(`${cc}: datasheet row ${C.stats[cc].sheet_any} · every item covered ${C.stats[cc].covered} · document ${C.stats[cc].doc} (older edition ${C.stats[cc].older}) · outside ${C.stats[cc].outside}`);
process.exit(fails ? 1 : 0);
