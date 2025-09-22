import requests
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, LineString, Polygon, MultiPolygon
from pathlib import Path
from typing import Optional


OVERPASS_URL = "https://overpass-api.de/api/interpreter"
DATA_ASSETS_PATH = Path("/workspaces/ukr_energy_dash/assets/data")
DATA_ASSETS_PATH.mkdir(parents=True, exist_ok=True)

# -----------------------
# FUNCTIONS
# -----------------------
def fetch_overpass_data(query: str) -> dict:
    r = requests.post(OVERPASS_URL, data={"data": query}, timeout=180)
    r.raise_for_status()
    return r.json()

def elements_to_geodataframe(data: dict) -> gpd.GeoDataFrame:
    """Convert Overpass JSON → GeoDataFrame (points/lines/polygons)."""
    node_by_id = {el["id"]: el for el in data["elements"] if el["type"] == "node"}
    way_by_id = {el["id"]: el for el in data["elements"] if el["type"] == "way"}

    features = []
    for el in data["elements"]:
        geom = None
        if el["type"] == "node":
            geom = Point(el["lon"], el["lat"])
        elif el["type"] == "way":
            coords = [(node_by_id[n]["lon"], node_by_id[n]["lat"]) for n in el.get("nodes", []) if n in node_by_id]
            if coords:
                geom = Polygon(coords) if coords[0] == coords[-1] else LineString(coords)
        elif el["type"] == "relation":
            polys = []
            for m in el.get("members", []):
                if m["type"] == "way" and m.get("role") in ["outer", ""]:
                    way = way_by_id.get(m["ref"])
                    if way:
                        coords = [(node_by_id[n]["lon"], node_by_id[n]["lat"]) for n in way.get("nodes", []) if n in node_by_id]
                        if coords and coords[0] == coords[-1]:
                            polys.append(Polygon(coords))
            if polys:
                geom = MultiPolygon(polys) if len(polys) > 1 else polys[0]

        if geom:
            features.append({
                "osm_id": el["id"],
                "osm_type": el["type"],
                **el.get("tags", {}),
                "geometry": geom
            })

    return gpd.GeoDataFrame(features, crs="EPSG:4326")

def filter_power_stations(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    mask = (
        gdf.get("plant:source").notna() |
        (gdf.get("substation") == "transmission")
    )
    gdf = gdf[mask].drop_duplicates(subset=["osm_id", "osm_type"])
    # reduce columns
    cols_to_keep = ['osm_id', 'osm_type', 'power', 'substation', 'name', 'name:en', 'operator',
                    'operator:en', 'barrier', 'voltage', 'landuse', 'plant:method', 'plant:output:electricity',
                    'plant:source', 'geometry']
    gdf = gdf[[col for col in cols_to_keep if col in gdf.columns]]
    # rename columns
    gdf = gdf.rename(columns={
        "name:en": "station_name_en"
    })
    return gdf

def assign_oblasts(
    stations_gdf: gpd.GeoDataFrame,
    gadm_url: str = "https://geodata.ucdavis.edu/gadm/gadm4.1/gpkg/gadm41_UKR.gpkg",
    swap_dict: Optional[dict] = None
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

    # Spatial join (stations to oblasts)
    stations = stations_gdf.to_crs(gdf_oblasts.crs)
    matched = gpd.sjoin(
        stations,
        gdf_oblasts,
        how="left",
        predicate="within"
    ).drop(columns=["index_right"])

    return matched, gdf_oblasts


def match_with_gppd(ukraine_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Add a boolean column 'gppd_overlap' to ukraine_gdf,
    True if any GPPD plant lies within 500 m of the station.
    """
    url = "https://github.com/wri/global-power-plant-database/raw/master/output_database/global_power_plant_database.csv"
    df_gppd = pd.read_csv(url, low_memory=False)  # suppress dtype warning
    gdf_gppd = gpd.GeoDataFrame(
        df_gppd,
        geometry=gpd.points_from_xy(df_gppd["longitude"], df_gppd["latitude"]),
        crs="EPSG:4326"
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
        predicate="intersects"
    )

    # Collapse → True if at least one match per station
    overlap_flags = joined.groupby("index")["index_right"].apply(lambda x: x.notna().any())

    # Assign back
    ukraine_gdf = ukraine_gdf.copy()
    ukraine_gdf["gppd_overlap"] = ukraine_gdf.index.map(overlap_flags)

    return ukraine_gdf


def main():
    QUERY = """
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

    print("Downloading OSM power stations...")
    data = fetch_overpass_data(QUERY)
    gdf = elements_to_geodataframe(data)
    gdf = filter_power_stations(gdf)

    print("Assigning oblasts...")
    gdf, oblasts_gdf = assign_oblasts(gdf)

    print("Matching with GPPD...")
    gdf = match_with_gppd(gdf)

    # Save outputs
    stations_path = DATA_ASSETS_PATH / "power_stations_with_oblasts.geojson"
    oblasts_path = DATA_ASSETS_PATH / "ukraine_oblasts.geojson"

    gdf.to_file(stations_path, driver="GeoJSON")
    oblasts_gdf.to_file(oblasts_path, driver="GeoJSON")

    print(f"✅ Saved stations → {stations_path}")
    print(f"✅ Saved oblasts → {oblasts_path}")

if __name__ == "__main__":
    main()
