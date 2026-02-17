"""
Template Registry Module

Provides template metadata and schema definitions for dynamic UI generation.
"""

from typing import Dict, List, Any, Optional

# Template metadata
TEMPLATES = [
    {
        "id": "tax",
        "name": "Tax Invoice (GTA)",
        "display_name": "Siva Sakthi GTA",
        "description": "GST Tax Invoice for Goods Transport Agency services",
        "icon": "📄",
        "category": "tax",
        "features": ["items", "gst", "supply_period", "reverse_charge"],
        "endpoints": {
            "default": "/api/invoice/tax/default",
            "process": "/api/invoice/tax/process",
            "export": "/api/invoice/tax/export",
            "save": "/api/invoice/tax/state",
            "command": "/api/invoice/tax/command"
        }
    },
    {
        "id": "bill",
        "name": "Freight Bill",
        "display_name": "Siva Sakthi Freight Bill",
        "description": "Freight Bill for Transport and Logistics Services",
        "icon": "🚚",
        "category": "logistics",
        "features": ["runs", "lr_numbers", "freight", "delivery_tracking"],
        "endpoints": {
            "default": "/api/invoice/bill/default",
            "process": "/api/invoice/bill/process",
            "export": "/api/invoice/bill/export",
            "save": "/api/invoice/bill/state",
            "command": "/api/invoice/bill/command"
        }
    }
]

