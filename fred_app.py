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

# Load weekly data
@st.cache_data  # Cache the data to avoid reloading on every interaction
def load_weekly_data():
    df = pd.read_csv('fred_weekly.csv', parse_dates=['date'], index_col='date')
    return df

# Load monthly data for the new chart
@st.cache_data
def load_monthly_data():
    df = pd.read_csv('fred_monthly.csv', parse_dates=['date'], index_col='date')
    return df

df_weekly = load_weekly_data()
df_monthly = load_monthly_data()

# Streamlit app
st.title("FRED Data Dashboard (WIP)")
st.write("Tracking market cycles using FRED data.")

# Sidebar for filters
st.sidebar.header("Filters")
start_date = st.sidebar.date_input("Select Start Date", value=date(2010, 1, 1))

# Filter data
filtered_weekly_df = df_weekly[df_weekly.index >= pd.to_datetime(start_date)]
filtered_monthly_df = df_monthly[df_monthly.index >= pd.to_datetime(start_date)]
filtered_monthly_df_2015 = filtered_monthly_df[filtered_monthly_df.index >= '2015-01-01']

# Get the latest value (last row) and the previous 52-period value
latest_values = filtered_weekly_df.iloc[-1]
previous_values = filtered_weekly_df.iloc[-53] if len(filtered_weekly_df) >= 53 else None

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

# Get the latest date for weekly data
latest_weekly_date = filtered_weekly_df.index[-1].strftime('%Y-%m-%d')
latest_monthly_date = filtered_monthly_df.index[-1].strftime('%Y-%m-%d')

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

# Display the weekly table
st.subheader("Latest Weekly Data")
st.write(f"Data as of: {latest_weekly_date}")
st.table(table_df)

# Get the latest monthly values (last row of monthly data)
latest_monthly = filtered_monthly_df.iloc[-1]

# Prepare data for the monthly table
monthly_table_data = {
    "Metric": ["BTC Monthly Return", "Nasdaq Monthly Return", "S&P 500 Monthly Return", "BBK GDP Growth", "CPI YoY", "CPI MoM Annualized", "Market Regime"],
    "Latest Value": [
        f"{latest_monthly['btc_return'] * 100:.2f}%",
        f"{latest_monthly['ndx_return'] * 100:.2f}%",
        f"{latest_monthly['spx_return'] * 100:.2f}%",
        f"{latest_monthly['bbk_gdp_yoy']:.2f}%",
        f"{latest_monthly['cpi_yoy']:.2f}%",
        f"{latest_monthly['cpi_annualized_mom']:.2f}%",
        latest_monthly['market_regime_V3']
    ]
}

# Convert to DataFrame
monthly_table_df = pd.DataFrame(monthly_table_data)

# Display the monthly table
st.subheader("Latest Monthly Data")
st.write(f"Data as of: {filtered_monthly_df.index[-1].strftime('%B %Y')}")
st.table(monthly_table_df)

# Define color map for market regimes (keep this outside tabs)
color_map = {
    "Goldilocks": "green",
    "Inflation": "blue",
    "Deflation": "red",
    "Stagflation": "orange"
}

# Create three tabs
tab1, tab2, tab3 = st.tabs(["Market Regime Analysis", "Net Liquidity Analysis", "Credit Cycle Analysis"])

