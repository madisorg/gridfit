"""Join the sources into support rows and product families.

A *row* is one way to talk to a product: a HA core integration, a HACS custom
integration or an evcc template, for one brand. A *family* groups rows and the
grid-register models of one product line. Every row carries the source it came from
and the date it was seen; nothing is asserted that a source does not say.
"""
import re
from collections import defaultdict
from pathlib import Path

import yaml

from .brands import Brands, slug

CONN_LABEL = {
    "modbus_tcp": "Modbus TCP", "modbus_rtu": "Modbus RTU (RS485)", "http": "HTTP / REST",
    "mqtt": "MQTT", "ble": "Bluetooth", "udp": "UDP (vendor protocol)", "ocpp": "OCPP",
    "cloud": "Cloud API", "other": "LAN (vendor protocol)",
}
CLASS_LABEL = {"inverter": "Inverter", "hybrid": "Hybrid inverter", "battery": "Battery",
               "wallbox": "Wallbox", "meter": "Meter / energy manager", "plug-in": "Plug-in solar"}
SOURCE_LABEL = {"ha_core": "Home Assistant core", "hacs": "HACS custom integration", "evcc": "evcc template"}
OHF_BROWSE = "https://device-database-preview.openhomefoundation.org/browse?q="
EVCC_DOCS = {"meter": "https://docs.evcc.io/en/meters", "charger": "https://docs.evcc.io/en/chargers"}
EVCC_BLOB = "https://github.com/evcc-io/evcc/blob/master/templates/definition"


def _kind(cls):
    """Brand-wide rows only spread to families of the same kind."""
    return cls if cls in ("wallbox", "meter") else "energy"


def local_from_iot(iot):
    if not iot:
        return None
    return iot.startswith("local") or iot == "assumed_state"


# ---------------------------------------------------------------- HA core
def _walk_integrations(tree):
    out = {}
    for key, val in tree.items():
        if "integrations" in val:
            out.update(_walk_integrations(val["integrations"]))
        else:
            out[key] = val
    return out


def ha_core_rows(curated, integrations, probes, seen):
    flat = _walk_integrations(integrations["integration"])
    rows = []
    for c in curated:
        d = c["domain"]
        meta = flat.get(d)
        probe = probes.get(d) or {}
        manifest = probe.get("manifest")
        if not meta or not manifest:
            print(f"  ! HA core integration {d} not found upstream - skipped")
            continue
        iot = manifest.get("iot_class") or meta.get("iot_class")
        wp = probe.get("write_platforms") or []
        rows.append({
            "source": "ha_core", "ref": d, "name": meta.get("name") or manifest.get("name") or d,
            "brand": c["brand"], "class": c["class"], "family_hint": None, "families": c.get("families"),
            "local": local_from_iot(iot), "iot_class": iot, "conn": c.get("conn", []),
            "control": "write" if wp else "read",
            "control_detail": ("settable entities: " + ", ".join(wp)) if wp else "sensors only (no settable entities found)",
            "quality": manifest.get("quality_scale"),
            "url": f"https://www.home-assistant.io/integrations/{d}/",
            "source_url": f"https://github.com/home-assistant/core/tree/dev/homeassistant/components/{d}",
            "ohf_url": OHF_BROWSE + c["brand"].split()[0].split("/")[0].lower(),
            "seen": seen,
        })
    return rows


# ---------------------------------------------------------------- HACS
def hacs_rows(curated, hacs_data, probes, seen):
    by_name = {v["full_name"].lower(): v for v in hacs_data.values()}
    rows = []
    for c in curated:
        meta = by_name.get(c["repo"].lower())
        if not meta:
            print(f"  ! {c['repo']} is not in the HACS default list - skipped")
            continue
        probe = probes.get(c["repo"]) or {}
        manifest = probe.get("manifest") or {}
        iot = manifest.get("iot_class")
        local = local_from_iot(iot)
        if local is None:
            local = None if not c.get("conn") else any(x != "cloud" for x in c["conn"])
        wp = probe.get("write_platforms") or []
        for brand in c["brands"]:
            rows.append({
                "source": "hacs", "ref": c["repo"], "name": meta.get("manifest_name") or c["repo"].split("/")[1],
                "brand": brand, "class": c["class"], "family_hint": c.get("family"),
                "families": c.get("families"),
                "local": local, "iot_class": iot, "conn": c.get("conn", []),
                "control": "write" if wp else ("read" if probe.get("manifest") else "unknown"),
                "control_detail": ("settable entities: " + ", ".join(wp)) if wp else (
                    "sensors only (no settable entities found)" if probe.get("manifest")
                    else "could not read the repo's manifest"),
                "stars": meta.get("stargazers_count") or 0, "updated": (meta.get("last_updated") or "")[:10],
                "description": (meta.get("description") or "").strip(),
                "note": c.get("note"),
                "url": f"https://github.com/{c['repo']}",
                "source_url": f"https://github.com/{c['repo']}",
                "seen": seen,
            })
    return rows


