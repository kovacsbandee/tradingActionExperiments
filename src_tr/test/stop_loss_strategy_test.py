import pandas as pd
from src_tr.main.strategies.StrategyWithStopLoss import StrategyWithStopLoss

csv_path = '/home/tamkiraly/Development/tradingActionExperiments/data_store/AAPL.csv'
sticker_df = pd.read_csv(csv_path)
sticker_df = sticker_df[['Datetime' ,'open', 'high', 'low', 'close', 'adj close', 'volume']]
sticker_df.set_index('Datetime', inplace=True)
date = csv_path[65:75].replace('_', '-')
sticker = csv_path.split('/')[-1][:-4]
avg_close = sticker_df['close'].mean()
avg_volume = sticker_df['volume'].mean()

sticker_dict_from_generator = {
    'AAPL' : sticker_df
}

strategy = StrategyWithStopLoss(sticker_dict_from_generator=sticker_dict_from_generator,
                                ma_short=5,
                                ma_long=12,
                                stop_loss_perc=0.0,
                                comission_ratio=0.0,
                                initial_capital=3000)

strategy.add_trendscalping_specific_indicators()
strategy.create_strategy_filter()
strategy.initialize_strategy_specific_fields()
strategy.apply_strategy()

# itt lehet plotolni vagy bármit csinálni a strategy.sticker_dict-ből