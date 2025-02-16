import pandas as pd
from fredapi import Fred
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Fetch FRED API key from environment variables
FRED_API_KEY = os.getenv('FRED_API_KEY')
if not FRED_API_KEY:
    raise ValueError("FRED API key not found in environment variables.")

# Initialize FRED API client
fred = Fred(api_key=FRED_API_KEY)

# Fetch FRED data (weekly)
def fetch_fred_data():
    date_index = pd.to_datetime(fred.get_series('FF').index)
    data = {
        'date': date_index,
        'assets': fred.get_series('WALCL').reindex(date_index),
        'tga': fred.get_series('WTREGEN').reindex(date_index),
        'repo': fred.get_series('RRPONTSYD').reindex(date_index),
        'btc': fred.get_series('CBBTCUSD').reindex(date_index),
        'nasdaq': fred.get_series('NASDAQ100').reindex(date_index),
        'SP500': fred.get_series('SP500').reindex(date_index),
        '10y2y': fred.get_series('T10Y2Y').reindex(date_index)
    }
    return pd.DataFrame(data).set_index('date')

# Fetch FRED data (monthly)
def fetch_monthly_data():
    # First get CPI dates as our reference timeline
    cpi_series = fred.get_series('CPIAUCSL', frequency='m', aggregation_method='eop')
    date_index = pd.to_datetime(cpi_series.index)
    
    data = {
        'date': date_index,
        'cpi': cpi_series,
        'bbk_gdp': fred.get_series('BBKMGDP', frequency='m', aggregation_method='eop').reindex(date_index),
    }
    
    # Fetch asset prices with explicit end-of-month values
    spx = fred.get_series('SP500', frequency='m', aggregation_method='eop')
    ndx = fred.get_series('NASDAQ100', frequency='m', aggregation_method='eop')
    btc = fred.get_series('CBBTCUSD', frequency='m', aggregation_method='eop')
    wei = fred.get_series('WEI', frequency='m', aggregation_method='eop')
    
    # Convert to DataFrame for easier date handling
    assets_df = pd.DataFrame({
        'spx': spx,
        'ndx': ndx,
        'btc': btc,
        'wei': wei
    })
    
    # Reindex asset price data to match CPI dates
    for col in ['spx', 'ndx', 'btc', 'wei']:
        data[col] = assets_df[col].reindex(date_index, method=None)
    
    return pd.DataFrame(data).set_index('date')


# Process FRED data (weekly)
def process_data(df):
    # Forward-fill missing values and resample to weekly frequency
    df.fillna(method='ffill', inplace=True)
    df = df.resample('W').last()

    # Calculate net liquidity and percentage changes
    df['net_liq'] = (df['assets'] - (df['tga'] * 1000 + df['repo'] * 1000)) / 1000
    df['net_liq_change'] = df['net_liq'].pct_change(periods=52)
    df['btc_change'] = df['btc'].pct_change(periods=52)
    df['nasdaq_change'] = df['nasdaq'].pct_change(periods=52)
    df['sp500_change'] = df['SP500'].pct_change(periods=52)
    df['10y2y_change'] = df['10y2y'].diff(periods=52)

    # Calculate rolling correlations
    window_size = 52
    df['corr_netliq_btc'] = df['net_liq_change'].rolling(window=window_size).corr(df['btc_change'])
    df['corr_netliq_nasdaq'] = df['net_liq_change'].rolling(window=window_size).corr(df['nasdaq_change'])
    df['corr_netliq_sp500'] = df['net_liq_change'].rolling(window=window_size).corr(df['sp500_change'])

    # Filter data to start from 2000
    return df[df.index > '2000-01-01']

