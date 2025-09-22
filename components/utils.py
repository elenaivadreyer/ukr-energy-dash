"""
Utility functions for Ukraine Energy Dashboard components.

This module provides utility functions for map visualization, data processing,
and UI component generation for the Ukraine Energy Dashboard.
"""

from typing import Any

import geopandas as gpd
import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html
from matplotlib import colors as mcolors
from shapely.geometry import MultiPolygon, Point, Polygon

# ---------------- Color scheme ---------------- #
power_source_colors = {
    "solar": "#FFB84D",
    "nuclear": "#e31a1c",
    "gas;coal": "#640A64",
    "gas": "#640A64",
    "oil;gas": "#640A64",
    "coal": "#6a3d9a",
    "wind": "#33a02c",
    "hydro": "#4871EF",
    "coal;oil": "#640A64",
    "gas;mazut": "#640A64",
    "coal;gas;oil": "#640A64",
    "gas;oil": "#640A64",
    "biogas": "#33a02c",
    "waste": "#FFFFFF",
    "diesel": "#640A64",
    "oil;gas;diesel": "#640A64",
}


def hex_to_rgba(hex_color: str, alpha: float = 0.25) -> str:
    """
    Convert hex color to rgba string.

    Args:
        hex_color: Hexadecimal color string (e.g., '#FF0000')
        alpha: Alpha transparency value between 0 and 1

    Returns:
        RGBA color string in format 'rgba(r,g,b,alpha)'

    """
    rgb = mcolors.to_rgb(hex_color)
    r, g, b = [int(c * 255) for c in rgb]
    return f"rgba({r},{g},{b},{alpha})"


def add_station_markers(fig: go.Figure, stations_df: gpd.GeoDataFrame) -> None:
    """
    Add plants and substations to the map as separate traces.

    Args:
        fig: Plotly figure object to add markers to
        stations_df: GeoDataFrame containing station data with geometry and attributes

    """
    # ---------------- Plants ---------------- #
    plants_df = stations_df[stations_df["power"] == "plant"]
    if not plants_df.empty:
        lats, lons, colors, indices, hovertexts = [], [], [], [], []

        for idx, row in plants_df.iterrows():
            geom = row.geometry
            lat, lon = (geom.centroid.y, geom.centroid.x) if not isinstance(geom, Point) else (geom.y, geom.x)
            source = row.get("plant:source", "Other")
            color = power_source_colors.get(source, "#6a3d9a")

            lats.append(lat)
            lons.append(lon)
            colors.append(color)
            indices.append(idx)
            hovertexts.append(row.get("station_name_en", "Unknown"))

        fig.add_trace(
            go.Scattermapbox(
                lat=lats,
                lon=lons,
                mode="markers",
                marker={"size": 8, "color": colors, "symbol": "circle"},
                customdata=indices,
                hoverinfo="text",
                hovertext=hovertexts,
                name="Plants",
            )
        )

    # ---------------- Substations ---------------- #
    subs_df = stations_df[stations_df["power"] == "substation"]
    if not subs_df.empty:
        lats, lons, hovertexts = [], [], []
        for _, row in subs_df.iterrows():
            geom = row.geometry
            # use centroid for polygon or point
            lat, lon = (geom.centroid.y, geom.centroid.x) if not geom.geom_type == "Point" else (geom.y, geom.x)
            lats.append(lat)
            lons.append(lon)
            hovertexts.append(row.get("station_name_en", "Unknown"))

        fig.add_trace(
            go.Scattermapbox(
                lat=lats,
                lon=lons,
                mode="markers",
                marker={
                    "size": 6,
                    "color": "#382b2b",  # fill
                    "symbol": "circle",  # only symbol that supports color/size
                },
                text=hovertexts,
                hovertext=hovertexts,
                hoverinfo="text",
                customdata=subs_df.index,
                name="Substation",
            )
        )

    return fig


