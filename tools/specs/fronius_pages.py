"""Spec layer: read the spec table of Fronius help-center product pages (HTML, one model per page).

    python -I tools/specs/fronius_pages.py cache/specs/fronius/pages > cache/specs/fronius/pages.json

Each page carries the datasheet's rows as <th>label</th><td>value</td> pairs; the rows that matter
are the MPP tracker count, max/nominal AC output power, max AC current and the grid connection
(1~ / 3~). The product name is the page's <h1>. Output: JSON list, one object per page.
"""
import html
import json
import re
import sys
from pathlib import Path

WANT = {
    "mppt": r"^number of mpp trackers",
    "pac_max": r"^max\.? output power \(pac ?max\)|^max\.? output power",
    "pac_nom": r"^ac nominal output|^nominal output power|^rated output power",
    "iac_max": r"^max\.? (ac )?output current",
    "grid": r"^grid connection \(u ?ac",  # the PV Point row is a bare "Grid connection"
    "pdc_max": r"^max\.? pv generator power",
}


def clean(x):
    return html.unescape(re.sub(r"<[^>]+>", " ", x)).replace("\xa0", " ").strip()


def main(d):
    out = []
    for f in sorted(Path(d).glob("*.html")):
        s = f.read_text(encoding="utf-8", errors="replace")
        if "Number of MPP trackers" not in s:
            continue
        m = re.search(r"<title>(.*?)</title>", s, re.S)
        name = clean(m.group(1)).split("|")[0].strip() if m else f.stem
        rows = {}
        body = s.split("Technical Data", 1)[-1].split("Footnotes", 1)[0]
        for k, v in re.findall(r"<th[^>]*>(.*?)</th>\s*<td[^>]*>(.*?)</td>", body, re.S):
            k, v = clean(k), clean(v)
            for key, pat in WANT.items():
                if key not in rows and re.search(pat, k, re.I):
                    rows[key] = v
        out.append({"page": f.name, "name": name, **rows})
    json.dump(out, sys.stdout, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main(sys.argv[1])
