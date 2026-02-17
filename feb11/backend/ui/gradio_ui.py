# gradio_ui.py
from __future__ import annotations

import os
import json
import gradio as gr
from typing import Optional, Tuple

from core.invoice_schema import get_default_invoice_data
from core.invoice_math import calculate_invoice_totals
from templates.invoice_templates import render_invoice_html_template, get_row_management_js_base64
from core.state_store import (
    load_overrides, apply_overrides, save_overrides, update_state_with_json,
    get_initial_state, save_combined_state, apply_user_patch, _deep_merge
)
# Old export functions removed - now using unified invoice_exporter module
from integrations.audio_transcribe import transcribe_audio

# MongoDB and context mapper
from integrations.mongodb_client import (
    get_all_bank_accounts, get_bank_account_by_id,
    get_all_client_companies, get_client_company_by_id,
    get_all_parent_companies, get_parent_company_by_id,
    get_all_terms_and_conditions, get_terms_and_conditions_by_id
)
from integrations.invoice_context_mapper import (
    map_bank_to_invoice_state,
    map_client_company_to_billing_to,
    map_parent_company_to_company_info,
    map_terms_to_invoice_state
)

# Split agents (feature-gated)
_HAS_SPLIT_AGENTS = False
_HAS_BILL_AGENT = False
try:
    # NEW: use the modern Tax Agent entrypoint
    from agents.invoice_agent_tax import agent_update_tax_from_file
    _HAS_SPLIT_AGENTS = True
except Exception:
    _HAS_SPLIT_AGENTS = False

try:
    # NEW: use the modern Bill Invoice Agent
    from agents.invoice_agent_bill import agent_update_bill_from_file
    _HAS_BILL_AGENT = True
except Exception:
    _HAS_BILL_AGENT = False


# --------------------- App state ---------------------
def initialize_app_state():
    base = get_default_invoice_data()
    ov = load_overrides()
    cur = apply_overrides(base, ov)
    cur = calculate_invoice_totals(cur)
    html_tax = render_invoice_html_template(cur, "Siva Sakthi GTA")
    html_bill = render_invoice_html_template(cur, "Siva Sakthi Freight Bill")
    # state, tax_preview, bill_preview, hidden_edit_buffer
    return cur, html_tax, html_bill, ""


# --------------------- Helpers -----------------------
# _deep_merge removed - imported from state_store

def _compute_diff_patch(current_state: dict, defaults: dict) -> dict:
    """
    Compute a differential patch: only fields that differ from defaults.
    This creates a minimal override JSON that only contains changed values.
    """
    diff_patch = {}
    
    for key, current_value in current_state.items():
        default_value = defaults.get(key)
        
        # Handle nested dicts (like billing_to, freight_bill)
        if isinstance(current_value, dict) and isinstance(default_value, dict):
            nested_diff = {}
            for nested_key, nested_current in current_value.items():
                nested_default = default_value.get(nested_key)
                # Only include if different from default
                if nested_current != nested_default:
                    nested_diff[nested_key] = nested_current
            if nested_diff:
                diff_patch[key] = nested_diff
        
        # Handle lists (like items)
        elif isinstance(current_value, list):
            # Always include lists if they differ from default
            if current_value != default_value:
                diff_patch[key] = current_value
        
        # Handle scalar values
        else:
            # Only include if different from default
            if current_value != default_value:
                diff_patch[key] = current_value
    
    return diff_patch

def _clean_items(items):
    out = []
    for it in items or []:
        if not isinstance(it, dict):
            continue
        def _f(x):
            try:
                return float((x or 0) or 0)
            except Exception:
                return 0.0
        out.append({
            "description": (it.get("description") or "").strip(),
            "hsn_code": (it.get("hsn_code") or "").strip(),
            "uom": (it.get("uom") or "").strip(),
            "quantity": _f(it.get("quantity")),
            "unit_price": _f(it.get("unit_price")),
            "gst_rate": _f(it.get("gst_rate") if it.get("gst_rate") is not None else 18),
            "line_discount": _f(it.get("line_discount")),
        })
    return out

def _update_store(inv):
    """
    Persist only changed fields to overrides (differential save).
    Compare against defaults and only save fields that differ.
    """
    from core.state_store import save_overrides
    from core.invoice_schema import get_default_invoice_data
    
    # Compute differential patch
    defaults = get_default_invoice_data()
    diff_patch = _compute_diff_patch(inv, defaults)
    
    # Save only the changed fields
    save_overrides(diff_patch)


# ---------------- Context files (tax/bill) ------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go up to invoice_app/
CTX_TAX_PATH  = os.path.join(ROOT, "contexts", "context_tax_invoice.py")
CTX_BILL_PATH = os.path.join(ROOT, "contexts", "context_bill_invoice.py")

# Context files are loaded from disk, no hardcoded defaults needed

def _ensure_file(path: str, default_text: str) -> None:
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(default_text)

def _read_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""

def _write_text(path: str, text: str) -> str:
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text or "")
        return "✅ Saved"
    except Exception as e:
        return f"⚠️ Save failed: {e}"

def load_contexts():
    # Context files should already exist, just read them
    return _read_text(CTX_TAX_PATH), _read_text(CTX_BILL_PATH)

def save_ctx_tax(text: str) -> str:
    return _write_text(CTX_TAX_PATH, text)

def save_ctx_bill(text: str) -> str:
    return _write_text(CTX_BILL_PATH, text)


# ---------------- Live sync from DOM -----------------
def live_sync_from_dom(edited_json, current_state):
    try:
        merged_state = update_state_with_json(edited_json, current_state)
        if "items" in merged_state:
            merged_state["items"] = _clean_items(merged_state.get("items", []))
        final = calculate_invoice_totals(merged_state)
        _update_store(final)
        html_tax = render_invoice_html_template(final, "Siva Sakthi GTA")
        html_bill = render_invoice_html_template(final, "Siva Sakthi Freight Bill")
        return final, html_tax, html_bill, "✓ Saved"
    except Exception as e:
        html_tax = render_invoice_html_template(current_state, "Siva Sakthi GTA")
        html_bill = render_invoice_html_template(current_state, "Siva Sakthi Freight Bill")
        return current_state, html_tax, html_bill, f"Error: {e}"


