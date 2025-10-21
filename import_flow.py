"""Complete CSV import and categorization flow."""

import sys
import os
from typing import Tuple
import pandas as pd
import yaml as yaml_module

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.core.import_bank_data import import_csv
from modules.core.account_manager import AccountManager
from modules.core.categorize_expenses import auto_categorize


def clear_data_files(yaml_dir: str = "yaml") -> None:
    """
    Clear transactions and accounts YAML files for fresh import.
    
    Args:
        yaml_dir: Directory containing YAML files
    """
    transactions_file = os.path.join(yaml_dir, "transactions.yaml")
    accounts_file = os.path.join(yaml_dir, "accounts.yaml")
    
    # Reset transactions.yaml
    if os.path.exists(transactions_file):
        with open(transactions_file, 'w', encoding='utf-8') as f:
            yaml_module.dump({'transactions': []}, f, default_flow_style=False, allow_unicode=True)
        print(f"✓ Cleared {transactions_file}")
    
    # Reset accounts.yaml
    if os.path.exists(accounts_file):
        with open(accounts_file, 'w', encoding='utf-8') as f:
            yaml_module.dump({'accounts': []}, f, default_flow_style=False, allow_unicode=True)
        print(f"✓ Cleared {accounts_file}")


def import_and_process_csv(csv_path: str, yaml_dir: str = "yaml") -> Tuple[str, int]:
    """
    Complete import flow: import CSV, create account, categorize, and save.
    
    Args:
        csv_path: Path to CSV file
        yaml_dir: Directory for YAML files
        
    Returns:
        Tuple of (account_name, number_of_transactions)
    """
    print(f"Importing CSV file: {csv_path}")
    
    # Step 1: Import and normalize CSV
    account_name, df = import_csv(csv_path)
    print(f"✓ Extracted account name: {account_name}")
    print(f"✓ Loaded {len(df)} transactions")
    
    # Step 2: Create or get account
    manager = AccountManager(yaml_dir=yaml_dir)
    
    # Get the latest balance from the CSV
    latest_balance = df['balance'].iloc[0] if 'balance' in df.columns else 0.0
    
    account = manager.create_account(
        name=account_name,
        source_file=csv_path,
        balance=latest_balance
    )
    print(f"✓ Account created/updated: {account_name} (Balance: {latest_balance} SEK)")
    
    # Step 3: Auto-categorize transactions
    print("Categorizing transactions...")
    df = auto_categorize(df)
    print(f"✓ Transactions categorized")
    
    # Step 4: Convert to transaction format and save
    transactions = []
    for _, row in df.iterrows():
        transaction = {
            'date': row['date'].strftime('%Y-%m-%d') if pd.notna(row['date']) else '',
            'description': str(row.get('description', '')),
            'amount': float(row.get('amount', 0)),
            'balance': float(row.get('balance', 0)),
            'category': row.get('category', 'Övrigt'),
            'subcategory': row.get('subcategory', 'Okategoriserat'),
            'account': account_name,
            'currency': row.get('currency', 'SEK'),
            'sender': str(row.get('sender', '')),
            'receiver': str(row.get('receiver', '')),
            'name': str(row.get('name', ''))
        }
        transactions.append(transaction)
    
    manager.add_transactions(transactions)
    print(f"✓ {len(transactions)} transactions saved to {yaml_dir}/transactions.yaml")
    
    # Step 5: Update account balance
    manager.update_account_balance(account_name, latest_balance)
    print(f"✓ Account balance updated")
    
    return account_name, len(transactions)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Import and process bank CSV file')
    parser.add_argument('csv_file', help='Path to CSV file to import')
    parser.add_argument('--yaml-dir', default='yaml', help='Directory for YAML files (default: yaml)')
    parser.add_argument('--clear', action='store_true', 
                        help='Clear existing transactions and accounts before import')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.csv_file):
        print(f"Error: File not found: {args.csv_file}")
        sys.exit(1)
    
    try:
        # Clear data files if requested
        if args.clear:
            print("Clearing existing data files...")
            clear_data_files(args.yaml_dir)
            print()
        
        account_name, num_transactions = import_and_process_csv(args.csv_file, args.yaml_dir)
        print(f"\n✓ Import complete!")
        print(f"  Account: {account_name}")
        print(f"  Transactions: {num_transactions}")
    except Exception as e:
        print(f"Error during import: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
