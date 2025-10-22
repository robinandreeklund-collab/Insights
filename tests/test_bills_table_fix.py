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
        
        # Create an Amex bill with line items
        bill2 = bill_manager.add_bill(
            name='American Express',
            amount=5234.50,
            due_date='2025-11-15',
            is_amex_bill=True
        )
        
        # Add line items to Amex bill
        bill_manager.add_line_item(
            bill_id=bill2['id'],
            vendor='ICA',
            description='Food',
            amount=100.00,
            date='2025-10-05',
            category='Mat & Dryck'
        )
        
        # Get all bills
        bills = bill_manager.get_bills()
        
        # Verify raw bills have line_items and is_amex_bill
        amex_bill = [b for b in bills if b.get('is_amex_bill')][0]
        assert 'line_items' in amex_bill
        assert 'is_amex_bill' in amex_bill
        assert len(amex_bill['line_items']) == 1
        
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
        
        # Verify filtered data doesn't have line_items or is_amex_bill
        for row in table_data:
            assert 'line_items' not in row
            assert 'is_amex_bill' not in row
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
