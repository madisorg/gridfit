// The requirement check (tools/check/run.py → .data/checks.json): for a register model, every requirement of every
// country profile with one state — meets by datasheet, set at commissioning (the sheet's range covers it), meets by the
// maker's document, documented for an older edition, checked by the operator's own list, not shown, over a line (another
// procedure), outside by datasheet, no check, and — for a power line a listed model's sheet does not answer — within or
// over the line by the list's own figure (weaker than the sheet). The engine stores only the rows that say something;
// the plain "not shown" and "no check" rows are rebuilt here from the item and from whether a sheet or a document exists.
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { inScope } from "./countries";

export type State = "S" | "P" | "D" | "O" | "R" | "V" | "W" | "N" | "L" | "X" | "I";
export const STATE_WORD: Record<State, string> = {
  S: "meets by datasheet", P: "range covers; set at commissioning", D: "meets by maker's document", O: "documented for an older edition", R: "checked by the operator's list", N: "not shown",
  V: "within by the list's figure", W: "over a line by the list's figure",
  L: "over a line: other procedure", X: "outside by datasheet", I: "no check",
};
export type Item = { id: string; rule: string; value: string; kind: string; field?: string; provable_by?: string[]; changed_in?: string; changed?: string;
  source: string; why?: string; applies?: { classes?: string[]; below_kw?: number; above_kw?: number; phases?: number[] }; meaning?: string; limit?: number; range?: number[]; over?: string; three_phase_above_kw?: number;
  from?: string; before?: string; cite?: string[] };
export type Edition = { norm: string; id: string; date: string; in_force?: string; label: string; transition_until?: string };
// until: the day a document to an older edition stops counting (the edition's transition); withdrawn: that day has passed
export type Doc = { id: string; title: string; url: string; kind: string; issuer: string; cert_no: string; issued: string; seen: string; standards: string; edition: string | null; older: boolean; firmware: string;
  until?: string; withdrawn?: boolean; more?: { title: string; url: string; edition: string | null }[] };
const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
export const dayWords = (iso: string) => { const [y, m, d] = iso.split("-"); return `${Number(d)} ${MONTHS[Number(m) - 1]} ${y}`; };
export type Row = { item: Item; state: State; text: string; note: string };
export type Sheet = { code: string; url: string; version: string; seen: string; title: string };
export type ListCheck = { word: string; what: string; not_carried: string };
export type CountryCheck = { cc: string; country: string; norm: string; edition: Edition; decided_by: string; rows: Row[]; na: Item[];
  sum: Partial<Record<State, number>>; doc: Doc | null; named: Named[]; accepts: string[]; sheet: Sheet | null; covered: number; applicable: number;
  list: ListCheck | null; listed: boolean; charger: boolean };
export type Named = { title: string; url: string; kind: string; is: string[] };

type Raw = { built: string; profiles: Record<string, { country: string; norm: string; edition: Edition; decided_by: string; accepts: string[]; items: Item[];
    list?: ListCheck; on_application?: string }>;
  models: Record<string, { sheet?: Sheet; cc: Record<string, { sum: Partial<Record<State, number>>; rows?: Record<string, [State, string?, string?]>; na?: number[]; doc?: Doc; named?: Named[]; listed?: boolean }> }>;
  stats: Record<string, Record<string, number>>; doc_accepted?: Record<string, string[]> };
const C: Raw = JSON.parse(readFileSync(resolve(process.cwd(), ".data/checks.json"), "utf-8"));
export const CHECK_BUILT: string = C.built;
export const CHECK_STATS = C.stats;
export const CHECK_COUNTRIES: string[] = Object.keys(C.profiles).filter(inScope);
// the kinds of maker's document a country's operator takes, in words
export const ACCEPT_WORD: Record<string, string> = {
  "generic-en50549-1": "an EN 50549-1 certificate", "national-declaration": "a declaration against the national rule", "country-release": "the maker's released-countries table",
  "no standard cited": "a document that cites no standard",
};

// per maker's document (evidence file's brand | document id): the countries whose operator takes its kind (`accepts`),
// as tools/check/run.py classed it. evidence.ts fitsIn reads it, so the grid's "likely fit", the model page's list tiers
// and the requirement check never disagree about one document. null: no profile for the country, so no rule to apply.
const DOC_ACCEPTED = new Map(Object.entries(C.doc_accepted ?? {}).map(([k, v]) => [k, new Set(v)]));
export function docAccepted(brand: string, id: string, cc: string): boolean | null {
  if (!(cc in C.profiles)) return null;
  return DOC_ACCEPTED.get(brand + "|" + id)?.has(cc) ?? false;
}

export function checksOf(d: { brand: string; model: string; cls?: string }): CountryCheck[] {
  const m = C.models[d.brand + "|" + d.model];
  if (!m) return [];
  const sheet = m.sheet ?? null;
  const out: CountryCheck[] = [];
  for (const [cc, p] of Object.entries(C.profiles)) {
    const r = m.cc[cc];
    if (!r || !inScope(cc)) continue;
    const na = new Set(r.na ?? []);
    // a plain "not shown" row gets the profile's reason: on the list, which does not carry it; or off it, decided on the application
    const why = (r.listed ? p.list?.not_carried : p.on_application) ?? "";
    const rows: Row[] = [];
    p.items.forEach((item, i) => {
      if (na.has(i)) return;
      if (item.kind === "none") { rows.push({ item, state: "I", text: "", note: item.why ?? "" }); return; }
      const st = r.rows?.[String(i)];
      if (st) rows.push({ item, state: st[0], text: st[1] ?? "", note: st[2] ?? "" });
      else rows.push({ item, state: "N", text: "", note: why });  // without a profile reason the page words it from the sheet / document presence
    });
    const applicable = rows.filter((x) => x.state !== "I").length;
    const covered = rows.filter((x) => x.state !== "N" && x.state !== "I").length;
    out.push({ cc, country: p.country, norm: p.norm, edition: p.edition, decided_by: p.decided_by, rows, na: p.items.filter((_, i) => na.has(i)),
      sum: r.sum, doc: r.doc ?? null, named: r.named ?? [], accepts: p.accepts ?? [], sheet, covered, applicable, list: p.list ?? null, listed: !!r.listed, charger: d.cls === "wallbox" });
  }
  // the country with the most to say first; the reader's own country is moved up by the page's script (the gf-cc cookie)
  return out.sort((a, b) => b.covered - a.covered || (a.sum.N ?? 0) - (b.sum.N ?? 0) || a.cc.localeCompare(b.cc));
}
