from trade import Trade

def buy_check(open_trades, data, i, cash, buy_markers, equity, trades):
    current_date = data.index[i]
    close = data['D_Close'].iloc[i]

    # === Indicators ===
    ema_50 = data['EMA_50'].iloc[i]
    ema_200 = data['EMA_200'].iloc[i]
    ema_200_past = data['EMA_200'].iloc[i - 5]

    # Daily Ichimoku future
    senkou_a_future = data['D_Senkou_span_A'].iloc[i + 26]
    senkou_b_future = data['D_Senkou_span_B'].iloc[i + 26]

    # Weekly Ichimoku (current)
    w_senkou_a = data['W_Senkou_span_A'].iloc[i]
    w_senkou_b = data['W_Senkou_span_B'].iloc[i]

    # === Bollinger Bands ===
    bb_upper = data['D_BB_Upper_20'].iloc[i]
    bb_lower = data['D_BB_Lower_20'].iloc[i]
    bb_middle = data['D_BB_Middle_20'].iloc[i]
    bb_width = bb_upper - bb_lower
    bb_width_prev = data['D_BB_Upper_20'].iloc[i-1] - data['D_BB_Lower_20'].iloc[i-1]

    # ✅ Condition 1: BB Squeeze -> Expansion
    bb_squeeze = bb_width_prev < (bb_middle * 0.04)  # squeeze <4% of mid price
    close_above_upper_bb = close > bb_upper  # breakout confirmation

    # ✅ Condition 2: Daily Ichimoku future bullish
    cloud_future_is_green = senkou_a_future > senkou_b_future

    # ✅ Condition 3: Close above Weekly Cloud
    above_weekly_cloud = close > max(w_senkou_a, w_senkou_b)

    # ✅ Condition 4: EMA uptrend
    ema_trend_ok = ema_200 > ema_200_past and ema_50 > ema_200

    # === Final Buy Signal ===
    pre_buy_signal = (
        not open_trades and
        #bb_squeeze and
        close_above_upper_bb and
        cloud_future_is_green and
        above_weekly_cloud and
        ema_trend_ok
    )

    if pre_buy_signal:
        stoploss_price = ema_200
        risk_per_unit = close - stoploss_price
        if risk_per_unit > 0:
            max_risk = 0.02 * equity
            quantity = max_risk / risk_per_unit
            cost = quantity * close

            if cash >= cost:
                print(f"✅ BUY [{current_date}] @ {close:.2f} (BB Breakout + Green Cloud + Weekly Above)")
                trade = Trade(entry_date=current_date,
                              entry_price=close,
                              quantity=quantity,
                              stoploss=stoploss_price,
                              entry_equity=equity)
                trades.append(trade)
                open_trades.append(trade)
                buy_markers.append((current_date, close))
                cash -= cost

    return open_trades, cash, buy_markers, trades
