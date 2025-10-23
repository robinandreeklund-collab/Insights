"""Tests for internal transfer detection."""

import pytest
import os
import yaml
import tempfile
import shutil
from datetime import datetime, timedelta

from modules.core.account_manager import AccountManager


class TestInternalTransfers:
    """Test internal transfer detection functionality."""
    
    @pytest.fixture
    def temp_yaml_dir(self):
        """Create a temporary YAML directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def manager(self, temp_yaml_dir):
        """Create an AccountManager with temp directory."""
        return AccountManager(yaml_dir=temp_yaml_dir)
    
    def test_detect_simple_transfer(self, manager):
        """Test detection of a simple transfer between two accounts."""
        # Create two accounts
        acc1 = manager.create_account("Account A", 5000.0)
        acc2 = manager.create_account("Account B", 3000.0)
        
        # Create matching transactions (transfer from A to B)
        today = datetime.now().strftime('%Y-%m-%d')
        
        transactions = [
            {
                'account': 'Account A',
                'date': today,
                'amount': -1000.0,  # Outgoing
                'description': 'Transfer to Account B',
                'category': 'Transfer'
            },
            {
                'account': 'Account B',
                'date': today,
                'amount': 1000.0,  # Incoming
                'description': 'Transfer from Account A',
                'category': 'Transfer'
            }
        ]
        
        manager.add_transactions(transactions)
        
        # Detect transfers
        count = manager.detect_internal_transfers()
        
        # Should detect 1 pair
        assert count == 1
        
        # Check that transactions are marked
        all_txs = manager.get_all_transactions()
        assert len(all_txs) == 2
        
        for tx in all_txs:
            assert tx.get('is_internal_transfer') == True
            assert 'transfer_label' in tx
            assert 'Flytt mellan konton' in tx['transfer_label']
            assert 'transfer_counterpart_id' in tx
    
    def test_detect_multiple_transfers(self, manager):
        """Test detection of multiple transfers."""
        # Create accounts
        acc1 = manager.create_account("Account 1", 5000.0)
        acc2 = manager.create_account("Account 2", 3000.0)
        acc3 = manager.create_account("Account 3", 2000.0)
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        transactions = [
            # Transfer 1: Account 1 -> Account 2
            {'account': 'Account 1', 'date': today, 'amount': -500.0, 'description': 'Transfer'},
            {'account': 'Account 2', 'date': today, 'amount': 500.0, 'description': 'Transfer'},
            # Transfer 2: Account 2 -> Account 3
            {'account': 'Account 2', 'date': today, 'amount': -300.0, 'description': 'Transfer'},
            {'account': 'Account 3', 'date': today, 'amount': 300.0, 'description': 'Transfer'},
        ]
        
        manager.add_transactions(transactions)
        count = manager.detect_internal_transfers()
        
        # Should detect 2 pairs
        assert count == 2
        
        # All should be marked
        all_txs = manager.get_all_transactions()
        marked = [tx for tx in all_txs if tx.get('is_internal_transfer')]
        assert len(marked) == 4
    
    def test_no_false_positives(self, manager):
        """Test that non-transfers are not detected."""
        acc1 = manager.create_account("Account A", 5000.0)
        acc2 = manager.create_account("Account B", 3000.0)
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        transactions = [
            # Different amounts
            {'account': 'Account A', 'date': today, 'amount': -1000.0, 'description': 'Purchase'},
            {'account': 'Account B', 'date': today, 'amount': 500.0, 'description': 'Deposit'},
            # Same amount but both negative
            {'account': 'Account A', 'date': today, 'amount': -200.0, 'description': 'Purchase'},
            {'account': 'Account B', 'date': today, 'amount': -200.0, 'description': 'Purchase'},
        ]
        
        manager.add_transactions(transactions)
        count = manager.detect_internal_transfers()
        
        # Should not detect any transfers
        assert count == 0
    
    def test_date_tolerance(self, manager):
        """Test that transfers within date tolerance are detected."""
        acc1 = manager.create_account("Account A", 5000.0)
        acc2 = manager.create_account("Account B", 3000.0)
        
        today = datetime.now()
        tomorrow = (today + timedelta(days=1)).strftime('%Y-%m-%d')
        today_str = today.strftime('%Y-%m-%d')
        
        transactions = [
            {'account': 'Account A', 'date': today_str, 'amount': -1000.0, 'description': 'Transfer'},
            {'account': 'Account B', 'date': tomorrow, 'amount': 1000.0, 'description': 'Transfer'},
        ]
        
        manager.add_transactions(transactions)
        count = manager.detect_internal_transfers()
        
        # Should detect transfer (1 day apart is within 2 day tolerance)
        assert count == 1
    
    def test_date_outside_tolerance(self, manager):
        """Test that transfers outside date tolerance are not detected."""
        acc1 = manager.create_account("Account A", 5000.0)
        acc2 = manager.create_account("Account B", 3000.0)
        
        today = datetime.now()
        far_date = (today + timedelta(days=5)).strftime('%Y-%m-%d')
        today_str = today.strftime('%Y-%m-%d')
        
        transactions = [
            {'account': 'Account A', 'date': today_str, 'amount': -1000.0, 'description': 'Transfer'},
            {'account': 'Account B', 'date': far_date, 'amount': 1000.0, 'description': 'Transfer'},
        ]
        
        manager.add_transactions(transactions)
        count = manager.detect_internal_transfers()
        
        # Should not detect transfer (5 days apart is outside 2 day tolerance)
        assert count == 0
    
    def test_same_account_not_detected(self, manager):
        """Test that transactions in same account are not detected as transfers."""
        acc1 = manager.create_account("Account A", 5000.0)
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        transactions = [
            {'account': 'Account A', 'date': today, 'amount': -1000.0, 'description': 'Expense'},
            {'account': 'Account A', 'date': today, 'amount': 1000.0, 'description': 'Income'},
        ]
        
        manager.add_transactions(transactions)
        count = manager.detect_internal_transfers()
        
        # Should not detect transfer (same account)
        assert count == 0
    
    def test_already_marked_skipped(self, manager):
        """Test that already marked transfers are not re-processed."""
        acc1 = manager.create_account("Account A", 5000.0)
        acc2 = manager.create_account("Account B", 3000.0)
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        transactions = [
            {
                'account': 'Account A',
                'date': today,
                'amount': -1000.0,
                'description': 'Transfer',
                'is_internal_transfer': True  # Already marked
            },
            {
                'account': 'Account B',
                'date': today,
                'amount': 1000.0,
                'description': 'Transfer',
                'is_internal_transfer': True  # Already marked
            }
        ]
        
        manager.add_transactions(transactions)
        count = manager.detect_internal_transfers()
        
        # Should not detect any (already marked)
        assert count == 0
    
    def test_forecast_excludes_transfers(self, manager):
        """Test that forecast calculations exclude internal transfers."""
        from modules.core.forecast_engine import calculate_average_income_and_expenses
        
        acc1 = manager.create_account("Account A", 5000.0)
        acc2 = manager.create_account("Account B", 3000.0)
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        transactions = [
            # Regular expense
            {'account': 'Account A', 'date': today, 'amount': -500.0, 'description': 'Purchase'},
            # Internal transfer (should be excluded)
            {'account': 'Account A', 'date': today, 'amount': -1000.0, 'description': 'Transfer',
             'is_internal_transfer': True},
            {'account': 'Account B', 'date': today, 'amount': 1000.0, 'description': 'Transfer',
             'is_internal_transfer': True},
            # Regular income
            {'account': 'Account A', 'date': today, 'amount': 2000.0, 'description': 'Salary'},
        ]
        
        manager.add_transactions(transactions)
        
        # Calculate stats
        stats = calculate_average_income_and_expenses(transactions, days=30)
        
        # Should only count regular transactions
        # Income: 2000, Expense: 500
        # Since we're looking at 1 day, daily averages are the same
        assert stats['avg_daily_income'] > 0
        assert stats['avg_daily_expenses'] > 0
        
        # The transfer amounts should not be included
        # Total expense should be around 500, not 1500
        assert stats['avg_daily_expenses'] < 1000
