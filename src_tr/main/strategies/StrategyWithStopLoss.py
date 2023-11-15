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
                 epsilon):
        super().__init__()
        self.ma_short = ma_short
        self.ma_long = ma_long
        self.stop_loss_perc = stop_loss_perc
        self.comission_ratio = 0.0
        self.epsilon = epsilon
        self.capital = initial_capital

    def update_capital_amount(self, account_cash):
        # TradingClient.get_account().cash
        self.capital = account_cash

    #def set_sticker_df(self, sticker_df):
    #    sticker_df = sticker_df

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
   
    ''' 
    def apply_combined_strategy(self, trading_client: TradingClient, symbol: str):
        # set current_capital column
        sticker_df.loc[sticker_df.index[-1], CURRENT_CAPITAL] = self.capital

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
        sticker_df[self.SMALL_IND_COL] = sticker_df[self.ind_price].rolling(self.ma_short, center=False).mean().diff()
        sticker_df[self.BIG_IND_COL] = sticker_df[self.ind_price].rolling(self.ma_long, center=False).mean().diff()
        last_index = sticker_df.index[-1]

        expected_position = None
        
        small_ind_col = sticker_df.loc[last_index, self.SMALL_IND_COL]
        big_ind_col = sticker_df.loc[last_index, self.BIG_IND_COL]

        if small_ind_col > self.epsilon \
            and big_ind_col > self.epsilon:
            expected_position = POS_LONG_BUY
        elif small_ind_col < -self.epsilon \
            and big_ind_col < -self.epsilon:
            expected_position = POS_SHORT_SELL
        else:
            expected_position = POS_OUT

        sticker_df.loc[sticker_df.index[-1], POSITION] = expected_position
        sticker_df.loc[sticker_df.index[-2], POSITION] = previous_position

        # set trading action
        if sticker_df.iloc[-1][POSITION] == sticker_df.iloc[-2][POSITION]:
            sticker_df.loc[last_index, TRADING_ACTION] = ACT_NO_ACTION

        if sticker_df.iloc[-1][POSITION] == POS_LONG_BUY and sticker_df.iloc[-2][POSITION] != POS_LONG_BUY:
            sticker_df.loc[last_index, TRADING_ACTION] = ACT_BUY_NEXT_LONG
            self.prev_long_buy_position_index = last_index

        if sticker_df.iloc[-1][POSITION] == POS_SHORT_SELL and sticker_df.iloc[-2][POSITION] != POS_SHORT_SELL:
            sticker_df.loc[last_index, TRADING_ACTION] = ACT_SELL_NEXT_SHORT
            self.prev_short_sell_position_index = last_index

        if sticker_df.iloc[-2][POSITION] == POS_LONG_BUY and sticker_df.iloc[-1][POSITION] != POS_LONG_BUY:
            sticker_df.loc[last_index, TRADING_ACTION] = ACT_SELL_PREV_LONG

        # set stop loss signal
        if self.prev_long_buy_position_index is not None:
            if (sticker_df.loc[last_index, self.ind_price] < sticker_df.loc[self.prev_long_buy_position_index, self.ind_price]) \
                and sticker_df.loc[last_index, POSITION] == POS_LONG_BUY:
                sticker_df.loc[last_index, STOP_LOSS_OUT_SIGNAL] = STOP_LOSS_LONG
                sticker_df.loc[last_index, TRADING_ACTION] = ACT_SELL_PREV_LONG

        if self.prev_short_sell_position_index is not None:
            if (sticker_df.loc[last_index, self.ind_price] > sticker_df.loc[self.prev_short_sell_position_index, self.ind_price]) \
                and sticker_df.loc[last_index, POSITION] == POS_SHORT_SELL:
                sticker_df.loc[last_index, STOP_LOSS_OUT_SIGNAL] = STOP_LOSS_SHORT
                sticker_df.loc[last_index, TRADING_ACTION] = ACT_BUY_PREV_SHORT
                
        sticker_df.to_csv('combined_strategy_log.csv')
        '''
    
    def apply_long_strategy(self, trading_client: TradingClient, symbol: str, sticker_dict: dict):
        sticker_df: pd.DataFrame = sticker_dict[STICKER_DF]
        ind_price: str = sticker_dict[IND_PRICE]
        # set current_capital column
        sticker_df.loc[sticker_df.index[-1], CURRENT_CAPITAL] = self.capital

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
        sticker_df[OPEN_SMALL_IND_COL] = sticker_df[ind_price].rolling(self.ma_short, center=False).mean().diff()
        sticker_df[OPEN_BIG_IND_COL] = sticker_df[ind_price].rolling(self.ma_long, center=False).mean().diff()
        #TODO: az indikátorokon is meg kell futtatni a mozgóátlag-számítást
        last_index = sticker_df.index[-1]

        expected_position = None
        small_ind_col = sticker_df.loc[last_index, OPEN_SMALL_IND_COL]
        big_ind_col = sticker_df.loc[last_index, OPEN_BIG_IND_COL]

        # set expected positions:
        if small_ind_col > self.epsilon \
            and big_ind_col > self.epsilon:
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
            self.prev_long_buy_position_index = last_index

        if sticker_df.iloc[-2][POSITION] == POS_LONG_BUY and sticker_df.iloc[-1][POSITION] != POS_LONG_BUY:
            sticker_df.loc[last_index, TRADING_ACTION] = ACT_SELL_PREV_LONG
            
        if self.prev_long_buy_position_index is not None:
            if (sticker_df.loc[last_index, ind_price] < sticker_df.loc[self.prev_long_buy_position_index, ind_price]) \
                and sticker_df.loc[last_index, POSITION] == POS_LONG_BUY:
                sticker_df.loc[last_index, STOP_LOSS_OUT_SIGNAL] = STOP_LOSS_LONG
                sticker_df.loc[last_index, TRADING_ACTION] = ACT_SELL_PREV_LONG
        
        sticker_df.to_csv(f'{sticker_dict[symbol]}_long_strategy_log.csv')
        
        # update the current sticker DataFrame
        sticker_dict[STICKER_DF] = sticker_df
        return sticker_dict