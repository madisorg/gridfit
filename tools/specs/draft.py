"""Spec layer, step 3: draft data/specs/<brand>.yaml from what the readers pulled out of the datasheets.

    python tools/specs/draft.py            # writes data/specs/deye.yaml, fronius.yaml, goodwe.yaml

A draft, not the truth: every value is reviewed against the sheet before the file is committed, and the
hand corrections live HERE (named, with the reason) so a re-run does not lose them. Each model row keeps
the sheet's own model code, the numbers as read (kW, kVA, A, MPPT count, phases, max PV kW) and the
source id; each source has the URL, the sheet's own version/date where it has one, and the day it was read.
Values the sheet does not state stay null -- "not collected" on the site, never a guess.
"""
import json
import re
from pathlib import Path

import yaml

SEEN = "2026-10-31"
OUT = Path("data/specs")
CACHE = Path("cache/specs")

RULE = ("Every number is the maker's own datasheet as read on the seen date: MPPT count, rated AC power (kW; kVA where the sheet "
        "gives apparent power), max AC output current (A), phases (from the AC connection row), max PV input (kW). A model code is "
        "matched to the lists exactly (upper case, spaces removed, comma as decimal point), or by `match` where the lists spell the "
        "same hardware differently. A value the sheet does not state is null and shows as 'not collected'. Hardware revisions with "
        "another suffix are other models.")


def num(s):
    if s is None:
        return None
    m = re.search(r"\d+(?:[.,]\d+)?", str(s).replace(",", "."))
    return float(m.group(0).replace(",", ".")) if m else None


def kw(w, raw=""):
    """W or VA -> kW unless the row's label already says (kW) / (kVA)."""
    v = num(w)
    if v is None:
        return None
    return round(v, 2) if re.search(r"\(k(W|VA)\)", raw or "") else round(v / 1000, 2)


def mppt_of(s):
    """'2/1+1' -> 2 ; '8/2+2+...' -> 8 ; '2' -> 2"""
    v = num(str(s).split("/")[0]) if s else None
    return None if v is None else int(v)


def row(code, mppt, ac_kw, ac_kva, ac_a, phases, pv_kw, sid):
    return {"code": code, "mppt": mppt, "ac_kw": ac_kw, "ac_kva": ac_kva, "ac_a": ac_a, "phases": phases, "pv_kw": pv_kw, "source": sid}


def dump(brand, doc):
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / f"{brand}.yaml"
    p.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")
    print(p, len(doc["models"]), "models,", len(doc["sources"]), "sources")


# ---------------------------------------------------------------- Deye: official sheets, deye.com/wp-content
DEYE_SUFFIX = {  # sheets whose model row is cut after the series letters: the rest of the code per column
    "datasheet_sun-14-20k-sg05lp3-eu-sm2_20260706_en": "LP3-EU-SM2",
    "datasheet_sun-3-8k-sg06lp3-eu-bm2_20260706_en": "LP3-EU-BM2",
    "datasheet_sun-3-8k-sg06lp3-eu-cm2_20260706_en": "LP3-EU-CM2",
    "datasheet_sun-3.6-10k-sg05lp1-eu-am2-p_20260706_en": "LP1-EU-AM2-P",
    "datasheet_sun-3.6-10k-sg05lp1-eu-sm2-p_20260706_en": "LP1-EU-SM2-P",
    "datasheet_sun-5-25k-sg01hp3-eu-am2_20260706_en": "HP3-EU-AM2",
    "datasheet_sun-7-12k-sg06lp1-eu-bm3_20260706_en": "LP1-EU-BM3",
    "datasheet_sun-7-12k-sg06lp1-eu-cm3_20260706_en-1": "LP1-EU-CM3",
    "datasheet_sun-7.6-12k-sg02lp1-eu-am2_20260706_en": "LP1-EU-AM2",
    "sun-3-12k-sg05lp3-eu-sm2": "LP3-EU-SM2",
}
DEYE_SUFFIX_PER_MODEL = {  # one sheet, two revisions side by side (header lines of the sheet)
    "datasheet_sun-29.9-50k-sg01hp3-eu-bm4_20260706_en": {
        "SUN-29.9K-SG01": "HP3-EU-BM3", "SUN-30K-SG01": "HP3-EU-BM3", "SUN-35K-SG01": "HP3-EU-BM3",
        "SUN-40K-SG01": "HP3-EU-BM4", "SUN-50K-SG01": "HP3-EU-BM4"},
}
DEYE_SKIP = {"sun-3-6.6k-og03lp1-eu-am2", "sun-5-12k-sg04lp3_20260706_en",  # off-grid series; duplicate download of the SG04LP3 sheet
             "datasheet_sun-6-8k-g06p3-eu-bm2-lv-p1_20260706_en"}  # two columns read as the same model and 35 kW for an 8 kW unit: not readable by machine, left out
DEYE_SUFFIX.update({  # string-inverter sheets: the model row carries the series only, the full code is in the sheet's title
    "datasheet_sun-1-4k-g04p1-eu-am1_20260706_en": "P1-EU-AM1",
    "datasheet_sun-3-15k-g06p3-eu-bm2-p1_20260706_en": "__G06P3",  # "SUN-3K-G06-P1" -> "SUN-3K-G06P3-EU-BM2-P1", handled below
    "datasheet_sun-3.6-6.2k-g05p1-eu-am2_20260706_en": "P1-EU-AM2",
})
DEYE_HAND2 = {
    # the 4.2K and 4.6K headers touch on this sheet and were read as one column; both rows from the text
    "datasheet_sun-3.6-6.2k-g05p1-eu-am2_20260706_en": [
        ("SUN-3.6K-G05P1-EU-AM2", 2, 3.6, 17.3, 5.4), ("SUN-4K-G05P1-EU-AM2", 2, 4.0, 19.2, 6.0), ("SUN-4.2K-G05P1-EU-AM2", 2, 4.2, 20.1, 6.3),
        ("SUN-4.6K-G05P1-EU-AM2", 2, 4.6, 22.0, 6.9), ("SUN-5K-G05P1-EU-AM2", 2, 5.0, 24.0, 7.5), ("SUN-5.2K-G05P1-EU-AM2", 2, 5.2, 24.9, 7.8),
        ("SUN-6K-G05P1-EU-AM2", 2, 6.0, 28.7, 9.0), ("SUN-6.2K-G05P1-EU-AM2", 2, 6.2, 29.7, 9.3)],
}
# the SG06LP1 BM2/CM2 sheets put two header rows above seven columns and the reader saw two; rows by hand from the text
DEYE_HAND = {
    "datasheet-sun-3-6k-sg06lp1-eu-bm2-en": [
        ("SUN-3K-SG06LP1-24-EU-BM1", 1, 3.0, 15, 4.8), ("SUN-3K-SG06LP1-EU-BM1", 1, 3.0, 15, 4.8), ("SUN-3.6K-SG06LP1-EU-BM2", 2, 3.6, 18, 5.76),
        ("SUN-4K-SG06LP1-EU-BM2", 2, 4.0, 20, 6.4), ("SUN-4.6K-SG06LP1-EU-BM2", 2, 4.6, 21, 7.36), ("SUN-5K-SG06LP1-EU-BM2", 2, 5.0, 25, 8.0),
        ("SUN-6K-SG06LP1-EU-BM2", 2, 6.0, 30, 9.6)],
    "datasheet_sun-3-6k-sg06lp1-eu-cm2_20260728_en": [
        ("SUN-3K-SG06LP1-24-EU-CM1", 1, 3.0, 15, 4.8), ("SUN-3K-SG06LP1-EU-CM1", 1, 3.0, 15, 4.8), ("SUN-3.6K-SG06LP1-EU-CM2", 2, 3.6, 18, 5.76),
        ("SUN-4K-SG06LP1-EU-CM2", 2, 4.0, 20, 6.4), ("SUN-4.6K-SG06LP1-EU-CM2", 2, 4.6, 21, 7.36), ("SUN-5K-SG06LP1-EU-CM2", 2, 5.0, 25, 8.0),
        ("SUN-6K-SG06LP1-EU-CM2", 2, 6.0, 30, 9.6)],
}


def deye():
    urls = dict(line.split(" ", 1) for line in (CACHE / "deye/SOURCES.txt").read_text(encoding="utf-8").splitlines() if " " in line)
    sources, models = [], []
    urls.update(dict(line.split(" ", 1) for line in (CACHE / "deye2/SOURCES.txt").read_text(encoding="utf-8").splitlines() if " " in line))
    for jf in sorted(list((CACHE / "deye").glob("*.table.json")) + list((CACHE / "deye2").glob("*.table.json"))):
        stem = jf.name[: -len(".table.json")]
        if stem in DEYE_SKIP or not stem:
            continue
        pdf = stem + ".pdf"
        d = json.loads(jf.read_text(encoding="utf-8"))
        ver = re.search(r"_(2026\d{4})_", stem)
        sid = re.sub(r"^datasheet[_-]|_\d{8}_en(-1)?$|-en$", "", stem).replace("_", "-")
        sources.append({"id": sid, "url": urls.get(pdf, ""), "file": pdf, "version": ver.group(1) if ver else "",
                        "note": "" if ver else "no date on the sheet or in its file name", "seen": SEEN})
        hand = {**DEYE_HAND, **DEYE_HAND2}
        if stem in hand:
            for code, mp, ackw, aca, pv in hand[stem]:
                models.append(row(code, mp, ackw, None, aca, 1, pv, sid))
            continue
        r = d["rows"]
        for m in d["models"]:
            if m == "Model":
                continue
            suf = DEYE_SUFFIX_PER_MODEL.get(stem, {}).get(m, DEYE_SUFFIX.get(stem, ""))
            code = m.replace("-G06-P1", "-G06P3-EU-BM2-P1") if suf == "__G06P3" else m + suf
            if code.endswith("-G04-LV") or code.endswith("-G05-LV"):
                code = code  # the LV sheets write the full code already
            phs = str((r.get("phases") or {}).get(m, ""))
            ph = 3 if "3L" in phs or re.search(r"(LP3|HP3|P3|G0[345]-LV|K-G0[345]$)", code) and not re.search(r"P1|M\d", code) else 1
            # Deye writes "max AC input/output current" as in/out; the output side is the grid-side figure
            out_a = str((r.get("ac_a") or {}).get(m, "")).split("/")
            aca = out_a[1] if len(out_a) > 1 else out_a[0]
            raw = lambda k: (r.get(k) or {}).get("raw", "")
            pvraw = raw("pv_w")
            pv = kw((r.get("pv_w") or {}).get(m), pvraw) if "Power" in pvraw else None
            ackw_v = kw((r.get("ac_w") or {}).get(m), raw("ac_w"))
            if pv is not None and ackw_v and pv > 3 * ackw_v:
                pv = None  # the reader took the "Max. PV Input Voltage" row (800 V / 550 V) for the power row on some sheets
            models.append(row(code, mppt_of((r.get("mppt") or {}).get(m)), kw((r.get("ac_w") or {}).get(m), raw("ac_w")),
                              kw((r.get("ac_va") or {}).get(m), raw("ac_va")), num(aca), ph, pv, sid))
    # the -BE spelling on the Belgian list is the same hardware sold through Belgium (same sheet on deye.com)
    for m in models:
        if m["code"].endswith("-EU") or "-EU-" in m["code"]:
            m["match"] = "^" + re.escape(m["code"]).replace(r"\-EU", r"-(EU|BE)").replace("-EU", "-(EU|BE)") + "$"
    dump("deye", {"brand": "Deye", "maker_site": "https://deye.com/", "rule": RULE, "sources": sources, "models": models})


# ---------------------------------------------------------------- Fronius: help-center product pages (HTML spec table)
def fronius():
    urls = dict(line.split(" ", 1) for line in (CACHE / "fronius/SOURCES.txt").read_text(encoding="utf-8").splitlines() if " " in line)
    pages = json.loads((CACHE / "fronius/pages.json").read_text(encoding="utf-8"))
    seen_names, sources, models = set(), [], []
    for p in sorted(pages, key=lambda p: p["name"]):
        if p["name"] in seen_names:
            continue
        seen_names.add(p["name"])
        slug = p["page"].split("--", 1)[-1][: -len(".html")]
        if slug not in urls:
            continue
        sid = slug.replace("fronius-", "")
        sources.append({"id": sid, "url": urls[slug], "title": p["name"] + " - technical data (Fronius help center)", "version": "",
                        "note": "web page, no version; the row is the page as read on the seen date", "seen": SEEN})
        code = p["name"].replace("Fronius ", "")
        grid = p.get("grid", "")
        ph = 3 if "3~" in grid else 1 if "1~" in grid else None
        ackw = num(p.get("pac_nom"))
        if ackw is not None and "kW" not in p.get("pac_nom", ""):
            ackw = round(ackw / 1000, 2)
        kva = num(p.get("pac_max"))
        if kva is not None and "kVA" not in p.get("pac_max", ""):
            kva = round(kva / 1000, 2)
        m = row(code, int(num(p["mppt"])) if p.get("mppt") else None, ackw, kva, num(p.get("iac_max")), ph, num(p.get("pdc_max")), sid)
        # the lists spell these "Symo GEN24 10.0 Plus", "Symo Gen24 plus 10.0", "Fronius GEN24 12.0 Plus SC", "Primo GEN24 5.0 Plus SC"
        mm = re.match(r"^(Symo|Primo) GEN24 ([\d.]+)( Plus)?( SC)?$", code)
        if mm:
            ser, pw, plus, sc = mm.group(1).upper(), re.escape(mm.group(2)), mm.group(3), mm.group(4)
            body = f"({pw}PLUS|PLUS{pw})" if plus else pw
            # SC is its own hardware revision, never joined with the non-SC row; only the SC rows may lack the series word on a list
            m["match"] = f"^(FRONIUS)?({ser})?GEN24{body}SC$" if sc else f"^(FRONIUS)?{ser}GEN24{body}$"
        models.append(m)
    dump("fronius", {"brand": "Fronius", "maker_site": "https://www.fronius.com/", "rule": RULE, "sources": sources, "models": models})


# ---------------------------------------------------------------- GoodWe: official sheets, en.goodwe.com/Ftp (rows read from the text by hand)
GW = {  # file stem: (phases, [(code, mppt, ac_kw, ac_kva, ac_a)])
    "GW_DNS_Datasheet-EN": (1, [
        ("GW3000D-NS", 2, 3.0, 3.0, 13.6), ("GW3600D-NS", 2, 3.68, 3.68, 16.0), ("GW4200D-NS", 2, 4.2, 4.2, 19.0), ("GW5000D-NS", 2, 5.0, 5.0, 22.8),
        ("GW6000D-NS", 2, 6.0, 6.0, 27.3), ("GW3000T-DS", 2, 3.0, 3.0, 13.6), ("GW3600T-DS", 2, 3.68, 3.68, 16.0), ("GW4200T-DS", 2, 4.2, 4.2, 19.0),
        ("GW5000T-DS", 2, 5.0, 5.0, 22.8), ("GW6000T-DS", 2, 6.0, 6.0, 27.3)]),
    "GW_DNSx20G3_Datasheet-EN": (1, [
        ("GW3000-DNS-30", 2, 3.0, 3.0, 14.4), ("GW3600-DNS-30", 2, 3.6, 3.6, 17.3), ("GW4200-DNS-30", 2, 4.2, 4.2, 20.1), ("GW5000-DNS-30", 2, 5.0, 5.0, 24.0),
        ("GW6000-DNS-30", 2, 6.0, 6.0, 28.8)]),
    "GW_EH_Datasheet-EN": (1, [("GW3600-EH", 2, None, 3.6, 15.7), ("GW5000-EH", 2, None, 5.0, 21.7), ("GW6000-EH", 2, None, 6.0, 26.1)]),
    "GW_EHB_Datasheet-EN": (1, [("GW5000-EHB", 3, None, 5.0, 23.0), ("GW6500-EHB", 4, None, 6.5, 28.5), ("GW8600-EHB", 4, None, 8.6, 39.0), ("GW0010-EHB", 4, None, 10.0, 43.5)]),
    "GW_EM_Datasheet-EN": (1, [("GW3048-EM", 1, None, 3.0, 10.0), ("GW3648-EM", 2, None, 3.68, 10.0), ("GW5048-EM", 2, None, 5.0, 10.0)]),
    "GW_ES_Datasheet-EN": (1, [("GW3648D-ES", None, None, 3.68, 16.0), ("GW5048D-ES", None, None, 4.6, 20.0)]),
    "GW_ESx20G2_Datasheet-EN": (1, [
        ("GW3000-ES-20", 1, 3.0, 3.0, 13.6), ("GW3500L-ES-20", 2, 3.5, 3.5, 27.6), ("GW3600-ES-20", 2, 3.68, 3.68, 16.7), ("GW3600M-ES-20", 2, 3.68, 3.68, 16.7),
        ("GW5000-ES-20", 2, 5.0, 5.0, 22.7), ("GW5000M-ES-20", 2, 5.0, 5.0, 22.7), ("GW6000-ES-20", 2, 6.0, 6.0, 27.3), ("GW6000M-ES-20", 2, 6.0, 6.0, 27.3)]),
    "GW_ETx2015-30kW_Datasheet-EN": (3, [
        ("GW15K-ET", 2, 15.0, 15.0, 22.7), ("GW20K-ET", 2, 20.0, 20.0, 30.3), ("GW25K-ET", 3, 25.0, 25.0, 37.9), ("GW29.9K-ET", 3, 29.9, 29.9, 45.5), ("GW30K-ET", 3, 30.0, 30.0, 45.5)]),
    "GW_MS_Datasheet-EN": (1, [("GW5000-MS", 3, 5.0, None, 25.0), ("GW6000-MS", 3, 6.0, None, 30.0), ("GW7000-MS", 3, 7.0, None, 35.0), ("GW8500-MS", 3, 8.5, None, 42.5), ("GW10K-MS", 3, 10.0, None, 45.5)]),
    "GW_MT_Datasheet-EN": (3, [
        ("GW50KN-MT", 4, 50.0, 50.0, 80.0), ("GW60KN-MT", 4, 60.0, 60.0, 96.0), ("GW50KBF-MT", 4, 50.0, 50.0, 80.0), ("GW60KBF-MT", 4, 60.0, 60.0, 96.0),
        ("GW75KBF-MT", 4, 75.0, 75.0, 95.3), ("GW80KBF-MT", 4, 80.0, 80.0, 94.1), ("GW70KHV-MT", 4, 70.0, 70.0, 89.0), ("GW80KHV-MT", 4, 80.0, 80.0, 94.1),
        ("GW75K-MT", 4, 75.0, 75.0, 133.0), ("GW80K-MT", 4, 80.0, 80.0, 133.0)]),
    "GW_SMT_Datasheet-EN": (3, [("GW25K-MT", None, 25.0, 25.0, 40.0), ("GW30K-MT", None, 30.0, 30.0, 48.0), ("GW36K-MT", None, 36.0, 36.0, 53.3)]),
    "GW_XS_Datasheet-EN": (1, [
        ("GW700-XS", 1, 0.7, 0.7, 3.5), ("GW1000-XS", 1, 1.0, 1.0, 4.8), ("GW1500-XS", 1, 1.5, 1.5, 7.2), ("GW2000-XS", 1, 2.0, 2.0, 9.6), ("GW2500-XS", 1, 2.5, 2.5, 12.0),
        ("GW3000-XS", 1, 3.0, 3.0, 14.3)]),
}
GW_MATCH = {"GW5000-DNS-30": "^GW5000-DNS-(EU)?30$", "GW5000-EH": "^GW5000-EH(-BE)?$"}  # the Belgian / EU spellings of the same sheet's model


