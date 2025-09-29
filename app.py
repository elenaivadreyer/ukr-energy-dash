"""
Ukraine Energy Dashboard - Main Application Module.

This module contains the main Dash application for visualizing Ukraine's power stations.
It includes data loading, layout setup, callbacks for interactivity, and server configuration.
"""

import datetime as dt
import os
import uuid
from typing import Any

import dash
import dash_bootstrap_components as dbc
import geopandas as gpd
import pandas as pd
from dash import Input, Output, State, dcc, html
from dotenv import load_dotenv
from flask import Flask

# ================= Utilities =================
from components.utils import default_map_figure, generate_map_figure, get_station_details
from layouts.layout_main import get_main_layout, unique_oblasts


def _apply_power_source_filter(stations_df: gpd.GeoDataFrame, filter_type: str) -> gpd.GeoDataFrame:
    """
    Apply power source type filter to stations data.

    Args:
        stations_df: GeoDataFrame containing station data
        filter_type: Type of filter to apply ('renewable', 'fossil', 'nuclear')

    Returns:
        Filtered GeoDataFrame

    """
    if filter_type == "all":
        return stations_df

    # Define categories
    renewable = {"solar", "hydro", "wind", "biomass", "biogas", "waste", "wood"}
    fossil = {"coal", "gas", "oil", "diesel", "mazut"}

    # Always include substations
    substations_df = stations_df[stations_df["power"] == "substation"]
    plants_df = stations_df[stations_df["power"] == "plant"]

    if filter_type == "renewable":
        # Filter for renewable plants
        renewable_plants = plants_df[
            plants_df["plant:source"].apply(
                lambda sources: any(fuel in renewable for fuel in str(sources).split(";")) if pd.notna(sources) else False
            )
        ]
        return pd.concat([renewable_plants, substations_df], ignore_index=True)

    elif filter_type == "fossil":
        # Filter for fossil fuel plants
        fossil_plants = plants_df[
            plants_df["plant:source"].apply(
                lambda sources: any(fuel in fossil for fuel in str(sources).split(";")) if pd.notna(sources) else False
            )
        ]
        return pd.concat([fossil_plants, substations_df], ignore_index=True)

    elif filter_type == "nuclear":
        # Filter for nuclear plants
        nuclear_plants = plants_df[
            plants_df["plant:source"].apply(
                lambda sources: "nuclear" in str(sources).split(";") if pd.notna(sources) else False
            )
        ]
        return pd.concat([nuclear_plants, substations_df], ignore_index=True)

    return stations_df

# ================= Load Data =================
stations_df = gpd.read_file("assets/data/power_stations_with_oblasts.geojson").set_geometry("geometry")
stations_df = stations_df.to_crs(4326)
if "centroid" not in stations_df.columns:
    stations_df["centroid"] = stations_df.geometry.centroid

oblasts_gdf = gpd.read_file("assets/data/ukraine_oblasts.geojson").set_geometry("geometry")
outer_ukraine = gpd.read_file("assets/data/full_ukraine.geojson").set_geometry("geometry")

# ================= Env =================
load_dotenv()
server = Flask(__name__)

# ================= App Setup =================
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Kaisei+Decol&family=Libre+Franklin:wght@100..900&display=swap",
    ],
    server=server,
)
server.secret_key = os.getenv("FLASK_SECRET_KEY", str(uuid.uuid4()))

app.layout = get_main_layout(unique_oblasts, stations_df)

app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <!-- Font Awesome -->
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""


# ================= Filter Stores =================
@app.callback(Output("gppd-filter-store", "data"), Input("gppd-filter", "value"))
def store_gppd_filter(value: list[str]) -> dict[str, bool]:
    """
    Store GPPD filter state in dcc.Store component.

    Args:
        value: List of selected filter values

    Returns:
        Dictionary with enabled state for GPPD filter

    """
    return {"enabled": "gppd" in value}


