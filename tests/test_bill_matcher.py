"""Tests for bill matcher module."""

import os
import tempfile
import shutil
import pytest
from datetime import datetime, timedelta
from modules.core.bill_manager import BillManager
from modules.core.account_manager import AccountManager
from modules.core.bill_matcher import BillMatcher


class TestBillMatcher:
    """Test suite for BillMatcher class."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up and tear down test environment."""
        # Create temporary directory for test YAML files
        self.test_dir = tempfile.mkdtemp()
        self.bill_manager = BillManager(yaml_dir=self.test_dir)
        self.account_manager = AccountManager(yaml_dir=self.test_dir)
        self.matcher = BillMatcher(self.bill_manager, self.account_manager)
        
        yield
        
        # Clean up
        shutil.rmtree(self.test_dir)
    
    def test_matcher_initialization(self):
        """Test that BillMatcher initializes correctly."""
        assert self.matcher.bill_manager is not None
        assert self.matcher.account_manager is not None
    
    def test_calculate_match_confidence_exact_match(self):
        """Test confidence calculation with exact match."""
        bill = {
            'name': 'Elräkning',
            'amount': 850.0,
            'category': 'Boende'
        }
        
        transaction = {
            'description': 'Elräkning betald',
            'amount': -850.0,
            'category': 'Boende'
        }
        
        confidence = self.matcher._calculate_match_confidence(bill, transaction, 850.0, 850.0)
        
        # Should have high confidence with exact amount, text match, and category match
        assert confidence >= 0.7
    
    def test_calculate_match_confidence_partial_match(self):
        """Test confidence calculation with partial match."""
        bill = {
            'name': 'Elräkning',
            'amount': 850.0,
            'category': 'Boende'
        }
        
        transaction = {
            'description': 'Något annat',
            'amount': -860.0,  # Slightly different amount
            'category': 'Övrigt'  # Different category
        }
        
        confidence = self.matcher._calculate_match_confidence(bill, transaction, 850.0, 860.0)
        
        # Should have lower confidence
        assert confidence < 0.7
    
    def test_find_matching_transaction_exact_match(self):
        """Test finding a matching transaction."""
        # Add a bill
        due_date = datetime.now().strftime('%Y-%m-%d')
        bill = self.bill_manager.add_bill(
            name="Elräkning",
            amount=850.0,
            due_date=due_date,
            category="Boende"
        )
        
        # Add a matching transaction
        transactions = [{
            'date': due_date,
            'description': 'Elräkning betald',
            'amount': -850.0,
            'category': 'Boende',
            'id': 'TX-001'
        }]
        
        match = self.matcher._find_matching_transaction(bill, transactions, tolerance_days=7)
        
        assert match is not None
        assert match['bill_id'] == bill['id']
        assert match['transaction_id'] == 'TX-001'
        assert match['confidence'] >= 0.7
    
    def test_find_matching_transaction_within_tolerance(self):
        """Test finding transaction within date tolerance."""
        # Add a bill
        due_date = (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')
        bill = self.bill_manager.add_bill(
            name="Elräkning",
            amount=850.0,
            due_date=due_date,
            category="Boende"
        )
        
        # Add a transaction a few days before due date
        tx_date = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
        transactions = [{
            'date': tx_date,
            'description': 'Elräkning betald',
            'amount': -850.0,
            'category': 'Boende',
            'id': 'TX-001'
        }]
        
        match = self.matcher._find_matching_transaction(bill, transactions, tolerance_days=7)
        
        assert match is not None
    
    def test_find_matching_transaction_no_match(self):
        """Test when no matching transaction is found."""
        # Add a bill
        due_date = datetime.now().strftime('%Y-%m-%d')
        bill = self.bill_manager.add_bill(
            name="Elräkning",
            amount=850.0,
            due_date=due_date,
            category="Boende"
        )
        
        # Add a completely different transaction
        transactions = [{
            'date': due_date,
            'description': 'Mat',
            'amount': -50.0,  # Very different amount
            'category': 'Mat & Dryck',
            'id': 'TX-001'
        }]
        
        match = self.matcher._find_matching_transaction(bill, transactions, tolerance_days=7)
        
        # Should not match due to different amount and description
        assert match is None
    
    def test_find_matching_transaction_positive_amount(self):
        """Test that positive amounts (income) are not matched."""
        # Add a bill
        due_date = datetime.now().strftime('%Y-%m-%d')
        bill = self.bill_manager.add_bill(
            name="Elräkning",
            amount=850.0,
            due_date=due_date
        )
        
        # Add a transaction with positive amount (income)
        transactions = [{
            'date': due_date,
            'description': 'Elräkning',
            'amount': 850.0,  # Positive = income
            'category': 'Boende',
            'id': 'TX-001'
        }]
        
        match = self.matcher._find_matching_transaction(bill, transactions, tolerance_days=7)
        
        # Should not match positive amounts
        assert match is None
    
    def test_manual_match(self):
        """Test manually matching a bill to a transaction."""
        # Add a bill
        due_date = datetime.now().strftime('%Y-%m-%d')
        bill = self.bill_manager.add_bill(
            name="Elräkning",
            amount=850.0,
            due_date=due_date
        )
        
        # Manually match
        success = self.matcher.manual_match(bill['id'], 'TX-MANUAL-001')
        
        assert success
        
        # Verify bill is marked as paid
        updated_bill = self.bill_manager.get_bill_by_id(bill['id'])
        assert updated_bill['status'] == 'paid'
        assert updated_bill['matched_transaction_id'] == 'TX-MANUAL-001'
    
    def test_get_unmatched_bills(self):
        """Test getting unmatched bills."""
        # Add bills
        due_date = datetime.now().strftime('%Y-%m-%d')
        bill1 = self.bill_manager.add_bill("Bill 1", 100.0, due_date)
        bill2 = self.bill_manager.add_bill("Bill 2", 200.0, due_date)
        
        # Match one bill
        self.bill_manager.mark_as_paid(bill1['id'], 'TX-001')
        
        # Get unmatched bills
        unmatched = self.matcher.get_unmatched_bills()
        
        assert len(unmatched) == 1
        assert unmatched[0]['id'] == bill2['id']
    
    def test_get_transaction_id(self):
        """Test getting/generating transaction ID."""
        # Transaction with ID
        tx_with_id = {'id': 'TX-123'}
        assert self.matcher._get_transaction_id(tx_with_id) == 'TX-123'
        
        # Transaction without ID
        tx_without_id = {
            'date': '2025-01-01',
            'description': 'Test transaction',
            'amount': -100.0
        }
        generated_id = self.matcher._get_transaction_id(tx_without_id)
        assert generated_id.startswith('TX-')
