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

import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # the coverage line has × and · (a cp1252 console)

ROOT = Path(__file__).resolve().parents[2]  # runs from web/ (npm run build) as well as from the repo root
OUT = ROOT / "web/.data/checks.json"
REG = ROOT / "web/.data/registers.json"
PROFILES, SPECS, EVIDENCE = ROOT / "data/profiles", ROOT / "data/specs", ROOT / "data/evidence"

CLASSES = ("inverter", "hybrid", "battery", "plug-in")   # a wallbox has no model-level grid requirement in these profiles
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
# states: S meets by datasheet, P the sheet's range covers it and the operator sets the values at commissioning,
# D meets by maker's document, O documented for an older edition (this item changed since), N not shown,
# L over a line by datasheet (another RfG type, procedure, EMC class or protection set-up applies — not a breach),
# X outside by datasheet, I no check (optional / installation-level)
STATES = ("S", "P", "D", "O", "N", "L", "X", "I")
LINES = {"rfg-type", "procedure", "emc-class", "protection"}   # over these the rule changes; over "phases" it is broken
UNIT = {"ac_kw": " kW", "ac_kva": " kVA", "ac_a": " A", "idc_pct": " %", "thdi_pct": " %", "fsw_khz": " kHz", "isc_a": " A", "cosphi": "",
        "freq_hz": " Hz", "vac_v": " V"}
LABEL = {"thdi_pct": "current THD", "idc_pct": "DC injection", "fsw_khz": "switching frequency", "isc_a": "short-circuit current",
         "cosphi": "cos φ", "ac_a": "max AC current", "freq_hz": "frequency range", "vac_v": "voltage range"}
YM = re.compile(r"(20\d\d)-(\d\d)")


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
    acc = p.get("accepts")
    if not isinstance(acc, list) or not acc or not set(acc) <= ACCEPTS:
        errs.append(f"{name}: accepts must be a non-empty subset of {sorted(ACCEPTS)}")
    cite = p.get("document_must_cite")
    if not isinstance(cite, list) or not cite or not all(isinstance(c, str) and c for c in cite):
        errs.append(f"{name}: document_must_cite must be a non-empty list of strings")
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
        ch = c.get("changed_in")
        if ch is not None and not (isinstance(ch, str) and YM.fullmatch(ch)):
            errs.append(f"{where}: changed_in must be YYYY-MM")
        if ch is not None and not c.get("changed"):
            errs.append(f"{where}: changed_in needs a changed text (what changed)")
    return errs


def load_profiles() -> dict:
    out, errs = {}, []
    for f in sorted(PROFILES.glob("*.yaml")):
        p = yaml.safe_load(f.read_text(encoding="utf-8"))
        errs += validate_profile(p, f.name)
        out[p["cc"]] = p
    if errs:
        print("\n".join("ERROR " + e for e in errs))
        sys.exit(1)
    return out


# ---- the two evidence layers --------------------------------------------------------------------------------------
def load_specs() -> dict:
    idx = {}
    for f in sorted(SPECS.glob("*.yaml")):
        doc = yaml.safe_load(f.read_text(encoding="utf-8"))
        src = {s["id"]: s for s in doc["sources"]}
        rows = []
        for m in doc["models"]:
            s = src[m["source"]]
            rows.append((norm(m["code"]), re.compile(m["match"]) if m.get("match") else None,
                         {**m, "src": {"url": s["url"], "version": s.get("version") or "", "seen": s["seen"], "title": s.get("title") or s.get("file") or ""}}))
        idx[doc["brand"].lower()] = rows
    return idx


def sheet_of(idx: dict, brand: str, model: str):
    rows = idx.get(brand.lower())
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
        b = yaml.safe_load(f.read_text(encoding="utf-8"))
        lst = []
        for d in b["documents"]:
            doc = {k: v for k, v in d.items() if k != "families"}
            for fam in d["families"]:
                if fam.get("match"):
                    lst.append((re.compile(fam["match"]), doc, fam))
        idx[b["brand"].lower()] = lst
    return idx


def docs_of(idx: dict, brand: str, model: str, cc: str) -> list[dict]:
    n = norm(model)
    out, seen = [], set()
    for rx, doc, fam in idx.get(brand.lower(), []):
        # `countries` is what the document names; `accepted_in` is derived by tools/evidence/build.py from data/evidence/rules
        if (cc in (fam.get("countries") or []) or cc in (fam.get("accepted_in") or [])) and rx.search(n) and doc["id"] not in seen:
            seen.add(doc["id"])
            out.append(doc)
    return out


