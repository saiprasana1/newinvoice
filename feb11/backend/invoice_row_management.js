// === invoice_row_management.js ===
// Inline editing + DOM→JSON bridge + instant client-side recalculation

window.InvoiceRowManager = (() => {
  const api = {};
  let mo = null;
  let isCapturing = false;

  // -----------------------------
  // Helpers
  // -----------------------------
  const qs = (sel, scope = document) => scope.querySelector(sel);
  const qsa = (sel, scope = document) => Array.from(scope.querySelectorAll(sel));
  const debounce = (fn, t = 200) => {
    let h;
    return (...a) => {
      clearTimeout(h);
      h = setTimeout(() => fn(...a), t);
    };
  };

  const parseNum = (s) => {
    if (typeof s === "number") return Number.isFinite(s) ? s : 0;
    const v = parseFloat(String(s || "").replace(/[^\d.-]/g, ""));
    return Number.isFinite(v) ? v : 0;
  };

  const fmt = (n, decimals = 2, stripTrailingZero = false) => {
    const num = Number.isFinite(n) ? n : 0;
    let formatted = num.toLocaleString(undefined, {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
    if (stripTrailingZero) {
      formatted = formatted.replace(/(\.\.0+|(?<=\.\d*[1-9])0+)$/, ""); // remove .00
    }
    return formatted;
  };

  const numberToWords = (num) => {
    if (!num || num === 0) return "ZERO RUPEES ONLY";
    
    const ones = ["", "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE"];
    const teens = ["TEN", "ELEVEN", "TWELVE", "THIRTEEN", "FOURTEEN", "FIFTEEN", "SIXTEEN", "SEVENTEEN", "EIGHTEEN", "NINETEEN"];
    const tens = ["", "", "TWENTY", "THIRTY", "FORTY", "FIFTY", "SIXTY", "SEVENTY", "EIGHTY", "NINETY"];
    const thousands = ["", "THOUSAND", "LAKH", "CRORE"];
    
    const convertLessThanThousand = (n) => {
      if (n === 0) return "";
      if (n < 10) return ones[n];
      if (n < 20) return teens[n - 10];
      if (n < 100) {
        const ten = Math.floor(n / 10);
        const one = n % 10;
        return tens[ten] + (one > 0 ? " " + ones[one] : "");
      }
      const hundred = Math.floor(n / 100);
      const remainder = n % 100;
      return ones[hundred] + " HUNDRED" + (remainder > 0 ? " " + convertLessThanThousand(remainder) : "");
    };
    
    const convertIndianNumbering = (n) => {
      if (n === 0) return "ZERO";
      
      const crores = Math.floor(n / 10000000);
      n %= 10000000;
      const lakhs = Math.floor(n / 100000);
      n %= 100000;
      const thousands = Math.floor(n / 1000);
      n %= 1000;
      const hundreds = n;
      
      let result = "";
      if (crores > 0) result += convertLessThanThousand(crores) + " CRORE ";
      if (lakhs > 0) result += convertLessThanThousand(lakhs) + " LAKH ";
      if (thousands > 0) result += convertLessThanThousand(thousands) + " THOUSAND ";
      if (hundreds > 0) result += convertLessThanThousand(hundreds);
      
      return result.trim();
    };
    
    const rupees = Math.floor(num);
    const paise = Math.round((num - rupees) * 100);
    
    let words = convertIndianNumbering(rupees) + " RUPEES";
    if (paise > 0) {
      words += " " + convertIndianNumbering(paise) + " PAISE";
    }
    words += " ONLY";
    
    return words;
  };

  const setByPath = (obj, path, value) => {
    const parts = (path || "").split(".").filter(Boolean);
    if (!parts.length) return;
    let cur = obj;
    for (let i = 0; i < parts.length - 1; i++) {
      const key = parts[i];
      const next = parts[i + 1];
      if (/^\d+$/.test(next)) {
        if (!Array.isArray(cur[key])) cur[key] = [];
        const idx = parseInt(next, 10);
        while (cur[key].length <= idx) cur[key].push({});
        cur = cur[key][idx];
        i++;
      } else {
        if (typeof cur[key] !== "object" || cur[key] == null) cur[key] = {};
        cur = cur[key];
      }
    }
    cur[parts[parts.length - 1]] = value;
  };

  const isActiveEditable = () => {
    const ae = document.activeElement;
    return !!ae?.closest('.editable[contenteditable="true"]');
  };

  const getInvoiceFromDOM = () => {
    const data = {};
    qsa(".editable[data-field]").forEach((el) => {
      const path = el.dataset.field;
      if (!path) return;
      const isNumeric = el.classList.contains("numeric");
      let val = el.textContent.trim();
      setByPath(data, path, isNumeric ? parseNum(val) : val);
    });
    return data;
  };

  // -----------------------------
  // TAX INVOICE TOTALS
  // -----------------------------
  const recalcTaxTotals = () => {
    const tbody = qs(".items-inner-table tbody");
    if (!tbody) return;

    let subtotal = 0;
    qsa("tr.items-row", tbody).forEach((row) => {
      const qty = parseNum(row.querySelector('[data-field$=".quantity"]')?.textContent);
      const rate = parseNum(row.querySelector('[data-field$=".unit_price"]')?.textContent);
      const line = qty * rate;
      const taxableRounded = Math.round(line);
      subtotal += taxableRounded;

      const tds = qsa("td", row);
      if (tds.length >= 8) {
        tds[6].textContent = fmt(taxableRounded, 0);
        const subSpan = tds[7].querySelector('[data-field$=".line_total"]');
        if (subSpan) subSpan.textContent = fmt(line, 2);
        else tds[7].textContent = fmt(line, 2);
      }
    });

    const cgstRate = parseNum(qs('[data-field="cgst_rate"]')?.textContent);
    const sgstRate = parseNum(qs('[data-field="sgst_rate"]')?.textContent);
    const igstRate = parseNum(qs('[data-field="igst_rate"]')?.textContent);

    const cgst = subtotal * (cgstRate / 100);
    const sgst = subtotal * (sgstRate / 100);
    const igst = subtotal * (igstRate / 100);
    const grandTotal = subtotal + cgst + sgst + igst;

    // Bottom Total (integer with no .00)
    const elSub = qs('[data-field="subtotal"]');
    if (elSub) elSub.textContent = fmt(subtotal, 0, true);

    // Taxes and final total with 2 decimals
    const updateCell = (field, val) => {
      const el = qs(`[data-field="${field}"]`);
      if (el) el.textContent = fmt(val, 2);
    };
    updateCell("cgst_amount", cgst);
    updateCell("sgst_amount", sgst);
    updateCell("igst_amount", igst);
    updateCell("total", grandTotal);
  };

  // -----------------------------
  // FREIGHT BILL TOTALS
  // -----------------------------
  const recalcFreightTotals = () => {
    const table = qs(".freight-runs-table");
    if (!table) return;
    const tbody = table.tBodies[0] || table;
    let subtotal = 0, dcTotal = 0, grTotal = 0;

    qsa("tr.freight-row", tbody).forEach((row) => {
      const dc = parseNum(row.querySelector('[data-field$=".dc_qty_mt"]')?.textContent);
      const gr = parseNum(row.querySelector('[data-field$=".gr_qty_mt"]')?.textContent);
      const rate = parseNum(row.querySelector('[data-field$=".rate"]')?.textContent);
      const line = gr * rate;
      dcTotal += dc; grTotal += gr; subtotal += line;

      const lt = row.querySelector('[data-field$=".line_total"]');
      if (lt) lt.textContent = fmt(line, 2);
    });

    const setText = (sel, val, d = 2) => {
      const el = qs(sel);
      if (el) el.textContent = fmt(val, d);
    };
    setText(".dc-total", dcTotal, 2);
    setText(".gr-total", grTotal, 2);
    setText(".subtotal-total", subtotal, 2);
    
    // Update amount in words
    const amountWordsEl = qs(".amount-words-text");
    if (amountWordsEl) {
      amountWordsEl.textContent = numberToWords(subtotal);
    }
  };

  const recalcPreviewTotals = () => {
    recalcTaxTotals();
    recalcFreightTotals();
  };

  // -----------------------------
  // SYNC
  // -----------------------------
  api.captureAndSendData = () => {
    if (isCapturing) return;
    isCapturing = true;
    try {
      const data = getInvoiceFromDOM();
      recalcPreviewTotals();
      const root = (window.gradioApp && window.gradioApp()) || document;
      const tb =
        root.querySelector("#edited_invoice_data textarea") ||
        root.querySelector('textarea[aria-label="edited_invoice_data"]');
      if (tb) {
        const next = JSON.stringify(data);
        if (tb.value !== next) {
          tb.value = next;
          tb.dispatchEvent(new Event("input", { bubbles: true }));
          tb.dispatchEvent(new Event("change", { bubbles: true }));
        }
      }
    } finally {
      isCapturing = false;
    }
  };

  // -----------------------------
  // EDITABLE BINDINGS
  // -----------------------------
  const makeEditable = (el) => {
    if (el.getAttribute("contenteditable") !== "true" || el.dataset.listenerAttached) return;
    el.dataset.listenerAttached = "1";
    const debRecalc = debounce(recalcPreviewTotals, 120);
    el.addEventListener("input", debRecalc);
    el.addEventListener("blur", () => api.captureAndSendData());
    el.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        el.blur();
      }
    });
  };

  const bindAllEditable = () => qsa(".editable[data-field]").forEach(makeEditable);

  // -----------------------------
  // INIT
  // -----------------------------
  api.init = () => {
    bindAllEditable();
    if (mo) mo.disconnect();
    mo = new MutationObserver(() =>
      setTimeout(() => {
        if (isActiveEditable()) return;
        bindAllEditable();
        recalcPreviewTotals();
      }, 50)
    );
    mo.observe(document.body, { childList: true, subtree: true });
    recalcPreviewTotals();
  };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", api.init);
  else api.init();

  return api;
})();
