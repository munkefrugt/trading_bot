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

def extend_index(df, extra_periods=26):
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
    new_dates = pd.date_range(start=start, periods=extra_periods, freq=freq)
    extension = pd.DataFrame(index=new_dates)
    return pd.concat([df_extended, extension])