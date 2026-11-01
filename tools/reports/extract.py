"""Pre-certification pilot, the automation test: can one parser read the settable ranges out of the makers' EN 50549-1
documents, and how many of the evidence layer's EN 50549 documents carry such a table at all?

    python -I -X utf8 tools/reports/extract.py score cache/reports            # parser vs the hand-read data/test-reports
    python -I -X utf8 tools/reports/extract.py corpus DIR [DIR ...] [--registers web/.data/registers.json]
                                                                             # which evidence documents carry a table

Reads only the text files tools/specs/extract.py wrote next to each PDF (<file>.txt or <file>.pdf.pages.txt) — the
PDFs are downloaded, untrusted files, hence -I. Writes nothing. The parser is deliberately one generic pass (a label
family, then the first range with the right unit after it, stages in order of appearance): what it misses is the
measure of how uneven the forms are.
"""
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

import yaml

ROOT = Path(__file__).resolve().parents[2]
NUM = r"(\d+(?:[.,]\d+)?)"
UNIT = {"un": r"(?:U\s*n|Un|U\s*c)", "s": r"s(?![a-z])", "hz": r"Hz(?!/)", "hzs": r"Hz\s*/\s*s(?:ec)?", "pct": r"%"}
# a label family: (regex, unit kind, the (function, parameter) slots it fills in order of appearance)
FAMILIES = [
    (r"under-?\s*voltage|too low voltage", "un", [("uv1", "threshold_un"), ("uv2", "threshold_un")]),
    (r"under-?\s*voltage|too low voltage", "s", [("uv1", "time_s"), ("uv2", "time_s")]),
    (r"(?<!10 min )over-?\s*voltage(?! (ride|category|10|cat))|surge operating", "un", [("ov1", "threshold_un"), ("ov2", "threshold_un")]),
    (r"(?<!10 min )over-?\s*voltage(?! (ride|category|10|cat))|surge operating", "s", [("ov1", "time_s"), ("ov2", "time_s")]),
    (r"10\s*min(utes)?\s*(mean|protection|on average)|10 min mean", "un", [("ov10", "threshold_un")]),
    (r"(?<!response to )under-?\s*frequency(?! (deviation|power))|too low frequency", "hz", [("uf1", "threshold_hz"), ("uf2", "threshold_hz")]),
    (r"(?<!response to )over-?\s*frequency(?! (deviation|power))|too high frequency", "hz", [("of1", "threshold_hz"), ("of2", "threshold_hz")]),
    (r"threshold frequency f\s*1", "hz", [("lfsm_o", "f1_hz"), ("lfsm_u", "f1_hz")]),
    (r"droop|statism", "pct", [("lfsm_o", "droop_pct"), ("lfsm_u", "droop_pct")]),
    (r"observation time", "s", [("reconnect", "observation_s"), ("start", "observation_s")]),
]
SLOTS = sorted({s for _, _, ss in FAMILIES for s in ss})


def flat(path: Path) -> str:
    t = path.read_text(encoding="utf-8", errors="replace")
    return re.sub(r"\s+", " ", t)


def num(s: str) -> float:
    return float(s.replace(",", "."))


def ranges_after(text: str, start: int, unit: str, window: int = 140):
    seg = text[start:start + window]
    # "0,2 Un – 1 Un", "47,0 Hz – 50,0 Hz", "0.1 s – 100 s", "Config. from 1.0 to 1.2 Un", "2 % – 12 %"
    rx = re.compile(NUM + r"\s*(?:" + UNIT[unit] + r")?\s*(?:[–-]|to)\s*" + NUM + r"\s*" + UNIT[unit], re.I)
    m = rx.search(seg)
    if not m:
        return None
    a, b = num(m.group(1)), num(m.group(2))
    return start + m.start(), (min(a, b), max(a, b))   # "49,8 Hz – 46 Hz" is a range too


def parse(text: str) -> dict:
    out = {}
    for fam, unit, slots in FAMILIES:
        found, used = [], set()
        for m in re.finditer(fam, text, re.I):
            hit = ranges_after(text, m.end(), unit)
            if hit and hit[0] not in used:   # a label split around its value meets the same range twice
                used.add(hit[0])
                found.append(hit[1])
            if len(found) == len(slots):
                break
        for slot, r in zip(slots, found):
            out.setdefault(slot, r)
    m = re.search(r"ROCOF.{0,200}?(?:up to\s*±?\s*" + NUM + r"\s*Hz/s|" + NUM + r"\s*[–-]\s*" + NUM + r"\s*Hz/s)", text, re.I)
    if m:
        out[("rocof", "immunity_hz_s")] = (0.0, num(m.group(1))) if m.group(1) else (num(m.group(2)), num(m.group(3)))
    return out


def hand(spec) -> tuple | None:
    if not isinstance(spec, dict):
        return None
    if "range" in spec:
        return tuple(float(x) for x in spec["range"])
    if "max" in spec:
        return (0.0, float(spec["max"]))
    return None


