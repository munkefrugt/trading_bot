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

    # Keep your line tracking up-to-date every day
    #check_micro_trendline(data, i, prev_date, current_date)
    #check_macro_trendline(data, i, prev_date, current_date)

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

        # Gate: require SenB_future to rise 
        # if not pd.notna(w_senB_future) or not pd.notna(w_senB_future_prev) or not (w_senB_future > w_senB_future_prev + 1e-9):
        #     data.at[current_date, 'Uptrend'] = prev_uptrend
        #     return data

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
        if (not prev_uptrend and w_senB_future > w_senB_future_prev):

                sen_a_confirm = w_senA_future > w_senB_future * (1 + sen_a_buffer)
                # zone conditions
                if (
                    #price_above week cloud
                    D_close > w_senA and
                    D_close > w_senB and
                    D_close > Ema_200 and
                    senb_flat_range < flat_threshold and
                    w_senB_future > flat_base_avg * (1 + breakout_pct) and
                    w_senA_future > w_senA_future_prev and
                    w_senB_future > w_senB_future_prev and
                    sen_a_confirm #and
                    #price_above_or_inside_D_cloud
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

            #if Weekly HA candels has been going down for 2 candels, then we are in a dead zone
            W_HA = config.weekly_data_HA


            
            # zone conditions:
            if (
            #past_2_HA_candles_down
            w_senB_future > w_senA_future
            #(future_trend_down or future_trend_flat) and
            #ema50_decline #and 
            #price_below_cloud
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

