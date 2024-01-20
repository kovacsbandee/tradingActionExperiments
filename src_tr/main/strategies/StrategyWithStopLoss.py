import pandas as pd
import numpy as np
from dotenv import load_dotenv

from src_tr.main.strategies.StrategyBase import StrategyBase
from src_tr.main.enums_and_constants.trading_constants import *

class StrategyWithStopLoss(StrategyBase):

    def __init__(self,
                 ma_short, 
                 ma_long,
                 rsi_len,
                 stop_loss_perc,
                 epsilon,
                 trading_day,
                 run_id,
                 db_path):
        super().__init__()
        self.ma_short = ma_short
        self.ma_long = ma_long
        self.rsi_len = rsi_len
        self.stop_loss_perc = stop_loss_perc
        self.comission_ratio = 0.0
        self.epsilon = epsilon
        self.trading_day = trading_day.strftime('%Y_%m_%d')
        self.run_id = run_id
        load_dotenv()
        self.db_path = db_path
        self.name = 'strategy_with_stoploss'
        self.daily_dir_name = self.run_id + '_' + 'trading_day' + '_' + self.trading_day

    def update_capital_amount(self, account_cash):
        self.capital = account_cash
        
    def apply_long_strategy(self, previous_position: str, symbol: str, symbol_dict: dict):
        symbol_df: pd.DataFrame = symbol_dict[SYMBOL_DF]
        ind_price: str = symbol_dict[IND_PRICE]

        # set current_capital column
        symbol_df.loc[symbol_df.index[-1], CURRENT_CAPITAL] = self.capital

        # calculate indicators:           
        symbol_df[OPEN_SMALL_IND_COL] = symbol_df[OPEN_NORM].rolling(self.ma_short, center=False).mean().diff()
        symbol_df[OPEN_BIG_IND_COL] = symbol_df[OPEN_NORM].rolling(self.ma_long, center=False).mean().diff()
        
        symbol_df[OPEN_SMALL_IND_COL] = symbol_df[OPEN_SMALL_IND_COL].rolling(self.ma_short, center=False).mean()
        symbol_df[OPEN_BIG_IND_COL] = symbol_df[OPEN_BIG_IND_COL].rolling(self.ma_long, center=False).mean()

        symbol_df[GAIN_LOSS] = symbol_df[ind_price].diff(1)
        symbol_df[GAIN] = np.where(symbol_df[GAIN_LOSS] > 0.0, symbol_df[GAIN_LOSS], 0.0)
        symbol_df[LOSS] = -1 * np.where(symbol_df[GAIN_LOSS] < 0.0, symbol_df[GAIN_LOSS], 0.0)
        symbol_df[AVG_GAIN] = symbol_df[GAIN].rolling(self.rsi_len, center=False).mean()
        symbol_df[AVG_LOSS] = symbol_df[LOSS].rolling(self.rsi_len, center=False).mean()
        symbol_df[RSI] = 100 - (100 / (1 + symbol_df[AVG_GAIN] / symbol_df[AVG_LOSS]))
        last_index = symbol_df.index[-1]

        expected_position = None
        small_ind_col = symbol_df.loc[last_index, OPEN_SMALL_IND_COL]
        big_ind_col = symbol_df.loc[last_index, OPEN_BIG_IND_COL]

        # set expected positions:
        if small_ind_col > self.epsilon and big_ind_col > self.epsilon:
            expected_position = POS_LONG_BUY
        else:
            expected_position = POS_OUT

        symbol_df.loc[symbol_df.index[-1], POSITION] = expected_position
        symbol_df.loc[symbol_df.index[-2], POSITION] = previous_position

        # set trading action
        if symbol_df.iloc[-1][POSITION] == symbol_df.iloc[-2][POSITION]:
            symbol_df.loc[last_index, TRADING_ACTION] = ACT_NO_ACTION

        if symbol_df.iloc[-1][POSITION] == POS_LONG_BUY and symbol_df.iloc[-2][POSITION] != POS_LONG_BUY:
            symbol_df.loc[last_index, TRADING_ACTION] = ACT_BUY_NEXT_LONG
            symbol_dict[PREV_LONG_BUY_POSITION_INDEX] = last_index

        if symbol_df.iloc[-2][POSITION] == POS_LONG_BUY and symbol_df.iloc[-1][POSITION] != POS_LONG_BUY:
            symbol_df.loc[last_index, TRADING_ACTION] = ACT_SELL_PREV_LONG
            
        if symbol_dict[PREV_LONG_BUY_POSITION_INDEX] is not None:
            if (symbol_df.loc[last_index, ind_price] < symbol_df.loc[symbol_dict[PREV_LONG_BUY_POSITION_INDEX], ind_price]) \
                and symbol_df.loc[last_index, POSITION] == POS_LONG_BUY:
                symbol_df.loc[last_index, STOP_LOSS_OUT_SIGNAL] = STOP_LOSS_LONG
                symbol_df.loc[last_index, TRADING_ACTION] = ACT_SELL_PREV_LONG
                
        symbol_df.to_csv(f'{self.db_path}/{self.daily_dir_name}/daily_files/csvs/{symbol}_{self.trading_day}_{self.name}.csv')
        # update the current symbol DataFrame
        symbol_dict[SYMBOL_DF] = symbol_df
        return symbol_dict
    
        ''' 
    def apply_combined_strategy(self, trading_client: TradingClient, symbol: str):
        # set current_capital column
        symbol_df.loc[symbol_df.index[-1], CURRENT_CAPITAL] = self.capital

        # get current positions TODO: kiszervezni
        positions = trading_client.get_all_positions()
        previous_position = None
        if positions is not None and len(positions) > 0:
            p: Position = positions[0]
            if p.symbol == symbol:
                previous_position = p.side.value
        else:
            previous_position = POS_OUT

        # calculate indicators TODO: kiszervezni
        symbol_df[self.SMALL_IND_COL] = symbol_df[self.ind_price].rolling(self.ma_short, center=False).mean().diff()
        symbol_df[self.BIG_IND_COL] = symbol_df[self.ind_price].rolling(self.ma_long, center=False).mean().diff()
        last_index = symbol_df.index[-1]

        expected_position = None
        
        small_ind_col = symbol_df.loc[last_index, self.SMALL_IND_COL]
        big_ind_col = symbol_df.loc[last_index, self.BIG_IND_COL]

        if small_ind_col > self.epsilon \
            and big_ind_col > self.epsilon:
            expected_position = POS_LONG_BUY
        elif small_ind_col < -self.epsilon \
            and big_ind_col < -self.epsilon:
            expected_position = POS_SHORT_SELL
        else:
            expected_position = POS_OUT

        symbol_df.loc[symbol_df.index[-1], POSITION] = expected_position
        symbol_df.loc[symbol_df.index[-2], POSITION] = previous_position

        # set trading action
        if symbol_df.iloc[-1][POSITION] == symbol_df.iloc[-2][POSITION]:
            symbol_df.loc[last_index, TRADING_ACTION] = ACT_NO_ACTION

        if symbol_df.iloc[-1][POSITION] == POS_LONG_BUY and symbol_df.iloc[-2][POSITION] != POS_LONG_BUY:
            symbol_df.loc[last_index, TRADING_ACTION] = ACT_BUY_NEXT_LONG
            self.prev_long_buy_position_index = last_index

        if symbol_df.iloc[-1][POSITION] == POS_SHORT_SELL and symbol_df.iloc[-2][POSITION] != POS_SHORT_SELL:
            symbol_df.loc[last_index, TRADING_ACTION] = ACT_SELL_NEXT_SHORT
            self.prev_short_sell_position_index = last_index

        if symbol_df.iloc[-2][POSITION] == POS_LONG_BUY and symbol_df.iloc[-1][POSITION] != POS_LONG_BUY:
            symbol_df.loc[last_index, TRADING_ACTION] = ACT_SELL_PREV_LONG

        # set stop loss signal
        if self.prev_long_buy_position_index is not None:
            if (symbol_df.loc[last_index, self.ind_price] < symbol_df.loc[self.prev_long_buy_position_index, self.ind_price]) \
                and symbol_df.loc[last_index, POSITION] == POS_LONG_BUY:
                symbol_df.loc[last_index, STOP_LOSS_OUT_SIGNAL] = STOP_LOSS_LONG
                symbol_df.loc[last_index, TRADING_ACTION] = ACT_SELL_PREV_LONG

        if self.prev_short_sell_position_index is not None:
            if (symbol_df.loc[last_index, self.ind_price] > symbol_df.loc[self.prev_short_sell_position_index, self.ind_price]) \
                and symbol_df.loc[last_index, POSITION] == POS_SHORT_SELL:
                symbol_df.loc[last_index, STOP_LOSS_OUT_SIGNAL] = STOP_LOSS_SHORT
                symbol_df.loc[last_index, TRADING_ACTION] = ACT_BUY_PREV_SHORT
                
        symbol_df.to_csv('combined_strategy_log.csv')
        '''