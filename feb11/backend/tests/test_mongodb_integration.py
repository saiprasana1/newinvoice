"""
Test MongoDB Integration Workflow
Simulates loading parent company, client company, and bank data from MongoDB
and verifies they integrate correctly into overrides without affecting other fields.
"""

import json
import os
from copy import deepcopy
from core.state_store import get_initial_state, save_overrides, load_overrides
from integrations.invoice_context_mapper import (
    map_parent_company_to_company_info,
    map_client_company_to_billing_to,
    map_bank_to_invoice_state,
    apply_master_data_to_invoice_state
)

def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

def save_json_file(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"✓ Saved {filename}")

def load_json_file(filename):
    with open(filename, 'r') as f:
        return json.load(f)

# ============================================================================
# STEP 1: Setup - Create initial state with some existing data
# ============================================================================
print_section("STEP 1: Setup Initial State with Existing Data")

# Clean slate
for f in ["overrides_tax.json", "overrides_bill.json"]:
    if os.path.exists(f):
        os.remove(f)

# Get fresh state
initial_state = get_initial_state()

# Add some existing invoice data (to test that it doesn't get overwritten)
initial_state["invoice_number"] = "INV-2025-001"
initial_state["invoice_date"] = "15-12-2025"
initial_state["cgst_rate"] = 9.0
initial_state["sgst_rate"] = 9.0
initial_state["items"] = [
    {
        "description": "Existing Item 1",
        "hsn_code": "996511",
        "uom": "MT",
        "quantity": 100,
        "unit_price": 500,
        "line_total": 50000
    }
]

# Save this as our baseline
save_overrides(initial_state)
print("\nInitial overrides_tax.json:")
print(json.dumps(load_json_file("overrides_tax.json"), indent=2))

print("\n✓ Baseline state created with:")
print(f"  - Invoice number: {initial_state['invoice_number']}")
print(f"  - CGST rate: {initial_state['cgst_rate']}")
print(f"  - Items: {len(initial_state['items'])} item(s)")

# ============================================================================
# STEP 2: Load Parent Company from MongoDB
# ============================================================================
print_section("STEP 2: Load Parent Company (Siva Sakthi Logistics)")

# Simulate MongoDB document for parent company
mock_parent_doc = {
    "_id": "siva_sakthi_logistics",
    "parent_company_title": "Siva Sakthi Logistics",
    "parent_company_tagline": "INTEGRATED LOGISTICS & TRANSPORT SOLUTIONS",
    "parent_company_address": "# 21, SIDCO Industrial Estate, Kurichi, Coimbatore - 641021",
    "parent_company_phone": "0422-2678901",
    "parent_company_mobile": "098765 43210",
    "parent_company_email": "contact@sivasakthilogistics.com",
    "parent_company_state": "Tamil Nadu",
    "parent_company_state_code": "33",
    "parent_company_gstin": "33ABCDE1234F1Z5",
    "parent_company_pan": "ABCDE1234F"
}

print("\nMongoDB Parent Company Document:")
print(json.dumps(mock_parent_doc, indent=2))

# Map to invoice state format
mapped_parent = map_parent_company_to_company_info(mock_parent_doc)

# Load current state and merge
current_state = get_initial_state()
current_state["company_info"] = mapped_parent

# Save back to overrides
save_overrides(current_state)

print("\n✓ Parent company loaded and saved")

# Verify other fields are intact
reloaded = get_initial_state()
print(f"\n✓ Verification after parent company load:")
print(f"  - Invoice number: {reloaded['invoice_number']} (should be INV-2025-001)")
print(f"  - CGST rate: {reloaded['cgst_rate']} (should be 9.0)")
print(f"  - Items count: {len(reloaded['items'])} (should be 1)")
print(f"  - Company name: {reloaded['company_info']['name']}")
print(f"  - Company GSTIN: {reloaded['company_info']['gstin']}")

assert reloaded['invoice_number'] == "INV-2025-001", "Invoice number was overwritten!"
assert reloaded['cgst_rate'] == 9.0, "CGST rate was overwritten!"
assert len(reloaded['items']) == 1, "Items were overwritten!"
print("✅ Other fields intact!")

# ============================================================================
# STEP 3: Load Client Company from MongoDB
# ============================================================================
print_section("STEP 3: Load Client Company (RAMCO CEMENTS LTD)")

# Simulate MongoDB document for client company
mock_client_doc = {
    "_id": "ramco_cements_ltd",
    "client_company_name": "RAMCO CEMENTS LTD.",
    "client_company_address": "RR Nagar, Cement Works, Alathiyur, Ariyalur - 621707",
    "client_company_gstin": "33AAACR9589E1ZQ",
    "client_company_state": "Tamil Nadu",
    "client_company_state_code": "33"
}

print("\nMongoDB Client Company Document:")
print(json.dumps(mock_client_doc, indent=2))

# Map to invoice state format
mapped_client = map_client_company_to_billing_to(mock_client_doc)

