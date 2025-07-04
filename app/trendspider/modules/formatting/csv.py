import logging
from typing import List, Dict, Any, Tuple

from ... import config
from ..filtering.conditions import matches_filter_conditions, filter_and_sort_results

# Setup logging
logger = logging.getLogger(__name__)

def format_csv_for_tradingview(results: List[Dict[str, Any]]) -> Tuple[str, int, int]:
    """
    Format the filtered results as a CSV for TradingView watchlist import
    
    Args:
        results: List of symbol data dictionaries
        
    Returns:
        Tuple of (CSV content, matching count, total processed count)
    """
    # Count total processed
    total_processed = len(results)
    
    # Count matching results before filtering
    matching_count = len([r for r in results if r.get("success", False) and matches_filter_conditions(r)])
    
    # Use shared filtering and sorting logic
    display_results = filter_and_sort_results(results)
    
    # Generate CSV content
    csv_lines = []
    
    # Add each symbol in the format expected by TradingView
    for data in display_results:
        # Skip failures (should already be filtered)
        if not data.get("success", False):
            continue
            
        symbol = data["symbol"]
        
        # Format for TradingView: BYBIT:SYMBOL.P (perpetual futures)
        tradingview_symbol = f"BYBIT:{symbol}.P"
        csv_lines.append(tradingview_symbol)
    
    # Join with newlines
    csv_content = "\n".join(csv_lines)
    
    return csv_content, matching_count, total_processed