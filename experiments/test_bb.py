import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression

# === 1. Download BTC-USD data ===
btc = yf.download("BTC-USD", start="2022-08-01", end="2024-08-01", interval="1d").reset_index()
btc = btc[['Date', 'Close']].dropna()
btc.columns = ['ds', 'y']

# === 2. Compute Bollinger Bands ===
window = 20
btc['MA'] = btc['y'].rolling(window=window).mean()
btc['STD'] = btc['y'].rolling(window=window).std()
btc['BB_upper'] = btc['MA'] + 2 * btc['STD']
btc['BB_lower'] = btc['MA'] - 2 * btc['STD']
btc['BB_width'] = btc['BB_upper'] - btc['BB_lower']

# === Parameters ===
bb_bubble_threshold = btc['BB_width'].mean() + 1.5 * btc['BB_width'].std()
calm_offset = 7
slope_threshold = 0.02       # flat slope threshold
r2_threshold = 0.8           # good regression fit
min_base_days = 20           # minimum base length

# === 3. Detect bubbles (BB width spikes) ===
btc['Bubble'] = btc['BB_width'] > bb_bubble_threshold
bubble_starts = btc.index[(btc['Bubble'] & ~btc['Bubble'].shift(1).fillna(False))].tolist()

foundations = []

# === 4. Loop bubbles to find Calm A -> Breakout B and regression ===
for i in range(len(bubble_starts)-1):
    bubble_start = bubble_starts[i]
    calm_A_idx = bubble_start + calm_offset
    if calm_A_idx >= len(btc): continue

    next_bubble_start = bubble_starts[i+1]
    if next_bubble_start <= calm_A_idx: continue

    A_date = btc.loc[calm_A_idx, 'ds']
    B_date = btc.loc[next_bubble_start, 'ds']

    # Slice flat base region (A to just before B)
    base_df = btc.iloc[calm_A_idx:next_bubble_start]

    if len(base_df) < min_base_days:
        continue

    # Regression Fit (A->B)
    X = np.arange(len(base_df)).reshape(-1, 1)
    y = base_df['y'].values.reshape(-1, 1)
    model = LinearRegression().fit(X, y)
    slope = model.coef_[0][0]
    r2 = model.score(X, y)
    y_pred = model.predict(X).flatten()

    # Check flat & solid
    if abs(slope) < slope_threshold and r2 > r2_threshold:
        foundations.append({
            'A_idx': calm_A_idx,
            'B_idx': next_bubble_start,
            'A_date': A_date,
            'B_date': B_date,
            'y_pred': y_pred,
            'base_df': base_df
        })

# === 5. Plot ===
fig = go.Figure()

# BTC Close
fig.add_trace(go.Scatter(x=btc['ds'], y=btc['y'], mode='lines', name='BTC Close', line=dict(color='royalblue')))

# Bollinger Bands
fig.add_trace(go.Scatter(x=btc['ds'], y=btc['BB_upper'], name='BB Upper', line=dict(color='gray', dash='dot')))
fig.add_trace(go.Scatter(x=btc['ds'], y=btc['BB_lower'], name='BB Lower', line=dict(color='gray', dash='dot')))

# Bubble zones & markers
for b_idx in bubble_starts:
    fig.add_vrect(
        x0=btc.loc[b_idx, 'ds'], 
        x1=btc.loc[min(b_idx+5, len(btc)-1), 'ds'], 
        fillcolor="rgba(255,0,0,0.1)", line_width=0
    )
    fig.add_trace(go.Scatter(
        x=[btc.loc[b_idx, 'ds']],
        y=[btc.loc[b_idx, 'y']],
        mode='markers',
        marker=dict(color='purple', size=10, symbol='diamond'),
        name='Oval Bubble Start'
    ))

# Flat Foundations (Regression Lines A->B)
for f in foundations:
    fig.add_trace(go.Scatter(
        x=f['base_df']['ds'], 
        y=f['y_pred'],
        mode='lines',
        name=f"Foundation {f['A_date'].strftime('%b %Y')}",
        line=dict(color='green', width=2)
    ))
    # Mark Calm A and Breakout B
    fig.add_trace(go.Scatter(
        x=[f['A_date']], y=[f['base_df']['y'].iloc[0]],
        mode='markers', marker=dict(color='orange', size=10, symbol='circle'), name='Calm A'
    ))
    fig.add_trace(go.Scatter(
        x=[f['B_date']], y=[btc.loc[f['B_idx'], 'y']],
        mode='markers', marker=dict(color='red', size=10, symbol='triangle-up'), name='Breakout B'
    ))

fig.update_layout(
    title="BTC: Flat Base (A→B) Foundations Before Breakout",
    xaxis_title="Date", yaxis_title="Price (USD)",
    template="plotly_white",
    hovermode="x unified"
)

fig.show()
