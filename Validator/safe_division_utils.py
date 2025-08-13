"""
Utility functions for safe division operations to prevent division by zero errors
"""

def safe_divide(numerator, denominator, default=0):
    """
    Safely divide two numbers, returning a default value if denominator is zero
    
    Args:
        numerator: The number to be divided
        denominator: The number to divide by
        default: Value to return if denominator is zero (default: 0)
    
    Returns:
        Result of division or default value
    """
    if denominator == 0 or denominator is None:
        return default
    try:
        return numerator / denominator
    except (ZeroDivisionError, TypeError):
        return default

def safe_percentage(part, whole, default=0):
    """
    Calculate percentage safely
    
    Args:
        part: The partial value
        whole: The total value
        default: Value to return if whole is zero (default: 0)
    
    Returns:
        Percentage or default value
    """
    if whole == 0 or whole is None:
        return default
    try:
        return (part / whole) * 100
    except (ZeroDivisionError, TypeError):
        return default

def safe_ratio(numerator, denominator, default=0):
    """
    Calculate ratio safely
    
    Args:
        numerator: The numerator
        denominator: The denominator
        default: Value to return if denominator is zero (default: 0)
    
    Returns:
        Ratio or default value
    """
    return safe_divide(numerator, denominator, default)

def safe_average(values, default=0):
    """
    Calculate average safely
    
    Args:
        values: List of values to average
        default: Value to return if list is empty (default: 0)
    
    Returns:
        Average or default value
    """
    if not values or len(values) == 0:
        return default
    try:
        return sum(values) / len(values)
    except (ZeroDivisionError, TypeError):
        return default