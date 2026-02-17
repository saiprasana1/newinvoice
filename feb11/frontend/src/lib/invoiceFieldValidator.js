export const invoiceFieldValidator = {
  parseNum: (s) => {
    if (typeof s === "number") return Number.isFinite(s) ? s : 0;
    const v = parseFloat(String(s || "").replace(/[^\d.-]/g, ""));
    return Number.isFinite(v) ? v : 0;
  },

  validateNumericField: (value, fieldName) => {
    const num = this.parseNum(value);
    if (!Number.isFinite(num)) {
      return { valid: false, error: `${fieldName} must be a valid number` };
    }
    return { valid: true };
  },

  validateDateField: (value, fieldName) => {
    if (!value) return { valid: true };
    const dateRegex = /^\d{2}-\d{2}-\d{4}$/;
    if (!dateRegex.test(value)) {
      return { valid: false, error: `${fieldName} must be in DD-MM-YYYY format` };
    }
    return { valid: true };
  },

  validateTextField: (value, fieldName) => {
    if (typeof value !== "string") {
      return { valid: false, error: `${fieldName} must be text` };
    }
    return { valid: true };
  },

  validateFreightRun: (run) => {
    const errors = [];
    
    if (run.date && !this.validateDateField(run.date, "Date").valid) {
      errors.push("Invalid date format");
    }
    
    if (!this.validateNumericField(run.dc_qty_mt, "DC Qty").valid) {
      errors.push("DC Qty must be numeric");
    }
    
    if (!this.validateNumericField(run.gr_qty_mt, "GR Qty").valid) {
      errors.push("GR Qty must be numeric");
    }
    
    if (!this.validateNumericField(run.rate, "Rate").valid) {
      errors.push("Rate must be numeric");
    }

    return { valid: errors.length === 0, errors };
  },

  validateFreightBill: (freightBill) => {
    const errors = [];

    if (freightBill.runs && Array.isArray(freightBill.runs)) {
      freightBill.runs.forEach((run, idx) => {
        const validation = this.validateFreightRun(run);
        if (!validation.valid) {
          errors.push(`Run ${idx + 1}: ${validation.errors.join(", ")}`);
        }
      });
    }

    return { valid: errors.length === 0, errors };
  },
};
