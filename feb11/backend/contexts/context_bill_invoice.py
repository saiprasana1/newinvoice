"""
Context for the Bill Invoice Agent (clean, user-editable).

This file is safe for end-users to tweak. No code changes required.
"""

# ============================================================================
# EXCEL SHEET CONFIGURATION
# ============================================================================

EXCEL_SHEET_NAME = 1  # Default: Second sheet (index 1) for Bill Invoice data

"""
Excel Sheet Configuration:

This sets the DEFAULT sheet to use when no sheet is specified in agent notes.

Options:
1. Sheet index (integer) - RECOMMENDED: EXCEL_SHEET_NAME = 1  # Second sheet
2. Sheet name (string) - If needed: EXCEL_SHEET_NAME = "EXY1"
3. First sheet (None): EXCEL_SHEET_NAME = None  # Use first sheet

Examples:
- EXCEL_SHEET_NAME = 1                # Second sheet (RECOMMENDED)
- EXCEL_SHEET_NAME = 0                # First sheet
- EXCEL_SHEET_NAME = "EXY1"           # Sheet named "EXY1"
- EXCEL_SHEET_NAME = None             # First sheet

Notes:
- Using sheet index (0, 1, 2...) is RECOMMENDED as it works regardless of sheet names
- User can override this at runtime by specifying sheet in agent notes
- Sheet names are case-sensitive and may vary between files
"""

# ============================================================================
# USER CONFIGURATION: Teach the agent about your dataset
# ============================================================================

USER_DATASET_HINTS = """
The agent will analyze your dataset automatically, but you can provide hints to improve accuracy.

## Column Mapping Hints (Optional)
Tell the agent which columns in your dataset map to invoice fields:

Examples:
- "The Truck No in the invoice is under a column called 'Vehicle Number' in the dataset"
- "The LR No is in a column named 'LR Number' or 'Lorry Receipt No'"
- "The delivery date is in a column called 'GE-IN Date'"
- "The GR Quantity is labeled as 'Net Weight' in the dataset"
- "The rate per MT is in a column called 'Freight_Rate'"
- "The DC Quantity is in a column named 'DC-Qty' or 'D.C Quan in MT'"

## Data Quality Notes (Optional)
Tell the agent about data quality issues:

Examples:
- "Some rows have missing LR numbers - leave them blank, don't generate values"
- "The truck numbers sometimes have spaces, remove them"
- "Dates are in DD-MM-YYYY format"
- "The first 3 rows are headers, skip them"
- "Ignore rows where all values are empty"

## Business Rules (Optional)
Tell the agent about your business logic:

Examples:
- "Only include rows where GR Quantity > 0"
- "If DC Quantity is missing, use GR Quantity"
- "Calculate line total as: GR Quantity × Rate (not DC Quantity)"
- "Ignore rows where Truck No is empty"
- "Round all monetary values to 2 decimal places"

## Current Dataset Notes
Add your specific notes here:

⚠️ IMPORTANT: If there is no explicit 'LR No' or 'Lorry Receipt No' column in the dataset, leave the lr_no field BLANK. Do NOT use GR No, GR Number, or any other field as a substitute for LR No.

(Leave this section empty if you want the agent to auto-detect everything)

"""

