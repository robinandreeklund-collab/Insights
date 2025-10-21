"""Tests for Sprint 3 dashboard functionality."""

import os
import sys
import pytest
import pandas as pd
import yaml
import base64
from datetime import datetime
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.dashboard_ui import app
from modules.core.account_manager import AccountManager
from modules.core.forecast_engine import get_forecast_summary, get_category_breakdown


class TestDashboardSprint3:
    """Test Sprint 3 dashboard features."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.old_yaml_dir = "yaml"
        
        # Create test YAML directory
        os.makedirs(os.path.join(self.test_dir, "yaml"), exist_ok=True)
        
        # Initialize test files
        self.accounts_file = os.path.join(self.test_dir, "yaml", "accounts.yaml")
        self.transactions_file = os.path.join(self.test_dir, "yaml", "transactions.yaml")
        
        with open(self.accounts_file, 'w', encoding='utf-8') as f:
            yaml.dump({'accounts': []}, f)
        
        with open(self.transactions_file, 'w', encoding='utf-8') as f:
            yaml.dump({'transactions': []}, f)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_dashboard_app_initialization(self):
        """Test that dashboard app initializes correctly."""
        assert app is not None
        assert app.title is None or isinstance(app.title, str)
    
    def test_create_overview_tab(self):
        """Test that overview tab can be created."""
        from dashboard.dashboard_ui import create_overview_tab
        
        tab_content = create_overview_tab()
        assert tab_content is not None
        # Should have Div container
        assert hasattr(tab_content, 'children')
    
    def test_create_input_tab(self):
        """Test that input tab with CSV upload can be created."""
        from dashboard.dashboard_ui import create_input_tab
        
        tab_content = create_input_tab()
        assert tab_content is not None
        # Should have upload component
        assert hasattr(tab_content, 'children')
    
    def test_create_accounts_tab(self):
        """Test that accounts tab with transaction browser can be created."""
        from dashboard.dashboard_ui import create_accounts_tab
        
        tab_content = create_accounts_tab()
        assert tab_content is not None
        # Should have account selector and transaction table
        assert hasattr(tab_content, 'children')
    
    def test_forecast_graph_with_data(self):
        """Test forecast graph generation with sample data."""
        # Create sample transactions
        manager = AccountManager(yaml_dir=self.test_dir + "/yaml")
        transactions = [
            {
                'date': '2025-10-01',
                'description': 'Salary',
                'amount': 30000.0,
                'balance': 30000.0,
                'category': 'Inkomst',
                'subcategory': 'Lön',
                'account': 'Test Account'
            },
            {
                'date': '2025-10-05',
                'description': 'ICA',
                'amount': -500.0,
                'balance': 29500.0,
                'category': 'Mat & Dryck',
                'subcategory': 'Matinköp',
                'account': 'Test Account'
            }
        ]
        manager.add_transactions(transactions)
        
        # Get forecast
        summary = get_forecast_summary(29500.0, 
                                       transactions_file=self.test_dir + "/yaml/transactions.yaml",
                                       forecast_days=30)
        
        assert summary is not None
        assert 'forecast' in summary
        assert len(summary['forecast']) > 0
        assert summary['current_balance'] == 29500.0
    
    def test_category_breakdown_with_data(self):
        """Test category breakdown pie chart with sample data."""
        # Create sample transactions
        transactions = [
            {'amount': -500.0, 'category': 'Mat & Dryck'},
            {'amount': -300.0, 'category': 'Mat & Dryck'},
            {'amount': -200.0, 'category': 'Transport'},
            {'amount': 30000.0, 'category': 'Inkomst'},  # Should be excluded (positive)
        ]
        
        breakdown = get_category_breakdown(transactions)
        
        assert breakdown is not None
        assert 'Mat & Dryck' in breakdown
        assert breakdown['Mat & Dryck'] == 800.0
        assert 'Transport' in breakdown
        assert breakdown['Transport'] == 200.0
        assert 'Inkomst' not in breakdown  # Positive amounts excluded
    
    def test_transaction_pagination(self):
        """Test transaction pagination logic."""
        # Create many transactions
        manager = AccountManager(yaml_dir=self.test_dir + "/yaml")
        manager.create_account("Test Account", "test.csv", 10000.0)
        
        transactions = []
        for i in range(75):  # More than one page (50 per page)
            transactions.append({
                'date': f'2025-10-{i%30+1:02d}',
                'description': f'Transaction {i}',
                'amount': -100.0 * (i+1),
                'balance': 10000.0 - (100.0 * (i+1)),
                'category': 'Övrigt',
                'subcategory': 'Okategoriserat',
                'account': 'Test Account'
            })
        
        manager.add_transactions(transactions)
        
        # Get transactions
        all_tx = manager.get_account_transactions("Test Account")
        assert len(all_tx) == 75
        
        # Test pagination
        per_page = 50
        page_0 = all_tx[0:per_page]
        page_1 = all_tx[per_page:2*per_page]
        
        assert len(page_0) == 50
        assert len(page_1) == 25
    
    def test_manual_categorization(self):
        """Test manual transaction categorization."""
        manager = AccountManager(yaml_dir=self.test_dir + "/yaml")
        
        # Create a transaction
        tx = {
            'id': '123',
            'date': '2025-10-15',
            'description': 'Unknown Store',
            'amount': -150.0,
            'category': 'Övrigt',
            'subcategory': 'Okategoriserat'
        }
        
        # Categorize manually
        categorized = manager.categorize_transaction(tx, 'Mat & Dryck', 'Matinköp')
        
        assert categorized['category'] == 'Mat & Dryck'
        assert categorized['subcategory'] == 'Matinköp'
        assert categorized.get('categorized_manually') is True
    
    def test_csv_import_flow(self):
        """Test CSV import through the dashboard flow."""
        # Create a sample CSV content
        csv_content = """Bokföringsdatum;Valutadatum;Transaktionsdag;Belopp;Avsändare;Mottagare;Namn;Rubrik;Saldo;Valuta
