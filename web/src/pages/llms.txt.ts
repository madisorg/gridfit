// llms.txt: what the site is and where the machine-readable dataset lives.
import type { APIRoute } from "astro";
import { data, REPO, SITE, TAGLINE } from "../lib/data";
import { COUNTRIES } from "../lib/registers";
import { COUNTS } from "../lib/devices";
import { SCOPE } from "../lib/countries";

export const GET: APIRoute = () => new Response([
  `# ${SITE}`, "", `> ${TAGLINE} One database, two lenses: for each solar inverter, hybrid, home battery and wallbox, whether it works locally with Home Assistant (core and HACS) and evcc and can be controlled or only read, and, in the ${COUNTS.countries} countries the site covers (${SCOPE.join(", ")}), which grid-connection lists (${COUNTRIES.join(", ")} read in full) carry its models, with each list's own status, firmware and dates.`, "",
  `- ${COUNTS.families} product families with a smart-home route, ${COUNTS.regModels} register models, ${COUNTS.brands} brands, checked ${data.seen}.`,
  "- One answer per model and country: on the list / with a condition / refused or expired / not on the list; where a country has no list: fit by the maker's own document (data/evidence/) / accepted on other EU lists / over the type-A limit / nothing known. An empty cell means \"not found\", never \"does not work\" or \"not approved\". Every row carries its source URL and the date it was seen.",
  "- URLs: /grid/ (register model table), /grid/{cc}/ (one page per country covered), /{brand}/ (both lenses), /{brand}/{family}/ (device page), /{brand}/model/{code}/ (register model no family claims yet).", "",
  "## Data", "",
  `- [rows.csv](${REPO}/blob/main/data/dataset/rows.csv): one row per integration route, CC BY 4.0`,
  `- [families.json](${REPO}/blob/main/data/dataset/families.json): families with register models and the one-line answer`,
  `- [countries.yaml](${REPO}/blob/main/data/countries.yaml): per EU+ country, whether a public list exists and what applies per device class; scope: in marks the countries the site covers`,
  `- [profiles/](${REPO}/blob/main/data/profiles): country requirement profiles (who decides, the basis, thresholds, documents)`,
  `- [evidence/](${REPO}/blob/main/data/evidence): the makers' own released-countries documents, family by family`,
  `- [specs/](${REPO}/blob/main/data/specs): the makers' datasheets — MPPT count, rated power, phases per model code`,
  `- [changelog.json](${REPO}/blob/main/data/dataset/changelog.json): what changed between rebuilds`,
  `- [registers/changelog.json](${REPO}/blob/main/data/registers/changelog.json): added / removed / changed register rows per refresh`, "",
  "## Pages", "", "- [Grid lists](/grid/)", "- [Changes](/changes/)", "- [How we know](/about/)", "",
].join("\n"), { headers: { "Content-Type": "text/plain; charset=utf-8" } });