# ---------------------------------------------------------------- evcc
SKIP_GROUPS = {"heating", "heatinggeneric", "generic", "switchsockets"}
PLUGIN_BRANDS = {"Zendure", "Marstek", "Anker SOLIX", "APsystems", "Hoymiles", "EcoFlow"}


def _evcc_class(typ, usage):
    if typ == "charger":
        return "wallbox"
    u = set(usage or [])
    if "charge" in u or "aux" in u or not u or u == {"grid"}:
        return "meter"
    if "battery" in u and "pv" in u:
        return "hybrid"
    if "battery" in u:
        return "battery"
    return "inverter"


def evcc_rows(evcc_dir: Path, brands: Brands, seen):
    rows = []
    for typ in ("meter", "charger"):
        for f in sorted((evcc_dir / "templates/definition" / typ).glob("*.yaml")):
            t = yaml.safe_load(f.read_text(encoding="utf-8"))
            if t.get("deprecated") or t.get("group") in SKIP_GROUPS:
                continue
            tname = t.get("template") or f.stem
            params = t.get("params") or []
            pnames = {p.get("name") for p in params if p.get("name")}
            usage, modbus = [], []
            for p in params:
                if p.get("name") == "usage":
                    usage = p.get("choice") or []
                if p.get("name") == "modbus":
                    modbus = p.get("choice") or []
            render = t.get("render") or ""
            conn = []
            conn += ["modbus_tcp"] if "tcpip" in modbus else []
            conn += ["modbus_rtu"] if "rs485" in modbus else []
            conn += ["udp"] if "udp" in modbus else []
            if re.search(r"source:\s*http", render):
                conn.append("http")
            if re.search(r"source:\s*mqtt", render):
                conn.append("mqtt")
            is_ocpp = tname.startswith("ocpp")
            if is_ocpp:
                conn.append("ocpp")
            has_local_addr = bool(modbus) or bool(pnames & {"host", "uri", "ip"}) or is_ocpp
            has_creds = bool(pnames & {"user", "password", "token", "accesstoken", "refreshtoken", "clientid", "apikey"})
            if has_local_addr:
                local = True
            elif has_creds:
                local = False
                conn.append("cloud")
            else:
                local = None
            if local and not conn:
                conn.append("other")
            caps = t.get("capabilities") or []
            sponsor = "sponsorship" in ((t.get("requirements") or {}).get("evcc") or [])
            if typ == "charger":
                control, detail = "write", "evcc controls charging" + (
                    " (incl. 1p/3p phase switching)" if "1p3p" in caps else "")
            elif "battery-control" in caps:
                control, detail = "write", "evcc controls battery charge/discharge (battery-control)" + (
                    " and can curtail PV" if "curtail" in caps else "")
            elif "curtail" in caps:
                control, detail = "write", "evcc can curtail PV output (curtail)"
            else:
                control, detail = "read", "metering only"
            for prod in t.get("products") or []:
                raw_brand = prod.get("brand")
                if not raw_brand:
                    continue
                brand = brands.canon(raw_brand, strict=False)
                if not brand:
                    continue
                generic = ((prod.get("description") or {}).get("generic") or "").strip()
                cls = _evcc_class(typ, usage)
                if brand in PLUGIN_BRANDS and cls in ("inverter", "battery", "hybrid"):
                    cls = "plug-in"
                rows.append({
                    "source": "evcc", "ref": f"{tname}:{generic}" if generic else tname, "template": tname,
                    "product": generic, "name": f"{tname}" + (f" ({generic})" if generic else ""),
                    "brand": brand, "class": cls, "family_hint": generic or tname.replace("-", " ").capitalize(),
                    "local": local, "conn": conn, "control": control, "control_detail": detail,
                    "capabilities": caps, "sponsor": sponsor, "evcc_type": typ,
                    "url": EVCC_DOCS[typ], "source_url": f"{EVCC_BLOB}/{typ}/{f.name}",
                    "seen": seen,
                })
    return rows