# ------------- Manual add/clear actions --------------
def add_empty_row(current):
    work = dict(current)
    items = list(work.get("items", []))
    items.append({"description": "", "hsn_code": "", "uom": "", "quantity": 0, "unit_price": 0, "gst_rate": 18, "line_discount": 0})
    work["items"] = items
    final = calculate_invoice_totals(work)
    _update_store(final)
    html_tax = render_invoice_html_template(final, "Siva Sakthi GTA")
    html_bill = render_invoice_html_template(final, "Siva Sakthi Freight Bill")
    return final, html_tax, html_bill, ""

def add_bill_run(current):
    work = dict(current)
    fb = dict(work.get("freight_bill", {}) or {})
    runs = list(fb.get("runs", []))
    runs.append({
        "date": "",
        "truck_no": "",
        "lr_no": "",
        "qty": 0.0,
        "rate": 0.0,
        "line_total": 0.0,
    })
    fb["runs"] = runs
    work["freight_bill"] = fb
    final = calculate_invoice_totals(work)
    _update_store(final)
    html_tax = render_invoice_html_template(final, "Siva Sakthi GTA")
    html_bill = render_invoice_html_template(final, "Siva Sakthi Freight Bill")
    return final, html_tax, html_bill, ""

def clear_tax_invoice_state(current):
    """Clear only tax invoice fields, preserve freight bill data."""
    from core.state_store import OVERRIDES_TAX_PATH, _safe_write
    
    # Clear the tax overrides file completely
    _safe_write(OVERRIDES_TAX_PATH, {})
    
    # Reload state from defaults (this will now have no tax overrides)
    final = get_initial_state()
    
    # Render templates
    html_tax = render_invoice_html_template(final, "Siva Sakthi GTA")
    html_bill = render_invoice_html_template(final, "Siva Sakthi Freight Bill")
    
    return final, html_tax, html_bill, "", ""

def clear_bill_invoice_state(current):
    """Clear only freight bill fields, preserve tax invoice data."""
    from core.state_store import OVERRIDES_BILL_PATH, _safe_write
    
    # Clear the bill overrides file completely
    _safe_write(OVERRIDES_BILL_PATH, {})
    
    # Reload state from defaults (this will now have no bill overrides)
    final = get_initial_state()
    
    # Render templates
    html_tax = render_invoice_html_template(final, "Siva Sakthi GTA")
    html_bill = render_invoice_html_template(final, "Siva Sakthi Freight Bill")
    
    return final, html_tax, html_bill, "", ""

def clear_invoice_state():
    """Clear all invoice data (both tax and freight bill) and reset to defaults."""
    from core.state_store import OVERRIDES_TAX_PATH, OVERRIDES_BILL_PATH, _safe_write
    
    # Clear both override files completely
    _safe_write(OVERRIDES_TAX_PATH, {})
    _safe_write(OVERRIDES_BILL_PATH, {})
    
    # Reload state from pure defaults (no overrides)
    base = get_initial_state()
    
    # Render templates
    html_tax = render_invoice_html_template(base, "Siva Sakthi GTA")
    html_bill = render_invoice_html_template(base, "Siva Sakthi Freight Bill")
    
    return base, html_tax, html_bill, "", ""

def handle_audio_transcription(audio_input):
    """Transcribe audio to text for agent commands."""
    if audio_input:
        text, status = transcribe_audio(audio_input)
        return (text or ""), (f"✅ {status}" if text else f"❌ {status}")
    return "", "No audio input"

# ----------------- MongoDB Bank Loading --------------------
def load_bank_dropdown_choices():
    """Load bank account choices from MongoDB for dropdown."""
    try:
        bank_accounts = get_all_bank_accounts()
        # Return list of tuples: (label, id)
        choices = [(ba["label"], ba["id"]) for ba in bank_accounts]
        return gr.Dropdown(choices=choices)
    except Exception as e:
        print(f"Error loading bank accounts: {e}")
        return gr.Dropdown(choices=[])

def load_bank_details(bank_id, current_state):
    """
    Load bank details from MongoDB and update invoice state.
    
    Args:
        bank_id: The ID of the selected bank account
        current_state: Current invoice state
    
    Returns:
        Tuple of (updated_state, tax_preview, bill_preview, status_message)
    """
    if not bank_id:
        return current_state, \
               render_invoice_html_template(current_state, "Siva Sakthi GTA"), \
               render_invoice_html_template(current_state, "Siva Sakthi Freight Bill"), \
               "⚠️ Please select a bank account"
    
    try:
        # Fetch bank document from MongoDB
        bank_doc = get_bank_account_by_id(bank_id)
        
        if not bank_doc:
            return current_state, \
                   render_invoice_html_template(current_state, "Siva Sakthi GTA"), \
                   render_invoice_html_template(current_state, "Siva Sakthi Freight Bill"), \
                   f"❌ Bank account not found: {bank_id}"
        
        # Map MongoDB document to invoice state format
        mapped_bank = map_bank_to_invoice_state(bank_doc)
        
        # Update current state with bank details
        updated_state = dict(current_state)
        if "company_info" not in updated_state:
            updated_state["company_info"] = {}
        updated_state["company_info"]["bank"] = mapped_bank
        
        # Save to overrides
        save_overrides(updated_state)
        
        # Recalculate totals
        updated_state = calculate_invoice_totals(updated_state)
        
        # Render previews
        html_tax = render_invoice_html_template(updated_state, "Siva Sakthi GTA")
        html_bill = render_invoice_html_template(updated_state, "Siva Sakthi Freight Bill")
        
        bank_name = bank_doc.get("bank_name", "Unknown")
        status_msg = f"✅ Loaded: {bank_name}"
        
        return updated_state, html_tax, html_bill, status_msg
    
    except Exception as e:
        error_msg = f"❌ Error loading bank: {str(e)}"
        print(error_msg)
        return current_state, \
               render_invoice_html_template(current_state, "Siva Sakthi GTA"), \
               render_invoice_html_template(current_state, "Siva Sakthi Freight Bill"), \
               error_msg

