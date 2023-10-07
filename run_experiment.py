# TODO 1005:
#  - csináld meg jól a pozíciós plot-ot: EZ KÉSZ!
#  - fejezd be a kereskedést 14-kor: EZ ÚGY NÉZ KI HASZNÁL!
#  - próbáld ki a simított gradienst
# TODO:
#  - rá kell tenni az indikátorokra is a pozícióba állás és a kijövetel jelét!
#  - meg kell csinálni hosszú időszakra, sok stock-ra a gradiensek eloszlását
#  - mi lenne ha mindig csak a kezdeti tőkét tenném be és a nyereséget kivenném minden pozíció után és
#  emellé beállítanék egy stop loss-t, ami kijön a pozícióból, ha valamennyi veszteség termelődik, de nem megy vissza ugyan abba, megvárja a következőt

# feltételezés, hogy egyik napról a másikra nem változik nagyon:
# epsilon függvényében a nullátmenetek távolsága nagy legyen! illetve legyen kiegyensúlyozott a volume, legyen pici a szórása

'''
Ha a kereskedésben hirtelen spike-ok vannak, akkor rosszul működik a trend scalping, mert gyorsabban változik az ár mint ahogyan a gradiensek le tudják követni:
megoldások lehetnek:
    - órás periódus idejű változásokat mutató stock-okat keresünk a scanner-el, mert a 5-12-es MA-k ezen működnek a legjobban, vagyis a 'periódus idő' legyen ötszöröse a hosszú átlagnak
    ->
    -> a változás kb. fél órás nagyságrendű shortma5 és longma12 esetén; az amplitúdó néhány %; nem nagy a percen belüli szórás; a volume gradiense nő;
        van benne egybefüggő legalább fél óra hosszú egyirányú mozgás (EZ VALÓSZÍNŰLEG A RITKASÁG....)
    -> kellene egy olyan elgondolás, ami az ABCD pattern-t használja...
    - buy jelet a long_ma adja, sell jelet pedig a short_ma, és a símított gradiens legyen konstans
'''


import pandas as pd
from datetime import datetime

from scanners.scanners import get_nasdaq_stickers, andrewAzizRecommendedScanner
from data_sources.generate_price_data import generatePriceData
from strategies.strategies import add_strategy_specific_indicators
from strategies.strategies import apply_single_long_strategy, apply_single_short_strategy, apply_simple_combined_trend_following_strategy, apply_simple_combined_trend_following_strategy_w_stopping_crit

# initial variables:
final_results = list()
experiement_start_date = '2023-09-10'
number_of_experiment_days = 15
mashort=10
malong=24

exp_name = 'longer_mas_for_low_freq_gain'
for TRADING_DAY in [TRADING_DAY.strftime('%Y-%m-%d') for TRADING_DAY in pd.bdate_range(pd.to_datetime(experiement_start_date, format='%Y-%m-%d'), periods=number_of_experiment_days).to_list()]:
    if datetime.strptime(TRADING_DAY, '%Y-%m-%d').strftime('%A') != 'Sunday' or datetime.strptime(TRADING_DAY, '%Y-%m-%d').strftime('%A') != 'Saturday':
        # 0) initializations
        experiment_data = dict()
        experiment_data['trading_day'] = TRADING_DAY
        experiment_data['stickers'] = dict()
        # 1) Get watchlist
        azis_scanner = andrewAzizRecommendedScanner(trading_day=TRADING_DAY,
                                                    lower_price_boundary=10,
                                                    upper_price_boundary=100,
                                                    avg_volume_cond=25000,
                                                    price_range_perc_cond=10)

        azis_scanner.calculate_filtering_stats()
        azis_scanner.recommend_premarket_watchlist()
        stickers =  azis_scanner.recommended_stickers
        for sticker in stickers:
            experiment_data['stickers'][sticker] = dict()
        # 2) Load trading day data
        get_price_data = generatePriceData(date=TRADING_DAY, exp_dict=experiment_data)
        get_price_data.load_watchlist_daily_price_data()
        # 3) Apply strategy
        add_strategy_specific_indicators(exp_data=experiment_data,
                                         averaged_cols=['open', 'volume'],
                                         ma_short=mashort,
                                         ma_long=malong,
                                         plot_strategy_indicators = False)
        #long_results = apply_single_long_strategy(exp_data=experiment_data, day=TRADING_DAY)
        #short_results = apply_single_short_strategy(exp_data=experiment_data, day=TRADING_DAY)
        combined_results = apply_simple_combined_trend_following_strategy(exp_data=experiment_data,
                                                                          exp_name=exp_name,
                                                                          ind_price='open',
                                                                          ma_short=mashort,
                                                                          ma_long=malong,
                                                                          short_epsilon=0.01,
                                                                          long_epsilon=0.01,
                                                                          day=TRADING_DAY)
        combined_results_w_time_restriction = apply_simple_combined_trend_following_strategy_w_stopping_crit(exp_data=experiment_data,
                                                                                                             exp_name=exp_name,
                                                                                                             ind_price='open',
                                                                                                             ma_short=mashort,
                                                                                                             ma_long=malong,
                                                                                                             short_epsilon=0.01,
                                                                                                             long_epsilon=0.01,
                                                                                                             day=TRADING_DAY)
    #final_results.append(long_results)
    #final_results.append(short_results)
    final_results.append(combined_results)
    final_results.append(combined_results_w_time_restriction)

result = []
for r in [res for res in final_results if len(res) != 0]:
    for t in r:
        result.append(t)
df = pd.DataFrame(result, columns=['date', 'position_type', 'sticker', 'gain_per_stock'])
df.sort_values(by='gain_per_stock', inplace=True)
print(df[['position_type', 'gain_per_stock']].groupby(by='position_type').sum())

df.to_csv(f'F:/tradingActionExperiments/data_store/gains_from_all_stickers_{experiement_start_date}_w_open_as_price_base_scanner{exp_name}.csv', index=False)


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