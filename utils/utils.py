from datetime import datetime, timedelta
import pandas as pd

# TODO:
def save_experiment_data():
    '''
    This method saves the experiment_data dictionary into the data_store.
    :return: nothing
    '''
    pass

# TODO:
def load_experiment_data():
    '''
    This one loads the previous file!
    :return: experiment_data
    '''
    pass

def calculate_scanning_day(trading_day: datetime) -> datetime:
    if (trading_day - timedelta(days=1)).strftime('%A') == 'Sunday':
        return trading_day - timedelta(days=3)
    else:
        return trading_day - timedelta(days=1)
    
def get_nasdaq_stickers(filename: str, path: str):
    if not filename:
        raise ValueError(f"No files found with path '{path}' and filename '{filename}'")
    daily_nasdaq_stickers = pd.read_csv(f'{path}/data_store/{filename}')
    daily_nasdaq_stickers['Last Sale'] = daily_nasdaq_stickers['Last Sale'].str.lstrip('$').astype(float)
    daily_nasdaq_stickers = daily_nasdaq_stickers[(~daily_nasdaq_stickers['Market Cap'].isna()) & \
                                                  (daily_nasdaq_stickers['Market Cap'] != 0.0)]
    return list(daily_nasdaq_stickers['Symbol'].unique())