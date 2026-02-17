from __future__ import annotations
import html, json
from templates.invoice_templates import _fmt, _amount_in_words, get_row_management_js_base64

# Precise, explicit formatters
def _fmt0(x) -> str:
    try:
        v = float(x or 0)
    except Exception:
        v = 0.0
    return f"{v:,.0f}"

def _fmt2(x) -> str:
    try:
        v = float(x or 0)
    except Exception:
        v = 0.0
    return f"{v:,.2f}"

def render_tax_invoice(inv: dict) -> str:
    comp = inv.get("company_info") or {}
    bill = inv.get("billing_to") or {}

    # Use company_info from state (supports MongoDB loading)
    header_name    = comp.get("name", "Siva Sakthi Roadways")
    header_tagline = comp.get("tagline", "GOODS TRANSPORT AGENCY & WEIGH BRIDGE")
    header_addr    = comp.get("address", "# D-46, CMDA Truck Terminal Complex, Madhavaram, Chennai - 600 110")
    header_phone   = comp.get("phone", "044-2553 0165")
    header_mobile  = comp.get("mobile", "094453 84189")
    header_email   = comp.get("email", "sekars.ssr@gmail.com")

    invoice_no     = inv.get("invoice_number","")
    invoice_date   = inv.get("invoice_date","")
    reverse_charge = "YES" if inv.get("reverse_charge") else "NO"

    supply_mode    = inv.get("supply_mode", "Goods Transport Agency Service")
    supply_period  = inv.get("supply_period","")
    place_supply   = inv.get("place_of_supply","")

    supplier_gstin = comp.get("gstin","33ARMPS3396J2Z4")
    supplier_pan   = comp.get("pan","ARMPS3396J")
    state          = comp.get("state","Tamil Nadu")
    state_code     = comp.get("state_code","33")

    billed_to_title  = bill.get("client_name","")
    company_name     = bill.get("client_name","")
    company_address  = (bill.get("address","") or "").replace("\n","<br>")
    company_gstin    = bill.get("gstin","")
    company_state    = bill.get("state","")
    company_code     = bill.get("state_code","")
    purchase_order_no = bill.get("purchase_order_no","")
    spo_no           = bill.get("spo_no","")

    items = inv.get("items") or []
    subtotal          = float(inv.get("subtotal", 0.0) or 0.0)
    words_value       = subtotal

    cgst_r     = float(inv.get("cgst_rate",0) or 0)
    sgst_r     = float(inv.get("sgst_rate",0) or 0)
    igst_r     = float(inv.get("igst_rate",0) or 0)
    cgst_v     = float(inv.get("cgst_amount",0) or 0)
    sgst_v     = float(inv.get("sgst_amount",0) or 0)
    igst_v     = float(inv.get("igst_amount",0) or 0)
    total_with_tax = subtotal + cgst_v + sgst_v + igst_v
    amount_due = subtotal

    bank = (comp.get("bank") or {})
    bank_account = bank.get("account_no","11327915122")
    bank_name    = bank.get("name","STATE BANK OF INDIA")
    bank_ifsc    = bank.get("ifsc","SBIN0002814")
    bank_branch  = bank.get("branch","YERRAGUNTLA")

    js_b64 = get_row_management_js_base64()

    # Terms and Conditions from state (array of strings)
    tnc_list = inv.get("terms_and_conditions", [])
    if not tnc_list:  # Fallback to hardcoded defaults if empty
        tnc_list = [
            "Notification No 3/2017 dated 19/6/2017 GST is payable under Reverse charge by the Recipient of service.",
            "Interest @ 18% per annum will be charged on delayed payment of bills.",
            "All disputes are subject to Yerraguntla Jurisdiction only.",
            "This Invoice details will be uploaded in our GST Returns as applicable."
        ]
    
    # Build T&C HTML with auto-numbering (skip empty lines)
    tnc_html_lines = []
    for idx, line in enumerate(tnc_list, start=1):
        if line and line.strip():  # Only include non-empty lines
            tnc_html_lines.append(f"<div>{idx}. {html.escape(line)}</div>")
    tnc_html = "\n          ".join(tnc_html_lines)

    rows_html = []
    for i, r in enumerate(items):
        q = (r.get('quantity', 0) or 0)
        p = (r.get('unit_price', 0) or 0)
        try: q = float(q)
        except Exception: q = 0.0
        try: p = float(p)
        except Exception: p = 0.0
        line_precise = q * p
        taxable_display = round(line_precise)
        subtotal_display = line_precise

        rows_html.append(f"""
        <tr class="items-row" data-row-index="{i}">
          <td>{i+1}</td>
          <td class="item-desc"><span class="editable" contenteditable="true" data-field="items.{i}.description">{html.escape(str(r.get('description','')))}</span></td>
          <td><span class="editable" contenteditable="true" data-field="items.{i}.hsn_code">{html.escape(str(r.get('hsn_code','')))}</span></td>
          <td><span class="editable" contenteditable="true" data-field="items.{i}.uom">{html.escape(str(r.get('uom','')))}</span></td>
          <td><span class="editable numeric" contenteditable="true" data-field="items.{i}.quantity">{_fmt(r.get('quantity',0), True)}</span></td>
          <td><span class="editable numeric" contenteditable="true" data-field="items.{i}.unit_price">{_fmt(r.get('unit_price',0), True)}</span></td>
          <td>{_fmt0(taxable_display)}</td>
          <td><span class="editable" contenteditable="false" data-field="items.{i}.line_total">{_fmt2(subtotal_display)}</span></td>
        </tr>
        """)
    item_rows_html = "".join(rows_html)

    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Tax Invoice</title>
