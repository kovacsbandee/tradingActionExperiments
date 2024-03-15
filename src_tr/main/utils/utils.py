import os
from datetime import date, timedelta
import pandas as pd
import pickle

from config import config
from src_tr.main.data_sources.market_holidays import market_holidays


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
def calculate_capital_from_in_out_positions_in_result_daily_price_data_df(daily_price_data_df, initial_capital):
    # TODO: van olyan eset, amikor nincsen benne buy_next_long_position a trading_action-ben lsd.: CMSCS 2024_03_12,
    # viszont ebben csak sell_previous_position van!!!
    prev_long_buy_position_index = daily_price_data_df[daily_price_data_df['trading_action'] == 'buy_next_long_position'].index[0]
    prev_capital_index = prev_long_buy_position_index
    daily_price_data_df['current_capital_post_calculation'] = None
    daily_price_data_df['gain_per_qty_per_position_post_calculation'] = None
    daily_price_data_df.loc[prev_capital_index, 'current_capital_post_calculation'] = initial_capital
    prev_position = None
    for i, row in daily_price_data_df.iterrows():
        if row['trading_action'] == 'sell_previous_long_position':
            daily_price_data_df.loc[i, 'gain_per_qty_per_position_post_calculation'] = daily_price_data_df.loc[i, 'o'] - daily_price_data_df.loc[prev_long_buy_position_index, 'o']
            daily_price_data_df.loc[i, 'current_capital_post_calculation'] = \
                (daily_price_data_df.loc[prev_capital_index, 'current_capital_post_calculation'] +
                (daily_price_data_df.loc[i, 'gain_per_qty_per_position_post_calculation'] *
                 (daily_price_data_df.loc[prev_long_buy_position_index, 'current_capital_post_calculation'] / daily_price_data_df.loc[prev_long_buy_position_index, 'o'])))
            prev_capital_index = i
            prev_position = 'sell_previous_long_position'
        if row['trading_action'] == 'buy_next_long_position':
            prev_long_buy_position_index = i
            daily_price_data_df.loc[i, 'current_capital_post_calculation'] = daily_price_data_df.loc[prev_capital_index, 'current_capital_post_calculation']
            prev_position = 'buy_next_long_position'
    return daily_price_data_df
