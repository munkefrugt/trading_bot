from plotly.subplots import make_subplots
import plotly.graph_objects as go
import pandas as pd
def plot_price_with_indicators(
    data,
    buy_signals=None, 
    sell_signals=None,
    trades=None, 
    equity_curve=None, 
    cash_series=None,
    weekly_data_HA=None
):
    fig = make_subplots(
        rows=3, cols=1,  # Added an extra subplot row
        shared_xaxes=True,
        row_heights=[0.7, 0.2, 0.15],  # Adjusted heights: Price, Slope, Equity, Cash
        vertical_spacing=0.03,
        subplot_titles=("Price with Indicators", "Equity Curve", "Cash")
    )

    # === Daily price candlesticks ===
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['D_Open'],
        high=data['D_High'],
        low=data['D_Low'],
        close=data['D_Close'],
        name='Daily',
        visible=True
    ), row=1, col=1)
    
    # === Weekly HA candlesticks ===
    if all(col in data.columns for col in ['W_HA_Open', 'W_HA_High', 'W_HA_Low', 'W_HA_Close']):
        fig.add_trace(go.Candlestick(
            x=data.index,
            open=data['W_HA_Open'],
            high=data['W_HA_High'],
            low=data['W_HA_Low'],
            close=data['W_HA_Close'],
            name='Weekly HA',
            increasing_line_color='blue',
            decreasing_line_color='yellow',
            opacity=0.7,
            visible='legendonly'
        ), row=1, col=1)

    # === Weekly HA candlesticks (pretty) ===
    if weekly_data_HA is not None:
        fig.add_trace(go.Candlestick(
            x=weekly_data_HA.index,
            open=weekly_data_HA['W_HA_Open'],
            high=weekly_data_HA['W_HA_High'],
            low=weekly_data_HA['W_HA_Low'],
            close=weekly_data_HA['W_HA_Close'],
            name='Weekly HA pretty',
            increasing_line_color='blue',
            decreasing_line_color='yellow',
            opacity=0.6,
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
                line=dict(color=color, width=1),
                visible='legendonly'
            ), row=1, col=1)

    # === Donchian Channel ===
    if 'DC_Upper_365' in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['DC_Upper_365'],
            mode='lines',
            name='DC Upper (52W)',
            line=dict(color='darkgreen', width=1, dash='dot'),
            visible='legendonly'
        ), row=1, col=1)

    if 'DC_Lower_365' in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['DC_Lower_365'],
            mode='lines',
            name='DC Lower (52W)',
            line=dict(color='darkred', width=1, dash='dot'),
            visible='legendonly'
        ), row=1, col=1)

    if 'DC_Middle_365' in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['DC_Middle_365'],
            mode='lines',
            name='DC Mid (52W)',
            line=dict(color='gray', width=1, dash='dot'),
            visible='legendonly'
        ), row=1, col=1)

    # === Daily Ichimoku Lines ===
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
                line=dict(color=color, width=1),
                visible='legendonly'
                ), row=1, col=1)

    # === Ichimoku Cloud fill (Daily) ===
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
            name='Ichimoku Cloud',
            visible='legendonly'
        ), row=1, col=1)

    # === Weekly Ichimoku (dot lines) ===
    ichimoku_weekly_lines = {
        'W_Tenkan_sen': ('orange', 'W Tenkan-sen'),
        'W_Kijun_sen': ('purple', 'W Kijun-sen'),
        'W_Senkou_span_A': ('lightgreen', 'W Senkou A'),
        'W_Senkou_span_B': ('lightcoral', 'W Senkou B'),
        'W_Chikou_span': ('gray', 'W Chikou')
    }
    for col, (color, label) in ichimoku_weekly_lines.items():
        if col in data.columns:
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data[col],
                mode='lines',
                name=label,
                line=dict(color=color, width=3, dash='dot')
            ), row=1, col=1)
    
    # === W_SenB_Future_flat_to_up_point ===
    if 'W_SenB_Future_flat_to_up_point' in data.columns:
        future_senb_points = data[data['W_SenB_Future_flat_to_up_point']]
        fig.add_trace(go.Scatter(
            x=future_senb_points.index,
            y=future_senb_points['W_Senkou_span_B'],  # mark at SenB future value
            mode='markers',
            name='SenB Future falt -> Rising',
            marker=dict(color='cyan', size=14, symbol='star')
        ), row=1, col=1)


    
        # === SenB Trend Dead (Future Black Star) ===
    if 'W_SenB_Trend_Dead' in data.columns:
        dead_points = data[data['W_SenB_Trend_Dead']]
        if not dead_points.empty:
            fig.add_trace(go.Scatter(
                x=dead_points.index,
                y=dead_points['W_Senkou_span_B'],  # Plot at SenB future level
                mode='markers',
                name='SenB Trend Dead',
                marker=dict(color='black', size=16, symbol='square')
            ), row=1, col=1)

        # === Real Uptrend Start Marker ===
    if 'Real_uptrend_start' in data.columns:
        start_points = data[data['Real_uptrend_start']]
        if not start_points.empty:
            fig.add_trace(go.Scatter(
                x=start_points.index,
                y=start_points['D_Close'],  # Plot on close price
                mode='markers',
                name='Uptrend Start',
                marker=dict(color='lime', size=14, symbol='star')
            ), row=1, col=1)

    # === Real Uptrend End Marker ===
    if 'Real_uptrend_end' in data.columns:
        end_points = data[data['Real_uptrend_end']]
        if not end_points.empty:
            fig.add_trace(go.Scatter(
                x=end_points.index,
                y=end_points['D_Close'],  # Plot on close price
                mode='markers',
                name='Uptrend End',
                marker=dict(color='purple', size=14, symbol='square')
            ), row=1, col=1)



    # === Trend Channel Lines ===
    if 'Channel_Top' in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['Channel_Top'],
            mode='lines',
            name='Trend Channel Top',
            line=dict(color='green', width=2, dash='dash'),
            connectgaps=False
        ), row=1, col=1)

    if 'Channel_Bottom' in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['Channel_Bottom'],
            mode='lines',
            name='Trend Channel Bottom',
            line=dict(color='red', width=2, dash='dash'),
            connectgaps=False
        ), row=1, col=1)

    # === Buy Markers ===
    if buy_signals:
        buy_x, buy_y = zip(*buy_signals)
        fig.add_trace(go.Scatter(
            x=buy_x,
            y=buy_y,
            mode='markers',
            name='Buy Signal',
            marker=dict(color='green', size=20, symbol='triangle-up')
        ), row=1, col=1)

    # === Sell Markers ===
    if sell_signals:
        sell_x, sell_y = zip(*sell_signals)
        fig.add_trace(go.Scatter(
            x=sell_x,
            y=sell_y,
            mode='markers',
            name='Sell Signal',
            marker=dict(color='red', size=20, symbol='triangle-down')
        ), row=1, col=1)

    # === Bollinger Bands (20) ===
    if all(col in data.columns for col in ['D_BB_Middle_20', 'D_BB_Upper_20', 'D_BB_Lower_20']):
        # Middle Line
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['D_BB_Middle_20'],
            mode='lines',
            name='BB Middle (20)',
            line=dict(color='gray', width=2, dash='dot')
        ), row=1, col=1)

        # Upper Band
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['D_BB_Upper_20'],
            mode='lines',
            name='BB Upper (20)',
            line=dict(color='blue', width=2)
        ), row=1, col=1)

        # Lower Band
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['D_BB_Lower_20'],
            mode='lines',
            name='BB Lower (20)',
            line=dict(color='blue', width=2)
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

    

    # === Layout ===
    fig.update_layout(
        hovermode='x unified',  # Single hover line shared across subplots
        xaxis=dict(rangeslider=dict(visible=False)),
        xaxis2=dict(matches='x'),  # Match x-axis of subplot 2 to the first
        xaxis3=dict(matches='x'),  # Match x-axis of subplot 3
        xaxis4=dict(matches='x')   # Match x-axis of subplot 4
    )


    fig.show()
