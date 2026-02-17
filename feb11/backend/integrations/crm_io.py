import os
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def load_crm_data(file_path):
    """Load CRM data from Excel file with robust error handling."""
    try:
        if not os.path.exists(file_path):
            return None, f"File not found: {file_path}"
        
        # Try multiple approaches to read the Excel file
        df = None
        error_messages = []
        
        # Method 1: Standard openpyxl
        try:
            df = pd.read_excel(file_path, engine="openpyxl")
        except Exception as e:
            error_messages.append(f"openpyxl: {str(e)}")
        
        # Method 2: Try with xlrd for older Excel files
        if df is None:
            try:
                df = pd.read_excel(file_path, engine="xlrd")
            except Exception as e:
                error_messages.append(f"xlrd: {str(e)}")
        
        # Method 3: Try reading specific sheet
        if df is None:
            try:
                # Read the first sheet explicitly
                df = pd.read_excel(file_path, sheet_name=0, engine="openpyxl")
            except Exception as e:
                error_messages.append(f"sheet_name=0: {str(e)}")
        
        # Method 4: Try reading with different encoding assumptions
        if df is None:
            try:
                # For CSV-like files that might be misnamed
                df = pd.read_csv(file_path, encoding='utf-8')
            except Exception as e:
                error_messages.append(f"csv utf-8: {str(e)}")
                try:
                    df = pd.read_csv(file_path, encoding='latin-1')
                except Exception as e2:
                    error_messages.append(f"csv latin-1: {str(e2)}")
        
        if df is None:
            return None, f"Failed to load file with all methods: {'; '.join(error_messages)}"
        
        if df.empty:
            return None, "Excel file is empty"
        
        # Clean column names (remove extra spaces, special characters)
        df.columns = df.columns.astype(str).str.strip()
        
        logger.info(f"Successfully loaded Excel file: {len(df)} rows, {len(df.columns)} columns")
        return df, f"Excel data loaded successfully. {len(df)} rows, {len(df.columns)} columns."
    
    except Exception as e:
        logger.error(f"Error loading CRM data: {e}")
        return None, f"Error loading CRM data: {str(e)}"
