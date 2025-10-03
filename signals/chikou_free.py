# signals/chikou_free.py
import pandas as pd

def chikou_free(data: pd.DataFrame, i: int) -> bool:
    """
    Chikou free (calendar version):
    - Origin = 26 calendar weeks before current bar.
    - Mark origin for plotting.
    - If ANY close between origin and current close > current close → blocked.
    - Else → free.
    """
    if i <= 0 or i >= len(data) or "D_Close" not in data.columns:
        return False

    # 1) figure out 26 weeks earlier
    current_ts = data.index[i]
    origin_ts = current_ts - pd.Timedelta(weeks=26)

    # 2) snap to nearest available bar ≤ origin_ts
    origin_loc = data.index.get_indexer([origin_ts], method="pad")[0]
    if origin_loc < 0:
        return False

    # for plotting
    data.at[data.index[origin_loc], "chikou_free_check_origin"] = True

    # 3) compare closes between origin and current
    close_now = data.at[data.index[i], "D_Close"]
    segment = data["D_Close"].iloc[origin_loc+1:i]

    if (segment > close_now).any():
        return False
    return True
