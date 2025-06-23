from trade import Trade
from get_data import fetch_btc_data
from analyse import compute_heikin_ashi, compute_ema, compute_ichimoku
from signals import detect_signals

def run_backtest():
    data = fetch_btc_data()
    ha = compute_heikin_ashi(data)  # You can keep this if you're using HA in `plot`, else remove
    ema50 = compute_ema(data, 50)
    ema200 = compute_ema(data, 200)
    ichimoku = compute_ichimoku(data)

    trades = []
    buy_markers = []
    sell_markers = []
    current_trade = None

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

        # Buy condition — without Heikin-Ashi
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

        if current_trade is None and buy_signal:
            current_trade = Trade(entry_date=current_date, entry_price=close)
            trades.append(current_trade)
            buy_markers.append((current_date, close))

        elif current_trade and sell_signal:
            current_trade.close(exit_date=current_date, exit_price=close)
            sell_markers.append((current_date, close))
            current_trade = None

    return data, [ema50, ema200], ichimoku, buy_markers, sell_markers, trades
