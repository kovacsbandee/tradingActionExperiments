from scanners.scanners import get_nasdaq_stickers
from data_sources.generate_price_data import generatePriceData

# initial variables:
TRADING_DAY = '2023-09-06'
experiment_data = dict()
experiment_data['trading_day'] = TRADING_DAY
experiment_data['stickers'] = dict()

# 1) get watchlist
nasdaq_stickers = get_nasdaq_stickers()[0:110]
sticker_list = ['AA', 'PLTR','MRVL']
for sticker in nasdaq_stickers:
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