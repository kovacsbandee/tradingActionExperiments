import os
from dotenv import load_dotenv
import websocket, json
from datetime import datetime
import time
import schedule
import traceback
import threading

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
    if datetime.now().strftime("%H:%M") == "16:56":
        ws.close()
    else:
        print("\nNew bar data received")
        print(f"\t[Time: {datetime.now()}]")
        print(f"\t[Message: {message}]\n")

def on_close(ws):
    print("closed connection")

def on_ping(ws):
    print("ping!")

def on_pong(ws):
    print("pong!")

def run():
    print(f"Opening WS connection at {datetime.now()}")
    ws.run_forever()

def close():
    ws.close()
    print(f"WS connection closed at {datetime.now()}")

def run_scheduler():
    schedule.every().thursday.at("16:55").do(run)
    #schedule.every().thursday.at("16:10").do(run)
    #schedule.every().tuesday.at("18:00").do(close)
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            print("Received KeyboardInterrupt, closing...")
            close()
            break

if __name__ == "__main__":
    ws = websocket.WebSocketApp(url=SOCKET_URL,
                                on_open=on_open,
                                on_message=on_message,
                                on_close=on_close,
                                on_ping=on_ping,
                                on_pong=on_pong)

    scheduler_thread = threading.Thread(target=run_scheduler)

    try:
        scheduler_thread.start()
        #run()  # Run the WebSocket in the main thread
    except:
        traceback.print_exc()
    finally:
        close()  # Ensure WebSocket is closed when the main thread exits
        scheduler_thread.join()  # Wait for the scheduler thread to finish