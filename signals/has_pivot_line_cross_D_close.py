# signals/has_pivot_line_cross_D_close.py

import pandas as pd


def has_pivot_line_cross_D_close(
    data: pd.DataFrame,
    i: int,
    seq,
    lookback_days: int = 14,
) -> bool:
    """
    Look for a DAILY CLOSE cross above the active pivot / regression
    resistance line within the last `lookback_days`, including today.

    - Start from today and walk backwards
    - The first (most recent) cross found is used
    - Once a candidate exists, do nothing
    """

    # --------------------------------------------------
    # Require an active pivot / regression line
    # --------------------------------------------------
    res_m = seq.helpers.get("pivot_resistance_m")
    res_b = seq.helpers.get("pivot_resistance_b")

    if res_m is None or res_b is None:
        return False

    # Need at least one previous bar to compare against
    if i < 1:
        return False

    # --------------------------------------------------
    # Walk backwards from today, up to lookback_days
    # --------------------------------------------------
    days_checked = 0
    j = i  # current bar

    while j >= 1 and days_checked < lookback_days:
        # Previous and current index positions
        x_prev = data.index.get_loc(data.index[j - 1])
        x_curr = data.index.get_loc(data.index[j])

        # Pivot line values
        prev_res = res_m * x_prev + res_b
        curr_res = res_m * x_curr + res_b

        # Daily closes
        prev_close = data["D_Close"].iloc[j - 1]
        curr_close = data["D_Close"].iloc[j]

        # Check for real close cross
        if prev_close <= prev_res and curr_close > curr_res:
            # seq.helpers["active_pivot_cross_i"] = j
            seq.helpers["active_pivot_cross_time"] = data.index[j]
            seq.helpers["active_pivot_cross_source"] = "recent_window"

            print(
                f"📍 PIVOT CLOSE CROSS | {data.index[j]} | "
                f"D_Close={curr_close:.2f} | "
                f"Res={curr_res:.2f} | "
                f"symbol={seq.symbol} | seq={seq.id}"
            )

            return True

        # Move one day back
        j -= 1
        days_checked += 1

    return False
