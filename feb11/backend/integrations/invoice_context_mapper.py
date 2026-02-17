"""
invoice_context_mapper.py

Pure mapping functions (NO DB calls, NO Gradio, NO templates).

Purpose:
- Convert MongoDB "master data" documents (bank_accounts / parent_companies / client_companies)
  into the shape your invoice runtime state expects (company_info / billing_to / company_info.bank).

Why this file exists:
- MongoDB field names can be descriptive and stable.
- Invoice state field names are template-driven.
- This file is the single, explicit translation layer between the two.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


def _s(val: Any, default: str = "") -> str:
    """Safe string conversion."""
    if val is None:
        return default
    # Keep numbers (e.g., state_code) as string; templates often want strings.
    return str(val).strip()


def _maybe_keep_empty(val: Any) -> str:
    """Return string (possibly empty)."""
    return _s(val, default="")


# -------------------------------------------------------------------
# BANK
# -------------------------------------------------------------------

def map_bank_to_invoice_state(bank_doc: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    MongoDB: invoice_app.bank_accounts
      {
        "_id": "...",
        "bank_account_number": "...",
        "bank_name": "...",
        "bank_ifsc_code": "...",
        "branch": "...",
        "display": {...}
      }

    Invoice state: company_info.bank
      {
        "account_no": "...",
        "name": "...",
        "ifsc": "...",
        "branch": "..."
      }
    """
    if not bank_doc:
        return {}

    return {
        "account_no": _maybe_keep_empty(bank_doc.get("bank_account_number")),
        "name": _maybe_keep_empty(bank_doc.get("bank_name")),
        "ifsc": _maybe_keep_empty(bank_doc.get("bank_ifsc_code")),
        "branch": _maybe_keep_empty(bank_doc.get("branch")),
    }


# -------------------------------------------------------------------
# PARENT COMPANY
# -------------------------------------------------------------------

