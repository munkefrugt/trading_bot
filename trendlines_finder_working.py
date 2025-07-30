import yfinance as yf
import pandas as pd
import numpy as np
from prophet import Prophet
from sklearn.linear_model import LinearRegression
from scipy.signal import argrelextrema
import plotly.graph_objects as go

# Step 1: Download BTC-USD data
btc = yf.download("BTC-USD", start="2022-10-25", end="2023-10-25", interval="1d").reset_index()
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
from scipy.signal import find_peaks
elbows, _ = find_peaks(np.abs(btc['acceleration']), height=np.nanstd(btc['acceleration']) * 1.2, distance=20)
btc['segment'] = 0
for i, idx in enumerate(elbows):
    btc.loc[idx:, 'segment'] = i + 1

# Step 5: Find confirmed local extrema
def find_confirmed_extrema(y, order=3):
    values = y.values
    length = len(values)
    maxima = argrelextrema(values, np.greater_equal, order=order)[0]
    minima = argrelextrema(values, np.less_equal, order=order)[0]

    # Only keep extrema that have enough data before and after to be truly confirmed
    maxima = [idx for idx in maxima if order <= idx < length - order]
    minima = [idx for idx in minima if order <= idx < length - order]

    return maxima, minima


channels = []
breakouts = []

# Step 6: Compute channel per segment with extrema check
def compute_confirmed_channel(seg_df):
    if len(seg_df) < 20:
        return None

    maxima, minima = find_confirmed_extrema(seg_df['y'])

    if len(maxima) < 2 and len(minima) < 2:
        return None  # Not enough structure to form lines

    x = np.arange(len(seg_df)).reshape(-1, 1)
    y = seg_df['y'].values
    reg = LinearRegression().fit(x, y)
    base = reg.predict(x)
    residuals = y - base

    # Use only residuals at confirmed extrema to build envelope
    top_resid = [residuals[i] for i in maxima]
    bot_resid = [residuals[i] for i in minima]

    # Require at least 2 extrema to establish valid envelope
    if len(top_resid) >= 2:
        top_outer = base + max(top_resid)
        top_inner = base + np.percentile(top_resid, 75)
    else:
        top_outer = top_inner = np.full_like(base, np.nan)

    if len(bot_resid) >= 2:
        bottom_outer = base + min(bot_resid)
        bottom_inner = base + np.percentile(bot_resid, 25)
    else:
        bottom_outer = bottom_inner = np.full_like(base, np.nan)

    # Detect breakouts (if price is beyond any defined outer band)
    for i, row in seg_df.iterrows():
        if not np.isnan(top_outer[i - seg_df.index[0]]) and row.y > top_outer[i - seg_df.index[0]]:
            breakouts.append({'ds': row.ds, 'y': row.y, 'type': 'breakout_up'})
        if not np.isnan(bottom_outer[i - seg_df.index[0]]) and row.y < bottom_outer[i - seg_df.index[0]]:
            breakouts.append({'ds': row.ds, 'y': row.y, 'type': 'breakout_down'})

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

for _, seg in btc.groupby('segment'):
    result = compute_confirmed_channel(seg)
    if result:
        channels.append(result)

# Step 7: Plot with Plotly
fig = go.Figure()
fig.add_trace(go.Scatter(x=btc['ds'], y=btc['y'], mode='lines', name='BTC Close', line=dict(color='royalblue')))
fig.add_trace(go.Scatter(x=btc['ds'], y=btc['trend'], mode='lines', name='Prophet Forecast', line=dict(dash='dash', color='orange')))

for ch in channels:
    fig.add_trace(go.Scatter(x=ch['x'], y=ch['top_outer'], mode='lines', name=f"{ch['label']} top outer", line=dict(dash='dash', color='green')))
    fig.add_trace(go.Scatter(x=ch['x'], y=ch['bottom_outer'], mode='lines', name=f"{ch['label']} bottom outer", line=dict(dash='dash', color='red')))
    fig.add_trace(go.Scatter(x=ch['x'], y=ch['top_inner'], mode='lines', name=f"{ch['label']} top inner", line=dict(dash='dot', color='green')))
    fig.add_trace(go.Scatter(x=ch['x'], y=ch['bottom_inner'], mode='lines', name=f"{ch['label']} bottom inner", line=dict(dash='dot', color='red')))

# Breakout markers
if breakouts:
    bdf = pd.DataFrame(breakouts)
    up = bdf[bdf['type'] == 'breakout_up']
    down = bdf[bdf['type'] == 'breakout_down']
    fig.add_trace(go.Scatter(x=up['ds'], y=up['y'], mode='markers', name='Breakout ↑', marker=dict(color='green', size=10, symbol='triangle-up')))
    fig.add_trace(go.Scatter(x=down['ds'], y=down['y'], mode='markers', name='Breakout ↓', marker=dict(color='red', size=10, symbol='triangle-down')))

fig.update_layout(
    title="BTC-USD with Validated Trend Channels and Logical Breakout Detection",
    xaxis_title="Date",
    yaxis_title="Price (USD)",
    legend=dict(font=dict(size=9)),
    template='plotly_white',
    height=600
)

fig.show()
