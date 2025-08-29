import yfinance as yf
import pandas as pd
from datetime import datetime


"""
Large-Cap Coins (High Liquidity, Lower Volatility)

These will test your algo on more “stable” crypto price action.

    BTC-USD – the “gold standard” for crypto testing.

    ETH-USD – similar market cycles but with different volatility and trend lengths.

    BNB-USD – strong trends but occasional sharp corrections.

Mid-Cap Coins (Trend-Friendly but Choppier)

These will test if your algo survives slightly noisier markets.

    ADA-USD (Cardano) – long consolidations, breakout bursts.

    SOL-USD (Solana) – strong vertical moves, deep pullbacks.

    AVAX-USD – cyclical but smaller community; less smooth charts.

High-Volatility / “Speculative” Coins

Great for stress-testing stop-loss and position sizing logic.

    DOGE-USD – meme volatility; big social media influence.

    SHIB-USD – insane spikes, mostly flat otherwise.

    PEPE-USD (or similar) – extreme pump-and-dump profiles.
"""
start = "2015-01-01"
end = datetime.today().strftime("%Y-%m-%d")

def fetch_btc_data(start=start, end=end, interval="1d"):
    data = yf.download("BTC-USD", start=start, end=end, interval=interval, auto_adjust=False)
    
    # Flatten multi-level column names if needed
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0] for col in data.columns]
    
    return data

def fetch_btc_weekly_data(start=start, end=end):

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
