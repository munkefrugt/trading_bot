import numpy as np
from signals.trendline_maker.trendline_builder import best_pivot_trendline


def build_pivot_trendlines(y_raw, pivot_lows, pivot_highs):
    """
    Build support + resistance pivot trendlines using pivots from
    weekly_pivot_update.

    Lines are defined in the FULL y_raw index space so they can be
    projected across the entire segment without extra logic elsewhere.

    Returns:
        support_line = (m, b) or None
        resistance_line = (m, b) or None
    """

    n = len(y_raw)
    x_full = np.arange(n)

    support_line = None
    resistance_line = None

    # ----------------------------------------------------------
    # Support from low pivots
    # ----------------------------------------------------------
    if len(pivot_lows) >= 2:
        (
            sup_slope,
            sup_int,
            _,
            _,
            _,
            _,
            _,
            _,
            _,
        ) = best_pivot_trendline(x_full, y_raw, pivot_lows, support=True)

        if sup_slope is not None:
            support_line = (sup_slope, sup_int)

    # ----------------------------------------------------------
    # Resistance from high pivots
    # ----------------------------------------------------------
    if len(pivot_highs) >= 2:
        (
            res_slope,
            res_int,
            _,
            _,
            _,
            _,
            _,
            _,
            _,
        ) = best_pivot_trendline(x_full, y_raw, pivot_highs, support=False)

        if res_slope is not None:
            resistance_line = (res_slope, res_int)

    return support_line, resistance_line
