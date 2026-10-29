// Compact index the cross-view filter pages through (same shape as the Python build's registers/index.json).
import type { APIRoute } from "astro";
import { devices, COUNTRIES, byBrand, best, deviceUrl } from "../../lib/registers";

const CODE: Record<string, string> = { listed: "L", restricted: "R", limited: "T", "limited-past": "P", expired: "E", nein: "N", other: "O" };

export const GET: APIRoute = () => {
  const bidx = new Map(byBrand.map(([b], i) => [b, i]));
  const lc = (s: string) => s.toLowerCase();
  const order = [...devices].sort((a, b) => b.n - a.n || (lc(a.brand) < lc(b.brand) ? -1 : lc(a.brand) > lc(b.brand) ? 1 : 0) || (lc(a.model) < lc(b.model) ? -1 : lc(a.model) > lc(b.model) ? 1 : 0));
  const rows = order.map((d) => [bidx.get(d.brand_slug), d.model, d.cls, deviceUrl(d), COUNTRIES.map((c) => (d.cells[c] ? CODE[best(d.cells[c])] : "-")).join("")]);
  return new Response(JSON.stringify({ countries: COUNTRIES, brands: byBrand.map(([, ds]) => ds[0].brand), rows }),
    { headers: { "Content-Type": "application/json" } });
};
