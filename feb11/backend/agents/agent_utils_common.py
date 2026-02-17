"""
Agent Utils Common - Shared utilities for all agents

This module provides common utility functions used across all invoice agents,
including data cleaning, type conversion, and path manipulation.
"""

import re
from typing import Any, Dict, List


def safe_num(val: Any, default: float = 0.0) -> float:
    """
    Convert value to float, handling common formats.
    
    Args:
        val: Value to convert
        default: Default if conversion fails
    
    Returns:
        Float value
    
    Example:
        >>> safe_num("₹1,234.56")
        1234.56
        >>> safe_num("", 0.0)
        0.0
        >>> safe_num(None, 10.0)
        10.0
    """
    if val is None or val == "":
        return default
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        # Remove currency symbols, commas, spaces
        cleaned = re.sub(r'[₹,\s]', '', val.strip())
        try:
            return float(cleaned)
        except ValueError:
            return default
    return default


def drop_empty_rows(df):
    """
    Drop rows that are completely empty or have only NaN values.
    
    Args:
        df: DataFrame
    
    Returns:
        Cleaned DataFrame
    
    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({'A': [1, None, 3], 'B': [4, None, 6]})
        >>> cleaned = drop_empty_rows(df)
        >>> len(cleaned)
        2
    """
    return df.dropna(how='all').reset_index(drop=True)


def nest_set(obj: dict, path: str, value: Any) -> None:
    """
    Set nested dictionary value using dot notation.
    
    Args:
        obj: Dictionary to modify
        path: Dot-separated path
        value: Value to set
    
    Example:
        >>> data = {}
        >>> nest_set(data, "billing_to.client_name", "Acme Corp")
        >>> print(data)
        {'billing_to': {'client_name': 'Acme Corp'}}
    """
    keys = path.split('.')
    for key in keys[:-1]:
        obj = obj.setdefault(key, {})
    obj[keys[-1]] = value


def path_to_wildcard(path: str) -> str:
    """
    Convert numeric indexes in path to wildcard form.
    
    Args:
        path: Path with numeric indexes
    
    Returns:
        Path with wildcards
    
    Example:
        >>> path_to_wildcard("items.0.description")
        'items.*.description'
        >>> path_to_wildcard("items.{0}.unit_price")
        'items.*.unit_price'
    """
    out = []
    for seg in str(path).split("."):
        s = seg.strip()
        if s.isdigit() or (s.startswith("{") and s.endswith("}")):
            out.append("*")
        else:
            out.append(s)
    return ".".join(out)


def normalize_path_wildcards(path: str, index: int) -> str:
    """
    Replace wildcards in path with actual index.
    
    Args:
        path: Path with wildcards
        index: Index to use
    
    Returns:
        Normalized path
    
    Example:
        >>> normalize_path_wildcards("items.*.description", 0)
        'items.0.description'
        >>> normalize_path_wildcards("freight_bill.runs.*.truck_no", 2)
        'freight_bill.runs.2.truck_no'
    """
    return path.replace('*', str(index))

