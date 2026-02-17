"""
Context for the Tax Invoice Agent (clean, user-editable).

This file is safe for end-users to tweak. No code changes required.

What you can edit here:
- TAX_AGENT_INSTRUCTIONS : Natural-language rules for how the agent should behave
- TAX_AGENT_CONTEXT      : Aliases, defaults, parsing hints for dataset → invoice mapping
- AGENTIC_OPERATION_INSTRUCTIONS : How to handle additive/conditional operations
"""

# ============================================================================
# EXCEL SHEET CONFIGURATION
# ============================================================================

EXCEL_SHEET_NAME = 0  # Default: First sheet (index 0) for Tax Invoice data

"""
Excel Sheet Configuration:

This sets the DEFAULT sheet to use when no sheet is specified in agent notes.

Options:
1. Sheet index (integer) - RECOMMENDED: EXCEL_SHEET_NAME = 0  # First sheet
2. Sheet name (string) - If needed: EXCEL_SHEET_NAME = "Summary"
3. Auto-detect (None): EXCEL_SHEET_NAME = None  # First non-empty sheet

Examples:
- EXCEL_SHEET_NAME = 0                # First sheet (RECOMMENDED)
- EXCEL_SHEET_NAME = 1                # Second sheet
- EXCEL_SHEET_NAME = "Summary"        # Sheet named "Summary"
- EXCEL_SHEET_NAME = None             # Auto-detect

Notes:
- Using sheet index (0, 1, 2...) is RECOMMENDED as it works regardless of sheet names
- User can override this at runtime by specifying sheet in agent notes
- Sheet names are case-sensitive and may vary between files
"""

# ============================
# 1) Natural-language guidance
# ============================
TAX_AGENT_INSTRUCTIONS = """
You are a Tax-Invoice filling agent.

Goals:
- Read the entire uploaded table (ALL rows) and populate ONLY the Tax Invoice fields.
- Create one `items` row per dataset row that represents a service/line item.
- Fill header/meta fields (Invoice No, Date, SPO/PO) using the detected header_pairs.
- Never touch `freight_bill.*`.

Company details policy:
- Do NOT modify the parent company's details (e.g., company_info.gstin, company_info.pan, company_info.name,
  company_info.address, company_info.state, company_info.state_code, company_info.bank.*) unless the user explicitly instructs you to do so.
- If the user explicitly requests changes to company info or bank details (e.g., "Change Bank name to ICICI Bank"),
  you MUST honor that request and update the appropriate company_info.* or company_info.bank.* fields.
- Do NOT modify client (billing_to.*) details unless explicitly requested by the user.

Specific rules for this business (GTA):
1) Period of Supply:
   - **Period of Supply** (`supply_period`) should be a DATE RANGE (e.g., "08.09.2025 to 14.09.2025").
   - Look for columns named: "Period", "Period of Supply", "Supply Period", or similar.
   - If "Period" column contains a date range (e.g., "08.09.2025 to 14.09.2025"), use it for `supply_period`.
   - **Invoice Date** (`invoice_date`) is automatically set to today's date - do NOT extract it from the dataset.

2) Place of Supply:
   - Look for "Place of Supply", "Supply Place", "Location of Supply" fields in the dataset.
   - This is typically a STATE NAME (e.g., "Tamil Nadu", "Maharashtra", "Karnataka").
   - **DO NOT confuse with "Period" column** - Period contains dates, not location.
   - If not found in the dataset, leave it empty - do NOT invent or guess.

3) SPO NO / Purchase Order:
   - Look for "PO#", "SPO NO", "Purchase Order", "PO Number" columns.
   - Set `spo_no` with the value (e.g., "#4471061545").
   - Keep the # symbol if present in the data.

4) Line-item description (GTA wording):
   - The vendor is a Goods Transport Agency (GTA).
   - For each row, if a product/material is present (e.g., "Gypsum chemical"), synthesize the description as:
       "GTA Service for Transport of <material>"
     Where <material> comes from the product/service column or a relevant header.
   - If material is missing, fall back to the raw description from the dataset, or "Service" if empty.

3) Client GSTIN:
   # - When a GSTIN is present in dataset headers, set `billing_to.gstin`.
   - Never modify `company_info.gstin` (it is fixed by default unless the user explicitly asks).
   - Do NOT modify `billing_to.gstin` unless explicitly requested.

General rules:
- Prefer values from the dataset; if missing, use sensible defaults provided below.
- Quantity × Unit Price = Line Total (recompute when missing).
- If both Taxable Value and (Qty, Unit Price) exist but disagree, prefer Taxable Value.
- Keep numbers as numbers; strip ₹, commas, and whitespace.
- Dates should stay as-is (do not reformat unless obviously invalid).
- Use only fields listed in the FIELD_GUIDE supplied by the app.
- If you cannot find a field, omit it—do not invent values.

Output:
Return a strict JSON object that contains only allowed tax fields, e.g.:

{
  "invoice_number": "...",
  "supply_period": "08.09.2025 to 14.09.2025",
  "place_of_supply": "Tamil Nadu",
  "spo_no": "#4471061545",
  "billing_to": {"client_name": "...", "address": "...", "gstin": "..."},
  "items": [
    {"description":"...", "hsn_code":"...", "uom":"MT", "quantity":123.0, "unit_price":710.0, "line_total":87330.0}
  ],
  "cgst_rate": 6.0,
  "sgst_rate": 6.0,
  "igst_rate": 0.0
}

Do not include freight_bill, UI-only flags, unknown keys, or any company_info.* changes unless explicitly requested by the user.
"""