def goodwe():
    urls = dict(line.split(" ", 1) for line in (CACHE / "goodwe/SOURCES.txt").read_text(encoding="utf-8").splitlines() if " " in line)
    sources, models = [], []
    for stem, (ph, rows) in GW.items():
        pdf = stem + ".pdf"
        sid = stem.replace("_Datasheet-EN", "").replace("GW_", "").replace("x20", "-").lower()
        sources.append({"id": sid, "url": urls.get(pdf, ""), "file": pdf, "version": "", "note": "the sheet carries no version or date", "seen": SEEN})
        for code, mp, ackw, kva, aca in rows:
            m = row(code, mp, ackw, kva, aca, ph, None, sid)
            if code in GW_MATCH:
                m["match"] = GW_MATCH[code]
            models.append(m)
    dump("goodwe", {"brand": "GoodWe", "maker_site": "https://en.goodwe.com/", "rule": RULE, "sources": sources, "models": models})


# ---------------------------------------------------------------- Kostal: official sheets, kostal-solar-electric.com/fileadmin (rows read from the text by hand)
# The lists spell these "PLENTICORE S G3 4.0", "PLENTICORE S G3 4 kW", "PLENTICORE S G3 5,5 kW", "Plenticore G3 S": the match
# takes the size with or without ".0" / "kW". PIKO MP plus "-1" variants have one tracker and no column on the sheet: no row.
KOSTAL = {  # file stem: (phases, [(code, mppt, ac_kw, ac_kva, ac_a, match)])
    "DB_PLENTICORE-G3_en": (3, [
        ("PLENTICORE S G3 4.0", 3, 4.0, None, 11.2, r"^PLENTICORESG3(4|4\.0)(KW)?$"), ("PLENTICORE S G3 5.5", 3, 5.5, None, 11.2, r"^PLENTICORESG35\.5(KW)?$"),
        ("PLENTICORE S G3 7.0", 3, 7.0, None, 11.2, r"^PLENTICORESG3(7|7\.0)(KW)?$"),
        ("PLENTICORE M G3 8.5", 3, 8.5, None, 20.0, r"^PLENTICOREMG38\.5(KW)?$"), ("PLENTICORE M G3 10", 3, 10.0, None, 20.0, r"^PLENTICOREMG3(10|10\.0)(KW)?$"),
        ("PLENTICORE M G3 12.5", 3, 12.5, None, 20.0, r"^PLENTICOREMG312\.5(KW)?$"),
        ("PLENTICORE L G3 15", 3, 15.0, None, 32.0, r"^PLENTICORELG3(15|15\.0)(KW)?$"), ("PLENTICORE L G3 17.5", 3, 17.5, None, 32.0, r"^PLENTICORELG317\.5(KW)?$"),
        ("PLENTICORE L G3 20", 3, 20.0, None, 32.0, r"^PLENTICORELG3(20|20\.0)(KW)?$")]),
    "DB_PIKO-IQ_en": (3, [
        ("PIKO IQ 3.0", 2, 3.0, None, 4.81, ""), ("PIKO IQ 4.2", 2, 4.2, None, 6.74, ""), ("PIKO IQ 5.5", 2, 5.5, None, 8.82, ""),
        ("PIKO IQ 7.0", 2, 7.0, None, 11.23, ""), ("PIKO IQ 8.5", 2, 8.5, None, 13.63, ""), ("PIKO IQ 10", 2, 10.0, None, 16.04, "")]),
    "DB_PIKO-MP-plus_en": (1, [
        ("PIKO MP plus 3.0-2", 2, 3.0, None, 14.0, ""), ("PIKO MP plus 3.6-2", 2, 3.68, None, 16.0, ""), ("PIKO MP plus 4.6-2", 2, 4.6, None, 20.0, ""),
        ("PIKO MP plus 5.0-2", 2, 5.0, None, 22.0, "")]),
}


def kostal():
    urls = dict(line.split(" ", 1) for line in (CACHE / "kostal/SOURCES.txt").read_text(encoding="utf-8").splitlines() if " " in line)
    sources, models = [], []
    for stem, (ph, rows) in KOSTAL.items():
        pdf = stem + ".pdf"
        sid = stem.replace("DB_", "").replace("_en", "").lower()
        sources.append({"id": sid, "url": urls.get(pdf, ""), "file": pdf, "version": "", "note": "the sheet carries no version or date in its text", "seen": SEEN})
        for code, mp, ackw, kva, aca, match in rows:
            m = row(code, mp, ackw, kva, aca, ph, None, sid)
            if match:
                m["match"] = match
            models.append(m)
    dump("kostal", {"brand": "Kostal", "maker_site": "https://www.kostal-solar-electric.com/", "rule": RULE, "sources": sources, "models": models})


# ---------------------------------------------------------------- SMA: official sheets, files.sma.de (rows read from the text by hand)
# The lists spell the Smart Energy units "SBSE3.6-50 (Sunny Boy Smart Energy 3.6)" and the 50 series "STP 12-50": the match
# takes the code at the start / without the space. STP 12-50's current row did not come through the text layer: null.
SMA = {  # file stem: (phases, [(code, mppt, ac_kw, ac_kva, ac_a, match)])
    "SBSE36-60-DS-en-18": (1, [
        ("SBSE3.6-50", 3, 3.6, None, 16.0, r"^SBSE3\.6-50"), ("SBSE4.0-50", 3, 4.0, None, 20.0, r"^SBSE4\.0-50"),
        ("SBSE5.0-50", 3, 5.0, None, 25.0, r"^SBSE5\.0-50"), ("SBSE6.0-50", 3, 6.0, None, 30.0, r"^SBSE6\.0-50")]),
    "STPxx-3SE-40-DS-en-22": (3, [
        ("STP5.0-3SE-40", 2, 5.0, None, 7.6, ""), ("STP6.0-3SE-40", 2, 6.0, None, 9.1, ""), ("STP8.0-3SE-40", 2, 8.0, None, 12.1, ""),
        ("STP10.0-3SE-40", 2, 10.0, None, 15.2, "")]),
    "STP50-41-DS-en-20": (3, [("STP50-41", 6, 50.0, None, 72.5, "")]),
    "STPxx-50-DS-en-24": (3, [
        ("STP 12-50", 3, 12.0, None, None, ""), ("STP 15-50", 3, 15.0, None, None, ""), ("STP 20-50", 3, 20.0, None, None, ""), ("STP 25-50", 3, 25.0, None, None, "")]),
}


def sma():
    urls = dict(line.split(" ", 1) for line in (CACHE / "sma/SOURCES.txt").read_text(encoding="utf-8").splitlines() if " " in line)
    sources, models = [], []
    for stem, (ph, rows) in SMA.items():
        pdf = stem + ".pdf"
        ver = stem.rsplit("-", 1)[-1]
        sources.append({"id": stem.lower(), "url": urls.get(pdf, ""), "file": pdf, "version": ver, "note": "the version is the number at the end of the file name", "seen": SEEN})
        for code, mp, ackw, kva, aca, match in rows:
            m = row(code, mp, ackw, kva, aca, ph, None, stem.lower())
            if match:
                m["match"] = match
            models.append(m)
    dump("sma", {"brand": "SMA", "maker_site": "https://www.sma.de/", "rule": RULE, "sources": sources, "models": models})


# ---------------------------------------------------------------- Fox ESS: official sheets, fox-ess.com/Public/Uploads (rows read from the text by hand)
# Sheet versions are in the file names (ENTG3datasheetV2.520260703 = V2.5, 2026-07-03). AC output figures are the grid-side
# "AC OUTPUT" block, never the EPS block. ac_kw is the sheet's nominal/rated active power [W]; where a sheet states nominal power in
# VA only (H3-Pro, P3-Pro) it goes to ac_kva and ac_kw stays null. pv_kw is "Max. Input Power"/"Max. DC Input Power" [W]; a
# sheet with only "Max. Array Power [Wp]" gives that. A cell with two figures ("4048/3680*1", "75*/82.5", "130[1]/137.5") is null.
# P100E currents are three figures at 220/230/240 V: the 230 V figure is taken. AC1-x-E-G2 share the H1 G2 sheet whose PV block
# is headed "ONLY FOR HYBRID": AC-coupled, mppt 0. The lists spell the PowerCube units with the battery stack attached
# ("PQ3-5.0-M_TQ5000-S-P (w)_2S", "PQ3 5.0-M_TQ5000…", "PQ3-10.0 M_TQ5000…"): the match takes the inverter code at the start.
# Older generations on the lists (T3…T25 without -G3, H3-x-E/-M, AC3-x-E/-Pro, P3-Pro-x-AC, P3-x-SA, P50/P100-x-H, 1K5-HI) have no
# sheet on the current download centre: no row.
FOX = {  # file stem: (phases, [(code, mppt, ac_kw, ac_kva, ac_a, pv_kw)])
    "ENTG3datasheetV2.520260703": (3, [
        ("T3-G3", 2, 3.0, 3.3, 4.8, 4.5), ("T4-G3", 2, 4.0, 4.4, 6.4, 6.0), ("T5-G3", 2, 5.0, 5.5, 8.0, 7.5), ("T6-G3", 2, 6.0, 6.6, 9.6, 9.0),
        ("T8-G3", 2, 8.0, 8.8, 12.8, 12.0), ("T10-G3", 2, 10.0, 11.0, 15.9, 15.0), ("T12-G3", 2, 12.0, 13.2, 19.1, 18.0), ("T15-G3", 2, 15.0, 16.5, 23.9, 22.5),
        ("T17-G3", 2, 17.0, 18.7, 27.1, 25.5), ("T20-G3", 2, 20.0, 22.0, 31.9, 30.0), ("T23-G3", 2, 23.0, 25.3, 36.7, 34.5), ("T25-G3", 2, 25.0, 27.5, 39.9, 37.5)]),
    "ENH3PRODatasheetV2.720260605": (3, [
        ("H3-Pro-15.0", 3, None, 15.0, 25.0, 30.0), ("H3-Pro-20.0", 3, None, 20.0, 33.3, 40.0), ("H3-Pro-24.9", 3, None, 24.9, 37.7, 50.0),
        ("H3-Pro-25.0", 3, None, 25.0, 41.7, 50.0), ("H3-Pro-29.9", 3, None, 29.9, 45.3, 60.0), ("H3-Pro-30.0", 3, None, 30.0, 50.0, 60.0)]),
    "ENP3PRODatasheetV1.320260605": (3, [
        ("P3-Pro-15.0", 3, None, 15.0, 25.0, 30.0), ("P3-Pro-20.0", 3, None, 20.0, 33.3, 40.0), ("P3-Pro-25.0", 3, None, 25.0, 41.7, 50.0),
        ("P3-Pro-30.0", 3, None, 30.0, 50.0, 60.0)]),
    "ENH3SmartDatasheetV2.020260609": (3, [
        ("H3-5.0-Smart", 3, 5.0, 5.5, 8.3, 11.0), ("H3-6.0-Smart", 3, 6.0, 6.6, 10.0, 13.2), ("H3-8.0-Smart", 3, 8.0, 8.8, 13.3, 17.6),
        ("H3-9.9-Smart", 3, 9.9, 9.9, 15.0, 18.0), ("H3-10.0-Smart", 3, 10.0, 11.0, 16.7, 18.0), ("H3-12.0-Smart", 3, 12.0, 13.2, 20.0, 22.5),
        ("H3-15.0-Smart", 3, 15.0, 16.5, 25.0, 22.5)]),
    "ENH3PlusDatasheetV2.920261022": (3, [
        ("H3-50-Plus", 4, 50.0, 55.0, 83.6, 100.0), ("H3-60-Plus", 4, 60.0, 66.0, 100.3, 120.0), ("H3-80-Plus", 8, 80.0, 88.0, 133.7, 160.0),
        ("H3-100-Plus", 8, 100.0, 110.0, 167.2, 200.0), ("H3-125-Plus", 8, 125.0, None, 198.5, 250.0)]),
    "ENP3PlusDatasheetV1.320261028": (3, [
        ("P3-50-Plus", 4, 50.0, 55.0, 83.6, 100.0), ("P3-60-Plus", 4, 60.0, 66.0, 100.3, 120.0), ("P3-80-Plus", 8, 80.0, 88.0, 133.7, 160.0),
        ("P3-100-Plus", 8, 100.0, 110.0, 167.2, 200.0), ("P3-125-Plus", 8, 125.0, 137.5, 198.5, 250.0)]),
    "ENP3SDatasheetV1.320260605": (3, [
        ("P3-5.0-SH", 2, 5.0, 5.5, 8.3, 11.0), ("P3-6.0-SH", 2, 6.0, 6.6, 10.0, 13.2), ("P3-8.0-SH", 3, 8.0, 8.8, 13.3, 17.6),
        ("P3-10.0-SH", 3, 10.0, 11.0, 16.7, 18.0), ("P3-12.0-SH", 3, 12.0, 13.2, 20.0, 22.5), ("P3-15.0-SH", 3, 15.0, 16.5, 25.0, 22.5)]),
    "ENSG2DatasheetV3.520260703": (1, [
        ("S700-G2", 1, 0.7, 0.8, 3.5, 1.05), ("S1000-G2", 1, 1.0, 1.1, 4.8, 1.5), ("S1500-G2", 1, 1.5, 1.65, 7.2, 2.25), ("S2000-G2", 1, 2.0, 2.2, 9.6, 3.0),
        ("S2500-G2", 1, 2.5, 2.75, 12.0, 3.75), ("S3000-G2", 1, 3.0, 3.3, 14.3, 4.5), ("S3300-G2", 1, 3.3, 3.3, 14.3, 4.95)]),
    "ENH1G2DatasheetV2.220260609": (1, [
        ("H1-2.5-E-G2", 2, 2.5, 2.75, 12.5, 5.0), ("H1-3.0-E-G2", 2, 3.0, 3.3, 15.0, 6.0), ("H1-3.7-E-G2", 2, 3.68, None, 18.4, 7.4),
        ("H1-4.0-E-G2", 2, 4.0, 4.4, 20.0, 8.0), ("H1-4.6-E-G2", 2, 4.6, 5.06, 23.0, 9.2), ("H1-5.0-E-G2", 2, 5.0, 5.5, 25.0, 10.0), ("H1-6.0-E-G2", 2, 6.0, 6.6, 30.0, 12.0),
        ("AC1-2.5-E-G2", 0, 2.5, 2.75, 12.5, None), ("AC1-3.0-E-G2", 0, 3.0, 3.3, 15.0, None), ("AC1-3.7-E-G2", 0, 3.68, None, 18.4, None),
        ("AC1-4.0-E-G2", 0, 4.0, 4.4, 20.0, None), ("AC1-4.6-E-G2", 0, 4.6, 5.06, 23.0, None), ("AC1-5.0-E-G2", 0, 5.0, 5.5, 25.0, None), ("AC1-6.0-E-G2", 0, 6.0, 6.6, 30.0, None)]),
    "ENH1G2wlDatasheetV1.320260609": (1, [
        ("H1-2.5-E-G2-WL", 2, 2.5, 2.75, 12.5, 5.0), ("H1-3.0-E-G2-WL", 2, 3.0, 3.3, 15.0, 6.0), ("H1-3.7-E-G2-WL", 2, 3.68, None, 18.4, 7.4),
        ("H1-4.0-E-G2-WL", 2, 4.0, 4.4, 20.0, 8.0), ("H1-4.6-E-G2-WL", 2, 4.6, 5.06, 23.0, 9.2), ("H1-5.0-E-G2-WL", 2, 5.0, 5.5, 25.0, 10.0),
        ("H1-6.0-E-G2-WL", 2, 6.0, 6.6, 30.0, 12.0),
        ("AC1-2.5-E-G2-WL", 0, 2.5, 2.75, 12.5, None), ("AC1-3.0-E-G2-WL", 0, 3.0, 3.3, 15.0, None), ("AC1-3.7-E-G2-WL", 0, 3.68, None, 18.4, None),
        ("AC1-4.0-E-G2-WL", 0, 4.0, 4.4, 20.0, None), ("AC1-4.6-E-G2-WL", 0, 4.6, 5.06, 23.0, None), ("AC1-5.0-E-G2-WL", 0, 5.0, 5.5, 25.0, None),
        ("AC1-6.0-E-G2-WL", 0, 6.0, 6.6, 30.0, None)]),
    "ENP100EdatasheetV1.420260702": (1, [
        ("P100E-5-H", 2, 5.0, 5.5, 23.9, 15.0), ("P100E-6-H", 2, 6.0, 6.6, 28.7, 16.0), ("P100E-8-H", 3, 8.0, 8.8, 38.3, 18.0), ("P100E-10-H", 3, 10.0, 11.0, 47.8, 20.0)]),
    "ENVdatasheetV2.320260703": (3, [
        ("V30", 3, 30.0, 33.0, 50.2, None), ("V33", 3, 33.0, 36.3, 55.2, None), ("V36", 4, 36.0, 39.6, 60.2, None), ("V40", 4, 40.0, 44.0, 66.9, None),
        ("V50", 4, 50.0, 55.0, 83.6, None), ("V60", 6, 60.0, 66.0, 100.3, None), ("V75", 6, 75.0, 75.0, 114.0, None)]),
    "ENRG2DatasheetV1.420260703": (3, [
        ("R75-G2", 9, 75.0, None, None, 150.0), ("R80-G2", 9, 80.0, 88.0, 133.3, 160.0), ("R100-G2", 9, 100.0, 110.0, 166.7, 200.0),
        ("R110-G2", 10, 110.0, 121.0, 183.3, 220.0), ("R125-G2", 10, 125.0, 137.5, 199.3, 250.0), ("R136-G2", 10, 136.0, 138.0, 200.0, 272.0)]),
    "ENPowerCubePQ3MTQ5000datasheetV1.220260723": (3, [
        ("PQ3-5.0-M", 3, 5.0, 5.5, 8.3, 11.0), ("PQ3-6.0-M", 3, 6.0, 6.6, 10.0, 13.2), ("PQ3-8.0-M", 3, 8.0, 8.8, 13.3, 17.6), ("PQ3-10.0-L-M", 3, 9.999, 9.999, 15.2, 20.0),
        ("PQ3-10.0-M", 3, 10.0, 11.0, 16.7, 20.0), ("PQ3-12.0-M", 3, 12.0, 13.2, 20.0, 24.0), ("PQ3-15.0-M", 3, 15.0, 16.5, 25.0, 30.0)]),
    "ENPowerCubePQ3MPlusCQ7datasheetV1.220260723": (3, [
        ("PQ3-5.0-M-P", 3, 5.0, 5.5, 8.3, 11.0), ("PQ3-6.0-M-P", 3, 6.0, 6.6, 10.0, 13.2), ("PQ3-8.0-M-P", 3, 8.0, 8.8, 13.3, 17.6), ("PQ3-10.0-L-M-P", 3, 9.999, 9.999, 15.2, 20.0),
        ("PQ3-10.0-M-P", 3, 10.0, 11.0, 16.7, 20.0), ("PQ3-12.0-M-P", 3, 12.0, 13.2, 20.0, 24.0), ("PQ3-15.0-M-P", 3, 15.0, 16.5, 25.0, 30.0)]),
    "ENMEdatasheetV2.220260331": (1, [("M1-600-E", 2, 0.6, None, None, None), ("M1-800-E", 2, 0.8, None, None, None), ("M1-1000-E", 2, 1.0, None, None, None), ("M1-1200-E", 2, 1.2, None, None, None)]),
    "ENF3.0DatasheetV1.220260703": (1, [
        ("F3000", 2, 3.0, 3.3, 15.0, 6.0), ("F3600", 2, 3.6, 3.96, 18.0, 7.2), ("F4600", 2, 4.6, 5.06, 23.0, 9.2), ("F5000", 2, 5.0, 5.5, 25.0, 10.0),
        ("F5300", 2, 5.3, 5.83, 26.5, 10.6), ("F6000", 2, 6.0, 6.6, 30.0, 12.0)]),
    "ENFG2DatasheetV2.020260703": (1, [
        ("F3000-G2", 2, None, 3.3, 14.3, 4.5), ("F3600-G2", 2, None, 3.96, 17.2, 5.4), ("F4600-G2", 2, None, 5.06, 22.0, 6.9), ("F5000-G2", 2, None, 5.5, 23.9, 7.5),
        ("F5300-G2", 2, None, 5.83, 25.3, 7.95), ("F6000-G2", 2, None, 6.0, 26.1, 9.0)]),
}


