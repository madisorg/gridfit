"""Requirement check, model × country: what the maker's datasheet shows, what the maker's document proves, and
what neither says — one state per requirement of every country profile, for every register model.

    python tools/check/run.py              # writes web/.data/checks.json, prints coverage per country
    python tools/check/run.py --validate   # only checks the profiles' `check` blocks against the schema (docs/checks.md)
    python tools/check/run.py --fixture tools/check/fixtures/gr --out web/.data/checks-fixture.json
                                           # the same run over a test fixture (profiles/, specs/, evidence/, registers.json)

Inputs: data/profiles/*.yaml (`edition`, `document_must_cite`, `must_meet[].check`), data/specs/*.yaml (the datasheet
layer, matched like tools/specs/build.py), data/evidence/*.yaml (the maker's documents, matched like
web/src/lib/evidence.ts) and web/.data/registers.json (the register models). Nothing is guessed: a requirement whose
value the sheet does not state and no document covers is "not shown", never "fails". "Outside by datasheet" needs a
number that is present and clearly outside the rule (an 8 kW single-phase unit in Italy; a unit over the type-A line).
"""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # the coverage line has × and · (a cp1252 console)

ROOT = Path(__file__).resolve().parents[2]  # runs from web/ (npm run build) as well as from the repo root
sys.path.insert(0, str(ROOT))  # gridfit/ (strictyaml); -I leaves the repo off the path
from gridfit import strictyaml  # noqa: E402 — a key written twice is an error, not a silent last-wins
OUT = ROOT / "web/.data/checks.json"
REG = ROOT / "web/.data/registers.json"
PROFILES, SPECS, EVIDENCE = ROOT / "data/profiles", ROOT / "data/specs", ROOT / "data/evidence"

CLASSES = ("inverter", "hybrid", "battery", "plug-in", "wallbox")
# a charging point is checked only against an item whose applies.classes names it (Italy's CEI 0-21 Allegato X): the
# generator rules are not a charger's, so every other item is "not applicable" for it, and a country with no such item
# has no block for it
CHARGER = "wallbox"
KINDS = {"range", "max", "min", "phases", "cosphi", "stated", "settable", "document", "none"}
# the sheet fields a check reads; all but phases/ac_kw/ac_kva are optional in data/specs, present only where the sheet states them
FIELDS = {"ac_kw", "ac_kva", "ac_a", "phases", "freq_hz", "vac_v", "vac_pct", "cosphi", "idc_pct", "thdi_pct", "fsw_khz", "isc_a"}
RANGE_FIELDS = {"freq_hz", "vac_v", "vac_pct"}
PROVERS = {"datasheet", "document", "operator"}
# what a power or current line means in that country: the RfG type, a procedure (notification vs full application),
# the phase rule, the EMC standard class (IEC 61000-3-2/-3 up to 16 A per phase, -3-11/-3-12 above), where protection sits
MEANINGS = {"rfg-type", "procedure", "phases", "emc-class", "protection"}
# which kind of maker's document the country's operator takes as evidence
ACCEPTS = {"generic-en50549-1", "national-declaration", "country-release"}
GENERIC = ("EN 50549", "EN 50438")
POSITIVE = ("listed", "restricted", "limited")   # a list entry that admits the model (registers.json `show`)
# states: S meets by datasheet, P the sheet's range covers it and the operator sets the values at commissioning,
# D meets by maker's document, O documented for an older edition (this item changed since), R checked by the operator's
# own list (the model is on it and the profile's `list_checks` names the item as one the operator checks), N not shown,
# L over a line by datasheet (another RfG type, procedure, EMC class or protection set-up applies — not a breach),
# X outside by datasheet, I no check (optional / installation-level), V within a line by the list's figure and W over a
# line by the list's figure (the operator's list states the type's kW or kVA and phases: weaker than the maker's sheet,
# used only where neither a sheet nor a document answers the row — never S)
STATES = ("S", "P", "D", "O", "R", "V", "W", "N", "L", "X", "I")
POWER_FIELDS = ("ac_kw", "ac_kva")
LINES = {"rfg-type", "procedure", "emc-class", "protection"}   # over these the rule changes; over "phases" it is broken
UNIT = {"ac_kw": " kW", "ac_kva": " kVA", "ac_a": " A", "idc_pct": " %", "thdi_pct": " %", "fsw_khz": " kHz", "isc_a": " A", "cosphi": "",
        "freq_hz": " Hz", "vac_v": " V"}
LABEL = {"thdi_pct": "current THD", "idc_pct": "DC injection", "fsw_khz": "switching frequency", "isc_a": "short-circuit current",
         "cosphi": "cos φ", "ac_a": "max AC current", "freq_hz": "frequency range", "vac_v": "voltage range"}
YM = re.compile(r"(20\d\d)-(\d\d)")
YMD = re.compile(r"20\d\d-\d\d-\d\d")
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")


def day_words(iso: str) -> str:
    """2027-03-01 -> '1 March 2027'"""
    y, m, d = iso.split("-")
    return f"{int(d)} {MONTHS[int(m) - 1]} {y}"


