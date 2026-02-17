"""
Context Loader - Dynamic context module loading

This module provides utilities for loading context configuration files
dynamically with hot-reload support.
"""

import importlib
import sys
import os


def load_context_module(module_name: str, required_attrs: list = None):
    """
    Dynamically load a context module.
    
    Args:
        module_name: Name of module (e.g., 'context_tax_invoice')
        required_attrs: List of required attributes to check
    
    Returns:
        Module object or None if loading fails
    
    Example:
        >>> ctx = load_context_module('context_tax_invoice')
        >>> if ctx:
        ...     print(ctx.EXCEL_SHEET_NAME)
    """
    try:
        # Reload if already imported (for hot-reload)
        if module_name in sys.modules:
            return importlib.reload(sys.modules[module_name])
        else:
            return importlib.import_module(module_name)
    except Exception as e:
        print(f"⚠️  Warning: Could not load {module_name}: {e}")
        return None


def get_context_attr(context_module, attr_name: str, default=None):
    """
    Safely get attribute from context module.
    
    Args:
        context_module: Module object
        attr_name: Attribute name
        default: Default value if not found
    
    Returns:
        Attribute value or default
    
    Example:
        >>> ctx = load_context_module('context_tax_invoice')
        >>> sheet_name = get_context_attr(ctx, 'EXCEL_SHEET_NAME', 0)
    """
    if context_module is None:
        return default
    return getattr(context_module, attr_name, default)