def foxess():
    urls = dict(line.split(" ", 1) for line in (CACHE / "foxess/SOURCES.txt").read_text(encoding="utf-8").splitlines() if " " in line)
    sources, models = [], []
    for stem, (ph, rows) in FOX.items():
        pdf = stem + ".pdf"
        mv = re.match(r"^(?:EN)?(.*?)[Dd]atasheet[Vv]?([\d.]+?)(\d{8})$", stem)
        sid = re.sub(r"[^a-z0-9]+", "-", mv.group(1).lower()).strip("-") if mv else stem.lower()
        ver = f"V{mv.group(2)} {mv.group(3)[:4]}-{mv.group(3)[4:6]}-{mv.group(3)[6:]}" if mv else ""
        sources.append({"id": sid, "url": urls.get(pdf, ""), "file": pdf, "version": ver, "note": "version and date from the file name (the sheet's footer carries the same)", "seen": SEEN})
        for code, mp, ackw, kva, aca, pv in rows:
            m = row(code, mp, ackw, kva, aca, ph, pv, sid)
            pq = re.match(r"^PQ3-(\d+\.\d)-(L-)?M(-P)?$", code)
            if pq:  # "PQ3-5.0-M_TQ5000-S-P (w)_2S", "PQ3 5.0-M_TQ5000…", "PQ3-10.0 M_TQ5000…", "PQ3-5.0-M-P_CQ6.6-S (w)_2S"
                m["match"] = f"^PQ3-?{re.escape(pq.group(1))}-?{'L-' if pq.group(2) else ''}M{'-P_CQ' if pq.group(3) else '_TQ'}"
            models.append(m)
    dump("foxess", {"brand": "Fox ESS", "maker_site": "https://www.fox-ess.com/", "rule": RULE, "sources": sources, "models": models})


# ---------------------------------------------------------------- Growatt: official sheets, en.growatt.com/upload/file (rows read from the text by hand)
# The download centre (support/download/datasheet, 48 pages, static HTML) lists ~450 sheets. The HU / XH-BP / WIT 4-25K / SPM / MODA /
# MID X3 / MIN XH2 / SPH BL-UP sheets are image-only PDFs without a text layer and are left out. Versions: "2026.5 Update" in the file
# name, or the YYYYMM suffix. ac_kw = "AC nominal power" [W] (grid side, never the backup block); ac_kva = "Max. AC apparent power";
# ac_a = "Max. output current" (the SPH/SPA 1-phase hybrids write "input/output" pairs, the output figure is taken); pv_kw = "Max.
# recommended PV power (for module STC)". "11000VA*" is read as 11000. MOD 17-33KTL3-X3: the MPPT row spans "2" over 17/20/25 K and
# "3" over 30/33 K (string row 2/2 vs 2/2/1). SPA (storage AC inverters) sheets have no PV input block at all: AC-coupled, mppt 0.
# Lists spell the same hardware "MIN 2500TL-X" / "2500TL-X", "MOD 10000TL3-XH" / sheet "MOD10KTL3-XH", "MIN 4200TL-X2" / sheet
# "MIN 4200TL-X2 (Pro)": handled by `match`. Old TL3-S / -S / TL-XE / XA units and the MID-XH/MOD-XA/HU lines have no readable sheet.
GROWATT = {  # file stem: (phases, version, [(code, mppt, ac_kw, ac_kva, ac_a, pv_kw)])
    "MOD_3000_9000TL3-X_2026.5_Update": (3, "2026.5", [
        ("MOD 3000TL3-X", 2, 3.0, 3.3, 5.0, 4.5), ("MOD 4000TL3-X", 2, 4.0, 4.4, 6.7, 6.0), ("MOD 5000TL3-X", 2, 5.0, 5.5, 8.3, 7.5), ("MOD 6000TL3-X", 2, 6.0, 6.6, 10.0, 9.0),
        ("MOD 7000TL3-X", 2, 7.0, 7.7, 11.7, 10.5), ("MOD 8000TL3-X", 2, 8.0, 8.8, 13.3, 12.0), ("MOD 9000TL3-X", 2, 9.0, 9.9, 15.0, 13.5)]),
    "MOD_10_15KTL3-X_2026.5_Update": (3, "2026.5", [
        ("MOD 10KTL3-X", 2, 10.0, 11.0, 16.7, 15.0), ("MOD 11KTL3-X", 2, 11.0, 12.1, 18.3, 16.5), ("MOD 12KTL3-X", 2, 12.0, 13.2, 20.0, 18.0),
        ("MOD 13KTL3-X", 2, 13.0, 14.3, 21.7, 19.5), ("MOD 15KTL3-X", 2, 15.0, 16.5, 25.0, 22.5)]),
    "MOD_3000-9000TL3-X3_2026.5_Update": (3, "2026.5", [
        ("MOD 3000TL3-X3", 2, 3.0, 3.3, 5.0, 4.5), ("MOD 4000TL3-X3", 2, 4.0, 4.4, 6.7, 6.0), ("MOD 5000TL3-X3", 2, 5.0, 5.5, 8.3, 7.5), ("MOD 6000TL3-X3", 2, 6.0, 6.6, 10.0, 9.0),
        ("MOD 7000TL3-X3", 2, 7.0, 7.7, 11.7, 10.5), ("MOD 8000TL3-X3", 2, 8.0, 8.8, 13.3, 12.0), ("MOD 9000TL3-X3", 2, 9.0, 9.9, 15.0, 13.5)]),
    "MOD_10-15KTL3-X3_2026.5_Update": (3, "2026.5", [
        ("MOD 10KTL3-X3", 2, 10.0, 11.0, 16.7, 15.0), ("MOD 11KTL3-X3", 2, 11.0, 12.1, 18.3, 16.5), ("MOD 12KTL3-X3", 2, 12.0, 13.2, 20.0, 18.0),
        ("MOD 13KTL3-X3", 2, 13.0, 14.3, 21.7, 19.5), ("MOD 15KTL3-X3", 2, 15.0, 16.5, 25.0, 22.5)]),
    "MOD_17-33KTL3-X3_2026.5_Update": (3, "2026.5", [
        ("MOD 17KTL3-X3", 2, 17.0, 18.7, 28.3, 25.5), ("MOD 20KTL3-X3", 2, 20.0, 22.0, 33.3, 30.0), ("MOD 25KTL3-X3", 2, 25.0, 27.5, 41.7, 37.5),
        ("MOD 30KTL3-X3", 3, 30.0, 33.0, 50.0, 45.0), ("MOD 33KTL3-X3", 3, 33.0, 36.3, 55.0, 50.0)]),
    "MOD_3000_6000TL3-X2_Pro_2026.5_Update": (3, "2026.5", [
        ("MOD 3000TL3-X2 (Pro)", 2, 3.0, 3.3, 5.0, 4.5), ("MOD 4000TL3-X2 (Pro)", 2, 4.0, 4.4, 6.7, 6.0), ("MOD 5000TL3-X2 (Pro)", 2, 5.0, 5.5, 8.3, 7.5),
        ("MOD 6000TL3-X2 (Pro)", 2, 6.0, 6.6, 10.0, 9.0)]),
    "MOD_7-15KTL3-X2_Pro_Datasheet_EN_202610": (3, "2026-10", [
        ("MOD 7KTL3-X2 (Pro)", 2, 7.0, 7.7, 11.7, 10.5), ("MOD 8KTL3-X2 (Pro)", 2, 8.0, 8.8, 13.3, 12.0), ("MOD 10KTL3-X2 (Pro)", 2, 10.0, 11.0, 16.0, 15.0),
        ("MOD 12KTL3-X2 (Pro)", 2, 12.0, 13.2, 20.0, 18.0), ("MOD 15KTL3-X2 (Pro)", 2, 15.0, 16.5, 25.0, 22.5)]),
    "MOD_3000-10000TL3-XH_Datasheet_202209": (3, "2022-09", [
        ("MOD 3000TL3-XH", 2, 3.0, 3.3, 5.0, 6.0), ("MOD 4000TL3-XH", 2, 4.0, 4.4, 6.7, 8.0), ("MOD 5000TL3-XH", 2, 5.0, 5.5, 8.3, 10.0), ("MOD 6000TL3-XH", 2, 6.0, 6.6, 10.0, 12.0),
        ("MOD 7000TL3-XH", 2, 7.0, 7.7, 11.7, 14.0), ("MOD 8000TL3-XH", 2, 8.0, 8.8, 13.3, 16.0), ("MOD 9000TL3-XH", 2, 9.0, 9.9, 15.0, 18.0), ("MOD 10KTL3-XH", 2, 10.0, 11.0, 16.7, 20.0)]),
    "MID_15_25KTL3-X_2026.5_Update": (3, "2026.5", [
        ("MID 15KTL3-X", 2, 15.0, 16.6, 24.2, 22.5), ("MID 17KTL3-X", 2, 17.0, 18.8, 27.4, 25.5), ("MID 20KTL3-X", 2, 20.0, 22.0, 31.9, 30.0),
        ("MID 22KTL3-X", 2, 22.0, 24.4, 35.5, 33.0), ("MID 25KTL3-X", 2, 25.0, 27.7, 40.2, 37.5)]),
    "Growatt_MID_25_40KTL3-X_EU_2026.5_Update": (3, "2026.5", [
        ("MID 25KTL3-X1", 3, 25.0, 27.7, 41.9, 37.5), ("MID 30KTL3-X", 3, 30.0, 33.3, 50.5, 45.0), ("MID 33KTL3-X", 3, 33.0, 36.6, 55.5, 49.5),
        ("MID 36KTL3-X", 4, 36.0, 39.6, 60.0, 54.0), ("MID 40KTL3-X", 4, 40.0, 44.0, 66.6, 60.0)]),
    "MID_17_30KTL3-X2_2026.5_Update": (3, "2026.5", [
        ("MID 17KTL3-X2", 2, 17.0, 18.8, 28.6, 25.5), ("MID 20KTL3-X2", 2, 20.0, 22.0, 33.6, 30.0), ("MID 25KTL3-X2", 2, 25.0, 27.7, 42.0, 37.5),
        ("MID 30KTL3-X2", 2, 30.0, 33.3, 50.5, 45.0)]),
    "MID_30_50KTL3-X2_2026.5_Update": (3, "2026.5", [
        ("MID 33KTL3-X2", 3, 33.0, 36.6, 55.5, 49.5), ("MID 36KTL3-X2", 3, 36.0, 40.0, 60.6, 54.0), ("MID 40KTL3-X2", 4, 40.0, 44.4, 67.3, 60.0),
        ("MID 50KTL3-X2", 4, 50.0, 55.5, 84.1, 75.0)]),
    "MIN_2500_6000_TL-X_2026.5_Update": (1, "2026.5", [
        ("MIN 2500TL-X", 2, 2.5, 2.5, 11.3, 3.5), ("MIN 3000TL-X", 2, 3.0, 3.0, 13.6, 4.2), ("MIN 3600TL-X", 2, 3.6, 3.6, 16.0, 5.04), ("MIN 4200TL-X", 2, 4.2, 4.2, 19.0, 5.88),
        ("MIN 4600TL-X", 2, 4.6, 4.6, 20.9, 6.44), ("MIN 5000TL-X", 2, 5.0, 5.0, 22.7, 7.0), ("MIN 6000TL-X", 2, 6.0, 6.0, 27.2, 8.1)]),
    "MIN_7000_10000_TL-X_2026.5_Update": (1, "2026.5", [
        ("MIN 7000TL-X", 3, 7.0, 7.0, 33.5, 12.0), ("MIN 8000TL-X", 3, 8.0, 8.0, 38.3, 12.0), ("MIN 9000TL-X", 3, 9.0, 9.0, 43.0, 13.5), ("MIN 10000TL-X", 3, 10.0, 10.0, 45.5, 15.0)]),
    "MIN_4200_6000_TL-X2_Pro_2026.5_Update": (1, "2026.5", [
        ("MIN 4200TL-X2 (Pro)", 2, 4.2, 4.2, 19.0, 6.3), ("MIN 4600TL-X2 (Pro)", 2, 4.6, 4.6, 20.9, 6.9), ("MIN 5000TL-X2 (Pro)", 2, 5.0, 5.0, 22.7, 7.5),
        ("MIN 6000TL-X2 (Pro)", 2, 6.0, 6.0, 27.2, 9.0)]),
    "MIN_7000_10000_TL-X2_2026.5_Update": (1, "2026.5", [
        ("MIN 7000TL-X2", 3, 7.0, 7.0, 33.5, 12.0), ("MIN 8000TL-X2", 3, 8.0, 8.0, 38.3, 12.0), ("MIN 9000TL-X2", 3, 9.0, 9.0, 43.0, 13.5), ("MIN 10000TL-X2", 3, 10.0, 10.0, 45.5, 15.0)]),
    "MIN_2500_6000_TL-XH_Datasheet_202208": (1, "2022-08", [
        ("MIN 2500TL-XH", 2, 2.5, 2.5, 11.3, 5.0), ("MIN 3000TL-XH", 2, 3.0, 3.0, 13.6, 6.0), ("MIN 3600TL-XH", 2, 3.6, 3.6, 16.0, 7.2), ("MIN 4200TL-XH", 2, 4.2, 4.2, 19.0, 8.4),
        ("MIN 4600TL-XH", 2, 4.6, 4.6, 20.9, 9.2), ("MIN 5000TL-XH", 2, 5.0, 5.0, 22.7, 10.0), ("MIN 6000TL-XH", 2, 6.0, 6.0, 27.2, 10.0)]),
    "MIC_750_3300TL-X_2026.5_Update": (1, "2026.5", [
        ("MIC 750TL-X", 1, 0.75, 0.75, 3.6, None), ("MIC 1000TL-X", 1, 1.0, 1.0, 4.8, None), ("MIC 1500TL-X", 1, 1.5, 1.5, 7.1, None), ("MIC 2000TL-X", 1, 2.0, 2.0, 9.5, None),
        ("MIC 2500TL-X", 1, 2.5, 2.5, 11.9, None), ("MIC 3000TL-X", 1, 3.0, 3.0, 14.3, None), ("MIC 3300TL-X", 1, 3.3, 3.3, 14.3, None)]),
    "MIC_600_3300TL-X2_2026.5_Update": (1, "2026.5", [
        ("MIC 600TL-X2", 1, 0.6, 0.6, 2.9, 0.9), ("MIC 750TL-X2", 1, 0.75, 0.75, 3.6, 1.12), ("MIC 800TL-X2", 1, 0.8, 0.8, 3.8, 1.2), ("MIC 1000TL-X2", 1, 1.0, 1.0, 4.8, 1.5),
        ("MIC 1500TL-X2", 1, 1.5, 1.5, 7.1, 2.25), ("MIC 2000TL-X2", 1, 2.0, 2.0, 9.5, 3.0), ("MIC 2500TL-X2", 1, 2.5, 2.5, 11.9, 3.75), ("MIC 3000TL-X2", 1, 3.0, 3.0, 14.3, 4.5),
        ("MIC 3300TL-X2", 1, 3.3, 3.3, 14.3, 4.95)]),
    "SPH_4000-10000TL3_BH-UP_Datasheet_EN": (3, "", [
        ("SPH 4000TL3 BH-UP", 2, 4.0, 4.0, 6.1, None), ("SPH 5000TL3 BH-UP", 2, 5.0, 5.0, 7.6, None), ("SPH 6000TL3 BH-UP", 2, 6.0, 6.0, 9.1, None),
        ("SPH 7000TL3 BH-UP", 2, 7.0, 7.0, 10.6, None), ("SPH 8000TL3 BH-UP", 2, 8.0, 8.0, 12.1, None), ("SPH 10000TL3 BH-UP", 2, 10.0, 10.0, 15.2, None)]),
    "SPA_4000-10000TL3_BH-UP_Datasheet_202208": (3, "2022-08", [
        ("SPA4000TL3BH-UP", 0, None, 4.0, 6.1, None), ("SPA5000TL3BH-UP", 0, None, 5.0, 7.6, None), ("SPA6000TL3BH-UP", 0, None, 6.0, 9.1, None),
        ("SPA7000TL3BH-UP", 0, None, 7.0, 10.6, None), ("SPA8000TL3BH-UP", 0, None, 8.0, 12.1, None), ("SPA10000TL3BH-UP", 0, None, 10.0, 15.2, None)]),
    "SPH_3000-6000TL-HUB_Datasheet_EN_202408": (1, "2024-08", [
        ("SPH 3000TL-HUB", 2, 3.0, 3.0, 16.0, 6.0), ("SPH 3600TL-HUB", 2, 3.68, 3.68, 16.0, 7.2), ("SPH 4000TL-HUB", 2, 4.0, 4.0, 22.0, 8.0), ("SPH 4600TL-HUB", 2, 4.6, 4.6, 22.0, 9.2),
        ("SPH 5000TL-HUB", 2, 5.0, 5.0, 27.0, 10.0), ("SPH 5500TL-HUB", 2, 5.5, 5.5, 25.0, 11.0), ("SPH 6000TL-HUB", 2, 6.0, 6.0, 27.0, 12.0)]),
    "SPA_3000-6000TL-AUB_Datasheet_EN_202408": (1, "2024-08", [
        ("SPA 3000TL-AUB", 0, 3.0, 3.0, 16.0, None), ("SPA 3600TL-AUB", 0, 3.68, 3.68, 16.0, None), ("SPA 4000TL-AUB", 0, 4.0, 4.0, 22.0, None), ("SPA 4600TL-AUB", 0, 4.6, 4.6, 22.0, None),
        ("SPA 5000TL-AUB", 0, 5.0, 5.0, 27.0, None), ("SPA 5500TL-AUB", 0, 5.5, 5.5, 25.0, None), ("SPA 6000TL-AUB", 0, 6.0, 6.0, 27.0, None)]),
    "SPH_10000TL-HU_Datasheet_EN_202505": (1, "2025-05", [("SPH 10000TL-HU", 3, 10.0, 10.0, 50.0, 15.0)]),
    # WIT 29.9-50K-XHU: the grid block is "AC input/output nominal power(Grid) 59.8kW/29.9kW": the output (second) figure is taken
    "WIT_29.9_50K-XHU_Datasheet_EN_202410": (3, "2024-10", [
        ("WIT 29.9K-XHU", 4, 29.9, 29.9, 45.3, 59.8), ("WIT 30K-XHU", 4, 30.0, 33.0, 50.0, 60.0), ("WIT 36K-XHU", 4, 36.0, 39.6, 60.0, 72.0),
        ("WIT 40K-XHU", 4, 40.0, 44.0, 66.7, 80.0), ("WIT 50K-XHU", 4, 50.0, 55.0, 83.3, 100.0)]),
    "NEO_1200_2000M-X_2026.5_Update": (1, "2026.5", [("NEO 1200M-X", 3, 1.2, 1.2, 5.58, 1.8), ("NEO 1600M-X", 4, 1.6, 1.6, 7.44, 2.4), ("NEO 2000M-X", 4, 2.0, 2.0, 9.3, 3.0)]),
    "NEO_1600_2500M-X2-WiFi_2026.5_Update": (1, "2026.5", [
        ("NEO 1600M-X2", 4, 1.6, 1.6, 7.27, None), ("NEO 1800M-X2", 4, 1.8, 1.8, 8.18, None), ("NEO 2000M-X2", 4, 2.0, 2.0, 9.09, None), ("NEO 2250M-X2", 4, 2.25, 2.25, 10.23, None),
        ("NEO 2500M-X2", 4, 2.5, 2.5, 11.36, None)]),
    "MAX_50_80KTL3_LV_2026.5_Update": (3, "2026.5", [
        ("MAX 50KTL3 LV", 6, 50.0, 55.5, 80.5, 75.0), ("MAX 60KTL3 LV", 6, 60.0, 66.6, 96.6, 90.0), ("MAX 70KTL3 LV", 7, 70.0, 77.7, 112.7, 105.0), ("MAX 80KTL3 LV", 7, 80.0, 88.8, 128.8, 120.0)]),
    "MAX100_125KTL3-X2_LV_2026.5_Update": (3, "2026.5", [
        ("MAX 100KTL3-X2 LV", 8, 100.0, 110.0, 158.8, None), ("MAX 110KTL3-X2 LV", 8, 110.0, 121.0, 174.6, None), ("MAX 120KTL3-X2 LV", 8, 120.0, 132.0, 190.5, None),
        ("MAX 125KTL3-X2 LV", 8, 125.0, 137.5, 198.5, None)]),
    "MAX100_125KTL3-X_LV_2026.5_Update": (3, "2026.5", [
        ("MAX 100KTL3-X LV", 10, 100.0, 110.0, 167.1, None), ("MAX 110KTL3-X LV", 10, 110.0, 121.0, 183.8, None), ("MAX 120KTL3-X LV", 10, 120.0, 132.0, 200.5, None),
        ("MAX 125KTL3-X LV", 10, 125.0, 137.5, 208.9, None)]),
    "MAX_150KTL3-X_LV_2026.5_Update": (3, "2026.5", [("MAX 150KTL3-X LV", 10, 150.0, 165.0, 238.2, 225.0)]),
}