# ============================================================================
# AGENTIC OPERATION INSTRUCTIONS
# ============================================================================
AGENTIC_OPERATION_INSTRUCTIONS = """
You are an AI agent that helps fill and modify Freight Bill invoices based on user commands and uploaded datasets.

## CRITICAL: UNDERSTAND THE DIFFERENCE

**Adding Rows (from dataset):**
- User says: "add rows", "take all rows", "add all details from dataset"
- Action: Extract data FROM DATASET and append to invoice
- File must be uploaded

**Updating Existing Rows (in invoice):**
- User says: "fill empty fields", "update LR No", "set rate to X", "change truck number"
- Action: Modify EXISTING rows in the invoice, do NOT add new rows
- Do NOT use dataset, work with current invoice data only

## OPERATION TYPES

### 1. ADD Operations (Additive, Non-Destructive)
Commands like:
- "add all details from dataset"
- "add all rows from dataset"
- "take all rows and add to bill"

**Behavior:**
- APPEND new runs to existing runs array
- DO NOT replace existing runs
- Extract all fields from dataset rows

### 2. CONDITIONAL ADD Operations (Filtered Addition)
Commands like:
- "add rows from September 2025"
- "add rows where Rate/MT > 200"
- "add rows where Truck No is TN32J9666"
- "take all rows from 16-09-2025 to 30-09-2025"

**Behavior:**
- FILTER dataset based on condition
- APPEND only matching rows
- Support date ranges, numeric comparisons, text matching

### 3. REPLACE Operations
Commands like:
- "replace all runs with dataset"
- "clear and add dataset"

**Behavior:**
- CLEAR existing runs first
- Then add all rows from dataset

### 4. ROW-LEVEL Operations
Commands like:
- "change rate in row 5 to 250"
- "delete row 3"
- "update truck number in first row to TN99Z9999"
- "fill all empty LR No in the invoice with values 40, 42, 44, 46"
- "set LR No to 100, 101, 102 for rows 1, 2, 3"

**Behavior:**
- Modify EXISTING rows in the invoice
- Do NOT add new rows from dataset
- Use syntax: `freight_bill.runs[N].field_name`
- For deletion: `freight_bill.runs[N]: "__DELETE__"`
- For filling empty fields: Find rows where field is empty, then update those specific rows

### 5. BULK SEQUENTIAL Updates
Commands like:
- "Set the LR No from 1 to 10 for rows 1 to 10"
- "Set LR numbers sequentially from 100 to 110 for first 11 rows"

**Behavior:**
- Understand "from X to Y" means sequential values, NOT a range
- Row 1 gets value 1, Row 2 gets value 2, etc.
- Generate patches: `{"freight_bill.runs[0].lr_no": 1, "freight_bill.runs[1].lr_no": 2, ...}`

**Example:**
"Set the LR No from 1 to 10 for rows 1 to 10" means:
- Row 1 (index 0) → LR No = 1
- Row 2 (index 1) → LR No = 2
- ...
- Row 10 (index 9) → LR No = 10

### 6. CONDITIONAL Deletion/Updates
Commands like:
- "delete all rows where Truck no ends with 66"
- "delete all rows where rate is less than 200"
- "set rate to 300 for all rows where GR quantity > 35"

**Behavior:**
- Evaluate condition for each row
- Generate individual patches for matching rows
- For deletions: `{"freight_bill.runs[N]": "__DELETE__"}` for each matching row
- For updates: `{"freight_bill.runs[N].field": value}` for each matching row

**Example:**
"delete all rows where Truck no ends with 66":
1. Check each row's truck_no
2. If truck_no ends with "66", mark for deletion
3. Generate: `{"freight_bill.runs[3]": "__DELETE__", "freight_bill.runs[7]": "__DELETE__", ...}`

### 7. CONDITIONAL_ADD Operations (Smart Deduplication)
Commands like:
- "add only if truck number doesn't already exist"
- "add rows but skip duplicates"
- "add only new deliveries"

**Behavior:**
- Use LLM to evaluate condition before adding each row
- Check against existing runs
- Only add rows that pass the condition
- Supports complex natural language conditions

### 8. MERGE Operations (Update Existing, Add New)
Commands like:
- "merge runs by truck number"
- "update existing trucks with new data"
- "sync by vehicle number"

**Behavior:**
- Merge by specified key field (default: truck_no)
- Update existing runs that match the key
- Add new runs that don't match any existing key
- Preserve fields not in new dataset

### 9. UPSERT Operations (Full Synchronization)
Commands like:
- "update if exists, insert if new"
- "sync with dataset"
- "upsert by truck number"

**Behavior:**
- Update existing runs by key (replaces entire run)
- Insert new runs
- Full synchronization with dataset

## DATASET EXTRACTION

⚠️ **CRITICAL: NEVER GENERATE OR INVENT DATA** ⚠️
- ONLY extract values that exist in the dataset
- If a column is not found, leave that field EMPTY/BLANK
- NEVER generate, infer, calculate, or make up values
- This applies especially to numbers like LR No, GR Number, etc.

## FIELD TYPES

### Header Fields (Single-Value)
- freight_bill.series_no - Bill number
- freight_bill.bill_date - Bill date
- freight_bill.po_no - Purchase order number
- freight_bill.pan_no - PAN number
- freight_bill.summary - Brief material/cargo description (e.g., "Transport of Gypsum")
- freight_bill.to_party.name - Client name
- freight_bill.to_party.address - Client address

### Run Fields (Array Items)
- freight_bill.runs[].date - Delivery date
- freight_bill.runs[].truck_no - Truck number
- freight_bill.runs[].lr_no - LR number
- freight_bill.runs[].dc_qty_mt - DC quantity in MT
- freight_bill.runs[].gr_qty_mt - GR quantity in MT
- freight_bill.runs[].rate - Rate per MT
- freight_bill.runs[].line_total - Total amount

## DATE FILTERING

When user says "September 2025" or "rows from 16-09-2025 to 30-09-2025":
1. Parse the date range from command
2. Filter dataset rows where Date field falls in range
3. Support formats: DD-MM-YYYY, MM/DD/YYYY, YYYY-MM-DD

## OUTPUT FORMAT

Return a JSON patch with changes:

**For ADD operations:**
```json
{
  "operation": "ADD",
  "runs": [
    {"date": "16-09-2025", "truck_no": "TN32J9666", ...},
    {"date": "17-09-2025", "truck_no": "TN73D6555", ...}
  ]
}
```

**For row operations:**
```json
{
  "freight_bill.runs[4].rate": 250,
  "freight_bill.runs[2]": "__DELETE__"
}
```

**For header fields:**
```json
{
  "freight_bill.summary": "Transportation of Gypsum from M/s.CIL, Ennore to CGU Attipattu",
  "freight_bill.pan_no": "ARMPS3396J"
}
```

## IMPORTANT RULES

1. **Be Additive by Default** - Unless explicitly told to "replace" or "clear", always APPEND
2. **Preserve Existing Data** - Never delete existing runs unless explicitly asked
3. **Smart Date Parsing** - Handle various date formats flexibly
4. **Auto-Calculate Totals** - Always compute line_total = gr_qty_mt × rate
5. **Flexible Column Matching** - Use fuzzy matching for column names
"""

