"""True lastmod for the sitemap: data/sitemap/lastmod.json keeps, per sitemap path, a hash of the page's own content and the
day that hash last changed. Run after a build with GRIDFIT_BASE_URL set (the sitemaps list the paths):

    python tools/sitemap/lastmod.py web/dist            # updates data/sitemap/lastmod.json, prints what changed
    python tools/sitemap/lastmod.py web/dist --date 2026-11-12

What is hashed is the page's <main> as text plus its links, with scripts, styles and asset names left out and the
dataset's "last checked" date blanked, so a weekly refresh that only moves that date changes no lastmod; a new model
row, a new list status or a new requirement does. Paths no longer in the sitemap leave the file. refresh.yml and
lastmod.yml run this and commit the file; web/src/lib/sitemap.ts reads it at the next build.
"""
import argparse
import hashlib
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "data/sitemap/lastmod.json"
MAIN = re.compile(r"<main\b[^>]*>(.*)</main>", re.S | re.I)
DROP = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)
HREF = re.compile(r"""href=["']([^"']+)["']""")
TAG = re.compile(r"<[^>]+>")


def seen_date() -> str:
    rows = json.loads((ROOT / "data/dataset/rows.json").read_text(encoding="utf-8"))
    rows = rows["rows"] if isinstance(rows, dict) else rows
    return max((r.get("seen") or "") for r in rows)


def fingerprint(page: str, seen: str) -> str:
    m = MAIN.search(page)
    body = DROP.sub("", m.group(1) if m else page)
    links = " ".join(h for h in HREF.findall(body) if not h.startswith("/_astro/"))
    text = re.sub(r"\s+", " ", html.unescape(TAG.sub(" ", body))).strip()
    blob = (text + "\n" + links).replace(seen, "<seen>")
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:16]


def sitemap_paths(dist: Path) -> list[str]:
    index = dist / "sitemap.xml"
    if not index.exists() or not index.read_text(encoding="utf-8").strip():
        sys.exit(f"{index} is missing or empty: build with GRIDFIT_BASE_URL set")
    out = []
    for loc in re.findall(r"<loc>([^<]+)</loc>", index.read_text(encoding="utf-8")):
        child = dist / loc.rsplit("/", 1)[-1]
        out += [re.sub(r"^https?://[^/]+", "", u) for u in re.findall(r"<loc>([^<]+)</loc>", child.read_text(encoding="utf-8"))]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dist", type=Path)
    ap.add_argument("--date", default=datetime.now(timezone.utc).date().isoformat())
    a = ap.parse_args()
    seen = seen_date()
    old = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    new, changed, added, missing = {}, 0, 0, []
    for p in sitemap_paths(a.dist):
        f = a.dist / p.strip("/") / "index.html" if p != "/" else a.dist / "index.html"
        if not f.exists():
            missing.append(p)
            continue
        h = fingerprint(f.read_text(encoding="utf-8", errors="replace"), seen)
        if p not in old:
            new[p], added = [h, a.date], added + 1
        elif old[p][0] != h:
            new[p], changed = [h, a.date], changed + 1
        else:
            new[p] = old[p]
    if missing:
        sys.exit(f"sitemap paths without a built page: {missing[:5]}")
    gone = len(set(old) - set(new))
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(dict(sorted(new.items())), indent=0, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"lastmod: {len(new)} paths · {added} new · {changed} changed on {a.date} · {gone} gone · unchanged {len(new) - added - changed}")


if __name__ == "__main__":
    main()
