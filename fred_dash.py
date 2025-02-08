import requests
import json
import pandas as pd
import gspread
from datetime import date
from fredapi import Fred
import plotly.graph_objects as go
import plotly.io as pio
import plotly.subplots as sp
import os
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output
from flask import Flask
import numpy as np
import statsmodels.api as sm

# FRED API Key
fred = Fred(api_key='bcdbd0c11009bc3d7fec55ad2b5e50a6')

# Get Fred data and calculate net liquidity
date_index = pd.to_datetime(fred.get_series('FF').index)
#date_index = pd.to_datetime(fred.get_series('T10Y2Y').index)
data = {
    'date': date_index,
    'assets': fred.get_series('WALCL').reindex(date_index),
    'tga': fred.get_series('WTREGEN').reindex(date_index),
    'repo': fred.get_series('RRPONTSYD').reindex(date_index),
    'btc': fred.get_series('CBBTCUSD').reindex(date_index),
    'rates2y': fred.get_series('DGS2').reindex(date_index),
    'nasdaq': fred.get_series('NASDAQ100').reindex(date_index),
    'SP500': fred.get_series('SP500').reindex(date_index),
    '10y2y': fred.get_series('T10Y2Y').reindex(date_index)
}

df_fred = pd.DataFrame(data).set_index('date')
df_fred.fillna(method='ffill', inplace=True)
df_fred = df_fred.resample('W').last()

df_fred['net_liq'] = (df_fred['assets'] - (df_fred['tga'] * 1000 + df_fred['repo'] * 1000)) / 1000
df_fred['net_liq_change'] = df_fred['net_liq'].pct_change(periods=52)
df_fred['btc_change'] = df_fred['btc'].pct_change(periods=52)
df_fred['rates2y_change'] = df_fred['rates2y'].pct_change(periods=52)
df_fred['nasdaq_change'] = df_fred['nasdaq'].pct_change(periods=52)
df_fred['sp500_change'] = df_fred['SP500'].pct_change(periods=52)
df_fred['10y2y_change'] = df_fred['10y2y'].diff(periods=52)

window_size = 52

df_fred['corr_netliq_btc'] = df_fred['net_liq_change'].rolling(window=window_size).corr(df_fred['btc_change'])
df_fred['corr_netliq_nasdaq'] = df_fred['net_liq_change'].rolling(window=window_size).corr(df_fred['nasdaq_change'])
df_fred['corr_netliq_sp500'] = df_fred['net_liq_change'].rolling(window=window_size).corr(df_fred['sp500_change'])

##df_fred = df_fred[df_fred.index >= '2015-01-01']
df_fred.to_csv('fred_weekly.csv', index=True)


# Function to determine color
def get_color(value):
    return 'green' if value > 0 else 'red'

# Function to get latest values
def get_latest_values(df):
    latest = df.iloc[-1]
    return {
        'Net Liquidity Amount': f"${latest['net_liq']:,.2f}",  # Format as $ with commas and 2 decimal places
        'Net Liquidity Annual Change': f"{latest['net_liq_change'] * 100:.2f}%",  # Format as percentage with 2 decimal places
        'SP500 Amount': f"${latest['SP500']:,.2f}",  # Format as $ with commas and 2 decimal places
        'SP500 Annual Change': f"{latest['sp500_change'] * 100:.2f}%",  # Format as percentage with 2 decimal places
        'Nasdaq Amount': f"${latest['nasdaq']:,.2f}",  # Format as $ with commas and 2 decimal places
        'Nasdaq Annual Change': f"{latest['nasdaq_change'] * 100:.2f}%",  # Format as percentage with 2 decimal places
        'BTC Amount': f"${latest['btc']:,.2f}",  # Format as $ with commas and 2 decimal places
        'BTC Annual Change': f"{latest['btc_change'] * 100:.2f}%"  # Format as percentage with 2 decimal places
    }

# Create and run app
server = Flask(__name__)
app = dash.Dash(__name__, server=server)

