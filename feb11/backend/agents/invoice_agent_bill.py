# invoice_agent_bill_new.py
"""
Agentic Bill Invoice Agent with LLM-based natural language operations.
Similar to invoice_agent_tax.py but for Freight Bills.
"""

from __future__ import annotations
from typing import Dict, Any, Tuple, Optional
import json
import os
from datetime import datetime

# Common modules for shared functionality
from integrations.llm_client import call_llm, HAS_OPENAI
from utils.file_reader import read_excel_or_csv, detect_sheet_override
from contexts.context_loader import load_context_module, get_context_attr
from agents.agent_utils_common import safe_num, drop_empty_rows, nest_set


#safe_num( removed - now using safe_num from agent_utils_common


def _load_context():
    """Load context from context_bill_invoice.py using context_loader"""
    ctx_module = load_context_module('contexts.context_bill_invoice')
    return {
        'agentic_instructions': get_context_attr(ctx_module, 'AGENTIC_OPERATION_INSTRUCTIONS', ''),
        'extraction_instructions': get_context_attr(ctx_module, 'EXTRACTION_INSTRUCTIONS', ''),
        'user_dataset_hints': get_context_attr(ctx_module, 'USER_DATASET_HINTS', ''),
        'excel_sheet_name': get_context_attr(ctx_module, 'EXCEL_SHEET_NAME', None),
    }


# _detect_sheet_override_llm removed - now using detect_sheet_override from file_reader


