"""
FastAPI Backend for Invoice Generation System

This API exposes the invoice agents as REST endpoints for a React frontend.
Supports both Tax Invoice and Bill Invoice (Freight Bill) operations.

Run: uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env early (BEFORE importing agents that may read env vars)
ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

# Optional: quick sanity log (remove later)
print(f"FASTAPI sees OPENAI_API_KEY? {bool(os.getenv('OPENAI_API_KEY'))}")

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import tempfile
import shutil
import asyncio
import copy
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# Import invoice agents
from agents.invoice_agent_tax import agent_update_tax_from_file
from agents.invoice_agent_bill import agent_update_bill_from_file

# Import schema for default state
from core.invoice_schema import get_default_invoice_data

# Import calculation and export utilities
from core.invoice_math import calculate_invoice_totals
from templates.invoice_templates import render_invoice_html_template
from export.invoice_exporter import export_invoice

# Import MongoDB client and context mapper
from integrations.mongodb_client import (
    get_all_bank_accounts, get_bank_account_by_id,
    get_all_client_companies, get_client_company_by_id,
    get_all_parent_companies, get_parent_company_by_id,
    get_all_terms_and_conditions, get_terms_and_conditions_by_id
)
from integrations.invoice_context_mapper import (
    map_bank_to_invoice_state,
    map_client_company_to_billing_to,
    map_client_company_to_to_party,
    map_parent_company_to_company_info,
    map_terms_to_invoice_state
)
from core.state_store import get_initial_state, get_bill_initial_state, get_tax_initial_state, save_overrides
from core.template_registry import get_all_templates, get_template_schema_response
from api.invoice_field_editor import router as field_editor_router

# Create FastAPI app
app = FastAPI(
    title="Invoice Generation API",
    description="REST API for Tax Invoice and Bill Invoice generation with AI-powered agents",
    version="1.0.0"
)

# Thread pool for running sync Playwright code in async context
executor = ThreadPoolExecutor(max_workers=4)

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register field editor router
app.include_router(field_editor_router)

# ============================================================================
# Pydantic Models for Request/Response
# ============================================================================

class ProcessRequest(BaseModel):
    """Request model for processing invoices without file upload"""
    state: Dict[str, Any]
    command: str

class ProcessResponse(BaseModel):
    """Response model for all processing operations"""
    success: bool
    state: Dict[str, Any]
    message: str
    timestamp: str

class ExportRequest(BaseModel):
    """Request model for exporting invoices"""
    state: Dict[str, Any]
    format: str = "pdf"  # pdf, png, or html
    template_name: Optional[str] = None

# ============================================================================
# Helper Functions
# ============================================================================

def get_default_tax_state() -> Dict[str, Any]:
    """Get default state for tax invoice (tax overrides only, no freight_bill bleed)"""
    state = get_tax_initial_state()
    return calculate_invoice_totals(copy.deepcopy(state))

def get_default_bill_state() -> Dict[str, Any]:
    """Get default state for bill invoice (bill overrides only)"""
    state = get_bill_initial_state()
    return calculate_invoice_totals(copy.deepcopy(state))

def save_upload_file(upload_file: UploadFile) -> str:
    """Save uploaded file to temp directory and return path"""
    try:
        # Create temp file with same extension
        suffix = os.path.splitext(upload_file.filename)[1]
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        
        # Write uploaded content
        shutil.copyfileobj(upload_file.file, temp_file)
        temp_file.close()
        
        return temp_file.name
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}")
    finally:
        upload_file.file.close()

def cleanup_temp_file(file_path: str):
    """Clean up temporary file"""
    try:
        if file_path and os.path.exists(file_path):
            os.unlink(file_path)
    except Exception:
        pass  # Ignore cleanup errors

# ============================================================================
# Template Discovery Endpoints
# ============================================================================

@app.get("/api/invoice/templates")
async def get_templates():
    """
    Get list of all available invoice templates
    
    Returns:
        JSON response with template metadata
    """
    try:
        templates = get_all_templates()
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "templates": templates,
                "count": len(templates)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get templates: {str(e)}")


@app.get("/api/invoice/templates/{template_id}/schema")
async def get_template_schema(template_id: str):
    """
    Get field schema for a specific template
    
    Args:
        template_id: Template identifier (e.g., 'tax', 'bill')
        
    Returns:
        JSON response with template schema
    """
    try:
        schema_response = get_template_schema_response(template_id)
        
        if not schema_response:
            raise HTTPException(
                status_code=404,
                detail=f"Template '{template_id}' not found"
            )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                **schema_response
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get schema: {str(e)}")


# ============================================================================
# Tax Invoice Endpoints
# ============================================================================

@app.get("/api/invoice/tax/default")
async def get_tax_default_state():
    """
    Get default state for a new tax invoice
    
    Returns:
        Default tax invoice state with all fields initialized
    """
    return ProcessResponse(
        success=True,
        state=get_default_tax_state(),
        message="Default tax invoice state",
        timestamp=datetime.now().isoformat()
    )

@app.post("/api/invoice/tax/process")
async def process_tax_invoice(
    file: Optional[UploadFile] = File(None),
    state: str = Form(...),
    command: str = Form(...)
):
    """
    Process tax invoice with optional file upload and command
    
    Args:
        file: Optional Excel/CSV file to extract data from
        state: Current invoice state as JSON string
        command: User command (e.g., "add all details from dataset", "set CGST to 9%")
    
    Returns:
        Updated invoice state and status message
    """
    temp_file_path = None
    
    try:
        # Parse state from JSON
        try:
            current_state = json.loads(state)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in state parameter")
        
        # Save uploaded file if present
        if file:
            temp_file_path = save_upload_file(file)
        
        # Call the tax agent
        updated_state, message = agent_update_tax_from_file(
            file_path=temp_file_path,
            current_state=copy.deepcopy(current_state),
            user_notes=command
        )
        
        # Recalculate totals
        updated_state = calculate_invoice_totals(updated_state)
        
        # Save to overrides file
        save_overrides(updated_state)
        
        return ProcessResponse(
            success=True,
            state=updated_state,
            message=message,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    
    finally:
        # Clean up temp file
        if temp_file_path:
            cleanup_temp_file(temp_file_path)

@app.put("/api/invoice/tax/state")
async def save_tax_state(request: ProcessRequest):
    """
    Save tax invoice state without exporting
    
    Args:
        request: Request with state to save
        
    Returns:
        Updated state with recalculated totals
    """
    try:
        # Recalculate totals
        state = calculate_invoice_totals(copy.deepcopy(request.state))
        
        # Save to overrides file
        save_overrides(state)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "state": state,
                "message": "Tax invoice state saved successfully",
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save state: {str(e)}")


@app.post("/api/invoice/tax/export")
async def export_tax_invoice(request: ExportRequest):
    state = calculate_invoice_totals(copy.deepcopy(request.state))
    template_name = request.template_name or "Siva Sakthi GTA"
    format_lower = request.format.lower()

    if format_lower == "html":
        html = render_invoice_html_template(state, template_name)
        return JSONResponse(content={"html": html})

    try:
        # Save to overrides file
        save_overrides(state)
        
        # Export
        loop = asyncio.get_event_loop()
        output_path, status = await loop.run_in_executor(
            executor,
            export_invoice,
            state,              # invoice_data
            template_name,      # template_name
            request.format,     # format
            "exports",          # output_dir
            None                # filename
        )
        
        if not output_path:
            raise Exception(status)
        
        if request.format == "html":
            # For HTML, return content directly
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
            return JSONResponse(content={"html": content})
        else:
            # For PDF/PNG, return file
            filename = os.path.basename(output_path)
            return FileResponse(
                path=output_path,
                filename=filename,
                media_type=f"application/{request.format}"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# ============================================================================
# Bill Invoice (Freight Bill) Endpoints
# ============================================================================

@app.post("/api/invoice/bill/add-row")
async def add_bill_row(request: Dict[str, Any]):
    """
    Add an empty row to the bill invoice items
    """
    try:
        state = copy.deepcopy(request.get("state", {}))
        
        # Ensure freight_bill structure exists
        if "freight_bill" not in state:
            state["freight_bill"] = {}
            
        if "runs" not in state["freight_bill"]:
            state["freight_bill"]["runs"] = []
            
        # Create empty run row (Freight Bill specific)
        empty_row = {
            "date": "",
            "truck_no": "",
            "lr_no": "",
            "dc_qty_mt": 0,
            "gr_qty_mt": 0,
            "rate": 0,
            "line_total": 0
        }
        
        # Append to runs
        state["freight_bill"]["runs"].append(empty_row)
        
        # Save to overrides file
        save_overrides(state)
        
        return {
            "success": True,
            "state": state,
            "message": "Added new row"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add row: {str(e)}")

@app.post("/api/invoice/tax/add-row")
async def add_tax_row(request: Dict[str, Any]):
    """
    Add an empty row to the tax invoice items
    """
    try:
        state = copy.deepcopy(request.get("state", {}))

        if "items" not in state:
            state["items"] = []

        empty_item = {
            "description": "",
            "hsn_code": "",
            "uom": "",
            "quantity": 0,
            "unit_price": 0,
            "line_total": 0
        }

        state["items"].append(empty_item)

        save_overrides(state)

        return {
            "success": True,
            "state": state,
            "message": "Added new item row"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add row: {str(e)}")

@app.post("/api/invoice/bill/delete-row")
async def delete_bill_row(request: Dict[str, Any]):
    """Delete a row from the bill invoice by index"""
    try:
        state = copy.deepcopy(request.get("state", {}))
        row_index = request.get("row_index")

        if row_index is None:
            raise HTTPException(status_code=400, detail="row_index is required")

        runs = state.get("freight_bill", {}).get("runs", [])
        if row_index < 0 or row_index >= len(runs):
            raise HTTPException(status_code=400, detail="Invalid row index")

        runs.pop(row_index)
        state["freight_bill"]["runs"] = runs
        state = calculate_invoice_totals(state)
        save_overrides(state)

        return {"success": True, "state": state, "message": "Row deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete row: {str(e)}")

@app.post("/api/invoice/tax/delete-row")
async def delete_tax_row(request: Dict[str, Any]):
    """Delete a row from the tax invoice by index"""
    try:
        state = copy.deepcopy(request.get("state", {}))
        row_index = request.get("row_index")

        if row_index is None:
            raise HTTPException(status_code=400, detail="row_index is required")

        items = state.get("items", [])
        if row_index < 0 or row_index >= len(items):
            raise HTTPException(status_code=400, detail="Invalid row index")

        items.pop(row_index)
        state["items"] = items
        state = calculate_invoice_totals(state)
        save_overrides(state)

        return {"success": True, "state": state, "message": "Row deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete row: {str(e)}")

@app.post("/api/invoice/bill/clear")
async def clear_bill_state():
    """
    Clear bill invoice overrides and return default state
    """
    try:
        # Clear overrides file
        from core.state_store import OVERRIDES_BILL_PATH, _safe_write
        _safe_write(OVERRIDES_BILL_PATH, {})
        
        # Return default state
        return ProcessResponse(
            success=True,
            state=get_default_bill_state(),
            message="Bill invoice state cleared",
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear bill state: {str(e)}")

@app.post("/api/invoice/tax/clear")
async def clear_tax_state():
    """
    Clear tax invoice overrides and return default state
    """
    try:
        # Clear overrides file
        from core.state_store import OVERRIDES_TAX_PATH, _safe_write
        _safe_write(OVERRIDES_TAX_PATH, {})

        # Return default state
        return ProcessResponse(
            success=True,
            state=get_default_tax_state(),
            message="Tax invoice state cleared",
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear tax state: {str(e)}")

@app.get("/api/invoice/bill/default")
async def get_bill_default_state():
    """
    Get default state for a new bill invoice
    
    Returns:
        Default bill invoice state with all fields initialized
    """
    return ProcessResponse(
        success=True,
        state=get_default_bill_state(),
        message="Default bill invoice state",
        timestamp=datetime.now().isoformat()
    )

@app.post("/api/invoice/bill/process")
async def process_bill_invoice(
    file: Optional[UploadFile] = File(None),
    state: str = Form(...),
    command: str = Form(...)
):
    """
    Process bill invoice with optional file upload and command
    
    Args:
        file: Optional Excel/CSV file to extract data from
        state: Current invoice state as JSON string
        command: User command
    
    Returns:
        Updated invoice state and status message
    """
    temp_file_path = None
    
    try:
        # Parse state from JSON
        try:
            current_state = json.loads(state)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in state parameter")
        
        # Save uploaded file if present
        if file:
            temp_file_path = save_upload_file(file)
        
        # Call the bill agent
        updated_state, message = agent_update_bill_from_file(
            file_path=temp_file_path,
            current_state=copy.deepcopy(current_state),
            user_notes=command
        )
        
        # Recalculate totals
        updated_state = calculate_invoice_totals(updated_state)
        
        # Save to overrides file
        save_overrides(updated_state)
        
        return ProcessResponse(
            success=True,
            state=updated_state,
            message=message,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    
    finally:
        # Clean up temp file
        if temp_file_path:
            cleanup_temp_file(temp_file_path)

@app.put("/api/invoice/bill/state")
async def save_bill_state(request: ProcessRequest):
    """
    Save bill invoice state without exporting
    
    Args:
        request: Request with state to save
        
    Returns:
        Updated state with recalculated totals
    """
    try:
        # Recalculate totals
        state = calculate_invoice_totals(copy.deepcopy(request.state))
        
        # Save to overrides file
        save_overrides(state)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "state": state,
                "message": "Bill invoice state saved successfully",
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save state: {str(e)}")


@app.post("/api/invoice/bill/export")
async def export_bill_invoice(request: ExportRequest):
    state = calculate_invoice_totals(request.state)
    template_name = request.template_name or "Siva Sakthi Freight Bill"
    format_lower = request.format.lower()

    if format_lower == "html":
        html = render_invoice_html_template(state, template_name)
        return JSONResponse(content={"html": html})

    try:
        # Save to overrides file
        save_overrides(state)
        
        # Export
        loop = asyncio.get_event_loop()
        output_path, status = await loop.run_in_executor(
            executor,
            export_invoice,
            state,              # invoice_data
            template_name,      # template_name
            request.format,     # format
            "exports",          # output_dir
            None                # filename
        )
        
        if not output_path:
            raise Exception(status)
        
        if request.format == "html":
            # For HTML, return content directly
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
            return JSONResponse(content={"html": content})
        else:
            # For PDF/PNG, return file
            filename = os.path.basename(output_path)
            return FileResponse(
                path=output_path,
                filename=filename,
                media_type=f"application/{request.format}"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# ============================================================================
# Master Data Endpoints
# ============================================================================

@app.get("/api/invoice/master-data/parent-companies")
async def get_parent_companies():
    """Get all parent companies (billers)"""
    try:
        companies = get_all_parent_companies()
        return {
            "success": True,
            "companies": companies,
            "count": len(companies)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch parent companies: {str(e)}")

@app.get("/api/invoice/master-data/client-companies")
async def get_client_companies():
    """Get all client companies (billed to)"""
    try:
        companies = get_all_client_companies()
        return {
            "success": True,
            "companies": companies,
            "count": len(companies)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch client companies: {str(e)}")

@app.post("/api/invoice/load-parent-company")
async def load_parent_company(request: Dict[str, Any]):
    """
    Load parent company details into invoice state.
    
    This endpoint handles BOTH tax and bill invoices:
    - For Bill Invoices: Updates freight_bill.company_info
    - For Tax Invoices: Updates top-level company_info
    
    Args:
        request: { "state": {...}, "selected_id": "..." }
    """
    try:
        state = copy.deepcopy(request.get("state", {}))
        selected_id = request.get("selected_id")
        
        if not selected_id:
            raise HTTPException(status_code=400, detail="selected_id is required")
            
        company = get_parent_company_by_id(selected_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
            
        # Map to invoice state
        mapped_data = map_parent_company_to_company_info(company)
        
        # Check if this is a bill invoice
        # If freight_bill exists in state, update freight_bill.company_info
        # Otherwise, update top-level company_info (for tax invoices)
        
        if "freight_bill" in state:
            # This is a BILL INVOICE: Update freight_bill.company_info
            if "company_info" not in state["freight_bill"]:
                state["freight_bill"]["company_info"] = {}
            state["freight_bill"]["company_info"] = mapped_data
        else:
            # This is a TAX INVOICE: Update top-level company_info
            state["company_info"] = mapped_data
        
        updated_state = state
        
        # Recalculate totals
        updated_state = calculate_invoice_totals(updated_state)
        
        # Save to overrides file
        save_overrides(updated_state)
        
        return {
            "success": True,
            "state": updated_state,
            "message": f"Loaded parent company: {company.get('parent_company_title', 'Unknown')}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load parent company: {str(e)}")

@app.post("/api/invoice/load-client-company")
async def load_client_company(request: Dict[str, Any]):
    """
    Load client company details into invoice state.
    
    This endpoint handles BOTH tax and bill invoices:
    - For Bill Invoices: Updates freight_bill.to_party
    - For Tax Invoices: Updates top-level billing_to
    
    Args:
        request: { "state": {...}, "selected_id": "..." }
    """
    try:
        state = copy.deepcopy(request.get("state", {}))
        selected_id = request.get("selected_id")
        
        if not selected_id:
            raise HTTPException(status_code=400, detail="selected_id is required")
            
        company = get_client_company_by_id(selected_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Check if this is a bill invoice
        # If freight_bill exists in state, update freight_bill.to_party
        # Otherwise, update top-level billing_to (for tax invoices)
        
        if "freight_bill" in state:
            # This is a BILL INVOICE: Update freight_bill.to_party
            # Map to to_party format (different from billing_to)
            from integrations.invoice_context_mapper import map_client_company_to_to_party
            mapped_data = map_client_company_to_to_party(company)
            
            # Directly assign (to_party is a single object, not merged)
            state["freight_bill"]["to_party"] = mapped_data
        else:
            # This is a TAX INVOICE: Update top-level billing_to
            mapped_data = map_client_company_to_billing_to(company)
            state["billing_to"] = mapped_data
        
        updated_state = state
        
        # Recalculate totals
        updated_state = calculate_invoice_totals(updated_state)
        
        # Save to overrides file
        save_overrides(updated_state)
        
        return {
            "success": True,
            "state": updated_state,
            "message": f"Loaded client company: {company.get('name')}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load client company: {str(e)}")

@app.get("/api/invoice/master-data/bank-accounts")
async def get_bank_accounts():
    """Get all bank accounts"""
    try:
        accounts = get_all_bank_accounts()
        return {
            "success": True,
            "accounts": accounts,
            "count": len(accounts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch bank accounts: {str(e)}")

@app.get("/api/invoice/master-data/terms-and-conditions")
async def get_terms_and_conditions():
    """Get all terms and conditions templates"""
    try:
        terms = get_all_terms_and_conditions()
        return {
            "success": True,
            "terms": terms,
            "count": len(terms)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch terms and conditions: {str(e)}")

@app.post("/api/invoice/load-bank-account")
async def load_bank_account(request: Dict[str, Any]):
    """
    Load bank account details into invoice state
    
    Args:
        request: { "state": {...}, "selected_id": "..." }
    """
    try:
        state = copy.deepcopy(request.get("state", {}))
        selected_id = request.get("selected_id")
        
        if not selected_id:
            raise HTTPException(status_code=400, detail="selected_id is required")
            
        bank = get_bank_account_by_id(selected_id)
        if not bank:
            raise HTTPException(status_code=404, detail="Bank account not found")
            
        # Map to invoice state
        mapped_data = map_bank_to_invoice_state(bank)
        
        # Update company_info.bank
        if "company_info" not in state:
            state["company_info"] = {}
        state["company_info"]["bank"] = mapped_data
        
        # Save to overrides file
        save_overrides(state)
        
        return {
            "success": True,
            "state": state,
            "message": f"Loaded bank account: {bank.get('name')}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load bank account: {str(e)}")

@app.post("/api/invoice/load-terms-and-conditions")
async def load_terms_and_conditions(request: Dict[str, Any]):
    """
    Load terms and conditions into invoice state
    
    Args:
        request: { "state": {...}, "selected_id": "..." }
    """
    try:
        state = copy.deepcopy(request.get("state", {}))
        selected_id = request.get("selected_id")
        
        if not selected_id:
            raise HTTPException(status_code=400, detail="selected_id is required")
            
        terms = get_terms_and_conditions_by_id(selected_id)
        if not terms:
            raise HTTPException(status_code=404, detail="Terms and conditions not found")
            
        # Map to invoice state
        mapped_data = map_terms_to_invoice_state(terms)
        
        # Update terms_and_conditions in state
        state["terms_and_conditions"] = mapped_data.get("terms_and_conditions", [])
        
        # Save to overrides file
        save_overrides(state)
        
        return {
            "success": True,
            "state": state,
            "message": f"Loaded terms and conditions"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load terms and conditions: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
