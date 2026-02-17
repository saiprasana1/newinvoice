import json
import os
import sys

from utils.merge_utils import deep_merge

# Windows-compatible file locking
try:
    import fcntl  # Unix/Linux/macOS
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False
    try:
        import msvcrt  # Windows
        HAS_MSVCRT = True
    except ImportError:
        HAS_MSVCRT = False

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "config")
DEFAULTS_PATH = os.path.join(CONFIG_DIR, "defaults.json")
OVERRIDES_BILL_PATH = os.path.join(CONFIG_DIR, "overrides_bill.json")
OVERRIDES_TAX_PATH = os.path.join(CONFIG_DIR, "overrides_tax.json")

# ---------- Helpers ----------
def _get_defaults() -> dict:
    """Load defaults from defaults.json"""
    if not os.path.exists(DEFAULTS_PATH):
        return {}
    try:
        with open(DEFAULTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _load_bill_overrides() -> dict:
    """Load only bill overrides from overrides_bill.json"""
    if not os.path.exists(OVERRIDES_BILL_PATH):
        return {}
    try:
        with open(OVERRIDES_BILL_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _load_tax_overrides() -> dict:
    """Load only tax overrides from overrides_tax.json"""
    if not os.path.exists(OVERRIDES_TAX_PATH):
        return {}
    try:
        with open(OVERRIDES_TAX_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _load_split_overrides() -> dict:
    """Load overrides from both bill and tax files, merge them"""
    overrides = {}

    bill_data = _load_bill_overrides()
    if bill_data:
        overrides = deep_merge(overrides, bill_data)

    tax_data = _load_tax_overrides()
    if tax_data:
        overrides = deep_merge(overrides, tax_data)

    return overrides


def _safe_write(file_path: str, data: dict) -> bool:
    """
    Write data to file with platform-specific locking.
    Windows: uses msvcrt.locking()
    Unix/Linux/macOS: uses fcntl.flock()
    Fallback: best-effort write without locking
    """
    temp_path = file_path + ".tmp"
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        if HAS_FCNTL:
            # Unix/Linux/macOS: use fcntl
            with open(temp_path, "w", encoding="utf-8") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    f.flush()
                    os.fsync(f.fileno())
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        elif HAS_MSVCRT:
            # Windows: write to temp, then atomic replace
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
        else:
            # Fallback: write without locking
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()

        # os.replace is atomic on both Windows and Unix
        os.replace(temp_path, file_path)
        return True
    except Exception as e:
        print(f"Error writing to {file_path}: {e}")
        # Clean up temp file if it exists
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass
        return False


def _save_split_overrides(state: dict) -> bool:
    """
    Save state to split override files.
    Extracts freight_bill into bill file, everything else into tax file.
    Preserves existing overrides if new state is empty.
    """
    success = True

    # Save freight_bill overrides
    if "freight_bill" in state:
        bill_overrides = {"freight_bill": state["freight_bill"]}
        if not _safe_write(OVERRIDES_BILL_PATH, bill_overrides):
            success = False
    elif os.path.exists(OVERRIDES_BILL_PATH):
        # If no freight_bill in state but file exists, preserve it
        pass

    # Save tax overrides (all keys except freight_bill)
    tax_keys = {k: v for k, v in state.items() if k != "freight_bill"}
    if tax_keys:
        if not _safe_write(OVERRIDES_TAX_PATH, tax_keys):
            success = False
    elif os.path.exists(OVERRIDES_TAX_PATH):
        # If no tax keys in state but file exists, preserve it
        pass

    return success


def save_overrides_locked(state: dict) -> bool:
    """
    Thread-safe save with file locking.
    Saves to split override files.
    """
    return _save_split_overrides(state)


def save_overrides(state: dict) -> bool:
    """
    Legacy function for backward compatibility.
    Saves state to split override files.
    """
    return _save_split_overrides(state)


# ---------- Type-specific state loaders ----------
def get_bill_initial_state() -> dict:
    """Get state for bill invoice: defaults + bill overrides only."""
    defaults = _get_defaults()
    overrides = _load_bill_overrides()
    return deep_merge(defaults, overrides)


def get_tax_initial_state() -> dict:
    """Get state for tax invoice: defaults + tax overrides only."""
    defaults = _get_defaults()
    overrides = _load_tax_overrides()
    merged = deep_merge(defaults, overrides)

    # Remove freight_bill key to prevent misidentification as bill invoice
    if "freight_bill" in merged:
        del merged["freight_bill"]

    # Remove shipping_to as it's not used in tax invoice templates
    if "shipping_to" in merged:
        del merged["shipping_to"]

    return merged


def get_initial_state() -> dict:
    """
    Get the full merged state: defaults + all overrides.
    Kept for backward compatibility (fallback in field editor).
    """
    defaults = _get_defaults()
    overrides = _load_split_overrides()
    return deep_merge(defaults, overrides)


def update_state_with_json(edit_json: str, base_state: dict) -> dict:
    """
    Parse a JSON string, merge it with base_state, persist, and return the result.
    """
    try:
        if isinstance(edit_json, str):
            edited_dict = json.loads(edit_json)
        else:
            edited_dict = edit_json
    except (json.JSONDecodeError, TypeError):
        return base_state

    if not isinstance(edited_dict, dict):
        return base_state

    # Merge
    merged = deep_merge(base_state, edited_dict)

    # Persist the split slices
    _save_split_overrides(merged)

    return merged


# ---------- live edit helpers (split-aware) ----------
def update_field(path: str, value):
    """
    Persist an individual field edit into the correct split file,
    and enforce company state defaults if cleared.
    """
    state = get_initial_state()

    # Parse path and update
    parts = path.split(".")
    current = state
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value

    # Persist
    _save_split_overrides(state)
    return state
