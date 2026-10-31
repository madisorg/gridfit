# Legacy layer — maker-stated discontinued / end-of-life products

Research notes of 2026-11-01. One YAML per brand, same shape throughout:

```yaml
brand: SMA
documents:
  - id: …            # stable id, ends in the month seen or the notice date
    title: "…"       # the page's own title
    url: https://…   # the maker's own page, nothing else
    seen: "2026-11-01"
    kind: archive-page | eol-notice | discontinued-list
    note: ""         # what the page literally says, and what it does not
    models:
      - code: "…"    # exactly as the page writes it
        match: '…'   # regex over the register code normalised: upper case, spaces removed (punctuation kept,
                     # same convention as generations.yaml — NOT the alias `norm` of registers/listing.json, which also
                     # strips dots, slashes and hyphens)
        note: "…"    # only what the page states (date, successor, scope)
```

Rules followed: makers' own sites only; plain HTTP fetches and web search, no headless browser, no accounts, no archive
services, no Huawei (its terms forbid automated access — nothing was attempted), no third-party shops or forums.
Precision over volume: a model is matched only where the maker's page literally says discontinued / end of life /
no longer sold / no longer in production / is placed under a heading the maker itself labels Legacy, Archive or
Discontinued. Statements seen only in search-engine snippets of pages that now redirect or 404 are mentioned in the
notes but never transcribed as models. Type codes the page does not print (SMA prints product names, not STP/SB codes)
are said so in the note.

Three kinds, in descending strength:

