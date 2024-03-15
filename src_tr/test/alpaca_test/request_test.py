import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockQuotesRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.models.bars import BarSet
import pandas as pd
from pandas import DataFrame
from config import config


load_dotenv()

ALPACA_KEY = os.environ["ALPACA_KEY"]
ALPACA_SECRET_KEY = os.environ["ALPACA_SECRET_KEY"]

client = StockHistoricalDataClient(ALPACA_KEY, ALPACA_SECRET_KEY)

#symbol = ["COIN", "MARA", "AAPL", "TSLA"]

def download_quotes_data_for_trading_day(trading_day='2024_03_12', run_id='E-RSI_10-MACD16_6_3--C-AVG_5-RSI_70', agg_time_frame='10S'):
    timeframe = TimeFrame(amount=1, unit=TimeFrameUnit.Minute)
    for symbol in [f.split('_')[0] for f in
                   os.listdir(f"{config['output_stats']}/{run_id}/{run_id}_{trading_day}/daily_files/csvs") if run_id in f]:
        print(f'Dowloading order book data for {symbol} in {agg_time_frame}, time window.')
        quotes_request = StockQuotesRequest(
            symbol_or_symbols=['AAPL', 'BAC'],
            timeframe=timeframe,
            start=datetime.strptime(trading_day, '%Y_%m_%d') + timedelta(hours=17) + timedelta(minutes=30),
            end=datetime.strptime(trading_day, '%Y_%m_%d') + timedelta(hours=17) + timedelta(minutes=31)
        )

        quotes = client.get_stock_quotes(quotes_request)#.data

        df = pd.DataFrame.from_dict([dict(e) for e in quotes[symbol]])
        # df.drop(['symbol', 'tape', 'conditions'], axis=1, inplace=True)
        # df.set_index('timestamp', inplace=True)
        #
        # df=df.groupby(['ask_exchange', 'bid_exchange', pd.Grouper(freq=agg_time_frame)]).agg({'ask_price': 'mean',
        #                                                                          'ask_size': 'sum',
        #                                                                          'bid_price': 'mean',
        #                                                                          'bid_size': 'sum'}).reset_index()
        # df = df[['timestamp', 'ask_exchange', 'ask_size', 'ask_price', 'bid_exchange', 'bid_size', 'bid_price']]
        # df.sort_values('timestamp', inplace=True)
        df.to_csv(f"{config['output_stats']}/{run_id}/{run_id}_{trading_day}/daily_files/csvs/{symbol}_2024_03_12_quotes_raw.csv", index=False)

trading_day='2024_03_12'
run_id='E-RSI_10-MACD16_6_3--C-AVG_5-RSI_70'
df = pd.read_csv(f"{config['output_stats']}/{run_id}/{run_id}_{trading_day}/daily_files/csvs/AAPL_2024_03_12_quotes_raw.csv")





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
            quotes_df.to_csv(f"{key}_quotes.csv", index=True)
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
