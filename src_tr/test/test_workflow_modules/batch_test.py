import os
from typing import List
from dotenv import load_dotenv
from datetime import datetime, timedelta
import traceback

from src_tr.test.test_workflow_modules.TestTradingClientDivided import TestTradingClientDivided
from src_tr.main.utils.test_utils import run_test_experiment

from src_tr.main.utils.test_utils import get_yf_local_db_symbols, get_all_symbols_daily_data_yf_db, get_polygon_local_db_symbols, get_polygon_trading_day_data
from src_tr.main.utils.local_yf_db_handler import get_possible_local_yf_trading_days

from src_tr.main.checks.checks import check_trading_day
from src_tr.main.utils.utils import calculate_scanning_day, get_nasdaq_symbols
from src_tr.main.utils.data_management import DataManager
from src_tr.main.scanners.PreMarketScannerPolygonDB import PreMarketScannerPolygonDB

from src_tr.main.data_generators.PriceDataGeneratorMain import PriceDataGeneratorMain
from src_tr.main.trading_algorithms.TradingAlgorithmWithStopLossPrevPrice import TradingAlgorithmWithStopLossPrevPrice
from src_tr.test.test_workflow_modules.TestTradingManagerDivided import TestTradingManagerDivided

from config import config

load_dotenv()
SYMBOL_CSV_PATH = os.environ["SYMBOL_CSV_PATH"]
ALPACA_KEY = os.environ["ALPACA_KEY"]
ALPACA_SECRET_KEY = os.environ["ALPACA_SECRET_KEY"]
DB_PATH = config["db_path"]

RUN_ID = 'only_short_ind'

MODE = 'POLYGON_LOCAL_DB'
#if MODE == 'LOCAL_YF_DB':
#    trading_dates, scanning_days = get_possible_local_yf_trading_days()
    
daily_folder_dates = os.listdir(config["resource_paths"]["polygon"]["daily_data_output_folder"])
trading_dates = [datetime.strptime(date,"%Y_%m_%d") for date in daily_folder_dates]
trading_dates.sort()

#trading_days = trading_dates[1:]
#scanning_days = trading_dates[:-1]

# range
trading_days = [trading_dates[35]]
scanning_days = [trading_dates[34]]

for scanning_day, trading_day in zip(scanning_days, trading_days):
    try:
        data_manager = DataManager(mode=MODE, trading_day=trading_day, scanning_day=scanning_day, run_id=RUN_ID, db_path=DB_PATH)
        
        input_symbols: List[str] = get_polygon_local_db_symbols(trading_day=trading_day, only_sp_500=True)

        run_parameters = \
            {
                'run_id': RUN_ID,
                'trading_day': trading_day.strftime('%Y_%m_%d'),
                'symbol_csvs': SYMBOL_CSV_PATH,
                'init_cash': 10000,
                'lower_price_boundary': 10,
                'upper_price_boundary': 400,
                'price_range_perc_cond': 5,
                'avg_volume_cond': 10000,
                'ma_short': 5,
                'ma_long': 12,
                'epsilon': 0.0015,
                'rsi_len': 12,
                'stop_loss_perc': 0.0
                #TODO: 'rsi_threshold' : 20
            }

        data_manager.create_daily_dirs()
        data_manager.save_params(params=run_parameters)

        scanner = PreMarketScannerPolygonDB(run_id=RUN_ID, 
                                    trading_day=data_manager.trading_day,
                                    scanning_day=data_manager.scanning_day,
                                    symbols=input_symbols,
                                    lower_price_boundary=run_parameters['lower_price_boundary'],
                                    upper_price_boundary=run_parameters['upper_price_boundary'],
                                    price_range_perc_cond=run_parameters['price_range_perc_cond'],
                                    avg_volume_cond=run_parameters['avg_volume_cond'])
        
        scanner.calculate_filtering_stats()
        recommended_symbol_list: List[dict] = scanner.recommend_premarket_watchlist()

        data_manager.recommended_symbol_list = recommended_symbol_list
        
        trading_client = TestTradingClientDivided(init_cash=run_parameters['init_cash'],
                                                  symbol_list=recommended_symbol_list,
                                                  mode='same')
        
        #trading_client = TestTradingClient(init_cash=run_parameters['init_cash'],
        #                                   symbol_list=data_manager.recommended_symbol_list)
        
        trading_client.initialize_positions()
        
        data_generator = PriceDataGeneratorMain(recommended_symbol_list=recommended_symbol_list)
                
        trading_algorithm = TradingAlgorithmWithStopLossPrevPrice(ma_short=run_parameters['ma_short'],
                                                 ma_long=run_parameters['ma_long'],
                                                 epsilon=run_parameters['epsilon'],
                                                 rsi_len=run_parameters['rsi_len'],
                                                 stop_loss_perc=run_parameters['stop_loss_perc'],
                                                 trading_day=data_manager.trading_day,
                                                 run_id=RUN_ID,
                                                 db_path=DB_PATH) # TODO: rsi_threshold
        
        trading_manager = TestTradingManagerDivided(data_generator=data_generator,
                                             trading_algorithm=trading_algorithm,
                                             trading_client=trading_client,
                                             api_key='test_key',
                                             secret_key='test_secret')
        
        data_generator.initialize_symbol_dict()

        # all_symbols_daily_data = get_all_symbols_daily_data(recommended_symbol_list=recommended_symbol_list,
        #                                                     s=start,
        #                                                     e=end,
        #                                                     alpaca_key=ALPACA_KEY,
        #                                                     alpaca_secret_key=ALPACA_SECRET_KEY)

        #all_symbols_daily_data = get_all_symbols_daily_data_yf_db(recommended_symbol_list=recommended_symbol_list,
        #                                                          s=trading_day)
        
        all_symbols_daily_data = get_polygon_trading_day_data(recommended_symbols=recommended_symbol_list,
                                                              trading_day=trading_day.strftime("%Y_%m_%d"),
                                                              limit=240) # NOTE: 240 = 4h
        
        # limit_trading

        run_test_experiment(all_symbols_daily_data=all_symbols_daily_data, trading_manager=trading_manager)

    except Exception as e:
        traceback.print_exc()

    finally:
        data_manager.save_daily_statistics_and_aggregated_plots(recommended_symbols=scanner.recommended_symbols,
                                                                symbol_dict=data_generator.symbol_dict)
        data_manager.save_daily_charts(symbol_dict=data_generator.symbol_dict)
        print('Experiment ran successfully, with run id: ', data_manager.run_id, 'and run parameters', data_manager.run_parameters)
        
        del data_manager
        del scanner
        del trading_client
        del data_generator
        del trading_algorithm
        del trading_manager