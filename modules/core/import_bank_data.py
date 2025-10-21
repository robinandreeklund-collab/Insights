"""Import bank data module for loading and normalizing data from various formats."""

from typing import Optional
import pandas as pd


def load_file(path: str) -> pd.DataFrame:
    """
    Load a file from the given path.
    
    Args:
        path: Path to the file (CSV, Excel, or JSON)
        
    Returns:
        DataFrame with the loaded data
    """
    pass


def detect_format(data: pd.DataFrame) -> str:
    """
    Detect the format of the bank data.
    
    Args:
        data: DataFrame with bank data
        
    Returns:
        String indicating the detected format (e.g., 'nordea', 'swedbank')
    """
    pass


def normalize_columns(data: pd.DataFrame, format: str) -> pd.DataFrame:
    """
    Normalize column names based on the detected format.
    
    Args:
        data: DataFrame with bank data
        format: Detected format string
        
    Returns:
        DataFrame with normalized column names
    """
    pass
