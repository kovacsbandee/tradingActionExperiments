import threading
import traceback

from src_tr.main.utils.runtime_scheduler import run_scheduler, close_websocket_connection

if __name__ == "__main__":
    scheduler_thread = threading.Thread(target=run_scheduler)
    try:
        scheduler_thread.start()
    except:
        traceback.print_exc()
    finally:
        close_websocket_connection() #TODO: pozíciólezárás/újraindítás/egyéb hibakezelés
        scheduler_thread.join()