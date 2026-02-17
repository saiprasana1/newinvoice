import json
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from core.state_store import update_state_with_json, get_initial_state
from core.invoice_math import calculate_invoice_totals
from core.field_validator import validate_edited_json
from utils.merge_utils import deep_merge

router = APIRouter()


def _flatten_to_nested(flat_dict: dict) -> dict:
    """Convert dot-notation keys to nested structure.

    Example: {"freight_bill.runs.0.rate": 750} → {"freight_bill": {"runs": [{"rate": 750}]}}
    """
    result = {}
    for key, value in flat_dict.items():
        if "." in key:
            parts = key.split(".")
            current = result

            for i, part in enumerate(parts[:-1]):
                next_part = parts[i + 1]

                if part.isdigit():
                    continue

                if next_part.isdigit():
                    if part not in current:
                        current[part] = []

                    idx = int(next_part)
                    while len(current[part]) <= idx:
                        current[part].append({})

                    current = current[part][idx]
                else:
                    if part not in current:
                        current[part] = {}
                    current = current[part]

            final_key = parts[-1]
            if not final_key.isdigit():
                current[final_key] = value
        else:
            result[key] = value
    return result


async def _update_fields_common(payload: Dict[str, Any]) -> dict:
    """
    Shared logic for both bill and tax update-fields endpoints.
    Merges edited fields into state, validates, recalculates, and persists.
    """
    edited_json = payload.get("edited_json", {})
    frontend_state = payload.get("state", {})

    if not isinstance(edited_json, dict):
        raise HTTPException(status_code=400, detail="edited_json must be a dictionary")

    if frontend_state and isinstance(frontend_state, dict):
        current_state = frontend_state
    else:
        current_state = get_initial_state()

    # Support both nested and dot-notation formats for edited_json
    if any("." in str(key) for key in edited_json.keys()):
        edited_json = _flatten_to_nested(edited_json)

    valid, errors = validate_edited_json(edited_json)
    if not valid:
        print(f"Warning: Validation warnings: {', '.join(errors)}")

    updated_state = deep_merge(current_state, edited_json)
    final_state = calculate_invoice_totals(updated_state)

    from core.state_store import save_overrides_locked
    saved = save_overrides_locked(final_state)
    if not saved:
        raise HTTPException(status_code=500, detail="Failed to persist changes to disk")

    return {
        "state": final_state,
        "success": True,
        "message": "Field updated successfully"
    }


@router.post("/api/invoice/bill/update-fields")
async def update_fields_from_json(payload: Dict[str, Any]):
    """Update bill invoice fields from inline editing JSON."""
    try:
        return await _update_fields_common(payload)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating fields: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error updating fields: {str(e)}")


@router.post("/api/invoice/tax/update-fields")
async def update_tax_fields_from_json(payload: Dict[str, Any]):
    """Update tax invoice fields from inline editing JSON."""
    try:
        return await _update_fields_common(payload)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating tax fields: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error updating fields: {str(e)}")
