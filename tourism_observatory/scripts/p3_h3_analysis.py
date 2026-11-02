#!/usr/bin/env python3
"""P3 H3 — HEC association: descriptive hotspot-overlap (D-3 fallback + D-18 pins).

The R1 gate (audit-D-10, pre-freeze) established the Morrison et al. (2025,
GECCO 62:e03742) records never contained GPS coordinates (village-name
level), so the D-3-registered downgrade is active: descriptive KDE-percentile
overlap ONLY — no Poisson/NB, no IRR table, no residual Moran's I. The exact
recipe was pinned in prereg §7 D-18 before any H3 statistic (freeze R7d):

  1. Screen the Figshare workbook (dates, nature, species, ranges); drop and
     count unparseable/out-of-window rows; elephant subset reported.
  2. Geocode place names (Nominatim, district viewbox, cached; precision
     tiers place -> section -> range-centroid; unmatched excluded + counted).
  3. Incident surface: weighted Gaussian KDE (sigma = 1000 m) on the H3
     500 m grid inside the district (outside-WDPA sensitivity reported).
  4. Covariates (pre-2011 only as primary): Hansen-2000 forest-edge density
     + forest-cover share, CCI-2005 cropland/urban share, Hansen 2000-2010
     loss share, OSM road density (vintage-caveated), DEM elevation,
     facility count within 1 km (tourism, tested covariate); GLAD 2000-2020
     built-up gain only as labelled-leaky secondary; rainfall unavailable.
  5. Overlap = mean/median covariate percentile at incident-KDE top-decile
     cells + Spearman rho between percentile surfaces (descriptive effect
     sizes; no p-values, no CIs, no coefficient claims).
  6. V2 direction check vs the paper's stated drivers (qualitative).

Outputs:
  data/processed/h3_place_geocodes_{date}.csv   (geocode cache; manifest entry)
  outputs/qaqc/p3_h3_facts_{date}.json
"""
import json
import math
import sys
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from shapely.geometry import box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
RAW, PROC, QA = ROOT / "data/raw", ROOT / "data/processed", ROOT / "outputs/qaqc"
TODAY = date.today().isoformat()

STAGING = RAW / "staging_h3/Original_records_sensitive_data_removed_including_namesandaddress.xlsx"
# Cache filename pinned verbatim in prereg §7 D-18 (freeze R7d); the run
# started 2026-10-28, was interrupted by a host restart, and resumes from
# this same file.
GEOCODES = PROC / "h3_place_geocodes_2026-10-28.csv"
FACTS = QA / f"p3_h3_facts_{TODAY}.json"

WINDOW = (pd.Timestamp("2011-01-01"), pd.Timestamp("2014-12-31"))
DISTRICT = RAW / "geoBoundaries-IND-ADM2_simplified.geojson"
GRID_M = 500.0
SIGMA_M = 1000.0
CCI_CROPLAND = {10, 11, 12, 20, 30}
CCI_URBAN = 190
HANSEN_FOREST_PCT = 30
NM = "https://nominatim.openstreetmap.org/search"
VIEWBOX = "75.70,11.40,76.50,12.02"  # district + pad
UA = {"User-Agent": "tourism-observatory-research (academic reproducibility)"}


def norm(s):
    return s.astype(str).str.strip().str.replace(r"\s+", " ", regex=True).fillna("")


def classify_nature(v):
    v = str(v).lower()
    if "crop" in v:
        return "crop"
    if "cattle" in v:
        return "cattle"
    if "attack" in v:
        return "attack"
    if "damage" in v:
        return "property"
    return "other_nil"


