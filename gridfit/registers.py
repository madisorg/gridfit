"""EU grid registers: download, parse, snapshot, diff, and the device cross-view.

The data flow, refreshed by hand about once a month (`python build.py --registers-refresh`):

    register web pages ──curl──> cache/registers/raw/<date>/          (downloads only; never executed)
    tools/registers/parse.py (python -I) ──> cache/registers/parsed/<date>/entries.jsonl
    snapshot()  ──> data/registers/snapshots/<date>.json.gz            (committed; one per refresh)
                ──> data/registers/changelog.json                      (committed; diff against the previous one)
                ──> data/registers/listing.json                        (committed; membership for the v1 family pages)

A plain `python build.py` reads only the committed files, so the site builds without touching the registers.
"""
import collections
import datetime
import gzip
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from .brands import slug

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/130.0 Safari/537.36")

# Column order of the cross-view. AT-EV (the Austrian charger list) shows in the AT column.
COUNTRIES = ["AT", "BE", "CZ", "NL", "PL", "SE"]
COUNTRY_OF = {"AT-EV": "AT"}

REGISTERS = {
    "AT": {
        "country": "Austria", "short": "Austrian TOR Erzeuger Typ A list",
        "name": "Wechselrichterliste TOR Erzeuger Typ A",
        "operator": "Oesterreichs Energie, for a project group of 14 grid operators",
        "url": "https://www.wechselrichterliste.at/tor-sea-typ-a",
        "basis": "E-Control TOR Stromerzeugungsanlagen Typ A v1.4 (in force 2026-06-01); test standard OVE R 25.",
        "gate": "De facto: a listed unit needs no individual review by the grid operator.",
        "contains": "PV, hybrid and AC-battery inverters with the list's own status (Ja / Ja - mit Einschränkung / "
                    "Ja - befristet / Nein), the firmware from which a restriction applies, and the end date of "
                    "time-limited entries. No certificate numbers.",
        "terms": "No reuse terms are stated (imprint only).",
        "use": "status word, firmware note and end date per row, with a link to the list",
        "date_label": "time-limited until", "fw_label": "restriction applies from firmware",
        "files": [("at_typ_a", "page", "https://www.wechselrichterliste.at/tor-sea-typ-a",
                   r'href="([^"]*Liste_TYP_A_TOR_ERZ[^"]*\.xlsx)"')],
    },
    "AT-EV": {
        "country": "Austria", "short": "Austrian charger list (TOR Verteilernetzanschluss)",
        "name": "Ladeeinrichtungen (TOR Verteilernetzanschluss)",
        "operator": "Oesterreichs Energie",
        "url": "https://www.wechselrichterliste.at/ladeeinrichtungen",
        "basis": "TOR Verteilernetzanschluss ch. 8.1 + OVE R 37; test reports required from 2026-12-15.",
        "gate": "De facto, as for the inverter list.",
        "contains": "EV chargers with the OVE R 37 (charging) status, e.g. Ja / Ja - <= 16 A / Ja - befristet, "
                    "the firmware from which a restriction applies and the end date of time-limited entries.",
        "terms": "No reuse terms are stated (imprint only).",
        "use": "status word, firmware note and end date per row, with a link to the list",
        "date_label": "time-limited until", "fw_label": "restriction applies from firmware",
        "files": [("at_laden", "page", "https://www.wechselrichterliste.at/ladeeinrichtungen",
                   r'href="([^"]*Liste_TOR_VNA_Ladeeinrichtungen[^"]*\.xlsx)"')],
    },
    "BE": {
        "country": "Belgium", "short": "Belgian Synergrid C10/26 list",
        "name": "Synergrid C10/26 — list of power-generating units compliant with C10/11",
        "operator": "Synergrid vzw",
        "url": "https://www.synergrid.be/nl/homologatie/elektriciteit/decentrale-productie-eenheden",
        "basis": "C10/11 ed. 2.4 Annex D; homologation procedure C10/26.",
        "gate": "Yes: grid operators accept only listed units.",
        "contains": "PV, battery, hybrid, plug&play units, bidirectional chargers, CHP and wind, with firmware, "
                    "homologation reference and dates.",
        "terms": "Synergrid's website terms allow viewing, downloading and reproducing for personal use only.",
        "use": "only whether a model is listed (or in the expired sheet), with a link — no firmware, reference or "
               "dates; open the list itself for those",
        "date_label": "", "fw_label": "",
        "files": [("be_c10_26", "url",
                   "https://www.synergrid.be/images/downloads/c10_26_list_of_pgu_compliant_with_c10_11_ed2_1_12_2019.xlsx", "")],
    },
    "CZ": {
        "country": "Czechia", "short": "Czech ČEZ Distribuce list",
        "name": "Seznam schválených střídačů a otestovaných ochran",
        "operator": "ČEZ Distribuce (evidence from EG.D and ČEZd lab protocols and SZÚ certificates)",
        "url": "https://www.cezdistribuce.cz/cs/pro-vyrobce/overeni-souladu-s-rfg",
        "basis": "NC RfG via PPDS Příloha 4 and the MPO methodology 2023.",
        "gate": "Yes at ČEZ Distribuce for A1/A2 units since 2025-01-01.",
        "contains": "Inverters and storage units with the approved firmware, the settings profile, the kind of "
                    "evidence (certificate or protocol and its issuer) and the date of entry. No certificate numbers.",
        "terms": "No reuse terms are stated (\"Všechna práva vyhrazena\").",
        "use": "firmware, evidence type and date of entry per row, with a link to the list",
        "date_label": "added to the list", "fw_label": "approved firmware",
        "files": [("cz_seznam", "url",
                   "https://www.cezdistribuce.cz/file/edee/distribuce/legislativa/seznam_schvalenych_stridacu.xlsx", "")],
    },
    "NL": {
        "country": "Netherlands", "short": "Dutch Netbeheer Nederland type-A list",
        "name": "Goedgekeurde omvormers type A (opwek + opslag)",
        "operator": "Netbeheer Nederland, served by energieleveren.nl",
        "url": "https://www.energieleveren.nl/",
        "basis": "Netcode elektriciteit (ACM); EN 50549-1/-2; type-A certificate required since 2021-04-27.",
        "gate": "De facto: grid operators check the type when the installation is registered.",
        "contains": "Brand and type only, in two lists (generation and storage).",
        "terms": "No reuse terms are stated.",
        "use": "brand and type, with a link to the list",
        "date_label": "", "fw_label": "",
        "files": [("nl_power_generating", "url",
                   "https://api.energieleveren.nl/api/v2/files/homologation-file/POWER_GENERATING", ""),
                  ("nl_electrical_storage", "url",
                   "https://api.energieleveren.nl/api/v2/files/homologation-file/ELECTRICAL_STORAGE", "")],
    },
    "PL": {
        "country": "Poland", "short": "Polish PTPiREE WiPWC 1.3 list",
        "name": "Wykaz urządzeń (WiPWC 1.3)",
        "operator": "PTPiREE, for the Polish grid operators",
        "url": "https://ptpiree.pl/kodeksy-sieci/wykaz-certyfikatow/",
        "basis": "NC RfG + PSE WOS + WiPWC; devices certified only to WiPWC 1.2 are not accepted for new type-A "
                 "connections from 2027-01-01.",
        "gate": "Yes from 2027-01-01.",
        "contains": "Type A–D units and components with document number, a date column, WOS version, maker, "
                    "device type, model, PPM type and firmware.",
        "terms": "No reuse terms are stated (© footer).",
        "use": "document number, date and firmware per row, with a link to the list",
        "date_label": "date in the column 'Document acceptance date' (mostly in the future — read it as the "
                      "certificate's end date and check the certificate)",
        "fw_label": "firmware",
        "files": [("pl", "page", "https://ptpiree.pl/kodeksy-sieci/wykaz-certyfikatow/",
                   r'href="([^"]*Wykaz-urzadzen_1\.3\.pdf)"')],
    },
    "SE": {
        "country": "Sweden", "short": "Swedish Rikta Rätt inverter list",
        "name": "Rikta Rätt — växelriktare för solceller",
        "operator": "Energiföretagen Sverige",
        "url": "https://www.energiforetagen.se/energifakta/elsystemet/produktion/solceller/rikta-ratt--vaxelriktare-for-solceller",
        "basis": "Ellagen; RfG / EN 50549-1; EIFS 2018:2. A 2.0 XML database is announced.",
        "gate": "No (\"not binding\"); listing in Rikta Rätt 2.0 is expected from Q2 2027.",
        "contains": "PV, battery and hybrid inverters with the list's running number, firmware, power, phases, "
                    "energy source and review date.",
        "terms": "No reuse terms are stated.",
        "use": "running number, firmware and review date per row, with a link to the list",
        "date_label": "reviewed", "fw_label": "firmware",
        "files": [("se", "page",
                   "https://www.energiforetagen.se/energifakta/elsystemet/produktion/solceller/rikta-ratt--vaxelriktare-for-solceller",
                   r'href="([^"]*rikta-ratt-[\d-]+\.csv)"')],
    },
}

