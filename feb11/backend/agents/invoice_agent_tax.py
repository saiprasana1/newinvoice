
from __future__ import annotations
from typing import Dict, Any, Tuple, Optional, List
import re
import os
import json
import pandas as pd
from integrations.llm_client import call_llm, HAS_OPENAI
from utils.file_reader import read_excel_or_csv, detect_sheet_override
from contexts.context_loader import load_context_module, get_context_attr
from agents.agent_utils_common import safe_num, drop_empty_rows, nest_set, path_to_wildcard


try:
    import core.invoice_schema as _schema_tax
    TAX_EDITABLE_FIELDS = list(getattr(_schema_tax, "EDITABLE_FIELDS"))
except Exception:
    TAX_EDITABLE_FIELDS = [
        "invoice_number", "invoice_date", "reverse_charge",
        "supply_mode", "supply_period", "place_of_supply",
        "billing_to.client_name", "billing_to.address", "billing_to.gstin", "billing_to.spo_no", "billing_to.purchase_order_no",
        "billing_to.state", "billing_to.state_code",
        "items.*.description", "items.*.hsn_code", "items.*.uom",
        "items.*.quantity", "items.*.unit_price", "items.*.line_total",
        "cgst_rate", "sgst_rate", "igst_rate",
        "discount", "shipping_handling", "subtotal", "total",
    ]


def discover_editable_fields_tax() -> Dict[str, Any]:
    """Build the authoritative FIELD_GUIDE for the Tax invoice."""
    try:
        import tax_invoice_template as _tit
        import inspect
        src = inspect.getsource(_tit)
        fields = set()
        for m in re.finditer(r'data-field\s*=\s*"([^"]+)"', src):
            fields.add(path_to_wildcard(m.group(1)))
        template_fields = sorted(fields)
    except Exception:
        template_fields = []
    
    schema_fields = [path_to_wildcard(p) for p in (TAX_EDITABLE_FIELDS or [])]
    merged = sorted(set(template_fields).union(schema_fields))
    return {"editable_fields": merged}


