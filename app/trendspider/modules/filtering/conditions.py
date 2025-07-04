import logging
from typing import Dict, Any, List

from ... import config

# Setup logging
logger = logging.getLogger(__name__)

def matches_custom_filter_conditions(data: Dict[str, Any], filter_conditions: Dict[str, str]) -> bool:
    """
    Check if a symbol matches custom filter conditions
    
    Args:
        data: Symbol data dictionary
        filter_conditions: Dictionary of filter conditions
        
    Returns:
        True if matches all conditions, False otherwise
    """
    # Return False if there was an error or no EMAs calculated
    if not data.get("success", False) or not data.get("emas"):
        return False
        
    # No conditions means everything matches
    if not filter_conditions:
        return True
        
    # Check each condition
    for period_str, condition in filter_conditions.items():
        try:
            # Convert period to int if needed
            period = int(period_str)
            
            # Skip if we don't have EMA data for this period
            if str(period) not in data["emas"] or str(period) not in data["percent_from_ema"]:
                return False
                
            # Get values
            ema_value = data["emas"][str(period)]
            price = data["price"]
            percent_diff = data["percent_from_ema"][str(period)]
            
            # Check the condition
            if condition == "above":
                if price <= ema_value:
                    return False
            elif condition == "below":
                if price >= ema_value:
                    return False
            elif condition.startswith("above_by:"):
                # Handle both single threshold and zone formats
                parts = condition.split(":")
                if len(parts) == 2:
                    # Single threshold: above_by:X (price must be X% or more above EMA)
                    try:
                        threshold = float(parts[1])
                        if percent_diff <= threshold:
                            return False
                    except:
                        # Invalid format, consider not matching
                        return False
                elif len(parts) == 3:
                    # Zone format: above_by:X:Y (price must be between X% and Y% above EMA)
                    try:
                        min_threshold = float(parts[1])
                        max_threshold = float(parts[2])
                        # Ensure price is between min and max thresholds above EMA
                        if percent_diff <= min_threshold or percent_diff >= max_threshold:
                            return False
                    except:
                        # Invalid format, consider not matching
                        return False
                else:
                    # Invalid format, consider not matching
                    return False
            elif condition.startswith("below_by:"):
                # Handle both single threshold and zone formats
                parts = condition.split(":")
                if len(parts) == 2:
                    # Single threshold: below_by:X (price must be X% or more below EMA)
                    try:
                        threshold = float(parts[1])
                        if percent_diff >= -threshold:
                            return False
                    except:
                        # Invalid format, consider not matching
                        return False
                elif len(parts) == 3:
                    # Zone format: below_by:X:Y (price must be between X% and Y% below EMA)
                    try:
                        min_threshold = float(parts[1])
                        max_threshold = float(parts[2])
                        # Ensure price is between min and max thresholds below EMA (negative values)
                        if percent_diff >= -min_threshold or percent_diff <= -max_threshold:
                            return False
                    except:
                        # Invalid format, consider not matching
                        return False
                else:
                    # Invalid format, consider not matching
                    return False
            elif condition.startswith("near:"):
                # Extract percentage
                try:
                    threshold = float(condition.split(":")[1])
                    if abs(percent_diff) > threshold:
                        return False
                except:
                    # Invalid format, consider not matching
                    return False
                
        except Exception as e:
            logger.error(f"Error checking condition {period_str}:{condition} - {str(e)}")
            # Consider not matching if there's an error
            return False
            
    # If we reach here, all conditions matched
    return True

def matches_filter_conditions(data: Dict[str, Any]) -> bool:
    """
    Check if a symbol matches all the filter conditions from config
    
    Args:
        data: Symbol data dictionary
        
    Returns:
        True if matches all conditions, False otherwise
    """
    # Get filter conditions from config
    filter_conditions = config.FILTER_CONDITIONS
    return matches_custom_filter_conditions(data, filter_conditions)

def filter_and_sort_results(results: List[Dict[str, Any]], show_only_matching: bool = None) -> List[Dict[str, Any]]:
    """
    Filter and sort scan results based on configuration.
    This extracts the common logic used by both format_results and format_csv_for_tradingview.
    
    Args:
        results: List of symbol data dictionaries
        show_only_matching: Whether to show only matching symbols (uses config default if None)
        
    Returns:
        Filtered and sorted list of results
    """
    # Use config default if not specified
    if show_only_matching is None:
        show_only_matching = config.SHOW_ONLY_MATCHING
    
    # Count total and filter if needed
    matching_results = []
    
    for data in results:
        # Skip failures
        if not data.get("success", False):
            continue
            
        # Check if it matches conditions
        if matches_filter_conditions(data):
            matching_results.append(data)
            
    # Use either filtered or all results
    if show_only_matching:
        display_results = matching_results
    else:
        # For unfiltered display, still put matches at the top
        non_matching = [r for r in results if r.get("success", False) and r not in matching_results]
        display_results = matching_results + non_matching
        
    # Sort the results (import here to avoid circular imports)
    from ..formatting.results import sort_results
    display_results = sort_results(display_results)
    
    return display_results

def format_condition_text(period: int, condition: str) -> str:
    """
    Format the condition text for display
    
    Args:
        period: EMA period
        condition: Condition string
        
    Returns:
        Formatted condition text
    """
    try:
        if condition == "above":
            return f"Price above {period} EMA"
        elif condition == "below":
            return f"Price below {period} EMA"
        elif condition.startswith("above_by:"):
            parts = condition.split(":")
            if len(parts) == 2:
                # Single threshold
                threshold = float(parts[1])
                return f"Price above {period} EMA by {threshold}%+"
            elif len(parts) == 3:
                # Zone format
                min_threshold = float(parts[1])
                max_threshold = float(parts[2])
                return f"Price {min_threshold}% to {max_threshold}% above {period} EMA"
            else:
                return f"Price above {period} EMA by {condition.split(':', 1)[1]}"
        elif condition.startswith("below_by:"):
            parts = condition.split(":")
            if len(parts) == 2:
                # Single threshold
                threshold = float(parts[1])
                return f"Price below {period} EMA by {threshold}%+"
            elif len(parts) == 3:
                # Zone format
                min_threshold = float(parts[1])
                max_threshold = float(parts[2])
                return f"Price {min_threshold}% to {max_threshold}% below {period} EMA"
            else:
                return f"Price below {period} EMA by {condition.split(':', 1)[1]}"
        elif condition.startswith("near:"):
            threshold = float(condition.split(":")[1])
            return f"Price within {threshold}% of {period} EMA"
        else:
            return f"{period} EMA: {condition}"
    except:
        return f"{period} EMA: {condition}" 