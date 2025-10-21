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
