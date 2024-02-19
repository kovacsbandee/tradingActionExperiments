import pandas as pd
import numpy as np

from config import config

class TradingAlgorithmMain():
    def __init__(self,
                 trading_day,
                 daily_dir_name):
        self.comission_ratio = 0.0
        self.trading_day = trading_day.strftime('%Y_%m_%d')
        self.name = 'trading_algorithm_with_stoploss_prev_price'
        self.daily_dir_name = daily_dir_name

    def update_capital_amount(self, account_cash):
        self.capital = account_cash
        
    def apply_long_trading_algorithm(self, 
                                     previous_position: str, 
                                     symbol: str, 
                                     symbol_dict: dict, 
                                     algo_params: dict):
        symbol_df: pd.DataFrame = symbol_dict['daily_price_data_df']

        # set current_capital column
        symbol_df.loc[symbol_df.index[-1], 'current_capital'] = self.capital
        
        # calculate RSI
        symbol_df = self.calculate_current_rsi(symbol_df, algo_params["rsi_length"])
        
        # calculate current range
        if algo_params['close_signal'] == 'ATR':
            symbol_df = self.calculate_current_range(symbol_df)
        
        # evaluate current position
        eval_result = None
        if symbol_dict['previous_long_buy_position_index'] is None:
            if algo_params["entry_signal"] == "default":
                symbol_df = self.entry_signal_default(symbol_df=symbol_df,
                                                        ma_short=algo_params["entry_windows"]["short"],
                                                        ma_long=algo_params["entry_windows"]["long"],
                                                        epsilon=algo_params["entry_windows"]["epsilon"],
                                                        rsi=algo_params["entry_rsi"],
                                                        weighted=algo_params["entry_weighted"],
                                                        previous_position=previous_position)
            elif algo_params["entry_signal"] == "MACD":
                symbol_df = self.entry_signal_MACD(symbol_df=symbol_df,
                                                   macd_windows=algo_params['entry_windows'],
                                                   rsi=algo_params['entry_rsi'],
                                                   weighted=algo_params['entry_weighted'],
                                                   previous_position=previous_position)
                
            eval_result = self.set_buy_action(symbol_df, symbol_dict)
                
        elif symbol_dict['previous_long_buy_position_index'] is not None:
            if algo_params["close_signal"] == "AVG":
                symbol_df = self.close_signal_avg(symbol_df=symbol_df,
                                                  rsi=algo_params["close_rsi"], 
                                                  window_size=algo_params["close_window"], 
                                                  weighted=algo_params["close_weighted"],
                                                  previous_position=previous_position)
            elif algo_params["close_signal"] == "ATR":
                symbol_df = self.close_signal_atr(symbol_df=symbol_df,
                                                  symbol_dict=symbol_dict,
                                                  rsi=algo_params["close_rsi"],
                                                  window_size=algo_params["close_window"],
                                                  weighted=algo_params["close_weighted"],
                                                  previous_position=previous_position)
                
            eval_result = self.set_close_action(symbol_df=symbol_df, symbol_dict=symbol_dict)
        
        symbol_df = eval_result["symbol_df"]
        symbol_dict = eval_result["symbol_dict"]
        
        symbol_df.to_csv(f"{config['output_stats']}/{self.daily_dir_name}/daily_files/csvs/{symbol}_{self.trading_day}_{self.name}.csv")
        
        # update the current symbol DataFrame
        symbol_dict['daily_price_data_df'] = symbol_df
        return symbol_dict
    
    def calculate_current_rsi(self, symbol_df: pd.DataFrame, rsi_len: int):
        symbol_df['gain_loss'] = symbol_df['o'].diff(1)
        symbol_df['gain'] = np.where(symbol_df['gain_loss'] > 0.0, symbol_df['gain_loss'], 0.0)
        symbol_df['loss'] = -1 * np.where(symbol_df['gain_loss'] < 0.0, symbol_df['gain_loss'], 0.0)
        symbol_df['avg_gain'] = symbol_df['gain'].rolling(rsi_len, center=False).mean()
        symbol_df['avg_loss'] = symbol_df['loss'].rolling(rsi_len, center=False).mean()
        symbol_df['rsi'] = 100 - (100 / (1 + symbol_df['avg_gain'] / symbol_df['avg_loss']))
        return symbol_df
    
    def calculate_current_range(self, symbol_df: pd.DataFrame):
        current_high = symbol_df.iloc[-1]['h']
        current_low = symbol_df.iloc[-1]['l']
        previous_close = symbol_df.iloc[-2]['c']
        symbol_df.loc[symbol_df.index[-1], "current_range"] = \
            max([current_high-current_low, abs(current_high-previous_close), abs(current_low-previous_close)])
            
        return symbol_df

    def set_buy_action(self, symbol_df: pd.DataFrame, symbol_dict: dict):
        if symbol_df.iloc[-1]['position'] == symbol_df.iloc[-2]['position']:
            symbol_df.loc[symbol_df.index[-1], 'trading_action'] = 'no_action'

        if symbol_df.iloc[-1]['position'] == 'long' and symbol_df.iloc[-2]['position'] != 'long':
            symbol_df.loc[symbol_df.index[-1], 'trading_action'] = 'buy_next_long_position'
            symbol_dict['previous_long_buy_position_index'] = symbol_df.index[-1]
            
        return {
            "symbol_df" : symbol_df,
            "symbol_dict" : symbol_dict
        }
        
    def set_close_action(self, symbol_df: pd.DataFrame, symbol_dict: dict):
        if symbol_df.iloc[-1]['position'] == symbol_df.iloc[-2]['position']:
            symbol_df.loc[symbol_df.index[-1], 'trading_action'] = 'no_action'
            
        if symbol_df.iloc[-2]['position'] == 'long' and symbol_df.iloc[-1]['position'] != 'long':
            symbol_df.loc[symbol_df.index[-1], 'trading_action'] = 'sell_previous_long_position'
            symbol_dict['previous_long_buy_position_index'] = None
        
        return {
            "symbol_df" : symbol_df,
            "symbol_dict" : symbol_dict
        }
    
    def entry_signal_default(self, symbol_df: pd.DataFrame, ma_short: int, ma_long: int, epsilon: float, 
                             rsi: dict, weighted: bool, previous_position: str):
        expected_position = 'out'
        overbought = None
        oversold = None
        if rsi:
            overbought = rsi["overbought"]
            oversold = rsi["oversold"]
            
        symbol_df['open_small_indicator'] = symbol_df['open_norm'].rolling(ma_short, center=False).mean().diff()
        symbol_df['open_big_indicator'] = symbol_df['open_norm'].rolling(ma_long, center=False).mean().diff()
        
        symbol_df['open_small_indicator'] = symbol_df['open_small_indicator'].rolling(ma_short, center=False).mean()
        symbol_df['open_big_indicator'] = symbol_df['open_big_indicator'].rolling(ma_long, center=False).mean()
        
        small_ind_col = symbol_df.loc[symbol_df.index[-1], 'open_small_indicator']
        big_ind_col = symbol_df.loc[symbol_df.index[-1], 'open_big_indicator']
        
        if small_ind_col > epsilon and big_ind_col > epsilon:
            expected_position = 'long'
        else:
            if previous_position == 'long':
                expected_position = 'long'

        symbol_df.loc[symbol_df.index[-1], 'position'] = expected_position
        symbol_df.loc[symbol_df.index[-2], 'position'] = previous_position
        
        return symbol_df
    
    def entry_signal_MACD(self, symbol_df: pd.DataFrame, macd_windows: dict,
                          rsi: dict, weighted: bool, previous_position: str):
        expected_position = 'out'
        ema_short = macd_windows["short"]
        ema_long = macd_windows["long"]
        signal_ema = macd_windows["signal"]
        symbol_df[f"EMA{ema_short}"] = symbol_df['c'].ewm(span=ema_short, adjust=False).mean()
        symbol_df[f"EMA{ema_long}"] = symbol_df['c'].ewm(span=ema_long, adjust=False).mean()
        symbol_df['MACD'] = symbol_df[f"EMA{ema_short}"] - symbol_df[f"EMA{ema_long}"]
        symbol_df['signal_line'] = symbol_df['MACD'].ewm(span=signal_ema, adjust=False).mean()
        
        if rsi:
            if symbol_df.iloc[-1]['rsi'] <= rsi["oversold"]:
                expected_position = 'long'
                symbol_df.loc[symbol_df.index[-1], 'entry_signal_type'] = 'entry_RSI'
            elif symbol_df.iloc[-2]['MACD'] < symbol_df.iloc[-2]['signal_line'] \
                and symbol_df.iloc[-1]['MACD'] > symbol_df.iloc[-1]['signal_line']:
                expected_position = 'long'
                symbol_df.loc[symbol_df.index[-1], 'entry_signal_type'] = 'entry_MACD'
            else:
                if previous_position == 'long':
                    expected_position = 'long'
        else:
            if symbol_df.iloc[-2]['MACD'] < symbol_df.iloc[-2]['signal_line'] \
                and symbol_df.iloc[-1]['MACD'] > symbol_df.iloc[-1]['signal_line']:
                expected_position = 'long'
                symbol_df.loc[symbol_df.index[-1], 'entry_signal_type'] = 'entry_MACD'
            else:
                if previous_position == 'long':
                    expected_position = 'long'

        symbol_df.loc[symbol_df.index[-1], 'position'] = expected_position
        symbol_df.loc[symbol_df.index[-2], 'position'] = previous_position
        
        return symbol_df
    
    def close_signal_avg(self, symbol_df: pd.DataFrame, rsi: dict, window_size: int, weighted: bool, previous_position: str):
        if symbol_df.loc[symbol_df.index[-1], 'c'] < symbol_df.loc[symbol_df.index[-2], 'o']:
            if weighted:    
                symbol_df["close_signal_avg"] = symbol_df['o'].ewm(span=window_size, adjust=False).mean()
            else:
                symbol_df["close_signal_avg"] = symbol_df['o'].rolling(window=window_size, center=False).mean()
                
            current_close_avg = symbol_df.loc[symbol_df.index[-1], 'close_signal_avg']
            
            if rsi:
                if symbol_df.iloc[-1]['rsi'] >= rsi['overbought']:
                    symbol_df.loc[symbol_df.index[-1], 'position'] = 'out'
                    symbol_df.loc[symbol_df.index[-1], 'close_signal_type'] = 'close_RSI'
                elif symbol_df.loc[symbol_df.index[-1], 'c'] <= current_close_avg:
                    symbol_df.loc[symbol_df.index[-1], 'position'] = 'out'
                    symbol_df.loc[symbol_df.index[-1], 'close_signal_type'] = 'close_AVG'
                else:
                    symbol_df.loc[symbol_df.index[-1], 'position'] = previous_position
            else:
                if symbol_df.loc[symbol_df.index[-1], 'c'] <= current_close_avg:
                    symbol_df.loc[symbol_df.index[-1], 'position'] = 'out'
                    symbol_df.loc[symbol_df.index[-1], 'close_signal_type'] = 'close_AVG'
                else:
                    symbol_df.loc[symbol_df.index[-1], 'position'] = previous_position
                
            return symbol_df
        else:
            symbol_df.loc[symbol_df.index[-1], 'position'] = previous_position
            return symbol_df

    def close_signal_atr(self, symbol_df: pd.DataFrame, symbol_dict: dict, rsi: dict, window_size: int, weighted: bool, previous_position: str):
        if (symbol_df.loc[symbol_df.index[-1], 'c'] < symbol_df.loc[symbol_df.index[-2], 'o']):
            if weighted:
                symbol_df['atr_short'] = symbol_df['current_range'].ewm(span=window_size, adjust=False).mean()
            else:
                symbol_df['atr_short'] = symbol_df['current_range'].rolling(window=window_size, center=False).mean()
            
            if rsi:
                if symbol_df.iloc[-1]['rsi'] >= rsi['overbought']:
                    symbol_df.loc[symbol_df.index[-1], 'position'] = 'out'
                    symbol_df.loc[symbol_df.index[-1], 'close_signal_type'] = 'close_RSI'
                elif symbol_df.loc[symbol_df.index[-2], 'o']-symbol_df.loc[symbol_df.index[-1], 'c'] > symbol_df.loc[symbol_df.index[-1], 'atr_short']:
                    symbol_df.loc[symbol_df.index[-1], 'position'] = 'out'
                    symbol_df.loc[symbol_df.index[-1], 'close_signal_type'] = 'close_ATR'
                else:
                    symbol_df.loc[symbol_df.index[-1], 'position'] = previous_position
            else:
                if symbol_df.loc[symbol_df.index[-2], 'o']-symbol_df.loc[symbol_df.index[-1], 'c'] > symbol_df.loc[symbol_df.index[-1], 'atr_short']:
                    symbol_df.loc[symbol_df.index[-1], 'position'] = 'out'
                    symbol_df.loc[symbol_df.index[-1], 'close_signal_type'] = 'close_ATR'
                else:
                    symbol_df.loc[symbol_df.index[-1], 'position'] = previous_position
        
            return symbol_df
        else:
            symbol_df.loc[symbol_df.index[-1], 'position'] = previous_position
            return symbol_df