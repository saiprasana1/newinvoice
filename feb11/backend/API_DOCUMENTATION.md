# Invoice Generation API Documentation

**Version**: 2.0 (Complete)  
**Base URL**: `http://localhost:8000`  
**Last Updated**: January 3, 2026

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Template Discovery](#template-discovery)
4. [Tax Invoice Endpoints](#tax-invoice-endpoints)
5. [Bill Invoice Endpoints](#bill-invoice-endpoints)
6. [Master Data Endpoints](#master-data-endpoints)
7. [Health Check](#health-check)
8. [Error Handling](#error-handling)
9. [React Integration Guide](#react-integration-guide)
10. [Data Models](#data-models)

---

## Overview

Complete backend API for invoice generation with:

✅ **Template Discovery** - Dynamically discover available templates  
✅ **Schema API** - Get field definitions for automatic form generation  
✅ **State Management** - Save and load invoice drafts  
✅ **File Processing** - Excel/CSV upload with AI-powered extraction  
✅ **Text Commands** - Natural language invoice editing  
✅ **Export** - PDF, PNG, and HTML formats  
✅ **Master Data** - Bank accounts, clients, terms & conditions  

### Supported Templates

1. **Tax Invoice (GTA)** - GST Tax Invoice for Goods Transport Agency
2. **Freight Bill** - Transportation/freight bills with delivery tracking

---

## Quick Start

```javascript
// 1. Get available templates
const { templates } = await fetch('/api/invoice/templates').then(r => r.json());

// 2. Select template and get schema
const { schema } = await fetch(`/api/invoice/templates/tax/schema`).then(r => r.json());

// 3. Get default state
const { state } = await fetch('/api/invoice/tax/default').then(r => r.json());

// 4. Process with file or command
const formData = new FormData();
formData.append('file', file);
formData.append('state', JSON.stringify(state));
formData.append('command', 'add all details from dataset');
const { state: updated } = await fetch('/api/invoice/tax/process', {
  method: 'POST',
  body: formData
}).then(r => r.json());

// 5. Save state
await fetch('/api/invoice/tax/state', {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ state: updated, command: '' })
});

// 6. Export
const pdfBlob = await fetch('/api/invoice/tax/export', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ state: updated, format: 'pdf' })
}).then(r => r.blob());
```

---

## Template Discovery

### GET /api/invoice/templates

Get list of all available invoice templates.

**Response** (200 OK):
```json
{
  "success": true,
  "templates": [
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
        "save": "/api/invoice/tax/state"
      }
    }
  ],
  "count": 2
}
```

---

### GET /api/invoice/templates/{id}/schema

Get field schema for a specific template.

**Path Parameters**:
- `id`: Template identifier (`tax` or `bill`)

**Response** (200 OK):
```json
{
  "success": true,
  "template_id": "tax",
  "schema": {
    "invoice_number": {
      "type": "string",
      "label": "Invoice Number",
      "required": true,
      "editable": true,
      "placeholder": "INV-001"
    },
    "items": {
      "type": "array",
      "label": "Items",
      "required": true,
      "editable": true,
      "item_schema": {
        "description": { "type": "string", "required": true },
        "quantity": { "type": "number", "required": true },
        "unit_price": { "type": "number", "required": true }
      }
    },
    "total": {
      "type": "number",
      "label": "Total",
      "computed": true,
      "editable": false
    }
  }
}
```

---

## Tax Invoice Endpoints

### GET /api/invoice/tax/default

Get default state for a new tax invoice.

**Response** (200 OK):
```json
{
  "success": true,
  "state": {
    "invoice_number": "",
    "invoice_date": "2026-01-03",
    "items": [],
    "cgst_rate": 6.0,
    "sgst_rate": 6.0,
    "subtotal": 0.0,
    "total": 0.0
  }
}
```

---

### POST /api/invoice/tax/process

Process tax invoice with optional file upload and command.

**Content-Type**: `multipart/form-data`

**Form Parameters**:
- `file` (file, optional): Excel/CSV file
- `state` (string, required): Current invoice state as JSON
- `command` (string, required): User command

**Supported Commands**:

**With File**:
- `"add all details from dataset to invoice"`
- `"add rows from September 2025"`
- `"add rows where quantity > 100"`

**Without File**:
- `"set invoice number to INV-001"`
- `"set CGST rate to 9%"`
- `"delete row 3"`
- `"change quantity in row 2 to 50"`

**Response** (200 OK):
```json
{
  "success": true,
  "state": { /* Updated state */ },
  "message": "✓ Agentic operation complete: ADD"
}
```

---

### PUT /api/invoice/tax/state

Save tax invoice state (auto-save).

**Content-Type**: `application/json`

**Request Body**:
```json
{
  "state": { /* Invoice state */ },
  "command": ""
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "state": { /* State with recalculated totals */ },
  "message": "Tax invoice state saved successfully"
}
```

**Features**:
- Automatically recalculates totals
- Saves to config/overrides_tax.json
- Returns updated state

---

### POST /api/invoice/tax/export

Export tax invoice to PDF, PNG, or HTML.

**Content-Type**: `application/json`

**Request Body**:
```json
{
  "state": { /* Invoice state */ },
  "format": "pdf"  // or "png" or "html"
}
```

**Response (PDF/PNG)** (200 OK):
- Content-Type: `application/pdf` or `image/png`
- Body: Binary file content

**Response (HTML)** (200 OK):
```json
{
  "success": true,
  "html": "<html>...</html>"
}
```

---

## Bill Invoice Endpoints

### GET /api/invoice/bill/default

Get default state for a new freight bill.

### POST /api/invoice/bill/process

Process bill invoice (same as tax, but with `freight_bill` structure).

### PUT /api/invoice/bill/state

Save bill invoice state.

### POST /api/invoice/bill/export

Export bill invoice to PDF/PNG/HTML.

---

## Master Data Endpoints

### GET /api/invoice/master-data/bank-accounts

Get list of bank accounts.

**Response** (200 OK):
```json
[
  { "id": "11327915122", "label": "SBI – Yerraguntla" },
  { "id": "9988776655", "label": "HDFC – Coimbatore" }
]
```

---

### POST /api/invoice/load-bank-account

Load bank account into invoice state.

**Request Body**:
```json
{
  "state": { /* Current state */ },
  "account_number": "11327915122"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "state": { /* State with bank details populated */ }
}
```

---

### GET /api/invoice/master-data/client-companies

Get list of client companies.

**Response** (200 OK):
```json
[
  { "id": "zuari_cement", "label": "Zuari Cement Ltd." },
  { "id": "ramco_cements", "label": "Ramco Cements Ltd." }
]
```

---

### POST /api/invoice/load-client-company

Load client company into invoice state.

**Request Body**:
```json
{
  "state": { /* Current state */ },
  "client_id": "zuari_cement"
}
```

---

### GET /api/invoice/master-data/parent-companies

Get list of parent companies.

### POST /api/invoice/load-parent-company

Load parent company into invoice state.

### GET /api/invoice/master-data/terms-and-conditions

Get list of terms and conditions templates.

### POST /api/invoice/load-terms-and-conditions

Load terms and conditions into invoice state.

---

## Health Check

### GET /

Basic health check.

**Response** (200 OK):
```json
{
  "status": "ok",
  "message": "Invoice Generation API is running",
  "version": "1.0"
}
```

---

### GET /health

Detailed health check.

---

## Error Handling

### Error Response Format

```json
{
  "detail": "Error message"
}
```

### HTTP Status Codes

- **200 OK**: Success
- **400 Bad Request**: Invalid parameters
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error

---

## React Integration Guide

### Complete Workflow

```javascript
import React, { useState, useEffect } from 'react';

function InvoiceApp() {
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [schema, setSchema] = useState(null);
  const [invoiceState, setInvoiceState] = useState(null);

  // Step 1: Load templates
  useEffect(() => {
    fetch('/api/invoice/templates')
      .then(res => res.json())
      .then(data => setTemplates(data.templates));
  }, []);

  // Step 2: Load schema and default state
  const handleTemplateSelect = async (templateId) => {
    const [schemaRes, stateRes] = await Promise.all([
      fetch(`/api/invoice/templates/${templateId}/schema`),
      fetch(`/api/invoice/${templateId}/default`)
    ]);
    
    const schemaData = await schemaRes.json();
    const stateData = await stateRes.json();
    
    setSchema(schemaData.schema);
    setInvoiceState(stateData.state);
    setSelectedTemplate(templateId);
  };

  // Step 3: Auto-save
  useEffect(() => {
    if (!invoiceState || !selectedTemplate) return;

    const interval = setInterval(async () => {
      await fetch(`/api/invoice/${selectedTemplate}/state`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ state: invoiceState, command: '' })
      });
    }, 30000);

    return () => clearInterval(interval);
  }, [invoiceState, selectedTemplate]);

  // Step 4: File upload
  const handleFileUpload = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('state', JSON.stringify(invoiceState));
    formData.append('command', 'add all details from dataset to invoice');

    const res = await fetch(`/api/invoice/${selectedTemplate}/process`, {
      method: 'POST',
      body: formData
    });

    const data = await res.json();
    setInvoiceState(data.state);
  };

  // Step 5: Export
  const handleExport = async (format) => {
    const res = await fetch(`/api/invoice/${selectedTemplate}/export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ state: invoiceState, format })
    });

    if (format === 'html') {
      const data = await res.json();
      // Display HTML
    } else {
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `invoice.${format}`;
      a.click();
    }
  };

  return (
    <div>
      {/* Template selector */}
      <select onChange={(e) => handleTemplateSelect(e.target.value)}>
        {templates.map(t => (
          <option key={t.id} value={t.id}>{t.icon} {t.display_name}</option>
        ))}
      </select>

      {/* Dynamic form from schema */}
      {schema && <DynamicForm schema={schema} state={invoiceState} onChange={setInvoiceState} />}

      {/* File upload */}
      <input type="file" onChange={(e) => handleFileUpload(e.target.files[0])} />

      {/* Export */}
      <button onClick={() => handleExport('pdf')}>Export PDF</button>
      <button onClick={() => handleExport('png')}>Export PNG</button>
    </div>
  );
}
```

---

## Data Models

### Tax Invoice State

```typescript
interface TaxInvoiceState {
  invoice_number: string;
  invoice_date: string;
  reverse_charge: "YES" | "NO";
  supply_period: string;
  
  company_info: {
    name: string;
    address: string;
    gstin: string;
    bank: {
      account_no: string;
      name: string;
      ifsc: string;
    };
  };
  
  billing_to: {
    client_name: string;
    address: string;
    gstin: string;
  };
  
  items: Array<{
    description: string;
    quantity: number;
    unit_price: number;
    amount: number;
  }>;
  
  cgst_rate: number;
  sgst_rate: number;
  subtotal: number;
  cgst: number;
  sgst: number;
  total: number;
}
```

### Bill Invoice State

```typescript
interface BillInvoiceState {
  freight_bill: {
    series_no: string;
    bill_date: string;
    
    to_party: {
      name: string;
      address: string;
    };
    
    runs: Array<{
      date: string;
      truck_no: string;
      lr_no: string;
      dc_qty_mt: number;
      gr_qty_mt: number;
      rate: number;
      line_total: number;
    }>;
    
    total: number;
  };
}
```

---

## API Summary

**Total Endpoints**: 20

**Template Management** (2):
- GET /api/invoice/templates
- GET /api/invoice/templates/{id}/schema

**Tax Invoice** (4):
- GET /api/invoice/tax/default
- POST /api/invoice/tax/process
- PUT /api/invoice/tax/state
- POST /api/invoice/tax/export

**Bill Invoice** (4):
- GET /api/invoice/bill/default
- POST /api/invoice/bill/process
- PUT /api/invoice/bill/state
- POST /api/invoice/bill/export

**Master Data** (8):
- GET /api/invoice/master-data/bank-accounts
- POST /api/invoice/load-bank-account
- GET /api/invoice/master-data/client-companies
- POST /api/invoice/load-client-company
- GET /api/invoice/master-data/parent-companies
- POST /api/invoice/load-parent-company
- GET /api/invoice/master-data/terms-and-conditions
- POST /api/invoice/load-terms-and-conditions

**Health** (2):
- GET /
- GET /health

---

## Changelog

### Version 2.0 (2026-01-03)
- ✅ Added template discovery API
- ✅ Added schema API for dynamic forms
- ✅ Added state save endpoints
- ✅ Added `/invoice/` prefix to all endpoints
- ✅ Reorganized code into folders
- ✅ Complete React integration support

### Version 1.0 (2025-11-24)
- Initial release
- Tax and Bill invoice processing
- File upload with AI extraction
- Export to PDF/HTML

---

## Support

For issues or questions, contact the development team.

**Interactive Docs**: Visit `http://localhost:8000/docs` for Swagger UI
