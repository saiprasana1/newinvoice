from __future__ import annotations
import os, base64

from core.invoice_math import calculate_invoice_totals

# Expose shared helpers for the sub-templates to import
def _fmt(n, whole_ok: bool = False):
    try:
        v = float(n or 0)
        if whole_ok and v == int(v):
            return f"{int(v):,}"
        return f"{v:,.2f}"
    except Exception:
        return "0.00"

def _amount_in_words(n: float) -> str:
    try:
        r = int(n); p = int(round((n - r) * 100))
        def w(x: int):
            ones = ["Zero","One","Two","Three","Four","Five","Six","Seven","Eight","Nine","Ten",
                    "Eleven","Twelve","Thirteen","Fourteen","Fifteen","Sixteen","Seventeen","Eighteen","Nineteen"]
            tens = ["","","Twenty","Thirty","Forty","Fifty","Sixty","Seventy","Eighty","Ninety"]
            if x < 20: return ones[x]
            if x < 100: return tens[x//10] + ("" if x%10==0 else " " + ones[x%10])
            if x < 1000: return ones[x//100] + " Hundred" + ("" if x%100==0 else " " + w(x%100))
            if x < 100000: return w(x//1000) + " Thousand" + ("" if x%1000==0 else " " + w(x%1000))
            if x < 10000000: return w(x//100000) + " Lakh" + ("" if x%100000==0 else " " + w(x%100000))
            return w(x//10000000) + " Crore" + ("" if x%10000000==0 else " " + w(x%10000000))
        s = f"{w(r)} Rupees"
        if p: s += f" and {w(p)} Paise"
        return (s + " only").upper().replace(" AND ", " ")
    except Exception:
        return "RUPEES ONLY"

def _b64(s: str) -> str:
    return base64.b64encode(s.encode("utf-8")).decode("utf-8")

def get_row_management_js_base64():
    """
    Loads invoice_row_management.js (or static/…) and inlines it into the page.
    Falls back to a no-op if missing.
    """
    try:
        here = os.path.dirname(__file__)
        for p in [
            os.path.join(here, "static", "invoice_row_management.js"),
            os.path.join(here, "invoice_row_management.js"),
        ]:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    return _b64(f.read())
    except Exception:
        pass
    return _b64("window.InvoiceRowManager={addRow(){},deleteRow(){},addBillRun(){},deleteBillRun(){},captureAndSendData(){}};")

# --- Router API used by the rest of the app ---

def get_template_options():
    return ["Siva Sakthi GTA", "Siva Sakthi Freight Bill"]

def render_invoice_html_template(invoice_data, template: str = "Siva Sakthi GTA") -> str:
    """
    Public entry used by UI/exports. Keeps behavior unchanged.
    """
    from templates.tax_invoice_template import render_tax_invoice
    from templates.bill_invoice_template import render_freight_bill

    inv = calculate_invoice_totals(invoice_data or {})
    if template == "Siva Sakthi Freight Bill":
        return render_freight_bill(inv)  # bill invoice
    return render_tax_invoice(inv)       # tax invoice
