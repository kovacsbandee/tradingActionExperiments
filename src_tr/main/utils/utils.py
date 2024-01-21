from datetime import datetime, timedelta
import pandas as pd

'''
 itt lehetne egy get_dates() metódus, ami visszadja a trading_day-t és a scanning_day-t a megfelelő ellenőrzésekkel,
'''

def calculate_scanning_day(trading_day: datetime) -> datetime:
    '''
    If the previous day is sunday it returns the date for friday as a scanning day
    '''
    previous_day = (trading_day - timedelta(days=1)).strftime('%A')
    if previous_day == 'Sunday':
        return trading_day - timedelta(days=3)
    else:
        return trading_day - timedelta(days=1)

def get_nasdaq_symbols(file_path: str=None) -> list:
    '''
    Reads in a csv file downloaded from: https://www.nasdaq.com/market-activity/stocks/screener
    and stored in the project directory in src_tr/main/data_sources. The file_path is an environmental variable.
    returns: a list of the unique Symbols
    '''
    if not file_path:
        raise ValueError(f"No files found with path '{file_path}'")
    daily_nasdaq_symbols = pd.read_csv(f'{file_path}')
    #daily_nasdaq_symbols['Last Sale'] = daily_nasdaq_symbols['Last Sale'].str.lstrip('$').astype(float)
    # itt direkt van egy szűrés azokra a symbol-ekre, amiknek nincs vagy nulla a kapitalizációjuk
    daily_nasdaq_symbols = daily_nasdaq_symbols[(~daily_nasdaq_symbols['Market Cap'].isna()) & \
                                                 (daily_nasdaq_symbols['Market Cap'] != 0.0)]
    return list(daily_nasdaq_symbols['Symbol'].unique())