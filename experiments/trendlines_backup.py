from prophet import Prophet
import yfinance as yf
import pandas as pd
import numpy as np
from scipy.signal import argrelextrema
import plotly.graph_objs as go

# === Download BTC-USD Data ===
btc = yf.download("BTC-USD", start="2021-10-25", end="2023-10-25", interval="1d").reset_index()
if isinstance(btc.columns, pd.MultiIndex):
    btc.columns = [col[0] for col in btc.columns]

btc['ds'] = btc['Date']
btc['y'] = btc['Close']
df = btc[['ds', 'y']]

# === Fit Prophet Model ===
model = Prophet(daily_seasonality=True)
model.fit(df)

# === Forecast ===
future = model.make_future_dataframe(periods=7)
forecast = model.predict(future)

# === Merge forecast with actual BTC data ===
forecast = forecast.set_index('ds')
df = df.set_index('ds')
merged = df.join(forecast[['yhat', 'trend']]).reset_index()

# Detect trend direction changes
merged['trend_diff'] = merged['trend'].diff()
merged['trend_slope'] = np.sign(merged['trend_diff'])
merged['slope_change'] = merged['trend_slope'].ne(merged['trend_slope'].shift())
merged['segment'] = merged['slope_change'].cumsum()

# === Label slope direction ===
def get_slope_label(slope_val):
    if slope_val > 0.01:
        return "up"
    elif slope_val < -0.01:
        return "down"
    else:
        return "flat"

# === Compute trendlines per segment — clean and self-contained ===
def compute_trendlines(group):
    group = group.copy().reset_index(drop=True)  # FULL reset
    group['residual'] = group['y'] - group['yhat']

    # Local extrema
    n = 10
    local_max_idx = argrelextrema(group['residual'].values, np.greater_equal, order=n)[0]
    local_min_idx = argrelextrema(group['residual'].values, np.less_equal, order=n)[0]

    max_residuals = group.iloc[local_max_idx]['residual']
    min_residuals = group.iloc[local_min_idx]['residual']

    # Offset defaults
    upper_offset = max_residuals.mean() if len(max_residuals) >= 2 else group['residual'].max()
    lower_offset = min_residuals.mean() if len(min_residuals) >= 2 else group['residual'].min()

    # Build upper/lower trendlines
    group['upper_trend'] = group['yhat'] + upper_offset
    group['lower_trend'] = group['yhat'] + lower_offset

    # Force per-row minimum width
    min_gap = 1000
    actual_gap = group['upper_trend'] - group['lower_trend']
    too_small = actual_gap < min_gap
    mid = group['yhat']
    group.loc[too_small, 'upper_trend'] = mid[too_small] + min_gap / 2
    group.loc[too_small, 'lower_trend'] = mid[too_small] - min_gap / 2

    # Label
    start_label = group['ds'].iloc[0].strftime('%b')
    end_label = group['ds'].iloc[-1].strftime('%b %Y')
    slope = (group['trend'].iloc[-1] - group['trend'].iloc[0]) / len(group)
    slope_label = get_slope_label(slope)
    group['channel_label'] = f'{start_label}–{end_label} {slope_label}'

    return group

# === Apply clean segmentation ===
segments = []
for _, group in merged.groupby('segment'):
    if len(group) < 10:
        continue
    segment = compute_trendlines(group)
    segments.append(segment)

# Combine results
final_df = pd.concat(segments, ignore_index=True)

# === Plotting ===
fig = go.Figure()

# BTC price + Prophet line
fig.add_trace(go.Scatter(x=final_df['ds'], y=final_df['y'], mode='lines', name='BTC Close'))
fig.add_trace(go.Scatter(x=final_df['ds'], y=final_df['yhat'], mode='lines', name='Prophet Forecast', line=dict(dash='dash')))

# Add each channel separately
for label, group in final_df.groupby('channel_label'):
    fig.add_trace(go.Scatter(x=group['ds'], y=group['upper_trend'], mode='lines', name=f'{label} top', line=dict(dash='dot', color='green')))
    fig.add_trace(go.Scatter(x=group['ds'], y=group['lower_trend'], mode='lines', name=f'{label} bottom', line=dict(dash='dot', color='red')))

# Mark today's price
today_row = final_df.iloc[-1]
fig.add_trace(go.Scatter(
    x=[today_row['ds']],
    y=[today_row['y']],
    mode='markers',
    marker=dict(color='black', size=10),
    name='Today'
))

# Breakout annotation
if today_row['y'] > today_row['upper_trend']:
    fig.add_annotation(text="Breakout ↑", x=today_row['ds'], y=today_row['y'],
                       showarrow=True, arrowhead=1, font=dict(color="green"))
elif today_row['y'] < today_row['lower_trend']:
    fig.add_annotation(text="Breakout ↓", x=today_row['ds'], y=today_row['y'],
                       showarrow=True, arrowhead=1, font=dict(color="red"))

# Layout
fig.update_layout(
    title='BTC-USD with Fully Isolated Prophet Trend Channels',
    xaxis_title='Date',
    yaxis_title='Price (USD)',
    hovermode='x unified',
    template='plotly_white'
)

fig.show()