def extract_bill_data_from_file_llm(file_path: str, user_filter: str = "") -> Dict[str, Any]:
    """
    Use LLM to extract Bill Invoice data from Excel/CSV file.
    The LLM handles filtering based on user_filter (e.g., "September 2025", "rate > 200").
    Returns extracted data in JSON format.
    """
    if not HAS_OPENAI:
        print("⚠ OpenAI not available, skipping LLM extraction")
        return {"runs": []}
    
    try:
        import pandas as pd
        
        # LEVEL 1: Load default sheet configuration from context
        ctx_module = load_context_module('contexts.context_bill_invoice')
        default_sheet_config = get_context_attr(ctx_module, 'EXCEL_SHEET_NAME', None)
        
        # LEVEL 2: Check for runtime override in user notes
        runtime_sheet_override = detect_sheet_override(user_filter or "", call_llm)
        
        # Determine which sheet to use (priority: runtime > default > fallback)
        sheet_config = runtime_sheet_override if runtime_sheet_override is not None else default_sheet_config
        
        # Read file with sheet configuration
        if file_path.endswith('.xlsx') or file_path.endswith('.xls') or file_path.endswith('.xlsm'):
            # Excel file - use sheet configuration
            xl_file = pd.ExcelFile(file_path)
            
            # Show available sheets for transparency
            if len(xl_file.sheet_names) > 1:
                print(f"ℹ️  Excel file contains {len(xl_file.sheet_names)} sheets: {xl_file.sheet_names}")
            
            if sheet_config is not None:
                try:
                    # Handle both sheet name (string) and index (int)
                    if isinstance(sheet_config, int):
                        # Sheet index
                        if 0 <= sheet_config < len(xl_file.sheet_names):
                            sheet_name = xl_file.sheet_names[sheet_config]
                            df = pd.read_excel(file_path, sheet_name=sheet_name)
                            source = "runtime override" if runtime_sheet_override is not None else "default config"
                            print(f"📊 Using sheet index {sheet_config} ('{sheet_name}') from {source}")
                        else:
                            print(f"⚠ Sheet index {sheet_config} out of range, using first sheet")
                            df = pd.read_excel(file_path, sheet_name=0)
                    else:
                        # Sheet name (string)
                        if sheet_config in xl_file.sheet_names:
                            df = pd.read_excel(file_path, sheet_name=sheet_config)
                            source = "runtime override" if runtime_sheet_override is not None else "default config"
                            print(f"📊 Using sheet '{sheet_config}' from {source}")
                        else:
                            print(f"⚠ Sheet '{sheet_config}' not found, using first sheet")
                            print(f"   Available sheets: {xl_file.sheet_names}")
                            df = pd.read_excel(file_path, sheet_name=0)
                except Exception as e:
                    print(f"⚠ Error reading configured sheet: {e}, using first sheet")
                    df = pd.read_excel(file_path, sheet_name=0)
            else:
                # No config, use first sheet (default behavior)
                df = pd.read_excel(file_path, sheet_name=0)
                print(f"📊 Using first sheet (no configuration)")
        else:
            # CSV file
            df = pd.read_csv(file_path)
        
        if df.empty:
            return {"runs": []}
        
        # Convert to JSON for LLM
        data_json = df.to_json(orient='records', date_format='iso')
        
        # Load context with user hints
        ctx = _load_context()
        extraction_instructions = ctx.get('extraction_instructions', '')
        user_hints = ctx.get('user_dataset_hints', '')
        
        # Inject user hints into instructions
        prompt_with_hints = extraction_instructions.format(user_hints=user_hints or "No user hints provided.")
        
        # Build prompt with filter if present
        if user_filter:
            prompt = f"""Extract freight bill data from this dataset.

FILTER CONDITION: {user_filter}

Apply semantic filtering intelligently:
- Understand date ranges ("September 2025", "last week", "16-09-2025 to 30-09-2025")
- Handle text patterns ("trucks ending with 66", "Tamil Nadu vehicles", "contains ABC")
- Support comparisons ("rate above 200", "quantity > 30", "expensive deliveries")
- Handle complex conditions ("September deliveries where rate > 200")

Only include rows that match the filter condition. Parse dates flexibly and apply the filter intelligently.

Dataset:
{data_json}"""
            print(f"🤖 Calling LLM to extract and filter data from {len(df)} rows...")
        else:
            prompt = f"Extract freight bill data from this dataset:\n\n{data_json}"
            print(f"🤖 Calling LLM to extract data from {len(df)} rows...")
        
        response_content = call_llm(
            system_prompt=prompt_with_hints,
            user_prompt=prompt,
            response_format={"type": "json_object"},
            model="gpt-4.1-mini"
        )
        
        result = json.loads(response_content)
        print(f"✓ LLM extraction complete")
        
        # POST-PROCESSING: Remove client company fields from file uploads
        # Client company details (to_party.name, to_party.address) are managed by database loaders only
        if 'to_party' in result:
            if result['to_party'].get('name') or result['to_party'].get('address'):
                print(f"⚠️  Removing client company fields from file upload (use database loaders instead)")
                del result['to_party']
        
        # Print dataset analysis if available (transparency!)
        analysis = result.get('dataset_analysis', {})
        if analysis:
            print(f"\n📊 Dataset Analysis:")
            mappings = analysis.get('mappings_used', {})
            if mappings:
                print(f"  Column Mappings:")
                for field, column in mappings.items():
                    print(f"    • {field} ← {column}")
            
            hints_applied = analysis.get('user_hints_applied', [])
            if hints_applied:
                print(f"\n  ✓ User hints applied:")
                for hint in hints_applied:
                    print(f"    • {hint}")
            
            issues = analysis.get('issues_found', [])
            if issues:
                print(f"\n  ⚠ Issues found:")
                for issue in issues:
                    print(f"    • {issue}")
            
            confidence = analysis.get('confidence', 'unknown')
            print(f"\n  Confidence: {confidence.upper()}")
        
        # Print summary
        runs = result.get('runs', [])
        print(f"\n📋 Extracted data:")
        if result.get('summary'):
            print(f"  • Summary: {result['summary']}")
        print(f"  • Runs: {len(runs)} rows")
        # Note: to_party fields not shown as they should not be extracted from files
        if user_filter:
            print(f"  • Filter applied: {user_filter}")
        
        return result
        
    except Exception as e:
        print(f"❌ LLM extraction failed: {e}")
        return {"runs": []}