# App layout with tabs
app.layout = html.Div([
    html.H1("FRED Data Dashboard"),
    dcc.Tabs(id="tabs", value='tab-1', children=[
        dcc.Tab(label='Net Liquidity', value='tab-1', children=[
            html.P("Net Liquidity = Federal Reserve's total assets less the Treasury General Account (TGA) and Reverse Repo Operations (RRP). It is a simple, imperfect market liquidity measure.",
                style={'font-size': '20px', 'color': '#555','margin-top': '10px','margin-bottom': '20px'}),
            html.H3(f"Latest Values (Updated: {df_fred.index[-1].strftime('%Y-%m-%d')})"),
    
            html.Label("Select Start Date", style={'font-size': '18px', 'font-weight': 'bold'}),
            dcc.DatePickerSingle(
                id='date-picker',
                min_date_allowed=df_fred.index.min(),
                max_date_allowed=df_fred.index.max(),
                initial_visible_month=df_fred.index.min(),
                date=df_fred.index.min()
            ),
            dcc.Graph(id='correlation-graph')
        ]),
        dcc.Tab(label='Credit Cycle', value='tab-2', children=[
            html.Div([
                html.H3('Credit Cycle Analysis'),
                html.Label("Select Start Date", style={'font-size': '18px', 'font-weight': 'bold'}),
                dcc.DatePickerSingle(
                    id='date-picker-2',
                    min_date_allowed=df_fred.index.min(),
                    max_date_allowed=df_fred.index.max(),
                    initial_visible_month=df_fred.index.min(),
                    date=df_fred.index.min()
                ),
                dcc.Graph(id='credit-cycle-graph')
            ])
        ]),
        dcc.Tab(label='Tab 3', value='tab-3', children=[
            html.Div([
                html.H3('Tab 3 Content'),
                # Add content for Tab 3 here
            ])
        ]),
        dcc.Tab(label='Tab 4', value='tab-4', children=[
            html.Div([
                html.H3('Tab 4 Content'),
                # Add content for Tab 4 here
            ])
        ]),
        dcc.Tab(label='Tab 5', value='tab-5', children=[
            html.Div([
                html.H3('Tab 5 Content'),
                # Add content for Tab 5 here
            ])
        ]),
    ])
])

# Callback to update the graph for Tab 2
@app.callback(
    Output('credit-cycle-graph', 'figure'),
    [Input('date-picker-2', 'date')]
)

def update_credit_cycle_graph(selected_date):
    # Filter DataFrame based on selected date
    filtered_df = df_fred[df_fred.index >= selected_date]

    # Ensure there is a valid max date
    max_date = filtered_df.index.max() if not filtered_df.empty else selected_date

    # Create a new 2x2 figure
    fig = sp.make_subplots(
        rows=2, cols=2,
        subplot_titles=('10y2y Scatter 1', '10y2y Scatter 2',
                        '10y2y Change', 'Placeholder 4'),
        shared_xaxes=True,
        vertical_spacing=0.1,
        specs=[[{"secondary_y": True}, {"secondary_y": True}],
               [{"secondary_y": True}, {"secondary_y": True}]]
    )

    # Add scatter plot for 10y2y to subplot 1,1
    fig.add_trace(
        go.Scatter(x=filtered_df.index, y=filtered_df['10y2y'], mode='lines', name='10y2y Scatter 1', marker=dict(color='blue')),
        row=1, col=1, secondary_y=False
    )

    # Add scatter plot for 10y2y to subplot 1,2
    fig.add_trace(
        go.Scatter(x=filtered_df.index, y=filtered_df['10y2y'], mode='lines', name='10y2y Scatter 2', marker=dict(color='red')),
        row=1, col=2, secondary_y=False
    )
    
    # Add scatter plot for 10y2y_change to subplot 2,1
    fig.add_trace(
        go.Scatter(x=filtered_df.index, y=filtered_df['10y2y_change'], mode='markers', name='10y2y Change',
                   marker=dict(color=filtered_df['10y2y_change'], colorscale='RdYlGn_r')),
        row=2, col=1, secondary_y=False
    )
    
    fig.add_trace(
        go.Scatter(x=filtered_df.index, y=filtered_df['nasdaq_change'], mode='markers', name='Nasdaq Change',
                   marker=dict(color='blue')),
        row=2, col=1, secondary_y=True
    )

    # Update layout
    fig.update_layout(
        height=1200, width=2800,
        showlegend=False,
        margin=dict(l=50, r=50, t=50, b=50),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )

    # Update x-axis range
    fig.update_xaxes(range=[selected_date, max_date], row=1, col=1)
    fig.update_xaxes(range=[selected_date, max_date], row=1, col=2)
    fig.update_xaxes(range=[selected_date, max_date], row=2, col=1)
    fig.update_xaxes(range=[selected_date, max_date], row=2, col=2)

    return fig

