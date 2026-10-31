"""Spec layer, step 0b: harvest the makers' datasheet PDFs, unattended, every week.

    python tools/specs/harvest.py --http            # the HTTP recipes of tools/specs/harvest.yaml (GitHub Actions, Monday)
    python tools/specs/harvest.py --edge            # the Edge recipes: pages rendered in headless Edge (madis-pc, Sunday)
    python tools/specs/harvest.py --http --only deye,sofar --limit 3 --dry-run

For every recipe the maker's own listing (sitemap -> product pages, a download centre's pages or its API, or a page
rendered in Edge) is read for datasheet links; each sheet is fetched politely (robots.txt for this user agent, one
request per second per host, If-None-Match / If-Modified-Since from the last run) into cache/specs/<brand>/, and the
manifest data/specs/harvest.json (harvest-edge.json for --edge) records per PDF the URL, sha256, size, first and last
seen, the maker and the route. A sheet that is new or changed is read with tools/specs/table.py and lands as a
review draft in data/specs/_drafts/<brand>.yaml -- never in the live data/specs/<brand>.yaml, which stays a
reviewed, by-hand step. docs/harvest-report.md says what came in, what changed, what could not be read and which
routes failed. A host whose robots.txt disallows the user agent (en.growatt.com /upload/, the 403 of
w3oss.hoymiles.com) keeps its sheets listed in the manifest with route "robots", unfetched. Downloads are data,
never code: table.py runs with python -I.
"""
import argparse
import datetime
import hashlib
import html
import importlib.util
import json
import re
import subprocess
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


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


watch = _load("watch_run", ROOT / "tools/watch/run.py")  # one politeness implementation: Net, norm_model, items_sitemap
norm_model = watch.norm_model


class Net(watch.Net):
    """The watch's Net, with robots.txt read the way RFC 9309 and the search engines read it: the most specific
    (longest) matching rule wins. urllib.robotparser takes the first matching rule, so "Allow: /" followed by
    "Disallow: /upload/" (en.growatt.com) would let every file through; the maker meant the opposite."""

    def allowed(self, url):
        host = self._host(url)
        if host not in self.robots:  # as the watch reads it, but decoded with utf-8-sig: a BOM (en.goodwe.com) hides the first group
            rp = urllib.robotparser.RobotFileParser()
            try:
                status, _, body = self._raw(host + "/robots.txt", {})
                if status == 200:
                    rp.parse(body.decode("utf-8-sig", "replace").splitlines())
                elif status in (401, 403):
                    rp.disallow_all = True
                else:
                    rp.allow_all = True
            except Exception:  # noqa: BLE001 - no robots.txt reachable: the standard says allowed
                rp.allow_all = True
            self.robots[host] = rp
            self.delay[host] = max(1.0, float(rp.crawl_delay(watch.UA) or 0))
        if not super().allowed(url):
            return False
        rp = self.robots[host]
        entry = next((e for e in rp.entries if e.applies_to(watch.UA)), None) or rp.default_entry
        if entry is None:
            return True
        path = urllib.parse.quote(urllib.parse.urlparse(url).path or "/")
        best = None
        for rl in entry.rulelines:
            if rl.path == "*" or path.startswith(rl.path):
                if best is None or len(rl.path) > len(best.path):
                    best = rl
        return True if best is None else bool(best.allowance)

TODAY = datetime.date.today().isoformat()
CFG = yaml.safe_load((Path(__file__).parent / "harvest.yaml").read_text(encoding="utf-8"))
UA = CFG.get("ua") or watch.UA
watch.UA = UA
CACHE = ROOT / "cache/specs"
DRAFTS = ROOT / "data/specs/_drafts"
REPORT = ROOT / "docs/harvest-report.md"
REGISTERS = ROOT / "web/.data/registers.json"
MIN_PDF = 5_000
RULE = ("DRAFT - every value below was read by tools/specs/table.py from the sheet named in `source` and has not been reviewed. "
        "Review each row against the sheet, correct it in tools/specs/draft.py (named, with the reason) and let draft.py write "
        "data/specs/<brand>.yaml; this file is never read by the site.")


def manifest_path(edge):
    return ROOT / ("data/specs/harvest-edge.json" if edge else "data/specs/harvest.json")


def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def dump_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def slug(brand):
    return re.sub(r"[^a-z0-9]+", "", brand.lower())


def file_name(url):
    name = urllib.parse.unquote(urllib.parse.urlparse(url).path.rsplit("/", 1)[-1])
    name = re.sub(r"[^A-Za-z0-9._()+,-]+", "_", name).strip("_")[:120]
    return name if name.lower().endswith(".pdf") else name + ".pdf"


# ---------------------------------------------------------------- HTTP helpers on top of the watch's Net
def post(net, url, body, headers=None):
    if not net.allowed(url):
        return "robots", {}, b""
    net._wait(net._host(url))
    net.requests += 1
    h = {"User-Agent": UA, "Accept": "*/*", "X-Requested-With": "XMLHttpRequest",
         "Content-Type": "application/x-www-form-urlencoded", **(headers or {})}
    req = urllib.request.Request(url, data=body.encode() if isinstance(body, str) else body, headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.status, dict(r.headers), r.read(watch.MAX_BYTES)
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {}), b""


