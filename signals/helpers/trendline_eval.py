# helpers/trendline_eval.py
import numpy as np
import pandas as pd


def trendline_eval(
    data: pd.DataFrame,
    start_ts: pd.Timestamp,
    end_ts: pd.Timestamp,
    pivot_m: float,
    price_col: str = "D_Close_smooth",
    col_mid: str = "trendln_mid",
    slope_tol: float = 0.35,
):
    """
    Evaluate trend structure on frozen regression channel.

    Returns:
        dict with:
            - crossings
            - reg_slope
            - parallel
    """

    seg = data.loc[start_ts:end_ts]
    if seg.empty or col_mid not in seg:
        return {}

    prices = seg[price_col].values
    mids = seg[col_mid].values
    x = np.arange(len(mids))

    # ---- regression slope from existing midline ----
    valid = ~np.isnan(mids)
    if valid.sum() < 5:
        return {}

    reg_m, _ = np.polyfit(x[valid], mids[valid], 1)

    # ---- midline crossings (chop metric) ----
    crossings = 0
    state = None

    for p, m in zip(prices, mids):
        if np.isnan(m):
            continue

        if state is None:
            state = "above" if p > m else "below"
            continue

        if state == "above" and p < m:
            crossings += 1
            state = "below"
        elif state == "below" and p > m:
            crossings += 1
            state = "above"

    # ---- slope parallelism ----
    parallel = False
    if pivot_m is not None:
        if np.sign(reg_m) == np.sign(pivot_m):
            denom = max(abs(reg_m), abs(pivot_m), 1e-9)
            parallel = abs(reg_m - pivot_m) / denom < slope_tol

    return {
        "crossings": crossings,
        "reg_slope": reg_m,
        "parallel": parallel,
    }
