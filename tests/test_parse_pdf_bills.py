"""Tests for PDF bill parser module."""

import os
import pytest
from modules.core.parse_pdf_bills import PDFBillParser, extract_bills_from_pdf
from modules.core.bill_manager import BillManager
import tempfile
import shutil


class TestPDFBillParser:
    """Test suite for PDFBillParser class."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up and tear down test environment."""
        self.parser = PDFBillParser()
        self.test_dir = tempfile.mkdtemp()
        
        yield
        
        # Clean up
        shutil.rmtree(self.test_dir)
    
    def test_parser_initialization(self):
        """Test that parser initializes correctly."""
        assert 'pdf' in self.parser.supported_formats
    
    def test_parse_pdf_placeholder(self):
        """Test PDF parsing with placeholder data."""
        # Create a dummy file
        dummy_pdf = os.path.join(self.test_dir, "test.pdf")
        with open(dummy_pdf, 'w') as f:
            f.write("dummy content")
        
        bills = self.parser.parse_pdf(dummy_pdf)
        
        # Should return example bills
        assert len(bills) > 0
        assert all('name' in bill for bill in bills)
        assert all('amount' in bill for bill in bills)
        assert all('due_date' in bill for bill in bills)
    
    def test_parse_pdf_nonexistent_file(self):
        """Test parsing with nonexistent file."""
        with pytest.raises(FileNotFoundError):
            self.parser.parse_pdf("nonexistent.pdf")
    
    def test_validate_bill_data_valid(self):
        """Test validating valid bill data."""
        from datetime import datetime, timedelta
        
        valid_bill = {
            'name': 'Test Bill',
            'amount': 100.0,
            'due_date': (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
        }
        
        assert self.parser.validate_bill_data(valid_bill)
    
    def test_validate_bill_data_missing_fields(self):
        """Test validating bill data with missing fields."""
        invalid_bill = {
            'name': 'Test Bill',
            'amount': 100.0
            # Missing due_date
        }
        
        assert not self.parser.validate_bill_data(invalid_bill)
    
    def test_validate_bill_data_invalid_amount(self):
        """Test validating bill data with invalid amount."""
        from datetime import datetime, timedelta
        
        invalid_bill = {
            'name': 'Test Bill',
            'amount': 'not a number',
            'due_date': (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
        }
        
        assert not self.parser.validate_bill_data(invalid_bill)
    
    def test_validate_bill_data_invalid_date(self):
        """Test validating bill data with invalid date format."""
        invalid_bill = {
            'name': 'Test Bill',
            'amount': 100.0,
            'due_date': 'invalid-date'
        }
        
        assert not self.parser.validate_bill_data(invalid_bill)
    
    def test_import_bills_to_manager(self):
        """Test importing bills to bill manager."""
        bill_manager = BillManager(yaml_dir=self.test_dir)
        
        # Create a dummy file
        dummy_pdf = os.path.join(self.test_dir, "test.pdf")
        with open(dummy_pdf, 'w') as f:
            f.write("dummy content")
        
        count = self.parser.import_bills_to_manager(dummy_pdf, bill_manager)
        
        assert count > 0
        
        # Verify bills were actually added
        bills = bill_manager.get_bills()
        assert len(bills) == count
    
    def test_parse_pdf_demo_mode(self):
        """Test parsing with demo mode (no file required)."""
        # Should work without an actual file when demo mode is enabled
        bills = self.parser.parse_pdf("nonexistent.pdf", use_demo_data=True)
        
        assert len(bills) > 0
        assert all('name' in bill for bill in bills)
        assert all('amount' in bill for bill in bills)
        assert all('due_date' in bill for bill in bills)
    
    def test_import_bills_demo_mode(self):
        """Test importing bills with demo mode."""
        bill_manager = BillManager(yaml_dir=self.test_dir)
        
        # Should work without an actual file when demo mode is enabled
        count = self.parser.import_bills_to_manager("nonexistent.pdf", bill_manager, use_demo_data=True)
        
        assert count > 0
        
        # Verify bills were actually added
        bills = bill_manager.get_bills()
        assert len(bills) == count
    
    def test_extract_bills_from_pdf_function(self):
        """Test the wrapper function."""
        # Create a dummy file
        dummy_pdf = os.path.join(self.test_dir, "test.pdf")
        with open(dummy_pdf, 'w') as f:
            f.write("dummy content")
        
        bills = extract_bills_from_pdf(dummy_pdf)
        
        assert len(bills) > 0
        assert all('name' in bill for bill in bills)
    
    def test_extract_nordea_payment_format(self):
        """Test extraction from Nordea Hantera betalningar format."""
        # Use the actual test PDF if it exists
        test_pdf = "test_nordea_betalningar.pdf"
        if os.path.exists(test_pdf):
            bills = self.parser.parse_pdf(test_pdf)
            
            # Should extract all 8 bills
            assert len(bills) == 8
            
            # All bills should have account information
            assert all('account' in bill for bill in bills)
            
            # Check that bills are properly distributed across accounts
            accounts = set(bill['account'] for bill in bills)
            assert len(accounts) == 3  # 3 different accounts
            
            # Verify some specific bills
            bill_names = [bill['name'] for bill in bills]
            assert 'Elräkning Vattenfall' in bill_names
            assert 'Netflix Abonnemang' in bill_names
            assert 'Hyresavi November' in bill_names
    
    def test_nordea_format_detection(self):
        """Test detection of Nordea payment format."""
        nordea_text = """
        Nordea - Hantera betalningar
        Konto: 3570 12 34567
        Faktura              Belopp      Förfallodatum
        Elräkning            1,245.50    2025-11-15
        """
        
        assert self.parser._is_nordea_payment_format(nordea_text)
        
        simple_text = "Some bill 123.45"
        assert not self.parser._is_nordea_payment_format(simple_text)
    
    def test_bill_categorization(self):
        """Test bill categorization logic."""
        assert self.parser._categorize_bill("Elräkning Vattenfall") == "Boende"
        assert self.parser._categorize_bill("Netflix Abonnemang") == "Nöje"
        assert self.parser._categorize_bill("Spotify Premium") == "Nöje"
        assert self.parser._categorize_bill("Telenor Mobilabonnemang") == "Boende"
        assert self.parser._categorize_bill("Random bill") == "Övrigt"
    
    def test_import_with_accounts(self):
        """Test importing bills with account information."""
        bill_manager = BillManager(yaml_dir=self.test_dir)
        
        # Use the actual test PDF if it exists
        test_pdf = "test_nordea_betalningar.pdf"
        if os.path.exists(test_pdf):
            count = self.parser.import_bills_to_manager(test_pdf, bill_manager)
            
            assert count == 8
            
            # Get bills grouped by account
            bills_by_account = bill_manager.get_bills_by_account()
            
            # Should have 3 accounts
            assert len(bills_by_account) == 3
            
            # Check account summary
            summaries = bill_manager.get_account_summary()
            assert len(summaries) == 3
            
            # Each summary should have the expected structure
            for summary in summaries:
                assert 'account' in summary
                assert 'bill_count' in summary
                assert 'total_amount' in summary
                assert 'bills' in summary
                assert summary['bill_count'] > 0
