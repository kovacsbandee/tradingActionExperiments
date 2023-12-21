from datetime import datetime, timedelta
import pandas as pd

'''
 itt lehetne egy get_dates() metódus, ami visszadja a trading_day-t és a scanning_day-t a program futtatásának napjára,
 ebbe kéne bele építeni a check-et is.
'''

def calculate_scanning_day(trading_day: datetime) -> datetime:
    previous_day = (trading_day - timedelta(days=1)).strftime('%A')
    if previous_day == 'Sunday':
        return trading_day - timedelta(days=3)
    else:
        return trading_day - timedelta(days=1)
    
def get_nasdaq_stickers(file_path: str=None) -> list:
    '''
    Reads in a csv file downloaded from: https://www.nasdaq.com/market-activity/stocks/screener
    and stored in the project directory in src_tr/main/data_sources. The file_path is an environmental variable.
    returns: a list of the unique Symbols
    '''
    if not file_path:
        raise ValueError(f"No files found with path '{file_path}'")
    daily_nasdaq_stickers = pd.read_csv(f'{file_path}')
    #daily_nasdaq_stickers['Last Sale'] = daily_nasdaq_stickers['Last Sale'].str.lstrip('$').astype(float)
    # itt direkt van egy szűrés azokra a sticker-ekre, amiknek nincs vagy nulla a kapitalizációjuk
    daily_nasdaq_stickers = daily_nasdaq_stickers[(~daily_nasdaq_stickers['Market Cap'].isna()) & \
                                                 (daily_nasdaq_stickers['Market Cap'] != 0.0)]
    return list(daily_nasdaq_stickers['Symbol'].unique())