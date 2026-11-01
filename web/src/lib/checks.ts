// The requirement check (tools/check/run.py → .data/checks.json): for a register model, every requirement of every
// country profile with one state — meets by datasheet, set at commissioning (the sheet's range covers it), meets by the
// maker's document, documented for an older edition, not shown, over a line (another procedure), outside by datasheet, no check. The engine stores only the rows that say something; the plain "not shown"
// and "no check" rows are rebuilt here from the item and from whether a sheet or a document exists.
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

export type State = "S" | "P" | "D" | "O" | "N" | "L" | "X" | "I";
export const STATE_WORD: Record<State, string> = {
  S: "meets by datasheet", P: "range covers; set at commissioning", D: "meets by maker's document", O: "documented for an older edition", N: "not shown",
  L: "over a line: other procedure", X: "outside by datasheet", I: "no check",
};
export type Item = { id: string; rule: string; value: string; kind: string; field?: string; provable_by?: string[]; changed_in?: string; changed?: string;
  source: string; why?: string; applies?: { classes?: string[]; below_kw?: number; above_kw?: number; phases?: number[] }; meaning?: string; limit?: number; range?: number[]; over?: string; three_phase_above_kw?: number };
export type Edition = { norm: string; id: string; date: string; in_force?: string; label: string };
export type Doc = { id: string; title: string; url: string; kind: string; issuer: string; cert_no: string; issued: string; seen: string; standards: string; edition: string | null; older: boolean; firmware: string;
  more?: { title: string; url: string; edition: string | null }[] };
export type Row = { item: Item; state: State; text: string; note: string };
export type Sheet = { code: string; url: string; version: string; seen: string; title: string };
export type CountryCheck = { cc: string; country: string; norm: string; edition: Edition; decided_by: string; rows: Row[]; na: Item[];
  sum: Partial<Record<State, number>>; doc: Doc | null; named: Named[]; accepts: string[]; sheet: Sheet | null; covered: number; applicable: number };
export type Named = { title: string; url: string; kind: string; is: string[] };

type Raw = { built: string; profiles: Record<string, { country: string; norm: string; edition: Edition; decided_by: string; accepts: string[]; items: Item[] }>;
  models: Record<string, { sheet?: Sheet; cc: Record<string, { sum: Partial<Record<State, number>>; rows?: Record<string, [State, string?, string?]>; na?: number[]; doc?: Doc; named?: Named[] }> }>;
  stats: Record<string, Record<string, number>> };
const C: Raw = JSON.parse(readFileSync(resolve(process.cwd(), ".data/checks.json"), "utf-8"));
export const CHECK_BUILT: string = C.built;
export const CHECK_STATS = C.stats;
export const CHECK_COUNTRIES: string[] = Object.keys(C.profiles);
// the kinds of maker's document a country's operator takes, in words
export const ACCEPT_WORD: Record<string, string> = {
  "generic-en50549-1": "an EN 50549-1 certificate", "national-declaration": "a declaration against the national rule", "country-release": "the maker's released-countries table",
  "no standard cited": "a document that cites no standard",
};

export function checksOf(d: { brand: string; model: string }): CountryCheck[] {
  const m = C.models[d.brand + "|" + d.model];
  if (!m) return [];
  const sheet = m.sheet ?? null;
  const out: CountryCheck[] = [];
  for (const [cc, p] of Object.entries(C.profiles)) {
    const r = m.cc[cc];
    if (!r) continue;
    const na = new Set(r.na ?? []);
    const rows: Row[] = [];
    p.items.forEach((item, i) => {
      if (na.has(i)) return;
      if (item.kind === "none") { rows.push({ item, state: "I", text: "", note: item.why ?? "" }); return; }
      const st = r.rows?.[String(i)];
      if (st) rows.push({ item, state: st[0], text: st[1] ?? "", note: st[2] ?? "" });
      else rows.push({ item, state: "N", text: "", note: "" });  // the page words it from the sheet / document presence
    });
    const applicable = rows.filter((x) => x.state !== "I").length;
    const covered = rows.filter((x) => x.state !== "N" && x.state !== "I").length;
    out.push({ cc, country: p.country, norm: p.norm, edition: p.edition, decided_by: p.decided_by, rows, na: p.items.filter((_, i) => na.has(i)),
      sum: r.sum, doc: r.doc ?? null, named: r.named ?? [], accepts: p.accepts ?? [], sheet, covered, applicable });
  }
  // the country with the most to say first; the reader's own country is moved up by the page's script (the gf-cc cookie)
  return out.sort((a, b) => b.covered - a.covered || (a.sum.N ?? 0) - (b.sum.N ?? 0) || a.cc.localeCompare(b.cc));
}
