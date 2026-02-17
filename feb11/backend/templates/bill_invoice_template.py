# bill_invoice_template.py
import html, json
from templates.invoice_templates import _fmt, _amount_in_words, get_row_management_js_base64

def render_freight_bill(inv: dict) -> str:
    # Try freight_bill.company_info first (Bill-specific), fallback to top-level company_info
    comp = inv.get("freight_bill", {}).get("company_info") or inv.get("company_info") or {}
    fb   = inv.get("freight_bill") or {}

    # Header (dynamic from company_info)
    header_name = f"{comp.get('name', '')}," if comp.get('name') else ''
    header_addr1 = comp.get('tagline', '')
    
    # Split address into 2 lines
    address_full = comp.get('address', '')
    address_parts = [p.strip() for p in address_full.replace('\n', ',').split(',') if p.strip()]
    header_addr2 = address_parts[0] if len(address_parts) > 0 else ''
    header_addr3 = ', '.join(address_parts[1:]) if len(address_parts) > 1 else ''
    
    # Phone and mobile with prefixes
    header_phone = f"PH: {comp.get('phone', '')}" if comp.get('phone') else ''
    header_mobile = f"Mobile No: {comp.get('mobile', '')}" if comp.get('mobile') else ''

    
    # PAN - try company_info first, fallback to freight_bill
    pan_no = comp.get('pan', fb.get("pan_no", ""))

    # Top meta
    series_no = fb.get("series_no", "Freight Bill No.")
    bill_date = fb.get("bill_date", inv.get("invoice_date",""))
    po_no     = fb.get("po_no", "")

    # Party
    to_party  = fb.get("to_party") or {"name":"Zuari Cement Ltd,", "address":"CGU - Attipattu,\nChennai."}
    to_name   = to_party.get("name","")
    to_addr   = (to_party.get("address","") or "").replace("\n","<br>")

    # Summary line
    summary = fb.get("summary", "")

    # Runs
    runs = fb.get("runs") or []
    subtotal     = 0.0
    dc_qty_total = 0.0
    gr_qty_total = 0.0

    rows_html = []
    for i, r in enumerate(runs):
        d        = str(r.get("date",""))
        trk      = str(r.get("truck_no",""))
        lr       = str(r.get("lr_no",""))
        dc_qty   = float(r.get("dc_qty_mt", 0) or 0)
        gr_qty   = float(r.get("gr_qty_mt", 0) or 0)
        rate     = float(r.get("rate", 0) or 0)
        line     = float(r.get("line_total", gr_qty * rate))

        dc_qty_total += dc_qty
        gr_qty_total += gr_qty
        subtotal     += line

        rows_html.append(f"""
        <tr class="freight-row" data-row-index="{i}">
          <td>{i+1}</td>
          <td><span class="editable" contenteditable="true" data-field="freight_bill.runs.{i}.date">{html.escape(d)}</span></td>
          <td><span class="editable" contenteditable="true" data-field="freight_bill.runs.{i}.truck_no">{html.escape(trk)}</span></td>
          <td><span class="editable" contenteditable="true" data-field="freight_bill.runs.{i}.lr_no">{html.escape(lr)}</span></td>
          <td><span class="editable numeric" contenteditable="true" data-field="freight_bill.runs.{i}.dc_qty_mt">{_fmt(dc_qty, True)}</span></td>
          <td><span class="editable numeric" contenteditable="true" data-field="freight_bill.runs.{i}.gr_qty_mt">{_fmt(gr_qty, True)}</span></td>
          <td><span class="editable numeric" contenteditable="true" data-field="freight_bill.runs.{i}.rate">{_fmt(rate, False)}</span></td>
          <td class="line-total"><span class="numeric calculated">{_fmt(line)}</span></td>
        </tr>""")

    run_rows = "".join(rows_html)
    words_value = subtotal
    js_b64 = get_row_management_js_base64()

    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Freight Bill</title>
