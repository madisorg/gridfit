"""Freshness watch: where a new inverter, battery or wallbox model shows up first, and is it in GridFit yet.

    python tools/watch/run.py                 # every HTTP source in tools/watch/sources.yaml (GitHub Actions, weekly)
    python tools/watch/run.py --edge          # the JavaScript pages, through headless Edge (madis-pc only)
    python tools/watch/run.py --only deye-products,pv-magazine   # some sources; --dry-run writes nothing

Each source is fetched politely (robots.txt for this user agent, one request per second per host or the site's
Crawl-delay, ETag / Last-Modified where the server gives them), its items (product URLs, feed entries, model codes,
integration keys) are compared with the previous run (data/watch/seen/<id>.txt), and every model code found is
checked against the latest register snapshot, the curated families and the datasheet layer.

Writes data/watch/state.json, data/watch/seen/, data/watch/codes.json (first-seen date of every code, for the
lead-time numbers), data/watch/candidates.json and docs/watch-report.md. --edge writes state-edge.json,
codes-edge.json and candidates-edge.json instead, so the madis-pc run and the Actions run never edit the same file; the report folds
the Edge candidates in. Downloads go into new directories under cache/ and are only ever read, never executed.
"""
import argparse
import datetime
import gzip
import hashlib
import html
import json
import re
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from gridfit import registers  # noqa: E402

UA = "GridFit watch (+https://gridfit.eu)"
WATCH = ROOT / "data/watch"
REPORT = ROOT / "docs/watch-report.md"
MAX_BYTES = 40_000_000
TODAY = datetime.date.today().isoformat()


# ---------------------------------------------------------------- polite HTTP
class Net:
    def __init__(self):
        self.robots, self.delay, self.last = {}, {}, {}
        self.requests = 0

    def _host(self, url):
        p = urllib.parse.urlparse(url)
        return f"{p.scheme}://{p.netloc}"

    def _wait(self, host):
        gap = self.delay.get(host, 1.0)
        dt = time.monotonic() - self.last.get(host, 0)
        if dt < gap:
            time.sleep(gap - dt)
        self.last[host] = time.monotonic()

    def allowed(self, url):
        host = self._host(url)
        if host not in self.robots:
            rp = urllib.robotparser.RobotFileParser()
            try:
                status, _, body = self._raw(host + "/robots.txt", {})
                if status == 200:
                    rp.parse(body.decode("utf-8", "replace").splitlines())
                elif status in (401, 403):
                    rp.disallow_all = True
                else:
                    rp.allow_all = True
            except Exception:  # noqa: BLE001 - no robots.txt reachable: the standard says allowed
                rp.allow_all = True
            self.robots[host] = rp
            cd = rp.crawl_delay(UA)
            self.delay[host] = max(1.0, float(cd or 0))
        return self.robots[host].can_fetch(UA, url)

    def _raw(self, url, headers):
        self._wait(self._host(url))
        self.requests += 1
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*", **headers})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.status, dict(r.headers), r.read(MAX_BYTES)
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers or {}), b""

    def get(self, url, prev=None):
        """-> (status, headers, body); status 'robots' when robots.txt disallows, 304 when unchanged."""
        if not self.allowed(url):
            return "robots", {}, b""
        h = {}
        if prev and prev.get("etag"):
            h["If-None-Match"] = prev["etag"]
        if prev and prev.get("last_modified"):
            h["If-Modified-Since"] = prev["last_modified"]
        return self._raw(url, h)


# ---------------------------------------------------------------- model codes
def norm_model(raw):
    """The register normaliser (tools/registers/parse.py norm_model), so a code here compares with the snapshot."""
    s = str(raw or "").strip().upper()
    m = re.search(r"\s*\(([^()]*)\)\s*$", s)
    if m and not re.search(r"\d\s*(KW|KVA|W|KWH)\b", m.group(1)):
        s = s[:m.start()]
    for _ in range(2):
        s = re.sub(r"(?:-|\s)?(EU|SM2|SM|G2EU)$", "", s, flags=re.I)
    s = re.sub(r"(\d)\.0\b", r"\1", s)
    return re.sub(r"[\s\-_/\.,()]+", "", s)