def norm(code: str) -> str:
    return re.sub(r"\s+", "", code.upper()).replace(",", ".")


# ---- schema ---------------------------------------------------------------------------------------------------------
def validate_profile(p: dict, name: str) -> list[str]:
    errs = []
    e = p.get("edition")
    if not isinstance(e, dict) or not all(isinstance(e.get(k), str) and e.get(k) for k in ("norm", "id", "date", "label")):
        errs.append(f"{name}: edition needs norm, id, date (YYYY-MM), label")
    elif not YM.fullmatch(e["date"]):
        errs.append(f"{name}: edition.date must be YYYY-MM, got {e['date']!r}")
    elif e.get("transition_until") is not None and not (isinstance(e["transition_until"], str) and YMD.fullmatch(e["transition_until"])
                                                       and e["transition_until"][:7] > e["date"]):
        errs.append(f"{name}: edition.transition_until must be YYYY-MM-DD, after the edition's date")
    acc = p.get("accepts")
    if not isinstance(acc, list) or not acc or not set(acc) <= ACCEPTS:
        errs.append(f"{name}: accepts must be a non-empty subset of {sorted(ACCEPTS)}")
    cite = p.get("document_must_cite")
    if not isinstance(cite, list) or not cite or not all(isinstance(c, str) and c for c in cite):
        errs.append(f"{name}: document_must_cite must be a non-empty list of strings")
    ids = {m.get("id") for m in p.get("must_meet") or []}
    lc = p.get("list_checks")
    if lc is not None:
        if not isinstance(lc, dict) or not all(isinstance(lc.get(k), str) and lc[k] for k in ("word", "what", "not_carried")):
            errs.append(f"{name}: list_checks needs word, what and not_carried")
        elif not isinstance(lc.get("items"), list) or not lc["items"] or not set(lc["items"]) <= ids:
            errs.append(f"{name}: list_checks.items must be must_meet ids")
        elif any(m["check"].get("kind") == "none" or "document" not in (m["check"].get("provable_by") or [])
                 for m in p["must_meet"] if m.get("id") in lc["items"]):
            errs.append(f"{name}: list_checks.items are items a document can prove (a list stands in for the papers the operator read)")
        ow = lc.get("only_where") or {}
        if not isinstance(ow, dict) or not set(ow) <= set(lc.get("items") or []):
            errs.append(f"{name}: list_checks.only_where is keyed by list_checks.items")
        for k, w in (ow.items() if isinstance(ow, dict) else []):
            if not (isinstance(w, dict) and set(w) == {"field", "match", "else"} and all(isinstance(w[x], str) and w[x] for x in w)):
                errs.append(f"{name}: list_checks.only_where.{k} needs field, match and else (strings) only")
                continue
            try:
                re.compile(w["match"])
            except re.error as x:
                errs.append(f"{name}: list_checks.only_where.{k}.match is not a regex: {x}")
        fg = lc.get("figures")
        if fg is not None and not (isinstance(fg, dict) and set(fg) <= {"power", "phases", "phases_not_if"} and fg.get("power") in ("kw", "kva")
                                   and isinstance(fg.get("phases", False), bool) and isinstance(fg.get("phases_not_if", ""), str)):
            errs.append(f"{name}: list_checks.figures needs power (kw | kva), optional phases (true/false) and phases_not_if (a regex on the row's comment)")
    if p.get("on_application") is not None and not (isinstance(p["on_application"], str) and p["on_application"]):
        errs.append(f"{name}: on_application must be a sentence")
    seen = set()
    for i, m in enumerate(p.get("must_meet") or []):
        where = f"{name}: must_meet[{i}]"
        for k in ("id", "rule", "value"):
            if not isinstance(m.get(k), str) or not m[k]:
                errs.append(f"{where}: {k} missing")
        mid = m.get("id", "")
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", mid):
            errs.append(f"{where}: id {mid!r} is not kebab-case")
        if mid in seen:
            errs.append(f"{where}: duplicate id {mid!r}")
        seen.add(mid)
        c = m.get("check")
        if not isinstance(c, dict):
            errs.append(f"{where}: check block missing")
            continue
        kind = c.get("kind")
        if kind not in KINDS:
            errs.append(f"{where}: kind must be one of {sorted(KINDS)}, got {kind!r}")
            continue
        if not isinstance(c.get("source"), str) or not c["source"]:
            errs.append(f"{where}: source (the clause) missing")
        if kind == "none":
            if not c.get("why"):
                errs.append(f"{where}: kind none needs a why")
            continue
        pb = c.get("provable_by")
        if not isinstance(pb, list) or not pb or not set(pb) <= PROVERS:
            errs.append(f"{where}: provable_by must be a non-empty subset of {sorted(PROVERS)}")
            pb = []
        if kind == "document" and pb != ["document"]:
            errs.append(f"{where}: kind document is provable_by [document] only")
        if ("operator" in pb) != (kind == "settable"):
            errs.append(f"{where}: operator in provable_by goes with kind settable, and only with it")
        if kind == "settable":
            if c.get("field") not in RANGE_FIELDS:
                errs.append(f"{where}: kind settable reads a range field {sorted(RANGE_FIELDS)}")
            if "datasheet" not in pb:
                errs.append(f"{where}: kind settable needs datasheet in provable_by")
            r = c.get("range")
            if r is not None and not (isinstance(r, list) and len(r) == 2 and r[0] < r[1]):
                errs.append(f"{where}: range, when given, must be [low, high]")
        if kind == "stated" and (c.get("field") not in FIELDS or "datasheet" not in pb):
            errs.append(f"{where}: kind stated needs a field and datasheet in provable_by")
        mean = c.get("meaning")
        if kind == "max" and c.get("field") in ("ac_kw", "ac_kva", "ac_a") and mean is None:
            errs.append(f"{where}: a power or current line needs a meaning {sorted(MEANINGS)}")
        if mean is not None and mean not in MEANINGS:
            errs.append(f"{where}: meaning must be one of {sorted(MEANINGS)}, got {mean!r}")
        if kind in ("range", "max", "min", "cosphi"):
            if c.get("field") not in FIELDS:
                errs.append(f"{where}: field must be one of {sorted(FIELDS)}, got {c.get('field')!r}")
            if "datasheet" not in pb:
                errs.append(f"{where}: a numeric kind needs datasheet in provable_by")
        if kind == "range":
            r = c.get("range")
            if not (isinstance(r, list) and len(r) == 2 and all(isinstance(x, (int, float)) for x in r) and r[0] < r[1]):
                errs.append(f"{where}: range must be [low, high]")
        if kind in ("max", "min", "cosphi") and not isinstance(c.get("limit"), (int, float)):
            errs.append(f"{where}: limit must be a number")
        if kind == "max" and not c.get("over"):
            errs.append(f"{where}: kind max needs an over text (what applies above the limit)")
        if kind == "min" and not c.get("under"):
            errs.append(f"{where}: kind min needs an under text")
        if kind == "phases" and not isinstance(c.get("three_phase_above_kw"), (int, float)):
            errs.append(f"{where}: kind phases needs three_phase_above_kw")
        ap = c.get("applies") or {}
        if not isinstance(ap, dict) or not set(ap) <= {"classes", "below_kw", "above_kw", "phases"}:
            errs.append(f"{where}: applies may hold classes, below_kw, above_kw, phases only")
        elif ap.get("phases") is not None and not set(ap["phases"]) <= {1, 2, 3}:
            errs.append(f"{where}: applies.phases must be within [1, 2, 3]")
        elif ap.get("classes") is not None and not set(ap["classes"]) <= set(CLASSES):
            errs.append(f"{where}: applies.classes must be within {CLASSES}")
        if isinstance(ap, dict) and CHARGER in (ap.get("classes") or []) and set(ap["classes"]) != {CHARGER}:
            errs.append(f"{where}: an item for a charging point (applies.classes [wallbox]) names no generator class beside it")
        fr = c.get("from")
        if fr is not None and not (isinstance(fr, str) and YMD.fullmatch(fr)):
            errs.append(f"{where}: from must be YYYY-MM-DD (the day the item starts to apply)")
        if c.get("before") is not None and not (fr and isinstance(c["before"], str) and c["before"]):
            errs.append(f"{where}: before (what holds until `from`) needs a from date and a sentence")
        ct = c.get("cite")
        if ct is not None and not (isinstance(ct, list) and ct and all(isinstance(x, str) and x for x in ct)):
            errs.append(f"{where}: cite, when given, is a list of strings a covering document must also cite")
        ch = c.get("changed_in")
        if ch is not None and not (isinstance(ch, str) and YM.fullmatch(ch)):
            errs.append(f"{where}: changed_in must be YYYY-MM")
        if ch is not None and not c.get("changed"):
            errs.append(f"{where}: changed_in needs a changed text (what changed)")
    return errs


