# helpers/day_to_week.py

import pandas as pd
import config

WEEKDAY_TO_ANCHOR = {
    0: "W-MON",
    1: "W-TUE",
    2: "W-WED",
    3: "W-THU",
    4: "W-FRI",
    5: "W-SAT",
    6: "W-SUN",
}


def _infer_weekly_anchor(weekly_index: pd.DatetimeIndex) -> str:
    if not isinstance(weekly_index, pd.DatetimeIndex):
        raise TypeError("weekly_index must be a DatetimeIndex")

    weekdays = {ts.weekday() for ts in weekly_index[:10]}

    if len(weekdays) != 1:
        raise RuntimeError(
            f"Ambiguous weekly index weekdays={weekdays}. "
            f"Weekly data must have a consistent close day."
        )

    return WEEKDAY_TO_ANCHOR[weekdays.pop()]


def day_to_week(
    daily: pd.DataFrame,
    i: int,
    weekly: pd.DataFrame | None = None,
) -> int | None:
    """
    Map daily row index i to matching weekly row position.

    - weekly defaults to config.weekly_data
    - anchor auto-inferred from weekly index
    - safe for crypto + stocks + any exchange
    """

    if weekly is None:
        weekly = getattr(config, "weekly_data", None)

    if daily is None or weekly is None:
        return None

    anchor = _infer_weekly_anchor(weekly.index)

    d_period = daily.index[i].to_period(anchor)
    w_period = weekly.index.to_period(anchor)

    try:
        return int(w_period.get_loc(d_period))
    except KeyError:
        return None
