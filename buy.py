# buy.py
from trade import Trade

def buy_check(open_trades, data, i, cash, buy_markers, equity, trades):
    current_date = data.index[i]
    close = float(data["D_Close"].iloc[i])

    # One position at a time (keep your current rule)
    if len(open_trades) > 0:
        return open_trades, cash, buy_markers, trades, data

    # --- 5% stop below close ---
    stoploss_price = close * 0.95
    risk_per_unit = close - stoploss_price  # = 0.05 * close

    if risk_per_unit <= 0:
        return open_trades, cash, buy_markers, trades, data

    # --- 2% equity risk, allow FRACTIONS; cap by available cash ---
    max_risk = 0.02 * equity
    raw_qty = max_risk / risk_per_unit                # target size by risk
    cash_cap_qty = cash / close                       # fractional sizing
    quantity = min(raw_qty, cash_cap_qty)

    if quantity <= 0:
        return open_trades, cash, buy_markers, trades, data

    cost = quantity * close

    #print(f"✅ BUY [{current_date}] @ {close:.2f} qty={quantity:.6f} "
    #      f"stop={stoploss_price:.2f} (risk/unit={risk_per_unit:.4f})")

    trade = Trade(
        entry_date=current_date,
        entry_price=close,
        quantity=quantity,
        stoploss=float(stoploss_price),
        entry_equity=equity,
    )
    trades.append(trade)
    open_trades.append(trade)
    buy_markers.append((current_date, close))
    cash -= cost

    return open_trades, cash, buy_markers, trades, data
