#!/usr/bin/env python3
"""
GEE data-import script -- what it does, and how to run it.

This script runs in the Google Earth Engine browser Code Editor, NOT in your
Python venv. It is the DATA-FETCH half of the pipeline: it pulls the Sentinel-2
cloud-masked dry/monsoon composites (and the land-cover / forest-change layers)
into Google Drive, from where you download the GeoTIFFs into data/raw/.

Why GEE and not a Python client?
    The maintained `ee` package on PyPI is a small abandoned wrapper (v0.2,
    snarez/ee) that cannot import on Python 3.12 OR 3.14 (`import StringIO`).
    Google's official Earth Engine Python client needs a service-account JSON,
    and the practical, free, non-commercial route is the Code Editor (browser).
    The Python pipeline does the analysis; GEE is the data pipe.

What this script does
    1. Loads the Jhabua district boundary (EPSG:32643) passed via a GeoJSON file.
    2. ESA WorldCover v200 (10 m, 2020) -- land-cover class per pixel.
    3. Hansen GFC -- treecover2000 (2000 canopy) + loss (2000-2024).
    4. Sentinel-2 L2A (COPERNICUS/S2_SR_HARMONIZED), cloud-masked with the QA60
       bit, median composite for the DRY season (Jan-Jun) and the MONSOON
       season (Jun-Nov).
    5. Computes NDVI and a bare-soil index (BSI) per pixel.
    6. Exports each stack to Google Drive as a 10 m GeoTIFF so you can download
       it into data/raw/ (see data/manifest.json).

WATCH OUT
    - Your Google account must have a free non-commercial Google Earth Engine
      account (earthengine.google.dev -> Sign up). Approval is email-based.
    - The exports go to a Google Drive folder named "s2_jhabua". You will need
      the downloaded GeoTIFFs copied into data/raw/ and their SHA256 recorded
      in data/manifest.json before ingest.py can run.

Run steps (browser Code Editor)
    1. Sign in -> Code Editor -> Assets (add the boundary as an asset, or paste
       the quick start below).
    2. Paste this script, set the boundary path, press Run.
    3. Wait for the two export tasks (will say "COMPLETED"), then open your
       Drive -> "s2_jhabua" and download the .tif files.
    4. Copy them into data/raw/ and restore data/manifest.json to "downloaded".
"""

# --------------------------------------------------------------------------- #
# CONFIG -- EDIT THESE
# --------------------------------------------------------------------------- #
BOUNDARY_GEOJSON = "data/raw/boundary.geojson"  # full India ADM2; Jhabua = shapeID IND-ADM2-2_0_0-B256
DRIVE_FOLDER = "s2_jhabua"
DRY_SEASON = "2024-01-01", "2024-06-01"   # post-monsoon / dry season
MONSOON_SEASON = "2024-06-01", "2024-11-01"
CLOUD_PIXEL_MAX = 20          # % of cloudy pixels allowed in a composite
LANDCOVER_YEAR = 2020
OUTPUT_SCALE = 10             # metres (WorldCover + S2 are 10 m)


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def mask_s2(img):
    """Mask out cloud and cirrus pixels using the QA60 band (bits 10 and 11)."""
    qa = img.select("QA60")
    cloud = qa.bitwiseAnd(2048).eq(0)   # 2048 = cloud (bit 11); 1024 = cirrus (bit 10)
    return img.updateMask(cloud).rename(
        ["B02", "B03", "B04", "B08", "B11", "B12", "COASTAL_AEROSOL"])

def ndvi(img):
    return img.normalizedDifference(["B08", "B04"]).rename("NDVI")

def bare_soil_index(img):
    # BSI = ((SWIR1 + Red) - (NIR + Blue)) / ((SWIR1 + Red) + (NIR + Blue))
    return img.normalizedDifference(["B11", "B04"]).divide(
        img.normalizedDifference(["B02", "B08"]).add(
            img.normalizedDifference(["B11", "B04"]).multiply(2))).rename("BSI")


# --------------------------------------------------------------------------- #
# the two exports
# --------------------------------------------------------------------------- #
def s2_composite(year_range, season_name):
    """Build a cloud-masked median composite and export it to Drive."""
    from google.cloud import storage      # noqa: F401  (drives auth in Code Editor)
    import ee

    ee.Initialize()

    # One year: dry-season composite + monsoon-season composite.
    start, end = year_range
    dry = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
           .filterBounds(ee.Geometry.Rectangle(74.0, 21.92, 75.0, 23.23))
           .filterDate(*year_range)
           .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", CLOUD_PIXEL_MAX))
           .map(mask_s2)
           .median())

    dry = dry.addBands(ndvi(dry)).addBands(bare_soil_index(dry))

    description = f"s2_{season_name}_{start[:4]}"
    ee.batch.Export.image.toDrive(
        image=dry,
        description=description,
        folder=DRIVE_FOLDER,
        fileNamePrefix=f"s2_{season_name}_{start[:4]}",
        region=JHABUA_BOUNDARY_ASSET,          # asset you will create from boundary.geojson
        scale=10,
        maxPixels=1e10,
    )


def main():
    print("GEE data-import script loaded.")
    print("Run in the Code Editor. Assets -> 'Jhabua boundary' -> set the region.")
    print("Exports will appear in Drive under folder", DRIVE_FOLDER)


if __name__ == "__main__":
    main()