def load_client_dropdown_choices():
    """Load client company choices from MongoDB for dropdown."""
    try:
        client_companies = get_all_client_companies()
        # Return list of tuples: (label, id)
        choices = [(cc["label"], cc["id"]) for cc in client_companies]
        return gr.Dropdown(choices=choices)
    except Exception as e:
        print(f"Error loading client companies: {e}")
        return gr.Dropdown(choices=[])

def load_parent_dropdown_choices():
    """Load parent company choices from MongoDB for dropdown."""
    try:
        parent_companies = get_all_parent_companies()
        # Return list of tuples: (label, id)
        choices = [(pc["label"], pc["id"]) for pc in parent_companies]
        return gr.Dropdown(choices=choices)
    except Exception as e:
        print(f"Error loading parent companies: {e}")
        return gr.Dropdown(choices=[])

def load_parent_details(parent_id, current_state):
    """
    Load parent company details from MongoDB and update invoice state.
    
    Args:
        parent_id: The ID of the selected parent company
        current_state: Current invoice state
    
    Returns:
        Tuple of (updated_state, tax_preview, bill_preview, status_message)
    """
    if not parent_id:
        return current_state, \
               render_invoice_html_template(current_state, "Siva Sakthi GTA"), \
               render_invoice_html_template(current_state, "Siva Sakthi Freight Bill"), \
               "⚠️ Please select a parent company"
    
    try:
        # Fetch parent company from MongoDB
        parent_doc = get_parent_company_by_id(parent_id)
        
        if not parent_doc:
            return current_state, \
                   render_invoice_html_template(current_state, "Siva Sakthi GTA"), \
                   render_invoice_html_template(current_state, "Siva Sakthi Freight Bill"), \
                   f"❌ Parent company not found: {parent_id}"
        
        # Map MongoDB document to invoice state format
        mapped_parent = map_parent_company_to_company_info(parent_doc)
        
        # Update current state with parent company details using deep merge
        from core.state_store import _deep_merge
        updated_state = dict(current_state)
        if "company_info" not in updated_state:
            updated_state["company_info"] = {}
        updated_state["company_info"] = _deep_merge(updated_state["company_info"], mapped_parent)
        
        # Save to overrides
        save_overrides(updated_state)
        
        # Recalculate totals
        updated_state = calculate_invoice_totals(updated_state)
        
        # Render updated previews
        tax_preview = render_invoice_html_template(updated_state, "Siva Sakthi GTA")
        bill_preview = render_invoice_html_template(updated_state, "Siva Sakthi Freight Bill")
        
        parent_name = parent_doc.get('parent_company_title', 'Unknown')
        return updated_state, tax_preview, bill_preview, f"✅ Loaded: {parent_name}"
        
    except Exception as e:
        print(f"Error loading parent company: {e}")
        import traceback
        traceback.print_exc()
        return current_state, \
               render_invoice_html_template(current_state, "Siva Sakthi GTA"), \
               render_invoice_html_template(current_state, "Siva Sakthi Freight Bill"), \
               f"❌ Error: {str(e)}"

def load_bill_parent_details(parent_id, current_state):
    """
    Load parent company details for BILL INVOICE ONLY.
    Updates freight_bill.company_info and saves to overrides_bill.json.
    
    Args:
        parent_id: The ID of the selected parent company
        current_state: Current invoice state
    
    Returns:
        Tuple of (updated_state, tax_preview, bill_preview, status_message)
    """
    if not parent_id:
        return current_state, \
               render_invoice_html_template(current_state, "Siva Sakthi GTA"), \
               render_invoice_html_template(current_state, "Siva Sakthi Freight Bill"), \
               "⚠️ Please select a parent company"
    
    try:
        # Fetch parent company from MongoDB
        parent_doc = get_parent_company_by_id(parent_id)
        
        if not parent_doc:
            return current_state, \
                   render_invoice_html_template(current_state, "Siva Sakthi GTA"), \
                   render_invoice_html_template(current_state, "Siva Sakthi Freight Bill"), \
                   f"❌ Parent company not found: {parent_id}"
        
        # Map MongoDB document to invoice state format
        mapped_parent = map_parent_company_to_company_info(parent_doc)
        
        # Update BILL-SPECIFIC company info (inside freight_bill)
        from core.state_store import _deep_merge
        updated_state = dict(current_state)
        
        # Ensure freight_bill exists
        if "freight_bill" not in updated_state:
            updated_state["freight_bill"] = {}
        
        # Update freight_bill.company_info (NOT top-level company_info)
        if "company_info" not in updated_state["freight_bill"]:
            updated_state["freight_bill"]["company_info"] = {}
        
        updated_state["freight_bill"]["company_info"] = _deep_merge(
            updated_state["freight_bill"]["company_info"], 
            mapped_parent
        )
        
        # Save to overrides (will go to overrides_bill.json because it's under freight_bill)
        save_overrides(updated_state)
        
        # Recalculate totals
        updated_state = calculate_invoice_totals(updated_state)
        
        # Render updated previews
        tax_preview = render_invoice_html_template(updated_state, "Siva Sakthi GTA")
        bill_preview = render_invoice_html_template(updated_state, "Siva Sakthi Freight Bill")
        
        parent_name = parent_doc.get('parent_company_title', 'Unknown')
        return updated_state, tax_preview, bill_preview, f"✅ Loaded: {parent_name}"
        
    except Exception as e:
        print(f"Error loading bill parent company: {e}")
        import traceback
        traceback.print_exc()
        return current_state, \
               render_invoice_html_template(current_state, "Siva Sakthi GTA"), \
               render_invoice_html_template(current_state, "Siva Sakthi Freight Bill"), \
               f"❌ Error: {str(e)}"

