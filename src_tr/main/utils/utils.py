import os
from datetime import date, timedelta
import pandas as pd
import pickle

from config import config
from src_tr.main.data_sources.market_holidays import market_holidays
from src_tr.main.utils.plots import daily_time_series_charts_post_process

def check_trading_day(trading_day: date) -> date:
    if _check_market_holiday(trading_day) \
        or trading_day.strftime('%A') == 'Sunday' \
        or trading_day.strftime('%A') == 'Saturday':
        return 'holiday'
    else:
        return trading_day
    
def calculate_scanning_day(trading_day: date) -> date:
    if trading_day != 'holiday':
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
    else:
        return "holiday"

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

def save_watchlist_bin(recommended_symbol_list: list, trading_day: date):
    trading_day = trading_day.strftime(f"%Y-%m-%d")
    with open(f"src_tr/main/data_sources/watchlist_{trading_day}.p", "wb") as daily_stats:
        pickle.dump(recommended_symbol_list, daily_stats)
        
def load_watchlist_bin(trading_day: date):
    trading_day = trading_day.strftime(f"%Y-%m-%d")
    with open(f"src_tr/main/data_sources/watchlist_{trading_day}.p", "rb") as daily_stats:
        return pickle.load(daily_stats)

#TODO: refaktorálás, stb.
def calculate_capital_from_in_out_positions_in_result_csvs():
    dir = 'adatkimaradas_paper_trading_live/adatkimaradas_paper_trading_live_2024_03_05'
    db_path = config['output_stats']
    initial_capital = 10000
    csvs_path = f'{db_path}/{dir}/daily_files/csvs'
    daily_csvs = os.listdir(csvs_path)
    corrected = list()
    for file in daily_csvs:
        daily_price_data_df = pd.read_csv(f'{csvs_path}/{file}')

        prev_long_buy_position_index = daily_price_data_df[daily_price_data_df['trading_action'] == 'buy_next_long_position'].index[0]
        prev_capital_index = prev_long_buy_position_index
        daily_price_data_df['current_capital_post_calculation'] = 0
        daily_price_data_df['gain_per_qty_per_position_post_calculation'] = 0
        daily_price_data_df.loc[prev_capital_index, 'current_capital_post_calculation'] = initial_capital

        for i, row in daily_price_data_df.iterrows():
            if row['trading_action'] == 'sell_previous_long_position':
                daily_price_data_df.loc[i, 'gain_per_qty_per_position_post_calculation'] = daily_price_data_df.loc[i, 'c'] - daily_price_data_df.loc[prev_long_buy_position_index, 'c']
                daily_price_data_df.loc[i, 'current_capital_post_calculation'] = \
                    (daily_price_data_df.loc[prev_capital_index, 'current_capital_post_calculation'] +
                    (daily_price_data_df.loc[i, 'gain_per_qty_per_position_post_calculation'] *
                     (daily_price_data_df.loc[prev_long_buy_position_index, 'current_capital_post_calculation'] / daily_price_data_df.loc[prev_long_buy_position_index, 'c'])))
                prev_capital_index = i
            if row['trading_action'] == 'buy_next_long_position':
                prev_long_buy_position_index = i
                daily_price_data_df.loc[i, 'current_capital_post_calculation'] = daily_price_data_df.loc[prev_capital_index, 'current_capital_post_calculation']
        corrected.append({'file': file,
                          'corrected_timestamp_num': len(daily_price_data_df[~daily_price_data_df['data_correction'].isna()]),
                          'max_cap': daily_price_data_df['current_capital_post_calculation'].max(),
                          'min_cap': daily_price_data_df[daily_price_data_df['current_capital_post_calculation'] != 0.0]['current_capital_post_calculation'].min()})
        print(file, daily_price_data_df[daily_price_data_df['current_capital_post_calculation'] != 0.0]['current_capital_post_calculation'])
        out_file = file.split('.')[0] + 'post_calculation' + '.csv'
        daily_price_data_df.to_csv(f'{csvs_path}/{out_file}', index=False)
        daily_time_series_charts_post_process(daily_price_data_df, file=file, epsilon=0.0, mode=None, db_path=db_path, daily_dir_name=dir)
    df = pd.DataFrame.from_records(corrected)
    print('Correlation between missing data and capital')
    print(df[['corrected_timestamp_num', 'max_cap', 'min_cap']].corr())