def screen():
    xl = pd.ExcelFile(STAGING)
    rows = []
    raw_rows, no_place = {}, []
    for sheet in xl.sheet_names:
        df = xl.parse(sheet)
        df.columns = [str(c).strip() for c in df.columns]
        raw_rows[sheet] = len(df)
        if "Place" in df.columns:
            place = norm(df["Place"])
        else:
            place = pd.Series([""] * len(df))
            no_place.append(sheet)
        d = pd.DataFrame({
            "sheet": sheet,
            "place": place,
            "range": norm(df["Range"]) if "Range" in df.columns else "",
            "section": norm(df["Section"]) if "Section" in df.columns else "",
            "nature_raw": norm(df["Nature of Lost"]) if "Nature of Lost" in df.columns else "",
            "species_raw": norm(df[[c for c in df.columns
                                    if "pecies" in c or "naimal" in c][0]])
            if any("pecies" in c or "naimal" in c for c in df.columns) else "",
            "date_raw": df["Date of occurance"] if "Date of occurance" in df.columns else pd.NaT,
        })
        rows.append(d)
    rec = pd.concat(rows, ignore_index=True)
    rec["date"] = pd.to_datetime(rec["date_raw"], errors="coerce")
    n_total = len(rec)
    n_unparsed = int(rec["date"].isna().sum())
    in_win = rec["date"].between(*WINDOW)
    n_oow = int((rec["date"].notna() & ~in_win).sum())
    rec = rec[in_win].copy()
    rec["nature"] = rec["nature_raw"].map(classify_nature)
    sp = rec["species_raw"].str.upper()
    # na=False: missing species -> not-elephant (not NA), so the downstream
    # boolean mask has no NaN (pandas rejects NA masks)
    rec["elephant"] = sp.str.contains("ELP|ELEPHANT", na=False)
    rec["range"] = rec["range"].replace({"Kurichyat": "Kurichiat", "Nil": ""})
    facts = {
        "sheets_row_counts": raw_rows,
        "parsed_rows": n_total,
        "dropped_unparseable_date": n_unparsed,
        "dropped_out_of_window_2011_2014": n_oow,
        "kept_rows": int(len(rec)),
        "date_range_kept": [str(rec.date.min())[:10], str(rec.date.max())[:10]],
        "nature_counts": rec["nature"].value_counts().to_dict(),
        "species_top": sp.value_counts().head(10).to_dict(),
        "elephant_rows": int(rec["elephant"].sum()),
        "unique_places": int(rec[rec.place != ""].place.nunique()),
        "unique_sections": int(rec[rec.section != ""].section.nunique()),
        "ranges": sorted(rec[rec["range"] != ""]["range"].unique().tolist()),
        "place_column_absent_sheets": no_place,
    }
    return rec, facts


