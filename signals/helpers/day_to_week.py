# helpers/day_to_week.py
import pandas as pd
import config

WEEKLY_ANCHOR = getattr(config, "WEEKLY_ANCHOR", "W-SUN")

def day_to_week(data: pd.DataFrame, i: int, weekly: pd.DataFrame = None, anchor: str = WEEKLY_ANCHOR) -> int | None:
    """
    Map a daily row index i to the matching weekly row position.
    Returns the integer weekly position, or None if not found.

    - data: daily DF (DateTimeIndex)
    - i: daily row integer index
    - weekly: weekly DF (DateTimeIndex). Defaults to config.ichimoku_weekly
    - anchor: pandas weekly anchor like "W-SUN" (BTC), "W-MON", etc.
    """
    if weekly is None:
        weekly = getattr(config, "ichimoku_weekly", None)
        if weekly is None:
            return None

    d_week = data.index[i].to_period(anchor)
    w_period = weekly.index.to_period(anchor)

    try:
        return int(w_period.get_loc(d_week))
    except KeyError:
        return None
