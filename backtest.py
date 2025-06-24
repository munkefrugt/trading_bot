from trade import Trade
from get_data import fetch_btc_data
from analyse import compute_ema, compute_ichimoku , extend_index
import pandas as pd

def run_backtest():
    data = fetch_btc_data()
    data = extend_index(data)
    ema50 = compute_ema(data, 50)
    ema200 = compute_ema(data, 200)
    ichimoku = compute_ichimoku(data)
    print(ichimoku.tail(30))
    trades = []
    buy_markers = []
    sell_markers = []
    open_trades = []

    cash_series = []

    equity_series = []
    equity_index = []

    cash = 10000  # Starting capital

    for i in range(52, len(data) - 26):
        # === Current date and price ===
        current_date = data.index[i]
        close = data['Close'].iloc[i]

        # === Equity snapshot before any new trades or exits ===
        current_equity = cash + sum(t.quantity * close for t in open_trades)
        equity_series.append(current_equity)
        equity_index.append(current_date)
        cash_series.append(cash)

        # Indicator values
        ema_50 = ema50.iloc[i]
        ema_200 = ema200.iloc[i]
        tenkan = ichimoku['Tenkan_sen'].iloc[i]
        kijun = ichimoku['Kijun_sen'].iloc[i]
        chikou = close
        close_26_back = data['Close'].iloc[i - 26] if i >= 26 else None

        senkou_a = ichimoku['Senkou_span_A'].iloc[i]
        senkou_b = ichimoku['Senkou_span_B'].iloc[i]
        senkou_a_future = ichimoku['Senkou_span_A'].iloc[i]
        senkou_b_future = ichimoku['Senkou_span_B'].iloc[i]
        #senkou_a_prev   = ichimoku['Senkou_span_A'].iloc[i-1]

        #cloud_is_green = senkou_a_future > senkou_b_future
        #cloud_is_upgoing = senkou_a_future > senkou_a_prev
        
        buy_signal = (
            close > ema_50 > ema_200 and
            #cloud_is_green and
            #cloud_is_upgoing and
            close > max(senkou_a, senkou_b) and
            tenkan > kijun and
            chikou > close_26_back
        )


        # Sell condition
        sell_signal = (
            chikou < close_26_back
        )

        # Position sizing based on stoploss and risk

        if buy_signal and not open_trades:
            stoploss_price = ema_200
            risk_per_unit = close - stoploss_price

            if risk_per_unit > 0:
                equity = cash + sum((close - t.entry_price) * t.quantity for t in open_trades)
                max_risk = 0.02 * equity
                quantity = max_risk / risk_per_unit
                cost = quantity * close

                if cash >= cost:
                    trade = Trade(
                        entry_date=current_date,
                        entry_price=close,
                        quantity=quantity,
                        stoploss=stoploss_price
                    )
                    trades.append(trade)
                    open_trades.append(trade)
                    buy_markers.append((current_date, close))
                    cash -= cost

        # Check each open trade for stoploss or sell signal
        for trade in open_trades[:]:
            if trade.is_stopped_out(close):
                print(f"💥 STOPLOSS on {current_date.date()} | Close={close:.2f} | Stoploss={trade.stoploss:.2f}")
                trade.close(exit_date=current_date, exit_price=close)
                cash += trade.exit_price * trade.quantity
                sell_markers.append((current_date, close))
                open_trades.remove(trade)

            elif sell_signal:
                print(f"🔻 SELL SIGNAL on {current_date.date()} | Chikou={chikou:.2f} vs Close={close:.2f} | Trade Entry: {trade.entry_date.date()} @ {trade.entry_price:.2f}")
                trade.close(exit_date=current_date, exit_price=close)
                cash += trade.exit_price * trade.quantity
                sell_markers.append((current_date, close))
                open_trades.remove(trade)


    equity_df = pd.Series(equity_series, index=equity_index, name="Equity")
    equity_df = equity_df.reindex(data.index).ffill().fillna(method="bfill")
    cash_df = pd.Series(cash_series, index=equity_index, name="Cash")
    return data, [ema50, ema200], ichimoku, buy_markers, sell_markers, trades, equity_df, cash_df