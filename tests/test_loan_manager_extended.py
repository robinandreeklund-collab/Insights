"""Tests for enhanced loan manager functionality with extended fields."""

import os
import tempfile
import shutil
import pytest
from datetime import datetime
from modules.core.loan_manager import LoanManager


class TestLoanManagerExtended:
    """Test suite for extended loan manager functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up and tear down test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.loan_manager = LoanManager(yaml_dir=self.test_dir)
        
        yield
        
        shutil.rmtree(self.test_dir)
    
    def test_add_loan_with_extended_fields(self):
        """Test adding a loan with extended OCR fields."""
        loan = self.loan_manager.add_loan(
            name="Bolån Swedbank",
            principal=2000000.0,
            interest_rate=3.5,
            start_date="2020-01-15",
            term_months=360,
            description="Test loan with extended fields",
            # Extended fields
            loan_number="12345-678",
            original_amount=2000000.0,
            current_amount=1850000.0,
            amortized=150000.0,
            base_interest_rate=3.75,
            discount=0.25,
            effective_interest_rate=3.5,
            rate_period="3 months",
            binding_period="5 years",
            next_change_date="2025-06-30",
            disbursement_date="2020-01-15",
            borrowers=["Anna Svensson", "Erik Andersson"],
            borrower_shares={"Anna Svensson": 50, "Erik Andersson": 50},
            currency="SEK",
            collateral="Fastighet",
            lender="Swedbank AB",
            payment_interval="Monthly",
            payment_account="3300123456789",
            repayment_account="3300987654321"
        )
        
        assert loan['loan_number'] == "12345-678"
        assert loan['lender'] == "Swedbank AB"
        assert loan['original_amount'] == 2000000.0
        assert loan['amortized'] == 150000.0
        assert loan['base_interest_rate'] == 3.75
        assert loan['discount'] == 0.25
        assert loan['effective_interest_rate'] == 3.5
        assert loan['payment_account'] == "3300123456789"
        assert loan['repayment_account'] == "3300987654321"
        assert len(loan['borrowers']) == 2
        assert "Anna Svensson" in loan['borrowers']
    
    def test_add_interest_payment(self):
        """Test adding an interest payment."""
        # Create a loan
        loan = self.loan_manager.add_loan(
            name="Test Loan",
            principal=1000000.0,
            interest_rate=3.0,
            start_date="2024-01-01"
        )
        
        # Add interest payment
        success = self.loan_manager.add_interest_payment(
            loan['id'], 
            2500.0, 
            "2024-02-01",
            transaction_id="TXN-001"
        )
        
        assert success is True
        
        # Verify interest payment was added
        updated_loan = self.loan_manager.get_loan_by_id(loan['id'])
        assert len(updated_loan['interest_payments']) == 1
        assert updated_loan['interest_payments'][0]['amount'] == 2500.0
        assert updated_loan['interest_payments'][0]['transaction_id'] == "TXN-001"
        
        # Balance should not change for interest payment
        assert updated_loan['current_balance'] == 1000000.0
    
    def test_transaction_matching_by_account_number(self):
        """Test automatic transaction matching by account number."""
        # Create loan with payment account
        loan = self.loan_manager.add_loan(
            name="Test Loan",
            principal=1000000.0,
            interest_rate=3.0,
            start_date="2024-01-01",
            payment_account="3300123456789"
        )
        
        # Create transaction with matching account
        transaction = {
            'id': 'TXN-001',
            'date': '2024-02-01',
            'amount': -5000.0,
            'description': 'Loan payment',
            'account_number': '3300123456789'
        }
        
        # Match transaction
        result = self.loan_manager.match_transaction_to_loan(transaction)
        
        assert result is not None
        assert result['matched'] is True
        assert result['loan_id'] == loan['id']
        assert result['amount'] == 5000.0
        assert result['payment_type'] == 'amortization'
        
        # Verify loan balance updated
        updated_loan = self.loan_manager.get_loan_by_id(loan['id'])
        assert updated_loan['current_balance'] == 995000.0
    
    def test_transaction_matching_interest_payment(self):
        """Test identifying interest payments from transaction description."""
        loan = self.loan_manager.add_loan(
            name="Test Loan",
            principal=1000000.0,
            interest_rate=3.0,
            start_date="2024-01-01",
            payment_account="3300123456789"
        )
        
        # Transaction with interest keyword
        transaction = {
            'id': 'TXN-002',
            'date': '2024-02-01',
            'amount': -2500.0,
            'description': 'Ränteinbetalning Test Loan',
            'account_number': '3300123456789'
        }
        
        result = self.loan_manager.match_transaction_to_loan(transaction)
        
        assert result is not None
        assert result['payment_type'] == 'interest'
        
        # Balance should not change for interest payment
        updated_loan = self.loan_manager.get_loan_by_id(loan['id'])
        assert updated_loan['current_balance'] == 1000000.0
        assert len(updated_loan['interest_payments']) == 1
    
    def test_transaction_matching_by_loan_number(self):
        """Test transaction matching using loan number in description."""
        loan = self.loan_manager.add_loan(
            name="Test Loan",
            principal=1000000.0,
            interest_rate=3.0,
            start_date="2024-01-01",
            loan_number="ABC-12345"
        )
        
        transaction = {
            'id': 'TXN-003',
            'date': '2024-02-01',
            'amount': -5000.0,
            'description': 'Payment for loan ABC-12345',
            'account_number': ''
        }
        
        result = self.loan_manager.match_transaction_to_loan(transaction)
        
        assert result is not None
        assert result['matched'] is True
        assert result['loan_id'] == loan['id']
    
    def test_loan_with_multiple_borrowers(self):
        """Test loan with multiple borrowers and shares."""
        loan = self.loan_manager.add_loan(
            name="Joint Loan",
            principal=2000000.0,
            interest_rate=3.5,
            start_date="2024-01-01",
            borrowers=["Person A", "Person B", "Person C"],
            borrower_shares={
                "Person A": 50,
                "Person B": 30,
                "Person C": 20
            }
        )
        
        assert len(loan['borrowers']) == 3
        assert loan['borrower_shares']["Person A"] == 50
        assert loan['borrower_shares']["Person B"] == 30
        assert loan['borrower_shares']["Person C"] == 20
    
    def test_account_number_normalization(self):
        """Test that account numbers are normalized for matching."""
        loan = self.loan_manager.add_loan(
            name="Test Loan",
            principal=1000000.0,
            interest_rate=3.0,
            start_date="2024-01-01",
            payment_account="3300-123-456789"  # With hyphens
        )
        
        # Transaction with different formatting
        transaction = {
            'id': 'TXN-004',
            'date': '2024-02-01',
            'amount': -5000.0,
            'description': 'Payment',
            'account_number': '3300 123 456789'  # With spaces
        }
        
        result = self.loan_manager.match_transaction_to_loan(transaction)
        
        # Should match despite different formatting
        assert result is not None
        assert result['matched'] is True
    
    def test_payment_with_transaction_id_link(self):
        """Test that payment records link to transaction IDs."""
        loan = self.loan_manager.add_loan(
            name="Test Loan",
            principal=1000000.0,
            interest_rate=3.0,
            start_date="2024-01-01"
        )
        
        # Add payment with transaction ID
        success = self.loan_manager.add_payment(
            loan['id'],
            5000.0,
            "2024-02-01",
            transaction_id="TXN-999"
        )
        
        assert success is True
        
        updated_loan = self.loan_manager.get_loan_by_id(loan['id'])
        assert updated_loan['payments'][0]['transaction_id'] == "TXN-999"
    
    def test_loan_without_extended_fields(self):
        """Test that loans work without extended fields (backward compatibility)."""
        loan = self.loan_manager.add_loan(
            name="Simple Loan",
            principal=500000.0,
            interest_rate=2.5,
            start_date="2024-01-01"
        )
        
        # Should still work with just basic fields
        assert loan['name'] == "Simple Loan"
        assert loan['principal'] == 500000.0
        assert loan['interest_rate'] == 2.5
        assert loan['status'] == 'active'
        
        # Extended fields should not be present or should be None
        assert loan.get('loan_number') is None
        assert loan.get('lender') is None
