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

# innentől, minden új timestamp-nél kiszámítjuk az alábbiakat és ezek alapján meghatározzuk a pozíciókat

    def add_trendscalping_specific_indicators(self):
        # NOTE: működik de csak 1 elemű lista
        for df in self.sticker_dict.values():
            self.SMALL_IND_COL = f'{self.ind_price}_ma{self.ma_short}_grad'
            df[self.SMALL_IND_COL] = df[self.ind_price].rolling(window = self.ma_short, center=False).mean().diff()

            self.BIG_IND_COL = f'{self.ind_price}_ma{self.ma_long}_grad'
            df[self.BIG_IND_COL] = df[self.ind_price].rolling(window = self.ma_long, center=False).mean().diff()

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

    def initialize_strategy_specific_fields(self):
        filters = self.strategy_filters
        for df in self.sticker_dict.values():
            df[POSITION] = POS_OUT
            # add positions
            df.loc[filters['long_filter'].values, POSITION] = POS_LONG_BUY
            df.loc[filters['short_filter'].values, POSITION] = POS_SHORT_SELL
            df[TRADING_ACTION] = ''
            df['prev_position_lagged'] = df[POSITION].shift(1)

            # init prev indices
            prev_capital_indices = list()
            if POS_LONG_BUY in df[POSITION].unique():
                self.prev_long_buy_position_index = df[df[POSITION] == POS_LONG_BUY].index[0]
                prev_capital_indices.append(self.prev_long_buy_position_index)

            if POS_SHORT_SELL in df[POSITION].unique():
                self.prev_short_sell_position_index = df[df[POSITION] == POS_SHORT_SELL].index[0]
                prev_capital_indices.append(self.prev_short_sell_position_index)

            df['gain_per_position'] = 0
            df[CURRENT_CAPITAL] = 0
            self.prev_capital_index = min(prev_capital_indices) if len(prev_capital_indices)>0 else df.index[0]
            df.loc[self.prev_capital_index, CURRENT_CAPITAL] = self.capital

            self.tz_str = df.index[0][-6:]
        
    def initialize_additional_fields(self):
        self.SMALL_IND_COL = f'{self.ind_price}_small_ind_col'
        self.BIG_IND_COL = f'{self.ind_price}_big_ind_col'
        self.sticker_df[POSITION] = POS_OUT
        self.sticker_df[TRADING_ACTION] = ACT_NO_ACTION
        self.sticker_df[CURRENT_CAPITAL] = self.capital
        self.sticker_df[STOP_LOSS_OUT_SIGNAL] = STOP_LOSS_NONE
    
    def apply_strategy(self, trading_client: TradingClient, symbol: str):
        # set current_capital column
        self.sticker_df.loc[self.sticker_df.index[-1], CURRENT_CAPITAL] = self.capital

        # get current positions
        positions = trading_client.get_all_positions()
        previous_position = None
        if positions is not None and len(positions) > 0:
            p: Position = positions[0]
            if p.symbol == symbol:
                previous_position = p.side.value
            # loop through dict values and check if symbol is present
            # if present, set current index's POSITION column to symbol's position
            # else, set current index's POSITION to POS_OUT
        else:
            previous_position = POS_OUT

        # calculate indicators:
        self.sticker_df[self.SMALL_IND_COL] = self.sticker_df[self.ind_price].rolling(self.ma_short, center=False).mean().diff()
        self.sticker_df[self.BIG_IND_COL] = self.sticker_df[self.ind_price].rolling(self.ma_long, center=False).mean().diff()
        last_index = self.sticker_df.index[-1]

        # ORIGINAL:
        # set position start
        #if self.sticker_df.loc[last_index, self.SMALL_IND_COL] > self.epsilon \
        #    and self.sticker_df.loc[last_index, self.BIG_IND_COL] > self.epsilon:
        #    self.sticker_df.loc[last_index, POSITION] = POS_LONG_BUY
        #elif self.sticker_df.iloc[-1][self.SMALL_IND_COL] < -self.epsilon \
        #    and self.sticker_df.iloc[-1][self.BIG_IND_COL] < -self.epsilon:
        #    self.sticker_df.loc[last_index, POSITION] = POS_SHORT_SELL
        #else:
        #    self.sticker_df.loc[last_index, POSITION] = POS_OUT
        # set position end

        expected_position = None

        # LIVE-IMPLEMENTED:
        if self.sticker_df.loc[last_index, self.SMALL_IND_COL] > self.epsilon \
            and self.sticker_df.loc[last_index, self.BIG_IND_COL] > self.epsilon:
            #self.sticker_df.loc[last_index, POSITION] = POS_LONG_BUY
            expected_position = POS_LONG_BUY
        # elif self.sticker_df.iloc[-1][self.SMALL_IND_COL] < -self.epsilon \
        #     and self.sticker_df.iloc[-1][self.BIG_IND_COL] < -self.epsilon:
        #     #self.sticker_df.loc[last_index, POSITION] = POS_SHORT_SELL
        #     to_be_position = POS_SHORT_SELL
        else:
            #self.sticker_df.loc[last_index, POSITION] = POS_OUT
            expected_position = POS_OUT

        #self.sticker_df.iloc[-1][POSITION] = to_be_position
        #self.sticker_df.iloc[-2][POSITION] = previous_position

        self.sticker_df.loc[self.sticker_df.index[-1], POSITION] = expected_position
        self.sticker_df.loc[self.sticker_df.index[-2], POSITION] = previous_position

        # set trading action
        if self.sticker_df.iloc[-1][POSITION] == self.sticker_df.iloc[-2][POSITION]:
            self.sticker_df.loc[last_index, TRADING_ACTION] = ACT_NO_ACTION

        if self.sticker_df.iloc[-1][POSITION] == POS_LONG_BUY and self.sticker_df.iloc[-2][POSITION] != POS_LONG_BUY:
            self.sticker_df.loc[last_index, TRADING_ACTION] = ACT_BUY_NEXT_LONG
            #self.sticker_df.loc[last_index, CURRENT_CAPITAL] = self.sticker_df.iloc[-2][CURRENT_CAPITAL]
            self.prev_long_buy_position_index = last_index

        #if self.sticker_df.iloc[-1][POSITION] == POS_SHORT_SELL and self.sticker_df.iloc[-2][POSITION] != POS_SHORT_SELL:
        #    self.sticker_df.loc[last_index, TRADING_ACTION] = ACT_SELL_NEXT_SHORT
        #    #self.sticker_df.loc[last_index, CURRENT_CAPITAL] = self.sticker_df.iloc[-2][CURRENT_CAPITAL]
        #    self.prev_short_sell_position_index = last_index

        if self.sticker_df.iloc[-2][POSITION] == POS_LONG_BUY and self.sticker_df.iloc[-1][POSITION] != POS_LONG_BUY:
            self.sticker_df.loc[last_index, TRADING_ACTION] = ACT_SELL_PREV_LONG
            #self.sticker_df.loc[last_index, POSITION] = POS_OUT

        #if self.sticker_df.iloc[-2][POSITION] == POS_SHORT_SELL and self.sticker_df.iloc[-1][POSITION] != POS_SHORT_SELL:
        #    self.sticker_df.loc[last_index, TRADING_ACTION] = ACT_BUY_PREV_SHORT
        #    #self.sticker_df.loc[last_index, POSITION] = POS_OUT
        ## set trading action end

        # ORIGINAL WITH CURRENT_CAPITAL CALCULATION:
        # calculate capital and apply stop loss start
        #if self.sticker_df.loc[last_index, POSITION] == POS_OUT and self.sticker_df.loc[last_index, TRADING_ACTION] == ACT_NO_ACTION:
        #    self.sticker_df.loc[last_index, CURRENT_CAPITAL] = self.sticker_df.iloc[-2][CURRENT_CAPITAL]
        #
        #if (self.sticker_df.loc[last_index, POSITION] == POS_LONG_BUY and self.sticker_df.loc[last_index, TRADING_ACTION] == ACT_NO_ACTION) or \
        #        self.sticker_df.loc[last_index, TRADING_ACTION] == ACT_SELL_PREV_LONG:
        #    self.sticker_df.loc[last_index, CURRENT_CAPITAL] = self.sticker_df.loc[self.prev_short_sell_position_index, CURRENT_CAPITAL] + \
        #                                                    (self.sticker_df.loc[last_index, self.ind_price] - self.sticker_df.loc[self.prev_short_sell_position_index, self.ind_price]) * \
        #                                                    (self.sticker_df.loc[self.prev_short_sell_position_index, CURRENT_CAPITAL] / self.sticker_df.loc[self.prev_short_sell_position_index, self.ind_price])
        #
        #if (self.sticker_df.loc[last_index, POSITION] == POS_SHORT_SELL and self.sticker_df.loc[last_index, TRADING_ACTION] == ACT_NO_ACTION) or \
        #        self.sticker_df.loc[last_index, TRADING_ACTION] == ACT_BUY_PREV_SHORT:
        #    self.sticker_df.loc[last_index, CURRENT_CAPITAL] = self.sticker_df.loc[self.prev_long_buy_position_index, CURRENT_CAPITAL] + \
        #                                                    (self.sticker_df.loc[self.prev_long_buy_position_index, self.ind_price] - self.sticker_df.loc[last_index, self.ind_price]) * \
        #                                                    (self.sticker_df.loc[self.prev_long_buy_position_index, CURRENT_CAPITAL] / self.sticker_df.loc[self.prev_long_buy_position_index, self.ind_price])

        if self.prev_long_buy_position_index is not None: #TODO: ide nem a prev_long_buy_position_index kell?
            if (self.sticker_df.loc[last_index, self.ind_price] < self.sticker_df.loc[self.prev_long_buy_position_index, self.ind_price]) \
                and self.sticker_df.loc[last_index, POSITION] == POS_LONG_BUY:
                    
                self.sticker_df.loc[last_index, STOP_LOSS_OUT_SIGNAL] = STOP_LOSS_LONG
                self.sticker_df.loc[last_index, TRADING_ACTION] = ACT_SELL_PREV_LONG
                #self.sticker_df.loc[last_index, CURRENT_CAPITAL] = self.sticker_df.loc[self.prev_short_sell_position_index, CURRENT_CAPITAL] + \
                #                                                (self.sticker_df.loc[last_index, self.ind_price] - self.sticker_df.loc[self.prev_short_sell_position_index, self.ind_price]) * \
                #                                                (self.sticker_df.loc[self.prev_short_sell_position_index, CURRENT_CAPITAL] /
                #                                                self.sticker_df.loc[self.prev_short_sell_position_index, self.ind_price])
                #self.sticker_df.loc[last_index, POSITION] = POS_OUT

        #if self.prev_long_buy_position_index is not None:
        #    if (self.sticker_df.loc[last_index, self.ind_price] > self.sticker_df.loc[self.prev_long_buy_position_index, self.ind_price]) \
        #        and self.sticker_df.loc[last_index, POSITION] == POS_SHORT_SELL:
        #            
        #        self.sticker_df.loc[last_index, STOP_LOSS_OUT_SIGNAL] = STOP_LOSS_SHORT
        #        self.sticker_df.loc[last_index, TRADING_ACTION] = ACT_BUY_PREV_SHORT
        #        #self.sticker_df.loc[last_index, CURRENT_CAPITAL] = self.sticker_df.loc[self.prev_long_buy_position_index, CURRENT_CAPITAL] + \
        #        #                                                (self.sticker_df.loc[self.prev_long_buy_position_index, self.ind_price] - self.sticker_df.loc[last_index, self.ind_price]) * \
        #        #                                                (self.sticker_df.loc[self.prev_long_buy_position_index, CURRENT_CAPITAL] /
        #        #                                                self.sticker_df.loc[self.prev_long_buy_position_index, self.ind_price])
        #        #self.sticker_df.loc[last_index, POSITION] = POS_OUT
        #calculate capital and apply stop loss end
        #print(self.sticker_df)
        self.sticker_df.to_csv('sticker_df_log.csv')