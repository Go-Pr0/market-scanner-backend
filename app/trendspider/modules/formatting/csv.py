from typing import Dict, List, Any, Tuple

from ... import config
from ..filtering.conditions import matches_filter_conditions
from .results import sort_results

def format_csv_for_tradingview(results: List[Dict[str, Any]]) -> Tuple[str, int, int]:
    """
    Format the filtered results as a simple list for TradingView watchlist import
    
    Args:
        results: List of symbol data dictionaries
        
    Returns:
        Tuple of (list content, matching count, total processed count)
    """
    # Count total and matching results
    total_processed = len(results)
    matching_results = []
    
    for data in results:
        # Skip failures
        if not data.get("success", False):
            continue
            
        # Check if it matches conditions
        if matches_filter_conditions(data):
            matching_results.append(data)
            
    # Use either filtered or all results
    if config.SHOW_ONLY_MATCHING:
        display_results = matching_results
    else:
        # For unfiltered display, still put matches at the top
        non_matching = [r for r in results if r.get("success", False) and r not in matching_results]
        display_results = matching_results + non_matching
        
    # Sort the results
    display_results = sort_results(display_results)
    
    # Generate simple list format
    lines = []
    
    for data in display_results:
        if not data.get("success", False):
            continue
            
        symbol = data["symbol"]
        # Convert USDT symbols to .P format for perpetual contracts
        if symbol.endswith("USDT"):
            # Remove USDT and add .P for perpetual format
            base_symbol = symbol[:-4]  # Remove 'USDT'
            formatted_symbol = f"BYBIT:{base_symbol}USDT.P"
        else:
            # Fallback for non-USDT symbols
            formatted_symbol = f"BYBIT:{symbol}.P"
            
        lines.append(formatted_symbol)
        
    # Join all lines
    content = "\n".join(lines)
    
    return content, len(matching_results), total_processed