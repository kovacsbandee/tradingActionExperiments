# tradingActionExperiments

In this repo the tradingBot repo is revised, the aim here is to test various watchlists and strategies on loads of equities and choose the appropriet trading actions based on the nature of each portfolio element.
The general strategy is the following: we stay in each position until 1% of gain is reached, and the stop loss is 0.5% in every case!
For strategies trend scalping and MACD are the first candidates.

- További teendők a projekttel:
    - Mindenképpen meg kell csinálni:
      - Meg kell csinálni a cumulative gain számítást!
      - Ellenőriztetni kell a stratégiát és a programot külső szemlélővel!
      - Egyesével ellenőrizni kell, hogy ahol a combined stratégia negatív gain-t hozott mi volt a probléma!
      - Az összes NASDAQ sticker-en meg kell tudni futtani a programot, annak érdekében, hogy ellenőrizzük a watchlist működését, esetleg jobb megoldást találjunk rá.
      - Hosszabb időtávról kell perces adatot szerezni, hogy legyen több teszt mintánk!
      - Tuningolni szükséges az alábbi paramétereket: epsilon, short_ma, long_ma, oly módon, hogy optimális legyen a gain. (ehhez rohadt sokszor le fogjuk futtani az egészet)
      
    - Nice to have:
      - experiment_data mentésére és olvasására alkalmas tool



Meg kell vizsgálni, hogyan csökken a volume egy-egy kereskedési napon a kezdő órákhoz vizsonyítva és be kell állítani egy limit-et hol hagyja abba a bot!