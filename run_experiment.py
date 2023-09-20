import pandas as pd
from random import sample
from datetime import datetime

from scanners.scanners import get_nasdaq_stickers, andrewAzizRecommendedScanner
from data_sources.generate_price_data import generatePriceData
from strategies.strategies import add_strategy_specific_indicators
from strategies.strategies import apply_single_long_strategy, apply_single_short_strategy, apply_simple_combined_trend_following_strategy

# initial variables:
final_results = list()

for TRADING_DAY in [TRADING_DAY.strftime('%Y-%m-%d') for TRADING_DAY in pd.bdate_range(pd.to_datetime('2023-08-09', format='%Y-%m-%d'), periods=20).to_list()]:
    if datetime.strptime(TRADING_DAY, '%Y-%m-%d').strftime('%A') != 'Sunday' or datetime.strptime(TRADING_DAY, '%Y-%m-%d').strftime('%A') != 'Saturday':
        # 0) initializations
        experiment_data = dict()
        experiment_data['trading_day'] = TRADING_DAY
        experiment_data['stickers'] = dict()
        # 1) Get watchlist
        azis_scanner = andrewAzizRecommendedScanner(trading_day=TRADING_DAY)
        azis_scanner.get_filtering_stats()
        azis_scanner.recommend_premarket_watchlist()
        stickers =  azis_scanner.recommended_stickers
        # TODO Tamas: debug!
        #stickers = get_nasdaq_stickers()
        for sticker in stickers:
            experiment_data['stickers'][sticker] = dict()
        # 2) Load trading day data
        get_price_data = generatePriceData(date=TRADING_DAY, exp_dict=experiment_data)
        get_price_data.load_watchlist_daily_price_data()
        # 3) Apply strategy
        add_strategy_specific_indicators(exp_data=experiment_data, averaged_cols=['close', 'volume'], ma_short=5, ma_long=12, plot_strategy_indicators = True)
        long_results = apply_single_long_strategy(exp_data=experiment_data, day=TRADING_DAY)
        short_results = apply_single_short_strategy(exp_data=experiment_data, day=TRADING_DAY)
        combined_results = apply_simple_combined_trend_following_strategy(exp_data=experiment_data, day=TRADING_DAY)
    final_results.append(long_results)
    final_results.append(short_results)
    final_results.append(combined_results)


result = []
for r in [res for res in final_results if len(res) != 0]:
    for t in r:
        result.append(t)
df = pd.DataFrame(result, columns=['date', 'position_type', 'sticker', 'gain_per_stock'])
df.to_csv('F:/tradingActionExperiments/data_store/gains_from_all_stickers_0815_w_workaround.csv', index=False)

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