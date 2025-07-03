from typing import Union
from ... import config

def format_number(value: Union[int, float]) -> str:
    """
    Format numbers for display with K, M, B suffixes
    
    Args:
        value: Number to format
        
    Returns:
        Formatted string
    """
    # Don't format if not enabled
    if not config.FORMAT_LARGE_NUMBERS:
        if isinstance(value, float):
            # Round to 2-8 decimal places based on magnitude
            if abs(value) >= 100:
                return f"{value:.2f}"
            elif abs(value) >= 10:
                return f"{value:.3f}"
            elif abs(value) >= 1:
                return f"{value:.4f}"
            elif abs(value) >= 0.1:
                return f"{value:.5f}"
            elif abs(value) >= 0.01:
                return f"{value:.6f}"
            elif abs(value) >= 0.001:
                return f"{value:.7f}"
            else:
                return f"{value:.8f}"
        return str(value)
    
    # Format with suffixes for large numbers
    try:
        abs_value = abs(value)
        sign = "-" if value < 0 else ""
        
        if abs_value >= 1_000_000_000:
            # Billions
            return f"{sign}{abs_value / 1_000_000_000:.2f}B"
        elif abs_value >= 1_000_000:
            # Millions
            return f"{sign}{abs_value / 1_000_000:.2f}M"
        elif abs_value >= 1_000:
            # Thousands
            return f"{sign}{abs_value / 1_000:.2f}K"
        elif isinstance(value, float):
            # Scale decimal places based on magnitude
            if abs_value >= 100:
                return f"{value:.2f}"
            elif abs_value >= 10:
                return f"{value:.3f}"
            elif abs_value >= 1:
                return f"{value:.4f}"
            elif abs_value >= 0.1:
                return f"{value:.5f}"
            elif abs_value >= 0.01:
                return f"{value:.6f}"
            elif abs_value >= 0.001:
                return f"{value:.7f}"
            else:
                return f"{value:.8f}"
        else:
            return str(value)
    except:
        return str(value) 