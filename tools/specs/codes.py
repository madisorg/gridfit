"""The model-code level of rated power and phases (data/specs/naming/codes.yaml): try every rule on the register models of its
brand, keep a rule's kW and its phases only where they agree with the figures lists and datasheets state, and export the
readings for the site.

    python tools/specs/codes.py            # after tools/site_data.py and tools/specs/build.py: writes web/.data/codes.json

Known figures: a list's kVA (AT, BE, SE) and phases (AT, SE), and the datasheet rows in web/.data/specs.json (matched as
tools/specs/build.py matches them). kW agrees when the known figure is 0.87-1.15 times the code's (lists give kVA, sheets
kW); phases must be equal. A part of a rule (kW, phases) is kept with at least MIN_N agreeing samples and an agreement
share of at least MIN_SHARE. The first rule of a brand that matches a model reads it.
"""
import json
import re
import sys
from pathlib import Path

import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[2]
RULES = ROOT / "data/specs/naming/codes.yaml"
REG, SPECS, OUT = ROOT / "web/.data/registers.json", ROOT / "web/.data/specs.json", ROOT / "web/.data/codes.json"
MIN_N, MIN_SHARE, LO, HI = 3, 0.9, 0.87, 1.15


def norm(code: str) -> str:
    return re.sub(r"\s+", "", code.upper()).replace(",", ".")


def reading(rule: dict, m: re.Match):
    g = m.groupdict()
    kw = None
    if g.get("kw"):
        kw = float(g["kw"] + ("." + g["frac"] if g.get("frac") else ""))
    elif g.get("w"):
        kw = int(g["w"]) / 1000
    ph = rule.get("phases")
    if g.get("ph") and rule.get("ph_map"):
        ph = rule["ph_map"].get(g["ph"])
    return (round(kw, 3) if kw else None), ph


def known_of(d: dict, sheets: list):
    kva = ph = None
    for c in ("AT", "SE", "BE"):
        for e in d["cells"].get(c, []):
            try:
                v = float(e.get("kva") or 0)
            except ValueError:
                v = 0
            if kva is None and v > 0:
                kva = v
            p = (e.get("extra") or {}).get("phases", "")
            if ph is None and p in ("1", "3"):
                ph = int(p)
    n = norm(d["model"])
    for exact, rx, row in sheets:
        if n == exact or (rx and rx.search(n)):
            kva = row.get("ac_kw") or row.get("ac_kva") or kva
            ph = row.get("phases") or ph
            break
    return kva, ph


def main():
    cfg = yaml.safe_load(RULES.read_text(encoding="utf-8"))
    devs = [d for d in json.loads(REG.read_text(encoding="utf-8"))["devices"] if not d["unmatched"]]
    spec = {b["brand"].lower(): [(r["norm"], re.compile(r["match"]) if r["match"] else None, r) for r in b["models"]]
            for b in json.loads(SPECS.read_text(encoding="utf-8"))["brands"]}
    rules_out, models = [], {}
    for b in cfg["brands"]:
        rules = [dict(r, rx=re.compile(r["match"])) for r in b["rules"]]
        stats = [{"kw": [0, 0], "ph": [0, 0], "used": 0} for _ in rules]
        read = []
        for d in (d for d in devs if d["brand"].lower() == b["brand"].lower()):
            n = norm(d["model"])
            for i, r in enumerate(rules):
                m = r["rx"].search(n)
                if not m:
                    continue
                kw, ph = reading(r, m)
                kva, kph = known_of(d, spec.get(b["brand"].lower(), []))
                if kw and kva:
                    stats[i]["kw"][1] += 1
                    stats[i]["kw"][0] += LO <= kva / kw <= HI
                if ph and kph:
                    stats[i]["ph"][1] += 1
                    stats[i]["ph"][0] += ph == kph
                read.append((d, i, kw, ph))
                break
        ok = [{k: s[k][1] >= MIN_N and s[k][0] / s[k][1] >= MIN_SHARE for k in ("kw", "ph")} for s in stats]
        for d, i, kw, ph in read:
            out = {}
            if kw and ok[i]["kw"]:
                out["kw"] = kw
            if ph and ok[i]["ph"]:
                out["ph"] = ph
            if out:
                out["rule"] = len(rules_out) + i
                models[d["brand"] + "|" + d["model"]] = out
                stats[i]["used"] += 1
        for i, r in enumerate(rules):
            s = stats[i]
            rules_out.append({"brand": b["brand"], "match": r["match"], "note": r.get("note", ""), "kw_agree": s["kw"], "ph_agree": s["ph"],
                              "kw_used": ok[i]["kw"], "ph_used": ok[i]["ph"], "models": s["used"]})
            print(f"{b['brand']:16} {r['match'][:52]:52}  kW {s['kw'][0]:3}/{s['kw'][1]:<3} {'used' if ok[i]['kw'] else 'LEFT OUT':8}"
                  f"  phases {s['ph'][0]:3}/{s['ph'][1]:<3} {'used' if ok[i]['ph'] else 'LEFT OUT':8}  models {s['used']}")
    OUT.write_text(json.dumps({"rules": rules_out, "models": models, "min_n": MIN_N, "min_share": MIN_SHARE}, ensure_ascii=False, separators=(",", ":")),
                   encoding="utf-8")
    print(OUT, len(models), "models read from their code,", sum("kw" in v for v in models.values()), "with kW,", sum("ph" in v for v in models.values()), "with phases")


if __name__ == "__main__":
    main()
