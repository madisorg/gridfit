// The sitemap, by kind: an index at /sitemap.xml and one child per kind of page (robots.txt names the index).
// lastmod is true: data/sitemap/lastmod.json keeps, per path, a hash of the page's own content and the day that hash last
// changed; tools/sitemap/lastmod.py updates it from a finished build (refresh.yml weekly, lastmod.yml on every push to
// main). A path the file does not know yet gets the dataset's date until the next update. Pages are built from nothing on
// every deploy, so the state has to live in the repo.
import { existsSync, readFileSync } from "node:fs";
import { data, familyUrl, DATA } from "./data";
import { COUNTRIES } from "./registers";
import { PROFILES } from "./profiles";
import { inScope } from "./countries";
import { BRANDS, modelPages, brandSlugOf } from "./devices";

export const KINDS = ["pages", "brands", "families", "models"] as const;
export type Kind = (typeof KINDS)[number];

export const SITEMAP: Record<Kind, string[]> = {
  // the front door, the sections and the country pages (only those with a profile are indexed)
  pages: ["/", "/grid/", "/brands/", "/changes/", "/about/",
    ...[...new Set([...COUNTRIES, ...Object.keys(PROFILES)])].filter(inScope).sort().map((c) => `/grid/${c.toLowerCase()}/`)],
  brands: BRANDS.map((b) => `/${b.slug}/`),
  families: data.families.map(familyUrl),
  models: modelPages.map((d) => `/${brandSlugOf(d)}/model/${d.slug}/`),
};

const STATE = DATA + "sitemap/lastmod.json";
const state: Record<string, [string, string]> = existsSync(STATE) ? JSON.parse(readFileSync(STATE, "utf-8")) : {};
export const lastmodOf = (path: string): string => state[path]?.[1] ?? data.seen;
export const lastmodOfKind = (k: Kind): string => SITEMAP[k].map(lastmodOf).reduce((a, b) => (b > a ? b : a), "");