# Registers that exist but are not read, shown on the hub so the gap is visible.
NOT_READ = [
    ("DE", "Germany", "ZEREZ (FGW)", "https://zerez.net/", "a web app; the public view needs checking and it holds no wallboxes"),
    ("EE", "Estonia", "Elektrilevi inverter list", "https://www.elektrilevi.ee/", "planned; the page moved in October 2026"),
    ("IE", "Ireland", "ESB Networks LCT register", "https://www.esbnetworks.ie/about-us/projects/low-carbon-technology-register", "planned"),
    ("RO", "Romania", "Rețele Electrice inverter list", "https://www.reteleelectrice.ro/racordare/prosumator/", "planned"),
    ("UK", "United Kingdom", "ENA Type Test Register (Connect Direct)", "https://connect-direct.energynetworks.org/", "a web app; public access unverified"),
    ("DK", "Denmark", "Green Power Denmark positive lists", "https://elnet.dk/vejledning-teknik/nettilslutning/positivlister", "PDF only, not read yet"),
    ("HU", "Hungary", "MVM / E.ON HMKE lists", "https://mvmhalozat.hu/", "PDF only, not read yet"),
]

CLASS_LABEL = {"inverter": "PV inverter", "hybrid": "Hybrid inverter", "battery": "Battery / AC inverter",
               "plug-in": "Plug-in solar / battery (≤ 800 VA)", "wallbox": "Wallbox", "other": "Other (CHP, wind, generators)"}