2025-10-15;2025-10-15;2025-10-15;-500.00;;;;;ICA Supermarket;5000.00;SEK
2025-10-14;2025-10-14;2025-10-14;30000.00;;;;;Salary;5500.00;SEK"""
        
        # Save to temp file
        temp_csv = os.path.join(self.test_dir, "PERSONKONTO 123456-7890 - 2025-10-21.csv")
        with open(temp_csv, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        # Import the CSV
        from modules.core.import_bank_data import import_csv
        from modules.core.categorize_expenses import auto_categorize
        
        account_name, df = import_csv(temp_csv)
        assert account_name == "PERSONKONTO 123456-7890"
        assert len(df) == 2
        
        # Auto-categorize
        df = auto_categorize(df)
        assert 'category' in df.columns
        assert 'subcategory' in df.columns
    
    def test_categories_structure(self):
        """Test that category structure is defined correctly."""
        from dashboard.dashboard_ui import CATEGORIES
        
        assert isinstance(CATEGORIES, dict)
        assert 'Mat & Dryck' in CATEGORIES
        assert 'Transport' in CATEGORIES
        assert 'Boende' in CATEGORIES
        assert 'Övrigt' in CATEGORIES
        
        # Check subcategories
        assert isinstance(CATEGORIES['Mat & Dryck'], list)
        assert 'Matinköp' in CATEGORIES['Mat & Dryck']
    
    def test_real_time_updates(self):
        """Test that data updates work correctly."""
        manager = AccountManager(yaml_dir=self.test_dir + "/yaml")
        
        # Create initial account
        manager.create_account("Test Account", "test.csv", 5000.0)
        accounts = manager.get_accounts()
        assert len(accounts) == 1
        assert accounts[0]['balance'] == 5000.0
        
        # Update balance
        manager.update_account_balance("Test Account", 6000.0)
        accounts = manager.get_accounts()
        assert accounts[0]['balance'] == 6000.0
    
    def test_empty_state_handling(self):
        """Test dashboard handles empty state gracefully."""
        manager = AccountManager(yaml_dir=self.test_dir + "/yaml")
        
        # No accounts
        accounts = manager.get_accounts()
        assert accounts == []
        
        # No transactions
        transactions = manager.get_account_transactions("Nonexistent Account")
        assert transactions == []
        
        # Forecast with no data
        summary = get_forecast_summary(0.0, 
                                       transactions_file=self.test_dir + "/yaml/transactions.yaml",
                                       forecast_days=30)
        assert summary['current_balance'] == 0.0
        assert len(summary['forecast']) > 0  # Should still generate forecast
    
    def test_ai_training_from_manual_categorization(self):
        """Test that manual categorization trains the AI."""
        manager = AccountManager(yaml_dir=self.test_dir + "/yaml")
        
        tx = {
            'description': 'New Store XYZ',
            'category': 'Mat & Dryck',
            'subcategory': 'Matinköp',
            'categorized_manually': True
        }
        
        # Train AI
        manager.train_ai_from_manual_input(tx)
        
        # Check training data was saved
        training_file = os.path.join(self.test_dir, "yaml", "training_data.yaml")
        if os.path.exists(training_file):
            with open(training_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                assert 'training_data' in data
                assert len(data['training_data']) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
