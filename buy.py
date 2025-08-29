# buy.py
import pandas as pd
import config
from trade import Trade


def buy_check(open_trades, data, i, cash, buy_markers, equity, trades):

    current_date = data.index[i]
    close = float(data["D_Close"].iloc[i])

    # --- Weekly event (build mask & mark first daily of each event) ---
    w = config.ichimoku_weekly

    # --- Daily Ichimoku (future cloud + stop source) ---
    D_sen_A_future = float(data["D_Senkou_span_A_future"].iloc[i])
    D_sen_B_future = float(data["D_Senkou_span_B_future"].iloc[i])
    D_future_cloud_green = D_sen_A_future > D_sen_B_future
    D_kijun = float(data["D_Kijun_sen"].iloc[i])

    # --- Donchian filters ---
    DC_26_prev = float(data["DC_Upper_26"].iloc[i - 1]) if i > 0 else float(data["DC_Upper_26"].iloc[i])
    above_DC_26_line = close > DC_26_prev
    above_DC_year_line = (close > float(data["DC_Upper_365"].iloc[i - 1])) if i > 0 else False

    buy_signal = (
        (len(open_trades) == 0)
        and D_future_cloud_green
        and above_DC_26_line
        and above_DC_year_line
    )

    if buy_signal:
        stoploss_price = D_kijun
        risk_per_unit = close - stoploss_price
        if risk_per_unit > 0:
            max_risk = 0.02 * equity  # 2% risk per trade
            quantity = max_risk / risk_per_unit
            cost = quantity * close

            if cash >= cost:
                print(f"✅ BUY [{current_date}] @ {close:.2f} (W_SenB flat→rise + EMA staircase)")
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
