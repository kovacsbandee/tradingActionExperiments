import os
from dotenv import load_dotenv
import websocket, json
from alpaca.data.live import StockDataStream

load_dotenv()


ALPACA_KEY= os.environ["ALPACA_KEY"]
ALPACA_SECRET_KEY= os.environ["ALPACA_SECRET_KEY"]
SOCKET_URL= os.environ["SOCKET_URL"]

stream = StockDataStream(api_key=ALPACA_KEY, secret_key=ALPACA_SECRET_KEY)
stream._connect()

def on_open(ws):
    print("opened")
    auth_data = {"action": "auth", "key": f"{ALPACA_KEY}", "secret": f"{ALPACA_SECRET_KEY}"}

    ws.send(json.dumps(auth_data))

    listen_message = {
        "action":"subscribe",
        "trades":["AAPL"], # NOTE: ide jönnek a watchlistben lévő részvények
        "quotes":["BOWL","CABA"], # NOTE: vagy ide?
        "dailyBars":["*"]
        }
    
    listen_message = {"action": "listen", "data": {"streams": ["AM.TSLA"]}}

    ws.send(json.dumps(listen_message))


def on_message(ws, message):
    print("received a message")
    print(message)
    #file = open("message.txt", "w")
    #file.write(message)
    #file.close()

def on_close(ws):
    print("closed connection")

socket = SOCKET_URL

ws = websocket.WebSocketApp(socket, on_open=on_open, on_message=on_message, on_close=on_close)
ws.run_forever()