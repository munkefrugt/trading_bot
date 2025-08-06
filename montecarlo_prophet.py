import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout

# -------------------------------
# 1. Download Stock Data
# -------------------------------
ticker = "AAPL"  # <-- Change to your stock symbol
df = yf.download(ticker, start="2020-01-01", end="2024-01-01")
prices = df[['Close']].values

# Normalize data (LSTM performs better with scaled input)
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_prices = scaler.fit_transform(prices)

# -------------------------------
# 2. Prepare Training Data
# -------------------------------
lookback = 60  # number of past days to use for prediction
X, y = [], []
for i in range(lookback, len(scaled_prices)):
    X.append(scaled_prices[i-lookback:i, 0])
    y.append(scaled_prices[i, 0])
X, y = np.array(X), np.array(y)
X = np.reshape(X, (X.shape[0], X.shape[1], 1))  # reshape for LSTM [samples, timesteps, features]

# -------------------------------
# 3. Build LSTM Model with Dropout
# -------------------------------
model = Sequential()
model.add(LSTM(50, return_sequences=True, input_shape=(X.shape[1], 1)))
model.add(Dropout(0.2))  # Dropout for Monte Carlo
model.add(LSTM(50))
model.add(Dropout(0.2))  # Dropout for Monte Carlo
model.add(Dense(1))  # Output layer
model.compile(optimizer='adam', loss='mean_squared_error')
model.fit(X, y, epochs=20, batch_size=32, verbose=1)

# -------------------------------
# 4. Monte Carlo Dropout Predictions
# -------------------------------
future_days = 30  # how many days to predict forward
mc_samples = 200  # number of Monte Carlo simulations

last_sequence = scaled_prices[-lookback:]  # last 60 days for seed
predictions_mc = []

for s in range(mc_samples):
    seq = last_sequence.copy()
    future_preds = []
    for _ in range(future_days):
        X_pred = np.reshape(seq, (1, lookback, 1))
        pred = model(X_pred, training=True).numpy()[0, 0]  # <-- Keep dropout active
        future_preds.append(pred)
        seq = np.vstack([seq[1:], [[pred]]])  # slide window forward
    predictions_mc.append(future_preds)

predictions_mc = np.array(predictions_mc)
mean_pred = predictions_mc.mean(axis=0)
low_pred = np.percentile(predictions_mc, 10, axis=0)  # 10% lower bound
high_pred = np.percentile(predictions_mc, 90, axis=0)  # 90% upper bound

# -------------------------------
# 5. Plot Results
# -------------------------------
plt.figure(figsize=(12, 6))
plt.plot(df.index, prices, label="Historical Price", color='black')

# Create future date index
future_dates = pd.date_range(start=df.index[-1], periods=future_days+1, freq='B')[1:]

# Plot mean prediction and uncertainty band
plt.plot(future_dates, scaler.inverse_transform(mean_pred.reshape(-1, 1)), label="LSTM MC Mean Prediction", color='blue')
plt.fill_between(future_dates,
                 scaler.inverse_transform(low_pred.reshape(-1, 1)).flatten(),
                 scaler.inverse_transform(high_pred.reshape(-1, 1)).flatten(),
                 color='red', alpha=0.2, label="Monte Carlo Uncertainty (10-90%)")

plt.title(f"{ticker} Price Forecast with LSTM + Monte Carlo Dropout")
plt.xlabel("Date")
plt.ylabel("Price (USD)")
plt.legend()
plt.show()
