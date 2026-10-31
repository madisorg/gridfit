// One resolver over both halves of the dataset — integration families (data.ts) and register devices
// (registers.ts) — so every page reads the same answer for the same device and the two lenses cannot
// disagree. A device is a family when one claims the model code, else the register model itself.
import { data, summary, familyUrl, slug, type Family } from "./data";
import { devices as regDevices, COUNTRIES, REGS, META, RS, best, anchor, type Device as RegDevice, type Entry } from "./registers";
import { COUNTRIES_ALL, COUNTRY_BY, CLASS_KEY, type ClassState } from "./countries";
import { LIMITS } from "./profiles";
import { releaseOf, type Release } from "./evidence";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

export type LocalState = "control" | "read" | "cloud" | "brand-route" | "none";
// grid cell: a match in the list, or what the country's table says for this class when no model matched
export type GridState = "listed" | "restricted" | "expired" | "refused" | "" | "rule" | "free" | "banned" | "unknown";

export const LOCAL_WORD: Record<LocalState, string> = {
  control: "local control", read: "local, read only", cloud: "cloud only", "brand-route": "brand route, model unconfirmed", none: "not found",
};
export const GRID_WORD: Record<GridState, string> = {
  listed: "listed", restricted: "listed, conditions", expired: "expired or date passed", refused: "not accepted",
  "": "not found on the list", rule: "no list, a requirement applies", free: "nothing to approve",
  banned: "not allowed", unknown: "unknown",
};

const norm = (s: string) => s.toUpperCase().replace(/[\s\-_./,()+]/g, "");
const lc = (s: string) => s.toLowerCase();
const cmp = (a: string, b: string) => (a < b ? -1 : a > b ? 1 : 0);

// ---- brands: one slug per brand across both halves; the family brand's slug wins when both exist
const famsBySlug = new Map<string, Family[]>();
for (const f of data.families) (famsBySlug.get(f.brand_slug) ?? famsBySlug.set(f.brand_slug, []).get(f.brand_slug)!).push(f);
export function brandSlugOf(d: RegDevice): string {
  const v = d.v1brand ? slug(d.v1brand) : "";
  if (v && famsBySlug.has(v)) return v;
  return d.brand_slug;
}

// ---- register device -> family: exact normalised code inside the same brand
const famByCode = new Map<string, Family>();
for (const f of data.families) for (const m of f.models) famByCode.set(f.brand_slug + "\u0000" + (data.normOf.get(f.brand + "\u0000" + m.model) ?? norm(m.model)), f);
export const familyOf = (d: RegDevice): Family | undefined => famByCode.get(brandSlugOf(d) + "\u0000" + d.norm);

const matched = new Map<Family, RegDevice[]>();
export const regByBrand = new Map<string, RegDevice[]>();
for (const d of regDevices) {
  if (d.unmatched) continue;
  const f = familyOf(d);
  if (f) (matched.get(f) ?? matched.set(f, []).get(f)!).push(d);
  const b = brandSlugOf(d);
  (regByBrand.get(b) ?? regByBrand.set(b, []).get(b)!).push(d);
}
for (const list of matched.values()) list.sort((a, b) => cmp(lc(a.model), lc(b.model)));
for (const list of regByBrand.values()) list.sort((a, b) => cmp(lc(a.model), lc(b.model)));
export const modelsOf = (f: Family): RegDevice[] => matched.get(f) ?? [];

// ---- local lens
export function localOf(f: Family): LocalState {
  const s = summary(f);
  if (s.control) return "control";
  if (s.ha === "local" || s.evcc === "local") return "read";
  if (s.ha === "cloud" || s.evcc === "cloud") return "cloud";
  return "none";
}
export function localOfModel(d: RegDevice): LocalState {
  const fams = famsBySlug.get(brandSlugOf(d)) ?? [];
  return fams.some((f) => ["control", "read"].includes(localOf(f))) ? "brand-route" : "none";
}
export const localRoutes = (f: Family) => f.rows.filter((r) => r.local).map((r) => r.name);