def load_bill_client_details(client_id, current_state):
    """
    Load client company details for BILL INVOICE ONLY.
    Updates freight_bill.to_party and saves to overrides_bill.json.
    
    Args:
        client_id: The ID of the selected client company
        current_state: Current invoice state
    
    Returns:
        Tuple of (updated_state, tax_preview, bill_preview, status_message)
    """
    if not client_id:
        return current_state, \
               render_invoice_html_template(current_state, "Siva Sakthi GTA"), \
               render_invoice_html_template(current_state, "Siva Sakthi Freight Bill"), \
               "⚠️ Please select a client company"
    
    try:
        # Fetch client company from MongoDB
        client_doc = get_client_company_by_id(client_id)
        
        if not client_doc:
            return current_state, \
                   render_invoice_html_template(current_state, "Siva Sakthi GTA"), \
                   render_invoice_html_template(current_state, "Siva Sakthi Freight Bill"), \
                   f"❌ Client company not found: {client_id}"
        
        # Map MongoDB document to to_party format
        from integrations.invoice_context_mapper import map_client_company_to_to_party
        mapped_client = map_client_company_to_to_party(client_doc)
        
        # Update BILL-SPECIFIC client info (inside freight_bill.to_party)
        updated_state = dict(current_state)
        
        # Ensure freight_bill exists
        if "freight_bill" not in updated_state:
            updated_state["freight_bill"] = {}
        
        # Update freight_bill.to_party (NOT top-level billing_to)
        updated_state["freight_bill"]["to_party"] = mapped_client
        
        # Save to overrides (will go to overrides_bill.json because it's under freight_bill)
        save_overrides(updated_state)
        
        # Recalculate totals
        updated_state = calculate_invoice_totals(updated_state)
        
        # Render updated previews
        tax_preview = render_invoice_html_template(updated_state, "Siva Sakthi GTA")
        bill_preview = render_invoice_html_template(updated_state, "Siva Sakthi Freight Bill")
        
        client_name = client_doc.get('client_company_name', 'Unknown')
        return updated_state, tax_preview, bill_preview, f"✅ Loaded: {client_name}"
        
    except Exception as e:
        print(f"Error loading bill client company: {e}")
        import traceback
        traceback.print_exc()
        return current_state, \
               render_invoice_html_template(current_state, "Siva Sakthi GTA"), \
               render_invoice_html_template(current_state, "Siva Sakthi Freight Bill"), \
               f"❌ Error: {str(e)}"

def load_client_details(client_id, current_state):
    """
    Load client company details from MongoDB and update invoice state.
    
    Args:
        client_id: The ID of the selected client company
        current_state: Current invoice state
    
    Returns:
        Tuple of (updated_state, tax_preview, bill_preview, status_message)
    """
    if not client_id:
        return current_state, \
               render_invoice_html_template(current_state, "Siva Sakthi GTA"), \
               render_invoice_html_template(current_state, "Siva Sakthi Freight Bill"), \
               "⚠️ Please select a client company"
    
    try:
        # Fetch client document from MongoDB
        client_doc = get_client_company_by_id(client_id)
        
        if not client_doc:
            return current_state, \
                   render_invoice_html_template(current_state, "Siva Sakthi GTA"), \
                   render_invoice_html_template(current_state, "Siva Sakthi Freight Bill"), \
                   f"❌ Client company not found: {client_id}"
        
        # Map MongoDB document to invoice state format
        mapped_client = map_client_company_to_billing_to(client_doc)
        
        # Update current state with client details using deep merge
        from core.state_store import _deep_merge
        updated_state = dict(current_state)
        if "billing_to" not in updated_state:
            updated_state["billing_to"] = {}
        updated_state["billing_to"] = _deep_merge(updated_state["billing_to"], mapped_client)
        
        # Save to overrides
        save_overrides(updated_state)
        
        # Recalculate totals
        updated_state = calculate_invoice_totals(updated_state)
        
        # Render previews
        html_tax = render_invoice_html_template(updated_state, "Siva Sakthi GTA")
        html_bill = render_invoice_html_template(updated_state, "Siva Sakthi Freight Bill")
        
        client_name = client_doc.get("client_company_name", "Unknown")
        status_msg = f"✅ Loaded: {client_name}"
        
        return updated_state, html_tax, html_bill, status_msg
    
    except Exception as e:
        error_msg = f"❌ Error loading client: {str(e)}"
        print(error_msg)
        return current_state, \
               render_invoice_html_template(current_state, "Siva Sakthi GTA"), \
               render_invoice_html_template(current_state, "Siva Sakthi Freight Bill"), \
               error_msg


# ----------------- MongoDB T&C Loading --------------------
def load_tnc_dropdown_choices():
    """Load Terms and Conditions choices from MongoDB for dropdown."""
    try:
        tnc_list = get_all_terms_and_conditions()
        if not tnc_list:
            return gr.Dropdown(choices=[("No T&C available", "")])
        choices = [(tnc["label"], tnc["id"]) for tnc in tnc_list]
        return gr.Dropdown(choices=choices)
    except Exception as e:
        print(f"Error loading T&C dropdown: {e}")
        return gr.Dropdown(choices=[("Error loading T&C", "")])

def load_tnc_details(tnc_id, current_state):
    """
    Load terms and conditions from MongoDB and update invoice state.
    
    Args:
        tnc_id: The ID of the selected T&C
        current_state: Current invoice state
    
    Returns:
        Tuple of (updated_state, tax_preview, bill_preview, status_message)
    """
    if not tnc_id:
        return current_state, \
               render_invoice_html_template(current_state, "Siva Sakthi GTA"), \
               render_invoice_html_template(current_state, "Siva Sakthi Freight Bill"), \
               "⚠️ Please select terms & conditions"
    
    try:
        # Fetch T&C document from MongoDB
        tnc_doc = get_terms_and_conditions_by_id(tnc_id)
        
        if not tnc_doc:
            return current_state, \
                   render_invoice_html_template(current_state, "Siva Sakthi GTA"), \
                   render_invoice_html_template(current_state, "Siva Sakthi Freight Bill"), \
                   f"❌ Terms & conditions not found: {tnc_id}"
        
        # Map MongoDB document to invoice state format
        mapped_tnc = map_terms_to_invoice_state(tnc_doc)
        
        # Update current state with T&C using deep merge
        from core.state_store import _deep_merge
        updated_state = dict(current_state)
        updated_state = _deep_merge(updated_state, mapped_tnc)
        
        # Save to overrides
        save_overrides(updated_state)
        
        # Recalculate totals
        updated_state = calculate_invoice_totals(updated_state)
        
        # Render previews
        html_tax = render_invoice_html_template(updated_state, "Siva Sakthi GTA")
        html_bill = render_invoice_html_template(updated_state, "Siva Sakthi Freight Bill")
        
        tnc_label = tnc_doc.get("label", "Unknown")
        status_msg = f"✅ Loaded: {tnc_label}"
        
        return updated_state, html_tax, html_bill, status_msg
    
    except Exception as e:
        error_msg = f"❌ Error loading T&C: {str(e)}"
        print(error_msg)
        return current_state, \
               render_invoice_html_template(current_state, "Siva Sakthi GTA"), \
               render_invoice_html_template(current_state, "Siva Sakthi Freight Bill"), \
               error_msg


