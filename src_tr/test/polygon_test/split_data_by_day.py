import os
import pandas as pd

def split_data_by_day_Kovi_original():
    full_symbol_df = pd.read_csv('F:/tradingActionExperiments_database/input/polygon/bar_dfs/AAPL_2023-01-26_2023-04-03.csv')
    full_symbol_df['timestamp'] = pd.DatetimeIndex(pd.to_datetime(full_symbol_df['timestamp'], utc=True)).tz_convert('US/Eastern')

    dates = full_symbol_df['timestamp'].dt.date.unique()


    for i, date in enumerate(dates[:-2]):
        daily_df = full_symbol_df[(full_symbol_df['timestamp'].dt.date > dates[i]) &
                                (full_symbol_df['timestamp'].dt.date < dates[i+2])].copy()


        trading_day_df: pd.DataFrame = daily_df[daily_df['timestamp'] > pd.to_datetime(dates[i].strftime('%Y-%m-%d') + ' ' + '09:30:00', utc=True).tz_convert('US/Eastern')]


        date_str = date.strftime('%Y_%m_%d')
        out_symbol_name = daily_df.symbol.unique()[0]
        trading_day_df.set_index('timestamp', inplace=True)
        trading_day_df.drop('symbol', inplace=True, axis=1)
        if f'stock_prices_for_{date_str}' not in os.listdir('F:/tradingActionExperiments_database/input/polygon/daywise_database'):
            os.mkdir(f'F:/tradingActionExperiments_database/input/polygon/daywise_database/stock_prices_for_{date_str}')
        trading_day_df.to_csv(f'F:/tradingActionExperiments_database/input/polygon/daywise_database/stock_prices_for_{date_str}/{out_symbol_name}.csv')
        
def split_data_by_day(full_symbol_df: pd.DataFrame):
    #TODO: configból
    output_folder_path = "/home/tamkiraly/Development/tradingActionExperiments/src_tr/test/polygon_test/daily_bars"

    full_symbol_df['timestamp'] = pd.DatetimeIndex(pd.to_datetime(full_symbol_df['timestamp'], utc=True)).tz_convert('US/Eastern')
    dates = full_symbol_df['timestamp'].dt.date.unique()

    for i, date in enumerate(dates[:-2]):
        daily_df = full_symbol_df[(full_symbol_df['timestamp'].dt.date > dates[i]) &
                                (full_symbol_df['timestamp'].dt.date < dates[i+2])].copy()

        trading_day_df = daily_df[daily_df['timestamp'] > pd.to_datetime(dates[i].strftime('%Y-%m-%d') + ' ' + '09:30:00', utc=True).tz_convert('US/Eastern')]

        date_str = date.strftime('%Y_%m_%d')
        out_symbol_name = daily_df.symbol.unique()[0]
        trading_day_df.set_index('timestamp', inplace=True)
        trading_day_df.drop('symbol', inplace=True, axis=1)
        if date_str not in os.listdir(output_folder_path):
            os.mkdir(f"{output_folder_path}/{date_str}")
        trading_day_df.to_csv(f"{output_folder_path}/{date_str}/{out_symbol_name}.csv")
        
def split_downloaded_data():
    #TODO: configból
    csv_dir = "/home/tamkiraly/Development/tradingActionExperiments/src_tr/test/polygon_test/bar_data_csvs"
    for filename in os.listdir(csv_dir):
        csv_file_path = os.path.join(csv_dir, filename)
        if os.path.isfile(csv_file_path):
            full_symbol_df = pd.read_csv(csv_file_path)
            split_data_by_day(full_symbol_df)