#!/usr/bin/env python3
"""P6/P7 — build a QGIS project (.qgs) referencing the FROZEN data layers.

Hand-built minimal-but-valid QGIS 3 project XML (no QGIS bindings in this
env): relative datasources, per-layer CRS/extent, default styling (restyle
in QGIS). Figures F1-F9 in outputs/figures mirror these layers. Rendering-
only scope: no data modified, no statistics computed.

Usage: python scripts/p6_build_qgis_project.py
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path
from xml.sax.saxutils import escape

import geopandas as gpd
import rasterio

ROOT = Path(__file__).resolve().parents[1]
FIGOUT = ROOT / "outputs/figures"
QGS = FIGOUT / "wayanad_observatory_site1.qgs"

FIGDIR_REL = "../../data/processed/"    # from outputs/figures/*.qgs
QA_REL = "../qaqc/"

def srs_block(crs_wkt_src):
    """Minimal spatialrefsys for EPSG:32643 or 4326."""
    if crs_wkt_src == "EPSG:32643":
        proj4, srid, authid, desc, svc = (
            "+proj=utm +zone=43 +datum=WGS84 +units=m +no_defs",
            "32643", "EPSG:32643", "WGS 84 / UTM zone 43N", "false_x 500000.0 false_y 0.0")
    else:
        proj4, srid, authid, desc, svc = (
            "+proj=longlat +datum=WGS84 +no_defs",
            "4326", "EPSG:4326", "WGS 84", "false_x 0.0 false_y 0.0")
    return f"""        <proj4>{proj4}</proj4>
        <srsid>{srid}</srsid>
        <srid>{srid}</srid>
        <authid>{authid}</authid>
        <description>{desc}</description>
        <projectionacronym>utm</projectionacronym>
        <ellipsoidacronym>WGS84</ellipsoidacronym>
        <geographicflag>{str(crs_wkt_src != 'EPSG:32643').lower()}</geographicflag>"""


RASTERS = [
    ("Copernicus DEM 30 m (topography)", "dem_copernicus30m_32643.tif"),
    ("Slope (degrees, P2)", "slope_deg_32643.tif"),
    ("H1 built-up change 2000-2020 (GLAD)", "builtup_change_2000_2020_32643.tif"),
    ("H1 built-up expansion 2000-2020 (GLAD)", "builtup_expansion_2000_2020_32643.tif"),
    ("ESA WorldCover 2021 (built-up check)", "builtup_worldcover2021_32643.tif"),
    ("Hansen tree cover 2000", "hansen_treecover2000_32643.tif"),
    ("Hansen treecover_loss 2000-2020", "treecover_loss_2000_2020_32643.tif"),
    ("D-20 CHIRPS rain annual total 2011-2014", "chirps_rain_annual_2011_2014_32643.tif"),
    ("D-20 CHIRPS Jun-Sep share 2011-2014", "chirps_rain_monsoon_share_2011_2014_32643.tif"),
    ("F6 incident KDE rank (display raster)", None, "f6_incident_kde_rank_500m_32643.tif"),
    ("H2a hazard KDE percentile (frozen)", None, "p3_h2a_kde_inventory_500m_32643.tif"),
    ("P7 D-21 display stack, 9 bands: built 2000/2020, expansion, forest "
     "2000/2020/2024, loss 2001-2024, loss 2021-2024, dominant loss decade",
     None, "p7_500m_display_32643.tif"),
]

VECTORS = [
    ("Wayanad district boundary (geoBoundaries ADM2)",
     FIGDIR_REL + "wayanad_boundary_32643.geojson", "Polygon"),
    ("Protected-area complexes (WDPA, all-touched)",
     FIGDIR_REL + "wdpa_wayanad_32643.gpkg|layername=wdpa", "Polygon"),
    ("Protected remnant parcels (1 km, P2)",
     FIGDIR_REL + "parcels_1km_32643.gpkg|layername=parcels", "Polygon"),
    ("Landslide inventory - WMS proxy (D-15/D-17a)",
     FIGDIR_REL + "inventory_wms_kl_landslides_new_32643.gpkg|layername=inventory_wms", "Polygon"),
    ("2024 Chooralmala-Mundakkai scar (NRSC VAP3 digitized)",
     FIGDIR_REL + "scar_chooralmala_mundakkai_2024_32643.gpkg|layername=scar", "Polygon"),
    ("Roads (OSM 2026-10)", FIGDIR_REL + "roads_wayanad_32643.gpkg|layername=roads", "LineString"),
    ("Google Open Buildings v3 (imagery <= 2023-05)",
     FIGDIR_REL + "buildings_google_wayanad_32643.gpkg|layername=buildings", "Polygon"),
    ("OSM buildings (snapshot 2026-10-26)",
     FIGDIR_REL + "buildings_osm_wayanad_32643.gpkg|layername=buildings", "Polygon"),
    ("Facility registry geocoded (P1 universe 123)", FIGDIR_REL + "registry_geocoded_2026-10-23.geojson", "Point"),
]


def maplayer_xml(name, datasource, kind, geom, srsxml, ext):
    uid = "{" + str(uuid.uuid4()) + "}"
    return f"""    <maplayer type="{kind}" id="{uid}" name="{escape(name)}"\n{'              ' if kind == 'vector' else ''}{
'geometry="' + geom + '">' if kind == 'vector' else '>'}
      <datasource>{escape(datasource)}</datasource>
      <provider>{'ogr' if kind == 'vector' else 'gdal'}</provider>
      <layername>{escape(name)}</layername>
      <srs>
        <spatialrefsys>
{srsxml}
        </spatialrefsys>
      </srs>
      <extent>
        <xmin>{ext[0]}</xmin>
        <ymax>{ext[3]}</ymax>
        <xmax>{ext[2]}</xmax>
        <ymin>{ext[1]}</ymin>
      </extent>
    </maplayer>"""


def main() -> int:
    tree_nodes, layers_nodes = [], []
    for spec in RASTERS:
        if len(spec) == 3:
            name, path = spec[0], QA_REL + spec[2]
            full = ROOT / "outputs/qaqc" / spec[2]
        else:
            name, path = spec[0], FIGDIR_REL + spec[1]
            full = ROOT / "data/processed" / spec[1]
        with rasterio.open(full) as src:
            b, crs = src.bounds, str(src.crs)
        ext = (b.left, b.bottom, b.right, b.top)
        sx = srs_block(crs)
        node = f"""    <maplayer type="raster" id="{{{uuid.uuid4()}}}" name="{escape(name)}">
      <datasource>{escape(path)}</datasource>
      <provider>gdal</provider>
      <layername>{escape(name)}</layername>
      <srs>
        <spatialrefsys>
{sx}
        </spatialrefsys>
      </srs>
      <extent>
        <xmin>{ext[0]}</xmin>
        <ymax>{ext[3]}</ymax>
        <xmax>{ext[2]}</xmax>
        <ymin>{ext[1]}</ymin>
      </extent>
    </maplayer>"""
        layers_nodes.append(node)
        tree_nodes.append(f"""<layer-tree-layer expanded="1" checked="Qt::Checked" id="{node.split('id="')[1].split('"')[0]}" source="{escape(path)}" name="{escape(name)}"/>""")

    for name, path, geom in VECTORS:
        full_str = path.split("|")[0].replace("../../data/processed/", "")
        full = ROOT / "data/processed" / full_str
        gdf = gpd.read_file(full)
        b = gdf.total_bounds
        crs = str(gdf.crs)
        ext = (b[0], b[1], b[2], b[3])
        sx = srs_block(crs)
        node = maplayer_xml(name, path, "vector", geom, sx, ext)
        layers_nodes.append(node)
        tree_nodes.append(f"""<layer-tree-layer expanded="1" checked="Qt::Checked" id="{node.split('id="')[1].split('"')[0]}" source="{escape(path)}" name="{escape(name)}"/>""")

    qgs = f"""<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.34.15-Prizren" projectname="tourism_observatory — Wayanad Site 1 (rendering-only P6/P7)">
  <projectCrs>
    <spatialrefsys>
      <proj4>+proj=utm +zone=43 +datum=WGS84 +units=m +no_defs</proj4>
      <srsid>32643</srsid>
      <srid>32643</srid>
      <authid>EPSG:32643</authid>
      <description>WGS 84 / UTM zone 43N</description>
      <projectionacronym>utm</projectionacronym>
      <ellipsoidacronym>WGS84</ellipsoidacronym>
      <geographicflag>false</geographicflag>
    </spatialrefsys>
  </projectCrs>
  <layer-tree-group>
{chr(10).join(tree_nodes)}
    <custom-order enabled="0"/>
  </layer-tree-group>
  <projectlayers>
{chr(10).join(layers_nodes)}
  </projectlayers>
</qgis>
"""
    FIGOUT.mkdir(parents=True, exist_ok=True)
    QGS.write_text(qgs)
    # sanity: XML well-formed?
    import xml.etree.ElementTree as ET
    ET.parse(QGS)
    n = len(layers_nodes)
    print(f"project written: {QGS.relative_to(ROOT)} ({n} layers; XML well-formed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