def text(body):
    return body.decode("utf-8", "replace")


def refresh_target(body, base):
    """A download page that is only <meta http-equiv="Refresh" content=".1; url=/uploads/file/x.pdf"> (SolaX, Hoymiles)."""
    m = re.search(r'http-equiv=["\']?Refresh["\']?\s+content=["\'][^"\']*?url=([^"\'>\s]+)', text(body[:4000]), re.I)
    return urllib.parse.urljoin(base, html.unescape(m.group(1))) if m else ""


def find_items(rx, body, base, dotall=False):
    out = []
    for m in rx.finditer(body):
        d = m.groupdict()
        url = urllib.parse.urljoin(base, html.unescape(d["url"]))
        url = urllib.parse.quote(url, safe=":/?&=%+,;@()[]!$'*~#")  # an IRI in the page (Deye's 【b】 prefix) -> a URI
        title = html.unescape(re.sub(r"\s+", " ", d.get("title") or "")).strip() or file_name(url)
        out.append({"url": url, "title": title, "type": (d.get("type") or "").strip(), "page": base})
    return out


def compile_item(rc):
    return re.compile(rc["item"], re.S if rc.get("item_dotall") else 0)


# ---------------------------------------------------------------- listing kinds
def list_sitemap_pages(rc, net, log, render=None):
    pages, _ = watch.items_sitemap(rc, net, {}, None, log)
    rx, out = compile_item(rc), []
    for p in pages:
        u = p["url"]
        if render:
            if not net.allowed(u):
                log.append(f"{rc['id']}: robots.txt disallows {u}")
                continue
            net._wait(net._host(u))
            body = render(u)
        else:
            st, _, b = net.get(u)
            if st != 200:
                log.append(f"{rc['id']}: page {u} HTTP {st}")
                continue
            body = text(b)
        out += find_items(rx, body, u, rc.get("item_dotall"))
    return out, len(pages)


def list_pages(rc, net, log):
    rx, out, seen = compile_item(rc), [], set()
    for page in range(1, int(rc.get("pages", 20)) + 1):
        u = rc["url"].format(page=page)
        if rc.get("method", "GET").upper() == "POST":
            st, _, b = post(net, u, rc.get("body", "").format(page=page))
        else:
            st, _, b = net.get(u)
        if st == "robots":
            raise RuntimeError("robots.txt disallows this user agent")
        if st != 200:
            log.append(f"{rc['id']}: page {page} HTTP {st}")
            break
        body = text(b)
        if rc.get("json_field"):
            try:
                body = json.loads(body).get(rc["json_field"]) or ""
            except json.JSONDecodeError:
                log.append(f"{rc['id']}: page {page} is not JSON")
                break
        items = [it for it in find_items(rx, body, u, rc.get("item_dotall")) if it["url"] not in seen]
        if not items:
            break
        seen.update(it["url"] for it in items)
        out += items
    return out, page


def list_hoymiles(rc, net, log):
    """type tree (dr_getdownloadtype per site section) -> series ids -> products -> the product's file list page."""
    api, cat, site = rc["url"], rc["catid"], rc["siteid"]
    series = {}
    for sid in rc.get("sids", ["1"]):
        st, _, b = post(net, api + "?c=api&m=dr_getdownloadtype", urllib.parse.urlencode({"sid": sid, "catid": cat, "siteid": site}))
        if st == "robots":
            raise RuntimeError("robots.txt disallows this user agent")
        try:
            tree = json.loads(b).get("data") or []
        except (json.JSONDecodeError, AttributeError):
            log.append(f"{rc['id']}: dr_getdownloadtype sid={sid} HTTP {st}, not JSON")
            continue
        for t in tree:
            for c in t.get("child") or []:
                for s in c.get("child") or []:
                    series[str(s["id"])] = f"{t.get('title', '')} / {s.get('title', '')}"
    products = {}
    for eid, name in series.items():
        st, _, b = post(net, api + "?c=api&m=dr_getdownloadproducts", urllib.parse.urlencode({"eid": eid, "catid": cat, "siteid": site}))
        try:
            for p in json.loads(b).get("data") or []:
                products[str(p["id"])] = html.unescape(p.get("title", ""))
        except (json.JSONDecodeError, AttributeError):
            log.append(f"{rc['id']}: dr_getdownloadproducts eid={eid} HTTP {st}")
    out, seen = [], set()
    for pid, pname in products.items():
        get = urllib.parse.quote(json.dumps({"catid": cat, "siteid": site, "title": "", "pid": int(pid)}, separators=(",", ":")))
        u = f"{api}?s=download&c=api&m=template&name=list_data.html&cache_siteid={site}&get={get}"
        st, _, b = net.get(u)
        if st != 200:
            log.append(f"{rc['id']}: list_data pid={pid} HTTP {st}")
            continue
        for m in re.finditer(r'href="(/downloads/[^"]+\.html)"[^>]*>\s*<div class="std-text3 pcrw-text">([^<]*)</div>\s*<div class="std-text3 pcrw-date">([^<]*)</div>', text(b)):
            href = urllib.parse.urljoin(api, m.group(1))
            if href in seen:
                continue
            seen.add(href)
            out.append({"url": href, "title": html.unescape(m.group(2)).strip(), "type": "", "page": pname, "date": m.group(3).strip()})
    log.append(f"{rc['id']}: {len(series)} series, {len(products)} products, {len(out)} files listed")
    return out, len(products)