def growatt():
    urls = dict(line.split(" ", 1) for line in (CACHE / "growatt/SOURCES.txt").read_text(encoding="utf-8").splitlines() if " " in line)
    sources, models = [], []
    for stem, (ph, ver, rows) in GROWATT.items():
        pdf = stem + ".pdf"
        sid = re.sub(r"[^a-z0-9]+", "-", re.sub(r"^growatt_|_?datasheet.*$|_2026\.5_update$", "", stem, flags=re.I).lower()).strip("-")
        sources.append({"id": sid, "url": urls.get(pdf, ""), "file": pdf, "version": ver,
                        "note": "version from the file name ('2026.5 Update' or the YYYYMM suffix)" if ver else "the sheet carries no version or date", "seen": SEEN})
        for code, mp, ackw, kva, aca, pv in rows:
            m = row(code, mp, ackw, kva, aca, ph, pv, sid)
            mm = re.match(r"^(MIN|MOD|MIC) (\d+)(K?TL3?-X[23H]?)( \(Pro\))?$", code)
            if mm:  # "2500TL-X" without the series word; "MOD 10000TL3-XH" for the sheet's "MOD 10KTL3-XH"; "(Pro)" dropped on the lists
                ser, pw, rest, pro = mm.groups()
                body = f"({pw}K|{pw}000){re.escape(rest[1:])}" if rest.startswith("K") else f"{pw}{re.escape(rest)}"
                m["match"] = f"^({ser})?{body}{r'(\(PRO\))?' if pro else ''}$"
            models.append(m)
    dump("growatt", {"brand": "Growatt", "maker_site": "https://en.growatt.com/", "rule": RULE, "sources": sources, "models": models})


# ---------------------------------------------------------------- Solis: official flyers/datasheets, cmsdata.solisinverters.com (rows read from the text by hand)
# The download centre is a Vue page over /api/Form/getDownloadcenterNavbar + /api/Form/getForm/name/<series>; each series has one
# "Global Flyer" PDF whose last page is the datasheet. The flyer names the series ("S5-GR3P(3-20)K") and lists the full model codes on
# page 1 ("S5-GR3P3K / S5-GR3P4K …"); the table heads its columns with the size only ("3K"), so code = series prefix + column + series
# suffix. Version = the "V3.8" in the file name (and the YYYYMM where the name has one). Max output current is given as "18.2 A / 17.3 A"
# (220 V / 230 V): the 230 V figure is taken. The hybrid (EH) flyers give only "Rated grid output current" in the grid block: ac_a null.
# "MPPT number / Max. input strings number" is a spanned row; where the spans cannot be put under their columns (S6-GC 80-125K, 50-75K-LV,
# S6-EH3P(3-10)K-H, S6-GC3P50K04-NV-ND) mppt is null. S6-EA1P-L flyers have no PV block (AC-coupled storage inverter): mppt 0.
# The RHI-(3-6)K-48ES-5G datasheet link on the centre is dead (OSS NoSuchKey). The older Solis-xK-4G/5G and Solis-mini names on the
# lists have no sheet on the centre.
SOLIS = {  # file stem: (phases, version, [(code, mppt, ac_kw, ac_kva, ac_a, pv_kw)])
    "S5-GR3P_3-20_K-Global-Flyer-V3_8": (3, "V3.8", [
        ("S5-GR3P3K", 2, 3.0, 3.3, 4.7, 4.5), ("S5-GR3P4K", 2, 4.0, 4.4, 6.4, 6.0), ("S5-GR3P5K", 2, 5.0, 5.5, 7.9, 7.5), ("S5-GR3P6K", 2, 6.0, 6.6, 9.5, 9.0),
        ("S5-GR3P8K", 2, 8.0, 8.8, 12.7, 12.0), ("S5-GR3P9K", 2, 9.0, 9.9, 14.3, 13.5), ("S5-GR3P10K", 2, 10.0, 11.0, 15.9, 15.0), ("S5-GR3P12K", 2, 12.0, 13.2, 19.1, 18.0),
        ("S5-GR3P13K", 2, 13.0, 14.3, 20.7, 19.5), ("S5-GR3P15K", 2, 15.0, 16.5, 23.8, 22.5), ("S5-GR3P17K", 2, 17.0, 18.7, 27.0, 25.5), ("S5-GR3P20K", 2, 20.0, 22.0, 31.8, 30.0)]),
    "S6-GR1P_0_7-3_6_K-Global-Flyer-V3_8": (1, "V3.8", [
        ("S6-GR1P0.7K-M", 1, 0.7, 0.77, 4.4, 1.1), ("S6-GR1P1K-M", 1, 1.0, 1.1, 5.2, 1.5), ("S6-GR1P1.5K-M", 1, 1.5, 1.65, 8.1, 2.3), ("S6-GR1P2K-M", 1, 2.0, 2.2, 10.5, 3.0),
        ("S6-GR1P2.5K-M", 1, 2.5, 2.75, 13.3, 3.8), ("S6-GR1P3K-M", 1, 3.0, 3.3, 15.7, 4.5), ("S6-GR1P3.6K-M", 1, 3.6, 3.6, 16.0, 5.4)]),
    "S6-GR1P_0_7-3_6_K-Global-Flyer-V1_0": (1, "V1.0", [
        ("S6-GR1P0.7K01-NV-YD", 1, 0.7, 0.77, 3.5, 1.1), ("S6-GR1P1K01-NV-YD", 1, 1.0, 1.1, 5.0, 1.5), ("S6-GR1P1.5K01-NV-YD", 1, 1.5, 1.65, 7.5, 2.3),
        ("S6-GR1P2K01-NV-YD", 1, 2.0, 2.2, 10.0, 3.0), ("S6-GR1P2.5K01-NV-YD", 1, 2.5, 2.75, 12.5, 3.8), ("S6-GR1P3K01-NV-YD", 1, 3.0, 3.3, 15.0, 4.5),
        ("S6-GR1P3.6K01-NV-YD", 1, 3.6, 3.6, 16.0, 5.4)]),
    "S6-GR1P_2_5-6_K-ND-Global-Flyer-V3_8": (1, "V3.8", [  # the flyer's own title is S6-GR1P(2.5-6)K-S(21A)
        ("S6-GR1P2.5K-S(21A)", 2, 2.5, 2.5, 11.4, 3.75), ("S6-GR1P3K-S(21A)", 2, 3.0, 3.0, 13.6, 4.5), ("S6-GR1P3.6K-S(21A)", 2, 3.6, 3.6, 16.0, 5.4),
        ("S6-GR1P4K-S(21A)", 2, 4.0, 4.0, 18.2, 6.0), ("S6-GR1P4.6K-S(21A)", 2, 4.6, 4.6, 20.9, 6.9), ("S6-GR1P5K-S(21A)", 2, 5.0, 5.0, 22.7, 7.5),
        ("S6-GR1P6K-S(21A)", 2, 6.0, 6.0, 27.3, 9.0)]),
    "Solis_Inverter_S6-GR3P_3-10_K02-NV-ND_Datasheet_GLOBAL_V2_7_202507": (3, "V2.7 2025-07", [
        ("S6-GR3P3K02-NV-ND", 2, 3.0, 3.0, 4.3, 4.5), ("S6-GR3P4K02-NV-ND", 2, 4.0, 4.0, 5.8, 6.0), ("S6-GR3P5K02-NV-ND", 2, 5.0, 5.0, 7.2, 7.5),
        ("S6-GR3P6K02-NV-ND", 2, 6.0, 6.0, 8.7, 9.0), ("S6-GR3P8K02-NV-ND", 2, 8.0, 8.0, 11.5, 12.0), ("S6-GR3P9K02-NV-ND", 2, 9.0, 9.0, 13.0, 13.5),
        ("S6-GR3P10K02-NV-ND", 2, 10.0, 10.0, 14.4, 15.0)]),
    # S5-GC(25-50)K: the MPPT row reads "3 / 6" centred under 25K-40K and "4 / 8" under the two -HV columns
    "S5-GC_25-50_K-Global-Flyer-V3_8": (3, "V3.8", [
        ("S5-GC25K", 3, 25.0, 27.5, 41.8, 37.5), ("S5-GC30K", 3, 30.0, 33.0, 50.2, 45.0), ("S5-GC33K", 3, 33.0, 36.3, 55.1, 49.5), ("S5-GC36K", 3, 36.0, 39.6, 60.2, 54.0),
        ("S5-GC40K", 3, 40.0, 44.0, 66.9, 60.0), ("S5-GC40K-HV", 4, 40.0, 44.0, 53.0, 60.0), ("S5-GC50K-HV", 4, 50.0, 55.0, 66.2, 75.0)]),
    "S5-GC_50-60_K-Global-Flyer-V3_8": (3, "V3.8", [("S5-GC50K", 5, 50.0, 55.0, 83.6, None), ("S5-GC60K", 6, 60.0, 66.0, 100.3, None)]),
    "S5-GC_100-125_K-Global-Flyer-V3_8": (3, "V3.8", [("S5-GC100K", 10, 100.0, 110.0, 167.1, None), ("S5-GC110K", 10, 110.0, 121.0, 183.8, None), ("S5-GC125K-HV", 10, 125.0, 137.5, 165.4, None)]),
    "S6-GC_80-125_K-Global-Flyer-V4_0": (3, "V4.0", [
        ("S6-GC80K", None, 80.0, 88.0, 133.7, None), ("S6-GC100K", None, 100.0, 110.0, 167.1, None), ("S6-GC110K", None, 110.0, 121.0, 183.8, None),
        ("S6-GC125K", None, 125.0, 125.0, 189.9, None), ("S6-GC125K-HV", None, 125.0, 137.5, 165.4, None)]),
    "S6-GC_50-75_K-Global-Flyer-V4_0": (3, "V4.0", [("S6-GC50K-LV", None, 50.0, 55.0, 144.3, None), ("S6-GC60K-LV", None, 60.0, 66.0, 173.2, None), ("S6-GC75K-LV", None, 75.0, 75.0, 196.8, None)]),
    "S5-GC_15-23_K-Global-Flyer-V3_8": (3, "V3.8", [("S5-GC15K-LV", 3, 15.0, 16.5, 43.3, 22.5), ("S5-GC20K-LV", 3, 20.0, 22.0, 57.7, 30.0), ("S5-GC23K-LV", 3, 23.0, 25.0, 65.0, 34.5)]),
    "S5-GC_25-36_K-Global-Flyer-V3_8": (3, "V3.8", [("S5-GC25K-LV", 4, 25.0, 27.5, 72.2, None), ("S5-GC30K-LV", 4, 30.0, 33.0, 86.6, None), ("S5-GC36K-LV", 4, 36.0, 36.0, 94.5, None)]),
    "S6-GC3P_25-40_K-ND-Global-Flyer-V3_9": (3, "V3.9", [
        ("S6-GC3P25K03-NV-ND", 3, 25.0, 25.0, 36.1, 37.5), ("S6-GC3P30K03-NV-ND", 3, 30.0, 30.0, 43.3, 45.0), ("S6-GC3P33K03-NV-ND", 3, 33.0, 33.0, 47.6, 49.5),
        ("S6-GC3P36K03-NV-ND", 3, 36.0, 36.0, 52.0, 54.0), ("S6-GC3P40K03-HV-ND", 3, 40.0, 40.0, 48.1, 60.0)]),
    "S6-GC3P_40-60_K-ND-Global-Flyer-V3_9": (3, "V3.9", [
        ("S6-GC3P40K04-NV-ND", 4, 40.0, 40.0, 57.7, None), ("S6-GC3P50K04-NV-ND", None, 50.0, 50.0, 72.2, None), ("S6-GC3P60K05-NV-ND", 5, 60.0, 60.0, 86.6, None),
        ("S6-GC3P50K04-HV-ND", 4, 50.0, 50.0, 60.1, None), ("S6-GC3P60K05-HV-ND", 5, 60.0, 60.0, 72.2, None)]),
    "S6-GC3P_150-200_K-ND-Global-Flyer-V4_2": (3, "V4.2", [("S6-GC3P150K07-NV-ND", 7, 150.0, 165.0, 250.6, None), ("S6-GC3P200K07-HV-ND", 7, 200.0, 200.0, 240.6, None)]),
    "S6-GC3P_23-36_K-Global-Flyer-V3_8": (3, "V3.8", [
        ("S6-GC3P23K03-LV-ND", 3, 23.0, 23.0, 57.7, None), ("S6-GC3P25K04-LV-ND", 4, 25.0, 25.0, 62.8, None), ("S6-GC3P30K04-LV-ND", 4, 30.0, 30.0, 75.3, None),
        ("S6-GC3P36K04-LV-ND", 4, 36.0, 36.0, 90.4, None)]),
    "S6-GC3P_15-20_K-Global-Flyer-V3_8": (3, "V3.8", [("S6-GC3P15K03-LV-ND", 3, 15.0, 15.0, 37.7, 22.5), ("S6-GC3P20K03-LV-ND", 3, 20.0, 20.0, 50.2, 30.0)]),
    "S6-EH3P_3-10_K-ND-Global-Flyer-V3_8": (3, "V3.8", [
        ("S6-EH3P5K2-H", None, 5.0, 5.0, None, 10.0), ("S6-EH3P6K2-H", None, 6.0, 6.0, None, 12.0), ("S6-EH3P8K2-H", None, 8.0, 8.0, None, 16.0), ("S6-EH3P10K2-H", None, 10.0, 10.0, None, 20.0),
        ("S6-EH3P3K-H-EU", None, 3.0, 3.0, None, 6.0), ("S6-EH3P4K-H-EU", None, 4.0, 4.0, None, 8.0), ("S6-EH3P5K-H-EU", None, 5.0, 5.0, None, 10.0),
        ("S6-EH3P6K-H-EU", None, 6.0, 6.0, None, 12.0), ("S6-EH3P8K-H-EU", None, 8.0, 8.0, None, 16.0), ("S6-EH3P10K-H-EU", None, 10.0, 10.0, None, 20.0)]),
    "S6-EH3P12K-ND-Global-Flyer-V3_8": (3, "V3.8", [("S6-EH3P12K-H-EU(21A)", 4, 12.0, 12.0, None, 24.0)]),
    "S6-EH3P_15-20_K-Global-Flyer-V4_0": (3, "V4.0", [("S6-EH3P15K-H", 4, 15.0, 15.0, None, 30.0), ("S6-EH3P20K-H", 4, 20.0, 20.0, None, 40.0)]),
    "S6-EH3P_15-20_K-ND-Global-Flyer-V4_0": (3, "V4.0", [("S6-EH3P15K-ND-H", 4, 15.0, 15.0, None, 30.0), ("S6-EH3P20K-ND-H", 4, 20.0, 20.0, None, 40.0)]),
    "S6-EH3P_29_9-50_K-Global-Flyer-V3_8": (3, "V3.8", [
        ("S6-EH3P29.9K-H", 3, 29.9, 29.9, None, 59.8), ("S6-EH3P30K-H", 3, 30.0, 30.0, None, 60.0), ("S6-EH3P40K-H", 4, 40.0, 40.0, None, 80.0), ("S6-EH3P50K-H", 4, 50.0, 50.0, None, 100.0)]),
    "S6-EH3P_30-50_K-ND-Global-Flyer-V3_8": (3, "V3.8", [
        ("S6-EH3P30K-H-ND", 3, 30.0, 30.0, None, 60.0), ("S6-EH3P40K-H-ND", 4, 40.0, 40.0, None, 80.0), ("S6-EH3P49K-H-ND", 4, 49.0, 49.0, None, 98.0), ("S6-EH3P50K-H-ND", 4, 50.0, 50.0, None, 100.0)]),
    "S6-EH3P_5-18_K-Global-Flyer-V4_1": (3, "V4.1", [
        ("S6-EH3P5K02-NV-YD-L", 2, 5.0, 5.0, None, 10.0), ("S6-EH3P6K02-NV-YD-L", 2, 6.0, 6.0, None, 12.0), ("S6-EH3P8K02-NV-YD-L", 2, 8.0, 8.0, None, 16.0),
        ("S6-EH3P10K02-NV-YD-L", 2, 10.0, 10.0, None, 20.0), ("S6-EH3P12K02-NV-YD-L", 2, 12.0, 12.0, None, 24.0), ("S6-EH3P15K02-NV-YD-L", 2, 15.0, 15.0, None, 30.0),
        ("S6-EH3P18K02-NV-YD-L", 2, 18.0, 18.0, None, 36.0)]),
    "S6-EH1P_3-10_K-Global-Flyer-V4_1": (1, "V4.1", [
        ("S6-EH1P3K-L-PLUS", 2, 3.0, 3.0, None, 6.0), ("S6-EH1P3.6K-L-PLUS", 2, 3.6, 3.6, None, 7.2), ("S6-EH1P4.6K-L-PLUS", 2, 4.6, 4.6, None, 9.2),
        ("S6-EH1P5K-L-PLUS", 2, 5.0, 5.0, None, 10.0), ("S6-EH1P6K-L-PLUS", 2, 6.0, 6.0, None, 12.0), ("S6-EH1P8K-L-PLUS", 2, 8.0, 8.0, None, 16.0)]),
    "Solis_datasheet_S6-EH1P_3-6_K-L-EU_Global_V3_4_202411": (1, "V3.4 2024-11", [
        ("S6-EH1P3K-L-EU", 2, 3.0, 3.0, 13.0, 4.8), ("S6-EH1P3.6K-L-EU", 2, 3.6, 3.6, 15.7, 5.7), ("S6-EH1P4.6K-L-EU", 2, 4.6, 4.6, 20.0, 7.0),
        ("S6-EH1P5K-L-EU", 2, 5.0, 5.0, 21.7, 8.0), ("S6-EH1P6K-L-EU", 2, 6.0, 6.0, 26.1, 9.6)]),
    "Solis_datasheet_S6-EH1P_3-6_K-L-PRO_GLOBAL_V1_7_202504": (1, "V1.7 2025-04", [
        ("S6-EH1P3K-L-PRO", 2, 3.0, 3.3, 15.0, 6.0), ("S6-EH1P3.6K-L-PRO", 2, 3.6, 4.0, 20.0, 7.2), ("S6-EH1P5K-L-PRO", 2, 5.0, 5.5, 25.0, 10.0), ("S6-EH1P6K-L-PRO", 2, 6.0, 6.6, 30.0, 12.0)]),
    "S6-EA1P_3_6-6_K-ND-Global-Flyer-V3_8": (1, "V3.8", [
        ("S6-EA1P3.6K-L", 0, 3.6, 3.6, 15.7, None), ("S6-EA1P4.6K-L", 0, 4.6, 4.6, 20.0, None), ("S6-EA1P5K-L", 0, 5.0, 5.0, 21.8, None), ("S6-EA1P6K-L", 0, 6.0, 6.0, 26.1, None)]),
}


