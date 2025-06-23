import yfinance as yf
import pandas as pd

def fetch_btc_data(start="2014-01-01", end="2020-01-01", interval="1d"):
    data = yf.download("BTC-USD", start=start, end=end, interval=interval, auto_adjust=False)
    
    # Flatten multi-level column names if needed
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0] for col in data.columns]
    
    return data