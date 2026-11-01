// Compact index the grid view filters and pages through: one row per register model — the 7 list cells as
// one-letter codes, the smart-home lens as two marks (Home Assistant, evcc), phases, kVA, MPPT count and the
// countries the maker's own document releases the model for — plus what applies per class in each of the countries
// the site covers (`countries`, the default columns) and the type-A ceilings, so a chosen country without a list still gets one status per model; row[11] is the
// legacy tier (web/src/lib/legacy.ts), hidden by default in the view
// (web/src/lib/grid-filter.js decides it; web/test/facets.mjs proves the counts add up).
import type { APIRoute } from "astro";
import { devices, COUNTRIES, best } from "../../lib/registers";
import { BRANDS, brandSlugOf, modelUrl, familyOf, marksOfModel, specOf } from "../../lib/devices";
import { IN_SCOPE, SCOPE, inScope } from "../../lib/countries";
import { LIMITS, PROFILES, NOT_LISTED } from "../../lib/profiles";
import { releasesOf, releaseCountries } from "../../lib/evidence";
import { legacyOf } from "../../lib/legacy";

const CODE: Record<string, string> = { listed: "L", restricted: "R", limited: "T", "limited-past": "P", expired: "E", nein: "N", other: "O" };

export const GET: APIRoute = () => {
  const bidx = new Map(BRANDS.map((b, i) => [b.slug, i]));
  const lc = (s: string) => s.toLowerCase();
  const order = devices.filter((d) => !d.unmatched).sort((a, b) =>
    b.n - a.n || (lc(a.brand) < lc(b.brand) ? -1 : lc(a.brand) > lc(b.brand) ? 1 : 0) || (lc(a.model) < lc(b.model) ? -1 : lc(a.model) > lc(b.model) ? 1 : 0));
  const rows = order.map((d) => {
    const f = familyOf(d), s = specOf(d), mk = marksOfModel(d), rel = releasesOf(d.brand, d.model);
    return [bidx.get(brandSlugOf(d)), d.model, d.cls, modelUrl(d), COUNTRIES.map((c) => (d.cells[c] ? CODE[best(d.cells[c])] : "-")).join(""),
      mk.ha + mk.evcc, f ? f.name : "", s.phases, s.kva, s.mppt, releaseCountries(rel).filter(inScope).join(","), legacyOf(d).tier];
  });
  const scope = Object.fromEntries(IN_SCOPE.map((c) => [c.cc, c.classes]));
  const names = Object.fromEntries(IN_SCOPE.map((c) => [c.cc, c.country]));
  return new Response(JSON.stringify({ read: COUNTRIES, countries: SCOPE, names, scope, limits: LIMITS, how: Object.keys(PROFILES), notListed: NOT_LISTED, brands: BRANDS.map((b) => b.name), rows }),
    { headers: { "Content-Type": "application/json" } });
};
