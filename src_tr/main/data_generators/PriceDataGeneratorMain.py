from typing import List
from .PriceDataGeneratorBase import PriceDataGeneratorBase
import pandas as pd
from pandas import DataFrame

from src_tr.main.enums_and_constants.trading_constants import *

class PriceDataGeneratorMain(PriceDataGeneratorBase):

    def __init__(self, recommended_symbol_list):
        super().__init__(recommended_symbol_list)
        self.ind_price = OPEN
        # Mi a definíciója az out_position-nek? Ha azt jelenti, hogy hány symbol nincsen pozícióban,
        # akkor nem lenne egyszerűbb azt nézni hány symbol van pozícióban?
        self.out_positions = len(recommended_symbol_list) # TODO: le kell kérni az Alpacáról minden indításnál!
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


    # Mi lenne ha nem lenne külön symbol_list és symbol_dict?
    # hanem csak egy adattároló, amit elkezdünk feltölteni először a premarket scanner-rel,
    # utána folytatjuk a kereskedés inicializálással, gyakorlatilag evvel ami itt van,
    # majd folyamatosan töltjük a bejövő adatokkal és a pozíciókkal,
    # a végén pedig jó lenne kimenteni (valami olyan adatbázisba, amit mindenki elér) mindent, hogy utána lehessen rajtuk elemzéseket végezni
    def initialize_symbol_dict(self):
        if self.recommended_symbol_list is not None:
            for e in self.recommended_symbol_list:
                self.symbol_dict[e[SYMBOL]] = {
                    SYMBOL_DF : None,
                    PREV_LONG_BUY_POSITION_INDEX : None,
                    PREV_SHORT_SELL_POSITION_INDEX : None,
                    IND_PRICE : OPEN,
                    PREV_DAY_DATA : {
                        AVG_OPEN : e[AVG_OPEN],
                        STD_OPEN: e[STD_OPEN]
                    }
                }
        else:
            raise ValueError("Recommended symbol list is empty.")
        
    def initialize_additional_columns(self, symbol):
        self.symbol_dict[symbol][SYMBOL_DF][POSITION] = POS_OUT
        self.symbol_dict[symbol][SYMBOL_DF][TRADING_ACTION] = ACT_NO_ACTION
        self.symbol_dict[symbol][SYMBOL_DF][CURRENT_CAPITAL] = 0.0 #TODO: check!
        self.symbol_dict[symbol][SYMBOL_DF][STOP_LOSS_OUT_SIGNAL] = STOP_LOSS_NONE
        self.symbol_dict[symbol][SYMBOL_DF][RSI] = None
        self.symbol_dict[symbol][SYMBOL_DF][OPEN_SMALL_IND_COL] = None
        self.symbol_dict[symbol][SYMBOL_DF][OPEN_BIG_IND_COL] = None
        self.symbol_dict[symbol][SYMBOL_DF][OPEN_NORM] = None
        self.symbol_dict[symbol][SYMBOL_DF][GAIN_LOSS] = None
        self.symbol_dict[symbol][SYMBOL_DF][GAIN] = None
        self.symbol_dict[symbol][SYMBOL_DF][LOSS] = None
        self.symbol_dict[symbol][SYMBOL_DF][AVG_GAIN] = None
        self.symbol_dict[symbol][SYMBOL_DF][AVG_LOSS] = None
        #-----TODO-----
        # Mi az AMOUNT_SOLD és az AMOUNT_BOUGHT definíciója? Mit értünk alattuk?
        self.symbol_dict[symbol][SYMBOL_DF][AMOUNT_SOLD] = None
        self.symbol_dict[symbol][SYMBOL_DF][AMOUNT_BOUGHT] = None
                
    def update_symbol_df(self, minute_bars: List[dict]):
        if minute_bars is not None and len(minute_bars) > 0:
            for bar in minute_bars:
                symbol = bar['S']
                bar_df = DataFrame([bar])
                bar_df.set_index('t', inplace=True)

                if self.symbol_dict[symbol][SYMBOL_DF] is None:
                    self.symbol_dict[symbol][SYMBOL_DF] = bar_df
                    self.initialize_additional_columns(symbol)
                elif isinstance(self.symbol_dict[symbol][SYMBOL_DF], DataFrame):
                    self.symbol_dict[symbol][SYMBOL_DF] = pd.concat([self.symbol_dict[symbol][SYMBOL_DF], bar_df])
                else:
                    raise ValueError("Unexpected data structure for the symbol in current_data_window")
        else:
            raise ValueError("Minute bar list is empty.")

    # Ezt hol használjuk és mire való?
    def update_symbol_df_yahoo(self, minute_bars: DataFrame):
        if minute_bars is not None and len(minute_bars) > 0:
            symbol = minute_bars['S'][0]
            #minute_bars.set_index('t', inplace=True)
            if self.symbol_dict[symbol] is None:
                self.symbol_dict[symbol] = minute_bars
            elif isinstance(self.symbol_dict[symbol], DataFrame):
                self.symbol_dict[symbol] = pd.concat([self.symbol_dict[symbol], minute_bars])
            else:
                raise ValueError("Unexpected data structure for the symbol in current_data_window")
        else:
            raise ValueError("Yahoo data is empty.")

    # Ezt hol használjuk?
    # Ha jól értem, hogy ez a trading_day-re vontakozó scanner statisztika, akkor ez is kiszámítható az általános kiszervezett statisztika számolóval majd.
    def load_watchlist_daily_price_data(self):
        if self.recommended_symbol_list is not None:
            for symbol in self.recommended_symbol_list:

                avg_close = self.symbol_dict[symbol]["c"].mean()
                avg_volume = self.symbol_dict[symbol]["v"].mean()
                max_high = self.symbol_dict[symbol]["h"].max()
                min_low = self.symbol_dict[symbol]["l"].min()
                max_volume = self.symbol_dict[symbol]["v"].max()
                min_volume = self.symbol_dict[symbol]["v"].min()
               
                self.trading_day_symbol_stats = {
                    'avg_close': avg_close,
                    'avg_volume': avg_volume,
                    'price_range_perc': (max_high - min_low) / avg_close * 100,
                    'volume_range_ratio': (max_volume - min_volume) / avg_volume
                    }
                
                self.symbol_data['symbols'][symbol]['trading_day_data'] = pd.DataFrame(self.symbol_dict[symbol])
                self.symbol_data['symbols'][symbol]['trading_day_symbol_stats'] = pd.DataFrame.from_dict(self.trading_day_symbol_stats)
        else: 
            raise ValueError('recommended_symbol_list is empty or None!')