def list_solis(rc, net, log):
    st, _, b = net.get(rc["url"])
    if st == "robots":
        raise RuntimeError("robots.txt disallows this user agent")
    if st != 200:
        raise RuntimeError(f"navbar API HTTP {st}")
    try:
        nav = json.loads(b)
    except json.JSONDecodeError:
        raise RuntimeError("navbar API did not answer JSON")
    names = set()

    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k in ("name", "title", "seriesName") and isinstance(v, str) and re.search(r"[A-Z]\d|S[56]-|RHI|RAI", v):
                    names.add(v)
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(nav)
    out = []
    for n in sorted(names):
        st, _, b = net.get(rc["form"].format(name=urllib.parse.quote(n)))
        if st != 200:
            continue
        for m in re.finditer(r'"(https?://cmsdata\.solisinverters\.com/[^"]+\.pdf)"', text(b)):
            u = html.unescape(m.group(1))
            out.append({"url": u, "title": file_name(u), "type": "", "page": n})
    return out, len(names)


# ---------------------------------------------------------------- Edge
class Edge:
    """Headless Edge over DevTools, with the homelab's ui-kontroll launcher (as tools/specs/dom.py). PDF URLs are read from
    the DOM and from Network.responseReceived / downloadWillBegin events; downloads are denied, the URL is enough."""

    def __init__(self):
        self.dom = _load("dom", ROOT / "tools/specs/dom.py")
        self.dom.UA = UA
        self.proc, self.cdp = self.dom.uik.launch(Path(tempfile.gettempdir()) / "gridfit-harvest-edge-profile")
        self.seen_urls = set()
        try:
            self.cdp.call("Browser.setDownloadBehavior", {"behavior": "deny", "eventsEnabled": True})
        except Exception:  # noqa: BLE001 - older protocol: downloads then simply happen nowhere
            pass

        def on_event(msg):
            p = msg.get("params", {})
            if msg["method"] == "Network.responseReceived":
                r = p.get("response", {})
                if "pdf" in (r.get("mimeType") or "").lower() or re.search(r"\.pdf(\?|$)", r.get("url", ""), re.I):
                    self.seen_urls.add(r["url"])
            elif msg["method"].endswith("downloadWillBegin"):
                self.seen_urls.add(p.get("url", ""))
        self.cdp.on_event = on_event

    def close(self):
        try:
            self.cdp.ws.close()
        except Exception:  # noqa: BLE001
            pass
        self.proc.kill()

    def render(self, url, clicks=(), paginate=None, collect=None, wait=6.0):
        cdp = self.cdp
        ctx = cdp.call("Target.createBrowserContext")["browserContextId"]
        t = cdp.call("Target.createTarget", {"url": "about:blank", "browserContextId": ctx, "width": 1600, "height": 1000})["targetId"]
        s = cdp.call("Target.attachToTarget", {"targetId": t, "flatten": True})["sessionId"]
        cdp.call("Emulation.setUserAgentOverride", {"userAgent": UA}, s)
        cdp.call("Page.enable", {}, s)
        cdp.call("Network.enable", {}, s)
        try:
            cdp.call("Page.setDownloadBehavior", {"behavior": "deny"}, s)
        except Exception:  # noqa: BLE001
            pass
        cdp.send("Page.navigate", {"url": url}, s)
        cdp.pump(wait)

        def js(expr, timeout=15):
            return cdp.call("Runtime.evaluate", {"returnByValue": True, "expression": expr}, s, timeout=timeout).get("result", {}).get("value")

        def click(sel):
            r = js("(() => { const e = document.querySelector(%s); if (!e) return 'none'; e.scrollIntoView(); e.click(); return 'ok'; })()" % json.dumps(sel))
            cdp.pump(2.5)
            return r == "ok"

        # a consent or region banner is ordinary browsing: the first visible button whose text accepts/closes it
        js("""(() => { const rx = /^(accept( all( cookies)?)?|agree|got it|i agree|allow all|akzeptieren|alle akzeptieren|zustimmen)$/i;
               for (const b of document.querySelectorAll('button, a, [role=button]')) {
                 const t = (b.textContent || '').trim(); const r = b.getBoundingClientRect();
                 if (rx.test(t) && r.width > 0 && r.height > 0) { b.click(); return t; } } return ''; })()""")
        cdp.pump(1.5)
        for sel in clicks:
            if not click(sel):
                pass
        for y in (1000, 3000, 6000, 12000, 0):
            js(f"window.scrollTo(0,{y})", 10)
            cdp.pump(0.6)
        cdp.pump(1.5)
        pages = [js("document.documentElement.outerHTML", 30) or ""]
        if paginate and collect:
            found = set(collect(pages[-1]))
            for _ in range(int(paginate.get("max", 10))):
                if not click(paginate["next"]):
                    break
                h = js("document.documentElement.outerHTML", 30) or ""
                new = set(collect(h)) - found
                if not new:
                    break
                found |= new
                pages.append(h)
        try:
            cdp.call("Target.closeTarget", {"targetId": t})
            cdp.call("Target.disposeBrowserContext", {"browserContextId": ctx})
        except Exception:  # noqa: BLE001
            pass
        return "\n".join(pages)