NOISE = re.compile(r"^(\d+([.,]\d+)?(K?W|KWH|KWP|MWH?|GWH?|TWH?|KVA|MVA|V|A|AH|HZ|MM|KG|PCS|GB|MB|H|S|X|C|%)?"
                   r"|(19|20)\d\d([-/]\d+)*|Q[1-4]|H[12]|[1-6]G|CO2E?|COVID-?19|PV\d*|EV\d?|V\d.*|MPPT\d*|IP\d\d"
                   r"|LFP\d*|NMC\d*|TOPCON\d*|HJT\d*|ISO\d+.*|IEC\d+.*|EN\d+.*|VDE.*|UL\d+.*|RFG\d*|AC\d?|DC\d?)$")
TOKEN = re.compile(r"(?<![\w-])([A-Za-z0-9]+(?:[-./][A-Za-z0-9]+)*)(?![\w-])")
GENERIC = set("""series three single phase hybrid solar inverter inverters battery batteries residential commercial
industrial utility scale string storage system systems energy home charger wallbox ev ac dc with for and the new
smart rooftop retrofit coupled high low voltage plus product products kw kwh microinverter micro module power
station all in one portable balcony plug play ess bms solution solutions html""".split())


def looks_like_code(tok):
    t = tok.upper()
    if not (4 <= len(t) <= 40) or not re.search(r"[A-Z]", t) or not re.search(r"\d", t):
        return False
    if NOISE.match(norm_model(t)) or NOISE.match(t):
        return False
    return "-" in t or len(re.findall(r"[A-Z]+|\d+", t)) >= 3


def codes_in_text(text):
    return sorted({m.group(1) for m in TOKEN.finditer(text) if looks_like_code(m.group(1))})


def strip_brand(code, brand):
    b = re.sub(r"\W+", "-", (brand or "").upper()).strip("-")
    return code[len(b) + 1:] if b and code.startswith(b + "-") else code


def code_from_url(url):
    """The model or family named by a product URL's last segment: words up to the first generic one."""
    seg = urllib.parse.unquote(urllib.parse.urlparse(url).path.rstrip("/").rsplit("/", 1)[-1])
    seg = re.sub(r"\.(html?|php|aspx?)$", "", seg, flags=re.I)
    seg = re.sub(r"_[a-z]{2,3}$", "", seg)  # Solis: S6-EH3P(15-20)K-ND-H_gl
    words = []
    for w in re.split(r"[-_\s]+", seg):
        if w.lower() in GENERIC and words:
            break
        if w and w.lower() not in GENERIC:
            words.append(w)
    name = "-".join(words).upper()
    return name if 2 <= len(name) <= 40 else ""


class Known:
    """What GridFit already knows: register rows (latest snapshot), curated families, datasheet rows, brand names."""

    def __init__(self):
        snap = registers.latest(ROOT)
        self.snapshot = snap
        self.snapshot_date = snap["date"] if snap else ""
        self.lists, self.by_maker = {}, {}
        for e in (snap or {}).get("entries", []):
            if e.get("unmatched") or not e.get("norm"):
                continue
            reg = registers.COUNTRY_OF.get(e["reg"], e["reg"])
            self.lists.setdefault(e["norm"], set()).add(reg)
            self.by_maker.setdefault(e["maker"], set()).add(e["norm"])
        fam = yaml.safe_load((ROOT / "data/curated/families.yaml").read_text(encoding="utf-8"))
        self.families = {b: [(f["name"], re.compile(f["match"])) for f in fs if f.get("match")] for b, fs in fam.items()}
        self.specs = set()
        for p in (ROOT / "data/specs").glob("*.yaml"):
            for m in (yaml.safe_load(p.read_text(encoding="utf-8")) or {}).get("models") or []:
                self.specs.add(norm_model(m.get("code")))
        brands = yaml.safe_load((ROOT / "data/curated/brands.yaml").read_text(encoding="utf-8"))
        self.alias = {}
        for canon, spellings in brands.items():
            for s in [canon.lower(), *spellings]:
                if len(s) >= 3:
                    self.alias[s.lower()] = canon
        names = sorted(self.alias, key=len, reverse=True)
        self.brand_re = re.compile(r"(?<![\w-])(" + "|".join(re.escape(n) for n in names) + r")(?![\w-])", re.I)

    def brands_in(self, text):
        return sorted({self.alias[m.group(1).lower()] for m in self.brand_re.finditer(text)})

    def check(self, code, brand):
        n = norm_model(code)
        out = {"code": code, "norm": n, "brand": brand, "in_lists": sorted(self.lists.get(n, ())), "partial": [],
               "family": "", "specs": n in self.specs}
        if not out["in_lists"] and len(n) >= 6:
            pool = self.by_maker.get(brand, ()) if brand else ()
            out["partial"] = sorted(x for x in pool if x.startswith(n) or n.startswith(x))[:5]
        for name, rx in self.families.get(brand, []):
            if rx.search(n):
                out["family"] = name
                break
        out["verdict"] = ("in GridFit" if out["in_lists"] else "close to a listed model" if out["partial"]
                          else "family known, in no list yet" if out["family"] else "new to GridFit")
        return out