// ---- the smart-home lens as two marks, Home Assistant and evcc: W local control, L local read, C cloud only,
// B brand route (another family of the brand has a local route; this model unconfirmed), - nothing found
export type Mark = "W" | "L" | "C" | "B" | "-";
export const MARK_WORD: Record<Mark, string> = { W: "local control", L: "local, read only", C: "cloud only", B: "brand route, model unconfirmed", "-": "not found" };
const markOf = (rows: { local: boolean | null; control: string }[]): Mark =>
  rows.some((r) => r.local && r.control === "write") ? "W" : rows.some((r) => r.local) ? "L" : rows.length ? "C" : "-";
export function marksOf(f: Family): { ha: Mark; evcc: Mark } {
  return { ha: markOf(f.rows.filter((r) => r.source !== "evcc")), evcc: markOf(f.rows.filter((r) => r.source === "evcc")) };
}
export function marksOfModel(d: RegDevice): { ha: Mark; evcc: Mark } {
  const f = familyOf(d);
  if (f) return marksOf(f);
  const fams = famsBySlug.get(brandSlugOf(d)) ?? [];
  const any = (src: "ha" | "evcc") => fams.some((g) => ["W", "L"].includes(marksOf(g)[src]));
  return { ha: any("ha") ? "B" : "-", evcc: any("evcc") ? "B" : "-" };
}

// ---- grid lens
const SHOW_STATE: Record<string, GridState> = {
  listed: "listed", limited: "restricted", restricted: "restricted", "limited-past": "expired", expired: "expired", nein: "refused", other: "restricted",
};
export const stateOfCells = (es: Entry[]): GridState => SHOW_STATE[best(es)] ?? "restricted";
export function scopeState(cc: string, cls: string): GridState {
  const key = CLASS_KEY[cls] ?? null;
  if (!key) return "free";
  const st: ClassState | undefined = COUNTRY_BY[cc]?.classes[key];
  return !st ? "unknown" : st === "list" ? "" : st;
}
export function gridOfFamily(f: Family): Record<string, GridState> {
  const out: Record<string, GridState> = {};
  for (const cc of COUNTRIES) {
    const sts = modelsOf(f).filter((d) => d.cells[cc]).map((d) => stateOfCells(d.cells[cc]));
    out[cc] = sts.length ? (sts.includes("listed") ? "listed" : sts.includes("restricted") ? "restricted" : sts.includes("expired") ? "expired" : "refused") : scopeState(cc, f.class);
  }
  return out;
}
export function gridOfModel(d: RegDevice): Record<string, GridState> {
  const out: Record<string, GridState> = {};
  for (const cc of COUNTRIES) out[cc] = d.cells[cc] ? stateOfCells(d.cells[cc]) : scopeState(cc, d.cls);
  return out;
}
// entries per parsed country for a family: every matched model's rows, flattened
export function entriesOfFamily(f: Family): Record<string, Entry[]> {
  const out: Record<string, Entry[]> = {};
  for (const d of modelsOf(f)) for (const [cc, es] of Object.entries(d.cells)) (out[cc] ??= []).push(...es);
  return out;
}
export const OTHER_COUNTRIES = COUNTRIES_ALL.filter((c) => !COUNTRIES.includes(c.cc));
export const othersOf = (cls: string) => OTHER_COUNTRIES.map((c) => {
  const key = CLASS_KEY[cls] ?? null;
  return { cc: c.cc, country: c.country, list: c.list, list_url: c.list_url,
    state: (key ? c.classes[key] : "free") as ClassState, confidence: key ? c.confidence[key] : "checked" };
});

// ---- specs. The lists carry phases (AT, SE) and rated power in kVA (AT, BE, SE). MPPT count, rated kW and max AC
// current come from the makers' own datasheets — data/specs/*.yaml, exported by tools/specs/build.py to .data/specs.json —
// matched to a register model by exact normalised code or the row's `match` regex. A model without a datasheet row shows
// "not collected", never a guess; the list's own figure wins where both have one.
export type Sheet = { code: string; mppt: number | null; ac_kw: number | null; ac_kva: number | null; ac_a: number | null; phases: number | null;
  pv_kw: number | null; src: { url: string; version: string; seen: string; title: string } };
