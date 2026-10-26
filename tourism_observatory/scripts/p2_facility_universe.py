"""P2 step (b2) — unified facility universe for treatment sourcing (§2, Wayanad).

Frozen §2 requires geocoding BOTH the approved-homestay list (M5 orders, P1 geocoded)
AND the department's accommodation registry by district (D-2 classified portal).
This script merges them into ONE deduplicated facility universe with the best
available coordinates:

  coordinate preference (logged P2 spec detail, pre-outcome):
    1. portal JSON-LD GeoCoordinates pin  → precision P1_facility_point
       (official property location published by the portal; all pins verified
       inside the district; no jitter applied)
    2. P1 round-2 geocode of the M5 address (precision classes P2–P5, unchanged)
    3. fresh ladder geocode (same engine/rules as p1_registry_geocode round 2:
       PIN-first, Nominatim+Photon, no jitter, in-district scoring) for
       classified properties that have neither a pin nor an M5 geocode

  dedupe rules (logged):
    - within D-2: same property_id (portal lists some properties twice, e.g.
      under two categories) → one facility; an accommodation category
      (Homestay/Resort/Hotel/Serviced Villa) wins over non-accommodation
    - across lists: normalized name containment (len ≥ 6) D2-name ⊂ M5
      name_address → one facility with both source flags
    - non-accommodation categories (Tour Operator / Restaurant / Ayurveda
      Centre, unless the same pid also carries an accommodation category)
      are EXCLUDED from the facility universe: §2 defines treatment as a
      "tourism accommodation facility"

Outputs:
  data/processed/facility_universe_<date>.csv   (facility_id, sources, coords,
                                                 precision, inside_district)
  outputs/qaqc/p2_facility_universe_facts.json

Usage:  python scripts/p2_facility_universe.py
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p1_registry_geocode as pg          # noqa: E402  (round-2 ladder, reused)

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
QAQC = ROOT / "outputs" / "qaqc"

ACC_CATS = {"Homestay", "Resort", "Hotel", "Serviced Villa"}
EXCL_CATS = {"Tour Operator", "Restaurant", "Ayurveda Centre"}


def clean_text(s: str) -> str:
    s = re.sub(r"<br\s*/?>", " ", str(s))
    s = re.sub(r"(Mobile|Phone)\s*:\s*[^,<]+", " ", s)
    s = re.sub(r"<[^>]+>", " ", s)
    return " ".join(s.split()).strip(" ,")


def norm_name(s: str) -> str:
    s = str(s).lower()
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(r"\b(wayanad|kerala|p o|po|post)\b", " ", s)
    return " ".join(s.split())


def main() -> int:
    cls = pd.read_csv(PROC / "registry_classified_wayanad_2026-10-23.csv")
    details = json.load(open(PROC / "classified_details_2026-10-23.json"))
    m5 = pd.read_csv(PROC / "registry_homestays_wayanad_2026-10-22.csv")
    m5g = pd.read_csv(PROC / "registry_geocoded_2026-10-23.csv")

    # ---- D-2: dedupe by property_id, keep accommodation preference ----------
    cls["name_clean"] = cls["name"].map(clean_text)
    cls["acc"] = cls.category.isin(ACC_CATS)
    rows = []
    for pid, g in cls.groupby("property_id", sort=True):
        acc = g[g.acc] if g.acc.any() else g
        r = acc.iloc[0]
        det = details.get(str(pid), {})
        geo = det.get("geo") or {}
        rows.append({
            "d2_pid": pid, "d2_name": r["name_clean"],
            "d2_category": r["category"],
            "d2_is_accommodation": bool(g.acc.any()),
            "d2_name_address": clean_text(r["name_address"]),
            "d2_pin_lat": float(geo["latitude"]) if geo else None,
            "d2_pin_lon": float(geo["longitude"]) if geo else None,
            "d2_detail_ok": bool(det.get("detail_ok")),
            "d2_postal": det.get("postalCode"),
        })
    d2 = pd.DataFrame(rows)
    acc_d2 = d2[d2.d2_is_accommodation]
    print(f"D-2 cards {len(cls)} → unique properties {len(d2)}; "
          f"accommodation {len(acc_d2)} (excluded non-accommodation "
          f"{len(d2) - len(acc_d2)})")

    # ---- cross-list dedupe: normalized name containment ---------------------
    m5g["nname"] = m5g.name_address.map(norm_name)
    acc_d2 = acc_d2.copy()
    acc_d2["m5_match"] = None
    m5_matched: set[int] = set()
    for i, r in acc_d2.iterrows():
        nn = norm_name(r.d2_name)
        if len(nn) < 6:
            continue
        for _, m in m5g.iterrows():
            if m.sl in m5_matched:
                continue
            if nn in m.nname or (len(m.nname) >= 10 and m.nname in nn):
                acc_d2.at[i, "m5_match"] = int(m.sl)
                m5_matched.add(int(m.sl))
                break
    n_match = int(acc_d2.m5_match.notna().sum())
    print(f"cross-list name matches: {n_match} (of {len(acc_d2)} D-2 accom, "
          f"{len(m5g)} M5)")

    # ---- ladder-geocode D-2 accommodation properties with no pin & no M5 ----
    aoi = gpd.read_file(PROC / "wayanad_boundary_32643.geojson")
    aoi_ll = aoi if str(aoi.crs) == "EPSG:4326" else aoi.to_crs("EPSG:4326")
    aoi_geom = aoi_ll.geometry.iloc[0]
    need = acc_d2[(acc_d2.d2_pin_lat.isna()) & (acc_d2.m5_match.isna())]
    print(f"ladder-geocoding {len(need)} D-2 properties (no pin, no M5 match)")
    ladder = {}
    import time as _t
    STOP = {"wayanad", "kerala", "post", "mobile", "phone", "resort", "resorts",
            "homestay", "homes", "villa", "hotel", "enterprises", "limited",
            "plantation", "holiday", "holidays", "peak", "valley", "spring",
            "p", "opo", "eachome", "malankara"}          # noqa: E501 (seed stoplist)
    for _, r in need.iterrows():
        row = pd.Series({"name_address": f"{r.d2_name}, {r.d2_name_address}"})
        plan = pg.query_plan(row)
        district_run = plan.pop()                          # keep district as LAST rung
        # extra rungs: locality tokens lifted from the address string itself
        toks = []
        for t in re.split(r"[^A-Za-z]+", str(r.d2_name_address)):
            tl = t.lower()
            if len(tl) >= 5 and tl not in STOP and tl not in toks and tl != norm_name(r.d2_name):
                toks.append(tl)
        for tok in toks[:4]:
            plan.append(("nominatim_token", "nominatim",
                         {"q": f"{tok}, Wayanad, Kerala, India", "format": "jsonv2",
                          "limit": 3, "addressdetails": 1}))
            plan.append(("photon_token", "photon", {"q": f"{tok}, Wayanad", "limit": 3}))
        plan.append(district_run)
        best, best_score = None, None
        for label, engine, params in plan:
            res = pg.http_get(pg.PHOTON if engine == "photon" else pg.NOMINATIM,
                              params, engine)
            _t.sleep(pg.PHOTON_SLEEP if engine == "photon" else pg.NOM_SLEEP)
            items = res if isinstance(res, list) else []
            for item in items[:3]:
                cand = pg.to_candidate(label, engine, item, None,
                                       pg.extract_locality(str(row.name_address)))
                if cand is None:
                    continue
                pt = Point(cand["lon"], cand["lat"])
                cand["inside_district"] = bool(pt.within(aoi_geom))
                score = (int(cand["inside_district"]),
                         int("wayanad" in cand["display_name"].lower()),
                         -pg.rank(cand["precision_class"]))
                if best_score is None or score > best_score:
                    best, best_score = cand, score
            if best is not None and best["inside_district"] and \
                    pg.rank(best["precision_class"]) <= 2:
                break
        ladder[r.d2_pid] = best
        print(f"  {r.d2_pid} {r.d2_name[:40]!r} → "
              f"{best['precision_class'] if best else 'FAIL'} "
              f"({best['via'] if best else '-'})")
        _t.sleep(pg.NOM_SLEEP)

    # ---- assemble universe ---------------------------------------------------
    m5g_idx = m5g.set_index("sl")
    facs = []
    fid = 0
    # A: D-2 accommodation properties (each once)
    for _, r in acc_d2.iterrows():
        fid += 1
        if r.d2_pin_lat == r.d2_pin_lat and r.d2_pin_lat is not None:
            lat, lon, pc, src = r.d2_pin_lat, r.d2_pin_lon, "P1_facility_point", "d2_pin"
            via = "portal_geojson_pin"
        elif r.m5_match == r.m5_match and r.m5_match is not None:
            m = m5g_idx.loc[int(r.m5_match)]
            lat, lon, pc, src = m.lat, m.lon, m.precision_class, "m5_geocode"
            via = m.matched_via
        elif r.d2_pid in ladder and ladder[r.d2_pid]:
            c = ladder[r.d2_pid]
            lat, lon, pc, src = c["lat"], c["lon"], c["precision_class"], "d2_ladder"
            via = c["via"]
        else:
            lat = lon = pc = None
            src, via = "unresolved", None
        facs.append({
            "facility_id": f"F{fid:03d}",
            "sources": ("d2+m5" if r.m5_match == r.m5_match and r.m5_match == r.m5_match
                        and pd.notna(r.m5_match) else "d2"),
            "d2_pid": r.d2_pid, "m5_sl": (int(r.m5_match) if pd.notna(r.m5_match) else None),
            "name": r.d2_name, "d2_category": r.d2_category,
            "coord_source": src, "precision_class": pc, "matched_via": via,
            "lat": lat, "lon": lon,
        })
    # B: M5 facilities with no D-2 twin
    for _, m in m5g[~m5g.sl.isin(m5_matched)].iterrows():
        fid += 1
        facs.append({
            "facility_id": f"F{fid:03d}", "sources": "m5",
            "d2_pid": None, "m5_sl": int(m.sl),
            "name": m.name_address[:70], "d2_category": "homestay_approved",
            "coord_source": "m5_geocode", "precision_class": m.precision_class,
            "matched_via": m.matched_via, "lat": m.lat, "lon": m.lon,
        })
    univ = pd.DataFrame(facs)
    univ["inside_district"] = [
        bool(Point(x, y).within(aoi_geom)) if pd.notna(x) else None
        for x, y in zip(univ.lon, univ.lat)]

    # collision note: two facility_ids at identical coords?
    shared = univ.dropna(subset=["lat"]).groupby(["lat", "lon"]).size()
    n_shared = int((shared > 1).sum())

    today = date.today().isoformat()
    out = PROC / f"facility_universe_{today}.csv"
    univ.to_csv(out, index=False)
    facts = {
        "date": today,
        "d2_cards": int(len(cls)), "d2_unique_properties": int(len(d2)),
        "d2_accommodation": int(len(acc_d2)),
        "d2_excluded_non_accommodation": int(len(d2) - len(acc_d2)),
        "cross_list_matches": n_match,
        "m5_total": int(len(m5g)), "m5_unmatched": int(len(m5g) - n_match),
        "facility_universe": int(len(univ)),
        "coord_sources": univ.coord_source.value_counts().to_dict(),
        "precision_classes": univ.precision_class.value_counts().to_dict(),
        "inside_district": int((univ.inside_district == True).sum()),  # noqa: E712
        "unresolved": int(univ.lat.isna().sum()),
        "shared_coord_groups": n_shared,
        "note": ("Coordinate preference: portal pin (official property geo) > "
                 "P1 r2 M5 geocode > fresh PIN-first ladder; no jitter. "
                 "Non-accommodation service providers excluded (§2 facility = "
                 "tourism accommodation). Existence verification at the FINAL "
                 "coordinate follows (separate step)."),
    }
    QAQC.mkdir(parents=True, exist_ok=True)
    (QAQC / "p2_facility_universe_facts.json").write_text(
        json.dumps(facts, indent=1) + "\n")
    print("\n" + json.dumps(facts, indent=1))
    print(f"csv: {out.relative_to(ROOT)}")
    if univ.lat.isna().any():
        print("WARN: unresolved facilities:",
              univ[univ.lat.isna()][["facility_id", "name"]].to_dict("records"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
