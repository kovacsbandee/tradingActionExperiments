from typing import List
import json
import threading

from .TradingManagerBase import TradingManagerBase

class TradingManagerDraft(TradingManagerBase):

    def __init__(self):
        super().__init__()
        self.event = threading.Event()
        self.minute_bars = []
    
    def handle_message(self, message):
        #TODO: fel kell készíteni arra, ha nincs megfelelő mennyiségű adat
        for item in message:
            #TODO: az első két üzenet az autentikáció és a subscription-visszaigazolás, ezt csekkolni kell!
            self.minute_bars.append(item)

        if len(self.minute_bars) == len(self.price_data_generator.recommended_symbol_list):
            self.event.set()
            do_progress = self._process_data()
            if do_progress:
                # továbbhalad a folyamat: trading_day_stats update -> apply_strategy -> execute_trading_action
                pass
            # else:
            #     self.wait_for_data() / self.event.clear() ???
        else:
            self.wait_for_data()

    def _process_data(self) -> bool:
        #TODO: kell idő-check ->
        # tőzsde-zárás előtt egy-két órával le kell állítani a kereskedést
        # az ezután érkező message-eket ignoráljuk (self.market_open, self.market_close)
        
        # if timecheck, stb:
        self.price_data_generator.update_symbol_df(self.minute_bars)
        self.event.clear()
        return True
        # else: 
        #     TRADING-DAY UPDATE/RESET VAGY VALAMI
        #     return false

    def wait_for_data(self):
        self.event.wait()

    def on_open(self):
        print("opened")
        auth_data = {"action": "auth", "key": f"{self.key}", "secret": f"{self.secret_key}"}

        self.ws.send(json.dumps(auth_data))

        listen_message = {
            "action":"subscribe",
            "bars": self.price_data_generator.recommended_symbol_list
            }

        self.ws.send(json.dumps(listen_message))