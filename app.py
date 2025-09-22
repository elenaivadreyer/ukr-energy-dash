# ================= app.py =================
import datetime as dt
import os
import uuid

import dash
import dash_bootstrap_components as dbc
import geopandas as gpd
import pandas as pd
from dash import Input, Output, State, dcc
from dotenv import load_dotenv
from flask import Flask

# ================= Utilities =================
from components.utils import default_map_figure, generate_map_figure, get_station_details
from layouts.layout_main import get_main_layout, unique_oblasts

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

# ================= Layout =================
app.layout = get_main_layout(unique_oblasts)

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
def store_gppd_filter(value):
    return {"enabled": "gppd" in value}


@app.callback(Output("substation-filter-store", "data"), Input("substation-filter", "value"))
def store_substation_filter(value):
    return {"enabled": "substations" in value}


# ================= Map Callback =================
@app.callback(
    Output("map-display", "figure"),
    [
        Input("oblast-dropdown", "value"),
        Input("map-display", "clickData"),
        Input("map-display", "relayoutData"),
        Input("map-display", "selectedData"),
        Input("gppd-filter-store", "data"),
    ],
    State("map-view-store-mainpage", "data"),
    prevent_initial_call=False,
)
def update_map(selected_oblast, clickData, relayoutData, selectedData, gppd_store, store_data):
    ctx = dash.callback_context
    triggered = ctx.triggered[0]["prop_id"] if ctx.triggered else ""
    ignore_click = "oblast-dropdown" in triggered  # ignore stale click

    # 🔹 Apply GPPD filter
    filtered_stations = stations_df.copy()
    if gppd_store and gppd_store.get("enabled"):
        filtered_stations = filtered_stations[filtered_stations["gppd_overlap"] == True]

    # ---------------- Map Logic ----------------
    if "map-display.relayoutData" in triggered:
        if selected_oblast:
            return generate_map_figure(
                filtered_stations,
                oblasts_gdf,
                selected_oblast=selected_oblast,
                clickData=None,
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
            clickData=None,
            reset=False,
            outer_ukraine=outer_ukraine,
        )

    if "map-display.clickData" in triggered and clickData and not ignore_click:
        return generate_map_figure(
            filtered_stations,
            oblasts_gdf,
            selected_oblast=selected_oblast,
            clickData=clickData,
            reset=False,
            outer_ukraine=outer_ukraine,
        )

    if "map-display.selectedData" in triggered:
        return generate_map_figure(
            filtered_stations,
            oblasts_gdf,
            selected_oblast=selected_oblast,
            clickData=None,
            reset=False,
            outer_ukraine=outer_ukraine,
        )

    # Default fallback
    return generate_map_figure(
        filtered_stations,
        oblasts_gdf,
        selected_oblast=selected_oblast,
        clickData=None,
        reset=False,
        outer_ukraine=outer_ukraine,
    )


# ================= Station Sidebar =================
@app.callback(
    Output("station-details", "children"),
    [Input("map-display", "clickData"), Input("map-display", "relayoutData"), Input("oblast-dropdown", "value")],
    prevent_initial_call=False,
)
def update_station_details(clickData, relayoutData, selected_oblast):
    ctx = dash.callback_context
    triggered = ctx.triggered[0]["prop_id"] if ctx.triggered else ""

    if clickData and "points" in clickData and len(clickData["points"]) > 0:
        point = clickData["points"][0]
        station_index = point.get("customdata")
        if station_index is not None and station_index in stations_df.index:
            station_row = stations_df.loc[int(station_index)]
            return get_station_details(station_row)


# ================= Lasso / Selected Stations Table =================


@app.callback(
    Output("stations-table", "data"),
    Input("oblast-dropdown", "value"),
    Input("gppd-filter-store", "data"),
    Input("map-display", "selectedData"),
    prevent_initial_call=False,
)
def update_table(selected_oblast, gppd_filter, selectedData):
    df = stations_df.copy()

    # filter by oblast
    if selected_oblast:
        df = df[df["oblast_name_en"] == selected_oblast]

    # apply GPPD filter
    if gppd_filter and gppd_filter.get("enabled"):
        df = df[df["gppd_overlap"]]

    # filter by lasso selection
    if selectedData and "points" in selectedData:
        indices = [pt.get("customdata") for pt in selectedData["points"] if pt.get("customdata") in stations_df.index]
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
def download_csv(n_clicks, table_data):
    if not table_data:
        return None
    df = pd.DataFrame(table_data)
    # save with a timestamp
    timestamp = dt.datetime.now().strftime("%Y%m%d")
    return dcc.send_data_frame(df.to_csv, f"ukraine_power_stations_osm_{timestamp}.csv", index=False)


# ================= Run Server =================
if __name__ == "__main__":
    app.run(debug=True)
