# trend_check.py

import pandas as pd
import config
from trend.w_senb_flat_to_rise import flat_to_rise  # (unused here, keep if you call it elsewhere)
from trend.build_trend_line import find_trend_start_point
from trend.trend_check_line_search import check_macro_trendline, check_micro_trendline
from trend.senb_consolidation import mark_consolidation_zone
from trend.macro_trendline import build_macro_trendline_from_last_X
from trend.regression_line import build_regression_from_last_adjusted_start
from trend.flatness import calc_flatness_from_last_adjusted_start
from trend.bb_squeeze import check_bb_squeeze
from trend.count_cross_regline import count_regline_crosses_consolidation
from trend.causal_slope import trailing_poly_gate_with_stamp


def trend_check(data, i):
    """Check W_SenB trend conditions and update uptrend states in `data`."""

    current_date = data.index[i]
    prev_date = data.index[i - 1] if i > 0 else current_date

    # --- Config ---
    flat_threshold = 0.04
    breakout_pct = 0.01
    sen_a_buffer = 0.01
    # NEW: max allowed extension above weekly cloud top
    cloud_max_ext_pct = getattr(config, "CLOUD_MAX_EXT_PCT", 0.15)

    prev_uptrend = data['Uptrend'].iloc[i - 1] if i > 0 else False

    # Keep your line tracking up-to-date every day
    # check_micro_trendline(data, i, prev_date, current_date)
    # check_macro_trendline(data, i, prev_date, current_date)

    # Bounds for any future-index writes / lookbacks
    if not (i + (26 * 7) < len(data) and i - (12 * 7) >= 0):
        data.at[current_date, 'Uptrend'] = prev_uptrend
        return data

    # --- Weekly DF with future spans ---
    w = config.ichimoku_weekly

    # Only run weekly logic on exact weekly dates
    if current_date in w.index:

        w_pos = w.index.get_loc(current_date)
        D_close = data['D_Close'].iloc[i]  # Daily close price
        Ema_200 = data['EMA_200'].iloc[i]  # Daily EMA 200
        w_senA = w['W_Senkou_span_A'].iloc[w_pos]
        w_senB = w['W_Senkou_span_B'].iloc[w_pos]

        w_senA_future = w['W_Senkou_span_A_future'].iloc[w_pos]
        w_senB_future = w['W_Senkou_span_B_future'].iloc[w_pos]
        w_senA_future_prev = w['W_Senkou_span_A_future'].iloc[w_pos - 1]
        w_senB_future_prev = w['W_Senkou_span_B_future'].iloc[w_pos - 1]

        # Flat base over past 12 weeks (exclude current week)
        lookback_w = 8
        if w_pos - lookback_w < 0:
            data.at[current_date, 'Uptrend'] = prev_uptrend
            return data

        w_senB_past = w['W_Senkou_span_B_future'].iloc[w_pos - lookback_w: w_pos]

        flat_base_avg = w_senB_past.mean()
        if not pd.notna(flat_base_avg) or flat_base_avg == 0:
            data.at[current_date, 'Uptrend'] = prev_uptrend
            return data
        senb_flat_range = (w_senB_past.max() - w_senB_past.min()) / flat_base_avg

        # Weekly Heikin-Ashi trend check
        w_ha = getattr(config, "weekly_data_HA", None)
        if w_ha is not None and w_pos < len(w_ha):
            positive_w_ha = (
                w_ha["W_HA_Open"].iloc[w_pos] < w_ha["W_HA_Close"].iloc[w_pos]
            )
        else:
            positive_w_ha = False

        # === CASE 1: Not in uptrend → BUY ZONE ===
        if (w_senB_future > w_senB_future_prev):

            # NEW: only cap how far above the weekly cloud top price is
            w_cloud_top = max(w_senA, w_senB)
            if w_cloud_top and w_cloud_top > 0:
                rel_dist_to_top = (D_close - w_cloud_top) / w_cloud_top
                print("rel_dist_to_top")
                print(rel_dist_to_top)
            else:
                rel_dist_to_top = float("inf")
            relative_close_to_w_cloud = (rel_dist_to_top <= cloud_max_ext_pct)

            sen_a_confirm = w_senA_future > w_senB_future * (1 + sen_a_buffer)
            slope_EMA_365_flat = abs(data['EMA_365_slope_%'].iloc[i]) < 7
            # all gates EXCEPT slope (used to decide stamping and final gate)
            zone_ok_wo_slope = (
                D_close > w_senA and
                D_close > w_senB and
                D_close > Ema_200 and
                senb_flat_range < flat_threshold and
                w_senB_future > flat_base_avg * (1 + breakout_pct) and
                w_senA_future > w_senA_future_prev and
                w_senB_future > w_senB_future_prev and
                sen_a_confirm and
                # relative_close_to_w_cloud
                slope_EMA_365_flat
            )

            # ONE call: compute slope, write plot cols, and stamp last N weeks behind this bar when other gates pass
            sen_b_slope_ok = trailing_poly_gate_with_stamp(
                w, w_pos, current_date,
                col="W_Senkou_span_B_future",
                window=9,
                degree=2,
                threshold_pct=1.0,              # >= 1%/week
                fit_col="W_SenB_trailing_poly",
                slope_col="W_SenB_trailing_slope_pct",
                stamp_if=zone_ok_wo_slope,      # stamp only when other gates pass (your “star”)
                stamp_bars=4,                   # ~1 month of weekly bars
                only_fill_nans=True             # keep earlier stamped segments
            )

            # final zone gate
            if zone_ok_wo_slope and sen_b_slope_ok:
                future_index = i + (26 * 7)
                if future_index < len(data):
                    future_date = data.index[future_index]
                    data.at[data.index[future_index], 'W_SenB_Future_flat_to_up_point'] = True

                data.at[data.index[i], 'Real_uptrend_start'] = True
                data.at[current_date, 'Uptrend'] = True
                data.at[current_date, 'Trend_Buy_Zone'] = True
                print(f"📈 Entering Buy Zone: {current_date} (W_SenA confirmed & price in/above D cloud)")

                data = mark_consolidation_zone(
                    data,
                    current_date=future_date,
                )

                data, r_2 = build_regression_from_last_adjusted_start(
                    data,
                    current_index=i,
                    out_col="Regline_from_last_adjusted",
                    flag_col="W_SenB_Consol_Start_Price_Adjusted",
                    min_points=5,
                )
                print(r_2)

                flatness = calc_flatness_from_last_adjusted_start(
                    data,
                    current_index=i,
                    y_col="D_Close",
                    flag_col="W_SenB_Consol_Start_Price_Adjusted",
                    min_points=5,
                )
                if flatness is not None:
                    data.loc[current_date, "Flatness_ratio"] = flatness
                    print("Flatness:", flatness)

                crosses = count_regline_crosses_consolidation(
                    data,
                    price_col="EMA_50",
                    line_col="Regline_from_last_adjusted",
                    flag_col="W_SenB_Consol_Start_Price_Adjusted",
                    end_index=i,
                )
                data.at[current_date, "regline_crosses"] = float(crosses)
                data.at[current_date, "regline_aproved"] = bool((crosses > 2) or (r_2 is not None and r_2 > 0.9))

        else:
            data.at[current_date, 'Uptrend'] = prev_uptrend

        # === CASE 2: Already in uptrend → DEAD ZONE ===
        if prev_uptrend:
            lookback_w_death = 4
            start = max(0, w_pos - lookback_w_death)
            senb_4w = w['W_Senkou_span_B_future'].iloc[start: w_pos + 1]  # include current week
            mean4 = senb_4w.mean()
            future_trend_down = w_senB_future < w_senB_future_prev
            future_trend_flat = (mean4 is not None and mean4 != 0) and ((senb_4w.max() - senb_4w.min()) / mean4 < 0.005)

            # Daily EMA/cloud checks (use 4 weeks ~ 28 daily rows)
            ema50_past = data['EMA_50'].iloc[i - 4 * 7] if i - 4 * 7 >= 0 else data['EMA_50'].iloc[0]
            ema50_now = data['EMA_50'].iloc[i]
            ema50_decline = ema50_past > ema50_now

            price_below_cloud = (
                data['D_Close'].iloc[i - 1] < data['D_Senkou_span_A'].iloc[i - 1] and
                data['D_Close'].iloc[i - 1] < data['D_Senkou_span_B'].iloc[i - 1] and
                data['D_Close'].iloc[i] < data['D_Senkou_span_A'].iloc[i] and
                data['D_Close'].iloc[i] < data['D_Senkou_span_B'].iloc[i]
            )

            # if Weekly HA candles has been going down for 2 candles, then we are in a dead zone
            W_HA = config.weekly_data_HA

            # zone conditions:
            if (
                # past_2_HA_candles_down
                w_senB_future > w_senA_future
                # (future_trend_down or future_trend_flat) and
                # ema50_decline # and
                # price_below_cloud
            ):
                future_index = i + (26 * 7)
                if future_index < len(data):
                    data.at[data.index[future_index], 'W_SenB_Trend_Dead'] = True

                data.at[data.index[i], 'Real_uptrend_end'] = True
                data.at[current_date, 'Uptrend'] = False
                data.at[current_date, 'Trend_Buy_Zone'] = False

                print("📉 End of Buy Zone)")
                data = find_trend_start_point(data, current_index=i)
                data.at[current_date, 'Searching_micro_trendline'] = True
            else:
                data.at[current_date, 'Uptrend'] = prev_uptrend
    else:
        data.at[current_date, 'Uptrend'] = prev_uptrend
    return data
