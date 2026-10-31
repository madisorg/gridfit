"""Spec layer, step 2: read the per-model columns of a datasheet table.

    python -I tools/specs/table.py cache/specs/<brand>/<file>.pdf [--header REGEX]

Datasheets put one model per column and one quantity per row. pdfplumber gives every word with its
x position, so a value is assigned to the model column whose header is nearest; a value that
appears once on a row applies to every model, and a row with fewer values than models is read as
spanned cells (each value covers the columns from its own to the next value's). Output is JSON on
stdout: one object per model with the raw strings of the rows that matter (mppt, ac_w, ac_va,
ac_a, pv_w, phases). The YAML in data/specs/ is still written by hand from this output.
"""
import json
import re
import sys
from pathlib import Path

import pdfplumber

ROWS = {
    "mppt": r"(no\.?|number)\s*of\s*(independent\s+)?mpp|mpp\s*trackers?\b|mppt\s*(count|trackers?|inputs?)|anzahl.*mpp",
    "ac_w": r"(rated|nominal|nom\.?)\s*(ac\s*)?(input/)?(output\s*)?(active\s*)?power\s*\(?\s*k?w|ac\s*nominal\s*power|rated\s*power\s*\(?k?w|nominal\s*ac\s*output",
    "ac_va": r"max(imum|\.)?\s*(ac\s*)?(input/)?(output\s*)?apparent\s*power|max\.?\s*ac\s*output\s*power\s*\(?va",
    "ac_a": r"max(imum|\.)?\s*(ac\s*)?(input/)?(output\s*)?current\s*\(?a|max\.?\s*continuous\s*(ac\s*)?(output\s*)?current",
    "pv_w": r"max(imum|\.)?\s*(pv|dc)\s*(input\s*)?power|max\.?\s*recommended\s*pv",
    "phases": r"rated\s*(input/)?(output\s*)?(grid\s*)?voltage|ac\s*(grid\s*)?connection|grid\s*type|phase",
}
HEADER = r"^(SUN-|SG|SH|S[56]|X[13]-|GW|RHI|RAI|PLENTI|PIKO|STP|SB|STPS|ET|EH|ES|EM|SPF|MIN|MID|MAX|MOD|HYD|KTL|SE|FOX|H[13]-|KH|AC[13]|T[0-9]|H[0-9])"


def rows_of(page):
    words = page.extract_words(keep_blank_chars=False, x_tolerance=2, y_tolerance=3)
    lines = {}
    for w in words:
        key = round(w["top"] / 3)
        lines.setdefault(key, []).append(w)
    out = []
    for key in sorted(lines):
        ws = sorted(lines[key], key=lambda w: w["x0"])
        out.append(ws)
    return out


def assign_row(models, cols, vals, text):
    """Each value goes to the nearest model column; a value that is missing for a column is the
    spanned cell of the value to its left (the first value also covers columns left of it)."""
    assign = {}
    for v in vals:
        cx = (v["x0"] + v["x1"]) / 2
        i = min(range(len(cols)), key=lambda j: abs(cols[j] - cx))
        assign[i] = (assign.get(i, "") + " " + v["text"]).strip()
    per, cur, first = {}, None, min(assign)
    for i, m in enumerate(models):
        cur = assign.get(i, cur if i > first else assign[first])
        per[m] = cur
    per["raw"] = text
    if len(vals) < len(models):
        per["spanned"] = True
    return per


def main(pdf, header_re):
    hdr = re.compile(header_re, re.I)
    models, cols, found, pending = [], [], {}, None
    with pdfplumber.open(pdf) as doc:
        for page in doc.pages:
            for ws in rows_of(page):
                text = " ".join(w["text"] for w in ws)
                if not models:
                    cand = [w for w in ws if hdr.search(w["text"]) and len(w["text"]) >= 3]
                    if len(cand) >= 2 and len(cand) >= len(ws) - 1:
                        models = [w["text"] for w in cand]
                        cols = [(w["x0"] + w["x1"]) / 2 for w in cand]
                        continue
                    continue
                # a second header row ("-SG04LP3-EU" under "SUN-5K") completes the model names
                if len(ws) == len(models) and all(w["text"].startswith("-") for w in ws):
                    models = [m + w["text"] for m, w in zip(models, ws)]
                    continue
                label_end = min(cols) - 20
                # a label split over two lines ("No. of MPP Trackers/" / "No. of Strings ...") has its
                # values on a line of their own in between: a line made of numbers only
                if pending and all(re.search(r"^[\d.,/+x-]+$", w["text"]) for w in ws):
                    key, pending = pending, None
                    vals = ws
                    text = found[key]["raw"] + " | " + " ".join(w["text"] for w in ws)
                    found[key] = assign_row(models, cols, vals, text)
                    continue
                if pending and not re.search(r"\d", text):
                    pending = None if len(found[pending]) > 1 else pending
                for key, pat in ROWS.items():
                    if (key in found and len(found[key]) > 1) or not re.search(pat, text, re.I):
                        continue
                    vals = [w for w in ws if w["x0"] >= label_end and re.search(r"\d", w["text"])]
                    if not vals:
                        found[key] = {"raw": text}
                        pending = key
                        continue
                    if len(vals) == 1 or key == "phases":
                        found[key] = {m: " ".join(v["text"] for v in vals) for m in models}
                        found[key]["raw"] = text
                        continue
                    found[key] = assign_row(models, cols, vals, text)
    print(json.dumps({"file": Path(pdf).name, "models": models, "rows": found}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    a = sys.argv[1:]
    h = HEADER
    if "--header" in a:
        h = a[a.index("--header") + 1]
        a = [x for x in a if x not in ("--header", h)]
    main(a[0], h)