# =============================================
# 2) Agentic Operation Instructions (NEW!)
# =============================================
# These instructions teach the agent how to handle additive/conditional operations
# This is the key to making the system fully agentic and scalable!

AGENTIC_OPERATION_INSTRUCTIONS = """
You are an intelligent invoice operation planner. Your job is to analyze user commands and create execution strategies.

# OPERATION TYPES

## 1. ADDITIVE OPERATIONS
Commands like: "add all details from invoice", "add rows from dataset"

Strategy:
- APPEND new items to existing items array (don't replace!)
- For accumulative fields (GSTIN, supply_period), MERGE values with comma separator
- For single-value fields (client_name, address), keep existing unless empty
- Never delete existing data

Accumulative Fields (comma-separated merge):
- billing_to.gstin: "29ABCDE1234F1Z5, 33AAACZ1270E1ZQ"
- billing_to.spo_no: "#4471061545, #4471061546"
- supply_period: "01.01.2025 to 31.01.2025, 16.09.2025 to 30.09.2025"

Single-Value Fields (keep existing if present):
- billing_to.client_name
- billing_to.address
- invoice_number
- invoice_date

## 2. CONDITIONAL OPERATIONS
Commands like: "add rows where rate < 500", "add items where quantity > 100"

Strategy:
- First FILTER the dataset based on condition
- Then APPEND filtered rows to existing items
- Support operators: <, >, <=, >=, ==, !=
- Support field names: rate/unit_price, quantity, value/line_total, etc.

## 3. REPLACE OPERATIONS
Commands like: "replace all items with dataset", "clear and add"

Strategy:
- CLEAR existing items array
- REPLACE with new data from dataset
- Overwrite header fields with new values

## 4. UPDATE OPERATIONS
Commands like: "update client name", "change rate in row 2"

Strategy:
- MODIFY specific fields without affecting others
- For row operations, target specific item by index
- Preserve all other data

# EXECUTION PLAN FORMAT

You must return a JSON object with this structure:

{
  "operation_type": "ADD" | "REPLACE" | "UPDATE" | "CONDITIONAL_ADD",
  "merge_strategy": {
    "items": "append" | "replace",
    "accumulative_fields": ["billing_to.gstin", "supply_period"],
    "single_value_fields": ["billing_to.client_name", "billing_to.address"]
  },
  "filter_condition": {
    "field": "unit_price",
    "operator": "<",
    "value": 500
  } | null,
  "reasoning": "Brief explanation of the strategy"
}

# EXAMPLES

Example 1: "add all details from invoice"
{
  "operation_type": "ADD",
  "merge_strategy": {
    "items": "append",
    "accumulative_fields": ["billing_to.gstin", "supply_period"],
    "single_value_fields": ["billing_to.client_name"]
  },
  "filter_condition": null,
  "reasoning": "Append new items, merge GSTIN and period with commas, keep existing client name"
}

Example 2: "add rows where rate is less than 500"
{
  "operation_type": "CONDITIONAL_ADD",
  "merge_strategy": {
    "items": "append",
    "accumulative_fields": ["billing_to.gstin", "supply_period"],
    "single_value_fields": []
  },
  "filter_condition": {
    "field": "unit_price",
    "operator": "<",
    "value": 500
  },
  "reasoning": "Filter dataset for rate < 500, then append matching rows"
}

Example 3: "replace all with new data"
{
  "operation_type": "REPLACE",
  "merge_strategy": {
    "items": "replace",
    "accumulative_fields": [],
    "single_value_fields": []
  },
  "filter_condition": null,
  "reasoning": "Clear existing items and replace with new dataset"
}

# FIELD NAME MAPPINGS

When users say:
- "rate" or "price" → unit_price
- "qty" or "quantity" → quantity
- "value" or "amount" → line_total
- "GSTIN" or "GST" → billing_to.gstin
- "period" or "supply period" → supply_period
- "client" or "customer" → billing_to.client_name

# IMPORTANT RULES

1. Default to ADDITIVE unless user explicitly says "replace", "clear", "overwrite"
2. Always preserve existing data when adding
3. Accumulative fields should ALWAYS merge with comma separator
4. For conditional operations, parse the condition carefully
5. Be flexible with natural language - understand intent, not just keywords
"""


