"""Settings Panel - Hanterar användarinställningar och UI-konfiguration."""

import os
import yaml
from typing import Dict, Any, Optional


class SettingsPanel:
    """Hanterar användarinställningar, toggles och konfiguration."""
    
    def __init__(self, yaml_dir: str = "yaml"):
        """Initialisera settings panel."""
        self.yaml_dir = yaml_dir
        self.settings_file = os.path.join(yaml_dir, "settings_panel.yaml")
        
        # Ensure yaml directory exists
        os.makedirs(yaml_dir, exist_ok=True)
        
        # Initialize with defaults if not exists
        if not os.path.exists(self.settings_file):
            self._initialize_defaults()
    
    def _load_yaml(self, filepath: str) -> dict:
        """Load YAML file or return default structure."""
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                return data
        return {}
    
    def _save_yaml(self, filepath: str, data: dict) -> None:
        """Save data to YAML file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    def _initialize_defaults(self) -> None:
        """Initialize settings with default values."""
        defaults = {
            'general': {
                'currency': 'SEK',
                'date_format': 'YYYY-MM-DD',
                'decimal_places': 2,
                'theme': 'light'
            },
            'forecast': {
                'default_days': 30,
                'include_bills': True,
                'include_income': True,
                'confidence_threshold': 0.7
            },
            'categorization': {
                'auto_categorize': True,
                'ai_enabled': True,
                'min_confidence': 0.6,
                'manual_review_threshold': 0.5
            },
            'notifications': {
                'bill_reminders': True,
                'reminder_days_before': 3,
                'low_balance_alert': True,
                'low_balance_threshold': 1000.0
            },
            'display': {
                'items_per_page': 50,
                'auto_refresh': True,
                'refresh_interval': 5000,
                'show_pie_chart': True,
                'show_forecast_graph': True
            },
            'budget': {
                'enabled': False,
                'monthly_limit': 0.0,
                'category_limits': {}
            }
        }
        
        self._save_yaml(self.settings_file, defaults)
    
    def load_settings(self) -> Dict[str, Any]:
        """Load all settings.
        
        Returns:
            Dictionary with all settings
        """
        return self._load_yaml(self.settings_file)
    
    def get_setting(self, section: str, key: str) -> Any:
        """Get a specific setting value.
        
        Args:
            section: Settings section (e.g., 'general', 'forecast')
            key: Setting key
            
        Returns:
            Setting value or None if not found
        """
        settings = self.load_settings()
        section_data = settings.get(section, {})
        return section_data.get(key)
    
    def update_setting(self, section: str, key: str, value: Any) -> bool:
        """Update a specific setting.
        
        Args:
            section: Settings section
            key: Setting key
            value: New value
            
        Returns:
            True if updated successfully
        """
        settings = self.load_settings()
        
        if section not in settings:
            settings[section] = {}
        
        settings[section][key] = value
        self._save_yaml(self.settings_file, settings)
        
        return True
    
    def update_settings(self, updates: Dict[str, Dict[str, Any]]) -> bool:
        """Update multiple settings at once.
        
        Args:
            updates: Dictionary of section -> {key: value} updates
            
        Returns:
            True if updated successfully
        """
        settings = self.load_settings()
        
        for section, section_updates in updates.items():
            if section not in settings:
                settings[section] = {}
            
            for key, value in section_updates.items():
                settings[section][key] = value
        
        self._save_yaml(self.settings_file, settings)
        
        return True
    
    def reset_to_defaults(self, section: str = None) -> bool:
        """Reset settings to default values.
        
        Args:
            section: Optional section to reset. If None, resets all.
            
        Returns:
            True if reset successfully
        """
        if section is None:
            # Reset all
            self._initialize_defaults()
        else:
            # Reset specific section
            self._initialize_defaults()
            defaults = self.load_settings()
            
            if section in defaults:
                current = self.load_settings()
                current[section] = defaults[section]
                self._save_yaml(self.settings_file, current)
        
        return True
    
    def get_ui_config(self) -> Dict[str, Any]:
        """Get UI configuration settings.
        
        Returns:
            Dictionary with UI-related settings
        """
        settings = self.load_settings()
        
        return {
            'display': settings.get('display', {}),
            'general': settings.get('general', {}),
            'forecast': {
                'default_days': settings.get('forecast', {}).get('default_days', 30)
            }
        }
    
    def get_notification_config(self) -> Dict[str, Any]:
        """Get notification configuration.
        
        Returns:
            Dictionary with notification settings
        """
        settings = self.load_settings()
        return settings.get('notifications', {})
    
    def validate_setting(self, section: str, key: str, value: Any) -> tuple[bool, str]:
        """Validate a setting value.
        
        Args:
            section: Settings section
            key: Setting key
            value: Value to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validation rules
        validation_rules = {
            'general': {
                'decimal_places': lambda x: isinstance(x, int) and 0 <= x <= 4,
            },
            'forecast': {
                'default_days': lambda x: isinstance(x, int) and 1 <= x <= 365,
                'confidence_threshold': lambda x: isinstance(x, (int, float)) and 0 <= x <= 1,
            },
            'categorization': {
                'min_confidence': lambda x: isinstance(x, (int, float)) and 0 <= x <= 1,
                'manual_review_threshold': lambda x: isinstance(x, (int, float)) and 0 <= x <= 1,
            },
            'notifications': {
                'reminder_days_before': lambda x: isinstance(x, int) and 0 <= x <= 30,
                'low_balance_threshold': lambda x: isinstance(x, (int, float)) and x >= 0,
            },
            'display': {
                'items_per_page': lambda x: isinstance(x, int) and 1 <= x <= 200,
                'refresh_interval': lambda x: isinstance(x, int) and 1000 <= x <= 60000,
            }
        }
        
        if section in validation_rules and key in validation_rules[section]:
            validator = validation_rules[section][key]
            if not validator(value):
                return False, f"Invalid value for {section}.{key}"
        
        return True, ""


def load_settings(yaml_dir: str = "yaml") -> Dict[str, Any]:
    """Wrapper function to load settings."""
    panel = SettingsPanel(yaml_dir)
    return panel.load_settings()


def update_setting(section: str, key: str, value: Any, yaml_dir: str = "yaml") -> bool:
    """Wrapper function to update a setting."""
    panel = SettingsPanel(yaml_dir)
    return panel.update_setting(section, key, value)


def get_setting(section: str, key: str, yaml_dir: str = "yaml") -> Any:
    """Wrapper function to get a setting."""
    panel = SettingsPanel(yaml_dir)
    return panel.get_setting(section, key)
