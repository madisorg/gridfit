// Legacy models: a model nobody is buying new any more, hidden from the grid view by default and shown on request
// (Madis, 2026-11-01). The flag is evidence, never an age guess, in three tiers, each with its reason in words:
//   A  sure, the lists — every entry the model has is expired, past its end date or refused;
//   B  sure, the maker — the maker's own archive or end-of-life page names it (data/legacy/<brand>.yaml);
//   C  probable — the oldest list date is more than six years old, no list has changed the entry since, and the
//      brand has a newer generation of the family on the lists (data/legacy/generations.yaml).
// No date (EE, BE, NL, AT carry none) means current: honesty over tidiness. A search by model code ignores the
// hiding, so an owner always finds an old unit.
import { readdirSync, readFileSync } from "node:fs";
import { parse } from "yaml";
import { DATA } from "./data";
import { COUNTRIES, REGS, META, devices as regDevices, type Device, type Entry } from "./registers";

export type Tier = "A" | "B" | "C" | "";
export type Legacy = { tier: Tier; reason: string; source?: { title: string; url: string; seen: string } };
export const TIER_WORD: Record<Exclude<Tier, "">, string> = { A: "legacy: expired or refused on every list", B: "legacy: discontinued by the maker", C: "probably legacy: an older generation" };

const norm = (s: string) => s.toUpperCase().replace(/\s+/g, "").replace(",", ".");
const NEG = new Set(["limited-past", "expired", "nein"]);
const YEARS = 6;
const today = new Date();
const cutoff = new Date(today.getFullYear() - YEARS, today.getMonth(), today.getDate()).toISOString().slice(0, 10);

// ---- B: the maker's own archive / end-of-life pages
type Doc = { id: string; title: string; url: string; seen: string; kind: string; note?: string; models: { code: string; match?: string; note?: string }[] };
const archive = new Map<string, { rx: RegExp; doc: Doc; note?: string; code: string }[]>();
export const LEGACY_BRANDS: string[] = [];
try {
  for (const f of readdirSync(DATA + "legacy")) {
    if (!f.endsWith(".yaml") || f === "generations.yaml") continue;
    const b = parse(readFileSync(DATA + "legacy/" + f, "utf-8")) as { brand: string; documents: Doc[] };
    const list: { rx: RegExp; doc: Doc; note?: string; code: string }[] = [];
    for (const doc of b.documents ?? []) for (const m of doc.models ?? []) {
      const rx = m.match ? new RegExp(m.match) : new RegExp("^" + norm(m.code).replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "$");
      list.push({ rx, doc, note: m.note, code: m.code });
    }
    if (list.length) { archive.set(b.brand.toLowerCase(), list); LEGACY_BRANDS.push(b.brand); }
  }
} catch { /* no archive pages read yet */ }

// ---- C: generation rules, and which brands have the newer generation on a list
type Gen = { brand: string; old: string; new: string; note: string };
let GENS: (Gen & { oldRx: RegExp; newRx: RegExp; successors: string[] })[] = [];
try {
  const gens = parse(readFileSync(DATA + "legacy/generations.yaml", "utf-8")) as Gen[];
  GENS = gens.map((g) => ({ ...g, oldRx: new RegExp(g.old), newRx: new RegExp(g.new), successors: [] }));
  for (const d of regDevices) {
    if (d.unmatched) continue;
    const n = norm(d.model);
    for (const g of GENS) if (g.brand.toLowerCase() === d.brand.toLowerCase() && g.newRx.test(n) && g.successors.length < 3) g.successors.push(d.model);
  }
} catch { /* no rules */ }

// the entries' own dates: SE "reviewed", CZ "added"; AT's and PL's dates are end dates, BE / EE / NL carry none
const datedRegs = new Set(["SE", "CZ"]);
const oldestDate = (d: Device): { date: string; reg: string } | null => {
  let best: { date: string; reg: string } | null = null;
  for (const es of Object.values(d.cells)) for (const e of es) {
    if (!datedRegs.has(e.reg) || !/^\d{4}-\d{2}-\d{2}/.test(e.date ?? "")) continue;
    if (!best || e.date < best.date) best = { date: e.date.slice(0, 10), reg: e.reg };
  }
  return best;
};
// a change in the register changelog since the oldest date means someone is still touching the entry
const changed = new Set<string>();
try {
  const log = JSON.parse(readFileSync(DATA + "registers/changelog.json", "utf-8")) as any[];
  for (const e of log) for (const x of Object.values(e.registers ?? {}) as any[]) for (const row of x.changed ?? []) changed.add(norm(String(row[0])) + "\u0000" + norm(String(row[1])));
} catch { /* no log */ }

const cache = new Map<Device, Legacy>();
export function legacyOf(d: Device): Legacy {
  if (cache.has(d)) return cache.get(d)!;
  let out: Legacy = { tier: "", reason: "" };
  const entries = Object.values(d.cells).flat();
  const lists = Object.keys(d.cells);
  if (entries.length && entries.every((e) => NEG.has(e.show))) {
    const words = lists.map((c) => `${c}: ${bestWord(d.cells[c])}`).join("; ");
    out = { tier: "A", reason: `expired or refused on every list that carries it (${words})` };
  } else {
    const hit = archive.get(d.brand.toLowerCase())?.find((x) => x.rx.test(norm(d.model)));
    if (hit) out = { tier: "B", reason: `${d.brand} lists it as discontinued — “${hit.doc.title}” (${hit.doc.kind.replace("-", " ")}, seen ${hit.doc.seen})${hit.note ? `; ${hit.note}` : ""}`, source: { title: hit.doc.title, url: hit.doc.url, seen: hit.doc.seen } };
    else {
      const od = oldestDate(d);
      if (od && od.date < cutoff && !changed.has(norm(d.brand) + "\u0000" + norm(d.model))) {
        const g = GENS.find((g) => g.brand.toLowerCase() === d.brand.toLowerCase() && g.oldRx.test(norm(d.model)) && g.successors.length);
        if (g) out = { tier: "C", reason: `the ${REGS[od.reg]?.short ?? od.reg} entry dates from ${od.date} and no list has changed it since; ${d.brand} has a newer generation on the lists (${g.note}; e.g. ${g.successors.join(", ")})` };
      }
    }
  }
  cache.set(d, out);
  return out;
}
const bestWord = (es: Entry[]) => { const e = es[0]; return e.reg === "BE" ? "expired" : e.show === "limited-past" ? `time-limited until ${e.valid}` : e.show === "nein" ? `“${e.word}”` : "expired"; };

export const LEGACY_COUNTS = (() => {
  const c: Record<string, number> = { A: 0, B: 0, C: 0, current: 0 };
  for (const d of regDevices) { if (d.unmatched) continue; const t = legacyOf(d).tier; c[t || "current"]++; }
  return c;
})();
