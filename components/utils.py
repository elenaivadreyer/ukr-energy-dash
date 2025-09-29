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

power_source_colors = {
    # Renewables
    "solar": "#FDBF00",  # bright golden yellow
    "wind": "#2CA02C",  # medium-dark green
    "hydro": "#1F78B4",  # deep blue
    "biogas": "#66A61E",  # olive green
    "biomass": "#B2DF8A",  # light green
    "wood": "#8C510A",  # natural brown
    "waste": "#B15928",  # earthy rust orange
    # Nuclear
    "nuclear": "#E31A1C",  # bold red (stands out strongly)
    # Fossil fuels (dark shades)
    "coal": "#252525",  # near-black
    "gas": "#54278F",  # deep violet
    "oil": "#843C39",  # dark brownish red
    "diesel": "#6E016B",  # very dark purple
    "mazut": "#4B0082",  # indigo
    # Mixed fossil combinations (keep them dark & distinct)
    "gas;coal": "#3F007D",
    "gas;oil": "#5E3C99",
    "coal;oil": "#4A1486",
    "coal;gas": "#2D004B",
    "coal;gas;oil": "#1B0033",
    "gas;mazut": "#35004D",
    "oil;gas": "#5E3C99",
    "oil;gas;diesel": "#4E005F",
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


def add_station_markers(fig: go.Figure, stations_df: gpd.GeoDataFrame, show_legend: bool = False) -> None:
    """
    Add plants and substations to the map as separate traces.

    Args:
        fig: Plotly figure object to add markers to
        stations_df: GeoDataFrame containing station data with geometry and attributes
        show_legend: Whether to show legend with separate traces for each power source

    """
    if show_legend:
        # Create separate traces for each power source for elegant legend
        _add_station_markers_with_legend(fig, stations_df)
    else:
        # Original implementation - single trace per power type
        _add_station_markers_single_trace(fig, stations_df)

    return fig


def _add_station_markers_single_trace(fig: go.Figure, stations_df: gpd.GeoDataFrame) -> None:
    """Original implementation with single trace per power type."""
    # Plants
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
                showlegend=False,
            )
        )

    # Substations
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
                name="Substations",
                showlegend=False,
            )
        )


def _add_station_markers_with_legend(fig: go.Figure, stations_df: gpd.GeoDataFrame) -> None:
    """Create separate traces for each power source for elegant legend."""
    # Define power source categories with display names
    power_source_categories = {
        # Renewables
        "solar": "Solar",
        "wind": "Wind", 
        "hydro": "Hydro",
        "biogas": "Biogas",
        "biomass": "Biomass",
        "wood": "Wood",
        "waste": "Waste",
        # Nuclear
        "nuclear": "Nuclear",
        # Fossil fuels
        "coal": "Coal",
        "gas": "Gas",
        "oil": "Oil",
        "diesel": "Diesel",
        "mazut": "Mazut",
    }
    
    # Plants - group by power source
    plants_df = stations_df[stations_df["power"] == "plant"]
    if not plants_df.empty:
        # Group stations by power source
        for source, display_name in power_source_categories.items():
            source_plants = plants_df[plants_df["plant:source"] == source]
            if source_plants.empty:
                continue
                
            lats, lons, indices, hovertexts = [], [], [], []
            
            for idx, row in source_plants.iterrows():
                geom = row.geometry
                lat, lon = (geom.centroid.y, geom.centroid.x) if not isinstance(geom, Point) else (geom.y, geom.x)
                
                lats.append(lat)
                lons.append(lon)
                indices.append(idx)
                hovertexts.append(row.get("station_name_en", "Unknown"))

            # Get color for this source
            color = power_source_colors.get(source, "#6a3d9a")
            
            fig.add_trace(
                go.Scattermapbox(
                    lat=lats,
                    lon=lons,
                    mode="markers",
                    marker={"size": 8, "color": color, "symbol": "circle"},
                    customdata=indices,
                    hoverinfo="text",
                    hovertext=hovertexts,
                    name=display_name,
                    showlegend=True,
                    legendgroup="plants",
                )
            )
        
        # Handle mixed and other sources
        mixed_plants = plants_df[~plants_df["plant:source"].isin(power_source_categories.keys())]
        if not mixed_plants.empty:
            lats, lons, indices, hovertexts = [], [], [], []
            
            for idx, row in mixed_plants.iterrows():
                geom = row.geometry
                lat, lon = (geom.centroid.y, geom.centroid.x) if not isinstance(geom, Point) else (geom.y, geom.x)
                
                lats.append(lat)
                lons.append(lon)
                indices.append(idx)
                hovertexts.append(row.get("station_name_en", "Unknown"))

            fig.add_trace(
                go.Scattermapbox(
                    lat=lats,
                    lon=lons,
                    mode="markers",
                    marker={"size": 8, "color": "#6a3d9a", "symbol": "circle"},
                    customdata=indices,
                    hoverinfo="text",
                    hovertext=hovertexts,
                    name="Mixed/Other",
                    showlegend=True,
                    legendgroup="plants",
                )
            )

    # Substations - single trace
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
                name="Substations",
                showlegend=True,
                legendgroup="substations",
            )
        )


