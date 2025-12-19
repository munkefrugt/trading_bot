# signals/helpers/trend_regression.py
import numpy as np
from types import SimpleNamespace


def find_trend_regression(
    data,
    start_ts,
    end_ts,
    price_col: str = "D_Close",
    upper_q: float = 0.90,
    lower_q: float = 0.10,
):
    """
    Pure regression finder over a fixed time window.

    Inputs:
        - data: DataFrame
        - start_ts, end_ts: index timestamps
        - price_col: column to regress on

    Returns:
        SimpleNamespace with regression parameters
        or None if window is too small.
    """

    y = data.loc[start_ts:end_ts, price_col].values
    if len(y) < 2:
        return None

    x = np.arange(len(y))

    m, b = np.polyfit(x, y, 1)
    mid = m * x + b
    resid = y - mid

    return SimpleNamespace(
        m=m,
        b=b,
        up_offset=np.nanquantile(resid, upper_q),
        low_offset=np.nanquantile(resid, lower_q),
        r2_offset=np.nanquantile(resid, 0.975),
        breakout_offset=np.nanmax(resid),
        breakdown_offset=np.nanmin(resid),
        start_ts=start_ts,
        end_ts=end_ts,
    )
