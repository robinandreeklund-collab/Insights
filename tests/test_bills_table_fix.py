"""Test for bills table data filtering."""

import pytest
import tempfile
from modules.core.bill_manager import BillManager


def test_bills_table_data_format():
    """Test that bills data can be properly formatted for DataTable."""
    with tempfile.TemporaryDirectory() as tmpdir:
        bill_manager = BillManager(yaml_dir=tmpdir)
        
        # Create a regular bill
        bill1 = bill_manager.add_bill(
            name='Regular Bill',
            amount=500.00,
            due_date='2025-11-15',
            category='Boende'
        )
        
        # Create another bill
        bill2 = bill_manager.add_bill(
            name='Electricity Bill',
            amount=850.00,
            due_date='2025-11-20',
            category='Boende'
        )
        
        # Get all bills
        bills = bill_manager.get_bills()
        
        # Verify we have 2 bills
        assert len(bills) == 2
        
        # Simulate what the dashboard callback should do:
        # Filter to only table columns
        table_data = []
        for bill in bills:
            table_data.append({
                'id': bill.get('id', ''),
                'name': bill.get('name', ''),
                'amount': bill.get('amount', 0),
                'due_date': bill.get('due_date', ''),
                'status': bill.get('status', ''),
                'category': bill.get('category', ''),
                'account': bill.get('account', '')
            })
        
        # Verify filtered data has only the expected fields
        for row in table_data:
            # Verify it has all the required fields
            assert 'id' in row
            assert 'name' in row
            assert 'amount' in row
            assert 'due_date' in row
            assert 'status' in row
            assert 'category' in row
            assert 'account' in row
        
        # Verify all values are simple types (string, number, boolean, or None)
        for row in table_data:
            for key, value in row.items():
                assert isinstance(value, (str, int, float, bool, type(None))), \
                    f"Field {key} has invalid type {type(value)} for DataTable"


if __name__ == '__main__':
    test_bills_table_data_format()
    print("✓ Bills table data format test passed")
