# get_data.py

import yfinance as yf
import pandas as pd
from datetime import datetime
import config

# YYYY-MM-DD
start = "2015-01-01"
# end = "2023-11-05"  # (debug cross)
# end = "2023-06-21"

end = datetime.today().strftime("%Y-%m-%d")


def fetch_btc_data(start=start, end=end, interval="1d"):
    """
    Fetch DAILY data only.
    This is the single source of truth.
    """
    symbol = "BTC-USD"

    data = yf.download(
        symbol,
        start=start,
        end=end,
        interval=interval,
        auto_adjust=False,
    )

    # Flatten multi-level column names if needed
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0] for col in data.columns]

    return data


def fetch_btc_weekly_data(anchor="W-THU", min_days=6):
    """
    FAIL-SAFE weekly data builder.

    This function NO LONGER downloads weekly data.
    It derives weekly data from config.daily_data ONLY.

    If daily data is missing → crash loudly.
    """

    daily = getattr(config, "daily_data", None)

    if daily is None:
        raise RuntimeError(
            "fetch_btc_weekly_data() called before daily data exists.\n"
            "Weekly data MUST be derived from daily data to avoid lookahead."
        )

    weekly = daily.resample(anchor).agg(
        W_Open=("Open", "first"),
        W_High=("High", "max"),
        W_Low=("Low", "min"),
        W_Close=("Close", "last"),
        W_Volume=("Volume", "sum"),
        W_Count=("Close", "count"),
    )

    # 🔒 HARD RULE: drop partial weeks
    weekly = weekly[weekly["W_Count"] >= min_days]

    return weekly


def extend_weekly_index(df, extra_periods=26):
    """
    Extend weekly DataFrame index with future periods
    for forward-shifted indicators (e.g. Ichimoku cloud).
    """
    df_extended = df.copy()
    last_date = df.index[-1]

    start = last_date + pd.Timedelta(days=7)
    new_dates = pd.date_range(start=start, periods=extra_periods, freq="7D")

    extension = pd.DataFrame(index=new_dates)
    return pd.concat([df_extended, extension])
