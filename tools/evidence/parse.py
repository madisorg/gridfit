"""Evidence layer, step 1: read a maker's country document into {column or family: [country codes]}.

Imported by build.py; run alone it prints what one file gives:

    python -I tools/evidence/parse.py xtable cache/evidence/kostal/Released-countries-inverter.pdf
    python -I tools/evidence/parse.py codes cache/evidence/goodwe/x.pdf --start "Safety" --end "Commissioning"

Parsers (named in tools/evidence/sources.yaml as `parser`):
  xtable  a released-countries matrix: one row per country (ISO code in the first column), one column per family
          with a rotated header, an X where the family is released. Columns are found by x position, so a family
          added to the document becomes a new key, not a misread.
  codes   the list of selectable country / grid-code settings in a manual or a code list: every country named
          (English name, or a code in a grid-code token like "EN50549-EE", "EE-LV") between `start` and `end`
          patterns. One list per document, given to the families the source names.
  pages   `codes`, but per family: `sections` maps a family to its own start/end patterns.
  cert    a certificate: proves `standard` and the `models` pattern are in the text; the countries come from the
          standard (data/evidence/rules/accepts.yaml), not from the file.
The files are untrusted data; nothing here evaluates them.
"""
import re
import sys
import urllib.parse
from collections import defaultdict
from pathlib import Path

import pdfplumber

# EU+ and neighbours, the names makers print in their setting lists
NAMES = {
    "AL": ["Albania"], "AT": ["Austria", "Österreich"], "BA": ["Bosnia"], "BE": ["Belgium", "Belgique"], "BG": ["Bulgaria"],
    "CH": ["Switzerland", "Schweiz"], "CY": ["Cyprus"], "CZ": ["Czech", "Czechia"], "DE": ["Germany", "Deutschland"],
    "DK": ["Denmark", "Danmark"], "EE": ["Estonia", "Eesti"], "ES": ["Spain", "España"], "FI": ["Finland", "Suomi"],
    "FR": ["France"], "GB": ["United Kingdom", "Great Britain", "UK"], "GR": ["Greece"], "HR": ["Croatia"],
    "HU": ["Hungary"], "IE": ["Ireland"], "IS": ["Iceland"], "IT": ["Italy", "Italia"], "LT": ["Lithuania"],
    "LU": ["Luxembourg"], "LV": ["Latvia"], "ME": ["Montenegro"], "MK": ["North Macedonia", "Macedonia"], "MT": ["Malta"],
    "NL": ["Netherlands", "Netherland", "Nederland"], "NO": ["Norway", "Norge"], "PL": ["Poland", "Polska"], "PT": ["Portugal"],
    "RO": ["Romania"], "RS": ["Serbia"], "SE": ["Sweden", "Sverige"], "SI": ["Slovenia"], "SK": ["Slovakia"],
    "TR": ["Turkey", "Türkiye"], "UA": ["Ukraine"],
}
CODES = set(NAMES)


def file_name(src):
    """The cache file of a source: its `file`, else the last part of its URL."""
    return src.get("file") or urllib.parse.unquote(urllib.parse.urlsplit(src["url"]).path.rsplit("/", 1)[-1])


def text_of(pdf, first=None):
    """Page texts; the whole file's are kept next to it as <file>.pages.txt, so a 300-page manual is read once per download."""
    pdf = Path(pdf)
    cache = pdf.with_name(pdf.name + ".pages.txt")
    if cache.exists() and cache.stat().st_mtime >= pdf.stat().st_mtime:
        return cache.read_text(encoding="utf-8").split("\f")[:first]
    with pdfplumber.open(str(pdf)) as doc:
        if first:
            return [p.extract_text() or "" for p in doc.pages[:first]]
        pages = [p.extract_text() or "" for p in doc.pages]
    cache.write_text("\f".join(pages), encoding="utf-8")
    return pages


def countries_in(text, codes=True, ignore=()):
    """Country codes named in a piece of text: English/local names, and two-letter codes standing alone or in a
    grid-code token (EN50549-EE, EE_LV, "EE:"). Bare codes are only read when `codes` is set: in prose "IT" or "DE"
    are words."""
    found = set()
    for cc, names in NAMES.items():
        if any(re.search(r"(?<![A-Za-z])" + re.escape(n) + r"(?![a-z])", text) for n in names):
            found.add(cc)
    if codes:
        for m in re.finditer(r"(?<![A-Za-z])([A-Z]{2})(?![a-z])", text):
            if m.group(1) in CODES and m.group(1) not in {"IS", "ME", *ignore}:  # English words in upper case
                found.add(m.group(1))
    return found