def analyze_bill_operation(user_notes: str, current_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Use LLM to analyze user command and determine operation type and strategy.
    """
    if not HAS_OPENAI:
        return {"operation_type": "STANDARD"}
    
    ctx = _load_context()
    instructions = ctx.get('agentic_instructions', '')
    
    # Summarize current state
    fb = current_state.get('freight_bill', {})
    current_runs = len(fb.get('runs', []))
    
    state_summary = f"""
Current Bill Invoice State:
- Runs: {current_runs} existing runs
- Bill No: {fb.get('series_no', 'not set')}
- Client: {fb.get('to_party', {}).get('name', 'not set')}
"""
    
    try:
        print(f"🧠 Analyzing operation: '{user_notes}'")
        
        response_content = call_llm(
            system_prompt=instructions,
            user_prompt=f"{state_summary}\n\nUser command: {user_notes}\n\nAnalyze this command and return a JSON strategy.",
            response_format={"type": "json_object"},
            model="gpt-4.1-mini"
        )
        
        strategy = json.loads(response_content)
        print(f"✓ Strategy: {json.dumps(strategy, indent=2)}")
        
        return strategy
        
    except Exception as e:
        print(f"❌ Operation analysis failed: {e}")
        return {"operation_type": "STANDARD"}


def execute_bill_strategy(
    strategy: Dict[str, Any],
    extracted_data: Dict[str, Any],
    current_state: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute the strategy determined by the LLM.
    """
    operation_type = strategy.get('operation_type') or strategy.get('operation', 'STANDARD')
    
    state = dict(current_state)
    fb = state.setdefault('freight_bill', {})
    fb.setdefault('runs', [])
    
    print(f"⚙️ Executing {operation_type} operation...")
    
    if operation_type == "ADD":
        # Additive operation - append new runs
        # LLM has already filtered the data during extraction
        new_runs = extracted_data.get('runs', [])
        
        # Append runs
        fb['runs'].extend(new_runs)
        print(f"✓ Appended {len(new_runs)} runs (total: {len(fb['runs'])})")
        
        # Update header fields if present (but NOT client company details)
        # Client company (to_party) is managed by database loaders only
        if extracted_data.get('summary'):
            fb['summary'] = extracted_data['summary']
        # Note: to_party fields are intentionally NOT updated from file uploads
    
    elif operation_type == "REPLACE":
        # Replace operation - clear and add
        new_runs = extracted_data.get('runs', [])
        fb['runs'] = new_runs
        print(f"✓ Replaced runs with {len(new_runs)} new runs")
        
        # Update header fields (but NOT client company details)
        # Client company (to_party) is managed by database loaders only
        if extracted_data.get('summary'):
            fb['summary'] = extracted_data['summary']
        # Note: to_party fields are intentionally NOT updated from file uploads
    
    elif operation_type == "CONDITIONAL_ADD":
        # NEW: Add only if condition is met
        instructions = strategy.get('instructions', {})
        condition = instructions.get('condition', 'not duplicate')
        new_runs = extracted_data.get('runs', [])
        
        # Use LLM to evaluate condition for each run
        added_count = 0
        for new_run in new_runs:
            should_add = _evaluate_condition_llm(new_run, fb['runs'], condition)
            if should_add:
                fb['runs'].append(new_run)
                added_count += 1
        
        print(f"✓ Conditionally added {added_count}/{len(new_runs)} runs (condition: {condition})")
    
    elif operation_type == "MERGE":
        # NEW: Merge by key field
        instructions = strategy.get('instructions', {})
        merge_key = instructions.get('merge_key', 'truck_no')
        new_runs = extracted_data.get('runs', [])
        
        # Create lookup by merge key
        existing_by_key = {run.get(merge_key): i for i, run in enumerate(fb['runs']) if run.get(merge_key)}
        
        merged = 0
        added = 0
        # Merge or add
        for new_run in new_runs:
            key_value = new_run.get(merge_key)
            if key_value and key_value in existing_by_key:
                # Update existing run
                idx = existing_by_key[key_value]
                fb['runs'][idx].update(new_run)
                merged += 1
            else:
                # Add new run
                fb['runs'].append(new_run)
                added += 1
        
        print(f"✓ Merged by {merge_key}: {merged} updated, {added} added")
    
    elif operation_type == "UPSERT":
        # NEW: Update if exists, insert if not
        instructions = strategy.get('instructions', {})
        upsert_key = instructions.get('upsert_key', 'truck_no')
        new_runs = extracted_data.get('runs', [])
        
        existing_keys = {run.get(upsert_key): i for i, run in enumerate(fb['runs']) if run.get(upsert_key)}
        updated = 0
        inserted = 0
        
        for new_run in new_runs:
            key_value = new_run.get(upsert_key)
            if key_value and key_value in existing_keys:
                # Update existing
                idx = existing_keys[key_value]
                fb['runs'][idx] = new_run
                updated += 1
            else:
                # Insert new
                fb['runs'].append(new_run)
                inserted += 1
        
        print(f"✓ Upserted: {updated} updated, {inserted} inserted")
    
    else:
        # Unknown operation type - default to ADD
        print(f"⚠ Unknown operation type: {operation_type}, defaulting to ADD")
        new_runs = extracted_data.get('runs', [])
        fb['runs'].extend(new_runs)
        print(f"✓ Appended {len(new_runs)} runs (total: {len(fb['runs'])})")
    
    return state


def _evaluate_condition_llm(new_item: Dict, existing_items: list, condition: str) -> bool:
    """
    Use LLM to evaluate if a condition is met for adding an item.
    This allows for complex, natural language conditions.
    """
    if not condition or not HAS_OPENAI:
        return True
    
    try:
        prompt = f"""Evaluate if this new item should be added based on the condition.
        
CONDITION: {condition}
        
NEW ITEM: {json.dumps(new_item)}
        
EXISTING ITEMS: {json.dumps(existing_items[:10])}  # Show first 10 for context
        
Return JSON:
{{
  "should_add": true or false,
  "reasoning": "brief explanation"
}}
"""
        
        response_content = call_llm(
            system_prompt="You evaluate conditions for adding items to an invoice.",
            user_prompt=prompt,
            response_format={"type": "json_object"},
            model="gpt-4.1-mini"
        )
        
        result = json.loads(response_content)
        should_add = result.get('should_add', True)
        reasoning = result.get('reasoning', '')
        
        if not should_add:
            print(f"  ⊘ Skipped item (truck: {new_item.get('truck_no', 'N/A')}): {reasoning}")
        
        return should_add
        
    except Exception as e:
        print(f"⚠ Condition evaluation failed: {e}, defaulting to True")
        return True


def create_bill_patch_from_notes(user_notes: str, current_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a patch for Bill Invoice from user notes (for row-level operations).
    Similar to create_tax_patch_from_notes but for freight_bill.runs.
    """
    if not HAS_OPENAI:
        return {}
    
    try:
        # Load context for advanced operations
        ctx = _load_context()
        agentic_instructions = ctx.get('agentic_instructions', '')
        
        # Get current runs data for conditional operations
        runs = current_state.get('freight_bill', {}).get('runs', [])
        
        # Build field mapping for LLM
        field_mappings = [
            "freight_bill.series_no - Bill number",
            "freight_bill.bill_date - Bill date",
            "freight_bill.po_no - Purchase order number",
            "freight_bill.pan_no - PAN number",
            "freight_bill.summary - Summary description",
            "freight_bill.to_party.name - Client name",
            "freight_bill.to_party.address - Client address",
            "freight_bill.runs[N].date - Delivery date for row N",
            "freight_bill.runs[N].truck_no - Truck number for row N",
            "freight_bill.runs[N].lr_no - LR number for row N",
            "freight_bill.runs[N].dc_qty_mt - DC quantity for row N",
            "freight_bill.runs[N].gr_qty_mt - GR quantity for row N",
            "freight_bill.runs[N].rate - Rate for row N",
            "freight_bill.runs[N].line_total - Total for row N",
        ]
        
        # Include current runs data for conditional/bulk operations
        runs_summary = []
        for i, run in enumerate(runs):  # Show ALL runs for conditional operations
            runs_summary.append(f"Row {i+1} (index {i}): date={run.get('date')}, truck_no={run.get('truck_no')}, lr_no={run.get('lr_no')}, rate={run.get('rate')}")
        
        prompt = f"""You are an intelligent invoice assistant. Analyze the current invoice data and user command, then generate the appropriate patch.

USER COMMAND: "{user_notes}"

CURRENT INVOICE DATA:
Total runs: {len(runs)}
{chr(10).join(runs_summary)}

AVAILABLE FIELDS:
{chr(10).join(field_mappings)}

CONTEXT INSTRUCTIONS:
{agentic_instructions}

YOUR TASK:
1. **ANALYZE** the user command and understand what needs to be done
2. **EXAMINE** the current invoice data to identify which rows match the criteria
3. **GENERATE** a JSON patch with the exact indices of rows to modify/delete

GENERATE A JSON PATCH:

Examples:
- "change rate in row 5 to 250" → {{"freight_bill.runs[4].rate": 250}}
- "delete row 3" → {{"freight_bill.runs[2]": "__DELETE__"}}
- "set summary to Transport of Gypsum" → {{"freight_bill.summary": "Transport of Gypsum"}}
- "Set the LR No from 1 to 10 for rows 1 to 10" → {{"freight_bill.runs[0].lr_no": 1, "freight_bill.runs[1].lr_no": 2, ..., "freight_bill.runs[9].lr_no": 10}}
- "delete all rows where Truck no ends with 66" → Check each row's truck_no field. If truck_no.endsWith('66') is true, add that index to deletion patch.
  Example: If only row 22 (index 21) has truck_no='AP39VF5566' (ends with '66'), then: {{"freight_bill.runs[21]": "__DELETE__"}}

CRITICAL RULES:
⚠️ **NEVER CREATE NEW ROWS** - Only generate patches for existing rows (indices 0 to {len(runs)-1})
⚠️ **VERIFY ROW EXISTS** - Before generating a patch for index N, confirm N < {len(runs)}
- For sequential updates ("from X to Y"), assign sequential values: row 1 gets X, row 2 gets X+1, etc.
- For conditional operations, evaluate the condition against CURRENT STATE data and generate individual patches for ONLY the rows that match
- For "ends with" conditions, check if the string ENDS with the exact suffix (e.g., 'AP39VF5566' ends with '66', but 'AP39WD5886' does NOT end with '66')
- Use array indices (0-based): row 1 = index 0, row 2 = index 1, etc.
- ONLY include rows that EXACTLY match the condition
- When filling empty fields, ONLY update rows where the field is currently empty, do NOT create new rows

Return ONLY the JSON patch, no explanation."""
        
        response_content = call_llm(
            system_prompt="You are a JSON patch generator for freight bill invoices.",
            user_prompt=prompt,
            response_format={"type": "json_object"},
            model="gpt-4.1-mini"
        )
        
        patch = json.loads(response_content)
        print(f"✓ LLM generated patch: {patch}")
        
        return patch
        
    except Exception as e:
        print(f"❌ Patch generation failed: {e}")
        return {}


def _apply_patch_agentic(state: Dict[str, Any], patch: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply patch using deterministic code for reliability.
    Patch generation is agentic (LLM), but application is deterministic.
    """
    from core.patch_applicator import apply_patch_deterministic
    
    if not patch:
        return state
    
    try:
        return apply_patch_deterministic(state, patch)
    except Exception as e:
        print(f"❌ Patch application failed: {e}")
        import traceback
        traceback.print_exc()
        return state


def _should_extract_from_dataset(user_command: str) -> bool:
    """
    Use LLM to determine if the user wants to extract data from dataset or just update existing invoice.
    Pure agentic reasoning - no hard-coded keywords.
    """
    if not HAS_OPENAI:
        return False
    
    try:
        prompt = f"""Analyze this user command for a Bill Invoice system:

COMMAND: "{user_command}"

Determine the user's intent:

A) **EXTRACT FROM DATASET** - User wants to add NEW rows by extracting data from an uploaded Excel/CSV file
   Examples:
   - "add all rows from dataset"
   - "take all rows from September 2025"
   - "add details from the uploaded file"
   - "import data from Excel"

B) **UPDATE EXISTING INVOICE** - User wants to modify/update fields in EXISTING rows (already in the invoice)
   Examples:
   - "fill all empty LR No with values 40, 42, 44"
   - "update rate in row 5 to 250"
   - "change truck number to XYZ"
   - "delete rows from S.No 13 to 42"
   - "set LR No to 100 for all rows"

Return JSON:
{{
  "intent": "EXTRACT_FROM_DATASET" or "UPDATE_EXISTING_INVOICE",
  "reasoning": "Brief explanation"
}}
"""
        
        response_content = call_llm(
            system_prompt="You are an intent classifier for invoice operations.",
            user_prompt=prompt,
            response_format={"type": "json_object"},
            model="gpt-4.1-mini"
        )
        
        result = json.loads(response_content)
        intent = result.get('intent', 'UPDATE_EXISTING_INVOICE')
        reasoning = result.get('reasoning', '')
        
        print(f"🧠 Intent Analysis: {intent}")
        if reasoning:
            print(f"   Reasoning: {reasoning}")
        
        return intent == "EXTRACT_FROM_DATASET"
        
    except Exception as e:
        print(f"⚠ Intent analysis failed: {e}")
        return False  # Default to update mode if analysis fails


def agent_update_bill_from_file(
    file_path: Optional[str],
    current_state: Dict[str, Any],
    user_notes: str = ""
) -> Tuple[Dict[str, Any], str]:
    """
    Main entry point for Bill Invoice agentic agent.
    
    Args:
        file_path: Path to Excel/CSV file (optional)
        current_state: Current invoice state
        user_notes: User command/notes
    
    Returns:
        (updated_state, summary_message)
    """
    if not HAS_OPENAI:
        return current_state, "⚠ OpenAI not available, agentic operations disabled"
    
    # Use LLM to determine if this is a dataset extraction operation
    # Let the LLM understand the user's intent instead of hard-coding keywords
    is_agentic = False
    if file_path and user_notes:
        is_agentic = _should_extract_from_dataset(user_notes)
    
    if is_agentic:
        print("🤖 AGENTIC OPERATION DETECTED")
        
        # Step 1: Analyze operation to get filter
        strategy = analyze_bill_operation(user_notes, current_state)
        
        # Step 2: Extract data from file with filter
        # LLM will handle filtering intelligently
        user_filter = user_notes  # Pass the entire command to LLM for intelligent parsing
        extracted_data = extract_bill_data_from_file_llm(file_path, user_filter=user_filter)
        
        # Step 3: Execute strategy
        state = execute_bill_strategy(strategy, extracted_data, current_state)
        
        summary = f"✓ Agentic operation complete: {strategy.get('operation_type') or strategy.get('operation', 'UNKNOWN')}"
        return state, summary
    
    else:
        # Standard operation (row-level edits, header changes)
        print("📋 STANDARD OPERATION")
        
        # DO NOT extract from file in standard mode
        # File extraction only happens in agentic mode when user explicitly requests it
        state = dict(current_state)
        
        # Apply notes patch if present (AGENTIC)
        if user_notes:
            patch = create_bill_patch_from_notes(user_notes, state)
            if patch:
                state = _apply_patch_agentic(state, patch)
        
        summary = f"✓ Standard operation complete"
        return state, summary