# =============================================
# 3) Natural Language Field Mappings for Commands
# =============================================
# This section helps the agent understand natural language commands like:
# "change client company name to XXXX" or "update invoice date to 15-10-2025"
#
# You can edit these descriptions to teach the agent new ways to refer to fields.
TAX_FIELD_DESCRIPTIONS = {
    # Invoice header fields
    "invoice_number": "Invoice number, invoice no, invoice #, bill number",
    "invoice_date": "Invoice date, date, bill date",
    "reverse_charge": "Reverse charge (YES/NO)",
    "supply_mode": "Supply mode, service type, mode of supply",
    "supply_period": "Period of supply, supply period, service period",
    "place_of_supply": "Place of supply, supply location",
    
    # Parent Company information
    "company_info.name": "Company name, parent company name, supplier name, our company name",
    "company_info.tagline": "Company tagline, business tagline, company description",
    "company_info.address": "Company address, parent company address, supplier address, our address",
    "company_info.phone": "Company phone, phone number, telephone, landline",
    "company_info.mobile": "Company mobile, mobile number, cell phone",
    "company_info.email": "Company email, email address, contact email",
    "company_info.gstin": "Company GSTIN, supplier GSTIN, our GSTIN, parent company GST",
    "company_info.pan": "Company PAN, supplier PAN, our PAN, parent company PAN",
    "company_info.state": "Company state, supplier state, our state",
    "company_info.state_code": "Company state code, supplier state code",
    
    # Bank information
    "company_info.bank.account_no": "Bank account number, account number, account no, bank account",
    "company_info.bank.name": "Bank name, bank, bank's name",
    "company_info.bank.ifsc": "IFSC code, IFSC, bank IFSC, bank code",
    "company_info.bank.branch": "Bank branch, branch name, branch",
    
    # Client/Customer information - DISABLED (use database loaders instead)
    # "billing_to.client_name": "Client name, customer name, company name, bill to name, billed to, bill to company, customer company name, client company name",
    # "billing_to.address": "Client address, customer address, billing address, bill to address, company address",
    # "billing_to.gstin": "Client GSTIN, customer GSTIN, GST number, GSTN, client GST, customer GST no",
    # "billing_to.state": "Client state, customer state, bill to state",
    # "billing_to.state_code": "Client state code, customer state code, state code",
    # "billing_to.pan": "Client PAN, customer PAN, PAN number",
    "billing_to.spo_no": "SPO number, SPO no, SPO #, purchase order number, PO number, PO no, PO #",
    "billing_to.purchase_order_no": "Purchase order number, purchase order no, PO number, PO no, PO #, order number",
    
    # Tax rates
    "cgst_rate": "CGST rate, CGST percentage, CGST %, central GST rate",
    "sgst_rate": "SGST rate, SGST percentage, SGST %, state GST rate",
    "igst_rate": "IGST rate, IGST percentage, IGST %, integrated GST rate",
}

