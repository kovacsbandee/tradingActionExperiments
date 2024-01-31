import os
from typing import List
from dotenv import load_dotenv
from datetime import datetime, timedelta

from src_tr.test.test_workflow_modules.TestTradingClient import TestTradingClient
from src_tr.test.test_workflow_modules.TestTradingClientDivided import TestTradingClientDivided
from src_tr.main.utils.test_utils import get_all_symbols_daily_data_base, run_test_experiment

from src_tr.main.utils.test_utils import get_yf_local_db_symbols, get_all_symbols_daily_data_yf_db

from src_tr.main.checks.checks import check_trading_day
from src_tr.main.utils.utils import calculate_scanning_day, get_nasdaq_symbols
from src_tr.main.utils.data_management import DataManager
from src_tr.main.utils.plots import create_candle_stick_chart_w_indicators_for_trendscalping_for_mass_experiments, plot_daily_statistics
from src_tr.main.scanners.PreMarketScanner import PreMarketScanner
from src_tr.main.scanners.PreMarketScannerYFDB import PreMarketScannerYFDB
#from src_tr.main.scanners.PreMarketDumbScanner import PreMarketDumbScanner
from src_tr.main.scanners.PreMarketPolygonScanner import PreMarketPolygonScanner

from src_tr.main.data_generators.PriceDataGeneratorMain import PriceDataGeneratorMain
from src_tr.main.trading_algorithms.TradingAlgorithmWithStopLoss import TradingAlgorithmWithStopLoss
from src_tr.main.trading_algorithms.TradingAlgorithmWithStopLossPrevPrice import TradingAlgorithmWithStopLossPrevPrice
from src_tr.test.test_workflow_modules.TestTradingManager import TestTradingManager
from src_tr.test.test_workflow_modules.TestTradingManagerDivided import TestTradingManagerDivided

# 1) Scanner inicializálása -> watchlist létrehozás
load_dotenv()
SYMBOL_CSV_PATH = os.environ["SYMBOL_CSV_PATH"]
ALPACA_KEY = os.environ["ALPACA_KEY"]
ALPACA_SECRET_KEY = os.environ["ALPACA_SECRET_KEY"]
DB_PATH = os.environ['DB_PATH']
RUN_ID = 'DEV_RUN_ID_valami'

