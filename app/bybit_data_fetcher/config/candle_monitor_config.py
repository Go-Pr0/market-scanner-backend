"""
Configuration settings for the candle monitor system.
"""
import os

# Monitor settings
CHECK_INTERVAL = 60  # Check interval in seconds
RESET_DB_ON_START = False  # Whether to reset the database on startup

# Logging settings
LOG_LEVEL = "INFO"
# Update log path to work with integrated structure
_current_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(_current_dir)))
LOG_FILE = os.path.join(_backend_dir, "logs", "candle_monitor.log")

def get_trading_pairs():
    """
    Return the list of trading pairs to monitor.
    
    Returns:
        list: List of trading pair symbols
    """
    return ['1000BONKUSDT', '1000PEPEUSDT', 'AAVEUSDT', 
           'ADAUSDT', 'AERGOUSDT', 'AI16ZUSDT', 'ALCHUSDT', 'APTUSDT', 
           'ARBUSDT', 'ARCUSDT', 'ARKUSDT', 'ATOMUSDT', 'AVAXUSDT', 'BABYUSDT', 
           'BCHUSDT', 'BERAUSDT', 'BIOUSDT', 'BNBUSDT', 'BSWUSDT', 'BTCUSDT', 
           'CRVUSDT', 'DOGEUSDT', 'DOTUSDT', 'ELXUSDT', 'ENAUSDT', 'ENJUSDT', 
           'ETCUSDT', 'ETHUSDT', 'FARTCOINUSDT', 'FHEUSDT', 'FILUSDT', 
           'FLMUSDT', 'GALAUSDT', 'GASUSDT', 'GMTUSDT', 'GOATUSDT', 'GUNUSDT', 
           'HBARUSDT', 'HIGHUSDT', 'HYPEUSDT', 'INJUSDT', 'IPUSDT', 'JASMYUSDT', 
           'JELLYJELLYUSDT', 'JUPUSDT', 'KERNELUSDT', 'KOMAUSDT', 
           'LINKUSDT', 'LTCUSDT', 'MAGICUSDT', 'MAJORUSDT', 'MAVIAUSDT', 
           'MEMEUSDT', 'MOVEUSDT', 'MUBARAKUSDT', 'NEARUSDT', 'NKNUSDT', 'NOTUSDT', 
           'OGNUSDT', 'OLUSDT', 'OMUSDT', 'ONDOUSDT', 'OPUSDT', 'ORCAUSDT', 
           'ORDIUSDT', 'PARTIUSDT', 'PEOPLEUSDT', 'PERPUSDT', 'PNUTUSDT', 
           'POPCATUSDT', 'PROMPTUSDT', 'RENDERUSDT', 'RFCUSDT', 
           'SEIUSDT', 'SOLAYERUSDT', 'SOLUSDT', 'SUIUSDT', 'TAIUSDT', 'TAOUSDT', 
           'TIAUSDT', 'TONUSDT', 'TRBUSDT', 'TRUMPUSDT', 'TRXUSDT', 'TUSDT', 
           'TUTUSDT', 'USUALUSDT', 'VINEUSDT', 'VIRTUALUSDT', 'VOXELUSDT', 
           'VTHOUSDT', 'WALUSDT', 'WCTUSDT', 'WIFUSDT', 'WLDUSDT', 'XAIUSDT', 
           'XCNUSDT', 'XRPUSDT']
