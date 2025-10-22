"""Unit tests for CategoryManager."""

import pytest
import os
import tempfile
import shutil
from modules.core.category_manager import CategoryManager


class TestCategoryManager:
    """Test cases for CategoryManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.manager = CategoryManager(yaml_dir=self.test_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_initialization(self):
        """Test CategoryManager initialization."""
        assert os.path.exists(self.test_dir)
        assert os.path.exists(self.manager.categories_file)
    
    def test_get_default_categories(self):
        """Test getting default categories."""
        categories = self.manager.get_categories()
        assert 'Mat & Dryck' in categories
        assert 'Transport' in categories
        assert 'Övrigt' in categories
        assert len(categories) >= 7
    
    def test_add_category(self):
        """Test adding a new category."""
        success = self.manager.add_category('Hälsa', ['Läkare', 'Medicin'])
        assert success is True
        
        categories = self.manager.get_categories()
        assert 'Hälsa' in categories
        assert 'Läkare' in categories['Hälsa']
        assert 'Medicin' in categories['Hälsa']
    
    def test_add_duplicate_category(self):
        """Test adding a duplicate category."""
        self.manager.add_category('Test')
        success = self.manager.add_category('Test')
        assert success is False
    
    def test_add_empty_category(self):
        """Test adding an empty category name."""
        success = self.manager.add_category('')
        assert success is False
        
        success = self.manager.add_category('   ')
        assert success is False
    
    def test_add_subcategory(self):
        """Test adding a subcategory to existing category."""
        success = self.manager.add_subcategory('Mat & Dryck', 'Snabbmat')
        assert success is True
        
        categories = self.manager.get_categories()
        assert 'Snabbmat' in categories['Mat & Dryck']
    
    def test_add_subcategory_to_nonexistent_category(self):
        """Test adding subcategory to non-existent category."""
        success = self.manager.add_subcategory('Nonexistent', 'Subcat')
        assert success is False
    
    def test_add_duplicate_subcategory(self):
        """Test adding a duplicate subcategory."""
        self.manager.add_subcategory('Transport', 'Test')
        success = self.manager.add_subcategory('Transport', 'Test')
        assert success is False
    
    def test_add_empty_subcategory(self):
        """Test adding an empty subcategory."""
        success = self.manager.add_subcategory('Transport', '')
        assert success is False
        
        success = self.manager.add_subcategory('Transport', '   ')
        assert success is False
    
    def test_remove_custom_category(self):
        """Test removing a custom category."""
        self.manager.add_category('Custom')
        success = self.manager.remove_category('Custom')
        assert success is True
        
        categories = self.manager.get_categories()
        assert 'Custom' not in categories
    
    def test_remove_default_category(self):
        """Test that default categories cannot be removed."""
        success = self.manager.remove_category('Mat & Dryck')
        assert success is False
        
        categories = self.manager.get_categories()
        assert 'Mat & Dryck' in categories
    
    def test_remove_subcategory(self):
        """Test removing a subcategory."""
        self.manager.add_subcategory('Transport', 'TestSubcat')
        success = self.manager.remove_subcategory('Transport', 'TestSubcat')
        assert success is True
        
        categories = self.manager.get_categories()
        assert 'TestSubcat' not in categories['Transport']
    
    def test_reset_to_defaults(self):
        """Test resetting categories to defaults."""
        # Add custom categories
        self.manager.add_category('Custom1')
        self.manager.add_category('Custom2')
        
        # Reset
        success = self.manager.reset_to_defaults()
        assert success is True
        
        # Check defaults are restored
        categories = self.manager.get_categories()
        assert 'Custom1' not in categories
        assert 'Custom2' not in categories
        assert 'Mat & Dryck' in categories
    
    def test_persistence(self):
        """Test that categories persist across instances."""
        # Add category with first instance
        self.manager.add_category('Persistent', ['Test'])
        
        # Create new instance
        manager2 = CategoryManager(yaml_dir=self.test_dir)
        categories = manager2.get_categories()
        
        assert 'Persistent' in categories
        assert 'Test' in categories['Persistent']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
