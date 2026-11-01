// The evidence layer (data/evidence/<brand>.yaml): the maker's own document that releases a product family
// for named countries. Joined to a register model by a regex over the normalised code, the same way the
// datasheet layer is. "Fit by the maker's document" in a country without a list is this and nothing else.
import { readdirSync, readFileSync } from "node:fs";
import { parse } from "yaml";
import { DATA } from "./data";

export type Doc = { id: string; title: string; url: string; version?: string; doc_no?: string; seen: string; kind: string; note?: string;
  issuer?: string; cert_no?: string; issued?: string; valid_until?: string; standards?: string[]; firmware?: string };
// countries: what the document itself names; accepted: countries whose grid operator names the certificate's standard
// (tools/evidence/build.py derives it from data/evidence/rules/accepts.yaml — an EN 50549-1 certificate in Estonia)
export type Release = { brand: string; family: string; note?: string; countries: string[]; accepted: string[]; doc: Doc };
export const fitsIn = (r: Release, cc: string) => r.countries.includes(cc) || r.accepted.includes(cc);
export const releaseCountries = (rs: Release[]) => [...new Set(rs.flatMap((r) => [...r.countries, ...r.accepted]))];
type Brand = { brand: string; rule: string; documents: (Doc & { families: { name: string; match?: string; note?: string; countries: string[]; accepted_in?: string[] }[] })[] };

const idx = new Map<string, { rx: RegExp; rel: Release }[]>();
export const EVIDENCE_BRANDS: string[] = [];
// per country: every document that releases at least one family there (the country page lists them)
const byCountry = new Map<string, { brand: string; families: string[]; doc: Doc }[]>();
try {
  for (const f of readdirSync(DATA + "evidence")) {
    if (!f.endsWith(".yaml")) continue;
    const b: Brand = parse(readFileSync(DATA + "evidence/" + f, "utf-8"));
    const list: { rx: RegExp; rel: Release }[] = [];
    for (const d of b.documents) {
      const { families: fams, ...doc } = d;
      for (const cc of new Set(fams.flatMap((x) => x.countries ?? []))) {
        if (!byCountry.has(cc)) byCountry.set(cc, []);
        byCountry.get(cc)!.push({ brand: b.brand, families: fams.filter((x) => (x.countries ?? []).includes(cc)).map((x) => x.name), doc });
      }
    }
    for (const d of b.documents) for (const fam of d.families) {
      if (!fam.match) continue;
      const { families: _f, ...doc } = d;
      list.push({ rx: new RegExp(fam.match), rel: { brand: b.brand, family: fam.name, note: fam.note, countries: fam.countries ?? [], accepted: fam.accepted_in ?? [], doc } });
    }
    idx.set(b.brand.toLowerCase(), list);
    EVIDENCE_BRANDS.push(b.brand);
  }
} catch { /* no evidence yet */ }
export const docsFor = (cc: string) => [...(byCountry.get(cc) ?? [])].sort((a, b) => a.brand.localeCompare(b.brand) || (b.doc.issued ?? "").localeCompare(a.doc.issued ?? ""));

const norm = (s: string) => s.toUpperCase().replace(/\s+/g, "").replace(/,/g, ".");
// every document whose family matches: a Spanish certificate must not hide the Italian one for the same model
export function releasesOf(brand: string, model: string): Release[] {
  const list = idx.get(brand.toLowerCase());
  if (!list) return [];
  const n = norm(model);
  return list.filter((x) => x.rx.test(n)).map((x) => x.rel);
}