STATUS_RANK = ["listed", "restricted", "limited", "expired", "nein", "other"]
STATUS_LABEL = {"listed": "listed", "restricted": "listed with restrictions", "limited": "time-limited",
                "limited-past": "time-limited, date passed", "expired": "expired", "nein": "Nein", "other": "see list"}
STATUS_SHORT = {"listed": "✓", "restricted": "✓*", "limited": "⏱", "limited-past": "⏱!", "expired": "exp",
                "nein": "Nein", "other": "?"}
PAGE_CLASSES = {"inverter", "hybrid", "battery", "plug-in", "wallbox"}


# ---------------------------------------------------------------- download + parse
def _curl(url, dest):
    r = subprocess.run(["curl", "-sSL", "--max-time", "180", "-A", UA, "-o", str(dest), "-w", "%{http_code}", url],
                       capture_output=True, text=True)
    return r.stdout.strip(), r.stderr.strip()


def download(root: Path, seen: str) -> Path:
    """Download every register file into a new, empty directory; returns it."""
    base = root / "cache/registers/raw" / seen
    raw, i = base, 2
    while raw.exists() and any(raw.iterdir()):
        raw, i = base.with_name(f"{seen}-{i}"), i + 1
    raw.mkdir(parents=True, exist_ok=True)
    pages = raw.parent / f"{raw.name}-pages"  # HTML of the pages that hold the current file link
    pages.mkdir(exist_ok=True)
    for reg, cfg in REGISTERS.items():
        for prefix, kind, url, pattern in cfg["files"]:
            if kind == "page":
                page = pages / f"{prefix}.html"
                code, err = _curl(url, page)
                m = re.search(pattern, page.read_text(encoding="utf-8", errors="replace")) if code == "200" else None
                if not m:
                    print(f"  {reg}: no file link on {url} (HTTP {code}) {err}")
                    continue
                href = m.group(1).replace("&amp;", "&")
                url = href if href.startswith("http") else re.match(r"https?://[^/]+", url)[0] + href
                name = f"{prefix}__{url.rsplit('/', 1)[-1]}"
            else:
                ext = {"cz_seznam": ".xlsx", "be_c10_26": ".xlsx"}.get(prefix, ".xlsx")
                name = prefix + ext
            code, err = _curl(url, raw / name)
            size = (raw / name).stat().st_size if (raw / name).exists() else 0
            head = (raw / name).read_bytes()[:4] if size else b""
            ok = code == "200" and size > 10_000 and (head.startswith(b"PK") or head.startswith(b"%PDF") or name.endswith(".csv"))
            print(f"  {reg}: {name} HTTP {code} {size} bytes {'ok' if ok else 'REJECTED'} {err}")
            if not ok and (raw / name).exists():
                (raw / name).unlink()
    return raw


