"""
Unified Invoice Export System

Handles PDF and PNG export for any invoice template.
Replaces the old template-specific export functions.
"""

import os
import tempfile
import logging
from typing import Tuple, Optional, Literal
from datetime import datetime
from playwright.sync_api import sync_playwright
from templates.invoice_templates import render_invoice_html_template
from core.invoice_math import calculate_invoice_totals

logger = logging.getLogger(__name__)

# A4 dimensions
A4_CSS_WIDTH = 794
A4_CSS_HEIGHT = 1123
PNG_SCALE_FACTOR = 2480 / A4_CSS_WIDTH  # ~3.125 for ~300dpi


class InvoiceExporter:
    """
    Unified export system for invoice templates.
    Handles PDF and PNG generation for any template.
    """
    
    def __init__(self):
        self.temp_files = []
    
    def export(
        self,
        invoice_data: dict,
        template_name: str,
        format: Literal['pdf', 'png'],
        output_dir: str = "exports",
        filename: Optional[str] = None,
        recalculate: bool = True
    ) -> Tuple[Optional[str], str]:
        """
        Export invoice to PDF or PNG.
        
        Args:
            invoice_data: Invoice data dictionary
            template_name: Template name (e.g., "Siva Sakthi GTA", "Siva Sakthi Freight Bill")
            format: 'pdf' or 'png'
            output_dir: Output directory path
            filename: Optional custom filename (without extension)
            recalculate: Whether to recalculate totals before export
        
        Returns:
            Tuple of (file_path, status_message)
        """
        try:
            # Recalculate totals if requested
            if recalculate:
                invoice_data = calculate_invoice_totals(invoice_data)
            
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate filename
            if not filename:
                filename = self._generate_filename(invoice_data)
            filename = self._safe_filename(filename)
            
            # Export based on format
            if format == 'pdf':
                return self._export_pdf(invoice_data, template_name, output_dir, filename)
            elif format == 'png':
                return self._export_png(invoice_data, template_name, output_dir, filename)
            else:
                return None, f"❌ Unsupported format: {format}"
        
        except Exception as e:
            logger.exception(f"Export failed: {e}")
            return None, f"❌ Export failed: {e}"
    
    def _export_pdf(
        self,
        invoice_data: dict,
        template_name: str,
        output_dir: str,
        filename: str
    ) -> Tuple[Optional[str], str]:
        """Generate PDF export"""
        pdf_path = os.path.join(output_dir, f"{filename}.pdf")
        temp_html = self._create_temp_html(invoice_data, template_name)
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(f"file://{temp_html}")
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(500)
                
                # Generate PDF with A4 settings
                page.pdf(
                    path=pdf_path,
                    format="A4",
                    print_background=True,
                    margin={
                        "top": "0mm",
                        "right": "0mm",
                        "bottom": "0mm",
                        "left": "0mm"
                    }
                )
                
                browser.close()
            
            return pdf_path, f"✓ PDF exported: {os.path.basename(pdf_path)}"
        
        finally:
            self._cleanup_temp_file(temp_html)
    
    def _export_png(
        self,
        invoice_data: dict,
        template_name: str,
        output_dir: str,
        filename: str
    ) -> Tuple[Optional[str], str]:
        """Generate PNG export"""
        png_path = os.path.join(output_dir, f"{filename}.png")
        temp_html = self._create_temp_html(invoice_data, template_name)
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                
                # Viewport at A4 CSS size; device scale factor yields ~300dpi
                context = browser.new_context(
                    viewport={"width": A4_CSS_WIDTH, "height": A4_CSS_HEIGHT},
                    device_scale_factor=PNG_SCALE_FACTOR,
                )
                page = context.new_page()
                page.goto(f"file://{temp_html}")
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(500)
                
                # Ensure A4 dimensions
                page.evaluate("""
                    () => {
                        const style = document.createElement('style');
                        style.textContent = `
                            @page { size: 210mm 297mm; margin: 0; }
                            body { width: 210mm; height: 297mm; margin: 0; padding: 0; }
                        `;
                        document.head.appendChild(style);
                    }
                """)
                
                # Take full page screenshot
                page.screenshot(
                    path=png_path,
                    full_page=True,
                    type="png"
                )
                
                browser.close()
            
            return png_path, f"✓ PNG exported: {os.path.basename(png_path)}"
        
        finally:
            self._cleanup_temp_file(temp_html)
    
    def _create_temp_html(self, invoice_data: dict, template_name: str) -> str:
        """Create temporary HTML file from invoice data"""
        html = render_invoice_html_template(invoice_data or {}, template_name)
        f = tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".html",
            delete=False,
            encoding="utf-8"
        )
        with f:
            f.write(html)
        
        self.temp_files.append(f.name)
        return f.name
    
    def _cleanup_temp_file(self, filepath: str):
        """Clean up temporary file"""
        try:
            if os.path.exists(filepath):
                os.unlink(filepath)
            if filepath in self.temp_files:
                self.temp_files.remove(filepath)
        except Exception as e:
            logger.warning(f"Failed to cleanup temp file {filepath}: {e}")
    
    def _generate_filename(self, invoice_data: dict) -> str:
        """Generate filename from invoice data"""
        invoice_no = (invoice_data or {}).get("invoice_number", "").strip()
        if invoice_no:
            return f"invoice_{invoice_no}"
        else:
            return f"invoice_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def _safe_filename(self, s: str) -> str:
        """Sanitize filename"""
        return "".join(c for c in (s or "") if c.isalnum() or c in ("-", "_")) or "invoice"
    
    def cleanup_all(self):
        """Clean up all temporary files"""
        for filepath in self.temp_files[:]:
            self._cleanup_temp_file(filepath)


# Global exporter instance
_exporter = None

def get_exporter() -> InvoiceExporter:
    """Get global InvoiceExporter instance"""
    global _exporter
    if _exporter is None:
        _exporter = InvoiceExporter()
    return _exporter


# Convenience functions for direct use
def export_invoice(
    invoice_data: dict,
    template_name: str,
    format: Literal['pdf', 'png'],
    output_dir: str = "exports",
    filename: Optional[str] = None
) -> Tuple[Optional[str], str]:
    """
    Export invoice to PDF or PNG.
    
    Args:
        invoice_data: Invoice data dictionary
        template_name: Template name (e.g., "Siva Sakthi GTA")
        format: 'pdf' or 'png'
        output_dir: Output directory
        filename: Optional custom filename
    
    Returns:
        Tuple of (file_path, status_message)
    """
    exporter = get_exporter()
    return exporter.export(invoice_data, template_name, format, output_dir, filename)
