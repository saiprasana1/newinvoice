"""
File Reader - Unified Excel/CSV reading with multi-sheet support

This module provides a single implementation for reading Excel and CSV files
with intelligent sheet detection and user override support.
"""

import pandas as pd
import os
from typing import Tuple, Optional, Union


def read_excel_or_csv(
    file_path: str,
    sheet_name: Optional[Union[str, int]] = None,
    sheet_override: Optional[Union[str, int]] = None
) -> Tuple[pd.DataFrame, str]:
    """
    Read Excel or CSV file with sheet support.
    
    Args:
        file_path: Path to file
        sheet_name: Default sheet (from config)
        sheet_override: Runtime override (from user notes)
    
    Returns:
        (DataFrame, source_description)
    
    Example:
        >>> df, source = read_excel_or_csv("data.xlsx", sheet_name=0, sheet_override=1)
        >>> print(source)
        "Excel file: data.xlsx, sheet: 1 (runtime override)"
    """
    # Determine which sheet to use
    target_sheet = sheet_override if sheet_override is not None else sheet_name
    
    # Read file
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
        source = f"CSV file: {os.path.basename(file_path)}"
    else:
        # Excel file
        if target_sheet is not None:
            df = pd.read_excel(file_path, sheet_name=target_sheet)
            override_note = " (runtime override)" if sheet_override is not None else " (default config)"
            source = f"Excel file: {os.path.basename(file_path)}, sheet: {target_sheet}{override_note}"
        else:
            # Auto-detect first non-empty sheet
            xl = pd.ExcelFile(file_path)
            for sheet in xl.sheet_names:
                temp_df = pd.read_excel(file_path, sheet_name=sheet)
                if not temp_df.empty and len(temp_df.columns) >= 2:
                    df = temp_df
                    source = f"Excel file: {os.path.basename(file_path)}, sheet: {sheet} (auto-detected)"
                    break
            else:
                df = pd.read_excel(file_path)
                source = f"Excel file: {os.path.basename(file_path)}"
    
    return df, source


def detect_sheet_override(notes: str, llm_call_fn) -> Optional[Union[str, int]]:
    """
    Detect sheet override from user notes using LLM.
    
    Args:
        notes: User notes
        llm_call_fn: LLM call function
    
    Returns:
        Sheet name/index or None
    
    Example:
        >>> from integrations.llm_client import call_llm
        >>> override = detect_sheet_override("add all details from sheet 1", call_llm)
        >>> print(override)
        0  # (0-indexed)
    """
    if not notes or len(notes.strip()) < 5:
        return None
    
    prompt = f"""
Analyze this user request and determine if they're specifying which Excel sheet to use:

"{notes}"

If they mention a sheet (e.g., "use sheet 1", "from the second sheet", "Summary sheet"), 
return ONLY the sheet identifier:
- If numeric: return just the number (0-indexed, so "sheet 1" = 0)
- If name: return just the sheet name
- If no sheet mentioned: return "NONE"

Examples:
"add all details from sheet 1" → 0
"use the second sheet" → 1
"extract from Summary sheet" → Summary
"add these rows" → NONE
"""
    
    try:
        result = llm_call_fn(
            system_prompt="You are a sheet reference detector. Return only the sheet identifier or NONE.",
            user_prompt=prompt
        ).strip()
        
        if result == "NONE" or not result:
            return None
        
        # Try to parse as int
        try:
            return int(result)
        except ValueError:
            # If it's a string (sheet name), return it
            # But if it's JSON or other format, return None
            if result.startswith('{') or result.startswith('['):
                return None
            return result
    except Exception as e:
        # If anything goes wrong, return None (no override)
        print(f"⚠ Sheet detection failed: {e}, using default config")
        return None

