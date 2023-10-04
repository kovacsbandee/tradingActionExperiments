import os
import sys
print(sys.executable)
from dotenv import load_dotenv
import pandas as pd
from random import sample
from datetime import datetime, timedelta

from scanners.AndrewAzizRecommendedScanner import AndrewAzizRecommendedScanner
from data_sources.AlpacaPriceDataGenerator import AlpacaPriceDataGenerator
from strategies.strategies import add_strategy_specific_indicators
from strategies.strategies import apply_single_long_strategy, apply_single_short_strategy, apply_simple_combined_trend_following_strategy
from checks.checks import check_trading_day
from utils.utils import calculate_scanning_day, get_nasdaq_stickers, append_to_bar_list

load_dotenv()
PROJECT_PATH = os.environ["PROJECT_PATH"]
STICKER_CSV_PATH = os.environ["STICKER_CSV_PATH"]

# initial variables:
final_results = list()
tr_day_list = [trd.strftime('%Y-%m-%d') for trd in pd.bdate_range(pd.to_datetime('2023-09-12', format='%Y-%m-%d'), periods=20).to_list()]

stickers = get_nasdaq_stickers(project_path=PROJECT_PATH, file_path=STICKER_CSV_PATH)

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

        # TODO Tamas: debug!
        #stickers = get_nasdaq_stickers()
        
        # 2) Load trading day data
        price_data_generator = AlpacaPriceDataGenerator(trading_day=temp_trading_day, recommended_sticker_list=recommended_stickers, 
                                                  lower_price_boundary=10, upper_price_boundary=100, lower_volume_boundary=10000,
                                                  data_window_size=10)
        price_data_generator.initialize_sticker_dict()
        price_data_generator.initialize_current_data_window()
        price_data_generator.load_prev_day_watchlist_data()
        # innentől érdekes, hogy hogyan update-elünk a websocket message alapján
        # a) "ősfeltöltés" -> current_data_window feltöltése n elemig
        # b) n elem után engedjük továbbfutni
        # c) WARNING! Van, hogy nem egyetlen listában jönnek az összes sticker adatai, 
        #    hanem több, különálló message-ben és meglehetősen random
        #    -> megoldás: itt is egy számláló, amihez ez if tartozik és csak akkor futtatjuk az algot, ha eléri az x értéket (?)
        minute_bar_list = [] # TODO: a kereskedési esemény megtörténtekor ki kell üríteni
        # on message:
        append_to_bar_list(message="websocket_message", bar_list=minute_bar_list)
        # HINT: threading, Event(), set, wait, stb.

        price_data_generator.load_watchlist_daily_price_data()
        
        # 3) Apply strategy
        add_strategy_specific_indicators(exp_data=experiment_data, averaged_cols=['close', 'volume'], ma_short=5, ma_long=12, plot_strategy_indicators = True)
        long_results = apply_single_long_strategy(exp_data=experiment_data, day=temp_trading_day)
        short_results = apply_single_short_strategy(exp_data=experiment_data, day=temp_trading_day)
        combined_results = apply_simple_combined_trend_following_strategy(exp_data=experiment_data, day=temp_trading_day)
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