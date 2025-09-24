"""
Data processing module for Ukraine Energy Dashboard.

This module provides functions for fetching and processing power station data
from OpenStreetMap using the Overpass API and matching with the Global Power
Plant Database (GPPD).
"""

import logging
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import LineString, MultiPolygon, Point, Polygon

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
DATA_ASSETS_PATH = Path(__file__).parent.parent / "assets" / "data"
DATA_ASSETS_PATH.mkdir(parents=True, exist_ok=True)


def fetch_overpass_data(query: str) -> dict[str, Any]:
    """
    Fetch data from Overpass API using the provided query.

    Args:
        query: Overpass QL query string

    Returns:
        JSON response from Overpass API as dictionary

    Raises:
        requests.HTTPError: If the request fails

    """
    r = requests.post(OVERPASS_URL, data={"data": query}, timeout=180)
    r.raise_for_status()
    return r.json()


def elements_to_geodataframe(data: dict) -> gpd.GeoDataFrame:
    """
    Convert Overpass JSON → GeoDataFrame (points/lines/polygons). Only keeps elements with valid geometries.

    Args:
        data: JSON response from Overpass API

    Returns:
        GeoDataFrame with geometries.

    """
    # Map nodes and ways
    node_by_id = {el["id"]: el for el in data["elements"] if el["type"] == "node"}
    way_by_id = {el["id"]: el for el in data["elements"] if el["type"] == "way"}

    features = []

    for el in data["elements"]:
        geom = None

        if el["type"] == "node":
            if "lon" in el and "lat" in el:
                geom = Point(el["lon"], el["lat"])

        elif el["type"] == "way":
            coords = [(node_by_id[n]["lon"], node_by_id[n]["lat"]) for n in el.get("nodes", []) if n in node_by_id]
            if coords:
                if coords[0] == coords[-1] and len(coords) >= 4:
                    poly = Polygon(coords)
                    if poly.is_valid and not poly.is_empty:
                        geom = poly
                else:
                    line = LineString(coords)
                    if line.is_valid and not line.is_empty:
                        geom = line

        elif el["type"] == "relation":
            polys = []
            for m in el.get("members", []):
                if m["type"] == "way" and m.get("role") in ["outer", ""]:
                    way = way_by_id.get(m["ref"])
                    if way:
                        coords = [
                            (node_by_id[n]["lon"], node_by_id[n]["lat"])
                            for n in way.get("nodes", [])
                            if n in node_by_id
                        ]
                        if len(coords) >= 3:  # relaxed: allow polygons even if not perfectly closed
                            try:
                                poly = Polygon(coords)
                                if poly.is_valid:
                                    polys.append(poly)
                            except Exception:
                                logger.warning(f"Invalid polygon for way {way['id']} in relation {el['id']}")
                                continue
            if polys:
                geom = MultiPolygon(polys) if len(polys) > 1 else polys[0]

        # Only keep elements with valid geometry
        if geom is not None and geom.is_valid and not geom.is_empty:
            features.append({"osm_id": el["id"], "osm_type": el["type"], **el.get("tags", {}), "geometry": geom})

    return gpd.GeoDataFrame(features, crs="EPSG:4326")


