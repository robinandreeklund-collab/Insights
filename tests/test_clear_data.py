"""Unit tests for clear data functionality."""

import pytest
import os
import tempfile
import shutil
import yaml
from import_flow import clear_data_files


class TestClearDataFiles:
    """Test cases for clearing data files."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_clear_data_files_empty_files(self):
        """Test clearing when files don't exist yet."""
        # Should not raise exception
        clear_data_files(self.test_dir)
        
        # Files should be created
        assert not os.path.exists(os.path.join(self.test_dir, "transactions.yaml"))
        assert not os.path.exists(os.path.join(self.test_dir, "accounts.yaml"))
    
    def test_clear_data_files_with_data(self):
        """Test clearing files that contain data."""
        transactions_file = os.path.join(self.test_dir, "transactions.yaml")
        accounts_file = os.path.join(self.test_dir, "accounts.yaml")
        
        # Create files with data
        with open(transactions_file, 'w') as f:
            yaml.dump({'transactions': [
                {'id': 1, 'description': 'Test 1'},
                {'id': 2, 'description': 'Test 2'}
            ]}, f)
        
        with open(accounts_file, 'w') as f:
            yaml.dump({'accounts': [
                {'name': 'Account 1'},
                {'name': 'Account 2'}
            ]}, f)
        
        # Clear the files
        clear_data_files(self.test_dir)
        
        # Verify files are reset
        with open(transactions_file, 'r') as f:
            data = yaml.safe_load(f)
            assert data == {'transactions': []}
        
        with open(accounts_file, 'r') as f:
            data = yaml.safe_load(f)
            assert data == {'accounts': []}
    
    def test_clear_preserves_file_structure(self):
        """Test that clear maintains proper YAML structure."""
        transactions_file = os.path.join(self.test_dir, "transactions.yaml")
        accounts_file = os.path.join(self.test_dir, "accounts.yaml")
        
        # Create initial files
        with open(transactions_file, 'w') as f:
            yaml.dump({'transactions': [{'id': 1}]}, f)
        
        with open(accounts_file, 'w') as f:
            yaml.dump({'accounts': [{'name': 'test'}]}, f)
        
        # Clear
        clear_data_files(self.test_dir)
        
        # Verify structure is maintained
        with open(transactions_file, 'r') as f:
            content = f.read()
            assert 'transactions:' in content
        
        with open(accounts_file, 'r') as f:
            content = f.read()
            assert 'accounts:' in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
