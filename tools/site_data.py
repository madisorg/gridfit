"""Export the grid-register cross-view for the Astro site (web/), from the committed snapshot.

    python tools/site_data.py            # -> web/.data/registers.json (git-ignored)

Runs the same grouping as build.py (gridfit.registers.devices on the latest snapshot) and writes
what the /registers/ pages need. It reads data/ and changes nothing there.
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from gridfit import registers as R  # noqa: E402
from gridfit.brands import Brands  # noqa: E402

KEEP = ("reg", "show", "word", "maker_raw", "model_raw", "fw", "cert", "id", "valid", "date", "trust", "kva")
EXTRA = ("list", "battery", "setup", "comment", "note", "phases", "type", "category", "kind")


def main():
    snap = R.latest(ROOT)
    devs = R.devices(snap, ROOT / "data/registers/alias.json", snap["date"])
    brands = Brands(ROOT / "data/curated/brands.yaml")
    log = json.loads((ROOT / "data/registers/changelog.json").read_text(encoding="utf-8"))
    shown = [d for d in devs if d["cls"] in R.PAGE_CLASSES]
    out_devs = []
    for d in shown:
        cells = {c: [dict({k: e.get(k) or "" for k in KEEP},
                          extra={k: e["extra"][k] for k in EXTRA if e["extra"].get(k)}) for e in es]
                 for c, es in d["cells"].items()}
        out_devs.append({"brand": d["brand"], "model": d["model"], "norm": d["norm"], "cls": d["cls"],
                         "n": d["n"], "unmatched": d["unmatched"], "variants": d["variants"],
                         "brand_slug": d["brand_slug"], "slug": d.get("slug"), "page": d["page"],
                         "v1brand": brands.canon(d["brand"]) or "", "cells": cells})
    stats = {}
    for c in R.COUNTRIES:
        regs = [r for r in R.REGISTERS if R.COUNTRY_OF.get(r, r) == c]
        entries = [e for e in snap["entries"] if e["reg"] in regs]
        words = Counter((e["reg"], e["word"] or e["status"]) for e in entries)
        stats[c] = {"regs": regs, "rows": len(entries), "other_rows": sum(1 for e in entries if e["cls"] == "other"),
                    "words": [[r, w, n] for (r, w), n in sorted(words.items(), key=lambda x: -x[1])]}
    meta = {k: {f: v.get(f) for f in ("source_date", "seen", "rows", "carried_over", "unread_lp")} for k, v in snap["meta"].items()}
    data = {
        "date": snap["date"], "countries": R.COUNTRIES, "country_of": R.COUNTRY_OF,
        "registers": {k: {f: v.get(f, "") for f in ("country", "short", "name", "operator", "url", "basis", "gate",
                                                    "contains", "terms", "use", "date_label", "fw_label")}
                      for k, v in R.REGISTERS.items()},
        "not_read": R.NOT_READ, "class_label": R.CLASS_LABEL, "status_label": R.STATUS_LABEL,
        "status_short": R.STATUS_SHORT, "meta": meta, "log": log, "stats": stats, "devices": out_devs,
    }
    dest = ROOT / "web/.data/registers.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"registers: {len(out_devs)} devices, {sum(d['page'] for d in out_devs)} model pages -> {dest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
