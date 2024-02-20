from datetime import date, timedelta
import pandas as pd

from config import config
from src_tr.main.data_sources.market_holidays import market_holidays

def check_trading_day(trading_day: date) -> date:
    if _check_market_holiday(trading_day):
        raise ValueError(f"Trading day is a market holiday.")
    if trading_day.strftime('%A') == 'Sunday' or trading_day.strftime('%A') == 'Saturday':
        raise ValueError(f"Trading day is {trading_day}. Choose a weekday.")
    else:
        return trading_day
    
def calculate_scanning_day(trading_day: date) -> date:
    scanning_day = trading_day-timedelta(days=1)
    if scanning_day.strftime('%A') == 'Sunday':
        scanning_day = trading_day-timedelta(days=3)
        if _check_market_holiday(scanning_day):
            scanning_day = scanning_day-timedelta(days=1)
    
    if _check_market_holiday(scanning_day):
        if scanning_day.strftime('%A') == 'Monday':
            scanning_day = trading_day-timedelta(days=4)
        else:
            scanning_day = trading_day-timedelta(days=2)
            
    return scanning_day

def _check_market_holiday(market_date: date):
    current_year = market_date.strftime("%Y")
    return market_date in market_holidays[current_year]

def get_nasdaq_symbols():
    file_path = config["resource_paths"]["nasdaq_symbols_csv"]
    if not file_path:
        raise ValueError(f"No files found with path '{file_path}'")
    daily_nasdaq_symbols = pd.read_csv(file_path)
    daily_nasdaq_symbols = daily_nasdaq_symbols[(~daily_nasdaq_symbols['Market Cap'].isna()) & \
                                                 (daily_nasdaq_symbols['Market Cap'] != 0.0)]
    symbol_list = list(daily_nasdaq_symbols['Symbol'].unique())
    with open(f"src_tr/main/data_sources/nasdaq_symbols.py", "w") as output:
        output.write("nasdaq_symbols = [\n")
        for i, symbol in enumerate(symbol_list):
            if i%10 == 0:
                output.write("\n")
            output.write(f"'{symbol}', ")
        output.write("]")
    return symbol_list