def list_edge_page(rc, net, log, edge):
    if not net.allowed(rc["url"]):
        raise RuntimeError("robots.txt disallows this user agent")
    net._wait(net._host(rc["url"]))
    rx = compile_item(rc)
    collect = lambda h: [m.groupdict()["url"] for m in rx.finditer(h)]  # noqa: E731
    before = set(edge.seen_urls)
    dom = edge.render(rc["url"], rc.get("clicks") or (), rc.get("paginate"), collect)
    out = find_items(rx, dom, rc["url"], rc.get("item_dotall"))
    for u in edge.seen_urls - before:  # PDFs the page fetched or tried to download while being clicked through
        if u and u not in {o["url"] for o in out}:
            out.append({"url": u, "title": file_name(u), "type": "", "page": rc["url"]})
    return out, 1


# ---------------------------------------------------------------- the draft (table.py -> _drafts/<brand>.yaml)
def num(s):
    m = re.search(r"\d+(?:[.,]\d+)?", str(s or "").replace(",", "."))
    return float(m.group(0)) if m else None


def kw(v, raw=""):
    n = num(v)
    if n is None:
        return None
    return round(n, 2) if re.search(r"\(k(W|VA)\)|\bk(W|VA)\b", raw or "", re.I) and n < 1000 else round(n / 1000, 2)


def mppt_of(s):
    n = num(str(s or "").split("/")[0])
    return None if n is None or n > 40 else int(n)


def phases_of(s):
    s = str(s or "")
    if re.search(r"\b3\s*[/|]?\s*(N\s*[/|]?\s*)?PE\b|three|3L|3W|3-?phase|3P\b|400\s*V|380", s, re.I):
        return 3
    if re.search(r"\bL\s*/\s*N|single|1L|1-?phase|1P\b|230\s*V|220", s, re.I):
        return 1
    return None


def read_table(pdf, header):
    cmd = [sys.executable, "-I", str(ROOT / "tools/specs/table.py"), str(pdf)] + (["--header", header] if header else [])
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300, encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return None, "table.py timed out"
    if r.returncode != 0:
        return None, (r.stderr or "table.py failed").strip().splitlines()[-1][:200]
    try:
        d = json.loads(r.stdout)
    except json.JSONDecodeError:
        return None, "table.py gave no JSON"
    models = [m for m in d.get("models") or [] if m.lower() not in ("model", "models", "type", "modell")]
    if models:
        return d, ""
    # a single-model sheet (Sungrow, most SMA): no model columns; the code stands alone in the sheet's first lines. The
    # draft then carries the code with every value null, and the register match still says what the sheet could cover.
    if header:
        r = subprocess.run([sys.executable, "-I", "-c", "import pdfplumber,sys\nwith pdfplumber.open(sys.argv[1]) as d:\n"
                            "    print((d.pages[0].extract_text() or '')[:3000])", str(pdf)], capture_output=True, text=True,
                           timeout=120, encoding="utf-8", errors="replace")
        hdr, codes = re.compile(header, re.I), []
        for ln in r.stdout.splitlines()[:25]:
            for w in re.split(r"[\s/|,]+", ln.strip()):
                if hdr.search(w) and 4 <= len(w) <= 24 and re.search(r"\d", w) and w not in codes:
                    codes.append(w)
        if codes:
            return {"file": pdf.name, "models": codes[:6], "rows": {}, "title_only": True}, "single-model sheet: code from the title, no table columns"
    return None, "no model columns found"


def draft_rows(d, sid):
    r = d["rows"]
    raw = lambda k: (r.get(k) or {}).get("raw", "")  # noqa: E731
    out = []
    for m in d["models"]:
        if m.lower() in ("model", "models", "type", "modell"):
            continue
        cell = lambda k: (r.get(k) or {}).get(m)  # noqa: E731
        aca = str(cell("ac_a") or "").split("/")
        row = {"code": m, "mppt": mppt_of(cell("mppt")), "ac_kw": kw(cell("ac_w"), raw("ac_w")), "ac_kva": kw(cell("ac_va"), raw("ac_va")),
               "ac_a": num(aca[-1]), "phases": phases_of(cell("phases")), "pv_kw": kw(cell("pv_w"), raw("pv_w")), "source": sid,
               "raw": {k: str(cell(k)) for k in ("mppt", "ac_w", "ac_va", "ac_a", "pv_w", "phases") if cell(k) is not None}}
        if d.get("title_only"):
            row["note"] = "single-model sheet: the code is from the title, the values are to be read by hand"
        out.append(row)
    return out