type SheetRow = Sheet & { norm: string; match: string };
const SPECS: { brands: { brand: string; maker_site: string; rule: string; models: SheetRow[] }[] } =
  JSON.parse(readFileSync(resolve(process.cwd(), ".data/specs.json"), "utf-8"));
export const SPEC_BRANDS: string[] = SPECS.brands.map((b) => b.brand);
export const SPEC_ROWS: number = SPECS.brands.reduce((n, b) => n + b.models.length, 0);
export const SPEC_RULE: string = SPECS.brands[0]?.rule ?? "";
const specNorm = (s: string) => s.toUpperCase().replace(/\s+/g, "").replace(/,/g, ".");
const sheetIdx = new Map<string, { exact: Map<string, Sheet>; rx: [RegExp, Sheet][] }>();
for (const b of SPECS.brands) {
  const exact = new Map<string, Sheet>(), rx: [RegExp, Sheet][] = [];
  for (const m of b.models) { exact.set(m.norm, m); if (m.match) rx.push([new RegExp(m.match), m]); }
  sheetIdx.set(b.brand.toLowerCase(), { exact, rx });
}
const sheetCache = new Map<RegDevice, Sheet | null>();
export function sheetOf(d: RegDevice): Sheet | null {
  if (sheetCache.has(d)) return sheetCache.get(d)!;
  const ix = sheetIdx.get(d.brand.toLowerCase());
  let hit: Sheet | null = null;
  if (ix) { const n = specNorm(d.model); hit = ix.exact.get(n) ?? ix.rx.find(([r]) => r.test(n))?.[1] ?? null; }
  sheetCache.set(d, hit);
  return hit;
}
export type Spec = { phases: string; kva: number | null; mppt: number | null; kw: number | null; sheet: Sheet | null };
export function specOf(d: RegDevice): Spec {
  let phases = "", kva: number | null = null;
  for (const cc of ["AT", "SE", "BE"]) for (const e of d.cells[cc] ?? []) {
    if (!phases && e.extra?.phases && /^[123]$/.test(e.extra.phases)) phases = e.extra.phases;
    if (kva === null && e.kva !== undefined && e.kva !== null && e.kva !== "") { const n = Number(e.kva); if (Number.isFinite(n) && n > 0) kva = Math.round(n * 100) / 100; }
  }
  const sh = sheetOf(d);
  if (!phases && sh?.phases) phases = String(sh.phases);
  if (kva === null && sh) kva = sh.ac_kva ?? sh.ac_kw ?? null;
  return { phases, kva, mppt: sh?.mppt ?? null, kw: sh?.ac_kw ?? sh?.ac_kva ?? null, sheet: sh };
}
export function specOfFamily(f: Family): { phases: string; kvaMin: number | null; kvaMax: number | null; mppt: string; sheets: number } {
  const ph = new Set<string>(), mp = new Set<number>(); let lo: number | null = null, hi: number | null = null, n = 0;
  for (const d of modelsOf(f)) {
    const s = specOf(d);
    if (s.phases) ph.add(s.phases);
    if (s.kva !== null) { lo = lo === null ? s.kva : Math.min(lo, s.kva); hi = hi === null ? s.kva : Math.max(hi, s.kva); }
    if (s.mppt !== null) mp.add(s.mppt);
    if (s.sheet) n++;
  }
  return { phases: [...ph].sort().join("/"), kvaMin: lo, kvaMax: hi, mppt: [...mp].sort().join("/"), sheets: n };
}
export const MPPT_OPTS: [string, string][] = [["1", "1 MPPT"], ["2", "2 MPPT"], ["3", "3 MPPT"], ["4", "4 or more MPPT"]];
export const KVA_BUCKETS: [string, string, number, number][] = [
  ["0-3.7", "up to 3.7 kVA (one-phase, 16 A)", 0, 3.7], ["3.7-6", "3.7 to 6 kVA", 3.7, 6], ["6-12", "6 to 12 kVA", 6, 12],
  ["12-30", "12 to 30 kVA", 12, 30], ["30-", "over 30 kVA", 30, Infinity],
];
export const kindOf = (cls: string) => (cls === "wallbox" ? "ev" : cls === "meter" ? "meter" : "inv");

