import plotly.graph_objects as go
from plotly.subplots import make_subplots

def plot_price_with_indicators(data, ema_list, ichimoku, buy_signals=None, sell_signals=None, trades=None, equity_curve=None, cash_series=None):
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        row_heights=[0.6, 0.25, 0.15],
        vertical_spacing=0.03,
        subplot_titles=("Price with Indicators", "Equity Curve", "Cash")
    )

    # Price candlesticks
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name='Price'
    ), row=1, col=1)



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
        ), row=1, col=1)

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
            ), row=1, col=1)

    # Cloud fill
    fig.add_trace(go.Scatter(
        x=ichimoku.index,
        y=ichimoku['Senkou_span_A'],
        line=dict(color='rgba(0,0,0,0)'),
        showlegend=False,
        name='CloudTop'
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=ichimoku.index,
        y=ichimoku['Senkou_span_B'],
        fill='tonexty',
        fillcolor='rgba(200,200,200,0.3)',
        line=dict(color='rgba(0,0,0,0)'),
        name='Cloud'
    ), row=1, col=1)

    # Buy/Sell signals
    if buy_signals:
        buy_x, buy_y = zip(*buy_signals)
        fig.add_trace(go.Scatter(x=buy_x, y=buy_y, mode='markers',
                                 name='Buy Signal',
                                 marker=dict(color='green', size=20, symbol='triangle-up')), row=1, col=1)

    if sell_signals:
        sell_x, sell_y = zip(*sell_signals)
        fig.add_trace(go.Scatter(x=sell_x, y=sell_y, mode='markers',
                                 name='Sell Signal',
                                 marker=dict(color='red', size=20, symbol='triangle-down')), row=1, col=1)

    # Equity curve subplot
    if equity_curve is not None:
        fig.add_trace(go.Scatter(
            x=equity_curve.index,
            y=equity_curve,
            name='Equity Curve',
            line=dict(color='black')
        ), row=2, col=1)

    # Cash subplot
    if cash_series is not None:
        fig.add_trace(go.Scatter(
            x=cash_series.index,
            y=cash_series,
            name='Cash',
            line=dict(color='orange')
        ), row=3, col=1)

    fig.update_layout(
        hovermode='x unified',
        xaxis=dict(rangeslider=dict(visible=False)),
        xaxis3=dict(title="Date"),
        yaxis2=dict(title="Cumulative Profit (USD)"),
        yaxis3=dict(title="Cash (USD)")
    )

    fig.show()
