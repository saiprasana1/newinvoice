import json
from typing import Dict, Any, Tuple


def validate_numeric_field(value, field_name: str) -> Tuple[bool, str]:
    """Validate that a value is numeric."""
    try:
        float(value)
        return True, ""
    except (ValueError, TypeError):
        return False, f"{field_name} must be numeric"


def validate_date_field(value, field_name: str) -> Tuple[bool, str]:
    """Validate date format DD-MM-YYYY."""
    if not value:
        return True, ""
    
    import re
    if not re.match(r'^\d{2}-\d{2}-\d{4}$', str(value)):
        return False, f"{field_name} must be in DD-MM-YYYY format"
    
    return True, ""


def validate_text_field(value, field_name: str) -> Tuple[bool, str]:
    """Validate text field."""
    if not isinstance(value, str):
        return False, f"{field_name} must be text"
    return True, ""


def validate_freight_run(run: Dict[str, Any], index: int) -> Tuple[bool, list]:
    """Validate a single freight run row."""
    errors = []
    
    if "date" in run:
        valid, msg = validate_date_field(run["date"], f"Run {index + 1} Date")
        if not valid:
            errors.append(msg)
    
    if "dc_qty_mt" in run:
        valid, msg = validate_numeric_field(run["dc_qty_mt"], f"Run {index + 1} DC Qty")
        if not valid:
            errors.append(msg)
    
    if "gr_qty_mt" in run:
        valid, msg = validate_numeric_field(run["gr_qty_mt"], f"Run {index + 1} GR Qty")
        if not valid:
            errors.append(msg)
    
    if "rate" in run:
        valid, msg = validate_numeric_field(run["rate"], f"Run {index + 1} Rate")
        if not valid:
            errors.append(msg)
    
    return len(errors) == 0, errors


def validate_freight_bill(freight_bill: Dict[str, Any]) -> Tuple[bool, list]:
    """Validate entire freight bill section."""
    errors = []
    
    if not isinstance(freight_bill, dict):
        return False, ["freight_bill must be a dictionary"]
    
    if "runs" in freight_bill and isinstance(freight_bill["runs"], list):
        for idx, run in enumerate(freight_bill["runs"]):
            if isinstance(run, dict):
                valid, run_errors = validate_freight_run(run, idx)
                if not valid:
                    errors.extend(run_errors)
    
    return len(errors) == 0, errors


def validate_edited_json(edited_json: Dict[str, Any]) -> Tuple[bool, list]:
    """Validate the entire edited JSON payload."""
    errors = []
    
    if "freight_bill" in edited_json:
        valid, fb_errors = validate_freight_bill(edited_json["freight_bill"])
        if not valid:
            errors.extend(fb_errors)
    
    return len(errors) == 0, errors