def load_profiles() -> dict:
    out, errs = {}, []
    for f in sorted(PROFILES.glob("*.yaml")):
        p = strictyaml.load(f.read_text(encoding="utf-8"))
        errs += validate_profile(p, f.name)
        out[p["cc"]] = p
    if errs:
        print("\n".join("ERROR " + e for e in errs))
        sys.exit(1)
    return out


# ---- the two evidence layers --------------------------------------------------------------------------------------
def _brand_keys() -> dict:
    """spelling -> canonical name, both lower case, from data/curated/brands.yaml: an evidence or datasheet file that
    writes "Victron" and a register that writes "Victron Energy" are one brand, never a join to nothing."""
    keys = {}
    for canon, spellings in (strictyaml.load((ROOT / "data/curated/brands.yaml").read_text(encoding="utf-8")) or {}).items():
        for s in [canon, *(spellings or [])]:
            keys[str(s).strip().lower()] = str(canon).strip().lower()
    return keys


BRAND_KEYS = _brand_keys()


def bkey(brand: str) -> str:
    b = (brand or "").strip().lower()
    return BRAND_KEYS.get(b, b)


def load_specs() -> dict:
    idx = {}
    for f in sorted(SPECS.glob("*.yaml")):
        doc = strictyaml.load(f.read_text(encoding="utf-8"))
        src = {s["id"]: s for s in doc["sources"]}
        rows = []
        for m in doc["models"]:
            s = src[m["source"]]
            rows.append((norm(m["code"]), re.compile(m["match"]) if m.get("match") else None,
                         {**m, "src": {"url": s["url"], "version": s.get("version") or "", "seen": s["seen"], "title": s.get("title") or s.get("file") or ""}}))
        idx.setdefault(bkey(doc["brand"]), []).extend(rows)   # two files of one brand are joined, never last-wins
    return idx


