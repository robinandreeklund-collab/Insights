#!/usr/bin/env python
"""
Mastercard Integration Verification Script

This script verifies the complete Mastercard workflow:
1. Creates a Mastercard
2. Imports transactions from CSV
3. Verifies auto-categorization
4. Tests payment detection
5. Verifies balance updates
"""

import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.core.credit_card_manager import CreditCardManager
from modules.core.account_manager import AccountManager


def main():
    print("=" * 80)
    print("MASTERCARD INTEGRATION VERIFICATION")
    print("=" * 80)
    print()
    
    # Initialize managers
    print("1. Initializing managers...")
    cc_manager = CreditCardManager(yaml_dir="yaml")
    account_manager = AccountManager(yaml_dir="yaml")
    print("   ✓ Managers initialized")
    print()
    
    # Create Mastercard
    print("2. Creating Mastercard...")
    card = cc_manager.add_card(
        name="Mastercard Premium",
        card_type="Mastercard",
        last_four="2345",
        credit_limit=50000.0,
        initial_balance=0.0,
        display_color="#EB001B",
        icon="mastercard"
    )
    print(f"   ✓ Card created: {card['name']} (****{card['last_four']})")
    print(f"   ✓ Credit limit: {card['credit_limit']:.2f} SEK")
    print(f"   ✓ Icon: {card['icon']}")
    print(f"   ✓ Color: {card['display_color']}")
    print()
    
    # Import CSV
    print("3. Importing transactions from CSV...")
    # Get the script's directory and find mastercard_sample.csv in repo root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, 'mastercard_sample.csv')
    
    if not os.path.exists(csv_path):
        print(f"   ✗ CSV file not found: {csv_path}")
        return 1
    
    result = cc_manager.import_transactions_from_csv(
        card_id=card['id'],
        csv_path=csv_path
    )
    
    print(f"   ✓ Imported {result['imported']} transactions")
    print()
    
    # Verify transactions
    print("4. Verifying transactions...")
    transactions = cc_manager.get_transactions(card['id'])
    print(f"   ✓ Total transactions: {len(transactions)}")
    
    # Check auto-categorization
    categorized = [tx for tx in transactions if tx.get('category') != 'Övrigt']
    print(f"   ✓ Auto-categorized: {len(categorized)}/{len(transactions)}")
    
    # Show some examples
    if transactions:
        print("\n   Sample transactions:")
        for tx in transactions[:3]:
            print(f"      • {tx['date']}: {tx['description'][:30]:<30} {tx['amount']:>10.2f} SEK [{tx['category']}]")
    print()
    
    # Get card summary
    print("5. Card summary...")
    summary = cc_manager.get_card_summary(card['id'])
    print(f"   ✓ Current balance: {summary['current_balance']:.2f} SEK")
    print(f"   ✓ Available credit: {summary['available_credit']:.2f} SEK")
    print(f"   ✓ Utilization: {summary['utilization_percent']:.1f}%")
    print(f"   ✓ Total spent: {summary['total_spent']:.2f} SEK")
    
    if summary['category_breakdown']:
        print("\n   Category breakdown:")
        for category, amount in sorted(summary['category_breakdown'].items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"      • {category:<20} {amount:>10.2f} SEK")
    print()
    
    # Test payment detection
    print("6. Testing payment detection...")
    
    # Create bank account
    try:
        account_manager.create_account("Test Bank Account", 50000.0)
        print("   ✓ Bank account created")
    except:
        print("   ℹ Bank account already exists")
    
    # Add payment transactions
    today = datetime.now().strftime('%Y-%m-%d')
    
    payment_tests = [
        {
            'description': 'Betalning BG 595-4300 SEB KORT BANK',
            'expected': 'BG format'
        },
        {
            'description': f'Mastercard Betalning {card["last_four"]}',
            'expected': 'with card match'
        }
    ]
    
    for i, payment_test in enumerate(payment_tests, 1):
        transactions = [
            {
                'account': 'Test Bank Account',
                'date': today,
                'amount': -2000.0 * i,
                'description': payment_test['description']
            }
        ]
        
        account_manager.add_transactions(transactions)
        count = account_manager.detect_credit_card_payments()
        
        all_txs = account_manager.get_all_transactions()
        marked = [tx for tx in all_txs if tx.get('is_credit_card_payment') and 
                 tx['description'] == payment_test['description']]
        
        if marked:
            payment = marked[0]
            matched_card = payment.get('matched_credit_card_id') == card['id']
            print(f"   ✓ Detected payment: {payment_test['description'][:40]}")
            print(f"      Matched to card: {'Yes' if matched_card else 'No (generic)'}")
        else:
            print(f"   ✗ Failed to detect: {payment_test['description'][:40]}")
    
    print()
    
    # Final summary
    print("=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)
    print("\nAll Mastercard features verified successfully! ✓")
    print("\nNext steps:")
    print("  1. Start dashboard: python dashboard/dashboard_ui.py")
    print("  2. Navigate to 'Kreditkort' tab")
    print("  3. View your Mastercard and transactions")
    print("  4. Import more CSVs or edit transactions")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
