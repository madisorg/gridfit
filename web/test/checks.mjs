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
import { readFileSync, readdirSync } from "node:fs";
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
// the items a country's list stands in for: read back from the profile file, not from the engine's output
import yaml from "yaml";
const LISTS = {};
const listItems = (cc) => (LISTS[cc] ??= new Set(yaml.parse(readFileSync(resolve(here, `../../data/profiles/${cc.toLowerCase()}.yaml`), "utf-8")).list_checks?.items ?? []));
let models = 0, sheetAny = {}, covered = {}, outside = {}, overLine = {}, listedN = {};
for (const [key, m] of Object.entries(C.models)) {
  models++;
  // a charging point has a block only in a country with an item written for one (Italy's Allegato X)
  const charger = Object.keys(m.cc).every((cc) => C.profiles[cc].items.some((it) => it.applies?.classes?.includes("wallbox")));
  for (const cc of ccs) {
    const r = m.cc[cc];
    ok(r || charger, `${key} ${cc}: entry`);
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
      if (row[0] === "O") ok(r.doc.withdrawn || (items[i].changed_in && r.doc.edition < items[i].changed_in), `${key} ${cc}: ${items[i].id} is older than the change`);
      // the list's figure: a power line on a listed model, worded from the list, never where the sheet states the field
      if (row[0] === "V" || row[0] === "W") ok(r.listed && LINES.has(items[i].meaning) && ["ac_kw", "ac_kva"].includes(items[i].field) && /^the list: /.test(row[1] ?? ""),
        `${key} ${cc}: ${items[i].id} ${row[0]} is a listed model's power line, worded from the list`);
      if (row[0] === "W") ok(!/ within /.test(row[1]), `${key} ${cc}: ${items[i].id} W says over`);
      // checked by the operator's list: only on a model the country's own list admits, only for an item the profile names
      if (row[0] === "R") ok(r.listed && (C.profiles[cc].list ? true : false) && listItems(cc).has(items[i].id), `${key} ${cc}: ${items[i].id} R only for a listed model and a list item`);
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
    if (r.sum.R) listedN[cc] = (listedN[cc] ?? 0) + 1;
    if (r.sum.R) ok(r.listed, `${key} ${cc}: R rows only with the listed flag`);
  }
}
for (const cc of ccs) {
  eq(sheetAny[cc] ?? 0, C.stats[cc].sheet_any, `${cc}: sheet_any stat`);
  eq(covered[cc] ?? 0, C.stats[cc].covered, `${cc}: covered stat`);
  eq(outside[cc] ?? 0, C.stats[cc].outside, `${cc}: outside stat`);
  eq(overLine[cc] ?? 0, C.stats[cc].over_line, `${cc}: over-a-line stat`);
  eq(listedN[cc] ?? 0, C.stats[cc].listed, `${cc}: checked-by-the-list stat`);
  // a country whose profile words both cases (on its list / off it) leaves no "not shown" row without a reason
  if (C.profiles[cc].list && C.profiles[cc].on_application) eq(C.stats[cc].bare, 0, `${cc}: every "not shown" row says why`);
}
// Estonia: every model on Elektrilevi's list, in a class the profile checks, has its list items checked by the list
{
  const reg = JSON.parse(readFileSync(resolve(here, "../.data/registers.json"), "utf-8"));
  const onList = reg.devices.filter((d) => !d.unmatched && ["inverter", "hybrid", "battery", "plug-in"].includes(d.cls) && (d.cells.EE ?? []).some((e) => ["listed", "restricted", "limited"].includes(e.show)));
  eq(C.stats.EE.listed, onList.length, "EE: every listed model is checked by the list");
  const lst = listItems("EE"), items = C.profiles.EE.items;
  for (const d of onList.slice(0, 400)) {
    const r = C.models[d.brand + "|" + d.model].cc.EE, na = new Set(r.na ?? []);
    for (const [i, it] of items.entries()) if (lst.has(it.id) && !na.has(i)) ok(["S", "P", "L", "X", "R"].includes(r.rows?.[String(i)]?.[0]), `${d.brand} ${d.model} EE: ${it.id} answered by sheet or list`);
  }
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
  eq((it.na ?? []).map(id).join(","), "storage,charging-controller", "TRIO × IT: storage and the charging-point item do not apply to a PV inverter");
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
// engine round 2 on the real data
{
  const reg = JSON.parse(readFileSync(resolve(here, "../.data/registers.json"), "utf-8"));
  const POS = ["listed", "restricted", "limited"];
  const idx = (cc, id) => C.profiles[cc].items.findIndex((x) => x.id === id);
  const row = (key, cc, id) => { const r = C.models[key]?.cc?.[cc]; const i = idx(cc, id); return r ? ((r.na ?? []).includes(i) ? ["-"] : r.rows?.[String(i)] ?? ["N"]) : null; };
  const listed = (cc, pred) => reg.devices.filter((d) => !d.unmatched && ["inverter", "hybrid", "battery", "plug-in"].includes(d.cls) && C.models[d.brand + "|" + d.model]
    && pred((d.cells[cc] ?? []).filter((e) => POS.includes(e.show))));
  // 1. the list's figure (AT, SE): weaker than the sheet, so a sheet still wins — Sunways STT-40KTL is 45 kW on Rikta Rätt, 40 kW on its sheet
  eq(row("Sunways|STT-40KTL", "SE", "power-class")?.join("|"), "S|40 kW — within 1500 kW", "Sunways STT-40KTL × SE: the sheet's 40 kW, not the list's 45");
  eq(row("Sunways|STT-40KTL", "SE", "micro-producer")?.[0], "S", "Sunways STT-40KTL × SE: micro-producer line by the sheet");
  ok(C.stats.AT.list_figure > 2000 && C.stats.SE.list_figure > 2000, `AT ${C.stats.AT.list_figure} and SE ${C.stats.SE.list_figure} models answered by the list's figure`);
  eq(C.stats.BE.list_figure ?? 0, 0, "BE: Synergrid's figures are not used (personal-use terms)");
  // 2. list_checks by the list row: NL storage from the storage file only, PL RoCoF from a WOS 2025 row only, CZ A2 items by VM category
  eq(row("Anker|X1-H5K-T", "NL", "storage")?.[0], "N", "Anker X1-H5K-T × NL (generation file only): storage not shown");
  ok(/generating units only/.test(row("Anker|X1-H5K-T", "NL", "storage")?.[2] ?? ""), "Anker X1-H5K-T × NL: the reason names the generation file");
  eq(row("Afore|AF3K-TH", "NL", "storage")?.[0], "R", "Afore AF3K-TH × NL (both files): storage checked by the list");
  const wos = (es, y) => es.some((e) => (e.extra?.wos ?? "").includes("WOS " + y));
  const pl25 = listed("PL", (es) => wos(es, 2025)), pl18 = listed("PL", (es) => es.length && !wos(es, 2025) && wos(es, 2018));
  ok(pl25.length > 1000 && pl18.length > 100, `PL: ${pl25.length} models with a WOS 2025 row, ${pl18.length} with WOS 2018 rows only`);
  ok(pl25.every((d) => row(d.brand + "|" + d.model, "PL", "rocof")?.[0] === "R"), "PL: every model with a WOS 2025 row has RoCoF checked by the list");
  ok(pl18.every((d) => row(d.brand + "|" + d.model, "PL", "rocof")?.[0] !== "R"), "PL: no WOS 2018-only model has RoCoF checked by the list");
  const a2 = listed("CZ", (es) => es.length && es.every((e) => /A2/.test(e.extra?.category ?? ""))), a1 = listed("CZ", (es) => es.length && !es.some((e) => /A2/.test(e.extra?.category ?? "")));
  ok(a2.length > 500 && a1.length > 10, `CZ: ${a2.length} models of an A2 category, ${a1.length} without`);
  for (const id of ["power-recovery", "power-reduction-input"]) {
    ok(a2.every((d) => ["R", "-"].includes(row(d.brand + "|" + d.model, "CZ", id)?.[0])), `CZ: ${id} checked by the list on every A2-category model where it applies`);
    ok(a1.every((d) => row(d.brand + "|" + d.model, "CZ", id)?.[0] !== "R"), `CZ: ${id} never checked by the list without category A2`);
  }
  // 3. Italian charging points: CEI 0-21 Allegato X from 1 January 2027, and no generator item
  const wb = reg.devices.filter((d) => !d.unmatched && d.cls === "wallbox" && C.models[d.brand + "|" + d.model]);
  ok(wb.length > 400, `IT: ${wb.length} charging points have a block`);
  const before27 = C.built < "2027-01-01";
  for (const d of wb) {
    const r = C.models[d.brand + "|" + d.model].cc;
    eq(Object.keys(r).join(","), "IT", `${d.brand} ${d.model}: a charging point is checked in Italy only`);
    const x = row(d.brand + "|" + d.model, "IT", "charging-controller");
    ok(x[0] === "D" || (before27 ? /^required from 1 January 2027/.test(x[2] ?? "") : x[0] === "N"), `${d.brand} ${d.model} × IT: Allegato X ${before27 ? "required from 1 January 2027" : "required"}`);
    eq((r.IT.na ?? []).length, C.profiles.IT.items.length - 1, `${d.brand} ${d.model} × IT: every generator item is not applicable`);
  }
  // 4. Germany's transition: an older-edition row says until when it is accepted, and after that day it is withdrawn
  const until = C.profiles.DE.edition.transition_until;
  eq(until, "2027-03-01", "DE: the 2026-03 edition's transition ends on 1 March 2027");
  let de = 0;
  for (const [k, m] of Object.entries(C.models)) {
    const r = m.cc.DE;
    if (!r?.doc?.older) continue;
    de++;
    eq(r.doc.until, until, `${k} × DE: the document carries the transition's end`);
    eq(r.doc.withdrawn, C.built >= until, `${k} × DE: withdrawn only after the transition`);
    for (const x of Object.values(r.rows ?? {})) if (x[0] === "O") ok(C.built >= until ? /transition .* ended on 1 March 2027/.test(x[2]) : /accepted until 1 March 2027$/.test(x[2]), `${k} × DE: an older-edition row says until when`);
  }
  ok(de > 1000, `DE: ${de} models documented for an older edition`);
}
// the fixture's Testland (qa.yaml), run with --today 2027-06-01: what no real profile can show on any day
{
  const items = F.profiles.QA.items, at = (key) => {
    const r = F.models[key]?.cc?.QA;
    return r ? Object.fromEntries(items.map((it, i) => [it.id, (r.na ?? []).includes(i) ? "-" : (r.rows?.[String(i)] ?? ["N"])[0]])) : null;
  };
  const s = (key) => { const x = at(key); return x && Object.entries(x).map(([k, v]) => `${k}=${v}`).join(" "); };
  const note = (key, id) => F.models[key].cc.QA.rows?.[String(items.findIndex((x) => x.id === id))]?.[2] ?? "";
  eq(s("Synthetic|LISTED-40"), "power-class=V single-phase=V protection=W simplified=N rocof=R lfsm-o=N remote-stop=R storage=- charger=- charger-later=-",
    "LISTED-40 (list: 40 kVA, 3-phase, no sheet): within type A, the single-phase line does not apply, over the 30 kVA line, power unknown for applicability resolved by the list");
  ok(/40 kVA, over the 20 kW line, but not the active power/.test(note("Synthetic|LISTED-40", "simplified")), "LISTED-40: a kVA figure over a kW line is not shown, with the reason");
  eq(s("Synthetic|ONE-PHASE-6K"), "power-class=S single-phase=L protection=S simplified=S rocof=R lfsm-o=N remote-stop=R storage=- charger=- charger-later=-",
    "ONE-PHASE-6K (sheet 6 kW single-phase; list 9 kVA three-phase): the sheet wins on every power line");
  eq(at("Synthetic|LISTED-1PH-HYB").storage, "N", "LISTED-1PH-HYB: storage only from the storage file");
  eq(note("Synthetic|LISTED-1PH-HYB", "storage"), "on the generation file only", "LISTED-1PH-HYB: only_where's reason");
  eq(at("Synthetic|MULTI 230 V 48/3000").storage, "R", "MULTI 230 V (storage file): storage checked by the list");
  for (const k of ["Synthetic|TREFAS-1PH", "Synthetic|MULTI 230 V 48/3000"]) {
    eq(at(k)["single-phase"], "N", `${k}: the list's phases column is not used`);
    ok(/not the unit's own phase count/.test(note(k, "single-phase")), `${k}: and the row says why`);
  }
  eq(s("Synthetic|WALLBOX-NODOC").replace(/^.*charger=/, "charger="), "charger=N charger-later=N", "WALLBOX-NODOC: both charger rows not shown");
  eq(note("Synthetic|WALLBOX-NODOC", "charger-later"), "required from 1 January 2028; until then none is asked for", "WALLBOX-NODOC: before `from`, the row says from when");
  eq(note("Synthetic|WALLBOX-NODOC", "charger"), "", "WALLBOX-NODOC: after `from`, a plain not shown");
  eq(at("Synthetic|WALLBOX-11").charger, "N", "WALLBOX-11: a certificate without Allegato X does not cover the charger item");
  eq(at("Synthetic|WALLBOX-22").charger, "D", "WALLBOX-22: a certificate citing Allegato X does");
  eq(Object.keys(F.models["Synthetic|WALLBOX-22"].cc).join(","), "QA", "a charging point has no block where no item names it (GR)");
  const g = F.models["GoodWe|GW10K-ET-20"].cc.QA;
  eq(g.doc?.withdrawn, true, "GW10K × QA: the transition ended on 2027-03-01, so the 2023 certificate is for a withdrawn edition");
  eq(s("GoodWe|GW10K-ET-20"), "power-class=S single-phase=- protection=S simplified=S rocof=O lfsm-o=O remote-stop=O storage=O charger=- charger-later=-",
    "GW10K × QA: after the transition every document row is O, not only the changed one");
}

// an honest "outside": a single-phase unit over 6 kW in Italy, judged on its sheet
const one = Object.entries(C.models).find(([, m]) => m.cc.IT.rows && Object.values(m.cc.IT.rows).some((r) => r[0] === "X" && /1-phase/.test(r[1])));
ok(one, "an 8 kW single-phase unit is outside the Italian phase rule by its datasheet");

// every evidence file is keyed by a brand the register has: the loaders join by `brand:` lowercased, so a display name
// ("Victron Energy" for the register's "Victron") silently joins nothing (found 2026-11-12, Spain)
{
  const R = JSON.parse(readFileSync(resolve(here, "../.data/registers.json"), "utf-8"));
  const have = new Set(R.devices.map((d) => d.brand.toLowerCase()));
  const evDir = resolve(here, "../../data/evidence");
  for (const f of readdirSync(evDir).filter((x) => x.endsWith(".yaml"))) {
    const b = /^brand:\s*(.+?)\s*$/m.exec(readFileSync(resolve(evDir, f), "utf-8"))?.[1]?.replace(/^['"]|['"]$/g, "");
    ok(b && have.has(b.toLowerCase()), `data/evidence/${f}: brand ${JSON.stringify(b)} is not a register brand`);
  }
  const mp = C.models["Victron|MultiPlus-II 48/8000/110-100/100"];
  ok(mp?.cc?.ES?.doc, "Victron MultiPlus-II 48/8000/110-100/100 × ES: the Spanish NTS certificate joins");
}

// every maker's-document file joins its brand: the engine and the page key data/evidence/<brand>.yaml on its `brand`,
// lower-cased, against the register brand, so a display name there ("Victron Energy" for the register's "Victron")
// silently joins nothing (found 2026-11-12: Victron's AT/BE/PL/DE documents reached no model)
{
  const { readdirSync } = await import("node:fs");
  const R = JSON.parse(readFileSync(resolve(here, "../.data/registers.json"), "utf-8"));
  const regBrands = new Set(R.devices.map((d) => d.brand.toLowerCase()));
  const evDir = resolve(here, "../../data/evidence");
  for (const f of readdirSync(evDir).filter((x) => x.endsWith(".yaml"))) {
    const b = yaml.parse(readFileSync(resolve(evDir, f), "utf-8")).brand;
    ok(regBrands.has(String(b).toLowerCase()), `data/evidence/${f}: brand "${b}" is a register brand`);
  }
  const vic = Object.entries(C.models).find(([k]) => /^Victron\|MultiPlus-II 48\/10000\/140-100/i.test(k));
  ok(vic && Object.values(vic[1].cc).some((r) => r.doc), "Victron MultiPlus-II 48/10000/140-100 carries its maker's document in some country");
}
console.log(`${checks} checks, ${fails} failures · ${models} models × ${ccs.length} countries`);
for (const cc of ccs) console.log(`${cc}: datasheet row ${C.stats[cc].sheet_any} · every item covered ${C.stats[cc].covered} · document ${C.stats[cc].doc} (older edition ${C.stats[cc].older}) · outside ${C.stats[cc].outside}`);
process.exit(fails ? 1 : 0);
