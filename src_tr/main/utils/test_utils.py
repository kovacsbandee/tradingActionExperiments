import pandas as pd
import json
from datetime import datetime
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest

from config import config


def download_daily_data_base(symbol, start, end, alpaca_key, alpaca_secret_key):
    client = StockHistoricalDataClient(alpaca_key, alpaca_secret_key)
    timeframe = TimeFrame(amount=1, unit=TimeFrameUnit.Minute)

    bars_request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=timeframe,
        start=start,
        end=end
    )
    latest_bars = client.get_stock_bars(bars_request).data
    daily_data_list = _convert_data_base(latest_bars, symbol)
    return daily_data_list


def _convert_data_base(latest_bars: dict, symbol: str):
    bar_list = []
    for e in latest_bars[symbol]:
        bar_list.append({
            'T': 'b',
            't': e.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'S': e.symbol,
            'o': e.open,
            'c': e.close,
            'h': e.high,
            'l': e.low,
            'v': e.volume,
            'n': e.trade_count
        })
    return bar_list


def get_all_symbols_daily_data_base(recommended_symbol_list, s, e, alpaca_key, alpaca_secret_key):
    all_symbols_daily_data = list()
    for symbol in recommended_symbol_list:
        daily_data = download_daily_data_base(symbol=symbol['symbol'], start=s, end=e, alpaca_key=alpaca_key, alpaca_secret_key=alpaca_secret_key)
        all_symbols_daily_data.append(daily_data)
    return all_symbols_daily_data


def get_yf_local_db_symbols(start):
    file = open(f"{config['db_path']}/daywise_common_files.json")
    data = file.readlines()
    file.close()
    daywise_common_files = [json.loads(l) for l in data]
    days_and_file_names = [d for d in daywise_common_files if start.strftime('%Y_%m_%d') in d['day']][0]
    scanning_day_parts =  days_and_file_names['prev_day'].split('_')
    scanning_day = datetime.strptime(scanning_day_parts[-3] + scanning_day_parts[-2] + scanning_day_parts[-1], '%Y%m%d')
    yahoo_symbols = [file.split('.')[0] for file in days_and_file_names['common_files']]
    return scanning_day, yahoo_symbols

def _convert_yf_db_data_yf_db(latest_bars: dict, symbol: str):
    bar_list = []
    for e in latest_bars[symbol]:
        bar_list.append({
        'T': 'b',
        't': e['timestamp'].strftime('%Y-%m-%dT%H:%M:%SZ'),
        'S': e['symbol'],
        'o': e['open'],
        'c': e['close'],
        'h': e['high'],
        'l': e['low'],
        'v': e['volume'],
        'n': e['trade_count']
    })
    return bar_list

def download_daily_data_yf_db(symbol, start):
    latest_bars = pd.read_csv(f"{config['db_path']}/daywise_database/stock_prices_for_{start.strftime('%Y_%m_%d')}/csvs/{symbol}.csv")
    latest_bars['timestamp'] = pd.to_datetime(latest_bars['Datetime'])
    latest_bars['symbol'] = symbol
    latest_bars['trade_count'] = latest_bars['volume']
    latest_bars['vwap'] = latest_bars['open']
    latest_bars = {symbol: latest_bars.to_dict('records')}
    daily_data_list = _convert_yf_db_data_yf_db(latest_bars, symbol)
    return daily_data_list

def get_all_symbols_daily_data_yf_db(recommended_symbol_list, s):
    all_symbols_daily_data = list()
    for symbol in recommended_symbol_list:
        daily_data = download_daily_data_yf_db(symbol=symbol['symbol'], start=s)
        all_symbols_daily_data.append(daily_data)
    return all_symbols_daily_data

def run_test_experiment(all_symbols_daily_data, trading_manager):
    i = 0
    while i < len(all_symbols_daily_data[0]):
        minute_bars = []
        for symbol_daily_data in all_symbols_daily_data:
            minute_bars.append(symbol_daily_data[i])
        trading_manager.handle_message(ws=None, message=minute_bars)
        minute_bars = []
        i += 1