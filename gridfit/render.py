"""Render the static site from the assembled families with Jinja2."""
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .assemble import CLASS_LABEL, CONN_LABEL, SOURCE_LABEL
from . import registers
from .brands import slug

SITE_NAME = "GridFit"
TAGLINE = "Does it work locally with Home Assistant and evcc?"
REPO_URL = "https://github.com/madisorg/gridfit"


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


def site(root, families, rows, unmatched, regdata, changelog, stats, seen, base_url="", analytics="", reg=None):
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

    if reg:
        pages += registers_site(env, out, reg, families, common)

    for name in ("about", "changelog"):
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


# ---------------------------------------------------------------- grid-register cross-view
def registers_site(env, out, reg, families, common):
    """/registers/: the cross-view hub, one page per brand, model (in >= 2 registers), country, and the change log."""
    devs, snap, log = reg
    R = registers
    env.globals.update(RC=R.CLASS_LABEL, RS=R.STATUS_LABEL, RSHORT=R.STATUS_SHORT, RREG=R.REGISTERS,
                       COUNTRIES=R.COUNTRIES)
    env.filters["best"] = R.best
    env.filters["n"] = lambda v: f"{v:,}"
    meta, pages = snap["meta"], []
    shown = [d for d in devs if d["cls"] in R.PAGE_CLASSES]
    fam_url = {}
    for f in families:
        for m in f["models"]:
            fam_url[(m["brand"], m["norm"])] = (f"{f['brand_slug']}/{f['slug']}/", f"{f['brand']} {f['name']}")
    v1_brands = {f["brand_slug"] for f in families}
    rc = dict(common, snap=snap, meta=meta, not_read=R.NOT_READ)

    def url(d):
        return f"brand/{d['brand_slug']}/{d['slug']}/" if d["page"] else f"brand/{d['brand_slug']}/#m-{_anchor(d)}"

    # hub: a compact JSON index the filter script pages through; the page itself lists brands for no-JS readers
    code = {"listed": "L", "restricted": "R", "limited": "T", "limited-past": "P", "expired": "E", "nein": "N", "other": "O"}
    by_brand = defaultdict(list)
    for d in shown:
        by_brand[d["brand_slug"]].append(d)
    brands = sorted(by_brand, key=lambda b: by_brand[b][0]["brand"].lower())
    bidx = {b: i for i, b in enumerate(brands)}
    order = sorted(shown, key=lambda d: (-d["n"], d["brand"].lower(), d["model"].lower()))
    index = {"countries": R.COUNTRIES, "brands": [by_brand[b][0]["brand"] for b in brands],
             "rows": [[bidx[d["brand_slug"]], d["model"], d["cls"], url(d),
                       "".join(code[R.best(d["cells"][c])] if c in d["cells"] else "-" for c in R.COUNTRIES)]
                      for d in order]}
    (out / "registers").mkdir(parents=True, exist_ok=True)
    (out / "registers/index.json").write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    counts = {c: sum(1 for d in shown if c in d["cells"]) for c in R.COUNTRIES}
    _write(out / "registers/index.html", env.get_template("registers/hub.html.j2").render(
        page="registers/", rel="../", devices=len(shown), pages_n=sum(d["page"] for d in shown),
        multi=sum(1 for d in shown if d["n"] >= 2 and not d["unmatched"]), counts=counts,
        brand_links=[(b, by_brand[b][0]["brand"], len(by_brand[b])) for b in brands], log=log, **rc))
    pages.append("registers/")

    for b in brands:
        ds = sorted(by_brand[b], key=lambda d: (d["model"].lower()))
        for d in ds:
            d["anchor"] = _anchor(d)
        groups = [(c, [d for d in ds if d["cls"] == c]) for c in R.CLASS_LABEL if any(d["cls"] == c for d in ds)]
        name = ds[0]["brand"]
        _write(out / "registers/brand" / b / "index.html", env.get_template("registers/brand.html.j2").render(
            page=f"registers/brand/{b}/", rel="../../../", brand=name, groups=groups, total=len(ds),
            countries_listed=[c for c in R.COUNTRIES if any(c in d["cells"] for d in ds)],
            v1=b if b in v1_brands else "", **rc))
        pages.append(f"registers/brand/{b}/")
        for d in ds:
            if not d["page"]:
                continue
            fam = fam_url.get((d.get("v1brand"), d["norm"]))
            faq = _faq(d, meta)
            _write(out / "registers/brand" / b / d["slug"] / "index.html", env.get_template("registers/model.html.j2").render(
                page=f"registers/brand/{b}/{d['slug']}/", rel="../../../../", d=d, faq=faq, fam=fam,
                faq_ld=[{"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}}
                        for f in faq], **rc))
            pages.append(f"registers/brand/{b}/{d['slug']}/")

    for c in R.COUNTRIES:
        regs = [r for r in R.REGISTERS if R.COUNTRY_OF.get(r, r) == c]
        entries = [e for e in snap["entries"] if e["reg"] in regs]
        words = Counter((e["reg"], e["word"] or e["status"]) for e in entries)
        here = [d for d in shown if c in d["cells"]]
        top = Counter(d["brand_slug"] for d in here).most_common(20)
        _write(out / "registers/country" / c.lower() / "index.html", env.get_template("registers/country.html.j2").render(
            page=f"registers/country/{c.lower()}/", rel="../../../", c=c, regs=regs, rows=len(entries),
            words=sorted(words.items(), key=lambda x: -x[1]), devices=len(here),
            by_class=Counter(d["cls"] for d in here), elsewhere=sum(1 for d in here if d["n"] >= 2),
            other_rows=sum(1 for e in entries if e["cls"] == "other"),
            top=[(b, by_brand[b][0]["brand"], n) for b, n in top], **rc))
        pages.append(f"registers/country/{c.lower()}/")

    _write(out / "registers/changes/index.html", env.get_template("registers/changes.html.j2").render(
        page="registers/changes/", rel="../../", log=log, **rc))
    pages.append("registers/changes/")
    return pages


def _anchor(d):
    return slug(d["model"])[:60]


def _faq(d, meta):
    """One question per register that lists the model, answered in the register's own words."""
    out = []
    for c in registers.COUNTRIES:
        for e in d["cells"].get(c, [])[:1]:
            r = registers.REGISTERS[e["reg"]]
            src = meta.get(e["reg"], {}).get("source_date", "")
            st = registers.STATUS_LABEL[e["show"]]
            q = f"Is the {d['brand']} {d['model']} on the {r['short']}?"
            if e["show"] in ("listed", "restricted", "limited"):
                a = f"Yes — the {r['short']} lists it as “{e['word'] if e['reg'] != 'BE' else 'listed'}”"
            else:
                a = f"The {r['short']} shows it as “{e['word'] or st}”"
            if e["valid"]:
                a += f", until {e['valid']}"
            if e["fw"] and e["reg"] != "BE":
                fw = e["fw"] if len(e["fw"]) <= 80 else e["fw"][:80].rsplit(" ", 1)[0] + " …"
                a += f"; {r['fw_label']}: {fw}"
            a += f" (list dated {src}, checked {e['seen'] if e.get('seen') else meta.get(e['reg'], {}).get('seen', '')})."
            de = ""
            if c == "AT":
                de = (f"Steht der {d['brand']} {d['model']} auf der österreichischen "
                      f"{'Liste der Ladeeinrichtungen' if e['reg'] == 'AT-EV' else 'Wechselrichterliste (TOR Erzeuger Typ A)'}? "
                      f"Laut Liste vom {src}: „{e['word']}“"
                      + (f", befristet bis {e['valid']}" if e["valid"] else "") + ".")
            out.append({"c": c, "q": q, "a": a, "de": de})
    return out
