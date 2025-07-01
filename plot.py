import plotly.graph_objects as go
import pandas as pd
from plotly.subplots import make_subplots
def plot_price_with_indicators(data,
                                buy_signals=None, sell_signals=None,
                                trades=None, equity_curve=None, cash_series=None,
                                weekly_ha=None, weekly_cloud=None):
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        row_heights=[0.6, 0.25, 0.15],
        vertical_spacing=0.03,
        subplot_titles=("Price with Indicators", "Equity Curve", "Cash")
    )

    # === Daily price candlesticks ===
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name='Daily',
        visible='legendonly'
    ), row=1, col=1)

    # === Daily EMA lines ===
    ema_config = [
        ('EMA_50', 'blue', 'EMA 50'),
        ('EMA_200', 'darkcyan', 'EMA 200')
    ]
    for col, color, label in ema_config:
        if col in data.columns:
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data[col],
                mode='lines',
                name=label,
                line=dict(color=color, width=1)
            ), row=1, col=1)

    # === Ichimoku Lines ===
    ichimoku_lines = {
        'D_Tenkan_sen': ('orange', 'Tenkan-sen'),
        'D_Kijun_sen': ('purple', 'Kijun-sen'),
        'D_Senkou_span_A': ('green', 'Senkou A'),
        'D_Senkou_span_B': ('red', 'Senkou B'),
        'D_Chikou_span': ('gray', 'Chikou')
    }

    for col, (color, label) in ichimoku_lines.items():
        if col in data.columns:
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data[col],
                mode='lines',
                name=label,
                line=dict(color=color, width=1)
            ), row=1, col=1)

    # === Ichimoku Cloud fill ===
    if 'D_Senkou_span_A' in data.columns and 'D_Senkou_span_B' in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['D_Senkou_span_A'],
            line=dict(color='rgba(0,0,0,0)'),
            showlegend=False
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['D_Senkou_span_B'],
            fill='tonexty',
            fillcolor='rgba(200,200,200,0.3)',
            line=dict(color='rgba(0,0,0,0)'),
            name='Ichimoku Cloud'
        ), row=1, col=1)

    # === Buy/Sell Markers ===
    if buy_signals:
        buy_x, buy_y = zip(*buy_signals)
        fig.add_trace(go.Scatter(x=buy_x, y=buy_y, mode='markers',
                                 name='Buy Signal',
                                 marker=dict(color='green', size=20, symbol='triangle-up')), row=1, col=1)
    # === Buy/Sell Markers ===
    if buy_signals:
        buy_x, buy_y = zip(*buy_signals)
        fig.add_trace(go.Scatter(x=buy_x, y=buy_y, mode='markers',
                                 name='Buy Signal',
                                 marker=dict(color='green', size=20, symbol='triangle-up')), row=1, col=1)

    # === Future Senkou A marker at time of buy ===
        if 'D_Senkou_span_A' in data.columns:
            projected_dates = []
            projected_values = []
            for date, _ in buy_signals:
                if date in data.index:
                    idx = data.index.get_loc(date)
                    future_idx = idx + 26
                    if future_idx < len(data):
                        projected_dates.append(data.index[future_idx])
                        projected_values.append(data['D_Senkou_span_A'].iloc[future_idx])

            fig.add_trace(go.Scatter(
                x=projected_dates,
                y=projected_values,
                mode='markers',
                name='Future Senkou A @ Buy',
                marker=dict(color='black', size=10, symbol='star')
            ), row=1, col=1)


    if sell_signals:
        sell_x, sell_y = zip(*sell_signals)
        fig.add_trace(go.Scatter(x=sell_x, y=sell_y, mode='markers',
                                 name='Sell Signal',
                                 marker=dict(color='red', size=20, symbol='triangle-down')), row=1, col=1)


    # === Chikou Span marker at time of buy ===
    if 'D_Chikou_span' in data.columns:
        chikou_dates = []
        chikou_values = []
        for date, _ in buy_signals:
            if date in data.index:
                idx = data.index.get_loc(date)
                chikou_idx = idx - 26
                if chikou_idx >= 0:
                    chikou_dates.append(data.index[chikou_idx])
                    chikou_values.append(data['Close'].iloc[idx])  # Use close at time of buy

        fig.add_trace(go.Scatter(
            x=chikou_dates,
            y=chikou_values,
            mode='markers',
            name='Chikou Span @ Buy',
            marker=dict(color='purple', size=10, symbol='square')
        ), row=1, col=1)


    # === Weekly HA candles overlay ===
    if weekly_ha is not None:
        fig.add_trace(go.Candlestick(
            x=weekly_ha.index,
            open=weekly_ha['Open'],
            high=weekly_ha['High'],
            low=weekly_ha['Low'],
            close=weekly_ha['Close'],
            name='Weekly HA',
            increasing_line_color='blue',
            decreasing_line_color='gold',
            opacity=0.8,
            showlegend=True
        ), row=1, col=1)

    # === Weekly Ichimoku Overlay ===
    if weekly_cloud is not None:
        for line, color, label in zip(
            ['Senkou_span_A', 'Senkou_span_B'],
            ['lightgreen', 'lightcoral'],
            ['Weekly Senkou A', 'Weekly Senkou B']
        ):
            if line in weekly_cloud.columns:
                fig.add_trace(go.Scatter(
                    x=weekly_cloud.index,
                    y=weekly_cloud[line],
                    mode='lines',
                    name=label,
                    line=dict(color=color, width=2, dash='dash')
                ), row=1, col=1)

    # === Equity subplot ===
    if equity_curve is not None:
        fig.add_trace(go.Scatter(
            x=equity_curve.index,
            y=equity_curve,
            name='Equity Curve',
            line=dict(color='black')
        ), row=2, col=1)

    # === Cash subplot ===
    if cash_series is not None:
        fig.add_trace(go.Scatter(
            x=cash_series.index,
            y=cash_series,
            name='Cash',
            line=dict(color='orange')
        ), row=3, col=1)

    # === Final Layout ===
    fig.update_layout(
        hovermode='x unified',
        xaxis=dict(rangeslider=dict(visible=False)),
        xaxis3=dict(title="Date"),
        yaxis2=dict(title="Equity (USD)"),
        yaxis3=dict(title="Cash (USD)")
    )

    fig.show()
