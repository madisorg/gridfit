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


if __name__ == "__main__":
    deye()
    fronius()
    goodwe()
