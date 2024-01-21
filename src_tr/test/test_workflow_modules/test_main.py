import os
from typing import List
from dotenv import load_dotenv
from datetime import datetime, timedelta

from src_tr.test.test_workflow_modules.TestTradingClient import TestTradingClient
from src_tr.test.test_workflow_modules.TestTradingClientDivided import TestTradingClientDivided
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

from src_tr.main.checks.checks import check_trading_day
from src_tr.main.utils.utils import calculate_scanning_day, get_nasdaq_symbols
from src_tr.main.utils.data_management import DataManager
from src_tr.main.utils.plots import create_candle_stick_chart_w_indicators_for_trendscalping_for_mass_experiments, plot_daily_statistics
from src_tr.main.scanners.PreMarketScanner import PreMarketScanner
#from src_tr.main.scanners.PreMarketDumbScanner import PreMarketDumbScanner
from src_tr.main.scanners.PreMarketPolygonScanner import PreMarketPolygonScanner

from src_tr.main.data_generators.PriceDataGeneratorMain import PriceDataGeneratorMain
from src_tr.main.strategies.StrategyWithStopLoss import StrategyWithStopLoss
from src_tr.main.strategies.StrategyWithStopLossPrevPrice import StrategyWithStopLossPrevPrice
from src_tr.test.test_workflow_modules.TestTradingManager import TestTradingManager
from src_tr.test.test_workflow_modules.TestTradingManagerDivided import TestTradingManagerDivided

# 1) Scanner inicializálása -> watchlist létrehozás
load_dotenv()
SYMBOL_CSV_PATH = os.environ["SYMBOL_CSV_PATH"]
ALPACA_KEY = os.environ["ALPACA_KEY"]
ALPACA_SECRET_KEY = os.environ["ALPACA_SECRET_KEY"]
DB_PATH = os.environ['DB_PATH']
RUN_ID = 'DEV_RUN_ID'

