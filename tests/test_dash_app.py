"""
Test the Dash application functionality
"""

import pytest
from app import app
from data.data_loader import DataLoader


def test_app_creation():
    """Test that the app can be created without errors"""
    assert app is not None
    assert app.title == "Ukraine Energy Dashboard"


def test_data_loader():
    """Test that the data loader works correctly"""
    loader = DataLoader()
    data = loader.load_sample_data()
    
    assert not data.empty
    assert 'date' in data.columns
    assert 'energy_production' in data.columns
    assert 'energy_consumption' in data.columns
    assert len(data) == 365  # One year of daily data


def test_data_loader_summary():
    """Test data summary functionality"""
    loader = DataLoader()
    data = loader.load_sample_data()
    stats = loader.get_summary_stats(data)
    
    assert 'energy_production' in stats
    assert 'energy_consumption' in stats
    assert 'mean' in stats['energy_production']
    assert 'max' in stats['energy_production']