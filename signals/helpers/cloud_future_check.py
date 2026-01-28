# signals/helpers/future_check.py
from .day_to_week import day_to_week
import config


def future_week_sena_above_senb(data, i):
    weekly = config.ichimoku_weekly
    """
    Returns True if future weekly Senkou Span A > Senkou Span B.
    """
    w_i = day_to_week(data, i, weekly)
    if w_i is None:
        return False
    return (
        weekly["W_Senkou_span_A_future"].iloc[w_i]
        > weekly["W_Senkou_span_B_future"].iloc[w_i]
    )


def future_week_sena_below_senb(data, i):
    w_i = day_to_week(data, i, config.ichimoku_weekly)
    if w_i is None:
        return False
    return (
        config.ichimoku_weekly["W_Senkou_span_A_future"].iloc[w_i]
        < config.ichimoku_weekly["W_Senkou_span_B_future"].iloc[w_i]
    )
