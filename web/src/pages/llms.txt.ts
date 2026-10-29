// llms.txt: what the site is and where the machine-readable dataset lives.
import type { APIRoute } from "astro";
import { data, brands, REPO, SITE, TAGLINE } from "../lib/data";

export const GET: APIRoute = () => new Response([
  `# ${SITE}`, "", `> ${TAGLINE} An open dataset with two answers per solar inverter, hybrid, home battery and wallbox: whether it works locally with Home Assistant (core and HACS) and evcc and can be controlled or only read, and which EU grid-connection lists (AT, CZ, EE, NL, PL, SE on family pages; AT, BE, CZ, EE, NL, PL, SE in /registers/) carry its models, with each list's own status, firmware and dates.`, "",
  `- ${data.families.length} product families, ${brands().length} brands, checked ${data.seen}.`,
  "- An empty cell means \"not found\", never \"does not work\" or \"not approved\". Every row carries its source URL and the date it was seen.", "",
  "## Data", "",
  `- [rows.csv](${REPO}/blob/main/data/dataset/rows.csv): one row per integration route, CC BY 4.0`,
  `- [families.json](${REPO}/blob/main/data/dataset/families.json): families with register models and the one-line answer`,
  `- [changelog.json](${REPO}/blob/main/data/dataset/changelog.json): what changed between rebuilds`,
  `- [registers/changelog.json](${REPO}/blob/main/data/registers/changelog.json): added / removed / changed register rows per refresh`, "",
  "## Pages", "", "- [How we know](/about/)", "- [Grid registers cross-view](/registers/)", "- [Register changes](/registers/changes/)", "- [Changes](/changelog/)", "",
].join("\n"), { headers: { "Content-Type": "text/plain; charset=utf-8" } });
