# Invoice Generation System

Complete invoice generation system with AI-powered data extraction, natural language commands, and multi-format export.

## Features

✅ **Multiple Templates** - Tax Invoice (GTA) and Freight Bill  
✅ **AI Data Extraction** - Upload Excel/CSV files for automatic data extraction  
✅ **Natural Language Commands** - Edit invoices using plain English  
✅ **Multi-Format Export** - PDF, PNG, and HTML  
✅ **Master Data Management** - Banks, clients, terms & conditions  
✅ **State Management** - Save drafts and auto-save support  
✅ **RESTful API** - Complete FastAPI backend for React frontend  

## Quick Start

### Prerequisites

- Python 3.11
- MongoDB (for master data)
- Node.js 22+ (for React frontend)

### Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="your-api-key"
export MONGODB_URI="your-mongodb-uri"
```

### Running the Application

**Option 1: Gradio UI (Testing)**
```bash
python app.py
# Open http://localhost:7860
```

**Option 2: FastAPI Server (Production)**
```bash
python api_server.py
# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

## Project Structure

```
invoice_app/
├── app.py                    # Gradio UI entry point
├── api_server.py             # FastAPI server entry point
├── core/                     # Business logic
│   ├── invoice_math.py       # Calculations
│   ├── patch_applicator.py   # State updates
│   ├── state_store.py        # State management
│   └── template_registry.py  # Template discovery
├── agents/                   # Invoice processing agents
│   ├── invoice_agent_tax.py
│   └── invoice_agent_bill.py
├── contexts/                 # Agent context configurations
│   ├── context_tax_invoice.py
│   └── context_bill_invoice.py
├── templates/                # HTML invoice templates
│   ├── invoice_template_gta.py
│   └── invoice_template_freight_bill.py
├── export/                   # Export system
│   └── invoice_exporter.py
├── integrations/             # External services
│   ├── mongodb_client.py
│   ├── llm_client.py
│   └── audio_client.py
├── utils/                    # Utilities
│   ├── file_reader.py
│   └── sheet_config_manager.py
├── ui/                       # Gradio interface
│   └── gradio_ui.py
├── config/                   # Configuration files
│   ├── overrides_tax.json
│   └── overrides_bill.json
└── tests/                    # Tests
```

## API Documentation

See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for complete API reference.

### Key Endpoints

- `GET /api/invoice/templates` - List all templates
- `GET /api/invoice/templates/{id}/schema` - Get field schema
- `GET /api/invoice/{type}/default` - Get default state
- `POST /api/invoice/{type}/process` - Process with file/command
- `PUT /api/invoice/{type}/state` - Save state
- `POST /api/invoice/{type}/export` - Export to PDF/PNG/HTML

## Usage Examples

### Python

```python
import requests

# Get available templates
response = requests.get('http://localhost:8000/api/invoice/templates')
templates = response.json()['templates']

# Get default tax invoice
response = requests.get('http://localhost:8000/api/invoice/tax/default')
state = response.json()['state']

# Process with file
files = {'file': open('data.xlsx', 'rb')}
data = {
    'state': json.dumps(state),
    'command': 'add all details from dataset to invoice'
}
response = requests.post('http://localhost:8000/api/invoice/tax/process', 
                        files=files, data=data)
updated_state = response.json()['state']

# Export to PDF
response = requests.post('http://localhost:8000/api/invoice/tax/export',
                        json={'state': updated_state, 'format': 'pdf'})
with open('invoice.pdf', 'wb') as f:
    f.write(response.content)
```

### JavaScript/React

```javascript
// Get templates
const { templates } = await fetch('/api/invoice/templates').then(r => r.json());

// Get schema
const { schema } = await fetch('/api/invoice/templates/tax/schema').then(r => r.json());

// Process with file
const formData = new FormData();
formData.append('file', file);
formData.append('state', JSON.stringify(state));
formData.append('command', 'add all details from dataset');

const { state: updated } = await fetch('/api/invoice/tax/process', {
  method: 'POST',
  body: formData
}).then(r => r.json());

// Export
const blob = await fetch('/api/invoice/tax/export', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ state: updated, format: 'pdf' })
}).then(r => r.blob());
```

## Supported Commands

### File Upload Commands
- `"add all details from dataset to invoice"` - Extract all data
- `"add rows from September 2025"` - Filter by date
- `"add rows where quantity > 100"` - Filter by condition

### Text-Only Commands
- `"set invoice number to INV-001"` - Update header fields
- `"set CGST rate to 9%"` - Update tax rates
- `"delete row 3"` - Remove item
- `"change quantity in row 2 to 50"` - Update item field

## Development

### Adding New Templates

1. Create agent in `agents/invoice_agent_new.py`
2. Create context in `contexts/context_new.py`
3. Create HTML template in `templates/invoice_template_new.py`
4. Register in `core/template_registry.py`

### Running Tests

```bash
python -m pytest tests/
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY` - OpenAI API key for LLM
- `MONGODB_URI` - MongoDB connection string
- `GRADIO_SERVER_PORT` - Gradio UI port (default: 7860)
- `API_SERVER_PORT` - FastAPI server port (default: 8000)

### Config Files

- `config/overrides_tax.json` - Tax invoice saved state
- `config/overrides_bill.json` - Bill invoice saved state

## Deployment

### Production Checklist

- [ ] Set environment variables
- [ ] Configure MongoDB connection
- [ ] Add authentication (JWT)
- [ ] Restrict CORS to frontend domain
- [ ] Add rate limiting
- [ ] Add input validation
- [ ] Set up logging
- [ ] Configure SSL/TLS

### Docker

```bash
# Build
docker build -t invoice-app .

# Run
docker run -p 8000:8000 -e OPENAI_API_KEY=xxx invoice-app
```

## Troubleshooting

### Port Already in Use

```bash
# Find process
ps aux | grep "python.*app.py"

# Kill process
kill <PID>
```

### MongoDB Connection Error

Check `MONGODB_URI` environment variable and ensure MongoDB is running.

### File Upload Error

Ensure uploaded files are in Excel (.xlsx, .xls) or CSV (.csv) format.

## License

Proprietary - All rights reserved

## Support

For issues or questions, contact the development team.

## Version

**Version**: 2.0  
**Last Updated**: January 3, 2026
