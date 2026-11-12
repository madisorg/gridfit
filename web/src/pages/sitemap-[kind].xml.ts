// One child sitemap per kind of page (pages, brands, families, models), each URL with its true lastmod.
import type { APIRoute } from "astro";
import { KINDS, SITEMAP, lastmodOf, type Kind } from "../lib/sitemap";

export function getStaticPaths() {
  return KINDS.map((kind) => ({ params: { kind } }));
}
export const GET: APIRoute = ({ site, params }) => {
  if (!site) return new Response("", { headers: { "Content-Type": "application/xml" } });
  const urls = SITEMAP[params.kind as Kind].map((p) => `<url><loc>${new URL(p, site)}</loc><lastmod>${lastmodOf(p)}</lastmod></url>`).join("");
  return new Response(`<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${urls}</urlset>`,
    { headers: { "Content-Type": "application/xml" } });
};
