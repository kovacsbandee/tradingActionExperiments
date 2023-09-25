import os
from dotenv import load_dotenv
import pandas as pd
from random import sample
from datetime import datetime, timedelta

from scanners.scanners import get_nasdaq_stickers, andrewAzizRecommendedScanner
from scanners.AndrewAzizRecommendedScanner import AndrewAzizRecommendedScanner
from data_sources.generate_price_data import generatePriceData
from strategies.strategies import add_strategy_specific_indicators
from strategies.strategies import apply_single_long_strategy, apply_single_short_strategy, apply_simple_combined_trend_following_strategy
from checks.checks import check_trading_day
from utils.utils import calculate_scanning_day

load_dotenv()
PROJECT_PATH = os.environ["PROJECT_PATH"]

# initial variables:
final_results = list()
tr_day_list = [trd.strftime('%Y-%m-%d') for trd in pd.bdate_range(pd.to_datetime('2023-09-12', format='%Y-%m-%d'), periods=20).to_list()]

stickers = get_nasdaq_stickers(PROJECT_PATH)

#for TRADING_DAY in tr_day_list:
if datetime.strptime(tr_day_list[0], '%Y-%m-%d').strftime('%A') != 'Sunday' or datetime.strptime(tr_day_list[0], '%Y-%m-%d').strftime('%A') != 'Saturday':
    # 0) initializations
    experiment_data = dict()
    experiment_data['trading_day'] = tr_day_list[0]
    experiment_data['stickers'] = dict()
    recommended_stickers = []
    long_results = []
    short_results = []
    combined_results = []
    # 1) Get watchlist
    temp_trading_day: datetime = check_trading_day(tr_day_list[0])
    temp_scanning_day: datetime = calculate_scanning_day(temp_trading_day)
    aziz_scanner = AndrewAzizRecommendedScanner(PROJECT_PATH, 'KTAZIZ', temp_trading_day, temp_scanning_day, stickers, 10, 100, 10, 25000)
    pre_market_stats = aziz_scanner.get_filtering_stats()
    if pre_market_stats is not None:
        recommended_stickers = aziz_scanner.recommend_premarket_watchlist()
    
        stickers = recommended_stickers
        # TODO Tamas: debug!
        #stickers = get_nasdaq_stickers()
        for sticker in stickers: # TODO: a generatePriceData-ban listát használunk, oda mehetne a recommended_stickers is, ne legyen oda-vissza
            experiment_data['stickers'][sticker] = dict()
        # 2) Load trading day data
        get_price_data = generatePriceData(date=tr_day_list[0], exp_dict=experiment_data)
        get_price_data.load_watchlist_daily_price_data()
        # 3) Apply strategy
        add_strategy_specific_indicators(exp_data=experiment_data, averaged_cols=['close', 'volume'], ma_short=5, ma_long=12, plot_strategy_indicators = True)
        long_results = apply_single_long_strategy(exp_data=experiment_data, day=tr_day_list[0])
        short_results = apply_single_short_strategy(exp_data=experiment_data, day=tr_day_list[0])
        combined_results = apply_simple_combined_trend_following_strategy(exp_data=experiment_data, day=tr_day_list[0])
final_results.append(long_results)
final_results.append(short_results)
final_results.append(combined_results)


result = []
for r in [res for res in final_results if len(res) != 0]:
    for t in r:
        result.append(t)
df = pd.DataFrame(result, columns=['date', 'position_type', 'sticker', 'gain_per_stock'])
df.to_csv(f'{PROJECT_PATH}/data_store/gains_from_all_stickers_0815_w_workaround.csv', index=False)

# TODO olyan mintha nem prev_trading_day-en futna a stratégia
# NOTE (Tamas): a load_watchlist_daily_price_data-ban nincsenek is prev_trading_day értékek [tessék azért még háromszor csekkolni]
# 20230901: BEKE, AMC
# 20230829: NVCR
# 20230823: M
# 20230824: PBR

'''
experiment_data structure
    # stickers as keys
        # price data
        # strategy parameters
            # name
            # details
        # scanner name
        # gains
        # plot names = list()

4) Analyse results
'''