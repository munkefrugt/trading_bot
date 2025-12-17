#helpers/trendline_eval.py
import pandas as pd

def trendline_eval(
    data: pd.DataFrame,
    start_ts: pd.Timestamp,
    end_ts: pd.Timestamp,
    price_col: str = "D_Close_smooth",
    col_mid: str = "trendln_mid",
) -> dict:
    """
    Minimal evaluation:
    Walk through bars and count how many times price crosses the midline.
    """

    seg = data.loc[start_ts:end_ts]
    if seg.empty:
        return {}

    prices = seg[price_col].values
    mids = seg[col_mid].values

    crossings = 0
    i = 0

    # find initial state
    state = None
    while i < len(prices) and state is None:
        if prices[i] > mids[i]:
            state = "above"
        elif prices[i] < mids[i]:
            state = "below"
        i += 1

    # walk through rest and detect flips
    while i < len(prices):
        if state == "above" and prices[i] < mids[i]:
            crossings += 1
            state = "below"
        elif state == "below" and prices[i] > mids[i]:
            crossings += 1
            state = "above"
        i += 1

    return crossings
