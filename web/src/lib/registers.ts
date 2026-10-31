// The grid-register cross-view, as tools/site_data.py exports it from gridfit.registers.
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { data as v1, familyUrl } from "./data";

const R = JSON.parse(readFileSync(resolve(process.cwd(), ".data/registers.json"), "utf-8"));

export type Entry = {
  reg: string; show: string; word: string; maker_raw: string; model_raw: string; fw: string; cert: string;
  id: string; valid: string; date: string; trust: string; kva?: number | string; extra: Record<string, string>;
};
export type Device = {
  brand: string; model: string; norm: string; cls: string; n: number; unmatched: string | boolean; variants: string[];
  brand_slug: string; slug: string | null; page: boolean; v1brand: string; cells: Record<string, Entry[]>;
};
export type Reg = {
  country: string; short: string; name: string; operator: string; url: string; basis: string; gate: string;
  contains: string; terms: string; use: string; date_label: string; fw_label: string;
};

export const SNAP_DATE: string = R.date;
export const COUNTRIES: string[] = R.countries;
export const COUNTRY_OF: Record<string, string> = R.country_of;
export const REGS: Record<string, Reg> = R.registers;
export const NOT_READ: [string, string, string, string, string][] = R.not_read;
export const RC: Record<string, string> = R.class_label;
export const RS: Record<string, string> = R.status_label;
export const RSHORT: Record<string, string> = R.status_short;
export const META: Record<string, { source_date?: string; seen?: string; rows?: number; carried_over?: boolean; unread_lp?: string[] }> = R.meta;
export const LOG: any[] = R.log;
export const STATS: Record<string, { regs: string[]; rows: number; other_rows: number; words: [string, string, number][] }> = R.stats;
export const devices: Device[] = R.devices;

const ORDER = ["listed", "restricted", "limited", "limited-past", "expired", "nein", "other"];
export const best = (cell: Entry[]) => cell.map((e) => e.show).sort((a, b) => ORDER.indexOf(a) - ORDER.indexOf(b))[0];
export const regsOf = (c: string) => Object.keys(REGS).filter((r) => (COUNTRY_OF[r] ?? r) === c);
export const slug = (t: string) =>
  t.toLowerCase().replace(/&/g, " and ").replace(/\+/g, " plus ").replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "x";
export const anchor = (d: Device) => slug(d.model).slice(0, 60);
export const deviceUrl = (d: Device) =>
  d.page ? `/registers/brand/${d.brand_slug}/${d.slug}/` : `/registers/brand/${d.brand_slug}/#m-${anchor(d)}`;
export const trustOf = (d: Device) => {
  const t = new Set(Object.values(d.cells).flat().map((e) => e.trust));
  return t.has("unmatched") ? "unmatched" : t.has("alias") ? "alias" : "exact";
};

// a register device -> its GridFit family page, by canonical brand and normalised model code
const norm = (s: string) => s.toUpperCase().replace(/[\s\-_./,()+]/g, "");
const famOf = new Map<string, { url: string; title: string }>();
for (const f of v1.families) for (const m of f.models) famOf.set(f.brand + "\u0000" + norm(m.model), { url: familyUrl(f), title: `${f.brand} ${f.name}` });
export const familyOf = (d: Device) => famOf.get(d.v1brand + "\u0000" + d.norm);
export const v1BrandSlugs = new Set(v1.families.map((f) => f.brand_slug));

export const byBrand = (() => {
  const m = new Map<string, Device[]>();
  for (const d of devices) (m.get(d.brand_slug) ?? m.set(d.brand_slug, []).get(d.brand_slug)!).push(d);
  const lc = (s: string) => s.toLowerCase();
  return [...m.entries()].sort((a, b) => (lc(a[1][0].brand) < lc(b[1][0].brand) ? -1 : lc(a[1][0].brand) > lc(b[1][0].brand) ? 1 : 0));
})();

// one question per register that lists the model, in the register's own words (as gridfit/render.py _faq)
export function faq(d: Device) {
  const out: { q: string; a: string; de: string }[] = [];
  for (const c of COUNTRIES) {
    const e = d.cells[c]?.[0];
    if (!e) continue;
    const r = REGS[e.reg];
    const st = RS[e.show];
    const q = `Is the ${d.brand} ${d.model} on the ${r.short}?`;
    let a = ["listed", "restricted", "limited"].includes(e.show)
      ? `Yes — the ${r.short} lists it as “${e.reg !== "BE" ? e.word : "listed"}”`
      : `The ${r.short} shows it as “${e.word || st}”`;
    if (e.valid) a += `, until ${e.valid}`;
    if (e.fw && e.reg !== "BE") a += `; ${r.fw_label}: ${e.fw.length <= 80 ? e.fw : e.fw.slice(0, 80).replace(/\s+\S*$/, "") + " …"}`;
    const src = META[e.reg]?.source_date ?? "";
    a += src ? ` (list dated ${src}, checked ${META[e.reg]?.seen ?? ""}).` : ` (the list is undated; checked ${META[e.reg]?.seen ?? ""}).`;
    const de = c !== "AT" ? "" :
      `Steht der ${d.brand} ${d.model} auf der österreichischen ${e.reg === "AT-EV" ? "Liste der Ladeeinrichtungen" : "Wechselrichterliste (TOR Erzeuger Typ A)"}? ` +
      `Laut Liste vom ${src || "—"}: „${e.word}“` + (e.valid ? `, befristet bis ${e.valid}` : "") + ".";
    out.push({ q, a, de });
  }
  return out;
}
