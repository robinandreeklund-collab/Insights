"""Tests for history_viewer module."""

import unittest
import os
import yaml
import tempfile
import shutil
from datetime import datetime, timedelta

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.core.history_viewer import HistoryViewer


class TestHistoryViewer(unittest.TestCase):
    """Test cases for HistoryViewer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for test YAML files
        self.test_dir = tempfile.mkdtemp()
        self.viewer = HistoryViewer(yaml_dir=self.test_dir)
        
        # Create sample transactions
        self._create_sample_transactions()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
    
    def _create_sample_transactions(self):
        """Create sample transactions for testing."""
        current_month = datetime.now().strftime('%Y-%m')
        last_month = (datetime.now() - timedelta(days=30)).strftime('%Y-%m')
        
        transactions = {
            'transactions': [
                {
                    'id': '1',
                    'date': f'{current_month}-01',
                    'description': 'Lön',
                    'amount': 30000.0,
                    'account': 'Test',
                    'category': 'Inkomst'
                },
                {
                    'id': '2',
                    'date': f'{current_month}-05',
                    'description': 'ICA Matinköp',
                    'amount': -500.0,
                    'account': 'Test',
                    'category': 'Mat & Dryck'
                },
                {
                    'id': '3',
                    'date': f'{current_month}-10',
                    'description': 'Hyra',
                    'amount': -10000.0,
                    'account': 'Test',
                    'category': 'Boende'
                },
                {
                    'id': '4',
                    'date': f'{last_month}-01',
                    'description': 'Lön',
                    'amount': 30000.0,
                    'account': 'Test',
                    'category': 'Inkomst'
                },
                {
                    'id': '5',
                    'date': f'{last_month}-05',
                    'description': 'Matinköp',
                    'amount': -450.0,
                    'account': 'Test',
                    'category': 'Mat & Dryck'
                }
            ]
        }
        
        transactions_file = os.path.join(self.test_dir, 'transactions.yaml')
        with open(transactions_file, 'w', encoding='utf-8') as f:
            yaml.dump(transactions, f)
    
    def test_history_viewer_initialization(self):
        """Test HistoryViewer initialization."""
        self.assertIsNotNone(self.viewer)
        self.assertEqual(self.viewer.yaml_dir, self.test_dir)
    
    def test_get_monthly_summary(self):
        """Test getting monthly summary."""
        current_month = datetime.now().strftime('%Y-%m')
        summary = self.viewer.get_monthly_summary(current_month)
        
        self.assertIsNotNone(summary)
        self.assertEqual(summary['month'], current_month)
        self.assertEqual(summary['income'], 30000.0)
        self.assertEqual(summary['expenses'], 10500.0)
        self.assertEqual(summary['net'], 19500.0)
        self.assertEqual(summary['income_count'], 1)
        self.assertEqual(summary['expense_count'], 2)
    
    def test_get_monthly_summary_no_month(self):
        """Test getting monthly summary for current month when no month specified."""
        summary = self.viewer.get_monthly_summary()
        self.assertIsNotNone(summary)
        self.assertIn('month', summary)
    
    def test_get_category_trend(self):
        """Test getting category trend."""
        trend = self.viewer.get_category_trend('Mat & Dryck', months=2)
        
        self.assertIsNotNone(trend)
        self.assertIsInstance(trend, list)
        self.assertTrue(len(trend) > 0)
        
        # Check structure
        for data_point in trend:
            self.assertIn('month', data_point)
            self.assertIn('amount', data_point)
            self.assertIn('count', data_point)
    
    def test_get_account_balance_history(self):
        """Test getting account balance history."""
        history = self.viewer.get_account_balance_history('Test')
        
        self.assertIsNotNone(history)
        self.assertIsInstance(history, list)
        self.assertTrue(len(history) > 0)
        
        # Check structure
        for entry in history:
            self.assertIn('date', entry)
            self.assertIn('balance', entry)
            self.assertIn('transaction_id', entry)
    
    def test_get_account_balance_history_all_accounts(self):
        """Test getting balance history for all accounts."""
        history = self.viewer.get_account_balance_history()
        
        self.assertIsNotNone(history)
        self.assertIsInstance(history, list)
    
    def test_get_top_expenses(self):
        """Test getting top expenses."""
        current_month = datetime.now().strftime('%Y-%m')
        top = self.viewer.get_top_expenses(current_month, top_n=5)
        
        self.assertIsNotNone(top)
        self.assertIsInstance(top, list)
        self.assertTrue(len(top) <= 5)
        
        # Check that largest expense is first
        if len(top) > 1:
            self.assertGreaterEqual(abs(top[0]['amount']), abs(top[1]['amount']))
    
    def test_get_top_expenses_no_month(self):
        """Test getting top expenses for current month."""
        top = self.viewer.get_top_expenses()
        self.assertIsNotNone(top)
        self.assertIsInstance(top, list)
    
    def test_get_all_months(self):
        """Test getting all months with transactions."""
        months = self.viewer.get_all_months()
        
        self.assertIsNotNone(months)
        self.assertIsInstance(months, list)
        self.assertTrue(len(months) > 0)
        
        # Check format (YYYY-MM)
        for month in months:
            self.assertRegex(month, r'\d{4}-\d{2}')


if __name__ == '__main__':
    unittest.main()