def solis():
    urls = dict(line.split(" ", 1) for line in (CACHE / "solis/SOURCES.txt").read_text(encoding="utf-8").splitlines() if " " in line)
    sources, models = [], []
    for stem, (ph, ver, rows) in SOLIS.items():
        pdf = stem + ".pdf"
        sid = re.sub(r"[^a-z0-9]+", "-", re.sub(r"-global-flyer-v[\d_]+$|^solis_(datasheet|inverter)_|_datasheet|_global.*$", "", stem.lower())).strip("-")
        sources.append({"id": sid, "url": urls.get(pdf, ""), "file": pdf, "version": ver, "note": "version from the file name; the flyer's last page is the datasheet", "seen": SEEN})
        for code, mp, ackw, kva, aca, pv in rows:
            m = row(code, mp, ackw, kva, aca, ph, pv, sid)
            if re.match(r"^S[56]-G[RC]", code):  # "Solis S5-GR3P10K", "S6-GC3P23K03-LV-ND (Connected in Delta 3X230V)"
                m["match"] = f"^(SOLIS)?{re.escape(code)}(\\(CONNECTED.*\\))?$"
            models.append(m)
    dump("solis", {"brand": "Solis", "maker_site": "https://www.solisinverters.com/", "rule": RULE, "sources": sources, "models": models})


# ---------------------------------------------------------------- hand-read sheets (SAJ, SolaX, Hoymiles): one table per brand
def hand_brand(key, brand, site, cache_dir, table, src_note=""):
    """table: {pdf stem: (phases, version, note, rows)}; a row is (code, mppt, ac_kw, ac_kva, ac_a, pv_kw[, match]).
    The rows are typed from the sheet's table (cache/specs/<brand>/<stem>.txt, spanned cells read by x-position with
    pdfplumber); the source id is the stem in lower case. A code is matched exactly unless the row carries a `match` regex."""
    urls = dict(line.split(" ", 1) for line in (CACHE / cache_dir / "SOURCES.txt").read_text(encoding="utf-8").splitlines() if " " in line)
    sources, models = [], []
    for stem, (ph, ver, note, rows) in table.items():
        pdf = stem + ".pdf"
        sid = re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")
        url = urls.get(pdf, "").split(" (")[0]
        sources.append({"id": sid, "url": url, "file": pdf, "version": ver, "note": (note + ("; " if note and src_note else "") + src_note).strip(), "seen": SEEN})
        for r in rows:
            code, mp, ackw, kva, aca, pv = r[:6]
            m = row(code, mp, ackw, kva, aca, ph, pv, sid)
            if len(r) > 6 and r[6]:
                m["match"] = r[6]
            models.append(m)
    dump(key, {"brand": brand, "maker_site": site, "rule": RULE, "sources": sources, "models": models})


# SAJ: www.saj-electric.com download centre (HubSpot, server-rendered; ?type=Datasheet&page=N). English BEU/EU/Global sheets.
# The sheets carry no version except where noted; "updated" is the download centre's own "Last updated" date.
# HS5/HS2/HS3/AS3 are all-in-one units: the code's X is the battery configuration, W/G the communication module (sheet note).
def saj_hs5(prefix, three):
    if three:
        return [(f"{prefix} HS5-8K-T3-X", 3, 8.0, 8.8, 12.8, 16.0, rf"^{prefix}HS5-?8K-?T3-(\d+|X;.*)$"),
                (f"{prefix} HS5-10K-T3-X", 3, 9.999, 9.999, 14.5, 20.0, rf"^{prefix}HS5-?10K-?T3-(\d+|X;.*)$"),
                (f"{prefix} HS5-12K-T3-X", 3, 12.0, 13.2, 19.1, 24.0, rf"^{prefix}HS5-?12K-?T3-(\d+|X;.*)$"),
                (f"{prefix} HS5-12K-T3-X-IE", 3, 11.0, 11.0, 15.9, 24.0, rf"^{prefix}HS5-?12K-?T3-(\d+-IE|X-IE;.*)$"),
                (f"{prefix} HS5-15K-T3-X", 3, 15.0, 16.5, 23.9, 30.0, rf"^{prefix}HS5-?15K-?T3-(\d+|X;.*)$"),
                (f"{prefix} HS5-20K-T3-X", 3, 20.0, 22.0, 31.9, 40.0, rf"^{prefix}HS5-?20K-?T3-(\d+|X;.*)$")]
    last = 10.0 if prefix == "EK70" else 9.999
    return [(f"{prefix} HS5-5K-S3-X", 3, 4.999, 4.999, 21.7, 10.0, rf"^{prefix}HS5-?5K-?S3-(\d+|X;.*)$"),
            (f"{prefix} HS5-6K-S3-X", 3, 6.0, 6.6, 28.7, 12.0, rf"^{prefix}HS5-?6K-?S3-(\d+|X;.*)$"),
            (f"{prefix} HS5-6K-S3-X-IE", 3, 5.75, 5.75, 25.0, 12.0, rf"^{prefix}HS5-?6K-?S3-(\d+-IE|X-IE;.*)$"),
            (f"{prefix} HS5-8K-S3-X", 3, 8.0, 8.8, 38.3, 16.0, rf"^{prefix}HS5-?8K-?S3-(\d+|X;.*)$"),
            (f"{prefix} HS5-10K-S4-X", 4, last, last, 47.8 if prefix == "EK70" else 43.5, 20.0, rf"^{prefix}HS5-?10K-?S4-(\d+|X;.*)$")]


def saj_hs2(code, mp, kw, kva, a, pv):  # "HS2-5K-T2-X": the lists write HS2-5K-T2, HS2-5K-T2-3, HS2-5K-T2-3 WiFi, HS2-5K-T2-X WiFi (X=2, 3, 4, 5)
    base = re.escape(code[:-2])
    return (code, mp, kw, kva, a, pv, rf"^{base}(-[2-5X])?(WIFI(\(X=.*\))?)?$")


def saj_hs3(code, mp, kw, kva, a, pv):  # "HS3-5K-T2-W/G-PX": the lists write HS3-5K-T2-W-PX, HS3-5K-T2-G-PX and "HS3-5K-T2-W-PX; HS3-5K-T2-G-PX (X=1, ...)"
    base, tail = code.split("-W/G-")
    return (code, mp, kw, kva, a, pv, rf"^{re.escape(base)}-[WG]-{re.escape(tail)}(;.*)?$")


SAJ = {
    "EK70_HS5_Three_Phase-EU": (3, "", "updated 2026-06-16", saj_hs5("EK70", True)),
    "EK70_HS5_Single_Phase-EU": (1, "", "updated 2026-06-16", saj_hs5("EK70", False)),
    "EK90_HS5_Three_Phase-EU": (3, "", "updated 2026-05-29", saj_hs5("EK90", True)),
    "EK90_HS5_Single_Phase-EU": (1, "", "updated 2026-05-29", saj_hs5("EK90", False)),
    "HS3-5-12K-T2-datasheet-EN-BEU": (3, "", "updated 2025-07-22", [
        saj_hs3("HS3-5K-T2-W/G-PX", 2, 5.0, 5.5, 8.0, 10.0), saj_hs3("HS3-6K-T2-W/G-PX", 2, 6.0, 6.6, 9.6, 12.0), saj_hs3("HS3-8K-T2-W/G-PX", 2, 8.0, 8.8, 12.8, 12.0),
        saj_hs3("HS3-10K-T2-W/G-PX", 2, 10.0, 11.0, 15.9, 15.0), saj_hs3("HS3-12K-T2-W/G-PX", 2, 12.0, 12.0, 17.4, 15.0)]),
    "HS3-3-6K-S2-datasheet-EN-BEU": (1, "", "updated 2025-07-22", [
        saj_hs3("HS3-3K-S2-W/G-PX", 2, 3.0, 3.3, 14.3, 6.0), saj_hs3("HS3-3.6K-S2-W/G-PX", 2, 3.6, 3.6, 15.7, 7.2), saj_hs3("HS3-4K-S2-W/G-PX", 2, 4.0, 4.4, 19.1, 8.0),
        saj_hs3("HS3-4.6K-S2-W/G-PX", 2, 4.6, 4.6, 20.0, 9.2), saj_hs3("HS3-5K-S2-W/G-PX", 2, 5.0, 5.5, 23.9, 10.0), saj_hs3("HS3-6K-S2-W/G-PX", 2, 6.0, 6.0, 27.3, 12.0)]),
    "HS3-10K-T2-datasheet-EN-BEU": (3, "", "Belgian variant; updated 2025-07-22", [("HS3-10K-T2-W/G-P-BE", 2, 10.0, 10.0, 14.5, 15.0, r"^HS3-10K-T2-[WG]-PX-BE(;.*)?$")]),
    "HS3-5K-S2-datasheet-EN-BEU": (1, "", "Belgian variant; updated 2025-07-22", [("HS3-5K-S2-W/G-P-BE", 2, 5.0, 5.0, 21.7, 10.0, r"^HS3-5K-S2-[WG]-PX-BE(;.*)?$")]),
    "HS2-5-10K-T2-datasheet-EN-BEU": (3, "", "updated 2025-07-22", [
        saj_hs2("HS2-5K-T2-X", 2, 5.0, 5.5, 8.3, 7.5), saj_hs2("HS2-6K-T2-X", 2, 6.0, 6.6, 10.0, 9.0), saj_hs2("HS2-8K-T2-X", 2, 8.0, 8.8, 13.3, 12.0),
        saj_hs2("HS2-10K-T2-B-X", 2, 10.0, 10.0, 15.2, 15.0), saj_hs2("HS2-10K-T2-X", 2, 10.0, 11.0, 16.7, 15.0)]),
    "HS2-3-6K-S2-datasheet-EN-BEU": (1, "", "updated 2025-07-22", [
        saj_hs2("HS2-3K-S2-X", 2, 3.0, 3.3, 15.0, 4.5), saj_hs2("HS2-3.6K-S2-X", 2, 3.68, 3.68, 16.0, 5.4), saj_hs2("HS2-4K-S2-X", 2, 4.0, 4.4, 20.0, 6.0),
        saj_hs2("HS2-4.6K-S2-X", 2, 4.6, 4.6, 20.0, 6.9), saj_hs2("HS2-5K-S2-B-X", 2, 5.0, 5.0, 22.7, 7.5), saj_hs2("HS2-5K-S2-X", 2, 5.0, 5.5, 25.0, 7.5),
        saj_hs2("HS2-6K-S2-X", 2, 6.0, 6.0, 27.3, 9.0)]),
    "H2-5-10K-T2-datasheet-EN-BEU": (3, "", "updated 2025-07-22", [
        ("H2-5K-T2", 2, 5.0, 5.5, 8.3, 7.5), ("H2-6K-T2", 2, 6.0, 6.6, 10.0, 9.0), ("H2-8K-T2", 2, 8.0, 8.8, 13.3, 12.0), ("H2-10K-T2", 2, 10.0, 11.0, 16.7, 15.0),
        ("H2-10K-T2-B", 2, 10.0, 10.0, 15.2, 15.0)]),
    "H2-3-6K-S2-datasheet-EN-BEU": (1, "", "updated 2025-07-22", [
        ("H2-3K-S2", 2, 3.0, 3.3, 15.0, 4.5), ("H2-3.6K-S2", 2, 3.68, 3.68, 16.7, 5.4), ("H2-4K-S2", 2, 4.0, 4.4, 20.0, 6.0), ("H2-5K-S2", 2, 5.0, 5.5, 25.0, 7.5),
        ("H2-6K-S2", 2, 6.0, 6.0, 27.3, 9.0)]),
    "H2-5-10K-S3_datasheet_en": (1, "", "updated 2025-05-25", [
        ("H2-5K-S3", 3, 5.0, 5.5, 25.0, 7.5), ("H2-6K-S3-IE", 3, 5.5, 5.5, 25.0, 9.0), ("H2-6K-S3", 3, 6.0, 6.6, 30.0, 9.0), ("H2-7K-S3", 3, 7.0, 7.7, 35.0, 10.5),
        ("H2-8K-S3", 3, 8.0, 8.8, 40.0, 12.0), ("H2-10K-S3", 3, 10.0, 10.0, 45.5, 15.0)]),
    "H2-10-30K-T2T3-datasheet-EN-BEU": (3, "", "T2 = 2 MPPT, T3 = 3 MPPT (spanned cells read by position); updated 2025-07-22", [
        ("H2-10K-T3", 3, 10.0, 11.0, 16.0, 20.0), ("H2-12K-T3", 3, 12.0, 13.2, 19.2, 24.0), ("H2-15K-T2", 2, 15.0, 16.5, 24.0, 30.0), ("H2-15K-T3", 3, 15.0, 16.5, 24.0, 30.0),
        ("H2-20K-T2", 2, 20.0, 22.0, 31.9, 30.0), ("H2-20K-T3", 3, 20.0, 22.0, 31.9, 40.0), ("H2-25K-T3-BE", 3, 25.0, 25.0, 36.3, 45.0), ("H2-25K-T3", 3, 25.0, 27.5, 39.9, 45.0),
        ("H2-30K-T3-DE", 3, 29.999, 29.999, 43.4, 45.0), ("H2-30K-T3", 3, 30.0, 33.0, 47.9, 45.0)]),
    "R5-0.7-3K-S1-datasheet-EN-BEU": (1, "", "the lists also write 'R5 Series 1K K-S1-15'; updated 2025-07-22", [
        ("R5-0.7K-S1-15", 1, 0.7, 0.77, 3.5, 1.05, r"^(R5-|R5SERIES)0\.7KK?-S1-15$"), ("R5-1K-S1-15", 1, 1.0, 1.1, 5.0, 1.5, r"^(R5-|R5SERIES)1KK?-S1-15$"),
        ("R5-1.5K-S1-15", 1, 1.5, 1.65, 7.5, 2.25, r"^(R5-|R5SERIES)1\.5KK?-S1-15$"), ("R5-2K-S1-15", 1, 2.0, 2.2, 10.0, 3.0, r"^(R5-|R5SERIES)2KK?-S1-15$"),
        ("R5-2.5K-S1-15", 1, 2.5, 2.75, 12.5, 3.75, r"^(R5-|R5SERIES)2\.5KK?-S1-15$"), ("R5-3K-S1-15", 1, 3.0, 3.3, 15.0, 4.5, r"^(R5-|R5SERIES)3KK?-S1-15$")]),
    "R5-3-8K-S2-datasheet-EN-BEU": (1, "", "the lists also write 'R5 Series 3K K-S2-15'; updated 2025-07-22", [
        ("R5-3K-S2-15", 2, 3.0, 3.3, 14.4, 4.5, r"^(R5-|R5SERIES)3KK?-S2-15$"), ("R5-3.6K-S2-15", 2, 3.68, 3.68, 16.0, 5.52, r"^(R5-|R5SERIES)3\.6KK?-S2-15$"),
        ("R5-4K-S2-15", 2, 4.0, 4.4, 19.2, 6.0, r"^(R5-|R5SERIES)4KK?-S2-15$"), ("R5-5K-S2-15", 2, 5.0, 5.5, 23.9, 7.5, r"^(R5-|R5SERIES)5KK?-S2-15$"),
        ("R5-5K-S2-15-B", 2, 5.0, 5.0, 21.8, 7.5), ("R5-6K-S2-15", 2, 6.0, 6.0, 26.1, 9.0, r"^(R5-|R5SERIES)6KK?-S2-15$"),
        ("R5-7K-S2-15", 2, 7.0, 7.7, 33.5, 10.5, r"^(R5-|R5SERIES)7KK?-S2-15$"), ("R5-8K-S2-15", 2, 8.0, 8.0, 34.8, 12.0, r"^(R5-|R5SERIES)8KK?-S2-15$")]),
    "R6-3-15K-T2-datasheet-EN-BEU": (1, "", "the file is named R6-(3-15K)-T2 but holds the single-phase R6 S2 sheet; updated 2026-10-13", [
        ("R6-5K-S2-X", 2, 5.0, 5.5, 25.0, 7.5), ("R6-6K-S2-X", 2, 6.0, 6.6, 30.0, 9.0), ("R6-7K-S2-X", 2, 7.0, 7.7, 35.0, 10.5), ("R6-8K-S2-X", 2, 8.0, 8.8, 40.0, 12.0),
        ("R6-9K-S2-X", 2, 9.0, 9.9, 45.0, 12.0), ("R6-10K-S2-X", 2, 10.0, 10.0, 45.5, 12.0)]),
    "R6-5-10K-S2-datasheet-EN-BEU": (1, "", "the file is named R6-(5-10K)-S2 but holds the R6 S3 sheet; updated 2025-07-22", [
        ("R6-5K-S3", 3, 5.0, 5.5, 25.0, 7.5), ("R6-6K-S3", 3, 6.0, 6.6, 30.0, 9.0), ("R6-7K-S3", 3, 7.0, 7.7, 35.0, 10.5), ("R6-8K-S3", 3, 8.0, 8.8, 40.0, 12.0),
        ("R6-9K-S3", 3, 9.0, 9.9, 45.0, 13.5), ("R6-10K-S3", 3, 10.0, 10.0, 45.5, 15.0)]),
    "R6-8-25K-T2-datasheet-EN-BEU": (3, "", "updated 2025-07-22", [
        ("R6-15K-T2-32", 2, 15.0, 16.5, 25.0, 22.5), ("R6-17K-T2-32", 2, 17.0, 18.7, 28.3, 25.5), ("R6-20K-T2-32", 2, 20.0, 22.0, 33.3, 30.0), ("R6-22K-T2-32", 2, 22.0, 24.2, 36.7, 33.0),
        ("R6-25K-T2-32-B", 2, 25.0, 25.0, 37.9, 37.5), ("R6-25K-T2-32", 2, 25.0, 27.5, 41.7, 37.5)]),
    "R6-25-50K-T3T4-datasheet-EN-BEU": (3, "", "T3 = 3 MPPT, T4 = 4 MPPT (spanned cells read by position); updated 2025-07-22", [
        ("R6-25K-T3-32-B", 3, 25.0, 25.0, 37.9, 37.5), ("R6-25K-T3-32", 3, 25.0, 27.5, 41.7, 37.5), ("R6-30K-T3-32-B", 3, 30.0, 30.0, 45.5, 45.0), ("R6-30K-T3-32", 3, 30.0, 33.0, 50.0, 45.0),
        ("R6-33K-T3-32", 3, 33.0, 36.3, 55.0, 49.5), ("R6-36K-T3-32", 3, 36.0, 39.6, 60.0, 54.0), ("R6-36K-T4-32", 4, 36.0, 39.6, 60.0, 54.0), ("R6-40K-T4-32", 4, 40.0, 44.0, 66.7, 60.0),
        ("R6-50K-T4-32", 4, 50.0, 50.0, 75.8, 75.0)]),
    "C6_String_Inverter-datasheet-EN-BEU": (3, "", "T6/T9/T12 = 6/9/12 MPPT (spanned cell read by position); updated 2025-07-22", [
        ("C6-75K-T6-40", 6, 75.0, 82.5, 119.1, 144.0), ("C6-100K-T9-40", 9, 100.0, 110.0, 158.8, 200.0), ("C6-110K-T12-40", 12, 110.0, 121.0, 174.6, 220.0), ("C6-125K-T12-40", 12, 125.0, 125.0, 180.4, 250.0)]),
    "EK60_H3-2.9-6K-LS2_Datasheet_en_EU": (1, "V1.1", "max AC current is given per grid voltage (e.g. 13.4/12.8) and left null; updated 2026-06-29", [
        ("EK60 H3-2.9K-LS2", 2, 2.94, 2.94, None, 4.64), ("EK60 H3-3K-LS2", 2, 3.0, 3.3, None, 4.8), ("EK60 H3-3.6K-LS2", 2, 3.68, 3.68, None, 5.76), ("EK60 H3-4K-LS2", 2, 4.0, 4.4, None, 6.4),
        ("EK60 H3-4.6K-LS2", 2, 4.6, 4.6, None, 7.36), ("EK60 H3-5K-LS2", 2, 4.999, 4.999, None, 8.0), ("EK60 H3-6K-LS2", 2, 6.0, 6.6, None, 9.6), ("EK60 H3-6K-LS2-IE", 2, 5.75, 5.75, 25.0, 9.6)]),
    "H1-3-6K-S2-15-EN": (1, "V2.3", "updated 2025-07-09", [
        ("H1-3K-S2-15", 2, 3.0, 3.0, 13.6, 4.5), ("H1-3.6K-S2-15", 2, 3.68, 3.68, 16.7, 5.4), ("H1-4K-S2-15", 2, 4.0, 4.0, 18.2, 6.0), ("H1-4.6K-S2-15", 2, 4.6, 4.6, 20.9, 6.9),
        ("H1-5K-S2-15", 2, 5.0, 5.0, 22.7, 7.5), ("H1-6K-S2-15-IE", 2, 5.5, 5.5, 25.0, 9.0), ("H1-6K-S2-15", 2, 6.0, 6.0, 27.3, 9.0)]),
    "AS3-3K-8K-T-datasheet-EN-BEU": (3, "V1.0", "AC-coupling solution: the sheet lists no PV input, hence mppt 0; updated 2026-03-31", [
        ("AS3-3K-T-W/G-PX", 0, 3.0, None, 4.8, None, r"^AS3-3K-T-[WG]-PX$"), ("AS3-4K-T-W/G-PX", 0, 4.0, None, 6.4, None, r"^AS3-4K-T-[WG]-PX$"),
        ("AS3-5K-T-W/G-PX", 0, 5.0, None, 8.0, None, r"^AS3-5K-T-[WG]-PX$"), ("AS3-6K-T-W/G-PX", 0, 6.0, None, 9.6, None, r"^AS3-6K-T-[WG]-PX$"),
        ("AS3-8K-T-W/G-PX", 0, 8.0, None, 12.8, None, r"^AS3-8K-T-[WG]-PX$")]),
    "AS3-10K-12K-T-datasheet-EN-BEU": (3, "V1.0", "AC-coupling solution: the sheet lists no PV input, hence mppt 0; updated 2026-03-31", [
        ("AS3-10K-T-W/G-PX", 0, 10.0, None, 15.9, None, r"^AS3-10K-T-[WG]-PX$"), ("AS3-10K-T-W/G-PX-BE", 0, 10.0, None, 14.5, None, r"^AS3-10K-T-[WG]-PX-BE$"),
        ("AS3-12K-T-W/G-PX", 0, 12.0, None, 17.4, None, r"^AS3-12K-T-[WG]-PX$"), ("AS3-12K-T-W/G-PX-IE", 0, 11.0, None, 15.9, None, r"^AS3-12K-T-[WG]-PX-IE$")]),
    "AS3-3K-4.6K-S-datasheet-EN-BEU": (1, "V1.0", "AC-coupling solution: the sheet lists no PV input, hence mppt 0; updated 2026-03-31", [
        ("AS3-3K-S-W/G-PX", 0, 3.0, None, 14.4, None, r"^AS3-3K-S-[WG]-PX$"), ("AS3-3.6K-S-W/G-PX", 0, 3.6, None, 15.7, None, r"^AS3-3\.6K-S-[WG]-PX$"),
        ("AS3-4K-S-W/G-PX", 0, 4.0, None, 19.1, None, r"^AS3-4K-S-[WG]-PX$"), ("AS3-4.6K-S-W/G-PX", 0, 4.6, None, 20.0, None, r"^AS3-4\.6K-S-[WG]-PX$")]),
    "AS3-5K-6K-S-datasheet-EN-BEU": (1, "V1.0", "AC-coupling solution: the sheet lists no PV input, hence mppt 0; updated 2026-03-31", [
        ("AS3-5K-S-W/G-PX", 0, 5.0, None, 23.9, None, r"^AS3-5K-S-[WG]-PX$"), ("AS3-5K-S-W/G-PX-BE", 0, 5.0, None, 21.7, None, r"^AS3-5K-S-[WG]-PX-BE$"),
        ("AS3-6K-S-W/G-PX", 0, 6.0, None, 26.1, None, r"^AS3-6K-S-[WG]-PX$"), ("AS3-6K-S-W/G-PX-IE", 0, 5.75, None, 25.0, None, r"^AS3-6K-S-[WG]-PX-IE$")]),
    "CHS2-29.9K-50K-X_datasheet_en_BNL": (3, "V1.1", "C&I hybrid: the sheet gives strings per MPPT (2) but no MPPT count row; updated 2025-05-25", [
        ("CHS2-29.9K-T4-X", None, 29.999, None, 43.3, 59.998), ("CHS2-30K-T4-X", None, 30.0, None, 47.9, 60.0), ("CHS2-50K-T6-X", None, 50.0, None, 79.8, 100.0),
        ("CH2-29.9K-T4", None, 29.999, 29.999, 43.3, 59.998), ("CH2-30K-T4", None, 30.0, 33.0, 47.9, 60.0), ("CH2-50K-T6", None, 50.0, 55.0, 79.8, 100.0)]),
    "M2-1.8-2.25K-S4-datasheet-EN-BEU": (1, "", "microinverter: the sheet gives 'Maximum Output Power [VA]' and a nominal (not max) current; updated 2025-07-22", [
        ("M2-1.8K-S4", 4, None, 1.8, None, None), ("M2-2K-S4", 4, None, 2.0, None, None), ("M2-2.2K-S4", 4, None, 2.2, None, None), ("M2-2.25K-S4", 4, None, 2.25, None, None)]),
    "M2-0.6-1K-S2-datasheet-EN-BEU": (1, "", "microinverter: the sheet gives 'Maximum Output Power [VA]' and a nominal (not max) current; updated 2025-07-22", [
        ("M2-0.6K-S2", 2, None, 0.6, None, None), ("M2-0.8K-S2", 2, None, 0.8, None, None), ("M2-1K-S2", 2, None, 1.0, None, None)]),
}