def between(pages, start, end):
    t = "\n".join(pages)
    m = re.search(start, t, re.S | re.I)
    if not m:
        raise ValueError(f"start pattern not found: {start}")
    rest = t[m.end():]
    e = re.search(end, rest, re.S | re.I) if end else None
    return rest[: e.start()] if e else rest


def xtable(pdf, page=0, **_):
    """{column header: [ISO codes]} from a matrix with rotated column headers and X marks."""
    with pdfplumber.open(str(pdf)) as doc:
        p = doc.pages[page]
        words = p.extract_words()
    rows = {w["text"]: (w["top"] + w["bottom"]) / 2 for w in words if w.get("upright", True) and w["text"] in CODES and w["x0"] < 90}
    if not rows:
        raise ValueError("no country rows")
    first = min(rows.values())
    head = defaultdict(list)
    for w in words:
        if not w.get("upright", True) and w["bottom"] < first:
            head[round(w["x0"])].append(w)
    cols = {}
    for x, ws in head.items():
        # rotated 90° counter-clockwise: each word comes out reversed, and the reading order is bottom to top
        cols[x] = " ".join(w["text"][::-1] for w in sorted(ws, key=lambda w: -w["top"]))
    xs = sorted(cols)
    out = {cols[x]: set() for x in xs}
    for w in words:
        if w["text"] != "X" or w["top"] < first - 5:
            continue
        cx = (w["x0"] + w["x1"]) / 2
        x = min(xs, key=lambda c: abs(c + 4 - cx))
        cy = (w["top"] + w["bottom"]) / 2
        cc = min(rows, key=lambda c: abs(rows[c] - cy))
        if abs(rows[cc] - cy) < 6:
            out[cols[x]].add(cc)
    return {k: sorted(v) for k, v in out.items() if v}


def codes(pdf, start, end=None, bare_codes=True, ignore=(), **_):
    return {"*": sorted(countries_in(between(text_of(pdf), start, end), bare_codes, ignore))}


def pages(pdf, sections, bare_codes=True, **_):
    t = text_of(pdf)
    return {fam: sorted(countries_in(between(t, s["start"], s.get("end")), bare_codes)) for fam, s in sections.items()}


def cert(pdf, standard, models=None, **_):
    """A certificate names no country: it certifies a standard for models. The source states both; this proves they are
    in the text (a scan with no text layer, or a file that changed, fails loudly) and returns the model codes it finds."""
    t = re.sub(r"[ \t]+", " ", "\n".join(text_of(pdf)))
    # "AF*-TH (*=3K, 4K, 5K)" is three models; write them out so `models` finds each
    t += "\n" + "\n".join(f"{m.group(1)}{v.strip()}{m.group(2)}" for m in re.finditer(r"([\w.]+)\*([\w.\-/]*)\s*\(\s*\*\s*=\s*([^)]*)\)", t)
                          for v in m.group(3).split(","))
    if not re.search(standard, t, re.I):
        raise ValueError(f"standard /{standard}/ is not in the text (a scan without a text layer?)")
    found = sorted({m.group(0).upper().replace(" ", "") for m in re.finditer(models, t, re.I)}) if models else []
    if models and not found:
        raise ValueError(f"no model code /{models}/ in the text")
    return {"*": [], "_models": found}


def meta(pdf, version=None, doc_no=None, cert_no=None, issued=None, **_):
    """The document's own version / number, by the patterns the source gives; several groups are joined by a space
    (the text layer drops spaces between columns: "V2.22026-09-15" is version V2.2 of 2026-09-15)."""
    t = "\n".join(text_of(pdf, first=2))
    out = {}
    for k, pat in (("version", version), ("doc_no", doc_no), ("cert_no", cert_no), ("issued", issued)):
        if pat:
            m = re.search(pat, t)
            if m:
                v = " ".join(g for g in m.groups() if g)
                out[k] = re.sub(r"\s+", " ", re.sub(r"\s*/\s*", "/", v)).strip()
    return out


PARSERS = {"xtable": xtable, "codes": codes, "pages": pages, "cert": cert}

if __name__ == "__main__":
    kind, path, *rest = sys.argv[1:]
    kw = {}
    for i in range(0, len(rest), 2):
        kw[rest[i].lstrip("-")] = rest[i + 1]
    for k, v in PARSERS[kind](Path(path), **kw).items():
        print(f"{k}: {' '.join(v)}")