# ---------------- Default map ---------------- #
def default_map_figure(stations_df: gpd.GeoDataFrame, outer_ukraine: gpd.GeoDataFrame | None = None) -> go.Figure:
    """
    Default whole-Ukraine view with all stations (single trace).

    Args:
        stations_df: GeoDataFrame containing station data
        outer_ukraine: Optional GeoDataFrame containing Ukraine border geometry

    Returns:
        Plotly figure object with default map view

    """
    fig = go.Figure()

    # lightweight Ukraine border (can be combined further if desired)
    if outer_ukraine is not None and not outer_ukraine.empty:
        for _, row in outer_ukraine.iterrows():
            geom = row.geometry
            if geom is None or geom.is_empty:
                continue
            polygons = [geom] if isinstance(geom, Polygon) else geom.geoms
            for poly in polygons:
                x, y = poly.exterior.xy
                fig.add_trace(
                    go.Scattermapbox(
                        lat=list(y),
                        lon=list(x),
                        mode="lines",
                        line={"width": 1, "color": "black"},
                        hoverinfo="none",
                        showlegend=False,
                    )
                )

    # markers (one trace)
    fig = add_station_markers(fig, stations_df)

    # always set a full mapbox layout so centering works reliably
    fig.update_layout(
        mapbox={"style": "carto-positron", "center": {"lat": 48.3794, "lon": 31.1656}, "zoom": 5},
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        showlegend=False,
    )
    return fig


def generate_map_figure(
    stations_df: gpd.GeoDataFrame,
    oblasts_gdf: gpd.GeoDataFrame,
    selected_oblast: str | None = None,
    click_data: dict[str, Any] | None = None,
    reset: bool = False,
    outer_ukraine: gpd.GeoDataFrame | None = None,
) -> go.Figure:
    """
    Build Mapbox figure with priority.

    1) reset=True → full Ukraine
    2) click_data → zoom to clicked station (even if no oblast)
    3) selected_oblast → zoom to oblast centroid
    4) fallback → full Ukraine.

    Args:
        stations_df: GeoDataFrame containing station data
        oblasts_gdf: GeoDataFrame containing oblast boundaries
        selected_oblast: Name of selected oblast to zoom to
        click_data: Click event data from map interaction
        reset: Whether to reset to full Ukraine view
        outer_ukraine: Optional GeoDataFrame containing Ukraine border geometry

    Returns:
        Plotly figure object with map visualization

    Note:
        Lasso/box selection is enabled.

    """
    fig = go.Figure()

    # 1️⃣ Reset or no selection → full Ukraine
    if reset or (selected_oblast is None and not click_data):
        fig = default_map_figure(stations_df, outer_ukraine=outer_ukraine)

    # 2️⃣ ClickData present → zoom to clicked station
    elif click_data and "points" in click_data and len(click_data["points"]) > 0:
        point = click_data["points"][0]
        station_index = point.get("customdata")
        if station_index is not None and station_index in stations_df.index:
            station_row = stations_df.loc[station_index]
            geom = station_row.geometry
            source = station_row.get("plant:source") or station_row.get("power_source") or "Other"
            color = power_source_colors.get(source, "#382b2b")
            fill_rgba = hex_to_rgba(color, 0.25)

            # compute centroid for centering
            if isinstance(geom, Point):
                lat, lon = geom.y, geom.x
            else:
                c = geom.centroid
                lat, lon = c.y, c.x

            # Add all stations as markers
            fig = add_station_markers(fig, stations_df)

            # Zoom to clicked station
            fig.update_layout(
                mapbox={"center": {"lat": lat, "lon": lon}, "zoom": 15, "style": "carto-positron"},
                margin={"r": 0, "t": 0, "l": 0, "b": 0},
                showlegend=False,
            )

            # Draw polygon fill if polygonal
            if isinstance(geom, Polygon | MultiPolygon):
                polygons = [geom] if isinstance(geom, Polygon) else geom.geoms
                for poly in polygons:
                    x, y = poly.exterior.xy
                    fig.add_trace(
                        go.Scattermapbox(
                            lat=list(y),
                            lon=list(x),
                            mode="lines",
                            fill="toself",
                            fillcolor=fill_rgba,
                            line={"width": 2, "color": color},
                            hoverinfo="none",
                            showlegend=False,
                        )
                    )
            # click zoom has top priority → return early
            fig.update_layout(dragmode="lasso", hovermode="closest")
            return fig

    # 3️⃣ selected_oblast → zoom to oblast
    elif selected_oblast:
        filtered_oblast = oblasts_gdf[oblasts_gdf["oblast_name_en"] == selected_oblast]
        if not filtered_oblast.empty:
            # Draw oblast outline
            for _, row in filtered_oblast.iterrows():
                geom = row.geometry
                polygons = [geom] if isinstance(geom, Polygon) else geom.geoms
                for poly in polygons:
                    x, y = poly.exterior.xy
                    fig.add_trace(
                        go.Scattermapbox(
                            lat=list(y),
                            lon=list(x),
                            mode="lines",
                            line={"width": 2, "color": "black"},
                            hoverinfo="none",
                            showlegend=False,
                        )
                    )
            # Add stations inside oblast
            filtered_stations = stations_df[stations_df["oblast_name_en"] == selected_oblast]
            fig = add_station_markers(fig, filtered_stations)

            # Center on oblast centroid
            centroid = filtered_oblast.geometry.unary_union.centroid
            fig.update_layout(
                mapbox={"center": {"lat": centroid.y, "lon": centroid.x}, "zoom": 7, "style": "carto-positron"},
                margin={"r": 0, "t": 0, "l": 0, "b": 0},
                showlegend=False,
                dragmode="lasso",
                hovermode="closest",
            )
            return fig

    # 4️⃣ fallback → full Ukraine
    fig = default_map_figure(stations_df, outer_ukraine=outer_ukraine)
    fig.update_layout(dragmode="lasso", hovermode="closest")
    return fig