def parse(root: Path, raw: Path, seen: str) -> Path:
    out = root / "cache/registers/parsed" / raw.name
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    # -I: the parser runs isolated, with neither the raw directory nor the repo on sys.path
    subprocess.run([sys.executable, "-I", "-X", "utf8", str(root / "tools/registers/parse.py"), str(raw), str(out),
                    str(root / "data/registers/alias.json"), seen], check=True, cwd=out)
    return out


# ---------------------------------------------------------------- snapshot + diff
def _key(e):
    if e["unmatched"]:
        return (e["reg"], "~" + e["maker_raw"], e["model_raw"] + "#" + e["id"])
    return (e["reg"], e["maker"], e["norm"])


def _state(es):
    return {"status": sorted({e["word"] or e["status"] for e in es}), "fw": sorted({e["fw"] for e in es if e["fw"]}),
            "valid": sorted({e["valid"] for e in es if e["valid"]}),
            "maker": es[0]["maker"], "model": es[0]["model_raw"]}


def snapshot(root: Path, parsed: Path, seen: str):
    """Store the parsed entries as the snapshot of `seen`, diff it against the previous snapshot,
    and refresh the change log and the v1 listing."""
    entries = [json.loads(l) for l in (parsed / "entries.jsonl").open(encoding="utf-8")]
    meta = json.loads((parsed / "meta.json").read_text(encoding="utf-8"))
    errors = (parsed / "errors.txt").read_text(encoding="utf-8").strip().splitlines()
    # a list that came back empty is treated as not downloaded, never as "every model removed"
    meta = {r: m for r, m in meta.items() if m.get("rows")}
    if not entries:
        raise SystemExit("register parse gave no rows - see " + str(parsed / "errors.txt") + "; nothing stored")
    snapdir = root / "data/registers/snapshots"
    snapdir.mkdir(parents=True, exist_ok=True)
    prev_files = sorted(p for p in snapdir.glob("*.json.gz") if p.name[:10] < seen)
    # a register whose download failed keeps its previous rows instead of "losing" them all
    if prev_files:
        prev = load_snapshot(prev_files[-1])
        missing = [r for r in prev["meta"] if r not in meta]
        for r in missing:
            meta[r] = dict(prev["meta"][r], carried_over=True)
            entries += [e for e in prev["entries"] if e["reg"] == r]
            print(f"  {r}: not downloaded this time, previous rows carried over")
    else:
        prev = None
    with gzip.open(snapdir / f"{seen}.json.gz", "wt", encoding="utf-8") as fh:
        json.dump({"date": seen, "meta": meta, "errors": errors, "entries": entries}, fh, ensure_ascii=False,
                  separators=(",", ":"))

    log_path = root / "data/registers/changelog.json"
    log = json.loads(log_path.read_text(encoding="utf-8")) if log_path.exists() else []
    log = [x for x in log if x["date"] != seen]
    if prev is None:
        entry = {"date": seen, "baseline": True,
                 "note": f"Baseline: {len(entries):,} rows from {len(meta)} lists. Later refreshes are compared with it.",
                 "registers": {}}
    else:
        entry = {"date": seen, "baseline": False, "previous": prev["date"], "registers": diff(prev, entries, meta)}
    log.insert(0, entry)
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return entry


