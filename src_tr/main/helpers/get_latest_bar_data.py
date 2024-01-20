import os
from datetime import datetime
from dotenv import load_dotenv
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestBarRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.models.bars import BarSet
import pandas as pd
from pandas import DataFrame
import yfinance as yf

load_dotenv()

def get_alpaca_bar_data(alpaca_key, alpaca_secret_key, input_symbol):

    client = StockHistoricalDataClient(alpaca_key, alpaca_secret_key)

    symbol = [input_symbol]
    timeframe = TimeFrame(amount=1, unit=TimeFrameUnit.Minute)

    bars_request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=timeframe
        #end=datetime.now()
        #limit=12
    )
    
    latest_bars = client.get_stock_bars(bars_request)
    bar_df = convert_alpaca_data(latest_bars.df, 2000)
    bar_df.to_csv('latest_bars.csv')
    return bar_df

def convert_alpaca_data(latest_bars: DataFrame, n_last_bars):
    df = latest_bars.reset_index()

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

    df['T'] = 'b'
    df['t'] = df['t'].dt.strftime('%Y-%m-%dT%H:%M:%SZ')

    df = df.set_index('t')
    df_tail = df.tail(n_last_bars)
    return df_tail

def get_yahoo_data(symbol, start_date: datetime, end_date: datetime, n_last_bars):
    ticker = yf.Ticker(symbol)
    ticker_history = ticker.history(start=start_date, end=end_date, interval='1m', period='1d', prepost=True) if ticker else None
    converted_df = convert_yahoo_data(ticker_history, n_last_bars, symbol)
    return converted_df

def convert_yahoo_data(ticker_history: DataFrame, n_last_bars, symbol):
    ticker_history = ticker_history.reset_index()
    ticker_history['S'] = symbol

    # Rename the columns to match the desired format
    ticker_history = ticker_history.rename(columns={
        'Datetime': 't',
        'Open': 'o',
        'High': 'h',
        'Low': 'l',
        'Close': 'c',
        'Volume': 'v'
    })

    # Add 'b' to a new column 'T' to match the format
    #df['T'] = 'b'
    #df['t'] = df['t'].dt.strftime('%Y-%m-%dT%H:%M:%SZ')

    # Set the 't' column as the new index
    ticker_history = ticker_history.set_index('t')
    df_tail = ticker_history.tail(n_last_bars)
    return df_tail

#df = get_yahoo_data('AAPL', datetime(2023, 11, 10), datetime(2023, 11, 11), 10)
#df.to_csv('yahoo_bars.csv')