# ----------------- Export helpers (Unified System) --------------------
from export.invoice_exporter import export_invoice

def _prepare_invoice_for_export(current, edited_json):
    """Prepare invoice data by merging with edited JSON"""
    work = dict(current)
    if edited_json and edited_json.strip():
        try:
            ed = json.loads(edited_json) or {}
            if "items" in ed:
                ed["items"] = _clean_items(ed.get("items", []))
            work = _deep_merge(work, ed)
        except Exception:
            pass
    return work

def export_invoice_generic(current, download_dir, edited_json, template_name, format):
    """
    Unified export function for any invoice template.
    
    Args:
        current: Current invoice state
        download_dir: Output directory
        edited_json: Optional JSON edits to apply
        template_name: Template name (e.g., "Siva Sakthi GTA")
        format: 'pdf' or 'png'
    """
    if not download_dir:
        import tempfile
        download_dir = tempfile.gettempdir()
    
    invoice_data = _prepare_invoice_for_export(current, edited_json)
    return export_invoice(invoice_data, template_name, format, download_dir)

# Convenience wrappers for UI (can be removed if UI is updated to use generic function)
def export_tax_png(current, download_dir, edited_json=None):
    return export_invoice_generic(current, download_dir, edited_json, "Siva Sakthi GTA", 'png')

def export_tax_pdf(current, download_dir, edited_json=None):
    return export_invoice_generic(current, download_dir, edited_json, "Siva Sakthi GTA", 'pdf')

def export_bill_png(current, download_dir, edited_json=None):
    return export_invoice_generic(current, download_dir, edited_json, "Siva Sakthi Freight Bill", 'png')

def export_bill_pdf(current, download_dir, edited_json=None):
    return export_invoice_generic(current, download_dir, edited_json, "Siva Sakthi Freight Bill", 'pdf')


# -------------- Split-agent actions ------------------
# --- keep all existing imports / code above ---

def run_tax_agent_action(current_state, file_obj, user_notes: str, ctx_text: str, edited_json: str) -> Tuple[str, str, str, dict]:
    if not _HAS_SPLIT_AGENTS:
        tax_html = render_invoice_html_template(current_state, "Siva Sakthi GTA")
        bill_html = render_invoice_html_template(current_state, "Siva Sakthi Freight Bill")
        return tax_html, bill_html, "Split agents not installed.", current_state
    try:
        # Don't save edited_json here - the agent handles all persistence
        work = dict(current_state)
        
        df_path = getattr(file_obj, "name", None) if file_obj else None
        # NEW: allow running notes-only (no file) too
        if not df_path and not (user_notes and user_notes.strip()):
            tax_html = render_invoice_html_template(work, "Siva Sakthi GTA")
            bill_html = render_invoice_html_template(work, "Siva Sakthi Freight Bill")
            return tax_html, bill_html, "❌ No file uploaded and no notes provided.", work

        # NEW: call modern Tax Agent with notes
        # agent_update_tax_from_file now accepts user_notes (may be None)
        updated_state, report = agent_update_tax_from_file(df_path, work, user_notes=user_notes or "")

        final = calculate_invoice_totals(updated_state)
        
        # Save the updated state (differential save)
        _update_store(final)
        
        html_tax = render_invoice_html_template(final, "Siva Sakthi GTA")
        html_bill = render_invoice_html_template(final, "Siva Sakthi Freight Bill")

        try:
            report_text = json.dumps(report, indent=2, ensure_ascii=False)
        except Exception:
            report_text = str(report)

        return html_tax, html_bill, report_text, final
    except Exception as e:
        tax_html = render_invoice_html_template(current_state, "Siva Sakthi GTA")
        bill_html = render_invoice_html_template(current_state, "Siva Sakthi Freight Bill")
        return tax_html, bill_html, f"⚠️ Tax agent failed: {e}", current_state


def run_bill_agent_action(current_state, file_obj, user_notes: str, ctx_text: str, edited_json: str) -> Tuple[str, str, str, dict]:
    """Run Bill Invoice agent with agentic operations."""
    if not _HAS_BILL_AGENT:
        tax_html = render_invoice_html_template(current_state, "Siva Sakthi GTA")
        bill_html = render_invoice_html_template(current_state, "Siva Sakthi Freight Bill")
        return tax_html, bill_html, "Bill agent not installed.", current_state
    try:
        work = dict(current_state)
        
        df_path = getattr(file_obj, "name", None) if file_obj else None
        # Allow running notes-only (no file) too
        if not df_path and not (user_notes and user_notes.strip()):
            tax_html = render_invoice_html_template(work, "Siva Sakthi GTA")
            bill_html = render_invoice_html_template(work, "Siva Sakthi Freight Bill")
            return tax_html, bill_html, "❌ No file uploaded and no notes provided.", work

        # Call Bill Invoice Agent with notes
        updated_state, report = agent_update_bill_from_file(df_path, work, user_notes=user_notes or "")

        final = calculate_invoice_totals(updated_state)
        
        # Save the updated state (differential save)
        _update_store(final)
        
        html_tax = render_invoice_html_template(final, "Siva Sakthi GTA")
        html_bill = render_invoice_html_template(final, "Siva Sakthi Freight Bill")

        try:
            report_text = json.dumps(report, indent=2, ensure_ascii=False)
        except Exception:
            report_text = str(report)

        return html_tax, html_bill, report_text, final
    except Exception as e:
        import traceback
        tax_html = render_invoice_html_template(current_state, "Siva Sakthi GTA")
        bill_html = render_invoice_html_template(current_state, "Siva Sakthi Freight Bill")
        error_msg = f"⚠️ Bill agent failed: {e}\n\n{traceback.format_exc()}"
        return tax_html, bill_html, error_msg, current_state


