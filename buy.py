from trade import Trade


def buy_check(open_trades, data, i, cash, buy_markers, equity, trades):

    # Require historical and future context, but check only what’s actually needed
    # if i < 52:
    #     return open_trades, cash, buy_markers, trades

    current_date = data.index[i]
    close = data['D_Close'].iloc[i]
    chikou = data['D_Chikou_span'].iloc[i-26]
    close_26_back = data['D_Close'].iloc[i - 26]


    # === Indicators ===
    ema_50 = data['EMA_50'].iloc[i]
    ema_200 = data['EMA_200'].iloc[i]
    ema_200_past = data['EMA_200'].iloc[i - 5]

    tenkan = data['D_Tenkan_sen'].iloc[i]
    kijun = data['D_Kijun_sen'].iloc[i]
    senkou_a_future = data['D_Senkou_span_A'].iloc[i + 26]
    senkou_b_future = data['D_Senkou_span_B'].iloc[i + 26]
    senkou_b_future_prev = data['D_Senkou_span_B'].iloc[i - 25]

    DC_Upper_365 = data['DC_Upper_365'].iloc[i]
    DC_Upper_365_prev = data['DC_Upper_365'].iloc[i - 1]

    # === Ichimoku Logic ===
    cloud_future_is_green = senkou_a_future > senkou_b_future
    cloud_future_is_upgoing = senkou_a_future > data['D_Senkou_span_A'].iloc[i + 25]
    senkou_b_rising = senkou_b_future > senkou_b_future_prev

    chikou_index = i - 26
    if chikou_index < 26:
        return open_trades, cash, buy_markers, trades  # Avoid negative index

    # === Daily Chikou Clearance ===
    chikou_clearance_level = max(
        data['D_High'].iloc[chikou_index - 26:chikou_index].max(),
        data['D_Senkou_span_A'].iloc[chikou_index - 26:chikou_index].max(),
        data['D_Senkou_span_B'].iloc[chikou_index - 26:chikou_index].max()
    )
    chikou_has_clear_sight = chikou > chikou_clearance_level

    # === Weekly Chikou Clearance ===
    chikou_weekly = data['W_Chikou_span'].iloc[i-(26*7)]
    weekly_chikou_index = i - 26
    if weekly_chikou_index < 26:
        return open_trades, cash, buy_markers, trades

    weekly_chikou_clearance_level = max(
        data['W_High'].iloc[weekly_chikou_index - 26:weekly_chikou_index].max(),
        data['W_Senkou_span_A'].iloc[weekly_chikou_index - 26:weekly_chikou_index].max(),
        data['W_Senkou_span_B'].iloc[weekly_chikou_index - 26:weekly_chikou_index].max()
    )
    weekly_chikou_has_clear_sight = chikou_weekly > weekly_chikou_clearance_level

    # === Trend logic ===
    ema200_is_rising = ema_200 > ema_200_past
    ema_close_together = abs(ema_50 - ema_200) / ema_200 < 0.7

    # === Trigger: breakout above DC upper ===
    crossed_dc_upper = close > DC_Upper_365_prev

    # === Final buy signal ===
    buy_signal = (
        crossed_dc_upper and
        ema_close_together and
        not open_trades and
        chikou_has_clear_sight and
        weekly_chikou_has_clear_sight and
        cloud_future_is_green and
        cloud_future_is_upgoing and
        senkou_b_rising
    )

    if buy_signal:
        #if compute_latest_channel_breakout(data, i):  
        stoploss_price = ema_200
        risk_per_unit = close - stoploss_price
        if risk_per_unit > 0:
            max_risk = 0.02 * equity
            quantity = max_risk / risk_per_unit
            cost = quantity * close

            if cash >= cost:
                print("✅ BUY SIGNAL detected!")
                print(f"[{current_date}] Buy @ {close:.2f}, Chikou: {chikou:.2f}, Future Cloud: {senkou_a_future:.2f}/{senkou_b_future:.2f}")
                trade = Trade(
                    entry_date=current_date,
                    entry_price=close,
                    quantity=quantity,
                    stoploss=stoploss_price,
                    entry_equity=equity
                )
                trades.append(trade)
                open_trades.append(trade)
                buy_markers.append((current_date, close))
                cash -= cost

    return open_trades, cash, buy_markers, trades
