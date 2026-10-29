"""Turn the grid-register parser output into data/registers/listing.json.

Usage: python tools/import_registers.py <parser-output-dir>

The parser (register_kirje.jsonl + seade.jsonl) reads the published type-approval
lists of six grid registers. Only the membership fact is kept here - which register
lists which model, with the register's own status word - never firmware strings,
certificate numbers or dates, and never Belgium's Synergrid list (its terms allow
personal use only). AT "Nein" rows are dropped: an empty cell, not a negative.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from gridfit.brands import Brands  # noqa: E402

REGISTERS = {
    "AT": {"name": "Austria - Wechselrichterliste (TOR Erzeuger Typ A) and charger list",
           "url": "https://www.wechselrichterliste.at/", "snapshot": "2026-10-23"},
    "NL": {"name": "Netherlands - Netbeheer Nederland type-A list (energieleveren.nl)",
           "url": "https://www.energieleveren.nl/", "snapshot": "2026-10-28"},
    "CZ": {"name": "Czechia - CEZ Distribuce RfG conformity list",
           "url": "https://www.cezdistribuce.cz/cs/pro-vyrobce/overeni-souladu-s-rfg", "snapshot": "2026-08-21"},
    "SE": {"name": "Sweden - Energiforetagen Rikta Ratt inverter list",
           "url": "https://www.energiforetagen.se/energifakta/elsystemet/produktion/solceller/rikta-ratt--vaxelriktare-for-solceller",
           "snapshot": "2026-10-23"},
    "PL": {"name": "Poland - PTPiREE list of certificates (WiPWC)",
           "url": "https://ptpiree.pl/kodeksy-sieci/wykaz-certyfikatow/", "snapshot": "2026-10-26"},
}
STATUS = {"jah": "listed", "piiranguga": "listed with restrictions", "befristet": "listed, time-limited"}
SKIP_CLASS = {"chp", "genset", "tuul", "turbiin", "muu"}
CLASS = {"hybrid": "hybrid", "pv-inverter": "inverter", "inverter": "inverter", "mikroinverter": "plug-in",
         "aku-inverter": "battery", "varutoide": "battery", "wallbox": "wallbox", "kontroller": "inverter"}
TRUST = {"täpne": "exact", "alias": "alias"}


def main(src: Path):
    brands = Brands(ROOT / "data/curated/brands.yaml")
    status = defaultdict(dict)
    for line in (src / "register_kirje.jsonl").open(encoding="utf-8"):
        r = json.loads(line)
        reg = "AT" if r["register"] == "AT-laadija" else r["register"]
        if reg not in REGISTERS or r["staatus"] not in STATUS:
            continue
        status[(r["tootja_norm"], r["mudel_norm"])].setdefault(reg, STATUS[r["staatus"]])

    out = []
    for line in (src / "seade.jsonl").open(encoding="utf-8"):
        d = json.loads(line)
        if d["klass"] in SKIP_CLASS:
            continue
        regs = status.get((d["tootja_norm"], d["mudel_norm"]))
        if not regs:
            continue
        brand = brands.canon(d["tootja_norm"])
        if not brand:
            continue
        out.append({
            "brand": brand,
            "model": d["mudel_raw"][0].strip(),
            "norm": d["mudel_norm"],
            "class": CLASS.get(d["klass"], "inverter"),
            "registers": dict(sorted(regs.items())),
            "trust": TRUST.get(d["usaldusaste"], "exact"),
        })
    out.sort(key=lambda x: (x["brand"].lower(), x["norm"]))
    dest = ROOT / "data/registers/listing.json"
    dest.write_text(json.dumps({"registers": REGISTERS, "models": out}, ensure_ascii=False, indent=0) + "\n",
                    encoding="utf-8")
    per = defaultdict(int)
    for m in out:
        for k in m["registers"]:
            per[k] += 1
    print(f"{len(out)} models from {len({m['brand'] for m in out})} brands -> {dest}")
    print("per register:", dict(sorted(per.items())))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(Path(sys.argv[1]))
