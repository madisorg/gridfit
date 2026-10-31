"""Spec layer, step 4: export data/specs/*.yaml for the site and say how far it reaches.

    python tools/specs/build.py            # writes web/.data/specs.json, prints coverage per brand

The site matches a register model to a spec row by normalised code (upper case, no spaces, comma as decimal
point) or by the row's `match` regex; this script does the same match against web/.data/registers.json so the
coverage printed here is what the pages will show. Nothing is guessed: a register model without a row shows
"not collected".
"""
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]  # runs from web/ (npm run build) as well as from the repo root
OUT = ROOT / "web/.data/specs.json"
REG = ROOT / "web/.data/registers.json"
SPECS = ROOT / "data/specs"


def norm(code: str) -> str:
    return re.sub(r"\s+", "", code.upper()).replace(",", ".")


def main():
    brands = []
    for f in sorted(SPECS.glob("*.yaml")):
        doc = yaml.safe_load(f.read_text(encoding="utf-8"))
        src = {s["id"]: s for s in doc["sources"]}
        rows = []
        for m in doc["models"]:
            s = src[m["source"]]
            rows.append({"code": m["code"], "norm": norm(m["code"]), "match": m.get("match") or "", "mppt": m.get("mppt"), "ac_kw": m.get("ac_kw"),
                         "ac_kva": m.get("ac_kva"), "ac_a": m.get("ac_a"), "phases": m.get("phases"), "pv_kw": m.get("pv_kw"),
                         "src": {"url": s["url"], "version": s.get("version") or "", "seen": s["seen"], "title": s.get("title") or s.get("file") or ""}})
        brands.append({"brand": doc["brand"], "maker_site": doc.get("maker_site", ""), "rule": doc["rule"], "models": rows})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"brands": brands}, ensure_ascii=False, indent=0), encoding="utf-8")
    print(OUT, sum(len(b["models"]) for b in brands), "rows,", len(brands), "brands")
    if not REG.exists():
        return
    devs = json.loads(REG.read_text(encoding="utf-8"))["devices"]
    for b in brands:
        regs = [d for d in devs if d["brand"].lower() == b["brand"].lower()]
        pats = [(re.compile(r["match"]) if r["match"] else None, r) for r in b["models"]]
        hit, used = 0, set()
        for d in regs:
            n = norm(d["model"])
            for pat, r in pats:
                if n == r["norm"] or (pat and pat.search(n)):
                    hit += 1
                    used.add(r["code"])
                    break
        unused = [r["code"] for r in b["models"] if r["code"] not in used]
        print(f"{b['brand']:8} register models {len(regs):4}  with a spec row {hit:4}  rows unused on any list {len(unused):3}")
        if unused:
            print("   unused:", ", ".join(unused[:40]))


if __name__ == "__main__":
    main()
