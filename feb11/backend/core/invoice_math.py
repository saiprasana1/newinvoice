import math
from typing import Dict, Any, List


# -----------------------------
# Helpers
# -----------------------------
def _to_num(x, default: float = 0.0) -> float:
    """Coerce string/float/int to float safely."""
    try:
        if isinstance(x, (int, float)):
            return float(x)
        s = str(x).strip()
        if not s:
            return float(default)
        if s.startswith("$"):
            s = s[1:]
        s = s.replace(",", "")
        return float(s)
    except Exception:
        try:
            return float(x)
        except Exception:
            return float(default)


def _finite(n: float) -> float:
    try:
        return n if math.isfinite(n) else 0.0
    except Exception:
        return 0.0


def _fmt_whole_or_float(val: float):
    """Return int if whole else float (useful for quantity display downstream)."""
    try:
        return int(val) if float(val).is_integer() else float(val)
    except Exception:
        return float(val) if isinstance(val, (int, float)) else 0.0


# -----------------------------
# Freight Bill math
# -----------------------------
def _calculate_freight_bill(inv: Dict[str, Any]) -> None:
    """
    Normalizes and computes math for the Freight Bill section, aligned with UI/schema:

      For each run:
        line_total = gr_qty_mt * rate

      Aggregates:
        dc_total   = sum(dc_qty_mt)
        gr_total   = sum(gr_qty_mt)
        subtotal   = sum(line_total)
        total      = subtotal

    Mutates inv["freight_bill"] in place.
    """
    fb = inv.get("freight_bill")
    if not isinstance(fb, dict):
        return

    runs_in = fb.get("runs") or []
    if not isinstance(runs_in, list):
        runs_in = []

    runs_out: List[Dict[str, Any]] = []
    subtotal = 0.0
    dc_total = 0.0
    gr_total = 0.0

    for r in runs_in:
        if not isinstance(r, dict):
            continue

        dc = _finite(_to_num(r.get("dc_qty_mt", 0)))
        gr = _finite(_to_num(r.get("gr_qty_mt", 0)))
        rate = _finite(_to_num(r.get("rate", 0)))

        line = gr * rate
        dc_total += dc
        gr_total += gr
        subtotal += line

        runs_out.append(
            {
                "date": r.get("date", ""),
                "truck_no": r.get("truck_no", ""),
                "lr_no": r.get("lr_no", ""),
                "dc_qty_mt": _fmt_whole_or_float(dc),
                "gr_qty_mt": _fmt_whole_or_float(gr),
                "rate": _fmt_whole_or_float(rate),
                "line_total": line,
            }
        )

    fb["runs"] = runs_out
    fb["dc_total"] = dc_total
    fb["gr_total"] = gr_total
    fb["subtotal"] = subtotal
    fb["total"] = subtotal
    inv["freight_bill"] = fb


# -----------------------------
# Tax invoice math (items + GST split)
# -----------------------------
def calculate_invoice_totals(invoice_data: dict) -> dict:
    """
    Computes normalized item math and splits GST as:

      For each item:
        line_total    = quantity * unit_price      (2-dec, used for 'Subtotal' column per row)
        taxable_value = round(line_total)          (0-dec, shown in 'Taxable Value' column)

      Aggregates:
        subtotal   = sum(taxable_value)            <-- CHANGED: sum of Taxable Value column
        discount
        sub_less   = max(0, subtotal - discount)
        CGST       = cgst_rate% of sub_less
        SGST       = sgst_rate% of sub_less
        IGST       = igst_rate% of sub_less
        total      = sub_less + CGST + SGST + IGST + shipping_handling

    Also computes Freight Bill math if present in invoice_data["freight_bill"].
    Returns an updated invoice_data dict with all totals.
    """
    if not isinstance(invoice_data, dict):
        invoice_data = {}

    # ---- Items (Tax invoice) ----
    items = invoice_data.get("items", [])
    if not isinstance(items, list):
        items = []
    valid_items = []

    subtotal_from_taxable = 0.0
    for it in items:
        if not isinstance(it, dict):
            continue
        q = _finite(_to_num(it.get("quantity", 0)))
        p = _finite(_to_num(it.get("unit_price", 0)))

        # Normalize stored values
        it["quantity"] = _fmt_whole_or_float(q)
        it["unit_price"] = _fmt_whole_or_float(p)

        # Per-row math
        line_precise = q * p                   # used for per-row "Subtotal" (2 dec)
        taxable_val  = round(line_precise)     # used for "Taxable Value" (0 dec)

        # Persist both so UI can render both columns consistently
        it["line_total"] = line_precise        # 2-dec display (template formats)
        it["taxable_value"] = taxable_val      # 0-dec display helper (optional)

        subtotal_from_taxable += taxable_val
        valid_items.append(it)

    invoice_data["items"] = valid_items

    # ---- Discounts & shipping ----
    discount = _finite(_to_num(invoice_data.get("discount", 0)))
    shipping = _finite(_to_num(invoice_data.get("shipping_handling", 0)))
    sub_less = max(0.0, subtotal_from_taxable - discount)

    # ---- GST rates (editable, with defaults) ----
    cgst_r = _finite(_to_num(invoice_data.get("cgst_rate", 6.0)))
    sgst_r = _finite(_to_num(invoice_data.get("sgst_rate", 6.0)))
    igst_r = _finite(_to_num(invoice_data.get("igst_rate", 5.0)))

    # ---- GST amounts ----
    cgst_v = sub_less * (cgst_r / 100.0)
    sgst_v = sub_less * (sgst_r / 100.0)
    igst_v = sub_less * (igst_r / 100.0)

    # ---- Total ----
    total = sub_less + cgst_v + sgst_v + igst_v + shipping

    # ---- Update tax-invoice totals ----
    invoice_data.update(
        {
            "subtotal": subtotal_from_taxable,      # <-- CHANGED
            "discount": discount,
            "shipping_handling": shipping,
            "cgst_rate": cgst_r,
            "sgst_rate": sgst_r,
            "igst_rate": igst_r,
            "cgst_amount": cgst_v,
            "sgst_amount": sgst_v,
            "igst_amount": igst_v,
            "total": total,
        }
    )

    # ---- Freight Bill math (if present) ----
    try:
        _calculate_freight_bill(invoice_data)
    except Exception:
        # Never let freight-bill math break main invoice calculations
        pass

    return invoice_data