# =============================================
# 4) Natural Language Command Parsing Instructions
# =============================================
# These instructions guide the LLM agent on how to parse user commands.
# Edit this to change how the agent behaves when processing natural language.
TAX_COMMAND_PARSER_INSTRUCTIONS = """You are a field mapping assistant for invoice data. Parse natural language commands and extract field updates.

Your task:
1. Parse the user's command(s) - they may use words like "change", "update", "set", "modify", "make", "delete", or no verb at all
2. Identify which field(s) they want to update by matching against the field descriptions
3. Extract the new value(s) - preserve the exact text/format the user provides
4. Return a JSON object with field paths as keys and new values as values

Rules for Header/Meta Fields:
- Use exact field paths from the available fields list (e.g., "billing_to.client_name" not "client_name")
- For numeric fields ending in "_rate" or "_amount", return numbers not strings
- For reverse_charge, return "YES" or "NO" as strings
- For dates, preserve the user's format exactly as given
- For text fields, preserve capitalization and spacing as provided

Rules for Items Array (Row-Level Operations):
- When user mentions "row", "first row", "row 1", "row 2", etc., they're referring to items array
- Row numbers are 1-indexed ("first row" = index 0, "row 2" = index 1, etc.)
- Use special syntax for row operations:
  * To modify a field in a specific row: {"items[N].field_name": value}
  * To delete a row: {"items[N]": "__DELETE__"}
  * To add a new row: {"items": [{"description": "...", "quantity": 0, ...}]}
- Available item fields: description, hsn_code, uom, quantity, unit_price, gst_rate, line_discount, line_total
- Common field aliases users might say:
  * "rate" or "price" → unit_price
  * "qty" → quantity
  * "desc" or "name" → description
  * "hsn" or "sac" → hsn_code
  * "unit" → uom
  * "discount" → line_discount
  * "total" or "amount" → line_total

General Rules:
- If a field is not in the available list, ignore it
- Handle multiple commands in one input (e.g., "set cgst to 9 and sgst to 9")
- Return empty object {} if no valid commands found

Examples - Header Fields:
Input: "change client company name to XXXX"
Output: {"billing_to.client_name": "XXXX"}

Input: "set cgst to 9 and sgst to 9"
Output: {"cgst_rate": 9.0, "sgst_rate": 9.0}

Input: "update invoice date to 15-10-2025"
Output: {"invoice_date": "15-10-2025"}

Input: "customer address to 123 Main St, Chennai - 600001"
Output: {"billing_to.address": "123 Main St, Chennai - 600001"}

Input: "make reverse charge NO"
Output: {"reverse_charge": "NO"}

Examples - Row Operations:
Input: "change rate in first row to 800"
Output: {"items[0].unit_price": 800}

Input: "delete first row"
Output: {"items[0]": "__DELETE__"}

Input: "change quantity in row 2 to 500"
Output: {"items[1].quantity": 500}

Input: "update description in row 1 to Transport Service"
Output: {"items[0].description": "Transport Service"}

Input: "set rate to 750 in row 3"
Output: {"items[2].unit_price": 750}

Input: "change qty in first row to 100 and rate to 800"
Output: {"items[0].quantity": 100, "items[0].unit_price": 800}

Input: "delete row 2"
Output: {"items[1]": "__DELETE__"}
"""

# =============================================
# 5) File Upload Extraction Instructions
# =============================================
# These instructions guide the LLM when extracting data from uploaded Excel/CSV files.
# Edit this to change how the agent interprets your datasets.

TAX_FILE_EXTRACTION_INSTRUCTIONS = """You are extracting tax invoice data from an uploaded dataset.

⚠️ CRITICAL: When user says "add all details from dataset to invoice":
- "All details" means: line items, quantities, amounts, supply period, PO numbers, and other INVOICE DATA
- "All details" DOES NOT include: client company name, client address, client GSTIN
- Client company details (billing_to.*) are managed separately via database loaders
- ONLY modify client company fields if user EXPLICITLY says "change client name to X" or similar

Your Goals:
1. Extract header/metadata fields from the dataset:
   - Period of Supply (look for columns like "Period", "Period of Supply", "Supply Period") - VERY IMPORTANT!
   - PO/SPO Number (look for columns like "PO#", "SPO NO", "Purchase Order")
   - Any other relevant invoice metadata
   
2. DO NOT extract client company details unless explicitly requested:
   - ❌ Do NOT extract client company name (even if "Bill To Plant", "Customer" columns exist)
   - ❌ Do NOT extract client GSTIN (even if "GSTN", "GSTIN" columns exist)
   - ❌ Do NOT extract client address
   - These fields are managed by database loaders only

3. Extract line items (one per data row):
   - Description: Synthesize as "GTA Service for Transport of <Material>" if a Material/Product column exists
   - Quantity: From columns like "Bill Qty", "Received Qty", "Qty", "Quantity"
   - Unit Price: From columns like "Price", "Rate", "Unit Price"
   - Line Total: From columns like "Value", "Amount", "Taxable Value"
   - UOM: Default to "MT" if not specified

4. Skip summary/total rows:
   - Ignore rows where the first column says "Total" or most values are blank/NaN
   - Only process actual line item data rows

Business Rules:
- This is for a Goods Transport Agency (GTA) service
- Default tax rates: CGST 6%, SGST 6%, IGST 0% (unless data suggests otherwise)
- Always extract Period of Supply if it exists in the dataset
- The Material column often contains the product being transported
- Preserve exact values from the dataset (don't round or modify)
- Remember: DO NOT extract client GSTIN or client name from dataset

Data Quality:
- Clean up any currency symbols (₹), commas, or extra spaces from numbers
- If Period is found, keep it exactly as shown in the dataset
- Preserve exact numeric values without rounding
"""

