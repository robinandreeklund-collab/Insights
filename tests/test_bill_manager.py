"""Tests for bill management module."""

import os
import tempfile
import shutil
import pytest
from datetime import datetime, timedelta
from modules.core.bill_manager import BillManager


class TestBillManager:
    """Test suite for BillManager class."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up and tear down test environment."""
        # Create temporary directory for test YAML files
        self.test_dir = tempfile.mkdtemp()
        self.bill_manager = BillManager(yaml_dir=self.test_dir)
        
        yield
        
        # Clean up
        shutil.rmtree(self.test_dir)
    
    def test_bill_manager_initialization(self):
        """Test that BillManager initializes correctly."""
        assert self.bill_manager.yaml_dir == self.test_dir
        assert os.path.exists(self.bill_manager.bills_file)
    
    def test_add_bill(self):
        """Test adding a new bill."""
        due_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
        bill = self.bill_manager.add_bill(
            name="Elräkning December",
            amount=850.0,
            due_date=due_date,
            description="Elkostnad för december",
            category="Boende"
        )
        
        assert bill['name'] == "Elräkning December"
        assert bill['amount'] == 850.0
        assert bill['due_date'] == due_date
        assert bill['status'] == 'pending'
        assert bill['id'].startswith('BILL-')
    
    def test_get_bills(self):
        """Test getting all bills."""
        due_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
        self.bill_manager.add_bill("Bill 1", 100.0, due_date)
        self.bill_manager.add_bill("Bill 2", 200.0, due_date)
        
        bills = self.bill_manager.get_bills()
        assert len(bills) == 2
    
    def test_get_bills_by_status(self):
        """Test filtering bills by status."""
        due_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
        bill1 = self.bill_manager.add_bill("Bill 1", 100.0, due_date)
        bill2 = self.bill_manager.add_bill("Bill 2", 200.0, due_date)
        
        # Mark one as paid
        self.bill_manager.mark_as_paid(bill1['id'])
        
        pending_bills = self.bill_manager.get_bills(status='pending')
        paid_bills = self.bill_manager.get_bills(status='paid')
        
        assert len(pending_bills) == 1
        assert len(paid_bills) == 1
    
    def test_get_bill_by_id(self):
        """Test getting a bill by ID."""
        due_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
        bill = self.bill_manager.add_bill("Test Bill", 100.0, due_date)
        
        retrieved_bill = self.bill_manager.get_bill_by_id(bill['id'])
        assert retrieved_bill is not None
        assert retrieved_bill['name'] == "Test Bill"
    
    def test_update_bill(self):
        """Test updating a bill."""
        due_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
        bill = self.bill_manager.add_bill("Test Bill", 100.0, due_date)
        
        success = self.bill_manager.update_bill(bill['id'], {'amount': 150.0})
        assert success
        
        updated_bill = self.bill_manager.get_bill_by_id(bill['id'])
        assert updated_bill['amount'] == 150.0
    
    def test_delete_bill(self):
        """Test deleting a bill."""
        due_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
        bill = self.bill_manager.add_bill("Test Bill", 100.0, due_date)
        
        success = self.bill_manager.delete_bill(bill['id'])
        assert success
        
        retrieved_bill = self.bill_manager.get_bill_by_id(bill['id'])
        assert retrieved_bill is None
    
    def test_mark_as_paid(self):
        """Test marking a bill as paid."""
        due_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
        bill = self.bill_manager.add_bill("Test Bill", 100.0, due_date)
        
        success = self.bill_manager.mark_as_paid(bill['id'], "TX-123")
        assert success
        
        paid_bill = self.bill_manager.get_bill_by_id(bill['id'])
        assert paid_bill['status'] == 'paid'
        assert paid_bill['matched_transaction_id'] == "TX-123"
        assert paid_bill['paid_at'] is not None
    
    def test_schedule_payment(self):
        """Test scheduling a payment."""
        due_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
        bill = self.bill_manager.add_bill("Test Bill", 100.0, due_date)
        
        payment_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        success = self.bill_manager.schedule_payment(bill['id'], payment_date)
        assert success
        
        scheduled_bill = self.bill_manager.get_bill_by_id(bill['id'])
        assert scheduled_bill['scheduled_payment_date'] == payment_date
    
    def test_get_upcoming_bills(self):
        """Test getting upcoming bills."""
        today = datetime.now()
        
        # Add bills with different due dates
        self.bill_manager.add_bill("Soon", 100.0, (today + timedelta(days=5)).strftime('%Y-%m-%d'))
        self.bill_manager.add_bill("Later", 200.0, (today + timedelta(days=25)).strftime('%Y-%m-%d'))
        self.bill_manager.add_bill("Much Later", 300.0, (today + timedelta(days=60)).strftime('%Y-%m-%d'))
        
        upcoming_30 = self.bill_manager.get_upcoming_bills(days=30)
        assert len(upcoming_30) == 2  # Only first two should be within 30 days
    
    def test_overdue_bills(self):
        """Test that bills become overdue."""
        # Add a bill with past due date
        past_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        self.bill_manager.add_bill("Overdue Bill", 100.0, past_date)
        
        bills = self.bill_manager.get_bills()
        # After get_bills(), the status should be updated to overdue
        assert any(b['status'] == 'overdue' for b in bills)
