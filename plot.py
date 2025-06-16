import plotly.graph_objects as go

def plot_btc_close(data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='BTC-USD Close'))

    fig.update_layout(
        title="BTC Plot",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        dragmode='zoom'
    )

    fig.show()


def plot_heikin_ashi(data):
    """
    Plot Heikin-Ashi candles using Plotly.
    """
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name='Heikin-Ashi'
    ))

    fig.update_layout(
        title="Bitcoin Heikin-Ashi Candles",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        hovermode='x unified',
        dragmode='zoom',
        xaxis=dict(rangeslider=dict(visible=False))
    )

    fig.show()


def plot_heikin_ashi_with_indicators(ha_data, ema_list, ichimoku):
    """
    Plot Heikin-Ashi candles with multiple EMAs and Ichimoku indicators.
    """
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

    # EMA lines with labels
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

    # Ichimoku Components
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

    # Ichimoku Cloud Fill
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

    fig.update_layout(
        title="Bitcoin Heikin-Ashi with EMAs & Ichimoku",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        hovermode='x unified',
        dragmode='zoom',
        xaxis=dict(rangeslider=dict(visible=False))
    )

    fig.show()
