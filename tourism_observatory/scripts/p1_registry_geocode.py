"""P1 registry geocoding, round 2 — Wayanad approved homestays.

Permitted pre-freeze work: "registry geocoding, facility-existence verification"
(prereg §5). No construction dating, no control comparison, no outcome maps.

Round 1 (archived: outputs/qaqc/geocode_log_r1.json) resolved 51/51 but 43 of
them only to P5 (district centroid) because full-address queries failed on the
registry's messy strings. Round 2 changes the QUERY LADDER, not the honesty
rules:

  1. PIN-code structured query (Indian PINs are in most rows; resolve to the
     post office = village-level placement)
  2. PIN as free text with district context
  3. full address with district context
  4. known Wayanad town/taluk extracted from the string
  5. Photon (Komoot) cross-check for PIN and town
  6. district_only — LAST resort, always classed P5

Candidates are scored: in-district > Wayanad-labelled > finer precision >
earlier query. Precision classes cap the claim (P3/P5 are locality-level;
facility-exact placement is the separate imagery existence-verification step).
No point is jittered.

Outputs (same names as round 1; round-1 raw/log archived with _r1 suffix):
  data/processed/registry_geocoded_<date>.csv / .geojson
  data/processed/geocode_raw_<date>.json
  outputs/qaqc/geocode_log.json      (audit-D-1 success-rate log)

Usage:  python scripts/p1_registry_geocode.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import date
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import Point, shape

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
BOUNDARY = PROC / "wayanad_boundary_32643.geojson"
REGISTRY = PROC / "registry_homestays_wayanad_2026-10-22.csv"

UA = {"User-Agent": "tourism-observatory-p1/0.1 (research geocoding; non-commercial)"}
NOMINATIM = "https://nominatim.openstreetmap.org/search"
PHOTON = "https://photon.komoot.io/api/"
NOM_SLEEP = 1.05          # Nominatim usage policy: max 1 req/s
PHOTON_SLEEP = 0.5

PRECISION_ORDER = ["P1_facility_point", "P2_street", "P3_village",
                   "P4_town_city", "P5_district_or_coarser"]

POINT_TYPES = {"house", "building", "dwelling", "bungalow", "hotel", "chalet",
               "guest_house", "hostel", "apartment", "farm", "tourism",
               "attraction", "camp_site", "motel", "yes", "housenumber"}
STREET_TYPES = {"highway", "road", "street", "path", "residential", "service",
                "footway", "steps", "track", "cycleway", "pedestrian"}
VILLAGE_TYPES = {"village", "hamlet", "locality", "neighbourhood", "suburb",
                 "quarter", "isolated_dwelling", "populated_place"}
TOWN_TYPES = {"town", "city", "municipality", "county", "district"}

# Wayanad taluk HQs + known localities/hamlets appearing in registry addresses.
WAYANAD_TOWNS = [
    "sulthan bathery", "sultan bathery", "mananthavady", "mananthavadi",
    "mananthawadi", "kalpetta", "vythiri", "meppadi", "panamaram", "pulpally",
    "adivaram", "ambalavayal", "chundale", "meenangadi", "karapuzha",
    "vellarimala", "muppainad", "kaniyambetta", "thekkumbad", "kottathara",
    "anjarakandy", "bavali", "thrissileri", "niravilppu", "makkiyad",
    "thonnernad", "kanjirangad", "paramikavu", "chembra", "nilambur",
]


def precision_from_nominatim(res: dict) -> str:
    cls = (res.get("class") or "").lower()
    typ = (res.get("type") or "").lower()
    at = (res.get("addresstype") or "").lower()
    key = at or typ
    if key in POINT_TYPES or (cls in {"building", "tourism", "amenity", "leisure"}
                              and typ in POINT_TYPES):
        return "P1_facility_point"
    if typ in STREET_TYPES or cls == "highway":
        return "P2_street"
    if key in VILLAGE_TYPES or typ in VILLAGE_TYPES:
        return "P3_village"
    if key in TOWN_TYPES or typ in TOWN_TYPES:
        return "P4_town_city"
    return "P5_district_or_coarser"


def precision_from_photon(props: dict) -> str:
    if props.get("housenumber"):
        return "P1_facility_point"
    if props.get("street"):
        return "P2_street"
    if any(props.get(k) for k in ("village", "hamlet", "neighbourhood", "suburb")):
        return "P3_village"
    if any(props.get(k) for k in ("city", "town")):
        return "P4_town_city"
    return "P5_district_or_coarser"


def rank(pcls: str) -> int:
    return PRECISION_ORDER.index(pcls)


def extract_pin(txt: str) -> str | None:
    m = re.search(r"\b(6[0-9]{5})\b", txt)
    return m.group(1) if m else None


def extract_locality(txt: str) -> str | None:
    low = txt.lower()
    for t in sorted(WAYANAD_TOWNS, key=len, reverse=True):
        if t in low:
            return t
    return None


def http_get(url: str, params: dict, engine: str) -> list | dict:
    for attempt in range(1, 4):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=30)
            if r.status_code == 429:
                time.sleep(5 * attempt)
                continue
            r.raise_for_status()
            data = r.json()
            if engine == "photon":
                return data.get("features", [])
            return data
        except requests.RequestException as e:
            print(f"      {engine} error: {e}; retry {attempt}/3", flush=True)
            time.sleep(3 * attempt)
    return []


def query_plan(row: pd.Series) -> list[tuple[str, str, dict]]:
    """(label, engine, params) — ordered, most likely to resolve fine first."""
    txt = " ".join(str(row["name_address"]).split())
    pin = extract_pin(txt)
    loc = extract_locality(txt)
    plan: list[tuple[str, str, dict]] = []
    if pin:
        plan.append(("nominatim_pin", "nominatim",
                     {"postalcode": pin, "state": "Kerala", "country": "India",
                      "format": "jsonv2", "limit": 3, "addressdetails": 1}))
        plan.append(("nominatim_pin_text", "nominatim",
                     {"q": f"{pin}, Wayanad, Kerala, India", "format": "jsonv2",
                      "limit": 3, "addressdetails": 1}))
    plan.append(("nominatim_full", "nominatim",
                 {"q": f"{txt}, Wayanad, Kerala, India", "format": "jsonv2",
                  "limit": 3, "addressdetails": 1}))
    if loc and loc not in txt.lower()[:0]:      # locality present by definition
        plan.append(("nominatim_locality", "nominatim",
                     {"q": f"{loc}, Wayanad, Kerala, India", "format": "jsonv2",
                      "limit": 3, "addressdetails": 1}))
    if pin:
        plan.append(("photon_pin", "photon", {"q": pin, "limit": 3}))
    if loc:
        plan.append(("photon_locality", "photon",
                     {"q": f"{loc}, Wayanad, Kerala"}))
    plan.append(("nominatim_district", "nominatim",
                 {"q": "Wayanad, Kerala, India", "format": "jsonv2",
                  "limit": 3, "addressdetails": 1}))
    return plan


def to_candidate(label: str, engine: str, item: dict, pin: str | None,
                 loc: str | None) -> dict | None:
    if engine == "photon":
        props = item.get("properties", {})
        lon, lat = item["geometry"]["coordinates"][:2]
        name_bits = [props.get(k) for k in ("name", "street", "city", "village",
                                            "county", "state") if props.get(k)]
        display = ", ".join(str(b) for b in name_bits)
        return {"engine": "photon", "via": label, "lat": float(lat),
                "lon": float(lon), "display_name": display,
                "precision_class": precision_from_photon(props),
                "osm_type": props.get("osm_type"), "osm_id": props.get("osm_id"),
                "raw_type": str(props.get("type") or "")}
    lat, lon = float(item["lat"]), float(item["lon"])
    return {"engine": "nominatim", "via": label, "lat": lat, "lon": lon,
            "display_name": item.get("display_name") or "",
            "precision_class": precision_from_nominatim(item),
            "osm_type": item.get("osm_type"), "osm_id": item.get("osm_id"),
            "raw_type": f"{item.get('class')}/{item.get('type')}"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    for p in (REGISTRY, BOUNDARY):
        if not p.exists():
            print(f"FAIL: missing input {p}")
            return 1
    df = pd.read_csv(REGISTRY)
    if len(df) != 51:
        print(f"FAIL: registry rows {len(df)} != 51")
        return 1

    aoi = gpd.read_file(BOUNDARY)
    aoi_ll = aoi if str(aoi.crs) == "EPSG:4326" else aoi.to_crs("EPSG:4326")
    aoi_geom = aoi_ll.geometry.iloc[0]
    aoi_m = aoi if str(aoi.crs) == "EPSG:32643" else aoi.to_crs("EPSG:32643")

    if args.dry_run:
        for _, row in df.iterrows():
            pin = extract_pin(str(row["name_address"]))
            loc = extract_locality(str(row["name_address"]))
            print(f"{row['sl']:>4} pin={pin} loc={loc}  {str(row['name_address'])[:60]!r}")
        return 0

    today = date.today().isoformat()
    records, raw_log = [], []
    stats = {"total": int(len(df)), "round": 2, "geocoded_any": 0,
             "inside_district": 0, "by_precision": {}, "by_engine": {},
             "by_query": {}, "failures": [], "shared_coordinate_groups": 0}

    for i, row in df.iterrows():
        sl = int(row["sl"])
        txt = " ".join(str(row["name_address"]).split())
        pin, loc = extract_pin(txt), extract_locality(txt)
        plan = query_plan(row)
        print(f"[{i+1}/51] sl={sl} pin={pin} loc={loc} ({len(plan)} queries)",
              flush=True)

        best = None
        best_score = None
        tried: list[dict] = []
        for label, engine, params in plan:
            res = http_get(PHOTON if engine == "photon" else NOMINATIM,
                           params, engine)
            time.sleep(PHOTON_SLEEP if engine == "photon" else NOM_SLEEP)
            items = res if isinstance(res, list) else []
            tried.append({"via": label, "n": len(items)})
            for item in items[:3]:
                cand = to_candidate(label, engine, item, pin, loc)
                if cand is None:
                    continue
                pt = Point(cand["lon"], cand["lat"])
                cand["inside_district"] = bool(pt.within(aoi_geom))
                # score: in-district, Wayanad-labelled, finer precision, earlier query
                qrank = [t[0] for t in plan].index(label)
                score = (int(cand["inside_district"]),
                         int("wayanad" in cand["display_name"].lower()),
                         -rank(cand["precision_class"]), -qrank)
                cand["score"] = list(score)
                if best_score is None or score > best_score:
                    best, best_score = cand, score
            # early stop: in-district village-level or better already found
            if best is not None and best["inside_district"] and \
                    rank(best["precision_class"]) <= 2:
                break
            # early stop: any in-district P4 that is a Wayanad label (diminishing
            # returns once two in-district candidates exist and plan is long)
            if best is not None and best["inside_district"] and qrank >= 4:
                break

        raw_log.append({"sl": sl, "name_address": txt, "pin": pin,
                        "locality": loc, "queries": tried,
                        "chosen_via": best["via"] if best else None})

        rec = row.to_dict()
        rec["pin"] = pin
        rec["locality"] = loc
        if best is None:
            rec.update({"lat": None, "lon": None, "precision_class": None,
                        "display_name": None, "matched_via": None,
                        "engine": None, "inside_district": None,
                        "distance_to_aoi_m": None})
            stats["failures"].append({"sl": sl, "name": txt[:70]})
        else:
            inside = best["inside_district"]
            if inside:
                dist = 0.0
            else:
                pt_m = gpd.GeoSeries([Point(best["lon"], best["lat"])],
                                     crs="EPSG:4326").to_crs("EPSG:32643")
                dist = float(pt_m.distance(aoi_m.geometry.iloc[0]).iloc[0])
            rec.update({
                "lat": best["lat"], "lon": best["lon"],
                "precision_class": best["precision_class"],
                "display_name": best["display_name"],
                "osm_type": best["osm_type"], "osm_id": best["osm_id"],
                "matched_via": best["via"], "engine": best["engine"],
                "inside_district": inside,
                "distance_to_aoi_m": round(dist, 1)})
            stats["geocoded_any"] += 1
            stats["inside_district"] += int(inside)
            pc = best["precision_class"]
            stats["by_precision"][pc] = stats["by_precision"].get(pc, 0) + 1
            stats["by_engine"][best["engine"]] = stats["by_engine"].get(best["engine"], 0) + 1
            stats["by_query"][best["via"]] = stats["by_query"].get(best["via"], 0) + 1
        records.append(rec)

    out = pd.DataFrame(records)
    csv_path = PROC / f"registry_geocoded_{today}.csv"
    out.to_csv(csv_path, index=False)

    geo_rows = out[out["lat"].notna()].drop(columns=["contact"], errors="ignore")
    gdf = gpd.GeoDataFrame(
        geo_rows,
        geometry=[Point(xy) for xy in zip(geo_rows["lon"], geo_rows["lat"])],
        crs="EPSG:4326")
    geo_path = PROC / f"registry_geocoded_{today}.geojson"
    if geo_path.exists():
        geo_path.unlink()
    gdf.to_file(geo_path, driver="GeoJSON")
    (PROC / f"geocode_raw_{today}.json").write_text(json.dumps(raw_log, indent=1))

    dup = (out[out["lat"].notna()].groupby(["lat", "lon"]).size()
           .reset_index(name="n"))
    shared = dup[dup["n"] > 1]
    stats["shared_coordinate_groups"] = int(len(shared))
    stats["shared_coordinate_facilities"] = int(shared["n"].sum()) if len(shared) else 0
    stats["geocode_rate_pct"] = round(100 * stats["geocoded_any"] / stats["total"], 1)
    stats["inside_rate_pct"] = round(
        100 * stats["inside_district"] / max(stats["geocoded_any"], 1), 1)
    stats["fine_pct"] = round(100 * sum(
        v for k, v in stats["by_precision"].items()
        if k in PRECISION_ORDER[:3]) / max(stats["geocoded_any"], 1), 1)
    stats["date"] = today
    stats["source_registry"] = REGISTRY.name
    stats["round1_archive"] = "outputs/qaqc/geocode_log_r1.json"
    stats["note"] = ("Precision classes cap the claim: P3/P5 are locality-level "
                     "placements, NOT facility-exact coordinates. Facility-exact "
                     "placement is the separate imagery existence-verification "
                     "step. No point is jittered. Construction dating forbidden "
                     "(prereg §5).")

    log_dir = ROOT / "outputs" / "qaqc"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "geocode_log.json"
    log_path.write_text(json.dumps(stats, indent=1) + "\n")

    print("\nGeocoding summary round 2 (audit-D-1 success-rate log):")
    print(json.dumps(stats, indent=1))
    print(f"csv   : {csv_path.relative_to(ROOT)}")
    print(f"geojson: {geo_path.relative_to(ROOT)} ({len(gdf)} points)")
    print(f"log   : {log_path.relative_to(ROOT)}")
    if stats["geocoded_any"] == 0:
        print("FAIL: zero facilities geocoded")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
