#!/usr/bin/env python3
"""P7 — F8/F9: 2000-vs-now comparison figures (display only, D-21 / R9).

Reads the 500 m display stack written by scripts/p7_2000_vs_now.py and the
shared P6 render helpers. No statistic is computed here; the numbers of
record come from outputs/qaqc/p7_2000_vs_now_accounting_2026-11-03.json.

Usage: python scripts/p7_render_maps.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import p6_render_maps as r6  # noqa: E402  (shared render helpers)
import p3_h3_analysis as h3  # noqa: E402

QA = h3.QA
STACK = QA / "p7_500m_display_32643.tif"
LOG = ROOT / "outputs/figures/render_log.json"



def alpha_cmap(name, power=0.45, n=256):
    """Sequential cmap with alpha ramping from transparent to opaque.

    Sparse settlement (a few % of a 500 m cell) then tints the hillshade
    instead of painting it near-white; dense cells stay fully opaque.
    """
    from matplotlib.colors import ListedColormap
    base = plt.get_cmap(name)(np.linspace(0, 1, n))
    base[:, 3] = np.linspace(0, 1, n) ** power
    return ListedColormap(base)


def main() -> int:
    district = r6.load_district()
    ci = h3.CellIndex(district)
    tr = r6._cell_transform(ci)

    with rasterio.open(STACK) as s:
        bands = {n: s.read(i + 1, masked=True).astype(float).filled(np.nan)
                 for i, n in enumerate(s.descriptions)}

    figs = {}

    # ------------------------------- F8 -----------------------------------
    fig, axes = r6.new_axes(
        3, district, "F8 — Built-up 2000 vs 2020 (GLAD, 500 m cells)",
        (15.8, 4.4))
    titles = ["(i) built-up 2000", "(ii) built-up 2020",
              "(iii) expansion 2000–2020"]
    keys = ["built_share_2000", "built_share_2020", "built_expansion_share"]
    vmaxs = [0.6, 0.6, 0.35]
    for ax, k, t, vm in zip(axes, keys, titles, vmaxs):
        r6.hillshade_base(ax)
        arr = bands[k].copy()
        r6._panel_cells(ax, arr, tr, district, alpha_cmap("Blues"), t,
                        "share of cell", 0.0, vm)
    r6.finish(fig, "F8_builtup_2000_vs_2020",
              "D-21 descriptive (R9): GLAD extent 2000 = class 2, 2020 = "
              "class {1,2}, expansion = class 1, aggregated to 500 m cells; "
              "colours capped at p99-ish display max")

    # ------------------------------- F9 -----------------------------------
    fig, axes = r6.new_axes(
        4, district, "F9 — Forest 2000 vs now (Hansen, 500 m cells)",
        (20.6, 4.5))
    a1, a2, a3, a4 = axes
    for ax, k, t in [(a1, "forest_share_2000", "(i) forest 2000"),
                     (a2, "forest_share_2024", "(ii) forest 2024")]:
        r6.hillshade_base(ax)
        r6._panel_cells(ax, bands[k], tr, district, "Greens", t,
                        "forest share of cell", 0.5, 1.0)

    for ax, k, t in [(a3, "loss_share_2001_2024", "(iii) lost 2001–2024"),
                     (a4, "loss_share_2021_2024", "(iv) lost 2021–2024")]:
        r6.hillshade_base(ax)
        arr = bands[k].copy()
        arr[arr < 0.002] = np.nan      # < 0.2 % of cell = ""no loss"" shade
        vmax = max(0.05, float(np.nanpercentile(arr, 99)))
        r6._panel_cells(ax, arr, tr, district, "Reds", t,
                        "lost share of cell", 0.0, vmax)

    r6.finish(fig, "F9_forest_2000_vs_now",
              "D-21 descriptive (R9): Hansen treecover2000 >=30 % canopy; "
              "loss read by lossyear code; (iii) 2001-2024, (iv) 2021-2024; "
              "colour caps at the 99th percentile of each loss band")

    # ------------------------- merge render log ---------------------------
    log = json.loads(LOG.read_text()) if LOG.exists() else {"figures": {}}
    log.setdefault("figures", {})
    for name in ["F8_builtup_2000_vs_2020", "F9_forest_2000_vs_now"]:
        src = {"F8_builtup_2000_vs_2020":
               "D-21 descriptive (R9) — GLAD built-up extent/expansion "
               "aggregated to the 500 m grid of record",
               "F9_forest_2000_vs_now":
               "D-21 descriptive (R9) — Hansen forest 2000 / 2024 and loss "
               "share 2001-2024 / 2021-2024 per 500 m cell"}[name]
        log["figures"][name] = {
            "file": f"{name}.png",
            "note": src,
            "prereg": "D-21 / R9 bcaa9223…",
            "facts": "outputs/qaqc/p7_2000_vs_now_accounting_2026-11-03.json",
        }
    log["p7_note"] = ("F8–F9 are D-21 descriptive displays (no test). "
                      "Prereg pinned at R9 before computation.")
    LOG.write_text(json.dumps(log, indent=1))
    print("render log updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
