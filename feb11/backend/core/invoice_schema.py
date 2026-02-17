from datetime import datetime, timedelta

def get_default_invoice_data():
    """Returns default invoice structure with sensible, editable defaults."""
    return {
        "invoice_title": "INVOICE",
        "invoice_number": "",

        # DD-MM-YYYY as requested
        "invoice_date": datetime.now().strftime("%d-%m-%Y"),
        "due_date": (datetime.now() + timedelta(days=30)).strftime("%d-%m-%Y"),

        # Common toggle used by the tax invoice template
        "reverse_charge": "YES",

        # ── Parent company (supplier) ────────────────────────────────────────────
        # Header text is hard-coded in the HTML template, but IDs live in state.
        "company_info": {
            "name": "Siva Sakthi Roadways",
            "tagline": "GOODS TRANSPORT AGENCY & WEIGH BRIDGE",
            "address": "# D-46, CMDA Truck Terminal Complex, Madhavaram, Chennai - 600 110",
            "phone": "044-2553 0165",
            "mobile": "094453 84189",
            "email": "sekars.ssr@gmail.com",

            # Defaults that must appear by default but stay editable:
            "state": "Tamil Nadu",
            "state_code": "33",
            "gstin": "33ARMPS3396J2Z4",
            "pan": "ARMPS3396J",

            # Bank details (default + editable)
            "bank": {
                "account_no": "11327915122",
                "name": "STATE BANK OF INDIA",
                "ifsc": "SBIN0002814",
                "branch": "YERRAGUNTLA",
            },
        },

        # Top-level supply fields (parent-company context)
        "supply_mode": "Goods Transport Agency Service",  # default, editable
        "supply_period": "",                              # blank by default
        "place_of_supply": "",                            # blank by default

        # ── Taxes (defaults; editable) ───────────────────────────────────────────
        "cgst_rate": 6.0,
        "sgst_rate": 6.0,
        "igst_rate": 5.0,

        # Amounts are computed from subtotal × rates, but we keep them in state
        # so edits and exports always have a single source of truth.
        "cgst_amount": 0.0,
        "sgst_amount": 0.0,
        "igst_amount": 0.0,

        # ── Client/billing party ────────────────────────────────────────────────
        "billing_to": {
            "client_name": "",
            "address": "",
            "gstin": "",
            "state": "",
            "state_code": "",
            "purchase_order_no": "",
            "spo_no": "",
        },

        "payment_terms": "Payment due upon receipt, or as per contract.",
        "currency_symbol": "Rs",
        "date_format": "DD-MM-YYYY",

        # Items & totals (Tax Invoice)
        "items": [],
        "subtotal": 0.00,
        "discount": 0.00,
        # (Kept for backward-compat with any old code; not used for split GST)
        "tax_rate": 0.00,
        "tax_amount": 0.00,
        "shipping_handling": 0.00,
        "total": 0.00,

        "remarks": (
            "Thank you for choosing Your Logistics Co.! "
            "Please reference the invoice number for all inquiries."
        ),

        # ── Terms and Conditions (Tax Invoice) ──────────────────────────────────
        # Default T&C loaded from MongoDB on page load
        # Array of strings for easy template rendering
        "terms_and_conditions": [
            "Notification No 3/2017 dated 19/6/2017 GST is payable under Reverse charge mechanism.",
            "Interest @ 18% per annum will be charged on delayed payment of bills.",
            "All disputes are subject to Yerraguntla Jurisdiction only.",
            "This Invoice details will be uploaded in our GST Returns as applicable."
        ],

        # ── Freight Bill (Bill Invoice) ─────────────────────────────────────────
        # Used by the new 'Siva Sakthi Freight Bill' template
        "freight_bill": {
            "series_no": "",
            "bill_date": datetime.now().strftime("%d-%m-%Y"),
            "po_no": "",
            "pan_no": "ARMPS3396J",
            "summary": "",

            "to_party": {
                "name": "",
                "address": "",
            },

            # Rows of trips/runs
            # Each run: date, truck_no, lr_no, qty, rate, line_total
            "runs": [],

            # Optional convenience; if set, UI/agent can prefill missing rate
            "rate_default": 0.0,

            # Totals for the bill invoice
            "dc_total": 0.0,
            "gr_total": 0.0,
            "subtotal": 0.0,
            "total": 0.0,
            "amount_in_words": "",
        },
    }


def parse_date_for_crm(date_str, date_format="auto"):
    """
    Parse date string from CRM data according to specified format
    for filtering/comparison.
    """
    if not date_str or not isinstance(date_str, str):
        return None

    date_str = date_str.strip()

    # Known formats to try
    formats = {
        "DD-MM-YYYY": ["%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y"],
        "MM-DD-YYYY": ["%m-%d-%Y", "%m/%d/%Y", "%m.%d.%Y"],
        "YYYY-MM-DD": ["%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"],
    }

    if date_format != "auto" and date_format in formats:
        for fmt_str in formats[date_format]:
            try:
                return datetime.strptime(date_str, fmt_str)
            except ValueError:
                continue

    # Auto-detect: try all known patterns
    all_formats = [fmt for group in formats.values() for fmt in group]
    for fmt_str in all_formats:
        try:
            return datetime.strptime(date_str, fmt_str)
        except ValueError:
            continue

    return None


def get_date_format_options():
    """Get available date format options for the dropdown."""
    return ["auto", "DD-MM-YYYY", "MM-DD-YYYY", "YYYY-MM-DD"]


# Alias for backward compatibility with state_store.py
DEFAULT_STATE = get_default_invoice_data()
