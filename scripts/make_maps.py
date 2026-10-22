#!/usr/bin/env python3
"""Build portfolio maps from the aligned stack and screening outputs.

The maps are deliberately plain: a true-colour Sentinel-2 base, a reason-code
overlay, a waterfall chart, and a mixed-code close-up. They are generated from
the actual GeoTIFFs, so the hectares in the legend cannot drift from the run.

Usage:
    python scripts/make_maps.py config/jhabua.yaml
"""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
import yaml
from matplotlib.patches import Patch, Rectangle
from rasterio.transform import from_origin
from rasterio.warp import Resampling, reproject, transform_bounds
from rasterio.windows import from_bounds
from affine import Affine

ROOT = Path(__file__).resolve().parents[1]

REASON_COLORS = {
    0: "#2f8f4e",   # eligible
    1: "#123f2b",   # woody
    2: "#2f6fb0",   # built/water/wetland
    3: "#d9b44a",   # cropland (not excluded in census)
    4: "#d95f02",   # recent removal
    5: "#b2182b",   # steep
    6: "#7b3294",   # protected
    7: "#9e9e9e",   # nodata
    8: "#8c6d31",   # small patch
}
REASON_NAMES = {
    0: "Candidate (code 0)",
    1: "Woody cover",
    2: "Built / water / wetland",
    3: "Cropland (design exclusion)",
    4: "Recent woody removal",
    5: "Steep slope",
    6: "Protected area",
    7: "No data",
    8: "Small patch",
}


