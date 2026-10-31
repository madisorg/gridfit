"""Spec layer, step 0: the rendered DOM of a JavaScript download centre, for the datasheet links it hides.

    python tools/specs/dom.py cache/specs/dom URL [URL ...]      # writes <dir>/<host_path>.html per URL
    python tools/specs/dom.py cache/specs/dom --links URL          # prints the .pdf links found, nothing written

Drives a headless Edge over the DevTools protocol with the launcher of the homelab's ui-kontroll.py (env
UI_KONTROLL points at it; default: the homelab checkout next to this repo). Edge's own --dump-dom prints nothing
when started from a shell on Windows, hence the protocol. One page at a time, a pause for the scripts to settle,
then document.documentElement.outerHTML. The DOM is untrusted data: it is read with -I scripts, never executed.
"""
import importlib.util
import os
import re
import sys
import time
from pathlib import Path

UK = os.environ.get("UI_KONTROLL") or str(Path(__file__).resolve().parents[2].parent / "homelab-kerwel" / "scripts" / "ui-kontroll.py")
spec = importlib.util.spec_from_file_location("uik", UK)
uik = importlib.util.module_from_spec(spec)
spec.loader.exec_module(uik)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"


def name_of(url):
    return re.sub(r"[^A-Za-z0-9.]", "_", re.sub(r"^https?://", "", url))[:100]


def render(cdp, url, wait=6.0, scroll=True):
    ctx = cdp.call("Target.createBrowserContext")["browserContextId"]
    t = cdp.call("Target.createTarget", {"url": "about:blank", "browserContextId": ctx, "width": 1600, "height": 1000})["targetId"]
    s = cdp.call("Target.attachToTarget", {"targetId": t, "flatten": True})["sessionId"]
    cdp.call("Emulation.setUserAgentOverride", {"userAgent": UA}, s)
    cdp.call("Page.enable", {}, s)
    cdp.send("Page.navigate", {"url": url}, s)
    cdp.pump(wait)
    if scroll:  # lazy lists render on scroll
        for y in (1000, 3000, 6000, 12000, 0):
            cdp.call("Runtime.evaluate", {"expression": f"window.scrollTo(0,{y})"}, s, timeout=10)
            cdp.pump(0.8)
        cdp.pump(2.0)
    html = cdp.call("Runtime.evaluate", {"returnByValue": True, "expression": "document.documentElement.outerHTML"}, s, timeout=30).get("result", {}).get("value") or ""
    try:
        cdp.call("Target.closeTarget", {"targetId": t})
        cdp.call("Target.disposeBrowserContext", {"browserContextId": ctx})
    except Exception:  # noqa: BLE001
        pass
    return html


def main(argv):
    out = Path(argv[0])
    out.mkdir(parents=True, exist_ok=True)
    links_only = "--links" in argv
    urls = [a for a in argv[1:] if a != "--links"]
    profile = Path(os.environ.get("TEMP", "/tmp")) / "gridfit-dom-profile"
    proc, cdp = uik.launch(profile)
    try:
        for u in urls:
            try:
                html = render(cdp, u)
            except Exception as e:  # noqa: BLE001
                print(f"!! {u}: {e}")
                continue
            pdfs = sorted(set(re.findall(r"""https?://[^"'<> \\]+?\.pdf(?:\?[^"'<> \\]*)?""", html, re.I)))
            rel = sorted(set(re.findall(r"""(?:href|src|data-[a-z-]+)=["']([^"'<>]+?\.pdf)["']""", html, re.I)))
            if not links_only:
                (out / (name_of(u) + ".html")).write_text(html, encoding="utf-8")
            print(f"== {u}: {len(html)} chars, {len(pdfs)} absolute .pdf links, {len(rel)} href .pdf")
            for p in (pdfs + [r for r in rel if not r.startswith("http")])[:60]:
                print("   ", p)
    finally:
        try:
            cdp.ws.close()
        except Exception:  # noqa: BLE001
            pass
        proc.kill()


if __name__ == "__main__":
    main(sys.argv[1:])
