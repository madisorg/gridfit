// Every indexable page; written only when GRIDFIT_BASE_URL is set. Country pages without model rows are
// noindex until their notes (data/profiles/) are written, so only those with a profile are listed here.
import type { APIRoute } from "astro";
import { data, familyUrl } from "../lib/data";
import { COUNTRIES } from "../lib/registers";
import { PROFILES } from "../lib/profiles";
import { inScope } from "../lib/countries";
import { BRANDS, modelPages, brandSlugOf } from "../lib/devices";
export const GET: APIRoute = ({ site }) => {
  if (!site) return new Response("", { headers: { "Content-Type": "application/xml" } });
  const paths = ["/", "/grid/", "/changes/", "/about/",
    ...[...new Set([...COUNTRIES, ...Object.keys(PROFILES)])].filter(inScope).map((c) => `/grid/${c.toLowerCase()}/`),
    ...BRANDS.map((b) => `/${b.slug}/`), ...data.families.map(familyUrl),
    ...modelPages.map((d) => `/${brandSlugOf(d)}/model/${d.slug}/`)];
  const urls = paths.map((p) => `<url><loc>${new URL(p, site)}</loc><lastmod>${data.seen}</lastmod></url>`).join("");
  return new Response(`<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${urls}</urlset>`,
    { headers: { "Content-Type": "application/xml" } });
};
