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


def _apply_power_source_filter(stations_df: gpd.GeoDataFrame, filter_type: str, include_substations: bool = True) -> gpd.GeoDataFrame:
    """
    Apply power source type filter to stations data.

    Args:
        stations_df: GeoDataFrame containing station data
        filter_type: Type of filter to apply ('thermal', 'nuclear', 'renewable')
        include_substations: Whether to include substations in the filtered result

    Returns:
        Filtered GeoDataFrame

    """
    if filter_type == "all":
        return stations_df

    # Define categories based on new classification
    # Thermal: heat-based, usually combustion
    thermal = {"coal", "gas", "oil", "diesel", "mazut", "biogas", "biomass", "wood", "waste"}
    nuclear = {"nuclear"}
    # Renewables: non-thermal (solar, wind, hydro)
    renewable = {"solar", "wind", "hydro"}

    # Get plants only first
    plants_df = stations_df[stations_df["power"] == "plant"]

    if filter_type == "thermal":
        # Filter for thermal plants (all heat-based combustion sources)
        filtered_plants = plants_df[
            plants_df["plant:source"].apply(
                lambda sources: any(fuel in thermal for fuel in str(sources).split(";")) if pd.notna(sources) else False
            )
        ]
    elif filter_type == "nuclear":
        # Filter for nuclear plants
        filtered_plants = plants_df[
            plants_df["plant:source"].apply(
                lambda sources: "nuclear" in str(sources).split(";") if pd.notna(sources) else False
            )
        ]
    elif filter_type == "renewable":
        # Filter for renewable plants (non-thermal: solar, wind, hydro)
        filtered_plants = plants_df[
            plants_df["plant:source"].apply(
                lambda sources: any(fuel in renewable for fuel in str(sources).split(";")) if pd.notna(sources) else False
            )
        ]
    else:
        filtered_plants = plants_df

    # Add substations if requested
    if include_substations:
        substations_df = stations_df[stations_df["power"] == "substation"]
        return pd.concat([filtered_plants, substations_df], ignore_index=True)
    else:
        return filtered_plants

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


@app.callback(Output("substations-filter-store", "data"), Input("substations-filter", "value"))
def store_substations_filter(value: list[str]) -> dict[str, bool]:
    """
    Store substations filter state in dcc.Store component.

    Args:
        value: List of selected filter values

    Returns:
        Dictionary with enabled state for substations filter

    """
    return {"enabled": "substations" in value}


@app.callback(
    [
        Output("power-source-filter-store", "data"),
        Output("power-source-all", "className"),
        Output("power-source-thermal", "className"),
        Output("power-source-nuclear", "className"),
        Output("power-source-renewable", "className"),
    ],
    [
        Input("power-source-all", "n_clicks"),
        Input("power-source-thermal", "n_clicks"),
        Input("power-source-nuclear", "n_clicks"),
        Input("power-source-renewable", "n_clicks"),
    ],
)
def update_power_source_filter(all_clicks, thermal_clicks, nuclear_clicks, renewable_clicks):
    """
    Update power source filter based on button clicks.

    Args:
        all_clicks: Number of clicks on "All Sources" button
        thermal_clicks: Number of clicks on "Thermal" button
        nuclear_clicks: Number of clicks on "Nuclear" button
        renewable_clicks: Number of clicks on "Renewable" button

    Returns:
        Tuple of (store_data, all_className, thermal_className, nuclear_className, renewable_className)

    """
    ctx = dash.callback_context
    if not ctx.triggered:
        # Default state
        return (
            {"type": "all"},
            "power-source-btn power-source-btn-active",
            "power-source-btn",
            "power-source-btn",
            "power-source-btn",
        )

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    # Reset all button classes
    base_class = "power-source-btn"
    active_class = "power-source-btn power-source-btn-active"
    
    all_class = base_class
    thermal_class = base_class
    nuclear_class = base_class
    renewable_class = base_class
    
    if button_id == "power-source-all":
        all_class = active_class
        selected_type = "all"
    elif button_id == "power-source-thermal":
        thermal_class = active_class
        selected_type = "thermal"
    elif button_id == "power-source-nuclear":
        nuclear_class = active_class
        selected_type = "nuclear"
    elif button_id == "power-source-renewable":
        renewable_class = active_class
        selected_type = "renewable"
    else:
        all_class = active_class
        selected_type = "all"
    
    return (
        {"type": selected_type},
        all_class,
        thermal_class,
        nuclear_class,
        renewable_class,
    )


