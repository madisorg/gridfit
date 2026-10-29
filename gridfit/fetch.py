"""Download the open sources into cache/. Nothing here needs an account or an API key.

Sources (all public, see README "Sources and licences"):
  - Home Assistant core: generated/integrations.json + per-integration manifest.json (Apache-2.0)
  - HACS default store data: data-v2.hacs.xyz/integration/data.json (repo facts: stars, last update)
  - each curated HACS repo: custom_components/<domain>/manifest.json (iot_class)
  - evcc: templates/definition/{meter,charger}/*.yaml from the master tarball (MIT)
Entity-platform probes (number.py, select.py, ...) are HEAD requests to raw.githubusercontent.com,
so the build never touches the rate-limited GitHub REST API.
"""
import io
import json
import tarfile
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

UA = "gridfit-build/1.0 (+https://github.com/madisorg/gridfit)"
RAW = "https://raw.githubusercontent.com"
HA_RAW = f"{RAW}/home-assistant/core/dev/homeassistant"
EVCC_TARBALL = "https://codeload.github.com/evcc-io/evcc/tar.gz/refs/heads/master"
HACS_DATA = "https://data-v2.hacs.xyz/integration/data.json"
# Platforms through which an integration lets HA change something on the device.
WRITE_PLATFORMS = ("number", "select", "switch", "button")
MAX_AGE = 6 * 24 * 3600


def _get(url: str, method: str = "GET"):
    req = urllib.request.Request(url, method=method, headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, (r.read() if method == "GET" else b"")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return 404, b""
            if attempt == 2:
                raise
        except urllib.error.URLError:
            if attempt == 2:
                raise
        time.sleep(2 * (attempt + 1))
    return 0, b""


def _exists(url: str) -> bool:
    return _get(url, "HEAD")[0] == 200


class Cache:
    def __init__(self, root: Path, refresh: bool, offline: bool):
        self.root = root
        self.refresh = refresh
        self.offline = offline
        root.mkdir(parents=True, exist_ok=True)

    def fresh(self, name: str) -> bool:
        p = self.root / name
        if not p.exists():
            return False
        if self.offline:
            return True
        return not self.refresh and time.time() - p.stat().st_mtime < MAX_AGE

    def need(self, name: str):
        if self.offline and not (self.root / name).exists():
            raise SystemExit(f"--offline but cache/{name} is missing; run once without --offline")

    def json(self, name: str, url: str):
        p = self.root / name
        if not self.fresh(name):
            self.need(name)
            status, body = _get(url)
            if status != 200:
                raise SystemExit(f"download failed ({status}): {url}")
            p.write_bytes(body)
        return json.loads(p.read_text(encoding="utf-8"))

    def memo(self, name: str, compute):
        """Cache a computed JSON value (probes) under the same freshness rule."""
        p = self.root / name
        if self.fresh(name):
            return json.loads(p.read_text(encoding="utf-8"))
        self.need(name)
        value = compute()
        p.write_text(json.dumps(value, indent=1, sort_keys=True), encoding="utf-8")
        return value


def ha_integrations(cache: Cache):
    return cache.json("ha_integrations.json", f"{HA_RAW}/generated/integrations.json")


def _probe(base: str) -> dict:
    status, body = _get(f"{base}/manifest.json")
    manifest = json.loads(body) if status == 200 else None
    platforms = [p for p in WRITE_PLATFORMS if _exists(f"{base}/{p}.py")]
    return {"manifest": manifest, "write_platforms": platforms}


def ha_core_probes(cache: Cache, domains):
    def compute():
        with ThreadPoolExecutor(8) as ex:
            res = ex.map(lambda d: (d, _probe(f"{HA_RAW}/components/{d}")), domains)
        return dict(res)
    return cache.memo("ha_core_probes.json", compute)


def hacs_data(cache: Cache):
    return cache.json("hacs_data.json", HACS_DATA)


def hacs_probes(cache: Cache, repos_domains):
    """repos_domains: list of (repo, domain). Looks under HEAD, i.e. the default branch."""
    def compute():
        def one(rd):
            repo, domain = rd
            res = _probe(f"{RAW}/{repo}/HEAD/custom_components/{domain}")
            if res["manifest"] is None:  # hacs.json content_in_root: the integration sits at the repo root
                res = _probe(f"{RAW}/{repo}/HEAD")
            return repo, res
        with ThreadPoolExecutor(8) as ex:
            return dict(ex.map(one, repos_domains))
    return cache.memo("hacs_probes.json", compute)


def evcc_templates(cache: Cache) -> Path:
    """Extract meter/charger templates + LICENSE into cache/evcc/. Returns that directory."""
    dest = cache.root / "evcc"
    stamp = "evcc/.stamp"
    if not cache.fresh(stamp):
        cache.need(stamp)
        status, body = _get(EVCC_TARBALL)
        if status != 200:
            raise SystemExit("evcc tarball download failed")
        with tarfile.open(fileobj=io.BytesIO(body), mode="r:gz") as tf:
            for m in tf.getmembers():
                parts = m.name.split("/", 1)
                if len(parts) < 2 or not m.isfile():
                    continue
                rel = parts[1]
                keep = rel in ("LICENSE", "LICENSES/exclusions.md") or (
                    rel.startswith(("templates/definition/meter/", "templates/definition/charger/"))
                    and rel.endswith(".yaml"))
                if not keep or ".." in rel:
                    continue
                out = dest / rel
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(tf.extractfile(m).read())
        (cache.root / stamp).write_text(time.strftime("%Y-%m-%d"), encoding="utf-8")
    return dest
