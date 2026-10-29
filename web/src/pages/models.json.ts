// Model-code lookup for the search box: every register model, normalised the way the register
// parser does it (gridfit/brands.py norm_model), pointing at its family page — or at the brand
// page when no family claims it. Loaded by the browser only when a query contains a digit.
import type { APIRoute } from "astro";
import { data, familyUrl, slug } from "../lib/data";

const norm = (s: string) => s.toUpperCase().replace(/[\s\-_./,()+]/g, "");

export const GET: APIRoute = () => {
  const pages: string[] = [], titles: string[] = [], at = new Map<string, number>();
  const page = (url: string, title: string) => {
    if (!at.has(url)) { at.set(url, pages.length); pages.push(url); titles.push(title); }
    return at.get(url)!;
  };
  const models: [string, string, number][] = [];
  for (const f of data.families) {
    const i = page(familyUrl(f), `${f.brand} ${f.name}`);
    for (const m of f.models) models.push([norm(m.model), m.model, i]);
  }
  for (const [brand, ms] of data.unmatched) {
    const i = page(`/${slug(brand)}/`, `${brand} — not matched to a family`);
    for (const m of ms) models.push([norm(m.model), m.model, i]);
  }
  return new Response(JSON.stringify({ pages, titles, models }), { headers: { "Content-Type": "application/json" } });
};
