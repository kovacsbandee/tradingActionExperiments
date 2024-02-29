import os
from dotenv import load_dotenv
import websocket, json
from datetime import datetime

load_dotenv()


ALPACA_KEY= os.environ["ALPACA_KEY"]
ALPACA_SECRET_KEY= os.environ["ALPACA_SECRET_KEY"]
SOCKET_URL= os.environ["SOCKET_URL"]

#stream = StockDataStream(api_key=ALPACA_KEY, secret_key=ALPACA_SECRET_KEY)

def on_open(ws):
    print("opened")
    auth_data = {"action": "auth", "key": f"{ALPACA_KEY}", "secret": f"{ALPACA_SECRET_KEY}"}

    ws.send(json.dumps(auth_data))

    listen_message = {
        "action":"subscribe",
        "bars":["AAPL"]
        }

    ws.send(json.dumps(listen_message))


def on_message(ws, message):
    print("\nNew bar data received")
    print(f"\t[Time: {datetime.now()}]")
    print(f"\t[Message: {message}]\n")
    print(message)

def on_close(ws):
    print("closed connection")

def on_ping(ws):
    print("ping!")

def on_pong(ws):
    print("pong!")

socket = SOCKET_URL

ws = websocket.WebSocketApp(socket, 
                            on_open=on_open, 
                            on_message=on_message, 
                            on_close=on_close,
                            on_ping=on_ping,
                            on_pong=on_pong)
ws.ping_interval = 5.5
"""        on_message: function
            Callback object which is called when received data.
            on_message has 2 arguments.
            The 1st argument is this class object.
            The 2nd argument is utf-8 data received from the server."""
ws.run_forever()