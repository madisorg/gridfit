"""Parse the downloaded grid-register files into one entries.jsonl.

    python -I tools/registers/parse.py <raw-dir> <out-dir> <alias.json> <seen-date>

Runs isolated (-I) and lives outside the raw directory: the raw files are downloads, never code.
Writes <out-dir>/entries.jsonl (one line per register row), meta.json (per register: source file,
source date, row count) and errors.txt (rows that could not be read).

Belgium (Synergrid C10/26) is reduced here, at the first step, to maker + model + listed/expired:
its terms allow personal use only, so nothing else from its rows is ever stored.
"""
import collections
import csv
import datetime
import json
import pathlib
import re
import sys

import openpyxl
import pypdf

RAW, OUT, ALIAS_PATH, SEEN = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3]), sys.argv[4]
ALIAS = json.loads(ALIAS_PATH.read_text(encoding="utf-8"))
errors = []
meta = {}

# ---------------------------------------------------------------- normalisation
LEGAL = {"co", "ltd", "limited", "gmbh", "inc", "sa", "s.a", "srl", "bv", "b.v", "nv", "n.v", "ag", "kg",
         "technology", "technologies", "tech", "energy", "power", "new", "electric", "electronics", "electronic",
         "group", "international", "europe", "holding", "holdings", "corporation", "corp", "company", "llc",
         "oy", "ab", "as", "aps", "sp", "z", "o.o", "zoo", "s.p.a", "spa", "systems", "system", "solutions",
         "industrial", "industry", "industries", "renewable", "renewables", "storage", "supply", "digital", "plc"}
# PL rows on a few pages are shifted one column: the maker cell then holds a street address
ADDRESS = re.compile(r"\bul\.|\broad\b|\brd\.|\bstr\.|\bstreet\b|\bblock\b|\bno\.\s*\d|\bfloor\b|\d{2}-\d{3}\b|\b\d{5,6}\b|\broom\b", re.I)
_alias_index = {}


def clean_maker(raw):
    s = re.sub(r"\(.*?\)", " ", raw.lower())
    s = s.replace("&", " ").replace("|", " ")
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    toks = [t for t in s.split() if t not in LEGAL]
    return " ".join(toks) if toks else s


for canon, variants in ALIAS.items():
    if canon.startswith("_"):
        continue
    for v in variants + [canon]:
        _alias_index[re.sub(r"[^a-z0-9]+", " ", v.lower()).strip()] = canon
        _alias_index[clean_maker(v)] = canon


def norm_maker(raw):
    """-> (canonical, grade): 'exact' raw == canonical, 'alias' via the alias table, 'raw' cleanup only."""
    raw = re.sub(r"\b(WO)?S\s*20\d\d", " ", str(raw)).strip()  # PL: the WOS version sometimes bleeds into the maker cell
    raw = re.sub(r"\s+", " ", raw)
    key_full = re.sub(r"[^a-z0-9]+", " ", raw.lower()).strip()
    if key_full in _alias_index:
        c = _alias_index[key_full]
        return c, ("exact" if c.lower() == raw.lower() else "alias")
    cl = clean_maker(raw)
    if cl in _alias_index:
        return _alias_index[cl], "alias"
    first = cl.split()[0] if cl else ""
    if first in _alias_index and len(cl.split()) <= 3:
        return _alias_index[first], "alias"
    return cl.title(), "raw"


SUFFIX = re.compile(r"(?:-|\s)?(EU|SM2|SM|G2EU)$", re.I)


def norm_model(raw):
    s = str(raw or "").strip().upper()
    # a trailing note like "(Connected in Delta)" is a variant of the same unit; "(10 kW)" names a different one
    m = re.search(r"\s*\(([^()]*)\)\s*$", s)
    if m and not re.search(r"\d\s*(KW|KVA|W|KWH)\b", m.group(1)):
        s = s[:m.start()]
    s = SUFFIX.sub("", s)
    s = SUFFIX.sub("", s)
    s = re.sub(r"(\d)\.0\b", r"\1", s)  # "10.0 kW" and "10 kW", "SH8.0RT" and "SH8RT" are the same unit
    return re.sub(r"[\s\-_/\.,()]+", "", s)


def iso(d):
    if d is None or d == "":
        return ""
    if isinstance(d, (datetime.date, datetime.datetime)):
        return d.strftime("%Y-%m-%d")
    s = str(d).strip()
    m = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", s)
    if m:
        return f"{m[3]}-{int(m[2]):02d}-{int(m[1]):02d}"
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    return m[0] if m else ""


def s(v):
    return "" if v is None else re.sub(r"\s+", " ", str(v)).strip()