@app.callback(Output("power-source-filter-store", "data"), Input("power-source-filter", "value"))
def store_power_source_filter(value: str) -> dict[str, str]:
    """
    Store power source filter state in dcc.Store component.

    Args:
        value: Selected filter value

    Returns:
        Dictionary with type state for power source filter

    """
    return {"type": value}


# ================= Map Callback =================
@app.callback(
    Output("map-display", "figure"),
    [
        Input("oblast-dropdown", "value"),
        Input("map-display", "clickData"),
        Input("map-display", "relayoutData"),
        Input("map-display", "selectedData"),
        Input("gppd-filter-store", "data"),
        Input("power-source-filter-store", "data"),
    ],
    State("map-view-store-mainpage", "data"),
    prevent_initial_call=False,
)
def update_map(
    selected_oblast: str | None,
    click_data: dict[str, Any] | None,
    relayout_data: dict[str, Any] | None,
    selected_data: dict[str, Any] | None,
    gppd_store: dict[str, bool],
    power_source_store: dict[str, str],
    store_data: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Update the map visualization based on user interactions and filters.

    Args:
        selected_oblast: Currently selected oblast from dropdown
        click_data: Data from map click events
        relayout_data: Data from map zoom/pan events
        selected_data: Data from lasso/box selection
        gppd_store: GPPD filter state
        power_source_store: Power source filter state
        store_data: Stored map view state

    Returns:
        Dictionary containing the updated map figure

    """
    ctx = dash.callback_context
    triggered = ctx.triggered[0]["prop_id"] if ctx.triggered else ""
    ignore_click = "oblast-dropdown" in triggered  # ignore stale click

    # 🔹 Apply GPPD filter
    filtered_stations = stations_df.copy()
    if gppd_store and gppd_store.get("enabled"):
        filtered_stations = filtered_stations[filtered_stations["gppd_overlap"]]

    # 🔹 Apply power source filter
    if power_source_store and power_source_store.get("type") != "all":
        filter_type = power_source_store.get("type")
        filtered_stations = _apply_power_source_filter(filtered_stations, filter_type)

    # ---------------- Map Logic ----------------
    if "map-display.relayoutData" in triggered:
        if selected_oblast:
            return generate_map_figure(
                filtered_stations,
                oblasts_gdf,
                selected_oblast=selected_oblast,
                click_data=None,
                reset=True,
                outer_ukraine=outer_ukraine,
            )
        else:
            return default_map_figure(filtered_stations, outer_ukraine=outer_ukraine)

    if "oblast-dropdown" in triggered:
        return generate_map_figure(
            filtered_stations,
            oblasts_gdf,
            selected_oblast=selected_oblast,
            click_data=None,
            reset=False,
            outer_ukraine=outer_ukraine,
        )

    if "map-display.clickData" in triggered and click_data and not ignore_click:
        return generate_map_figure(
            filtered_stations,
            oblasts_gdf,
            selected_oblast=selected_oblast,
            click_data=click_data,
            reset=False,
            outer_ukraine=outer_ukraine,
        )

    if "map-display.selectedData" in triggered:
        return generate_map_figure(
            filtered_stations,
            oblasts_gdf,
            selected_oblast=selected_oblast,
            click_data=None,
            reset=False,
            outer_ukraine=outer_ukraine,
        )

    # Default fallback
    return generate_map_figure(
        filtered_stations,
        oblasts_gdf,
        selected_oblast=selected_oblast,
        click_data=None,
        reset=False,
        outer_ukraine=outer_ukraine,
    )


# ================= Station Sidebar =================
@app.callback(
    Output("station-details", "children"),
    [
        Input("map-display", "clickData"),
        Input("map-display", "relayoutData"),
        Input("oblast-dropdown", "value"),
        Input("gppd-filter-store", "data"),
        Input("power-source-filter-store", "data"),
    ],
    prevent_initial_call=False,
)
def update_station_details(
    click_data: dict[str, Any] | None,
    relayout_data: dict[str, Any] | None,
    selected_oblast: str | None,
    gppd_filter: dict[str, bool] | None,
    power_source_filter: dict[str, str] | None,
) -> html.Div | str:
    """
    Update station details panel based on map clicks and interactions.

    Args:
        click_data: Data from map click events
        relayout_data: Data from map zoom/pan events
        selected_oblast: Currently selected oblast
        gppd_filter: GPPD filter state

    Returns:
        HTML Div with station details or message string

    """
    ctx = dash.callback_context
    triggered = ctx.triggered[0]["prop_id"] if ctx.triggered else ""

    # Clear station details when dropdown changes, map is manipulated (zoom/pan), or filters change
    if "oblast-dropdown" in triggered or "relayoutData" in triggered or "gppd-filter-store" in triggered:
        return ""

    if click_data and "points" in click_data and len(click_data["points"]) > 0:
        point = click_data["points"][0]
        station_index = point.get("customdata")
        if station_index is not None and station_index in stations_df.index:
            station_row = stations_df.loc[int(station_index)]
            return get_station_details(station_row)

    return ""


# ================= Lasso / Selected Stations Table =================
@app.callback(
    Output("stations-table", "data"),
    Input("oblast-dropdown", "value"),
    Input("gppd-filter-store", "data"),
    Input("power-source-filter-store", "data"),
    Input("map-display", "selectedData"),
    prevent_initial_call=False,
)
def update_table(
    selected_oblast: str | None, 
    gppd_filter: dict[str, bool] | None, 
    power_source_filter: dict[str, str] | None,
    selected_data: dict[str, Any] | None
) -> list[dict[str, Any]]:
    """
    Update the stations table based on filters and selections.

    Args:
        selected_oblast: Currently selected oblast from dropdown
        gppd_filter: GPPD filter state
        power_source_filter: Power source filter state
        selected_data: Data from lasso/box selection on map

    Returns:
        List of station records for the data table

    """
    df = stations_df.copy()

    # filter by oblast
    if selected_oblast:
        df = df[df["oblast_name_en"] == selected_oblast]

    # apply GPPD filter
    if gppd_filter and gppd_filter.get("enabled"):
        df = df[df["gppd_overlap"]]

    # apply power source filter
    if power_source_filter and power_source_filter.get("type") != "all":
        filter_type = power_source_filter.get("type")
        df = _apply_power_source_filter(df, filter_type)

    # filter by lasso selection
    if selected_data and "points" in selected_data:
        indices = [pt.get("customdata") for pt in selected_data["points"] if pt.get("customdata") in stations_df.index]
        if indices:
            df = stations_df.loc[indices]

    if df.empty:
        return []

    return df[
        ["name", "station_name_en", "power", "plant:source", "plant:method", "oblast_name_en", "gppd_overlap"]
    ].to_dict("records")


# 2) Download callback
@app.callback(
    Output("download-data", "data"),
    Input("download-button", "n_clicks"),
    State("stations-table", "data"),
    prevent_initial_call=True,
)
def generate_excel_download(n_clicks: int | None, table_data: list[dict[str, Any]] | None) -> dict[str, Any] | None:
    """
    Generate Excel download for the current table data.

    Args:
        n_clicks: Number of times download button was clicked
        table_data: Current data in the stations table

    Returns:
        Download data for dcc.Download component or None

    """
    if not table_data:
        return None

    df = pd.DataFrame(table_data)
    timestamp = dt.datetime.now().strftime("%Y%m%d")

    # Use dcc.send_data_frame to send the Excel file
    return dcc.send_data_frame(
        df.to_excel, f"ukraine_power_stations_osm_{timestamp}.xlsx", index=False, engine="openpyxl"
    )


# ================= Run Server =================
if __name__ == "__main__":
    app.run(debug=True)
