"""Integration test for Amex workflow end-to-end."""

import pytest
import os
import tempfile
from modules.core.bill_manager import BillManager
from modules.core.amex_parser import AmexParser
from modules.core.ai_trainer import AITrainer


class TestAmexWorkflowIntegration:
    """Integration tests for complete Amex workflow."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def sample_amex_csv(self, temp_dir):
        """Create a sample Amex CSV file."""
        csv_path = os.path.join(temp_dir, 'amex_test.csv')
        data = """Date,Description,Card Member,Account #,Amount
2025-10-05,ICA SUPERMARKET,JOHN DOE,*****1234,856.50
2025-10-08,SHELL PETROL STATION,JOHN DOE,*****1234,650.00
2025-10-12,NETFLIX.COM,JOHN DOE,*****1234,119.00
2025-10-15,WILLYS SUPERMARKET,JOHN DOE,*****1234,1234.00
2025-10-18,STADIUM SPORT,JOHN DOE,*****1234,2375.00"""
        
        with open(csv_path, 'w') as f:
            f.write(data)
        
        return csv_path
    
    def test_complete_amex_workflow(self, temp_dir, sample_amex_csv):
        """Test the complete Amex workflow from bill creation to AI training."""
        
        # Step 1: Create an Amex bill manually
        bill_manager = BillManager(yaml_dir=temp_dir)
        bill = bill_manager.add_bill(
            name='American Express',
            amount=5234.50,
            due_date='2025-11-15',
            account='1722 20 34439',
            description='Monthly Amex bill',
            is_amex_bill=True
        )
        
        assert bill is not None
        assert bill['is_amex_bill'] is True
        assert bill['amount'] == 5234.50
        assert bill['line_items'] == []
        
        # Step 2: Parse Amex CSV
        parser = AmexParser(bill_manager=bill_manager)
        line_items, metadata = parser.parse_amex_csv(sample_amex_csv)
        
        assert len(line_items) == 5
        assert metadata['total_amount'] == 5234.50
        assert metadata['count'] == 5
        
        # Step 3: Find matching bill
        matched_bill = parser.find_matching_bill(metadata)
        
        assert matched_bill is not None
        assert matched_bill['id'] == bill['id']
        assert matched_bill['is_amex_bill'] is True
        
        # Step 4: Create linkage preview
        preview = parser.create_linkage_preview(line_items, metadata, matched_bill)
        
        assert preview['line_items_count'] == 5
        assert preview['purchases_total'] == 5234.50
        assert preview['net_balance'] == 5234.50  # No payments in this CSV
        assert preview['matched_bill'] is not None
        assert preview['match_confidence'] > 0.9  # High confidence match
        assert preview['will_create_new_bill'] is False
        
        # Step 5: Import line items to bill
        success = bill_manager.import_line_items_from_csv(bill['id'], line_items)
        
        assert success is True
        
        # Verify line items are saved
        updated_bill = bill_manager.get_bill_by_id(bill['id'])
        assert len(updated_bill['line_items']) == 5
        
        # Step 6: Verify line item properties
        first_item = updated_bill['line_items'][0]
        assert first_item['vendor'] == 'Ica Supermarket'
        assert first_item['amount'] == 856.50
        assert first_item['category'] == 'Mat & Dryck'
        assert first_item['subcategory'] == 'Matinköp'
        assert first_item['is_historical_record'] is True
        assert first_item['affects_cash'] is False
        
        # Step 7: Get all line items
        all_items = bill_manager.get_all_line_items()
        assert len(all_items) == 5
        
        # All items should have bill context
        assert all('bill_id' in item for item in all_items)
        assert all('bill_name' in item for item in all_items)
        
        # Step 8: Train AI with line items
        ai_trainer = AITrainer(yaml_dir=temp_dir)
        
        # Select some line items for training
        training_items = updated_bill['line_items'][:3]
        added_count = ai_trainer.add_training_samples_batch(training_items)
        
        assert added_count == 3
        
        # Verify training data
        training_data = ai_trainer.get_training_data()
        assert len(training_data) == 3
        assert training_data[0]['source'] == 'amex_line_item'
        assert training_data[0]['manual'] is True
        
        # Step 9: Verify cash flow impact
        # Bill total should be 5234.50
        assert bill['amount'] == 5234.50
        
        # Line items should NOT affect cash (affects_cash = False)
        for item in updated_bill['line_items']:
            assert item['affects_cash'] is False
            assert item['is_historical_record'] is True
        
        # Step 10: Mark bill as paid (simulating bank payment matching)
        success = bill_manager.mark_as_paid(bill['id'], transaction_id='TX-2025-11-14-AMEX-5234.50')
        
        assert success is True
        
        paid_bill = bill_manager.get_bill_by_id(bill['id'])
        assert paid_bill['status'] == 'paid'
        assert paid_bill['matched_transaction_id'] == 'TX-2025-11-14-AMEX-5234.50'
        
        # Line items should still be available for analysis
        assert len(paid_bill['line_items']) == 5
    
    def test_amex_workflow_with_filtering(self, temp_dir, sample_amex_csv):
        """Test filtering line items by category and date."""
        
        # Create bill and import line items
        bill_manager = BillManager(yaml_dir=temp_dir)
        bill = bill_manager.add_bill(
            name='American Express',
            amount=5234.50,
            due_date='2025-11-15',
            is_amex_bill=True
        )
        
        parser = AmexParser(bill_manager=bill_manager)
        line_items, _ = parser.parse_amex_csv(sample_amex_csv)
        bill_manager.import_line_items_from_csv(bill['id'], line_items)
        
        # Filter by category
        food_items = bill_manager.get_all_line_items(category='Mat & Dryck')
        assert len(food_items) == 2  # ICA and Willys
        
        # Filter by date range
        items_in_range = bill_manager.get_all_line_items(
            start_date='2025-10-01',
            end_date='2025-10-10'
        )
        assert len(items_in_range) == 2  # ICA (10-05) and Shell (10-08)
    
    def test_amex_workflow_no_matching_bill(self, temp_dir, sample_amex_csv):
        """Test CSV import when no matching bill exists."""
        
        bill_manager = BillManager(yaml_dir=temp_dir)
        parser = AmexParser(bill_manager=bill_manager)
        
        # Parse CSV without creating a bill
        line_items, metadata = parser.parse_amex_csv(sample_amex_csv)
        
        # Try to find matching bill
        matched_bill = parser.find_matching_bill(metadata)
        
        # No bill should be found
        assert matched_bill is None
        
        # Preview should indicate new bill creation
        preview = parser.create_linkage_preview(line_items, metadata, None)
        assert preview['will_create_new_bill'] is True
        assert preview['matched_bill'] is None
    
    def test_amex_workflow_multiple_bills(self, temp_dir, sample_amex_csv):
        """Test that CSV matches the correct bill when multiple exist."""
        
        bill_manager = BillManager(yaml_dir=temp_dir)
        
        # Create two Amex bills with different amounts
        bill1 = bill_manager.add_bill(
            name='Amex Bill 1',
            amount=1000.00,
            due_date='2025-11-10',
            is_amex_bill=True
        )
        
        bill2 = bill_manager.add_bill(
            name='Amex Bill 2',
            amount=5234.50,  # Matches CSV total
            due_date='2025-11-15',
            is_amex_bill=True
        )
        
        # Parse CSV
        parser = AmexParser(bill_manager=bill_manager)
        line_items, metadata = parser.parse_amex_csv(sample_amex_csv)
        
        # Should match bill2 based on amount
        matched_bill = parser.find_matching_bill(metadata)
        
        assert matched_bill is not None
        assert matched_bill['id'] == bill2['id']
        assert matched_bill['amount'] == 5234.50
    
    def test_line_item_edit_workflow(self, temp_dir, sample_amex_csv):
        """Test editing line items after import."""
        
        bill_manager = BillManager(yaml_dir=temp_dir)
        bill = bill_manager.add_bill(
            name='American Express',
            amount=5234.50,
            due_date='2025-11-15',
            is_amex_bill=True
        )
        
        # Import line items
        parser = AmexParser(bill_manager=bill_manager)
        line_items, _ = parser.parse_amex_csv(sample_amex_csv)
        bill_manager.import_line_items_from_csv(bill['id'], line_items)
        
        # Get first line item
        updated_bill = bill_manager.get_bill_by_id(bill['id'])
        first_item = updated_bill['line_items'][0]
        
        # Update the line item category
        success = bill_manager.update_line_item(
            bill_id=bill['id'],
            line_item_id=first_item['id'],
            updates={
                'category': 'Shopping',
                'subcategory': 'Food Shopping'
            }
        )
        
        assert success is True
        
        # Verify update
        updated_bill = bill_manager.get_bill_by_id(bill['id'])
        updated_item = updated_bill['line_items'][0]
        assert updated_item['category'] == 'Shopping'
        assert updated_item['subcategory'] == 'Food Shopping'