# Default map
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

    # markers with legend
    fig = add_station_markers(fig, stations_df, show_legend=True)

    # always set a full mapbox layout so centering works reliably
    fig.update_layout(
        mapbox={"style": "carto-positron", "center": {"lat": 48.3794, "lon": 31.1656}, "zoom": 5},
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.98,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="rgba(0,0,0,0.2)",
            borderwidth=1,
            font=dict(size=10),
        ),
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

    # Reset or no selection → full Ukraine
    if reset or (selected_oblast is None and not click_data):
        fig = default_map_figure(stations_df, outer_ukraine=outer_ukraine)

    # ClickData present → zoom to clicked station
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
            fig = add_station_markers(fig, stations_df, show_legend=True)

            # Zoom to clicked station
            fig.update_layout(
                mapbox={"center": {"lat": lat, "lon": lon}, "zoom": 15, "style": "carto-positron"},
                margin={"r": 0, "t": 0, "l": 0, "b": 0},
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=0.98,
                    xanchor="left",
                    x=0.01,
                    bgcolor="rgba(255,255,255,0.9)",
                    bordercolor="rgba(0,0,0,0.2)",
                    borderwidth=1,
                    font=dict(size=10),
                ),
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

    # selected_oblast → zoom to oblast
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
                            line={"width": 1, "color": "black"},
                            hoverinfo="none",
                            showlegend=False,
                        )
                    )
            # Add stations inside oblast
            filtered_stations = stations_df[stations_df["oblast_name_en"] == selected_oblast]
            fig = add_station_markers(fig, filtered_stations, show_legend=True)

            # Center on oblast centroid
            centroid = filtered_oblast.geometry.unary_union.centroid
            fig.update_layout(
                mapbox={"center": {"lat": centroid.y, "lon": centroid.x}, "zoom": 7, "style": "carto-positron"},
                margin={"r": 0, "t": 0, "l": 0, "b": 0},
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=0.98,
                    xanchor="left",
                    x=0.01,
                    bgcolor="rgba(255,255,255,0.9)",
                    bordercolor="rgba(0,0,0,0.2)",
                    borderwidth=1,
                    font=dict(size=10),
                ),
                dragmode="lasso",
                hovermode="closest",
            )
            return fig

    # fallback → full Ukraine
    fig = default_map_figure(stations_df, outer_ukraine=outer_ukraine)
    fig.update_layout(dragmode="lasso", hovermode="closest")
    return fig


# Station details
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
            html.H5(station_name_en, style={"marginBottom": "10px", "color": color, "fontSize": "16px"}),
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
                style={"marginBottom": "10px", "fontSize": "14px"},
            ),
            html.Div(
                [
                    html.Strong("Geometry:"),
                    dcc.Textarea(
                        value=str(geom), style={"width": "100%", "height": "80px", "fontSize": "12px"}, readOnly=True
                    ),
                ],
                style={"marginBottom": "10px", "fontSize": "14px"},
            ),
            html.Div(
                [
                    html.A("Open in Google Earth", href=google_earth_link, target="_blank"),
                ],
                style={"fontSize": "14px", "textDecoration": "underline"},
            ),
        ],
        className="station-details",
        style={"border": f"2px solid {color}", "padding": "10px", "borderRadius": "5px", "backgroundColor": "#f9f9f9"},
    )

    return details_layout


def generate_data_note(gdf: gpd.GeoDataFrame) -> html.Div:
    """
    Generate a note inside the sidebar summarizing the dataset.

    Args:
        gdf: GeoDataFrame containing station data with attributes

    Returns:
        Dash HTML Div component with formatted data note

    """
    # Split plants vs substation
    plants_df = gdf[gdf["power"] == "plant"].copy()
    substation_count = (gdf["power"] == "substation").sum()

    # Define categories
    renewable = {"solar", "hydro", "wind", "biomass", "biogas", "waste", "wood"}
    fossil = {"coal", "gas", "oil", "diesel", "mazut"}

    renew_count, fossil_count, nuclear_count = 0, 0, 0

    for sources in plants_df["plant:source"].dropna():
        fuels = set(str(sources).split(";"))
        if "nuclear" in fuels:
            nuclear_count += 1
        elif any(f in renewable for f in fuels):
            renew_count += 1
        elif any(f in fossil for f in fuels):
            fossil_count += 1
        else:
            # catch uncategorized sources
            renew_count += 0

    total_plants = plants_df.shape[0]
    total_stations = total_plants + substation_count

    return html.Div(
        [
            html.P(
                [
                    "Station locations were retrieved from ",
                    html.A("OpenStreetMap", href="https://www.openstreetmap.org", target="_blank"),
                    " using a custom Overpass query and validated against the ",
                    html.A(
                        "Global Power Plant Database",
                        href="https://datasets.wri.org/dataset/globalpowerplantdatabase",
                        target="_blank",
                    ),
                    " through spatial proximity checks.",
                ],
                className="data-note-text-1",
            ),
            html.P(
                [
                    "The dataset contains ",
                    html.Span(total_stations, className="data-number"),
                    " facilities in total: ",
                    html.Span(total_plants, className="data-number"),
                    " power plants and ",
                    html.Span(substation_count, className="data-number"),
                    " transmission substations.",
                ],
                className="data-note-text-2",
            ),
            html.P(
                [
                    "Among the power plants: ",
                    html.Span(renew_count, className="data-number"),
                    " renewable (solar, hydro, wind, biomass, etc.), ",
                    html.Span(fossil_count, className="data-number"),
                    " fossil-fuel (gas, coal, oil, etc.), and ",
                    html.Span(nuclear_count, className="data-number"),
                    " nuclear stations.",
                ],
                className="data-note-text-2",
            ),
        ],
        className="data-note",
    )