# ---------------------------------------------------------------- sources
def text_of(body):
    return body.decode("utf-8", "replace")


def tag(block, *names):
    for n in names:
        m = re.search(rf"<{n}\b[^>]*?(?:/>|>(.*?)</{n}>)", block, re.S | re.I)
        if m:
            v = m.group(1)
            if v is None:  # <link href="..."/>
                h = re.search(r'href="([^"]+)"', m.group(0))
                v = h.group(1) if h else ""
            v = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", v, flags=re.S)
            return html.unescape(re.sub(r"<[^>]+>", " ", html.unescape(v))).strip()
    return ""


def items_feed(src, body, known):
    t = text_of(body)
    out = []
    for block in re.findall(r"<(?:item|entry)\b.*?</(?:item|entry)>", t, re.S | re.I):
        title = re.sub(r"\s+", " ", tag(block, "title"))
        link = tag(block, "link")
        key = tag(block, "guid", "id") or link
        date = tag(block, "pubDate", "updated", "published")
        body_text = " ".join([title, tag(block, "description", "summary"), tag(block, "content:encoded", "content")])
        brands = known.brands_in(body_text)
        codes = codes_in_text(title + " " + body_text[:4000])
        it = {"key": key, "title": title, "url": link, "date": date, "brands": brands, "codes": codes}
        if src.get("press") and not (brands and codes):
            continue  # press: only entries that name a known brand and a model code
        out.append(it)
    return out


def items_sitemap(src, net, prev, known, log):
    status, h, body = net.get(src["url"])
    if status != 200:
        raise RuntimeError(f"HTTP {status}")
    t = text_of(body)
    locs = [html.unescape(x) for x in re.findall(r"<loc>\s*([^<]+?)\s*</loc>", t)]
    if "<sitemapindex" in t:
        children = [u for u in locs if re.search(src.get("follow", "."), u)]
        locs = []
        for u in children:
            s2, _, b2 = net.get(u)
            if s2 != 200:
                log.append(f"{src['id']}: child sitemap {u} HTTP {s2}")
                continue
            locs += [html.unescape(x) for x in re.findall(r"<loc>\s*([^<]+?)\s*</loc>", text_of(b2))]
    keep, drop = re.compile(src.get("keep", ".")), re.compile(src.get("drop", "^$"))
    out = []
    for u in sorted(set(locs)):
        if keep.search(u) and not drop.search(u):
            if src.get("slug") == "news":  # a press release: its title, not a code
                title = urllib.parse.unquote(u.rstrip("/").rsplit("/", 1)[-1]).rsplit(".", 1)[0].replace("-", " ")
                out.append({"key": u, "title": title, "url": u, "brands": [src.get("brand", "")], "codes": []})
                continue
            code = strip_brand(code_from_url(u), src.get("brand"))
            out.append({"key": u, "title": code or u, "url": u, "brands": [src.get("brand", "")],
                        "codes": [code] if code else []})
    return out, hashlib.sha256(body).hexdigest()


def items_keys(src, body, known):
    data = json.loads(body)
    if src.get("path"):
        data = data[src["path"]]
    energy = re.compile(r"(?i)\b(inverter|wechselrichter|solar|photovolt\w*|pv|battery|batteries|wallbox|charger|"
                        r"charging|evse|ocpp|energy storage|storage system|sunspec|bms)\b")
    out = []
    for k, v in data.items():
        v = v if isinstance(v, dict) else {}
        name = v.get("name") or v.get("full_name") or k
        text = " ".join(str(x) for x in (k, name, v.get("description", ""), v.get("domain", ""),
                                          " ".join(v.get("topics") or [])))
        brands = known.brands_in(text)
        if energy.search(text) or brands:
            url = (f"https://github.com/{v['full_name']}" if v.get("full_name")
                   else f"https://www.home-assistant.io/integrations/{k}/")
            out.append({"key": str(k), "title": name, "url": url, "brands": brands, "codes": []})
    return out