for start in [datetime(2024, 1, 10, 0, 0), datetime(2024, 1, 11, 0, 0)]:
    try:
        end = start + timedelta(hours=23) + timedelta(minutes=59)
        trading_day = check_trading_day(start)
        scanning_day = calculate_scanning_day(trading_day)
        
        data_manager = DataManager(trading_day=trading_day, scanning_day=scanning_day, run_id=RUN_ID, db_path=DB_PATH)
        
        nasdaq_symbols = get_nasdaq_symbols(file_path=SYMBOL_CSV_PATH)[:100]
        
        run_parameters = \
            {
                'run_id': RUN_ID,
                'trading_day': start.strftime('%Y_%m_%d'),
                'symbol_csvs': SYMBOL_CSV_PATH,
                'init_cash': 26000,
                'lower_price_boundary': 10,
                'upper_price_boundary': 400,
                'price_range_perc_cond': 5,
                'avg_volume_cond': 10000,
                'ma_short': 5,
                'ma_long': 12,
                'epsilon': 0.0015,
                'rsi_len': 12,
                'stop_loss_perc': 0.0,
                'rsi_threshold': 20,
                'rsi_minutes_before_trading_start': 45
            }
        
        # Professional scanner:
        scanner = PreMarketScanner(trading_day=data_manager.trading_day,
                                   scanning_day=data_manager.scanning_day,
                                   symbols=nasdaq_symbols,
                                   lower_price_boundary=run_parameters['lower_price_boundary'],
                                   upper_price_boundary=run_parameters['upper_price_boundary'],
                                   price_range_perc_cond=run_parameters['price_range_perc_cond'],
                                   avg_volume_cond=run_parameters['avg_volume_cond'])
        
        # Polygon scanner:
        # scanner = PreMarketPolygonScanner(trading_day=data_manager.trading_day,
        #                                   scanning_day=data_manager.scanning_day,
        #                                   symbols=nasdaq_symbols,
        #                                   lower_price_boundary=run_parameters['lower_price_boundary'],
        #                                   upper_price_boundary=run_parameters['upper_price_boundary'],
        #                                   price_range_perc_cond=run_parameters['price_range_perc_cond'],
        #                                   avg_volume_cond=run_parameters['avg_volume_cond'])
        
        
        # Dumb scanner:
        #dumb_symbols = ['MARA', 'RIOT', 'MVIS', 'SOS', 'CAN', 'EBON', 'BTBT', 'HUT', 'EQOS', 'MOGO', 'SUNW', 'XNET', 'PHUN', 'IDEX', 'ZKIN', 'SIFY', 'SNDL', 'NCTY', 'OCGN', 'NIO', 'FCEL', 'PLUG', 'TSLA', 'AAPL', 'AMZN', 'MSFT', 'GOOG', 'FB', 'GOOGL', 'NVDA', 'PYPL', 'ADBE', 'INTC', 'CMCSA', 'CSCO', 'NFLX', 'PEP', 'AVGO', 'TXN', 'COST', 'QCOM', 'TMUS', 'AMGN', 'CHTR', 'SBUX', 'AMD', 'INTU', 'ISRG', 'AMAT', 'MU', 'BKNG', 'MDLZ', 'ADP', 'GILD', 'CSX', 'FISV', 'VRTX', 'ATVI', 'ADSK', 'REGN', 'ILMN', 'BIIB', 'MELI', 'LRCX', 'JD', 'ADI', 'NXPI', 'ASML', 'KHC', 'MRNA', 'EA', 'BIDU', 'WBA', 'MAR', 'LULU', 'EXC', 'ROST', 'WDAY', 'KLAC', 'CTSH', 'ORLY', 'SNPS', 'DOCU', 'IDXX', 'SGEN', 'DXCM', 'PCAR', 'CDNS', 'XLNX', 'ANSS', 'NTES', 'MNST', 'VRSK', 'ALXN', 'FAST', 'SPLK', 'CPRT', 'CDW', 'PAYX', 'MXIM', 'SWKS', 'INCY', 'CHKP', 'TCOM', 'CTXS', 'VRSN', 'SGMS', 'DLTR', 'CERN', 'ULTA', 'FOXA', 'FOX', 'NTAP', 'WDC', 'TTWO', 'EXPE', 'XEL', 'MCHP', 'CTAS', 'MXL', 'WLTW', 'ANET', 'BMRN']
        # scanner = PreMarketDumbScanner(trading_day=data_manager.trading_day,
        #                                scanning_day=data_manager.scanning_day,
        #                                symbols=nasdaq_symbols,
        #                                lower_price_boundary=run_parameters['lower_price_boundary'],
        #                                upper_price_boundary=run_parameters['upper_price_boundary'],
        #                                price_range_perc_cond=run_parameters['price_range_perc_cond'],
        #                                avg_volume_cond=run_parameters['avg_volume_cond'])
        
        
        # initialize symbol list:
        
        scanner.calculate_filtering_stats()
        recommended_symbol_list: List[dict] = scanner.recommend_premarket_watchlist()
        
        data_manager.create_daily_dirs()
        data_manager.save_params_and_scanner_output(params=run_parameters, scanner_output=scanner.recommended_symbols)
        data_manager.recommended_symbol_list = recommended_symbol_list
        
        trading_client = TestTradingClientDivided(init_cash=run_parameters['init_cash'],
                                           symbol_list=recommended_symbol_list)        
        
        #trading_client = TestTradingClient(init_cash=run_parameters['init_cash'],
        #                                   symbol_list=data_manager.recommended_symbol_list)
        
        trading_client.initialize_positions()
        
        data_generator = PriceDataGeneratorMain(recommended_symbol_list=recommended_symbol_list)
        
        # Strategy with stop loss compared to the last price when opening the position:
        # strategy = StrategyWithStopLoss(ma_short=run_parameters['ma_short'],
        #                                 ma_long=run_parameters['ma_long'],
        #                                 epsilon=run_parameters['epsilon'],
        #                                 rsi_len=run_parameters['rsi_len'],
        #                                 stop_loss_perc=run_parameters['stop_loss_perc'],
        #                                 trading_day=data_manager.trading_day,
        #                                 run_id=RUN_ID,
        #                                 db_path=DB_PATH)
        
        # Strategy with stop loss compared to the previous price:
        strategy = StrategyWithStopLossPrevPrice(ma_short=run_parameters['ma_short'],
                                                 ma_long=run_parameters['ma_long'],
                                                 epsilon=run_parameters['epsilon'],
                                                 rsi_len=run_parameters['rsi_len'],
                                                 stop_loss_perc=run_parameters['stop_loss_perc'],
                                                 trading_day=data_manager.trading_day,
                                                 run_id=RUN_ID,
                                                 db_path=DB_PATH)
        
        #trading_manager = TestTradingManager(data_generator=data_generator,
        #                                     strategy=strategy,
        #                                     trading_client=trading_client,
        #                                     rsi_threshold=run_parameters['rsi_threshold'],
        #                                     minutes_before_trading_start=run_parameters['rsi_minutes_before_trading_start'],
        #                                     api_key='test_key',
        #                                     secret_key='test_secret')
        
        trading_manager = TestTradingManagerDivided(data_generator=data_generator,
                                             strategy=strategy,
                                             trading_client=trading_client,
                                             rsi_threshold=run_parameters['rsi_threshold'],
                                             minutes_before_trading_start=run_parameters['rsi_minutes_before_trading_start'],
                                             api_key='test_key',
                                             secret_key='test_secret')
        
        data_generator.initialize_symbol_dict()
        
        client = StockHistoricalDataClient(ALPACA_KEY, ALPACA_SECRET_KEY)
        
        def download_daily_data(symbol, start, end):
            timeframe = TimeFrame(amount=1, unit=TimeFrameUnit.Minute)
        
            bars_request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=timeframe,
                start=start,
                end=end
            )
            latest_bars = client.get_stock_bars(bars_request).data
            daily_data_list = _convert_data(latest_bars, symbol)
            return daily_data_list
        
        def _convert_data(latest_bars: dict, symbol: str):
            bar_list = []
            for e in latest_bars[symbol]:
                bar_list.append({
                'T': 'b',
                't': e.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'S': e.symbol,
                'o': e.open,
                'c': e.close,
                'h': e.high,
                'l': e.low,
                'v': e.volume,
                'n': e.trade_count
            })
            return bar_list
        
        all_symbols_daily_data: List[List] = []
        
        for symbol in recommended_symbol_list:
            daily_data = download_daily_data(symbol=symbol['symbol'], start=start, end=end)
            all_symbols_daily_data.append(daily_data)
        
        i = 0
        while i < len(all_symbols_daily_data[0]):
            minute_bars = []
            for symbol_daily_data in all_symbols_daily_data:
                minute_bars.append(symbol_daily_data[i])
            trading_manager.handle_message(ws=None, message=minute_bars)
            minute_bars = []
            i += 1

        plot_daily_statistics(data_man=data_manager)
        create_candle_stick_chart_w_indicators_for_trendscalping_for_mass_experiments(data_generator, data_manager)
    except Exception as e:
        print(str(e))

# visszaolvasni a daily csv-ket egyenként és megcsinálni a post trading aggregált statisztikákat majd kimenteni soronként a napi post trading statisztika file-ba

# megcsinálni az aggergált statisztikák ábrázolását