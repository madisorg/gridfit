// Country requirement profiles (data/profiles/{cc}.yaml): what the grid operator checks, what a model must
// meet, how a model gets onto the list. One file per country, written by hand from the operator's own documents.
import { readdirSync, readFileSync } from "node:fs";
import { parse } from "yaml";
import { DATA } from "./data";

export type Profile = {
  cc: string; country: string; decided_by: string; type_a_max_kw?: number; not_listed_short?: string;
  list?: { name: string; url: string; meaning: string; gate: string };
  basis: string[];
  must_meet: { rule: string; value: string }[];
  documents_for_listing: string[];
  apply?: { who: string; how: string; guide_url?: string; guide_date?: string; processing_time?: string };
  not_listed?: string; thresholds: string[]; commissioning?: string; evidence_for_documented?: string;
  sources: { title: string; url: string; date?: string; seen?: string }[];
};

export const PROFILES: Record<string, Profile> = {};
try {
  for (const f of readdirSync(DATA + "profiles")) {
    if (!f.endsWith(".yaml")) continue;
    const p: Profile = parse(readFileSync(DATA + "profiles/" + f, "utf-8"));
    PROFILES[p.cc] = p;
  }
} catch { /* no profiles yet */ }
// the type-A ceiling per country where a profile states one: above it the model is type B, another procedure
// what the country does with a model that is not on its list, in one sentence, for the cell's hover
export const NOT_LISTED: Record<string, string> = Object.fromEntries(Object.values(PROFILES).filter((p) => p.not_listed_short).map((p) => [p.cc, p.not_listed_short!]));
export const LIMITS: Record<string, { max_kw: number }> = Object.fromEntries(Object.values(PROFILES).filter((p) => p.type_a_max_kw).map((p) => [p.cc, { max_kw: p.type_a_max_kw! }]));
