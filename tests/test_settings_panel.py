"""Tests for settings_panel module."""

import unittest
import os
import yaml
import tempfile
import shutil

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.core.settings_panel import SettingsPanel


class TestSettingsPanel(unittest.TestCase):
    """Test cases for SettingsPanel class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for test YAML files
        self.test_dir = tempfile.mkdtemp()
        self.panel = SettingsPanel(yaml_dir=self.test_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
    
    def test_settings_panel_initialization(self):
        """Test SettingsPanel initialization."""
        self.assertIsNotNone(self.panel)
        self.assertEqual(self.panel.yaml_dir, self.test_dir)
        
        # Check that settings file was created with defaults
        settings_file = os.path.join(self.test_dir, 'settings_panel.yaml')
        self.assertTrue(os.path.exists(settings_file))
    
    def test_load_settings(self):
        """Test loading settings."""
        settings = self.panel.load_settings()
        
        self.assertIsNotNone(settings)
        self.assertIn('general', settings)
        self.assertIn('forecast', settings)
        self.assertIn('categorization', settings)
        self.assertIn('notifications', settings)
        self.assertIn('display', settings)
    
    def test_get_setting(self):
        """Test getting a specific setting."""
        currency = self.panel.get_setting('general', 'currency')
        self.assertEqual(currency, 'SEK')
        
        decimals = self.panel.get_setting('general', 'decimal_places')
        self.assertEqual(decimals, 2)
    
    def test_get_setting_nonexistent(self):
        """Test getting non-existent setting."""
        value = self.panel.get_setting('nonexistent', 'key')
        self.assertIsNone(value)
    
    def test_update_setting(self):
        """Test updating a specific setting."""
        result = self.panel.update_setting('general', 'currency', 'EUR')
        self.assertTrue(result)
        
        # Verify update
        currency = self.panel.get_setting('general', 'currency')
        self.assertEqual(currency, 'EUR')
    
    def test_update_settings_multiple(self):
        """Test updating multiple settings at once."""
        updates = {
            'general': {
                'currency': 'USD',
                'decimal_places': 4
            },
            'display': {
                'items_per_page': 100
            }
        }
        
        result = self.panel.update_settings(updates)
        self.assertTrue(result)
        
        # Verify updates
        currency = self.panel.get_setting('general', 'currency')
        decimals = self.panel.get_setting('general', 'decimal_places')
        items = self.panel.get_setting('display', 'items_per_page')
        
        self.assertEqual(currency, 'USD')
        self.assertEqual(decimals, 4)
        self.assertEqual(items, 100)
    
    def test_reset_to_defaults_all(self):
        """Test resetting all settings to defaults."""
        # First, modify some settings
        self.panel.update_setting('general', 'currency', 'EUR')
        self.panel.update_setting('display', 'items_per_page', 100)
        
        # Reset
        result = self.panel.reset_to_defaults()
        self.assertTrue(result)
        
        # Verify reset
        currency = self.panel.get_setting('general', 'currency')
        items = self.panel.get_setting('display', 'items_per_page')
        
        self.assertEqual(currency, 'SEK')
        self.assertEqual(items, 50)
    
    def test_reset_to_defaults_section(self):
        """Test resetting specific section to defaults."""
        # Modify settings
        self.panel.update_setting('general', 'currency', 'EUR')
        self.panel.update_setting('display', 'items_per_page', 100)
        
        # Reset only general section
        result = self.panel.reset_to_defaults('general')
        self.assertTrue(result)
        
        # Verify reset
        currency = self.panel.get_setting('general', 'currency')
        items = self.panel.get_setting('display', 'items_per_page')
        
        self.assertEqual(currency, 'SEK')  # Reset
        self.assertEqual(items, 100)  # Not reset
    
    def test_get_ui_config(self):
        """Test getting UI configuration."""
        config = self.panel.get_ui_config()
        
        self.assertIsNotNone(config)
        self.assertIn('display', config)
        self.assertIn('general', config)
        self.assertIn('forecast', config)
    
    def test_get_notification_config(self):
        """Test getting notification configuration."""
        config = self.panel.get_notification_config()
        
        self.assertIsNotNone(config)
        self.assertIn('bill_reminders', config)
        self.assertIn('low_balance_alert', config)
        self.assertIn('reminder_days_before', config)
        self.assertIn('low_balance_threshold', config)
    
    def test_validate_setting_valid(self):
        """Test validating valid settings."""
        valid, msg = self.panel.validate_setting('general', 'decimal_places', 2)
        self.assertTrue(valid)
        self.assertEqual(msg, "")
        
        valid, msg = self.panel.validate_setting('forecast', 'default_days', 30)
        self.assertTrue(valid)
        self.assertEqual(msg, "")
    
    def test_validate_setting_invalid(self):
        """Test validating invalid settings."""
        valid, msg = self.panel.validate_setting('general', 'decimal_places', 10)
        self.assertFalse(valid)
        
        valid, msg = self.panel.validate_setting('forecast', 'default_days', 500)
        self.assertFalse(valid)
        
        valid, msg = self.panel.validate_setting('display', 'items_per_page', -10)
        self.assertFalse(valid)
    
    def test_validate_setting_no_rule(self):
        """Test validating setting with no validation rule."""
        valid, msg = self.panel.validate_setting('general', 'currency', 'EUR')
        self.assertTrue(valid)
        self.assertEqual(msg, "")
    
    def test_default_values(self):
        """Test that default values are correct."""
        settings = self.panel.load_settings()
        
        # Check default values
        self.assertEqual(settings['general']['currency'], 'SEK')
        self.assertEqual(settings['general']['decimal_places'], 2)
        self.assertEqual(settings['forecast']['default_days'], 30)
        self.assertTrue(settings['categorization']['auto_categorize'])
        self.assertEqual(settings['display']['items_per_page'], 50)
        self.assertTrue(settings['notifications']['bill_reminders'])


if __name__ == '__main__':
    unittest.main()
