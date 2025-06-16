import pandas as pd

def compute_heikin_ashi(data):
    """
    Takes OHLCV dataframe and returns Heikin-Ashi OHLC dataframe.
    """
    ha = pd.DataFrame(index=data.index)
    
    ha['Close'] = (data['Open'] + data['High'] + data['Low'] + data['Close']) / 4

    ha['Open'] = 0.0  # placeholder, filled below
    ha['High'] = 0.0
    ha['Low'] = 0.0

    for i in range(len(data)):
        if i == 0:
            ha.iat[0, ha.columns.get_loc('Open')] = (data['Open'].iloc[0] + data['Close'].iloc[0]) / 2
        else:
            ha.iat[i, ha.columns.get_loc('Open')] = (ha['Open'].iloc[i-1] + ha['Close'].iloc[i-1]) / 2

        ha.iat[i, ha.columns.get_loc('High')] = max(data['High'].iloc[i], ha['Open'].iloc[i], ha['Close'].iloc[i])
        ha.iat[i, ha.columns.get_loc('Low')] = min(data['Low'].iloc[i], ha['Open'].iloc[i], ha['Close'].iloc[i])

    return ha

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