def diff(prev, entries, meta):
    def group(es):
        g = collections.defaultdict(list)
        for e in es:
            g[_key(e)].append(e)
        return {k: _state(v) for k, v in g.items()}

    old, new = group(prev["entries"]), group(entries)
    out = {}
    for reg in sorted(set(meta) | set(prev["meta"])):
        o = {k: v for k, v in old.items() if k[0] == reg}
        n = {k: v for k, v in new.items() if k[0] == reg}
        r = {"source_date": meta.get(reg, {}).get("source_date", ""),
             "previous_source_date": prev["meta"].get(reg, {}).get("source_date", ""),
             "added": [[n[k]["maker"], n[k]["model"], " / ".join(n[k]["status"])] for k in sorted(n.keys() - o.keys())],
             "removed": [[o[k]["maker"], o[k]["model"], " / ".join(o[k]["status"])] for k in sorted(o.keys() - n.keys())],
             "changed": []}
        for k in sorted(n.keys() & o.keys()):
            for fld in ("status", "fw", "valid"):
                if reg == "BE" and fld != "status":
                    continue
                if n[k][fld] != o[k][fld]:
                    r["changed"].append([n[k]["maker"], n[k]["model"], fld, " / ".join(o[k][fld]) or "—",
                                         " / ".join(n[k][fld]) or "—"])
        if r["added"] or r["removed"] or r["changed"] or r["source_date"] != r["previous_source_date"]:
            out[reg] = r
    return out


