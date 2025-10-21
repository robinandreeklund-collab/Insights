"""Integration test for the complete CSV import and forecast flow."""

import pytest
import os
import tempfile
import shutil
from import_flow import import_and_process_csv
from modules.core.forecast_engine import get_forecast_summary, get_category_breakdown


class TestIntegrationFlow:
    """Test the complete end-to-end flow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_complete_csv_import_flow(self):
        """Test the complete CSV import, categorization, and save flow."""
        csv_path = "PERSONKONTO 880104-7591 - 2025-10-21 15.38.56.csv"
        
        # Skip if CSV doesn't exist
        if not os.path.exists(csv_path):
            pytest.skip("Test CSV file not found")
        
        # Run the import flow
        account_name, num_transactions = import_and_process_csv(csv_path, self.test_dir)
        
        # Verify results
        assert account_name == "PERSONKONTO 880104-7591"
        assert num_transactions == 3
        
        # Verify files were created
        assert os.path.exists(os.path.join(self.test_dir, "accounts.yaml"))
        assert os.path.exists(os.path.join(self.test_dir, "transactions.yaml"))
        
        # Load and verify accounts file
        import yaml
        with open(os.path.join(self.test_dir, "accounts.yaml"), 'r') as f:
            accounts_data = yaml.safe_load(f)
            assert 'accounts' in accounts_data
            assert len(accounts_data['accounts']) == 1
            assert accounts_data['accounts'][0]['name'] == account_name
        
        # Load and verify transactions file
        with open(os.path.join(self.test_dir, "transactions.yaml"), 'r') as f:
            transactions_data = yaml.safe_load(f)
            assert 'transactions' in transactions_data
            assert len(transactions_data['transactions']) == 3
            
            # Verify categorization
            for tx in transactions_data['transactions']:
                assert 'category' in tx
                assert 'subcategory' in tx
                assert tx['category'] != ''
                
                # Check specific categorizations
                if 'Nordea Vardagspaket' in tx['description']:
                    assert tx['category'] == 'Boende'
                    assert tx['subcategory'] == 'Bank & Avgifter'
                elif 'Överföring' in tx['description']:
                    assert tx['category'] == 'Överföringar'
    
    def test_forecast_after_import(self):
        """Test that forecast works after importing data."""
        csv_path = "PERSONKONTO 880104-7591 - 2025-10-21 15.38.56.csv"
        
        if not os.path.exists(csv_path):
            pytest.skip("Test CSV file not found")
        
        # Import data
        account_name, num_transactions = import_and_process_csv(csv_path, self.test_dir)
        
        # Get forecast
        transactions_file = os.path.join(self.test_dir, "transactions.yaml")
        summary = get_forecast_summary(31.06, transactions_file, forecast_days=7)
        
        # Verify forecast structure
        assert 'current_balance' in summary
        assert 'forecast' in summary
        assert 'avg_daily_income' in summary
        assert 'avg_daily_expenses' in summary
        assert len(summary['forecast']) == 8  # Today + 7 forecast days (current day + 7 future days)
        
        # Verify category breakdown
        breakdown = get_category_breakdown(transactions_file=transactions_file)
        assert isinstance(breakdown, dict)
        # Should have at least one category (Boende for Nordea fees)
        assert len(breakdown) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
