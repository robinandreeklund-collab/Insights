"""Import bank data module for loading and normalizing data from various formats."""

from typing import Optional, Tuple
import pandas as pd
import re
import os
from datetime import datetime


def extract_account_name_from_filename(filename: str) -> Optional[str]:
    """
    Extract account name from filename.
    
    Examples:
        "PERSONKONTO 880104-7591 - 2025-10-21 15.38.56.csv" -> "PERSONKONTO 880104-7591"
        "PERSONKONTO 1709 20 72840 - 2025-10-21 09.39.41.csv" -> "PERSONKONTO 1709 20 72840"
        "path/to/PERSONKONTO 880104-7591.csv" -> "PERSONKONTO 880104-7591"
    
    Args:
        filename: Full path or filename
        
    Returns:
        Extracted account name or None
    """
    basename = os.path.basename(filename)
    # Remove file extension
    name_without_ext = os.path.splitext(basename)[0]
    
    # Try to extract account name pattern (e.g., "PERSONKONTO 880104-7591" or "PERSONKONTO 1709 20 72840")
    # Match "PERSONKONTO" followed by space and account number (digits, spaces, and hyphens)
    match = re.match(r'(PERSONKONTO\s+[\d\s-]+?)(?:\s*-\s*\d{4}-\d{2}-\d{2}|$)', name_without_ext)
    if match:
        return match.group(1).strip()
    
    # If no match, return the filename without timestamp and extension
    # Remove timestamp pattern like " - 2025-10-21 15.38.56"
    cleaned = re.sub(r'\s*-\s*\d{4}-\d{2}-\d{2}\s+\d{2}\.\d{2}\.\d{2}', '', name_without_ext)
    return cleaned.strip() if cleaned else None


def load_file(path: str) -> pd.DataFrame:
    """
    Load a file from the given path.
    
    Args:
        path: Path to the file (CSV, Excel, or JSON)
        
    Returns:
        DataFrame with the loaded data
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    
    file_ext = os.path.splitext(path)[1].lower()
    
    if file_ext == '.csv':
        # Try to detect encoding and delimiter
        try:
            # First try with UTF-8 and semicolon (common in Swedish banks)
            df = pd.read_csv(path, sep=';', encoding='utf-8')
        except:
            try:
                # Try with latin-1 encoding
                df = pd.read_csv(path, sep=';', encoding='latin-1')
            except:
                # Fall back to comma separator
                df = pd.read_csv(path, encoding='utf-8')
        return df
    elif file_ext in ['.xlsx', '.xls']:
        return pd.read_excel(path)
    elif file_ext == '.json':
        return pd.read_json(path)
    else:
        raise ValueError(f"Unsupported file format: {file_ext}")


def detect_format(data: pd.DataFrame) -> str:
    """
    Detect the format of the bank data.
    
    Args:
        data: DataFrame with bank data
        
    Returns:
        String indicating the detected format (e.g., 'nordea', 'amex', 'swedbank')
    """
    columns = [col.lower() for col in data.columns]
    
    # Amex format detection (check first to avoid false positives)
    amex_indicators = ['card member', 'cardmember']
    if any(indicator in columns for indicator in amex_indicators):
        return 'amex'
    
    # Also check for typical Amex column combination
    if 'date' in columns and 'description' in columns and 'amount' in columns:
        # If no typical bank columns but has these, might be Amex
        if 'bokföringsdag' not in columns and 'belopp' not in columns:
            return 'amex'
    
    # Nordea format detection
    # Swedish: Bokföringsdag, Belopp, Avsändare, Mottagare, Namn, Rubrik, Saldo, Valuta
    if 'bokföringsdag' in columns and 'belopp' in columns:
        return 'nordea'
    
    # Add more bank format detections here as needed
    # For now, default to 'nordea' if we have date and amount columns
    if any(col in columns for col in ['date', 'datum', 'bokföringsdag']) and \
       any(col in columns for col in ['amount', 'belopp']):
        return 'nordea'
    
    return 'unknown'


def normalize_columns(data: pd.DataFrame, format: str) -> pd.DataFrame:
    """
    Normalize column names based on the detected format.
    
    Args:
        data: DataFrame with bank data
        format: Detected format string
        
    Returns:
        DataFrame with normalized column names
    """
    df = data.copy()
    
    if format == 'nordea':
        # Map Nordea Swedish columns to standardized English names
        column_mapping = {
            'Bokföringsdag': 'date',
            'Belopp': 'amount',
            'Avsändare': 'sender',
            'Mottagare': 'receiver',
            'Namn': 'name',
            'Rubrik': 'description',
            'Saldo': 'balance',
            'Valuta': 'currency'
        }
        
        df = df.rename(columns=column_mapping)
        
        # Clean and convert data types
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], format='%Y/%m/%d', errors='coerce')
        
        if 'amount' in df.columns:
            # Convert Swedish number format (comma as decimal separator) to float
            df['amount'] = df['amount'].astype(str).str.replace(',', '.').astype(float)
        
        if 'balance' in df.columns:
            df['balance'] = df['balance'].astype(str).str.replace(',', '.').astype(float)
        
        # Fill NaN values in text columns with empty strings
        text_columns = ['sender', 'receiver', 'name', 'description']
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].fillna('')
    
    return df


def import_csv(csv_path: str) -> Tuple[str, pd.DataFrame]:
    """
    Import a CSV file and return account name and normalized transactions.
    
    Args:
        csv_path: Path to the CSV file
        
    Returns:
        Tuple of (account_name, normalized_dataframe)
    """
    # Extract account name from filename
    account_name = extract_account_name_from_filename(csv_path)
    if not account_name:
        raise ValueError(f"Could not extract account name from filename: {csv_path}")
    
    # Load and normalize the data
    df = load_file(csv_path)
    format_type = detect_format(df)
    normalized_df = normalize_columns(df, format_type)
    
    return account_name, normalized_df
