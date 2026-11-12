// The sitemap index: one child per kind of page (web/src/lib/sitemap.ts); written only when GRIDFIT_BASE_URL is set.
// Country pages without model rows are noindex until their notes (data/profiles/) are written, so only those with a
// profile are listed.
import type { APIRoute } from "astro";
import { KINDS, lastmodOfKind } from "../lib/sitemap";

export const GET: APIRoute = ({ site }) => {
  if (!site) return new Response("", { headers: { "Content-Type": "application/xml" } });
  const items = KINDS.map((k) => `<sitemap><loc>${new URL(`/sitemap-${k}.xml`, site)}</loc><lastmod>${lastmodOfKind(k)}</lastmod></sitemap>`).join("");
  return new Response(`<?xml version="1.0" encoding="UTF-8"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${items}</sitemapindex>`,
    { headers: { "Content-Type": "application/xml" } });
};
