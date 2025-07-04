# Trading Symbols Configuration
# This module now imports symbols from the shared core configuration

from ..core.symbols import TRADING_SYMBOLS, get_trading_symbols

# For backward compatibility, expose the symbols list directly
symbols = TRADING_SYMBOLS