def _read_any_table(file_path: str, user_notes: str = "") -> Tuple[pd.DataFrame, str]:
    """
    Read XLSX or CSV with two-level sheet configuration:
    1. Runtime override (from user notes)
    2. Default config (from context file)
    3. Auto-detect fallback
    """
    ctx_module = load_context_module('contexts.context_tax_invoice')
    default_sheet_config = get_context_attr(ctx_module, 'EXCEL_SHEET_NAME', None)
    
    runtime_sheet_override = None
    if user_notes:
        notes_lower = user_notes.lower()
        match = re.search(r'sheet\s+(\d+)', notes_lower)
        if match:
            runtime_sheet_override = int(match.group(1))
        elif 'first sheet' in notes_lower:
            runtime_sheet_override = 0
        elif 'second sheet' in notes_lower:
            runtime_sheet_override = 1
    
    sheet_config = runtime_sheet_override if runtime_sheet_override is not None else default_sheet_config
    
    ext = os.path.splitext(file_path)[1].lower()
    if ext in (".xlsx", ".xlsm", ".xls"):
        xl = pd.ExcelFile(file_path)
        
        if len(xl.sheet_names) > 1:
            print(f"ℹ️  Excel file contains {len(xl.sheet_names)} sheets: {xl.sheet_names}")
        
        if sheet_config is not None:
            try:
                sheet_name = xl.sheet_names[sheet_config]
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                print(f"✓ Using sheet: {sheet_name} (index {sheet_config})")
                return (df, sheet_name)
            except (IndexError, Exception) as e:
                print(f"⚠ Could not read sheet {sheet_config}: {e}")
        
        df = pd.read_excel(file_path, sheet_name=0)
        return (df, xl.sheet_names[0])
    
    elif ext in (".csv", ".txt"):
        df = pd.read_csv(file_path)
        return (df, "CSV")
    
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def profile_tabular_file(file_path: str, user_notes: str = "") -> Dict[str, Any]:
    """Profile a tabular file and return structured info."""
    df, sheet_name = _read_any_table(file_path, user_notes)
    
    df = drop_empty_rows(df)
    
    columns = df.columns.tolist()
    rows = df.to_dict('records')
    
    sample_rows = rows[:5] if len(rows) > 5 else rows
    
    def convert_timestamps(obj):
        if isinstance(obj, dict):
            return {k: convert_timestamps(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_timestamps(item) for item in obj]
        elif hasattr(obj, 'isoformat'):
            return obj.isoformat()
        else:
            return obj
    
    sample_rows_clean = convert_timestamps(sample_rows)
    
    dataset_info = {
        "columns": columns,
        "sample_rows": sample_rows_clean,
        "total_rows": len(rows),
    }
    
    return dataset_info


def create_tax_patch_from_summary_llm(
    file_summary: Dict[str, Any],
    field_guide: Dict[str, Any],
    agent_context: Dict[str, Any]
) -> Dict[str, Any]:
    """Use LLM to extract tax invoice data from file summary."""
    
    try:
        from contexts.context_tax_invoice import TAX_EXTRACTION_INSTRUCTIONS
        extraction_instructions = TAX_EXTRACTION_INSTRUCTIONS
    except Exception:
        extraction_instructions = "Extract all invoice data from the dataset."
    
    columns = file_summary.get("columns", [])
    rows = file_summary.get("sample_rows", [])
    
    sample_rows = rows[:5] if len(rows) > 5 else rows
    
    def convert_timestamps(obj):
        if isinstance(obj, dict):
            return {k: convert_timestamps(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_timestamps(item) for item in obj]
        elif hasattr(obj, 'isoformat'):
            return obj.isoformat()
        else:
            return obj
    
    sample_rows_clean = convert_timestamps(sample_rows)
    
    dataset_info = {
        "columns": columns,
        "sample_rows": sample_rows_clean,
        "total_rows": file_summary.get("total_rows", 0),
    }
    
    defaults = agent_context.get("defaults", {})
    
    system_prompt = f"""# BUSINESS INSTRUCTIONS (from user configuration):
{extraction_instructions}

# TECHNICAL REQUIREMENTS:

AVAILABLE FIELDS (use exact paths in your output):
{json.dumps(field_guide.get("editable_fields", []), indent=2)}

DEFAULT VALUES (use these if not found in dataset):
{json.dumps(defaults, indent=2)}

OUTPUT FORMAT (strict JSON):
{{
  "billing_to": {{  // OPTIONAL: Only include spo_no/purchase_order_no if found. Do NOT include client_name, gstin, or address.
    "spo_no": "..."  // Extract from PO# column if present
  }},
  "supply_period": "...",  // Extract from Period column
  "items": [
    {{
      "description": "GTA Service for Transport of <Material>",
      "quantity": 123.45,
      "unit_price": 710.0,
      "line_total": 87330.0,
      "uom": "MT"
    }}
  ],
  "cgst_rate": 6.0,
  "sgst_rate": 6.0,
  "igst_rate": 5.0
}}

CRITICAL RULES:
1. DO NOT extract client company details (billing_to.client_name, billing_to.gstin, billing_to.address) - these are managed by database loaders
2. ONLY extract billing_to.spo_no or billing_to.purchase_order_no if PO# column exists
3. ALWAYS extract supply_period from the Period column if it exists
4. Use exact field paths from the available fields list above
5. Extract ALL data rows (skip only Total/summary rows)
6. Return valid JSON only (no explanations)
"""

    user_prompt = f"""Dataset to analyze:
{json.dumps(dataset_info, indent=2, ensure_ascii=False)}

Extract all tax invoice data from this dataset. 

MANDATORY FIELDS TO EXTRACT:
1. supply_period - Extract from the Period column
2. billing_to.spo_no - Extract from the PO# column if present (optional)
3. All line items from the data rows (skip any Total/summary rows)

IMPORTANT: DO NOT extract client company details:
- Do NOT extract billing_to.client_name (even if Bill To Plant column exists)
- Do NOT extract billing_to.gstin (even if GSTN column exists)
- Do NOT extract billing_to.address
- These fields are managed by database loaders only
"""

    print(f"\n🤖 Calling LLM to extract data from {len(rows)} rows...")
    
    result = call_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_format={"type": "json_object"},
        model="gpt-4.1-mini"
    )
    
    try:
        patch = json.loads(result)
        print(f"✓ Extracted patch with {len(patch.get('items', []))} items")
        return patch
    except json.JSONDecodeError as e:
        print(f"⚠ Failed to parse LLM response: {e}")
        return {}


def create_tax_patch_from_notes(notes: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse natural language commands into a strict TAX patch using LLM.
    """
    patch: Dict[str, Any] = {}
    if not notes or not notes.strip():
        return patch

    try:
        try:
            from contexts.context_tax_invoice import TAX_FIELD_DESCRIPTIONS, TAX_COMMAND_PARSER_INSTRUCTIONS
            field_descriptions = TAX_FIELD_DESCRIPTIONS
            parser_instructions = TAX_COMMAND_PARSER_INSTRUCTIONS
            print(f"✓ Loaded context from context_tax_invoice.py")
        except Exception as e:
            print(f"⚠ Warning: Could not load context from context_tax_invoice.py: {e}")
            field_descriptions = {
                "billing_to.client_name": "Client name, customer name, company name",
                "invoice_date": "Invoice date",
            }
            parser_instructions = "Parse natural language commands and return JSON with field paths and values."

        system_prompt = f"""You are a JSON parser for tax invoice commands.

AVAILABLE FIELDS:
{json.dumps(field_descriptions, indent=2)}

INSTRUCTIONS:
{parser_instructions}

Return ONLY valid JSON with field paths as keys and new values. Example:
{{"invoice_number": "INV-001", "cgst_rate": 9.0}}
"""

        user_prompt = f"Parse this command and return JSON: {notes}"

        result = call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_format={"type": "json_object"},
            model="gpt-4.1-mini"
        )

        patch = json.loads(result)
        print(f"✓ Parsed command into patch: {patch}")
        return patch

    except Exception as e:
        print(f"⚠ Failed to parse command: {e}")
        return {}


def _apply_row_operations(patch: Dict[str, Any], current_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply row-level operations from patch to current state items.
    """
    result = {k: v for k, v in patch.items() if k != "items"}
    
    current_items = current_state.get("items", [])
    new_items = [dict(item) for item in current_items]
    
    row_ops = patch.get("items", {})
    if not isinstance(row_ops, dict):
        result["items"] = new_items
        return result
    
    rows_to_update = row_ops.get("update", {})
    rows_to_delete = row_ops.get("delete", [])
    
    for row_index_str, operations in rows_to_update.items():
        try:
            row_index = int(row_index_str)
            if row_index < len(new_items):
                for field_name, value in operations.items():
                    new_items[row_index][field_name] = value
            else:
                print(f"⚠ Warning: Row index {row_index} out of range (only {len(new_items)} rows)")
        except (ValueError, TypeError):
            pass
    
    for row_index in sorted(rows_to_delete, reverse=True):
        if row_index < len(new_items):
            del new_items[row_index]
            print(f"✓ Deleted row {row_index}")
    
    result = dict(result)
    if row_ops:
        result['items'] = new_items
    
    return result


def agent_update_tax_from_file(
    file_path: Optional[str],
    current_state: Dict[str, Any],
    user_notes: str = ""
) -> Tuple[Dict[str, Any], str]:
    """
    Main entry point for Tax Invoice agent.
    Handles both file extraction and user commands.
    """
    try:
        ctx = {}
        try:
            from contexts.context_tax_invoice import TAX_AGENT_CONTEXT
            ctx = TAX_AGENT_CONTEXT or {}
        except Exception:
            pass
        
        should_extract_from_file = False
        if file_path and os.path.exists(file_path) and user_notes:
            try:
                print(f"\n🤖 Analyzing user intent...")
                
                intent_prompt = f"""Analyze the user's command and determine their intent.

User's command: "{user_notes}"

Context: A file has been uploaded along with this command.

Determine if the user wants to:
A) EXTRACT/ADD data from the uploaded file into the invoice (e.g., "add all details from dataset", "extract data from file", "import rows", "load invoice data", "get all details from file")
B) EDIT existing invoice fields without extracting from the file (e.g., "set client name to X", "change rate to 9", "update invoice date", "delete row 2")

Return ONLY a JSON object with this exact format:
{{
  "intent": "extract" or "edit",
  "reasoning": "brief explanation of why"
}}

Rules:
- If the command asks to add/extract/import/load data FROM the file/dataset -> intent is "extract"
- If the command only asks to modify/update/change/set specific fields -> intent is "edit"
- When in doubt, prefer "edit" to avoid unwanted data extraction
"""
                
                intent_result_str = call_llm(
                    system_prompt="You are an intent classifier for invoice automation. Analyze user commands and determine if they want to extract data from a file or just edit existing fields. Always return valid JSON.",
                    user_prompt=intent_prompt,
                    response_format={"type": "json_object"},
                    model="gpt-4.1-mini"
                )
                
                intent_result = json.loads(intent_result_str)
                intent = intent_result.get('intent', 'edit')
                reasoning = intent_result.get('reasoning', '')
                
                print(f"✓ Intent detected: {intent.upper()}")
                print(f"  Reasoning: {reasoning}")
                
                should_extract_from_file = (intent == 'extract')
                
            except Exception as e:
                print(f"⚠ Intent detection failed: {e}")
                print(f"  Defaulting to 'edit' mode (no extraction)")
                should_extract_from_file = False
        
        if should_extract_from_file:
            print(f"\n📜 Processing file: {file_path}")
            
            field_guide = discover_editable_fields_tax()
            file_summary = profile_tabular_file(file_path, user_notes)
            
            patch = create_tax_patch_from_summary_llm(file_summary, field_guide, ctx)
            
            if patch:
                for key, value in patch.items():
                    if key == "items":
                        current_items = current_state.get("items", [])
                        new_items = value if isinstance(value, list) else []
                        current_state["items"] = current_items + new_items
                        print(f"✓ Added {len(new_items)} items (total: {len(current_state['items'])})")
                    elif key == "billing_to":
                        if "billing_to" not in current_state:
                            current_state["billing_to"] = {}
                        for sub_key, sub_value in value.items():
                            current_state["billing_to"][sub_key] = sub_value
                    else:
                        current_state[key] = value
                
                msg = f"✓ Added {len(patch.get('items', []))} items from dataset"
            else:
                msg = "⚠ No data extracted from file"
        elif file_path and os.path.exists(file_path) and not should_extract_from_file:
            print(f"\n📎 File attached but not extracting (user intent: edit fields only)")
            msg = ""
        
        if user_notes and user_notes.strip():
            print(f"\n📝 Processing command: {user_notes}")
            notes_patch = create_tax_patch_from_notes(user_notes, ctx)
            
            if notes_patch:
                processed_patch = _apply_row_operations(notes_patch, current_state)
                
                user_notes_lower = user_notes.lower()
                explicit_tax_rate_change = any(keyword in user_notes_lower for keyword in [
                    'cgst', 'sgst', 'igst', 'tax rate', 'gst rate', 'rate'
                ])
                
                for key, value in processed_patch.items():
                    if key == "items":
                        current_state["items"] = value
                    elif key == "billing_to":
                        if "billing_to" not in current_state:
                            current_state["billing_to"] = {}
                        for sub_key, sub_value in value.items():
                            current_state["billing_to"][sub_key] = sub_value
                    elif key in ["cgst_rate", "sgst_rate", "igst_rate"]:
                        if explicit_tax_rate_change:
                            current_state[key] = value
                    else:
                        current_state[key] = value
                
                msg = f"✓ Applied command: {user_notes}"
            else:
                msg = "⚠ Could not parse command"
        
        return (current_state, msg)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return (current_state, f"❌ Error: {str(e)}")