<style>
@page {{ size: A4; margin: 10mm; }}
body {{
  font-family: Arial, sans-serif; font-size: 9px; line-height: 1.25; color:#000;
  margin:0; padding:0; background:#f5f5f5;
}}
.invoice-container {{ max-width: 200mm; margin:0 auto; background:#fff; box-shadow:0 0 8px rgba(0,0,0,.08); box-sizing:border-box; padding:10mm; }}
.invoice-table {{ width:100%; border-collapse:collapse; border:0.5px solid #000; }}
.invoice-table td {{ border:0.5px solid #000; padding:4px 6px; vertical-align:top; }}
.company-header {{ text-align:center; padding:10px 8px; background:#fafafa; border-bottom:0.5px solid #000; }}
.company-name-header {{ font-weight:bold; font-size:18px; margin-bottom:3px; letter-spacing:.5px; }}
.company-tagline {{ font-size:9px; margin-bottom:5px; letter-spacing:.3px; }}
.company-contact {{ font-size:9px; line-height:1.4; }}

.invoice-title {{ text-align:center; font-weight:bold; font-size:12px; padding:8px; background:#efefef; }}
.header-left, .header-right {{ width:50%; padding:8px; }}
.header-row {{ margin-bottom:4px; }}
.header-label {{ display:inline-block; min-width:120px; }}

.company-table {{ width:100%; border-collapse:collapse; }}
.company-table td {{ border:0.5px solid #000; padding:4px 6px; }}
.company-label {{ font-weight:bold; width:80px; background:#f7f7f7; }}

.items-inner-table {{ width:100%; border-collapse:collapse; }}
.items-inner-table td {{ border:0.5px solid #000; padding:4px 6px; }}
.items-header {{ background:#ece6f7; font-weight:bold; text-align:center; }}
.items-row td {{ padding:7px 8px; text-align:center; }}
.item-desc {{ text-align:left; padding-left:8px; }}
.total-row {{ background:#f6f6f6; font-weight:bold; text-align:center; padding:6px 8px; }}
.total-label {{ text-align:right; padding-right:10px; }}

.words-section {{ width:55%; padding:8px; vertical-align:top; }}
.tax-section {{ width:45%; padding:8px; vertical-align:top; }}

.rcm-box {{ width: 100%; border-collapse: collapse; border: 0.6px solid #000; font-size: 9px; margin-top: 4px; }}
.rcm-box td {{ border: 0.6px solid #000; padding: 6px 6px; vertical-align: middle; }}
.rcm-box td:first-child {{ text-align: left; padding-left: 10px; }}
.rcm-box td:last-child  {{ text-align: right; padding-right: 10px; }}

.bank-section {{ width:55%; padding:8px; vertical-align:top; }}
.amounts-section {{ width:45%; padding:8px; vertical-align:top; }}

.terms-section {{ width:55%; padding:8px; vertical-align:top; }}
.signature-section {{ width:45%; padding:8px; text-align:center; vertical-align:top; }}
.editable {{ cursor:text; padding:2px 4px; border-radius:2px; display:inline-block; min-width:16px; }}
.editable.numeric {{ text-align:right; }}
.editable:hover {{ background:#e8f4fd; outline:1px solid #007acc; }}
.editable.editing {{ background:#fff; outline:2px solid #007acc; box-shadow:0 0 4px rgba(0,122,204,.3); }}

@media print {{
  body {{ background:#fff; }}
  .invoice-container {{ box-shadow:none; padding:0; }}
  .editable {{ padding:0; border-radius:0; display:inline; min-width:auto; cursor:auto; }}
  .editable:hover {{ background:transparent; outline:none; }}
  .editable.editing {{ background:transparent; outline:none; box-shadow:none; }}
}}
</style>
</head>
<body>
  <div class="invoice-container">
    <table class="invoice-table">
      <tr>
        <td colspan="2" class="company-header">
          <div class="company-name-header">{header_name}</div>
          <div class="company-tagline">{header_tagline}</div>
          <div class="company-contact">
            {header_addr}<br>
            Ph.: {header_phone} &nbsp; Mobile: {header_mobile} &nbsp; Email: {header_email}
          </div>
        </td>
      </tr>

      <tr><td colspan="2" style="text-align:right; padding:8px; font-size:10px;"><strong>Date:
        <span class="editable" contenteditable="true" data-field="invoice_date">{html.escape(str(invoice_date))}</span></strong></td></tr>

      <tr><td colspan="2" class="invoice-title">TAX INVOICE</td></tr>

      <tr>
        <td class="header-left">
          <div class="header-row"><span class="header-label">Reverse Charge</span>: <span class="editable" contenteditable="true" data-field="reverse_charge">{reverse_charge}</span></div>
          <div class="header-row"><span class="header-label">Invoice No.</span>: <span class="editable" contenteditable="true" data-field="invoice_number">{html.escape(str(invoice_no))}</span></div>
          <div class="header-row"><span class="header-label">Invoice Date</span>: <span class="editable" contenteditable="true" data-field="invoice_date">{html.escape(str(invoice_date))}</span></div>
        </td>
        <td class="header-right">
          <div class="header-row"><span class="header-label">Supply Mode</span>: <span class="editable" contenteditable="true" data-field="supply_mode">{html.escape(str(supply_mode))}</span></div>
          <div class="header-row"><span class="header-label">Period of Supply</span>: <span class="editable" contenteditable="true" data-field="supply_period">{html.escape(str(supply_period))}</span></div>
          <div class="header-row"><span class="header-label">Place of Supply</span>: <span class="editable" contenteditable="true" data-field="place_of_supply">{html.escape(str(place_supply))}</span></div>
          <div class="header-row"><span class="header-label">GSTIN No.</span>: <span class="editable" contenteditable="true" data-field="company_info.gstin">{html.escape(str(supplier_gstin))}</span></div>
          <div class="header-row"><span class="header-label">PAN No</span>: <span class="editable" contenteditable="true" data-field="company_info.pan">{html.escape(str(supplier_pan))}</span></div>
        </td>
      </tr>

      <tr>
        <td style="padding:6px 8px;">
          <strong>State</strong>:
          <span class="editable" contenteditable="true" data-field="company_info.state">{html.escape(str(state))}</span>
          &nbsp;&nbsp;
          <strong>State Code</strong>:
          <span class="editable" contenteditable="true" data-field="company_info.state_code">{html.escape(str(state_code))}</span>
        </td>
        <td style="padding:6px 8px;">
          <strong>Billed to: <span class="editable" contenteditable="true" data-field="billing_to.client_name">{html.escape(str(billed_to_title))}</span></strong>
        </td>
      </tr>

      <tr>
        <td colspan="2" style="padding:0;">
          <table class="company-table">
            <tr><td class="company-label">Name</td><td colspan="3"><span class="editable" contenteditable="true" data-field="billing_to.client_name">{html.escape(str(company_name))}</span></td></tr>
            <tr><td class="company-label">Address</td><td colspan="3"><span class="editable" contenteditable="true" data-field="billing_to.address">{company_address}</span></td></tr>
            <tr><td class="company-label">GSTIN</td><td colspan="3"><span class="editable" contenteditable="true" data-field="billing_to.gstin">{html.escape(str(company_gstin))}</span></td></tr>
            <tr><td class="company-label">State</td><td><span class="editable" contenteditable="true" data-field="billing_to.state">{html.escape(str(company_state))}</span></td><td class="company-label">Code</td><td><span class="editable" contenteditable="true" data-field="billing_to.state_code">{html.escape(str(company_code))}</span></td></tr>
          </table>
        </td>
      </tr>

      <tr>
        <td colspan="2" style="padding:4px 8px; border-top:1px solid #000;">
          <strong>PURCHASE ORDER NO:</strong>
          <span class="editable" contenteditable="true" data-field="billing_to.purchase_order_no">{html.escape(str(purchase_order_no))}</span>
          <span style="float:right;">
            <strong>SPO NO:</strong>
            <span class="editable" contenteditable="true" data-field="billing_to.spo_no">{html.escape(str(spo_no))}</span>
          </span>
        </td>
      </tr>

      <tr>
        <td colspan="2" style="padding:0;">
          <table class="items-inner-table">
        </td>
      </tr>

      <tr>
        <td colspan="2" style="padding:0;">
          <table class="items-inner-table">
            <thead>
              <tr>
                <td class="items-header" style="width:4%;">S.<br>No.</td>
                <td class="items-header" style="width:36%;">Name of Product /<br>Service</td>
                <td class="items-header" style="width:8%;">HSN SAC</td>
                <td class="items-header" style="width:6%;">UoM</td>
                <td class="items-header" style="width:10%;">Qty</td>
                <td class="items-header" style="width:10%;">Rate</td>
                <td class="items-header" style="width:12%;">Taxable Value</td>
                <td class="items-header" style="width:14%;">Subtotal</td>
              </tr>
            </thead>
            <tbody id="item-rows">
              {item_rows_html}
            </tbody>
            <tfoot>
              <tr class="total-row">
                <td colspan="6" class="total-label">Total :</td>
                <td></td>
                <!-- integer display -->
                <td class="tax-subtotal">{_fmt0(subtotal)}</td>
              </tr>
            </tfoot>
          </table>
        </td>
      </tr>

      <tr>
        <td class="words-section">
          <div style="font-weight:bold; margin-bottom:6px;">Total Invoice Amount In Words:</div>
          <div class="tax-amount-words">{_amount_in_words(float(words_value))}</div>
        </td>
        <td class="tax-section">
          <table class="rcm-box">
            <!-- integer display for taxable value under RCM -->
            <tr><td>Taxable Value Under RCM for Service</td><td class="tax-rcm-subtotal">{_fmt0(subtotal)}</td></tr>
            <tr><td>CGST@<span class="editable" contenteditable="true" data-field="cgst_rate">{_fmt2(cgst_r)}</span>%:</td><td class="tax-cgst-amount">{_fmt2(cgst_v)}</td></tr>
            <tr><td>SGST@<span class="editable" contenteditable="true" data-field="sgst_rate">{_fmt2(sgst_r)}</span>%:</td><td class="tax-sgst-amount">{_fmt2(sgst_v)}</td></tr>
            <tr><td>IGST@<span class="editable" contenteditable="true" data-field="igst_rate">{_fmt2(igst_r)}</span>%:</td><td class="tax-igst-amount">{_fmt2(igst_v)}</td></tr>
          </table>
        </td>
      </tr>

      <!-- Bank Details + Amounts -->
      <tr>
        <td class="bank-section">
          <div><strong>Bank Details :</strong></div>
          <div>• Bank Account Number&nbsp;&nbsp;: {html.escape(str(bank_account))}</div>
          <div>• Bank Name&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: {html.escape(str(bank_name))}</div>
          <div>&nbsp;&nbsp;Bank IFSC CODE&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: {html.escape(str(bank_ifsc))}</div>
          <div>• Branch&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: {html.escape(str(bank_branch))}</div>
        </td>
        <td class="amounts-section">
          <table class="rcm-box">
            <tr>
              <td>Total Invoice Amount including Tax under RCM</td>
              <td class="tax-grand-total">{_fmt0(total_with_tax)}</td>
            </tr>
            <tr>
              <td>Amount due from {html.escape(str(company_name))},</td>
              <td>{_fmt0(amount_due)}</td>
            </tr>
          </table>
        </td>
      </tr>

      <tr>
        <td class="terms-section">
          <div style="font-weight:bold; margin-bottom:6px;">Terms and Conditions :</div>
          {tnc_html}
        </td>
        <td class="signature-section">
          <div style="text-align:left; margin-bottom:12px;">Certified that the particulars given above are true and correct.<br><b>For: {header_name}</b></div>
          <div>Proprietor</div>
        </td>
      </tr>
    </table>
  </div>

  <div id="invoice_json" data-json='{json.dumps(inv).replace("'", "&#39;").replace("</", "</")}' style="display:none"></div>
  <script>try{{eval(atob("{js_b64}"));}}catch(e){{}}</script>
  <script>
    document.addEventListener('DOMContentLoaded', function() {{
      const debounce = (fn, t=250) => {{ let h; return (...a)=>{{clearTimeout(h); h=setTimeout(()=>fn(...a),t);}}; }};
      const send = () => {{
        if (window.InvoiceRowManager && window.InvoiceRowManager.captureAndSendData) {{
          window.InvoiceRowManager.captureAndSendData();
        }}
      }};
      const debSend = debounce(send, 250);
      document.querySelectorAll('.editable[contenteditable="true"]').forEach(el => {{
        if (el.dataset.bound) return; el.dataset.bound = "1";
        el.addEventListener('input', debSend);
        el.addEventListener('blur',  () => setTimeout(send, 50));
        el.addEventListener('keydown', (e) => {{ if (e.key === 'Enter') {{ e.preventDefault(); el.blur(); }} }});
      }});
    }});
  </script>
</body></html>"""
