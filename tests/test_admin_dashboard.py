"""Unit tests for admin dashboard module."""

import pytest
import os
import tempfile
import shutil
import yaml
from datetime import datetime, timedelta
from modules.core.admin_dashboard import AdminDashboard


class TestAdminDashboard:
    """Test cases for admin dashboard module."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.dashboard = AdminDashboard(yaml_dir=self.test_dir)
        
        # Create sample transactions
        self.sample_transactions = {
            'transactions': [
                {
                    'id': 'tx1',
                    'account': 'Test Account',
                    'date': '2025-01-15',
                    'amount': -150.0,
                    'description': 'ICA Supermarket',
                    'category': 'Mat & Dryck',
                    'subcategory': 'Matinköp',
                    'source': 'import.csv'
                },
                {
                    'id': 'tx2',
                    'account': 'Test Account',
                    'date': '2025-01-16',
                    'amount': -75.0,
                    'description': 'Shell Bensin',
                    'category': '',
                    'subcategory': '',
                    'source': 'import.csv'
                },
                {
                    'id': 'tx3',
                    'account': 'Another Account',
                    'date': '2025-01-17',
                    'amount': 5000.0,
                    'description': 'Lön',
                    'category': 'Inkomst',
                    'subcategory': 'Lön',
                    'source': 'manual'
                },
                {
                    'id': 'tx4',
                    'account': 'Test Account',
                    'date': '2025-01-18',
                    'amount': -200.0,
                    'description': 'Restaurang',
                    'category': 'Okategoriserat',
                    'subcategory': '',
                    'source': 'amex.csv'
                }
            ]
        }
        
        # Save sample transactions
        with open(self.dashboard.transactions_file, 'w', encoding='utf-8') as f:
            yaml.dump(self.sample_transactions, f)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_initialization(self):
        """Test AdminDashboard initialization."""
        assert self.dashboard.yaml_dir == self.test_dir
        assert os.path.exists(self.test_dir)
    
    def test_get_all_transactions_no_filter(self):
        """Test getting all transactions without filters."""
        transactions = self.dashboard.get_all_transactions()
        assert len(transactions) == 4
    
    def test_get_all_transactions_filter_by_source(self):
        """Test filtering transactions by source."""
        transactions = self.dashboard.get_all_transactions({'source': 'import.csv'})
        assert len(transactions) == 2
        assert all(tx['source'] == 'import.csv' for tx in transactions)
    
    def test_get_all_transactions_filter_by_date(self):
        """Test filtering transactions by date range."""
        transactions = self.dashboard.get_all_transactions({
            'date_from': '2025-01-16',
            'date_to': '2025-01-17'
        })
        assert len(transactions) == 2
        assert all('2025-01-16' <= tx['date'] <= '2025-01-17' for tx in transactions)
    
    def test_get_all_transactions_filter_by_amount(self):
        """Test filtering transactions by amount."""
        transactions = self.dashboard.get_all_transactions({
            'min_amount': -200,
            'max_amount': -50
        })
        # Should match tx1 (-150), tx2 (-75), tx4 (-200)
        assert len(transactions) == 3
        assert all(-200 <= tx['amount'] <= -50 for tx in transactions)
    
    def test_get_all_transactions_filter_by_category(self):
        """Test filtering transactions by category."""
        transactions = self.dashboard.get_all_transactions({'category': 'Mat & Dryck'})
        assert len(transactions) == 1
        assert transactions[0]['category'] == 'Mat & Dryck'
    
    def test_get_all_transactions_filter_uncategorized(self):
        """Test filtering uncategorized transactions."""
        transactions = self.dashboard.get_all_transactions({'uncategorized': True})
        assert len(transactions) == 2
        # Should include transactions with empty category and 'Okategoriserat'
    
    def test_get_all_transactions_filter_by_account(self):
        """Test filtering transactions by account."""
        transactions = self.dashboard.get_all_transactions({'account': 'Test Account'})
        assert len(transactions) == 3
        assert all(tx['account'] == 'Test Account' for tx in transactions)
    
    def test_get_transaction_sources(self):
        """Test getting unique transaction sources."""
        sources = self.dashboard.get_transaction_sources()
        assert len(sources) == 3
        assert 'import.csv' in sources
        assert 'manual' in sources
        assert 'amex.csv' in sources
    
    def test_get_uncategorized_count(self):
        """Test counting uncategorized transactions."""
        count = self.dashboard.get_uncategorized_count()
        assert count == 2
    
    def test_update_transaction_category(self):
        """Test updating a transaction's category."""
        result = self.dashboard.update_transaction_category(
            'tx2', 'Transport', 'Bränsle & Parkering'
        )
        assert result is True
        
        # Verify the update
        transactions = self.dashboard.get_all_transactions()
        tx2 = next(tx for tx in transactions if tx['id'] == 'tx2')
        assert tx2['category'] == 'Transport'
        assert tx2['subcategory'] == 'Bränsle & Parkering'
    
    def test_update_transaction_category_invalid_id(self):
        """Test updating with invalid transaction ID."""
        result = self.dashboard.update_transaction_category(
            'invalid_id', 'Transport', 'Bränsle & Parkering'
        )
        assert result is False
    
    def test_bulk_update_categories(self):
        """Test bulk updating categories."""
        updated = self.dashboard.bulk_update_categories(
            ['tx2', 'tx4'], 'Transport', 'Övrigt'
        )
        assert updated == 2
        
        # Verify the updates
        transactions = self.dashboard.get_all_transactions()
        tx2 = next(tx for tx in transactions if tx['id'] == 'tx2')
        tx4 = next(tx for tx in transactions if tx['id'] == 'tx4')
        assert tx2['category'] == 'Transport'
        assert tx4['category'] == 'Transport'
    
    def test_add_to_training_data(self):
        """Test adding a transaction to training data."""
        result = self.dashboard.add_to_training_data(
            'ICA Maxi', 'Mat & Dryck', 'Matinköp'
        )
        assert result is True
        
        # Verify training data was saved
        with open(self.dashboard.training_data_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        assert len(data['training_data']) == 1
        assert data['training_data'][0]['description'] == 'ICA Maxi'
        assert data['training_data'][0]['category'] == 'Mat & Dryck'
        assert data['training_data'][0]['manual'] is True
    
    def test_bulk_train_ai(self):
        """Test bulk training AI with multiple transactions."""
        transactions = [
            {'description': 'ICA Maxi', 'category': 'Mat & Dryck', 'subcategory': 'Matinköp'},
            {'description': 'Shell', 'category': 'Transport', 'subcategory': 'Bränsle'},
            {'description': 'Incomplete', 'category': ''}  # Should be skipped
        ]
        
        added = self.dashboard.bulk_train_ai(transactions)
        assert added == 2
        
        # Verify training data
        with open(self.dashboard.training_data_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        assert len(data['training_data']) == 2
    
    def test_get_category_statistics(self):
        """Test getting category statistics."""
        stats = self.dashboard.get_category_statistics()
        
        assert stats['total_transactions'] == 4
        assert stats['uncategorized_count'] == 2
        assert 'Mat & Dryck' in stats['category_counts']
        assert stats['category_counts']['Mat & Dryck'] == 1
        assert 'category_percentages' in stats
        assert 'total_amount_by_category' in stats
    
    def test_get_ai_accuracy_stats(self):
        """Test getting AI accuracy statistics."""
        # Add some training data first
        training_data = {
            'training_data': [
                {
                    'description': 'ICA',
                    'category': 'Mat & Dryck',
                    'subcategory': 'Matinköp',
                    'manual': True,
                    'added_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                {
                    'description': 'Shell',
                    'category': 'Transport',
                    'subcategory': 'Bränsle',
                    'manual': True,
                    'added_at': (datetime.now() - timedelta(days=8)).strftime('%Y-%m-%d %H:%M:%S')
                }
            ]
        }
        
        with open(self.dashboard.training_data_file, 'w', encoding='utf-8') as f:
            yaml.dump(training_data, f)
        
        stats = self.dashboard.get_ai_accuracy_stats()
        
        assert stats['total_training_samples'] == 2
        assert stats['manual_training_samples'] == 2
        assert stats['training_samples_last_7_days'] == 1
        assert stats['training_samples_prev_7_days'] == 1
    
    def test_merge_categories(self):
        """Test merging categories."""
        # Update tx4 to have a specific category first
        self.dashboard.update_transaction_category('tx4', 'Food', 'Restaurant')
        
        # Merge 'Food' into 'Mat & Dryck'
        updated = self.dashboard.merge_categories('Food', 'Mat & Dryck')
        assert updated == 1
        
        # Verify the merge
        transactions = self.dashboard.get_all_transactions()
        tx4 = next(tx for tx in transactions if tx['id'] == 'tx4')
        assert tx4['category'] == 'Mat & Dryck'
    
    def test_delete_category(self):
        """Test deleting a category."""
        # Update tx2 to have a specific category
        self.dashboard.update_transaction_category('tx2', 'OldCategory', 'Subcategory')
        
        # Delete the category (should move to 'Övrigt')
        updated = self.dashboard.delete_category('OldCategory')
        assert updated == 1
        
        # Verify the category was deleted
        transactions = self.dashboard.get_all_transactions()
        tx2 = next(tx for tx in transactions if tx['id'] == 'tx2')
        assert tx2['category'] == 'Övrigt'
    
    def test_get_import_errors(self):
        """Test getting import errors."""
        errors = self.dashboard.get_import_errors()
        assert isinstance(errors, list)
        # Currently returns empty list (placeholder)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
