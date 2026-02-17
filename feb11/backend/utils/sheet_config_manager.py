"""
Sheet Configuration Manager

Manages Excel sheet selection preferences for each invoice template.
Allows users to configure which sheet to read from without editing Python files.
"""

import json
from pathlib import Path
from typing import Optional, Union


class SheetConfigManager:
    """
    Manages sheet selection configuration for invoice templates.
    
    Configuration is stored per-template in JSON files under user_configs/ directory.
    Falls back to context file defaults if no user config exists.
    """
    
    def __init__(self, config_dir: str = "user_configs"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def get_sheet_config(self, template_name: str) -> dict:
        """
        Get sheet configuration for a template.
        
        Args:
            template_name: Name of the template (e.g., 'tax_invoice', 'bill_invoice')
        
        Returns:
            dict with keys:
                - mode: 'auto' | 'index' | 'name'
                - value: None | int | str (depending on mode)
                - label: Human-readable description
        """
        config_file = self.config_dir / f"{template_name}_sheet_config.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Error loading sheet config: {e}")
        
        # Return default config
        return self._get_default_config(template_name)
    
    def set_sheet_config(self, template_name: str, mode: str, value: Optional[Union[int, str]] = None):
        """
        Save sheet configuration for a template.
        
        Args:
            template_name: Name of the template
            mode: 'auto' | 'index' | 'name'
            value: Sheet index (int) or sheet name (str), or None for auto
        """
        config = {
            "mode": mode,
            "value": value,
            "label": self._generate_label(mode, value)
        }
        
        config_file = self.config_dir / f"{template_name}_sheet_config.json"
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"✓ Saved sheet config for {template_name}: {config['label']}")
        except Exception as e:
            print(f"❌ Error saving sheet config: {e}")
    
    def get_sheet_value_for_agent(self, template_name: str) -> Optional[Union[int, str]]:
        """
        Get the sheet value to pass to the agent.
        
        Returns:
            - None for auto-detect
            - int for sheet index
            - str for sheet name
        """
        config = self.get_sheet_config(template_name)
        
        if config['mode'] == 'auto':
            return None
        else:
            return config['value']
    
    def _get_default_config(self, template_name: str) -> dict:
        """Get default configuration based on template name"""
        # Default to context file values
        if template_name == 'tax_invoice':
            return {
                "mode": "index",
                "value": 0,
                "label": "Sheet 1 (First sheet)"
            }
        elif template_name == 'bill_invoice':
            return {
                "mode": "index",
                "value": 1,
                "label": "Sheet 2 (Second sheet)"
            }
        else:
            return {
                "mode": "auto",
                "value": None,
                "label": "Auto-detect (first non-empty sheet)"
            }
    
    def _generate_label(self, mode: str, value: Optional[Union[int, str]]) -> str:
        """Generate human-readable label for configuration"""
        if mode == 'auto':
            return "Auto-detect (first non-empty sheet)"
        elif mode == 'index':
            if value == 0:
                return "Sheet 1 (First sheet)"
            elif value == 1:
                return "Sheet 2 (Second sheet)"
            else:
                return f"Sheet {value + 1} (Index {value})"
        elif mode == 'name':
            return f"Sheet named '{value}'"
        else:
            return "Unknown configuration"
    
    def get_available_sheets(self, file_path: str) -> list:
        """
        Get list of available sheets in an Excel file.
        
        Args:
            file_path: Path to Excel file
        
        Returns:
            List of sheet names
        """
        try:
            import pandas as pd
            xl = pd.ExcelFile(file_path)
            return xl.sheet_names
        except Exception as e:
            print(f"⚠️  Error reading Excel file: {e}")
            return []
    
    def reset_to_default(self, template_name: str):
        """Reset configuration to default (delete user config file)"""
        config_file = self.config_dir / f"{template_name}_sheet_config.json"
        
        if config_file.exists():
            try:
                config_file.unlink()
                print(f"✓ Reset {template_name} sheet config to default")
            except Exception as e:
                print(f"❌ Error resetting config: {e}")


# Global instance
_sheet_config_manager = None

def get_sheet_config_manager() -> SheetConfigManager:
    """Get global SheetConfigManager instance"""
    global _sheet_config_manager
    if _sheet_config_manager is None:
        _sheet_config_manager = SheetConfigManager()
    return _sheet_config_manager