# ------------------------- UI ------------------------
def build_gradio_ui():
    theme = gr.themes.Soft(primary_hue="indigo", neutral_hue="slate")

    css = """
    .app-wrap { max-width: 1280px; margin: 0 auto; }
    .card {
        background: #ffffff;
        border: 1px solid rgba(15, 23, 42, .08);
        border-radius: 12px;
        box-shadow: 0 10px 24px -12px rgba(2, 6, 23, .15);
        padding: 16px;
    }
    .toolbar .gr-button { min-width: 90px; }
    .toolbar { gap: 8px !important; }
    .section-title {
        font-weight: 600; font-size: 14px; color: #0f172a;
        display:flex; align-items:center; gap:8px; margin-bottom:8px;
    }
    .section-title .dot {
        width:10px; height:10px; border-radius:50%; background:#6366f1; display:inline-block;
    }
    .invoice-preview {
        background: white;
        border: 1px solid rgba(15, 23, 42, .08);
        border-radius: 8px;
        padding: 8px;
    }
    .sync-badge {
        display:inline-block;
        padding:2px 8px; border-radius:999px; font-size:11px; line-height:18px;
        border:1px solid rgba(15, 23, 42, 0.12);
        background:#f8fafc; color:#334155;
        transition: opacity .3s ease;
    }
    .sync-badge.hidden { opacity:0; visibility:hidden; }
    .hidden-sync-field { display: none !important; }

    /* make both context editors scrollable/resizable */
    #ctx_tax_box textarea,
    #ctx_bill_box textarea {
        max-height: 360px;
        min-height: 220px;
        overflow: auto;
        resize: vertical;
        line-height: 1.3;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, "Courier New", monospace;
    }
    """

    commit_dom_js = r"""
    function () {
      const root = (window.gradioApp && window.gradioApp()) || document;
      const previews = root.querySelectorAll('#invoice_preview_tax, #invoice_preview_bill');
      previews.forEach((preview) => {
        if (!preview) return;
        preview.querySelectorAll('.editable.editing input').forEach(inp => { try { inp.blur(); } catch(e){} });
      });
      try {
        if (window.InvoiceRowManager && window.InvoiceRowManager.captureAndSendData) {
          window.InvoiceRowManager.captureAndSendData();
        }
      } catch(e) {}
      const tb = root.querySelector('#edited_invoice_data textarea') ||
                 root.querySelector('textarea[aria-label="edited_invoice_data"]');
      return tb ? tb.value : "";
    }
    """

    with gr.Blocks(title="Invoices", theme=theme, css=css, elem_classes=["app-wrap"]) as demo:
        invoice_state = gr.State()

        # Header
        gr.HTML("""
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
          <div style="display:flex;align-items:center;gap:12px;">
            <div style="width:36px;height:36px;border-radius:10px;background:#e0e7ff;display:flex;align-items:center;justify-content:center;">
              <span style="font-weight:800;color:#4338ca;">SS</span>
            </div>
            <div>
              <div style="font-weight:700;color:#0f172a;">Siva Sakthi Invoices</div>
              <div style="font-size:12px;color:#475569;">Inline edits • Live sync • PNG/PDF export • Dual preview</div>
            </div>
          </div>
          <div id="sync_badge" class="sync-badge hidden">Syncing…</div>
        </div>
        """)

        with gr.Row(equal_height=True):
            # Left column
            with gr.Column(scale=5):
                # Manual controls
                with gr.Group(elem_classes=["card"]):
                    gr.HTML('<div class="section-title"><span class="dot"></span>Manual Edits</div>')
                    with gr.Row(elem_classes=["toolbar"]):
                        btn_add_tax = gr.Button("Add Row to Tax Invoice")
                        btn_clear_tax = gr.Button("Clear Tax Invoice")
                    with gr.Row(elem_classes=["toolbar"]):
                        btn_add_bill = gr.Button("Add Run to Bill Invoice")
                        btn_clear_bill = gr.Button("Clear Bill Invoice")

                # Agents & context (split)
                with gr.Group(elem_classes=["card"]):
                    gr.HTML('<div class="section-title"><span class="dot"></span>Agents & Context</div>')
                    if _HAS_SPLIT_AGENTS:
                        with gr.Tab("Tax Agent"):
                            # Parent Company Section
                            with gr.Accordion("🏢 Load Parent Company from Database", open=False):
                                parent_dropdown = gr.Dropdown(
                                    label="Select Parent Company",
                                    choices=[],
                                    value=None,
                                    interactive=True
                                )
                                load_parent_btn = gr.Button("Load Parent Company", variant="secondary")
                                parent_load_status = gr.Textbox(label="Status", interactive=False, lines=1)
                            
                            # Bank Details Section
                            with gr.Accordion("🏦 Load Bank Details from Database", open=False):
                                bank_dropdown = gr.Dropdown(
                                    label="Select Bank Account",
                                    choices=[],
                                    value=None,
                                    interactive=True
                                )
                                load_bank_btn = gr.Button("Load Bank Details", variant="secondary")
                                bank_load_status = gr.Textbox(label="Status", interactive=False, lines=1)
                            
                            # Client Company Section
                            with gr.Accordion("👥 Load Client Company from Database", open=False):
                                client_dropdown = gr.Dropdown(
                                    label="Select Client Company",
                                    choices=[],
                                    value=None,
                                    interactive=True
                                )
                                load_client_btn = gr.Button("Load Client Company", variant="secondary")
                                client_load_status = gr.Textbox(label="Status", interactive=False, lines=1)
                            
                            # Terms and Conditions Section (Tax Invoice only)
                            with gr.Accordion("📋 Load Terms & Conditions from Database", open=False):
                                tnc_dropdown = gr.Dropdown(
                                    label="Select Terms & Conditions",
                                    choices=[],
                                    value=None,
                                    interactive=True
                                )
                                load_tnc_btn = gr.Button("Load Terms & Conditions", variant="secondary")
                                tnc_load_status = gr.Textbox(label="Status", interactive=False, lines=1)
                            
                            tax_file = gr.File(label="Tax: Upload Excel/CSV", file_types=[".xlsx", ".xls", ".csv"], type="filepath")
                            tax_notes = gr.Textbox(label="Agent notes (optional)", lines=3, placeholder="e.g., cgst=6 sgst=6 igst=5")
                            
                            with gr.Accordion("🎤 Voice Input (Optional)", open=False):
                                tax_audio_input = gr.Audio(sources=["microphone"], type="filepath", label="Record Command")
                                tax_audio_status = gr.Textbox(label="Transcription Status", interactive=False, lines=1)
                            
                            ctx_tax = gr.Textbox(
                                label="context_tax_invoice.py",
                                lines=10,
                                value="",
                                placeholder="Tax Invoice context configuration...",
                                elem_id="ctx_tax_box",  # scrollable
                            )
                            tax_ctx_status = gr.Markdown("", visible=True)
                            run_tax_btn = gr.Button("Run Tax Agent", variant="primary")

                        with gr.Tab("Bill Agent"):
                            # Parent Company Section
                            with gr.Accordion("🏢 Load Parent Company from Database", open=False):
                                bill_parent_dropdown = gr.Dropdown(
                                    label="Select Parent Company",
                                    choices=[],
                                    interactive=True
                                )
                                load_bill_parent_btn = gr.Button("Load Parent Company", variant="secondary")
                                bill_parent_status = gr.Textbox(label="Status", interactive=False, max_lines=1)
                            
                            with gr.Accordion("🏭 Load Client Company from Database", open=False):
                                bill_client_dropdown = gr.Dropdown(
                                    label="Select Client Company",
                                    choices=[],
                                    interactive=True
                                )
                                load_bill_client_btn = gr.Button("Load Client Company", variant="secondary")
                                bill_client_status = gr.Textbox(label="Status", interactive=False, max_lines=1)
                            
                            bill_file = gr.File(label="Bill: Upload Excel/CSV", file_types=[".xlsx", ".xls", ".csv"], type="filepath")
                            bill_notes = gr.Textbox(label="Agent notes (optional)", lines=3, placeholder="e.g., to=Zuari Cement Ltd")
                            
                            with gr.Accordion("🎤 Voice Input (Optional)", open=False):
                                bill_audio_input = gr.Audio(sources=["microphone"], type="filepath", label="Record Command")
                                bill_audio_status = gr.Textbox(label="Transcription Status", interactive=False, lines=1)
                            
                            ctx_bill = gr.Textbox(
                                label="context_bill_invoice.py",
                                lines=10,
                                value="",
                                placeholder="Bill Invoice context configuration...",
                                elem_id="ctx_bill_box",  # scrollable
                            )
                            bill_ctx_status = gr.Markdown("", visible=True)
                            run_bill_btn = gr.Button("Run Bill Agent", variant="primary")
                    else:
                        gr.Markdown("> *Split agents not detected — please ensure `agent_update_tax_from_file` is available in `invoice_agent.py`.*")

                with gr.Accordion("Export", open=False):
                    out_dir = gr.Textbox(label="Download Directory (optional)", value="")
                    gr.HTML('<div style="font-size:12px;color:#475569;margin:.25rem 0 .5rem;">Tax Invoice</div>')
                    with gr.Row():
                        btn_png_tax = gr.Button("Export Tax PNG")
                        btn_pdf_tax = gr.Button("Export Tax PDF")
                    gr.HTML('<div style="font-size:12px;color:#475569;margin:.75rem 0 .5rem;">Freight Bill</div>')
                    with gr.Row():
                        btn_png_bill = gr.Button("Export Bill PNG")
                        btn_pdf_bill = gr.Button("Export Bill PDF")
                    export_file = gr.File(label="Download file")
                    export_status = gr.Textbox(label="Export status", interactive=False)

            # Right column (dual preview)
            with gr.Column(scale=7):
                with gr.Group(elem_classes=["card"]):
                    gr.HTML('<div class="section-title"><span class="dot"></span>Preview</div>')
                    with gr.Tabs():
                        with gr.Tab("Tax Invoice"):
                            preview_tax = gr.HTML(elem_classes=["invoice-preview"], elem_id="invoice_preview_tax")
                        with gr.Tab("Freight Bill"):
                            preview_bill = gr.HTML(elem_classes=["invoice-preview"], elem_id="invoice_preview_bill")
                    edited = gr.Textbox(visible=True, elem_id="edited_invoice_data", container=False, show_label=False, elem_classes=["hidden-sync-field"])
                    gr.HTML('<div style="color:#64748b;font-size:12px;margin-top:6px;">Tip: click any light-gray field to type. Changes auto-save.</div>')

        # Init + load contexts
        demo.load(initialize_app_state, outputs=[invoice_state, preview_tax, preview_bill, edited])
        if _HAS_SPLIT_AGENTS:
            # load both contexts in a single call (prevents "too many outputs" warning)
            demo.load(load_contexts, outputs=[ctx_tax, ctx_bill])
            # Load parent dropdown choices from MongoDB
            demo.load(load_parent_dropdown_choices, outputs=[parent_dropdown])
            # Load bank dropdown choices from MongoDB
            demo.load(load_bank_dropdown_choices, outputs=[bank_dropdown])
            # Load client dropdown choices from MongoDB
            demo.load(load_client_dropdown_choices, outputs=[client_dropdown])
            # Load T&C dropdown choices from MongoDB
            demo.load(load_tnc_dropdown_choices, outputs=[tnc_dropdown])
            # Load Bill Agent parent dropdown
            demo.load(load_parent_dropdown_choices, outputs=[bill_parent_dropdown])
            demo.load(load_client_dropdown_choices, outputs=[bill_client_dropdown])

        # Live Sync badge
        def _echo(s): return s
        edited.change(
            fn=_echo, inputs=[edited], outputs=[edited],
            js=r"""
            function () {
              const b = document.getElementById('sync_badge');
              if (b) { b.textContent = 'Syncing…'; b.classList.remove('hidden'); }
              return [...arguments][0];
            }
            """
        ).then(
            fn=live_sync_from_dom,
            inputs=[edited, invoice_state],
            outputs=[invoice_state, preview_tax, preview_bill, gr.Textbox(visible=False)],
        ).then(
            fn=None, inputs=[], outputs=[],
            js=r"""
            function () {
              const b = document.getElementById('sync_badge');
              if (!b) return [];
              b.textContent = '✓ Saved';
              setTimeout(() => b.classList.add('hidden'), 700);
              return [];
            }
            """
        )

        # Manual add/clear
        btn_add_tax.click(
            fn=_echo, inputs=[edited], outputs=[edited], js=commit_dom_js
        ).then(
            fn=live_sync_from_dom,
            inputs=[edited, invoice_state],
            outputs=[invoice_state, preview_tax, preview_bill, gr.Textbox(visible=False)],
        ).then(
            fn=add_empty_row,
            inputs=[invoice_state],
            outputs=[invoice_state, preview_tax, preview_bill, gr.Markdown(visible=False)],
        )

        btn_add_bill.click(
            fn=_echo, inputs=[edited], outputs=[edited], js=commit_dom_js
        ).then(
            fn=live_sync_from_dom,
            inputs=[edited, invoice_state],
            outputs=[invoice_state, preview_tax, preview_bill, gr.Textbox(visible=False)],
        ).then(
            fn=add_bill_run,
            inputs=[invoice_state],
            outputs=[invoice_state, preview_tax, preview_bill, gr.Markdown(visible=False)],
        )

        btn_clear_tax.click(
            fn=clear_tax_invoice_state,
            inputs=[invoice_state],
            outputs=[invoice_state, preview_tax, preview_bill, gr.Markdown(visible=False), edited],
        )

        btn_clear_bill.click(
            fn=clear_bill_invoice_state,
            inputs=[invoice_state],
            outputs=[invoice_state, preview_tax, preview_bill, gr.Markdown(visible=False), edited],
        )

        # Exports
        for btn, fn_exp in [
            (btn_png_tax, export_tax_png),
            (btn_pdf_tax, export_tax_pdf),
            (btn_png_bill, export_bill_png),
            (btn_pdf_bill, export_bill_pdf),
        ]:
            btn.click(
                fn=_echo, inputs=[edited], outputs=[edited], js=commit_dom_js
            ).then(
                fn=live_sync_from_dom,
                inputs=[edited, invoice_state],
                outputs=[invoice_state, preview_tax, preview_bill, gr.Textbox(visible=False)],
            ).then(
                fn=fn_exp,
                inputs=[invoice_state, out_dir, edited],
                outputs=[export_file, export_status],
            )

        # Load inline-edit script once
        demo.load(
            None, None, None,
            js=f"""
                () => {{
                    try {{
                        if (!window.__invoiceRowManagerLoaded) {{
                            const s = document.createElement('script');
                            s.type = 'text/javascript';
                            s.src = 'data:text/javascript;base64,{get_row_management_js_base64()}';
                            document.head.appendChild(s);
                            window.__invoiceRowManagerLoaded = true;
                        }}
                    }} catch (e) {{
                        console.error('Failed to load invoice row manager:', e);
                    }}
                }}
            """
        )

        # Context auto-save + Agent wiring
                # Context auto-save + Agent wiring
        if _HAS_SPLIT_AGENTS:
            ctx_tax.change(fn=save_ctx_tax, inputs=[ctx_tax], outputs=[tax_ctx_status])
            ctx_bill.change(fn=save_ctx_bill, inputs=[ctx_bill], outputs=[bill_ctx_status])

            # Audio transcription for Tax Agent
            tax_audio_input.stop_recording(
                fn=handle_audio_transcription,
                inputs=[tax_audio_input],
                outputs=[tax_notes, tax_audio_status],
            )

            # Audio transcription for Bill Agent
            bill_audio_input.stop_recording(
                fn=handle_audio_transcription,
                inputs=[bill_audio_input],
                outputs=[bill_notes, bill_audio_status],
            )

            # Parent company loading
            load_parent_btn.click(
                fn=load_parent_details,
                inputs=[parent_dropdown, invoice_state],
                outputs=[invoice_state, preview_tax, preview_bill, parent_load_status],
            )

            # Bank loading
            load_bank_btn.click(
                fn=load_bank_details,
                inputs=[bank_dropdown, invoice_state],
                outputs=[invoice_state, preview_tax, preview_bill, bank_load_status],
            )

            # Client loading
            load_client_btn.click(
                fn=load_client_details,
                inputs=[client_dropdown, invoice_state],
                outputs=[invoice_state, preview_tax, preview_bill, client_load_status],
            )
            
            load_tnc_btn.click(
                fn=load_tnc_details,
                inputs=[tnc_dropdown, invoice_state],
                outputs=[invoice_state, preview_tax, preview_bill, tnc_load_status],
            )

            # Bill Agent - Parent Company Loading
            load_bill_parent_btn.click(
                fn=load_bill_parent_details,
                inputs=[bill_parent_dropdown, invoice_state],
                outputs=[invoice_state, preview_tax, preview_bill, bill_parent_status],
            )
            
            # Bill Agent - Client Company Loading
            load_bill_client_btn.click(
                fn=load_bill_client_details,
                inputs=[bill_client_dropdown, invoice_state],
                outputs=[invoice_state, preview_tax, preview_bill, bill_client_status],
            )

            run_tax_btn.click(
                fn=run_tax_agent_action,
                inputs=[invoice_state, tax_file, tax_notes, ctx_tax, edited],
                outputs=[preview_tax, preview_bill, gr.Markdown(visible=True), invoice_state],
            )

            run_bill_btn.click(
                fn=lambda s: s, inputs=[edited], outputs=[edited], js=commit_dom_js
            ).then(
                fn=live_sync_from_dom,
                inputs=[edited, invoice_state],
                outputs=[invoice_state, preview_tax, preview_bill, gr.Textbox(visible=False)],
            ).then(
                fn=run_bill_agent_action,
                inputs=[invoice_state, bill_file, bill_notes, ctx_bill, edited],
                outputs=[preview_tax, preview_bill, gr.Markdown(visible=True), invoice_state],
            )

        # 💾 Final safety: save on tab close
        demo.load(None, None, None, js="""
            () => {
              window.addEventListener("beforeunload", () => {
                try {
                  if (window.InvoiceRowManager?.captureAndSendData) {
                    window.InvoiceRowManager.captureAndSendData();
                  }
                } catch(e) {}
              });
            }
        """)

    return demo