# Process FRED data (monthly)
def process_monthly_data(df):
    # Forward-fill missing values
    df.fillna(method='ffill', inplace=True)

    # Calculate year-over-year changes for CPI and GDP
    df['cpi_yoy'] = df['cpi'].pct_change(periods=12)*100
    df['cpi_yoy_lagged'] = df['cpi_yoy'].shift(1)
    df['cpi_mom_change'] = df['cpi'].pct_change()
    df['cpi_annualized_mom'] = ((1 + df['cpi_mom_change']) ** 12 - 1) * 100
    df['cpi_annualized_mom_lagged'] = df['cpi_annualized_mom'].shift(1)

    df['wei_mom_change'] = df['wei'].diff()
    df['wei_mom_annualized'] = df['wei_mom_change'] * 12

    df['bbk_gdp_yoy'] = df['bbk_gdp']
    df['bbk_gdp_mom'] = df['bbk_gdp'].diff()
    df['bbk_gdp_yoy_lagged'] = df['bbk_gdp_yoy'].shift(1)

    # Calculate asset returns
    df['spx_return'] = df['spx'].pct_change()
    df['ndx_return'] = df['ndx'].pct_change()
    df['btc_return'] = df['btc'].pct_change()

    # Define market regimes using lagged values
    def classify_regime(row):
        if row['wei'] > 2 and row['cpi_yoy'] <= 2:
            return "Goldilocks"
        elif row['wei'] > 2 and row['cpi_yoy'] > 2:
            return "Inflation"
        elif row['wei'] <= 2 and row['cpi_yoy'] <= 2:
            return "Deflation"
        else:
            return "Stagflation"
        
    # Define market regimes using lagged values
    def classify_regime_V2(row):
        if row['wei_mom_annualized'] > 2 and row['cpi_annualized_mom'] <= 2:
            return "Goldilocks"
        elif row['wei_mom_annualized'] > 2 and row['cpi_annualized_mom'] > 2:
            return "Inflation"
        elif row['wei_mom_annualized'] <= 2 and row['cpi_annualized_mom'] <= 2:
            return "Deflation"
        else:
            return "Stagflation"
        
    # Define market regimes using lagged values
    def classify_regime_V3(row):
        if row['bbk_gdp_yoy_lagged'] > 2 and row['cpi_annualized_mom_lagged'] <= 2:
            return "Goldilocks"
        elif row['bbk_gdp_yoy_lagged'] > 2 and row['cpi_annualized_mom_lagged'] > 2:
            return "Inflation"
        elif row['bbk_gdp_yoy_lagged'] <= 2 and row['cpi_annualized_mom_lagged'] <= 2:
            return "Deflation"
        else:
            return "Stagflation"
        
    # Define market regimes using lagged values
    def classify_regime_V4(row):
        if row['bbk_gdp_yoy'] > 2 and row['cpi_annualized_mom'] <= 2:
            return "Goldilocks"
        elif row['bbk_gdp_yoy'] > 2 and row['cpi_annualized_mom'] > 2:
            return "Inflation"
        elif row['bbk_gdp_yoy'] <= 2 and row['cpi_annualized_mom'] <= 2:
            return "Deflation"
        else:
            return "Stagflation"
    
    # Define market regimes using lagged values
    def classify_regime_V5(row):
        if row['bbk_gdp_mom'] > 0 and row['cpi_mom_change'] <= 0:
            return "Goldilocks"
        elif row['bbk_gdp_mom'] > 0 and row['cpi_mom_change'] > 0:
            return "Inflation"
        elif row['bbk_gdp_mom'] <= 0 and row['cpi_mom_change'] <= 0:
            return "Deflation"
        else:
            return "Stagflation"

    def classify_regime_V6(row):
        if row['wei'] > 2 and row['cpi_annualized_mom'] <= 2:
            return "Goldilocks"
        elif row['wei'] > 2 and row['cpi_annualized_mom'] > 2:
            return "Inflation"
        elif row['wei'] <= 2 and row['cpi_annualized_mom'] <= 2:
            return "Deflation"
        else:
            return "Stagflation"

    # Apply regime classification
    df['market_regime'] = df.apply(classify_regime, axis=1)
    df['market_regime_V2'] = df.apply(classify_regime_V2, axis=1)
    df['market_regime_V3'] = df.apply(classify_regime_V3, axis=1)
    df['market_regime_V4'] = df.apply(classify_regime_V4, axis=1)
    df['market_regime_V5'] = df.apply(classify_regime_V5, axis=1)
    df['market_regime_V6'] = df.apply(classify_regime_V6, axis=1)
    

    # Filter data to start from 2000
    return df[df.index > '2000-01-01']




# Save processed data to CSV
def save_data(df, filename):
    df.to_csv(filename, index=True)

# Main function
if __name__ == "__main__":
    # Process weekly data
    weekly_df = fetch_fred_data()
    weekly_df = process_data(weekly_df)
    save_data(weekly_df, 'fred_weekly.csv')
    print("Weekly data saved to fred_weekly.csv")

    # Process monthly data
    monthly_df = fetch_monthly_data()
    monthly_df = process_monthly_data(monthly_df)
    save_data(monthly_df, 'fred_monthly.csv')
    print("Monthly data saved to fred_monthly.csv")

