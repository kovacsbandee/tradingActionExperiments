import os
from dotenv import load_dotenv
from datetime import date, datetime
import pandas as pd
import schedule
import time
import pytz
import websocket
import json
import traceback

from config import config
from src_tr.main.utils.utils import check_trading_day

load_dotenv()

WEBSOCKET_APP = None

ALPACA_KEY = os.environ["ALPACA_KEY"]
ALPACA_SECRET_KEY = os.environ["ALPACA_SECRET_KEY"]
TRADE_SOCKET_URL = os.environ["TRADE_SOCKET_URL"]
RUN_ID = "E-RSI_10-MACD16_6_3--C-AVG_5-RSI_70"


class TradeResponseManager():
    def __init__(self,
                 api_key: str,
                 secret_key: str,
                 recommended_symbol_list: list,
                 run_id: str,
                 trading_day):
        self.api_key = api_key
        self.secret_key = secret_key
        self.recommended_symbol_list = recommended_symbol_list
        self.run_id = run_id
        self.trading_day = trading_day
        self.daily_dir_name = '_'.join([run_id, trading_day.strftime('%Y_%m_%d')])
        self.all_messages = None


    def init_ws(self, ws: websocket.WebSocketApp):
        print(f"WebSocket connection opened on URL: {ws.url}")
        auth_data = {"action": "auth", "key": f"{self.api_key}", "secret": f"{self.secret_key}"}
        ws.send(json.dumps(auth_data))
        trade_updates_listen_message = \
            {
                "action": "listen",
                "data": {
                    "streams": ["trade_updates"]
                }
            }
        ws.send(json.dumps(trade_updates_listen_message))
        expected_message_cols = ['id', 'client_order_id', 'created_at', 'updated_at', 'submitted_at', 'filled_at', 'expired_at', 'cancel_requested_at', 'canceled_at',
                                 'failed_at', 'replaced_at', 'replaced_by', 'replaces', 'asset_id', 'symbol', 'asset_class', 'notional', 'qty', 'filled_qty',
                                 'filled_avg_price', 'order_class', 'order_type', 'type', 'side', 'time_in_force', 'limit_price', 'stop_price', 'status',
                                 'extended_hours', 'legs', 'trail_percent', 'trail_price', 'hwm', 'event', 'timestamp']
        td = self.trading_day.strftime("%Y_%m_%d")
        for symbol in self.recommended_symbol_list:
            pd.DataFrame(columns=expected_message_cols).\
                to_csv(f"{config['output_stats']}/{self.run_id}/{self.daily_dir_name}/daily_files/csvs/{symbol}_{td}_trade_messages.csv")
        print('csvs for each sybmbol were created waiting to get trade messages')

    def _parse_json(self, json_string):
        try:
            return json.loads(json_string)
        except json.JSONDecodeError as e:
            print(str(e))

    def handle_trade_update(self, ws, message, current_time=None):
        if current_time is None:
            current_time = current_time = datetime.now(pytz.timezone("UTC"))
        if datetime.now().strftime("%H:%M") == "21:00":
            self.ws_close_func()
        else:
            try:
                current_message = self._parse_json(message)
                self.all_messages = pd.DataFrame()
                base = current_message['data']['order']
                base['event'] = current_message['data']['event']
                base['timestamp'] = current_message['data']['timestamp']
                symbol = base['symbol']
                td = self.trading_day.strftime("%Y_%m_%d")
                pd.DataFrame([base]).\
                    to_csv(f"{config['output_stats']}/{self.run_id}/{self.daily_dir_name}/daily_files/csvs/{symbol}_{td}_trade_messages.csv",
                           mode='a',
                           header=False)
                print(current_message)
            except:
                traceback.print_exc()

    def on_ping(self, ws, ping_payload):
        print(f"Ping sent: {ping_payload}")

    def on_pong(self, ws, pong_payload):
        print(f"Pong received: {pong_payload}")

    def on_close(self, ws, close_status_code, close_msg):
        print(f"Connection closed with status code {close_status_code}: {close_msg}")

    def on_error(self, ws, error):
        print(f"WebSocket error: {error}")


trade_response_manager = TradeResponseManager(api_key=ALPACA_KEY,
                                              secret_key=ALPACA_SECRET_KEY,
                                              run_id=RUN_ID,
                                              trading_day=datetime(2024, 3, 15),
                                              recommended_symbol_list=['AAPL', 'AMZN', 'TSLA'])
print(f"Initializing WebSocket app @ {datetime.now()}")
WEBSOCKET_APP = websocket.WebSocketApp(url=TRADE_SOCKET_URL,
                                       on_open=trade_response_manager.init_ws,
                                       on_message=trade_response_manager.handle_trade_update,
                                       on_close=trade_response_manager.on_close,
                                       on_error=trade_response_manager.on_error)

WEBSOCKET_APP.run_forever(reconnect=True, ping_timeout=None)

td = '2024_03_12'

file_path = f"{config['output_stats']}/{RUN_ID}/{RUN_ID}_{td}"
file_name = f"trade_message_list.json"
with open(f"{file_path}/{file_name}", 'w') as fout:
    json.dump(trade_response_manager.all_messages, fout)

trade_messages = json.load(open(f"{file_path}/{file_name}"))

df = pd.DataFrame()
for i in range(2,len(trade_messages)):
    base = trade_messages[i]['data']['order']
    base['event'] = trade_messages[i]['data']['event']
    base['timestamp'] = trade_messages[i]['data']['timestamp']
    df = pd.concat([df, pd.DataFrame([base])])


df = pd.DataFrame.from_records(for_df)

for symbol in df['symbol'].unique():
    symbol_df = df[df['symbol'] == symbol]
    symbol_df.to_csv(\
        f"{config['output_stats']}/E-RSI_10-MACD16_6_3--C-AVG_5-RSI_70/E-RSI_10-MACD16_6_3--C-AVG_5-RSI_70_2024_03_12/daily_files/csvs/{symbol}_2024_03_12_trade_messages.csv", index=False)




























{'stream': 'trade_updates',
 'data':
     {'event': 'fill', 'timestamp': '2024-03-12T19:01:08.202781902Z', 'order':
         {'id': '822495cc-6eed-4530-84ae-6def1aaeca87',
          'client_order_id': 'ceb3cab7-0604-4f86-879c-8b703bcfc359',
          'created_at': '2024-03-12T19:01:05.314235272Z',
          'updated_at': '2024-03-12T19:01:08.20592968Z',
          'submitted_at': '2024-03-12T19:01:05.320275986Z',
          'filled_at': '2024-03-12T19:01:08.202781902Z',
          'expired_at': None,
          'cancel_requested_at': None,
          'canceled_at': None,
          'failed_at': None,
          'replaced_at': None,
          'replaced_by': None,
          'replaces': None,
          'asset_id': '27982558-2464-4daf-bb2f-b3b728659884',
          'symbol': 'ORCL',
          'asset_class': 'us_equity',
          'notional': None,
          'qty': '7.829014327',
          'filled_qty': '7.829014327',
          'filled_avg_price': '127.57',
          'order_class': '', 'order_type': 'market', 'type': 'market', 'side': 'sell', 'time_in_force': 'day', 'limit_price': None, 'stop_price': None, 'status': 'filled', 'extended_hours': False, 'legs': None, 'trail_percent': None, 'trail_price': None, 'hwm': None}, 'price': '127.57', 'qty': '1', 'position_qty': '0', 'execution_id': 'f7125e57-07c1-4e17-946c-08eeefbfec39'}}
