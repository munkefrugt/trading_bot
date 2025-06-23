import plotly.graph_objects as go

def plot_heikin_ashi_with_indicators(ha_data, ema_list, ichimoku, buy_signals=None, sell_signals=None):
    fig = go.Figure()

    # Heikin-Ashi Candles
    fig.add_trace(go.Candlestick(
        x=ha_data.index,
        open=ha_data['Open'],
        high=ha_data['High'],
        low=ha_data['Low'],
        close=ha_data['Close'],
        name='Heikin-Ashi'
    ))

    # EMA linesimport plotly.graph_objects as go

def plot_price_with_indicators(data, ema_list, ichimoku, buy_signals=None, sell_signals=None):
    fig = go.Figure()

    # Classic Candlesticks
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name='Price'
    ))

    # EMA lines
    ema_colors = ['blue', 'darkcyan']
    ema_labels = ['EMA 50', 'EMA 200']
    for ema, color, label in zip(ema_list, ema_colors, ema_labels):
        fig.add_trace(go.Scatter(
            x=ema.index,
            y=ema,
            mode='lines',
            name=label,
            line=dict(color=color, width=1)
        ))

    # Ichimoku lines
    color_map = {
        'Tenkan_sen': 'orange',
        'Kijun_sen': 'purple',
        'Senkou_span_A': 'green',
        'Senkou_span_B': 'red',
        'Chikou_span': 'gray'
    }

    for key, color in color_map.items():
        if key in ichimoku.columns:
            fig.add_trace(go.Scatter(
                x=ichimoku.index,
                y=ichimoku[key],
                mode='lines',
                name=key,
                line=dict(color=color, width=1)
            ))

    # Cloud fill
    fig.add_trace(go.Scatter(
        x=ichimoku.index,
        y=ichimoku['Senkou_span_A'],
        line=dict(color='rgba(0,0,0,0)'),
        showlegend=False,
        name='CloudTop'
    ))
    fig.add_trace(go.Scatter(
        x=ichimoku.index,
        y=ichimoku['Senkou_span_B'],
        fill='tonexty',
        fillcolor='rgba(200,200,200,0.3)',
        line=dict(color='rgba(0,0,0,0)'),
        name='Cloud'
    ))

    # Buy/Sell signals
    if buy_signals:
        buy_x, buy_y = zip(*buy_signals)
        fig.add_trace(go.Scatter(x=buy_x, y=buy_y, mode='markers',
                                 name='Buy Signal',
                                 marker=dict(color='green', size=10, symbol='triangle-up')))

    if sell_signals:
        sell_x, sell_y = zip(*sell_signals)
        fig.add_trace(go.Scatter(x=sell_x, y=sell_y, mode='markers',
                                 name='Sell Signal',
                                 marker=dict(color='red', size=10, symbol='triangle-down')))

    fig.update_layout(
        title="Bitcoin Price with EMA & Ichimoku + Buy/Sell Signals",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        hovermode='x unified',
        dragmode='zoom',
        xaxis=dict(rangeslider=dict(visible=False))
    )

    fig.show()

    ema_colors = ['blue', 'darkcyan']
    ema_labels = ['EMA 50', 'EMA 200']
    for ema, color, label in zip(ema_list, ema_colors, ema_labels):
        fig.add_trace(go.Scatter(
            x=ema.index,
            y=ema,
            mode='lines',
            name=label,
            line=dict(color=color, width=1)
        ))

    # Ichimoku lines
    color_map = {
        'Tenkan_sen': 'orange',
        'Kijun_sen': 'purple',
        'Senkou_span_A': 'green',
        'Senkou_span_B': 'red',
        'Chikou_span': 'gray'
    }

    for key, color in color_map.items():
        if key in ichimoku.columns:
            fig.add_trace(go.Scatter(
                x=ichimoku.index,
                y=ichimoku[key],
                mode='lines',
                name=key,
                line=dict(color=color, width=1)
            ))

    # Cloud fill
    fig.add_trace(go.Scatter(
        x=ichimoku.index,
        y=ichimoku['Senkou_span_A'],
        line=dict(color='rgba(0,0,0,0)'),
        showlegend=False,
        name='CloudTop'
    ))
    fig.add_trace(go.Scatter(
        x=ichimoku.index,
        y=ichimoku['Senkou_span_B'],
        fill='tonexty',
        fillcolor='rgba(200,200,200,0.3)',
        line=dict(color='rgba(0,0,0,0)'),
        name='Cloud'
    ))

    # Plot Buy/Sell markers
    if buy_signals:
        buy_x, buy_y = zip(*buy_signals)
        fig.add_trace(go.Scatter(x=buy_x, y=buy_y, mode='markers',
                                 name='Buy Signal',
                                 marker=dict(color='green', size=10, symbol='triangle-up')))

    if sell_signals:
        sell_x, sell_y = zip(*sell_signals)
        fig.add_trace(go.Scatter(x=sell_x, y=sell_y, mode='markers',
                                 name='Sell Signal',
                                 marker=dict(color='red', size=10, symbol='triangle-down')))

    fig.update_layout(
        title="Bitcoin Heikin-Ashi with EMAs & Ichimoku + Buy/Sell Signals",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        hovermode='x unified',
        dragmode='zoom',
        xaxis=dict(rangeslider=dict(visible=False))
    )

    fig.show()
