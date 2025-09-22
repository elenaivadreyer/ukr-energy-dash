from dash import dash_table, dcc, html

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


# ---------------- Header ---------------- #
def get_header_with_buttons():
    return html.Div(
        children=[
            html.Div(
                [
                    html.H1("Ukraine Power Stations Dashboard", className="title-section"),
                ],
                className="header-title",
            ),
        ],
        className="header-container",
    )


# ---------------- Footer ---------------- #
def get_footer():
    return html.Div(
        children=[
            html.Div(
                children=[
                    html.A(
                        html.I(className="fa-brands fa-github"),
                        href="https://github.com/elenaivadreyer/ukr_energy_dash",
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


def get_main_content_with_oblast(unique_oblasts):
    # Sidebar
    sidebar_content = html.Div(
        [
            html.Div(
                [html.H5("Explore Ukraine's power stations", className="site-description")],
                className="description-container",
            ),
            html.Div(
                [
                    html.Small(
                        [
                            "Station locations were retrieved from ",
                            html.A(
                                "OpenStreetMap",
                                href="https://www.openstreetmap.org/",
                                target="_blank",
                                className="note-link",
                            ),
                            " using a custom Overpass query. ",
                            "These points were validated against the ",
                            html.A(
                                "Global Power Plant Database",
                                href="https://datasets.wri.org/dataset/globalpowerplantdatabase",
                                target="_blank",
                                className="note-link",
                            ),
                            " through spatial proximity checks.",
                        ]
                    )
                ],
                className="data-note",
            ),
            # 🔹 Filters
            html.Div(
                [
                    html.H6("Filters", className="dropdown-title"),
                    # GPPD filter
                    dcc.Checklist(
                        id="gppd-filter",
                        options=[{"label": "Global Power Plant Database (GPPD)", "value": "gppd"}],
                        value=[],  # default unchecked
                        inputStyle={"margin-right": "6px"},
                        labelStyle={"margin-left": "6px"},
                    ),
                    dcc.Store(id="gppd-filter-store", data={"enabled": False}),
                ],
                className="dropdown-block",
                style={"margin-bottom": "15px"},
            ),  # adds spacing after filters
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
                    html.Span("Download CSV", className="download-text"),  # text next to button
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


# ---------------- Main Layout ---------------- #
def get_main_layout(unique_oblasts):
    return html.Div(
        [
            html.Div(children=[get_header_with_buttons()], className="header"),
            html.Div(children=[get_main_content_with_oblast(unique_oblasts)], className="body"),
            get_footer(),
        ],
        className="main-layout",
    )
