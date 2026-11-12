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
import html
import json
import pathlib
import re
import sys

import openpyxl
import pdfplumber

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
        # "Windenergie-Wechselrichter" is a wind turbine's inverter, not a PV one: class other (data/registers/classes.yaml)
        cls = ("other" if "wind" in a else "hybrid" if "hybrid" in a else "battery" if "batterie" in a or "speicher" in a
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
        sol, wind, chp, sto, _bak = (bool(s(r[i])) for i in (21, 22, 23, 24, 25))
        if sto and sol:
            return "hybrid"
        # "Backup power system" alone is a generator set (CAT, MWM, Cummins, ...), not storage: data/registers/classes.yaml
        if sto:
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
            add("BE", r[2], be_model(r[2], r[3], r[4]), cls_of(r), status, word,
                kva=(num(r[9]) or num(r[8]) or 0) / 1000 or None)


def be_model(maker, series, model):
    """A bare number in the model cell ("10", "8.5", "5.5/26", "3.0-1") names a unit only with its series (column D):
    KOSTAL "10" was PLENTICORE plus 10, PLENTICORE plus G2 10, PIKO IQ 10, PIKO 10 and PLENTICORE M G3 10 in one device.
    Written as the other lists write them: the maker's own name leaves the series ("Fronius Primo" -> "Primo 3.0-1"), and
    a G2 / Plus / SC tail goes after the number ("PLENTICORE plus 10 G2", "SYMO GEN24 10.0 Plus SC"). A five-digit
    article number (Perceval, as the Dutch list has it too) and a series that is no name ("(40-60)K") are left alone."""
    model, series = s(model), s(series)
    if not re.fullmatch(r"[\d.,/\s-]+K?", model, re.I) or re.fullmatch(r"\d{5,}", model) or not series \
            or "(" in series or series.upper().endswith(model.upper()):
        return model
    words = series.split()
    if len(words) > 1 and norm_maker(words[0])[0] == norm_maker(s(maker))[0]:
        words = words[1:]
    tail = []
    while len(words) > 2 and re.fullmatch(r"G\d|PLUS|SC", words[-1], re.I):
        tail.insert(0, words.pop())
    return " ".join(words + [model] + tail)


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
# "får enbart/endast anslutas/monteras i trefaskoppling" (also misspelt "anlsutas"): a single-phase unit listed only
# as part of a three-phase set — listed with a restriction, the comment is the restriction's wording
SE_THREE_PHASE_ONLY = re.compile(r"\b(enbart|endast)\b.{0,30}\btrefas", re.I)


def se_text(raw):
    """The CSV's code page changes between issues (2026-10-23 cp1252, 2026-11-09 cp850): the header names
    'Löp-nummer' and 'Energikälla', so the code page that spells them is the file's."""
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw[3:].decode("utf-8")
    for enc in ("utf-8", "cp1252", "cp850"):
        try:
            t = raw.decode(enc)
        except UnicodeDecodeError:
            continue
        if "Löp" in t[:200] and "Energikälla" in t[:300]:
            return t
    errors.append("SE: header not recognised in utf-8 / cp1252 / cp850 — read as cp1252")
    return raw.decode("cp1252", errors="replace")


def se_date(v):
    """ISO as written; four Growatt rows carry dd/mm/yyyy."""
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", s(v))
    return f"{m[3]}-{int(m[2]):02d}-{int(m[1]):02d}" if m else s(v)


def read_se():
    f = one("se_*.csv")
    meta["SE"] = {"file": f.name, "source_date": date_in_name(f.name, "")}
    for i, r in enumerate(csv.reader(se_text(f.read_bytes()).splitlines(), delimiter=";")):
        if i == 0 or len(r) < 8 or not s(r[1]):
            continue
        comment = s(r[8])[:200] if len(r) > 8 else ""
        src = s(r[6]).lower()
        if not re.search(r"sol|batteri|vind|nät", src):
            # the energy-source cell holds something else (row 3377: the maker's company name): a PV inverter unless
            # the comment says hybrid
            errors.append(f"SE: energy source {s(r[6])!r} id={s(r[0])} — read as PV")
            src = "sol batteri" if "hybrid" in comment.lower() else "sol"
        cls = ("hybrid" if "sol" in src and "batteri" in src else "battery" if "batteri" in src
               else "inverter" if "sol" in src else "other")
        status, word = ("restricted", comment) if SE_THREE_PHASE_ONLY.search(comment) else ("listed", "listed")
        # 40 Pylontech rows (3313–3362) read "FH3X?8K?HY?3P?10D": a dash the export could not encode, as the family's
        # other rows (2511 "FH3X-8K-HY-3P-10") show
        model = re.sub(r"(?<=[0-9A-Za-z])\?(?=[0-9A-Za-z])", "-", s(r[2]))
        add("SE", r[1], model, cls, status, word, rid=r[0], fw=r[3], date=se_date(r[7]), kva=num(r[4]),
            extra={"phases": s(r[5]), "source": s(r[6]), "comment": comment})


# ---------------------------------------------------------------- EE (HTML: one accordion per maker)
def read_ee():
    f = one("ee_*.html")
    meta["EE"] = {"file": f.name, "source_date": ""}  # the page carries no date
    t = f.read_text(encoding="utf-8", errors="replace")
    heads = list(re.finditer(r'accordion-button__text[^>]*>([^<]+)<', t))
    for i, h in enumerate(heads):
        block = t[h.end():heads[i + 1].start() if i + 1 < len(heads) else len(t)]
        maker = html.unescape(h.group(1))
        for row in re.findall(r"<tr class=\"table__row[^>]*>(.*?)</tr>", block, re.S)[1:]:
            cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
            if len(cells) < 2:
                continue
            model = html.unescape(re.sub(r"<[^>]+>", " ", cells[0]))
            battery = "yes" if "fill-primary" in cells[1] else "no" if "fill-danger" in cells[1] else ""
            add("EE", maker, model, "hybrid" if battery == "yes" else "inverter", "listed", "listed",
                extra={"battery": battery})


# ---------------------------------------------------------------- PL (PDF, ruled table)
# The list is an Excel sheet printed to PDF with every cell ruled, so the cells come from the ruling lines
# (pdfplumber), not from character columns: a layout-mode reader cut words at uneven gutters and let the PPM
# column ("A", "A, B") and the WOS version run into the model and maker cells on whole pages (2026-11-12).
PL_COLS = ["lp", "nr", "date", "wos", "maker", "address", "kind", "model", "ppm", "fw"]
PL_DATE = re.compile(r"\d{2}\.\d{2}\.\d{4}")


def pl_cell(v):
    """Lines of one cell; a line ending in '-' or '/' continues a code on the next line without a space."""
    out = ""
    for line in str(v or "").splitlines():
        line = line.strip()
        if line:
            out += line if not out or out[-1] in "-/" else " " + line
    return out


def pl_rows(f):
    """-> (page, {col: text}) per Lp row; a row the page break cut goes on with the first unnumbered rows of the
    next page, whose cells are appended to it."""
    rows, cont = [], 0
    with pdfplumber.open(str(f)) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            for table in page.extract_tables():
                for r in table:
                    if len(r) != len(PL_COLS):
                        errors.append(f"PL p{pno}: a table row of {len(r)} cells, not {len(PL_COLS)}")
                        continue
                    c = dict(zip(PL_COLS, (pl_cell(x) for x in r)))
                    if c["lp"].startswith("Lp") or "Nr dokumentu" in c["nr"] or not any(c.values()):
                        continue
                    m = re.match(r"(\d{1,5})(\S*)$", c["lp"])
                    if m:
                        # a long certificate number can run into the Lp cell ("1198T" + "C-GCC-…")
                        c["lp"], c["nr"] = m[1], m[2] + c["nr"]
                        rows.append((pno, c))
                    elif rows:
                        cont += 1
                        prev = rows[-1][1]
                        for k, v in c.items():
                            if v and k != "lp":
                                prev[k] = (prev[k] + ("" if prev[k][-1:] in "-/" else " ") + v).strip()
                    else:
                        errors.append(f"PL p{pno}: an unnumbered row before the first Lp: {c}")
    return rows, cont


def read_pl():
    f = one("pl_*.pdf")
    meta["PL"] = {"file": f.name, "source_date": date_in_name(f.name, "")}
    rows, cont = pl_rows(f)
    for pno, cell in rows:
        # the date cell can carry the end of a certificate number that overflowed ("-0 21.07.2031")
        d = PL_DATE.search(cell["date"])
        rest = (cell["date"][:d.start()] + cell["date"][d.end():]).strip() if d else cell["date"]
        nr = (cell["nr"] + ("" if rest.startswith("-") or cell["nr"].endswith("-") else " ") + rest).strip()
        k = cell["kind"].lower()
        cls = ("hybrid" if "hybryd" in k or "hybrid" in k
               else "inverter" if "mikro" in k
               else "battery" if any(w in k for w in ("bateryj", "magazyn", "konwersji", "przekszta", "akumulator"))
               else "inverter" if any(w in k for w in ("falownik", "inwerter", "inverter", "fotowolt", "pv"))
               else "other")
        add("PL", cell["maker"], cell["model"], cls, "listed", "listed", rid=cell["lp"],
            fw=cell["fw"], cert=nr, date=d[0] if d else "",
            extra={"wos": cell["wos"], "ppm": cell["ppm"], "kind": cell["kind"], "micro": "mikro" in k, "page": pno})
    lps = [int(c["lp"]) for _, c in rows]
    top = max(lps) if lps else 0
    got = {int(e["id"]) for e in entries if e["reg"] == "PL"}  # an Lp with an empty model cell was not read either
    missing = sorted(set(range(1, top + 1)) - got)
    dup = sorted(k for k, v in collections.Counter(lps).items() if v > 1)
    # what a column bleed looks like: a model that is only a PPM scope or ends in its row's PPM scope ("…-600 A"),
    # a maker carrying the WOS version, a row without its date
    pl = [e for e in entries if e["reg"] == "PL"]
    scope = re.compile(r"\(?[A-D](\s*,\s*[A-D])*\)?")
    bleed = [e["id"] for e in pl if scope.fullmatch(e["model_raw"]) or not e["date"]
             or re.search(r"\bWOS\b", e["maker_raw"])
             or (e["extra"]["ppm"] and e["model_raw"].endswith(" " + e["extra"]["ppm"]))]
    meta["PL"]["unread_lp"] = missing
    meta["PL"]["column_bleed"] = bleed
    errors.append(f"PL: Lp 1-{top}, read {len(got)}, unread {len(missing)}: {missing}; duplicate Lp {dup}; "
                  f"{cont} rows continued over a page break; column bleed {len(bleed)}: {bleed[:20]}")


for fn in (read_at, read_be, read_nl, read_cz, read_se, read_pl, read_ee):
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
