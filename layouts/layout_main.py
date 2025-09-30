"""
Main layout components for Ukraine Energy Dashboard.

This module defines the main layout structure, components, and UI elements
for the Ukraine Energy Dashboard including headers, footers, and content areas.
"""

import geopandas as gpd
from dash import dash_table, dcc, html

from components.utils import generate_data_note

unique_oblasts = [
    "Cherkasy",
    "Kiev",
    "Zaporizhia",
    "Mykolayiv",
    "Khmelnytskyi",
    "Rivne",
    "Kharkiv",
    "Vinnytsya",
    "Crimea",
    "Kherson",
    "Donetsk",
    "Kiev City",
    "Chernihiv",
    "Dnipropetrovsk",
    "Luhansk",
    "Lviv",
    "Sevastopol",
    "Odessa",
    "Chernivtsi",
    "Kirovohrad",
    "Ivano-Frankivsk",
    "Zakarpattia",
    "Volyn",
    "Ternopil",
    "Zhytomyr",
    "Sumy",
    "Poltava",
]


def get_header_with_buttons() -> html.Div:
    """
    Create the header section with title and navigation buttons.

    Returns:
        Dash HTML Div containing the dashboard header

    """
    return html.Div(
        children=[
            html.Div(
                [
                    html.H1("Ukraine Energy Infrastructure Dashboard", className="title-section"),
                ],
                className="header-title",
            ),
        ],
        className="header-container",
    )


def get_footer() -> html.Div:
    """
    Create the footer section with links and credits.

    Returns:
        Dash HTML Div containing the dashboard footer

    """
    return html.Div(
        children=[
            html.Div(
                children=[
                    html.A(
                        html.I(className="fa-brands fa-github"),
                        href="https://github.com/elenaivadreyer/ukr-energy-dash",
                        target="_blank",
                        className="github-link",
                        style={"margin-left": "10px", "color": "#333", "text-decoration": "none"},
                    ),
                ],
                className="info-container",
            )
        ],
        className="footer-main",
    )