# Load current state and merge
current_state = get_initial_state()
current_state["billing_to"] = mapped_client

# Save back to overrides
save_overrides(current_state)

print("\n✓ Client company loaded and saved")

# Verify other fields are intact
reloaded = get_initial_state()
print(f"\n✓ Verification after client company load:")
print(f"  - Invoice number: {reloaded['invoice_number']} (should be INV-2025-001)")
print(f"  - CGST rate: {reloaded['cgst_rate']} (should be 9.0)")
print(f"  - Items count: {len(reloaded['items'])} (should be 1)")
print(f"  - Company name: {reloaded['company_info']['name']} (should be Siva Sakthi Logistics)")
print(f"  - Client name: {reloaded['billing_to']['client_name']}")
print(f"  - Client GSTIN: {reloaded['billing_to']['gstin']}")

assert reloaded['invoice_number'] == "INV-2025-001", "Invoice number was overwritten!"
assert reloaded['cgst_rate'] == 9.0, "CGST rate was overwritten!"
assert len(reloaded['items']) == 1, "Items were overwritten!"
assert reloaded['company_info']['name'] == "Siva Sakthi Logistics", "Company name was overwritten!"
print("✅ Other fields intact!")

# ============================================================================
# STEP 4: Load Bank Details from MongoDB
# ============================================================================
print_section("STEP 4: Load Bank Details (ICICI Bank)")

# Simulate MongoDB document for bank
mock_bank_doc = {
    "_id": "icici_bank_chennai",
    "bank_account_number": "987654321012",
    "bank_name": "ICICI BANK",
    "bank_ifsc_code": "ICIC0001234",
    "branch": "T. Nagar, Chennai"
}

print("\nMongoDB Bank Document:")
print(json.dumps(mock_bank_doc, indent=2))

# Map to invoice state format
mapped_bank = map_bank_to_invoice_state(mock_bank_doc)

# Load current state and merge
current_state = get_initial_state()
current_state["company_info"]["bank"] = mapped_bank

# Save back to overrides
save_overrides(current_state)

print("\n✓ Bank details loaded and saved")

# Verify other fields are intact
reloaded = get_initial_state()
print(f"\n✓ Verification after bank load:")
print(f"  - Invoice number: {reloaded['invoice_number']} (should be INV-2025-001)")
print(f"  - CGST rate: {reloaded['cgst_rate']} (should be 9.0)")
print(f"  - Items count: {len(reloaded['items'])} (should be 1)")
print(f"  - Company name: {reloaded['company_info']['name']} (should be Siva Sakthi Logistics)")
print(f"  - Client name: {reloaded['billing_to']['client_name']} (should be RAMCO CEMENTS LTD.)")
print(f"  - Bank name: {reloaded['company_info']['bank']['name']}")
print(f"  - Bank account: {reloaded['company_info']['bank']['account_no']}")

assert reloaded['invoice_number'] == "INV-2025-001", "Invoice number was overwritten!"
assert reloaded['cgst_rate'] == 9.0, "CGST rate was overwritten!"
assert len(reloaded['items']) == 1, "Items were overwritten!"
assert reloaded['company_info']['name'] == "Siva Sakthi Logistics", "Company name was overwritten!"
assert reloaded['billing_to']['client_name'] == "RAMCO CEMENTS LTD.", "Client name was overwritten!"
print("✅ All other fields intact!")

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print_section("FINAL SUMMARY")

final_state = get_initial_state()

print("\n📋 Final Invoice State:")
print(f"  Invoice Number: {final_state['invoice_number']}")
print(f"  Invoice Date: {final_state['invoice_date']}")
print(f"  CGST Rate: {final_state['cgst_rate']}%")
print(f"  SGST Rate: {final_state['sgst_rate']}%")
print(f"  Items: {len(final_state['items'])} item(s)")
print(f"\n🏢 Parent Company:")
print(f"  Name: {final_state['company_info']['name']}")
print(f"  Address: {final_state['company_info']['address']}")
print(f"  GSTIN: {final_state['company_info']['gstin']}")
print(f"\n🏦 Bank Details:")
print(f"  Bank: {final_state['company_info']['bank']['name']}")
print(f"  Account: {final_state['company_info']['bank']['account_no']}")
print(f"  IFSC: {final_state['company_info']['bank']['ifsc']}")
print(f"\n👥 Client Company:")
print(f"  Name: {final_state['billing_to']['client_name']}")
print(f"  Address: {final_state['billing_to']['address']}")
print(f"  GSTIN: {final_state['billing_to']['gstin']}")

print("\n" + "=" * 80)
print("✅ ALL TESTS PASSED!")
print("=" * 80)
print("\n✓ Parent company data loaded correctly")
print("✓ Client company data loaded correctly")
print("✓ Bank details loaded correctly")
print("✓ Existing invoice fields preserved")
print("✓ No field interference detected")
print("\n🎉 MongoDB integration workflow verified successfully!")
