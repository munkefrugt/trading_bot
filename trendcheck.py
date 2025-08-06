def trend_check(data, i):
    """Check W_SenB trend conditions and update uptrend states in `data`."""

    current_date = data.index[i]

    W_flat_threshold = 0.04
    W_breakout_pct = 0.01
    W_sen_a_buffer = 0.01  # Require W_SenA to be at least 1% above W_SenB

    prev_uptrend = data['Uptrend'].iloc[i-1] if i > 0 else False

    if i + (26 * 7) < len(data) and i - (12 * 7) >= 0:
        # Weekly Future Lines
        W_senb_future_line = data['W_Senkou_span_B'].shift(-26 * 7)
        W_sena_future_line = data['W_Senkou_span_A'].shift(-26 * 7)

        # Past flatness check for W_SenB
        W_senb_past_future = W_senb_future_line.iloc[i - (12 * 7):i]
        W_flat_base_avg = W_senb_past_future.mean()
        W_senb_flat_range = (W_senb_past_future.max() - W_senb_past_future.min()) / W_flat_base_avg

        # Current weekly values
        W_senb_future_now = W_senb_future_line.iloc[i]
        W_senb_future_prev = W_senb_future_line.iloc[i - 7]
        W_sena_future_now = W_sena_future_line.iloc[i]

        # === CASE 1: If NOT in uptrend → Look for BUY ZONE ===
        if not prev_uptrend:
            W_sen_a_confirm = W_sena_future_now > W_senb_future_now * (1 + W_sen_a_buffer)

            # ✅ Price must be above or inside the daily cloud for 2 days
            D_price_above_or_inside_cloud = (
                (
                    (data['D_Close'].iloc[i-1] >= data['D_Senkou_span_B'].iloc[i-1]) or
                    (data['D_Close'].iloc[i-1] >= data['D_Senkou_span_A'].iloc[i-1])
                )
                and
                (
                    (data['D_Close'].iloc[i] >= data['D_Senkou_span_B'].iloc[i]) or
                    (data['D_Close'].iloc[i] >= data['D_Senkou_span_A'].iloc[i])
                )
            )

            if (
                W_senb_flat_range < W_flat_threshold
                and W_senb_future_now > W_flat_base_avg * (1 + W_breakout_pct)
                and W_sen_a_confirm
                and D_price_above_or_inside_cloud
            ):
                future_index = i + (26 * 7)
                data.at[data.index[future_index], 'W_SenB_Future_flat_to_up_point'] = True  # Cyan star
                data.at[data.index[i], 'Real_uptrend_start'] = True
                data.at[current_date, 'Uptrend'] = True
                data.at[current_date, 'Trend_Buy_Zone'] = True
                print(f"📈 Entering Buy Zone: {current_date} (W_SenA confirmed & price in/above D cloud)")
            else:
                data.at[current_date, 'Uptrend'] = prev_uptrend

        # === CASE 2: If IN uptrend → Look for DEAD ZONE ===
        else:
            if i - (4 * 7) >= 0:
                lookback = 4 * 7  # 4 weeks

                # W_SenB 4-week trend check
                W_senb_future_4w = W_senb_future_line.iloc[i - lookback:i]
                W_future_downward = W_senb_future_now < W_senb_future_prev
                W_future_flat_4w = (
                    (W_senb_future_4w.max() - W_senb_future_4w.min()) 
                    / W_senb_future_4w.mean()
                ) < 0.005

                # EMA 50 slope over same 4-week window
                EMA_decline_pct = 0.01
                EMA50_4w_ago = data['EMA_50'].iloc[i - lookback]
                EMA50_now = data['EMA_50'].iloc[i]
                EMA50_decline = EMA50_4w_ago > EMA50_now
                # D price under D cloud for 2 consecutive days
                D_price_under_cloud = (
                    data['D_Close'].iloc[i-1] < data['D_Senkou_span_A'].iloc[i-1]
                    and data['D_Close'].iloc[i-1] < data['D_Senkou_span_B'].iloc[i-1]
                    and data['D_Close'].iloc[i] < data['D_Senkou_span_A'].iloc[i]
                    and data['D_Close'].iloc[i] < data['D_Senkou_span_B'].iloc[i]
                )

                # Confirm trend end if W_SenB flat/down + EMA50 decline OR D price under D cloud 2 days
                if ((W_future_downward or W_future_flat_4w) 
                    and EMA50_decline
                    and D_price_under_cloud):
                    # 🔍 Only print lookback info if we actually exit the uptrend
                    EMA50_4w_ago_date = data.index[i - lookback]
                    EMA50_now_date = data.index[i]
                    # print(f"📉 Entering Dead Zone: {current_date}")
                    # print(f"   🔍 EMA50 Lookback: {EMA50_4w_ago_date} → {EMA50_now_date}")
                    # print(f"       Values: {EMA50_4w_ago:.2f} → {EMA50_now:.2f}")
                    # print(f"   • W_Future_downward: {W_future_downward}")
                    # print(f"   • W_Future_flat_4w: {W_future_flat_4w}")
                    # print(f"   • EMA50_decline: {EMA50_decline}")
                    # print(f"   • D_Price_under_cloud: {D_price_under_cloud}")

                    future_index = i + (26 * 7)
                    data.at[data.index[future_index], 'W_SenB_Trend_Dead'] = True
                    data.at[data.index[i], 'Real_uptrend_end'] = True

                    data.at[current_date, 'Uptrend'] = False
                    data.at[current_date, 'Trend_Buy_Zone'] = False
                else:
                    data.at[current_date, 'Uptrend'] = prev_uptrend

    return data