def filter_power_stations(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Filter GeoDataFrame to keep only power stations and transmission substations.

    Args:
        gdf: GeoDataFrame containing OpenStreetMap power infrastructure data

    Returns:
        Filtered GeoDataFrame with only relevant power stations and substations

    """
    # important filter
    mask = gdf.get("plant:source").notna() | (gdf.get("substation") == "transmission")
    gdf = gdf[mask].drop_duplicates(subset=["osm_id", "osm_type"])
    # reduce columns
    cols_to_keep = [
        "osm_id",
        "osm_type",
        "power",
        "substation",
        "name",
        "name:en",
        "operator",
        "operator:en",
        "barrier",
        "voltage",
        "landuse",
        "plant:method",
        "plant:output:electricity",
        "plant:source",
        "geometry",
    ]
    gdf = gdf[[col for col in cols_to_keep if col in gdf.columns]]
    # rename columns
    gdf = gdf.rename(columns={"name:en": "station_name_en"})
    return gdf


def assign_oblasts(
    stations_gdf: gpd.GeoDataFrame,
    gadm_url: str = "https://geodata.ucdavis.edu/gadm/gadm4.1/gpkg/gadm41_UKR.gpkg",
    swap_dict: dict | None = None,
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Assign each power station to a Ukrainian oblast and also return oblast polygons.

    Returns:
        stations_with_oblasts: GeoDataFrame of stations with 'oblast_name_en'
        oblasts_gdf: GeoDataFrame of oblast polygons (oblast_name_en + geometry)

    """
    gdf_oblasts = gpd.read_file(gadm_url, layer="ADM_ADM_1")

    # Clean up oblast polygons
    gdf_oblasts = gdf_oblasts.rename(columns={"NAME_1": "oblast_name_en"})
    gdf_oblasts = gdf_oblasts[["oblast_name_en", "geometry"]]

    if swap_dict is None:
        swap_dict = {
            "Khmel'nyts'kyy": "Khmelnytskyi",
            "Donets'k": "Donetsk",
            "Dnipropetrovs'k": "Dnipropetrovsk",
            "Luhans'k": "Luhansk",
            "L'viv": "Lviv",
            "Sevastopol'": "Sevastopol",
            "Ivano-Frankivs'k": "Ivano-Frankivsk",
            "Ternopil'": "Ternopil",
        }

    gdf_oblasts["oblast_name_en"] = gdf_oblasts["oblast_name_en"].replace(swap_dict)

    # Reproject stations
    stations = stations_gdf.to_crs(gdf_oblasts.crs)

    # First pass: strict 'within'
    matched_within = gpd.sjoin(stations, gdf_oblasts, how="left", predicate="within").drop(columns=["index_right"])

    # Find stations that weren't matched
    unmatched = matched_within[matched_within["oblast_name_en"].isna()].copy()

    if not unmatched.empty:
        # Second pass: more relaxed 'intersects'
        matched_intersects = gpd.sjoin(
            unmatched.drop(columns=["oblast_name_en"]),
            gdf_oblasts,
            how="left",
            predicate="intersects",
        ).drop(columns=["index_right"])

        # If multiple matches per station, keep the first
        matched_intersects = matched_intersects.groupby(matched_intersects.index).first()

        # Fill NaNs in the first pass with results from intersects
        matched_within.loc[matched_intersects.index, "oblast_name_en"] = matched_intersects["oblast_name_en"]

    return matched_within, gdf_oblasts


def match_with_gppd(ukraine_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Add a boolean column 'gppd_overlap' to ukraine_gdf.

    Checks if any GPPD plant lies within 500 m of the station.

    Args:
        ukraine_gdf: GeoDataFrame containing Ukrainian power stations

    Returns:
        GeoDataFrame with added 'gppd_overlap' boolean column

    """
    url = (
        "https://github.com/wri/global-power-plant-database/raw/master/output_database/global_power_plant_database.csv"
    )
    df_gppd = pd.read_csv(url, low_memory=False)  # suppress dtype warning
    gdf_gppd = gpd.GeoDataFrame(
        df_gppd, geometry=gpd.points_from_xy(df_gppd["longitude"], df_gppd["latitude"]), crs="EPSG:4326"
    )
    gdf_gppd_ua = gdf_gppd[gdf_gppd["country_long"] == "Ukraine"].to_crs(3857)

    # Buffer OSM stations
    gdf_buffered = ukraine_gdf.to_crs(3857).copy()
    gdf_buffered["geometry"] = gdf_buffered.geometry.buffer(500)

    # Spatial join: each station may appear multiple times if overlaps multiple GPPD points
    joined = gpd.sjoin(
        gdf_buffered.reset_index(),  # keep original index as column
        gdf_gppd_ua[["geometry"]],
        how="left",
        predicate="intersects",
    )

    # Collapse → True if at least one match per station
    overlap_flags = joined.groupby("index")["index_right"].apply(lambda x: x.notna().any())

    # Print stats for GPPD plants
    matched_gppd = joined["index_right"].dropna().unique()
    n_matched_gppd = len(matched_gppd)
    n_total_gppd = len(gdf_gppd_ua)
    print(f"{n_matched_gppd}/{n_total_gppd} GPPD plants matched with OSM stations")

    # Assign back
    ukraine_gdf = ukraine_gdf.copy()
    ukraine_gdf["gppd_overlap"] = ukraine_gdf.index.map(overlap_flags)

    return ukraine_gdf


def fetch_critical_relations(osm_ids: list[int]) -> dict:
    """Fetch full geometry for critical multipolygon relations."""
    import itertools

    critical_data_list = []
    for osm_id in osm_ids:
        query = f"""
        [out:json][timeout:180];
        relation({osm_id});
        out geom qt;
        """
        data = fetch_overpass_data(query)
        critical_data_list.append(data)

    # Flatten all elements from individual responses
    critical_elements = list(itertools.chain.from_iterable(d["elements"] for d in critical_data_list))
    return {"elements": critical_elements}


def main() -> None:
    """
    Main function to process Ukrainian power stations data.

    Implements two-step fetch: bulk skeleton + individual critical multipolygons.
    """
    # --- Bulk skeleton query ---
    bulk_query = """
    [out:json][timeout:180];
    area["ISO3166-1"="UA"][admin_level=2]->.a;
    (
      node["power"="plant"](area.a);
      way["power"="plant"](area.a);
      relation["power"="plant"](area.a);
      node["power"="substation"]["substation"="transmission"](area.a);
      way["power"="substation"]["substation"="transmission"](area.a);
      relation["power"="substation"]["substation"="transmission"](area.a);
    );
    out body; >; out skel qt;
    """
    print("Downloading bulk OSM power stations (skeleton)...")
    bulk_data = fetch_overpass_data(bulk_query)

    # --- Critical multipolygon relations ---
    critical_relations = [7317657]  # Kakhovka HPP, add others as needed
    print(f"Downloading critical relations with full geometry: {critical_relations}")
    critical_data = fetch_critical_relations(critical_relations)

    # --- Combine bulk + critical elements ---
    all_elements = bulk_data["elements"] + critical_data["elements"]
    combined_data = {"elements": all_elements}

    # --- Convert to GeoDataFrame ---
    gdf = elements_to_geodataframe(combined_data)
    print(f"Total features after conversion: {len(gdf)}")

    # --- Filter valid power stations / substations ---
    gdf = filter_power_stations(gdf)
    print(f"Total features after filtering: {len(gdf)}")

    # --- Assign oblasts ---
    gdf, oblasts_gdf = assign_oblasts(gdf)

    # --- Match with GPPD ---
    gdf = match_with_gppd(gdf)

    # --- Save outputs ---
    stations_path = DATA_ASSETS_PATH / "power_stations_with_oblasts.geojson"
    oblasts_path = DATA_ASSETS_PATH / "ukraine_oblasts.geojson"
    gdf.to_file(stations_path, driver="GeoJSON")
    oblasts_gdf.to_file(oblasts_path, driver="GeoJSON")

    print(f"✅ Saved stations → {stations_path}")
    print(f"✅ Saved oblasts → {oblasts_path}")


if __name__ == "__main__":
    main()
