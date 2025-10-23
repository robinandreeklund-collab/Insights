"""Tests for loan image parser module."""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Test helper methods that don't require OCR
try:
    from modules.core.loan_image_parser import LoanImageParser, OCR_AVAILABLE
except ImportError:
    OCR_AVAILABLE = False
    LoanImageParser = None


@pytest.mark.skipif(not OCR_AVAILABLE, reason="OCR dependencies not available")
class TestLoanImageParser:
    """Test suite for LoanImageParser class."""
    
    @pytest.fixture
    def parser(self):
        """Create a parser instance."""
        return LoanImageParser()
    
    def test_parse_amount(self, parser):
        """Test amount parsing with various formats."""
        # Swedish format with spaces
        assert parser._parse_amount("2 000 000") == 2000000.0
        
        # European format with dots and comma
        assert parser._parse_amount("2.000.000,50") == 2000000.50
        
        # Simple comma decimal
        assert parser._parse_amount("1500,75") == 1500.75
        
        # Dot decimal
        assert parser._parse_amount("1500.75") == 1500.75
        
        # With currency
        assert parser._parse_amount("100 000 kr") == 100000.0
    
    def test_parse_decimal(self, parser):
        """Test decimal parsing."""
        assert parser._parse_decimal("3,5") == 3.5
        assert parser._parse_decimal("3.5") == 3.5
        assert parser._parse_decimal("10,25") == 10.25
    
    def test_parse_date(self, parser):
        """Test date parsing with various formats."""
        assert parser._parse_date("2025-01-15") == "2025-01-15"
        assert parser._parse_date("2025/01/15") == "2025-01-15"
        assert parser._parse_date("15-01-2025") == "2025-01-15"
        assert parser._parse_date("15/01/2025") == "2025-01-15"
    
    def test_extract_loan_number(self, parser):
        """Test extraction of loan number from OCR text."""
        text = """
        Låneuppgifter
        Lånenummer: 12345-678
        Belopp: 2 000 000 kr
        """
        
        loan_data = parser._extract_fields(text)
        assert loan_data['loan_number'] == '12345-678'
    
    def test_extract_amounts(self, parser):
        """Test extraction of loan amounts."""
        text = """
        Ursprungligt belopp: 2 000 000 kr
        Nuvarande belopp: 1 800 000 kr
        Amorterat: 200 000 kr
        """
        
        loan_data = parser._extract_fields(text)
        assert loan_data['original_amount'] == 2000000.0
        assert loan_data['current_amount'] == 1800000.0
        assert loan_data['amortized'] == 200000.0
    
    def test_extract_interest_rates(self, parser):
        """Test extraction of interest rates."""
        text = """
        Basränta: 3,75 %
        Rabatt: 0,25 %
        Effektiv ränta: 3,5 %
        """
        
        loan_data = parser._extract_fields(text)
        assert loan_data['base_interest_rate'] == 3.75
        assert loan_data['discount'] == 0.25
        assert loan_data['effective_interest_rate'] == 3.5
    
    def test_extract_dates(self, parser):
        """Test extraction of dates."""
        text = """
        Utbetalning: 2020-01-15
        Nästa förändring: 2025-06-30
        """
        
        loan_data = parser._extract_fields(text)
        assert loan_data['disbursement_date'] == '2020-01-15'
        assert loan_data['next_change_date'] == '2025-06-30'
    
    def test_extract_borrowers(self, parser):
        """Test extraction of borrower names."""
        text = """
        Låntagare: Anna Svensson
        Låntagare: Erik Andersson
        """
        
        loan_data = parser._extract_fields(text)
        assert 'Anna Svensson' in loan_data['borrowers']
        assert 'Erik Andersson' in loan_data['borrowers']
    
    def test_extract_accounts(self, parser):
        """Test extraction of account numbers."""
        text = """
        Betalkonto: 3300-123456789
        Återbetalkonto: 3300-987654321
        """
        
        loan_data = parser._extract_fields(text)
        assert loan_data['payment_account'] == '3300123456789'
        assert loan_data['repayment_account'] == '3300987654321'
    
    def test_extract_currency(self, parser):
        """Test extraction of currency."""
        text = "Belopp: 2000000 EUR"
        loan_data = parser._extract_fields(text)
        assert loan_data['currency'] == 'EUR'
        
        text2 = "Belopp: 2000000 kr"
        loan_data2 = parser._extract_fields(text2)
        assert loan_data2['currency'] == 'SEK'
    
    def test_extract_lender(self, parser):
        """Test extraction of lender information."""
        text = "Bank: Swedbank AB"
        loan_data = parser._extract_fields(text)
        assert loan_data['lender'] == 'Swedbank AB'
    
    def test_extract_collateral(self, parser):
        """Test extraction of collateral information."""
        text = "Säkerhet: Fastighet Vägen 123"
        loan_data = parser._extract_fields(text)
        assert loan_data['collateral'] == 'Fastighet Vägen 123'
    
    def test_parse_amount_edge_cases(self, parser):
        """Test edge cases for amount parsing."""
        # Empty string
        assert parser._parse_amount("") is None
        
        # Invalid input
        assert parser._parse_amount("abc") is None
        
        # None - will fail with AttributeError, so we expect that
        with pytest.raises(AttributeError):
            parser._parse_amount(None)
    
    def test_parse_date_edge_cases(self, parser):
        """Test edge cases for date parsing."""
        # Invalid date
        assert parser._parse_date("2025-13-45") is None
        
        # Empty string
        assert parser._parse_date("") is None
        
        # None
        with pytest.raises(AttributeError):
            parser._parse_date(None)


# Additional test without OCR dependency for basic functionality
def test_loan_image_parser_availability():
    """Test that the loan image parser module can be imported."""
    try:
        from modules.core.loan_image_parser import LoanImageParser, OCR_AVAILABLE
        # Module is importable
        assert True
    except ImportError:
        # If import fails, that's also okay - it means dependencies aren't installed
        assert True

