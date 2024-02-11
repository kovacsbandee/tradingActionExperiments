import pandas as pd
import numpy as np

from src_tr.main.trading_algorithms.TradingAlgorithmBase import TradingAlgorithmBase

class TradingAlgorithmWithStopLossPrevPrice(TradingAlgorithmBase):
    #TODO: rsi_Threshold
    def __init__(self,
                 ma_short, 
                 ma_long,
                 epsilon,
                 rsi_len,
                 stop_loss_perc,
                 trading_day,
                 run_id,
                 db_path):
        super().__init__()
        self.ma_short = ma_short
        self.ma_long = ma_long
        self.epsilon = epsilon
        self.rsi_len = rsi_len
        self.stop_loss_perc = stop_loss_perc
        self.comission_ratio = 0.0
        self.trading_day = trading_day.strftime('%Y_%m_%d')
        self.run_id = run_id
        self.db_path = db_path
        self.name = 'trading_algorithm_with_stoploss_prev_price'
        self.daily_dir_name = self.run_id + '_' + 'trading_day' + '_' + self.trading_day

    def update_capital_amount(self, account_cash):
        self.capital = account_cash
        
    def apply_long_trading_algorithm(self, previous_position: str, symbol: str, symbol_dict: dict):
        symbol_df: pd.DataFrame = symbol_dict['daily_price_data_df']
        ind_price: str = symbol_dict['indicator_price']

        # set current_capital column
        symbol_df.loc[symbol_df.index[-1], 'current_capital'] = self.capital

        # calculate indicators:           
        symbol_df['open_small_indicator'] = symbol_df['open_norm'].rolling(self.ma_short, center=False).mean().diff()
        symbol_df['open_big_indicator'] = symbol_df['open_norm'].rolling(self.ma_long, center=False).mean().diff()
        
        symbol_df['open_small_indicator'] = symbol_df['open_small_indicator'].rolling(self.ma_short, center=False).mean()
        symbol_df['open_big_indicator'] = symbol_df['open_big_indicator'].rolling(self.ma_long, center=False).mean()

        symbol_df['gain_loss'] = symbol_df[ind_price].diff(1)
        symbol_df['gain'] = np.where(symbol_df['gain_loss'] > 0.0, symbol_df['gain_loss'], 0.0)
        symbol_df['loss'] = -1 * np.where(symbol_df['gain_loss'] < 0.0, symbol_df['gain_loss'], 0.0)
        symbol_df['avg_gain'] = symbol_df['gain'].rolling(self.rsi_len, center=False).mean()
        symbol_df['avg_loss'] = symbol_df['loss'].rolling(self.rsi_len, center=False).mean()
        symbol_df['rsi'] = 100 - (100 / (1 + symbol_df['avg_gain'] / symbol_df['avg_loss']))
        # TODO : rsi 10-30 között mindenképp beszállunk
        #   rsi >= 70 semmiképp nem szállunk be
        # TODO: MACD above signal line beszállunk
        # TODO: súlyozott kiszállási átlag
        #       rsi >= 70 mindenképp kiszállunk
        last_index = symbol_df.index[-1]
        
        # average true/ma_short range
        current_high = symbol_df.iloc[-1]['h']
        current_low = symbol_df.iloc[-1]['l']
        previous_close = symbol_df.iloc[-2]['c']
        
        current_range = max([current_high-current_low, abs(current_high-previous_close), abs(current_low-previous_close)])
        symbol_df.iloc[-1, symbol_df.columns.get_loc('current_range')] = current_range
        symbol_df['atr_short'] = symbol_df['current_range'].rolling(window=self.ma_short, center=False).mean() #NOTE: window-méret változatok
        
        symbol_df["stop_loss_ma_short"] = symbol_df['o'].rolling(window=self.ma_short, center=False).mean()
        curr_sl = symbol_df.loc[last_index, 'stop_loss_ma_short']
        curr_price = symbol_df.loc[symbol_df.index[-1], 'c']

        expected_position = 'out'
        small_ind_col = symbol_df.loc[last_index, 'open_small_indicator']
        big_ind_col = symbol_df.loc[last_index, 'open_big_indicator']

        # set expected positions:
        """
            TODO: RSI-t be kéne építeni!
        """
        if small_ind_col > self.epsilon and big_ind_col > self.epsilon:
            expected_position = 'long'
        else:
            if previous_position == 'long':
                expected_position = 'long'

        symbol_df.loc[symbol_df.index[-1], 'position'] = expected_position
        symbol_df.loc[symbol_df.index[-2], 'position'] = previous_position

        # set trading action
        if symbol_df.iloc[-1]['position'] == symbol_df.iloc[-2]['position']:
            symbol_df.loc[last_index, 'trading_action'] = 'no_action'

        if symbol_df.iloc[-1]['position'] == 'long' and symbol_df.iloc[-2]['position'] != 'long':
            symbol_df.loc[last_index, 'trading_action'] = 'buy_next_long_position'
            symbol_dict['previous_long_buy_position_index'] = last_index

        if symbol_df.iloc[-2]['position'] == 'long' and symbol_df.iloc[-1]['position'] != 'long':
            symbol_df.loc[last_index, 'trading_action'] = 'sell_previous_long_position'
            symbol_dict['previous_long_buy_position_index'] = None
            
        # stop loss ATR
        # if symbol_dict['previous_long_buy_position_index'] is not None:
        #     if (symbol_df.loc[last_index, ind_price] < symbol_df.loc[symbol_df.index[-2], ind_price]) \
        #         and symbol_df.loc[symbol_df.index[-2], 'position'] != 'out' \
        #         and symbol_df.loc[symbol_df.index[-2], 'trading_action'] != 'buy_next_long_position' \
        #         and symbol_df.loc[symbol_df.index[-2], ind_price]-symbol_df.loc[last_index, ind_price] > symbol_df.loc[last_index, 'atr_short']:
        #         symbol_df.loc[last_index, 'stop_loss_out_signal'] = 'stop_loss_long'
        #         symbol_df.loc[last_index, 'trading_action'] = 'sell_previous_long_position'
                
        # stop loss fix %
        if symbol_dict['previous_long_buy_position_index'] is not None:
            if (symbol_df.loc[last_index, ind_price] < symbol_df.loc[symbol_df.index[-2], ind_price]) \
                and symbol_df.loc[symbol_df.index[-2], 'position'] != 'out' \
                and symbol_df.loc[symbol_df.index[-1], ind_price] <= curr_sl: #NOTE 0.3 vagy horvát
                symbol_df.loc[last_index, 'stop_loss_out_signal'] = 'stop_loss_long'
                symbol_df.loc[last_index, 'trading_action'] = 'sell_previous_long_position'
        
        symbol_df.to_csv(f'{self.db_path}/{self.daily_dir_name}/daily_files/csvs/{symbol}_{self.trading_day}_{self.name}.csv')
        
        # update the current symbol DataFrame
        symbol_dict['daily_price_data_df'] = symbol_df
        return symbol_dict