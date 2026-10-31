// The evidence layer (data/evidence/<brand>.yaml): the maker's own document that releases a product family
// for named countries. Joined to a register model by a regex over the normalised code, the same way the
// datasheet layer is. "Fit by the maker's document" in a country without a list is this and nothing else.
import { readdirSync, readFileSync } from "node:fs";
import { parse } from "yaml";
import { DATA } from "./data";

export type Doc = { id: string; title: string; url: string; version?: string; doc_no?: string; seen: string; kind: string; note?: string;
  issuer?: string; cert_no?: string; issued?: string; valid_until?: string; standards?: string[]; firmware?: string };
export type Release = { brand: string; family: string; note?: string; countries: string[]; doc: Doc };
type Brand = { brand: string; rule: string; documents: (Doc & { families: { name: string; match?: string; note?: string; countries: string[] }[] })[] };

const idx = new Map<string, { rx: RegExp; rel: Release }[]>();
export const EVIDENCE_BRANDS: string[] = [];
try {
  for (const f of readdirSync(DATA + "evidence")) {
    if (!f.endsWith(".yaml")) continue;
    const b: Brand = parse(readFileSync(DATA + "evidence/" + f, "utf-8"));
    const list: { rx: RegExp; rel: Release }[] = [];
    for (const d of b.documents) for (const fam of d.families) {
      if (!fam.match) continue;
      const { families: _f, ...doc } = d;
      list.push({ rx: new RegExp(fam.match), rel: { brand: b.brand, family: fam.name, note: fam.note, countries: fam.countries, doc } });
    }
    idx.set(b.brand.toLowerCase(), list);
    EVIDENCE_BRANDS.push(b.brand);
  }
} catch { /* no evidence yet */ }

const norm = (s: string) => s.toUpperCase().replace(/\s+/g, "").replace(/,/g, ".");
export function releaseOf(brand: string, model: string): Release | null {
  const list = idx.get(brand.toLowerCase());
  if (!list) return null;
  const n = norm(model);
  return list.find((x) => x.rx.test(n))?.rel ?? null;
}
