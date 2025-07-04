"""
TrendSpider modules package
Contains refactored components from the main ema.py file for better organization
"""

# Import all the main functions to maintain backward compatibility
from .data.fetcher import fetch_kline_data_async
from .data.processor import process_symbol_batch, get_emas_for_all_symbols
from .calculation.ema import calculate_ema_tradingview, calculate_all_emas
from .filtering.conditions import matches_filter_conditions, matches_custom_filter_conditions, format_condition_text, filter_and_sort_results
from .formatting.results import format_results, sort_results
from .formatting.csv import format_csv_for_tradingview
from .utils.numbers import format_number

__all__ = [
    'fetch_kline_data_async',
    'process_symbol_batch', 
    'get_emas_for_all_symbols',
    'calculate_ema_tradingview',
    'calculate_all_emas',
    'matches_filter_conditions',
    'matches_custom_filter_conditions',
    'format_condition_text',
    'filter_and_sort_results',
    'format_results',
    'sort_results',
    'format_csv_for_tradingview',
    'format_number'
] 