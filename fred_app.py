import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date

# Set page config to light mode
st.set_page_config(page_title="FRED Data Dashboard", layout="wide", initial_sidebar_state="expanded")

# Apply custom CSS for light background
st.markdown(
    """
    <style>
    body {
        background-color: #ffffff;
        color: #000000;
    }
    .css-18e3th9 {
        background-color: #ffffff;
    }
    .streamlit-expanderHeader {
        background-color: #ffffff;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Load data
@st.cache_data  # Cache the data to avoid reloading on every interaction
def load_data():
    df = pd.read_csv('fred_weekly.csv', parse_dates=['date'], index_col='date')
    return df

df = load_data()

# Streamlit app
st.title("FRED Data Dashboard (WIP)")
st.write("Tracking interesting market data using FRED.")

# Sidebar for filters
st.sidebar.header("Filters")
start_date = st.sidebar.date_input("Select Start Date", value=date(2010, 1, 1))

# Filter data
filtered_df = df[df.index >= pd.to_datetime(start_date)]

# Get the latest value (last row) and the previous 52-period value
latest_values = filtered_df.iloc[-1]
previous_values = filtered_df.iloc[-53] if len(filtered_df) >= 53 else None

# Extract price values (latest and previous 52-period)
btc_price = latest_values['btc']
nasdaq_price = latest_values['nasdaq']
sp500_price = latest_values['SP500']
net_liq = latest_values['net_liq']

previous_btc_price = previous_values['btc'] if previous_values is not None else None
previous_nasdaq_price = previous_values['nasdaq'] if previous_values is not None else None
previous_sp500_price = previous_values['SP500'] if previous_values is not None else None
previous_sp500_price = previous_values['net_liq'] if previous_values is not None else None

# Extract pre-calculated change values
btc_change = latest_values['btc_change']
nasdaq_change = latest_values['nasdaq_change']
sp500_change = latest_values['sp500_change']
net_liq_change = latest_values['net_liq_change']

# Prepare data for the table
table_data = {
    "Metric": ["BTC Price", "Nasdaq Price", "S&P 500 Price", 'Net Liquidity'],
    "Latest Value": [
        f"${btc_price:,.2f}" if btc_price is not None else "N/A",
        f"${nasdaq_price:,.2f}" if nasdaq_price is not None else "N/A",
        f"${sp500_price:,.2f}" if sp500_price is not None else "N/A",
        f"${net_liq:,.2f}" if sp500_price is not None else "N/A"
    ],
    "Previous 52-Period Value": [
        f"${previous_btc_price:,.2f}" if previous_btc_price is not None else "N/A",
        f"${previous_nasdaq_price:,.2f}" if previous_nasdaq_price is not None else "N/A",
        f"${previous_sp500_price:,.2f}" if previous_sp500_price is not None else "N/A",
        f"${net_liq:,.2f}" if previous_sp500_price is not None else "N/A"
    ],
    "Change": [
        f"{btc_change * 100:.2f}%" if btc_change is not None else "N/A",
        f"{nasdaq_change * 100:.2f}%" if nasdaq_change is not None else "N/A",
        f"{sp500_change * 100:.2f}%" if sp500_change is not None else "N/A",
        f"{net_liq_change * 100:.2f}%" if sp500_change is not None else "N/A"
    ]
}

# Convert to DataFrame
table_df = pd.DataFrame(table_data)

# Display the table
st.subheader("Latest Price Values and Changes")
st.table(table_df)

# Plot Net Liquidity
st.subheader("Net Liquidity Over Time")
st.write("Net Liquidity = Federal Reserve's total assets less the TGA and RRP.")
fig_net_liq = px.line(filtered_df, x=filtered_df.index, y='net_liq', title='Net Liquidity')
st.plotly_chart(fig_net_liq)

# Plot Rolling Correlations
st.subheader("Rolling Correlations")
fig_corr = go.Figure()
fig_corr.add_trace(go.Scatter(x=filtered_df.index, y=filtered_df['corr_netliq_btc'], mode='lines', name='BTC'))
fig_corr.add_trace(go.Scatter(x=filtered_df.index, y=filtered_df['corr_netliq_nasdaq'], mode='lines', name='Nasdaq'))
fig_corr.add_trace(go.Scatter(x=filtered_df.index, y=filtered_df['corr_netliq_sp500'], mode='lines', name='S&P 500'))
fig_corr.update_layout(title='Rolling Correlations of Net Liquidity', xaxis_title='Date', yaxis_title='Correlation')
st.plotly_chart(fig_corr)

# Plot BTC vs Net Liquidity Change with Secondary Y-Axis
st.subheader("BTC vs Net Liquidity Change")
fig_btc = go.Figure()
# Primary Y-Axis: Net Liquidity Change
fig_btc.add_trace(go.Bar(
    x=filtered_df.index,
    y=filtered_df['net_liq_change'],
    name='Net Liquidity Change',
    marker_color=filtered_df['net_liq_change'].apply(lambda x: 'green' if x > 0 else 'red')
))
# Secondary Y-Axis: BTC Change
fig_btc.add_trace(go.Scatter(
    x=filtered_df.index,
    y=filtered_df['btc_change'],
    mode='lines',
    name='BTC Change',
    line=dict(color='red'),
    yaxis='y2'
))
# Update layout for secondary y-axis
fig_btc.update_layout(
    title='BTC vs Net Liquidity Change',
    xaxis_title='Date',
    yaxis_title='Net Liquidity Change',
    yaxis2=dict(
        title='BTC Change',
        overlaying='y',
        side='right'
    )
)
st.plotly_chart(fig_btc)

# Plot Nasdaq vs Net Liquidity Change with Secondary Y-Axis
st.subheader("Nasdaq vs Net Liquidity Change")
fig_nasdaq = go.Figure()
# Primary Y-Axis: Net Liquidity Change
fig_nasdaq.add_trace(go.Bar(
    x=filtered_df.index,
    y=filtered_df['net_liq_change'],
    name='Net Liquidity Change',
    marker_color=filtered_df['net_liq_change'].apply(lambda x: 'green' if x > 0 else 'red')
))
# Secondary Y-Axis: Nasdaq Change
fig_nasdaq.add_trace(go.Scatter(
    x=filtered_df.index,
    y=filtered_df['nasdaq_change'],
    mode='lines',
    name='Nasdaq Change',
    line=dict(color='green'),
    yaxis='y2'
))
# Update layout for secondary y-axis
fig_nasdaq.update_layout(
    title='Nasdaq vs Net Liquidity Change',
    xaxis_title='Date',
    yaxis_title='Net Liquidity Change',
    yaxis2=dict(
        title='Nasdaq Change',
        overlaying='y',
        side='right'
    )
)
st.plotly_chart(fig_nasdaq)

# Plot S&P 500 vs Net Liquidity Change with Secondary Y-Axis
st.subheader("S&P 500 vs Net Liquidity Change")
fig_sp500 = go.Figure()
# Primary Y-Axis: Net Liquidity Change
fig_sp500.add_trace(go.Bar(
    x=filtered_df.index,
    y=filtered_df['net_liq_change'],
    name='Net Liquidity Change',
    marker_color=filtered_df['net_liq_change'].apply(lambda x: 'green' if x > 0 else 'red')
))
# Secondary Y-Axis: S&P 500 Change
fig_sp500.add_trace(go.Scatter(
    x=filtered_df.index,
    y=filtered_df['sp500_change'],
    mode='lines',
    name='S&P 500 Change',
    line=dict(color='orange'),
    yaxis='y2'
))
# Update layout for secondary y-axis
fig_sp500.update_layout(
    title='S&P 500 vs Net Liquidity Change',
    xaxis_title='Date',
    yaxis_title='Net Liquidity Change',
    yaxis2=dict(
        title='S&P 500 Change',
        overlaying='y',
        side='right'
    )
)
st.plotly_chart(fig_sp500)

# Credit Cycle Charts
st.subheader("Credit Cycle Analysis")

# Chart 1: 10y2y Scatter 1
st.subheader("10Y2Y Spread")
fig_10y2y_1 = go.Figure()
fig_10y2y_1.add_trace(
    go.Scatter(
        x=filtered_df.index,
        y=filtered_df['10y2y'],
        mode='lines',
        name='10y2y',
        line=dict(color='blue')
    )
)
fig_10y2y_1.update_layout(
    title='10Y2Y Spread',
    xaxis_title='Date',
    yaxis_title='10y2y'
)
st.plotly_chart(fig_10y2y_1)

# Chart 3: 10y2y Change vs Nasdaq Change
st.subheader("10Y2Y Change vs Nasdaq Change (Annual)")
fig_10y2y_change = go.Figure()
# Primary Y-Axis: 10y2y Change
fig_10y2y_change.add_trace(
    go.Scatter(
        x=filtered_df.index,
        y=filtered_df['10y2y_change'],
        mode='markers',
        name='10y2y Change',
        marker=dict(color=filtered_df['10y2y_change'], colorscale='RdYlGn_r')
    )
)
# Secondary Y-Axis: Nasdaq Change
fig_10y2y_change.add_trace(
    go.Scatter(
        x=filtered_df.index,
        y=filtered_df['nasdaq_change'],
        mode='markers',
        name='Nasdaq Change',
        marker=dict(color='blue'),
        yaxis='y2'
    )
)
# Update layout for secondary y-axis
fig_10y2y_change.update_layout(
    title='10y2y Change vs Nasdaq Change',
    xaxis_title='Date',
    yaxis_title='10y2y Change',
    yaxis2=dict(
        title='Nasdaq Change',
        overlaying='y',
        side='right'
    )
)
st.plotly_chart(fig_10y2y_change)
