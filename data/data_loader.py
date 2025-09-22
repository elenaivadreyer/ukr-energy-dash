"""
Data loading and processing module for Ukraine Energy Dashboard
"""

import pandas as pd
import os
from typing import Optional, Dict, Any

class DataLoader:
    """Class for loading and processing energy data"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """Ensure data directory exists"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def load_sample_data(self) -> pd.DataFrame:
        """Load sample energy data for demonstration"""
        date_range = pd.date_range('2023-01-01', periods=365, freq='D')
        
        # Create realistic sample data with some seasonality
        import numpy as np
        np.random.seed(42)  # For reproducible results
        
        base_production = 100
        base_consumption = 95
        
        # Add seasonal variation
        seasonal_factor = np.sin(2 * np.pi * np.arange(365) / 365) * 10
        
        # Add random variation
        production_noise = np.random.normal(0, 5, 365)
        consumption_noise = np.random.normal(0, 3, 365)
        
        data = pd.DataFrame({
            'date': date_range,
            'energy_production': base_production + seasonal_factor + production_noise,
            'energy_consumption': base_consumption + seasonal_factor * 0.8 + consumption_noise,
            'renewable_production': np.random.uniform(10, 30, 365),
            'nuclear_production': np.random.uniform(30, 50, 365),
            'thermal_production': np.random.uniform(20, 40, 365)
        })
        
        # Ensure non-negative values
        data['energy_production'] = data['energy_production'].clip(lower=0)
        data['energy_consumption'] = data['energy_consumption'].clip(lower=0)
        
        return data
    
    def load_data_from_file(self, filename: str) -> Optional[pd.DataFrame]:
        """Load data from a CSV file"""
        file_path = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(file_path):
            print(f"Warning: File {file_path} not found")
            return None
        
        try:
            data = pd.read_csv(file_path)
            if 'date' in data.columns:
                data['date'] = pd.to_datetime(data['date'])
            return data
        except Exception as e:
            print(f"Error loading data from {file_path}: {e}")
            return None
    
    def save_data(self, data: pd.DataFrame, filename: str) -> bool:
        """Save data to a CSV file"""
        file_path = os.path.join(self.data_dir, filename)
        
        try:
            data.to_csv(file_path, index=False)
            print(f"Data saved to {file_path}")
            return True
        except Exception as e:
            print(f"Error saving data to {file_path}: {e}")
            return False
    
    def get_latest_data(self) -> pd.DataFrame:
        """Get the most recent data available"""
        # Try to load from file first, fallback to sample data
        data = self.load_data_from_file('energy_data.csv')
        
        if data is None:
            print("No data file found, using sample data")
            data = self.load_sample_data()
            # Save sample data for future use
            self.save_data(data, 'energy_data.csv')
        
        return data
    
    def get_summary_stats(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate summary statistics for the data"""
        numeric_cols = data.select_dtypes(include=[float, int]).columns
        
        stats = {}
        for col in numeric_cols:
            stats[col] = {
                'mean': data[col].mean(),
                'median': data[col].median(),
                'std': data[col].std(),
                'min': data[col].min(),
                'max': data[col].max(),
                'latest': data[col].iloc[-1] if not data.empty else None
            }
        
        return stats