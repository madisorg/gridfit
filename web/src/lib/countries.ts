// The EU+ grid-connection table (data/countries.yaml): per country, whether a public list exists and what
// applies per device class. The 7 parsed lists carry model rows on this site; the rest carry this table only.
import { readFileSync } from "node:fs";
import { parse } from "yaml";
import { DATA } from "./data";

export type ListFlag = "yes" | "partial" | "no";
export type ClassState = "list" | "rule" | "free" | "banned" | "unknown";
export type Country = {
  cc: string; country: string; list: ListFlag; list_url?: string;
  classes: Record<string, ClassState>; confidence: Record<string, string>;
};

export const COUNTRIES_ALL: Country[] = parse(readFileSync(DATA + "countries.yaml", "utf-8"));
export const COUNTRY_BY: Record<string, Country> = Object.fromEntries(COUNTRIES_ALL.map((c) => [c.cc, c]));
export const COUNTRIES_SOURCE = "EU+ grid-connection table, 2026-10-29";

export const LIST_WORD: Record<ListFlag, string> = {
  yes: "public list", partial: "partial list", no: "no public list",
};
export const LIST_LONG: Record<ListFlag, string> = {
  yes: "The grid operators publish a list of accepted models.",
  partial: "A list exists but is partial: frozen, members-only, a certificate register rather than an approval list, or not reachable.",
  no: "No public list: the grid operator checks the manufacturer's certificate or declaration per application.",
};
export const CLASS_WORD: Record<ClassState, string> = {
  list: "on a public list", rule: "no list, a rule applies", free: "nothing to approve: no list and no rule",
  banned: "not allowed", unknown: "not confirmed",
};
export const CLASS_LONG: Record<ClassState, string> = {
  list: "a public list covers this class; check the model there",
  rule: "no list, but a notification, registration or certificate rule applies — ask the grid operator",
  free: "no list and no model-level rule: nothing to approve",
  banned: "this kind of device is not allowed to be connected",
  unknown: "we have not confirmed whether a list or a rule applies",
};
export const CONF_WORD: Record<string, string> = { checked: "page opened", search: "from search results", unverified: "unverified" };
// family / register classes -> the table's five classes (a meter is not a grid-connection unit anywhere)
export const CLASS_KEY: Record<string, string | null> = {
  inverter: "inverter", hybrid: "hybrid", battery: "battery", "plug-in": "plug-in", wallbox: "wallbox", meter: null,
};
