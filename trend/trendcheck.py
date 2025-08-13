# trend_check.py

import pandas as pd
import config
from trend.w_senb_flat_to_rise import flat_to_rise  # (unused here, keep if you call it elsewhere)
from trend.build_trend_line import find_trend_start_point
from trend.trend_check_line_search import check_macro_trendline, check_micro_trendline


def trend_check(data, i):
    """Check W_SenB trend conditions and update uptrend states in `data`."""

    current_date = data.index[i]
    prev_date = data.index[i - 1] if i > 0 else current_date

    # --- Config ---
    flat_threshold = 0.04
    breakout_pct = 0.01
    sen_a_buffer = 0.01

    prev_uptrend = data['Uptrend'].iloc[i - 1] if i > 0 else False

    # Daily cloud context for confirmation
    price_above_or_inside_D_cloud = (
        (
            data['D_Close'].iloc[i - 1] >= data['D_Senkou_span_B'].iloc[i - 1] or
            data['D_Close'].iloc[i - 1] >= data['D_Senkou_span_A'].iloc[i - 1]
        ) and
        (
            data['D_Close'].iloc[i] >= data['D_Senkou_span_B'].iloc[i] or
            data['D_Close'].iloc[i] >= data['D_Senkou_span_A'].iloc[i]
        )
    )

    # Keep your line tracking up-to-date every day
    check_micro_trendline(data, i, prev_date, current_date, price_above_or_inside_D_cloud)
    check_macro_trendline(data, i, prev_date, current_date)

    # Bounds for any future-index writes / lookbacks
    if not (i + (26 * 7) < len(data) and i - (12 * 7) >= 0):
        data.at[current_date, 'Uptrend'] = prev_uptrend
        return data

    # --- Weekly DF with future spans ---
    w = config.ichimoku_weekly
    if ('W_Senkou_span_B_future' not in w.columns) or ('W_Senkou_span_A_future' not in w.columns):
        if ('W_Senkou_span_B' not in w.columns) or ('W_Senkou_span_A' not in w.columns):
            data.at[current_date, 'Uptrend'] = prev_uptrend
            return data
        w = w.copy()
        w['W_Senkou_span_A_future'] = w['W_Senkou_span_A'].shift(-26)  # 26 weeks ahead
        w['W_Senkou_span_B_future'] = w['W_Senkou_span_B'].shift(-26)
        config.ichimoku_weekly = w

    # Only run weekly logic on exact weekly dates
    if current_date not in w.index:
        data.at[current_date, 'Uptrend'] = prev_uptrend
        return data

    p = w.index.get_loc(current_date)
    if isinstance(p, slice):
        # if duplicate labels, use the last occurrence
        p = list(range(p.start, p.stop, p.step or 1))[-1]
    elif isinstance(p, (list, tuple)):
        p = p[-1]

    if p == 0:
        data.at[current_date, 'Uptrend'] = prev_uptrend
        return data

    # Weekly (future-shifted) values
    w_senA_future = w['W_Senkou_span_A_future'].iloc[p]
    w_senB_future = w['W_Senkou_span_B_future'].iloc[p]
    w_senA_future_prev = w['W_Senkou_span_A_future'].iloc[p - 1]
    w_senB_future_prev = w['W_Senkou_span_B_future'].iloc[p - 1]

    # Gate: require SenB_future to rise WoW
    if not pd.notna(w_senB_future) or not pd.notna(w_senB_future_prev) or not (w_senB_future > w_senB_future_prev + 1e-9):
        data.at[current_date, 'Uptrend'] = prev_uptrend
        return data

    # Flat base over past 12 weeks (exclude current week)
    lookback_w = 12
    if p - lookback_w < 0:
        data.at[current_date, 'Uptrend'] = prev_uptrend
        return data
    w_senB_past = w['W_Senkou_span_B_future'].iloc[p - lookback_w: p]
    flat_base_avg = w_senB_past.mean()
    if not pd.notna(flat_base_avg) or flat_base_avg == 0:
        data.at[current_date, 'Uptrend'] = prev_uptrend
        return data
    senb_flat_range = (w_senB_past.max() - w_senB_past.min()) / flat_base_avg

    # Week-ago values (already have prev)
    w_senA_week_ago = w_senA_future_prev
    w_senB_week_ago = w_senB_future_prev

    # === CASE 1: Not in uptrend → BUY ZONE ===
    if not prev_uptrend:
        sen_a_confirm = w_senA_future > w_senB_future * (1 + sen_a_buffer)

        if (
            senb_flat_range < flat_threshold and
            w_senB_future > flat_base_avg * (1 + breakout_pct) and
            w_senA_future > w_senA_week_ago and
            w_senB_future > w_senB_week_ago and
            sen_a_confirm and
            price_above_or_inside_D_cloud
        ):
            future_index = i + (26 * 7)
            if future_index < len(data):
                data.at[data.index[future_index], 'W_SenB_Future_flat_to_up_point'] = True

            data.at[data.index[i], 'Real_uptrend_start'] = True
            data.at[current_date, 'Uptrend'] = True
            data.at[current_date, 'Trend_Buy_Zone'] = True

            # Make sure your executor sees a buy:
            data.at[current_date, 'Buy_Signal'] = True
            data.at[current_date, 'Signal'] = 'BUY'
            data.at[current_date, 'Entry_Price'] = data['D_Close'].iloc[i]

            print(f"📈 Entering Buy Zone: {current_date} (W_SenA confirmed & price in/above D cloud)")
        else:
            data.at[current_date, 'Uptrend'] = prev_uptrend

    # === CASE 2: Already in uptrend → DEAD ZONE ===
    else:
        lookback_w_death = 4
        start = max(0, p - lookback_w_death)
        senb_4w = w['W_Senkou_span_B_future'].iloc[start: p + 1]  # include current week
        mean4 = senb_4w.mean()
        future_trend_down = w_senB_future < w_senB_future_prev
        future_trend_flat = (mean4 is not None and mean4 != 0) and ((senb_4w.max() - senb_4w.min()) / mean4 < 0.005)

        # Daily EMA/cloud checks (use 4 weeks ~ 28 daily rows)
        ema50_past = data['EMA_50'].iloc[i - 4 * 7] if i - 4 * 7 >= 0 else data['EMA_50'].iloc[0]
        ema50_now = data['EMA_50'].iloc[i]
        ema_decline = ema50_past > ema50_now

        price_below_cloud = (
            data['D_Close'].iloc[i - 1] < data['D_Senkou_span_A'].iloc[i - 1] and
            data['D_Close'].iloc[i - 1] < data['D_Senkou_span_B'].iloc[i - 1] and
            data['D_Close'].iloc[i] < data['D_Senkou_span_A'].iloc[i] and
            data['D_Close'].iloc[i] < data['D_Senkou_span_B'].iloc[i]
        )

        if (future_trend_down or future_trend_flat) and ema_decline and price_below_cloud:
            future_index = i + (26 * 7)
            if future_index < len(data):
                data.at[data.index[future_index], 'W_SenB_Trend_Dead'] = True

            data.at[data.index[i], 'Real_uptrend_end'] = True
            data.at[current_date, 'Uptrend'] = False
            data.at[current_date, 'Trend_Buy_Zone'] = False

            print("📉 Entering Dead Zone)")
            data = find_trend_start_point(data, current_index=i)
            data.at[current_date, 'Searching_micro_trendline'] = True
        else:
            data.at[current_date, 'Uptrend'] = prev_uptrend

    return data