def items_pdf(src, body):
    from pypdf import PdfReader
    import io
    text = "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(body)).pages)
    if src.get("line"):  # a document that names products on lines ("PLENTICORE MP G3"), not as codes
        names = sorted({re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines() if re.search(src["line"], ln.strip())})
        return [{"key": n, "title": n, "url": src["url"], "brands": [src.get("brand", "")], "codes": [n]} for n in names]
    return [{"key": c, "title": c, "url": src["url"], "brands": [src.get("brand", "")], "codes": [c]}
            for c in codes_in_text(text)]


def visible_text(page):
    page = re.sub(r"(?s)<(script|style|noscript)\b.*?</\1>", " ", page)
    return html.unescape(re.sub(r"<[^>]+>", " ", page))


def items_text(src, page):
    """kind page, or an edge source with text: true - the model codes printed on a product listing."""
    brand = src.get("brand", "")
    return [{"key": c, "title": c, "url": src["url"], "brands": [brand], "codes": [c]}
            for c in sorted({strip_brand(c.upper(), brand) for c in codes_in_text(visible_text(page))})]


def items_edge(src, render):
    page = render(src["url"])
    if src.get("text"):
        return items_text(src, page)
    hrefs = set(re.findall(r'href="([^"#?]+)"', page))
    base = src["url"]
    keep, drop = re.compile(src.get("keep", ".")), re.compile(src.get("drop", "^$"))
    out = []
    for h in sorted(hrefs):
        u = urllib.parse.urljoin(base, html.unescape(h))
        if urllib.parse.urlparse(u).netloc == urllib.parse.urlparse(base).netloc and keep.search(u) and not drop.search(u):
            code = strip_brand(code_from_url(u), src.get("brand"))
            out.append({"key": u, "title": code or u, "url": u, "brands": [src.get("brand", "")],
                        "codes": [code] if code else []})
    return out


def run_registers(net, log):
    """Download every list robots.txt allows (same file names as gridfit/registers.py), parse them with the
    register parser, and diff each list against the latest snapshot."""
    raw = Path(tempfile.mkdtemp(prefix="watch-", dir=ROOT / "cache/registers/raw"))
    skipped, files = {}, {}
    for reg, cfg in registers.REGISTERS.items():
        for prefix, kind, url, pattern in cfg["files"]:
            status, _, body = net.get(url)
            if status == "robots":
                skipped[reg] = f"robots.txt of {urllib.parse.urlparse(url).netloc} disallows this user agent"
                break
            if kind == "page":
                m = re.search(pattern, text_of(body)) if status == 200 else None
                if not m:
                    log.append(f"registers {reg}: no file link on {url} (HTTP {status})")
                    break
                href = m.group(1).replace("&amp;", "&")
                url = href if href.startswith("http") else re.match(r"https?://[^/]+", url)[0] + href
                name = f"{prefix}__{url.rsplit('/', 1)[-1]}"
                status, _, body = net.get(url)
                if status == "robots":
                    skipped[reg] = f"robots.txt disallows {url}"
                    break
            else:
                name = prefix + {"ee_inverterite-nimekiri": ".html"}.get(prefix, ".xlsx")
            ok = status == 200 and len(body) > 10_000 and (body[:2] == b"PK" or body[:4] == b"%PDF"
                                                             or name.endswith((".csv", ".html")))
            if not ok:
                log.append(f"registers {reg}: {name} HTTP {status}, {len(body)} bytes, rejected")
                continue
            (raw / name).write_bytes(body)
            files[name] = {"reg": reg, "sha256": hashlib.sha256(body).hexdigest(), "url": url}
    if not files:
        return {}, skipped, files
    parsed = registers.parse(ROOT, raw, TODAY)
    entries = [json.loads(line) for line in (parsed / "entries.jsonl").open(encoding="utf-8")]
    meta = {r: m for r, m in json.loads((parsed / "meta.json").read_text(encoding="utf-8")).items() if m.get("rows")}
    snap = registers.latest(ROOT)
    if not snap:
        return {}, skipped, files
    prev = {"date": snap["date"], "meta": {r: m for r, m in snap["meta"].items() if r in meta},
            "entries": [e for e in snap["entries"] if e["reg"] in meta]}
    diff = registers.diff(prev, entries, meta)
    for reg in list(diff):
        r = diff[reg]
        if r["source_date"] and r["source_date"] == r["previous_source_date"]:
            # the same dated file as the snapshot cannot hold new models: the differences are the parser's
            # (PL: pypdf reads the PDF differently on madis-pc and on GitHub Actions)
            log.append(f"registers {reg}: same file as the snapshot ({r['source_date']}); "
                       f"{len(r['added'])} added / {len(r['removed'])} removed are parser drift, not reported")
            del diff[reg]
    return diff, skipped, files


