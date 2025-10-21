"""Unit tests for account_manager module."""

import pytest
from modules.core.account_manager import AccountManager


class TestAccountManager:
    """Test cases for AccountManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = AccountManager()
    
    def test_account_manager_initialization(self):
        """Test that AccountManager can be instantiated."""
        assert self.manager is not None
        assert isinstance(self.manager, AccountManager)
    
    def test_create_account_stub(self):
        """Test create_account method exists and has correct signature."""
        # This is a stub test - just verifying the method exists
        result = self.manager.create_account("Test Account", "test.csv")
        # In Sprint 1, we expect None or pass behavior
        assert result is None or isinstance(result, dict)
    
    def test_delete_account_stub(self):
        """Test delete_account method exists and has correct signature."""
        result = self.manager.delete_account("Test Account")
        # In Sprint 1, we expect None or pass behavior
        assert result is None or isinstance(result, bool)
    
    def test_get_account_transactions_stub(self):
        """Test get_account_transactions method exists and has correct signature."""
        result = self.manager.get_account_transactions("Test Account")
        # In Sprint 1, we expect None or pass behavior
        assert result is None or isinstance(result, list)
    
    def test_categorize_transaction_stub(self):
        """Test categorize_transaction method exists and has correct signature."""
        tx = {"id": "1", "amount": 100}
        result = self.manager.categorize_transaction(tx, "Food", "Groceries")
        # In Sprint 1, we expect None or pass behavior
        assert result is None or isinstance(result, dict)
    
    def test_train_ai_from_manual_input_stub(self):
        """Test train_ai_from_manual_input method exists and has correct signature."""
        tx = {"id": "1", "category": "Food"}
        result = self.manager.train_ai_from_manual_input(tx)
        # In Sprint 1, we expect None (no return value)
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
