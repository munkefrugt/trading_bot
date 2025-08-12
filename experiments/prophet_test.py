from prophet import Prophet
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go

# Download BTC-USD data from Yahoo
btc = yf.download("BTC-USD", start="2021-10-25", end="2023-10-25", interval="1d")
btc = btc.reset_index()
btc['ds'] = btc['Date']
btc['y'] = btc['Close']

# Keep only Prophet-compatible columns
df = btc[['ds', 'y']]

# Fit model
model = Prophet(daily_seasonality=True)
model.fit(df)

# Forecast (next 1 day)
future = model.make_future_dataframe(periods=7) 
forecast = model.predict(future)

# === Plotly Plot ===
fig = go.Figure()

# BTC Close line
fig.add_trace(go.Scatter(x=df['ds'], y=df['y'], mode='lines', name='BTC Close'))

# Prophet forecast line
fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], mode='lines', name='Prophet Forecast', line=dict(dash='dash')))

# Add "Today" marker
fig.add_trace(go.Scatter(
    x=[df['ds'].iloc[-1]],
    y=[df['y'].iloc[-1]],
    mode='markers',
    marker=dict(color='gray', size=8),
    name='Today'
))

# Layout
fig.update_layout(
    title='BTC-USD: Close vs Prophet Forecast (2021-2023)',
    xaxis_title='Date',
    yaxis_title='Price (USD)',
    hovermode='x unified',
    template='plotly_white'
)

fig.show()