def num(v):
    try:
        return float(str(v).replace(",", ".").strip())
    except (TypeError, ValueError):
        return None


entries = []


def add(register, maker, model, cls, status, word, *, rid="", fw="", cert="", date="", valid="", kva=None,
        extra=None, unmatched=""):
    if not s(model) or not s(maker):
        errors.append(f"{register}: empty maker/model id={rid!r} maker={s(maker)[:60]!r} model={s(model)[:60]!r}")
        return
    mn, grade = norm_maker(s(maker))
    if not unmatched and grade == "raw" and ADDRESS.search(s(maker)):
        unmatched = "maker cell holds an address (shifted PDF columns)"
    if not unmatched and re.search(r"X{3,}|\*|-XX\b|\bxx\b", s(model)):
        unmatched = "model is a pattern, not a model"
    entries.append({
        "reg": register, "maker_raw": s(maker), "model_raw": s(model), "maker": mn, "maker_grade": grade,
        "norm": norm_model(model), "cls": cls, "status": status, "word": s(word), "id": s(rid),
        "fw": s(fw)[:240], "cert": s(cert), "date": iso(date), "valid": iso(valid), "kva": kva,
        "extra": extra or {}, "unmatched": unmatched,
    })


def sheet_rows(path, sheet):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    return list(wb[sheet].iter_rows(values_only=True))


def one(pattern):
    hits = sorted(RAW.glob(pattern))
    if not hits:
        raise FileNotFoundError(pattern)
    return hits[-1]


def date_in_name(name, fmt):
    m = re.search(r"(\d{2,4})[-_](\d{2})[-_](\d{2})", name)
    if not m:
        return ""
    y = m[1] if len(m[1]) == 4 else "20" + m[1]
    return f"{y}-{m[2]}-{m[3]}"


# ---------------------------------------------------------------- AT
def at_status(word):
    """Plain "Ja" is listed; "Ja - <anything>" carries a condition (power cap, own use, firmware ...)."""
    z = s(word).lower()
    if z.startswith("nein"):
        return "nein"
    if "befristet" in z:
        return "limited"
    if z == "ja":
        return "listed"
    return "restricted" if z.startswith("ja") else "other"


def read_at():
    f = one("at_typ_a*.xlsx")
    meta["AT"] = {"file": f.name, "source_date": date_in_name(f.name, "")}
    for r in sheet_rows(f, "Export")[1:]:
        if not any(r):
            continue
        marke, typ, pw, ps, ph, art, zul, fw, bef, usv = (list(r) + [None] * 10)[:10]
        a = s(art).lower()
        cls = ("hybrid" if "hybrid" in a else "battery" if "batterie" in a or "speicher" in a
               else "inverter" if "wechselrichter" in a else "other")
        add("AT", marke, typ, cls, at_status(zul), zul, fw=fw, valid=bef, kva=num(ps) or num(pw),
            extra={"phases": s(ph), "type": s(art)})
    f = one("at_laden*.xlsx")
    meta["AT-EV"] = {"file": f.name, "source_date": date_in_name(f.name, "")}
    for r in sheet_rows(f, "data")[1:]:
        if not any(r):
            continue
        marke, typ, kva, ph, art, ans, r37, r25, fw, bef = (list(r) + [None] * 13)[:10]
        add("AT-EV", marke, typ, "wallbox", at_status(r37), r37, fw=fw, valid=bef, kva=num(kva),
            extra={"phases": s(ph), "ac_dc": s(art), "feed_in_r25": s(r25)})


# ---------------------------------------------------------------- BE (maker, model, listed/expired only)
def read_be():
    f = one("be_*.xlsx")
    rows = sheet_rows(f, "C10-26 power-generating units")
    meta["BE"] = {"file": f.name, "source_date": iso(rows[6][1]) if len(rows) > 6 else ""}

    def cls_of(r):
        sol, wind, chp, sto, bak = (bool(s(r[i])) for i in (21, 22, 23, 24, 25))
        if sto and sol:
            return "hybrid"
        if sto or bak:
            return "battery"
        if sol:
            return "inverter"
        return "other"

    for sheet, status, word in (("C10-26 power-generating units", "listed", "listed"),
                                ("C10-26 expired homologations", "expired", "expired homologation")):
        for r in (rows if status == "listed" else sheet_rows(f, sheet))[10:]:
            if not s(r[1]) and not s(r[4]):
                continue
            # power is read only to tell plug-in units from the rest; it is not stored
            add("BE", r[2], r[4], cls_of(r), status, word, kva=(num(r[9]) or num(r[8]) or 0) / 1000 or None)