def sheet_of(idx: dict, brand: str, model: str):
    rows = idx.get(bkey(brand))
    if not rows:
        return None
    n = norm(model)
    for exact, rx, row in rows:
        if n == exact or (rx and rx.search(n)):
            return row
    return None


def load_evidence() -> dict:
    idx = {}
    for f in sorted(EVIDENCE.glob("*.yaml")):
        b = strictyaml.load(f.read_text(encoding="utf-8"))
        lst = []
        for d in b["documents"]:
            doc = {k: v for k, v in d.items() if k != "families"}
            doc["_brand"] = b["brand"]   # the file's own spelling: the site keys doc_accepted by it (web/src/lib/checks.ts)
            for fam in d["families"]:
                if fam.get("match"):
                    lst.append((re.compile(fam["match"]), doc, fam))
        idx.setdefault(bkey(b["brand"]), []).extend(lst)   # two files of one brand are joined, never last-wins
    return idx


def docs_of(idx: dict, brand: str, model: str, cc: str) -> list[dict]:
    n = norm(model)
    out, seen = [], set()
    for rx, doc, fam in idx.get(bkey(brand), []):
        # `countries` is what the document names; `accepted_in` is derived by tools/evidence/build.py from data/evidence/rules
        if (cc in (fam.get("countries") or []) or cc in (fam.get("accepted_in") or [])) and rx.search(n) and doc["id"] not in seen:
            seen.add(doc["id"])
            out.append(doc)
    return out


MMYY = re.compile(r"/(\d\d)\.(\d\d)(?!\d)")        # "VDE-AR-N 4105/11.18" = 2018-11
BARE_YEAR = re.compile(r"[: ](20\d\d)(?![\d-])")  # "VDE-AR-N 4105:2018" — the profile's edition_years says which month


def edition_of(doc: dict, prof: dict | None = None) -> str | None:
    """The newest edition a document cites: YYYY-MM, MM.YY after a slash, or a bare year of a norm that had one edition
    that year (the profile's `edition_years`, per norm); only then the month it was issued, which is not an edition."""
    norms = (prof or {}).get("edition_years") or {}
    dates = []
    for s in doc.get("standards") or []:
        found = [f"{y}-{m}" for y, m in YM.findall(s)] + [f"20{yy}-{mm}" for mm, yy in MMYY.findall(s)]
        if not found:
            for norm_name, years in norms.items():
                if norm_name.lower() in s.lower():
                    table = {str(k): str(v) for k, v in years.items()}
                    found += [table[y] for y in BARE_YEAR.findall(s) if y in table]
        dates += found
    if dates:
        return max(dates)
    iss = str(doc.get("issued") or "")
    m = YM.match(iss) or re.match(r"\d\d\.(\d\d)\.(20\d\d)", iss)   # 2024-07-01, or 15.08.2022 as a lab prints it
    return (m.group(0)[:7] if m.re is YM else f"{m.group(2)}-{m.group(1)}") if m else None


def cites(doc: dict, must) -> bool:
    """Whether the standards name one of `must` where a term starts: Spain's "NTS" is not the end of "requirements".
    The key may run on, because several keys are prefixes by design ("OVE-Richtlinie R" names "OVE-Richtlinie R25",
    "EN 50549" names "EN 50549-1:2019" and "NEN-EN 50549-1")."""
    text = " ".join(doc.get("standards") or []).lower()
    return any(re.search(r"(?<![a-z0-9])" + re.escape(c.lower()), text) for c in must)


def classes_of(doc: dict, prof: dict) -> set:
    """What kind of evidence a document is for this country: the maker's released-countries table, a generic
    EN 50549-1 / EN 50438 certificate, or a declaration against the country's own rule (document_must_cite)."""
    out = set()
    if doc.get("kind") == "country-release":
        out.add("country-release")
    if cites(doc, GENERIC):
        out.add("generic-en50549-1")
    if cites(doc, [c for c in prof["document_must_cite"] if not any(g.lower() in c.lower() for g in GENERIC)]):
        out.add("national-declaration")
    return out


def short_standards(doc: dict) -> str:
    """'CEI 0-21:2022-03; V1:2022-11; V2:2024-01' — the shared prefix once."""
    sts = doc.get("standards") or []
    out = []
    for s in sts:
        s = s.strip()
        if ";" in s and not s.startswith("CEI 0-21;V"):
            out.append(s)
            continue
        out.append(s.replace("CEI 0-21;", ""))
    return "; ".join(out)


