"""End-to-end smoke test: write aligned GeoTIFFs, run the CLI, read outputs back."""
import csv
import json
from pathlib import Path

import numpy as np
import rasterio
import yaml
from rasterio.transform import from_origin

from src.screening import load_config, main

CONFIG = Path(__file__).resolve().parents[1] / "config" / "jhabua.yaml"


def test_cli_end_to_end(tmp_path):
    cfg = load_config(CONFIG)
    shape = (80, 80)
    prof = dict(driver="GTiff", height=shape[0], width=shape[1], count=1,
                crs="EPSG:32643", transform=from_origin(600000, 2500000, 30, 30))

    district = np.ones(shape, dtype="uint8"); district[:, 0] = 0
    layers = {
        "district_mask": district,
        "worldcover": np.full(shape, 30, dtype="uint8"),
        "hansen_treecover2000": np.zeros(shape, dtype="uint8"),
        "hansen_lossyear": np.zeros(shape, dtype="uint8"),
        "hansen_gain": np.zeros(shape, dtype="uint8"),
        "slope_deg": np.full(shape, 3.0, dtype="float32"),
        "protected_areas": np.zeros(shape, dtype="uint8"),
    }
    layers["worldcover"][:10, :] = 10
    aligned = tmp_path / cfg["paths"]["aligned_dir"]
    aligned.mkdir(parents=True)
    for key, arr in layers.items():
        with rasterio.open(aligned / cfg["paths"]["layers"][key], "w", dtype=str(arr.dtype), **prof) as dst:
            dst.write(arr, 1)

    cfg["qa"]["reference_area_km2"] = float(district.sum()) * 900 / 1e6   # exact reference
    cfg_path = tmp_path / "test.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg))

    main([str(cfg_path), "--base", str(tmp_path)])

    out = tmp_path / cfg["paths"]["output_dir"] / cfg["project"]["name"]
    assert (out / "reason_codes.tif").exists() and (out / "confidence_flags.tif").exists()
    with rasterio.open(out / "reason_codes.tif") as src:
        reason = src.read(1)
        assert src.nodata == 255 and (reason[:, 0] == 255).all()
    rows = list(csv.DictReader(open(out / "waterfall.csv")))
    assert [r["step"] for r in rows][-1] == "CANDIDATE"
    summary = json.load(open(out / "run_summary.json"))
    assert summary["summary"]["candidate_ha"] > 0 and len(summary["config_sha256"]) == 64


def test_load_layers_rejects_wrong_resolution(tmp_path):
    import pytest
    from src.screening import QAError, load_layers

    cfg = load_config(CONFIG)
    shape = (20, 20)
    aligned = tmp_path / cfg["paths"]["aligned_dir"]
    aligned.mkdir(parents=True)
    arrays = {
        "district_mask": np.ones(shape, dtype="uint8"),
        "worldcover": np.full(shape, 30, dtype="uint8"),
        "hansen_treecover2000": np.zeros(shape, dtype="uint8"),
        "hansen_lossyear": np.zeros(shape, dtype="uint8"),
        "hansen_gain": np.zeros(shape, dtype="uint8"),
        "slope_deg": np.full(shape, 4.0, dtype="float32"),
        "protected_areas": np.zeros(shape, dtype="uint8"),
    }
    prof = dict(driver="GTiff", height=shape[0], width=shape[1], count=1,
                crs="EPSG:32643", transform=from_origin(600000, 2500000, 30, 30),
                nodata=0)
    for key, arr in arrays.items():
        with rasterio.open(aligned / cfg["paths"]["layers"][key], "w", dtype=str(arr.dtype), **prof) as dst:
            dst.write(arr, 1)

    layers, _ = load_layers(cfg, tmp_path)
    assert abs(layers["_pixel_area_ha"] - 0.09) < 1e-9

    # Rewriting one layer at 10 m must fail before any hectare is reported.
    with rasterio.open(aligned / cfg["paths"]["layers"]["slope_deg"], "w",
                       **{**prof, "dtype": "float32",
                          "transform": from_origin(600000, 2500000, 10, 10)}) as dst:
        dst.write(np.full(shape, 4.0, dtype="float32"), 1)
    with pytest.raises(QAError, match="same grid|resolution"):
        load_layers(cfg, tmp_path)
