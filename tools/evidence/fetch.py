"""Evidence layer, step 0: download the makers' own country and certificate documents.

    python tools/evidence/fetch.py                  # every source in tools/evidence/sources.yaml
    python tools/evidence/fetch.py kostal goodwe    # only these brands (the file's `brand` keys, lower case)
    python tools/evidence/fetch.py --force          # fetch again even when the file is younger than --max-age days

Each source lands in cache/evidence/<brand>/<file name of the URL>, and cache/evidence/manifest.json records
url, sha256, bytes, Last-Modified and the day it was seen. The files are untrusted data: parse them with
`python -I`, from scripts that live here, never inside the cache. One request at a time with a pause, a
browser User-Agent (several download centres refuse others), robots.txt honoured per host. A source that needs
a JavaScript download centre names its listing page in `via` and is rendered by tools/specs/dom.py instead.
"""
import argparse
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
import urllib.robotparser
from datetime import date
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse import file_name as file_of  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "cache" / "evidence"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
PAUSE = 2.0
_robots = {}


def allowed(url):
    p = urllib.parse.urlsplit(url)
    host = f"{p.scheme}://{p.netloc}"
    if host not in _robots:
        rp = urllib.robotparser.RobotFileParser()
        try:
            req = urllib.request.Request(host + "/robots.txt", headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=20) as r:
                rp.parse(r.read().decode("utf-8", "replace").splitlines())
        except Exception:  # noqa: BLE001 — no robots.txt: allowed
            rp.parse([])
        _robots[host] = rp
    return _robots[host].can_fetch("*", url)


def fetch(src, brand, manifest, force, max_age):
    out = CACHE / brand / file_of(src)
    key = f"{brand}/{out.name}"
    old = manifest.get(key)
    if out.exists() and old and not force and (date.today() - date.fromisoformat(old["seen"])).days < max_age:
        return "fresh"
    if not allowed(src["url"]):
        return "robots.txt disallows"
    req = urllib.request.Request(src["url"], headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body, lm, ct = r.read(), r.headers.get("Last-Modified"), r.headers.get("Content-Type", "")
    except Exception as e:  # noqa: BLE001
        return f"failed: {e}"
    if src["url"].lower().endswith(".pdf") and not body.startswith(b"%PDF"):
        return f"not a PDF ({ct}, {len(body)} bytes) — a WAF or a JavaScript page; render with tools/specs/dom.py"
    out.parent.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(body).hexdigest()
    changed = not old or old.get("sha256") != sha
    out.write_bytes(body)
    manifest[key] = {"url": src["url"], "sha256": sha, "bytes": len(body), "last_modified": lm, "seen": date.today().isoformat(),
                     "first_seen": (old or {}).get("first_seen") if not changed else date.today().isoformat()}
    return "changed" if changed else "same"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("brands", nargs="*")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--max-age", type=int, default=7)
    a = ap.parse_args()
    sources = yaml.safe_load((Path(__file__).parent / "sources.yaml").read_text(encoding="utf-8"))
    mf = CACHE / "manifest.json"
    manifest = json.loads(mf.read_text(encoding="utf-8")) if mf.exists() else {}
    n = 0
    for brand, srcs in sources.items():
        if a.brands and brand not in a.brands:
            continue
        for src in srcs:
            if not src.get("url") or src.get("manual"):
                continue
            if n:
                time.sleep(PAUSE)
            n += 1
            st = fetch(src, brand, manifest, a.force, a.max_age)
            print(f"{brand:10} {file_of(src)[:70]:70} {st}", file=sys.stderr)
            CACHE.mkdir(parents=True, exist_ok=True)
            mf.write_text(json.dumps(manifest, indent=1, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