<style>
@page {{ size: A4; margin: 10mm; }}
body {{ font-family: Arial, sans-serif; font-size: 11px; line-height: 1.3; color:#000; background:#f5f5f5; margin:0; }}
.bill-container {{ max-width: 200mm; margin:0 auto; background:#fff; box-shadow:0 0 8px rgba(0,0,0,.08); padding:10mm; box-sizing:border-box; }}
.bill-table {{ width:100%; border-collapse:collapse; border:1px solid #000; }}
.bill-table td {{ border:1px solid #000; padding:6px 8px; vertical-align:top; }}

/* Header */
.company-header {{ text-align:left; padding:8px; border-bottom:1px solid #000; }}
.company-name-header {{ font-weight:bold; font-size:16px; margin-bottom:2px; }}
.header-row {{ display:flex; justify-content:space-between; align-items:center; }}
.header-left {{ flex:1; }}
.header-right {{ text-align:right; font-weight:bold; }}

/* Client section */
.to-section {{ padding:8px; border-bottom:1px solid #000; }}
.to-label {{ font-weight:bold; margin-bottom:4px; }}

/* Bill info */
.bill-info {{ padding:8px; border-bottom:1px solid #000; }}
.bill-info-row {{ display:flex; justify-content:space-between; margin-bottom:2px; }}

/* Summary */
.summary-section {{ padding:8px; border-bottom:1px solid #000; font-weight:bold; text-align:center; }}

/* Table */
.runs-table {{ width:100%; border-collapse:collapse; margin-top:0; }}
.runs-table td {{ border:1px solid #000; padding:6px 6px; }}
.runs-head td {{ background:#ece6f7; font-weight:bold; text-align:center; font-size:10px; }}
.freight-row td {{ text-align:center; }}
.freight-row td:nth-child(2) {{ white-space:nowrap; }}

.total-row td {{ background:#f6f6f6; font-weight:bold; }}
.total-label {{ text-align:right; padding-right:10px; }}

/* Footer */
.footer-section {{ margin-top:10px; padding:8px; border:1px solid #000; }}
.amount-words {{ font-weight:bold; text-align:center; padding:10px; }}
.signature-section {{ text-align:right; padding:20px 10px; }}

.editable {{ cursor:text; padding:2px 4px; border-radius:2px; display:inline-block; min-width:16px; background:#f0f0f0; transition:background-color 0.2s; }}
.editable.numeric {{ text-align:right; }}
.editable:hover {{ background:#e0e0e0; outline:1px solid #999; }}
.editable[contenteditable="true"]:focus {{ background:#fff3cd; outline:2px solid #ffc107; box-shadow:0 0 4px rgba(255,193,7,.5); }}

.calculated {{ background:#fafafa !important; color:#666; font-weight:500; cursor:default !important; display:inline-block; padding:2px 4px; border-radius:2px; }}
.calculated:hover {{ background:#fafafa !important; outline:none !important; }}

@media print {{
  body {{ background:#fff; }}
  .bill-container {{ box-shadow:none; padding:0; }}
  .editable {{ padding:0; border-radius:0; display:inline; min-width:auto; cursor:auto; background:transparent; }}
  .editable:hover {{ background:transparent; outline:none; }}
  .editable[contenteditable="true"]:focus {{ background:transparent; outline:none; box-shadow:none; }}
  .calculated {{ background:transparent !important; color:#000; font-weight:normal; }}
}}
</style>
</head>
<body>
<div class="bill-container">
  <table class="bill-table">
    <!-- Header -->
    <tr>
      <td colspan="8" class="company-header">
        <div class="header-row">
          <div class="header-left">
            <div class="company-name-header">{header_name}</div>
            <div>{header_addr1}</div>
            <div>{header_addr2}</div>
            <div>{header_addr3}</div>
            <div>{header_phone}</div>
            <div>{header_mobile}</div>
          </div>
          <div class="header-right">
            PAN NO. <span class="editable" contenteditable="true" data-field="freight_bill.pan_no">{html.escape(pan_no)}</span>
          </div>
        </div>
      </td>
    </tr>
    
    <!-- To Section -->
    <tr>
      <td colspan="8" class="to-section">
        <div class="to-label">To</div>
        <div><span class="editable" contenteditable="true" data-field="freight_bill.to_party.name">{html.escape(to_name)}</span></div>
        <div><span class="editable" contenteditable="true" data-field="freight_bill.to_party.address">{to_addr}</span></div>
      </td>
    </tr>
    
    <!-- Bill Info -->
    <tr>
      <td colspan="8" class="bill-info">
        <div class="bill-info-row">
          <div><strong>Freight Bill</strong> <span class="editable" contenteditable="true" data-field="freight_bill.series_no">{html.escape(series_no)}</span></div>
          <div><strong>Dt</strong> <span class="editable" contenteditable="true" data-field="freight_bill.bill_date">{html.escape(bill_date)}</span></div>
          <div><strong>P.O No :</strong> <span class="editable" contenteditable="true" data-field="freight_bill.po_no">{html.escape(po_no)}</span></div>
        </div>
      </td>
    </tr>
    
    <!-- Summary -->
    <tr>
      <td colspan="8" class="summary-section">
        <span class="editable" contenteditable="true" data-field="freight_bill.summary">{html.escape(summary)}</span>
      </td>
    </tr>
    
    <!-- Table Header -->
    <tr class="runs-head">
      <td>S.No</td>
      <td>Date</td>
      <td>Truck No</td>
      <td>LR No</td>
      <td>D.C Quan in MT</td>
      <td>GR Quan in MT</td>
      <td>Rate/MT</td>
      <td>Subtotal</td>
    </tr>
    
    <!-- Runs -->
    {run_rows}
    
    <!-- Totals -->
    <tr class="total-row">
      <td colspan="4" class="total-label"></td>
      <td class="numeric dc-total">{_fmt(dc_qty_total, True)}</td>
      <td class="numeric gr-total">{_fmt(gr_qty_total, True)}</td>
      <td></td>
      <td class="numeric subtotal-total">{_fmt(subtotal)}</td>
    </tr>
  </table>
  
  <!-- Amount in Words -->
  <div class="footer-section">
    <div class="amount-words">
      Amount in Words : <span class="amount-words-text">{_amount_in_words(words_value)}</span>
    </div>
  </div>
  
  <!-- Signature -->
  <div class="signature-section">
    <div style="margin-top:40px; border-top:1px solid #000; display:inline-block; padding-top:5px;">
      For {comp.get('name', 'Siva Sakthi Roadways')}
    </div>
    <div style="margin-top:10px;">
      <strong>Authorised Signatory</strong>
    </div>
  </div>
</div>

<script src="data:text/javascript;base64,{js_b64}"></script>
<!-- Calculations handled by invoice_row_management.js -->
</body>
</html>"""

