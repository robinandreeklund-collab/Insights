"""Tests for loan management module."""

import os
import tempfile
import shutil
import pytest
from datetime import datetime
from modules.core.loan_manager import LoanManager


class TestLoanManager:
    """Test suite for LoanManager class."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up and tear down test environment."""
        # Create temporary directory for test YAML files
        self.test_dir = tempfile.mkdtemp()
        self.loan_manager = LoanManager(yaml_dir=self.test_dir)
        
        yield
        
        # Clean up
        shutil.rmtree(self.test_dir)
    
    def test_loan_manager_initialization(self):
        """Test that LoanManager initializes correctly."""
        assert self.loan_manager.yaml_dir == self.test_dir
        assert os.path.exists(self.loan_manager.loans_file)
    
    def test_add_loan(self):
        """Test adding a new loan."""
        loan = self.loan_manager.add_loan(
            name="Bolån",
            principal=2000000.0,
            interest_rate=3.5,
            start_date="2025-01-01",
            term_months=360,
            description="Huvudlån för bostad"
        )
        
        assert loan['name'] == "Bolån"
        assert loan['principal'] == 2000000.0
        assert loan['interest_rate'] == 3.5
        assert loan['status'] == 'active'
        assert loan['id'].startswith('LOAN-')
    
    def test_get_loans(self):
        """Test getting all loans."""
        self.loan_manager.add_loan("Loan 1", 100000.0, 3.0, "2025-01-01")
        self.loan_manager.add_loan("Loan 2", 200000.0, 4.0, "2025-01-01")
        
        loans = self.loan_manager.get_loans()
        assert len(loans) == 2
    
    def test_get_loans_by_status(self):
        """Test filtering loans by status."""
        loan1 = self.loan_manager.add_loan("Loan 1", 100000.0, 3.0, "2025-01-01")
        loan2 = self.loan_manager.add_loan("Loan 2", 200000.0, 4.0, "2025-01-01")
        
        # Mark one as paid off
        self.loan_manager.update_loan(loan1['id'], {'status': 'paid_off'})
        
        active_loans = self.loan_manager.get_loans(status='active')
        paid_loans = self.loan_manager.get_loans(status='paid_off')
        
        assert len(active_loans) == 1
        assert len(paid_loans) == 1
    
    def test_get_loan_by_id(self):
        """Test getting a loan by ID."""
        loan = self.loan_manager.add_loan("Test Loan", 100000.0, 3.0, "2025-01-01")
        
        retrieved_loan = self.loan_manager.get_loan_by_id(loan['id'])
        assert retrieved_loan is not None
        assert retrieved_loan['name'] == "Test Loan"
    
    def test_update_loan(self):
        """Test updating a loan."""
        loan = self.loan_manager.add_loan("Test Loan", 100000.0, 3.0, "2025-01-01")
        
        success = self.loan_manager.update_loan(loan['id'], {'interest_rate': 3.5})
        assert success
        
        updated_loan = self.loan_manager.get_loan_by_id(loan['id'])
        assert updated_loan['interest_rate'] == 3.5
    
    def test_delete_loan(self):
        """Test deleting a loan."""
        loan = self.loan_manager.add_loan("Test Loan", 100000.0, 3.0, "2025-01-01")
        
        success = self.loan_manager.delete_loan(loan['id'])
        assert success
        
        retrieved_loan = self.loan_manager.get_loan_by_id(loan['id'])
        assert retrieved_loan is None
    
    def test_add_payment(self):
        """Test adding a payment to a loan."""
        loan = self.loan_manager.add_loan("Test Loan", 100000.0, 3.0, "2025-01-01")
        
        success = self.loan_manager.add_payment(loan['id'], 5000.0, "2025-02-01")
        assert success
        
        updated_loan = self.loan_manager.get_loan_by_id(loan['id'])
        assert updated_loan['current_balance'] == 95000.0
        assert len(updated_loan['payments']) == 1
    
    def test_payment_paid_off(self):
        """Test that loan is marked paid_off when balance reaches 0."""
        loan = self.loan_manager.add_loan("Test Loan", 10000.0, 3.0, "2025-01-01")
        
        # Pay off entire loan
        success = self.loan_manager.add_payment(loan['id'], 10000.0, "2025-02-01")
        assert success
        
        updated_loan = self.loan_manager.get_loan_by_id(loan['id'])
        assert updated_loan['status'] == 'paid_off'
        assert updated_loan['current_balance'] == 0
    
    def test_calculate_monthly_payment(self):
        """Test calculating monthly payment."""
        # For a 100,000 SEK loan at 3% over 12 months
        payment = self.loan_manager.calculate_monthly_payment(100000.0, 3.0, 12)
        
        # Payment should be positive and reasonable
        assert payment > 0
        assert payment > 8000  # Should be more than just principal/12
        assert payment < 9000  # But not too much higher
    
    def test_calculate_monthly_payment_zero_interest(self):
        """Test calculating monthly payment with zero interest."""
        payment = self.loan_manager.calculate_monthly_payment(100000.0, 0.0, 12)
        
        # With 0% interest, payment should be exactly principal/months
        assert abs(payment - (100000.0 / 12)) < 0.01
    
    def test_get_amortization_schedule(self):
        """Test getting amortization schedule."""
        loan = self.loan_manager.add_loan("Test Loan", 100000.0, 3.0, "2025-01-01", term_months=12)
        
        schedule = self.loan_manager.get_amortization_schedule(loan['id'], months=12)
        
        assert len(schedule) == 12
        assert schedule[0]['month'] == 1
        assert schedule[0]['balance'] < 100000.0  # Balance should decrease
        assert schedule[-1]['balance'] >= 0  # Final balance should be non-negative
    
    def test_simulate_interest_change(self):
        """Test simulating interest rate change."""
        loan = self.loan_manager.add_loan("Test Loan", 100000.0, 3.0, "2025-01-01", term_months=360)
        
        simulation = self.loan_manager.simulate_interest_change(loan['id'], 4.0)
        
        assert simulation['current_interest_rate'] == 3.0
        assert simulation['new_interest_rate'] == 4.0
        assert simulation['new_monthly_payment'] > simulation['current_monthly_payment']
        assert simulation['difference'] > 0
        assert simulation['difference_percent'] > 0
    
    def test_simulate_interest_decrease(self):
        """Test simulating interest rate decrease."""
        loan = self.loan_manager.add_loan("Test Loan", 100000.0, 3.0, "2025-01-01", term_months=360)
        
        simulation = self.loan_manager.simulate_interest_change(loan['id'], 2.0)
        
        assert simulation['new_monthly_payment'] < simulation['current_monthly_payment']
        assert simulation['difference'] < 0
        assert simulation['difference_percent'] < 0
    
    def test_loan_with_fixed_rate_end_date(self):
        """Test adding a loan with fixed rate end date."""
        loan = self.loan_manager.add_loan(
            name="Fixed Rate Loan",
            principal=100000.0,
            interest_rate=3.0,
            start_date="2025-01-01",
            term_months=360,
            fixed_rate_end_date="2030-01-01"
        )
        
        assert loan['fixed_rate_end_date'] == "2030-01-01"
    
    def test_match_transaction_to_loan_with_id(self):
        """Test matching a transaction to a specific loan."""
        # Create a loan
        loan = self.loan_manager.add_loan(
            name="Bolån",
            principal=100000.0,
            interest_rate=3.5,
            start_date="2025-01-01",
            term_months=360
        )
        
        # Create a transaction
        transaction = {
            'description': 'Lånebetalning',
            'amount': -5000.0,
            'date': '2025-01-15'
        }
        
        # Match transaction to loan
        result = self.loan_manager.match_transaction_to_loan(transaction, loan['id'])
        
        assert result is not None
        assert result['matched'] is True
        assert result['loan_id'] == loan['id']
        assert result['amount'] == 5000.0
        assert result['new_balance'] == 95000.0
    
    def test_match_transaction_to_loan_auto(self):
        """Test auto-matching a transaction to a loan."""
        # Create a loan
        loan = self.loan_manager.add_loan(
            name="Bolån",
            principal=50000.0,
            interest_rate=3.0,
            start_date="2025-01-01",
            term_months=240
        )
        
        # Create a transaction with loan name in description
        transaction = {
            'description': 'Bolån amortering',
            'amount': -2000.0,
            'date': '2025-02-01'
        }
        
        # Auto-match transaction
        result = self.loan_manager.match_transaction_to_loan(transaction)
        
        assert result is not None
        assert result['matched'] is True
        assert result['loan_id'] == loan['id']
        assert result['amount'] == 2000.0
    
    def test_get_loan_payment_history(self):
        """Test getting payment history for a loan."""
        # Create a loan and add payments
        loan = self.loan_manager.add_loan(
            name="Billån",
            principal=30000.0,
            interest_rate=5.0,
            start_date="2025-01-01",
            term_months=60
        )
        
        self.loan_manager.add_payment(loan['id'], 1000.0, '2025-01-15')
        self.loan_manager.add_payment(loan['id'], 1000.0, '2025-02-15')
        
        # Get payment history
        history = self.loan_manager.get_loan_payment_history(loan['id'])
        
        assert len(history) == 2
        assert history[0]['amount'] == 1000.0
        assert history[1]['amount'] == 1000.0
