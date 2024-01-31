from typing import List
import os
import time
from datetime import timedelta, datetime
from dotenv import load_dotenv
from src_tr.main.utils.utils import get_nasdaq_symbols
from polygon import RESTClient
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json

load_dotenv()
SYMBOL_CSV_PATH = os.environ["SYMBOL_CSV_PATH"]
nasdaq_symbols = get_nasdaq_symbols(file_path=SYMBOL_CSV_PATH)[3701:]

def download_aggs(symbol: str, from_: str, to: str) -> List[dict]:
    if symbol is not None and isinstance(symbol, str) and '/' in symbol:
        symbol = symbol.replace("/", ".")
    #url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/minute/{from_}/{to}?adjusted=true&sort=asc&limit=50000&apiKey=Rdcy29x7wooeMAlqKIsnTfDiHOaz0J_d"
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/minute/{from_}/{to}?adjusted=true&sort=asc&limit=50000&apiKey=GANzpA5mg0SY4VXg1RrBoFMUgOy11uzZ"
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=60)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    data = session.get(url).text
    data_dict = json.loads(data)
    if data_dict is not None and 'results' in data_dict:
        return data_dict['results']
    else:
        print(f"No available bar data for {symbol} between {from_} and {to}")
        return None

def format(minute_data, symbol):
    return {
        'timestamp' : minute_data['t'],
        'symbol' : symbol,
        'open' : minute_data['o'],
        'close' : minute_data['c'],
        'volume' : minute_data['v'],
        'high' : minute_data['h'],
        'low' : minute_data['l'],
        'volume_weighted_avg_price' : minute_data['vw'],
        'n' : minute_data['n']
        }

def get_bar_data(symbol: str, from_: str, to: str):
    aggs = []
    #client = RESTClient(api_key="Rdcy29x7wooeMAlqKIsnTfDiHOaz0J_d")
    #aggregate_list = client.list_aggs(symbol=symbol, multiplier=1, timespan="minute", from_=from_, to=to, limit=50000)
    aggregate_list = download_aggs(symbol, from_, to)
    if aggregate_list is not None and len(aggregate_list) > 0:
        try:
            df = pd.DataFrame.from_records(aggregate_list)
            df.columns = ['volume', 'volume_weighted_avg_price', 'open', 'close', 'high', 'low', 'timestamp', 'n']
            df['timestamp'] = pd.DatetimeIndex(pd.to_datetime(df['timestamp'], utc=True, unit='ms')).tz_convert('US/Eastern')
            df['symbol'] = symbol
        except Exception as ex:
            print(f'Error: {ex}')
            # for a in aggregate_list:
            #     #a_dict = a.__dict__
            #     a_dict = format(a, symbol)
            #     #ts = int(a.timestamp)
            #     ts = int(a_dict['timestamp']) / 1000
            #     convert_ts = datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
            #     a_dict['timestamp'] = convert_ts
            #     a_dict['symbol'] = symbol
            #     aggs.append(a_dict)
        return aggs
    else:
        return None

def create_csvs_by_symbol(symbol_list: list, from_: str, to: str):
    counter = 0
    for symbol in symbol_list:
        if counter < 5:
            symbol_df = get_bar_data(symbol, from_, to)
            # split_data_by_day

            # bar_dict_list = []
            # if data_list_per_symbol is not None and len(data_list_per_symbol) > 0:
            #     bar_dict_list = [bd for bd in data_list_per_symbol]
            #
            # if len(bar_dict_list) > 0:
            #     bar_df = pd.DataFrame(bar_dict_list)
            #     bar_df.set_index('timestamp', inplace=True)
            #     #print(bar_df)
            #     pd.DataFrame(bar_df).to_csv(f"src_tr/test/polygon_test/bar_dfs/{symbol}_{from_}_{to}.csv")
            counter+=1
        else:
            time.sleep(61)
            counter = 0

# def split_data_by_day

full_symbol_df = pd.read_csv('F:/tradingActionExperiments_database/input/polygon/bar_dfs/AAPL_2023-01-26_2023-04-03.csv')
full_symbol_df['timestamp'] = pd.DatetimeIndex(pd.to_datetime(full_symbol_df['timestamp'], utc=True)).tz_convert('US/Eastern')

dates = full_symbol_df['timestamp'].dt.date.unique()


for i, date in enumerate(dates[:-2]):
    daily_df = full_symbol_df[(full_symbol_df['timestamp'].dt.date > dates[i]) &
                              (full_symbol_df['timestamp'].dt.date < dates[i+2])].copy()


    trading_day_df = daily_df[daily_df['timestamp'] > pd.to_datetime(dates[i].strftime('%Y-%m-%d') + ' ' + '09:30:00', utc=True).tz_convert('US/Eastern')]


    date_str = date.strftime('%Y_%m_%d')
    out_symbol_name = daily_df.symbol.unique()[0]
    trading_day_df.set_index('timestamp', inplace=True)
    trading_day_df.drop('symbol', inplace=True, axis=1)
    if f'stock_prices_for_{date_str}' not in os.listdir('F:/tradingActionExperiments_database/input/polygon/daywise_database'):
        os.mkdir(f'F:/tradingActionExperiments_database/input/polygon/daywise_database/stock_prices_for_{date_str}')
    trading_day_df.to_csv(f'F:/tradingActionExperiments_database/input/polygon/daywise_database/stock_prices_for_{date_str}/{out_symbol_name}.csv')





create_csvs_by_symbol(nasdaq_symbols, "2023-01-26", "2023-04-03")
create_csvs_by_symbol(nasdaq_symbols, "2023-04-04", "2023-07-03")
create_csvs_by_symbol(nasdaq_symbols, "2023-07-04", "2023-10-02")
create_csvs_by_symbol(nasdaq_symbols, "2023-10-03", "2023-12-01")
create_csvs_by_symbol(nasdaq_symbols, "2024-01-01", "2024-01-26")
                    
#create_csvs_by_symbol(nasdaq_symbols, "2023-01-26", "2023-02-28")
#create_csvs_by_symbol(nasdaq_symbols, "2023-03-01", "2023-04-03")
#create_csvs_by_symbol(nasdaq_symbols, "2023-04-04", "2023-05-01")
#create_csvs_by_symbol(nasdaq_symbols, "2023-05-02", "2023-06-01")
#create_csvs_by_symbol(nasdaq_symbols, "2023-06-02", "2023-07-03")
#create_csvs_by_symbol(nasdaq_symbols, "2023-07-04", "2023-08-01")
#create_csvs_by_symbol(nasdaq_symbols, "2023-08-02", "2023-09-01")
#create_csvs_by_symbol(nasdaq_symbols, "2023-09-04", "2023-10-02")
#create_csvs_by_symbol(nasdaq_symbols, "2023-10-03", "2023-11-01")
#create_csvs_by_symbol(nasdaq_symbols, "2023-11-02", "2023-12-01")
            