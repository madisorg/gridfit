"""Evidence layer, the measure: how many models with no list answer get the maker's own document.

    python tools/evidence/coverage.py                         # EE ES IT FI FR, against web/dist/grid/index.json
    python tools/evidence/coverage.py --before origin/main    # the same, evidence then vs now, brand by brand
    python tools/evidence/coverage.py --index PATH --cc EE,LV --top 25 --md

The model set is the built grid index (one row per register model, `npm run build` in web/): inverters, hybrids,
batteries and plug-in units. In a country whose list is read the set is the models not on it; in any other country
it is every model. A model counts when a document of its brand names the country for a family whose `match` takes
the model's code — every matching document, as the site does since 2026-11-01.
The count is split by what the document is: a released-countries table, a certificate naming the country, a
grid-code setting in the firmware — and, apart, a certificate against the standard the country's operator names
(`accepted_in`, data/evidence/rules/accepts.yaml), counted only for a model no document names the country for. Python regexes read the `match` patterns as the site's JavaScript does (no lookbehind is used).
"""
import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
KINDS = {"inverter", "hybrid", "battery", "plug-in"}
norm = lambda s: re.sub(r"\s+", "", s.upper()).replace(",", ".")  # noqa: E731 — as web/src/lib/evidence.ts


def load_evidence(ref=None):
    """{brand lower: [(regex, countries, kind, doc id, accepted_in)]} from the working tree or from a git ref."""
    texts = []
    if ref:
        names = subprocess.run(["git", "-C", str(ROOT), "ls-tree", "--name-only", f"{ref}:data/evidence"], capture_output=True, text=True).stdout.split()
        for n in names:
            if n.endswith(".yaml"):
                texts.append(subprocess.run(["git", "-C", str(ROOT), "show", f"{ref}:data/evidence/{n}"], capture_output=True, text=True, encoding="utf-8").stdout)
    else:
        texts = [p.read_text(encoding="utf-8") for p in sorted((ROOT / "data" / "evidence").glob("*.yaml"))]
    out = {}
    for t in texts:
        b = yaml.safe_load(t)
        lst = out.setdefault(b["brand"].lower(), [])
        for d in b["documents"]:
            for fam in d["families"]:
                if fam.get("match"):
                    lst.append((re.compile(fam["match"]), set(fam.get("countries") or []), d["kind"], d["id"], set(fam.get("accepted_in") or [])))
    return out


def measure(index, ev, ccs):
    """{cc: {"total", "any", "accepted", "kind": Counter, "brand": Counter(any), "gap": Counter(not any)}}"""
    res = {}
    for cc in ccs:
        i = index["read"].index(cc) if cc in index["read"] else -1
        r = {"total": 0, "any": 0, "accepted": 0, "kind": Counter(), "brand": Counter(), "gap": Counter()}
        for row in index["rows"]:
            if row[2] not in KINDS or (i >= 0 and row[4][i] != "-"):
                continue
            brand = index["brands"][row[0]]
            r["total"] += 1
            n = norm(row[1])
            hits = [x for x in ev.get(brand.lower(), []) if x[0].search(n)]
            named = [x for x in hits if cc in x[1]]
            if named:
                r["any"] += 1
                r["brand"][brand] += 1
                for k in {x[2] for x in named}:
                    r["kind"][k] += 1
            elif any(cc in x[4] for x in hits):
                r["any"] += 1
                r["accepted"] += 1
                r["brand"][brand] += 1
            else:
                r["gap"][brand] += 1
        res[cc] = r
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default=str(ROOT / "web" / "dist" / "grid" / "index.json"))
    ap.add_argument("--cc", default="EE,ES,IT,FI,FR")
    ap.add_argument("--before", help="git ref whose data/evidence is the 'before'")
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--md", action="store_true", help="markdown tables (for a PR)")
    a = ap.parse_args()
    index = json.loads(Path(a.index).read_text(encoding="utf-8"))
    ccs = a.cc.split(",")
    now = measure(index, load_evidence(), ccs)
    then = measure(index, load_evidence(a.before), ccs) if a.before else None
    w = sys.stdout.write
    if a.md:
        w("| country | models without a list answer | " + ("before | " if then else "") + "maker's document | names the country: release table / certificate / grid-code setting | certificate to the standard the operator names, only |\n")
        w("|---|---:|" + ("---:|" if then else "") + "---:|---|---:|\n")
        for cc in ccs:
            r = now[cc]
            k = r["kind"]
            w(f"| {cc} | {r['total']:,} | " + (f"{then[cc]['any']:,} | " if then else "") +
              f"**{r['any']:,}** | {k['country-release']:,} / {k['certificate'] + k['declaration']:,} / {k['grid-code-setting']:,} | {r['accepted']:,} |\n")
        w("\n")
    else:
        for cc in ccs:
            r = now[cc]
            w(f"{cc}: {r['any']} of {r['total']} have the maker's document" + (f" (before {then[cc]['any']})" if then else "")
              + f"; naming the country, by kind {dict(r['kind'])}; by the operator's standard only {r['accepted']}\n")
    for cc in ccs:
        r = now[cc]
        brands = sorted(set(r["brand"]) | set(r["gap"]), key=lambda b: -(r["brand"][b] + r["gap"][b]))[: a.top]
        if a.md:
            w(f"**{cc}, brand by brand** (largest first)\n\n| brand | without a list answer | " + ("before | " if then else "") + "document |\n|---|---:|" + ("---:|" if then else "") + "---:|\n")
            for b in brands:
                w(f"| {b} | {r['brand'][b] + r['gap'][b]} | " + (f"{then[cc]['brand'][b]} | " if then else "") + f"{r['brand'][b]} |\n")
            w("\n")
        else:
            w(f"  {cc} brands: " + ", ".join(f"{b} {r['brand'][b]}/{r['brand'][b] + r['gap'][b]}" + (f" (was {then[cc]['brand'][b]})" if then else "") for b in brands) + "\n")


if __name__ == "__main__":
    main()
