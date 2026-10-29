"""Build the GridReg dataset and static site in one command.

    python build.py              # download what is older than 6 days, then build
    python build.py --refresh    # download everything again
    python build.py --offline    # build from cache/ only

Writes data/dataset/ (committed: the dataset and its change log) and site/ (git-ignored).
Set GRIDREG_BASE_URL for canonical links and the sitemap, GRIDREG_ANALYTICS to
"plausible:<domain>" or "cloudflare:<token>" to include a cookie-free analytics tag.
"""
import argparse
import csv
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from gridreg import assemble, fetch, render  # noqa: E402
from gridreg.brands import Brands  # noqa: E402

DATASET = ROOT / "data/dataset"
FIELDS = ["id", "brand", "family", "class", "source", "name", "ref", "local", "iot_class", "conn",
          "control", "control_detail", "sponsor", "stars", "updated", "url", "source_url", "seen"]
DIFF_FIELDS = ("local", "control", "conn", "sponsor", "class")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()
    seen = time.strftime("%Y-%m-%d")
    cache = fetch.Cache(ROOT / "cache", args.refresh, args.offline)
    cur = ROOT / "data/curated"
    brands = Brands(cur / "brands.yaml")
    core_cfg = assemble.load_yaml(cur / "ha_core.yaml")
    hacs_cfg = assemble.load_yaml(cur / "hacs.yaml")
    fam_cfg = assemble.load_yaml(cur / "families.yaml")
    regdata = json.loads((ROOT / "data/registers/listing.json").read_text(encoding="utf-8"))

    print("fetching sources ...")
    integrations = fetch.ha_integrations(cache)
    core_probes = fetch.ha_core_probes(cache, [c["domain"] for c in core_cfg])
    hacs_data = fetch.hacs_data(cache)
    by_name = {v["full_name"].lower(): v for v in hacs_data.values()}
    pairs = [(c["repo"], by_name[c["repo"].lower()]["domain"]) for c in hacs_cfg
             if c["repo"].lower() in by_name and by_name[c["repo"].lower()].get("domain")]
    hacs_probes = fetch.hacs_probes(cache, pairs)
    evcc_dir = fetch.evcc_templates(cache)

    print("assembling ...")
    rows = (assemble.ha_core_rows(core_cfg, integrations, core_probes, seen)
            + assemble.hacs_rows(hacs_cfg, hacs_data, hacs_probes, seen)
            + assemble.evcc_rows(evcc_dir, brands, seen))
    for r in rows:
        r["id"] = f"{r['source']}:{r['ref']}:{r['brand']}"
    unknown = sorted(b for b in brands.unknown if b)
    if unknown:
        print(f"  note: {len(unknown)} brand spellings not in brands.yaml:",
              ", ".join(unknown[:40]) + (" ..." if len(unknown) > 40 else ""))
    families, unmatched = assemble.build_families(rows, fam_cfg, regdata["models"])
    for f in families:
        for r in f["rows"]:
            r.setdefault("families", None)
            r.setdefault("_fam", []).append(f"{f['brand_slug']}/{f['slug']}")

    changes = write_dataset(rows, families, seen)
    stats = report(rows, families, regdata)
    render.site(ROOT, families, rows, unmatched, regdata, changes, stats, seen,
                base_url=os.environ.get("GRIDREG_BASE_URL", "").rstrip("/"),
                analytics=os.environ.get("GRIDREG_ANALYTICS", ""))
    print("site written to site/  (preview: python -m http.server 8390 -d site)")


def _flat(r, fam):
    out = {k: r.get(k) for k in FIELDS}
    out["family"] = fam
    out["conn"] = ";".join(r.get("conn") or [])
    return out


def write_dataset(rows, families, seen):
    DATASET.mkdir(parents=True, exist_ok=True)
    table = []
    for f in families:
        for r in f["rows"]:
            table.append(_flat(r, f["name"]))
    table.sort(key=lambda x: (x["brand"].lower(), x["family"].lower(), x["source"], x["ref"]))
    prev_path = DATASET / "rows.json"
    prev = {}
    if prev_path.exists():
        for x in json.loads(prev_path.read_text(encoding="utf-8")):
            prev[(x["id"], x["family"])] = x
    new = {(x["id"], x["family"]): x for x in table}
    log_path = DATASET / "changelog.json"
    log = json.loads(log_path.read_text(encoding="utf-8")) if log_path.exists() else []
    entry = {"date": seen, "added": [], "removed": [], "changed": []}
    if not prev:
        entry["note"] = f"First public dataset: {len(table)} rows in {len(families)} families."
    else:
        entry["added"] = sorted(f"{k[0]} | {k[1]}" for k in new.keys() - prev.keys())
        entry["removed"] = sorted(f"{k[0]} | {k[1]}" for k in prev.keys() - new.keys())
        for k in sorted(new.keys() & prev.keys()):
            for fld in DIFF_FIELDS:
                if new[k].get(fld) != prev[k].get(fld):
                    entry["changed"].append({"row": f"{k[0]} | {k[1]}", "field": fld,
                                             "old": prev[k].get(fld), "new": new[k].get(fld)})
    if entry.get("note"):
        log = [entry]
    elif entry["added"] or entry["removed"] or entry["changed"]:
        log.insert(0, entry)
    prev_path.write_text(json.dumps(table, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    with (DATASET / "rows.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(table)
    fam_out = [{"brand": f["brand"], "family": f["name"], "class": f["class"], "curated": f["curated"],
                "faq": f["faq"], "registers": f["registers"],
                "models": [{"model": m["model"], "registers": m["registers"], "trust": m["trust"]} for m in f["models"]]}
               for f in families]
    (DATASET / "families.json").write_text(json.dumps(fam_out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return log


def report(rows, families, regdata):
    fam_rows = sum(len(f["rows"]) for f in families)
    src = Counter(r["source"] for r in rows)
    cls = Counter(f["class"] for f in families)
    brands = {f["brand"] for f in families}
    linked = sum(len(f["models"]) for f in families)
    stats = {"rows": len(rows), "family_rows": fam_rows, "families": len(families),
             "curated_families": sum(f["curated"] for f in families), "brands": len(brands),
             "by_source": dict(src), "by_class": dict(cls),
             "register_models": len(regdata["models"]), "register_models_linked": linked,
             "local_rows": sum(1 for r in rows if r["local"]),
             "control_rows": sum(1 for r in rows if r["control"] == "write")}
    print(json.dumps(stats, indent=1))
    return stats


if __name__ == "__main__":
    main()
