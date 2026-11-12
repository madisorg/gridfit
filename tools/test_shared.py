"""Tests for the two readers every tool shares: gridfit/strictyaml.py and gridfit/robots.py. Run by `npm test`.
python -I tools/test_shared.py"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from gridfit import strictyaml  # noqa: E402
from gridfit.robots import Robots  # noqa: E402

fails = []


def check(name, got, want):
    if got != want:
        fails.append(f"{name}: got {got!r}, want {want!r}")


# ---- strictyaml: a key written twice is an error; everything else reads as yaml.safe_load reads it
check("plain mapping", strictyaml.load("brand: X\ndocuments:\n- id: a\n- id: b\n"), {"brand": "X", "documents": [{"id": "a"}, {"id": "b"}]})
for name, text in [("doubled top-level key", "brand: X\ndocuments: []\nbrand: X\ndocuments: []\n"),
                   ("doubled key in a list item", "documents:\n- id: a\n  id: b\n")]:
    try:
        strictyaml.load(text)
        fails.append(f"{name}: loaded, should have been refused")
    except Exception as e:  # noqa: BLE001
        check(name + " says which key", "duplicate key" in str(e), True)
for f in sorted((ROOT / "data").rglob("*.yaml")):   # every data file of the repo reads strictly
    try:
        strictyaml.load(f.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        fails.append(f"{f.relative_to(ROOT)}: {str(e).splitlines()[0]}")

# ---- robots: RFC 9309 — longest match, Allow on a tie, wildcards, the product token's group before *
growatt = Robots("User-agent: *\nAllow: /\nDisallow: /upload/\n")
check("en.growatt.com upload", growatt.allowed("*", "https://en.growatt.com/upload/file/x.pdf"), False)
check("en.growatt.com page", growatt.allowed("*", "https://en.growatt.com/products"), True)
check("tie goes to Allow", Robots("User-agent: *\nAllow: /a\nDisallow: /a").allowed("x", "https://h/a/b"), True)
pdf = Robots("User-agent: *\nDisallow: /*.pdf$")
check("*.pdf$ blocks the file", pdf.allowed("x", "https://h/d/x.pdf"), False)
check("*.pdf$ lets a query through", pdf.allowed("x", "https://h/d/x.pdf?y=1"), True)
check("paths are case-sensitive", pdf.allowed("x", "https://h/d/x.PDF"), True)
spec = Robots("User-agent: *\nDisallow: /\n\nUser-agent: gridfit\nAllow: /\nCrawl-delay: 5")
check("own group before *", spec.allowed("GridFit watch (+https://gridfit.eu)", "https://h/x"), True)
check("others get *", spec.allowed("other/1", "https://h/x"), False)
check("crawl-delay of the group", spec.crawl_delay("GridFit watch"), 5.0)
check("a BOM hides nothing", Robots("﻿User-agent: *\nDisallow: /x").allowed("a", "https://h/x/1"), False)
check("no robots.txt", Robots("").allowed("a", "https://h/x"), True)
check("empty Disallow is no rule", Robots("User-agent: *\nDisallow:").allowed("a", "https://h/x"), True)
check("robots.txt itself", Robots("User-agent: *\nDisallow: /").allowed("a", "https://h/robots.txt"), True)

print(f"shared readers: {'0 failures' if not fails else str(len(fails)) + ' FAILURES'}")
for f in fails:
    print("  " + f)
sys.exit(1 if fails else 0)