@app.callback(
    [Output("substations-filter", "value"), Output("substations-filter", "options")],
    Input("power-source-filter", "value"),
    State("substations-filter", "value"),
)
def update_substations_filter(power_source: str, current_substations: list[str]) -> tuple[list[str], list[dict]]:
    """
    Automatically turn off substations when power source is not 'all'.

    Args:
        power_source: Currently selected power source filter value
        current_substations: Current substations filter value

    Returns:
        Tuple of (new substations value, substations options with disabled state)

    """
    if power_source != "all":
        # When power source is filtered, turn off substations
        return [], [{"label": "", "value": "substations", "disabled": True}]
    else:
        # When showing all sources, enable substations
        return current_substations, [{"label": "", "value": "substations", "disabled": False}]


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
        Input("substations-filter-store", "data"),
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
    substations_store: dict[str, bool],
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
        substations_store: Substations filter state
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
        filtered_stations = _apply_power_source_filter(filtered_stations, filter_type, include_substations=False)
    else:
        # 🔹 Apply substations filter only when showing all power sources
        if substations_store and not substations_store.get("enabled"):
            filtered_stations = filtered_stations[filtered_stations["power"] != "substation"]

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
        Input("substations-filter-store", "data"),
        Input("map-display", "selectedData"),
        Input("stations-table", "active_cell"),
    ],
    prevent_initial_call=False,
)
def update_station_details(
    click_data: dict[str, Any] | None,
    relayout_data: dict[str, Any] | None,
    selected_oblast: str | None,
    gppd_filter: dict[str, bool] | None,
    power_source_filter: dict[str, str] | None,
    substations_filter: dict[str, bool] | None,
    selected_data: dict[str, Any] | None,
    active_cell: dict[str, Any] | None,
) -> html.Div | str:
    """
    Update station details panel based on map clicks and interactions.

    Args:
        click_data: Data from map click events
        relayout_data: Data from map zoom/pan events
        selected_oblast: Currently selected oblast
        gppd_filter: GPPD filter state
        power_source_filter: Power source filter state
        substations_filter: Substations filter state
        selected_data: Data from lasso/box selection
        active_cell: Active cell in the table

    Returns:
        HTML Div with station details or message string

    """
    ctx = dash.callback_context
    triggered = ctx.triggered[0]["prop_id"] if ctx.triggered else ""

    # Clear station details when any filter changes, map is manipulated, table is interacted with, or lasso selection is made
    if (
        "oblast-dropdown" in triggered
        or "relayoutData" in triggered
        or "gppd-filter-store" in triggered
        or "power-source-filter-store" in triggered
        or "substations-filter-store" in triggered
        or "selectedData" in triggered
        or "active_cell" in triggered
    ):
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
    Input("substations-filter-store", "data"),
    Input("map-display", "selectedData"),
    prevent_initial_call=False,
)
def update_table(
    selected_oblast: str | None, 
    gppd_filter: dict[str, bool] | None, 
    power_source_filter: dict[str, str] | None,
    substations_filter: dict[str, bool] | None,
    selected_data: dict[str, Any] | None
) -> list[dict[str, Any]]:
    """
    Update the stations table based on filters and selections.

    Args:
        selected_oblast: Currently selected oblast from dropdown
        gppd_filter: GPPD filter state
        power_source_filter: Power source filter state
        substations_filter: Substations filter state
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
        df = _apply_power_source_filter(df, filter_type, include_substations=False)
    else:
        # apply substations filter only when showing all power sources
        if substations_filter and not substations_filter.get("enabled"):
            df = df[df["power"] != "substation"]

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


# ================= Auto-scroll Sidebar on Station Click =================
app.clientside_callback(
    """
    function(children) {
        // Only scroll if children is not empty (station details are shown)
        if (children && children !== "") {
            setTimeout(function() {
                const stationDetails = document.getElementById('station-details');
                const sidebar = document.querySelector('.sidebar-container');
                if (stationDetails && sidebar) {
                    // Calculate the position of station-details relative to the sidebar
                    const sidebarRect = sidebar.getBoundingClientRect();
                    const detailsRect = stationDetails.getBoundingClientRect();
                    const scrollOffset = detailsRect.top - sidebarRect.top + sidebar.scrollTop;
                    
                    // Scroll the sidebar container, not the whole page
                    sidebar.scrollTo({
                        top: scrollOffset,
                        behavior: 'smooth'
                    });
                }
            }, 100);
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("station-details", "data-scroll-trigger"),
    Input("station-details", "children"),
)


# ================= Run Server =================
if __name__ == "__main__":
    app.run(debug=True)
