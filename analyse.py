import pandas as pd



def compute_ema(data, period=200, column='Close'):
    """
    Compute Exponential Moving Average (EMA) for the given column.
    """
    return data[column].ewm(span=period, adjust=False).mean()

def compute_ichimoku(data):
    """
    Compute Ichimoku Cloud components.
    """
    ichimoku = pd.DataFrame(index=data.index)

    high_9 = data['High'].rolling(window=9).max()
    low_9 = data['Low'].rolling(window=9).min()
    ichimoku['Tenkan_sen'] = (high_9 + low_9) / 2

    high_26 = data['High'].rolling(window=26).max()
    low_26 = data['Low'].rolling(window=26).min()
    ichimoku['Kijun_sen'] = (high_26 + low_26) / 2

    ichimoku['Senkou_span_A'] = ((ichimoku['Tenkan_sen'] + ichimoku['Kijun_sen']) / 2).shift(26)

    high_52 = data['High'].rolling(window=52).max()
    low_52 = data['Low'].rolling(window=52).min()
    ichimoku['Senkou_span_B'] = ((high_52 + low_52) / 2).shift(26)

    ichimoku['Chikou_span'] = data['Close'].shift(-26)

    return ichimoku

def extend_index(df, future_days=26):
    """
    Extend a DataFrame's index with future periods to hold forward-shifted indicators.
    """
    df_extended = df.copy()
    last_date = df.index[-1]
    freq = df.index.inferred_freq or pd.infer_freq(df.index)
    if freq is None:
        freq = pd.Timedelta(df.index[1] - df.index[0])  # fallback

    if isinstance(freq, str) and not any(char.isdigit() for char in freq):
        freq = '1' + freq  # Add '1' in front if no number
    start = last_date + pd.to_timedelta(freq)    
    new_dates = pd.date_range(start=start, periods=future_days, freq=freq)
    extension = pd.DataFrame(index=new_dates)
    return pd.concat([df_extended, extension])

def compute_heikin_ashi(data):
    ha = pd.DataFrame(index=data.index)
    ha['Close'] = (data['Open'] + data['High'] + data['Low'] + data['Close']) / 4

    ha['Open'] = 0.0
    ha.iloc[0, ha.columns.get_loc('Open')] = (data['Open'].iloc[0] + data['Close'].iloc[0]) / 2  # seed first open

    for i in range(1, len(data)):
        ha.iloc[i, ha.columns.get_loc('Open')] = (ha.iloc[i-1]['Open'] + ha.iloc[i-1]['Close']) / 2

    # Use HA open/close in high/low calc
    ha['High'] = pd.concat([data['High'], ha['Open'], ha['Close']], axis=1).max(axis=1)
    ha['Low'] = pd.concat([data['Low'], ha['Open'], ha['Close']], axis=1).min(axis=1)

    return ha

