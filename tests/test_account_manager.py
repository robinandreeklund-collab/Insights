"""Unit tests for account_manager module."""

import pytest
import tempfile
import os
import shutil
from modules.core.account_manager import AccountManager


class TestAccountManager:
    """Test cases for AccountManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a temporary directory for test YAML files
        self.test_dir = tempfile.mkdtemp()
        self.manager = AccountManager(yaml_dir=self.test_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_account_manager_initialization(self):
        """Test that AccountManager can be instantiated."""
        assert self.manager is not None
        assert isinstance(self.manager, AccountManager)
        assert os.path.exists(self.test_dir)
    
    def test_create_account(self):
        """Test creating a new account."""
        result = self.manager.create_account("Test Account", "test.csv", balance=100.0)
        
        assert result is not None
        assert isinstance(result, dict)
        assert result['name'] == "Test Account"
        assert result['source_file'] == "test.csv"
        assert result['balance'] == 100.0
        assert 'created_at' in result
    
    def test_create_duplicate_account(self):
        """Test that creating duplicate account returns existing account."""
        account1 = self.manager.create_account("Test Account", "test.csv")
        account2 = self.manager.create_account("Test Account", "test2.csv")
        
        # Should return the same account
        assert account1['name'] == account2['name']
        assert account1['source_file'] == account2['source_file']
    
    def test_delete_account(self):
        """Test deleting an account."""
        self.manager.create_account("Test Account", "test.csv")
        result = self.manager.delete_account("Test Account")
        
        assert result is True
        
        # Verify account is gone
        accounts = self.manager.get_accounts()
        assert len(accounts) == 0
    
    def test_delete_nonexistent_account(self):
        """Test deleting a nonexistent account."""
        result = self.manager.delete_account("Nonexistent")
        assert result is False
    
    def test_get_accounts(self):
        """Test getting all accounts."""
        self.manager.create_account("Account 1", "file1.csv")
        self.manager.create_account("Account 2", "file2.csv")
        
        accounts = self.manager.get_accounts()
        assert len(accounts) == 2
        assert any(a['name'] == 'Account 1' for a in accounts)
        assert any(a['name'] == 'Account 2' for a in accounts)
    
    def test_add_and_get_transactions(self):
        """Test adding and retrieving transactions."""
        # Create account
        self.manager.create_account("Test Account", "test.csv")
        
        # Add transactions
        transactions = [
            {
                'date': '2025-10-01',
                'description': 'Test transaction',
                'amount': -100.0,
                'account': 'Test Account'
            }
        ]
        self.manager.add_transactions(transactions)
        
        # Get transactions
        result = self.manager.get_account_transactions("Test Account")
        assert len(result) == 1
        assert result[0]['description'] == 'Test transaction'
        assert 'id' in result[0]  # Should have generated ID
    
    def test_categorize_transaction(self):
        """Test manually categorizing a transaction."""
        tx = {"id": "1", "amount": 100, "description": "Test"}
        result = self.manager.categorize_transaction(tx, "Food", "Groceries")
        
        assert result is not None
        assert isinstance(result, dict)
        assert result['category'] == 'Food'
        assert result['subcategory'] == 'Groceries'
        assert result['categorized_manually'] is True
    
    def test_train_ai_from_manual_input(self):
        """Test training AI from manual categorization."""
        tx = {
            "id": "1",
            "description": "ICA Maxi",
            "category": "Mat & Dryck",
            "subcategory": "Matinköp",
            "categorized_manually": True
        }
        
        # Should not raise exception
        self.manager.train_ai_from_manual_input(tx)
        
        # Verify training data was saved
        import yaml
        training_file = os.path.join(self.test_dir, "training_data.yaml")
        assert os.path.exists(training_file)
        
        with open(training_file, 'r') as f:
            data = yaml.safe_load(f)
            assert 'training_data' in data
            assert len(data['training_data']) == 1
            assert data['training_data'][0]['description'] == 'ICA Maxi'
    
    def test_update_account_balance(self):
        """Test updating account balance."""
        self.manager.create_account("Test Account", "test.csv", balance=100.0)
        self.manager.update_account_balance("Test Account", 200.0)
        
        account = self.manager.get_account_by_name("Test Account")
        assert account['balance'] == 200.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
