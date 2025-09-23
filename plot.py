from plotly.subplots import make_subplots
import plotly.graph_objects as go
import pandas as pd
import config

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
    # === Daily close price ===
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['D_Close'],
        mode='lines',
        name='Daily Close',
        line=dict(color='black', width=1.5),
        visible=True
    ), row=1, col=1)    
    
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

    # === D_Close_smooth ===
    if 'D_Close_smooth' in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['D_Close_smooth'],
            mode='lines',
            name='D Close (smoothed)',
            line=dict(color='purple', width=1.5),
            opacity=0.8
        ), row=1, col=1)

    # === Weekly price candlesticks ===
    if all(col in data.columns for col in ['W_Open', 'W_High', 'W_Low', 'W_Close']):
        fig.add_trace(go.Candlestick(
            x=data.index,
            open=data['W_Open'],
            high=data['W_High'],
            low=data['W_Low'],
            close=data['W_Close'],
            name='Weekly',
            increasing_line_color='green',
            decreasing_line_color='red',
            opacity=0.7,
            visible='legendonly'
        ), row=1, col=1)

    # # === Weekly HA candlesticks ===
    # if all(col in data.columns for col in ['W_HA_Open', 'W_HA_High', 'W_HA_Low', 'W_HA_Close']):
    #     fig.add_trace(go.Candlestick(
    #         x=data.index,
    #         open=data['W_HA_Open'],
    #         high=data['W_HA_High'],
    #         low=data['W_HA_Low'],
    #         close=data['W_HA_Close'],
    #         name='Weekly HA',
    #         increasing_line_color='blue',
    #         decreasing_line_color='yellow',
    #         opacity=0.7,
    #         visible='legendonly'
    #     ), row=1, col=1)

    # # === Weekly HA candlesticks (pretty) ===
    # if weekly_data_HA is not None:
    #     fig.add_trace(go.Candlestick(
    #         x=weekly_data_HA.index,
    #         open=weekly_data_HA['W_HA_Open'],
    #         high=weekly_data_HA['W_HA_High'],
    #         low=weekly_data_HA['W_HA_Low'],
    #         close=weekly_data_HA['W_HA_Close'],
    #         name='Weekly HA pretty',
    #         increasing_line_color='blue',
    #         decreasing_line_color='yellow',
    #         opacity=0.6,
    #         visible='legendonly'
    #         ), row=1, col=1)
        

    # === Real Weekly Senkou Span A ===
    fig.add_trace(go.Scatter(
        x=config.ichimoku_weekly.index,
        y=config.ichimoku_weekly['W_Senkou_span_A'],
        mode='lines',
        name='Real W Senkou Span A',
        line=dict(color='green', width=1.5),
        opacity=0.8
    ), row=1, col=1)

    # === Weekly Bollinger Bands (20) ===
    if {'W_BB_Middle_20','W_BB_Upper_20','W_BB_Lower_20'}.issubset(config.weekly_bb.columns):
        # Middle line
        fig.add_trace(go.Scatter(
            x=config.weekly_bb.index,
            y=config.weekly_bb['W_BB_Middle_20'],
            mode='lines',
            name='W BB Middle (20)',
            line=dict(color='gray', width=2, dash='dot')
        ), row=1, col=1)

        # Upper band
        fig.add_trace(go.Scatter(
            x=config.weekly_bb.index,
            y=config.weekly_bb['W_BB_Upper_20'],
            mode='lines',
            name='W BB Upper (20)',
            line=dict(color='darkblue', width=1)
        ), row=1, col=1)

        # Lower band
        fig.add_trace(go.Scatter(
            x=config.weekly_bb.index,
            y=config.weekly_bb['W_BB_Lower_20'],
            mode='lines',
            name='W BB Lower (20)',
            line=dict(color='darkblue', width=1)
        ), row=1, col=1)




    # === Real Weekly Senkou Span B ===
    fig.add_trace(go.Scatter(
        x=config.ichimoku_weekly.index,
        y=config.ichimoku_weekly['W_Senkou_span_B'],
        mode='lines',
        name='Real W Senkou Span B',
        line=dict(color='red', width=1.5),
        opacity=0.8
    ), row=1, col=1)


    # === Daily EMA lines ===
    ema_config = [
        ('EMA_9', 'red', 'EMA 9'),
        ('EMA_20', 'orange', 'EMA 20'),
        ('EMA_50', 'blue', 'EMA 50'),
        ('EMA_100', 'purple', 'EMA 100'),
        ('EMA_200', 'darkcyan', 'EMA 200'),
        ('EMA_365', 'darkgreen', 'EMA 365'),
        ('EMA_2y', 'brown', 'EMA 2y')

    ]
    for col, color, label in ema_config:
        if col in data.columns:
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data[col],
                mode='lines',
                name=label,
                line=dict(color=color, width=1),
                visible=True if col == 'EMA_2y' else 'legendonly'
            ), row=1, col=1)

    # === Daily EMA slope % (row=2) ===
    ema_slope_config = [
        ('EMA_9_slope_%', 'red', 'EMA 9 slope%'),
        ('EMA_20_slope_%', 'orange', 'EMA 20 slope%'),
        ('EMA_50_slope_%', 'blue', 'EMA 50 slope%'),
        ('EMA_100_slope_%', 'purple', 'EMA 100 slope%'),
        ('EMA_200_slope_%', 'darkcyan', 'EMA 200 slope%'),
        ('EMA_365_slope_%', 'darkgreen', 'EMA 365 slope%'),
        ('EMA_2y_slope_%', 'darkgreen', 'EMA 2y slope%'),

    ]

    for col, color, label in ema_slope_config:
        if col in data.columns:
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data[col],
                mode='lines',
                name=label,
                line=dict(color=color, width=1),
                hovertemplate='%{y:.2f}%<extra>' + label + '</extra>',
                visible=True if col == 'EMA_2y_slope_%' else 'legendonly'
            ), row=2, col=1)

    fig.update_yaxes(title_text="EMA slope %", ticksuffix="%", zeroline=True, zerolinewidth=1, row=2, col=1)
    try:
        fig.add_hline(y=0, line_dash='dot', line_width=1, opacity=0.4, row=2, col=1)
    except Exception:
        pass


    # === Donchian Channel yearly===
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

    # === Donchian Channel 26 days ===
    if 'DC_Upper_26' in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['DC_Upper_26'],
            mode='lines',
            name='DC Upper (26 days)',
            line=dict(color='darkgreen', width=1, dash='dot'),
            visible='legendonly'
        ), row=1, col=1)

    if 'DC_Lower_26' in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['DC_Lower_26'],
            mode='lines',
            name='DC Lower (26 days)',
            line=dict(color='darkred', width=1, dash='dot'),
            visible='legendonly'
        ), row=1, col=1)

    if 'DC_Middle_26' in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['DC_Middle_26'],
            mode='lines',
            name='DC Mid (26 days)',
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
    
    # === Start of Dead Trendline Marker ===
    if 'Start_of_Dead_Trendline' in data.columns:
        dead_trendline_starts = data[data['Start_of_Dead_Trendline'] == True]
        if not dead_trendline_starts.empty:
            fig.add_trace(go.Scatter(
                x=dead_trendline_starts.index,
                y=dead_trendline_starts['D_Close'],
                mode='markers',
                name='Start of Dead Trendline',
                marker=dict(color='red', size=10, symbol='x')
            ), row=1, col=1)

    # === Fitted Macro Trendline  from Start_of_Dead_Trendline to senb coresponding dead point===
    # if 'Fitted_Macro_Trendline' in data.columns:
    #     fitted = data['Fitted_Macro_Trendline'].dropna()
    #     if not fitted.empty:
    #         fig.add_trace(go.Scatter(
    #             x=fitted.index,
    #             y=fitted,
    #             mode='lines',
    #             name='Fitted Macro Trendline',
    #             line=dict(color='red', width=2, dash='dot')
    #         ), row=1, col=1)


    # === Smoothed Weekly Senkou Span B (Savitzky–Golay) ===
    if 'W_Senkou_span_B_smooth' in config.ichimoku_weekly.columns:
        fig.add_trace(go.Scatter(
            x=config.ichimoku_weekly.index,
            y=config.ichimoku_weekly['W_Senkou_span_B_smooth'],
            mode='lines',
            name='W Senkou Span B (smoothed)',
            line=dict(color='blue', width=2, dash='solid'),
            opacity=0.9
        ), row=1, col=1)

    # === Optional: slope of smoothed SenB ===
    if 'W_Senkou_span_B_slope_pct' in config.ichimoku_weekly.columns:
        fig.add_trace(go.Scatter(
            x=config.ichimoku_weekly.index,
            y=config.ichimoku_weekly['W_Senkou_span_B_slope_pct'],
            mode='lines',
            name='Slope of W SenB (relative pct)',
            line=dict(color='blue', width=1, dash='dot'),
            opacity=0.8
        ), row=2, col=1)  # slope makes sense in 2nd subplot

    # === "real time" Weekly Senkou Span B (trailing poly fit, causal) ===
    if 'W_SenB_trailing_poly' in config.ichimoku_weekly.columns:
        fig.add_trace(go.Scatter(
            x=config.ichimoku_weekly.index,
            y=config.ichimoku_weekly['W_SenB_trailing_poly'],
            mode='lines',
            name='W SenB (trailing poly)',
            line=dict(color='purple', width=3, dash='solid'),
            opacity=0.9
        ), row=1, col=1)

    # === Slope of Weekly Senkou Span B (trailing poly, %/week) ===
    slope_col = "W_SenB_trailing_slope_pct"  # change if you named it differently
    if slope_col in config.ichimoku_weekly.columns:
        fig.add_trace(go.Scatter(
            x=config.ichimoku_weekly.index,
            y=config.ichimoku_weekly[slope_col],
            mode='lines',
            name='Slope of W SenB (relative %/week)',
            line=dict(color='blue', width=1, dash='dot'),
            opacity=0.8
        ), row=2, col=1)

        # optional reference lines
        fig.add_hline(y=1.0, line_dash="dash", line_width=1, line_color="black", row=2, col=1)  # your threshold
        fig.add_hline(y=0.0, line_dash="dot",  line_width=1, line_color="gray",  row=2, col=1)  # zero-line


    # === Plot Trendline_from_top (X) if it exists ===
    if 'Trendline_from_X' in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['Trendline_from_X'],
            mode='lines',
            name='Trendline from X',
            line=dict(color='orange', dash='dot'),
            connectgaps=False  # <- VERY important!
        ), row=1, col=1)

    # === Plot Trendline_from_top (X) if it exists ===
    if 'Macro_trendline_from_X' in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['Macro_trendline_from_X'],
            mode='lines',
            name='Macro_trendline_from_X',
            line=dict(color='red', dash='dot'),
            connectgaps=False  # <- VERY important!
        ), row=1, col=1)

    # # === Macro Trendlines from W_SenB ===
    # for col in data.columns:
    #     if col.startswith("Macro_Trend_"):
    #         fig.add_trace(go.Scatter(
    #             x=data.index,
    #             y=data[col],
    #             mode='lines',
    #             name=col.replace("Macro_Trend_", "Macro Trend "),
    #             line=dict(color='darkorange', width=2, dash='dashdot'),
    #             connectgaps=False
    #         ), row=1, col=1)

    #=== Weekly ATR ===
    if hasattr(config, "weekly_ATR"):
        for col in config.weekly_ATR.columns:
            fig.add_trace(go.Scatter(
                x=config.weekly_ATR.index,
                y=config.weekly_ATR[col],
                mode="lines",
                name=col.replace("W_", ""),   # cleaner legend name
                line=dict(width=1),
                visible=True
            ), row=3, col=1)


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

        # === SenB Consolidation Start (on SenB itself) ===
    if 'W_SenB_Consol_Start_SenB' in data.columns:
        senb_start_points = data[data['W_SenB_Consol_Start_SenB']]
        if not senb_start_points.empty:
            fig.add_trace(go.Scatter(
                x=senb_start_points.index,
                y=senb_start_points['W_Senkou_span_B'],  # Plot at SenB value
                mode='markers',
                name='SenB Consolidation Start (SenB)',
                marker=dict(color='blue', size=14, symbol='diamond')
            ), row=1, col=1)

    # === SenB Consolidation Start (on Price, 26w back) ===
    if 'W_SenB_Consol_Start_Price' in data.columns:
        price_start_points = data[data['W_SenB_Consol_Start_Price']]
        if not price_start_points.empty:
            fig.add_trace(go.Scatter(
                x=price_start_points.index,
                y=price_start_points['D_Close'],  # Plot on price
                mode='markers',
                name='SenB Consolidation Start (Price)',
                marker=dict(color='darkblue', size=14, symbol='x')
            ), row=1, col=1)

    if 'W_SenB_Consol_start_Adj_jump_6_months' in data.columns:
        adjusted_price_points = data[data['W_SenB_Consol_start_Adj_jump_6_months']]
        if not adjusted_price_points.empty:
            fig.add_trace(go.Scatter(
                x=adjusted_price_points.index,
                y=adjusted_price_points['D_Close'], 
                mode='markers',
                name='Consol jump(Adjusted)',
                marker=dict(color='green', size=14, symbol='x')
            ), row=1, col=1)
    
    if 'W_SenB_Consol_Start_Price_Adjusted' in data.columns:
        adjusted_price_points = data[data['W_SenB_Consol_Start_Price_Adjusted']]
        if not adjusted_price_points.empty:
            fig.add_trace(go.Scatter(
                x=adjusted_price_points.index,
                y=adjusted_price_points['D_Close_smooth'], 
                mode='markers',
                name='SenB Consol Start Price (Adjusted)',
                marker=dict(color='red', size=14, symbol='x')
            ), row=1, col=1)
    

    # === Regression line from last adjusted start ===
    col = "Regline_from_last_adjusted"
    if col in data.columns:
        reg = pd.to_numeric(data[col], errors="coerce")  # <- no dropna
        if reg.notna().any():
            fig.add_trace(go.Scatter(
                x=reg.index,
                y=reg,
                mode="lines",
                name="Regression from last adjusted start",
                line=dict(color = "blue", width=2, dash="dash"),
                connectgaps=False  # ensures NaN gaps are not bridged
            ), row=1, col=1)

    # R² for the regression base line
    col_r2 = "r_2_values_for_regline"
    if {col_r2, "D_Close"} <= set(data.columns):
        r2s = pd.to_numeric(data[col_r2], errors="coerce").dropna()
        if not r2s.empty:
            y_at_price = data.loc[r2s.index, "D_Close"]
            fig.add_trace(go.Scatter(
                x=r2s.index,
                y=y_at_price.values,           # place labels at the price
                mode="text",                   # text-only (no dots)
                text=[f"R² {v:.2f}" for v in r2s.values],
                textposition="top center",
                name="Regline R²",
                showlegend=True,
                visible='legendonly'
            ), row=1, col=1)
        
    
    # Flatness_ratio for the regression base line w_tenkan
    col = "Flatness_ratio"
    if {col, "D_Close"} <= set(data.columns):
        vals = pd.to_numeric(data[col], errors="coerce").dropna()
        if not vals.empty:
            y_at_price = data.loc[vals.index, "D_Close"]
            fig.add_trace(go.Scatter(
                x=vals.index,
                y=y_at_price.values,
                mode="text",
                text=[f"F {v:.3f}" for v in vals.values],  # label with flatness
                textposition="bottom center",
                name="Flatness ratio",
                showlegend=True,
                visible='legendonly'
            ), row=1, col=1)

    # --- Cross count annotations ---
    col_cross = "regline_crosses"
    if {col_cross, "D_Close"} <= set(data.columns):
        crosses = pd.to_numeric(data[col_cross], errors="coerce").dropna()
        if not crosses.empty:
            y_at_price = data.loc[crosses.index, "D_Close"]
            fig.add_trace(go.Scatter(
                x=crosses.index,
                y=y_at_price.values,
                mode="text",
                text=[f"{int(v)}" for v in crosses.values],
                textposition="bottom center",
                name="Regline crosses",
                showlegend=True
            ), row=1, col=1)
    

    # --- Approved gold star markers (as scatter points) ---
    col_appr = "regline_aproved"
    if {col_appr, "D_Close"} <= set(data.columns):
        stars = data.loc[data[col_appr] == True, "D_Close"]
        if not stars.empty:
            fig.add_trace(go.Scatter(
                x=stars.index,
                y=stars.values,
                mode="markers",
                marker=dict(symbol="star", color="gold", size=14, line=dict(width=1, color="black")),
                name="Regline approved",
                showlegend=True
            ), row=1, col=1)

    # --- Regline cross markers (green dots) ---
    col_cross = "Regline_cross_event"
    col_reg = "Regline_from_last_adjusted"
    if {col_cross, col_reg} <= set(data.columns):
        mask = data[col_cross].fillna(False)
        if mask.any():
            xs = data.index[mask]
            ys = data.loc[mask, col_reg]
            fig.add_trace(go.Scatter(
                x=xs,
                y=ys.values,                     # put dots ON the regline
                mode="markers",
                marker=dict(symbol="circle", color="green", size=8, line=dict(width=0)),
                name="Regline cross",
                showlegend=True,
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

    # # === Bollinger Bands (20) ===
    # if all(col in data.columns for col in ['D_BB_Middle_20', 'D_BB_Upper_20', 'D_BB_Lower_20']):
    #     # Middle Line
    #     fig.add_trace(go.Scatter(
    #         x=data.index,
    #         y=data['D_BB_Middle_20'],
    #         mode='lines',
    #         name='BB Middle (20)',
    #         line=dict(color='gray', width=2, dash='dot')
    #     ), row=1, col=1)

    #     # Upper Band
    #     fig.add_trace(go.Scatter(
    #         x=data.index,
    #         y=data['D_BB_Upper_20'],
    #         mode='lines',
    #         name='BB Upper (20)',
    #         line=dict(color='blue', width=2)
    #     ), row=1, col=1)

    #     # Lower Band
    #     fig.add_trace(go.Scatter(
    #         x=data.index,
    #         y=data['D_BB_Lower_20'],
    #         mode='lines',
    #         name='BB Lower (20)',
    #         line=dict(color='blue', width=2)
    #     ), row=1, col=1)

    # bb wwekly squeeze
    if 'W_BB_Squeeze' in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['W_BB_Squeeze'],
            mode='lines',
            name='Weekly BB Squeeze',
            line=dict(color='purple', width=2, dash='dash'),
            visible='legendonly'
        ), row=1, col=1)

    # *****************************START OF TTL SIGNALS *****************************

    # ================ SIGNALS TIME TO LIVE (TTL) see signals/core.py ==============
    # next block relevant helper signals

    # --- Signal: senb_w_future_slope_pct (plot on daily price ---
    if "senb_w_future_flat_base" in data.columns and "D_Close" in data.columns:
        mask = data["senb_w_future_flat_base"].fillna(False).infer_objects(copy=False).astype(bool)
        if mask.any():
            y = pd.Series(index=data.index, dtype="float64")
            y.loc[mask] = data.loc[mask, "D_Close"]
            fig.add_trace(go.Scatter(
                x=data.index,
                y=y,
                mode="lines",
                name="senb_w_future_flat_base",
                line=dict(color="purple", width=5),
                connectgaps=False,
                hovertemplate="senb_w_future_flat_base<br>%{x}<br>SENB_W: %{y:.2f}<extra></extra>",
            ), row=1, col=1)

    if "senb_w_future_slope_pct" in data.columns and "D_Close" in data.columns:
        mask = data["senb_w_future_slope_pct"].fillna(False).infer_objects(copy=False).astype(bool)
        if mask.any():
            y = pd.Series(index=data.index, dtype="float64")
            y.loc[mask] = data.loc[mask, "D_Close"]
            fig.add_trace(go.Scatter(
                x=data.index,
                y=y,
                mode="lines",
                name="senb_w_future_slope_pct",
                line=dict(color="green", width=5),
                connectgaps=False,
                hovertemplate="senb_w_future_slope_pct<br>%{x}<br>SENB_W: %{y:.2f}<extra></extra>",
            ), row=1, col=1)

    # --- All signals ON: gold star at price ---
    if "all_signals_on" in data.columns and "D_Close" in data.columns:
        mask = data["all_signals_on"].fillna(False).astype(bool)

        if mask.any():
            # keep only first True after a False (rising edge)
            rising_edges = mask & (~mask.shift(fill_value=False))

            xs = data.index[rising_edges]
            ys = data.loc[rising_edges, "D_Close"]

            fig.add_trace(go.Scatter(
                x=xs,
                y=ys,
                mode="markers",
                name="All signals ON",
                marker=dict(symbol="star", size=18, color="gold", line=dict(width=1, color="black")),
            ), row=1, col=1)

    # *****************************END OF TTL SIGNALS *****************************
    # ===== helper signals markers ======== #
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

        # === W_SenB_base_val ===
    if 'W_SenB_base_val' in data.columns:
        base_points = data[~data['W_SenB_base_val'].isna()]
        fig.add_trace(go.Scatter(
            x=base_points.index,
            y=base_points['W_SenB_base_val'],
            mode='markers',
            name='SenB Flat Base Anchor',
            marker=dict(color='orange', size=12, symbol='diamond')
        ), row=1, col=1)


    if 'W_SenB_Future_slope_ok_point' in data.columns:
        future_senb_points = data[data['W_SenB_Future_slope_ok_point']]
        fig.add_trace(go.Scatter(
            x=future_senb_points.index,
            y=future_senb_points['W_Senkou_span_B'],  # mark at SenB future value
            mode='markers',
            name='SenB Future -> rise %',
            marker=dict(color='green', size=14, symbol='star')
        ), row=1, col=1)


    # === END of helper signals ===
  



    # # === HMA Lines ===
    # if 'W_HMA_14' in config.weekly_HMA.columns:
    #     fig.add_trace(go.Scatter(
    #         x=config.weekly_HMA.index,
    #         y=config.weekly_HMA['W_HMA_14'],
    #         mode='lines',
    #         name='W HMA 14',
    #         line=dict(color='cyan', width=1.5),
    #         visible='legendonly'
    #     ), row=1, col=1)
        
    # if 'W_HMA_25' in config.weekly_HMA.columns:
    #     fig.add_trace(go.Scatter(
    #         x=config.weekly_HMA.index,
    #         y=config.weekly_HMA['W_HMA_25'],
    #         mode='lines',
    #         name='W HMA 25',
    #         line=dict(color='blue', width=1.5),
    #         visible='legendonly'
    #     ), row=1, col=1)

    # if 'W_HMA_50' in config.weekly_HMA.columns:
    #     fig.add_trace(go.Scatter(
    #         x=config.weekly_HMA.index,
    #         y=config.weekly_HMA['W_HMA_50'],
    #         mode='lines',
    #         name='W HMA 50',
    #         line=dict(color='orange', width=1.5),
    #         visible='legendonly'
    #     ), row=1, col=1)
    
    # if 'W_HMA_100' in config.weekly_HMA.columns:
    #     fig.add_trace(go.Scatter(
    #         x=config.weekly_HMA.index,
    #         y=config.weekly_HMA['W_HMA_100'],
    #         mode='lines',
    #         name='W HMA 100',
    #         line=dict(color='purple', width=1.5),
    #         visible='legendonly'
    #     ), row=1, col=1)

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
