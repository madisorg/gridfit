// llms.txt: what the site is and where the machine-readable dataset lives.
import type { APIRoute } from "astro";
import { data, REPO, SITE, TAGLINE } from "../lib/data";
import { COUNTRIES } from "../lib/registers";
import { COUNTS } from "../lib/devices";

export const GET: APIRoute = () => new Response([
  `# ${SITE}`, "", `> ${TAGLINE} One database, two lenses: for each solar inverter, hybrid, home battery and wallbox, whether it works locally with Home Assistant (core and HACS) and evcc and can be controlled or only read, and which EU grid-connection lists (${COUNTRIES.join(", ")} read in full; ${COUNTS.countries} countries described) carry its models, with each list's own status, firmware and dates.`, "",
  `- ${COUNTS.families} product families with a smart-home route, ${COUNTS.regModels} register models, ${COUNTS.brands} brands, checked ${data.seen}.`,
  "- An empty cell means \"not found\", never \"does not work\" or \"not approved\". Every row carries its source URL and the date it was seen.",
  "- URLs: /local/ (family table), /grid/ (register model table), /grid/{cc}/ (one page per country), /{brand}/ (both lenses), /{brand}/{family}/ (device page), /{brand}/model/{code}/ (register model no family claims yet).", "",
  "## Data", "",
  `- [rows.csv](${REPO}/blob/main/data/dataset/rows.csv): one row per integration route, CC BY 4.0`,
  `- [families.json](${REPO}/blob/main/data/dataset/families.json): families with register models and the one-line answer`,
  `- [countries.yaml](${REPO}/blob/main/data/countries.yaml): per EU+ country, whether a public list exists and what applies per device class`,
  `- [changelog.json](${REPO}/blob/main/data/dataset/changelog.json): what changed between rebuilds`,
  `- [registers/changelog.json](${REPO}/blob/main/data/registers/changelog.json): added / removed / changed register rows per refresh`, "",
  "## Pages", "", "- [Local control](/local/)", "- [Grid lists](/grid/)", "- [Changes](/changes/)", "- [How we know](/about/)", "",
].join("\n"), { headers: { "Content-Type": "text/plain; charset=utf-8" } });
