from datetime import datetime
import websocket, json
import traceback
import pytz
import pandas as pd
from config import config

class TradeResponseManager():
    def __init__(self,
                 recommended_symbol_list: list,
                 run_id: str,
                 trading_day,
                 api_key: str,
                 secret_key: str,
                 ws_close_function):
        self.recommended_symbol_list = recommended_symbol_list
        self.run_id = run_id
        self.trading_day = trading_day
        self.daily_dir_name = '_'.join([run_id, trading_day.strftime('%Y_%m_%d')])
        self.all_messages = None
        self.message_list = None
        self.current_message = None
        self.ws_close_function = ws_close_function
        self.api_key = api_key
        self.secret_key = secret_key


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
        print('listen message was sent')
        expected_message_cols = ['id', 'client_order_id', 'created_at', 'updated_at', 'submitted_at', 'filled_at', 'expired_at', 'cancel_requested_at', 'canceled_at',
                                 'failed_at', 'replaced_at', 'replaced_by', 'replaces', 'asset_id', 'symbol', 'asset_class', 'notional', 'qty', 'filled_qty',
                                 'filled_avg_price', 'order_class', 'order_type', 'type', 'side', 'time_in_force', 'limit_price', 'stop_price', 'status',
                                 'extended_hours', 'legs', 'trail_percent', 'trail_price', 'hwm', 'event', 'timestamp']
        td = self.trading_day.strftime("%Y_%m_%d")
        for symbol in self.recommended_symbol_list:
            pd.DataFrame(columns=expected_message_cols). \
                to_csv(f"{config['output_stats']}/{self.run_id}/{self.daily_dir_name}/daily_files/csvs/{symbol['symbol']}_{td}_trade_messages.csv")
            print('trade csvs were written out to disk')
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
                if self.current_message is None:
                    self.all_messages=pd.DataFrame(columns=['id','client_order_id','created_at','updated_at','submitted_at','filled_at','expired_at','cancel_requested_at',
                                          'canceled_at','failed_at','replaced_at','replaced_by','replaces','asset_id','symbol','asset_class','notional',
                                          'qty','filled_qty','filled_avg_price','order_class','order_type','type','side','time_in_force',
                                          'limit_price','stop_price','status','extended_hours','legs','trail_percent','trail_price','hwm','event','timestamp'])
                else:
                    print('in handle_trade_message messages are being handled')
                    current_message = self._parse_json(message)
                    print(current_message)
                    self.message_list.append(current_message)
                    #self.all_messages = pd.DataFrame()
                    base = current_message['data']['order']
                    base['event'] = current_message['data']['event']
                    base['timestamp'] = current_message['data']['timestamp']
                    print(base)
                    symbol = base['symbol']
                    self.all_messages = pd.concat([self.all_messages, pd.DataFrame([base])])
                    td = self.trading_day.strftime("%Y_%m_%d")
                    print(pd.DataFrame([base]))
                    pd.DataFrame([base]). \
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