def nm_query(name):
    params = urllib.parse.urlencode({
        "q": f"{name}, Wayanad, Kerala, India", "format": "json",
        "limit": 1, "viewbox": VIEWBOX, "bounded": "1"})
    req = urllib.request.Request(NM + "?" + params, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        out = json.loads(r.read().decode())
    return (float(out[0]["lat"]), float(out[0]["lon"]), out[0]["display_name"]) if out else None


def geocode(rec):
    cache = {}
    if GEOCODES.exists():
        c = pd.read_csv(GEOCODES)
        for _, r in c.iterrows():
            cache[(r["name"], r["tier"])] = (r.lat, r.lon, int(r.matched),
                                             str(r.display_name))
    todo = [("place", n) for n in sorted(rec.loc[rec.place != "", "place"].unique())]
    todo += [("section", n) for n in sorted(rec.loc[rec.section != "", "section"].unique())]
    todo = [t for t in todo if (t[1], t[0]) not in cache]
    rows = []
    for i, (tier, name) in enumerate(todo, 1):
        try:
            res = nm_query(name)
        except Exception:  # noqa: BLE001 - network
            res = None
            time.sleep(3)
        time.sleep(1.05)
        val = (res[0], res[1], 1, res[2]) if res else (np.nan, np.nan, 0, "")
        cache[(name, tier)] = val
        rows.append({"name": name, "tier": tier, "lat": val[0], "lon": val[1],
                     "matched": val[2], "display_name": val[3]})
        if i % 25 == 0:
            # always flush the FULL cache so an interruption cannot lose
            # previously-cached rows
            _write_cache(cache)
            print(f"  geocoded {i}/{len(todo)} new names", flush=True)
    return _write_cache(cache)


def _write_cache(cache):
    geo = pd.DataFrame([{"name": n, "tier": t, "lat": v[0], "lon": v[1],
                         "matched": v[2], "display_name": v[3]}
                        for (n, t), v in cache.items()])
    geo.to_csv(GEOCODES, index=False)
    return geo


def assign_points(rec, geo):
    lookup = {(r["name"], r.tier): (r.lat, r.lon)
              for _, r in geo.iterrows() if r.matched == 1}
    tmp = rec.merge(geo[(geo.tier == "place") & (geo.matched == 1)]
                    [["name", "lat", "lon"]],
                    left_on="place", right_on="name", how="left")
    rc = tmp[tmp.lat.notna()].groupby("range")[["lat", "lon"]].median().to_dict("index")

    def point(row):
        p = lookup.get((row.place, "place"))
        if p:
            return (*p, "place")
        p = lookup.get((row.section, "section"))
        if p:
            return (*p, "section")
        r = rc.get(row["range"])
        if r is not None:
            return (r["lat"], r["lon"], "range")
        return (np.nan, np.nan, "none")

    pts = rec.apply(point, axis=1, result_type="expand")
    pts.columns = ["lat", "lon", "tier"]
    # reset BOTH frames' indices: rec's index is gappy after the date-window
    # filter, and concat(axis=1) aligns on index labels — without this the
    # frames misalign and inject NaN rows (object-dtype boolean column).
    return pd.concat([rec.reset_index(drop=True), pts.reset_index(drop=True)],
                     axis=1)


class CellIndex:
    """Vectorized 30/300 m pixel -> 500 m retained-cell serial mapping."""

    def __init__(self, district, out_shape=None):
        minx, miny, maxx, maxy = district.bounds
        self.x0 = math.floor(minx / GRID_M) * GRID_M
        self.y0 = math.floor(miny / GRID_M) * GRID_M
        self.nx = int(math.ceil((maxx - self.x0) / GRID_M))
        self.ny = int(math.ceil((maxy - self.y0) / GRID_M))
        xs = self.x0 + (np.arange(self.nx) + 0.5) * GRID_M
        ys = self.y0 + (np.arange(self.ny) + 0.5) * GRID_M
        XX, YY = np.meshgrid(xs, ys)
        centres = gpd.GeoSeries(gpd.points_from_xy(XX.ravel(), YY.ravel()),
                                crs="EPSG:32643")
        inside = centres.within(district).to_numpy()
        self.centres = centres[inside]
        self.lut = np.full((self.ny, self.nx), -1, dtype=np.int64)
        iys, ixs = np.nonzero(inside.reshape(self.ny, self.nx))
        self.lut[iys, ixs] = np.arange(len(iys))
        self.ix_of = inside.reshape(self.ny, self.nx)

    @property
    def n(self):
        return len(self.centres)

    def __call__(self, xs, ys):
        ix = ((xs - self.x0) / GRID_M).astype(np.int64)
        iy = ((ys - self.y0) / GRID_M).astype(np.int64)
        ok = (ix >= 0) & (ix < self.nx) & (iy >= 0) & (iy < self.ny)
        out = np.full(ix.shape, -1, dtype=np.int64)
        out[ok] = self.lut[iy[ok], ix[ok]]
        return out


def aggregate(path, idx_fn, n_cells, mode):
    with rasterio.open(path) as s:
        a = s.read(1)
        t = s.transform
        nod = s.nodata
    h, w = a.shape
    rows, cols = np.mgrid[0:h, 0:w]
    xs = (t.c + (cols + 0.5) * t.a).ravel()
    ys = (t.f + (rows + 0.5) * t.e).ravel()
    ii = idx_fn(xs, ys)
    valid = (a.ravel() != nod) if nod is not None else np.ones(a.size, bool)
    ok = (ii >= 0) & valid
    vi, ci = a.ravel()[ok].astype(float), ii[ok]
    if mode == "mean":
        out = np.bincount(ci, weights=vi, minlength=n_cells)
        cnt = np.bincount(ci, minlength=n_cells)
        return np.where(cnt > 0, out / np.maximum(cnt, 1), np.nan)
    if mode == "max":
        out = np.full(n_cells, -np.inf)
        np.maximum.at(out, ci, vi)
        out[out == -np.inf] = np.nan
        return out
    raise ValueError(mode)


def main():
    adm = gpd.read_file(DISTRICT)
    adm = adm[adm.shapeName.str.contains("Wayanad", case=False, na=False)]
    district = unary_union(adm.to_crs("EPSG:32643").geometry)

    # ---- stage 1: screen ----
    rec, sfacts = screen()
    print(f"screen: kept {sfacts['kept_rows']}/{sfacts['parsed_rows']} rows "
          f"(dropped: {sfacts['dropped_unparseable_date']} unparsed, "
          f"{sfacts['dropped_out_of_window_2011_2014']} out-of-window)")

    # ---- stage 2: geocode ----
    geo = geocode(rec)
    pts = assign_points(rec, geo)
    placed = pts[pts.tier != "none"].copy()
    n_none = int((pts.tier == "none").sum())
    print(f"points: placed {len(placed)}/{len(pts)} (unplaced {n_none}); "
          f"tiers {placed.tier.value_counts().to_dict()}")

    # ---- stage 3: grid + incident KDE ----
    ci = CellIndex(district)
    n = ci.n
    cx = ci.centres.x.to_numpy()
    cy = ci.centres.y.to_numpy()

    def kde_surface(mask):
        sub = placed[mask]
        agg = sub.groupby(["lat", "lon"]).size().reset_index(name="w")
        px = gpd.GeoSeries(gpd.points_from_xy(agg.lon, agg.lat), crs="EPSG:4326"
                           ).to_crs("EPSG:32643")
        d2 = ((cx[:, None] - px.x.to_numpy()[None, :]) ** 2 +
              (cy[:, None] - px.y.to_numpy()[None, :]) ** 2)
        k = (agg.w.to_numpy()[None, :] * np.exp(-d2 / (2 * SIGMA_M ** 2))).sum(1)
        return pd.Series(k).rank(pct=True).to_numpy(), len(sub)

    kde_all, n_all = kde_surface(np.ones(len(placed), dtype=bool))
    kde_elp, n_elp = kde_surface(placed.elephant.to_numpy())

    # ---- covariates ----
    tc = aggregate(PROC / "hansen_treecover2000_32643.tif", ci, n, "mean")
    dem = aggregate(PROC / "dem_copernicus30m_32643.tif", ci, n, "mean")
    loss = aggregate(PROC / "hansen_lossyear_32643.tif", ci, n, "mean")
    wdpa = aggregate(PROC / "wdpa_all_touched_32643.tif", ci, n, "max")

    # forest cover share + edge density (Hansen 2000, pre-2011)
    with rasterio.open(PROC / "hansen_treecover2000_32643.tif") as s:
        tcv = s.read(1)
        t = s.transform
        nod = s.nodata
    forest = tcv >= HANSEN_FOREST_PCT
    if nod is not None:
        forest &= tcv != nod
    edge = np.zeros_like(forest)
    d0 = forest[:-1, :] != forest[1:, :]
    edge[:-1, :] |= d0
    edge[1:, :] |= d0
    d1 = forest[:, :-1] != forest[:, 1:]
    edge[:, :-1] |= d1
    edge[:, 1:] |= d1
    h, w = forest.shape
    rows, cols = np.mgrid[0:h, 0:w]
    ii = ci((t.c + (cols + 0.5) * t.a).ravel(), (t.f + (rows + 0.5) * t.e).ravel())
    ok = ii >= 0
    edge_density = (np.bincount(ii[ok], weights=edge.ravel()[ok].astype(float),
                                minlength=n) * 30.0 / (GRID_M ** 2))  # km edge/km2

    # CCI 2005 (300 m): cropland + urban share
    with rasterio.open(PROC / "cci_lulc_2005_32643.tif") as s:
        cci = s.read(1)
        ct = s.transform
        cn = s.nodata
    ch, cw = cci.shape
    crows, ccols = np.mgrid[0:ch, 0:cw]
    cii = ci((ct.c + (ccols + 0.5) * ct.a).ravel(),
             (ct.f + (crows + 0.5) * ct.e).ravel())
    cok = (cii >= 0) & ((cci.ravel() != cn) if cn is not None else True)
    cc, cic = cci.ravel()[cok].astype(int), cii[cok]
    ccnt = np.bincount(cic, minlength=n)
    safe = np.maximum(ccnt, 1)
    crop_share = np.bincount(cic, weights=np.isin(cc, list(CCI_CROPLAND)),
                             minlength=n) / safe
    urban_share = np.bincount(cic, weights=(cc == CCI_URBAN),
                              minlength=n) / safe

    # GLAD built-up gain 2000-2020 (LABELLED-LEAKY secondary)
    # run-of-record raster from p3_outcome_ingest: 1=expansion 2=stable 0=none
    with rasterio.open(PROC / "builtup_change_2000_2020_32643.tif") as s:
        gb = s.read(1)
        gt = s.transform
        gn = s.nodata
    bh, bw = gb.shape
    brows, bcols = np.mgrid[0:bh, 0:bw]
    bii = ci((gt.c + (bcols + 0.5) * gt.a).ravel(),
             (gt.f + (brows + 0.5) * gt.e).ravel())
    bok = (bii >= 0) & ((gb.ravel() != gn) if gn is not None else True)
    bv, bic = gb.ravel()[bok].astype(int), bii[bok]
    bcnt = np.bincount(bic, minlength=n)
    builtup_gain = np.bincount(bic, weights=(bv == 1), minlength=n) \
        / np.maximum(bcnt, 1)

    # road density (OSM 2026 snapshot, vintage-caveated) via overlay
    cells_gdf = gpd.GeoDataFrame(
        {"cell": np.arange(n)},
        geometry=[box(x - GRID_M / 2, y - GRID_M / 2,
                      x + GRID_M / 2, y + GRID_M / 2) for x, y in zip(cx, cy)],
        crs="EPSG:32643")
    roads = gpd.read_file(PROC / "roads_wayanad_32643.gpkg")[["geometry"]]
    inter = gpd.overlay(roads, cells_gdf, how="intersection", keep_geom_type=False)
    rl = inter.groupby("cell").geometry.apply(lambda g: g.length.sum() / 1000.0)
    road_density = np.zeros(n)
    road_density[rl.index.to_numpy()] = rl.to_numpy()  # km per cell (0.25 km2)

    # tourism presence: facilities within 1 km of the cell centre
    fac = pd.read_csv(PROC / "facility_existence_universe_2026-10-23.csv")
    fac = fac[fac.verified.fillna(False) & fac.inside_district.fillna(False)]
    fg = gpd.GeoSeries(gpd.points_from_xy(fac.lon, fac.lat), crs="EPSG:4326"
                       ).to_crs("EPSG:32643")
    d2f = ((cx[:, None] - fg.x.to_numpy()[None, :]) ** 2 +
           (cy[:, None] - fg.y.to_numpy()[None, :]) ** 2)
    fac_1km = (d2f <= 1000.0 ** 2).sum(1).astype(float)

    surfaces = {
        "forest_edge_density_km_per_km2": edge_density,
        "forest_cover_share": np.where(np.isnan(tc), np.nan, tc / 100.0),
        "cropland_share": crop_share,
        "urban_share_2005": urban_share,
        "forest_loss_2000_2010_share": np.where(np.isnan(loss), np.nan,
                                                (loss >= 1) & (loss <= 10)),
        "road_density_km_per_cell": road_density,
        "elevation_m": dem,
        "facilities_within_1km": fac_1km,
        "builtup_gain_2000_2020_LEAKY": builtup_gain,
    }
    outside_wdpa = ~(np.nan_to_num(wdpa, nan=0) == 1)

    def overlap(kde, mask):
        out = {}
        k = kde[mask]
        top = k >= np.nanquantile(k, 0.9)
        for name, arr in surfaces.items():
            v = arr[mask]
            ok = ~np.isnan(v)
            pct = pd.Series(v[ok]).rank(pct=True).to_numpy()
            kk = pd.Series(k[ok]).rank(pct=True).to_numpy()
            rho = float(np.corrcoef(pct, kk)[0, 1])
            vv = pct[top[ok]]
            out[name] = {
                "mean_pct_at_top_decile": round(float(np.mean(vv)), 4),
                "median_pct_at_top_decile": round(float(np.median(vv)), 4),
                "share_above_district_median": round(float((vv > 0.5).mean()), 4),
                "spearman_rho_vs_incident_kde": round(rho, 4),
                "n_cells_finite": int(ok.sum()),
            }
        return out

    facts = {
        "date": TODAY,
        "hypothesis": "H3 — HEC association; D-3 registered DOWNGRADE active "
                      "(village-level records, GPS never collected — "
                      "audit-D-10): descriptive hotspot-overlap only "
                      "(D-18-pinned recipe, freeze R7d)",
        "screen": sfacts,
        "geocoding": {
            "placed_records": int(len(placed)),
            "unplaced_records": n_none,
            "tier_counts": placed.tier.value_counts().to_dict(),
            "unique_points": int(placed.groupby(["lat", "lon"]).ngroups),
            "cache": str(GEOCODES.relative_to(ROOT.parent)),
        },
        "grid": {"cell_m": GRID_M, "cells_in_district": int(n),
                 "outside_wdpa_cells": int(outside_wdpa.sum())},
        "kde": {"sigma_m": SIGMA_M, "records_in_surface_all": n_all,
                "records_in_surface_elephant": n_elp},
        "overlap_all_cells_primary": overlap(kde_all, np.ones(n, dtype=bool)),
        "overlap_outside_wdpa_sensitivity": overlap(kde_all, outside_wdpa),
        "overlap_elephant_subset_sensitivity": overlap(kde_elp,
                                                       np.ones(n, dtype=bool)),
        "v2_direction_check": {
            "paper_stated_drivers": "C1 (Morrison et al. 2025): negative HEI "
                                    "concentrates around the sanctuary "
                                    "landscape / forest edge, season-"
                                    "dependent; cropland context",
            "how_checked": "descriptive sign of forest_edge_density mean "
                           "percentile at the incident top-decile and rho vs "
                           "the incident surface (no test, no p-value)",
        },
        "caveats": [
            "Village-level geocoded positions (precision tier per name in "
            "the geocode cache); the incident surface is a place-name "
            "hotspot surface, not a point process — no GPS exists at source "
            "(audit-D-10).",
            "Records cover 2011-2014 only (the paper's record window; "
            "2011-2023 was only its projection window).",
            "No Poisson/NB/IRR/residual-Moran's-I by design (D-3 "
            "downgrade); no p-values or CIs are computed anywhere in H3.",
            "Road density uses the 2026-10 OSM snapshot (post-window "
            "accessibility proxy; vintage-caveated).",
            "Seasonal rainfall: no raster exists in the data audit — "
            "covariate unavailable, documented, not silently dropped.",
            "builtup_gain_2000_2020 is LABELLED-LEAKY secondary (window "
            "ends 2020, not pre-2011); primary interpretation uses pre-2011 "
            "surfaces only.",
            "Documentation/effort bias: records are forest-department "
            "compensation registers — reporting effort concentrates near "
            "roads and range offices; the hotspot shape partly reflects "
            "access (H4-style caveat).",
        ],
    }
    QA.mkdir(parents=True, exist_ok=True)
    FACTS.write_text(json.dumps(facts, indent=1, default=str))
    print(f"facts -> {FACTS.relative_to(ROOT)}")
    print(f"grid: {n} cells ({int(outside_wdpa.sum())} outside WDPA); "
          f"KDE records all={n_all} elephant={n_elp}")
    for tag in ("overlap_all_cells_primary", "overlap_outside_wdpa_sensitivity"):
        print(f"[{tag}]")
        for k, v in facts[tag].items():
            print(f"  {k:36s} top%ile {v['mean_pct_at_top_decile']:.3f}  "
                  f"rho {v['spearman_rho_vs_incident_kde']:+.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