# ---- the sheet's fields ------------------------------------------------------------------------------------------------
def field_of(sheet: dict | None, field: str):
    if not sheet:
        return None
    if field == "ac_kw":
        return sheet.get("ac_kw") if sheet.get("ac_kw") is not None else sheet.get("ac_kva")
    if field == "vac_pct":
        v = sheet.get("vac_v")
        if not v:
            return None
        un = sheet.get("vac_un") or {3: 400, 1: 230}.get(sheet.get("phases"))
        if not un:
            return None
        return [round(100 * v[0] / un, 1), round(100 * v[1] / un, 1), v[0], v[1], un]
    return sheet.get(field)


def fmt(x) -> str:
    return f"{x:g}" if isinstance(x, (int, float)) else str(x)


# ---- one requirement for one model -------------------------------------------------------------------------------------
def applies(c: dict, cls: str, kw, ph) -> tuple[bool, str]:
    ap = c.get("applies") or {}
    if ap.get("classes") and cls not in ap["classes"]:
        return False, ""
    if ap.get("phases"):
        if ph is None:
            return True, "phases not collected, so whether this applies is not known"
        if ph not in ap["phases"]:
            return False, ""
    if "below_kw" in ap or "above_kw" in ap:
        if kw is None:
            return True, "rated power not collected, so whether this applies is not known"
        if "below_kw" in ap and kw > ap["below_kw"]:
            return False, ""
        if "above_kw" in ap and kw <= ap["above_kw"]:
            return False, ""
    return True, ""


def by_sheet(c: dict, sheet: dict | None):
    """(state, text) from the datasheet alone, or None when the sheet does not state the value."""
    kind, field = c["kind"], c.get("field")
    if kind == "phases":
        kw, ph = field_of(sheet, "ac_kw"), field_of(sheet, "phases")
        lim = c["three_phase_above_kw"]
        if kw is None or ph is None:
            return None
        if kw > lim:
            return ("S" if ph == 3 else "X", f"{fmt(kw)} kW, {ph}-phase — over {fmt(lim)} kW three-phase is required" + ("" if ph == 3 else "; the sheet says single-phase"))
        return ("S", f"{fmt(kw)} kW, {ph}-phase — up to {fmt(lim)} kW either is allowed")
    v = field_of(sheet, field)
    if v is None:
        return None
    if kind == "stated":
        return ("S", f"the sheet states {LABEL.get(field, field)} {'≤ ' if field == 'thdi_pct' else ''}{fmt(v)}{UNIT.get(field, '')}")
    if kind == "settable":
        if field == "vac_pct":
            plo, phi, vlo, vhi, un = v
            span, lo_hi = f"{fmt(vlo)}–{fmt(vhi)} V ({fmt(plo)}–{fmt(phi)} % of {fmt(un)} V)", (plo, phi)
        else:
            span, lo_hi = f"{fmt(v[0])}–{fmt(v[1])}{UNIT.get(field, '')}", (v[0], v[1])
        r = c.get("range")
        if r and not (lo_hi[0] <= r[0] and lo_hi[1] >= r[1]):
            return ("X", f"settable {span}, does not cover {fmt(r[0])}–{fmt(r[1])}")
        return ("P", f"settable {span}" + (f", covers {fmt(r[0])}–{fmt(r[1])}" if r else "") + "; the operator sets the values at commissioning")
    if kind == "range":
        lo, hi = c["range"]
        if field == "vac_pct":
            plo, phi, vlo, vhi, un = v
            ok = plo <= lo and phi >= hi
            return ("S" if ok else "X", f"{fmt(vlo)}–{fmt(vhi)} V at {fmt(un)} V nominal = {fmt(plo)}–{fmt(phi)} % Un, {'covers' if ok else 'does not cover'} {fmt(lo)}–{fmt(hi)} %")
        unit = {"freq_hz": "Hz"}.get(field, "")
        ok = v[0] <= lo and v[1] >= hi
        return ("S" if ok else "X", f"{fmt(v[0])}–{fmt(v[1])} {unit}, {'covers' if ok else 'does not cover'} {fmt(lo)}–{fmt(hi)} {unit}".strip())
    unit = UNIT.get(field, "")
    if kind == "max":
        ok = v <= c["limit"]
        return ("S" if ok else "X", f"{fmt(v)}{unit} — {'within' if ok else c['over'] + ' (limit'} {fmt(c['limit'])}{unit}" + ("" if ok else ")"))
    if kind == "min":
        ok = v >= c["limit"]
        return ("S" if ok else "X", f"{fmt(v)}{unit} — {'at least' if ok else c['under'] + ' (limit'} {fmt(c['limit'])}{unit}" + ("" if ok else ")"))
    if kind == "cosphi":
        ok = v <= c["limit"]
        return ("S" if ok else "X", f"cos φ adjustable to {fmt(v)} — {'reaches' if ok else 'does not reach'} {fmt(c['limit'])}")
    return None


