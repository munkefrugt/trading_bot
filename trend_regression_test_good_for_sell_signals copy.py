import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- Parameters ---
window_size = 25          # initial regression window
min_r2 = 0.9              # stricter R² threshold
max_slope_change = 0.15    # max % slope deviation allowed when extending

# --- Download BTC Data ---
start_date = (datetime.today() - timedelta(days=730)).strftime("%Y-%m-%d")
end_date = datetime.today().strftime("%Y-%m-%d")
btc = yf.download("BTC-USD", start=start_date, end=end_date, interval="1d").reset_index()
btc = btc[['Date', 'Close']].dropna()
btc.columns = ['ds', 'y']
btc.reset_index(drop=True, inplace=True)

segments = []
i = 0
while i < len(btc) - window_size:
    window = btc.iloc[i:i+window_size]
    X = np.arange(len(window)).reshape(-1, 1)
    y = window['y'].values
    
    model = LinearRegression().fit(X, y)
    r2 = model.score(X, y)
    slope = model.coef_[0]
    
    if r2 >= min_r2:
        # Extend forward while trend stays valid
        j = i + window_size
        last_slope = slope
        while j < len(btc):
            X_ext = np.arange(j - i).reshape(-1, 1)
            y_ext = btc['y'].iloc[i:j].values
            model_ext = LinearRegression().fit(X_ext, y_ext)
            r2_ext = model_ext.score(X_ext, y_ext)
            slope_ext = model_ext.coef_[0]
            
            slope_change = abs((slope_ext - last_slope) / last_slope) if last_slope != 0 else 0
            if r2_ext < min_r2 or slope_change > max_slope_change:
                break
            last_slope = slope_ext
            j += 1

        seg = btc.iloc[i:j]
        X_seg = np.arange(len(seg)).reshape(-1, 1)
        model_seg = LinearRegression().fit(X_seg, seg['y'])
        seg_line = model_seg.predict(X_seg)
        segments.append((seg['ds'], seg_line))
        i = j
    else:
        i += 1

# --- Plot ---
fig = go.Figure()
fig.add_trace(go.Scatter(x=btc['ds'], y=btc['y'], mode='lines', name='BTC Close', line=dict(color='royalblue')))
for seg_dates, seg_line in segments:
    fig.add_trace(go.Scatter(x=seg_dates, y=seg_line, mode='lines', name='Trend Segment', line=dict(color='orange', width=3)))

fig.update_layout(
    title="Sharper BTC-USD Trend Detection (Regression)",
    xaxis_title="Date",
    yaxis_title="Price (USD)",
    template="plotly_white",
    height=600
)
fig.show()
