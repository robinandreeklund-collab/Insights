"""Configuration Manager - Global access to system settings."""

from modules.core.settings_panel import SettingsPanel
from typing import Any, Dict


class ConfigManager:
    """Singleton-like manager for accessing system configuration."""
    
    _instance = None
    _settings_panel = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._settings_panel = SettingsPanel()
        return cls._instance
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            section: Settings section (e.g., 'general', 'display')
            key: Setting key
            default: Default value if not found
            
        Returns:
            Configuration value or default
        """
        value = self._settings_panel.get_setting(section, key)
        return value if value is not None else default
    
    def get_all(self) -> Dict:
        """Get all configuration settings.
        
        Returns:
            Dictionary with all settings
        """
        return self._settings_panel.load_settings()
    
    def reload(self):
        """Reload settings from file."""
        self._settings_panel = SettingsPanel()


# Global instance
config = ConfigManager()
