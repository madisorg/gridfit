// Compact index the grid view filters and pages through: one row per register model — the 7 list cells as
// one-letter codes, the smart-home lens as one letter, phases, kVA and MPPT count — plus what applies per class in every
// EU+ country, so a selected country without a list still gets a cell.
import type { APIRoute } from "astro";
import { devices, COUNTRIES, best } from "../../lib/registers";
import { BRANDS, brandSlugOf, modelUrl, familyOf, localOf, localOfModel, specOf } from "../../lib/devices";
import { COUNTRIES_ALL } from "../../lib/countries";

const CODE: Record<string, string> = { listed: "L", restricted: "R", limited: "T", "limited-past": "P", expired: "E", nein: "N", other: "O" };
const LOCAL: Record<string, string> = { control: "W", read: "L", cloud: "C", "brand-route": "B", none: "-" };

export const GET: APIRoute = () => {
  const bidx = new Map(BRANDS.map((b, i) => [b.slug, i]));
  const lc = (s: string) => s.toLowerCase();
  const order = devices.filter((d) => !d.unmatched).sort((a, b) =>
    b.n - a.n || (lc(a.brand) < lc(b.brand) ? -1 : lc(a.brand) > lc(b.brand) ? 1 : 0) || (lc(a.model) < lc(b.model) ? -1 : lc(a.model) > lc(b.model) ? 1 : 0));
  const rows = order.map((d) => {
    const f = familyOf(d), s = specOf(d);
    return [bidx.get(brandSlugOf(d)), d.model, d.cls, modelUrl(d), COUNTRIES.map((c) => (d.cells[c] ? CODE[best(d.cells[c])] : "-")).join(""),
      LOCAL[f ? localOf(f) : localOfModel(d)], f ? f.name : "", s.phases, s.kva, s.mppt];
  });
  const scope = Object.fromEntries(COUNTRIES_ALL.map((c) => [c.cc, c.classes]));
  const names = Object.fromEntries(COUNTRIES_ALL.map((c) => [c.cc, c.country]));
  return new Response(JSON.stringify({ read: COUNTRIES, names, scope, brands: BRANDS.map((b) => b.name), rows }),
    { headers: { "Content-Type": "application/json" } });
};