def write_draft(brand, sheet, table, dry):
    p = DRAFTS / f"{slug(brand)}.yaml"
    doc = yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else None
    doc = doc or {"brand": brand, "status": "draft", "rule": RULE, "sources": [], "models": []}
    sid = re.sub(r"\.pdf$", "", sheet["file"], flags=re.I).lower()
    doc["sources"] = [s for s in doc["sources"] if s["id"] != sid] + [
        {"id": sid, "url": sheet["url"], "file": sheet["file"], "title": sheet.get("title", ""), "sha256": sheet["sha256"], "seen": TODAY}]
    doc["models"] = [m for m in doc["models"] if m["source"] != sid] + draft_rows(table, sid)
    if not dry:
        DRAFTS.mkdir(parents=True, exist_ok=True)
        p.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")
    return [m for m in table["models"] if m.lower() not in ("model", "models", "type", "modell")]


# ---------------------------------------------------------------- register coverage of the sheets
class Registers:
    def __init__(self):
        self.by_brand = {}
        for d in load_json(REGISTERS, {}).get("devices", []):
            if not d.get("unmatched") and d.get("norm"):
                self.by_brand.setdefault(d["brand"].lower(), {})[d["norm"]] = d["model"]

    def covered(self, brand, codes):
        pool = self.by_brand.get(brand.lower(), {})
        hit = set()
        for c in codes:
            n = norm_model(c)
            if len(n) < 4:
                continue
            for dn in pool:
                if dn == n or (len(n) >= 6 and (dn.startswith(n) or n.startswith(dn) and len(dn) >= 6)):
                    hit.add(dn)
        return hit, len(pool)


# ---------------------------------------------------------------- main loop
def title_ok(rc, title, url):
    hay = f"{title} {file_name(url)}"
    keep = re.compile(rc.get("keep_title") or CFG["keep_title"])
    drop = re.compile(rc.get("drop_title") or CFG["drop_title"])
    return bool(keep.search(hay)) and not drop.search(hay)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def resolve(net, url):
    """The URL a redirecting download link ends at (GoodWe /Skippower/downloadFileF?id=.. -> /Ftp/.../x.pdf), robots.txt
    checked at every hop; the URL itself when it does not redirect."""
    opener = urllib.request.build_opener(_NoRedirect)
    for _ in range(4):
        if not net.allowed(url):
            return "robots", url
        net._wait(net._host(url))
        net.requests += 1
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"}, method="HEAD")
        try:
            with opener.open(req, timeout=60) as r:
                return r.status, url
        except urllib.error.HTTPError as e:
            loc = (e.headers or {}).get("Location") if e.code in (301, 302, 303, 307, 308) else None
            if not loc:
                return e.code, url
            url = urllib.parse.urljoin(url, loc)
    return 0, url


def fetch_sheet(net, url, prev):
    """-> (status, body, headers, final_url): follows a redirecting link or one meta-refresh download page;
    robots.txt is checked for every host on the way."""
    final = url
    if not re.search(r"\.pdf(\?|$)", urllib.parse.urlparse(url).path, re.I):
        st, final = resolve(net, url)
        if st == "robots":
            return "robots", b"", {}, final
    same = prev if prev and prev.get("route") in ("ok", "edge") and (prev.get("file_url") or prev["url"]) == final else None
    st, h, b = net.get(final, same)
    if st == 200 and not b.startswith(b"%PDF") and len(b) < 20_000:
        target = refresh_target(b, final)
        if target:
            if not net.allowed(target):
                return "robots", b"", {}, target
            st, h, b = net.get(target, prev if prev and prev.get("file_url") == target else None)
            return st, b, h, target
    return st, b, h, final


