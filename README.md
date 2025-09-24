# Ukraine Energy Infrastrcuture Dashboard

An interactive dashboard for visualizing Ukraine's power infrastructure, built with Plotly Dash.

The live app can be accessed [here](https://50df7176-a5f3-40b7-98e3-0b5a4a5fd93a.plotly.app/).

## Demo

<!-- Placeholder for demo video -->
*Coming soon: Short demo video showing dashboard features*


## Data Sources

The dashboard integrates data from multiple sources through various APIs and services:

- **[OpenStreetMap](https://www.openstreetmap.org/)**: Power station locations retrieved via custom [Overpass API](https://overpass-api.de/api/interpreter) queries targeting power generation facilities across Ukraine
- **[Global Power Plant Database (GPPD)](https://datasets.wri.org/dataset/globalpowerplantdatabase)**: Validation and additional power plant information through spatial proximity matching with WRI's comprehensive global database
- **[GADM](https://geodata.ucdavis.edu/gadm/)**: Administrative boundaries for Ukrainian oblasts sourced from GADM database version 4.1
- **[Google Earth Web](https://earth.google.com/web/)**: Direct integration allowing users to explore power station locations in satellite imagery with one-click access

## Features

The dashboard provides comprehensive visualization and analysis capabilities for Ukraine's power infrastructure:

- **Color-coded markers** by energy source (solar, wind, hydro, nuclear, fossil fuels)
- **Click-to-zoom** functionality for detailed station inspection
- **Lasso and box selection** tools for multi-station analysis
- **Oblast-based filtering** to focus on specific regions
- **Global Power Plant Database (GPPD) filter** for enhanced data validation
- **Google Earth integration** - Click any station to open its location in Google Earth Web

## Project Structure

```
ukr-energy-dash/
├── app.py                 # Main Dash application
├── assets/                # Static files and data
│   ├── data/              # Processed geospatial data files
│   └── styles.css         # Custom styling
├── components/            # Reusable UI components
│   └── utils.py           # Map utilities and station details
├── layouts/               # Page layouts and UI structure
│   └── layout_main.py     # Main dashboard layout
├── data/                  # Data processing pipeline
│   └── process.py         # OSM data processing and GPPD matching
├── notebooks/             # Analysis notebooks
└── requirements.txt       # Package dependencies
```

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the dashboard:**
   ```bash
   python app.py
   ```

3. **Access the dashboard:**
   Open your browser and navigate to `http://localhost:8050`

## Technology Stack

This dashboard is built with modern Python data visualization and web technologies:

- **[Plotly Dash](https://dash.plotly.com/)** - Interactive web application framework
- **[GeoPandas](https://geopandas.org/)** - Geospatial data processing and analysis
- **[Plotly](https://plotly.com/python/)** - Interactive mapping and visualization
- **[Bootstrap](https://getbootstrap.com/)** - Responsive UI components via dash-bootstrap-components
- **[Font Awesome](https://fontawesome.com/)** - Professional icons and styling

## Inspiration

The layout of this app was inspired by the [Michelin Guide to France](https://restaurant-guide-france.net/) developed by [pineapple-bois](https://github.com/pineapple-bois/Michelin_App_Development).