def list_figures(prof: dict, rows: list[dict]) -> dict | None:
    """The type's power and phases as the country's own list states them (profile list_checks.figures), from the rows
    that admit the model: a figure is taken only where every such row gives the same one. Phases are skipped on a row
    whose comment matches `phases_not_if` (Sweden: a single-phase unit listed for a three-phase set) and for a model whose
    name says 230 V, which a list's "3" does not make three-phase (Victron's 2022 Swedish rows)."""
    fg = (prof.get("list_checks") or {}).get("figures")
    if not fg or not rows:
        return None
    pw = {e.get("kva") for e in rows}
    out = {"unit": fg["power"], "power": None, "phases": None, "phases_why": ""}
    if len(pw) == 1 and isinstance(next(iter(pw)), (int, float)) and next(iter(pw)) > 0:
        out["power"] = next(iter(pw))
    if fg.get("phases"):
        nix = re.compile(fg["phases_not_if"], re.I) if fg.get("phases_not_if") else None
        phs = {(e.get("extra") or {}).get("phases") for e in rows}
        if len(phs) == 1 and next(iter(phs)) in ("1", "2", "3"):
            ph = int(next(iter(phs)))
            if nix and any(nix.search((e.get("extra") or {}).get("comment") or "") for e in rows):
                out["phases_why"] = "the list admits this unit only in a three-phase set, so its phases column is not the unit's own phase count"
            elif ph != 1 and any(re.search(r"\b230 ?V\b", e.get("model_raw") or "", re.I) for e in rows):
                out["phases_why"] = f"the list says {ph}-phase for a unit its name calls 230 V, so the column is not the unit's own phase count"
            else:
                out["phases"] = ph
    return out if out["power"] is not None or out["phases"] is not None or out["phases_why"] else None


def by_figure(c: dict, fig: dict | None, sheet: dict | None):
    """(state, text, note) for a power line (kind max on ac_kw / ac_kva, a meaning that is a line) from the list's own
    figure, where the sheet does not answer it; None when the list gives nothing that decides it. A kVA figure is an
    upper bound of the active power and a kW figure a lower bound of the apparent power, so a kVA figure within a kW line
    is within, a kW figure over a kVA line is over, and the other two are left "not shown" with the reason."""
    if not fig or c["kind"] != "max" or c.get("field") not in POWER_FIELDS or c.get("meaning") not in LINES:
        return None
    ap = c.get("applies") or {}
    if ap.get("phases"):
        ph = field_of(sheet, "phases") or fig["phases"]
        if ph is None:
            return ("N", "", fig["phases_why"] + "; the grid operator applies this line to the plant") if fig["phases_why"] else None
        if ph not in ap["phases"]:
            return ("V", f"the list: {ph}-phase — this line is for {' / '.join(f'{x}-phase' for x in ap['phases'])} units", "")
    v, unit, lim = fig["power"], fig["unit"], c["limit"]
    if v is None:
        return None
    want = "kva" if c["field"] == "ac_kva" else "kw"
    U = {"kw": "kW", "kva": "kVA"}
    over = v > lim
    if unit != want and over == (unit == "kva"):
        return ("N", "", f"the list gives {fmt(v)} {U[unit]}, {'over' if over else 'within'} the {fmt(lim)} {U[want]} line, but not the "
                         f"{'active power' if want == 'kw' else 'apparent power'} the line is drawn in; the grid operator applies it to the plant")
    if over:
        return ("W", f"the list: {fmt(v)} {U[unit]} — {c['over']} (limit {fmt(lim)} {U[want]})", "")
    return ("V", f"the list: {fmt(v)} {U[unit]} — within {fmt(lim)} {U[want]}", "")