def load_snapshot(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return json.load(fh)


def latest(root: Path):
    snaps = sorted((root / "data/registers/snapshots").glob("*.json.gz"))
    return load_snapshot(snaps[-1]) if snaps else None


# ---------------------------------------------------------------- devices
def _canon_names(alias_path: Path):
    return {k for k in json.loads(alias_path.read_text(encoding="utf-8")) if not k.startswith("_")}


def _collapse(x):
    return re.sub(r"\s+", " ", x).strip().upper()


def devices(snap, alias_path: Path, today: str):
    """Group register rows into devices (maker + normalised model) and decide class, trust and pages."""
    canon = _canon_names(alias_path)
    groups = collections.OrderedDict()
    for e in snap["entries"]:
        k = ("~", e["reg"], e["maker_raw"], e["model_raw"], e["id"]) if e["unmatched"] else (e["maker"], e["norm"])
        groups.setdefault(k, []).append(e)
    # one display name per normalised maker: the canonical name, else its most common spelling
    spell = collections.defaultdict(collections.Counter)
    for e in snap["entries"]:
        spell[e["maker"]][re.sub(r"\s+", " ", e["maker_raw"])] += 1
    shown = {m: m if m in canon else c.most_common(1)[0][0] for m, c in spell.items()}
    out = []
    for k, es in groups.items():
        brand = shown[es[0]["maker"]]
        models = collections.Counter(re.sub(r"\s+", " ", e["model_raw"]) for e in es)
        model = sorted(models.items(), key=lambda x: (-x[1], len(x[0])))[0][0]
        cells, sigs = collections.defaultdict(list), set()
        for e in es:
            # the same row twice (two sheets, two spellings of one model) is shown once
            sig = (e["reg"], e["model_raw"], e["status"]) if e["reg"] == "BE" else                 (e["reg"], e["model_raw"], e["word"], e["fw"], e["cert"], e["id"], e["valid"], e["date"], e["extra"].get("list"))
            if sig in sigs:
                continue
            sigs.add(sig)
            st = e["status"]
            if st == "limited" and e["valid"] and e["valid"] < today:
                st = "limited-past"
            exact = (_collapse(e["maker_raw"]) == _collapse(brand) or e["maker_grade"] == "exact") and \
                _collapse(e["model_raw"]) == _collapse(model)
            cells[COUNTRY_OF.get(e["reg"], e["reg"])].append(dict(
                e, show=st, trust="unmatched" if e["unmatched"] else ("exact" if exact else "alias")))
        out.append({"brand": brand, "model": model, "norm": es[0]["norm"], "cls": _class(es),
                    "cells": dict(cells), "n": len(cells), "unmatched": bool(es[0]["unmatched"]),
                    "variants": sorted(models)})
    _slugs(out)
    return out


def _class(es):
    if any(e["reg"] == "AT-EV" for e in es):
        return "wallbox"
    c = collections.Counter(e["cls"] for e in es if e["cls"] != "other")
    if not c:
        return "other"
    cls = c.most_common(1)[0][0]
    if "hybrid" in c and cls == "inverter" and c["hybrid"] * 2 >= c[cls]:
        cls = "hybrid"
    kvas = [e["kva"] for e in es if e.get("kva")]
    micro = any(e["extra"].get("micro") for e in es if e["reg"] == "PL")
    if (kvas and max(kvas) <= 0.8) or (micro and not kvas):
        return "plug-in"
    return cls


def _slugs(devs):
    used_b, used_m = {}, collections.defaultdict(set)
    for d in sorted(devs, key=lambda d: (d["brand"].lower(), d["model"].lower())):
        bs = slug(d["brand"])[:40].rstrip("-")
        # two spellings that slug the same ("Solax"/"SolaX") share a page; a different brand gets a suffix
        if used_b.get(bs, d["brand"].lower()) != d["brand"].lower():
            bs = f"{bs}-2"
        used_b.setdefault(bs, d["brand"].lower())
        d["brand_slug"] = bs
        d["page"] = d["cls"] in PAGE_CLASSES and d["n"] >= 2 and not d["unmatched"]
        if d["page"]:
            s = slug(d["model"])[:48].rstrip("-")
            base, i = s, 2
            while s in used_m[bs]:
                s, i = f"{base}-{i}", i + 1
            used_m[bs].add(s)
            d["slug"] = s


def best(cell):
    order = {"listed": 0, "restricted": 1, "limited": 2, "limited-past": 3, "expired": 4, "nein": 5, "other": 6}
    return min((e["show"] for e in cell), key=lambda s: order[s])


# ---------------------------------------------------------------- v1 family pages
def listing(devs, snap, brands, root: Path):
    """Membership only, for the v1 family pages: no BE (personal-use terms), no Nein, no unmatched rows."""
    v1 = {"listed": "listed", "restricted": "listed with restrictions", "limited": "listed, time-limited",
          "limited-past": "listed, time-limited"}
    models = []
    for d in devs:
        if d["unmatched"] or d["cls"] == "other":
            continue
        regs = {}
        for c, cell in d["cells"].items():
            if c == "BE":
                continue
            st = best(cell)
            if st in v1:
                regs[c] = v1[st]
        b = brands.canon(d["brand"])
        d["v1brand"] = b
        if not regs or not b:
            continue
        models.append({"brand": b, "model": d["model"], "norm": d["norm"],
                       "class": "plug-in" if d["cls"] == "plug-in" else d["cls"],
                       "registers": dict(sorted(regs.items())),
                       "trust": "exact" if all(e["trust"] == "exact" for cell in d["cells"].values() for e in cell) else "alias",
                       "page": f"registers/brand/{d['brand_slug']}/{d['slug']}/" if d["page"] else
                               f"registers/brand/{d['brand_slug']}/"})
    regs = {}
    for c in COUNTRIES:
        if c == "BE":
            continue
        m = snap["meta"].get(c, {})
        regs[c] = {"name": f"{REGISTERS[c]['country']} - {REGISTERS[c]['name']}", "url": REGISTERS[c]["url"],
                   "snapshot": m.get("source_date") or snap["date"]}
    models.sort(key=lambda x: (x["brand"].lower(), x["norm"]))
    (root / "data/registers/listing.json").write_text(
        json.dumps({"registers": regs, "models": models}, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
    return {"registers": regs, "models": models}
