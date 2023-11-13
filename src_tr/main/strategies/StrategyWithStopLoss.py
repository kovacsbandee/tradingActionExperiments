from datetime import datetime, timedelta
import pandas as pd

from alpaca.trading.client import TradingClient
from alpaca.trading.models import Position

from src_tr.main.strategies.StrategyBase import StrategyBase
from src_tr.main.enums_and_constants.trading_constants import *

class StrategyWithStopLoss(StrategyBase):

    SMALL_IND_COL: str = None
    BIG_IND_COL: str = None

    def __init__(self,
                 ma_short, 
                 ma_long,
                 stop_loss_perc, 
                 initial_capital, 
                 epsilon,
                 sticker_df=None):
        super().__init__(sticker_df)
        self.sticker_df: pd.DataFrame = sticker_df
        self.ma_short = ma_short
        self.ma_long = ma_long
        self.stop_loss_perc = stop_loss_perc
        self.comission_ratio = 0.0
        self.ind_price = CLOSE
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

    def set_sticker_df(self, sticker_df):
        self.sticker_df = sticker_df

    '''
    Ha t-1-ben nincsen pozícióban és a self.SMALL_IND_COL(t) és a self.BIG_IND_COL(t) is nagyobb mint, +epsilon, 
        -> akkor LONG_BUY(t)
    
    Ha long pozícióban van és a self.SMALL_IND_COL(t) és a self.BIG_IND_COL(t) is nagyobb mint, +epsilon, ÉS a price(t) >= price(pozícióba álláskor),
        -> akkor LONG_BUY marad
    
    Ha long pozícióban van és a self.SMALL_IND_COL(t) és a self.BIG_IND_COL(t) is nagyobb mint, +epsilon, ÉS a price(t) < price(pozícióba álláskor),
        -> akkor azonnal add el az előző LONG_BUY-t
        -> állítsd át a pozíciót out-ra
    
    Ha long pozícióban van és a self.SMALL_IND_COL(t) vagy a self.BIG_IND_COL(t) is kisebb mint, +epsilon,
        -> akkor azonnal add el az előző LONG_BUY-t
        -> állítsd át a pozíciót out-ra


    (short pozíció visszavásárlás: vegyél meg ugyan annyi darab részvényt, mint amennyit az elején eladtál (hitelbe elkérted a brókertől))
    Ha t-1-ben nincsen pozícióban és a self.SMALL_IND_COL és a self.BIG_IND_COL is kisebb mint, -epsilon,
        -> akkor SHORT_SELL(t)
    Ha short pozícióban van és a self.SMALL_IND_COL és a self.BIG_IND_COL is kisebb mint, -epsilon, ÉS a price(t) <= price(pozícióba álláskor),
        -> akkor SHORT_SELL marad
    Ha short pozícióban van és a self.SMALL_IND_COL és a self.BIG_IND_COL is kisebb mint, -epsilon, ÉS a price(t) > price(pozícióba álláskor),
        -> akkor azonnal vásárold vissz az előző SHORT_SELL-t
        -> állítsd át a pozíciót out-ra
    Ha short pozícióban van és a self.SMALL_IND_COL vagy a self.BIG_IND_COL nagyobb mint, -epsilon,
        -> akkor azonnal vásárold vissza az előző SHORT_SELL-t
        -> állítsd át a pozíciót out-ra    
    '''
        
    def initialize_additional_fields(self):
        self.SMALL_IND_COL = f'{self.ind_price}_small_ind_col'
        self.BIG_IND_COL = f'{self.ind_price}_big_ind_col'
        self.sticker_df[POSITION] = POS_OUT
        self.sticker_df[TRADING_ACTION] = ACT_NO_ACTION
        self.sticker_df[CURRENT_CAPITAL] = self.capital
        self.sticker_df[STOP_LOSS_OUT_SIGNAL] = STOP_LOSS_NONE
        
    def apply_combined_strategy(self, trading_client: TradingClient, symbol: str):
        # set current_capital column
        self.sticker_df.loc[self.sticker_df.index[-1], CURRENT_CAPITAL] = self.capital

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
        self.sticker_df[self.SMALL_IND_COL] = self.sticker_df[self.ind_price].rolling(self.ma_short, center=False).mean().diff()
        self.sticker_df[self.BIG_IND_COL] = self.sticker_df[self.ind_price].rolling(self.ma_long, center=False).mean().diff()
        last_index = self.sticker_df.index[-1]

        expected_position = None
        
        small_ind_col = self.sticker_df.loc[last_index, self.SMALL_IND_COL].iloc[1]
        big_ind_col = self.sticker_df.loc[last_index, self.BIG_IND_COL].iloc[1]

        if small_ind_col > self.epsilon \
            and big_ind_col > self.epsilon:
            expected_position = POS_LONG_BUY
        elif small_ind_col < -self.epsilon \
            and big_ind_col < -self.epsilon:
            expected_position = POS_SHORT_SELL
        else:
            expected_position = POS_OUT

        self.sticker_df.loc[self.sticker_df.index[-1], POSITION] = expected_position
        self.sticker_df.loc[self.sticker_df.index[-2], POSITION] = previous_position

        # set trading action
        if self.sticker_df.iloc[-1][POSITION] == self.sticker_df.iloc[-2][POSITION]:
            self.sticker_df.loc[last_index, TRADING_ACTION] = ACT_NO_ACTION

        if self.sticker_df.iloc[-1][POSITION] == POS_LONG_BUY and self.sticker_df.iloc[-2][POSITION] != POS_LONG_BUY:
            self.sticker_df.loc[last_index, TRADING_ACTION] = ACT_BUY_NEXT_LONG
            self.prev_long_buy_position_index = last_index

        if self.sticker_df.iloc[-1][POSITION] == POS_SHORT_SELL and self.sticker_df.iloc[-2][POSITION] != POS_SHORT_SELL:
            self.sticker_df.loc[last_index, TRADING_ACTION] = ACT_SELL_NEXT_SHORT
            self.prev_short_sell_position_index = last_index

        if self.sticker_df.iloc[-2][POSITION] == POS_LONG_BUY and self.sticker_df.iloc[-1][POSITION] != POS_LONG_BUY:
            self.sticker_df.loc[last_index, TRADING_ACTION] = ACT_SELL_PREV_LONG

        # set stop loss signal
        if self.prev_long_buy_position_index is not None:
            if (self.sticker_df.loc[last_index, self.ind_price] < self.sticker_df.loc[self.prev_long_buy_position_index, self.ind_price]) \
                and self.sticker_df.loc[last_index, POSITION] == POS_LONG_BUY:
                self.sticker_df.loc[last_index, STOP_LOSS_OUT_SIGNAL] = STOP_LOSS_LONG
                self.sticker_df.loc[last_index, TRADING_ACTION] = ACT_SELL_PREV_LONG

        if self.prev_short_sell_position_index is not None:
            if (self.sticker_df.loc[last_index, self.ind_price] > self.sticker_df.loc[self.prev_short_sell_position_index, self.ind_price]) \
                and self.sticker_df.loc[last_index, POSITION] == POS_SHORT_SELL:
                self.sticker_df.loc[last_index, STOP_LOSS_OUT_SIGNAL] = STOP_LOSS_SHORT
                self.sticker_df.loc[last_index, TRADING_ACTION] = ACT_BUY_PREV_SHORT
                
        self.sticker_df.to_csv('long_strategy_log.csv')
    
    def apply_long_strategy(self, trading_client: TradingClient, symbol: str):
        # set current_capital column
        self.sticker_df.loc[self.sticker_df.index[-1], CURRENT_CAPITAL] = self.capital

        # get current positions
        positions = trading_client.get_all_positions()
        previous_position = None
        if positions is not None and len(positions) > 0:
            p: Position = positions[0]
            if p.symbol == symbol:
                previous_position = p.side.value
        else:
            previous_position = POS_OUT

        # calculate indicators:
        self.sticker_df[self.SMALL_IND_COL] = self.sticker_df[self.ind_price].rolling(self.ma_short, center=False).mean().diff()
        self.sticker_df[self.BIG_IND_COL] = self.sticker_df[self.ind_price].rolling(self.ma_long, center=False).mean().diff()
        last_index = self.sticker_df.index[-1]

        expected_position = None
        small_ind_col = self.sticker_df.loc[last_index, self.SMALL_IND_COL].iloc[1]
        big_ind_col = self.sticker_df.loc[last_index, self.BIG_IND_COL].iloc[1]

        # LIVE-IMPLEMENTED:
        if small_ind_col > self.epsilon \
            and big_ind_col > self.epsilon:
            expected_position = POS_LONG_BUY
        else:
            expected_position = POS_OUT

        self.sticker_df.loc[self.sticker_df.index[-1], POSITION] = expected_position
        self.sticker_df.loc[self.sticker_df.index[-2], POSITION] = previous_position

        # set trading action
        if self.sticker_df.iloc[-1][POSITION] == self.sticker_df.iloc[-2][POSITION]:
            self.sticker_df.loc[last_index, TRADING_ACTION] = ACT_NO_ACTION

        if self.sticker_df.iloc[-1][POSITION] == POS_LONG_BUY and self.sticker_df.iloc[-2][POSITION] != POS_LONG_BUY:
            self.sticker_df.loc[last_index, TRADING_ACTION] = ACT_BUY_NEXT_LONG
            self.prev_long_buy_position_index = last_index

        if self.sticker_df.iloc[-2][POSITION] == POS_LONG_BUY and self.sticker_df.iloc[-1][POSITION] != POS_LONG_BUY:
            self.sticker_df.loc[last_index, TRADING_ACTION] = ACT_SELL_PREV_LONG
            
        if self.prev_long_buy_position_index is not None:
            if (self.sticker_df.loc[last_index, self.ind_price] < self.sticker_df.loc[self.prev_long_buy_position_index, self.ind_price]) \
                and self.sticker_df.loc[last_index, POSITION] == POS_LONG_BUY:
                self.sticker_df.loc[last_index, STOP_LOSS_OUT_SIGNAL] = STOP_LOSS_LONG
                self.sticker_df.loc[last_index, TRADING_ACTION] = ACT_SELL_PREV_LONG
                
        self.sticker_df.to_csv('long_strategy_log.csv')