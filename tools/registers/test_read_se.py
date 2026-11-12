"""Test of the Rikta Rätt reader (tools/registers/parse.py read_se) on a five-row file in both code pages it has come in.

    python tools/registers/test_read_se.py

Rikta Rätt's CSV of 2026-10-23 was cp1252, the one of 2026-11-09 cp850: read as cp1252 the second turns "får" into
"f†r" and changes 11 model codes. Each fixture is written to a fresh temporary directory and parsed in an isolated
interpreter, the way gridfit/registers.py runs the parser.
"""
import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
HEAD = "Löp-nummer;Fabrikat;Typbeteckning/ Modellnummer;Programvara (versionsnummer);Effekt (kW);Antal faser;Energikälla;Granskad (Datum);Kommentarer;"
ROWS = [
    "437;ABB;UNO-DM-3.0-TL-PLUS-Q;3.0;3;1;Sol;2021-07-14;Licens från Fimer Group;",
    "1001;AEG;AS-IR01-3600;V1;3,6;1;Sol;2022-01-10;Samma som GoodWe GW3600D-NS - Får enbart anslutas i trefaskoppling;",
    "1002;Växel AB;Kraftö 5K;1.0;5;3;Sol/Batteri;2023-03-01;Hybrid;",
    "3377;Solplanet;ASW150K-LT;V1;150;3;Aiswei B.V.;2026-06-01;;",
    "3395;Growatt ;WIT 50K-HU;TO1.0;50;3;Sol/Batteri;25/09/2026;Hybrid;",
]


def parse(enc):
    with tempfile.TemporaryDirectory() as tmp:
        raw, out = pathlib.Path(tmp, "raw"), pathlib.Path(tmp, "out")
        raw.mkdir()
        (raw / "se__rikta-ratt-26-11-09.csv").write_bytes(("\r\n".join([HEAD] + ROWS) + "\r\n").encode(enc))
        subprocess.run([sys.executable, "-I", "-X", "utf8", str(ROOT / "tools/registers/parse.py"), str(raw), str(out),
                        str(ROOT / "data/registers/alias.json"), "2026-11-12"], check=True, capture_output=True)
        rows = [json.loads(line) for line in (out / "entries.jsonl").read_text(encoding="utf-8").splitlines()]
        return [r for r in rows if r["reg"] == "SE"], (out / "errors.txt").read_text(encoding="utf-8")


def main():
    fails = 0
    for enc in ("cp1252", "cp850", "utf-8-sig"):
        rows, errs = parse(enc)
        by = {r["id"]: r for r in rows}
        checks = [
            (len(rows) == 5, f"5 rows, got {len(rows)}"),
            (by["437"]["extra"]["comment"] == "Licens från Fimer Group", f"comment {by['437']['extra']['comment']!r}"),
            (by["1002"]["model_raw"] == "Kraftö 5K", f"model {by['1002']['model_raw']!r}"),
            (by["1001"]["status"] == "restricted" and "trefaskoppling" in by["1001"]["word"], "three-phase only → restricted"),
            (by["437"]["status"] == "listed" and by["437"]["word"] == "listed", "plain row stays listed"),
            (by["3377"]["cls"] == "inverter" and "3377" in errs, "misplaced energy source → PV, reported"),
            (by["3395"]["date"] == "2026-09-25", f"date {by['3395']['date']!r}"),
            (by["1002"]["cls"] == "hybrid", "Sol/Batteri → hybrid"),
            ("header not recognised" not in errs, "header recognised"),
        ]
        for ok, what in checks:
            if not ok:
                fails += 1
                print(f"FAIL [{enc}] {what}")
    print("read_se: ok" if not fails else f"read_se: {fails} failures")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