# Market Regime Tab
with tab1:
    st.subheader("Market Regime Analysis")
    st.write("Regimes use BBK GDP & CPI MoM Annualized to estimate market regimes above/below 2% growth (1 month lag)")
    
    # Display the regime data table with colored backgrounds
    def color_regime(val):
        if val == 'Goldilocks':
            return 'background-color: lightgreen'
        elif val == 'Inflation':
            return 'background-color: lightblue'
        elif val == 'Deflation':
            return 'background-color: lightcoral'
        elif val == 'Stagflation':
            return 'background-color: orange'
        return ''

    # Create regime data table with additional returns
    regime_data = filtered_monthly_df_2015[['bbk_gdp_yoy_lagged', 'cpi_annualized_mom_lagged', 'spx_return', 'ndx_return', 'btc_return', 'market_regime_V3']].copy()
    regime_data = regime_data.round(4)  # Round to 4 decimal places for cleaner display
    regime_data.columns = ['GDP Growth', 'CPI Growth', 'S&P500 Returns', 'NASDAQ Returns', 'Bitcoin Returns', 'Market Regime']

    st.write("Monthly Data by Regime:")
    st.dataframe(regime_data.style.applymap(color_regime, subset=['Market Regime']))

    # Calculate and display regime counts
    regime_counts = filtered_monthly_df_2015['market_regime_V3'].value_counts()
    st.write("Number of Months in Each Regime:")
    st.dataframe(regime_counts)

    # Calculate and display average returns by market regime
    avg_returns = filtered_monthly_df_2015.groupby('market_regime_V3')[['spx_return', 'ndx_return', 'btc_return']].mean()
    avg_returns = avg_returns.round(4) * 100  # Convert to percentage
    avg_returns.columns = ['S&P500 Avg Return %', 'NASDAQ Avg Return %', 'Bitcoin Avg Return %']

    # Display average returns table with colored backgrounds
    def color_returns(val):
        if val > 0:
            return f'background-color: rgba(0, 255, 0, {min(abs(val)/20, 0.5)})'
        else:
            return f'background-color: rgba(255, 0, 0, {min(abs(val)/20, 0.5)})'

    st.write("Average Monthly Returns by Market Regime:")
    st.dataframe(avg_returns.style.applymap(color_returns))

    # Create scatter plot of GDP vs CPI colored by regime
    fig_regime_scatter = go.Figure()

    for regime, color in color_map.items():
        regime_data = filtered_monthly_df_2015[filtered_monthly_df_2015['market_regime_V3'] == regime]
        fig_regime_scatter.add_trace(
            go.Scatter(
                x=regime_data['bbk_gdp_yoy_lagged'],
                y=regime_data['cpi_annualized_mom_lagged'],
                mode='markers',
                name=regime,
                marker=dict(color=color, size=8, opacity=0.7)
            )
        )

    # Add horizontal and vertical lines at 2%
    fig_regime_scatter.add_hline(y=0.02, line_dash="dash", line_color="gray")
    fig_regime_scatter.add_vline(x=0.02, line_dash="dash", line_color="gray")

    # Update layout
    fig_regime_scatter.update_layout(
        title='GDP Growth vs CPI Growth by Market Regime',
        xaxis_title='GDP Growth (YoY)',
        yaxis_title='CPI Growth (YoY)',
        template='plotly_white'
    )

    st.plotly_chart(fig_regime_scatter)

    # New Chart: Bitcoin Price Scatter Plot Colored by Market Regime (2015-Onward)
    st.subheader("Bitcoin by Market Regime")

    # Create the scatter plot using Plotly
    fig_btc_regime = go.Figure()
    for regime, color in color_map.items():
        regime_data = filtered_monthly_df_2015[filtered_monthly_df_2015['market_regime_V3'] == regime]
        fig_btc_regime.add_trace(
            go.Scatter(
                x=regime_data.index,
                y=regime_data['btc'],
                mode='markers',
                name=regime,
                marker=dict(color=color, size=8, opacity=0.7)
            )
        )

    # Update layout
    fig_btc_regime.update_layout(
        title='Bitcoin Price by Market Regime (2015-Onward)',
        #yaxis_title='Bitcoin Price (USD)',
        yaxis_type='log',  # Use log scale for y-axis
        legend=dict(x=1.05, y=1, xanchor='left', yanchor='top'),
        template='plotly_white'
    )

    # Format x-axis to show years
    fig_btc_regime.update_xaxes(
        tickformat='%Y',
        dtick='M12'  # Show ticks every 12 months
    )

    st.plotly_chart(fig_btc_regime)

    # New Chart: Bitcoin Price Line Chart with Market Regime Background
    st.subheader("Bitcoin by Market Regime")

    # Create the line plot using Plotly
    fig_btc_regime = go.Figure()

    # First, create a list of all regime changes with their dates and colors
    regime_changes = []
    current_regime = None
    for date, regime in filtered_monthly_df_2015['market_regime_V3'].items():
        if regime != current_regime:
            regime_changes.append((date, regime))
            current_regime = regime

    # Track which regimes we've already added to the legend
    added_to_legend = set()

    # Add shaded backgrounds for each regime period
    for i in range(len(regime_changes)-1):
        start_date = regime_changes[i][0]
        end_date = regime_changes[i+1][0]
        regime = regime_changes[i][1]
        
        fig_btc_regime.add_vrect(
            x0=start_date,
            x1=end_date,
            fillcolor=color_map[regime],
            opacity=0.2,
            layer="below",
            line_width=0,
            name=regime,
            showlegend=(regime not in added_to_legend)  # Only show in legend if we haven't seen this regime before
        )
        added_to_legend.add(regime)

    # Add the last regime period to the end of the data
    if regime_changes:
        last_start = regime_changes[-1][0]
        last_regime = regime_changes[-1][1]
        fig_btc_regime.add_vrect(
            x0=last_start,
            x1=filtered_monthly_df_2015.index[-1],
            fillcolor=color_map[last_regime],
            opacity=0.2,
            layer="below",
            line_width=0,
            name=last_regime,
            showlegend=(last_regime not in added_to_legend)  # Only show in legend if we haven't seen this regime before
        )

    # Add BTC price line
    fig_btc_regime.add_trace(
        go.Scatter(
            x=filtered_monthly_df_2015.index,
            y=filtered_monthly_df_2015['btc'],
            mode='lines',
            name='Bitcoin Price',
            line=dict(color='black', width=2)
        )
    )

    # Update layout
    fig_btc_regime.update_layout(
        title='Bitcoin Price by Market Regime (2015-Onward)',
        yaxis_type='log',  # Use log scale for y-axis
        template='plotly_white',
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.05
        ),
        xaxis=dict(
            showgrid=False,
            tickformat='%Y',
            dtick='M12'  # Show ticks every 12 months
        ),
        yaxis=dict(
            showgrid=False
        )
    )

    # Format x-axis to show years
    fig_btc_regime.update_xaxes(
        tickformat='%Y',
        dtick='M12'  # Show ticks every 12 months
    )

    st.plotly_chart(fig_btc_regime)

    # New Chart: Bitcoin Price Scatter Plot Colored by Market Regime (2015-Onward)
    st.subheader("Nasdaq by Market Regime")

    # Create the scatter plot using Plotly
    fig_ndq_regime = go.Figure()
    for regime, color in color_map.items():
        regime_data = filtered_monthly_df_2015[filtered_monthly_df_2015['market_regime_V3'] == regime]
        fig_ndq_regime.add_trace(
            go.Scatter(
                x=regime_data.index,
                y=regime_data['ndx'],
                mode='markers',
                name=regime,
                marker=dict(color=color, size=8, opacity=0.7)
            )
        )

    # Update layout
    fig_ndq_regime.update_layout(
        title='Nasdaq Price by Market Regime (2015-Onward)',
        yaxis_type='log',  # Use log scale for y-axis
        legend=dict(x=1.05, y=1, xanchor='left', yanchor='top'),
        template='plotly_white'
    )

    # Format x-axis to show years
    fig_ndq_regime.update_xaxes(
        tickformat='%Y',
        dtick='M12'  # Show ticks every 12 months
    )

    st.plotly_chart(fig_ndq_regime)

    # New Chart: Nasdaq Price Line Chart with Market Regime Background
    st.subheader("Nasdaq by Market Regime")

    # Create the line plot using Plotly
    fig_ndx_regime = go.Figure()

    # Add shaded backgrounds for each regime period (reusing regime_changes from before)
    added_to_legend = set()  # Reset legend tracking
    
    # Add shaded backgrounds for each regime period
    for i in range(len(regime_changes)-1):
        start_date = regime_changes[i][0]
        end_date = regime_changes[i+1][0]
        regime = regime_changes[i][1]
        
        fig_ndx_regime.add_vrect(
            x0=start_date,
            x1=end_date,
            fillcolor=color_map[regime],
            opacity=0.2,
            layer="below",
            line_width=0,
            name=regime,
            showlegend=(regime not in added_to_legend)
        )
        added_to_legend.add(regime)

    # Add the last regime period to the end of the data
    if regime_changes:
        last_start = regime_changes[-1][0]
        last_regime = regime_changes[-1][1]
        fig_ndx_regime.add_vrect(
            x0=last_start,
            x1=filtered_monthly_df_2015.index[-1],
            fillcolor=color_map[last_regime],
            opacity=0.2,
            layer="below",
            line_width=0,
            name=last_regime,
            showlegend=(last_regime not in added_to_legend)
        )

    # Add Nasdaq price line
    fig_ndx_regime.add_trace(
        go.Scatter(
            x=filtered_monthly_df_2015.index,
            y=filtered_monthly_df_2015['ndx'],
            mode='lines',
            name='Nasdaq Price',
            line=dict(color='black', width=2)
        )
    )

    # Update layout
    fig_ndx_regime.update_layout(
        title='Nasdaq Price by Market Regime (2015-Onward)',
        yaxis_type='log',  # Use log scale for y-axis
        template='plotly_white',
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.05
        ),
        xaxis=dict(
            showgrid=False,
            tickformat='%Y',
            dtick='M12'  # Show ticks every 12 months
        ),
        yaxis=dict(
            showgrid=False
        )
    )

    st.plotly_chart(fig_ndx_regime)

    # Update existing regime scatter plots to remove gridlines
    # For the GDP vs CPI scatter plot
    fig_regime_scatter.update_layout(
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False)
    )

    # For the Bitcoin scatter plot
    fig_btc_regime.update_layout(
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False)
    )

    # For the Nasdaq scatter plot
    fig_ndq_regime.update_layout(
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False)
    )