for start in [datetime(2023, 9, 20, 0, 0), datetime(2023, 9, 21, 0, 0)]:
    try:
        start = start + timedelta(hours=0) + timedelta(minutes=00)
        end = start + timedelta(hours=23) + timedelta(minutes=59)
        trading_day = check_trading_day(start)
        scanning_day = calculate_scanning_day(trading_day)
        
        data_manager = DataManager(trading_day=trading_day, scanning_day=scanning_day, run_id=RUN_ID, db_path=DB_PATH)
        
        #input_symbols = get_nasdaq_symbols(file_path=SYMBOL_CSV_PATH)[0:100]

        scanning_day_yf_data, input_symbols = get_yf_local_db_symbols(start=start)

        run_parameters = \
            {
                'run_id': RUN_ID,
                'trading_day': start.strftime('%Y_%m_%d'),
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
                #'rsi_threshold': 20,
                #'rsi_minutes_before_trading_start': 45
            }

        data_manager.create_daily_dirs()
        data_manager.save_params(params=run_parameters)

        # Professional scanner:
        # scanner = PreMarketScanner(trading_day=data_manager.trading_day,
        #                            scanning_day=data_manager.scanning_day,
        #                            symbols=input_symbols,
        #                            lower_price_boundary=run_parameters['lower_price_boundary'],
        #                            upper_price_boundary=run_parameters['upper_price_boundary'],
        #                            price_range_perc_cond=run_parameters['price_range_perc_cond'],
        #                            avg_volume_cond=run_parameters['avg_volume_cond'])

        scanner = PreMarketScannerYFDB(trading_day=data_manager.trading_day,
                                   scanning_day=data_manager.scanning_day,
                                   symbols=input_symbols,
                                   lower_price_boundary=run_parameters['lower_price_boundary'],
                                   upper_price_boundary=run_parameters['upper_price_boundary'],
                                   price_range_perc_cond=run_parameters['price_range_perc_cond'],
                                   avg_volume_cond=run_parameters['avg_volume_cond'])


        # Polygon scanner:
        # scanner = PreMarketPolygonScanner(trading_day=data_manager.trading_day,
        #                                   scanning_day=data_manager.scanning_day,
        #                                   symbols=input_symbols,
        #                                   lower_price_boundary=run_parameters['lower_price_boundary'],
        #                                   upper_price_boundary=run_parameters['upper_price_boundary'],
        #                                   price_range_perc_cond=run_parameters['price_range_perc_cond'],
        #                                   avg_volume_cond=run_parameters['avg_volume_cond'])
        
        
        # Dumb scanner:
        #dumb_symbols = ['MARA', 'RIOT', 'MVIS', 'SOS', 'CAN', 'EBON', 'BTBT', 'HUT', 'EQOS', 'MOGO', 'SUNW', 'XNET', 'PHUN', 'IDEX', 'ZKIN', 'SIFY', 'SNDL', 'NCTY', 'OCGN', 'NIO', 'FCEL', 'PLUG', 'TSLA', 'AAPL', 'AMZN', 'MSFT', 'GOOG', 'FB', 'GOOGL', 'NVDA', 'PYPL', 'ADBE', 'INTC', 'CMCSA', 'CSCO', 'NFLX', 'PEP', 'AVGO', 'TXN', 'COST', 'QCOM', 'TMUS', 'AMGN', 'CHTR', 'SBUX', 'AMD', 'INTU', 'ISRG', 'AMAT', 'MU', 'BKNG', 'MDLZ', 'ADP', 'GILD', 'CSX', 'FISV', 'VRTX', 'ATVI', 'ADSK', 'REGN', 'ILMN', 'BIIB', 'MELI', 'LRCX', 'JD', 'ADI', 'NXPI', 'ASML', 'KHC', 'MRNA', 'EA', 'BIDU', 'WBA', 'MAR', 'LULU', 'EXC', 'ROST', 'WDAY', 'KLAC', 'CTSH', 'ORLY', 'SNPS', 'DOCU', 'IDXX', 'SGEN', 'DXCM', 'PCAR', 'CDNS', 'XLNX', 'ANSS', 'NTES', 'MNST', 'VRSK', 'ALXN', 'FAST', 'SPLK', 'CPRT', 'CDW', 'PAYX', 'MXIM', 'SWKS', 'INCY', 'CHKP', 'TCOM', 'CTXS', 'VRSN', 'SGMS', 'DLTR', 'CERN', 'ULTA', 'FOXA', 'FOX', 'NTAP', 'WDC', 'TTWO', 'EXPE', 'XEL', 'MCHP', 'CTAS', 'MXL', 'WLTW', 'ANET', 'BMRN']
        # scanner = PreMarketDumbScanner(trading_day=data_manager.trading_day,
        #                                scanning_day=data_manager.scanning_day,
        #                                symbols=input_symbols,
        #                                lower_price_boundary=run_parameters['lower_price_boundary'],
        #                                upper_price_boundary=run_parameters['upper_price_boundary'],
        #                                price_range_perc_cond=run_parameters['price_range_perc_cond'],
        #                                avg_volume_cond=run_parameters['avg_volume_cond'])
        
        
        # initialize symbol list:
        
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
        
        # Trading algorithm with stop loss compared to the last price when opening the position:
        # trading_algorithm = TradingAlgorithmWithStopLoss(ma_short=run_parameters['ma_short'],
        #                                 ma_long=run_parameters['ma_long'],
        #                                 epsilon=run_parameters['epsilon'],
        #                                 rsi_len=run_parameters['rsi_len'],
        #                                 stop_loss_perc=run_parameters['stop_loss_perc'],
        #                                 trading_day=data_manager.trading_day,
        #                                 run_id=RUN_ID,
        #                                 db_path=DB_PATH)
        
        # Trading algorithm with stop loss compared to the previous price:
        trading_algorithm = TradingAlgorithmWithStopLossPrevPrice(ma_short=run_parameters['ma_short'],
                                                 ma_long=run_parameters['ma_long'],
                                                 epsilon=run_parameters['epsilon'],
                                                 rsi_len=run_parameters['rsi_len'],
                                                 stop_loss_perc=run_parameters['stop_loss_perc'],
                                                 trading_day=data_manager.trading_day,
                                                 run_id=RUN_ID,
                                                 db_path=DB_PATH)
        
        #trading_manager = TestTradingManager(data_generator=data_generator,
        #                                     trading_algorithm=trading_algorithm,
        #                                     trading_client=trading_client,
        #                                     rsi_threshold=run_parameters['rsi_threshold'],
        #                                     minutes_before_trading_start=run_parameters['rsi_minutes_before_trading_start'],
        #                                     api_key='test_key',
        #                                     secret_key='test_secret')
        
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

        all_symbols_daily_data = get_all_symbols_daily_data_yf_db(recommended_symbol_list=recommended_symbol_list,
                                                                  s=start)

        run_test_experiment(all_symbols_daily_data=all_symbols_daily_data, trading_manager=trading_manager)

    except IndexError as ie:
        print(str(ie))

    finally:
        data_manager.save_daily_statistics_and_aggregated_plots(recommended_symbols=scanner.recommended_symbols,
                                                                symbol_dict=data_generator.symbol_dict)
        data_manager.save_daily_charts(symbol_dict=data_generator.symbol_dict)
        print('Experiment ran successfully, with run id: ', data_manager.run_id, 'and run parameters', data_manager.run_parameters)