def run(a):
    edge_mode = a.edge
    recipes = [r for r in CFG["recipes"] if (r["mode"] == "edge") == edge_mode and (not a.only or r["id"] in a.only)]
    if a.report_only or a.redraft:
        recipes = []
    manifest = load_json(manifest_path(edge_mode), {"sheets": {}, "routes": {}})
    sheets, routes = manifest["sheets"], manifest["routes"]
    net, log, regs = Net(), [], Registers()
    if a.redraft:  # offline: read every cached sheet whose table was not read (or only its title) once more
        headers = {r["id"]: r.get("header") for r in CFG["recipes"]}
        for url, rec in sheets.items():
            pdf = CACHE / slug(rec["brand"]) / (rec.get("file") or "")
            if not rec.get("file") or not pdf.exists() or (rec.get("models") and rec.get("table") == "columns"):
                continue
            table, why = read_table(pdf, headers.get(rec.get("recipe")))
            rec["models"] = write_draft(rec["brand"], rec, table, a.dry_run) if table else []
            rec["table"] = "title only" if table and table.get("title_only") else ("columns" if table else "none")
            print(f"   {rec['brand']}: {rec['file']} -> {rec['table']} {rec['models'][:4]}")
        for rid, r in routes.items():
            codes = [c for s in sheets.values() if s.get("recipe") == rid for c in s.get("models") or []]
            r["cover_all"], r["register_models"] = (lambda h, n: (len(h), n))(*regs.covered(r.get("brand", ""), codes))
            r["unread"] = sum(1 for s in sheets.values() if s.get("recipe") == rid and s.get("file") and s.get("table") != "columns")
        if not a.dry_run:
            dump_json(manifest_path(edge_mode), manifest)
    edge = Edge() if edge_mode else None
    results = {}  # recipe id -> summary for the report
    try:
        for rc in recipes:
            rid, brand = rc["id"], rc["brand"]
            print(f"== {rid} ({rc['kind']})", flush=True)
            res = {"brand": brand, "checked": TODAY, "kind": rc["kind"], "status": "ok", "error": "", "listed": 0, "kept": 0,
                   "new": [], "changed": [], "unchanged": 0, "robots": [], "failed": [], "unread": [], "models": {}, "pages": 0}
            try:
                if rc["kind"] == "sitemap-pages":
                    items, res["pages"] = list_sitemap_pages(rc, net, log)
                elif rc["kind"] == "pages":
                    items, res["pages"] = list_pages(rc, net, log)
                elif rc["kind"] == "hoymiles-api":
                    items, res["pages"] = list_hoymiles(rc, net, log)
                elif rc["kind"] == "solis-api":
                    items, res["pages"] = list_solis(rc, net, log)
                elif rc["kind"] == "edge-page":
                    items, res["pages"] = list_edge_page(rc, net, log, edge)
                elif rc["kind"] == "edge-sitemap":
                    items, res["pages"] = list_sitemap_pages(rc, net, log, render=lambda u: edge.render(u))
                else:
                    raise RuntimeError(f"unknown kind {rc['kind']}")
            except Exception as e:  # noqa: BLE001 - one route must not stop the others
                res.update(status="failed", error=f"{type(e).__name__}: {e}"[:300])
                print(f"   !! {res['error']}", flush=True)
                results[rid] = res
                routes[rid] = {k: v for k, v in res.items() if k not in ("new", "changed", "robots", "failed", "unread", "models")}
                continue
            seen, kept = set(), []
            for it in items:
                if it["url"] in seen:
                    continue
                seen.add(it["url"])
                if rc.get("type") and not re.search(rc["type"], it.get("type") or ""):
                    continue
                if title_ok(rc, it["title"], it["url"]):
                    kept.append(it)
            res["listed"], res["kept"] = len(seen), len(kept)
            print(f"   {len(seen)} files listed on {res['pages']} pages, {len(kept)} datasheet-like", flush=True)
            no_dl = slug(brand) in a.no_download
            # a maker whose listing is allowed but whose file host robots.txt disallows (Growatt /upload/, w3oss.hoymiles.com):
            # one robots.txt read says so, and no download page is touched for nothing
            file_host_blocked = bool(rc.get("file_host")) and not net.allowed(rc["file_host"].rstrip("/") + "/x.pdf")
            fetched = 0
            for it in kept:
                url = it["url"]
                rec = sheets.get(url) or {"url": url, "brand": brand, "recipe": rid, "first_seen": TODAY}
                rec.update({"title": it["title"], "last_seen": TODAY, "recipe": rid, "page": it.get("page", "")})
                sheets[url] = rec
                if no_dl or (a.limit and fetched >= a.limit):
                    rec.setdefault("route", "listed")
                    continue
                if file_host_blocked or not net.allowed(url):
                    host = urllib.parse.urlparse(rc["file_host"] if file_host_blocked else url).netloc
                    rec.update(route="robots", error=f"robots.txt of {host} disallows this user agent")
                    for k in ("file", "sha256", "size", "models", "table", "etag", "last_modified"):
                        rec.pop(k, None)
                    res["robots"].append(url)
                    continue
                fetched += 1
                try:
                    st, body, h, final = fetch_sheet(net, url, rec)
                except Exception as e:  # noqa: BLE001 - a bad URL or a dead host is this sheet's problem, not the run's
                    rec.update(route="failed", error=f"{type(e).__name__}: {e}"[:200])
                    res["failed"].append(f"{url} ({rec['error']})")
                    continue
                if st == "robots":
                    rec.update(route="robots", file_url=final, error=f"robots.txt of {urllib.parse.urlparse(final).netloc} disallows this user agent")
                    res["robots"].append(final)
                    continue
                if st == 304:
                    rec["route"] = "ok"
                    res["unchanged"] += 1
                    continue
                if st != 200 or not body.startswith(b"%PDF") or len(body) < MIN_PDF:
                    rec.update(route="failed", error=f"HTTP {st}, {len(body)} bytes, {'PDF' if body.startswith(b'%PDF') else 'not a PDF'}")
                    res["failed"].append(f"{url} ({rec['error']})")
                    continue
                sha = hashlib.sha256(body).hexdigest()
                old_sha, is_new = rec.get("sha256"), not rec.get("file")
                changed = bool(old_sha) and old_sha != sha
                rec.update(route="edge" if edge_mode else "ok", file_url=final if final != url else "", sha256=sha, size=len(body),
                           etag=h.get("ETag", ""), last_modified=h.get("Last-Modified", ""), error="")
                name = file_name(final if final != url else url)
                folder = CACHE / slug(brand)
                if (folder / name).exists() and rec.get("file") != name:
                    name = sha[:8] + "_" + name
                rec["file"] = name
                if not a.dry_run:
                    folder.mkdir(parents=True, exist_ok=True)
                    (folder / name).write_bytes(body)
                    if is_new or changed:
                        with (folder / "HARVEST.txt").open("a", encoding="utf-8") as f:
                            f.write(f"{name} {url} {TODAY}\n")
                if is_new or changed:
                    (res["new"] if is_new else res["changed"]).append(url)
                    if is_new:
                        rec["first_seen"] = rec.get("first_seen") or TODAY
                    else:
                        rec["changed"] = TODAY
                    pdf = folder / name
                    if a.dry_run:
                        tmp = Path(tempfile.mkdtemp(prefix="harvest-")) / name
                        tmp.write_bytes(body)
                        pdf = tmp
                    table, why = read_table(pdf, rc.get("header"))
                    rec["models"] = write_draft(brand, rec, table, a.dry_run) if table else []
                    rec["table"] = "title only" if table and table.get("title_only") else ("columns" if table else "none")
                    res["models"][url] = rec["models"]
                    if why:
                        res["unread"].append(f"{name}: {why}")
                else:
                    res["unchanged"] += 1
            # register coverage of everything this recipe has ever brought in, and of this run's new sheets
            all_codes = [c for u, r in sheets.items() if r.get("recipe") == rid for c in r.get("models") or []]
            res["cover_all"], res["register_models"] = (lambda h, n: (len(h), n))(*regs.covered(brand, all_codes))
            new_codes = [c for u in res["new"] + res["changed"] for c in res["models"].get(u, [])]
            res["cover_new"] = len(regs.covered(brand, new_codes)[0])
            print(f"   new {len(res['new'])}, changed {len(res['changed'])}, unchanged {res['unchanged']}, robots {len(res['robots'])}, "
                  f"failed {len(res['failed'])}, unread {len(res['unread'])}; register models covered by all sheets {res['cover_all']}/{res['register_models']}", flush=True)
            results[rid] = res
            routes[rid] = {k: v for k, v in res.items() if k not in ("new", "changed", "robots", "failed", "unread", "models")}
            routes[rid].update(new=len(res["new"]), changed=len(res["changed"]), robots=len(res["robots"]), failed=len(res["failed"]), unread=len(res["unread"]))
    finally:
        if edge:
            edge.close()
    if not a.report_only:
        manifest.update(run=TODAY, mode="edge" if edge_mode else "http", requests=net.requests, log=log)
    print(f"\n{net.requests} requests")
    if not a.dry_run:
        if not a.report_only:
            dump_json(manifest_path(edge_mode), manifest)
        if not edge_mode or a.report or a.report_only:
            other = load_json(manifest_path(not edge_mode), {"sheets": {}, "routes": {}})
            REPORT.write_text(render_report(manifest, other, results, regs), encoding="utf-8")
            print(f"report -> {REPORT.relative_to(ROOT)}")
    return manifest, results


