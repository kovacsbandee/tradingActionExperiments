import pandas as pd
import numpy as np

from src_tr.main.strategies.StrategyBase import StrategyBase
from src_tr.main.enums_and_constants.trading_constants import *

class StrategyWithStopLossPrevPrice(StrategyBase):

    def __init__(self,
                 ma_short, 
                 ma_long,
                 rsi_len,
                 stop_loss_perc,
                 epsilon,
                 trading_day):
        super().__init__()
        self.ma_short = ma_short
        self.ma_long = ma_long
        self.rsi_len = rsi_len
        self.stop_loss_perc = stop_loss_perc
        self.comission_ratio = 0.0
        self.epsilon = epsilon
        self.trading_day = trading_day.strftime('%Y-%m-%d')

    def update_capital_amount(self, account_cash):
        self.capital = account_cash
        
    def apply_long_strategy(self, previous_position: str, symbol: str, sticker_dict: dict):
        sticker_df: pd.DataFrame = sticker_dict[STICKER_DF]
        ind_price: str = sticker_dict[IND_PRICE]

        # set current_capital column
        sticker_df.loc[sticker_df.index[-1], CURRENT_CAPITAL] = self.capital

        # calculate indicators:           
        sticker_df[OPEN_SMALL_IND_COL] = sticker_df[OPEN_NORM].rolling(self.ma_short, center=False).mean().diff()
        sticker_df[OPEN_BIG_IND_COL] = sticker_df[OPEN_NORM].rolling(self.ma_long, center=False).mean().diff()
        
        sticker_df[OPEN_SMALL_IND_COL] = sticker_df[OPEN_SMALL_IND_COL].rolling(self.ma_short, center=False).mean()
        sticker_df[OPEN_BIG_IND_COL] = sticker_df[OPEN_BIG_IND_COL].rolling(self.ma_long, center=False).mean()

        sticker_df[GAIN_LOSS] = sticker_df[ind_price].diff(1)
        sticker_df[GAIN] = np.where(sticker_df[GAIN_LOSS] > 0.0, sticker_df[GAIN_LOSS], 0.0)
        sticker_df[LOSS] = -1 * np.where(sticker_df[GAIN_LOSS] < 0.0, sticker_df[GAIN_LOSS], 0.0)
        sticker_df[AVG_GAIN] = sticker_df[GAIN].rolling(self.rsi_len, center=False).mean()
        sticker_df[AVG_LOSS] = sticker_df[LOSS].rolling(self.rsi_len, center=False).mean()
        sticker_df[RSI] = 100 - (100 / (1 + sticker_df[AVG_GAIN] / sticker_df[AVG_LOSS]))
        last_index = sticker_df.index[-1]

        expected_position = None
        small_ind_col = sticker_df.loc[last_index, OPEN_SMALL_IND_COL]
        big_ind_col = sticker_df.loc[last_index, OPEN_BIG_IND_COL]

        # set expected positions:
        if small_ind_col > self.epsilon and big_ind_col > self.epsilon:
            expected_position = POS_LONG_BUY
        else:
            expected_position = POS_OUT

        sticker_df.loc[sticker_df.index[-1], POSITION] = expected_position
        sticker_df.loc[sticker_df.index[-2], POSITION] = previous_position

        # set trading action
        if sticker_df.iloc[-1][POSITION] == sticker_df.iloc[-2][POSITION]:
            sticker_df.loc[last_index, TRADING_ACTION] = ACT_NO_ACTION

        if sticker_df.iloc[-1][POSITION] == POS_LONG_BUY and sticker_df.iloc[-2][POSITION] != POS_LONG_BUY:
            sticker_df.loc[last_index, TRADING_ACTION] = ACT_BUY_NEXT_LONG
            sticker_dict[PREV_LONG_BUY_POSITION_INDEX] = last_index

        if sticker_df.iloc[-2][POSITION] == POS_LONG_BUY and sticker_df.iloc[-1][POSITION] != POS_LONG_BUY:
            sticker_df.loc[last_index, TRADING_ACTION] = ACT_SELL_PREV_LONG
            sticker_dict[PREV_LONG_BUY_POSITION_INDEX] = None
            
        if sticker_dict[PREV_LONG_BUY_POSITION_INDEX] is not None:
            if (sticker_df.loc[last_index, ind_price] < sticker_df.loc[sticker_df.index[-2], ind_price]) \
                and sticker_df.loc[sticker_df.index[-2], POSITION] != POS_OUT:
                sticker_df.loc[last_index, STOP_LOSS_OUT_SIGNAL] = STOP_LOSS_LONG
                sticker_df.loc[last_index, TRADING_ACTION] = ACT_SELL_PREV_LONG
        
        sticker_df.to_csv(f'{symbol}_{self.trading_day}_{self.epsilon}_long_stop_loss_previous_price.csv')
        
        # update the current sticker DataFrame
        sticker_dict[STICKER_DF] = sticker_df
        return sticker_dict