from typing import List
import time
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import logging

from src_tr.test.polygon_test.split_data_by_day import split_data_by_day
from src_tr.main.data_sources.nasdaq_symbols import nasdaq_symbols

global_request_counter = 0

def download_aggs(symbol: str, from_: str, to: str) -> List[dict]:
    global global_request_counter
    if symbol is not None and isinstance(symbol, str):
        if '/' in symbol:
            symbol = symbol.replace("/", ".")
        url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/minute/{from_}/{to}?adjusted=true&sort=asc&limit=50000&apiKey=nAFDGVldylM4uZBcWzaTYT5RKg9PZqYm"
        session = requests.Session()
        retry = Retry(connect=3, total=5, backoff_factor=60)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        response = session.get(url)
        if response.status_code == 200:
            data_dict = json.loads(response.text)
            if data_dict is not None and 'results' in data_dict:
                return data_dict['results']
            else:
                logging.error(f"No available bar data for %s between %s and %s", symbol, from_, to)
                global_request_counter+=1
                return None
        else:
            no_api_key_url = url.split("&apiKey")
            logging.error(f"%s %s at URL: %s", response.status_code, response.reason, no_api_key_url[0])
            global_request_counter+=1
            return None
    else:
        global_request_counter += 1
        return None
    
def get_bar_data(symbol: str, from_: str, to: str):
    global global_request_counter
    aggregate_list = download_aggs(symbol, from_, to)
    if aggregate_list is not None and len(aggregate_list) > 0:
        try:
            df = pd.DataFrame.from_records(aggregate_list)
            if not df.empty:
                df.columns = ['volume', 'volume_weighted_avg_price', 'open', 'close', 'high', 'low', 'timestamp', 'transactions']
                df['timestamp'] = pd.DatetimeIndex(pd.to_datetime(df['timestamp'], utc=True, unit='ms')).tz_convert('US/Eastern')
                df['symbol'] = symbol
                return df
            else:
                logging.error(f"Empty DataFrame - symbol: %s", symbol)
                global_request_counter += 1
        except Exception as ex:
            logging.error(f"%s in file: %s, line %s", ex, __file__)
            global_request_counter += 1
    else:
        global_request_counter += 1
        return None

def create_csvs_by_symbol(symbol_list: list, from_: str, to: str):
    global global_request_counter
    for symbol in symbol_list:
        if global_request_counter < 5:
            symbol_df = get_bar_data(symbol, from_, to)
            if symbol_df is not None and not symbol_df.empty:
                split_data_by_day(full_symbol_df=symbol_df, filter_length=None, limit_to_market_open=False)
                global_request_counter+=1
        else:
            time.sleep(61)
            global_request_counter = 0

#create_csvs_by_symbol(nasdaq_symbols, "2023-01-26", "2023-04-03")

if __name__ == '__main__':
    create_csvs_by_symbol(nasdaq_symbols, "2023-04-04", "2023-07-03")

#create_csvs_by_symbol(nasdaq_symbols, "2023-07-04", "2023-10-02")
#create_csvs_by_symbol(nasdaq_symbols, "2023-10-03", "2023-12-31")
#create_csvs_by_symbol(nasdaq_symbols, "2024-01-01", "2024-01-26")
