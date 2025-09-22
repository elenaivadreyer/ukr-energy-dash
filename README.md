# Ukraine Energy Dashboard

An interactive dashboard for visualizing Ukraine's power infrastructure, built with Plotly Dash.

## Demo

<!-- Placeholder for demo video -->
*Coming soon: Short demo video showing dashboard features*

## Data Sources

The dashboard integrates data from multiple sources:

- **[OpenStreetMap](https://www.openstreetmap.org/)**: Power station locations retrieved via custom Overpass API queries
- **[Global Power Plant Database (GPPD)](https://datasets.wri.org/dataset/globalpowerplantdatabase)**: Validation and additional power plant information through spatial proximity matching
- **[GADM](https://geodata.ucdavis.edu/gadm/)**: Administrative boundaries for Ukrainian oblasts

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -e .
   ```

2. **Run the dashboard:**
   ```bash
   python app.py
   ```

3. **Access the dashboard:**
   Open your browser and navigate to `http://localhost:8050`

## Project Structure

```
ukr_energy_dash/
├── app.py                 # Main Dash application
├── assets/                # Static files and data
│   ├── data/              # Processed geospatial data files
│   └── styles.css         # Custom styling
├── components/            # Reusable UI components
│   ├── __init__.py
│   └── utils.py           # Map utilities and station details
├── layouts/               # Page layouts and UI structure
│   ├── __init__.py
│   └── layout_main.py     # Main dashboard layout
├── data/                  # Data processing pipeline
│   ├── __init__.py
│   └── process.py         # OSM data processing and GPPD matching
└── requirements.txt       # Package dependencies
```

## Development

1. **Install development dependencies:**
   ```bash
   pip install -e ".[test]"
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