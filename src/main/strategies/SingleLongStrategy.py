import pandas as pd
from .StrategyBase import StrategyBase

class SingleLongStrategy(StrategyBase):

    def __init__(self, initial_capital, commission_ratio):
        super.__init__()
        self.initial_capital = initial_capital
        self.commission_ratio = commission_ratio        
    
    def apply_strategy(self):
        results=list()
        for sticker in self.sticker_data['stickers'].keys():
            sticker_df = self.sticker_data['stickers'][sticker]['trading_day_data']
            sticker_df['position'] = 'out'
            #TODO epsiolon has to be optimized!!!
            sticker_df.loc[(0.001 < sticker_df[f'close_ma{self.ma_long}_grad']) & (0.001 < sticker_df[f'close_ma{self.ma_short}_grad']), 'position'] = 'long_buy'
            #sticker_df.loc[(0.001 < sticker_df[f'close_ma{ma_long}_grad']) | (0.001 < sticker_df[f'close_ma{ma_short}_grad']), 'position'] = 'long_buy'
            sticker_df['trading_action'] = ''
            sticker_df['prev_position_lagged'] = sticker_df['position'].shift(1)
            #todo ki kell próbálni a 2. feltétel nélkül is, illetve meg kell nézni ha benne van, akkor van-e olyan trade, ami csak emiatt kerül bele, ugy kene mukodnie, hogy osszefuggo poziciokat alkossan az elso feltetellel
            sticker_df.loc[(sticker_df['position'] == 'long_buy') & (sticker_df['prev_position_lagged'] == 'out'), 'trading_action'] = 'buy next long position'
            sticker_df.loc[(sticker_df['position'] == 'out') & (sticker_df['prev_position_lagged'] == 'long_buy'), 'trading_action'] = 'sell previous long position'
            sticker_df.drop('prev_position_lagged', axis=1, inplace=True)
            trading_action_df = sticker_df[sticker_df['trading_action'] != ''].copy()
            sticker_df.loc[sticker_df.index > max(trading_action_df[trading_action_df['trading_action'] == 'sell previous long position'].index), 'trading_action'] = ''
            trading_action_df['gain_per_position'] = 0
            prev_long_buy_position_index = trading_action_df[trading_action_df['trading_action'] == 'buy next long position'].index[0]
            prev_capital_index = prev_long_buy_position_index
            trading_action_df['current_capital'] = 0
            trading_action_df.loc[prev_capital_index, 'current_capital'] = self.initial_capital
            if trading_action_df.shape[0] > 0:
                for i, row in trading_action_df.iterrows():
                    if row['trading_action'] == 'sell previous long position':
                        trading_action_df.loc[i, 'gain_per_position'] = trading_action_df.loc[i, 'close'] - trading_action_df.loc[prev_long_buy_position_index, 'close']
                        trading_action_df.loc[i, 'current_capital'] = (trading_action_df.loc[prev_capital_index, 'current_capital'] + (
                                                                                trading_action_df.loc[i, 'gain_per_position'] * \
                                                                                (trading_action_df.loc[prev_long_buy_position_index, 'current_capital'] /
                                                                                    trading_action_df.loc[prev_long_buy_position_index, 'close']))) - self.commission_ratio * \
                                                                    trading_action_df.loc[prev_capital_index, 'current_capital']
                        prev_capital_index = i
                    if row['trading_action'] == 'buy next long position':
                        prev_long_buy_position_index = i
                        trading_action_df.loc[i, 'current_capital'] = trading_action_df.loc[prev_capital_index, 'current_capital']
                print(f'Gain on {sticker} with simple long strategy', trading_action_df.gain_per_position.sum())
                results.append((sticker_df["trading_day"], 'long', sticker, trading_action_df.gain_per_position.sum()))
                sticker_df = pd.merge(sticker_df, trading_action_df[['trading_action', 'gain_per_position', 'current_capital']],
                                    how='left',
                                    left_index=True,
                                    right_index=True)
                sticker_df['gain_per_position'].fillna(0.0, inplace=True)
                self.sticker_data['stickers'][sticker]['trading_day_data_long_strategy'] = sticker_df
            else:
                sticker_df['gain_per_position'] = 0
                self.sticker_data['stickers'][sticker]['trading_day_data_long_strategy'] = sticker_df
        return results