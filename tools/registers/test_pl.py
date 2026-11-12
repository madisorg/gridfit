"""Read a downloaded PTPiREE list with the parser and check that every row came out whole.

    python -I tools/registers/test_pl.py <dir holding pl__*.pdf>

The list itself is not committed (no reuse terms), so this runs on a file downloaded for a refresh or by hand
(https://ptpiree.pl/kodeksy-sieci/wykaz-certyfikatow/). It fails on a missing Lp number, a model cell that holds only
a PPM scope ("A", "A, B"), a maker cell that holds the WOS version, a row without its date, or a known row read wrong.
"""
import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
raw = pathlib.Path(sys.argv[1])
with tempfile.TemporaryDirectory() as tmp:
    out = pathlib.Path(tmp)
    subprocess.run([sys.executable, "-I", "-X", "utf8", str(HERE / "parse.py"), str(raw), str(out),
                    str(HERE.parents[1] / "data/registers/alias.json"), "2000-01-01"], check=True,
                   capture_output=True)
    meta = json.loads((out / "meta.json").read_text(encoding="utf-8"))["PL"]
    pl = {e["id"]: e for e in map(json.loads, (out / "entries.jsonl").open(encoding="utf-8")) if e["reg"] == "PL"}

fails = []
if meta["unread_lp"]:
    fails.append(f"unread Lp {meta['unread_lp'][:20]}")
if meta.get("column_bleed") is None:
    fails.append("the parser reports no column-bleed check")
elif meta["column_bleed"]:
    fails.append(f"column bleed in Lp {meta['column_bleed'][:20]}")
print(f"PL {meta['file']}: {len(pl)} rows; " + ("; ".join(fails) if fails else "every row whole"))
sys.exit(1 if fails else 0)