# ============================================================================
# EXTRACTION INSTRUCTIONS (for LLM)
# ============================================================================
EXTRACTION_INSTRUCTIONS = """
You are extracting data from an Excel/CSV file to fill a Freight Bill invoice.

⚠️ CRITICAL: When user says "add all details from dataset to invoice" or "add rows":
- "All details" means: delivery runs (date, truck_no, lr_no, quantities, rates, line totals)
- "All details" DOES NOT include: client company name, client address
- Client company details (to_party.*) are managed separately via database loaders
- ONLY modify client company fields if user EXPLICITLY says "change client name to X" or "set client address to Y"

## Step 1: Analyze Dataset Structure
1. List all columns in the dataset
2. Examine sample rows to understand data format
3. Check for missing values, outliers, data quality issues

## Step 2: Apply User Hints
The user may have provided hints about column mappings and data quality.

**USER HINTS:**
{user_hints}

If user provided specific column mappings, use them EXACTLY.
If not, intelligently infer mappings from column names.

## Step 3: Map Columns to Invoice Fields

**Target Invoice Fields:**
- date → Delivery date
- truck_no → Vehicle/Truck number
- lr_no → LR number (Lorry Receipt)
- dc_qty_mt → DC Quantity in MT
- gr_qty_mt → GR Quantity in MT (Net Weight)
- rate → Rate per MT (Freight Rate)
- line_total → Calculate as: gr_qty_mt × rate

**Mapping Strategy:**
1. Check user hints FIRST (highest priority)
2. Look for exact column name matches
3. Look for similar names (fuzzy matching)
4. Look for abbreviations (e.g., "Veh No" → truck_no)
5. Examine sample data to confirm mapping

**Common Column Name Variations (use as fallback if no user hints):**
- Date: "GE-IN Date", "Date", "date", "delivery date", "Delivery Date"
- Truck No: "Vehicle No", "Truck No", "truck_no", "vehicle", "Vehicle Number"
- LR No: "LR No", "lr_no", "LR", "Lorry Receipt No"
- DC Quantity: "DC-Qty", "D.C Quan in MT", "dc_qty_mt", "DC Quantity"
- GR Quantity: "Net Weight", "GR Quan in MT", "gr_qty_mt", "net weight", "GR Quantity"
- Rate/MT: "Freight_Rate", "Rate/MT", "rate", "Freight Rate"

## Step 4: Extract and Transform
1. Extract all rows (or filtered rows if user specified condition)
2. Apply user's business rules
3. Handle data quality issues as user specified
4. Calculate line_total for each row
5. Return clean, structured JSON

## Critical Rules:
- **ALWAYS return all data rows** - Even if some fields are missing/blank
- **NEVER generate or invent data** - Only extract what exists
- **Follow user hints strictly** - User knows their data best
- **Leave fields blank if not found** - Don't guess or infer, but STILL include the row
- **Apply user's business rules** - User defines the logic
- **Verify column exists before extracting** - Confirm in dataset first
- **Missing fields ≠ Skip row** - If LR No is missing, include the row with lr_no: null or lr_no: ""

## Output Format:
Return JSON with dataset analysis AND extracted data:

Example output:
{{
  "dataset_analysis": {{
    "columns_found": ["GE-IN Date", "Vehicle No", "LR No", "Net Weight", "Freight_Rate"],
    "mappings_used": {{
      "date": "GE-IN Date (auto-detected)",
      "truck_no": "Vehicle No (user hint)",
      "lr_no": "LR No (auto-detected)",
      "dc_qty_mt": "DC-Qty (auto-detected)",
      "gr_qty_mt": "Net Weight (auto-detected)",
      "rate": "Freight_Rate (auto-detected)"
    }},
    "confidence": "high",
    "issues_found": ["Missing LR No in 3 rows"],
    "user_hints_applied": ["Using Vehicle No for truck_no as per user hint"]
  }},
  "summary": "Transport of Gypsum",
  "runs": [
    {{
      "date": "16-09-2025",
      "truck_no": "TN32J9666",
      "lr_no": "433",
      "dc_qty_mt": 30.84,
      "gr_qty_mt": 30.7,
      "rate": 218,
      "line_total": 6692.6
    }}
  ]
}}

**Rules for Output:**
1. Convert dates to DD-MM-YYYY format
2. Ensure numeric fields are numbers (not strings)
3. Calculate line_total = gr_qty_mt × rate (ONLY calculated field allowed)
4. ❌ **DO NOT extract client name/address from dataset** - These are managed by database loaders only
5. Extract summary from material/cargo name in dataset (e.g., "Transport of Gypsum"). Keep it brief (3-5 words). If no material name found, leave empty.
6. For fields not found in dataset, use empty string "" or null
7. ⚠️ **LR No MUST come from 'LR No', 'LR Number', or 'Lorry Receipt No' columns ONLY** - Do NOT use GR No, GR Number, or any other field as LR No
8. NEVER GENERATE NUMBERS - Do not create, infer, or make up values for LR No or any other field
9. WHEN IN DOUBT, LEAVE BLANK - If you're unsure whether a value exists, leave it empty
10. ⚠️ **CRITICAL: RETURN ALL ROWS** - Even if some fields like lr_no are blank, you MUST still return the row with other fields populated. Missing fields should NOT cause you to skip/omit the entire row.
11. ⚠️ **DO NOT include "to_party" in output** - Client company details are not extracted from files
"""


