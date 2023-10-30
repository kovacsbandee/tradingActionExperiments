from datetime import datetime, timedelta
import pandas as pd

from src_tr.main.strategies.StrategyBase import StrategyBase

class StrategyWithStopLoss(StrategyBase):

    def __init__(self,
                 sticker_dict,    # {'AAPL': pd.DataFrame} 
                 ma_short, 
                 ma_long, #NOTE: ugyanaz, mint a PriceDataGenerator data_window length
                 stop_loss_perc, 
                 initial_capital, 
                 epsilon):
        super().__init__(sticker_dict)
        self.ma_short = ma_short
        self.ma_long = ma_long
        self.stop_loss_perc = stop_loss_perc
        self.comission_ratio = 0.0
        self.ind_price = 'close'
        self.epsilon = epsilon
        self.strategy_filters = None
        self.capital = initial_capital
        self.prev_capital_index = None
        self.prev_long_buy_position_index = None
        self.prev_short_sell_position_index = None
        self.tz_str = None

    def update_capital_amount(self, account_cash):
        # TradingClient.get_account().cash
        self.capital = account_cash
    

    def initialize_additional_columns(self):
        ['position', 'current_capital', 'trading_action', 'position_quantity']
        pass


# innentől, minden új timestamp-nél kiszámítjuk az alábbiakat és ezek alapján meghatározzuk a pozíciókat

    def add_trendscalping_specific_indicators(self):
        # NOTE: működik de csak 1 elemű lista
        for df in self.sticker_dict.values():
            self.small_ind_col = f'{self.ind_price}_ma{self.ma_short}_grad'
            df[self.small_ind_col] = df[self.ind_price].rolling(window = self.ma_short, center=False).mean().diff()

            self.big_ind_col = f'{self.ind_price}_ma{self.ma_long}_grad'
            df[self.big_ind_col] = df[self.ind_price].rolling(window = self.ma_long, center=False).mean().diff()




    '''
    Ha t-1-ben nincsen pozícióban és a small_ind_col(t) és a big_ind_col(t) is nagyobb mint, +epsilon, 
        -> akkor LONG_BUY(t)
    
    Ha long pozícióban van és a small_ind_col(t) és a big_ind_col(t) is nagyobb mint, +epsilon, ÉS a price(t) >= price(pozícióba álláskor),
        -> akkor LONG_BUY marad
    
    Ha long pozícióban van és a small_ind_col(t) és a big_ind_col(t) is nagyobb mint, +epsilon, ÉS a price(t) < price(pozícióba álláskor),
        -> akkor azonnal add el az előző LONG_BUY-t
        -> állítsd át a pozíciót out-ra
    
    Ha long pozícióban van és a small_ind_col(t) vagy a big_ind_col(t) is kisebb mint, +epsilon,
        -> akkor azonnal add el az előző LONG_BUY-t
        -> állítsd át a pozíciót out-ra


    (short pozíció visszavásárlás: vegyél meg ugyan annyi darab részvényt, mint amennyit az elején eladtál (hitelbe elkérted a brókertől))
    Ha t-1-ben nincsen pozícióban és a small_ind_col és a big_ind_col is kisebb mint, -epsilon,
        -> akkor SHORT_SELL(t)
    Ha short pozícióban van és a small_ind_col és a big_ind_col is kisebb mint, -epsilon, ÉS a price(t) <= price(pozícióba álláskor),
        -> akkor SHORT_SELL marad
    Ha short pozícióban van és a small_ind_col és a big_ind_col is kisebb mint, -epsilon, ÉS a price(t) > price(pozícióba álláskor),
        -> akkor azonnal vásárold vissz az előző SHORT_SELL-t
        -> állítsd át a pozíciót out-ra
    Ha short pozícióban van és a small_ind_col vagy a big_ind_col nagyobb mint, -epsilon,
        -> akkor azonnal vásárold vissza az előző SHORT_SELL-t
        -> állítsd át a pozíciót out-ra    
    '''



# ezszar.
    def create_strategy_filter(self):
        # reutrns a boolean filter sequence for long buy, and another one for short sell
        df = list(self.sticker_dict.values())[0] #TODO: ide majd valami kevésbé kókány megoldás kellene
        
        long_filter = (self.long_epsilon < df[self.big_ind_col]) & (self.short_epsilon < df[self.small_ind_col])
        short_filter = (-self.long_epsilon > df[self.big_ind_col]) & (-self.short_epsilon > df[self.small_ind_col])
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