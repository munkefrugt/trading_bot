# signals/find_pivotline_cross.py

import pandas as pd


def find_pivotline_cross(
    data: pd.DataFrame,
    i: int,
    seq,
    lookback_days: int = 14,
) -> bool:
    """
    Detect whether DAILY CLOSE crossed ABOVE an EXISTING
    pivot resistance line within the last `lookback_days`.

    BASELINE DEBUG VERSION:
    - pivot-local x
    - close-based cross
    - minimal guards
    """
    # --------------------------------------------------
    # 1) Require pivot resistance
    # --------------------------------------------------
    res_m = seq.helpers.get("pivot_resistance_m")
    res_b = seq.helpers.get("pivot_resistance_b")
    pivot_start_ts = seq.helpers.get("pivot_start_ts")

    if res_m is None or res_b is None or pivot_start_ts not in data.index:
        return False

    pivot_start_i = data.index.get_loc(pivot_start_ts)

    # --------------------------------------------------
    # 2) Look back for DAILY CLOSE cross
    # --------------------------------------------------
    j = i
    days_checked = 0

    while j >= 1 and days_checked < lookback_days:

        x_prev = (j - 1) - pivot_start_i
        x_curr = j - pivot_start_i

        prev_res = res_m * x_prev + res_b
        curr_res = res_m * x_curr + res_b

        prev_close = data["D_Close"].iloc[j - 1]
        curr_close = data["D_Close"].iloc[j]

        if prev_close <= prev_res and curr_close > curr_res:

            #     print("------ PIVOT CROSS DEBUG ------")
            #     print(f"symbol        : {seq.symbol}")
            #     print(f"seq id        : {seq.id}")
            #     print(f"event date   : {data.index[j].date()}")
            #     print(f"prev close   : {prev_close:.2f}")
            #     print(f"prev pivot y : {prev_res:.2f}")
            #     print(f"curr close   : {curr_close:.2f}")
            #     print(f"curr pivot y : {curr_res:.2f}")
            #     print("--------------------------------")

            seq.helpers["pivot_break_ts"] = data.index[j]
            seq.helpers["pivot_break_val"] = curr_close

            # print(
            #     f"📍 PIVOT CLOSE CROSS at {data.index[j].date()} | "
            #     f"symbol={seq.symbol} | seq={seq.id}"
            # )

            return True

        j -= 1
        days_checked += 1

    return False
