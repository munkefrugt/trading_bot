import yfinance as yf
import pandas as pd
import numpy as np
from prophet import Prophet
from sklearn.linear_model import LinearRegression
from scipy.signal import find_peaks
import plotly.graph_objects as go

# Step 1: Download BTC-USD data
btc = yf.download("BTC-USD", start="2021-10-25", end="2023-10-25", interval="1d").reset_index()
btc = btc[['Date', 'Close']].dropna()
btc.columns = ['ds', 'y']

# Step 2: Fit Prophet model to get trend
model = Prophet(daily_seasonality=True)
model.fit(btc)
forecast = model.predict(model.make_future_dataframe(periods=0))
btc['trend'] = forecast['yhat'].values

# Step 3: Smooth the trend line and calculate slope & acceleration
btc['trend_smooth'] = btc['trend'].rolling(window=15, center=True).mean()
btc['slope'] = btc['trend_smooth'].diff()
btc['slope_smooth'] = btc['slope'].rolling(window=5, center=True).mean()
btc['acceleration'] = btc['slope_smooth'].diff()

# Step 4: Detect elbows (sudden changes in slope)
elbows, _ = find_peaks(np.abs(btc['acceleration']), height=np.nanstd(btc['acceleration']) * 1.2, distance=20)

btc['segment'] = 0
for i, idx in enumerate(elbows):
    btc.loc[idx:, 'segment'] = i + 1

# Step 5: Compute inner and outer channel lines for each segment
def compute_dual_channel(seg_df):
    if len(seg_df) < 20:
        return None
    x = np.arange(len(seg_df)).reshape(-1, 1)
    y = seg_df['y'].values
    reg = LinearRegression().fit(x, y)
    base = reg.predict(x)
    residuals = y - base
    top_inner = base + np.percentile(residuals, 75)
    bottom_inner = base + np.percentile(residuals, 25)
    top_outer = base + np.max(residuals)
    bottom_outer = base + np.min(residuals)
    start = seg_df['ds'].iloc[0].strftime('%b')
    end = seg_df['ds'].iloc[-1].strftime('%b %Y')
    label = f"{start}–{end}"
    return {
        'x': seg_df['ds'],
        'top_inner': top_inner,
        'bottom_inner': bottom_inner,
        'top_outer': top_outer,
        'bottom_outer': bottom_outer,
        'label': label
    }

channels = []
for _, seg in btc.groupby('segment'):
    result = compute_dual_channel(seg)
    if result:
        channels.append(result)

# Step 6: Plot with Plotly
fig = go.Figure()

fig.add_trace(go.Scatter(x=btc['ds'], y=btc['y'], mode='lines', name='BTC Close', line=dict(color='royalblue')))
fig.add_trace(go.Scatter(x=btc['ds'], y=btc['trend'], mode='lines', name='Prophet Forecast', line=dict(dash='dash', color='orange')))

for ch in channels:
    fig.add_trace(go.Scatter(x=ch['x'], y=ch['top_outer'], mode='lines', name=f"{ch['label']} top outer", line=dict(dash='dash', color='green')))
    fig.add_trace(go.Scatter(x=ch['x'], y=ch['bottom_outer'], mode='lines', name=f"{ch['label']} bottom outer", line=dict(dash='dash', color='red')))
    fig.add_trace(go.Scatter(x=ch['x'], y=ch['top_inner'], mode='lines', name=f"{ch['label']} top inner", line=dict(dash='dot', color='green')))
    fig.add_trace(go.Scatter(x=ch['x'], y=ch['bottom_inner'], mode='lines', name=f"{ch['label']} bottom inner", line=dict(dash='dot', color='red')))

fig.update_layout(
    title="BTC-USD with Prophet Elbow-Segmented Trend Channels",
    xaxis_title="Date",
    yaxis_title="Price (USD)",
    legend=dict(font=dict(size=9)),
    template='plotly_white',
    height=600
)

fig.show()