# ---------------- Station details ---------------- #
def get_station_details(row: pd.Series) -> html.Div:
    """
    Generate a detailed HTML Div for a power station.

    Args:
        row: Pandas Series containing station data with attributes

    Returns:
        Dash HTML Div component with formatted station details

    """
    substation = row.get("substation", "N/A")
    station_name = row.get("station_name", "Unknown")
    station_name_en = row.get("station_name_en", "Unknown")
    operator = row.get("operator", "N/A")
    operator_en = row.get("operator:en", "N/A")
    voltage = row.get("voltage", "N/A")
    method = row.get("plant:method", "N/A")
    output = row.get("plant:output:electricity", "N/A")
    source = row.get("plant:source", "Other")

    geom = row.geometry
    centroid = geom.centroid
    color = power_source_colors.get(source, "#382b2b")
    google_earth_link = f"https://earth.google.com/web/@{centroid.y},{centroid.x},1000a,1000d,35y,0h,0t,0r"

    details_layout = html.Div(
        [
            html.H5(station_name_en, style={"marginBottom": "10px", "color": color, "fontSize": "18px"}),
            html.Div(
                [
                    html.Strong("Station Name:"),
                    f" {station_name_en} / {station_name}",
                    html.Br(),
                    html.Strong("Operator:"),
                    f" {operator} / {operator_en}",
                    html.Br(),
                    html.Strong("Power Source:"),
                    f" {source}",
                    html.Br(),
                    html.Strong("Plant Method:"),
                    f" {method}",
                    html.Br(),
                    html.Strong("Substation:"),
                    f" {substation}",
                    html.Br(),
                    html.Strong("Voltage:"),
                    f" {voltage} kV",
                    html.Br(),
                    html.Strong("Output Electricity:"),
                    f" {output} MW",
                    html.Br(),
                    html.Strong("Centroid:"),
                    f" {centroid.y}, {centroid.x}",
                    html.Br(),
                ],
                style={"marginBottom": "10px"},
            ),
            html.Div(
                [
                    html.Strong("Geometry:"),
                    dcc.Textarea(value=str(geom), style={"width": "100%", "height": "80px"}, readOnly=True),
                ],
                style={"marginBottom": "10px"},
            ),
            html.Div([html.A("Open in Google Earth", href=google_earth_link, target="_blank")]),
        ],
        className="station-details",
        style={"border": f"2px solid {color}", "padding": "10px", "borderRadius": "5px", "backgroundColor": "#f9f9f9"},
    )

    return details_layout
