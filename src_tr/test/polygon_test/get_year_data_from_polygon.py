from typing import List
import os
import time
from dotenv import load_dotenv
from src_tr.main.utils.utils import get_nasdaq_symbols
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json

from src_tr.test.polygon_test.split_data_by_day import split_data_by_day

load_dotenv()
SYMBOL_CSV_PATH = os.environ["SYMBOL_CSV_PATH"]
nasdaq_symbols = get_nasdaq_symbols(file_path=SYMBOL_CSV_PATH)

def download_aggs(symbol: str, from_: str, to: str) -> List[dict]:
    if symbol is not None and isinstance(symbol, str) and '/' in symbol:
        symbol = symbol.replace("/", ".")
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/minute/{from_}/{to}?adjusted=true&sort=asc&limit=50000&apiKey=Rdcy29x7wooeMAlqKIsnTfDiHOaz0J_d"
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
        'transactions' : minute_data['n']
        }

def get_bar_data(symbol: str, from_: str, to: str):
    aggregate_list = download_aggs(symbol, from_, to)
    if aggregate_list is not None and len(aggregate_list) > 0:
        try:
            df = pd.DataFrame.from_records(aggregate_list)
            df.columns = ['volume', 'volume_weighted_avg_price', 'open', 'close', 'high', 'low', 'timestamp', 'transactions']
            df['timestamp'] = pd.DatetimeIndex(pd.to_datetime(df['timestamp'], utc=True, unit='ms')).tz_convert('US/Eastern')
            df['symbol'] = symbol
            return df
        except Exception as ex:
            print(f'Error: {ex}')
    else:
        return None

def create_csvs_by_symbol(symbol_list: list, from_: str, to: str):
    counter = 0
    for symbol in symbol_list:
        if counter < 5:
            symbol_df = get_bar_data(symbol, from_, to)
            split_data_by_day(symbol_df)
            counter+=1
        else:
            time.sleep(61)
            counter = 0
            

create_csvs_by_symbol(nasdaq_symbols, "2023-01-26", "2023-04-03")
create_csvs_by_symbol(nasdaq_symbols, "2023-04-04", "2023-07-03")
create_csvs_by_symbol(nasdaq_symbols, "2023-07-04", "2023-10-02")
create_csvs_by_symbol(nasdaq_symbols, "2023-10-03", "2023-12-01")
create_csvs_by_symbol(nasdaq_symbols, "2024-01-01", "2024-01-26")