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

# Fetch FRED data
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

# Process FRED data
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

# Save processed data to CSV
def save_data(df, filename='fred_weekly.csv'):
    df.to_csv(filename, index=True)

# Main function
if __name__ == "__main__":
    df = fetch_fred_data()
    df = process_data(df)
    save_data(df)
    print("Data saved to fred_weekly.csv")