# ---------------------------------------------------------------- families
def build_families(rows, families_cfg, register_models):
    fam_by_key = {}
    curated = defaultdict(list)
    for brand, fams in (families_cfg or {}).items():
        for f in fams:
            fam = {"brand": brand, "name": f["name"], "class": f["class"], "curated": True,
                   "match": re.compile(f["match"]) if f.get("match") else None,
                   "evcc": f.get("evcc") or [], "see_also": f.get("see_also") or [], "rows": [], "models": []}
            curated[brand].append(fam)
            fam_by_key[(brand, f["name"])] = fam

    def auto(brand, name, cls):
        key = (brand, name)
        if key not in fam_by_key:
            fam_by_key[key] = {"brand": brand, "name": name, "class": cls, "curated": False,
                               "match": None, "evcc": [], "see_also": [], "rows": [], "models": []}
        return fam_by_key[key]

    for r in rows:
        targets = []
        cur = curated.get(r["brand"], [])
        if r["source"] == "evcc":
            for fam in cur:
                for ref in fam["evcc"]:
                    tmpl, _, prod = ref.partition(":")
                    if tmpl == r["template"] and (not prod or prod == r["product"]):
                        targets.append(fam)
                        break
            if not targets:
                targets = [auto(r["brand"], r["family_hint"], r["class"])]
        else:
            restrict = r.get("families")
            if restrict is not None and cur:
                targets = [fam_by_key[(r["brand"], n)] for n in restrict if (r["brand"], n) in fam_by_key]
            elif cur and restrict is None:
                targets = [f for f in cur if _kind(f["class"]) == _kind(r["class"])]
            if not targets:
                targets = [auto(r["brand"], r["family_hint"] or r["name"], r["class"])]
        for fam in targets:
            fam["rows"].append(r)

    unmatched = defaultdict(list)
    for m in register_models:
        hit = None
        for fam in curated.get(m["brand"], []):
            if fam["match"] and fam["match"].search(m["norm"]):
                hit = fam
                break
        if hit:
            hit["models"].append(m)
        else:
            unmatched[m["brand"]].append(m)

    fams = [f for f in fam_by_key.values() if f["rows"] or f["models"]]
    used = defaultdict(set)
    for f in sorted(fams, key=lambda f: (not f["curated"], f["name"].lower())):
        s = slug(f["name"])
        base, i = s, 2
        while s in used[f["brand"]]:
            s, i = f"{base}-{i}", i + 1
        used[f["brand"]].add(s)
        f["slug"] = s
        f["brand_slug"] = slug(f["brand"])
        f["faq"] = faq(f)
        regs = set()
        for m in f["models"]:
            regs.update(m["registers"])
        f["registers"] = sorted(regs)
    return sorted(fams, key=lambda f: (f["brand"].lower(), not f["curated"], f["name"].lower())), unmatched


def _verb(rs, one, many):
    return one if len({r["name"] for r in rs}) == 1 else many


def _names(rs, n=2):
    names = []
    for r in rs:
        label = f"the {'HA core' if r['source'] == 'ha_core' else 'HACS'} integration “{r['name']}”"
        if label not in names:
            names.append(label)
    more = len(names) - n
    text = " and ".join(names[:n]) if len(names) <= n else ", ".join(names[:n])
    return text + (f" (+{more} more)" if more > 0 else "")


def faq(f):
    q = f"Does {f['brand']} {f['name']} work locally with Home Assistant?"
    ha = [r for r in f["rows"] if r["source"] in ("ha_core", "hacs")]
    ha_local = [r for r in ha if r["local"]]
    ha_cloud = [r for r in ha if r["local"] is False]
    ev = [r for r in f["rows"] if r["source"] == "evcc" and r["local"]]
    if ha_local:
        ctl = any(r["control"] == "write" for r in ha_local)
        a = (f"Yes, according to the public sources: {_names(ha_local)} {_verb(ha_local, 'talks', 'talk')} to it"
             " over the local network"
             + (f" and {_verb(ha_local, 'exposes', 'expose')} settable entities, not only sensors" if ctl
                else ", read-only as far as we can tell"))
    elif ha_cloud:
        a = f"Only through a cloud service as far as we found ({_names(ha_cloud)})"
    else:
        a = "We found no Home Assistant integration for it"
    if ev:
        ctl = [r for r in ev if r["control"] == "write"]
        what = "and lets evcc control it" if ctl else "for metering"
        sp = " (needs an evcc sponsor token)" if all(r.get("sponsor") for r in ev) else ""
        a += f"; evcc supports it locally {what}{sp}"
    if f.get("see_also"):
        a += "; a community YAML package also exists (linked below)"
    return {"q": q, "a": a + "."}


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))
