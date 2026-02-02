# get_data.py

import yfinance as yf
import pandas as pd
from datetime import datetime
import config

"""
stocks
"AAPL"
"TSLA"
"NVDA"
"AMD"
"MSFT"
"AMZN"
"META"
"GOOGL"
"NFLX"
"AVGO"
"BRK-B"

crypto
"BTC-USD"
"ETH-USD"
"SOL-USD"
"LINK-USD"
"XRP-USD"
"ADA-USD"
"LTC-USD"
"""
# =========================
# Date range
# =========================
START_DATE = "2000-01-01"
END_DATE = datetime.today().strftime("%Y-%m-%d")


# =========================
# Daily data (single source of truth)
# =========================
def fetch_daily_data(start=START_DATE, end=END_DATE, interval="1d"):
    # symbol = "AAPL"
    # symbol = "BRK-B"
    # symbol = "BTC-USD"
    # symbol = "ADA-USD"
    # symbol = "LINK-USD" (good swingtrader)

    # symbol = "GLD"  # gold ETF (to many sequences running)
    # symbol = "BTC-USD"
    # symbol = "GOOGL"
    # symbol = "BRK-B"
    # symbol = "LINK-USD"  # (good swingtrader)
    # symbol = "ADA-USD"  # (100 winrate 1 good trade)
    # symbol = "SOL-USD"
    # symbol = "XRP-USD"
    symbol = "BTC-USD"
    # symbol = "XRP-USD"

    """
    Fetch DAILY data only.
    This is the single source of truth for all higher timeframes.
    """
    data = yf.download(
        symbol,
        start=start,
        end=end,
        interval=interval,
        auto_adjust=False,
        progress=True,
    )

    if data.empty:
        raise RuntimeError(f"No daily data returned for symbol: {symbol}")

    # Flatten multi-index columns if present
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0] for col in data.columns]

    return data


# =========================
# Weekly data (derived from daily)
# =========================
def fetch_weekly_data_from_daily(anchor="W-THU", min_days=5):
    """
    FAIL-SAFE weekly data builder.

    - Never downloads weekly data
    - Always derives from config.daily_data
    - Drops clearly partial weeks
    """

    daily = getattr(config, "daily_data", None)

    if daily is None or daily.empty:
        raise RuntimeError(
            "Weekly data requested before daily data exists.\n"
            "Daily data must be fetched first."
        )

    weekly = daily.resample(anchor).agg(
        W_Open=("Open", "first"),
        W_High=("High", "max"),
        W_Low=("Low", "min"),
        W_Close=("Close", "last"),
        W_Volume=("Volume", "sum"),
        W_Count=("Close", "count"),
    )

    # Drop partial / broken weeks
    weekly = weekly[weekly["W_Count"] >= min_days]

    if weekly.empty:
        raise RuntimeError(
            "Weekly data is empty after resampling.\n"
            "Try lowering min_days or check daily data continuity."
        )

    return weekly


# =========================
# Weekly index extension (Ichimoku-safe)
# =========================
def extend_weekly_index(df, extra_periods=26):
    """
    Extend weekly index forward so forward-shifted indicators
    (e.g. Ichimoku Senkou spans) have space to live.
    """

    if df.empty:
        return df

    df_extended = df.copy()
    last_date = df_extended.index[-1]

    start = last_date + pd.Timedelta(days=7)
    future_index = pd.date_range(start=start, periods=extra_periods, freq="7D")

    extension = pd.DataFrame(index=future_index)

    return pd.concat([df_extended, extension])
