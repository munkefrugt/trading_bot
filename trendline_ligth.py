import yfinance as yf
import pandas as pd
import numpy as np
from scipy.signal import argrelextrema
import plotly.graph_objects as go

# === Helper: Confirmed extrema ===
def find_confirmed_extrema(y, order=5):
    maxima = argrelextrema(y, np.greater_equal, order=order)[0]
    minima = argrelextrema(y, np.less_equal, order=order)[0]
    return maxima, minima

# === Main: Stick Trend Channels (straight lines) ===
def compute_trend_channels(price_series, lookback=250, order=5):
    if not isinstance(price_series, pd.Series):
        raise ValueError("Input must be a Pandas Series of prices.")

    # Trim to lookback window
    if len(price_series) > lookback:
        price_series = price_series.iloc[-lookback:]

    data = price_series.to_frame(name="y")

    # === 1. Find pivot highs and lows ===
    maxima, minima = find_confirmed_extrema(data['y'].values, order=order)

    if len(maxima) < 2 or len(minima) < 2:
        return data, [], [], None, None, [], [], []

    # === 2. Fit straight lines to last 2 pivot highs and lows ===
    def fit_line(pivots):
        x = np.array(pivots)
        y = data['y'].iloc[pivots].values
        m, b = np.polyfit(x, y, 1)  # y = mx+b
        return m, b

    # Fit resistance and support lines
    m_top, b_top = fit_line(maxima[-2:])
    m_bot, b_bot = fit_line(minima[-2:])

    x_vals = np.arange(len(data))
    data['top_line'] = m_top * x_vals + b_top
    data['bot_line'] = m_bot * x_vals + b_bot

    # === 3. Breakout detection ===
    breakouts = []
    for i in range(len(data)):
        if data['y'].iloc[i] > data['top_line'].iloc[i]:
            breakouts.append((data.index[i], data['y'].iloc[i], 'breakout_up'))
        elif data['y'].iloc[i] < data['bot_line'].iloc[i]:
            breakouts.append((data.index[i], data['y'].iloc[i], 'breakout_down'))

    return data, maxima, minima, data['top_line'], data['bot_line'], [], [], breakouts


# === Download fresh BTC data ===
print("Downloading BTC data from Yahoo Finance...")
btc = yf.download("BTC-USD", period="2y", interval="1d")

# Flatten columns if multi-index
if isinstance(btc.columns, pd.MultiIndex):
    btc.columns = [col[0].lower() for col in btc.columns]

# Clean index
btc.reset_index(inplace=True)
btc.set_index('Date', inplace=True)
btc.index.name = 'date'

# Extract price series
price_series = btc['close']

# === Compute channels ===
data, maxima, minima, top_line, bot_line, _, _, breakouts = compute_trend_channels(
    price_series, lookback=365*2, order=5
)

# === Plot ===
fig = go.Figure()

# Price
fig.add_trace(go.Scatter(x=data.index, y=data['y'], mode='lines', name='BTC Close', line=dict(color='royalblue')))

# Channel lines
fig.add_trace(go.Scatter(x=data.index, y=top_line, mode='lines', name='Top Line', line=dict(color='green', dash='dash')))
fig.add_trace(go.Scatter(x=data.index, y=bot_line, mode='lines', name='Bottom Line', line=dict(color='red', dash='dash')))

# Pivots
fig.add_trace(go.Scatter(x=data.index[maxima], y=data['y'].iloc[maxima], mode='markers', name='Pivot Highs', marker=dict(color='green', size=8, symbol='triangle-up')))
fig.add_trace(go.Scatter(x=data.index[minima], y=data['y'].iloc[minima], mode='markers', name='Pivot Lows', marker=dict(color='red', size=8, symbol='triangle-down')))

# Breakouts
if breakouts:
    up = [(d, p) for d, p, t in breakouts if t == 'breakout_up']
    down = [(d, p) for d, p, t in breakouts if t == 'breakout_down']
    if up:
        fig.add_trace(go.Scatter(x=[d for d, _ in up], y=[p for _, p in up], mode='markers', name='Breakout ↑',
                                 marker=dict(color='lime', size=10, symbol='star')))
    if down:
        fig.add_trace(go.Scatter(x=[d for d, _ in down], y=[p for _, p in down], mode='markers', name='Breakout ↓',
                                 marker=dict(color='orange', size=10, symbol='star')))

fig.update_layout(
    title="BTC-USD Stick Trend Channel Detection",
    xaxis_title="Date",
    yaxis_title="Price (USD)",
    template='plotly_white',
    height=600
)
fig.show()
