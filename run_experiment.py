from scanners.scanners import get_nasdaq_stickers, andrewAzizRecommendedScanner
from data_sources.generate_price_data import generatePriceData
from random import sample

# initial variables:
TRADING_DAY = '2023-09-06'
experiment_data = dict()
experiment_data['trading_day'] = TRADING_DAY
experiment_data['stickers'] = dict()

# 1) get watchlist
#nasdaq_stickers = sample(get_nasdaq_stickers(), 1000) + ['MRVL']

azis_scanner = andrewAzizRecommendedScanner(trading_day=TRADING_DAY)
azis_scanner.get_filtering_stats()
azis_scanner.recommend_premarket_watchlist()
azis_scanner.recommended_stickers()
stickers = azis_scanner.recommended_stickers


for sticker in stickers:
    experiment_data['stickers'][sticker] = dict()

# 2) load trading day data
get_price_data = generatePriceData(date=TRADING_DAY, exp_dict=experiment_data)
get_price_data.load_watchlist_daily_price_data()



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


3) Apply strategy
4) Analyse results
'''