def map_parent_company_to_company_info(
    parent_doc: Optional[Dict[str, Any]],
    bank_doc: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    MongoDB: invoice_app.parent_companies
      {
        "_id": "...",
        "parent_company_title": "...",
        "parent_company_tagline": "...",
        "parent_company_address": "...",
        "parent_company_phone": "...",
        "parent_company_mobile": "...",
        "parent_company_email": "...",
        "parent_company_state": "...",
        "parent_company_state_code": "...",
        "parent_company_gstin": "...",
        "parent_company_pan": "...",
        "display": {...}
      }

    Invoice state: company_info
      {
        "name": "...",
        "tagline": "...",
        "address": "...",
        "phone": "...",
        "mobile": "...",
        "email": "...",
        "state": "...",
        "state_code": "...",
        "gstin": "...",
        "pan": "...",
        "bank": {...}
      }
    """
    if not parent_doc:
        return {}

    company_info: Dict[str, Any] = {
        "name": _maybe_keep_empty(parent_doc.get("parent_company_title")),
        "tagline": _maybe_keep_empty(parent_doc.get("parent_company_tagline")),
        "address": _maybe_keep_empty(parent_doc.get("parent_company_address")),
        "phone": _maybe_keep_empty(parent_doc.get("parent_company_phone")),
        "mobile": _maybe_keep_empty(parent_doc.get("parent_company_mobile")),
        "email": _maybe_keep_empty(parent_doc.get("parent_company_email")),
        "state": _maybe_keep_empty(parent_doc.get("parent_company_state")),
        "state_code": _maybe_keep_empty(parent_doc.get("parent_company_state_code")),
        "gstin": _maybe_keep_empty(parent_doc.get("parent_company_gstin")),
        "pan": _maybe_keep_empty(parent_doc.get("parent_company_pan")),
    }

    # Attach bank if provided (kept separate so you can change bank selection independently)
    bank_state = map_bank_to_invoice_state(bank_doc)
    if bank_state:
        company_info["bank"] = bank_state

    return company_info


# -------------------------------------------------------------------
# CLIENT COMPANY
# -------------------------------------------------------------------

def map_client_company_to_billing_to(
    client_doc: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    MongoDB: invoice_app.client_companies
      {
        "_id": "...",
        "client_company_name": "...",
        "client_company_address": "...",
        "client_company_gstin": "...",
        "client_company_state": "...",
        "client_company_state_code": "...",
        "display": {...}
      }

    Invoice state: billing_to
      {
        "client_name": "...",
        "address": "...",
        "gstin": "...",
        "state": "...",
        "state_code": "..."
      }

    Note:
    - PO / SPO are invoice-level (transaction-level) fields, so we do NOT map them here.
    """
    if not client_doc:
        return {}

    return {
        "client_name": _maybe_keep_empty(client_doc.get("client_company_name")),
        "address": _maybe_keep_empty(client_doc.get("client_company_address")),
        "gstin": _maybe_keep_empty(client_doc.get("client_company_gstin")),
        "state": _maybe_keep_empty(client_doc.get("client_company_state")),
        "state_code": _maybe_keep_empty(client_doc.get("client_company_state_code")),
    }

def map_client_company_to_to_party(client_doc: dict) -> dict:
    """
    Map MongoDB client company document to freight_bill.to_party format.
    Bill Invoice only needs name and address.
    
    MongoDB: invoice_app.ClientCompanies
      {
        "_id": "zuari_cement_ltd",
        "client_company_name": "ZUARI CEMENT LTD.",
        "client_company_address": "Krishna Nagar, Yerraguntla, Kadapa (A.P.) - 516311",
        ...
      }
    
    Returns (freight_bill.to_party format):
      {
        "name": "ZUARI CEMENT LTD.,",
        "address": "Krishna Nagar\nYerraguntla, Kadapa (A.P.) - 516311"
      }
    """
    if not client_doc:
        return {"name": "", "address": ""}
    
    name = client_doc.get('client_company_name', '')
    # Add comma after name for Bill Invoice format
    if name and not name.endswith(','):
        name += ','
    
    address = client_doc.get('client_company_address', '')
    # Convert comma-separated address to newline format for display
    # "Part1, Part2, Part3" -> "Part1\nPart2, Part3"
    address_parts = [p.strip() for p in address.split(',') if p.strip()]
    if len(address_parts) > 1:
        address = address_parts[0] + '\n' + ', '.join(address_parts[1:])
    
    return {
        "name": name,
        "address": address
    }


# -------------------------------------------------------------------
# OPTIONAL: convenience helpers for applying into a unified invoice state
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# TERMS AND CONDITIONS
# -------------------------------------------------------------------

def map_terms_to_invoice_state(tnc_doc: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    MongoDB: invoice_app.TermsAndConditions
      {
        "_id": "default_tnc_gst",
        "line_1": "Notification No 3/2017...",
        "line_2": "Interest @ 18%...",
        "line_3": "All disputes...",
        "line_4": "This Invoice details...",
        "display": {...}
      }

    Invoice state: terms_and_conditions (array of strings)
      {
        "terms_and_conditions": [
          "Notification No 3/2017...",
          "Interest @ 18%...",
          "All disputes...",
          "This Invoice details..."
        ]
      }
    
    Returns:
        Dict with terms_and_conditions key containing list of T&C lines
    """
    if not tnc_doc:
        return {"terms_and_conditions": []}
    
    # Extract lines 1-4, filter out empty ones
    lines = []
    for i in range(1, 5):  # line_1 through line_4
        line_key = f"line_{i}"
        line_value = _maybe_keep_empty(tnc_doc.get(line_key))
        if line_value:  # Only add non-empty lines
            lines.append(line_value)
    
    return {"terms_and_conditions": lines}


def apply_master_data_to_invoice_state(
    invoice_state: Dict[str, Any],
    *,
    parent_doc: Optional[Dict[str, Any]] = None,
    bank_doc: Optional[Dict[str, Any]] = None,
    client_doc: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Mutates and returns invoice_state by applying mapped master data.

    Use this if you want one place to apply all three selections:
      - company_info from parent_doc (+ bank_doc)
      - billing_to from client_doc

    This function does NOT persist anything.
    """
    if not isinstance(invoice_state, dict):
        invoice_state = {}

    if parent_doc is not None:
        invoice_state["company_info"] = map_parent_company_to_company_info(parent_doc, bank_doc)

    # If you select bank independently (without reselecting parent), you can still update:
    if parent_doc is None and bank_doc is not None:
        invoice_state.setdefault("company_info", {})
        invoice_state["company_info"]["bank"] = map_bank_to_invoice_state(bank_doc)

    if client_doc is not None:
        invoice_state["billing_to"] = map_client_company_to_billing_to(client_doc)

    return invoice_state