# Schema definitions for each template
SCHEMAS = {
    "tax": {
        "invoice_number": {
            "type": "string",
            "label": "Invoice Number",
            "required": True,
            "editable": True,
            "placeholder": "INV-001",
            "description": "Unique invoice identifier"
        },
        "invoice_date": {
            "type": "date",
            "label": "Invoice Date",
            "required": True,
            "editable": True,
            "default": "today",
            "description": "Date of invoice generation"
        },
        "company_info": {
            "type": "object",
            "label": "Company Information",
            "editable": False,
            "description": "Parent company details (loaded from database)",
            "fields": {
                "name": {"type": "string", "label": "Company Name", "editable": False},
                "address": {"type": "string", "label": "Address", "editable": False},
                "gstin": {"type": "string", "label": "GSTIN", "editable": False},
                "pan": {"type": "string", "label": "PAN", "editable": False}
            }
        },
        "billing_to": {
            "type": "object",
            "label": "Bill To",
            "editable": False,
            "description": "Client company details (loaded from database)",
            "fields": {
                "client_name": {"type": "string", "label": "Client Name", "editable": False},
                "address": {"type": "string", "label": "Address", "editable": False},
                "gstin": {
                    "type": "string",
                    "label": "GSTIN",
                    "editable": False,
                    "pattern": "^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
                },
                "state": {"type": "string", "label": "State", "editable": False},
                "state_code": {"type": "string", "label": "State Code", "editable": False}
            }
        },
        "supply_period": {
            "type": "string",
            "label": "Supply Period",
            "required": False,
            "editable": True,
            "placeholder": "01.01.2026 to 31.01.2026",
            "description": "Period of service supply"
        },
        "items": {
            "type": "array",
            "label": "Items",
            "editable": True,
            "description": "List of invoice line items",
            "item_schema": {
                "description": {
                    "type": "string",
                    "label": "Description",
                    "required": True,
                    "placeholder": "GTA Service"
                },
                "hsn_sac": {
                    "type": "string",
                    "label": "HSN/SAC",
                    "required": False,
                    "placeholder": "996791"
                },
                "quantity": {
                    "type": "number",
                    "label": "Quantity",
                    "required": True,
                    "min": 0,
                    "default": 1
                },
                "uom": {
                    "type": "string",
                    "label": "UOM",
                    "required": False,
                    "default": "Nos",
                    "options": ["Nos", "Kgs", "Tonnes", "Bags", "Boxes"]
                },
                "rate": {
                    "type": "number",
                    "label": "Rate",
                    "required": True,
                    "min": 0,
                    "precision": 2
                },
                "amount": {
                    "type": "number",
                    "label": "Amount",
                    "required": False,
                    "editable": False,
                    "computed": True,
                    "formula": "quantity * rate"
                }
            }
        },
        "cgst_rate": {
            "type": "number",
            "label": "CGST Rate (%)",
            "required": True,
            "editable": True,
            "default": 6.0,
            "min": 0,
            "max": 100
        },
        "sgst_rate": {
            "type": "number",
            "label": "SGST Rate (%)",
            "required": True,
            "editable": True,
            "default": 6.0,
            "min": 0,
            "max": 100
        },
        "igst_rate": {
            "type": "number",
            "label": "IGST Rate (%)",
            "required": True,
            "editable": True,
            "default": 0.0,
            "min": 0,
            "max": 100
        },
        "reverse_charge": {
            "type": "boolean",
            "label": "Reverse Charge",
            "required": False,
            "editable": True,
            "default": False,
            "description": "Whether reverse charge mechanism applies"
        },
        "bank_details": {
            "type": "object",
            "label": "Bank Details",
            "editable": False,
            "description": "Bank account details (loaded from database)",
            "fields": {
                "bank_name": {"type": "string", "label": "Bank Name", "editable": False},
                "account_number": {"type": "string", "label": "Account Number", "editable": False},
                "ifsc": {"type": "string", "label": "IFSC Code", "editable": False},
                "branch": {"type": "string", "label": "Branch", "editable": False}
            }
        },
        "terms_and_conditions": {
            "type": "array",
            "label": "Terms and Conditions",
            "editable": False,
            "description": "Terms and conditions (loaded from database)",
            "item_schema": {
                "type": "string"
            }
        }
    },
    "bill": {
        "invoice_number": {
            "type": "string",
            "label": "Bill Number",
            "required": True,
            "editable": True,
            "placeholder": "BILL-001"
        },
        "invoice_date": {
            "type": "date",
            "label": "Bill Date",
            "required": True,
            "editable": True,
            "default": "today"
        },
        "company_info": {
            "type": "object",
            "label": "Company Information",
            "editable": False,
            "fields": {
                "name": {"type": "string", "label": "Company Name", "editable": False},
                "address": {"type": "string", "label": "Address", "editable": False}
            }
        },
        "freight_bill": {
            "type": "object",
            "label": "Freight Bill Details",
            "editable": True,
            "fields": {
                "to_party": {
                    "type": "object",
                    "label": "To Party",
                    "editable": False,
                    "description": "Client details (loaded from database)",
                    "fields": {
                        "name": {"type": "string", "label": "Party Name", "editable": False},
                        "address": {"type": "string", "label": "Address", "editable": False}
                    }
                },
                "summary": {
                    "type": "string",
                    "label": "Summary",
                    "required": False,
                    "editable": True,
                    "placeholder": "Monthly freight charges"
                },
                "runs": {
                    "type": "array",
                    "label": "Delivery Runs",
                    "editable": True,
                    "item_schema": {
                        "date": {
                            "type": "date",
                            "label": "Date",
                            "required": True
                        },
                        "truck_number": {
                            "type": "string",
                            "label": "Truck Number",
                            "required": True,
                            "placeholder": "TN01AB1234"
                        },
                        "lr_number": {
                            "type": "string",
                            "label": "LR Number",
                            "required": False,
                            "placeholder": "LR123456"
                        },
                        "from_location": {
                            "type": "string",
                            "label": "From",
                            "required": True
                        },
                        "to_location": {
                            "type": "string",
                            "label": "To",
                            "required": True
                        },
                        "quantity": {
                            "type": "number",
                            "label": "Quantity",
                            "required": True,
                            "min": 0
                        },
                        "uom": {
                            "type": "string",
                            "label": "UOM",
                            "required": False,
                            "default": "Tonnes"
                        },
                        "rate": {
                            "type": "number",
                            "label": "Rate",
                            "required": True,
                            "min": 0
                        },
                        "amount": {
                            "type": "number",
                            "label": "Amount",
                            "editable": False,
                            "computed": True,
                            "formula": "quantity * rate"
                        }
                    }
                }
            }
        },
        "bank_details": {
            "type": "object",
            "label": "Bank Details",
            "editable": False,
            "fields": {
                "bank_name": {"type": "string", "label": "Bank Name", "editable": False},
                "account_number": {"type": "string", "label": "Account Number", "editable": False},
                "ifsc": {"type": "string", "label": "IFSC Code", "editable": False}
            }
        }
    }
}


def get_all_templates() -> List[Dict[str, Any]]:
    """
    Get list of all available invoice templates.
    
    Returns:
        List of template metadata dictionaries
    """
    return TEMPLATES


def get_template_by_id(template_id: str) -> Optional[Dict[str, Any]]:
    """
    Get template metadata by ID.
    
    Args:
        template_id: Template identifier (e.g., 'tax', 'bill')
        
    Returns:
        Template metadata dictionary or None if not found
    """
    for template in TEMPLATES:
        if template["id"] == template_id:
            return template
    return None


def get_template_schema(template_id: str) -> Optional[Dict[str, Any]]:
    """
    Get field schema for a template.
    
    Args:
        template_id: Template identifier (e.g., 'tax', 'bill')
        
    Returns:
        Schema dictionary or None if not found
    """
    return SCHEMAS.get(template_id)


def get_template_schema_response(template_id: str) -> Optional[Dict[str, Any]]:
    """
    Get complete schema response for API endpoint.
    
    Args:
        template_id: Template identifier
        
    Returns:
        Complete schema response with metadata or None if not found
    """
    template = get_template_by_id(template_id)
    schema = get_template_schema(template_id)
    
    if not template or not schema:
        return None
    
    return {
        "template_id": template["id"],
        "template_name": template["name"],
        "display_name": template["display_name"],
        "schema": schema
    }
