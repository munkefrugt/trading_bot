import yfinance as yf
import pandas as pd

def fetch_btc_data(start="2014-01-01", end="2020-01-01", interval="1d"):
    data = yf.download("BTC-USD", start=start, end=end, interval=interval, auto_adjust=False)
    
    # Flatten multi-level column names if needed
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0] for col in data.columns]
    
    return data

def fetch_btc_weekly_data(start="2014-01-01", end="2020-01-01"):
    return fetch_btc_data(start=start, end=end, interval="1wk")


def extend_weekly_index(df, extra_periods=26):
    """
    Extend weekly DataFrame index with future periods for forward-shifted indicators (like Ichimoku cloud).
    """
    df_extended = df.copy()
    last_date = df.index[-1]
    freq = '7D'  # fixed to weekly frequency
    start = last_date + pd.Timedelta(days=7)
    new_dates = pd.date_range(start=start, periods=extra_periods, freq=freq)
    extension = pd.DataFrame(index=new_dates)
    return pd.concat([df_extended, extension])
