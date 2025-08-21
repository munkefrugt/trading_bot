from trade import Trade

def sell_check(open_trades, data, i, cash, sell_markers):
    current_date = data.index[i]

    close = data['D_Close'].iloc[i]
    ema_50 = data['EMA_50'].iloc[i]

    # Weekly Heikin-Ashi values
    w_open = data['W_HA_Open'].iloc[i]
    w_close = data['W_HA_Close'].iloc[i]

    # === Sell conditions ===
    ha_red = w_close < w_open
    close_below_ema50 = close < ema_50

    for trade in open_trades[:]:
        if ha_red or close_below_ema50:
            print(f"⛔ SELL triggered on {current_date.date()}")
            trade.close(exit_date=current_date, exit_price=close)
            cash += trade.exit_price * trade.quantity
            sell_markers.append((current_date, close))
            open_trades.remove(trade)

    return open_trades, cash, sell_markers
