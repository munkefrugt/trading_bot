import yfinance as yf
import pandas as pd
import numpy as np
from scipy.signal import argrelextrema
import plotly.graph_objects as go
from itertools import combinations

# === Fetch BTC-USD Data (2 years) ===
btc = yf.download("BTC-USD", start="2022-08-01", end="2024-08-01", interval="1d").reset_index()
btc = btc[['Date', 'Close']].dropna()
btc.columns = ['ds', 'y']
btc.set_index('ds', inplace=True)

# === Detect Major Peaks ===
def find_peaks_and_valleys(series, order=10):
    """Find major peaks (tops) and valleys (bottoms)."""
    highs = argrelextrema(series.values, np.greater_equal, order=order)[0]
    lows = argrelextrema(series.values, np.less_equal, order=order)[0]
    return highs, lows

highs, lows = find_peaks_and_valleys(btc['y'], order=10)

# === Score Line Fit ===
def line_fit_score(x_idx, y_vals, slope, intercept, tolerance=0.02):
    """
    Score how well a line fits points.
    - tolerance: max % distance from line to count as a "touch"
    """
    predicted = slope * x_idx + intercept
    distance = np.abs(y_vals - predicted) / y_vals
    return np.mean(distance < tolerance)  # % of points within tolerance

# === Generate Candidate Lines (from tops or bottoms) ===
def generate_trendline(points_idx, prices):
    best_line = None
    best_score = 0
    
    for (i, j) in combinations(range(len(points_idx)), 2):  # pick 2 points
        x1, x2 = points_idx[i], points_idx[j]
        y1, y2 = prices[i], prices[j]
        
        slope = (y2 - y1) / (x2 - x1)
        intercept = y1 - slope * x1
        
        # Score line fit to all selected points
        score = line_fit_score(points_idx, prices, slope, intercept)
        if score > best_score:
            best_score = score
            best_line = (slope, intercept)
    return best_line, best_score

# === Macro Resistance (from highs) ===
high_x = np.array([btc.index.get_loc(btc.index[i]) for i in highs])
high_y = btc['y'].iloc[highs].values
res_line, res_score = generate_trendline(high_x, high_y)

# === Macro Support (from lows) ===
low_x = np.array([btc.index.get_loc(btc.index[i]) for i in lows])
low_y = btc['y'].iloc[lows].values
sup_line, sup_score = generate_trendline(low_x, low_y)

# === Compute Lines ===
x_vals = np.arange(len(btc))
res_line_vals = res_line[0] * x_vals + res_line[1]
sup_line_vals = sup_line[0] * x_vals + sup_line[1]

# === Plot ===
fig = go.Figure()

# Price
fig.add_trace(go.Scatter(x=btc.index, y=btc['y'], mode='lines', name='BTC Price', line=dict(color='blue')))

# Peaks & Valleys
fig.add_trace(go.Scatter(x=btc.index[highs], y=btc['y'].iloc[highs], mode='markers', name='Highs', marker=dict(color='red', size=8)))
fig.add_trace(go.Scatter(x=btc.index[lows], y=btc['y'].iloc[lows], mode='markers', name='Lows', marker=dict(color='green', size=8)))

# Trendlines
fig.add_trace(go.Scatter(x=btc.index, y=res_line_vals, mode='lines', name='Macro Resistance', line=dict(color='red', width=2)))
fig.add_trace(go.Scatter(x=btc.index, y=sup_line_vals, mode='lines', name='Macro Support', line=dict(color='green', width=2)))

fig.update_layout(
    title="BTC Macro Trendlines (Human-like)",
    xaxis_title="Date",
    yaxis_title="Price (USD)",
    template="plotly_white"
)
fig.show()
