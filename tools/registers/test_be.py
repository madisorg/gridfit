"""Belgium's C10/26 rows through tools/registers/parse.py, on a small invented workbook.

    python tools/registers/test_be.py

Proves the two things the Belgian parse gets wrong easily: a bare number in the model cell takes its series (else KOSTAL
"10" is five units in one device), and a generator set flagged "Backup power system" is not storage.
"""
import json
import pathlib
import subprocess
import sys
import tempfile

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[2]
#        brand, series, model, Smax, solar, storage, backup -> expected model, class
CASES = [
    ("KOSTAL", "PLENTICORE plus", "10", 10000, "X", "X", "", "PLENTICORE plus 10", "hybrid"),
    ("KOSTAL", "PLENTICORE plus G2", "10", 10000, "X", "X", "", "PLENTICORE plus 10 G2", "hybrid"),
    ("KOSTAL", "PIKO IQ", "8.5", 8500, "X", "", "", "PIKO IQ 8.5", "inverter"),
    ("KOSTAL", "PLENTICORE BI G2", "5.5/26", 5500, "", "X", "", "PLENTICORE BI 5.5/26 G2", "battery"),
    ("FRONIUS", "Fronius Primo", "3.0-1", 3000, "X", "", "", "Primo 3.0-1", "inverter"),
    ("FRONIUS", "SYMO GEN24 Plus SC", "10.0", 10000, "X", "X", "", "SYMO GEN24 10.0 Plus SC", "hybrid"),
    ("Ginlong", "Solis", "30K", 30000, "X", "", "", "Solis 30K", "inverter"),
    ("Solis", "(40-60)K", "40K", 40000, "X", "", "", "40K", "inverter"),
    ("Perceval", "GM2K2", "28513", 2200, "X", "", "", "28513", "inverter"),
    ("SMA", "Sunny Boy", "SB3.6-1AV-41", 3680, "X", "", "", "SB3.6-1AV-41", "inverter"),
    ("CAT", "G3516", "G3516H", 2000000, "", "", "X", "G3516H", "other"),
]


def workbook(path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "C10-26 power-generating units"
    for _ in range(10):
        ws.append([None] * 31)
    ws.cell(7, 2, "2026-10-30")
    for i, (brand, series, model, smax, sol, sto, bak, *_x) in enumerate(CASES):
        row = [None] * 31
        row[1], row[2], row[3], row[4], row[9] = f"GLV999-01-{i:04d}", brand, series, model, smax
        row[21], row[24], row[25] = sol or None, sto or None, bak or None
        ws.append(row)
    ex = wb.create_sheet("C10-26 expired homologations")
    for _ in range(10):
        ex.append([None] * 31)
    wb.save(path)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        raw, out = pathlib.Path(tmp, "raw"), pathlib.Path(tmp, "out")
        raw.mkdir()
        workbook(raw / "be_test.xlsx")
        subprocess.run([sys.executable, "-I", "-X", "utf8", str(ROOT / "tools/registers/parse.py"), str(raw), str(out),
                        str(ROOT / "data/registers/alias.json"), "2026-11-12"], check=True, capture_output=True)
        got = [json.loads(l) for l in (out / "entries.jsonl").open(encoding="utf-8") if '"reg": "BE"' in l]
    fails = []
    if len(got) != len(CASES):
        fails.append(f"{len(got)} BE rows, expected {len(CASES)}")
    for e, c in zip(got, CASES):
        if (e["model_raw"], e["cls"]) != (c[7], c[8]):
            fails.append(f"{c[0]} {c[1]!r} {c[2]!r}: got {e['model_raw']!r} {e['cls']}, expected {c[7]!r} {c[8]}")
    for f in fails:
        print("FAIL", f)
    print(f"test_be: {len(CASES) - len(fails)} of {len(CASES)} ok")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
