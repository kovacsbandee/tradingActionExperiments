import os
from datetime import datetime
from dotenv import load_dotenv
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockQuotesRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.models.bars import BarSet
import pandas as pd
from pandas import DataFrame

load_dotenv()

ALPACA_KEY = os.environ["ALPACA_KEY"]
ALPACA_SECRET_KEY = os.environ["ALPACA_SECRET_KEY"]

client = StockHistoricalDataClient(ALPACA_KEY, ALPACA_SECRET_KEY)

#symbol = ["COIN", "MARA", "AAPL", "TSLA"]
symbol = ["MARA"]
timeframe = TimeFrame(amount=1, unit=TimeFrameUnit.Minute)

quotes_request = StockQuotesRequest(
    symbol_or_symbols=symbol,
    timeframe=timeframe,
    start=datetime(2023, 11, 17, 9, 30),
    end=datetime(2023, 11, 17, 16, 30)
)

quotes = client.get_stock_quotes(quotes_request).data
quotes_part = {
               'MARA': quotes['MARA'][:12]
               }
#element = quotes['AAPL'][0].close
#print(element)
#print(quotes)

def convert_quotes_to_df(quotes: dict):
    quotes_df = pd.DataFrame()  # Initialize an empty DataFrame
    for key, value in quotes.items():
        for e in value:
            e_dict = {
                'timestamp': e.timestamp,
                'ask_exchange': e.ask_exchange,
                'ask_price': e.ask_price,
                'ask_size': e.ask_size,
                'bid_exchange': e.bid_exchange,
                'bid_price': e.bid_price,
                'bid_size': e.bid_size,
                'tape': e.tape,
                'symbol': key  # Include symbol in each row
            }
            # Create a DataFrame for the current element
            element_df = pd.DataFrame([e_dict])
            element_df.set_index('timestamp', inplace=True)
            
            # Concatenate the current element's DataFrame with the main DataFrame
            quotes_df = pd.concat([quotes_df, element_df])
            quotes_df.to_csv(f'{key}_quotes.csv', index=True)
    return quotes_df

            
convert_quotes_to_df(quotes_part)

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