# ---------------------------------------------------------------- the report
BLOCKED = [
    ("Huawei", "its terms forbid automated access; never fetched"),
    ("SolarEdge", "knowledge-center.solaredge.com and www.solaredge.com answer 403 to /robots.txt and to every page (Cloudflare); "
                  "the watch's rule reads a 403 on robots.txt as disallowed. No PDF path was found that answers without the challenge; not bypassed"),
    ("Sigenergy", "www.sigenergy.com/robots.txt allows crawling, but /en/support/download is a JavaScript app (the plain URL is 404) and the "
                  "product pages' /en/download-center-pdf/<id> links answer HTML, not a PDF; no PDF reachable by direct URL. Not pursued"),
    ("Growatt files", "en.growatt.com/robots.txt disallows /upload/, where every sheet lives; the listing (/support/download/datasheet) is "
                      "allowed, so the sheets are listed in the manifest with route `robots` and fetched by hand"),
    ("Hoymiles files", "www.hoymiles.com has no robots.txt (allowed) and its download centre is listed in full; each /downloads/<x>.html "
                       "refreshes to w3oss.hoymiles.com, whose /robots.txt answers 403 - under the same rule as SolarEdge the file host is "
                       "disallowed. RFC 9309 reads a 4xx robots.txt as 'unavailable = may crawl'; relaxing the rule in tools/watch/run.py Net.allowed "
                       "would open this route (an owner's call)"),
]


