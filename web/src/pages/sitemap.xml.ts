// Same pages as v1's sitemap; written only when GRIDFIT_BASE_URL is set.
import type { APIRoute } from "astro";
import { data, brands, familyUrl } from "../lib/data";
import { devices, byBrand, COUNTRIES } from "../lib/registers";
export const GET: APIRoute = ({ site }) => {
  if (!site) return new Response("", { headers: { "Content-Type": "application/xml" } });
  const paths = ["/", ...brands().map(([, fs]) => `/${fs[0].brand_slug}/`), ...data.families.map(familyUrl), "/about/", "/changelog/", "/registers/", "/registers/changes/",
    ...COUNTRIES.map((c) => `/registers/country/${c.toLowerCase()}/`), ...byBrand.map(([b]) => `/registers/brand/${b}/`),
    ...devices.filter((d) => d.page).map((d) => `/registers/brand/${d.brand_slug}/${d.slug}/`)];
  const urls = paths.map((p) => `<url><loc>${new URL(p, site)}</loc><lastmod>${data.seen}</lastmod></url>`).join("");
  return new Response(`<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${urls}</urlset>`,
    { headers: { "Content-Type": "application/xml" } });
};
