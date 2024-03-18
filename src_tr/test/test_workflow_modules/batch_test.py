import os
from typing import List

from dotenv import load_dotenv
from datetime import date
import traceback

from src_tr.test.test_workflow_modules.TestTradingClientDivided import TestTradingClientDivided
from src_tr.test.test_workflow_modules.test_utils import run_test_experiment
from src_tr.test.test_workflow_modules.test_utils import get_polygon_local_db_symbols, get_polygon_trading_day_data
from src_tr.main.utils.DataManager import DataManager
from src_tr.main.utils.data_loaders import load_MACD_days_polygon_data
from src_tr.main.scanners.PreMarketScannerMain import PreMarketScannerMain
from src_tr.main.data_generators.PriceDataGeneratorMain import PriceDataGeneratorMain
from src_tr.main.trading_algorithms.TradingAlgorithmMain import TradingAlgorithmMain
from src_tr.test.test_workflow_modules.TestTradingManagerDivided import TestTradingManagerDivided
from src_tr.main.data_sources.run_params import param_dict

from config import config

load_dotenv()
SYMBOL_CSV_PATH = os.environ["SYMBOL_CSV_PATH"]
ALPACA_KEY = os.environ["ALPACA_KEY"]
ALPACA_SECRET_KEY = os.environ["ALPACA_SECRET_KEY"]
DB_PATH = config["db_path"]

MODE = 'POLYGON_LOCAL_DB'
#if MODE == 'LOCAL_YF_DB':
#    trading_dates, scanning_days = get_possible_local_yf_trading_days()

def run():
    for id, params in param_dict.items():
        daily_folder_dates = os.listdir(config["resource_paths"]["polygon"]["daily_data_output_folder"])
        trading_dates = [date.fromisoformat(d.replace("_","-")) for d in daily_folder_dates][-40:]
        trading_dates.sort()
        print(trading_dates)
        run_id = id
        algo_params = params["algo_params"]
        scanner_params = params["scanner_params"]
        scanner_macd_long = scanner_params["windows"]["long"]
        
        for i in range(scanner_macd_long, len(trading_dates)-1):
            trading_day = trading_dates[i]
            scanning_day = trading_dates[i-1]
            macd_date_list = trading_dates[i-scanner_macd_long : i]
            try:
                data_manager = DataManager(mode=MODE, trading_day=trading_day, scanning_day=scanning_day, run_id=run_id)
                
                input_symbols: List[str] = get_polygon_local_db_symbols(trading_day=trading_day, only_sp_500=True)

                #TODO: ennek majd a param-fájlból kell jönnie
                run_parameters = \
                    {
                        'run_id': run_id,
                        'trading_day': trading_day.strftime('%Y_%m_%d'),
                        'symbol_csvs': SYMBOL_CSV_PATH,
                        'init_cash': 10000,
                        'lower_price_boundary': 10,
                        'upper_price_boundary': 400,
                        'price_range_perc_cond': 5,
                        'avg_volume_cond': 10000,
                        'ma_short': algo_params["entry_windows"]["short"],
                        'ma_long': algo_params["entry_windows"]["long"],
                        'entry_signal': algo_params["entry_windows"]["signal"] if "signal" in algo_params["entry_windows"] else 0.0,
                        'epsilon': algo_params["entry_windows"]["epsilon"] if "epsilon" in algo_params["entry_windows"] else 0.0,
                        'rsi_len': 12,
                        'stop_loss_perc': 0.0,
                        'macd_long' : scanner_params["windows"]["long"],
                        'macd_short' : scanner_params["windows"]["short"],
                        'signal_line' : scanner_params["windows"]["signal"]
                    }

                data_manager.create_daily_dirs()
                data_manager.save_params(params=run_parameters)
                daily_dir_name = f"{run_id}/{data_manager.daily_dir_name}"

                data_loader_func = load_MACD_days_polygon_data
                scanner = PreMarketScannerMain(run_id=run_id,
                                               data_loader_func=data_loader_func,
                                               daily_dir_name=daily_dir_name,
                                               trading_day=trading_day,
                                               scanning_day=scanning_day,
                                               scanner_params=scanner_params,
                                               macd_date_list=macd_date_list,
                                               symbols=input_symbols,
                                               lower_price_boundary=run_parameters['lower_price_boundary'],
                                               upper_price_boundary=run_parameters['upper_price_boundary'],
                                               price_range_perc_cond=run_parameters['price_range_perc_cond'],
                                               avg_volume_cond=run_parameters['avg_volume_cond'])

                recommended_symbol_list: List[dict] = scanner.recommend_premarket_watchlist()

                data_manager.recommended_symbol_list = recommended_symbol_list
                
                trading_client = TestTradingClientDivided(init_cash=run_parameters['init_cash'],
                                                        symbol_list=recommended_symbol_list,
                                                        mode='same')
                
                #trading_client = TestTradingClient(init_cash=run_parameters['init_cash'],
                #                                   symbol_list=data_manager.recommended_symbol_list)
                
                trading_client.initialize_positions()
                
                data_generator = PriceDataGeneratorMain(recommended_symbol_list=recommended_symbol_list)
                        
                trading_algorithm = TradingAlgorithmMain(trading_day=trading_day, 
                                                         daily_dir_name=daily_dir_name, 
                                                         run_id=run_id)
                
                trading_manager = TestTradingManagerDivided(data_generator=data_generator,
                                                            recommended_symbol_list=recommended_symbol_list,
                                                            trading_algorithm=trading_algorithm,
                                                            algo_params=algo_params,
                                                            trading_client=trading_client,
                                                            api_key='test_key',
                                                            secret_key='test_secret')
                
                trading_manager.initialize_symbol_dict()

                # all_symbols_daily_data = get_all_symbols_daily_data(recommended_symbol_list=recommended_symbol_list,
                #                                                     s=start,
                #                                                     e=end,
                #                                                     alpaca_key=ALPACA_KEY,
                #                                                     alpaca_secret_key=ALPACA_SECRET_KEY)

                #all_symbols_daily_data = get_all_symbols_daily_data_yf_db(recommended_symbol_list=recommended_symbol_list,
                #                                                          s=trading_day)
                
                all_symbols_daily_data = get_polygon_trading_day_data(recommended_symbols=recommended_symbol_list,
                                                                      trading_day=trading_day.strftime("%Y_%m_%d"))
                                                                    #limit=240
                
                run_test_experiment(all_symbols_daily_data=all_symbols_daily_data, trading_manager=trading_manager)

            except Exception:
                traceback.print_exc()

            finally:
                try:
                    data_manager.save_daily_statistics_and_aggregated_plots(recommended_symbols=scanner.recommended_symbols,
                                                                            symbol_dict=trading_manager.symbol_dict)
                    data_manager.save_daily_charts(symbol_dict=trading_manager.symbol_dict)
                    print('Experiment ran successfully, with run id: ', data_manager.run_id, 'and run parameters', data_manager.run_parameters)
                except Exception:
                    traceback.print_exc()

                del data_manager
                del scanner
                del trading_client
                del data_generator
                del trading_algorithm
                del trading_manager
                
if __name__ == "__main__":
    run()