def check_model(prof: dict, items: list[dict], sheet: dict | None, docs: list[dict], listed: bool = False,
                list_rows: list[dict] | None = None, today: str | None = None) -> dict:
    """One model × one country. `list_rows`: the country's list rows that admit the model (registers.json cells with a
    positive `show`), read for list_checks.only_where and list_checks.figures; `today` (YYYY-MM-DD) decides an item's
    `from` and the edition's `transition_until`."""
    cc = prof["cc"]
    today = today or date.today().isoformat()
    lc = prof.get("list_checks") or {}
    ow = lc.get("only_where") or {}
    by_list, list_why = set(), {}
    if listed:
        for it in lc.get("items") or []:
            w = ow.get(it)
            if not w or any(re.search(w["match"], str((e.get("extra") or {}).get(w["field"]) or "")) for e in list_rows or []):
                by_list.add(it)
            else:
                list_why[it] = w["else"]
    fig = list_figures(prof, list_rows) if listed else None
    acc = set(prof["accepts"])
    covering = [d for d in docs if classes_of(d, prof) & acc]
    covering.sort(key=lambda d: edition_of(d, prof) or "", reverse=True)
    best = covering[0] if covering else None
    best_ed = edition_of(best, prof) if best else None
    ed = prof["edition"]
    older = bool(best_ed and best_ed < ed["date"])
    until = ed.get("transition_until")
    # after the transition a certificate to the older edition no longer counts for any item, not only the changed ones
    ended = bool(older and until and today >= until)
    kw, ph = field_of(sheet, "ac_kw"), field_of(sheet, "phases")
    rows, na = {}, []
    counts = dict.fromkeys(STATES, 0)
    for i, m in enumerate(items):
        c = m["check"]
        if m["_cls"] == CHARGER and CHARGER not in ((c.get("applies") or {}).get("classes") or []):
            na.append(i)
            continue
        # a row is stored only where it says something: "no check" (kind none) and the plain "not shown" rows are
        # derived by the reader (web/src/lib/checks.ts) from the item and from whether a sheet / a document exists
        if c["kind"] == "none":
            counts["I"] += 1
            continue
        ok, note = applies(c, m["_cls"], kw, ph)
        if not ok:
            na.append(i)
            continue
        if note:
            # whether it applies is not known from the sheet: the list's own figure may decide a power line, and the
            # list's yes answers an item it checks whatever the power
            res = by_figure(c, fig, sheet)
            rows[i] = ((["N", "", res[2]] if res[0] == "N" else [res[0], res[1]]) if res else ["R"] if m["id"] in by_list
                       else ["N", "", list_why.get(m["id"], note)])   # the list's own reason says more than "power unknown"
            counts[rows[i][0]] += 1
            continue
        res = by_sheet(c, sheet) if "datasheet" in c["provable_by"] else None
        if res:
            st, text = res
            if st == "X" and c.get("meaning") in LINES:
                st = "L"
            rows[i] = [st, text]
            counts[st] += 1
            continue
        # the operator's own list before the maker's paper: listing is the operator having read those papers
        if m["id"] in by_list:
            rows[i] = ["R"]
            counts["R"] += 1
            continue
        doc = best
        if doc and c.get("cite"):   # the item asks a document to cite its own annex (Italy: CEI 0-21 Allegato X)
            doc = next((d for d in covering if cites(d, c["cite"])), None)
        if "document" in c["provable_by"] and doc:
            d_ed = edition_of(doc, prof)
            old = ended or (bool(c.get("changed_in")) and d_ed is not None and d_ed < c["changed_in"])
            note = (f"the transition to {ed['label'].split(' (')[0]} ended on {day_words(until)}; the operator asks for a certificate to it" if ended
                    else c["changed"] + (f"; a certificate to the older edition is accepted until {day_words(until)}" if older and until else "")) if old else ""
            rows[i] = ["O", "", note] if old else ["D"]
            counts["O" if old else "D"] += 1
            continue
        if c.get("from") and today < c["from"]:
            rows[i] = ["N", "", f"required from {day_words(c['from'])}; until then {c.get('before') or 'no proof is asked for'}"]
            counts["N"] += 1
            continue
        res = by_figure(c, fig, sheet)
        if res:
            rows[i] = [res[0], res[1]] if res[0] != "N" else ["N", "", res[2]]
            counts[res[0]] += 1
            continue
        if m["id"] in list_why:
            rows[i] = ["N", "", list_why[m["id"]]]
        counts["N"] += 1
    out = {"sum": {k: v for k, v in counts.items() if v}}
    if listed and lc:
        out["listed"] = True   # the reader words a plain "not shown" row from it (profile list.not_carried / on_application)
    if rows:
        out["rows"] = rows
    if na:
        out["na"] = na
    if best:
        out["doc"] = {"id": best["id"], "title": best["title"], "url": best["url"], "kind": best.get("kind", ""), "issuer": best.get("issuer", ""),
                      "cert_no": best.get("cert_no", ""), "issued": best.get("issued", ""), "seen": best.get("seen", ""),
                      "standards": short_standards(best), "edition": best_ed, "older": older,
                      "firmware": best.get("firmware", "")}
        if older and until:
            out["doc"]["until"] = until            # accepted until this day (the edition's transition)
            out["doc"]["withdrawn"] = ended        # the transition is over: documented for a withdrawn edition
        if len(covering) > 1:
            out["doc"]["more"] = [{"title": d["title"], "url": d["url"], "edition": edition_of(d, prof)} for d in covering[1:]]
    elif docs:
        out["named"] = [{"title": d["title"], "url": d["url"], "kind": d.get("kind", ""), "is": sorted(classes_of(d, prof)) or ["no standard cited"]} for d in docs]
    return out