- **eol-notice** — a sentence about a named product ("SMA no longer sells the Sunny Boy Storage", "the Fronius
  SnapINverter series has now been officially discontinued", "Color Control GX - End of life").
- **discontinued-list** — a list the maker heads Discontinued / Legacy (FIMER Legacy section, Deye's 'Discontinued'
  document tag, Solis NA 'Legacy Products', Growatt USA 'Discontinued Products').
- **archive-page** — the maker's archive. Weakest: SMA's and KACO's download archives are said by the maker to hold
  discontinued products, but their lists are script-filled and unreadable here; Victron's old-manuals archive holds old
  revisions of current products too and is deliberately matched to nothing; Sungrow's German Produktarchiv defines
  nothing on the page itself.

## Per brand

| brand | file | what was found | models/series matched | explicitness |
|---|---|---|---|---|
| SMA | sma.yaml | 12 product pages "SMA will no longer sell …" / "no longer marketed/distributed", most with named successor; download centre "Archive" category (unreadable) | 11 families (SBS 3.7–6.0, STP 15–25000TL, CORE1, CORE2, STPS60, SB 1.5–2.5, SBS 2.5, SB-US-41, SC 2200/2475, Com Gateway, EV Charger) | explicit per product; type codes not printed on the pages |
| Fronius | fronius.yaml | UK blog 2025-12-19: SnapINverter series "officially discontinued"; series membership from the SnapINverter support page | Primo, Symo (+Advanced), Symo Hybrid, Eco (GEN24 excluded) | explicit for the series, no model codes or dates on the live page |
| Kostal | kostal.yaml | download archive exists, undefined and script-filled | none | — |
| SolaX | solax.yaml | nothing | none | — |
| GoodWe | goodwe.yaml | "GoodWe is no longer selling GE-licensed products" (2024-11-19) | GE-branded GEP/GEH (prefixes not on the page) | explicit, no model names |
| Growatt | growatt.yaml | US product pages headed "Discontinued Products" | ATS-US, ARO US Battery | heading only, US |
| Solis | solis.yaml | NA knowledge base "Legacy Products: delisted … no longer being actively sold in the US and Canada" | RHI-1P(5-10)K-HVES-5G-US, Solis-(75-100)K-5G-US, DLS/DLB loggers | explicit, US/Canada only |
| Fox ESS | foxess.yaml | nothing | none | — |
| Deye | deye.yaml | download pages' PRODUCT SUBCLASS tag "Discontinued" on 13 document titles | 13 exact code groups (SG01LP1-EU 7.6–16K, SG04LP3-EU, SG05LP1-EU plain and -SM2, OG01/OG02LP1, BK kits, M-G4 micros, G06P3-EU-AM2(-P1), SE-F batteries) | tag per document; exact codes only, suffixed newer variants untouched |
| Sungrow | sungrow.yaml | German Produktarchiv (only regional archive still live) | SG-S, SG-D, SG KTL-M/-MT, SG125HV/HX, SH3K6/4K6, centrals, WiFi/E-Net | archive without definition |
| SolarEdge | solaredge.yaml | **blocked** — knowledge-center and www answer 403 | none | — |
| Enphase | enphase.yaml | NA compatibility matrix (PDF May 2025) and storage-compatibility page label "(EOL)": IQ6/IQ7, M Series, IQ Battery 3/10/3T/10T, IQ Combiner 4/4C, IQ System Controller 2; store "Legacy Microinverters / Historic Models" | IQ6, IQ7, M175–M250, D380, Encharge/IQ Battery 3/10, Combiner 4, System Controller 2, M190, M210 | label in a table, North America; see caveat |
| Victron | victron.yaml | CCGX end of life 2025-07-10; MultiGrid 2018; Phoenix 12/180–24/350 "(discontinued)"; Lynx M8 "no longer in production"; Lynx Ion+Shunt 2017; Lithium Smart 2018; old-manuals archive | CCGX, MultiGrid, small Phoenix, Lynx M8, Lynx Ion+Shunt, BAT… | explicit, dated |
| Hoymiles | hoymiles.yaml | statement 2026-07-09 "the discontinued HM Series microinverters" | HM-xxx classic codes (NT excluded) | explicit for the series, no codes |
| KACO | kaco.yaml | download archive "for software and documents of discontinued products", script-filled | none | — |
| ABB / FIMER | fimer.yaml | Legacy section, 4 pages, 35 items | UNO-DM-…-Q (EU) and -US, REACT 2, PVS-60/166/175-TL-US, centrals, MS turnkey, PVI-AEC-EVO, FLEXA/ELECTRA | heading only, no definition |
| Delta | delta.yaml | Solivia cloud monitoring ended (Azure, 2024-09-01); undated catalogue sentence without product name | M1G2 gateway | service end, not product end |
| Solarwatt | solarwatt.yaml | nothing (policy sentence only) | none | — |
| Sofar | sofar.yaml | nothing | none | — |
| Sigenergy | sigenergy.yaml | nothing (PSIRT support periods) | none | — |

## Caveats worth reading before the flag goes live

- **Enphase IQ7**: the only maker statement is "(EOL)" in a North-American compatibility table. The EU register entries
  (IQ7-60-2-INT, IQ7A-72-INT, IQ7+ …) are not addressed by that document. If the flag is to be shown in EU countries,
  consider dropping the IQ7 match or marking it region-scoped.
- **Fronius SnapINverter**: the live page is one sentence; the dates (end 2025-12-31, last order 2025-10-31) live only
  in search snippets of a redirected page. Galvo is not in the maker's SnapINverter list and is not matched.
- **Deye**: the 'Discontinued' tag is on a document, and the same family often has an untagged newer variant with a
  longer suffix (-AM2-P, -AM3-P, -BM2). The regexes match the plain codes only — do not loosen them.
- **Hoymiles HM**: the series is called discontinued, yet HM-…NT product pages are live on the US site; NT is excluded.
- **Sungrow**: the live German archive has no sentence saying what it is; the "AUSLAUFMODELL / AUSVERKAUFT" labels of
  the old German pages are gone from the live site.
- **Scope**: Solis and Growatt facts are US/Canada statements about -US type codes; Enphase is North America.

## Unreachable / not usable

- SolarEdge: 403 on knowledge-center.solaredge.com and www.solaredge.com.
- FIMER's old solar.fimer.com legacy pages: TLS certificate for another domain.
- SMA download-centre Archive, Kostal archive, KACO archive, SolaX downloads: filter lists filled by script.
- my.sma-service.com (Salesforce) pages: need JavaScript.
- Sungrow regional ProductArchive pages other than ger.: redirect to the new site, which has no archive.
- Huawei: not attempted (terms).
- Search-engine snippets were used to find pages only; anything not re-read on a live maker page is in a note, not a model.