def load_cfg(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def raster_extent(path: Path):
    with rasterio.open(path) as src:
        return tuple(src.bounds), (src.height, src.width)


def s2_background(district: gpd.GeoDataFrame, cfg: dict, res_m: float = 60.0):
    """Return a stretched RGB array and its UTM extent, cropped to the district."""
    candidates = [
        ROOT / cfg["paths"]["sources"]["s2_dry"],
        ROOT / "data/processed/s2_dry_2024.tif",
    ]
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        raise FileNotFoundError("no Sentinel-2 dry-season raster found")

    left, bottom, right, top = district.total_bounds
    with rasterio.open(path) as src:
        if src.crs != district.crs:
            left, bottom, right, top = transform_bounds(
                district.crs, src.crs, left, bottom, right, top
            )
        window = from_bounds(left, bottom, right, top, src.transform)
        window = window.round_offsets().round_lengths()
        # Read a display-sized version rather than a multi-hundred-megabyte
        # native-resolution window.
        out_w = min(2200, int(window.width))
        out_h = min(2200, int(window.height))
        data = src.read(
            [3, 2, 1], window=window, out_shape=(3, out_h, out_w),
            resampling=Resampling.average,
        ).astype("float32")
        src_transform = src.window_transform(window) * Affine.scale(
            window.width / out_w, window.height / out_h
        )
        src_crs = src.crs
        src_nodata = src.nodata

    left, bottom, right, top = district.total_bounds
    width = int(math.ceil((right - left) / res_m))
    height = int(math.ceil((top - bottom) / res_m))
    transform = from_origin(left, top, res_m, res_m)

    bands = []
    for band in data:
        dst = np.zeros((height, width), dtype="float32")
        reproject(
            band, dst,
            src_transform=src_transform, src_crs=src_crs,
            src_nodata=src_nodata,
            dst_transform=transform, dst_crs=district.crs,
            dst_nodata=0.0, resampling=Resampling.bilinear,
        )
        bands.append(dst)
    rgb = np.dstack(bands)
    valid = np.all(rgb > 0, axis=2)
    if valid.any():
        for i in range(3):
            vals = rgb[..., i][valid]
            lo, hi = np.percentile(vals, [1, 99])
            rgb[..., i] = np.clip((rgb[..., i] - lo) / max(hi - lo, 1e-6), 0, 1)
        rgb = np.clip(rgb ** 0.60, 0, 1)
    # Make the area outside the Sentinel-2 footprint light rather than black.
    rgb[~valid] = (0.94, 0.94, 0.91)
    return rgb, (left, bottom, right, top)


def add_scalebar(ax, extent, length_km=10, x_frac=0.06, y_frac=0.07):
    xmin, ymin, xmax, ymax = extent
    x0 = xmin + x_frac * (xmax - xmin)
    y0 = ymin + y_frac * (ymax - ymin)
    length = length_km * 1000.0
    ax.plot([x0, x0 + length], [y0, y0], color="black", lw=3.5, solid_capstyle="butt")
    ax.plot([x0, x0 + length / 2], [y0, y0], color="white", lw=1.5, solid_capstyle="butt")
    ax.text(x0 + length / 2, y0 + 0.015 * (ymax - ymin),
            f"{length_km} km", ha="center", va="bottom", fontsize=7)


def add_north(ax, xy=(0.955, 0.90), xytext=(0.955, 0.80)):
    ax.annotate(
        "N", xy=xy, xytext=xytext, xycoords="axes fraction",
        ha="center", va="center", fontsize=9, fontweight="bold",
        arrowprops=dict(arrowstyle="-|>", color="black", lw=1.4),
    )


def add_sources(fig, extra=""):
    text = (
        "Sources: ESA WorldCover 2021 v200; Hansen/UMD/Google/USGS/NASA GFC 2024 v1.12; "
        "Copernicus DEM GLO-30; WDPA Oct 2026 (UNEP-WCMC/IUCN); Sentinel-2; geoBoundaries. "
        "Independent pre-feasibility screen — not affiliated with Equilibrium Earth."
    )
    if extra:
        text += "\n" + extra
    fig.text(0.01, 0.01, text, ha="left", va="bottom", fontsize=6, color="#444444")


def map_study_area(district, wdpa, rgb, extent, out: Path):
    fig, ax = plt.subplots(figsize=(10, 9), dpi=200)
    # Matplotlib's extent order is (left, right, bottom, top).
    ax.imshow(rgb, extent=(extent[0], extent[2], extent[1], extent[3]), origin="upper")
    district.boundary.plot(ax=ax, color="black", linewidth=1.4)
    if len(wdpa):
        wdpa.boundary.plot(ax=ax, color="#6a3d9a", linewidth=0.45, alpha=0.65)
    ax.set_xlim(extent[0], extent[2])
    ax.set_ylim(extent[1], extent[3])
    ax.set_aspect("equal")
    ax.set_axis_off()
    ax.set_title("Jhabua district — study area", fontsize=17, fontweight="bold", pad=26)
    ax.text(0.01, 1.006, "Public-data land screening · EPSG:32643 · 30 m",
            transform=ax.transAxes, fontsize=9, color="#333333", va="bottom")
    handles = [
        Patch(facecolor="none", edgecolor="black", linewidth=1.4, label="District boundary"),
        Patch(facecolor="none", edgecolor="#6a3d9a", linewidth=0.8, label="WDPA protected areas (Oct 2026)"),
    ]
    ax.legend(handles=handles, loc="lower left", frameon=True, fontsize=8)
    ax.text(0.99, 0.02, "District: 3,433.8 km²", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=8,
            bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor="#cccccc", alpha=0.9))
    add_scalebar(ax, extent)
    add_north(ax)
    add_sources(fig)
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def map_reasons(reason_path: Path, district, cfg, out: Path, summary: dict):
    reason_arr, shape = raster_extent(reason_path)
    with rasterio.open(reason_path) as src:
        reason = src.read(1)
        extent = tuple(src.bounds)
    rgba = np.zeros((reason.shape[0], reason.shape[1], 4), dtype="float32")
    for code, color in REASON_COLORS.items():
        mask = reason == code
        if mask.any():
            rgba[mask] = matplotlib.colors.to_rgba(color, alpha=1.0)
    rgba[reason == 255] = (1, 1, 1, 0)

    fig, ax = plt.subplots(figsize=(10, 9), dpi=200)
    ax.imshow(rgba, extent=(extent[0], extent[2], extent[1], extent[3]), origin="upper")
    district.boundary.plot(ax=ax, color="black", linewidth=1.2)
    ax.set_xlim(extent[0], extent[2])
    ax.set_ylim(extent[1], extent[3])
    ax.set_aspect("equal")
    ax.set_axis_off()
    ax.set_title("Jhabua land screening — reason codes", fontsize=17, fontweight="bold", pad=26)
    ax.text(0.01, 1.006, "Census route · VM0047 v1.1 · every pixel has one code",
            transform=ax.transAxes, fontsize=9, color="#333333", va="bottom")

    handles = []
    for code in sorted(REASON_COLORS):
        n = int((reason == code).sum())
        if n:
            handles.append(Patch(facecolor=REASON_COLORS[code], label=f"{REASON_NAMES[code]} — {n * 0.09:,.0f} ha"))
    ax.legend(handles=handles, loc="lower right", frameon=True, fontsize=8, title="Reason code")
    ax.text(0.99, 0.34,
            f"Methodology-eligible: {summary['methodology_eligible_ha']:,.0f} ha\n"
            f"Candidate after design screens: {summary['candidate_ha']:,.0f} ha",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=8,
            bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor="#cccccc", alpha=0.92))
    add_scalebar(ax, extent)
    add_north(ax)
    add_sources(fig, "Codes 3, 4 and 7 are zero hectares in this run. Candidate still includes cropland because census mode keeps it.")
    fig.tight_layout(rect=(0, 0.045, 1, 1))
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def map_waterfall(csv_path: Path, summary: dict, out: Path):
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["stage"] in ("A_methodology", "B_design"):
                rows.append(row)

    fig, (ax, ax2) = plt.subplots(
        1, 2, figsize=(13, 6.5), dpi=200, gridspec_kw={"width_ratios": [2.0, 1.0]}
    )
    labels = [r["step"].replace("_", " ").title() for r in rows]
    values = [float(r["removed_ha"]) for r in rows]
    colors = ["#2b6cb0" if r["stage"] == "A_methodology" else "#dd6b20" for r in rows]
    y = np.arange(len(rows))
    ax.barh(y, values, color=colors, edgecolor="white")
    ax.set_yticks(y, labels, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Area removed (ha)")
    ax.set_title("Exclusion waterfall", loc="left", fontsize=15, fontweight="bold")
    ax.grid(axis="x", color="#dddddd", linewidth=0.7)
    ax.set_axisbelow(True)
    for yi, value in zip(y, values):
        ax.text(value + max(values) * 0.015, yi, f"{value:,.0f}", va="center", fontsize=7)
    ax.legend(
        handles=[
            Patch(facecolor="#2b6cb0", label="Stage A — methodology / data validity"),
            Patch(facecolor="#dd6b20", label="Stage B — project design"),
        ],
        loc="lower right", frameon=True, fontsize=8,
    )
    ax.set_xlim(0, max(values) * 1.22)

    ax2.axis("off")
    ax2.set_title("Area accounting", loc="left", fontsize=15, fontweight="bold")
    lines = [
        ("District", f"{summary['district_ha']:,.0f} ha"),
        ("Methodology-eligible", f"{summary['methodology_eligible_ha']:,.0f} ha"),
        ("Candidate", f"{summary['candidate_ha']:,.0f} ha"),
        ("Candidate share", f"{summary['candidate_ha'] / summary['district_ha'] * 100:.1f}%"),
    ]
    for i, (label, value) in enumerate(lines):
        y0 = 0.80 - i * 0.16
        ax2.text(0.02, y0, label, fontsize=9, color="#444444", va="top")
        ax2.text(0.98, y0, value, fontsize=11, fontweight="bold", ha="right", va="top")
    ax2.text(0.02, 0.08,
             "Candidate still includes cropland.\n"
             "Protected-area removal uses all WDPA polygons,\n"
             "including Reserve/Protected Forest designations.",
             fontsize=7.5, color="#555555", va="bottom")
    add_sources(fig)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def choose_closeup(reason: np.ndarray, window_px: int = 440, step_px: int = 220):
    """Pick a window with a mix of codes, not a monoculture."""
    h, w = reason.shape
    best = None
    for r in range(0, h - window_px, step_px):
        for c in range(0, w - window_px, step_px):
            sub = reason[r:r + window_px, c:c + window_px]
            outside = float((sub == 255).mean())
            if outside > 0.05:
                continue
            counts = np.bincount(sub.ravel(), minlength=9)[:9].astype(float)
            p = counts / max(counts.sum(), 1)
            entropy = -float(np.sum(p[p > 0] * np.log(p[p > 0])))
            # Prefer a real mix of eligible and excluded land.
            mix = 1.0 - abs(float(p[0]) - 0.55)
            score = entropy + 0.7 * mix
            if best is None or score > best[0]:
                best = (score, r, c)
    if best is None:
        return 0, 0, window_px
    return best[1], best[2], window_px


def map_closeup(reason_path: Path, district, rgb, rgb_extent, out: Path):
    with rasterio.open(reason_path) as src:
        reason = src.read(1)
        transform = src.transform
        full_extent = tuple(src.bounds)

    r, c, win = choose_closeup(reason)
    left = transform.c + c * transform.a
    right = left + win * transform.a
    top = transform.f + r * transform.e
    bottom = top + win * transform.e

    rgba = np.zeros((reason.shape[0], reason.shape[1], 4), dtype="float32")
    for code, color in REASON_COLORS.items():
        mask = reason == code
        if mask.any():
            rgba[mask] = matplotlib.colors.to_rgba(color, alpha=0.62)
    rgba[reason == 255] = (1, 1, 1, 0)

    fig, ax = plt.subplots(figsize=(9, 8), dpi=200)
    ax.imshow(rgb, extent=(rgb_extent[0], rgb_extent[2], rgb_extent[1], rgb_extent[3]), origin="upper")
    ax.imshow(rgba, extent=(full_extent[0], full_extent[2], full_extent[1], full_extent[3]), origin="upper")
    district.boundary.plot(ax=ax, color="black", linewidth=0.8, alpha=0.7)
    ax.set_xlim(left, right)
    ax.set_ylim(bottom, top)
    ax.set_aspect("equal")
    ax.set_axis_off()
    ax.set_title("Candidate close-up — mixed reason codes", fontsize=15, fontweight="bold", pad=24)
    ax.text(0.01, 1.006, "Sentinel-2 dry-season composite with the 30 m screen overlay",
            transform=ax.transAxes, fontsize=8.5, color="#333333", va="bottom")

    # Small locator map.
    inset = ax.inset_axes([0.68, 0.66, 0.28, 0.28])
    district.plot(ax=inset, facecolor="#f2f2f2", edgecolor="black", linewidth=0.8)
    inset.add_patch(Rectangle((left, bottom), right - left, top - bottom,
                              facecolor="none", edgecolor="#d62728", linewidth=1.4))
    inset.set_xlim(district.total_bounds[0], district.total_bounds[2])
    inset.set_ylim(district.total_bounds[1], district.total_bounds[3])
    inset.set_aspect("equal")
    inset.set_xticks([])
    inset.set_yticks([])
    inset.set_xlabel("")
    inset.set_ylabel("")
    inset.set_title("Location", fontsize=7, pad=3)

    handles = [
        Patch(facecolor=REASON_COLORS[code], label=REASON_NAMES[code])
        for code in sorted(REASON_COLORS) if (reason[r:r + win, c:c + win] == code).any()
    ]
    ax.legend(handles=handles, loc="lower right", frameon=True, fontsize=7.5, title="Reason code")
    add_scalebar(ax, (left, bottom, right, top), length_km=5)
    add_north(ax, xy=(0.06, 0.92), xytext=(0.06, 0.82))
    add_sources(fig)
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Build portfolio maps from the screening outputs.")
    parser.add_argument("config", nargs="?", default="config/jhabua.yaml")
    args = parser.parse_args(argv)

    cfg = load_cfg(ROOT / args.config)
    out_dir = ROOT / cfg["paths"]["output_dir"] / "maps"
    out_dir.mkdir(parents=True, exist_ok=True)

    district = gpd.read_file(ROOT / "data/processed/boundary_jhabua.geojson").to_crs(cfg["grid"]["crs"])
    wdpa = gpd.read_file(ROOT / cfg["paths"]["sources"]["protected_areas"]).to_crs(cfg["grid"]["crs"])
    wdpa = gpd.clip(wdpa, district)

    import json
    summary = json.loads(
        (ROOT / cfg["paths"]["output_dir"] / cfg["project"]["name"] / "run_summary.json")
        .read_text(encoding="utf-8")
    )["summary"]

    rgb, rgb_extent = s2_background(district, cfg)
    reason_path = ROOT / cfg["paths"]["output_dir"] / cfg["project"]["name"] / "reason_codes.tif"
    waterfall_path = ROOT / cfg["paths"]["output_dir"] / cfg["project"]["name"] / "waterfall.csv"

    map_study_area(district, wdpa, rgb, rgb_extent, out_dir / "01_study_area.png")
    map_reasons(reason_path, district, cfg, out_dir / "02_reason_codes.png", summary)
    map_waterfall(waterfall_path, summary, out_dir / "03_waterfall.png")
    map_closeup(reason_path, district, rgb, rgb_extent, out_dir / "04_candidate_closeup.png")

    print(f"[maps] wrote 4 maps to {out_dir}")
    for p in sorted(out_dir.glob("*.png")):
        print(f"  {p.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
