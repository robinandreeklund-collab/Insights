"""Account manager module for creating and managing accounts."""

from typing import List, Dict, Optional
import yaml
import os
from datetime import datetime
import uuid
import re


def extract_account_number(account_name: str) -> Optional[str]:
    """Extract and normalize account number from account name.
    
    Extracts patterns like "1722 20 34439" from names like "MAT 1722 20 34439".
    
    Args:
        account_name: Full account name that may contain account number
        
    Returns:
        Normalized account number with spaces preserved or None if not found
    """
    if not account_name:
        return None
    
    # Pattern: 4 digits, space, 2 digits, space, 5 digits
    # Common Swedish account format
    pattern = r'\b(\d{4})\s+(\d{2})\s+(\d{5})\b'
    match = re.search(pattern, account_name)
    
    if match:
        # Return normalized format with spaces preserved for consistency
        return f"{match.group(1)} {match.group(2)} {match.group(3)}"
    
    # Also try without spaces for flexibility
    pattern_no_space = r'\b(\d{4})(\d{2})(\d{5})\b'
    match = re.search(pattern_no_space, account_name)
    
    if match:
        return f"{match.group(1)} {match.group(2)} {match.group(3)}"
    
    return None


class AccountManager:
    """Creates, manages, and clears accounts. Supports manual categorization and AI training."""
    
    def __init__(self, yaml_dir: str = "yaml"):
        """Initialize the account manager."""
        self.yaml_dir = yaml_dir
        self.accounts_file = os.path.join(yaml_dir, "accounts.yaml")
        self.transactions_file = os.path.join(yaml_dir, "transactions.yaml")
        self.training_data_file = os.path.join(yaml_dir, "training_data.yaml")
        
        # Ensure yaml directory exists
        os.makedirs(yaml_dir, exist_ok=True)
    
    def _load_yaml(self, filepath: str) -> dict:
        """Load YAML file or return default structure."""
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                return data
        return {}
    
    def _save_yaml(self, filepath: str, data: dict) -> None:
        """Save data to YAML file."""
        # Convert numpy types to Python native types
        import numpy as np
        
        def convert_numpy(obj):
            """Recursively convert numpy types to Python types."""
            if isinstance(obj, dict):
                return {k: convert_numpy(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy(item) for item in obj]
            elif isinstance(obj, (np.integer, np.floating)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return obj
        
        clean_data = convert_numpy(data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(clean_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    def get_accounts(self) -> List[dict]:
        """Get all accounts."""
        data = self._load_yaml(self.accounts_file)
        return data.get('accounts', [])
    
    def get_account_by_name(self, name: str) -> Optional[dict]:
        """Get account by name."""
        accounts = self.get_accounts()
        for account in accounts:
            if account.get('name') == name:
                return account
        return None
    
    def get_account_by_number(self, account_number: str) -> Optional[dict]:
        """Get account by account number.
        
        Extracts account numbers from account names and matches them.
        This allows matching accounts like "MAT 1722 20 34439" via just "1722 20 34439".
        
        Args:
            account_number: Account number to search for (e.g., "1722 20 34439")
            
        Returns:
            Account dict if found, None otherwise
        """
        if not account_number:
            return None
        
        # Normalize the search number
        normalized_search = account_number.replace(' ', '').strip()
        
        accounts = self.get_accounts()
        for account in accounts:
            account_name = account.get('name', '')
            extracted_number = extract_account_number(account_name)
            
            if extracted_number:
                # Compare without spaces for flexibility
                normalized_extracted = extracted_number.replace(' ', '')
                if normalized_extracted == normalized_search:
                    return account
        
        return None
    
    def create_account(self, name: str, source_file: str, balance: float = 0.0, person: str = None) -> dict:
        """
        Create a new account from a source file.
        
        Args:
            name: Account name
            source_file: Path to the source CSV/Excel file
            balance: Initial balance
            person: Person/owner of the account (optional)
            
        Returns:
            Dictionary with account information
        """
        # Check if account already exists
        existing = self.get_account_by_name(name)
        if existing:
            return existing
        
        # Create new account
        account = {
            'name': name,
            'source_file': source_file,
            'created_at': datetime.now().strftime('%Y-%m-%d'),
            'balance': balance,
            'person': person or ''
        }
        
        # Load accounts and add new one
        data = self._load_yaml(self.accounts_file)
        if 'accounts' not in data:
            data['accounts'] = []
        data['accounts'].append(account)
        
        # Save
        self._save_yaml(self.accounts_file, data)
        return account
    
    def delete_account(self, name: str) -> bool:
        """
        Delete an account by name.
        
        Args:
            name: Account name to delete
            
        Returns:
            True if successful, False otherwise
        """
        data = self._load_yaml(self.accounts_file)
        if 'accounts' not in data:
            return False
        
        accounts = data['accounts']
        initial_count = len(accounts)
        data['accounts'] = [a for a in accounts if a.get('name') != name]
        
        if len(data['accounts']) < initial_count:
            self._save_yaml(self.accounts_file, data)
            return True
        return False
    
    def add_transactions(self, transactions: List[dict]) -> None:
        """
        Add transactions to the transactions file.
        
        Args:
            transactions: List of transaction dictionaries
        """
        data = self._load_yaml(self.transactions_file)
        if 'transactions' not in data:
            data['transactions'] = []
        
        # Add transactions with unique IDs
        for tx in transactions:
            if 'id' not in tx:
                tx['id'] = str(uuid.uuid4())
            data['transactions'].append(tx)
        
        self._save_yaml(self.transactions_file, data)
    
    def get_account_transactions(self, name: str) -> List[dict]:
        """
        Get all transactions for a specific account.
        
        Args:
            name: Account name
            
        Returns:
            List of transaction dictionaries
        """
        data = self._load_yaml(self.transactions_file)
        transactions = data.get('transactions', [])
        return [tx for tx in transactions if tx.get('account') == name]
    
    def get_all_transactions(self) -> List[dict]:
        """
        Get all transactions across all accounts.
        
        Returns:
            List of all transaction dictionaries
        """
        data = self._load_yaml(self.transactions_file)
        return data.get('transactions', [])
    
    def categorize_transaction(self, tx: dict, category: str, subcategory: str) -> dict:
        """
        Manually categorize a transaction.
        
        Args:
            tx: Transaction dictionary
            category: Main category
            subcategory: Subcategory
            
        Returns:
            Updated transaction dictionary
        """
        tx['category'] = category
        tx['subcategory'] = subcategory
        tx['categorized_manually'] = True
        return tx
    
    def train_ai_from_manual_input(self, tx: dict) -> None:
        """
        Train AI model from manual categorization.
        
        Args:
            tx: Transaction dictionary with manual categorization
        """
        if not tx.get('categorized_manually'):
            return
        
        # Add to training data
        data = self._load_yaml(self.training_data_file)
        if 'training_data' not in data:
            data['training_data'] = []
        
        training_entry = {
            'description': tx.get('description', ''),
            'category': tx.get('category', ''),
            'subcategory': tx.get('subcategory', ''),
            'manual': True
        }
        
        data['training_data'].append(training_entry)
        self._save_yaml(self.training_data_file, data)
    
    def update_account_balance(self, name: str, balance: float) -> None:
        """Update account balance."""
        data = self._load_yaml(self.accounts_file)
        if 'accounts' in data:
            for account in data['accounts']:
                if account.get('name') == name:
                    account['balance'] = balance
                    break
            self._save_yaml(self.accounts_file, data)
    
    def update_account(self, old_name: str, new_name: str = None, **kwargs) -> Optional[dict]:
        """Update account information.
        
        Args:
            old_name: Current account name
            new_name: New account name (optional)
            **kwargs: Additional fields to update (balance, source_file, person, etc.)
                     Common fields: person (owner name), balance (current balance)
            
        Returns:
            Updated account dictionary or None if not found
        """
        data = self._load_yaml(self.accounts_file)
        if 'accounts' not in data:
            return None
        
        for account in data['accounts']:
            if account.get('name') == old_name:
                # Update name if provided
                if new_name:
                    account['name'] = new_name
                
                # Update other fields
                for key, value in kwargs.items():
                    account[key] = value
                
                self._save_yaml(self.accounts_file, data)
                return account
        
        return None
    
    def save_transactions(self, data: dict) -> None:
        """
        Save transactions data to file.
        
        Args:
            data: Dictionary containing transactions
        """
        self._save_yaml(self.transactions_file, data)
