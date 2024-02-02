import os
import pandas as pd
import numpy as np
from datetime import datetime
        
def split_data_by_day(full_symbol_df: pd.DataFrame, filter_length=None):
    #TODO: configból
    output_folder_path = "/home/tamkiraly/Development/tradingActionExperiments/src_tr/test/polygon_test/daily_bars"

    #NOTE: erre csak a fájlból konvertáláshoz van szükségünk, mert abban nincs timezone infó
    full_symbol_df['timestamp'] = pd.DatetimeIndex(pd.to_datetime(full_symbol_df['timestamp'], utc=True)).tz_convert('US/Eastern')
    dates = np.sort(full_symbol_df['timestamp'].dt.date.unique())

    for date in dates:
        daily_df = full_symbol_df[(full_symbol_df['timestamp'].dt.date == date)].copy()
        symbol = daily_df.symbol.unique()
        
        if symbol.size > 1:
            raise ValueError(f"Daily DataFrame contains more than 1 symbol: {symbol.tolist()}")
        else:
            symbol = symbol[0]
            date_str = date.strftime('%Y_%m_%d')
            
            daily_df.set_index('timestamp', inplace=True)
            start_time = datetime.strptime('09:30:00', '%H:%M:%S').time()
            end_time = datetime.strptime('16:00:00', '%H:%M:%S').time()
            daily_df = daily_df.between_time(start_time, end_time)
            daily_df.drop('symbol', inplace=True, axis=1)
            
            if date_str not in os.listdir(output_folder_path):
                os.mkdir(f"{output_folder_path}/{date_str}")
            
            if filter_length is None or (filter_length > 0 and daily_df.shape[0] >= filter_length):
                daily_df.to_csv(f"{output_folder_path}/{date_str}/{symbol}.csv")
        
def split_downloaded_data():
    #TODO: configból
    csv_dir = "/home/tamkiraly/Development/tradingActionExperiments/src_tr/test/polygon_test/full_bar_csvs"
    for filename in os.listdir(csv_dir):
        csv_file_path = os.path.join(csv_dir, filename)
        if os.path.isfile(csv_file_path):
            full_symbol_df = pd.read_csv(csv_file_path)
            split_data_by_day(full_symbol_df, 200)