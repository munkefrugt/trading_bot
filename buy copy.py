from trade import Trade

def buy_check(open_trades, data, i, cash, buy_markers, equity, trades):
    close = data['Close'].iloc[i]
    chikou = data['D_Chikou_span'].iloc[i]
    close_26_back = data['Close'].iloc[i - 26] if i >= 26 else None
    DC_Upper_365 = data['DC_Upper_365'].iloc[i]
    DC_Upper_365_prev = data['DC_Upper_365'].iloc[i - 1] if i >= 1 else None
    ema_50 = data['EMA_50'].iloc[i]
    ema_200 = data['EMA_200'].iloc[i]
    ema_200_past = data['EMA_200'].iloc[i - 5]

    tenkan = data['D_Tenkan_sen'].iloc[i]
    kijun = data['D_Kijun_sen'].iloc[i]
    senkou_a = data['D_Senkou_span_A'].iloc[i]
    senkou_b = data['D_Senkou_span_B'].iloc[i]
    senkou_a_future = data['D_Senkou_span_A'].iloc[i + 26]
    senkou_b_future = data['D_Senkou_span_B'].iloc[i + 26]
    senkou_b_future_prev = data['D_Senkou_span_A'].iloc[i - 25]

    cloud_future_is_green = senkou_a_future > senkou_b_future
    cloud_future_is_upgoing = senkou_a_future > senkou_b_future_prev

    chikou_index = i - 26
    chikou_clearance_level = data['High'].iloc[chikou_index - 26 : chikou_index].max()
    chikou_has_clear_sight = chikou > chikou_clearance_level

    ema200_is_rising = ema_200 > ema_200_past

    current_date = data.index[i]
    # === special buy coditions: ===
    # === ema_close_together ===
    ema_close_together = abs(ema_50 - ema_200) / ema_200 < 0.7  # or 0.03, etc.

    # === Entry condition: breakout above DC upper ===
    crossed_dc_upper = (
        DC_Upper_365_prev is not None and
        close > DC_Upper_365_prev
        
    )

    # === Final buy signal ===
    buy_signal = (
        crossed_dc_upper and
        ema_close_together and
        not open_trades
        # Add more filters here if needed
    )

    if buy_signal:
        stoploss_price = ema_200
        risk_per_unit = close - stoploss_price
        if risk_per_unit > 0:
            max_risk = 0.02 * equity
            quantity = max_risk / risk_per_unit
            cost = quantity * close

            if cash >= cost:
                print("BUY SIGNAL detected!")
                print(f"[{current_date}] Buy @ {close:.2f}, Chikou: {chikou:.2f} vs Future Cloud: {senkou_a_future:.2f}/{senkou_b_future:.2f}")
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