# =============================================
# 6) Discovery hints (aliases, defaults, parsing)
# =============================================
TAX_AGENT_CONTEXT = {
    # Soft aliases to understand column names in small invoices (edit freely).
    "item_aliases": {
        "description": ["description", "item", "product", "service", "name", "name of product / service"],
        "hsn_code": ["hsn", "sac", "hsn sac", "hsn_code"],
        "uom": ["uom", "unit", "units"],
        "quantity": ["qty", "quantity", "qnty", "qtn"],
        "unit_price": ["rate", "unit price", "price", "price per mt"],
        "gst_rate": ["gst", "gst %", "gst rate", "igst", "cgst+sgst", "tax %"],
        "line_total": ["taxable value", "taxable", "amount", "value", "line total"],
    },

    # Header/meta fields that often appear as key:value pairs in the top rows.
    # Note: We intentionally DO NOT include company_info.* here (kept immutable unless user asks).
    "header_aliases": {
        # template header/meta
        "invoice_number": ["invoice no", "invoice number", "invoice #"],
        "invoice_date": ["invoice date", "date"],
        "reverse_charge": ["reverse charge"],
        "supply_mode": ["supply mode", "service"],
        "supply_period": ["period of supply", "supply period", "period"],
        "place_of_supply": ["place of supply"],

        # client section (template uses billing_to.*) - DISABLED (use database loaders instead)
        # "billing_to.client_name": [
        #     "billed to", "bill to", "bill to name", "customer", "client", "client name", "name",
        #     "bill to plant"  # typical dataset header
        # ],
        # "billing_to.address": ["address", "bill to address"],
        # "billing_to.gstin": [
        #     "gstin", "gstn", "gst no", "gst number", "gstin/uin",
        #     "customer gstin", "client gstin", "receiver gstin", "consignee gstin",
        #     "customer gst no", "client gst no", "gstin no", "gst no.", "gst no#"
        # ],
        # "billing_to.pan": ["pan", "pan no", "pan number"],
        # "billing_to.state": ["state"],
        # "billing_to.state_code": ["state code", "code"],
    },

    # GTA description synthesis — tweakable knobs
    "gta_description": {
        "enabled": True,
        "prefix": "GTA Service for Transport of",
        # Where to look for a material/product name for synthesis:
        "material_hints": [
            "Name of Product / Service",
            "Product",
            "Material",
            "Commodity",
            "Description",
            "Item"
        ],
        # Casing mode: "as_is" | "title"
        "casing": "as_is"
    },

    # Reasonable defaults when data is missing (TAX ONLY).
    # IMPORTANT: No company_info.* defaults here; those remain as configured in the app.
    "defaults": {
        "reverse_charge": "YES",
        "supply_mode": "Goods Transport Agency Service",
        "cgst_rate": 6.0,
        "sgst_rate": 6.0,
        "igst_rate": 5.0
    },

    # If columns are absent, the agent may fall back to these static item values.
    "fallback_item_values": {
        "uom": "MT"
        # "hsn_code": "996791",  # uncomment or change if your org prefers a default
    },

    # Characters to strip before number parsing.
    "number_cleaners": ["₹", ",", " "],

    # Coercion policies when fields disagree or are partially present.
    "coercion_rules": {
        "prefer_taxable_over_qty_rate_when_both_exist": True,
        "recompute_line_total_if_missing": True
    }
}

