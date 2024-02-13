param_list = [
    {
        "scanner_params" : {
            "windows" : {
                "short" : 12,
                "long" : 26,
                "signal" : 9
            }
        },
        "algo_params" : {
            "entry_signal" : "default",
            "rsi_length" : 12,
            "entry_rsi" : {
                "overbought" : 70,
                "oversold" : 30
            },
            "entry_windows" : {
                "short" : 4,
                "long" : 10,
                "epsilon" : 0.0015
            },
            "entry_weighted" : False,
            "close_signal" : "AVG",
            "close_rsi" : {
                "overbought" : 70,
                "oversold" : 30
            },
            "close_window" : 5,
            "close_weighted" : True
        }
    },
    {
        "scanner_params" : {
            "windows" : {
                "short" : 12,
                "long" : 26,
                "signal" : 9
            }
        },
        "algo_params" : {
            "entry_signal" : "MACD",
            "rsi_length" : 12,
            "entry_rsi" : None,
            "entry_windows" : {
                "short" : 12,
                "long" : 26,
                "signal" : 9
            },
            "entry_weighted" : True,
            "close_signal" : "ATR",
            "close_rsi" : None,
            "close_window" : 5,
            "close_weighted" : True 
        }
    }
]