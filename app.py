"""
Ukraine Energy Dashboard - Main Dash Application

A Plotly Dash application for visualizing Ukraine energy data.
"""

import dash
import os
from data.data_loader import DataLoader
from layouts.main_layout import create_main_layout

# Initialize the Dash app
app = dash.Dash(__name__, assets_folder='assets')

# Set the app title
app.title = "Ukraine Energy Dashboard"

# Load data
data_loader = DataLoader()
data = data_loader.get_latest_data()

# Define the app layout using the modular layout
app.layout = create_main_layout(data)

# Import callbacks (this registers them with the app)
try:
    import callbacks.chart_callbacks
except ImportError:
    # Callbacks are optional for basic functionality
    pass

# Run the server
if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 8050))
    app.run(debug=True, host='0.0.0.0', port=port)