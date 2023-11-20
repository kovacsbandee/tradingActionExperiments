from datetime import datetime, timedelta
import pandas as pd

def calculate_scanning_day(trading_day: datetime) -> datetime:
    previous_day = (trading_day - timedelta(days=1)).strftime('%A')
    if previous_day == 'Sunday':
        return trading_day - timedelta(days=3)
    else:
        return trading_day - timedelta(days=1)
    
def get_nasdaq_stickers(file_path: str=None) -> list:
    if not file_path:
        raise ValueError(f"No files found with path '{file_path}'")
    daily_nasdaq_stickers = pd.read_csv(f'{file_path}')
    #daily_nasdaq_stickers['Last Sale'] = daily_nasdaq_stickers['Last Sale'].str.lstrip('$').astype(float)
    #daily_nasdaq_stickers = daily_nasdaq_stickers[(~daily_nasdaq_stickers['Market Cap'].isna()) & \
    #                                              (daily_nasdaq_stickers['Market Cap'] != 0.0)]
    return list(daily_nasdaq_stickers['Symbol'].unique())