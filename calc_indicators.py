import pandas as pd



def compute_ema(data, period=200, column='D_Close'):
    """
    Compute Exponential Moving Average (EMA) for the given column.
    """
    return data[column].ewm(span=period, adjust=False).mean()

def compute_ichimoku(data, prefix="D_", weekly=False):
    """
    Compute Ichimoku Cloud components.

    Parameters:
    - data: DataFrame with prefixed OHLC columns
    - prefix: e.g. "D_" or "W_"
    - weekly: if True, overrides prefix to "W_"
    """
    if weekly:
        prefix = "W_"

    ichimoku = pd.DataFrame(index=data.index)

    high_9 = data[f'{prefix}High'].rolling(window=9).max()
    low_9 = data[f'{prefix}Low'].rolling(window=9).min()
    ichimoku[f'{prefix}Tenkan_sen'] = (high_9 + low_9) / 2

    high_26 = data[f'{prefix}High'].rolling(window=26).max()
    low_26 = data[f'{prefix}Low'].rolling(window=26).min()
    ichimoku[f'{prefix}Kijun_sen'] = (high_26 + low_26) / 2

    ichimoku[f'{prefix}Senkou_span_A'] = (
        (ichimoku[f'{prefix}Tenkan_sen'] + ichimoku[f'{prefix}Kijun_sen']) / 2
    ).shift(26)

    high_52 = data[f'{prefix}High'].rolling(window=52).max()
    low_52 = data[f'{prefix}Low'].rolling(window=52).min()
    ichimoku[f'{prefix}Senkou_span_B'] = ((high_52 + low_52) / 2).shift(26)

    ichimoku[f'{prefix}Chikou_span'] = data[f'{prefix}Close'].shift(-26)

    return ichimoku




def compute_heikin_ashi(data, prefix="D_", weekly=False):
    """
    Compute Heikin-Ashi candles using given OHLC columns.

    Parameters:
    - data: DataFrame containing OHLC columns
    - prefix: e.g. "D_", "W_"
    - weekly: if True, sets prefix to "W_"
    Returns a DataFrame with new Heikin-Ashi columns prefixed with HA_
    """
    if weekly:
        prefix = "W_"

    ha = pd.DataFrame(index=data.index)

    ha[f'{prefix}HA_Close'] = (
        data[f'{prefix}Open'] + data[f'{prefix}High'] +
        data[f'{prefix}Low'] + data[f'{prefix}Close']
    ) / 4

    ha[f'{prefix}HA_Open'] = 0.0
    ha.iloc[0, ha.columns.get_loc(f'{prefix}HA_Open')] = (
        data[f'{prefix}Open'].iloc[0] + data[f'{prefix}Close'].iloc[0]
    ) / 2

    for i in range(1, len(data)):
        ha.iloc[i, ha.columns.get_loc(f'{prefix}HA_Open')] = (
            ha.iloc[i - 1][f'{prefix}HA_Open'] + ha.iloc[i - 1][f'{prefix}HA_Close']
        ) / 2

    ha[f'{prefix}HA_High'] = pd.concat([
        data[f'{prefix}High'], ha[f'{prefix}HA_Open'], ha[f'{prefix}HA_Close']
    ], axis=1).max(axis=1)

    ha[f'{prefix}HA_Low'] = pd.concat([
        data[f'{prefix}Low'], ha[f'{prefix}HA_Open'], ha[f'{prefix}HA_Close']
    ], axis=1).min(axis=1)

    return ha



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