# Net Liquidity Tab
with tab2:
    st.subheader("Net Liquidity Analysis")
    
    # Add M2 YoY vs BTC YoY Change chart (now first)
    st.write("M2 Money Supply Year-over-Year Change vs Bitcoin Year-over-Year Return")
    fig_m2_btc = go.Figure()
    
    # Primary Y-Axis: M2 YoY Change
    fig_m2_btc.add_trace(go.Bar(
        x=filtered_monthly_df.index,
        y=filtered_monthly_df['m2_yoy'],
        name='M2 YoY Change',
        marker_color=filtered_monthly_df['m2_yoy'].apply(lambda x: 'green' if x > 0 else 'red')
    ))
    
    # Secondary Y-Axis: BTC YoY Change
    fig_m2_btc.add_trace(go.Scatter(
        x=filtered_monthly_df.index,
        y=filtered_monthly_df['btc_yoy'],  # Now using yearly change
        mode='lines',
        name='BTC Annual Return',
        line=dict(color='orange'),
        yaxis='y2'
    ))
    
    # Update layout for secondary y-axis
    fig_m2_btc.update_layout(
        title='M2 YoY Change vs BTC Annual Return',
        xaxis_title='Date',
        yaxis_title='M2 YoY Change (%)',
        yaxis2=dict(
            title='BTC Annual Return (%)',
            overlaying='y',
            side='right'
        )
    )
    st.plotly_chart(fig_m2_btc)

    # Move all other net liquidity related charts below
    st.write("Net Liquidity = Federal Reserve's total assets less the TGA and RRP.")
    fig_net_liq = px.line(filtered_weekly_df, x=filtered_weekly_df.index, y='net_liq', title='Net Liquidity')
    st.plotly_chart(fig_net_liq)

    # Rolling Correlations
    st.subheader("Rolling Correlations")
    fig_corr = go.Figure()
    fig_corr.add_trace(go.Scatter(x=filtered_weekly_df.index, y=filtered_weekly_df['corr_netliq_btc'], mode='lines', name='BTC'))
    fig_corr.add_trace(go.Scatter(x=filtered_weekly_df.index, y=filtered_weekly_df['corr_netliq_nasdaq'], mode='lines', name='Nasdaq'))
    fig_corr.add_trace(go.Scatter(x=filtered_weekly_df.index, y=filtered_weekly_df['corr_netliq_sp500'], mode='lines', name='S&P 500'))
    fig_corr.update_layout(title='Rolling Correlations of Net Liquidity', xaxis_title='Date', yaxis_title='Correlation')
    st.plotly_chart(fig_corr)

    # BTC vs Net Liquidity Change
    st.subheader("BTC vs Net Liquidity Change")
    fig_btc = go.Figure()
    # Primary Y-Axis: Net Liquidity Change
    fig_btc.add_trace(go.Bar(
        x=filtered_weekly_df.index,
        y=filtered_weekly_df['net_liq_change'],
        name='Net Liquidity Change',
        marker_color=filtered_weekly_df['net_liq_change'].apply(lambda x: 'green' if x > 0 else 'red')
    ))
    # Secondary Y-Axis: BTC Change
    fig_btc.add_trace(go.Scatter(
        x=filtered_weekly_df.index,
        y=filtered_weekly_df['btc_change'],
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

    # Nasdaq vs Net Liquidity Change
    st.subheader("Nasdaq vs Net Liquidity Change")
    fig_nasdaq = go.Figure()
    # Primary Y-Axis: Net Liquidity Change
    fig_nasdaq.add_trace(go.Bar(
        x=filtered_weekly_df.index,
        y=filtered_weekly_df['net_liq_change'],
        name='Net Liquidity Change',
        marker_color=filtered_weekly_df['net_liq_change'].apply(lambda x: 'green' if x > 0 else 'red')
    ))
    # Secondary Y-Axis: Nasdaq Change
    fig_nasdaq.add_trace(go.Scatter(
        x=filtered_weekly_df.index,
        y=filtered_weekly_df['nasdaq_change'],
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

    # S&P 500 vs Net Liquidity Change
    st.subheader("S&P 500 vs Net Liquidity Change")
    fig_sp500 = go.Figure()
    # Primary Y-Axis: Net Liquidity Change
    fig_sp500.add_trace(go.Bar(
        x=filtered_weekly_df.index,
        y=filtered_weekly_df['net_liq_change'],
        name='Net Liquidity Change',
        marker_color=filtered_weekly_df['net_liq_change'].apply(lambda x: 'green' if x > 0 else 'red')
    ))
    # Secondary Y-Axis: S&P 500 Change
    fig_sp500.add_trace(go.Scatter(
        x=filtered_weekly_df.index,
        y=filtered_weekly_df['sp500_change'],
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

# Credit Cycle Tab
with tab3:
    st.subheader("Credit Cycle Analysis")
    
    # Move all credit cycle related charts here
    # 10Y2Y Spread
    st.subheader("10Y2Y Spread")
    fig_10y2y_1 = go.Figure()
    fig_10y2y_1.add_trace(
        go.Scatter(
            x=filtered_weekly_df.index,
            y=filtered_weekly_df['10y2y'],
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
            x=filtered_weekly_df.index,
            y=filtered_weekly_df['10y2y_change'],
            mode='markers',
            name='10y2y Change',
            marker=dict(color=filtered_weekly_df['10y2y_change'], colorscale='RdYlGn_r')
        )
    )
    # Secondary Y-Axis: Nasdaq Change
    fig_10y2y_change.add_trace(
        go.Scatter(
            x=filtered_weekly_df.index,
            y=filtered_weekly_df['nasdaq_change'],
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

    # Chart: 10y2y Change vs BTC Change
    st.subheader("10Y2Y Change vs BTC Change (Annual)")
    fig_10y2y_btc = go.Figure()
    # Primary Y-Axis: 10y2y Change
    fig_10y2y_btc.add_trace(
        go.Scatter(
            x=filtered_weekly_df.index,
            y=filtered_weekly_df['10y2y_change'],
            mode='markers',
            name='10y2y Change',
            marker=dict(color=filtered_weekly_df['10y2y_change'], colorscale='RdYlGn_r')
        )
    )
    # Secondary Y-Axis: BTC Change
    fig_10y2y_btc.add_trace(
        go.Scatter(
            x=filtered_weekly_df.index,
            y=filtered_weekly_df['btc_change'],
            mode='markers',
            name='BTC Change',
            marker=dict(color='blue'),
            yaxis='y2'
        )
    )
    # Update layout for secondary y-axis
    fig_10y2y_btc.update_layout(
        title='10y2y Change vs BTC Change',
        xaxis_title='Date',
        yaxis_title='10y2y Change',
        yaxis2=dict(
            title='BTC Change',
            overlaying='y',
            side='right'
        )
    )
    st.plotly_chart(fig_10y2y_btc)