# Callback to update the graph based on the selected date
@app.callback(
    Output('correlation-graph', 'figure'),
    [Input('date-picker', 'date')]
)
def update_graph(selected_date):
    # Filter the DataFrame based on the selected date
    filtered_df = df_fred[df_fred.index >= selected_date]
    
    # Create a new figure with the filtered data
    fig = sp.make_subplots(
        rows=2, cols=2,
        subplot_titles=('Net Liquidity Rolling Correlations', 'Net Liquidity and BTC Annual Change',
                        'Net Liquidity and Nasdaq Annual Change', 'Net Liquidity and SP500 Annual Change'),
        shared_xaxes=True,
        vertical_spacing=0.1,
        specs=[[{'secondary_y': True}, {'secondary_y': True}],
               [{'secondary_y': True}, {'secondary_y': True}]]
    )

    # Add correlation chart to subplot 1,1
    fig.add_trace(
        go.Scatter(x=filtered_df.index, y=filtered_df['corr_netliq_btc'], mode='lines', name='BTC', line=dict(color='grey')),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=filtered_df.index, y=filtered_df['corr_netliq_nasdaq'], mode='lines', name='Nasdaq', line=dict(color='blue')),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=filtered_df.index, y=filtered_df['corr_netliq_sp500'], mode='lines', name='SP500', line=dict(color='green')),
        row=1, col=1
    )

    # Add BTC chart to subplot 1,2
    fig.add_trace(
        go.Bar(x=filtered_df.index, y=filtered_df['net_liq_change'], marker=dict(color=[get_color(v) for v in filtered_df['net_liq_change']]), name='Net Liquidity Change'),
        row=1, col=2
    )
    fig.add_trace(
        go.Scatter(x=filtered_df.index, y=filtered_df['btc_change'], mode='lines', name='BTC Annual Change', line=dict(color='grey')),
        row=1, col=2, secondary_y=True
    )

    # Add Nasdaq chart to subplot 2,1
    fig.add_trace(
        go.Bar(x=filtered_df.index, y=filtered_df['net_liq_change'], marker=dict(color=[get_color(v) for v in filtered_df['net_liq_change']]), name='Net Liquidity Change'),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(x=filtered_df.index, y=filtered_df['nasdaq_change'], mode='lines', name='Nasdaq Annual Change', line=dict(color='blue')),
        row=2, col=1, secondary_y=True
    )

    # Add SP500 chart to subplot 2,2
    fig.add_trace(
        go.Bar(x=filtered_df.index, y=filtered_df['net_liq_change'], marker=dict(color=[get_color(v) for v in filtered_df['net_liq_change']]), name='Net Liquidity Change'),
        row=2, col=2
    )
    fig.add_trace(
        go.Scatter(x=filtered_df.index, y=filtered_df['sp500_change'], mode='lines', name='SP500 Annual Change', line=dict(color='green')),
        row=2, col=2, secondary_y=True
    ),


    # Update layout with titles, axis labels, and yaxis2
    fig.update_layout(
        height=1200,
        width=2800,
        showlegend=False,
        yaxis=dict(title='Net Liquidity Change', side='left'),
        yaxis2=dict(title='Annual Change', side='right', overlaying='y1'),
        margin=dict(l=100, r=150, t=100, b=100),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )

    # Update x-axis range for each subplot individually
    fig.update_xaxes(range=[selected_date, filtered_df.index.max()], row=1, col=1)
    fig.update_xaxes(range=[selected_date, filtered_df.index.max()], row=1, col=2)
    fig.update_xaxes(range=[selected_date, filtered_df.index.max()], row=2, col=1)
    fig.update_xaxes(range=[selected_date, filtered_df.index.max()], row=2, col=2)

    # Add y-axis updates for each subplot, including secondary y-axis
    fig.update_yaxes(title_text='Correlation', row=1, col=1)
    fig.update_yaxes(title_text='Net Liquidity Change', row=1, col=2)
    fig.update_yaxes(title_text='Net Liquidity Change', row=2, col=1)
    fig.update_yaxes(title_text='Net Liquidity Change', row=2, col=2)
    fig.update_yaxes(title_text='BTC Annual Change', row=1, col=2, secondary_y=True)
    fig.update_yaxes(title_text='Nasdaq Annual Change', row=2, col=1, secondary_y=True)
    fig.update_yaxes(title_text='SP500 Annual Change', row=2, col=2, secondary_y=True)

    return fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=False)