# ---- the run ------------------------------------------------------------------------------------------------------------
def main(validate_only: bool = False, fixture: str | None = None, out: str | None = None, today: str | None = None):
    global PROFILES, SPECS, EVIDENCE, REG, OUT
    if fixture:
        fx = Path(fixture).resolve()
        PROFILES, SPECS, EVIDENCE, REG = fx / "profiles", fx / "specs", fx / "evidence", fx / "registers.json"
    if out:
        OUT = Path(out).resolve()
    profiles = load_profiles()
    print(f"profiles ok: {', '.join(f'{cc} ({len(p['must_meet'])} items, edition {p['edition']['id']})' for cc, p in profiles.items())}")
    if validate_only:
        return
    if not REG.exists():
        sys.exit(f"{REG} missing — run python tools/site_data.py first")
    specs, evidence = load_specs(), load_evidence()
    devs = [d for d in json.loads(REG.read_text(encoding="utf-8"))["devices"] if not d["unmatched"] and d["cls"] in CLASSES]
    out_prof = {}
    for cc, p in profiles.items():
        out_prof[cc] = {"country": p["country"], "norm": p["edition"]["norm"], "edition": p["edition"], "decided_by": p["decided_by"], "accepts": p["accepts"],
                        "items": [{"id": m["id"], "rule": m["rule"], "value": m["value"], **{k: v for k, v in m["check"].items()}} for m in p["must_meet"]]}
        if p.get("list_checks"):
            out_prof[cc]["list"] = {k: p["list_checks"][k] for k in ("word", "what", "not_carried")}
        if p.get("on_application"):
            out_prof[cc]["on_application"] = p["on_application"]
    models = {}
    stats = {cc: {"models": 0, "sheet_any": 0, "sheet_rows": 0, "covered": 0, "doc": 0, "outside": 0, "over_line": 0, "older": 0, "listed": 0,
                  "list_figure": 0, "bare": 0} for cc in profiles}
    for_charger = {cc for cc, p in profiles.items() if any(CHARGER in ((m["check"].get("applies") or {}).get("classes") or []) for m in p["must_meet"])}
    for d in devs:
        sheet = sheet_of(specs, d["brand"], d["model"])
        per = {}
        for cc, p in profiles.items():
            if d["cls"] == CHARGER and cc not in for_charger:
                continue
            items = [{**m, "_cls": d["cls"]} for m in p["must_meet"]]
            pos = [e for e in (d.get("cells") or {}).get(cc, []) if e["show"] in POSITIVE]
            r = check_model(p, items, sheet, docs_of(evidence, d["brand"], d["model"], cc), bool(pos), pos, today)
            per[cc] = r
            s, st = r["sum"], stats[cc]
            st["models"] += 1
            by_sheet_n = s.get("S", 0) + s.get("P", 0) + s.get("L", 0) + s.get("X", 0)
            st["sheet_rows"] += by_sheet_n
            if by_sheet_n:
                st["sheet_any"] += 1
            if not s.get("N"):
                st["covered"] += 1
            if r.get("doc"):
                st["doc"] += 1
                if r["doc"]["older"]:
                    st["older"] += 1
            if s.get("X"):
                st["outside"] += 1
            if s.get("L"):
                st["over_line"] += 1
            if s.get("R"):
                st["listed"] += 1
            if s.get("V") or s.get("W"):
                st["list_figure"] += 1
            # "not shown" rows with no reason: stored ones carry a note; plain ones get the profile's words when it has them
            plain = s.get("N", 0) - sum(1 for x in (r.get("rows") or {}).values() if x[0] == "N")
            worded = (p.get("list_checks") or {}).get("not_carried") if r.get("listed") else p.get("on_application")
            st["bare"] += 0 if worded else plain
        if not per:
            continue
        entry = {"cc": per}
        if sheet:
            entry["sheet"] = {"code": sheet["code"], **sheet["src"]}
        models[d["brand"] + "|" + d["model"]] = entry
    # per maker's document, the countries whose operator takes its kind: the site's "likely fit" (evidence.ts fitsIn) reads
    # it, so the grid cell, the model page's tiers and this check never disagree about one document
    doc_accepted = {}
    for lst in evidence.values():
        for _, doc, _ in lst:
            k = f"{doc['_brand']}|{doc['id']}"
            if k not in doc_accepted:
                doc_accepted[k] = sorted(cc for cc, p in profiles.items() if classes_of(doc, p) & set(p["accepts"]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"built": date.today().isoformat(), "states": list(STATES), "profiles": out_prof, "models": models, "stats": stats,
                               "doc_accepted": doc_accepted}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(OUT, f"{len(models)} models × {len(profiles)} countries, {OUT.stat().st_size // 1024} kB")
    for cc, st in stats.items():
        print(f"{cc}: {st['models']} models · at least one datasheet row {st['sheet_any']} ({st['sheet_rows']} rows) · every item covered {st['covered']} · "
              f"with a maker's document {st['doc']} (of which {st['older']} for an older edition) · over a line {st['over_line']} · outside by datasheet {st['outside']}"
              + (f" · checked by the list {st['listed']}" if st["listed"] else "") + (f" · by the list's figure {st['list_figure']}" if st["list_figure"] else "")
              + f" · bare 'not shown' rows {st['bare']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--fixture", help="a directory with profiles/, specs/, evidence/ and registers.json (tests)")
    ap.add_argument("--out", help="where to write the result (default web/.data/checks.json)")
    ap.add_argument("--today", help="YYYY-MM-DD to judge `from` and `transition_until` against (tests; default: today)")
    a = ap.parse_args()
    if a.today and not YMD.fullmatch(a.today):
        sys.exit("--today must be YYYY-MM-DD")
    main(a.validate, a.fixture, a.out, a.today)
