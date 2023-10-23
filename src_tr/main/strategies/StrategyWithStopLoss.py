from datetime import datetime, timedelta

from src_tr.main.strategies.StrategyBase import StrategyBase

class StrategyWithStopLoss(StrategyBase):

    def __init__(self, sticker_dict_from_generator, 
                 ma_short, 
                 ma_long, 
                 stop_loss_perc, 
                 comission_ratio,
                 initial_capital):
        super().__init__(sticker_dict_from_generator)
        self.ma_short = ma_short
        self.ma_long = ma_long
        self.stop_loss_perc = stop_loss_perc
        self.comission_ratio = comission_ratio
        self.averaged_cols = ['close']
        self.ind_price = 'close'
        self.short_epsilon = 0.01
        self.long_epsilon = 0.01
        self.strategy_filters = None
        self.capital = initial_capital
        self.prev_capital_index = None
        self.prev_long_buy_position_index = None
        self.prev_short_sell_position_index = None
        self.tz_str = None

    def update_capital_amount(self, account_cash):
        # TradingClient.get_account().cash
        self.capital = account_cash

    def add_trendscalping_specific_indicators(self):
        for df in self.sticker_dict.values():
            for col in self.averaged_cols: #TODO: ez egyszerűsíthető, ha ez csak egyetlen érték
                short_ind_col = f'{col}_ma{self.ma_short}'
                df[short_ind_col] = self.add_rolling_average(price_time_series=df,
                                                        col=col,
                                                        window_length=self.ma_short)
                df[f'{short_ind_col}_grad'] = self.add_gradient(price_time_series=df,
                                                        col=short_ind_col)
                
                long_ind_col = f'{col}_ma{self.ma_long}'
                df[long_ind_col] = self.add_rolling_average(price_time_series=df,
                                                    col=col,
                                                    window_length=self.ma_long)
                df[f'{long_ind_col}_grad'] = self.add_gradient(price_time_series=df,
                                                        col=long_ind_col)

    def create_strategy_filter(self):
        # reutrns a boolean filter sequence for long buy, and another one for short sell
        df = list(self.sticker_dict.values())[0] #TODO: ide majd valami kevésbé kókány megoldás kellene
        
        short_grad = f'{self.ind_price}_ma{self.ma_short}_grad'
        long_grad = f'{self.ind_price}_ma{self.ma_long}_grad'

        long_filter = (self.long_epsilon < df[long_grad]) & (self.short_epsilon < df[short_grad])
        short_filter = (-self.long_epsilon > df[long_grad]) & (-self.short_epsilon > df[short_grad])
        self.strategy_filters = {'short_filter': short_filter, 'long_filter': long_filter}

    def initialize_strategy_specific_fields(self):
        filters = self.strategy_filters
        for df in self.sticker_dict.values():
            df['position'] = 'out'
            # add positions
            df.loc[filters['long_filter'].values, 'position'] = 'long_buy'
            df.loc[filters['short_filter'].values, 'position'] = 'short_sell'
            df['trading_action'] = ''
            df['prev_position_lagged'] = df['position'].shift(1)

            # init prev indices
            prev_capital_indices = list()
            if 'long_buy' in df['position'].unique():
                self.prev_long_buy_position_index = df[df['position'] == 'long_buy'].index[0]
                prev_capital_indices.append(self.prev_long_buy_position_index)

            if 'short_sell' in df['position'].unique():
                self.prev_short_sell_position_index = df[df['position'] == 'short_sell'].index[0]
                prev_capital_indices.append(self.prev_short_sell_position_index)

            df['gain_per_position'] = 0
            df['current_capital'] = 0
            self.prev_capital_index = min(prev_capital_indices) if len(prev_capital_indices)>0 else df.index[0]
            df.loc[self.prev_capital_index, 'current_capital'] = self.capital

            self.tz_str = df.index[0][-6:]
        
    def apply_strategy(self):
        for df in self.sticker_dict.values():
            for i, row in df.iterrows():
                # ha a mostani capital rosszabb mint az i-edik sorban a price add el, és update-elj minden indexet!
                # különben mehet tovább lefelé!
                current_last_in_position_indices = []
                try:
                    current_last_in_position_indices.append(prev_long_buy_position_index)
                except:
                    pass
                try:
                    current_last_in_position_indices.append(prev_short_sell_position_index)
                except:
                    pass
                current_last_in_position_index = max(current_last_in_position_indices) if len(current_last_in_position_indices)>0 else df.index[0]
                if row['current_capital'] - self.stop_loss_perc * df.loc[current_last_in_position_index, 'current_capital'] < 0:
                    # add el:
                    if current_last_in_position_index == prev_long_buy_position_index:
                        #prev_short_sell_position_index = i
                        df.loc[i, 'gain_per_position'] = df.loc[i, self.ind_price] - df.loc[prev_long_buy_position_index, self.ind_price]
                        df.loc[i, 'current_capital'] = (df.loc[self.prev_capital_index, 'current_capital'] + \
                                                        (df.loc[i, 'gain_per_position'] * \
                                                        (df.loc[prev_long_buy_position_index, 'current_capital'] /
                                                        df.loc[prev_long_buy_position_index, self.ind_price]))) - \
                                                    self.comission_ratio * df.loc[self.prev_capital_index, 'current_capital']
                        self.prev_capital_index = i
                        forward_t_ind = i
                        while df.loc[forward_t_ind, 'position'] == 'long_buy':
                            df.loc[forward_t_ind, 'position'] = 'out'
                            df.loc[forward_t_ind, 'prev_position_lagged'] = 'out'
                            forward_t_ind = str(datetime.strptime(df.index[0][:-6], '%Y-%m-%d %H:%M:%S') + timedelta(minutes=1)) + self.tz_str
                    if current_last_in_position_index == prev_short_sell_position_index:
                        df.loc[i, 'gain_per_position'] = df.loc[prev_short_sell_position_index, self.ind_price] - df.loc[i, self.ind_price]
                        df.loc[i, 'current_capital'] = (df.loc[self.prev_capital_index, 'current_capital'] + \
                                                        (df.loc[i, 'gain_per_position'] * \
                                                        (df.loc[prev_short_sell_position_index, 'current_capital'] /
                                                        df.loc[prev_short_sell_position_index, self.ind_price]))) - \
                                                    self.comission_ratio * df.loc[self.prev_capital_index, 'current_capital']
                        self.prev_capital_index = i
                        forward_t_ind = i
                        while df.loc[forward_t_ind, 'position'] == 'long_buy':
                            df.loc[forward_t_ind, 'position'] = 'out'
                            df.loc[forward_t_ind, 'prev_position_lagged'] = 'out'
                            forward_t_ind = str(
                                datetime.strptime(df.index[0][:-6], '%Y-%m-%d %H:%M:%S') + timedelta(minutes=1)) + self.tz_str
                else:
                    # buy long position eset
                    if row['prev_position_lagged'] == 'out' and row['position'] == 'long_buy':
                        prev_long_buy_position_index = i
                        df.loc[i, 'current_capital'] = df.loc[self.prev_capital_index, 'current_capital']
                        df.loc[i, 'trading_action'] = 'buy_long'
                    # sell short eset
                    if row['prev_position_lagged'] == 'out' and row['position'] == 'short_sell':
                        prev_short_sell_position_index = i
                        df.loc[i, 'current_capital'] = df.loc[self.prev_capital_index, 'current_capital']
                        df.loc[i, 'trading_action'] = 'sell_short'
                    # sell long eset
                    if row['prev_position_lagged'] == 'long_buy' and row['position'] == 'out':
                        df.loc[i, 'gain_per_position'] = df.loc[i, self.ind_price] - df.loc[prev_long_buy_position_index, self.ind_price]
                        df.loc[i, 'current_capital'] = (df.loc[self.prev_capital_index, 'current_capital'] + \
                                                        (df.loc[i, 'gain_per_position'] * \
                                                        (df.loc[prev_long_buy_position_index, 'current_capital'] / \
                                                        df.loc[prev_long_buy_position_index, self.ind_price]))) - \
                                                    self.comission_ratio * df.loc[self.prev_capital_index, 'current_capital']
                        self.prev_capital_index = i
                        df.loc[i, 'trading_action'] = 'sell_long'
                    # buy short eset
                    if row['prev_position_lagged'] == 'short_sell' and row['position'] == 'out':
                        df.loc[i, 'gain_per_position'] = df.loc[prev_short_sell_position_index, self.ind_price] - df.loc[i, self.ind_price]
                        df.loc[i, 'current_capital'] = (df.loc[self.prev_capital_index, 'current_capital'] + \
                                                        (df.loc[i, 'gain_per_position'] * \
                                                        (df.loc[prev_short_sell_position_index, 'current_capital'] / \
                                                        df.loc[prev_short_sell_position_index, self.ind_price]))) - \
                                                    self.comission_ratio * df.loc[self.prev_capital_index, 'current_capital']
                        self.prev_capital_index = i
                        df.loc[i, 'trading_action'] = 'buy_short'
                    # buy short-sell long eset
                    if row['prev_position_lagged'] == 'short_sell' and row['position'] == 'long_buy':
                        prev_long_buy_position_index = i
                        df.loc[i, 'gain_per_position'] = df.loc[prev_short_sell_position_index, self.ind_price] - df.loc[i, self.ind_price]
                        df.loc[i, 'current_capital'] = (df.loc[self.prev_capital_index, 'current_capital'] + \
                                                        (df.loc[i, 'gain_per_position'] * \
                                                        (df.loc[prev_short_sell_position_index, 'current_capital'] / \
                                                        df.loc[prev_short_sell_position_index, self.ind_price]))) - \
                                                    self.comission_ratio * df.loc[self.prev_capital_index, 'current_capital']
                        self.prev_capital_index = i
                        df.loc[i, 'trading_action'] = 'buy_short_sell_long'
                    # sell long  - buy short eset
                    if row['prev_position_lagged'] == 'long_buy' and row['position'] == 'short_sell':
                        prev_short_sell_position_index = i
                        df.loc[i, 'gain_per_position'] = df.loc[i, self.ind_price] - df.loc[prev_long_buy_position_index, self.ind_price]
                        df.loc[i, 'current_capital'] = (df.loc[self.prev_capital_index, 'current_capital'] + \
                                                        (df.loc[i, 'gain_per_position'] * \
                                                        (df.loc[prev_long_buy_position_index, 'current_capital'] /
                                                        df.loc[prev_long_buy_position_index, self.ind_price]))) - \
                                                    self.comission_ratio * df.loc[self.prev_capital_index, 'current_capital']
                        self.prev_capital_index = i
                        df.loc[i, 'trading_action'] = 'sell_long_buy_short'