# ---------------------------------------------------------------- state
def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def seen_path(sid):
    return WATCH / "seen" / f"{sid}.txt"


def read_seen(sid):
    p = seen_path(sid)
    return set(p.read_text(encoding="utf-8").splitlines()) if p.exists() else None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--edge", action="store_true", help="the JavaScript pages through headless Edge (madis-pc)")
    ap.add_argument("--only", default="", help="comma-separated source ids")
    ap.add_argument("--dry-run", action="store_true", help="fetch and print, write nothing")
    a = ap.parse_args(argv)

    cfg = yaml.safe_load((Path(__file__).parent / "sources.yaml").read_text(encoding="utf-8"))["sources"]
    only = set(filter(None, a.only.split(",")))
    srcs = [s for s in cfg if (s["kind"] == "edge") == a.edge and (not only or s["id"] in only)]
    suffix = "-edge" if a.edge else ""
    state = load(WATCH / f"state{suffix}.json", {})
    codes = load(WATCH / f"codes{suffix}.json", {})
    known = Known()
    net, log, cands, pending, render = Net(), [], [], {}, None
    (ROOT / "cache/registers/raw").mkdir(parents=True, exist_ok=True)

    if a.edge:
        import importlib.util
        spec = importlib.util.spec_from_file_location("dom", ROOT / "tools/specs/dom.py")
        dom = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dom)
        dom.UA = UA  # an honest user agent, as for the HTTP sources
        proc, cdp = dom.uik.launch(Path(tempfile.gettempdir()) / "gridfit-watch-edge-profile")

        def render(url):
            return dom.render(cdp, url)

    try:
        for src in srcs:
            sid, kind = src["id"], src["kind"]
            st = state.setdefault(sid, {})
            st.update({"kind": kind, "checked": TODAY, "error": ""})
            print(f"== {sid} ({kind})", flush=True)
            try:
                if kind == "registers":
                    diff, skipped, files = run_registers(net, log)
                    pending = {"snapshot": known.snapshot_date, "lists": diff, "skipped": skipped}
                    old = st.get("files", {})
                    st["files"] = {n: f["sha256"] for n, f in files.items()}
                    st["status"] = "changed" if st["files"] != old else "unchanged"
                    st["items"] = sum(len(r["added"]) for r in diff.values())
                    for reg, r in diff.items():
                        for maker, model, word in r["added"]:
                            c = known.check(model, maker)
                            c.update({"source": sid, "kind": kind, "title": f"{maker} {model}", "date": r["source_date"],
                                      "url": registers.REGISTERS[reg]["url"], "list": reg, "status_word": word,
                                      "verdict": "in a list, not yet in GridFit"})
                            cands.append(c)
                    print(f"   {len(files)} files, skipped {sorted(skipped)}, "
                          f"{st['items']} rows added since snapshot {known.snapshot_date}")
                    continue
                if kind == "sitemap":
                    items, digest = items_sitemap(src, net, st, known, log)
                elif kind == "edge":
                    if not net.allowed(src["url"]):
                        raise RuntimeError("robots.txt disallows this user agent")
                    net._wait(net._host(src["url"]))
                    items, digest = items_edge(src, render), ""
                else:
                    status, h, body = net.get(src["url"], st)
                    if status == "robots":
                        raise RuntimeError("robots.txt disallows this user agent")
                    if status == 304:
                        st["status"] = "unchanged (304)"
                        print("   304 not modified")
                        continue
                    if status != 200:
                        raise RuntimeError(f"HTTP {status}")
                    st["etag"], st["last_modified"] = h.get("ETag", ""), h.get("Last-Modified", "")
                    digest = hashlib.sha256(body).hexdigest()
                    if digest == st.get("sha256"):
                        st["status"] = "unchanged (same content)"
                        print("   same content")
                        continue
                    if kind == "feed":
                        items = items_feed(src, body, known)
                    elif kind == "page":
                        items = items_text(src, text_of(body))
                    elif kind == "keys":
                        items = items_keys(src, body, known)
                    elif kind == "file":
                        items = items_pdf(src, body) if src.get("extract") == "pdf" else [
                            {"key": digest, "title": "new version", "url": src["url"], "brands": [], "codes": []}]
                    elif kind == "link":
                        m = re.search(src["pattern"], text_of(body))
                        link = urllib.parse.urljoin(src["url"], html.unescape(m.group(1))) if m else ""
                        items = [{"key": link, "title": link.rsplit("/", 1)[-1], "url": link, "brands": [], "codes": []}] if link else []
                        digest = link  # the page changes for many reasons; only the linked file name counts
                    else:
                        raise RuntimeError(f"unknown kind {kind}")
                prev_keys = read_seen(sid)
                keys = {it["key"] for it in items}
                baseline = prev_keys is None
                new = [it for it in items if baseline or it["key"] not in prev_keys]
                st.update({"sha256": digest, "items": len(items), "new": 0 if baseline else len(new),
                           "status": "baseline" if baseline else ("changed" if new else "unchanged items")})
                if new and not baseline:
                    st["changed"] = TODAY
                if not a.dry_run:
                    p = seen_path(sid)
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text("\n".join(sorted(keys)) + "\n", encoding="utf-8")
                print(f"   {len(items)} items, {'baseline' if baseline else f'{len(new)} new'}")
                if baseline and kind == "keys":
                    continue  # thousands of old integrations are not news
                for it in new:
                    brand = (it["brands"] or [""])[0]
                    base = {"source": sid, "kind": kind, "title": it["title"], "url": it["url"],
                            "date": it.get("date") or TODAY, "baseline": baseline, "brands": it["brands"]}
                    if not it["codes"]:
                        cands.append({**base, "code": "", "norm": "", "brand": brand, "in_lists": [], "partial": [],
                                      "family": "", "specs": False, "verdict": "no model code"})
                    for code in it["codes"]:
                        c = known.check(code, brand)
                        cands.append({**base, **c})
            except Exception as e:  # noqa: BLE001 - one source must not stop the others
                st["status"], st["error"] = "error", f"{type(e).__name__}: {e}"[:300]
                print(f"   !! {st['error']}", flush=True)
    finally:
        if a.edge:
            try:
                cdp.ws.close()
            except Exception:  # noqa: BLE001
                pass
            proc.kill()

    # first-seen register of every code from a maker, the press or the integrations, and when a list caught up
    for c in cands:
        n = c.get("norm")
        if not n or c["kind"] == "registers":
            continue
        rec = codes.setdefault(n, {"code": c["code"], "brand": c["brand"], "first_seen": TODAY, "source": c["source"],
                                   "baseline": bool(c.get("baseline"))})
        if c["in_lists"] and not rec.get("listed"):
            rec["listed"] = TODAY
    for n, rec in codes.items():
        if not rec.get("listed") and known.lists.get(n):
            rec["listed"] = TODAY

    out = {"run": TODAY, "mode": "edge" if a.edge else "http", "requests": net.requests,
           "snapshot": known.snapshot_date, "registers_pending": pending, "candidates": cands, "log": log}
    print(f"\n{len(cands)} candidates, {net.requests} requests")
    if a.dry_run:
        return out
    dump(WATCH / f"state{suffix}.json", state)
    dump(WATCH / f"codes{suffix}.json", codes)
    dump(WATCH / f"candidates{suffix}.json", out)
    if not a.edge:
        from report import render as render_report  # tools/watch/report.py
        REPORT.write_text(render_report(out, load(WATCH / "candidates-edge.json", {}), state,
                                        load(WATCH / "state-edge.json", {}),
                                        {**load(WATCH / "codes-edge.json", {}), **codes}), encoding="utf-8")
        print(f"report -> {REPORT.relative_to(ROOT)}")
    return out


if __name__ == "__main__":
    main()
