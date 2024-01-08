from typing import List
from .PriceDataGeneratorBase import PriceDataGeneratorBase
import pandas as pd
from pandas import DataFrame

from src_tr.main.enums_and_constants.trading_constants import *

class PriceDataGeneratorMain(PriceDataGeneratorBase):

    def __init__(self, recommended_sticker_list):
        super().__init__(recommended_sticker_list)
        self.ind_price = OPEN
        self.out_positions = len(recommended_sticker_list) # TODO: le kell kérni az Alpacáról minden indításnál!
        # Ezt miért kell lekérni minden indításnál?
        #   - nap elején biztosan nem leszünk pozícióban, mert nap végén le kell zárni minden nyitott pozíciót
        #    ha nem zárjuk le őket az aznapi nyereséget elviheti a premarket gap! Az megoldható, ha meghal a program, akkor azonnal kijöjjön minden pozícióból?
        # Lehet csinálni valami teljesen más programot, ami figyeli a kapcsolatot?
        #   - azt meg jó lenne elkerülni, hogy nap közben leálljon a program, de ha mégis megtörténik, azt szeretnénk evvel kezelni?
    
    def get_out_positions(self):
        return self.out_positions

    def increase_out_positions(self):
        self.out_positions = self.out_positions + 1

    def decrease_out_positions(self):
        self.out_positions = self.out_positions - 1


    # Mi lenne ha nem lenne külön sticker_list és sticker_dict?
    # hanem csak egy adattároló, amit elkezdünk feltölteni először a premarket scanner-rel,
    # utána folytatjuk a kereskedés inicializálással, gyakorlatilag evvel ami itt van,
    # majd folyamatosan töltjük a bejövő adatokkal és a pozíciókkal,
    # a végén pedig jó lenne kimenteni (valami olyan adatbázisba, amit mindenki elér) mindent, hogy utána lehessen rajtuk elemzéseket végezni
    def initialize_sticker_dict(self):
        if self.recommended_sticker_list is not None:
            for e in self.recommended_sticker_list:
                self.sticker_dict[e[SYMBOL]] = {
                    STICKER_DF : None,
                    PREV_LONG_BUY_POSITION_INDEX : None,
                    PREV_SHORT_SELL_POSITION_INDEX : None,
                    IND_PRICE : OPEN,
                    # itt talán nem érdemes az IND_PRICE-ot szerepeltetni, hiszen a PDP-ben implementált stratégia az open-nel működik jól
                    PREV_DAY_DATA : {
                        AVG_OPEN : e[AVG_OPEN],
                        STD_OPEN: e[STD_OPEN]
                    }
                }
        else:
            raise ValueError("Recommended sticker list is empty.")
        
    def initialize_additional_columns(self, symbol):
        self.sticker_dict[symbol][STICKER_DF][POSITION] = POS_OUT
        self.sticker_dict[symbol][STICKER_DF][TRADING_ACTION] = ACT_NO_ACTION
        self.sticker_dict[symbol][STICKER_DF][CURRENT_CAPITAL] = 0.0 #TODO: check!
        self.sticker_dict[symbol][STICKER_DF][STOP_LOSS_OUT_SIGNAL] = STOP_LOSS_NONE
        self.sticker_dict[symbol][STICKER_DF][RSI] = None
        self.sticker_dict[symbol][STICKER_DF][OPEN_SMALL_IND_COL] = None
        self.sticker_dict[symbol][STICKER_DF][OPEN_BIG_IND_COL] = None
        self.sticker_dict[symbol][STICKER_DF][OPEN_NORM] = None
        self.sticker_dict[symbol][STICKER_DF][GAIN_LOSS] = None
        self.sticker_dict[symbol][STICKER_DF][GAIN] = None
        self.sticker_dict[symbol][STICKER_DF][LOSS] = None
        self.sticker_dict[symbol][STICKER_DF][AVG_GAIN] = None
        self.sticker_dict[symbol][STICKER_DF][AVG_LOSS] = None
        #-----TODO-----
        # Mi az AMOUNT_SOLD és az AMOUNT_BOUGHT definíciója? Mit értünk alattuk?
        self.sticker_dict[symbol][STICKER_DF][AMOUNT_SOLD] = None
        self.sticker_dict[symbol][STICKER_DF][AMOUNT_BOUGHT] = None
                
    def update_sticker_df(self, minute_bars: List[dict]):
        if minute_bars is not None and len(minute_bars) > 0:
            for bar in minute_bars:
                symbol = bar['S']
                bar_df = DataFrame([bar])
                bar_df.set_index('t', inplace=True)

                if self.sticker_dict[symbol][STICKER_DF] is None:
                    self.sticker_dict[symbol][STICKER_DF] = bar_df
                    self.initialize_additional_columns(symbol)
                elif isinstance(self.sticker_dict[symbol][STICKER_DF], DataFrame):
                    self.sticker_dict[symbol][STICKER_DF] = pd.concat([self.sticker_dict[symbol][STICKER_DF], bar_df])
                else:
                    raise ValueError("Unexpected data structure for the symbol in current_data_window")
        else:
            raise ValueError("Minute bar list is empty.")

    # Ezt hol használjuk és mire való?
    def update_sticker_df_yahoo(self, minute_bars: DataFrame):
        if minute_bars is not None and len(minute_bars) > 0:
            symbol = minute_bars['S'][0]
            #minute_bars.set_index('t', inplace=True)
            if self.sticker_dict[symbol] is None:
                self.sticker_dict[symbol] = minute_bars
            elif isinstance(self.sticker_dict[symbol], DataFrame):
                self.sticker_dict[symbol] = pd.concat([self.sticker_dict[symbol], minute_bars])
            else:
                raise ValueError("Unexpected data structure for the symbol in current_data_window")
        else:
            raise ValueError("Yahoo data is empty.")

    # Ezt hol használjuk?
    def load_watchlist_daily_price_data(self):
        if self.recommended_sticker_list is not None:
            for symbol in self.recommended_sticker_list:

                avg_close = self.sticker_dict[symbol]["c"].mean()
                avg_volume = self.sticker_dict[symbol]["v"].mean()
                max_high = self.sticker_dict[symbol]["h"].max()
                min_low = self.sticker_dict[symbol]["l"].min()
                max_volume = self.sticker_dict[symbol]["v"].max()
                min_volume = self.sticker_dict[symbol]["v"].min()
               
                self.trading_day_sticker_stats = {
                    'avg_close': avg_close,
                    'avg_volume': avg_volume,
                    'price_range_perc': (max_high - min_low) / avg_close * 100,
                    'volume_range_ratio': (max_volume - min_volume) / avg_volume
                    }
                
                self.sticker_data['stickers'][symbol]['trading_day_data'] = pd.DataFrame(self.sticker_dict[symbol])
                self.sticker_data['stickers'][symbol]['trading_day_sticker_stats'] = pd.DataFrame.from_dict(self.trading_day_sticker_stats)
        else: 
            raise ValueError('recommended_sticker_list is empty or None!')