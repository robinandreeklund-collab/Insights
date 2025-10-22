"""Tests for Amex Parser."""

import pytest
import os
import tempfile
import pandas as pd
from modules.core.amex_parser import AmexParser
from modules.core.bill_manager import BillManager


class TestAmexParser:
    """Test cases for AmexParser."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def parser(self, temp_dir):
        """Create an AmexParser instance with a temp bill manager."""
        bill_manager = BillManager(yaml_dir=temp_dir)
        return AmexParser(bill_manager=bill_manager)
    
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
    
    @pytest.fixture
    def swedish_amex_csv(self, temp_dir):
        """Create a sample Swedish Amex CSV file."""
        csv_path = os.path.join(temp_dir, 'amex_swedish.csv')
        data = """Datum,Beskrivning,Kortmedlem,Konto #,Belopp
10/05/2025,COOP HJO,KARL FROJD,-31009,"164,00"
10/08/2025,SHELL BENSIN,KARL FROJD,-31009,"650,00"
10/12/2025,SPOTIFY STOCKHOLM,KARL FROJD,-31009,"129,00"
10/15/2025,PAYEX*WILLYS E HANDEL,KARL FROJD,-31009,"1234,00"
09/29/2025,"BETALNING MOTTAGEN, TACK",KARL FROJD,-31009,"-5000,00"
10/18/2025,STADIUM SPORT,KARL FROJD,-31009,"2375,00""" 
        
        with open(csv_path, 'w') as f:
            f.write(data)
        
        return csv_path
    
    def test_detect_amex_format_positive(self, parser):
        """Test Amex format detection with valid Amex CSV."""
        df = pd.DataFrame({
            'Date': ['2025-10-01'],
            'Description': ['Test'],
            'Card Member': ['John Doe'],
            'Account #': ['*****1234'],
            'Amount': [100.00]
        })
        
        assert parser.detect_amex_format(df) is True
    
    def test_detect_amex_format_negative(self, parser):
        """Test Amex format detection with non-Amex CSV."""
        df = pd.DataFrame({
            'Bokföringsdag': ['2025/10/01'],
            'Belopp': [-100.00],
            'Namn': ['Test']
        })
        
        assert parser.detect_amex_format(df) is False
    
    def test_parse_amex_csv(self, parser, sample_amex_csv):
        """Test parsing an Amex CSV file."""
        line_items, metadata = parser.parse_amex_csv(sample_amex_csv)
        
        # Check line items
        assert len(line_items) == 5
        assert all('date' in item for item in line_items)
        assert all('vendor' in item for item in line_items)
        assert all('description' in item for item in line_items)
        assert all('amount' in item for item in line_items)
        assert all('category' in item for item in line_items)
        
        # Check metadata
        assert metadata['count'] == 5
        assert metadata['purchases_total'] == 5234.50  # Sum of purchases only
        assert metadata['total_amount'] == 5234.50  # Net balance (no payments in this CSV)
        assert metadata['earliest_date'] == '2025-10-05'
        assert metadata['latest_date'] == '2025-10-18'
    
    def test_auto_categorize_food(self, parser):
        """Test auto-categorization of food vendors."""
        category, subcategory = parser._auto_categorize('ICA Supermarket', 'ICA SUPERMARKET')
        assert category == 'Mat & Dryck'
        assert subcategory == 'Matinköp'
    
    def test_auto_categorize_fuel(self, parser):
        """Test auto-categorization of fuel vendors."""
        category, subcategory = parser._auto_categorize('Shell', 'SHELL PETROL STATION')
        assert category == 'Transport'
        assert subcategory == 'Drivmedel'
    
    def test_auto_categorize_streaming(self, parser):
        """Test auto-categorization of streaming services."""
        category, subcategory = parser._auto_categorize('Netflix', 'NETFLIX.COM')
        assert category == 'Nöje'
        assert subcategory == 'Streaming'
    
    def test_auto_categorize_sports(self, parser):
        """Test auto-categorization of sports vendors."""
        category, subcategory = parser._auto_categorize('Stadium Sport', 'STADIUM SPORT')
        assert category == 'Shopping'
        assert subcategory == 'Sport'
    
    def test_find_matching_bill(self, parser, sample_amex_csv, temp_dir):
        """Test finding a matching bill for Amex CSV."""
        # Create a matching bill
        bill_manager = BillManager(yaml_dir=temp_dir)
        bill = bill_manager.add_bill(
            name='American Express',
            amount=5234.50,
            due_date='2025-11-15',
            account='1722 20 34439',
            is_amex_bill=True
        )
        
        # Parse CSV
        parser.bill_manager = bill_manager
        line_items, metadata = parser.parse_amex_csv(sample_amex_csv)
        
        # Find matching bill
        matched_bill = parser.find_matching_bill(metadata)
        
        assert matched_bill is not None
        assert matched_bill['id'] == bill['id']
        assert matched_bill['amount'] == 5234.50
    
    def test_find_matching_bill_no_match(self, parser, sample_amex_csv, temp_dir):
        """Test when no matching bill exists."""
        # Don't create any bills
        bill_manager = BillManager(yaml_dir=temp_dir)
        parser.bill_manager = bill_manager
        
        # Parse CSV
        line_items, metadata = parser.parse_amex_csv(sample_amex_csv)
        
        # Try to find matching bill
        matched_bill = parser.find_matching_bill(metadata)
        
        assert matched_bill is None
    
    def test_create_linkage_preview_with_match(self, parser, sample_amex_csv, temp_dir):
        """Test creating a linkage preview with a matched bill."""
        # Create a matching bill
        bill_manager = BillManager(yaml_dir=temp_dir)
        bill = bill_manager.add_bill(
            name='American Express',
            amount=5234.50,
            due_date='2025-11-15',
            account='1722 20 34439',
            is_amex_bill=True
        )
        
        # Parse CSV
        parser.bill_manager = bill_manager
        line_items, metadata = parser.parse_amex_csv(sample_amex_csv)
        
        # Create preview
        preview = parser.create_linkage_preview(line_items, metadata, bill)
        
        assert preview['line_items_count'] == 5
        assert preview['purchases_total'] == 5234.50
        assert preview['net_balance'] == 5234.50
        assert preview['matched_bill'] is not None
        assert preview['matched_bill']['id'] == bill['id']
        assert preview['will_create_new_bill'] is False
        assert preview['match_confidence'] > 0.9
    
    def test_create_linkage_preview_no_match(self, parser, sample_amex_csv):
        """Test creating a linkage preview without a matched bill."""
        # Parse CSV
        line_items, metadata = parser.parse_amex_csv(sample_amex_csv)
        
        # Create preview without matched bill
        preview = parser.create_linkage_preview(line_items, metadata, None)
        
        assert preview['line_items_count'] == 5
        assert preview['purchases_total'] == 5234.50
        assert preview['net_balance'] == 5234.50
        assert preview['matched_bill'] is None
        assert preview['will_create_new_bill'] is True
        assert preview['match_confidence'] == 0.0
    
    def test_extract_vendor_from_description(self, parser):
        """Test vendor name extraction."""
        vendor = parser._extract_vendor_from_description('ICA SUPERMARKET STOCKHOLM 12345')
        assert 'Ica Supermarket Stockholm' in vendor
        
        vendor = parser._extract_vendor_from_description('SHELL PETROL STATION')
        assert 'Shell Petrol Station' in vendor
    
    def test_parse_swedish_amex_csv(self, parser, swedish_amex_csv):
        """Test parsing a Swedish Amex CSV file."""
        line_items, metadata = parser.parse_amex_csv(swedish_amex_csv)
        
        # Should have 5 line items (payment excluded)
        assert len(line_items) == 5
        assert metadata['count'] == 5
        
        # Check that payment was excluded
        assert all('betalning' not in item['description'].lower() for item in line_items)
        
        # Check amount parsing (Swedish format with comma as decimal separator)
        amounts = [item['amount'] for item in line_items]
        assert 164.00 in amounts
        assert 650.00 in amounts
        assert 129.00 in amounts
        
    def test_swedish_format_detection(self, parser, swedish_amex_csv):
        """Test detection of Swedish Amex format."""
        import pandas as pd
        df = pd.read_csv(swedish_amex_csv)
        assert parser.detect_amex_format(df) is True
    
    def test_payment_exclusion(self, parser, swedish_amex_csv):
        """Test that payment/credit transactions are excluded."""
        line_items, metadata = parser.parse_amex_csv(swedish_amex_csv)
        
        # Verify no negative transactions
        for item in line_items:
            assert item['amount'] > 0
            assert 'betalning' not in item['description'].lower()
            assert 'payment' not in item['description'].lower()
