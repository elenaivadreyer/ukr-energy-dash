# Ukraine Energy Dashboard

An interactive dashboard for visualizing Ukraine's power infrastructure, built with Plotly Dash.

## Demo

<!-- Placeholder for demo video -->
*Coming soon: Short demo video showing dashboard features*

## Technology Stack

This dashboard is built with modern Python data visualization and web technologies:

- **[Plotly Dash](https://dash.plotly.com/)** - Interactive web application framework
- **[GeoPandas](https://geopandas.org/)** - Geospatial data processing and analysis
- **[Plotly](https://plotly.com/python/)** - Interactive mapping and visualization
- **[Bootstrap](https://getbootstrap.com/)** - Responsive UI components via dash-bootstrap-components
- **[Font Awesome](https://fontawesome.com/)** - Professional icons and styling


## Data Sources

The dashboard integrates data from multiple sources through various APIs and services:

- **[OpenStreetMap](https://www.openstreetmap.org/)**: Power station locations retrieved via custom [Overpass API](https://overpass-api.de/api/interpreter) queries targeting power generation facilities across Ukraine
- **[Global Power Plant Database (GPPD)](https://datasets.wri.org/dataset/globalpowerplantdatabase)**: Validation and additional power plant information through spatial proximity matching with WRI's comprehensive global database
- **[GADM](https://geodata.ucdavis.edu/gadm/)**: Administrative boundaries for Ukrainian oblasts sourced from GADM database version 4.1
- **[Google Earth Web](https://earth.google.com/web/)**: Direct integration allowing users to explore power station locations in satellite imagery with one-click access

## Features

The dashboard provides comprehensive visualization and analysis capabilities for Ukraine's power infrastructure:

### 🗺️ Interactive Map Visualization
- **Real-time exploration** of power stations across Ukraine
- **Color-coded markers** by energy source (solar, wind, hydro, nuclear, fossil fuels)
- **Click-to-zoom** functionality for detailed station inspection
- **Lasso and box selection** tools for multi-station analysis
- **Oblast boundaries** with administrative region filtering

### 🔍 Filtering and Search
- **Oblast-based filtering** to focus on specific regions
- **Global Power Plant Database (GPPD) integration** for enhanced data validation
- **Real-time map updates** based on selected filters

### 📊 Data Table and Export
- **Interactive data table** with station details and specifications
- **CSV export functionality** for filtered results
- **Pagination support** for large datasets
- **Sortable columns** for easy data analysis

### 🛰️ External Integration
- **Google Earth integration** - Click any station to open its location in Google Earth Web
- **Detailed station information** including:
  - Power source and generation method
  - Operator information (Ukrainian and English names)
  - Technical specifications (voltage, output capacity)
  - Geographic coordinates and geometry data

### 📱 Responsive Design
- **Mobile-friendly interface** with Bootstrap components
- **Scalable layouts** that adapt to different screen sizes
- **Professional styling** with custom CSS and Font Awesome icons

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

## Development

1. **Install development dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install .[test]
   ```

2. **Code formatting and linting:**
   ```bash
   ruff check . --fix
   ruff format .
   ```

3. **Run pre-commit hooks:**
   ```bash
   pre-commit run --all-files
   ```

## Inspiration

The layout of this app was inspired by the [Michelin Guide to France](https://restaurant-guide-france.net/) developed by [pineapple-bois](https://github.com/pineapple-bois/Michelin_App_Development).