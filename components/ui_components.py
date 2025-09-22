"""
Reusable components for Ukraine Energy Dashboard
"""

from dash import html, dcc
from typing import List, Dict, Any

def create_dropdown(id: str, options: List[Dict[str, Any]], value: Any = None, 
                   placeholder: str = "Select an option") -> dcc.Dropdown:
    """Create a styled dropdown component"""
    return dcc.Dropdown(
        id=id,
        options=options,
        value=value,
        placeholder=placeholder,
        style={
            'margin': '10px 0',
            'borderRadius': '4px'
        }
    )

def create_date_picker(id: str, start_date=None, end_date=None) -> dcc.DatePickerRange:
    """Create a date picker component"""
    return dcc.DatePickerRange(
        id=id,
        start_date=start_date,
        end_date=end_date,
        display_format='YYYY-MM-DD',
        style={
            'margin': '10px 0'
        }
    )

def create_card(title: str, content, icon: str = None) -> html.Div:
    """Create a card component with title and content"""
    card_header = [html.H4(title, style={'margin': '0 0 15px 0', 'color': '#2c3e50'})]
    
    if icon:
        card_header.insert(0, html.I(className=f"fas fa-{icon}", 
                                   style={'marginRight': '10px', 'color': '#3498db'}))
    
    return html.Div([
        html.Div(card_header),
        html.Div(content)
    ], style={
        'backgroundColor': 'white',
        'padding': '20px',
        'borderRadius': '8px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
        'margin': '10px'
    })

def create_metric_card(value: str, label: str, color: str = "#3498db", 
                      trend: str = None) -> html.Div:
    """Create a metric display card"""
    card_content = [
        html.Div(value, style={
            'fontSize': '2.5rem',
            'fontWeight': 'bold',
            'color': color,
            'margin': '10px 0',
            'textAlign': 'center'
        }),
        html.Div(label, style={
            'color': '#7f8c8d',
            'fontSize': '1.1rem',
            'textAlign': 'center'
        })
    ]
    
    if trend:
        trend_color = '#27ae60' if '+' in trend else '#e74c3c'
        card_content.append(
            html.Div(trend, style={
                'color': trend_color,
                'fontSize': '0.9rem',
                'textAlign': 'center',
                'marginTop': '5px'
            })
        )
    
    return html.Div(card_content, style={
        'backgroundColor': 'white',
        'padding': '20px',
        'borderRadius': '8px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
        'margin': '10px',
        'transition': 'transform 0.2s ease',
        'cursor': 'pointer'
    })

def create_loading_spinner(id: str) -> dcc.Loading:
    """Create a loading spinner component"""
    return dcc.Loading(
        id=id,
        type="default",
        children=html.Div(id=f"{id}-content")
    )

def create_alert(message: str, type: str = "info") -> html.Div:
    """Create an alert component"""
    color_map = {
        'info': '#d1ecf1',
        'success': '#d4edda', 
        'warning': '#fff3cd',
        'error': '#f8d7da'
    }
    
    border_color_map = {
        'info': '#bee5eb',
        'success': '#c3e6cb',
        'warning': '#ffeaa7',
        'error': '#f5c6cb'
    }
    
    return html.Div(message, style={
        'padding': '12px',
        'marginBottom': '20px',
        'border': f'1px solid {border_color_map.get(type, "#bee5eb")}',
        'borderRadius': '4px',
        'backgroundColor': color_map.get(type, "#d1ecf1"),
        'color': '#495057'
    })

def create_button(id: str, text: str, style_type: str = "primary") -> html.Button:
    """Create a styled button component"""
    color_map = {
        'primary': '#3498db',
        'success': '#27ae60',
        'warning': '#f39c12',
        'danger': '#e74c3c'
    }
    
    return html.Button(text, id=id, style={
        'backgroundColor': color_map.get(style_type, '#3498db'),
        'color': 'white',
        'border': 'none',
        'padding': '10px 20px',
        'borderRadius': '4px',
        'cursor': 'pointer',
        'fontSize': '14px',
        'transition': 'background-color 0.2s ease'
    })

def create_tabs(id: str, tabs: List[Dict[str, str]]) -> dcc.Tabs:
    """Create a tabs component"""
    return dcc.Tabs(id=id, value=tabs[0]['value'] if tabs else None, children=[
        dcc.Tab(label=tab['label'], value=tab['value']) for tab in tabs
    ], style={
        'height': '44px'
    })