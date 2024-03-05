from typing import List
from datetime import datetime, date
import os
import traceback
import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.enums import DataFeed

from config import config

def load_MACD_days_polygon_data(symbol: str, macd_date_list: List[date]) -> pd.DataFrame:
    try:
        symbol_history_df = None
        for date in macd_date_list:
            date = date.strftime('%Y_%m_%d')
            daily_df = pd.read_csv(
                os.path.join(config["resource_paths"]["polygon"]["daily_data_output_folder"], date, f"{symbol}.csv"))
            daily_df.columns = ["timestamp","open","close","volume","high","low","volume_weighted_avg_price","transactions"]
            if symbol_history_df is None:
                symbol_history_df = daily_df
            elif isinstance(symbol_history_df, pd.DataFrame):
                symbol_history_df = pd.concat([symbol_history_df, daily_df], ignore_index=True)
        timestamps_conv = pd.to_datetime(symbol_history_df['timestamp'], format="%Y-%m-%d %H:%M:%S%z", utc=True)
        symbol_history_df['date'] = timestamps_conv.dt.date
        return symbol_history_df
    except:
        traceback.print_exc()
        return None
    
def download_scanning_day_alpaca_data(symbol: str, alpaca_key: str, alpaca_secret_key: str,
                                      start: date, end: date) -> pd.DataFrame:
    client = StockHistoricalDataClient(alpaca_key, alpaca_secret_key)
    symbol = [symbol]
    timeframe = TimeFrame(amount=1, unit=TimeFrameUnit.Minute)
    bars_request = StockBarsRequest(
        start=start,
        symbol_or_symbols=symbol,
        timeframe=timeframe,
        end=end
    )
    latest_bars = client.get_stock_bars(bars_request)
    if latest_bars.data:
        latest_bars = latest_bars.df
        latest_bars = latest_bars.droplevel(level=0)
        latest_bars.reset_index(inplace=True)
        latest_bars['timestamp'] = pd.DatetimeIndex(pd.to_datetime(latest_bars['timestamp'], utc=True)).tz_convert('US/Eastern')
        latest_bars['date'] = latest_bars['timestamp'].dt.date
        latest_bars.set_index('timestamp', inplace=True)
        latest_bars = latest_bars.rename(columns={
            'trade_count': 'transactions',
            'vwap': 'volume_weighted_avg_price'
        })
        start_time = datetime.strptime('09:30:00', '%H:%M:%S').time()
        end_time = datetime.strptime('16:00:00', '%H:%M:%S').time()
        latest_bars = latest_bars.between_time(start_time, end_time)
        print(f"Downloaded {symbol} at {datetime.now()}" )
        return latest_bars
    else:
        print(f"No data available for {symbol}")
        return None

    