def saj():
    hand_brand("saj", "SAJ", "https://www.saj-electric.com/", "saj", SAJ)


# SolaX: www.solaxpower.com download centre (ysecm_api template data.html per productid; each /downloads-NNNN.html page links
# /uploads/file/*.pdf). English sheets; X1-Hybrid G4 and X1-FIT G4 only exist in German, X3-Hybrid G4 in English by direct file.
# SolaX sheets give a rated and a max apparent power but mostly only a rated (not max) current, so ac_a stays null there.
SOLAX = {
    "x3-hybrid-g4-datasheet-en": (3, "V3.8", "the lists also write X3-Hybrid-5.0-M, X3-Hybrid-5.0-D/M, 'X3 Hybrid G4 5.0', 'Solax X3-Hybrid-5.0-D'", [
        ("X3-HYBRID-5.0-D", 2, 5.0, 5.5, None, 10.0, r"^(SOLAX)?X3-HYBRID-5\.0K?-[DM](/M)?$|^X3HYBRIDG45\.0$"), ("X3-HYBRID-6.0-D", 2, 6.0, 6.6, None, 12.0, r"^(SOLAX)?X3-HYBRID-6\.0K?-[DM](/M)?$|^X3HYBRIDG46\.0$"),
        ("X3-HYBRID-8.0-D", 2, 8.0, 8.8, None, 16.0, r"^(SOLAX)?X3-HYBRID-8\.0K?-[DM](/M)?$|^X3HYBRIDG48\.0$"), ("X3-HYBRID-10.0-D", 2, 10.0, 11.0, None, 20.0, r"^(SOLAX)?X3-HYBRID-10\.0K?-[DM](/M)?$|^X3HYBRIDG410$"),
        ("X3-HYBRID-12.0-D", 2, 12.0, 13.2, None, 24.0, r"^(SOLAX)?X3-HYBRID-12\.0K?-[DM](/M)?$|^X3HYBRIDG412$"), ("X3-HYBRID-15.0-D", 2, 15.0, 15.0, None, 30.0, r"^(SOLAX)?X3-HYBRID-15\.0K?-[DM](/M)?$|^X3HYBRIDG415$")]),
    "solax-x3-hyb-g4-pro-datasheet-en": (3, "V2.7", "4-6 kW 2 MPPT, 8-15 kW 3 MPPT (spanned cells by position); the rated-power row is headed 'Rated output apparent power' but given in W", [
        ("X3-HYB-4.0-P", 2, 4.0, 4.4, None, 8.0, r"^X3-HYB-4\.0K?-P$"), ("X3-HYB-5.0-P", 2, 5.0, 5.5, None, 10.0, r"^X3-HYB-5\.0K?-P$"), ("X3-HYB-6.0-P", 2, 6.0, 6.6, None, 12.0, r"^X3-HYB-6\.0K?-P$"),
        ("X3-HYB-8.0-P", 3, 8.0, 8.8, None, 16.0, r"^X3-HYB-8\.0K?-P$"), ("X3-HYB-10.0-P", 3, 10.0, 11.0, None, 20.0, r"^X3-HYB-10\.0K?-P$"), ("X3-HYB-12.0-P", 3, 12.0, 13.2, None, 24.0, r"^X3-HYB-12\.0K?-P$"),
        ("X3-HYB-15.0-P", 3, 15.0, 16.5, None, 30.0, r"^X3-HYB-15\.0K?-P$")]),
    "x1-hybrid-g4-de": (1, "V2.9", "German sheet (no English one on the site); 5.0-D's power and current carry footnotes the reader lost, left null; the lists also write X1-HYBRID-G4-3.0-D/M, 'X1 Hybrid G4 3.0'", [
        ("X1-HYBRID-3.0-D", 2, 3.0, 3.3, 14.4, 6.0, r"^X1-HYBRID-3\.0K?-D$|^X1-HYBRID-G4-3\.0-D/M$|^X1HYBRIDG43\.0$"), ("X1-HYBRID-3.7-D", 2, 3.68, 3.68, 16.0, 7.4, r"^X1-HYBRID-3\.7K?-D$|^X1-HYBRID-G4-3\.7-D/M$|^X1HYBRIDG43\.7$"),
        ("X1-HYBRID-5.0-D", 2, None, None, None, 10.0, r"^X1-HYBRID-5\.0K?-D$|^X1-HYBRID-G4-5\.0-D/M$|^X1HYBRIDG45\.0$"), ("X1-HYBRID-6.0-D", 2, 6.0, 6.6, 28.6, 12.0, r"^X1-HYBRID-6\.0K?-D$|^X1-HYBRID-G4-6\.0-D/M$|^X1HYBRIDG46\.0$"),
        ("X1-HYBRID-7.5-D", 2, 7.5, 7.5, 32.6, 15.0, r"^X1-HYBRID-7\.5K?-D$|^X1-HYBRID-G4-7\.5-D/M$|^X1HYBRIDG47\.5$")]),
    "x1-fit-g4-de": (1, "V2.7", "German sheet; AC-coupled retrofit inverter, the sheet lists no PV input, hence mppt 0; apparent power and most currents carry footnotes the reader lost", [
        ("X1-FIT-3.7-W", 0, 3.68, None, 16.0, None), ("X1-FIT-4.6-W", 0, 4.6, None, None, None), ("X1-FIT-5.0-W", 0, 5.0, None, None, None), ("X1-FIT-6.0-W", 0, 6.0, None, 28.6, None), ("X1-FIT-7.5-W", 0, 7.5, None, None, None)]),
    "x3-retrofit-g4-datasheet-en": (3, "V2.7", "AC-coupled retrofit inverter: the sheet lists no PV input, hence mppt 0; the lists also write X3-Fit-G4-6.0-M/W", [
        ("X3-FIT-6.0-W", 0, 6.0, 6.6, 9.7, None, r"^X3-FIT-6\.0-W$|^X3-FIT-G4-6\.0-M/W$"), ("X3-FIT-8.0-W", 0, 8.0, 8.8, 12.9, None, r"^X3-FIT-8\.0-W$|^X3-FIT-G4-8\.0-M/W$"),
        ("X3-FIT-10.0-W", 0, 10.0, 11.0, 16.1, None, r"^X3-FIT-10\.0-W$|^X3-FIT-G4-10\.0-M/W$"), ("X3-FIT-15.0-W", 0, 15.0, 15.0, 24.1, None, r"^X3-FIT-15\.0-W$|^X3-FIT-G4-15\.0-M/W$")]),
    "x1-ac-datasheet-en": (1, "", "AC-coupled battery inverter ('AC Coupled' on the sheet, no PV input), hence mppt 0; power given in VA only", [
        ("X1-AC-3.0", 0, None, 3.0, 13.6, None), ("X1-AC-3.6", 0, None, 3.68, 16.8, None), ("X1-AC-4.6", 0, None, 4.6, 21.0, None), ("X1-AC-5.0", 0, None, 4.999, 21.7, None)]),
    "solax-x1-ies-a-datasheet-en": (1, "V1.0", "'AC-Coupling ESS': no PV input, hence mppt 0; nominal power in VA; first 'Max. AC current' row (grid side)", [
        ("X1-IES-3.7K-A", 0, None, 3.68, 16.0, None), ("X1-IES-5K-A", 0, None, 5.0, 21.8, None), ("X1-IES-6K-A", 0, None, 6.0, 28.7, None), ("X1-IES-8K-A", 0, None, 8.0, 34.8, None)]),
    "solax-x3-ies-a-datasheet-en": (3, "V1.0", "'AC-Coupling ESS': no PV input, hence mppt 0; nominal power in VA; first 'Max. AC current' row (grid side)", [
        ("X3-IES-5K-A", 0, None, 5.0, 8.0, None), ("X3-IES-10K-A", 0, None, 10.0, 14.5, None), ("X3-IES-15K-A", 0, None, 15.0, 24.0, None)]),
    "solax-x1-ies-datasheet-en": (1, "V2.0", "2.5-3.7 kW 2 MPPT, 5-8 kW 3 MPPT (spanned cells by position); kW from the sheet's 'Rated power' line; 5K's apparent power carries a VDE footnote the reader lost", [
        ("X1-IES-2.5K", 2, 2.5, 2.5, None, 5.0), ("X1-IES-3K", 2, 3.0, 3.3, None, 6.0), ("X1-IES-3.7K", 2, 3.7, 3.68, None, 7.4), ("X1-IES-5K", 3, 5.0, None, None, 10.0),
        ("X1-IES-6K", 3, 6.0, 6.6, None, 12.0), ("X1-IES-8K", 3, 8.0, 8.0, None, 16.0)]),
    "solax-x3-ies-datasheet-en": (3, "V1.8", "kW from the sheet's 'Rated power' line; the apparent-power row packs several models per cell and is left null", [
        ("X3-IES-4K", 2, 4.0, None, None, 8.0), ("X3-IES-5K", 2, 5.0, None, None, 10.0), ("X3-IES-6K", 2, 6.0, None, None, 12.0), ("X3-IES-8K", 2, 8.0, None, None, 16.0),
        ("X3-IES-10K", 2, 10.0, None, None, 20.0), ("X3-IES-12K", 2, 12.0, None, None, 24.0), ("X3-IES-15K", 2, 15.0, None, None, 30.0)]),
    "solax-x3-ies-p-datasheet-en": (3, "V2.0", "4-6 kW 2 MPPT, 8-15 kW 3 MPPT (spanned cells by position); kW from the sheet's 'Rated power' line; apparent power packed per cell, left null", [
        ("X3-IES-4K-P", 2, 4.0, None, None, 8.0), ("X3-IES-5K-P", 2, 5.0, None, None, 10.0), ("X3-IES-6K-P", 2, 6.0, None, None, 12.0), ("X3-IES-8K-P", 3, 8.0, None, None, 16.0),
        ("X3-IES-10K-P", 3, 10.0, None, None, 20.0), ("X3-IES-12K-P", 3, 12.0, None, None, 24.0), ("X3-IES-15K-P", 3, 15.0, None, None, 30.0)]),
    "solax-x3-neo-lv-datasheet-en": (3, "", "", [
        ("X3-NEO-5K-LV", 2, 5.0, 5.5, None, 10.0), ("X3-NEO-8K-LV", 2, 8.0, 8.8, None, 16.0), ("X3-NEO-10K-LV", 2, 10.0, 11.0, None, 20.0), ("X3-NEO-12K-LV", 2, 12.0, 13.2, None, 24.0),
        ("X3-NEO-15K-LV", 2, 15.0, 16.5, None, 30.0), ("X3-NEO-20K-LV", 2, 20.0, 22.0, None, 40.0)]),
    "solax-x1-vast-datasheet-en": (1, "V1.6", "5-6 kW 3 MPPT, 8-10 kW 4 MPPT (spanned cells by position)", [
        ("X1-VAST-5K", 3, 4.999, 4.999, None, 10.0), ("X1-VAST-6K", 3, 6.0, 6.0, None, 12.0), ("X1-VAST-8K", 4, 8.0, 8.0, None, 16.0), ("X1-VAST-10K", 4, 9.999, 9.999, None, 20.0)]),
    "solax-x3-mic-g2-datasheet-en-au-cec": (3, "V3.1", "the only English sheet is the AU/CEC edition (4999/9999/14999 W ratings); the lists also write X3-MIC 10.0-T-D G2, X3-MIC-10KW-G2", [
        ("X3-MIC-3K-G2", 2, 3.0, 3.3, None, 6.0, r"^X3-MIC-?3(K|KW|\.0-T-D)-?G2$"), ("X3-MIC-4K-G2", 2, 4.0, 4.4, None, 8.0, r"^X3-MIC-?4(K|KW|\.0-T-D)-?G2$"),
        ("X3-MIC-5K-G2", 2, 4.999, 4.999, None, 10.0, r"^X3-MIC-?5(K|KW|\.0-T-D)-?G2$"), ("X3-MIC-6K-G2", 2, 6.0, 6.6, None, 12.0, r"^X3-MIC-?6(K|KW|\.0-T-D)-?G2$"),
        ("X3-MIC-8K-G2", 2, 8.0, 8.8, None, 16.0, r"^X3-MIC-?8(K|KW|\.0-T-D)-?G2$"), ("X3-MIC-10K-G2", 2, 9.999, 9.999, None, 20.0, r"^X3-MIC-?10(K|KW|\.0-T-D)-?G2$"),
        ("X3-MIC-12K-G2", 2, 12.0, 13.2, None, 24.0, r"^X3-MIC-?12(K|KW|\.0-T-D)-?G2$"), ("X3-MIC-15K-G2", 2, 14.999, 14.999, None, 30.0, r"^X3-MIC-?15(K|KW|\.0-T-D)-?G2$")]),
    "solax-x3-pro-g2-datasheet-en-au": (3, "V2.8", "the only English sheet is the AU edition; 8-17 kW 2 MPPT, 20-30 kW 3 MPPT (spanned cells by position); the lists also write 'X3 PRO G2 10K', X3-PRO-10KW-G2", [
        ("X3-PRO-8K-G2", 2, 8.0, 8.8, None, 12.0, r"^X3-PRO-8KW?-G2$|^X3PROG28K$"), ("X3-PRO-10K-G2", 2, 10.0, 11.0, None, 15.0, r"^X3-PRO-10KW?-G2$|^X3PROG210K$"),
        ("X3-PRO-12K-G2", 2, 12.0, 13.2, None, 18.0, r"^X3-PRO-12KW?-G2$|^X3PROG212K$"), ("X3-PRO-15K-G2", 2, 15.0, 16.5, None, 22.5, r"^X3-PRO-15KW?-G2$|^X3PROG215K$"),
        ("X3-PRO-17K-G2", 2, 17.0, 18.7, None, 25.5, r"^X3-PRO-17KW?-G2$|^X3PROG217K$"), ("X3-PRO-20K-G2", 3, 20.0, 22.0, None, 30.0, r"^X3-PRO-20KW?-G2$|^X3PROG220K$"),
        ("X3-PRO-25K-G2", 3, 25.0, 27.5, None, 37.5, r"^X3-PRO-25KW?-G2$|^X3PROG225K$"), ("X3-PRO-30K-G2", 3, 30.0, 30.0, None, 45.0, r"^X3-PRO-30KW?-G2$|^X3PROG230K$")]),
    "solax-x3-mega-g2-datasheet-en": (3, "", "rated power given as kVA (40/50/60) and max apparent power; the lists also write 'X3 MEGA 40K-G2 (...)'", [
        ("X3-MGA-40K-G2", 4, None, 44.0, None, 60.0, r"^X3-MGA-40K-G2$|^X3MEGA40K-G2\("), ("X3-MGA-50K-G2", 5, None, 55.0, None, 75.0, r"^X3-MGA-50K-G2$|^X3MEGA50K-G2\("),
        ("X3-MGA-60K-G2", 6, None, 66.0, None, 90.0, r"^X3-MGA-60K-G2$|^X3MEGA60K-G2\(")]),
    "solax-x3-forth-datasheet-en": (3, "", "rated power given as kVA and max apparent power; 75-80 kW 9 MPPT, 100-125 kW 12 MPPT (spanned cells by position)", [
        ("X3-FTH-75K", 9, None, 75.0, None, 120.0), ("X3-FTH-80K", 9, None, 88.0, None, 120.0), ("X3-FTH-100K", 12, None, 110.0, None, 150.0), ("X3-FTH-110K", 12, None, 121.0, None, 165.0),
        ("X3-FTH-120K", 12, None, 132.0, None, 180.0), ("X3-FTH-125K", 12, None, 132.0, None, 188.0)]),
    "solax-x3-forth-plus-datasheet-en": (3, "", "rated power given as kVA and max apparent power", [
        ("X3-FTH-120K-P", 6, None, 132.0, None, 180.0), ("X3-FTH-125KT-P", 6, None, 137.5, None, 187.5), ("X3-FTH-125K-P", 6, None, 137.5, None, 187.5), ("X3-FTH-136K-P", 6, None, 150.0, None, 204.0),
        ("X3-FTH-150K-P", 6, None, 165.0, None, 225.0)]),
    "solax-x3-grand-hv-datasheet-en": (3, "V2.0", "800 V AC unit; rated power given as kVA and max apparent power", [
        ("X3-GRD-300K-HV", 6, None, 300.0, None, 450.0), ("X3-GRD-320K-HV", 6, None, 320.0, None, 480.0), ("X3-GRD-333K-HV", 6, None, 333.0, None, 499.5), ("X3-GRD-350K-HV", 6, None, 352.0, None, 525.0)]),
    "solax-x3-aelio-36k-datasheet-en": (3, "V1.1", "36K/37.5K are 208/220 V units, 60K the 400 V one", [
        ("X3-AELIO-36K", 6, 36.0, 36.0, None, 72.0), ("X3-AELIO-37.5K", 6, 37.5, 37.5, None, 75.0), ("X3-AELIO-60K", 6, 60.0, 66.0, None, 120.0)]),
    "solax-x1-boost-g4-datasheet-en-au": (1, "V1.7", "the only English sheet is the AU edition", [
        ("X1-BOOST-2.5K-G4", 2, 2.5, 2.75, None, 6.0), ("X1-BOOST-3K-G4", 2, 3.0, 3.3, None, 6.0), ("X1-BOOST-3.3K-G4", 2, 3.3, 3.63, None, 6.6), ("X1-BOOST-3.6K-G4", 2, 3.68, 4.048, None, 7.2),
        ("X1-BOOST-4K-G4", 2, 4.0, 4.0, None, 8.0), ("X1-BOOST-4.2K-G4", 2, 4.2, 4.62, None, 8.0), ("X1-BOOST-5K-G4", 2, 5.0, 5.0, None, 10.0), ("X1-BOOST-6K-G4", 2, 6.0, 6.0, None, 12.0)]),
    "x1-mini-g4-datasheet-for-au-en": (1, "V1.7", "the only English sheet is the AU edition", [
        ("X1-MINI-0.6K-G4", 1, 0.6, 0.6, None, 1.2), ("X1-MINI-0.7K-G4", 1, 0.7, 0.77, None, 1.4), ("X1-MINI-1.1K-G4", 1, 1.1, 1.21, None, 2.2), ("X1-MINI-1.5K-G4", 1, 1.5, 1.65, None, 3.0),
        ("X1-MINI-2.0K-G4", 1, 2.0, 2.2, None, 4.0), ("X1-MINI-2.5K-G4", 1, 2.5, 2.75, None, 5.0), ("X1-MINI-3.0K-G4", 1, 3.0, 3.3, None, 6.0), ("X1-MINI-3.3K-G4", 1, 3.3, 3.3, None, 6.6)]),
    "x1-boost-g3-datasheet-en": (1, "V3.3", "the sheet heads each column with a D(L) and an N(L) code; the lists also write X1-BOOST-3.0-T-D(L), 'X1 BOOST X1-3.0-T', 'X1 Boost 3.0 T'", [
        ("X1-3.0-T-D(L)", 2, 3.0, 3.3, 14.3, None, r"^(X1BOOST)?X1-3\.0-T(-[DN]\(L\))?$|^X1-BOOST-3\.0-T-[DN]\(L\)$|^X1BOOST3\.0T$"),
        ("X1-3.3-T-D(L)", 2, 3.3, 3.63, 15.8, None, r"^(X1BOOST)?X1-3\.3-T(-[DN]\(L\))?$|^X1-BOOST-3\.3-T-[DN]\(L\)$|^X1BOOST3\.3T$"),
        ("X1-3.6-T-D(L)", 2, 3.68, 4.048, 17.6, None, r"^(X1BOOST)?X1-3\.6-T(-[DN]\(L\))?$|^X1-BOOST-3\.6-T-[DN]\(L\)$|^X1BOOST3\.6T$"),
        ("X1-4.2-T-D(L)", 2, 4.2, 4.62, 20.1, None, r"^(X1BOOST)?X1-4\.2-T(-[DN]\(L\))?$|^X1-BOOST-4\.2-T-[DN]\(L\)$|^X1BOOST4\.2T$"),
        ("X1-4.6-T-D(L)", 2, 4.6, 5.06, 22.0, None, r"^(X1BOOST)?X1-4\.6K?-T(-[DN]\(L\))?$|^X1-BOOST-4\.6-T-[DN]\(L\)$|^X1BOOST4\.6T$"),
        ("X1-5.0-T-D(L)", 2, 5.0, 5.5, 23.9, None, r"^(X1BOOST)?X1-5\.0K?-T(-[DN]\(L\))?$|^X1-BOOST-5\.0-T-[DN]\(L\)$|^X1BOOST5\.0T$"),
        ("X1-5.5K-T-D(L)", 2, 5.5, 6.05, 26.3, None, r"^(X1BOOST)?X1-5\.5K-T(-[DN]\(L\))?$"),
        ("X1-6.0K-T-D(L)", 2, 6.0, 6.6, 28.7, None, r"^(X1BOOST)?X1-6(\.0)?K-T(-[DN]\(L\))?$")]),
    "solax-x1-micro-2-in-1-datasheet-en": (1, "", "microinverter: power in VA, 'Max. continuous output current'", [
        ("X1-Micro 750", 2, None, 0.75, 3.26, None), ("X1-Micro 800", 2, None, 0.8, 3.48, None), ("X1-Micro 900", 2, None, 0.9, 3.92, None), ("X1-Micro 1000", 2, None, 1.0, 4.35, None),
        ("X1-Micro 1200", 2, None, 1.2, 5.22, None)]),
    "solax-x1-micro-4-in-1-datasheet-en": (1, "", "microinverter: power in VA, 'Max. continuous output current'", [
        ("X1-Micro 1300", 4, None, 1.3, 5.66, None), ("X1-Micro 1500", 4, None, 1.5, 6.53, None), ("X1-Micro 1600", 4, None, 1.6, 6.96, None), ("X1-Micro 1800", 4, None, 1.8, 7.83, None),
        ("X1-Micro 2000", 4, None, 2.0, 8.70, None), ("X1-Micro 2200", 4, None, 2.2, 9.57, None), ("X1-Micro 2400", 4, None, 2.4, 10.43, None)]),
    "solax-x1-smart-g2-datasheet-en": (1, "V1.2", "", [
        ("X1-SMT-5K-G2", 3, 4.999, 4.999, None, 10.0), ("X1-SMT-6K-G2", 3, 6.0, 6.6, None, 12.0), ("X1-SMT-7K-G2", 3, 7.0, 7.7, None, 14.0), ("X1-SMT-8K-G2", 3, 8.0, 8.8, None, 16.0),
        ("X1-SMT-9K-G2", 3, 9.0, 9.9, None, 18.0), ("X1-SMT-10K-G2", 3, 9.999, 9.999, None, 20.0)]),
}


