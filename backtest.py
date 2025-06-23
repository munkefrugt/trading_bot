from trade import Trade
from get_data import fetch_btc_data
from analyse import compute_heikin_ashi, compute_ema, compute_ichimoku
import pandas as pd

def run_backtest():
    data = fetch_btc_data()
    ema50 = compute_ema(data, 50)
    ema200 = compute_ema(data, 200)
    ichimoku = compute_ichimoku(data)

    trades = []
    buy_markers = []
    sell_markers = []
    open_trades = []

    equity_series = []
    equity_index = []

    cash = 10000  # Starting capital

    for i in range(52, len(data)):
        current_date = data.index[i]
        close = data['Close'].iloc[i]

        # Indicator values
        ema_50 = ema50.iloc[i]
        ema_200 = ema200.iloc[i]
        tenkan = ichimoku['Tenkan_sen'].iloc[i]
        kijun = ichimoku['Kijun_sen'].iloc[i]
        senkou_a = ichimoku['Senkou_span_A'].iloc[i]
        senkou_b = ichimoku['Senkou_span_B'].iloc[i]
        chikou = ichimoku['Chikou_span'].iloc[i] if i < len(data) else None
        close_26_back = data['Close'].iloc[i - 26] if i >= 26 else None

        # Buy condition
        buy_signal = (
            close > ema_50 > ema_200 and
            senkou_a > senkou_b and
            close > max(senkou_a, senkou_b) and
            tenkan > kijun
        )

        # Sell condition
        sell_signal = (
            chikou is not None and close_26_back is not None and chikou < close_26_back
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
            if trade.is_stopped_out(close) or sell_signal:
                trade.close(exit_date=current_date, exit_price=close)
                cash += trade.exit_price * trade.quantity
                sell_markers.append((current_date, close))
                open_trades.remove(trade)

        # Equity = cash + current unrealized gains
        unrealized = sum((close - t.entry_price) * t.quantity for t in open_trades)
        equity_series.append(cash + unrealized)
        equity_index.append(current_date)

    equity_df = pd.Series(equity_series, index=equity_index, name="Equity")
    equity_df = equity_df.reindex(data.index).ffill().fillna(method="bfill")

    return data, [ema50, ema200], ichimoku, buy_markers, sell_markers, trades, equity_df
