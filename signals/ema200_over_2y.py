import pandas as pd

def ema200_over_2y(data: pd.DataFrame, i: int) -> bool:
    """
    Fires only on the bar where EMA_200 crosses UP through EMA_2y.
    Returns True exactly on the cross bar; otherwise False.
    """
    if i <= 0 or i >= len(data):
        return False

    prev_ema200 = data["EMA_200"].iloc[i-1]
    prev_ema2y  = data["EMA_2y"].iloc[i-1]
    ema200      = data["EMA_200"].iloc[i]
    ema2y       = data["EMA_2y"].iloc[i]

    crossed_up = (prev_ema200 <= prev_ema2y) and (ema200 > ema2y)
    if crossed_up:
        print(f"✅ EMA200 crossed UP over EMA2y at {data.index[i].date()}")
        return True
    return False
