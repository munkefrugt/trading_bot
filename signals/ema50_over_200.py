#signals/ema50_over_200.py
import pandas as pd

def ema50_over_200(data: pd.DataFrame, i: int) -> bool:
    """
    Fires only on the bar where EMA_50 crosses UP through EMA_200.
    Returns True exactly on the cross bar; otherwise False.
    """
    if i <= 0 or i >= len(data):
        return False

    prev_ema50  = data["EMA_50"].iloc[i-1]
    prev_ema200 = data["EMA_200"].iloc[i-1]
    ema50       = data["EMA_50"].iloc[i]
    ema200      = data["EMA_200"].iloc[i]

    crossed_up = (prev_ema50 <= prev_ema200) and (ema50 > ema200)
    if crossed_up:
        print(f"✅ EMA50 crossed UP over EMA200 at {data.index[i].date()}")
        return True
    return False