def solax():
    hand_brand("solax", "SolaX", "https://www.solaxpower.com/", "solax", SOLAX)


# Hoymiles: www.hoymiles.com download centre (ysecm_api dr_getdownloadtype/series/products, then list_data.html per product;
# each /downloads/<slug>.html meta-refreshes to w3oss.hoymiles.com). HMS-300..500-1T, HYS-LV-EUG1, HYT and HAT files answer 403.
HOYMILES = {
    "HIT-5-20L-G3-G3S_Global_EN_REV1.8": (3, "REV1.8", "one column per power, headed with the G3 and the G3S code; MPPT per column from the 'MPPT number/Max. input strings' row", [
        ("HIT-5L-G3", 2, 5.0, 5.5, 8.3, 10.0), ("HIT-6L-G3", 2, 6.0, 6.6, 10.0, 12.0), ("HIT-8L-G3", 3, 8.0, 8.8, 13.3, 16.0), ("HIT-10L-G3", 3, 10.0, 11.0, 16.7, 20.0),
        ("HIT-12L-G3", 4, 12.0, 13.2, 20.0, 24.0), ("HIT-15L-G3", 4, 15.0, 16.5, 25.0, 30.0), ("HIT-17L-G3", 4, 17.0, 18.7, 28.3, 34.0), ("HIT-20L-G3", 4, 20.0, 22.0, 33.3, 40.0),
        ("HIT-5L-G3S", 2, 5.0, 5.5, 8.3, 10.0), ("HIT-6L-G3S", 2, 6.0, 6.6, 10.0, 12.0), ("HIT-8L-G3S", 3, 8.0, 8.8, 13.3, 16.0), ("HIT-10L-G3S", 3, 10.0, 11.0, 16.7, 20.0),
        ("HIT-12L-G3S", 4, 12.0, 13.2, 20.0, 24.0), ("HIT-15L-G3S", 4, 15.0, 16.5, 25.0, 30.0), ("HIT-17L-G3S", 4, 17.0, 18.7, 28.3, 34.0), ("HIT-20L-G3S", 4, 20.0, 22.0, 33.3, 40.0)]),
    "HIS-3-6L-G3-G3S_Global_EN_REV1.9": (1, "REV1.9", "one column per power, headed with the G3 and the G3S code; 8L exists as G3S only", [
        ("HIS-3L-G3", 2, 3.0, 3.3, 15.0, 6.0), ("HIS-3.6L-G3", 2, 3.68, 3.68, 16.0, 7.2), ("HIS-4.6L-G3", 2, 4.6, 4.6, 20.0, 9.2), ("HIS-5L-G3", 2, 5.0, 5.5, 25.0, 10.0), ("HIS-6L-G3", 2, 6.0, 6.6, 30.0, 12.0),
        ("HIS-3L-G3S", 2, 3.0, 3.3, 15.0, 6.0), ("HIS-3.6L-G3S", 2, 3.68, 3.68, 16.0, 7.2), ("HIS-4.6L-G3S", 2, 4.6, 4.6, 20.0, 9.2), ("HIS-5L-G3S", 2, 5.0, 5.5, 25.0, 10.0), ("HIS-6L-G3S", 2, 6.0, 6.6, 30.0, 12.0),
        ("HIS-8L-G3S", 2, 8.0, 8.0, 36.4, 16.0)]),
    "HYS-LV-EUG2_EN_V1.4": (1, "REV1.4", "", [
        ("HYS-8.0LV-EUG2", 2, 8.0, 8.8, 38.3, 10.4), ("HYS-10.0LV-EUG2", 2, 10.0, 11.0, 47.8, 13.0), ("HYS-12.0LV-EUG2", 2, 12.0, 13.2, 57.4, 15.6)]),
    "HAS-LV-EUG1_EN_V1.5": (1, "REV1.5", "'AC-coupled Inverter': no PV input, hence mppt 0", [
        ("HAS-3.0LV-EUG1", 0, 3.0, 3.0, 13.0, None), ("HAS-3.6LV-EUG1", 0, 3.68, 3.68, 16.0, None), ("HAS-4.6LV-EUG1", 0, 4.6, 4.6, 20.0, None), ("HAS-5.0LV-EUG1", 0, 5.0, 5.0, 21.7, None)]),
    "HMS-600-1000-2T_EU_EN_V202408": (1, "V202408", "microinverter: rated power in VA, current only as rated (not max)", [
        ("HMS-600-2T", 2, None, 0.6, None, None), ("HMS-700-2T", 2, None, 0.7, None, None), ("HMS-800-2T", 2, None, 0.8, None, None), ("HMS-900-2T", 2, None, 0.9, None, None), ("HMS-1000-2T", 2, None, 1.0, None, None)]),
    "HMS-1600-2000-4T_EU_EN_V202506": (1, "V202506", "microinverter: rated power in VA, current only as rated (not max)", [
        ("HMS-1600-4T", 4, None, 1.6, None, None), ("HMS-1800-4T", 4, None, 1.8, None, None), ("HMS-2000-4T", 4, None, 2.0, None, None)]),
    "HMT-1600-2000_EMEA_EN_V202308": (3, "V202308", "three-phase microinverter: rated power in VA, current only as rated (not max); the sheet states 2 MPPTs", [
        ("HMT-1600-4T", 2, None, 1.6, None, None), ("HMT-1800-4T", 2, None, 1.8, None, None), ("HMT-2000-4T", 2, None, 2.0, None, None)]),
}


def hoymiles():
    hand_brand("hoymiles", "Hoymiles", "https://www.hoymiles.com/", "hoymiles", HOYMILES)


# INVT: www.invt-solar.com/downloads.html (static; brochure PDFs under /userfiles/files/download/Brochure/, folders dated
# 20240918 for XG and 20241205 for XD). The sheets give 'Rated Output Power' and 'Max. Output Power (kVA)' per column; the lists
# also write the codes with an 'iMars ' prefix or without the 'XG' letters.
INVT_NOTE = "spanned cells read by x-position; no version on the sheet, the download folder is dated 2024-09-18"


def invt_m(code):  # XG30KTR: the lists write XG30KTR, 30KTR, iMars XG30KTR
    return rf"^(IMARS)?(XG)?{re.escape(code[2:])}$"


INVT = {
    "INVT_XG3-15KTR-S_Three_Phase_On-Grid_Solar_Inverter_EN": (3, "", INVT_NOTE, [
        ("XG3KTR-S", 2, 3.0, 3.3, 4.8, 4.8), ("XG4KTR-S", 2, 4.0, 4.4, 6.4, 6.4), ("XG5KTR-S", 2, 5.0, 5.5, 8.0, 8.0), ("XG6KTR-S", 2, 6.0, 6.6, 9.6, 9.6),
        ("XG8KTR-S", 2, 8.0, 8.8, 12.8, 12.8), ("XG9KTR-S", 2, 9.0, 9.9, 14.4, 14.4), ("XG10KTR-S", 2, 10.0, 11.0, 15.9, 16.0), ("XG11KTR-S", 2, 11.0, 12.1, 17.5, 17.6),
        ("XG12KTR-S", 2, 12.0, 13.2, 19.1, 19.2), ("XG15KTR1-S", 2, 15.0, 16.5, 23.9, 24.0)]),
    "INVT_XG17-25KTR_Three_Phase_On-Grid_Solar_Inverter_EN": (3, "", INVT_NOTE, [
        ("XG17KTR", 2, 17.0, 18.8, 27.2, 27.2, invt_m("XG17KTR")), ("XG20KTR", 2, 20.0, 22.2, 32.1, 32.0, invt_m("XG20KTR")), ("XG22KTR", 2, 22.0, 24.4, 35.3, 35.2, invt_m("XG22KTR")),
        ("XG25KTR", 2, 25.0, 27.5, 39.8, 40.0, invt_m("XG25KTR"))]),
    "INVT_XG30-40KTR_Three_Phase_On-Grid_Solar_Inverter_EN": (3, "", "30/33 kW 3 MPPT, 36/40 kW 4 MPPT; " + INVT_NOTE, [
        ("XG30KTR", 3, 30.0, 33.3, 48.3, 48.0, invt_m("XG30KTR")), ("XG33KTR", 3, 33.0, 36.6, 53.0, 52.8, invt_m("XG33KTR")), ("XG36KTR", 4, 36.0, 39.6, 57.8, 57.6, invt_m("XG36KTR")),
        ("XG40KTR", 4, 40.0, 44.0, 64.3, 64.0, invt_m("XG40KTR"))]),
    "INVT_XG50-70KTR_Three_Phase_On-Grid_Solar_Inverter_EN": (3, "", "the KTRL models are the 277/480 V variants; " + INVT_NOTE, [
        ("XG50KTR", 4, 50.0, 55.0, 79.7, 80.0, invt_m("XG50KTR")), ("XG50KTRL", 4, 50.0, 55.0, 66.2, 80.0, invt_m("XG50KTRL")), ("XG60KTR", 4, 60.0, 66.0, 95.6, 96.0, invt_m("XG60KTR")),
        ("XG60KTRL", 4, 60.0, 66.0, 79.4, 96.0, invt_m("XG60KTRL")), ("XG66KTRL", 4, 66.0, 72.6, 87.4, 105.6, invt_m("XG66KTRL")), ("XG70KTRL", 4, 70.0, 77.0, 92.6, 112.0, invt_m("XG70KTRL"))]),
    "INVT_XG100-136KTR_Three_Phase_On-Grid_Solar_Inverter_EN": (3, "", "the LF/XF models are the 480 V / 540 V variants; " + INVT_NOTE, [
        ("XG100KTR-F", 9, 100.0, 110.0, 158.8, 150.0, invt_m("XG100KTR-F")), ("XG110KTR-F", 10, 110.0, 121.0, 174.6, 150.0, invt_m("XG110KTR-F")),
        ("XG136KTR-LF", 12, 136.0, 150.0, 174.6, 160.0, invt_m("XG136KTR-LF")), ("XG136KTR-XF", 12, 136.0, 150.0, 160.4, 160.0, invt_m("XG136KTR-XF"))]),
    "INVT_XG3-10KTL_Single_Phase_On-Grid_Solar_Inverter_EN": (1, "", INVT_NOTE, [
        ("XG3KTL-2M", 2, 3.0, 3.3, 15.0, 4.5), ("XG3.68KTL", 2, 3.68, 3.68, 16.0, 5.52), ("XG4KTL", 2, 4.0, 4.4, 20.0, 6.0), ("XG4.2KTL", 2, 4.2, 4.62, 21.0, 6.3),
        ("XG4.6KTL", 2, 4.6, 5.0, 23.0, 6.9), ("XG5KTL", 2, 5.0, 5.5, 25.0, 7.5), ("XG6KTL", 2, 6.0, 6.6, 30.0, 9.0), ("XG7KTL", 2, 7.0, 7.7, 35.0, 10.5),
        ("XG8KTL", 2, 8.0, 8.8, 40.0, 12.0), ("XG10KTL", 2, 10.0, 10.0, 45.5, 15.0), ("XG7KTL1", 2, 7.0, 7.7, 35.0, 10.5), ("XG8KTL1", 2, 8.0, 8.8, 40.0, 12.0),
        ("XG10KTL1", 2, 10.0, 10.0, 45.5, 15.0)]),
    "INVT_XD3-6KTL_Single_Phase_Hybrid_Inverter_EN": (1, "", "rated power given in kVA only (3/3.68/4/4.6/5/6 kVA), kept as null kW; download folder dated 2024-12-05", [
        ("XD3KTL", 2, None, 3.3, 15.0, 4.5), ("XD3K6TL", 2, None, 3.68, 16.0, 5.4), ("XD4KTL", 2, None, 4.4, 20.0, 6.0), ("XD4K6TL", 2, None, 4.6, 20.9, 6.9),
        ("XD5KTL", 2, None, 5.5, 22.7, 7.5), ("XD6KTL", 2, None, 6.0, 27.3, 9.0)]),
    "INVT_XD7-10KTL_Single_Phase_Hybrid_Inverter_EN": (1, "", "download folder dated 2024-12-05", [
        ("XD7KTL", 2, 7.0, None, 35.0, 10.5), ("XD8KTL", 2, 8.0, None, 40.0, 12.0), ("XD10KTL", 2, 10.0, None, 50.0, 15.0)]),
    "INVT_XD5-12KTR_Three_Phase_Hybrid_Inverter_EN": (3, "", "rated power given in kVA only, kept as null kW; download folder dated 2024-12-05", [
        ("XD5KTR", 2, None, 5.5, 7.2, 8.0), ("XD6KTR", 2, None, 6.6, 8.7, 9.6), ("XD8KTR", 2, None, 8.8, 11.6, 12.8), ("XD10KTR", 2, None, 11.0, 14.5, 16.0), ("XD12KTR", 2, None, 13.2, 17.4, 19.2)]),
    "INVT_XD30-60KTR_Three_Phase_Hybrid_Inverter_EN": (3, "", "download folder dated 2024-12-05", [
        ("XD30KTR", 4, 30.0, 33.0, 50.0, 48.0), ("XD40KTR", 4, 40.0, 44.0, 66.7, 64.0), ("XD50KTR", 4, 50.0, 55.0, 83.4, 80.0), ("XD60KTR", 4, 60.0, 66.0, 100.0, 96.0)]),
}


