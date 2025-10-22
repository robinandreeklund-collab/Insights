"""Tests for Bill Manager Line Items functionality."""

import pytest
import os
import tempfile
from modules.core.bill_manager import BillManager


class TestBillManagerLineItems:
    """Test cases for line items functionality in BillManager."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def manager(self, temp_dir):
        """Create a BillManager instance."""
        return BillManager(yaml_dir=temp_dir)
    
    def test_add_bill_with_amex_flag(self, manager):
        """Test adding an Amex bill."""
        bill = manager.add_bill(
            name='American Express',
            amount=5000.00,
            due_date='2025-11-15',
            account='1722 20 34439',
            is_amex_bill=True
        )
        
        assert bill['is_amex_bill'] is True
        assert bill['line_items'] == []
    
    def test_add_line_item(self, manager):
        """Test adding a line item to a bill."""
        # Create bill
        bill = manager.add_bill(
            name='American Express',
            amount=5000.00,
            due_date='2025-11-15',
            is_amex_bill=True
        )
        
        # Add line item
        line_item = manager.add_line_item(
            bill_id=bill['id'],
            vendor='ICA Supermarket',
            description='Groceries',
            amount=856.50,
            date='2025-10-05',
            category='Mat & Dryck',
            subcategory='Matinköp'
        )
        
        assert line_item is not None
        assert line_item['vendor'] == 'ICA Supermarket'
        assert line_item['amount'] == 856.50
        assert line_item['is_historical_record'] is True
        assert line_item['affects_cash'] is False
        
        # Verify it's saved
        bill = manager.get_bill_by_id(bill['id'])
        assert len(bill['line_items']) == 1
        assert bill['line_items'][0]['id'] == line_item['id']
    
    def test_add_multiple_line_items(self, manager):
        """Test adding multiple line items."""
        bill = manager.add_bill(
            name='American Express',
            amount=5000.00,
            due_date='2025-11-15',
            is_amex_bill=True
        )
        
        # Add multiple line items
        for i in range(5):
            manager.add_line_item(
                bill_id=bill['id'],
                vendor=f'Vendor {i}',
                description=f'Purchase {i}',
                amount=100.00 * (i + 1),
                date=f'2025-10-{i+1:02d}'
            )
        
        # Verify all saved
        bill = manager.get_bill_by_id(bill['id'])
        assert len(bill['line_items']) == 5
        
        # Check IDs are unique
        ids = [item['id'] for item in bill['line_items']]
        assert len(ids) == len(set(ids))
    
    def test_update_line_item(self, manager):
        """Test updating a line item."""
        bill = manager.add_bill(
            name='American Express',
            amount=5000.00,
            due_date='2025-11-15',
            is_amex_bill=True
        )
        
        line_item = manager.add_line_item(
            bill_id=bill['id'],
            vendor='ICA',
            description='Food',
            amount=100.00,
            date='2025-10-05'
        )
        
        # Update the line item
        success = manager.update_line_item(
            bill_id=bill['id'],
            line_item_id=line_item['id'],
            updates={
                'category': 'Mat & Dryck',
                'subcategory': 'Matinköp',
                'vendor': 'ICA Supermarket'
            }
        )
        
        assert success is True
        
        # Verify update
        bill = manager.get_bill_by_id(bill['id'])
        updated_item = bill['line_items'][0]
        assert updated_item['category'] == 'Mat & Dryck'
        assert updated_item['subcategory'] == 'Matinköp'
        assert updated_item['vendor'] == 'ICA Supermarket'
    
    def test_delete_line_item(self, manager):
        """Test deleting a line item."""
        bill = manager.add_bill(
            name='American Express',
            amount=5000.00,
            due_date='2025-11-15',
            is_amex_bill=True
        )
        
        # Add two line items
        item1 = manager.add_line_item(
            bill_id=bill['id'],
            vendor='Vendor 1',
            description='Item 1',
            amount=100.00,
            date='2025-10-05'
        )
        
        item2 = manager.add_line_item(
            bill_id=bill['id'],
            vendor='Vendor 2',
            description='Item 2',
            amount=200.00,
            date='2025-10-06'
        )
        
        # Delete first item
        success = manager.delete_line_item(bill['id'], item1['id'])
        assert success is True
        
        # Verify deletion
        bill = manager.get_bill_by_id(bill['id'])
        assert len(bill['line_items']) == 1
        assert bill['line_items'][0]['id'] == item2['id']
    
    def test_get_line_items(self, manager):
        """Test getting line items for a bill."""
        bill = manager.add_bill(
            name='American Express',
            amount=5000.00,
            due_date='2025-11-15',
            is_amex_bill=True
        )
        
        # Add line items
        for i in range(3):
            manager.add_line_item(
                bill_id=bill['id'],
                vendor=f'Vendor {i}',
                description=f'Item {i}',
                amount=100.00,
                date='2025-10-05'
            )
        
        # Get line items
        line_items = manager.get_line_items(bill['id'])
        assert len(line_items) == 3
    
    def test_import_line_items_from_csv(self, manager):
        """Test importing multiple line items at once."""
        bill = manager.add_bill(
            name='American Express',
            amount=5000.00,
            due_date='2025-11-15',
            is_amex_bill=True
        )
        
        # Prepare line items data
        csv_line_items = [
            {
                'date': '2025-10-05',
                'vendor': 'ICA Supermarket',
                'description': 'Groceries',
                'amount': 856.50,
                'category': 'Mat & Dryck',
                'subcategory': 'Matinköp'
            },
            {
                'date': '2025-10-08',
                'vendor': 'Shell',
                'description': 'Fuel',
                'amount': 650.00,
                'category': 'Transport',
                'subcategory': 'Drivmedel'
            },
            {
                'date': '2025-10-12',
                'vendor': 'Netflix',
                'description': 'Subscription',
                'amount': 119.00,
                'category': 'Nöje',
                'subcategory': 'Streaming'
            }
        ]
        
        # Import
        success = manager.import_line_items_from_csv(bill['id'], csv_line_items)
        assert success is True
        
        # Verify
        bill = manager.get_bill_by_id(bill['id'])
        assert len(bill['line_items']) == 3
        
        # Check first item
        first_item = bill['line_items'][0]
        assert first_item['vendor'] == 'ICA Supermarket'
        assert first_item['amount'] == 856.50
        assert first_item['is_historical_record'] is True
        assert first_item['affects_cash'] is False
    
    def test_get_all_line_items(self, manager):
        """Test getting all line items across bills."""
        # Create two bills with line items
        bill1 = manager.add_bill(
            name='Amex Bill 1',
            amount=1000.00,
            due_date='2025-11-15',
            is_amex_bill=True
        )
        
        bill2 = manager.add_bill(
            name='Amex Bill 2',
            amount=2000.00,
            due_date='2025-12-15',
            is_amex_bill=True
        )
        
        # Add line items to both
        manager.add_line_item(
            bill_id=bill1['id'],
            vendor='Vendor A',
            description='Item A',
            amount=500.00,
            date='2025-10-01',
            category='Mat & Dryck'
        )
        
        manager.add_line_item(
            bill_id=bill2['id'],
            vendor='Vendor B',
            description='Item B',
            amount=1000.00,
            date='2025-10-15',
            category='Transport'
        )
        
        # Get all line items
        all_items = manager.get_all_line_items()
        assert len(all_items) == 2
        
        # Check that bill context is included
        assert all('bill_id' in item for item in all_items)
        assert all('bill_name' in item for item in all_items)
    
    def test_get_all_line_items_with_filters(self, manager):
        """Test filtering line items."""
        bill = manager.add_bill(
            name='Amex Bill',
            amount=5000.00,
            due_date='2025-11-15',
            is_amex_bill=True
        )
        
        # Add items with different categories and dates
        manager.add_line_item(
            bill_id=bill['id'],
            vendor='ICA',
            description='Food',
            amount=500.00,
            date='2025-10-01',
            category='Mat & Dryck'
        )
        
        manager.add_line_item(
            bill_id=bill['id'],
            vendor='Shell',
            description='Fuel',
            amount=600.00,
            date='2025-10-15',
            category='Transport'
        )
        
        manager.add_line_item(
            bill_id=bill['id'],
            vendor='Willys',
            description='Groceries',
            amount=700.00,
            date='2025-10-20',
            category='Mat & Dryck'
        )
        
        # Filter by category
        food_items = manager.get_all_line_items(category='Mat & Dryck')
        assert len(food_items) == 2
        
        # Filter by date range
        items_in_range = manager.get_all_line_items(
            start_date='2025-10-10',
            end_date='2025-10-20'
        )
        assert len(items_in_range) == 2
    
    def test_line_item_backward_compatibility(self, manager):
        """Test that bills without line_items still work."""
        # Add a regular bill (not Amex)
        bill = manager.add_bill(
            name='Regular Bill',
            amount=500.00,
            due_date='2025-11-15'
        )
        
        # Should have empty line_items
        assert bill['line_items'] == []
        
        # Getting line items should return empty list
        line_items = manager.get_line_items(bill['id'])
        assert line_items == []
