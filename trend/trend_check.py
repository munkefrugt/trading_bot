# trend_check.py

import pandas as pd
import config
from trend.build_trend_line import find_trend_start_point
from trend.buy_zone import check_buy_zone_and_apply


def trend_check(data, i):
    """Check W_SenB trend conditions and update uptrend states in `data`."""
    current_date = data.index[i]
    prev_uptrend = data['Uptrend'].iloc[i - 1] if i > 0 else False

    # Set sensible defaults for today
    data.at[current_date, 'Uptrend'] = prev_uptrend
    data.at[current_date, 'Trend_Buy_Zone'] = False

    # Bounds
    if not (i + (26 * 7) < len(data) and i - (12 * 7) >= 0):
        return data

    w = config.ichimoku_weekly

    # Only run weekly logic on exact weekly dates
    if current_date in w.index:
        w_pos = w.index.get_loc(current_date)

        # === CASE 1: Buy Zone (offloaded) ===
        data = check_buy_zone_and_apply(data, i, w_pos)

        # === CASE 2: Already in uptrend → DEAD ZONE (kept minimal) ===
        if prev_uptrend:
            w_row = w.iloc[w_pos]
            if (w_row['W_Senkou_span_B_future'] > w_row['W_Senkou_span_A_future']):
                future_index = i + (26 * 7)
                if future_index < len(data):
                    data.at[data.index[future_index], 'W_SenB_Trend_Dead'] = True

                data.at[data.index[i], 'Real_uptrend_end'] = True
                data.at[current_date, 'Uptrend'] = False
                data.at[current_date, 'Trend_Buy_Zone'] = False

                print("📉 End of Buy Zone)")
                data = find_trend_start_point(data, current_index=i)
                data.at[current_date, 'Searching_micro_trendline'] = True

    return data
