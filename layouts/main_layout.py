"""
Layout components for Ukraine Energy Dashboard
"""

from dash import html, dcc
import plotly.express as px
import pandas as pd

def create_header() -> html.Div:
    """Create the main header component"""
    return html.Div([
        html.H1("Ukraine Energy Dashboard", 
                className='main-title',
                style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': 10}),
        html.P("Real-time monitoring of Ukraine's energy infrastructure",
               style={'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': 18,
                     'marginBottom': 30})
    ], className='main-header')

def create_metrics_row(data: pd.DataFrame) -> html.Div:
    """Create a row of key metrics"""
    if data.empty:
        return html.Div("No data available", style={'textAlign': 'center'})
    
    latest_production = data['energy_production'].iloc[-1] if 'energy_production' in data.columns else 0
    latest_consumption = data['energy_consumption'].iloc[-1] if 'energy_consumption' in data.columns else 0
    avg_production = data['energy_production'].mean() if 'energy_production' in data.columns else 0
    efficiency = (latest_production / latest_consumption * 100) if latest_consumption > 0 else 0
    
    return html.Div([
        html.Div([
            html.Div([
                html.Div(f"{latest_production:.1f}", className='metric-value'),
                html.Div("Current Production (TWh)", className='metric-label')
            ], className='metric-card', style={'backgroundColor': '#e8f5e8'})
        ], style={'width': '24%', 'display': 'inline-block'}),
        
        html.Div([
            html.Div([
                html.Div(f"{latest_consumption:.1f}", className='metric-value'),
                html.Div("Current Consumption (TWh)", className='metric-label')
            ], className='metric-card', style={'backgroundColor': '#e8f0ff'})
        ], style={'width': '24%', 'display': 'inline-block'}),
        
        html.Div([
            html.Div([
                html.Div(f"{avg_production:.1f}", className='metric-value'),
                html.Div("Average Production (TWh)", className='metric-label')
            ], className='metric-card', style={'backgroundColor': '#fff5e6'})
        ], style={'width': '24%', 'display': 'inline-block'}),
        
        html.Div([
            html.Div([
                html.Div(f"{efficiency:.1f}%", className='metric-value'),
                html.Div("Production Efficiency", className='metric-label')
            ], className='metric-card', style={'backgroundColor': '#f0f8ff'})
        ], style={'width': '24%', 'display': 'inline-block'})
    ], style={'textAlign': 'center', 'margin': '20px 0'})

def create_main_chart(data: pd.DataFrame) -> dcc.Graph:
    """Create the main energy chart"""
    if data.empty:
        return dcc.Graph(figure=px.scatter(title="No data available"))
    
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
    
    return dcc.Graph(id='main-energy-chart', figure=fig)

def create_energy_mix_chart(data: pd.DataFrame) -> dcc.Graph:
    """Create energy mix breakdown chart"""
    if data.empty or not any(col in data.columns for col in ['renewable_production', 'nuclear_production', 'thermal_production']):
        return dcc.Graph(figure=px.pie(title="Energy mix data not available"))
    
    # Calculate averages for pie chart
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
    
    fig = px.pie(values=values, names=energy_sources,
                 title='Average Energy Production Mix',
                 color_discrete_sequence=px.colors.qualitative.Set3)
    
    fig.update_layout(
        margin=dict(l=50, r=50, t=80, b=50),
        height=400
    )
    
    return dcc.Graph(id='energy-mix-chart', figure=fig)

def create_info_panel() -> html.Div:
    """Create information panel"""
    return html.Div([
        html.H3("Dashboard Information", style={'color': '#2c3e50', 'marginBottom': 20}),
        html.Div([
            html.H4("Features:", style={'color': '#34495e'}),
            html.Ul([
                html.Li("Real-time energy production monitoring"),
                html.Li("Energy consumption tracking and analysis"),
                html.Li("Historical data visualization"),
                html.Li("Energy mix breakdown by source"),
                html.Li("Key performance indicators")
            ], style={'lineHeight': '1.6'})
        ]),
        html.Hr(),
        html.Div([
            html.H4("Data Sources:", style={'color': '#34495e'}),
            html.P("This dashboard uses sample data for demonstration purposes. In a production environment, it would connect to real energy monitoring systems and databases.")
        ])
    ], className='info-panel', style={'backgroundColor': '#f8f9fa', 'borderRadius': '8px', 'padding': '20px', 'margin': '20px'})

def create_main_layout(data: pd.DataFrame) -> html.Div:
    """Create the complete main layout"""
    return html.Div([
        create_header(),
        create_metrics_row(data),
        
        html.Div([
            html.Div([
                create_main_chart(data)
            ], className='chart-container', style={'width': '70%', 'display': 'inline-block', 'verticalAlign': 'top'}),
            
            html.Div([
                create_energy_mix_chart(data)
            ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top'})
        ], style={'margin': '20px 0'}),
        
        create_info_panel()
    ])