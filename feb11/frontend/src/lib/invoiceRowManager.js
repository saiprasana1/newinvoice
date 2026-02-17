export class InvoiceRowManager {
  constructor({ container, onDataChange, onDelete, invoiceType = 'bill' }) {
    this.container = container;
    this.onDataChangeCallback = onDataChange;
    this.onDeleteCallback = onDelete || null;
    this.invoiceType = invoiceType;
    this.debounceTimer = null;
    this.observer = null;
    this.observerDebounceTimer = null;
    this.originalValues = new Map();
    this.delegatedListenersAttached = false;
  }

  parseNum(s) {
    if (typeof s === "number") return Number.isFinite(s) ? s : 0;
    const v = parseFloat(String(s || "").replace(/[^\d.-]/g, ""));
    return Number.isFinite(v) ? v : 0;
  }

  fmt(n, decimals = 2) {
    const num = Number.isFinite(n) ? n : 0;
    return num.toLocaleString(undefined, {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  }

  fmtInt(n) {
    const num = Number.isFinite(n) ? Math.round(n) : 0;
    return num.toLocaleString(undefined, {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    });
  }

  numberToWords(num) {
    const n = this.parseNum(num);
    if (!n || n === 0) return "ZERO RUPEES ONLY";

    const ones = ["", "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE"];
    const teens = ["TEN", "ELEVEN", "TWELVE", "THIRTEEN", "FOURTEEN", "FIFTEEN", "SIXTEEN", "SEVENTEEN", "EIGHTEEN", "NINETEEN"];
    const tens = ["", "", "TWENTY", "THIRTY", "FORTY", "FIFTY", "SIXTY", "SEVENTY", "EIGHTY", "NINETY"];

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

    const rounded = Math.round(n);
    if (rounded < 1000) return convertLessThanThousand(rounded);
    if (rounded < 1000000) {
      const thousands = Math.floor(rounded / 1000);
      const remainder = rounded % 1000;
      return convertLessThanThousand(thousands) + " THOUSAND" + (remainder > 0 ? " " + convertLessThanThousand(remainder) : "");
    }
    return "AMOUNT TOO LARGE";
  }

  setByPath(obj, path, value) {
    const parts = path.split(".").filter(Boolean);
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
  }

  recalcFreightLineTotal(row) {
    if (!row) return;
    const grQtyEl = row.querySelector('[data-field$=".gr_qty_mt"]');
    const rateEl = row.querySelector('[data-field$=".rate"]');
    const lineTotalEl = row.querySelector('[data-field$=".line_total"]');
    if (!grQtyEl || !rateEl || !lineTotalEl) return;

    const lineTotal = this.parseNum(grQtyEl.textContent) * this.parseNum(rateEl.textContent);
    lineTotalEl.textContent = this.fmt(lineTotal, 2);
  }

  recalcFreightTotals() {
    if (!this.container) return;
    const rows = this.container.querySelectorAll("tr.freight-row");
    let subtotal = 0, dcTotal = 0, grTotal = 0;

    rows.forEach((row) => {
      const dcEl = row.querySelector('[data-field$=".dc_qty_mt"]');
      const grEl = row.querySelector('[data-field$=".gr_qty_mt"]');
      const rateEl = row.querySelector('[data-field$=".rate"]');
      if (dcEl && grEl && rateEl) {
        const dc = this.parseNum(dcEl.textContent);
        const gr = this.parseNum(grEl.textContent);
        const rate = this.parseNum(rateEl.textContent);
        dcTotal += dc;
        grTotal += gr;
        subtotal += gr * rate;
        this.recalcFreightLineTotal(row);
      }
    });

    const dcTotalEl = this.container.querySelector(".dc-total");
    const grTotalEl = this.container.querySelector(".gr-total");
    const subtotalEl = this.container.querySelector(".subtotal-total");
    const amountWordsEl = this.container.querySelector(".amount-words-text");
    if (dcTotalEl) dcTotalEl.textContent = this.fmt(dcTotal, 2);
    if (grTotalEl) grTotalEl.textContent = this.fmt(grTotal, 2);
    if (subtotalEl) subtotalEl.textContent = this.fmt(subtotal, 2);
    if (amountWordsEl) amountWordsEl.textContent = this.numberToWords(subtotal);
  }

  recalcTaxTotals() {
    if (!this.container) return;

    const rows = this.container.querySelectorAll("tr.items-row");
    let subtotal = 0;

    rows.forEach((row) => {
      const qtyEl = row.querySelector('[data-field$=".quantity"]');
      const priceEl = row.querySelector('[data-field$=".unit_price"]');
      const totalEl = row.querySelector('[data-field$=".line_total"]');
      if (qtyEl && priceEl) {
        const qty = this.parseNum(qtyEl.textContent);
        const price = this.parseNum(priceEl.textContent);
        const lineTotal = qty * price;
        subtotal += lineTotal;
        if (totalEl) totalEl.textContent = this.fmt(lineTotal, 2);
      }
    });

    const cgstRateEl = this.container.querySelector('[data-field="cgst_rate"]');
    const sgstRateEl = this.container.querySelector('[data-field="sgst_rate"]');
    const igstRateEl = this.container.querySelector('[data-field="igst_rate"]');
    const cgstRate = cgstRateEl ? this.parseNum(cgstRateEl.textContent) : 0;
    const sgstRate = sgstRateEl ? this.parseNum(sgstRateEl.textContent) : 0;
    const igstRate = igstRateEl ? this.parseNum(igstRateEl.textContent) : 0;

    const cgstAmount = subtotal * cgstRate / 100;
    const sgstAmount = subtotal * sgstRate / 100;
    const igstAmount = subtotal * igstRate / 100;
    const grandTotal = subtotal + cgstAmount + sgstAmount + igstAmount;

    const subtotalEl = this.container.querySelector(".tax-subtotal");
    const rcmSubtotalEl = this.container.querySelector(".tax-rcm-subtotal");
    const cgstEl = this.container.querySelector(".tax-cgst-amount");
    const sgstEl = this.container.querySelector(".tax-sgst-amount");
    const igstEl = this.container.querySelector(".tax-igst-amount");
    const grandTotalEl = this.container.querySelector(".tax-grand-total");
    const wordsEl = this.container.querySelector(".tax-amount-words");

    if (subtotalEl) subtotalEl.textContent = this.fmtInt(subtotal);
    if (rcmSubtotalEl) rcmSubtotalEl.textContent = this.fmtInt(subtotal);
    if (cgstEl) cgstEl.textContent = this.fmt(cgstAmount, 2);
    if (sgstEl) sgstEl.textContent = this.fmt(sgstAmount, 2);
    if (igstEl) igstEl.textContent = this.fmt(igstAmount, 2);
    if (grandTotalEl) grandTotalEl.textContent = this.fmtInt(grandTotal);
    if (wordsEl) wordsEl.textContent = this.numberToWords(grandTotal);
  }

  recalcTotals() {
    if (this.invoiceType === 'tax') this.recalcTaxTotals();
    else this.recalcFreightTotals();
  }

  rollbackAll() {
    for (const [path, value] of this.originalValues) {
      const el = this.container?.querySelector(`[data-field="${path}"]`);
      if (el) el.textContent = value;
    }
    this.originalValues.clear();
    this.recalcTotals();
  }

  clearOriginals() {
    this.originalValues.clear();
  }

  injectDeleteButtons() {
    if (!this.container || !this.onDeleteCallback) return;

    const rowSelector = this.invoiceType === 'tax' ? 'tr.items-row' : 'tr.freight-row';
    const rows = this.container.querySelectorAll(rowSelector);

    if (!this.container.querySelector('#row-delete-styles')) {
      const style = document.createElement('style');
      style.id = 'row-delete-styles';
      style.textContent = `
        .row-delete-btn {
          display: none;
          cursor: pointer;
          color: #dc2626;
          background: none;
          border: none;
          padding: 1px 3px;
          line-height: 1;
          vertical-align: middle;
          margin-right: 2px;
          border-radius: 3px;
          opacity: 0.5;
          transition: opacity 0.15s;
        }
        .row-delete-btn:hover { opacity: 1; background: #fee2e2; }
        tr:hover .row-delete-btn { display: inline-block; }
        @media print { .row-delete-btn { display: none !important; } }
      `;
      this.container.prepend(style);
    }

    const trashSvg = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>';

    rows.forEach((row) => {
      const firstTd = row.querySelector('td');
      if (!firstTd || firstTd.querySelector('.row-delete-btn')) return;

      const rowIndex = row.dataset.rowIndex !== undefined
        ? parseInt(row.dataset.rowIndex, 10)
        : Array.from(rows).indexOf(row);

      const btn = document.createElement('button');
      btn.className = 'row-delete-btn';
      btn.innerHTML = trashSvg;
      btn.title = 'Delete this row';
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        e.preventDefault();
        if (window.confirm('Delete this row?')) {
          this.onDeleteCallback(rowIndex);
        }
      });

      firstTd.prepend(btn);
    });
  }

  attachDelegatedListeners() {
    if (!this.container || this.delegatedListenersAttached) return;

    const handleKeyDown = (e) => {
      const el = e.target;
      if (!el.classList.contains('editable') || !el.dataset.field) return;

      if (e.key === "Enter" || e.key === "Tab") {
        e.preventDefault();
        e.stopPropagation();

        const path = el.dataset.field;
        if (path && !path.includes(".line_total")) {
          let newValue = el.textContent.trim().replace(/<br\s*\/?>/gi, '').trim();
          const isNumeric = el.classList.contains("numeric");
          if (isNumeric) newValue = this.parseNum(newValue);

          const editedJson = {};
          this.setByPath(editedJson, path, newValue);

          if (this.onDataChangeCallback) {
            this.onDataChangeCallback(editedJson);
          }
        }

        if (e.key === "Tab") {
          const allEditables = Array.from(
            this.container.querySelectorAll('.editable[data-field][contenteditable="true"]')
          );
          const currentIndex = allEditables.indexOf(el);
          if (currentIndex !== -1) {
            const nextIndex = e.shiftKey
              ? (currentIndex - 1 + allEditables.length) % allEditables.length
              : (currentIndex + 1) % allEditables.length;
            el.blur();
            allEditables[nextIndex].focus();
          } else {
            el.blur();
          }
        } else {
          el.blur();
        }
      }
    };

    const handleFocus = (e) => {
      const el = e.target;
      if (!el.classList.contains('editable') || !el.dataset.field) return;
      this.originalValues.set(el.dataset.field, el.textContent.trim());
    };

    const handleInput = (e) => {
      const el = e.target;
      if (!el.classList.contains('editable')) return;
      clearTimeout(this.debounceTimer);
      this.debounceTimer = setTimeout(() => {
        this.recalcTotals();
      }, 100);
    };

    const handleBlur = (e) => {
      const el = e.target;
      if (!el.classList.contains('editable') || !el.dataset.field) return;
      if (el.dataset.field.includes(".line_total")) return;
      this.recalcTotals();
    };

    this.container.addEventListener('keydown', handleKeyDown, true);
    this.container.addEventListener('focus', handleFocus, true);
    this.container.addEventListener('input', handleInput, true);
    this.container.addEventListener('blur', handleBlur, true);

    this.delegatedListenersAttached = true;
  }

  init() {
    this.injectDeleteButtons();
    this.attachDelegatedListeners();

    this.observer = new MutationObserver(() => {
      clearTimeout(this.observerDebounceTimer);
      this.observerDebounceTimer = setTimeout(() => {
        this.injectDeleteButtons();
      }, 100);
    });

    if (this.container) {
      this.observer.observe(this.container, {
        childList: true,
        subtree: true,
        characterData: false
      });
    }

    this.recalcTotals();
  }

  destroy() {
    if (this.observer) {
      this.observer.disconnect();
      this.observer = null;
    }
    this.container = null;
    this.onDataChangeCallback = null;
    this.onDeleteCallback = null;
    this.debounceTimer = null;
    this.observerDebounceTimer = null;
    this.originalValues.clear();
    this.delegatedListenersAttached = false;
  }
}
