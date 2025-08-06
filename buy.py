from trade import Trade

def buy_check(open_trades, data, i, cash, buy_markers, equity, trades):
    current_date = data.index[i]
    close = data['D_Close'].iloc[i]

    # === Indicators ===
    ema_200 = data['EMA_200'].iloc[i]

    # === Bollinger Bands ===
    bb_upper = data['D_BB_Upper_20'].iloc[i]
    close_above_upper_bb = close > bb_upper

    # === Weekly Ichimoku Cloud (to confirm price position) ===
    w_senkou_a = data['W_Senkou_span_A'].iloc[i]
    w_senkou_b = data['W_Senkou_span_B'].iloc[i]
    above_weekly_cloud = close > max(w_senkou_a, w_senkou_b)

    # === Buy Condition ===
    pre_buy_signal = (
        not open_trades and            # No open trades
        close_above_upper_bb and       # BB breakout
        above_weekly_cloud             # Price above weekly cloud
    )

    if pre_buy_signal:
        # === Risk Management ===
        stoploss_price = ema_200
        risk_per_unit = close - stoploss_price
        if risk_per_unit > 0:
            max_risk = 0.02 * equity  # Risk 2% per trade
            quantity = max_risk / risk_per_unit
            cost = quantity * close

            # === Check cash and execute trade ===
            if cash >= cost:
                print(f"✅ BUY [{current_date}] @ {close:.2f} (BB breakout, above cloud)")
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

    return open_trades, cash, buy_markers, trades, data
