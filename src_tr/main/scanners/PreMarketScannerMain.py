import os
from typing import List
import pandas as pd
import numpy as np
from pandas import DataFrame
from joblib import Parallel, delayed
import logging
import traceback

from config import config


class PreMarketScannerMain():

    def __init__(self,
                 data_loader_func,
                 trading_day,
                 scanning_day,
                 symbols,
                 scanner_params,
                 run_id,
                 daily_dir_name,
                 key=None,
                 secret_key=None,
                 lower_price_boundary=None,
                 upper_price_boundary=None,
                 price_range_perc_cond=None,
                 avg_volume_cond=None,
                 macd_date_list=None):
        self.data_loader_func = data_loader_func
        self.trading_day = trading_day
        self.scanning_day = scanning_day
        self.symbols = symbols
        self.scanner_params = scanner_params
        self.macd_date_list = macd_date_list
        self.run_id = run_id
        self.daily_dir_name = daily_dir_name
        self.key = key
        self.secret_key = secret_key
        self.recommended_symbols = None
        self.pre_market_stats = None
        #TODO: kuka?
        self.lower_price_boundary = lower_price_boundary
        self.upper_price_boundary = upper_price_boundary
        self.price_range_perc_cond = price_range_perc_cond
        self.avg_volume_cond = avg_volume_cond
        
    def _assess_uptrend(self, macd_days_symbol_history):
        macd_ema_short = self.scanner_params["windows"]["short"]
        macd_ema_long = self.scanner_params["windows"]["long"]
        signal_line_ema = self.scanner_params["windows"]["signal"]
        macd_df = pd.DataFrame()
        for date in self.macd_date_list:
            df: pd.DataFrame = macd_days_symbol_history[macd_days_symbol_history['date'] == date]
            if macd_df.empty:
                macd_df = df.tail(1)
            else:
                macd_df = pd.concat([macd_df, df.tail(1)])
                
        #NOTE: close helyett adj_close
        macd_df[f"EMA{macd_ema_short}"] = macd_df['close'].ewm(span=macd_ema_short, adjust=False).mean()
        macd_df[f"EMA{macd_ema_long}"] = macd_df['close'].ewm(span=macd_ema_long, adjust=False).mean()
        macd_df['MACD'] = macd_df[f"EMA{macd_ema_short}"] - macd_df[f"EMA{macd_ema_long}"]
        macd_df[f"signal_EMA{signal_line_ema}"] = macd_df['MACD'].ewm(span=signal_line_ema, adjust=False).mean()
        #NOTE: histogram = macd_df['MACD'] - macd_df['signal_line'] ?
        
        if macd_df.iloc[-3]['MACD'] < macd_df.iloc[-3][f"signal_EMA{signal_line_ema}"] and \
            macd_df.iloc[-2]['MACD'] > macd_df.iloc[-2][f"signal_EMA{signal_line_ema}"] and \
                macd_df.iloc[-1]['MACD'] > macd_df.iloc[-1][f"signal_EMA{signal_line_ema}"]:
            logging.info("MACD line crossed above signal line")
            return True
        else:
            logging.info("MACD line crossed below signal line")
            return False
            
    def get_pre_market_stats(self, symbol: str) -> dict:
        try:
            symbol_history: pd.DataFrame = None
            scanning_day_symbol_history: pd.DataFrame = None
            #possible_uptrend_for_trading_day = None
            try:
                if self.macd_date_list is not None and len(self.macd_date_list) > 0:
                    if self.data_loader_func.__name__ == "load_MACD_days_polygon_data":
                        symbol_history = self.data_loader_func(symbol, self.macd_date_list)
                    if symbol_history is not None and not symbol_history.empty:
                        scanning_day_symbol_history = symbol_history[symbol_history['date'] == self.scanning_day]
                elif self.macd_date_list is None:
                    if self.data_loader_func.__name__ == "download_scanning_day_alpaca_data":
                        symbol_history = self.data_loader_func(symbol, self.key, self.secret_key, 
                                                            self.scanning_day, self.trading_day)
                        scanning_day_symbol_history = symbol_history
            except:
                traceback.print_exc()
                    
            if symbol_history is not None and not symbol_history.empty:

                # MACD
                #possible_uptrend_for_trading_day = self._assess_uptrend(macd_days_symbol_history=symbol_history)

                # volatility+volume/transactions
                scanning_day_symbol_history["percentage_change"] = \
                    (scanning_day_symbol_history['close'] - scanning_day_symbol_history['close'].shift(1)) / scanning_day_symbol_history['close'].shift(1) * 100
                volatility = scanning_day_symbol_history["percentage_change"].std()
                avg_transaction = scanning_day_symbol_history["transactions"].mean()

                # Kovi-féle eredetiek:
                avg_open = scanning_day_symbol_history['open'].mean()
                median_open = scanning_day_symbol_history['open'].median()
                std_open = scanning_day_symbol_history['open'].std()

                avg_close = scanning_day_symbol_history['close'].mean()
                median_close = scanning_day_symbol_history['close'].median()

                high_max = scanning_day_symbol_history['high'].max()
                low_min = scanning_day_symbol_history['low'].min()
                minute_oc_price_diff = scanning_day_symbol_history['open'] - scanning_day_symbol_history['close']
                minute_oc_price_diff_avg = np.mean(minute_oc_price_diff)
                minute_oc_price_diff_median = np.median(minute_oc_price_diff)
                minute_oc_price_diff_std = np.std(minute_oc_price_diff)

                avg_volume = scanning_day_symbol_history['volume'].mean()
                median_volume = scanning_day_symbol_history['volume'].median()
                volume_max = scanning_day_symbol_history['volume'].max()
                volume_min = scanning_day_symbol_history['volume'].min()

                price_range_perc = 0
                volume_range_ratio = 0
                close_monetary_avg_volume = 0
                close_monetary_min_volume = (scanning_day_symbol_history['close'] * scanning_day_symbol_history['volume']).min()

                if not pd.isnull(avg_volume) and avg_volume != 0:
                    price_range_perc = (high_max - low_min) / ((high_max + low_min) / 2) * 100
                    volume_range_ratio = (volume_max - volume_min) / avg_volume
                    close_monetary_avg_volume = median_close * median_volume

                return {
                    'symbol': symbol,
                    #'is_uptrend' : possible_uptrend_for_trading_day,
                    'volatility' : volatility,
                    'avg_transaction' : avg_transaction,
                    'avg_open': avg_open,
                    'median_open': median_open,
                    'std_open': std_open,
                    'avg_close': avg_close,
                    'median_close': median_close,
                    'high_max': high_max,
                    'low_min': low_min,
                    'minute_oc_price_diff_avg': minute_oc_price_diff_avg,
                    'minute_oc_price_diff_median': minute_oc_price_diff_median,
                    'minute_oc_price_diff_std': minute_oc_price_diff_std,
                    'avg_volume': avg_volume,
                    'median_volume': median_volume,
                    'max_volume': volume_max,
                    'min_volume': volume_min,
                    'close_monetary_avg_volume': close_monetary_avg_volume,
                    'close_monetary_min_volume': close_monetary_min_volume,
                    'price_range_perc': price_range_perc,
                    'volume_range_ratio': volume_range_ratio
                }
            else:
                return None
        except:
            traceback.print_exc()
            return None

    def calculate_filtering_stats(self) -> List:
        try:
            pre_market_symbol_stats = \
                Parallel(n_jobs=-1)(delayed(self.get_pre_market_stats)(symbol) for symbol in self.symbols)

            #NOTE: debuggoláshoz
            #pre_market_symbol_stats = [(lambda x : self.get_pre_market_stats(x))(x) for x in self.symbols]
            
            pre_market_symbol_stats = [stats for stats in pre_market_symbol_stats if stats is not None]

            stats_df = pd.DataFrame.from_records(pre_market_symbol_stats)
            date = self.trading_day.strftime('%Y_%m_%d')
            
            if stats_df is not None and not stats_df.empty:
                self.pre_market_stats = stats_df
                self.pre_market_stats.to_csv(\
                    f"{config['output_stats']}/{self.daily_dir_name}/daily_files/scanner_stats/pre_market_stats_{date}.csv", index=False)
            else:
                logging.error(f"Failed to create pre-market stats for trading day: %s", date)
        except:
            traceback.print_exc()

    def recommend_premarket_watchlist(self) -> List[dict]:
        self.calculate_filtering_stats()
        self.recommended_symbols = self.pre_market_stats.sort_values(by=['avg_transaction'], ascending=False)
        self.recommended_symbols = self.recommended_symbols.head(20)

        ##self.pre_market_stats['volatility_rank'] = self.pre_market_stats['volatility'].rank(ascending=False)
        ##self.pre_market_stats['transactions_rank'] = self.pre_market_stats['avg_transaction'].rank(ascending=False)
        ##self.pre_market_stats['combined_rank'] = self.pre_market_stats['volatility_rank'] + self.pre_market_stats['transactions_rank']
        #self.recommended_symbols = self.recommended_symbols.sort_values(by=['avg_volume'], ascending=False)
        #self.recommended_symbols = self.recommended_symbols.sort_values(by=['volatility'], ascending=False)
        #self.recommended_symbols = self.pre_market_stats[(self.pre_market_stats["is_uptrend"] == True)]
        
        #self.recommended_symbols = self.pre_market_stats.sort_values(by=['avg_transaction'], ascending=False)
        #self.recommended_symbols = self.recommended_symbols[(self.recommended_symbols['avg_transaction'] > 300.0)]

        
        # NOTE: régi
        #self.recommended_symbols: pd.DataFrame = self.pre_market_stats[
        #    (self.lower_price_boundary < self.pre_market_stats['avg_open']) & \
        #    (self.pre_market_stats['avg_open'] < self.upper_price_boundary) & \
        #    (self.price_range_perc_cond < self.pre_market_stats['price_range_perc']) & \
        #    (self.avg_volume_cond < self.pre_market_stats['avg_volume'])]

        self.recommended_symbols.to_csv(\
            f"{config['output_stats']}/{self.daily_dir_name}/daily_files/scanner_stats/recommended_symbols_{self.trading_day.strftime('%Y_%m_%d')}.csv", index=False)
        symbol_dict_list = []
        if self.recommended_symbols is not None:
            for index, row in self.recommended_symbols.iterrows():
                st_dict = {
                    'symbol': row['symbol'],
                    'avg_open': row['avg_open'],
                    'std_open': row['std_open']
                }
                symbol_dict_list.append(st_dict)
                # symbol_dict_list.append(row['symbol'])
        return symbol_dict_list



