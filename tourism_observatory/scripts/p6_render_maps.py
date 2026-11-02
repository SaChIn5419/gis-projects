#!/usr/bin/env python3
"""P6 — Wayanad map suite (RENDERING-ONLY; prereg-adjacent scope note in PROJECTSTATE §9).

Produces display figures F1-F7 + a QGIS project + a render log using files
ALREADY in data/ (manifest 36) and the frozen outputs of record. No new
covariate, statistic, test or reclassification enters the analysis; the
only geometric re-executions, both asserted against the facts of record,
are (i) the H3 incident KDE surface reproduced verbatim from the module of
record (facts dd73bddb / e1ab4cbe) and (ii) the H4 hotspot polygon from the
D-19(c) recipe (facts d945c4a6).

Figures -> outputs/figures/F*.png (+ f6 display raster)
Project -> outputs/figures/wayanad_observatory_site1.qgs (relative paths)
Log     -> outputs/figures/render_log.json

Usage: python scripts/p6_render_maps.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
import shapely
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
FIGDIR = ROOT / "outputs/figures"
sys.path.insert(0, str(ROOT / "scripts"))
import p3_h3_analysis as h3  # noqa: E402  (module of record, H3 KDE)

PROC = h3.PROC
QA = h3.QA
DISTRICT = PROC / "wayanad_boundary_32643.geojson"
DEM_R = PROC / "dem_copernicus30m_32643.tif"
SLOPE_R = PROC / "slope_deg_32643.tif"
CHANGE_R = PROC / "builtup_change_2000_2020_32643.tif"

FAC_BUF, HAZ_BUF = 500.0, 1000.0          # D-19(c) / H2b(b) radii of record
MARGIN_M = 2000.0
LOG = {"note": "rendering-only visualization of frozen outputs; prereg at R8; "
               "no statistics computed here; facts of record asserted", "figures": {}}


# ------------------------------- helpers ----------------------------------
def hillshade(a, azdeg=315.0, altitude=45.0, cell=30.0):
    """Local Horn-method hillshade (rasterio.dem unavailable in this env).

    Same display convention as GDAL: 0-255, sun w/ given azimuth/altitude.
    Purely a display product. Cell size fixed at 30 m (DEM resolution); a
    2x difference from the true 30 m x/y is subvisual at render scale.
    """
    a = np.asarray(a, dtype="float64")
    gy, gx = np.gradient(a, cell)          # d/dy (rows), d/dx (cols)
    slope = np.arctan(np.hypot(gx, gy))
    az = np.radians(450.0 - azdeg)         # GDAL azimuth convention
    alt = np.radians(altitude)
    aspect = np.arctan2(-gx, gy)
    shade = (np.sin(alt) * np.cos(slope) +
             np.cos(alt) * np.sin(slope) * np.cos(az - aspect))
    return (np.clip(shade, 0, 1) * 255).astype("float64")


def load_district():
    return unary_union(gpd.read_file(DISTRICT).geometry)


def extent_of(district, margin=MARGIN_M):
    minx, miny, maxx, maxy = district.bounds
    return minx - margin, miny - margin, maxx + margin, maxy + margin


def read_raster(path):
    with rasterio.open(path) as src:
        a = src.read(1).astype("float64")
        tr, nod = src.transform, src.nodata
    if nod is not None:
        a[a == nod] = np.nan
    return a, tr


def analyze_extent(tr, shape):
    """(left, right, bottom, top) in matplotlib imshow extent order."""
    ny, nx = shape
    return tr.c, tr.c + nx * tr.a, tr.f - ny * abs(tr.e), tr.f


def add_scalebar(ax, length_km=10):
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    x = x0 + (x1 - x0) * 0.02
    y = y0 + (y1 - y0) * 0.035
    ax.plot([x, x + length_km * 1000], [y, y], "k-", lw=3)
    ax.text(x + length_km * 500, y + (y1 - y0) * 0.018, f"{length_km} km",
            ha="center", fontsize=8)
    for xv in (x, x + length_km * 1000):
        ax.plot([xv, xv], [y - (y1 - y0) * 0.009, y + (y1 - y0) * 0.009],
                "k-", lw=1)


_DIST_PATH = None


def district_clip_patch(ax):
    """Clip-path from the district polygon — colors stay strictly inside."""
    global _DIST_PATH
    if _DIST_PATH is None:
        from matplotlib.path import Path as MPath
        rings = []
        for g in gpd.read_file(DISTRICT).geometry:
            for poly in (list(g.geoms) if g.geom_type == "MultiPolygon"
                         else [g]):
                rings.append(np.asarray(poly.exterior.coords))
                rings.extend(np.asarray(h.coords) for h in poly.interiors)
        verts, codes = [], []
        for r in rings:
            verts.append(r)
            codes.append(np.array([MPath.MOVETO] +
                                  [MPath.LINETO] * (len(r) - 2) +
                                  [MPath.CLOSEPOLY]))
        _DIST_PATH = MPath(np.vstack(verts), np.concatenate(codes))
    import matplotlib.patches as mpatches
    patch = mpatches.PathPatch(_DIST_PATH, transform=ax.transData,
                               facecolor="none", edgecolor="none")
    ax.add_patch(patch)
    return patch


def new_axes(fig_ncols, district, title, figsize):
    ext = extent_of(district)
    fig, axes = plt.subplots(1, fig_ncols, figsize=figsize)
    axes = [axes] if fig_ncols == 1 else list(axes)
    for ax in axes:
        ax.set_xlim(ext[0], ext[2])
        ax.set_ylim(ext[1], ext[3])
        ax._p6_ext = ext          # restored at finish() (imshows autoscale)
        ax.set_autoscale_on(False)  # imshows must not rescale the view
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
    fig.suptitle(title, fontsize=13, fontweight="bold")
    return fig, axes


def hillshade_base(ax, zorder=0):
    dem, tr = read_raster(DEM_R)
    hs = hillshade(dem, azdeg=315, altitude=45)
    ax.imshow(np.flipud(hs) if False else hs,
              extent=analyze_extent(tr, hs.shape), cmap="gray",
              vmin=0, vmax=255, zorder=zorder, interpolation="nearest")
    del dem
    return tr


def district_border(ax, zorder=7):
    gpd.read_file(DISTRICT).boundary.plot(ax=ax, edgecolor="black",
                                          linewidth=1.1, zorder=zorder)


def finish(fig, name, note):
    FIGDIR.mkdir(parents=True, exist_ok=True)
    for ax in fig.axes:
        if getattr(ax, "_p6_ext", None) is not None:
            ax.set_xlim(ax._p6_ext[0], ax._p6_ext[2])
            ax.set_ylim(ax._p6_ext[1], ax._p6_ext[3])
    p = FIGDIR / f"{name}.png"
    fig.savefig(p, dpi=170, bbox_inches="tight")
    plt.close(fig)
    LOG["figures"][name] = {"file": p.name, "note": note}
    print("rendered", p.relative_to(ROOT), flush=True)


def gser(geom):
    return gpd.GeoSeries([geom], crs="EPSG:32643")


# ------------------------------- figures ----------------------------------
def main() -> int:
    district = load_district()

    fac = pd.read_csv(PROC / "facility_existence_universe_2026-10-23.csv")
    fac_g = gpd.GeoDataFrame(
        fac, geometry=gpd.points_from_xy(fac.lon, fac.lat), crs="EPSG:4326"
    ).to_crs("EPSG:32643")
    ver_mask = fac_g.verified.fillna(False).astype(bool) & \
        fac_g.inside_district.fillna(False).astype(bool)
    verified = fac_g[ver_mask]
    others = fac_g[~ver_mask]

    inv = gpd.read_file(PROC / "inventory_wms_kl_landslides_new_32643.gpkg")
    scar = unary_union(gpd.read_file(
        PROC / "scar_chooralmala_mundakkai_2024_32643.gpkg").geometry)
    fac_union = unary_union([g.buffer(FAC_BUF) for g in verified.geometry])
    inv_union = unary_union([g.buffer(HAZ_BUF) for g in inv.geometry])

    # ---------------------------- F1 context -------------------------------
    fig, axes = new_axes(
        1, district, "F1 — Wayanad study site: facilities & WDPA",
        (8.0, 7.4))
    ax = axes[0]
    hillshade_base(ax)
    wdpa = gpd.read_file(PROC / "wdpa_wayanad_32643.gpkg")
    wdpa.plot(ax=ax, facecolor="#2e7d32", edgecolor="#1b5e20", alpha=0.45,
              zorder=2, linewidth=0.4)
    others.plot(ax=ax, color="grey", edgecolor="white", linewidth=0.3,
                markersize=14, zorder=4)
    verified.plot(ax=ax, color="#b30000", edgecolor="white", linewidth=0.4,
                  markersize=26, zorder=5)
    district_border(ax)
    add_scalebar(ax)
    ax.legend(handles=[
        Line2D([], [], marker="o", ls="", mfc="#b30000", mec="white",
               markersize=8,
               label=f"verified facilities inside district (n={len(verified)})"),
        Line2D([], [], marker="o", ls="", mfc="grey", mec="white",
               markersize=6, label="registry entries not verified / outside"),
        Patch(facecolor="#2e7d32", alpha=0.45,
              label="protected-area complexes (WDPA, all-touched)")],
        loc="lower right", fontsize=8, framealpha=0.9)
    finish(fig, "F1_context_facilities_wdpa",
           "universe 123 / verified 107 (facts of record, P2)")

    # ---------------------------- F2 topography ----------------------------
    dem, tr = read_raster(DEM_R)
    slope, trs = read_raster(SLOPE_R)
    fig, axes = new_axes(
        1, district, "F2 — Topography: elevation bands & slope ≥ 25°",
        (8.0, 7.4))
    ax = axes[0]
    hs = hillshade(dem, azdeg=315, altitude=45)
    ax.imshow(hs, extent=analyze_extent(tr, hs.shape), cmap="gray",
              vmin=0, vmax=255, zorder=0, interpolation="nearest")
    bands = [max(float(np.floor(np.nanmin(dem) / 100) * 100), 500.0),
             600, 750, 900, 1050, 1200, 1400, 1600,
             float(np.ceil(np.nanmax(dem) / 100) * 100)]
    bands = sorted(set(bands))
    cmap = plt.get_cmap("terrain", len(bands) - 1)
    norm = BoundaryNorm(bands, cmap.N)
    im2 = ax.imshow(dem, extent=analyze_extent(tr, dem.shape), cmap=cmap,
                    norm=norm, alpha=0.62, zorder=1, interpolation="nearest")
    sm = np.where(slope >= 25, 1.0, np.nan)
    ax.imshow(sm, extent=analyze_extent(trs, slope.shape),
              cmap=ListedColormap(["#d7301f"]), alpha=0.5, zorder=2,
              interpolation="nearest")
    district_border(ax)
    add_scalebar(ax)
    cb = fig.colorbar(im2, ax=ax, shrink=0.65, pad=0.01,
                      boundaries=bands, ticks=bands)
    cb.set_label("elevation (m)", fontsize=8)
    ax.legend(handles=[Patch(facecolor="#d7301f", alpha=0.5,
                             label="slope ≥ 25° (H2a(i) band)")],
              loc="lower right", fontsize=8, framealpha=0.9)
    finish(fig, "F2_topography_elevation_slope",
           "display only — no covariate change vs frozen run")

    # ---------------------------- F3 H1 pairs ------------------------------
    pairs = pd.read_csv(PROC / "matched_pairs_2026-10-26.csv")
    rates = pd.read_csv(PROC / "h1_pair_rates_2026-10-28.csv")
    r500 = rates[rates.radius_m == 500].set_index("pair")
    parcels = gpd.read_file(PROC / "parcels_1km_32643.gpkg")
    pid2geom = parcels.set_index("parcel_id").geometry.to_dict()
    del pairs
    fig, axes = new_axes(
        1, district, "F3 — H1 matched pairs: built-up change 2000–2020",
        (8.6, 7.4))
    ax = axes[0]
    chg, trc = read_raster(CHANGE_R)
    ax.imshow(chg, extent=analyze_extent(trc, chg.shape), cmap="copper",
              alpha=0.28, zorder=1, interpolation="nearest")
    gpd.GeoSeries(
        [g for g in (pid2geom.get(t) for t in r500.treated) if g is not None],
        crs="EPSG:32643").plot(
        ax=ax, facecolor="none", edgecolor="#3187bd", linewidth=0.9, zorder=4)
    dv = r500.diff_pp.to_numpy()
    vmax = float(max(abs(dv.min()), abs(dv.max())))
    cmap_r = plt.get_cmap("RdBu_r")
    for _, row in r500.iterrows():
        tg = pid2geom.get(row.treated)
        if tg is None:
            continue
        gser(tg).plot(ax=ax,
                      facecolor=cmap_r((row.diff_pp + vmax) / (2 * vmax)),
                      alpha=0.85, edgecolor="#b30000", linewidth=1.2,
                      zorder=5)
    district_border(ax)
    add_scalebar(ax)
    cb3 = fig.colorbar(plt.cm.ScalarMappable(
        norm=plt.Normalize(-vmax, vmax), cmap=cmap_r), ax=ax,
        shrink=0.6, pad=0.01)
    cb3.set_label("treated-parcel Δ built-up 2000–2020 @500 m (pp)", fontsize=8)
    ax.legend(handles=[Patch(facecolor="#3187bd", alpha=0.9,
                             label="matched control parcels")],
              loc="lower right", fontsize=8, framealpha=0.9)
    finish(fig, "F3_h1_matched_pairs_builtup_change",
           "pair/rate table of record h1_pair_rates (radius 500 rows)")

    # ---------------------------- F4 H2a KDE -------------------------------
    kde, trk = read_raster(QA / "p3_h2a_kde_inventory_500m_32643.tif")
    h2p = pd.read_csv(PROC / "h2a_facility_percentiles_2026-10-28.csv")
    fpts = gpd.GeoSeries(gpd.points_from_xy(h2p.lon, h2p.lat),
                         crs="EPSG:4326").to_crs("EPSG:32643")
    fig, axes = new_axes(
        1, district, "F4 — H2a: hazard KDE vs facilities",
        (8.0, 7.4))
    ax = axes[0]
    hillshade_base(ax)
    km = np.ma.masked_invalid(kde)
    im = ax.imshow(km, extent=analyze_extent(trk, kde.shape), cmap="magma",
                   vmin=0, vmax=1, alpha=0.75, zorder=2,
                   interpolation="nearest")
    district_border(ax)
    fpts.plot(ax=ax, c=h2p.pct_ii, cmap="viridis", markersize=34,
              edgecolor="white", linewidth=0.4, zorder=6)
    add_scalebar(ax)
    cb4 = fig.colorbar(im, ax=ax, shrink=0.62, pad=0.01)
    cb4.set_label("inventory KDE percentile", fontsize=8)
    finish(fig, "F4_h2a_hazard_kde_facility_percentiles",
           "facet markers = pct_ii (facts f3432795); no new statistics")

    # ---------------------------- F5 H2b footprints ------------------------
    fac_scar = verified[verified.intersects(scar)]
    assert len(fac_scar) == 0, "facts of record: scar has 0 facilities"
    fac_inv = verified[verified.intersects(inv_union)]
    fig, axes = new_axes(
        2, district, "F5 — H2b: 2024 scar vs inventory buffers",
        (14.2, 6.2))
    axl, axr = axes
    hillshade_base(axl)
    gser(scar).plot(ax=axl, facecolor="#d7301f", edgecolor="#7f0000",
                    linewidth=1.2, zorder=3, alpha=0.85)
    district_border(axl)
    axl.set_title("(a) 2024 Chooralmala–Mundakkai scar — 1.781 km²",
                  fontsize=10)
    add_scalebar(axl)
    axl.legend(handles=[Patch(facecolor="#d7301f", alpha=0.85,
                              label="scar footprint (0 facilities / 0 buildings)")],
               loc="lower right", fontsize=7.5, framealpha=0.9)
    hillshade_base(axr)
    gser(inv_union).plot(ax=axr, facecolor="#ff7f00", alpha=0.35,
                         edgecolor="none", zorder=2)
    inv.boundary.plot(ax=axr, color="#7f2704", linewidth=0.15, zorder=2.5)
    fac_inv.plot(ax=axr, color="#004529", edgecolor="white", linewidth=0.4,
                 markersize=26, zorder=6)
    facibility = verified[~verified.intersects(inv_union)]
    facibility.plot(ax=axr, color="grey", edgecolor="white", linewidth=0.3,
                    markersize=12, zorder=5)
    district_border(axr)
    axr.set_title("(b) 1 km inventory-buffer register — 992.90 km² (26/107)",
                  fontsize=10)
    add_scalebar(axr)
    axr.legend(handles=[
        Line2D([], [], marker="o", ls="", mfc="#004529", mec="white",
               markersize=8, label="facilities inside buffers (26)"),
        Line2D([], [], marker="o", ls="", mfc="grey", mec="white",
               markersize=6, label="outside (81)")],
        loc="lower right", fontsize=7.5, framealpha=0.9)
    finish(fig, "F5_h2b_footprints_two_populations",
           "counts quoted from p3_h2b facts (sha e50ae8bd)")

    # --------------------- F6 H3 + D-20 rainfall ---------------------------
    rec, sfacts = h3.screen()
    assert sfacts["kept_rows"] == 2704 and sfacts["elephant_rows"] == 2018
    geo = h3.geocode(rec)
    assert len(geo) == 425
    pts = h3.assign_points(rec, geo)
    placed = pts[pts.tier != "none"].copy()
    assert len(placed) == 2704 and (pts.tier == "none").sum() == 0
    ci = h3.CellIndex(district)
    n = ci.n
    cxg = ci.centres.x.to_numpy()
    cyg = ci.centres.y.to_numpy()
    agg = placed.groupby(["lat", "lon"]).size().reset_index(name="w")
    px = gpd.GeoSeries(gpd.points_from_xy(agg.lon, agg.lat),
                       crs="EPSG:4326").to_crs("EPSG:32643")
    d2 = ((cxg[:, None] - px.x.to_numpy()[None, :]) ** 2 +
          (cyg[:, None] - px.y.to_numpy()[None, :]) ** 2)
    kk = (agg.w.to_numpy()[None, :] *
          np.exp(-d2 / (2 * h3.SIGMA_M ** 2))).sum(1)
    kde_rank = pd.Series(kk).rank(pct=True).to_numpy()

    rk = h3.aggregate(PROC / "chirps_rain_annual_2011_2014_32643.tif",
                      ci, n, "mean")
    ms = h3.aggregate(PROC / "chirps_rain_monsoon_share_2011_2014_32643.tif",
                      ci, n, "mean")
    rho = float(np.corrcoef(pd.Series(rk).rank(pct=True), kde_rank)[0, 1])
    assert abs(rho - (-0.572)) < 0.01, f"rain rho mismatch vs facts: {rho}"
    print(f"F6 assertion OK: rain-annual rho {rho:+.3f} vs facts -0.572",
          flush=True)

    kde2d = np.full((ci.ny, ci.nx), np.nan)
    kde2d[ci.lut >= 0] = kde_rank[ci.lut[ci.lut >= 0]]
    # display: the continuous 500 m covariate rasters themselves (full grid,
    # already aligned to the same origin) — the analytic join above remains
    # the centre-in-district aggregate of record.
    rk_disp, tr_disp = read_raster(PROC / "chirps_rain_annual_2011_2014_32643.tif")
    ms_disp, _ = read_raster(PROC / "chirps_rain_monsoon_share_2011_2014_32643.tif")
    with rasterio.open(QA / "f6_incident_kde_rank_500m_32643.tif", "w",
                       driver="GTiff", height=ci.ny, width=ci.nx, count=1,
                       dtype="float32", crs="EPSG:32643",
                       transform=_cell_transform(ci), nodata=-9999) as dst:
        dst.write(np.where(np.isnan(kde2d), -9999, kde2d), 1)
    LOG["f6_display_raster"] = "f6_incident_kde_rank_500m_32643.tif " \
        "(display product; KDE of record re-rendered, rank values)"

    ext = extent_of(district)
    fig, axes = plt.subplots(1, 3, figsize=(15.8, 5.8))
    fig.suptitle(
        "F6 — H3 hotspots vs forest cover & D-20 rainfall "
        "(POST-HOC, non-inferential)",
        fontsize=13, fontweight="bold")
    a1, a2, a3 = [ax for ax in axes]
    for ax in axes:
        ax.set_xlim(ext[0], ext[2])
        ax.set_ylim(ext[1], ext[3])
        ax._p6_ext = ext          # restored at finish() (imshows autoscale)
        ax.set_autoscale_on(False)  # imshows must not rescale the view
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
    tc, trt = read_raster(PROC / "hansen_treecover2000_32643.tif")
    a1.imshow(tc, extent=analyze_extent(trt, tc.shape), cmap="Greens",
              vmin=0, vmax=100, zorder=0, interpolation="nearest")
    a1.scatter(cxg[~np.isnan(kde_rank)], cyg[~np.isnan(kde_rank)],
               c=kde_rank[~np.isnan(kde_rank)], cmap="magma", s=2.1,
               marker=",", zorder=3)
    district_border(a1)
    add_scalebar(a1)
    a1.set_title("(i) incident KDE rank (dots) vs tree cover 2000 (%)",
                 fontsize=10)
    _panel_cells(a2, rk_disp, tr_disp, district, "YlGnBu",
                 "(ii) CHIRPS rain annual total 2011–2014", "mm/yr",
                 vmin=1100, vmax=3650)
    _panel_cells(a3, ms_disp, tr_disp, district, "PuOr_r",
                 "(iii) CHIRPS Jun–Sep share 2011–2014", "SW-monsoon share",
                 vmin=0.50, vmax=0.65)
    fig.text(0.99, 0.01, "POST-HOC SENSITIVITY (D-20) — non-inferential; "
             "facts of record: ρ(annual, KDE) = −0.572", ha="right",
             fontsize=7.5, fontstyle="italic")
    finish(fig, "F6_h3_rainfall_sensitivity_panels",
           "KDE re-render asserted; rho matches facts e1ab4cbe")

    # ---------------------------- F7 H4 disputes ---------------------------
    evd = pd.read_csv(QA / "p4_h4_dispute_table_2026-11-02.csv")
    anchor = gpd.GeoSeries(
        gpd.points_from_xy(evd.anchor_lon, evd.anchor_lat),
        crs="EPSG:4326", index=evd.dispute_id).to_crs("EPSG:32643")
    hazard = unary_union([inv_union, scar])
    hotspot = shapely.intersection(fac_union, hazard)
    hotspot = shapely.intersection(hotspot, district)
    ha_km2 = hotspot.area / 1e6
    assert abs(ha_km2 - 15.0625) < 0.05, f"hotspot mismatch vs facts: {ha_km2}"
    print(f"F7 assertion OK: hotspot {ha_km2:.4f} km2 vs facts 15.0625 km2",
          flush=True)

    margins = {"D-003": 94, "D-004": 24, "D-008": 143}
    fig, axes = new_axes(
        1, district, "F7 — H4: disputes vs exposure hotspot",
        (8.4, 7.4))
    ax = axes[0]
    hillshade_base(ax)
    gser(inv_union).plot(ax=ax, facecolor="#ff7f00", alpha=0.25,
                         edgecolor="none", zorder=2)
    gser(fac_union).plot(ax=ax, facecolor="none", edgecolor="#05529c",
                         linewidth=0.3, zorder=3)
    gser(hotspot).plot(ax=ax, facecolor="#d7301f", edgecolor="#7f0000",
                       alpha=0.85, linewidth=1.3, zorder=4)
    for disp_id, pt in anchor.items():
        rr = float(evd.loc[evd.dispute_id == disp_id, "radius_m"].iloc[0])
        ov = bool(evd.loc[evd.dispute_id == disp_id,
                          "overlaps_hotspot"].iloc[0])
        gser(pt.buffer(rr)).plot(ax=ax, facecolor="#f7fcb9",
                                 edgecolor="#31a354" if ov else "#7f7f7f",
                                 alpha=0.7, linewidth=1.0, zorder=5)
        ax.scatter(pt.x, pt.y, s=34, marker="D",
                   c="#31a354" if ov else "black", edgecolor="white",
                   linewidth=0.6, zorder=6)
        extra = f" ({margins[disp_id]} m)" if disp_id in margins else ""
        ax.annotate(disp_id + extra, (pt.x, pt.y + rr * 1.6), fontsize=7,
                    zorder=7, ha="center", fontweight="bold",
                    color="#7f0000" if disp_id in margins else "black")
    district_border(ax)
    add_scalebar(ax)
    ax.legend(handles=[
        Patch(facecolor="#d7301f", alpha=0.85,
              label="exposure hotspot (15.06 km², 0.74% of district)"),
        Line2D([], [], marker="D", ls="", mfc="#31a354", mec="white",
               markersize=8, label="anchor overlapping hotspot (D-004, 24 m)"),
        Line2D([], [], marker="D", ls="", mfc="black", mec="white",
               markersize=6, label="anchor outside (D-003 miss 94 m; D-008 miss 143 m)")],
        loc="lower right", fontsize=7.5, framealpha=0.9)
    finish(fig, "F7_h4_dispute_hotspot",
           "hotspot geometry from D-19(c) recipe, asserted vs facts d945c4a6")

    LOG["assertions"] = {
        "f6_rain_annual_rho": round(rho, 3),
        "f7_hotspot_area_km2": round(ha_km2, 4),
        "sources": {
            "incident_kde": "p3_h3 module of record re-render (facts dd73bddb, e1ab4cbe)",
            "hotspot": "D-19(c) recipe re-executed (facts d945c4a6)",
            "layers": "data/ files of record, manifest 36 entries",
        },
    }
    FIGDIR.mkdir(parents=True, exist_ok=True)
    (FIGDIR / "render_log.json").write_text(json.dumps(LOG, indent=1))
    print("render log written")
    return 0


def _cell_transform(ci):
    from affine import Affine
    return Affine(500.0, 0, ci.x0, 0, -500.0, ci.y0 + ci.ny * 500.0)


def _panel_cells(ax, arr, tr, district, cmapv, title, cb_label, vmin, vmax):
    im = ax.imshow(np.ma.masked_invalid(arr), extent=analyze_extent(tr, arr.shape),
                   cmap=cmapv, vmin=vmin, vmax=vmax, zorder=2,
                   interpolation="nearest")
    im.set_clip_path(district_clip_patch(ax))   # colors fit the outline
    district_border(ax)
    add_scalebar(ax)
    ax.set_title(title, fontsize=10)
    cb = plt.colorbar(im, ax=ax, shrink=0.75, pad=0.01)
    cb.set_label(cb_label, fontsize=8)


if __name__ == "__main__":
    sys.exit(main())
