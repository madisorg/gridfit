"""Evidence layer, step 2: write the parsed sources into data/evidence/<brand>.yaml.

    python -I tools/evidence/build.py            # every brand in sources.yaml whose file is in cache/evidence
    python -I tools/evidence/build.py kostal     # one brand
    python -I tools/evidence/build.py --check    # parse and compare, write nothing; exit 1 when a file would change

A document whose id is in sources.yaml is rewritten from its file; every other document in the brand file (written
by hand: certificates read one by one, a source behind a WAF) is kept as it is, in place. A family the source maps
but the document no longer has, or a column the document has but the source does not map, is printed as a
warning: the maker changed the table and the mapping wants a look. `seen` is the day fetch.py last downloaded
the file (cache/evidence/manifest.json). `accepted_in` is derived for every certificate in the file, hand-written ones
too: the countries whose grid operator names the certified standard as its document (data/evidence/rules/accepts.yaml).
"""
import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # -I drops the script's directory; parse.py is ours, the cache is never on the path

import yaml  # noqa: E402

import parse  # noqa: E402

ROOT = HERE.parents[1]
CACHE = ROOT / "cache" / "evidence"
DATA = ROOT / "data" / "evidence"
HEADER = """# Evidence layer — see the rule below. URLs are the makers' own. Documents with an id in tools/evidence/sources.yaml
# are written by tools/evidence/build.py from the maker's file; the others were transcribed by hand. Do not edit the
# generated ones here: change the mapping in sources.yaml and rebuild.
"""
RULE = ("Facts transcribed from the maker's own document on the seen date: a released-countries table (an X per family and "
        "country), the list of country / grid-code settings in the firmware, or a certificate / test-lab declaration against the "
        "named standard, with the models it lists. GridFit shows it as \"fit by the maker's document\" in that country; the grid "
        "operator decides at the application, and where a country has a public list the list is the answer. Model codes are "
        "joined by `match`, a regex over the register code (upper case, spaces removed, comma read as a point).")
class Dumper(yaml.SafeDumper):
    pass


# a country list on one line, as the hand-written files have it
Dumper.add_representer(list, lambda d, v: d.represent_sequence("tag:yaml.org,2002:seq", v,
                       flow_style=bool(v) and all(isinstance(x, str) and len(x) == 2 for x in v)))
KEEP = ("title", "url", "via", "version", "doc_no", "issuer", "cert_no", "issued", "valid_until", "firmware", "kind", "confidence",
        "standards", "note")


def document(src, manifest, key, warn):
    f = CACHE / key / parse.file_name(src)
    m = manifest.get(f"{key}/{f.name}")
    if not f.exists() or not m:
        warn(f"{key}/{src['id']}: no file in cache/evidence — run tools/evidence/fetch.py {key}")
        return None
    try:
        cols = parse.PARSERS[src["parser"]](f, **(src.get("args") or {}))
    except Exception as e:  # noqa: BLE001 — one changed file must not stop the others; the old document stays
        warn(f"{key}/{src['id']}: {e}")
        return None
    doc = {"id": src["id"]}
    for k in KEEP:
        if k in src:
            doc[k] = src[k]
    doc.update(parse.meta(f, **(src.get("meta") or {})))
    doc["seen"] = m["seen"]
    doc["source"] = "tools/evidence"
    fams, used = [], set()
    for fam in src["families"]:
        col = fam.get("column", "*")
        if col not in cols:
            warn(f"{key}/{src['id']}: column '{col}' ({fam['name']}) is not in the document any more")
            continue
        used.add(col)
        out = {"name": fam["name"]}
        if fam.get("match"):
            out["match"] = fam["match"]
        if fam.get("note"):
            out["note"] = fam["note"]
        out["countries"] = [c for c in cols[col] if c not in (fam.get("drop") or [])]
        fams.append(out)
    if "_models" in cols:
        doc["models_in_document"] = models = cols.pop("_models")
        for fam, srcfam in zip(fams, src["families"]):
            if fam.get("match") == "auto":  # exactly the codes the certificate lists
                fam["match"] = "^(" + "|".join(re.escape(m) for m in models) + ")" + srcfam.get("suffix", "") + "$"
            elif fam.get("match") and srcfam.get("check", True) and not any(re.search(fam["match"], m) for m in models):
                warn(f"{key}/{src['id']}: {fam['name']} matches none of the document's model codes")
    for col in set(cols) - used:
        warn(f"{key}/{src['id']}: the document has a column the mapping does not name: '{col}' {cols[col]}")
    doc["families"] = fams
    return doc


def accepts():
    """[(regex over a standard's name, cc)] from data/evidence/rules/accepts.yaml."""
    f = DATA / "rules" / "accepts.yaml"
    rows = yaml.safe_load(f.read_text(encoding="utf-8")) if f.exists() else []
    return [(re.compile(re.escape(s.replace(" ", "")) + r"(?![0-9])", re.I), r["cc"]) for r in rows for s in r["standards"]]


def derive(docs, rules):
    """accepted_in on every family of a certificate whose standard a country's operator names (derived, rebuilt each time)."""
    for d in docs:
        std = [s.replace(" ", "") for s in d.get("standards") or []]
        ccs = sorted({cc for rx, cc in rules if any(rx.search(s) for s in std)}) if d.get("kind") == "certificate" else []
        for fam in d.get("families") or []:
            fam.pop("accepted_in", None)
            extra = [c for c in ccs if c not in (fam.get("countries") or [])]
            if extra and fam.get("match"):
                fam["accepted_in"] = extra


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("brands", nargs="*")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    sources = yaml.safe_load((HERE / "sources.yaml").read_text(encoding="utf-8"))
    mf = CACHE / "manifest.json"
    manifest = json.loads(mf.read_text(encoding="utf-8")) if mf.exists() else {}
    warnings, changed, rules = [], [], accepts()
    keys = list(sources) + sorted(f.stem for f in DATA.glob("*.yaml") if f.stem not in sources)
    for key in keys:
        srcs = sources.get(key) or []
        if a.brands and key not in a.brands:
            continue
        path = DATA / f"{key}.yaml"
        cur = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else None
        brand = (cur or {}).get("brand") or next((s["brand"] for s in srcs if s.get("brand")), key.title())
        docs = list((cur or {}).get("documents") or [])
        for src in srcs:
            if src.get("manual") or not src.get("parser"):
                continue
            d = document(src, manifest, key, warnings.append)
            if d is None:
                continue
            i = next((j for j, x in enumerate(docs) if x["id"] == d["id"]), None)
            if i is None:
                docs.append(d)
            else:
                docs[i] = d
        if not docs:
            continue
        derive(docs, rules)
        out = {"brand": brand, "maker_site": (cur or {}).get("maker_site", ""), "rule": RULE, "documents": docs}
        text = HEADER + yaml.dump(out, Dumper=Dumper, sort_keys=False, allow_unicode=True, width=130)
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            changed.append(path.name)
            if not a.check:
                path.write_text(text, encoding="utf-8")
    for w in warnings:
        print("warning:", w, file=sys.stderr)
    print(("would change: " if a.check else "written: ") + (", ".join(changed) or "nothing"), file=sys.stderr)
    sys.exit(1 if a.check and changed else 0)


if __name__ == "__main__":
    main()