# ---------------------------------------------------------------- NL
def read_nl():
    for pat, cls, part in (("nl_power*.xlsx", "inverter", "generation"), ("nl_electrical*.xlsx", "battery", "storage")):
        f = one(pat)
        rows = sheet_rows(f, "Goedgekeurde omvormers Type A")
        m = re.search(r"(\d{1,2}) (\w+) (\d{4})", s(rows[2][0]))
        months = ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus", "september",
                  "oktober", "november", "december"]
        d = f"{m[3]}-{months.index(m[2].lower()) + 1:02d}-{int(m[1]):02d}" if m and m[2].lower() in months else ""
        meta.setdefault("NL", {"file": [], "source_date": d})["file"].append(f.name)
        for r in rows[5:]:
            if not s(r[0]) or s(r[0]) == "Merk":
                continue
            add("NL", r[0], r[1], cls, "listed", "listed", extra={"list": part})


# ---------------------------------------------------------------- CZ
def read_cz():
    f = one("cz_*.xlsx")
    first = sheet_rows(f, "Schválené střídače")
    meta["CZ"] = {"file": f.name, "source_date": iso(first[0][1])}
    for sheet, cls in (("Schválené střídače", "inverter"), ("Schválené střídače - ZUE", "battery")):
        for r in (first if sheet == "Schválené střídače" else sheet_rows(f, sheet))[2:]:
            if not s(r[0]) or not s(r[1]) or s(r[0]).startswith(("„", "V ")):
                continue
            for model in str(r[1]).split("\n"):  # one cell may carry several models
                if s(model):
                    add("CZ", r[0], model, cls, "listed", "listed", fw=r[2], cert=r[4], date=r[6],
                        extra={"setup": s(r[3]), "cert_date": iso(r[5]), "category": s(r[7]), "note": s(r[8])[:200]})


# ---------------------------------------------------------------- SE
def read_se():
    f = one("se_*.csv")
    meta["SE"] = {"file": f.name, "source_date": date_in_name(f.name, "")}
    for i, r in enumerate(csv.reader(f.read_text(encoding="cp1252").splitlines(), delimiter=";")):
        if i == 0 or len(r) < 8 or not s(r[1]):
            continue
        src = s(r[6]).lower()
        cls = ("hybrid" if "sol" in src and "batteri" in src else "battery" if "batteri" in src
               else "inverter" if "sol" in src else "other")
        add("SE", r[1], r[2], cls, "listed", "listed", rid=r[0], fw=r[3], date=r[7], kva=num(r[4]),
            extra={"phases": s(r[5]), "source": s(r[6]), "comment": s(r[8])[:200] if len(r) > 8 else ""})


# ---------------------------------------------------------------- PL (PDF, layout mode)
PL_LABELS = ["Nr dokumentu", "Data akceptacji", "Wersja WOS", "Nazwa producenta", "Adres producenta",
             "Rodzaj Urządzenia", "Typ model", "PPM:", "Wersja"]
PL_COLS = ["nr", "date", "wos", "maker", "address", "kind", "model", "ppm", "fw"]
LP = re.compile(r"^\s{0,4}\d{1,4}\s{2,}")


