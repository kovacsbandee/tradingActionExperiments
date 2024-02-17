from datetime import datetime, timedelta
import pandas as pd

def calculate_scanning_day(trading_day: datetime) -> datetime:
    previous_day = (trading_day - timedelta(days=1)).strftime('%A')
    if previous_day == 'Sunday':
        return trading_day - timedelta(days=3)
    else:
        return trading_day - timedelta(days=1)

def get_nasdaq_symbols(file_path: str=None) -> list:
    if not file_path:
        raise ValueError(f"No files found with path '{file_path}'")
    daily_nasdaq_symbols = pd.read_csv(file_path)
    #daily_nasdaq_symbols['Last Sale'] = daily_nasdaq_symbols['Last Sale'].str.lstrip('$').astype(float)
    # itt direkt van egy szűrés azokra a symbol-ekre, amiknek nincs vagy nulla a kapitalizációjuk
    daily_nasdaq_symbols = daily_nasdaq_symbols[(~daily_nasdaq_symbols['Market Cap'].isna()) & \
                                                 (daily_nasdaq_symbols['Market Cap'] != 0.0)]
    return list(daily_nasdaq_symbols['Symbol'].unique())