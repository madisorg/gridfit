// Model-code lookup for the search box: every register model, normalised the way the register parser does it
// (gridfit/brands.py norm_model), pointing at its device page — the family's page when one claims the code,
// the model's own page when it is in two or more lists, else its row on the brand page.
import type { APIRoute } from "astro";
import { devices } from "../lib/registers";
import { familyOf, modelUrl } from "../lib/devices";

export const GET: APIRoute = () => {
  const pages: string[] = [], titles: string[] = [], at = new Map<string, number>();
  const page = (url: string, title: string) => {
    if (!at.has(url)) { at.set(url, pages.length); pages.push(url); titles.push(title); }
    return at.get(url)!;
  };
  const models: [string, string, number][] = [];
  for (const d of devices) {
    if (d.unmatched) continue;
    const f = familyOf(d);
    const url = modelUrl(d);
    const i = page(f ? url.replace(/#.*$/, "") : url, f ? `${f.brand} ${f.name}` : `${d.brand} ${d.model}`);
    models.push([d.norm, d.model, i]);
  }
  return new Response(JSON.stringify({ pages, titles, models }), { headers: { "Content-Type": "application/json" } });
};
