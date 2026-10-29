"""Render the static site from the assembled families with Jinja2."""
import json
import shutil
from collections import defaultdict
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .assemble import CLASS_LABEL, CONN_LABEL, SOURCE_LABEL
from .brands import slug

SITE_NAME = "GridReg"
TAGLINE = "Does it work locally with Home Assistant and evcc?"
REPO_URL = "https://github.com/madisorg/gridreg"


def _env(root: Path):
    env = Environment(loader=FileSystemLoader(root / "templates"), autoescape=select_autoescape(["html", "j2"]),
                      trim_blocks=True, lstrip_blocks=True)
    env.globals.update(SITE=SITE_NAME, TAGLINE=TAGLINE, REPO=REPO_URL, CLASS=CLASS_LABEL,
                       CONN=CONN_LABEL, SOURCE=SOURCE_LABEL)
    env.filters["conn"] = lambda xs: ", ".join(CONN_LABEL.get(x, x) for x in xs)
    env.filters["tojson_ld"] = lambda v: json.dumps(v, ensure_ascii=False).replace("</", "<\\/")
    return env


def _write(path: Path, html: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def site(root, families, rows, unmatched, regdata, changelog, stats, seen, base_url="", analytics=""):
    out = root / "site"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir()
    shutil.copytree(root / "static", out / "static")
    env = _env(root)
    common = {"seen": seen, "base_url": base_url, "analytics": analytics, "registers": regdata["registers"],
              "stats": stats}
    pages = []

    by_brand = defaultdict(list)
    for f in families:
        by_brand[f["brand"]].append(f)
    brand_list = sorted(by_brand, key=str.lower)

    # index: one compact entry per family, filtered client-side
    index_rows = []
    # curated families (the brands people ask about) first, the long tail after
    for f in sorted(families, key=lambda f: (not f["curated"], f["brand"].lower(), f["name"].lower())):
        rs = f["rows"]
        index_rows.append({
            "b": f["brand"], "f": f["name"], "u": f"{f['brand_slug']}/{f['slug']}/", "c": f["class"],
            "n": sorted({c for r in rs for c in r["conn"]}),
            "l": 2 if any(r["local"] and r["source"] != "evcc" for r in rs) else (1 if any(r["local"] for r in rs) else 0),
            "w": int(any(r["control"] == "write" and r["local"] for r in rs)),
            "s": sorted({r["source"] for r in rs}), "r": f["registers"], "m": len(f["models"]),
        })
    conns = sorted({c for x in index_rows for c in x["n"]}, key=lambda c: list(CONN_LABEL).index(c))
    _write(out / "index.html", env.get_template("index.html.j2").render(
        page="", rel="", brands=brand_list, conns=conns, total=len(index_rows), rows=index_rows, **common))
    pages.append("")

    for brand in brand_list:
        bs = slug(brand)
        fams = by_brand[brand]
        _write(out / bs / "index.html", env.get_template("brand.html.j2").render(
            page=f"{bs}/", rel="../", brand=brand, families=fams, unmatched=unmatched.get(brand, []), **common))
        pages.append(f"{bs}/")
        for f in fams:
            _write(out / bs / f["slug"] / "index.html", env.get_template("family.html.j2").render(
                page=f"{bs}/{f['slug']}/", rel="../../", f=f, **common))
            pages.append(f"{bs}/{f['slug']}/")

    for name in ("about", "changelog", "registers"):
        _write(out / name / "index.html", env.get_template(f"{name}.html.j2").render(
            page=f"{name}/", rel="../", changelog=changelog, **common))
        pages.append(f"{name}/")

    (out / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n" + (f"Sitemap: {base_url}/sitemap.xml\n" if base_url else ""), encoding="utf-8")
    if base_url:
        urls = "".join(f"<url><loc>{base_url}/{p}</loc><lastmod>{seen}</lastmod></url>" for p in pages)
        (out / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            + urls + "</urlset>", encoding="utf-8")
    print(f"  {len(pages)} pages")