def edition_of(doc: dict) -> str | None:
    """The newest edition a document cites (YYYY-MM from its standards), else the month it was issued."""
    dates = [f"{y}-{m}" for s in (doc.get("standards") or []) for y, m in YM.findall(s)]
    if dates:
        return max(dates)
    iss = str(doc.get("issued") or "")
    m = YM.match(iss) or re.match(r"\d\d\.(\d\d)\.(20\d\d)", iss)   # 2024-07-01, or 15.08.2022 as a lab prints it
    return (m.group(0)[:7] if m.re is YM else f"{m.group(2)}-{m.group(1)}") if m else None


def cites(doc: dict, must) -> bool:
    text = " ".join(doc.get("standards") or []).lower()
    return any(c.lower() in text for c in must)


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


def check_model(prof: dict, items: list[dict], sheet: dict | None, docs: list[dict]) -> dict:
    cc = prof["cc"]
    acc = set(prof["accepts"])
    covering = [d for d in docs if classes_of(d, prof) & acc]
    covering.sort(key=lambda d: edition_of(d) or "", reverse=True)
    best = covering[0] if covering else None
    best_ed = edition_of(best) if best else None
    kw, ph = field_of(sheet, "ac_kw"), field_of(sheet, "phases")
    rows, na = {}, []
    counts = dict.fromkeys(STATES, 0)
    for i, m in enumerate(items):
        c = m["check"]
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
            rows[i] = ["N", "", note]
            counts["N"] += 1
            continue
        res = by_sheet(c, sheet) if "datasheet" in c["provable_by"] else None
        if res:
            st, text = res
            if st == "X" and c.get("meaning") in LINES:
                st = "L"
            rows[i] = [st, text]
            counts[st] += 1
            continue
        if "document" in c["provable_by"] and best:
            old = bool(c.get("changed_in")) and best_ed is not None and best_ed < c["changed_in"]
            rows[i] = ["O", "", c["changed"]] if old else ["D"]
            counts["O" if old else "D"] += 1
            continue
        counts["N"] += 1
    out = {"sum": {k: v for k, v in counts.items() if v}}
    if rows:
        out["rows"] = rows
    if na:
        out["na"] = na
    if best:
        out["doc"] = {"id": best["id"], "title": best["title"], "url": best["url"], "kind": best.get("kind", ""), "issuer": best.get("issuer", ""),
                      "cert_no": best.get("cert_no", ""), "issued": best.get("issued", ""), "seen": best.get("seen", ""),
                      "standards": short_standards(best), "edition": best_ed, "older": bool(best_ed and best_ed < prof["edition"]["date"]),
                      "firmware": best.get("firmware", "")}
        if len(covering) > 1:
            out["doc"]["more"] = [{"title": d["title"], "url": d["url"], "edition": edition_of(d)} for d in covering[1:]]
    elif docs:
        out["named"] = [{"title": d["title"], "url": d["url"], "kind": d.get("kind", ""), "is": sorted(classes_of(d, prof)) or ["no standard cited"]} for d in docs]
    return out


# ---- the run ------------------------------------------------------------------------------------------------------------
def main(validate_only: bool = False, fixture: str | None = None, out: str | None = None):
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
    models = {}
    stats = {cc: {"models": 0, "sheet_any": 0, "sheet_rows": 0, "covered": 0, "doc": 0, "outside": 0, "over_line": 0, "older": 0} for cc in profiles}
    for d in devs:
        sheet = sheet_of(specs, d["brand"], d["model"])
        per = {}
        for cc, p in profiles.items():
            items = [{**m, "_cls": d["cls"]} for m in p["must_meet"]]
            r = check_model(p, items, sheet, docs_of(evidence, d["brand"], d["model"], cc))
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
        entry = {"cc": per}
        if sheet:
            entry["sheet"] = {"code": sheet["code"], **sheet["src"]}
        models[d["brand"] + "|" + d["model"]] = entry
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"built": date.today().isoformat(), "states": list(STATES), "profiles": out_prof, "models": models, "stats": stats},
                              ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(OUT, f"{len(models)} models × {len(profiles)} countries, {OUT.stat().st_size // 1024} kB")
    for cc, st in stats.items():
        print(f"{cc}: {st['models']} models · at least one datasheet row {st['sheet_any']} ({st['sheet_rows']} rows) · every item covered {st['covered']} · "
              f"with a maker's document {st['doc']} (of which {st['older']} for an older edition) · over a line {st['over_line']} · outside by datasheet {st['outside']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--fixture", help="a directory with profiles/, specs/, evidence/ and registers.json (tests)")
    ap.add_argument("--out", help="where to write the result (default web/.data/checks.json)")
    a = ap.parse_args()
    main(a.validate, a.fixture, a.out)