def text_for(pdf_dir: Path, url: str):
    base = Path(unquote(urlparse(url).path)).name
    for cand in (pdf_dir / (base + ".pages.txt"), pdf_dir / (Path(base).stem + ".txt")):
        if cand.exists():
            return cand
    return None


def score(cache: Path):
    tot = {"slots": 0, "found": 0, "right": 0}
    for f in sorted((ROOT / "data/test-reports").glob("*.yaml")):
        b = yaml.safe_load(f.read_text(encoding="utf-8"))
        for d in b["documents"]:
            funcs = d.get("functions") or {}
            want = {(fn, p): hand(funcs.get(fn, {}).get(p)) for fn, p in SLOTS + [("rocof", "immunity_hz_s")]}
            want = {k: v for k, v in want.items() if v}
            if not want:
                continue
            txt = None
            for sub in cache.iterdir() if cache.is_dir() else []:
                for t in sub.glob("*.txt"):
                    if t.name.endswith(".hits.txt"):
                        continue
                    if any(k in flat(t)[:4000] for k in filter(None, [d.get("cert_no"), d.get("report_no")])):
                        txt = t
                        break
                if txt:
                    break
            if not txt:
                print(f"{d['id']:<44} no cached text found")
                continue
            got = parse(flat(txt))
            right = sum(1 for k, v in want.items() if got.get(k) and abs(got[k][0] - v[0]) < 1e-6 and abs(got[k][1] - v[1]) < 1e-6)
            found = sum(1 for k in want if k in got)
            wrong = [f"{k[0]}.{k[1]} {got[k]}≠{want[k]}" for k in want if k in got and got[k] != want[k] and not (abs(got[k][0] - want[k][0]) < 1e-6 and abs(got[k][1] - want[k][1]) < 1e-6)]
            tot["slots"] += len(want); tot["found"] += found; tot["right"] += right
            print(f"{d['id']:<44} {right:>2}/{len(want):<2} right ({found} found){'  wrong: ' + '; '.join(wrong[:4]) if wrong else ''}")
    print(f"total: {tot['right']}/{tot['slots']} ranges read right by the one generic parser ({tot['found']} found)")


def corpus(dirs: list[Path], registers: Path | None):
    """Every EN 50549 document of data/evidence, classified by what its cached text carries."""
    devs = []
    if registers:
        devs = [x for x in json.loads(registers.read_text(encoding="utf-8"))["devices"] if not x["unmatched"] and x["cls"] in ("inverter", "hybrid", "battery", "plug-in")]
    norm = lambda c: re.sub(r"\s+", "", c.upper()).replace(",", ".")
    rows, models = [], {"table": set(), "no-table": set(), "not-cached": set()}
    for f in sorted((ROOT / "data/evidence").glob("*.yaml")):
        b = yaml.safe_load(f.read_text(encoding="utf-8"))
        for d in b["documents"]:
            if not any("50549" in s for s in d.get("standards") or []):
                continue
            path = next((p for p in (text_for(dd / b["brand"].lower(), d["url"]) for dd in dirs) if p), None)
            if path is None:
                path = next((p for dd in dirs for sub in dd.glob("*") if sub.is_dir() for p in [text_for(sub, d["url"])] if p), None)
            if path is None:
                cls = "not-cached"
            else:
                text = flat(path)
                titled = re.search(r"annex c parameter table|parameter table|interface protection (system default )?settings", text, re.I)
                cls = "table" if len(parse(text)) >= 6 or (titled and len(parse(text)) >= 3) else "no-table"
            ms = set()
            for fam in d.get("families") or []:
                if fam.get("match"):
                    rx = re.compile(fam["match"])
                    ms |= {x["brand"] + "|" + x["model"] for x in devs if x["brand"].lower() in (b["brand"].lower(), b["brand"].split()[0].lower()) and rx.search(norm(x["model"]))}
            models[cls] |= ms
            rows.append((b["brand"], d["id"], cls, len(ms), d.get("issued", "")))
    for r in rows:
        print(f"{r[0]:<11} {r[1]:<52} {r[2]:<11} models {r[3]:<4} {r[4]}")
    n = {k: sum(1 for r in rows if r[2] == k) for k in models}
    print(f"EN 50549 documents: {len(rows)} — with a parameter table {n['table']}, without {n['no-table']}, text not cached {n['not-cached']}")
    if devs:
        t = models["table"]
        print(f"register models joined: by a document with a table {len(t)}; only by one without {len(models['no-table'] - t)}; "
              f"only by uncached ones {len(models['not-cached'] - t - models['no-table'])}")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "score":
        score(Path(sys.argv[2]))
    elif len(sys.argv) >= 3 and sys.argv[1] == "corpus":
        args = sys.argv[2:]
        reg = None
        if "--registers" in args:
            i = args.index("--registers")
            reg = Path(args[i + 1])
            args = args[:i] + args[i + 2:]
        corpus([Path(a) for a in args], reg)
    else:
        sys.exit(__doc__)