// ---- three answers per cell; the rest is detail for the hover
export type Answer = "yes" | "cond" | "free" | "doc" | "no" | "none";
export const answerOf = (st: GridState | undefined): Answer =>
  st === "listed" ? "yes" : st === "restricted" ? "cond" : st === "free" ? "free" : st === "expired" || st === "refused" || st === "banned" ? "no" : "none";
export const RULE_WORD: Record<string, string> = { list: "list", rule: "certificate", free: "—", banned: "not allowed", unknown: "?" };
export type Tip = { title: string; lines: string[]; href?: string; hrefText?: string };
export function tipOf(cc: string, state: GridState, es: Entry[], cls?: string): Tip {
  const c = COUNTRY_BY[cc];
  const country = c?.country ?? cc;
  const there = { href: `/grid/${cc.toLowerCase()}/`, hrefText: "what applies there" };
  if (es.length) {
    const e = es[0], r = REGS[e.reg], m = META[e.reg], b = best(es);
    const title = b === "listed" ? "on the list" : b === "restricted" || b === "limited" ? "on the list, with a condition"
      : b === "limited-past" ? "not fit: the end date has passed" : b === "expired" ? "not fit: expired" : b === "nein" ? "not fit: the list says no" : "on the list";
    const lines = [`${r.name}${m?.source_date ? `, dated ${m.source_date}` : ""}`];
    if (e.reg !== "BE") {
      if (e.word && e.word.toLowerCase() !== RS[b]) lines.push(`the list says: \u201c${e.word}\u201d`);
      if (e.valid) lines.push(`${b === "limited-past" ? "was valid until" : "valid until"} ${e.valid}`);
      if (e.fw) lines.push(`${r.fw_label}: ${e.fw.length > 60 ? e.fw.slice(0, 60) + "\u2026" : e.fw}`);
      if (e.cert) lines.push(`${e.reg === "PL" ? "document" : "evidence"}: ${e.cert}`);
    }
    lines.push(`as written: ${e.maker_raw} \u00b7 ${e.model_raw}${es.length > 1 ? ` (+${es.length - 1} rows)` : ""}`);
    return { title, lines, href: r.url, hrefText: "open the list" };
  }
  const key = cls ? CLASS_KEY[cls] ?? null : null;
  const st: ClassState | "" = key && c ? c.classes[key] : "";
  if (state === "" || st === "list") {
    const r = REGS[cc];
    return { title: "nothing known: not found on the list", lines: [`${r ? r.name : country}${META[cc]?.source_date ? `, dated ${META[cc].source_date}` : ""}`,
      "the list may spell the model differently \u2014 never \u201cnot approved\u201d"], href: r?.url ?? c?.list_url, hrefText: "open the list" };
  }
  if (state === "rule") return { title: "nothing known: a certificate is required, no document found", lines: [`${country} has no list for this class; the grid operator checks the maker's certificate with the application`], ...there };
  if (state === "free") return { title: "fit: nothing to approve", lines: [`${country} lists no ${cls === "wallbox" ? "chargers" : cls === "meter" ? "meters or energy managers" : "devices of this class"}; nothing to check against a list`], ...there };
  if (state === "banned") return { title: "not fit: not allowed", lines: [`${country} does not allow this kind of device to be connected`], ...there };
  return { title: "nothing known: not confirmed", lines: [`whether ${country} lists or otherwise gates this class is not confirmed yet`], ...there };
}

// ---- urls and pages
export const modelAnchor = (d: RegDevice) => `m-${anchor(d)}`;
export function modelUrl(d: RegDevice): string {
  const f = familyOf(d);
  if (f) return `${familyUrl(f)}#${modelAnchor(d)}`;
  const b = brandSlugOf(d);
  return d.page ? `/${b}/model/${d.slug}/` : `/${b}/#${modelAnchor(d)}`;
}
// a register model gets its own page only when no family claims it and it is in two or more lists
export const modelPages = regDevices.filter((d) => d.page && !d.unmatched && !familyOf(d));

