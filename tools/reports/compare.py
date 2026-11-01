"""Pre-certification pilot: put each maker's document (data/test-reports/<brand>.yaml) beside each country's setting
values (tools/reports/country_values.yaml, tools/reports/gr_draft.yaml) and say, per requirement, whether the
document's settable range takes the country's value.

    python tools/reports/compare.py                                   # summary per document × country
    python tools/reports/compare.py --md                              # the Markdown tables docs/pre-cert.md carries
    python tools/reports/compare.py --registers web/.data/registers.json   # + how many register models each family joins
    python tools/reports/compare.py --json out.json                   # every state, for a later engine

States (docs/pre-cert.md): covers · outside · untested (the document names the function but prints no range for this
value, or tested one point that is not the country's) · absent (nothing about the function) · operator (the country
leaves the value to the grid operator per installation). Nothing is inferred from a standard the document cites:
that reading is the separate "floor" row (tools/reports/floor.yaml).
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path

import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
REPORTS, HERE = ROOT / "data/test-reports", Path(__file__).resolve().parent
STATES = ("covers", "outside", "untested", "absent", "operator")
MARK = {"covers": "✓", "outside": "✗", "untested": "?", "absent": "–", "operator": "op"}
# "how much the unit withstands": the country's number must be at or below what the document shows
CAPABILITY = {"immunity_hz_s", "band_47_5_48_5_min", "band_51_51_5_min"}
EPS = 1e-9
INF = math.inf


def norm(code: str) -> str:
    return re.sub(r"\s+", "", code.upper()).replace(",", ".")


def interval(v) -> tuple[float, float]:
    if isinstance(v, list):
        lo, hi = v
        return (-INF if lo is None else float(lo), INF if hi is None else float(hi))
    return (float(v), float(v))


def inside(x: float, lo: float, hi: float) -> bool:
    return lo - EPS <= x <= hi + EPS


def param_state(value, spec: dict | None, name: str) -> tuple[str, str]:
    """One country value against one parameter of a document. Returns (state, why)."""
    if value == "operator":
        return "operator", "set by the grid operator per installation"
    if spec is None:
        return "untested", "the function is there, this value is not printed"
    if value == "present":
        return ("covers", "present") if spec else ("untested", "not printed")
    if isinstance(value, dict) and "cover" in value:
        lo, hi = value["cover"]
        if "range" in spec:
            a, b = spec["range"]
            ok = a <= lo + EPS and b >= hi - EPS
            return ("covers" if ok else "outside", f"settable {a}–{b}, {'takes' if ok else 'does not take'} the whole {lo}–{hi}")
        if "fixed" in spec:
            return "outside", f"fixed at {spec['fixed']}, not settable over {lo}–{hi}"
        return "untested", f"no settable range printed (need {lo}–{hi})"
    lo, hi = interval(value)
    if name in CAPABILITY:
        declared = [spec[k] for k in ("max", "fixed", "default") if isinstance(spec.get(k), (int, float))]
        if "range" in spec:
            declared.append(spec["range"][1])
        need = lo
        if declared:
            c = max(declared)
            return ("covers" if need <= c + EPS else "outside", f"withstands {c:g}, needs {'unlimited' if need == INF else f'{need:g}'}")
        if "tested_at" in spec:
            t = spec["tested_at"]
            return ("covers" if need <= t + EPS else "untested", f"tested at {t:g}, needs {'unlimited' if need == INF else f'{need:g}'}")
        return "untested", "no value printed"
    if "range" in spec:
        a, b = spec["range"]
        ok = not (b < lo - EPS or a > hi + EPS)
        return ("covers" if ok else "outside", f"settable {a}–{b}, needs {fmt_iv(lo, hi)}")
    if "fixed" in spec:
        f = spec["fixed"]
        return ("covers" if inside(f, lo, hi) else "outside", f"fixed {f}, needs {fmt_iv(lo, hi)}")
    if "max" in spec:   # the document says the value stays at or below this (DC injection, a reduction rate)
        m = spec["max"]
        return ("covers" if m <= hi + EPS else "untested", f"at most {m}, needs {fmt_iv(lo, hi)}")
    for k, word in (("tested_at", "tested at"), ("default", "default")):
        if k in spec:
            t = spec[k]
            return ("covers" if inside(t, lo, hi) else "untested", f"{word} {t} only, needs {fmt_iv(lo, hi)}")
    return "untested", "no value printed"


def fmt_iv(lo, hi) -> str:
    if lo == hi:
        return f"{lo:g}"
    if lo == -INF:
        return f"≤ {hi:g}"
    if hi == INF:
        return f"≥ {lo:g}"
    return f"{lo:g}–{hi:g}"


def check_one(check, doc: dict) -> tuple[str, str, int | None]:
    fn, param, value = check
    funcs = doc.get("functions") or {}
    f = funcs.get(fn)
    if value == "operator":
        return "operator", "set by the grid operator per installation", None
    if f is None:
        if fn in (doc.get("tested") or []):
            return "untested", "the document says the function was assessed; no value printed", None
        return "absent", "not in the document", None
    page = f.get("page")
    if isinstance(value, dict) and "modes" in value:
        have = set(f.get("modes") or [])
        miss = [m for m in value["modes"] if m not in have]
        return ("outside" if miss else "covers", f"missing {', '.join(miss)}" if miss else "all modes listed", page)
    if value == "present" and param in ("curve", "method"):
        return "covers", str(f.get(param, "present")), page
    if value == "present":
        spec = f.get(param)
        return ("covers" if isinstance(spec, dict) and "range" in spec else "untested", "settable" if spec else "not printed", page)
    st, why = param_state(value, f.get(param), param)
    return st, why, page


def requirement_state(states: list[str]) -> str:
    s = set(states)
    if "outside" in s:
        return "outside"
    if s == {"covers"}:
        return "covers"
    if s == {"operator"}:
        return "operator"
    if "untested" in s:
        return "untested"
    return "absent"


def load():
    countries = {}
    for f in ("country_values.yaml", "gr_draft.yaml"):
        countries.update(yaml.safe_load((HERE / f).read_text(encoding="utf-8")))
    docs = []
    for f in sorted(REPORTS.glob("*.yaml")):
        b = yaml.safe_load(f.read_text(encoding="utf-8"))
        for d in b["documents"]:
            docs.append({**d, "brand": b["brand"]})
    floor = yaml.safe_load((HERE / "floor.yaml").read_text(encoding="utf-8"))
    floor = {**floor, "brand": "EN 50549-1", "kind": "standard-floor"}
    return countries, docs, floor


def compare(countries, docs):
    out = {}
    for d in docs:
        per = {}
        for cc, c in countries.items():
            reqs = []
            for r in c["requirements"]:
                rows = [(chk, *check_one(chk, d)) for chk in r["checks"]]
                reqs.append({"id": r["id"], "label": r["label"], "state": requirement_state([x[1] for x in rows]),
                             "checks": [{"fn": chk[0], "param": chk[1], "value": chk[2] if not isinstance(chk[2], float) or math.isfinite(chk[2]) else "unlimited",
                                         "state": st, "why": why, "page": pg} for chk, st, why, pg in rows]})
            per[cc] = reqs
        out[d["id"]] = per
    return out


def register_counts(path: Path, docs) -> dict:
    devs = [x for x in json.loads(path.read_text(encoding="utf-8"))["devices"] if not x["unmatched"] and x["cls"] in ("inverter", "hybrid", "battery", "plug-in")]
    counts = {}
    for d in docs:
        n = set()
        for fam in d.get("families") or []:
            if not fam.get("match"):
                continue
            rx = re.compile(fam["match"])
            n |= {x["brand"] + "|" + x["model"] for x in devs if x["brand"].lower() in (d["brand"].lower(), d["brand"].split()[0].lower()) and rx.search(norm(x["model"]))}
        counts[d["id"]] = len(n)
    return counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", action="store_true")
    ap.add_argument("--json")
    ap.add_argument("--registers", help="web/.data/registers.json (from tools/site_data.py) — counts the register models each family joins")
    a = ap.parse_args()
    countries, docs, floor = load()
    res = compare(countries, docs + [floor])
    reg = register_counts(Path(a.registers), docs) if a.registers else {}
    if a.json:
        Path(a.json).write_text(json.dumps({"countries": list(countries), "results": res, "registers": reg}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    ccs = list(countries)
    rows = docs + [floor]
    if a.md:
        print("| document | kind | models | " + " | ".join(f"{cc} ✓/✗/?/–/op" for cc in ccs) + " |")
        print("|---|---|---|" + "---|" * len(ccs))
        for d in rows:
            cells = []
            for cc in ccs:
                n = {s: 0 for s in STATES}
                for r in res[d["id"]][cc]:
                    n[r["state"]] += 1
                cells.append(f"{n['covers']}/{n['outside']}/{n['untested']}/{n['absent']}/{n['operator']} of {len(res[d['id']][cc])}")
            print(f"| {d['brand']} — {d['id']} | {d.get('kind', '')} | {reg.get(d['id'], '') if d['kind'] != 'standard-floor' else '—'} | " + " | ".join(cells) + " |")
        # a document that says nothing anywhere (a two-page certificate, a presets list) is a column of dashes: left out
        cols = [d for d in rows if d.get("functions") or d.get("tested")]
        for cc in ccs:
            print(f"\n**{cc}** — {countries[cc]['label']}\n")
            print("| requirement | " + " | ".join(d["brand"] + " " + d["id"].split("-")[-1] for d in cols) + " |")
            print("|---|" + "---|" * len(cols))
            for i, r in enumerate(countries[cc]["requirements"]):
                print(f"| {r['label']} | " + " | ".join(MARK[res[d['id']][cc][i]['state']] for d in cols) + " |")
        print("\n**Outside, by document and country** (the country's value is not in the printed settable range)\n")
        for d in rows:
            for cc in ccs:
                for r in res[d["id"]][cc]:
                    for c in r["checks"]:
                        if c["state"] == "outside":
                            pg = f", p. {c['page']}" if c.get("page") else ""
                            print(f"- {d['brand']} {d['id']} × {cc} — {r['id']}: {c['fn']}.{c['param']} {c['why']}{pg}")
        return
    for d in rows:
        line = []
        for cc in ccs:
            s = [r["state"] for r in res[d["id"]][cc]]
            line.append(f"{cc} {s.count('covers')}/{len(s)}" + (f" ✗{s.count('outside')}" if "outside" in s else ""))
        print(f"{d['brand']:<10} {d['id']:<42} {d.get('kind', ''):<22} {('models ' + str(reg[d['id']])) if d['id'] in reg else '':<10} " + "  ".join(line))


if __name__ == "__main__":
    main()
