def detect_signals(data, ha_data, ema50, ema200, ichimoku):
    buy_signals = []
    sell_signals = []

    for i in range(52, len(data)):  # make sure we have Ichimoku + EMAs
        close = data['Close'].iloc[i]

        # Check Heikin-Ashi: strong bullish momentum
        ha_green = (
            ha_data['Close'].iloc[i] > ha_data['Open'].iloc[i] and
            ha_data['Open'].iloc[i] > ha_data['Low'].iloc[i] and
            (ha_data['Close'].iloc[i] - ha_data['Open'].iloc[i]) > (0.5 * ha_data['Open'].iloc[i])  # long body
        )

        if (
            close > ema50.iloc[i] > ema200.iloc[i]
            and ichimoku['Senkou_span_A'].iloc[i] > ichimoku['Senkou_span_B'].iloc[i]
            and close > max(ichimoku['Senkou_span_A'].iloc[i], ichimoku['Senkou_span_B'].iloc[i])
            and ichimoku['Tenkan_sen'].iloc[i] > ichimoku['Kijun_sen'].iloc[i]
            and ha_green
        ):
            buy_signals.append((ha_data.index[i], close))

        # Chikou Span sell condition
        if i >= 26:
            chikou_span = ichimoku['Chikou_span'].iloc[i]
            price_26_back = data['Close'].iloc[i - 26]
            if chikou_span < price_26_back:
                sell_signals.append((ha_data.index[i], close))

    return buy_signals, sell_signals
