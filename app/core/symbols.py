# Shared Trading Symbols Configuration
# Single source of truth for cryptocurrency trading symbols monitored by the application

# Format: Each symbol should be in uppercase and include USDT suffix for Bybit spot market
# Example: BTCUSDT, ETHUSDT, etc.

# NOTE: These symbols must be available in the Bybit API and will be monitored by the data fetcher
# The bybit_data_fetcher module is responsible for collecting and storing the market data
# The trendspider module uses these symbols for EMA analysis

# Full list of symbols being monitored
TRADING_SYMBOLS = [
    '1000BONKUSDT', '1000PEPEUSDT', 'AAVEUSDT', 
    'ADAUSDT', 'AERGOUSDT', 'AI16ZUSDT', 'ALCHUSDT', 'APTUSDT', 
    'ARBUSDT', 'ARCUSDT', 'ARKUSDT', 'ATOMUSDT', 'AVAXUSDT', 'BABYUSDT', 
    'BCHUSDT', 'BERAUSDT', 'BIOUSDT', 'BNBUSDT', 'BSWUSDT', 'BTCUSDT', 
    'CRVUSDT', 'DOGEUSDT', 'DOTUSDT', 'ELXUSDT', 'ENAUSDT', 'ENJUSDT', 
    'ETCUSDT', 'ETHUSDT', 'FARTCOINUSDT', 'FHEUSDT', 'FILUSDT', 
    'FLMUSDT', 'GALAUSDT', 'GASUSDT', 'GMTUSDT', 'GOATUSDT', 'GUNUSDT', 
    'HBARUSDT', 'HIGHUSDT', 'HYPEUSDT', 'INJUSDT', 'IPUSDT', 'JASMYUSDT', 
    'JELLYJELLYUSDT', 'JUPUSDT', 'KERNELUSDT', 'KOMAUSDT', 'LEVERUSDT', 
    'LINKUSDT', 'LTCUSDT', 'MAGICUSDT', 'MAJORUSDT', 'MAVIAUSDT', 
    'MEMEUSDT', 'MOVEUSDT', 'MUBARAKUSDT', 'NEARUSDT', 'NKNUSDT', 'NOTUSDT', 
    'OGNUSDT', 'OLUSDT', 'OMUSDT', 'ONDOUSDT', 'OPUSDT', 'ORCAUSDT', 
    'ORDIUSDT', 'PARTIUSDT', 'PEOPLEUSDT', 'PERPUSDT', 'PNUTUSDT', 
    'POPCATUSDT', 'PROMPTUSDT', 'RENDERUSDT', 'RFCUSDT', 
    'SEIUSDT', 'SOLAYERUSDT', 'SOLUSDT', 'SUIUSDT', 'TAIUSDT', 'TAOUSDT', 
    'TIAUSDT', 'TONUSDT', 'TRBUSDT', 'TRUMPUSDT', 'TRXUSDT', 'TUSDT', 
    'TUTUSDT', 'USUALUSDT', 'VINEUSDT', 'VIRTUALUSDT', 'VOXELUSDT', 
    'VTHOUSDT', 'WALUSDT', 'WCTUSDT', 'WIFUSDT', 'WLDUSDT', 'XAIUSDT', 
    'XCNUSDT', 'XRPUSDT'
]

def get_trading_symbols():
    """
    Return the list of trading symbols to monitor.
    
    Returns:
        list: List of trading pair symbols
    """
    return TRADING_SYMBOLS.copy() 