#!/bin/bash
# Startup script for Ukraine Energy Dashboard

echo "Starting Ukraine Energy Dashboard..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt 2>/dev/null || pip install dash plotly pandas numpy

# Start the dashboard
echo "Starting dashboard on port ${PORT:-8050}..."
python app.py