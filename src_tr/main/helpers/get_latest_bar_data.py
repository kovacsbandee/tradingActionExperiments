import os
from datetime import datetime
from dotenv import load_dotenv
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.models.bars import BarSet
import pandas as pd
from pandas import DataFrame

def get_latest_bar_data(alpaca_key, alpaca_secret_key, input_symbol):

    client = StockHistoricalDataClient(alpaca_key, alpaca_secret_key)

    symbol = [input_symbol]
    timeframe = TimeFrame(amount=1, unit=TimeFrameUnit.Minute)

    bars_request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=timeframe
    )

    latest_bars = client.get_stock_bars(bars_request)
    return convert(latest_bars.df)

def convert(latest_bars: DataFrame):
    # Reset the index to move the 'symbol' and 'timestamp' to columns
    df = latest_bars.reset_index()

    # Rename the columns to match the desired format
    df = df.rename(columns={
        'timestamp': 't',
        'symbol': 'S',
        'open': 'o',
        'high': 'h',
        'low': 'l',
        'close': 'c',
        'volume': 'v',
        'trade_count': 'n',
        'vwap': 'vw'
    })

    # Add 'b' to a new column 'T' to match the format
    df['T'] = 'b'
    df['t'] = df['t'].dt.strftime('%Y-%m-%dT%H:%M:%SZ')

    # Set the 't' column as the new index
    df = df.set_index('t')
    return df.tail(12)

#print(convert(latest_bars.df))
