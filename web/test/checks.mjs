// Proves the requirement check adds up (web/.data/checks.json, written by tools/check/run.py): for every model and
// country the states sum to the applicable items, every "meets / outside by datasheet" row carries the number it was
// judged on, "outside" never appears without a datasheet row, and the worked example holds — ABB/FIMER TRIO-8.5-TL-OUTD
// in Italy: 7 rows by the datasheet, 9 by the maker's declaration, which cites CEI 0-21:2022-03 + V1 + V2 against the
// profile's 2026-07 edition, so the items changed in 2026-07 are unverified. A second run over a test fixture
// (tools/check/fixtures/gr: Greece × GoodWe GW10K-ET-20) proves what the schema must carry beyond Italy: several kW/A
// lines with different meanings, operator-set protection values, datasheet fields the operator asks for, and a generic
// EN 50549-1 certificate as the evidence the country accepts.
//
//     node web/test/checks.mjs            (npm test runs the fixture first; or python tools/check/run.py by hand)
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const C = JSON.parse(readFileSync(resolve(here, "../.data/checks.json"), "utf-8"));
const F = JSON.parse(readFileSync(resolve(here, "../.data/checks-fixture.json"), "utf-8"));
const LINES = new Set(["rfg-type", "procedure", "emc-class", "protection"]);
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
let models = 0, sheetAny = {}, covered = {}, outside = {}, overLine = {};
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
      if ("SPLX".includes(row[0])) ok(row[1] && m.sheet, `${key} ${cc}: ${items[i].id} ${row[0]} carries the sheet's number`);
      if (row[0] === "P") ok(items[i].kind === "settable", `${key} ${cc}: ${items[i].id} set at commissioning only for an operator-set item`);
      if (row[0] === "L") ok(LINES.has(items[i].meaning), `${key} ${cc}: ${items[i].id} over a line only where the line has that meaning`);
      if (row[0] === "X") ok(!LINES.has(items[i].meaning), `${key} ${cc}: ${items[i].id} a procedure line is never "outside"`);
      if (row[0] === "D" || row[0] === "O") ok(r.doc, `${key} ${cc}: ${items[i].id} ${row[0]} has a document`);
      if (row[0] === "O") ok(items[i].changed_in && r.doc.edition < items[i].changed_in, `${key} ${cc}: ${items[i].id} is older than the change`);
    }
    if (r.sum.X) ok(m.sheet, `${key} ${cc}: outside only with a datasheet`);
    if (r.doc && C.profiles[cc].accepts.includes("national-declaration") && !C.profiles[cc].accepts.includes("generic-en50549-1"))
      // generic = every standard it cites is an EN 50549 / EN 50438 edition (national adoptions included); a certificate
      // that cites the country's own rule beside EN 50549-1 (Deye's C10/11 certificate, Sungrow's PPDS declaration) is national
      ok(!r.doc.standards.split(/;\s*/).every((s) => /^(?:[A-ZČ-]+ )?(?:NBN |NEN-|SS-|ČSN )?EN 50(549|438)/.test(s)),
        `${key} ${cc}: a generic certificate does not count where the operator wants the national one`);
    if (r.sum.S || r.sum.P || r.sum.L || r.sum.X) sheetAny[cc] = (sheetAny[cc] ?? 0) + 1;
    if (r.sum.L) overLine[cc] = (overLine[cc] ?? 0) + 1;
    if (!r.sum.N) covered[cc] = (covered[cc] ?? 0) + 1;
    if (r.sum.X) outside[cc] = (outside[cc] ?? 0) + 1;
  }
}
for (const cc of ccs) {
  eq(sheetAny[cc] ?? 0, C.stats[cc].sheet_any, `${cc}: sheet_any stat`);
  eq(covered[cc] ?? 0, C.stats[cc].covered, `${cc}: covered stat`);
  eq(outside[cc] ?? 0, C.stats[cc].outside, `${cc}: outside stat`);
  eq(overLine[cc] ?? 0, C.stats[cc].over_line, `${cc}: over-a-line stat`);
}

