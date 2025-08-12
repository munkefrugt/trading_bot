
from trend.build_trend_line import find_trend_start_point
from trend.trend_check_line_search import check_macro_trendline, check_micro_trendline
def trend_check(data, i):
    """Check W_SenB trend conditions and update uptrend states in `data`."""

    current_date = data.index[i]
    prev_date = data.index[i-1]

    # === Configuration ===
    flat_threshold = 0.04
    breakout_pct = 0.01
    sen_a_buffer = 0.01  # Require W_SenA to be at least 1% above W_SenB

    # === Check if we were previously in an uptrend ===
    prev_uptrend = data['Uptrend'].iloc[i - 1] if i > 0 else False

    price_above_or_inside_cloud = (
        (
            data['D_Close'].iloc[i - 1] >= data['D_Senkou_span_B'].iloc[i - 1] or
            data['D_Close'].iloc[i - 1] >= data['D_Senkou_span_A'].iloc[i - 1]
        ) and
        (
            data['D_Close'].iloc[i] >= data['D_Senkou_span_B'].iloc[i] or
            data['D_Close'].iloc[i] >= data['D_Senkou_span_A'].iloc[i]
        )
    )
    check_micro_trendline(data, i, prev_date, current_date,price_above_or_inside_cloud)
    check_macro_trendline(data, i, prev_date, current_date)
       
    # === Check for buy zone ===
    if i + (26 * 7) < len(data) and i - (12 * 7) >= 0:
        # Future Senkou lines (shifted -26 weeks)
        senb_future = data['W_Senkou_span_B'].shift(-26 * 7)
        sena_future = data['W_Senkou_span_A'].shift(-26 * 7)

        # Flat base check in the past (before now)
        senb_past = senb_future.iloc[i - (12 * 7):i]
        flat_base_avg = senb_past.mean()
        senb_flat_range = (senb_past.max() - senb_past.min()) / flat_base_avg

        # Current values
        senb_now = senb_future.iloc[i]
        senb_prev = senb_future.iloc[i - 7]
        sena_now = sena_future.iloc[i]
        
# ===============================================================================
        # === CASE 1: Not in uptrend → Look for BUY ZONE ===
        if not prev_uptrend:
            sen_a_confirm = sena_now > senb_now * (1 + sen_a_buffer)


            # Buy Zone conditions:
            if (
                senb_flat_range < flat_threshold and
                senb_now > flat_base_avg * (1 + breakout_pct) and
                sen_a_confirm and
                price_above_or_inside_cloud
             ):
                future_index = i + (26 * 7)
                data.at[data.index[future_index], 'W_SenB_Future_flat_to_up_point'] = True
                data.at[data.index[i], 'Real_uptrend_start'] = True
                data.at[current_date, 'Uptrend'] = True
                data.at[current_date, 'Trend_Buy_Zone'] = True

                print(f"📈 Entering Buy Zone: {current_date} (W_SenA confirmed & price in/above D cloud)")
                #start search for macro trendline

                # make last check did we break out of macro or micro? 
                print
            else:
                data.at[current_date, 'Uptrend'] = prev_uptrend

        # === CASE 2: Already in uptrend → Look for DEAD ZONE ===
        else:
            if i - (4 * 7) >= 0:
                lookback = 4 * 7

                senb_4w = senb_future.iloc[i - lookback:i]
                future_trend_down = senb_now < senb_prev
                future_trend_flat = (
                    (senb_4w.max() - senb_4w.min()) / senb_4w.mean()
                ) < 0.005

                ema50_past = data['EMA_50'].iloc[i - lookback]
                ema50_now = data['EMA_50'].iloc[i]
                ema_decline = ema50_past > ema50_now

                price_below_cloud = (
                    data['D_Close'].iloc[i - 1] < data['D_Senkou_span_A'].iloc[i - 1] and
                    data['D_Close'].iloc[i - 1] < data['D_Senkou_span_B'].iloc[i - 1] and
                    data['D_Close'].iloc[i] < data['D_Senkou_span_A'].iloc[i] and
                    data['D_Close'].iloc[i] < data['D_Senkou_span_B'].iloc[i]
                )

                if (
                    (future_trend_down or future_trend_flat) and
                    ema_decline and
                    price_below_cloud
                ):
                    future_index = i + (26 * 7)
                    data.at[data.index[future_index], 'W_SenB_Trend_Dead'] = True
                    data.at[data.index[i], 'Real_uptrend_end'] = True
                    data.at[current_date, 'Uptrend'] = False
                    data.at[current_date, 'Trend_Buy_Zone'] = False

                    # Call start point finder
                    print(f"📉 Entering Dead Zone)")
                    data = find_trend_start_point(data, current_index=i)
                    #data,mirco_trendline_end = find_trend_line_from_start_point_to_current_i(data, current_index=i)
                    data.at[current_date, 'Searching_micro_trendline'] = True
                else:
                    data.at[current_date, 'Uptrend'] = prev_uptrend

    return data
