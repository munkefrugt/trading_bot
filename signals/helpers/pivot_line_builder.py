# signals/helpers/pivot_line_builder.py

import numpy as np
from signals.trendline_maker.trendline_builder import best_pivot_trendline


def build_pivot_trendlines(y_raw, pivot_lows, pivot_highs):
    """
    Build support + resistance pivot trendlines using the pivots from
    weekly_pivot_update, wrapped cleanly around best_pivot_trendline.

    Returns:
        support_line = (m, b) or None
        resistance_line = (m, b) or None
    """

    x = np.arange(len(y_raw))

    # --- Support from low pivots ---
    (
        sup_slope,
        sup_int,
        sup_A,
        sup_B,
        _,
        _,
        _,
        _,
        _,
    ) = best_pivot_trendline(x, y_raw, pivot_lows, support=True)

    # --- Resistance from high pivots ---
    (
        res_slope,
        res_int,
        res_A,
        res_B,
        _,
        _,
        _,
        _,
        _,
    ) = best_pivot_trendline(x, y_raw, pivot_highs, support=False)

    support_line = (sup_slope, sup_int) if sup_slope is not None else None
    resistance_line = (res_slope, res_int) if res_slope is not None else None

    return support_line, resistance_line