def render_report(http_m, edge_m, results, regs):
    L = [f"# Datasheet harvest\n", f"*{TODAY}. Written by `tools/specs/harvest.py`; recipes in `tools/specs/harvest.yaml`, the manifest in "
         f"`data/specs/harvest.json` (+ `harvest-edge.json` from madis-pc). Drafts: `data/specs/_drafts/<brand>.yaml` - unreviewed, never read by the site.*\n"]
    both = {"http": http_m, "edge": edge_m} if http_m.get("mode") != "edge" else {"edge": http_m, "http": edge_m}
    L.append("## Sheets per maker\n")
    L.append("| maker | route | run | listed | datasheets | in cache | new this run | changed | listed, not fetched (robots) | failed | table not read | register models a sheet covers |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for mode, m in both.items():
        for rid, r in sorted(m.get("routes", {}).items(), key=lambda x: x[1].get("brand", "")):
            have = sum(1 for s in m["sheets"].values() if s.get("recipe") == rid and s.get("file"))
            if r.get("status") == "failed":
                L.append(f"| {r.get('brand', rid)} | {mode} | {r.get('checked', '')} | - | - | {have} | - | - | - | **route failed**: {r.get('error', '')} | - | - |")
                continue
            L.append(f"| {r.get('brand', rid)} | {mode} | {r.get('checked', '')} | {r.get('listed', 0)} | {r.get('kept', 0)} | {have} | {r.get('new', 0)} | "
                     f"{r.get('changed', 0)} | {r.get('robots', 0)} | {r.get('failed', 0)} | {r.get('unread', 0)} | {r.get('cover_all', 0)} / {r.get('register_models', 0)} |")
    L.append("\n\"register models a sheet covers\": models of that maker in the register snapshot (`web/.data/registers.json`) whose code matches a "
             "model column of any harvested sheet - what the drafts could give the site once reviewed. The live `data/specs/` numbers are in the README.\n")
    # the lists come from the manifests' own dates, so a report can be rewritten from them (--report-only)
    def rows_of(key):
        out = []
        for m in both.values():
            run = m.get("run", "")
            for u, s in sorted(m.get("sheets", {}).items(), key=lambda x: (x[1].get("brand", ""), x[0])):
                if s.get("last_seen") != run:
                    continue
                fresh = s.get("first_seen") == run or s.get("changed") == run
                if key == "new" and s.get("file") and s.get("first_seen") == run:
                    out.append((s["brand"], u))
                elif key == "changed" and s.get("changed") == run:
                    out.append((s["brand"], u))
                elif key == "failed" and s.get("route") == "failed":
                    out.append((s["brand"], f"{u} ({s.get('error', '')})"))
                elif key == "unread" and s.get("file") and fresh and (not s.get("models") or s.get("table") == "title only"):
                    out.append((s["brand"], f"{s['file']} ({u}) - {'title only, no table columns' if s.get('models') else 'no model columns found'}"))
                elif key == "robots" and s.get("route") == "robots":
                    out.append((s["brand"], u))
            if key == "failed":
                out += [(r.get("brand", rid), f"route `{rid}`: {r.get('error', '')}") for rid, r in m.get("routes", {}).items()
                        if r.get("status") == "failed" and r.get("checked") == run]
        return out

    for title, key in (("New sheets", "new"), ("Changed sheets", "changed"), ("Routes and files that failed", "failed"),
                       ("Sheets whose table could not be read", "unread"), ("Listed, not fetched (robots.txt)", "robots")):
        rows = rows_of(key)
        L.append(f"## {title} ({len(rows)})\n")
        if not rows:
            L.append("none\n")
        for b, x in rows[:300]:
            extra = ""
            if key in ("new", "changed"):
                s = next((m["sheets"].get(x) for m in both.values() if x in m.get("sheets", {})), None) or {}
                models = s.get("models") or []
                cov, _ = regs.covered(b, models)
                extra = f" - {len(models)} model columns, {len(cov)} register models" if models else " - table not read"
            L.append(f"- {b}: {x}{extra}")
        if len(rows) > 300:
            L.append(f"- ... {len(rows) - 300} more in the manifest")
        L.append("")
    L.append("## Blocked, by rule\n")
    for who, why in BLOCKED:
        L.append(f"- **{who}** - {why}")
    L.append("")
    logs = (http_m.get("log") or []) + (edge_m.get("log") or [])
    if logs:
        L.append("## Log\n")
        L += [f"- {x}" for x in logs[:200]]
        L.append("")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--http", action="store_true", help="the HTTP recipes (GitHub Actions)")
    g.add_argument("--edge", action="store_true", help="the Edge recipes (madis-pc)")
    ap.add_argument("--only", default="", help="comma-separated recipe ids")
    ap.add_argument("--no-download", default="", help="comma-separated brand slugs: list only, fetch nothing")
    ap.add_argument("--limit", type=int, default=0, help="fetch at most N sheets per recipe (a test run)")
    ap.add_argument("--dry-run", action="store_true", help="fetch and print; write no manifest, cache or draft")
    ap.add_argument("--report", action="store_true", help="with --edge: also write docs/harvest-report.md")
    ap.add_argument("--report-only", action="store_true", help="fetch nothing; rewrite docs/harvest-report.md from both manifests")
    ap.add_argument("--redraft", action="store_true", help="fetch nothing; read the cached sheets whose table was not read once more")
    a = ap.parse_args(argv)
    a.only = set(filter(None, a.only.split(",")))
    a.no_download = set(filter(None, a.no_download.split(",")))
    run(a)


if __name__ == "__main__":
    main()
