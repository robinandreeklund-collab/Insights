"""Unit tests for import_bank_data module."""

import pytest
import pandas as pd
import os
from modules.core.import_bank_data import (
    extract_account_name_from_filename,
    load_file,
    detect_format,
    normalize_columns,
    import_csv
)


class TestImportBankData:
    """Test cases for import_bank_data module."""
    
    def test_extract_account_name_from_filename(self):
        """Test extracting account name from various filename formats."""
        # Test with full path and timestamp
        filename1 = "PERSONKONTO 880104-7591 - 2025-10-21 15.38.56.csv"
        assert extract_account_name_from_filename(filename1) == "PERSONKONTO 880104-7591"
        
        # Test with path
        filename2 = "/path/to/PERSONKONTO 880104-7591.csv"
        assert extract_account_name_from_filename(filename2) == "PERSONKONTO 880104-7591"
        
        # Test without timestamp
        filename3 = "PERSONKONTO 123456-7890.csv"
        assert extract_account_name_from_filename(filename3) == "PERSONKONTO 123456-7890"
    
    def test_detect_format_nordea(self):
        """Test detection of Nordea format."""
        # Create sample Nordea data
        data = pd.DataFrame({
            'Bokföringsdag': ['2025/10/01'],
            'Belopp': ['-35,00'],
            'Saldo': ['31,06']
        })
        
        format_type = detect_format(data)
        assert format_type == 'nordea'
    
    def test_normalize_columns_nordea(self):
        """Test normalization of Nordea columns."""
        # Create sample Nordea data
        data = pd.DataFrame({
            'Bokföringsdag': ['2025/10/01', '2025/09/01'],
            'Belopp': ['-35,00', '100,00'],
            'Avsändare': ['880104-7591', ''],
            'Mottagare': ['', '880104-7591'],
            'Namn': ['', ''],
            'Rubrik': ['Nordea Vardagspaket', 'Överföring'],
            'Saldo': ['31,06', '66,06'],
            'Valuta': ['SEK', 'SEK']
        })
        
        normalized = normalize_columns(data, 'nordea')
        
        # Check column names
        assert 'date' in normalized.columns
        assert 'amount' in normalized.columns
        assert 'balance' in normalized.columns
        assert 'description' in normalized.columns
        
        # Check data types and values
        assert normalized['amount'].dtype == float
        assert normalized['amount'].iloc[0] == -35.0
        assert normalized['amount'].iloc[1] == 100.0
        assert normalized['balance'].iloc[0] == 31.06
    
    def test_import_csv_integration(self):
        """Test complete CSV import flow."""
        csv_path = "PERSONKONTO 880104-7591 - 2025-10-21 15.38.56.csv"
        
        if os.path.exists(csv_path):
            account_name, df = import_csv(csv_path)
            
            # Verify account name
            assert account_name == "PERSONKONTO 880104-7591"
            
            # Verify DataFrame structure
            assert 'date' in df.columns
            assert 'amount' in df.columns
            assert 'description' in df.columns
            assert len(df) == 3  # We know there are 3 transactions in the test file


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