// the worked example
const trio = C.models["ABB|TRIO-8.5-TL-OUTD"];
ok(trio, "ABB TRIO-8.5-TL-OUTD is a register model with checks");
if (trio) {
  const it = trio.cc.IT, items = C.profiles.IT.items, id = (i) => items[i].id;
  eq(it.sum.S ?? 0, 7, "TRIO × IT: by datasheet");
  eq((it.sum.D ?? 0) + (it.sum.O ?? 0), 9, "TRIO × IT: by the maker's document");
  eq(it.sum.N ?? 0, 0, "TRIO × IT: nothing not shown");
  eq(it.sum.X ?? 0, 0, "TRIO × IT: nothing outside");
  eq(it.doc?.edition, "2024-01", "TRIO × IT: the declaration's newest cited variant is V2:2024-01");
  eq(C.profiles.IT.edition.id, "2026-07", "IT profile edition");
  eq(it.doc?.older, true, "TRIO × IT: documented for an older edition");
  const old = Object.entries(it.rows).filter(([, r]) => r[0] === "O").map(([i]) => id(i)).sort();
  eq(old.join(","), "p-of-u,spi-settings", "TRIO × IT: the two 2026-07 items are unverified");
  const sheet = Object.entries(it.rows).filter(([, r]) => r[0] === "S").map(([i]) => id(i)).sort();
  eq(sheet.join(","), "backup-ddi,freq-range,phases,power-class,reactive,spi-integrated,voltage-range", "TRIO × IT: the seven datasheet rows");
  eq((it.na ?? []).map(id).join(","), "storage", "TRIO × IT: storage does not apply to a PV inverter");
  eq(trio.cc.ES.doc, undefined, "TRIO × ES: no Spanish document");
  ok((trio.cc.ES.sum.S ?? 0) >= 2, "TRIO × ES: the datasheet still answers the numeric rows");
}
// the fixture: Greece × GoodWe GW10K-ET-20 (real sheet and certificate) and an invented single-phase 6 kW unit
{
  const items = F.profiles.GR.items, id = (i) => items[i].id;
  const byState = (r, st) => Object.entries(r.rows ?? {}).filter(([, x]) => x[0] === st).map(([i]) => id(i)).sort().join(",");
  const g = F.models["GoodWe|GW10K-ET-20"]?.cc.GR;
  ok(g, "fixture: GW10K-ET-20 × GR");
  if (g) {
    eq(JSON.stringify(g.sum), JSON.stringify({ S: 5, P: 2, D: 3, N: 3 }), "GW10K × GR: 5 datasheet, 2 set at commissioning, 3 certificate, 3 not shown");
    eq(byState(g, "S"), "emc-class,freq-range,notification-3ph,rfg-type,sheet-thdi", "GW10K × GR: the datasheet rows (three lines of three meanings)");
    eq(byState(g, "P"), "protection-frequency,protection-voltage", "GW10K × GR: protection values the operator sets");
    eq(byState(g, "D"), "lfsm-o,reconnection,rocof", "GW10K × GR: the EN 50549-1 certificate covers the type-tested rows");
    eq(g.doc?.cert_no, "A3 50588989 0001", "GW10K × GR: the TÜV certificate");
    eq((g.na ?? []).map(id).join(","), "notification-1ph", "GW10K × GR: the single-phase line does not apply to a three-phase unit");
  }
  const one = F.models["Synthetic|ONE-PHASE-6K"]?.cc.GR;
  ok(one, "fixture: the single-phase unit");
  if (one) {
    eq(byState(one, "L"), "emc-class,notification-1ph", "single-phase 6 kW × GR: over the 5 kW notification line and the 16 A EMC line — other procedures, not a breach");
    eq(one.sum.X ?? 0, 0, "single-phase 6 kW × GR: nothing outside");
    eq((one.na ?? []).map(id).join(","), "notification-3ph", "single-phase 6 kW × GR: the three-phase line does not apply");
    eq(one.doc, undefined, "single-phase 6 kW × GR: no document");
  }
}
// an honest "outside": a single-phase unit over 6 kW in Italy, judged on its sheet
const one = Object.entries(C.models).find(([, m]) => m.cc.IT.rows && Object.values(m.cc.IT.rows).some((r) => r[0] === "X" && /1-phase/.test(r[1])));
ok(one, "an 8 kW single-phase unit is outside the Italian phase rule by its datasheet");

console.log(`${checks} checks, ${fails} failures · ${models} models × ${ccs.length} countries`);
for (const cc of ccs) console.log(`${cc}: datasheet row ${C.stats[cc].sheet_any} · every item covered ${C.stats[cc].covered} · document ${C.stats[cc].doc} (older edition ${C.stats[cc].older}) · outside ${C.stats[cc].outside}`);
process.exit(fails ? 1 : 0);