def pl_boundaries(lines):
    """Column boundaries from low-ink gutters; nine wide runs right of the Lp digits are the boundaries,
    otherwise the run nearest to the midpoint of two adjacent header labels."""
    h1 = next((l for l in lines[:30] if "Nr dokumentu" in l), None)
    h2 = next((l for l in lines[:30] if "Wersja WOS" in l), None)
    if not h1 or not h2:
        return None, "header missing"
    centres = [3]
    for lab in PL_LABELS:
        line = h2 if lab == "Wersja WOS" else h1
        pos = line.rfind(lab) if lab == "Wersja" else line.find(lab)
        if pos < 0:
            return None, f"label {lab} missing"
        centres.append(pos + len(lab) // 2)
    data = [l for l in lines[30:] if l.strip()]
    width = max(len(l) for l in lines) + 1
    ink = [sum(1 for l in data if len(l) > c and l[c] != " ") for c in range(width)]
    thr = max(1, len(data) // 20)
    runs, x = [], 0
    while x < width:
        if ink[x] <= thr:
            y = x
            while y < width and ink[y] <= thr:
                y += 1
            if y - x >= 2:
                runs.append((x + y) // 2)
            x = y
        else:
            x += 1
    runs9 = [r for r in runs if r > 4]
    if len(runs9) == 9:
        return [0] + runs9 + [width + 1], ""
    bounds, used = [0], set()
    for a, b in zip(centres, centres[1:]):
        mid = (a + b) / 2
        cand = sorted((abs(r - mid), r) for r in runs if r not in used and r > bounds[-1])
        if not cand:
            return None, "no gutter"
        r = cand[0][1]
        used.add(r)
        bounds.append(r)
    bounds.append(width + 1)
    return bounds, ""


def pl_split_block(b):
    """Wrapped cell text sits above and below the Lp line: each line goes to the nearest Lp line."""
    lp_idx = [i for i, l in enumerate(b) if LP.match(l)]
    if len(lp_idx) <= 1:
        return [b] if lp_idx else []
    groups = [[] for _ in lp_idx]
    for i, l in enumerate(b):
        d = [(abs(i - j), -j) for j in lp_idx]
        groups[lp_idx.index(-min(d)[1])].append(l)
    return groups


def read_pl():
    f = one("pl_*.pdf")
    meta["PL"] = {"file": f.name, "source_date": date_in_name(f.name, "")}
    seen_lp, n_bad = set(), 0
    for pno, page in enumerate(pypdf.PdfReader(f).pages, 1):
        lines = page.extract_text(extraction_mode="layout").splitlines()
        bounds, why = pl_boundaries(lines)
        if bounds is None:
            errors.append(f"PL p{pno}: {why}, page skipped")
            continue
        hdr_end = max((i for i, l in enumerate(lines[:30]) if "Firmware version" in l or "Certyfikat / Certificate" in l),
                      default=12)
        blocks, cur = [], []
        for l in lines[hdr_end + 1:]:
            if l.strip():
                cur.append(l)
            elif cur:
                blocks.append(cur)
                cur = []
        if cur:
            blocks.append(cur)
        for b0 in blocks:
            if not any(LP.match(l) for l in b0):
                n_bad += any(re.search(r"[A-Za-z0-9]", l) for l in b0) and not any("Data publikacji" in l for l in b0)
                continue
            for b in pl_split_block(b0):
                lp = re.match(r"^\s*(\d+)", next(l for l in b if LP.match(l)))[1]
                cells, shifted = collections.defaultdict(list), False
                for l in b:
                    for ci, col in enumerate(PL_COLS):
                        a, z = bounds[ci + 1], bounds[ci + 2]
                        if l[a:z].strip():
                            cells[col].append(l[a:z].strip())
                        if len(l) > z > 0 and l[z - 1] != " " and l[z] != " ":
                            shifted = True
                cell = {k: " ".join(v) for k, v in cells.items()}
                k = cell.get("kind", "").lower()
                cls = ("hybrid" if "hybryd" in k or "hybrid" in k
                       else "inverter" if "mikro" in k
                       else "battery" if any(w in k for w in ("bateryj", "magazyn", "konwersji", "przekszta", "akumulator"))
                       else "inverter" if any(w in k for w in ("falownik", "inwerter", "inverter", "fotowolt", "pv"))
                       else "other")
                seen_lp.add(int(lp))
                add("PL", cell.get("maker", ""), cell.get("model", ""), cls, "listed", "listed", rid=lp,
                    fw=cell.get("fw", ""), cert=cell.get("nr", ""), date=cell.get("date", ""),
                    extra={"wos": cell.get("wos", ""), "ppm": cell.get("ppm", ""), "kind": cell.get("kind", ""),
                           "micro": "mikro" in k, "page": pno},
                    unmatched="a word crosses a PDF column boundary" if shifted else "")
    top = max(seen_lp) if seen_lp else 0
    got = {int(e["id"]) for e in entries if e["reg"] == "PL"}  # an Lp with an empty model cell was not read either
    missing = sorted(set(range(1, top + 1)) - got)
    meta["PL"]["unread_lp"] = missing
    errors.append(f"PL: Lp 1-{top}, read {len(got)}, unread {len(missing)}: {missing}; "
                  f"{n_bad} text blocks without an Lp number")


for fn in (read_at, read_be, read_nl, read_cz, read_se, read_pl):
    before = len(entries)
    try:
        fn()
    except Exception as e:  # one bad source must not hide the others
        errors.append(f"{fn.__name__} FAILED: {e!r}")
    print(f"{fn.__name__}: {len(entries) - before} rows")

for reg in meta:
    meta[reg]["rows"] = sum(1 for e in entries if e["reg"] == reg)
    meta[reg]["seen"] = SEEN
OUT.mkdir(parents=True, exist_ok=True)
with (OUT / "entries.jsonl").open("w", encoding="utf-8") as fh:
    for e in entries:
        fh.write(json.dumps(e, ensure_ascii=False) + "\n")
(OUT / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "errors.txt").write_text("\n".join(errors) + "\n", encoding="utf-8")
print(f"{len(entries)} entries, {len(errors)} error lines -> {OUT}")
