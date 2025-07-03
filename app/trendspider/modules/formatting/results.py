import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from ... import config
from ..filtering.conditions import matches_filter_conditions, format_condition_text
from ..utils.numbers import format_number

# Setup logging
logger = logging.getLogger(__name__)

def sort_results(results: List[Dict[str, Any]], sort_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Sort results based on the specified key
    
    Args:
        results: List of symbol data dictionaries
        sort_key: Key to sort by
        
    Returns:
        Sorted list of dictionaries
    """
    # Use default sort key if none provided
    if sort_key is None:
        sort_key = config.SORT_BY
        
    # Filter out failed results
    valid_results = [r for r in results if r.get("success", False)]
    failed_results = [r for r in results if not r.get("success", False)]
    
    try:
        # Sort based on the key
        if sort_key == "symbol":
            # Alphabetical by symbol
            sorted_results = sorted(valid_results, key=lambda x: x["symbol"])
        elif sort_key == "price":
            # Highest price first
            sorted_results = sorted(valid_results, key=lambda x: x.get("price", 0), reverse=True)
        elif sort_key == "volume":
            # Highest volume first
            sorted_results = sorted(valid_results, key=lambda x: x.get("volume", 0), reverse=True)
        elif sort_key and sort_key.startswith("percent_"):
            # Extract period
            try:
                period = int(sort_key.split("_")[1])
                # Sort by percentage difference from EMA, highest first
                sorted_results = sorted(
                    valid_results,
                    key=lambda x: x.get("percent_from_ema", {}).get(str(period), -float("inf")),
                    reverse=True
                )
            except:
                # Fall back to alphabetical
                sorted_results = sorted(valid_results, key=lambda x: x["symbol"])
        else:
            # Unknown sort key, use alphabetical
            sorted_results = sorted(valid_results, key=lambda x: x["symbol"])
            
        # Append failed results at the end
        return sorted_results + failed_results
        
    except Exception as e:
        logger.error(f"Error sorting results: {str(e)}")
        # Return unsorted on error
        return valid_results + failed_results

def format_results(results: List[Dict[str, Any]]) -> Tuple[str, int, int]:
    """
    Format the filtered results for Discord message
    
    Args:
        results: List of symbol data dictionaries
        
    Returns:
        Tuple of (formatted text, matching count, total processed count)
    """
    # Count total and filter if needed
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
    
    # Generate output text
    lines = []
    
    # Add header
    timeframe_label = config.get_timeframe_label(config.TIMEFRAME)
    lines.append(f"**EMA Scanner Results ({timeframe_label} Timeframe)**")
    lines.append("")
    
    # Add conditions
    if config.FILTER_CONDITIONS:
        lines.append("**Conditions:**")
        for period_str, condition in config.FILTER_CONDITIONS.items():
            condition_text = format_condition_text(int(period_str), condition)
            lines.append(f"• {condition_text}")
        lines.append("")
        
    # Add sorting info
    sort_method = "Symbol (A-Z)"
    if config.SORT_BY == "price":
        sort_method = "Price (Highest first)"
    elif config.SORT_BY == "volume":
        sort_method = "Volume (Highest first)"
    elif config.SORT_BY and config.SORT_BY.startswith("percent_"):
        period = config.SORT_BY.split("_")[1]
        sort_method = f"% from {period} EMA (Highest first)"
        
    lines.append(f"**Results (Sorted by: {sort_method})**")
    lines.append(f"**{len(matching_results)}** matching symbols out of **{total_processed}** processed")
    lines.append("")
    
    # If no results, return early
    if not display_results:
        lines.append("*No results to display*")
        output = "\n".join(lines)
        return output, len(matching_results), total_processed
    
    # Determine periods for display
    periods = config.EMA_PERIODS
    
    # Format results in a Discord-friendly way (using code blocks for alignment)
    lines.append("```")
    
    # Create header
    header_parts = ["Symbol".ljust(12), "Price".rjust(8)]
    for period in periods:
        header_parts.append(f"%{period}".rjust(8))
    
    lines.append(" ".join(header_parts))
    lines.append("-" * (12 + 8 + (len(periods) * 9) + 1))
    
    # Add data rows
    for data in display_results:
        # Skip failures (should already be filtered)
        if not data.get("success", False):
            continue
            
        # Get basic info
        symbol = data["symbol"]
        price = format_number(data["price"])
        
        # Build row parts
        row_parts = [symbol[:12].ljust(12), price.rjust(8)]
        
        # Add percent differences
        for period in periods:
            period_str = str(period)
            if period_str in data["percent_from_ema"]:
                percent = data["percent_from_ema"][period_str]
                if percent > 0:
                    percent_text = f"+{percent:.1f}%"
                else:
                    percent_text = f"{percent:.1f}%"
                row_parts.append(percent_text.rjust(8))
            else:
                row_parts.append("-".rjust(8))
                
        # Add row to output
        lines.append(" ".join(row_parts))
        
    lines.append("```")
    
    # Add footer with timestamp
    lines.append("")
    lines.append(f"*Scan completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    
    # Join all lines
    output = "\n".join(lines)
    
    return output, len(matching_results), total_processed 