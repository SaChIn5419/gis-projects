"""Ingest smoke test: synthetic raw layers -> aligned stack -> QA gate.

This does not pretend to be Jhabua data. It proves the contract: one grid,
correct resampling, correct dtypes/nodata, and a QA gate that measures the
result instead of trusting a manifest.
"""
from pathlib import Path

import numpy as np
import rasterio
import yaml
from rasterio.transform import from_origin

from src import ingest, qaqc
from src.screening import load_config

CONFIG = Path(__file__).resolve().parents[1] / "config" / "jhabua.yaml"


def _write_raster(path, arr, crs, transform, nodata):
    profile = dict(driver="GTiff", height=arr.shape[0], width=arr.shape[1], count=1,
                   dtype=str(arr.dtype), crs=crs, transform=transform, nodata=nodata,
                   compress="lzw")
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(arr, 1)


def test_ingest_builds_one_grid_and_qaqc_accepts_it(tmp_path):
    import geopandas as gpd
    from shapely.geometry import box

    # 600 m square = 36 ha at 30 m, origin on a 30 m grid.
    boundary = gpd.GeoDataFrame(
        {"shapeName": ["Jhabua"]},
        geometry=[box(600000, 2500020, 600600, 2500620)],
        crs="EPSG:32643",
    )
    boundary_path = tmp_path / "boundary.geojson"
    boundary.to_file(boundary_path, driver="GeoJSON")

    raw = tmp_path / "raw"
    raw.mkdir()
    # WorldCover at 10 m: 60 x 60 pixels over the same square.
    wc = np.full((60, 60), 30, dtype="uint8")
    wc[10:20, 10:20] = 40
    _write_raster(raw / "worldcover.tif", wc, "EPSG:32643",
                  from_origin(600000, 2500620, 10, 10), 0)

    # Hansen at 30 m, with one 2022 loss pixel and one gain pixel.
    tree = np.zeros((20, 20), dtype="uint8")
    tree[:, :3] = 55
    loss = np.zeros((20, 20), dtype="uint8")
    loss[0, 0] = 22
    gain = np.zeros((20, 20), dtype="uint8")
    gain[19, 19] = 1
    for name, arr in (("tree", tree), ("loss", loss), ("gain", gain)):
        _write_raster(raw / f"{name}.tif", arr, "EPSG:32643",
                      from_origin(600000, 2500620, 30, 30), 255)

    dem = np.full((20, 20), 300.0, dtype="float32")
    _write_raster(raw / "dem.tif", dem, "EPSG:32643",
                  from_origin(600000, 2500620, 30, 30), -9999.0)

    wdpa = gpd.GeoDataFrame(
        {"name": ["test pa"]},
        geometry=[box(600300, 2500020, 600600, 2500320)],
        crs="EPSG:32643",
    )
    wdpa_path = tmp_path / "wdpa.geojson"
    wdpa.to_file(wdpa_path, driver="GeoJSON")

    cfg = load_config(CONFIG)
    cfg["project"]["boundary"] = str(boundary_path)
    cfg["paths"]["aligned_dir"] = "data/processed/aligned"
    cfg["paths"]["output_dir"] = "outputs"
    cfg["paths"]["sources"] = {
        "worldcover": str(raw / "worldcover.tif"),
        "hansen_treecover2000": str(raw / "tree.tif"),
        "hansen_lossyear": str(raw / "loss.tif"),
        "hansen_gain": str(raw / "gain.tif"),
        "dem": str(raw / "dem.tif"),
        "protected_areas": str(wdpa_path),
        "s2_dry": str(tmp_path / "missing_dry.tif"),
        "s2_monsoon": str(tmp_path / "missing_monsoon.tif"),
    }
    cfg["qa"]["reference_area_km2"] = 0.36           # 600 m x 600 m
    cfg_path = tmp_path / "test.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")

    rc = ingest.main([str(cfg_path), "--base", str(tmp_path)])
    assert rc == 0

    aligned = tmp_path / "data/processed/aligned"
    with rasterio.open(aligned / cfg["paths"]["layers"]["district_mask"]) as src:
        assert src.res == (30.0, 30.0)
        assert src.crs.to_string() == "EPSG:32643"
        mask = src.read(1)
        assert mask.sum() == 400                     # 600 m / 30 m = 20 x 20
    with rasterio.open(aligned / cfg["paths"]["layers"]["worldcover"]) as src:
        assert src.read(1).shape == (20, 20)
        assert set(np.unique(src.read(1))).issubset({0, 30, 40})
    with rasterio.open(aligned / cfg["paths"]["layers"]["hansen_lossyear"]) as src:
        assert src.nodata == 255
    with rasterio.open(aligned / cfg["paths"]["layers"]["slope_deg"]) as src:
        assert src.dtypes[0] == "float32"
        assert float(src.read(1, masked=True).max()) < 1.0   # flat DEM

    # The QA gate must accept the stack it just measured.
    results, _ = qaqc.run_checks(cfg, tmp_path)
    critical = [r for r in results if r.kind == "critical" and not r.passed]
    assert not critical, [f"{r.check}: {r.message}" for r in critical]
