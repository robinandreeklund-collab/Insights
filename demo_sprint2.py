"""
Sprint 2 Demo Script
Demonstrates the complete CSV import and analysis flow.
"""

import os
import sys
from modules.core.import_bank_data import import_csv
from modules.core.account_manager import AccountManager
from modules.core.forecast_engine import get_forecast_summary, get_category_breakdown


def print_separator():
    """Print a visual separator."""
    print("\n" + "="*70 + "\n")


def demo_csv_import(csv_file="PERSONKONTO 880104-7591 - 2025-10-21 15.38.56.csv"):
    """Demonstrate CSV import functionality."""
    print("🔹 STEP 1: CSV IMPORT")
    print(f"Importing: {csv_file}")
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return None, None
    
    # Import CSV
    account_name, df = import_csv(csv_file)
    
    print(f"✅ Account Name: {account_name}")
    print(f"✅ Transactions Loaded: {len(df)}")
    print(f"✅ Latest Balance: {df['balance'].iloc[0]} SEK")
    
    print("\nSample Transactions:")
    print(df[['date', 'description', 'amount', 'balance']].head())
    
    return account_name, df


def demo_categorization(df):
    """Demonstrate transaction categorization."""
    print_separator()
    print("🔹 STEP 2: AUTOMATIC CATEGORIZATION")
    
    from modules.core.categorize_expenses import auto_categorize
    
    # Categorize
    df_categorized = auto_categorize(df)
    
    print("\nCategorized Transactions:")
    for idx, row in df_categorized.iterrows():
        print(f"  • {row['description'][:40]:40} → {row['category']:15} / {row['subcategory']}")
    
    return df_categorized


def demo_account_management(account_name, df):
    """Demonstrate account management."""
    print_separator()
    print("🔹 STEP 3: ACCOUNT MANAGEMENT")
    
    # Use temporary directory for demo
    import tempfile
    temp_dir = tempfile.mkdtemp()
    
    manager = AccountManager(yaml_dir=temp_dir)
    
    # Create account
    latest_balance = df['balance'].iloc[0]
    account = manager.create_account(account_name, "demo.csv", balance=latest_balance)
    
    print(f"✅ Account Created: {account['name']}")
    print(f"✅ Balance: {account['balance']} SEK")
    print(f"✅ Created At: {account['created_at']}")
    
    # Add transactions
    transactions = []
    for _, row in df.iterrows():
        tx = {
            'date': row['date'].strftime('%Y-%m-%d') if 'date' in row and pd.notna(row['date']) else '',
            'description': str(row.get('description', '')),
            'amount': float(row.get('amount', 0)),
            'balance': float(row.get('balance', 0)),
            'category': row.get('category', 'Övrigt'),
            'subcategory': row.get('subcategory', 'Okategoriserat'),
            'account': account_name,
            'currency': row.get('currency', 'SEK')
        }
        transactions.append(tx)
    
    manager.add_transactions(transactions)
    print(f"✅ {len(transactions)} transactions saved")
    
    return manager, temp_dir


def demo_forecast():
    """Demonstrate forecast functionality."""
    print_separator()
    print("🔹 STEP 4: BALANCE FORECAST")
    
    # Get forecast using actual data
    summary = get_forecast_summary(31.06, forecast_days=7)
    
    print(f"Current Balance: {summary['current_balance']} SEK")
    print(f"Forecast Period: {summary['forecast_days']} days")
    print(f"\nDaily Averages:")
    print(f"  • Income:   {summary['avg_daily_income']} SEK/day")
    print(f"  • Expenses: {summary['avg_daily_expenses']} SEK/day")
    print(f"  • Net:      {summary['avg_daily_net']} SEK/day")
    print(f"\nPredicted Final Balance: {summary['predicted_final_balance']} SEK")
    print(f"Expected Change: {summary['predicted_balance_change']:+.2f} SEK")
    
    if summary.get('warning'):
        print(f"\n⚠️  Warning: {summary['warning']}")
    
    print("\nForecast Timeline (first 5 days):")
    for day in summary['forecast'][:5]:
        print(f"  Day {day['day']:2}: {day['date']} - {day['predicted_balance']:8.2f} SEK")
    
    return summary


def demo_category_breakdown():
    """Demonstrate category breakdown."""
    print_separator()
    print("🔹 STEP 5: EXPENSE BREAKDOWN")
    
    breakdown = get_category_breakdown()
    
    if breakdown:
        print("\nExpenses by Category:")
        total = sum(breakdown.values())
        for category, amount in sorted(breakdown.items(), key=lambda x: x[1], reverse=True):
            percentage = (amount / total * 100) if total > 0 else 0
            print(f"  • {category:20} {amount:8.2f} SEK ({percentage:5.1f}%)")
        print(f"\n  Total Expenses: {total:.2f} SEK")
    else:
        print("No expense data available")
    
    return breakdown


def main():
    """Run complete demo."""
    print("\n" + "="*70)
    print(" "*20 + "SPRINT 2 DEMO - INSIGHTS")
    print("="*70)
    
    # Import pandas for date handling
    import pandas as pd
    globals()['pd'] = pd
    
    # Step 1: Import CSV
    account_name, df = demo_csv_import()
    if account_name is None:
        return
    
    # Step 2: Categorize
    df_categorized = demo_categorization(df)
    
    # Step 3: Account Management
    manager, temp_dir = demo_account_management(account_name, df_categorized)
    
    # Step 4: Forecast
    summary = demo_forecast()
    
    # Step 5: Category Breakdown
    breakdown = demo_category_breakdown()
    
    # Cleanup
    import shutil
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    
    print_separator()
    print("✅ DEMO COMPLETE!")
    print("\nKey Features Demonstrated:")
    print("  1. ✅ CSV import with automatic account name extraction")
    print("  2. ✅ Hybrid categorization (rules + AI/heuristics)")
    print("  3. ✅ Account and transaction management")
    print("  4. ✅ Balance forecasting based on historical data")
    print("  5. ✅ Category-based expense analysis")
    print("\nNext Steps:")
    print("  • Run 'python import_flow.py <YOUR_CSV>' to import your data")
    print("  • Run 'python dashboard/dashboard_ui.py' to start the dashboard")
    print("  • Run 'pytest tests/ -v' to run all tests")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
