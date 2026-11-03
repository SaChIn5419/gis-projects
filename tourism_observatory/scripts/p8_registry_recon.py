#!/usr/bin/env python3
"""P8 / R-M1 — tourism-accommodation registry reconnaissance for Mussoorie.

PRE-FREEZE, NON-INFERENTIAL. This script counts candidate facilities for the
G-M1 feasibility gate. It does not measure tourism impact, does not compare
arms, and does not date anything. Recipe pinned in
docs/preplan_mussoorie.md §4.2 *before* this file was run.

Sources (all attempted, per the pin):
  S1  uttarastays.com/property-list — UTDB-linked public booking list.
      Rendered with Chromium because the API encrypts payloads client-side;
      only the public page is read.
  S2  OSM Overpass, tourism=hotel|guest_house|apartment|resort|chalet|hostel
      inside the AOI polygon (ODbL).
  S3  Ministry of Tourism approved hotels/restaurants — reachability only.

AOI: 8 km ring around the pinned Mussoorie anchor, clipped to Dehradun district
(M-1 primary zone, EPSG:32644).

Outputs
  data/processed/registry_uttarastays_all_2026-11-03.csv
  outputs/qaqc/p8_registry_recon_facts_2026-11-03.json

Usage: python scripts/p8_registry_recon.py
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import Point, shape

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
QA = ROOT / "outputs" / "qaqc"

BOUNDARY = PROC / "dehradun_boundary_32644.geojson"
CRS = "EPSG:32644"
ANCHOR_4326 = (78.0740, 30.4598)
RING_KM = 8.0

LISTING_URL = "https://uttarastays.com/property-list"
CHROME = "/usr/bin/chromium"
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
OVERPASS = "https://overpass-api.de/api/interpreter"
OVERPASS_TAGS = ["hotel", "guest_house", "apartment", "resort", "chalet", "hostel"]
MOT_URL = "https://tourism.gov.in/approved-hotels-and-restaurants"

# Locality labels that put a listing inside the 8 km ring (pin rule 2).
# Label membership, not a geocode — recorded as a limitation, not hidden.
AOI_LOCALITIES = {
    "mussoorie", "landour", "kempty", "barlowganj", "jharipani",
    "mall road", "library", "cantonment", "happy valley", "george everest",
}
# Kanatal (~24 km) and Dhanolti (~16 km) were removed after a distance check:
# both are well outside the 8 km ring and would have inflated the AOI count.

ADDR_RE = re.compile(
    r"City\s*-\s*(?P<city>[^,]+?)\s*,\s*District\s*-\s*(?P<district>[^,]+?)\s*,\s*"
    r"(?P<pin>\d{6})")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def aoi_polygon():
    """8 km ring around the anchor, clipped to the district (M-1)."""
    d = gpd.read_file(BOUNDARY).to_crs(CRS)
    dgeom = d.geometry.union_all()
    anchor = gpd.GeoSeries([Point(*ANCHOR_4326)], crs="EPSG:4326").to_crs(CRS).iloc[0]
    return dgeom.intersection(anchor.buffer(RING_KM * 1000.0)), dgeom, anchor


def crawl_listings() -> list[dict]:
    """S1 — scroll the public listing to exhaustion and parse cards."""
    from playwright.sync_api import sync_playwright

    rows: list[dict] = []
    stated_total: int | None = None
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=CHROME)
        ctx = browser.new_context(user_agent=UA, viewport={"width": 1400, "height": 2600})
        page = ctx.new_page()
        page.goto(LISTING_URL, wait_until="networkidle", timeout=120000)
        page.wait_for_timeout(4000)

        text = page.inner_text("body")
        m = re.search(r"Search Results\s*\((\d+)\)", text)
        stated_total = int(m.group(1)) if m else None
        print(f"   listing reports {stated_total} results")

        stale, best = 0, 0
        for _ in range(240):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.mouse.wheel(0, 40000)
            page.wait_for_timeout(2600)
            text = page.inner_text("body")
            n = len(re.findall(r"City - [^\n]{0,60}District - [^\n]{0,40}", text))
            if n > best:
                best, stale = n, 0
            else:
                stale += 1
                if stated_total is not None and best >= stated_total:
                    break
                if stale >= 15:
                    break

        text = page.inner_text("body")
        browser.close()

    lines = [ln.strip() for ln in text.split("\n")]
    last_name = None
    for ln in lines:
        if not ln:
            continue
        if ADDR_RE.search(ln):
            m = ADDR_RE.search(ln)
            rows.append({
                "name": (last_name or "").strip(),
                "address": ln,
                "city": m.group("city").strip(),
                "district": m.group("district").strip(),
                "pin": m.group("pin"),
            })
            last_name = None
            continue
        if (ln.startswith("Amenities") or ln == "Wellness Member" or ln == "View"
                or ln.startswith("₹") or re.fullmatch(r"\d+% Off", ln)):
            continue
        last_name = ln
    return rows, stated_total


def overpass_facilities(aoi_geom) -> dict:
    """S2 — OSM tourism accommodation with coordinates inside the AOI."""
    minx, miny, maxx, maxy = aoi_geom.bounds
    mid = aoi_geom.centroid
    # query in WGS84 to keep Overpass happy; filter precisely afterwards
    box = gpd.GeoSeries([aoi_geom], crs=CRS).to_crs("EPSG:4326").total_bounds
    bbox = f"{box[1]:.4f},{box[0]:.4f},{box[3]:.4f},{box[2]:.4f}"
    q = ("[out:json][timeout:120];("
         + "".join(f'node["tourism"="{t}"]({bbox});way["tourism"="{t}"]({bbox});'
                   for t in OVERPASS_TAGS)
         + ");out center tags;")
    last_err = None
    for wait in (5, 15, 30, 60, 90):
        try:
            r = requests.post(OVERPASS, data={"data": q},
                              headers={"User-Agent": "tourism-observatory-research/1.0",
                                       "Accept": "application/json"},
                              timeout=240)
            if r.status_code == 200:
                els = r.json().get("elements", [])
                break
            last_err = f"HTTP {r.status_code}"
        except Exception as exc:  # noqa: BLE001
            last_err = str(exc)[:120]
        print(f"   overpass unavailable ({last_err}); retrying in {wait}s")
        time.sleep(wait)
    else:
        return {"elements_total": None, "inside": [], "error": last_err,
                "note": "Overpass at capacity after 5 backoff attempts"}

    inside, total = [], 0
    for el in els:
        if el["type"] == "node":
            lon, lat = el["lon"], el["lat"]
        else:
            c = el.get("center") or {}
            if "lon" not in c:
                continue
            lon, lat = c["lon"], c["lat"]
        total += 1
        pt = gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326").to_crs(CRS).iloc[0]
        if aoi_geom.contains(pt):
            tags = el.get("tags", {})
            inside.append({
                "osm_id": f'{el["type"]}/{el["id"]}',
                "name": tags.get("name", ""),
                "tourism": tags.get("tourism", ""),
                "institutional_hint": tags.get("name", "").lower().count("hostel") > 0,
            })
    return {"elements_total": total, "inside": inside}


def main() -> int:
    aoi, district, anchor = aoi_polygon()

    reuse = "--reuse-listings" in sys.argv
    cached = PROC / "registry_uttarastays_all_2026-11-03.csv"
    if reuse and cached.exists():
        print("S1 — reusing cached crawl")
        cached_df = pd.read_csv(cached)
        stated_total = 1034
        rows = cached_df.to_dict("records")
    else:
        print("S1 — crawling uttarastays.com public listing (may take a few minutes)…")
        rows, stated_total = crawl_listings()
    df = pd.DataFrame(rows).drop_duplicates(subset=["name", "address"]).reset_index(drop=True)
    df["inside_aoi"] = df["city"].str.strip().str.lower().isin(AOI_LOCALITIES)
    df["district_dehradun"] = df["district"].str.strip().str.lower().eq("dehradun")
    df = df.sort_values(["inside_aoi", "district_dehradun", "city", "name"],
                        ascending=[False, False, True, True])
    PROC.mkdir(parents=True, exist_ok=True)
    out_csv = PROC / "registry_uttarastays_all_2026-11-03.csv"
    df.to_csv(out_csv, index=False)

    print(f"   parsed {len(df)} unique listings")

    print("S2 — Overpass query for tourism accommodation in the AOI bbox…")
    osm = overpass_facilities(aoi)
    print(f"   {osm['elements_total']} elements in bbox, {len(osm['inside'])} inside AOI")

    print("S3 — Ministry of Tourism page reachability…")
    mot = {}
    try:
        rr = requests.get(MOT_URL, headers={"User-Agent": UA}, timeout=40)
        mot = {"status": rr.status_code, "bytes": len(rr.content),
               "note": "JS-rendered shell; no state-wise list in the HTML" if rr.status_code == 200 else "unreachable"}
    except Exception as exc:  # noqa: BLE001
        mot = {"status": None, "error": str(exc)[:120]}

    aoi_km2 = round(aoi.area / 1e6, 3)
    inside = df[df.inside_aoi]
    dehradun = df[df.district_dehradun]
    aoi_names = sorted(set(inside["name"]))
    osm_names = sorted({o["name"] for o in osm["inside"] if o["name"]})
    by_type = {}
    for o in osm["inside"]:
        by_type.setdefault(o["tourism"], []).append(o["name"])
    # tourism=hostel in Mussoorie is dominated by boarding-school/college hostels;
    # they are not commercial tourism accommodation and are excluded from the
    # commercial count (reported separately, never silently dropped).
    # duplicate node/way pairs for the same business are common in OSM
    seen, osm_uniq = set(), []
    for o in osm["inside"]:
        key = (o["name"].strip().lower(), o["tourism"])
        if key in seen:
            continue
        seen.add(key)
        osm_uniq.append(o)
    commercial = [o for o in osm_uniq if o["tourism"] != "hostel"]
    overlap = sorted(set(n.strip().lower() for n in aoi_names)
                     & set(n.strip().lower() for n in osm_names))

    facts = {
        "task": "P8 / R-M1 registry reconnaissance — candidate tourism accommodation",
        "label": "feasibility counts only; no change measurement, no arm comparison, "
                 "no approval status or date inferred",
        "inferential": False,
        "pin": "docs/preplan_mussoorie.md §4.2 (written before execution)",
        "date": "2026-11-03",
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "aoi": {"rule": "8 km ring around anchor ∩ Dehradun district (M-1)",
                "anchor_4326": list(ANCHOR_4326), "crs": CRS,
                "area_km2": aoi_km2},
        "s1_uttarastays": {
            "source": LISTING_URL,
            "provenance": "Uttarakhand Tourism Development Board booking initiative",
            "listings_total_state": int(len(df)),
            "stated_total_on_site": stated_total,
            "crawl_complete": (stated_total is not None and len(df) >= stated_total),
            "district_dehradun": int(len(dehradun)),
            "inside_aoi": int(len(inside)),
            "inside_aoi_names": aoi_names,
            "aoi_share_pct": round(100.0 * len(inside) / len(df), 2) if len(df) else None,
            "membership_rule": "stated locality label in AOI_LOCALITIES; not a geocode",
            "approval_dates_published": False,
            "note": "infinite-scroll crawl; deduplicated on (name, address)",
        },
        "s2_osm_overpass": {
            "tags": OVERPASS_TAGS,
            "elements_in_bbox": osm.get("elements_total"),
            "available": osm.get("elements_total") is not None,
            "error": osm.get("error"),
            "inside_aoi": len(osm["inside"]),
            "inside_aoi_named": osm_names,
            "by_type": {k: {"count": len(v), "names": sorted(n for n in v if n)}
                        for k, v in sorted(by_type.items())},
            "commercial_count_excl_hostel": len(commercial),
            "deduplicated_total": len(osm_uniq),
            "duplicates_removed": len(osm["inside"]) - len(osm_uniq),
            "hostel_count": len(by_type.get("hostel", [])),
            "classification_note": "tourism=hostel in Mussoorie is mostly boarding-school "
                                   "and college hostels; the commercial count excludes them "
                                   "and reports them separately",
            "licence": "ODbL 1.0 (OpenStreetMap contributors)",
            "note": "presence in OSM is not approval; coverage is volunteer-dependent",
        },
        "s3_mot": mot,
        "cross_source": {
            "name_overlap": overlap,
            "overlap_count": len(overlap),
            "note": "reported, not merged — the gate counts per-source and union separately",
        },
        "gate_g_m1": {
            "threshold": 40,
            "s1_inside_aoi": int(len(inside)),
            "union_estimate": len(set(n.strip().lower() for n in aoi_names)
                                  | set(n.strip().lower() for n in osm_names)),
            "s2_commercial": len(commercial),
            "passes_on_s1": bool(len(inside) >= 40),
            "passes_on_s2_commercial": bool(len(commercial) >= 40),
            "caveat": "S1 is a booking platform, not a hotel register: hotels that "
                      "do not list there are invisible to it",
        },
        "inputs_sha256": {
            "boundary_32644": sha256(BOUNDARY),
            "listings_csv": sha256(out_csv),
        },
    }
    QA.mkdir(parents=True, exist_ok=True)
    out = QA / "p8_registry_recon_facts_2026-11-03.json"
    out.write_text(json.dumps(facts, indent=1))

    print(f"\nlistings CSV -> {out_csv.relative_to(ROOT)}")
    print(f"facts        -> {out.relative_to(ROOT)}")
    print(f"S1: {len(df)} state-wide, {len(dehradun)} Dehradun district, "
          f"{len(inside)} inside AOI ({aoi_km2} km2)")
    print(f"S2: {len(osm['inside'])} OSM facilities inside AOI")
    print(f"G-M1 (>=40 inside AOI) on S1: {'PASS' if len(inside) >= 40 else 'FAIL'}")
    print(f"hash: csv {facts['inputs_sha256']['listings_csv'][:8]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