def get_main_content_with_oblast(unique_oblasts: list[str], stations_df: gpd.GeoDataFrame) -> html.Div:
    """
    Create the main content area with sidebar and map components.

    Args:
        unique_oblasts: List of oblast names for the dropdown filter
        stations_df: GeoDataFrame containing power station data for generating data note

    Returns:
        Dash HTML Div containing the main dashboard content

    """
    # Sidebar
    sidebar_content = html.Div(
        [
            html.Div(
                [html.H5("Explore Ukraine's power and substations", className="site-description")],
                className="description-container",
            ),
            # Data note
            generate_data_note(stations_df),
            # Filters
            html.Div(
                [
                    html.H6("Filters", className="dropdown-title"),
                    # Switch filters row
                    html.Div(
                        [
                            # GPPD switch
                            html.Div(
                                [
                                    html.Label("GPPD Validation", className="switch-label-inline"),
                                    html.Div(
                                        [
                                            dcc.Checklist(
                                                id="gppd-filter",
                                                options=[{"label": "", "value": "gppd"}],
                                                value=[],  # default unchecked
                                                className="switch-checkbox",
                                            ),
                                        ],
                                        className="switch-container-small",
                                    ),
                                ],
                                className="switch-item-inline",
                            ),
                            # Substations switch
                            html.Div(
                                [
                                    html.Label("Show Substations", className="switch-label-inline"),
                                    html.Div(
                                        [
                                            dcc.Checklist(
                                                id="substations-filter",
                                                options=[{"label": "", "value": "substations"}],
                                                value=["substations"],  # default checked
                                                className="switch-checkbox",
                                            ),
                                        ],
                                        className="switch-container-small",
                                    ),
                                ],
                                className="switch-item-inline",
                            ),
                        ],
                        className="switches-row-inline",
                        style={"margin-bottom": "15px"},
                    ),
                    dcc.Store(id="gppd-filter-store", data={"enabled": False}),
                    dcc.Store(id="substations-filter-store", data={"enabled": True}),
                ],
                className="dropdown-block",
                style={"margin-bottom": "15px"},
            ),  # adds spacing after filters
            # Power source button filters with icons
            html.Div(
                [
                    html.H6("Power Source Type", className="dropdown-title"),
                    html.Div(
                        [
                            html.Button(
                                [
                                    html.I(className="fas fa-globe", style={"margin-right": "6px"}),
                                    "All Sources"
                                ],
                                id="power-source-all",
                                className="power-source-btn power-source-btn-active",
                                n_clicks=0,
                            ),
                            html.Button(
                                [
                                    html.I(className="fas fa-fire", style={"margin-right": "6px"}),
                                    "Thermal"
                                ],
                                id="power-source-thermal",
                                className="power-source-btn",
                                n_clicks=0,
                            ),
                            html.Button(
                                [
                                    html.I(className="fas fa-atom", style={"margin-right": "6px"}),
                                    "Nuclear"
                                ],
                                id="power-source-nuclear",
                                className="power-source-btn",
                                n_clicks=0,
                            ),
                            html.Button(
                                [
                                    html.I(className="fas fa-leaf", style={"margin-right": "6px"}),
                                    "Renewable"
                                ],
                                id="power-source-renewable",
                                className="power-source-btn",
                                n_clicks=0,
                            ),
                        ],
                        className="power-source-buttons",
                    ),
                    dcc.Store(id="power-source-filter-store", data={"type": "all"}),
                ],
                className="dropdown-block",
                style={"margin-bottom": "15px"},
            ),
            # Oblast dropdown - default None means "All Ukraine"
            html.Div(
                [
                    html.H6("Select an Oblast", className="dropdown-title"),
                    dcc.Dropdown(
                        id="oblast-dropdown",
                        options=[{"label": "All Ukraine", "value": "all"}]
                        + [{"label": oblast, "value": oblast} for oblast in unique_oblasts],
                        value=None,  # default: show whole Ukraine
                        className="dropdown-style",
                        clearable=True,
                        placeholder="All Ukraine (default)",
                    ),
                ],
                className="dropdown-block",
            ),
            # Station details from click
            html.Div(id="station-details", children=[], className="station-details-container"),
        ],
        className="sidebar-container",
    )

    # Map
    map_section = html.Div(
        [
            dcc.Graph(
                id="map-display",
                responsive=True,
                className="map-display",
                config={
                    "displayModeBar": True,
                    "scrollZoom": True,
                    "modeBarButtonsToRemove": [
                        "pan2d",
                        "zoomIn2d",
                        "zoomOut2d",
                        "autoScale2d",
                        "resetScale2d",
                        "hoverClosestCartesian",
                        "hoverCompareCartesian",
                        "toggleSpikelines",
                        "toImage",
                    ],
                    "modeBarButtonsToAdd": ["zoom2d", "resetScale2d", "lasso2d"],
                },
            ),
            dcc.Store(id="map-view-store-mainpage", data={}),
        ],
        className="map-section",
    )

    # Combine map + sidebar
    top_section = html.Div(
        [
            map_section,
            sidebar_content,
        ],
        className="map-sidebar-container",
    )

    table_section = html.Div(
        id="stations-table-container",
        className="stations-table-section",
        children=[
            dash_table.DataTable(
                id="stations-table",
                columns=[
                    {"name": c, "id": c}
                    for c in [
                        "name",
                        "station_name_en",
                        "power",
                        "plant:source",
                        "plant:method",
                        "oblast_name_en",
                        "gppd_overlap",
                    ]
                ],
                data=[],
                page_size=10,
                export_format=None,  # disable default top-left export button
                style_table={
                    "overflowX": "auto",
                    "width": "100%",
                    "maxHeight": "400px",
                    "overflowY": "scroll",
                },  # scrollable table
                style_cell={"textAlign": "left", "padding": "5px"},
                style_header={"fontWeight": "bold"},
            ),
            html.Div(
                children=[
                    html.Span("Download", className="download-text"),  # text next to button
                    html.Button(
                        html.I(className="fa-solid fa-download"),  # Font Awesome icon
                        id="download-button",
                        n_clicks=0,
                        className="download-btn minimal-btn",
                    ),
                ],
                className="download-wrapper",
            ),
            dcc.Download(id="download-data"),
        ],
    )

    return html.Div([top_section, table_section], className="main-content")


def get_main_layout(unique_oblasts: list[str], stations_df: gpd.GeoDataFrame) -> html.Div:
    """
    Create the complete main layout for the dashboard.

    Args:
        unique_oblasts: List of oblast names for the dropdown filter
        stations_df: GeoDataFrame containing power station data for generating data note

    Returns:
        Dash HTML Div containing the complete dashboard layout

    """
    return html.Div(
        [
            html.Div(children=[get_header_with_buttons()], className="header"),
            html.Div(children=[get_main_content_with_oblast(unique_oblasts, stations_df)], className="body"),
            get_footer(),
        ],
        className="main-layout",
    )