def invt():
    hand_brand("invt", "INVT", "https://www.invt-solar.com/", "invt", INVT)


# Afore: www.aforenergy.com/download/ (WordPress document table, static). The single sheets are the MTH+ and SL+ revisions; the
# register codes are those of the 2026-10-10 product catalogue, so the rows come from the catalogue's per-series tables.
AFORE_CAT = "EN-Afore-catalogue-2026.10.10"
AFORE_NOTE = "catalogue dated 2026.10.10 in its file name; one table per series, spanned cells read by x-position"
AFORE = {
    AFORE_CAT: (3, "2026.10.10", AFORE_NOTE, [
        # three-phase hybrid AF-MTH 3-15 kW (Nominal AC Output Power kW; kVA = output side of 'Max. AC Input/Output Power'; Max. PV Access Power)
        ("AF3K-MTH", 2, 3.0, 3.3, 5.3, 6.0, r"^AF3K?-MTH$"), ("AF4K-MTH", 2, 4.0, 4.4, 7.0, 8.0, r"^AF4K?-MTH$"), ("AF5K-MTH", 2, 5.0, 5.5, 8.5, 10.0, r"^AF5K?-MTH$"),
        ("AF6K-MTH", 2, 6.0, 6.6, 10.5, 12.0, r"^AF6K?-MTH$"), ("AF8K-MTH", 2, 8.0, 8.8, 13.5, 16.0, r"^AF8K?-MTH$"), ("AF10K-MTH", 2, 10.0, 11.0, 17.0, 20.0, r"^AF10K?-MTH$"),
        ("AF12K-MTH", 2, 12.0, 13.2, 21.5, 24.0, r"^AF12K?-MTH$"), ("AF15K-MTH", 2, 15.0, 16.5, 27.0, 30.0, r"^AF15K?-MTH$"),
        # three-phase hybrid AF-TH 3-30 kW
        ("AF3K-TH", 2, 3.0, 3.3, 5.3, 6.0), ("AF4K-TH", 2, 4.0, 4.4, 7.0, 8.0), ("AF5K-TH", 2, 5.0, 5.5, 8.5, 10.0), ("AF6K-TH", 2, 6.0, 6.6, 10.5, 12.0),
        ("AF8K-TH", 2, 8.0, 8.8, 13.5, 16.0), ("AF10K-TH", 2, 10.0, 11.0, 17.0, 20.0), ("AF12K-TH", 2, 12.0, 13.2, 21.5, 24.0), ("AF15K-TH", 2, 15.0, 16.5, 27.0, 30.0),
        ("AF17K-TH", 2, 17.0, 18.7, 30.0, 34.0), ("AF20K-TH", 2, 20.0, 22.0, 32.0, 40.0), ("AF25K-TH", 2, 25.0, 27.5, 40.0, 50.0), ("AF30K-TH", 2, 30.0, 33.0, 48.0, 51.0),
        # three-phase hybrid AF-TH 36-60 kW
        ("AF36K-TH", 4, 36.0, 39.6, 60.5, 72.0), ("AF40K-TH", 4, 40.0, 44.0, 67.0, 80.0), ("AF45K-TH", 4, 45.0, 49.5, 75.5, 90.0), ("AF50K-TH", 4, 50.0, 55.0, 83.5, 100.0),
        ("AF60K-TH", 4, 60.0, 66.0, 96.0, 100.0),
        # three-phase string BNT 3-25 kW (Nominal Output Power W, Max. Output Power VA, Max. Output Current, Max. DC Power)
        ("BNT003KTL", 2, 3.0, 3.3, 5.3, 5.1), ("BNT004KTL", 2, 4.0, 4.4, 7.0, 6.0), ("BNT005KTL", 2, 5.0, 5.5, 8.5, 7.5), ("BNT006KTL", 2, 6.0, 6.6, 10.5, 9.0),
        ("BNT008KTL", 2, 8.0, 8.8, 13.5, 12.0), ("BNT010KTL", 2, 10.0, 11.0, 17.0, 15.0), ("BNT012KTL", 2, 12.0, 13.2, 21.5, 18.0), ("BNT013KTL", 2, 13.0, 14.3, 22.0, 19.5),
        ("BNT015KTL", 2, 15.0, 16.5, 27.0, 22.5), ("BNT017KTL", 2, 17.0, 18.7, 30.0, 25.5), ("BNT020KTL", 2, 20.0, 22.0, 32.0, 30.0), ("BNT025KTL", 2, 25.0, 27.5, 40.0, 37.5),
        # BNT 30-60 kW: MPPT row '2/5 3/6 3/7 4/8' over five columns, the last cell spanning 50 and 60 kW
        ("BNT030KTL", 2, 30.0, 33.0, 48.0, 45.0), ("BNT036KTL", 3, 36.0, 39.6, 60.0, 54.0), ("BNT040KTL", 3, 40.0, 44.0, 65.0, 60.0), ("BNT050KTL", 4, 50.0, 55.0, 80.0, 75.0),
        ("BNT060KTL", 4, 60.0, 66.0, 96.0, 90.0),
        # BNT 70-110 kW
        ("BNT070KTL", 6, 70.0, 77.0, 111.0, 105.0), ("BNT075KTL", 6, 75.0, 82.5, 120.0, 112.5), ("BNT080KTL", 6, 80.0, 88.0, 127.0, 120.0), ("BNT090KTL", 6, 90.0, 99.0, 143.0, 135.0),
        ("BNT100KTL", 6, 100.0, 110.0, 158.0, 150.0), ("BNT110KTL", 6, 110.0, 110.0, 159.5, 165.0)]),
}
AFORE_1P = {  # the catalogue's single-phase hybrid tables: 'Max Continuous Power (kVA)' and 'Max Continuous Current (A)', no kW row
    AFORE_CAT: (1, "2026.10.10", AFORE_NOTE + "; single-phase hybrids give a max continuous kVA and current, no kW row; the lists also write 'Hybrid inverter AF3K-SL'", [
        ("AF1K-SL-1", 1, None, 1.0, 5.0, 2.0), ("AF1.5K-SL-1", 1, None, 1.5, 7.0, 3.0), ("AF2K-SL-1", 1, None, 2.0, 10.0, 4.0), ("AF2.5K-SL-1", 1, None, 2.5, 12.0, 5.0),
        ("AF3K-SL-1", 2, None, 3.0, 14.0, 6.0), ("AF3.6K-SL-1", 2, None, 3.6, 17.0, 7.2), ("AF3K-SL", 2, None, 3.0, 14.0, 6.0, r"^(HYBRIDINVERTER)?AF3K-SL$"),
        ("AF3.6K-SL", 2, None, 3.6, 17.0, 7.2, r"^(HYBRIDINVERTER)?AF3\.6K-SL$"),
        ("AF4K-SLP", 2, None, 4.0, 19.0, 8.0), ("AF4.6K-SLP", 2, None, 4.6, 22.0, 9.2), ("AF5K-SLP", 2, None, 5.0, 23.0, 10.0), ("AF5.5K-SLP", 2, None, 5.5, 26.0, 11.0),
        ("AF6K-SLP", 2, None, 6.0, 28.0, 12.0)]),
}


def afore():
    # one PDF, two phase groups: build the three-phase table first, then append the single-phase rows under a second source id
    urls = dict(line.split(" ", 1) for line in (CACHE / "afore/SOURCES.txt").read_text(encoding="utf-8").splitlines() if " " in line)
    sources, models = [], []
    for tbl, suffix in ((AFORE, ""), (AFORE_1P, "-1p")):
        for stem, (ph, ver, note, rows) in tbl.items():
            sid = re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-") + suffix
            sources.append({"id": sid, "url": urls.get(stem + ".pdf", ""), "file": stem + ".pdf", "version": ver, "note": note, "seen": SEEN})
            for r in rows:
                m = row(r[0], r[1], r[2], r[3], r[4], ph, r[5], sid)
                if len(r) > 6 and r[6]:
                    m["match"] = r[6]
                models.append(m)
    dump("afore", {"brand": "Afore", "maker_site": "https://www.aforenergy.com/", "rule": RULE, "sources": sources, "models": models})


# ZCS Azzurro: www.zcsazzurro.com/en/documentation (static, 343 PDFs under /uploads/documetazione/). English sheets. They give
# 'Rated AC power', 'Maximum AC power' (VA) and 'Maximum AC current (per phase)'; PV power only per MPPT, so pv_kw stays null.
# The lists write the codes with or without a space before TL ('1PH 3000-TLM-V3', '3PH 15000TL-V3' for 3PH 15KTL-V3) and some with an
# 'AZZURRO ' prefix.
def zcs_hyd(code):  # "3PH HYD 5000 ZSS" -> also "AZZURRO 3PH HYD5000 ZSS"
    return rf"^(AZZURRO)?{re.escape(re.sub(r'\s+', '', code.upper()))}$"


ZCS = {
    "Datasheet-ZCS-3PH-3.3-12KTL-V3-EN": (3, "", "", [
        ("3PH 3.3KTL-V3", 2, 3.0, 3.3, 5.0, None), ("3PH 4.4KTL-V3", 2, 4.0, 4.4, 6.7, None), ("3PH 5.5KTL-V3", 2, 5.0, 5.5, 8.3, None), ("3PH 6.6KTL-V3", 2, 6.0, 6.6, 10.0, None),
        ("3PH 8.8KTL-V3", 2, 8.0, 8.8, 13.3, None), ("3PH 11KTL-V3", 2, 10.0, 11.0, 16.7, None), ("3PH 12KTL-V3", 2, 12.0, 13.2, 20.0, None)]),
    "Datasheet-ZCS-3PH-15-24KTL-V3-EN": (3, "", "the lists also write 3PH 15000TL-V3 / 3PH 15000KTL-V3", [
        ("3PH 15KTL-V3", 2, 15.0, 16.5, 23.9, None, r"^3PH15(000)?K?TL-V3$"), ("3PH 17KTL-V3", 2, 17.0, 18.7, 27.1, None, r"^3PH17(000)?K?TL-V3$"),
        ("3PH 20KTL-V3", 2, 20.0, 22.0, 31.9, None, r"^3PH20(000)?K?TL-V3$"), ("3PH 22KTL-V3", 2, 22.0, 24.2, 35.1, None, r"^3PH22(000)?K?TL-V3$"),
        ("3PH 24KTL-V3", 2, 24.0, 26.4, 38.3, None, r"^3PH24(000)?K?TL-V3$")]),
    "Datasheet-ZCS-3PH-25-50KTL-V3-EN": (3, "", "25-36 kW 3 MPPT, 40-50 kW 4 MPPT (spanned cells read by position)", [
        ("3PH 25KTL-V3", 3, 25.0, 28.0, 42.4, None), ("3PH 30KTL-V3", 3, 30.0, 34.0, 51.5, None), ("3PH 33KTL-V3", 3, 33.0, 37.0, 56.0, None), ("3PH 36KTL-V3", 3, 36.0, 40.0, 60.6, None),
        ("3PH 40KTL-V3", 4, 40.0, 44.0, 66.7, None), ("3PH 45KTL-V3", 4, 45.0, 50.0, 75.8, None), ("3PH 50KTL-V3", 4, 50.0, 55.0, 83.3, None)]),
    "Datasheet-ZCS-3PH-60-80KTL-V3-EN": (3, "", "", [("3PH 60KTL-V3", 6, 60.0, 66.0, 100.0, None), ("3PH 80KTL-V3", 6, 80.0, 88.0, 133.3, None)]),
    "Datasheet-ZCS-3PH-100-110KTL-V4-EN": (3, "", "", [("3PH 100KTL-V4", 10, 100.0, 110.0, 160.0, None), ("3PH 110KTL-V4", 10, 110.0, 125.0, 181.0, None)]),
    "Datasheet-ZCS-3PH-20000-33000TL-V2-EN": (3, "", "", [
        ("3PH 20000TL-V2", 2, 20.0, 22.0, 32.0, None), ("3PH 25000TL-V2", 2, 25.0, 27.5, 40.0, None), ("3PH 30000TL-V2", 2, 30.0, 33.0, 48.0, None), ("3PH 33000TL-V2", 2, 33.0, 36.3, 53.0, None)]),
    "Datasheet-ZCS-3PH-50000-60000TL-V1-EN": (3, "", "", [("3PH 50000TL-V1", 3, 50.0, 50.0, 80.0, None), ("3PH 60000TL-V1", 3, 60.0, 60.0, 90.0, None)]),
    "Datasheet-ZCS-1PH-1100-3300TL-V3-EN": (1, "", "", [
        ("1PH 1100TL-V3", 1, 1.1, 1.1, 5.3, None), ("1PH 1600TL-V3", 1, 1.6, 1.6, 7.7, None), ("1PH 2200TL-V3", 1, 2.2, 2.2, 10.6, None), ("1PH 2700TL-V3", 1, 2.7, 2.7, 13.0, None),
        ("1PH 3000TL-V3", 1, 3.0, 3.0, 14.5, None), ("1PH 3300TL-V3", 1, 3.3, 3.3, 16.0, None)]),
    "Datasheet-ZCS-1PH-3000-6000TLM-V3-EN": (1, "", "the lists write 1PH 3000-TLM-V3", [
        ("1PH 3000TLM-V3", 2, 3.0, 3.3, 15.0, None, r"^1PH3000-?TLM-V3$"), ("1PH 3680TLM-V3", 2, 3.68, 3.68, 16.0, None, r"^1PH3680-?TLM-V3$"), ("1PH 4000TLM-V3", 2, 4.0, 4.4, 20.0, None, r"^1PH4000-?TLM-V3$"),
        ("1PH 4600TLM-V3", 2, 4.6, 4.6, 23.0, None, r"^1PH4600-?TLM-V3$"), ("1PH 5000TLM-V3", 2, 5.0, 5.5, 25.0, None, r"^1PH5000-?TLM-V3$"), ("1PH 6000TLM-V3", 2, 6.0, 6.6, 29.0, None, r"^1PH6000-?TLM-V3$")]),
    "Datasheet-ZCS-3PH-HYD-5000-8000-ZSS-EN": (3, "", "", [
        ("3PH HYD 5000 ZSS", 2, 5.0, 5.5, 8.0, None, zcs_hyd("3PH HYD 5000 ZSS")), ("3PH HYD 6000 ZSS", 2, 6.0, 6.6, 10.0, None, zcs_hyd("3PH HYD 6000 ZSS")),
        ("3PH HYD 8000 ZSS", 2, 8.0, 8.8, 13.0, None, zcs_hyd("3PH HYD 8000 ZSS"))]),
    "Datasheet-ZCS-3PH-HYD-10000-20000-ZSS-EN": (3, "", "", [
        ("3PH HYD 10000 ZSS", 2, 10.0, 11.0, 16.0, None, zcs_hyd("3PH HYD 10000 ZSS")), ("3PH HYD 15000 ZSS", 2, 15.0, 16.5, 24.0, None, zcs_hyd("3PH HYD 15000 ZSS")),
        ("3PH HYD 20000 ZSS", 2, 20.0, 22.0, 32.0, None, zcs_hyd("3PH HYD 20000 ZSS"))]),
    "Datasheet-ZCS-3PH-HYD-5000-12000-ZP3-EN": (3, "", "", [
        ("3PH HYD 5000 ZP3", 3, 5.0, 5.5, 8.0, None, zcs_hyd("3PH HYD 5000 ZP3")), ("3PH HYD 6000 ZP3", 3, 6.0, 6.6, 9.6, None, zcs_hyd("3PH HYD 6000 ZP3")),
        ("3PH HYD 8000 ZP3", 3, 8.0, 8.8, 12.8, None, zcs_hyd("3PH HYD 8000 ZP3")), ("3PH HYD 10000 ZP3", 3, 10.0, 11.0, 15.9, None, zcs_hyd("3PH HYD 10000 ZP3")),
        ("3PH HYD 12000 ZP3", 3, 12.0, 13.2, 19.1, None, zcs_hyd("3PH HYD 12000 ZP3"))]),
    "Datasheet-ZCS-1PH-HYD-3000-6000-ZSS-EN": (1, "", "", [
        ("1PH HYD3000 ZSS", 2, 3.0, 3.0, 13.7, None), ("1PH HYD3600 ZSS", 2, 3.68, 3.68, 16.0, None), ("1PH HYD4000 ZSS", 2, 4.0, 4.0, 18.2, None), ("1PH HYD5000 ZSS", 2, 5.0, 5.0, 22.8, None),
        ("1PH HYD6000 ZSS", 2, 6.0, 6.0, 27.3, None)]),
    "Datasheet-ZCS-1PH-HYD-3000-6000-ZSS-HP-EN": (1, "", "", [
        ("1PH HYD 3000 ZSS HP", 2, 3.0, 3.3, 15.0, None), ("1PH HYD 3600 ZSS HP", 2, 3.68, 3.68, 16.0, None), ("1PH HYD 4000 ZSS HP", 2, 4.0, 4.4, 20.0, None), ("1PH HYD 4600 ZSS HP", 2, 4.6, 4.6, 20.9, None),
        ("1PH HYD 5000 ZSS HP", 2, 5.0, 5.5, 25.0, None), ("1PH HYD 6000 ZSS HP", 2, 6.0, 6.0, 27.3, None)]),
    "Datasheet-ZCS-1PH-HYD-3000-6000-ZP1-EN": (1, "", "", [
        ("1PH HYD 3000 ZP1", 2, 3.0, 3.3, 15.0, None), ("1PH HYD 3680 ZP1", 2, 3.68, 3.68, 16.7, None), ("1PH HYD 4000 ZP1", 2, 4.0, 4.4, 20.0, None), ("1PH HYD 4600 ZP1", 2, 4.6, 4.6, 20.9, None),
        ("1PH HYD 5000 ZP1", 2, 5.0, 5.5, 25.0, None), ("1PH HYD 6000 ZP1", 2, 6.0, 6.6, 30.0, None)]),
}


def zcs():
    hand_brand("zcs", "ZCS Azzurro", "https://www.zcsazzurro.com/", "zcs", ZCS)


if __name__ == "__main__":
    deye()
    fronius()
    goodwe()
    kostal()
    sma()
    foxess()
    growatt()
    solis()
    saj()
    solax()
    hoymiles()
    invt()
    afore()
    zcs()
