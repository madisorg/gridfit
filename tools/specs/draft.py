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


if __name__ == "__main__":
    deye()
    fronius()
    goodwe()
    kostal()
    sma()
    foxess()
    growatt()
    solis()
