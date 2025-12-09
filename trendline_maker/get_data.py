# trendline_maker/get_data.py

import pandas as pd
import yfinance as yf
from datetime import datetime


def load_csv_from_drive(file_id):
    """Load CSV from Google Drive file ID."""
    csv_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    df = pd.read_csv(csv_url, on_bad_lines="warn")

    df["time"] = pd.to_datetime(df.index)
    df["time_str"] = df["time"].dt.strftime("%Y-%m-%d")
    df["loc_index"] = range(len(df))
    return df


def load_yf(symbol, start, end):
    """Load OHLC data from Yahoo Finance."""
    df = yf.Ticker(symbol).history(interval="1d", prepost=False, start=start, end=end)
    df["time"] = df.index
    df["time_str"] = df["time"].dt.strftime("%Y-%m-%d")
    df["loc_index"] = range(len(df))
    return df