export type Brand = { slug: string; name: string; families: Family[]; models: RegDevice[] };
const names = new Map<string, string>();
for (const f of data.families) names.set(f.brand_slug, f.brand);
for (const [b, ds] of regByBrand) if (!names.has(b)) names.set(b, ds[0].brand);
export const BRANDS: Brand[] = [...names.entries()]
  .map(([s, name]) => ({ slug: s, name, families: famsBySlug.get(s) ?? [], models: regByBrand.get(s) ?? [] }))
  .sort((a, b) => cmp(lc(a.name), lc(b.name)));
export const brandOf = (s: string) => BRANDS.find((b) => b.slug === s);

// reserved first path segments: a brand slug must never collide with a section
export const RESERVED = new Set(["local", "grid", "changes", "about", "model", "search", "data", "devices", "sitemap", "404", "llms", "robots", "models"]);
for (const b of BRANDS) if (RESERVED.has(b.slug)) throw new Error(`brand slug collides with a reserved path: ${b.slug}`);
for (const f of data.families) if (f.slug === "model") throw new Error(`family slug "model" collides with the model pages: ${f.brand}`);

export const nf = (n: number) => n.toLocaleString("en").replace(/,/g, " ");
export const COUNTS = {
  families: data.families.length, brands: BRANDS.length, rows: data.rows.length,
  regModels: regDevices.filter((d) => !d.unmatched).length, lists: COUNTRIES.length, countries: COUNTRIES_ALL.length,
  modelPages: modelPages.length,
  localRoute: data.families.filter((f) => ["control", "read"].includes(localOf(f))).length,
};

// ---- the countries without a list (or with one not read): one status per device, the same rule as the grid view
// (web/src/lib/grid-filter.js cellCode): the maker's own document, the type-A ceiling, then what other EU lists say.
export type Tier = "D" | "K" | "B" | "F" | "?" | "X" | "-";
export const TIER_WORD: Record<Tier, string> = {
  D: "likely fit: the maker's document names the country", K: "possibly fit: accepted on other EU lists", B: "other procedure: over the type-A limit",
  F: "fit: nothing to approve for this kind of device", "?": "unknown: not confirmed", X: "not fit: not allowed", "-": "unknown: nothing known",
};
export type Other = { cc: string; country: string; list: string; list_url?: string; state: ClassState; confidence: string; tier: Tier; release: Release | null };
export function tierOf(cc: string, state: ClassState, positive: string[], releases: Release[], kva: number | null): { tier: Tier; release: Release | null } {
  if (state === "banned") return { tier: "X", release: null };
  if (state === "free") return { tier: "F", release: null };
  const rel = releases.find((r) => r.countries.includes(cc));
  if (rel) return { tier: "D", release: rel };
  if (state === "unknown") return { tier: "?", release: null };
  const lim = LIMITS[cc]?.max_kw;
  if (lim && kva !== null && kva > lim) return { tier: "B", release: null };
  return { tier: positive.length ? "K" : "-", release: null };
}
export const positiveOf = (cells: Record<string, GridState>) => COUNTRIES.filter((c) => cells[c] === "listed" || cells[c] === "restricted");
export function othersTiered(cls: string, cells: Record<string, GridState>, releases: Release[], kva: number | null): Other[] {
  const positive = positiveOf(cells);
  return othersOf(cls).map((o) => ({ ...o, ...tierOf(o.cc, o.state, positive, releases, kva) }));
}
export const releaseOfModel = (d: RegDevice): Release | null => releaseOf(d.brand, d.model);
export const releasesOfFamily = (f: Family): Release[] => {
  const seen = new Map<string, Release>();
  for (const d of modelsOf(f)) { const r = releaseOf(d.brand, d.model); if (r && !seen.has(r.family)) seen.set(r.family, r); }
  return [...seen.values()];
};
