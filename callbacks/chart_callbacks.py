"""
Callback functions for Ukraine Energy Dashboard
"""

from dash import Input, Output, callback
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta

@callback(
    Output('main-energy-chart', 'figure'),
    [Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date')]
)
def update_main_chart(start_date, end_date):
    """Update the main energy chart based on date range selection"""
    # This is a placeholder - in real implementation, you'd load filtered data
    from data.data_loader import DataLoader
    
    loader = DataLoader()
    data = loader.get_latest_data()
    
    if start_date and end_date:
        data = data[(data['date'] >= start_date) & (data['date'] <= end_date)]
    
    fig = px.line(data, x='date', y=['energy_production', 'energy_consumption'],
                  title='Ukraine Energy Production vs Consumption Over Time',
                  labels={'value': 'Energy (TWh)', 'date': 'Date', 'variable': 'Type'},
                  color_discrete_map={
                      'energy_production': '#2ecc71',
                      'energy_consumption': '#3498db'
                  })
    
    fig.update_layout(
        hovermode='x unified',
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        margin=dict(l=50, r=50, t=80, b=50),
        height=500
    )
    
    return fig

@callback(
    Output('energy-mix-chart', 'figure'),
    [Input('chart-type-dropdown', 'value')]
)
def update_energy_mix_chart(chart_type):
    """Update the energy mix chart based on chart type selection"""
    from data.data_loader import DataLoader
    
    loader = DataLoader()
    data = loader.get_latest_data()
    
    # Calculate averages for different energy sources
    energy_sources = []
    values = []
    
    if 'renewable_production' in data.columns:
        energy_sources.append('Renewable')
        values.append(data['renewable_production'].mean())
    
    if 'nuclear_production' in data.columns:
        energy_sources.append('Nuclear')
        values.append(data['nuclear_production'].mean())
    
    if 'thermal_production' in data.columns:
        energy_sources.append('Thermal')
        values.append(data['thermal_production'].mean())
    
    if chart_type == 'pie':
        fig = px.pie(values=values, names=energy_sources,
                     title='Average Energy Production Mix',
                     color_discrete_sequence=px.colors.qualitative.Set3)
    else:  # bar chart
        fig = px.bar(x=energy_sources, y=values,
                     title='Average Energy Production by Source',
                     labels={'x': 'Energy Source', 'y': 'Production (TWh)'},
                     color=energy_sources,
                     color_discrete_sequence=px.colors.qualitative.Set3)
    
    fig.update_layout(
        margin=dict(l=50, r=50, t=80, b=50),
        height=400
    )
    
    return fig

@callback(
    [Output('current-production-value', 'children'),
     Output('current-consumption-value', 'children'),
     Output('efficiency-value', 'children')],
    [Input('refresh-button', 'n_clicks')]
)
def update_metrics(n_clicks):
    """Update key metrics display"""
    from data.data_loader import DataLoader
    
    loader = DataLoader()
    data = loader.get_latest_data()
    
    if data.empty:
        return "N/A", "N/A", "N/A"
    
    latest_production = data['energy_production'].iloc[-1] if 'energy_production' in data.columns else 0
    latest_consumption = data['energy_consumption'].iloc[-1] if 'energy_consumption' in data.columns else 0
    efficiency = (latest_production / latest_consumption * 100) if latest_consumption > 0 else 0
    
    return f"{latest_production:.1f} TWh", f"{latest_consumption:.1f} TWh", f"{efficiency:.1f}%"

@callback(
    Output('data-summary', 'children'),
    [Input('summary-type-dropdown', 'value')]
)
def update_data_summary(summary_type):
    """Update data summary based on selected type"""
    from data.data_loader import DataLoader
    
    loader = DataLoader()
    data = loader.get_latest_data()
    stats = loader.get_summary_stats(data)
    
    if summary_type == 'production' and 'energy_production' in stats:
        stat = stats['energy_production']
        return f"""
        Mean: {stat['mean']:.2f} TWh
        Median: {stat['median']:.2f} TWh
        Min: {stat['min']:.2f} TWh
        Max: {stat['max']:.2f} TWh
        Latest: {stat['latest']:.2f} TWh
        """
    elif summary_type == 'consumption' and 'energy_consumption' in stats:
        stat = stats['energy_consumption']
        return f"""
        Mean: {stat['mean']:.2f} TWh
        Median: {stat['median']:.2f} TWh  
        Min: {stat['min']:.2f} TWh
        Max: {stat['max']:.2f} TWh
        Latest: {stat['latest']:.2f} TWh
        """
    else:
        return "Summary data not available"