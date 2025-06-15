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

import plotly.graph_objects as go

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
