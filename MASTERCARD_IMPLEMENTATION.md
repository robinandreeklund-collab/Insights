# Mastercard Implementation Guide

## Overview

This document describes the Mastercard implementation in the Insights system. Mastercard support follows the same architecture as Amex (PR #14) but with Mastercard-specific features including Swedish BG payment detection and Mastercard branding.

## Features

### 1. CSV Import for Mastercard
Import Mastercard transactions from CSV or Excel files with automatic categorization and balance tracking.

**Supported File Formats:**
- **CSV files** (.csv) - Standard text format
- **Excel files** (.xlsx) - **Automatic conversion and import**

**Multi-Cardholder Support:**
- **Automatically imports all cardholders** from the same statement
- Tracks which cardholder made each transaction (Kortmedlem column)
- Imports account-level fees (annual fee, extra card fee, etc.)
- Perfect for accounts with main card + supplementary cards

**Supported Data Formats:**

**Format 1: Swedish Mastercard Export (Actual)**
```csv
Datum,Bokfört,Specifikation,Ort,Valuta,Utl. belopp,Belopp
2025-10-21,2025-10-22,PIZZERIA & REST,HJO,SEK,0,130.0
2025-10-19,2025-10-20,MAXI ICA STORMARKNAD S,SKOVDE,SEK,0,544.75
2025-10-17,2025-10-20,ICA SUPERMARKET HJO,HJO,SEK,0,69.0
```

**Format 2: Generic CSV with Cardholder**
```csv
Datum,Beskrivning,Kortmedlem,Konto #,Belopp
10/15/2025,ICA SUPERMARKET MALMÖ,EXEMPEL ANVÄNDARE,-12345,"1250,50"
10/18/2025,SHELL BENSINSTATION,EXEMPEL ANVÄNDARE,-12345,"650,00"
```

**Key Features:**
- **Excel files** (.xlsx) automatically converted to CSV format
- **Excel parsing** handles Mastercard export structure with multiple sections:
  - "Totalt övriga händelser" (account fees, payments)
  - "Köp/uttag" sections for each cardholder
- **Multi-cardholder tracking** - imports all supplementary cards automatically
- **Format 1** (Actual): YYYY-MM-DD dates, decimal point, positive amounts = purchases
- **Format 2** (Generic): MM/DD/YYYY dates, comma decimal, positive amounts = purchases
- Both formats: Payments (negative amounts) automatically filtered
- Cardholder tracking (Kortmedlem)
- Location/City tracking (Ort)
- Account number tracking (Konto #)

### 2. Transaction History View
View all Mastercard transactions with:
- Automatic categorization using existing rules and AI
- Transaction editing (category, subcategory, description, amount)
- Per-cardholder breakdown (for supplementary cards)
- Category spending analysis
- Date filtering

### 3. Automatic Payment Matching

The system automatically detects and matches Mastercard payments from bank statements.

**Supported Payment Patterns:**
```
Mastercard Betalning 2345
Betalning BG 595-4300 SEB KORT BANK
MC Card payment
Master Card 2345
```

**How It Works:**
1. Monitors bank account transactions for credit card keywords
2. Matches payments to Mastercard by:
   - Card type keyword ("mastercard", "master card", "mc card")
   - Last 4 digits
   - Swedish payment patterns ("seb kort bank", "kort bank")
3. Automatically updates card balance
4. Labels transaction: "Inbetalning till kreditkort Mastercard Premium"

### 4. Mastercard Branding

**Icon Design:**
- Red and orange overlapping circles (Mastercard brand colors)
- Card color: #EB001B (Mastercard red)
- Icon automatically displays on card in dashboard

**Code:**
```python
card = cc_manager.add_card(
    name="Mastercard Premium",
    card_type="Mastercard",
    last_four="2345",
    credit_limit=50000.0,
    display_color="#EB001B",
    icon="mastercard"
)
```

### 5. Balance Management

**Key Principle:** Mastercard transactions do NOT affect bank account cash flow.

- Purchases increase card balance (money owed)
- Payments decrease card balance
- Card balance is separate from bank accounts
- Only payments appear in bank statements (as negative amounts)

**Example:**
```python
# Import Mastercard transactions
cc_manager.import_transactions_from_csv(
    card_id=card['id'],
    csv_path='mastercard_statement.csv'
)

# Card balance: 5,000 SEK (money owed)
# Bank balance: Unchanged

# Make payment from bank
account_manager.add_transactions([{
    'account': 'Bank Account',
    'date': '2025-10-25',
    'amount': -5000.0,
    'description': 'Mastercard Betalning'
}])

# Run payment detection
account_manager.detect_credit_card_payments()

# Card balance: 0 SEK (payment matched)
# Bank balance: -5,000 SEK (payment made)
```

## Usage Examples

### Creating a Mastercard

```python
from modules.core.credit_card_manager import CreditCardManager

manager = CreditCardManager()

# Create new Mastercard
card = manager.add_card(
    name="Mastercard Premium",
    card_type="Mastercard",
    last_four="2345",
    credit_limit=50000.0,
    initial_balance=0.0,  # Or previous balance if not importing from start
    display_color="#EB001B",
    icon="mastercard"
)
```

### Importing Transactions

```python
# Import from CSV
result = manager.import_transactions_from_csv(
    card_id=card['id'],
    csv_path='mastercard_sample.csv'
)

# Import from Excel (.xlsx) - NEW!
# Automatically converts Excel to CSV format
result = manager.import_transactions_from_csv(
    card_id=card['id'],
    csv_path='transactions-2025-10-21-to-2025-08-31.xlsx'
)

print(f"Imported {result['imported']} transactions")

# Manual transaction
manager.add_transaction(
    card_id=card['id'],
    date='2025-10-20',
    description='ICA Supermarket',
    amount=-1250.50,  # Negative = purchase
    category='Mat & Dryck',
    vendor='ICA'
)
```

### Viewing Card Summary

```python
summary = manager.get_card_summary(card['id'])

print(f"Card: {summary['name']}")
print(f"Balance: {summary['current_balance']} SEK")
print(f"Available: {summary['available_credit']} SEK")
print(f"Utilization: {summary['utilization_percent']:.1f}%")
print(f"Total spent: {summary['total_spent']} SEK")
print("\nCategory Breakdown:")
for category, amount in summary['category_breakdown'].items():
    print(f"  {category}: {amount:.2f} SEK")
```

### Editing Transactions

```python
# Update category
manager.update_transaction(
    card_id=card['id'],
    transaction_id='TX-abc123',
    category='Shopping',
    subcategory='Kläder'
)

# Delete transaction
manager.delete_transaction(
    card_id=card['id'],
    transaction_id='TX-abc123'
)
```

### Payment Detection

```python
from modules.core.account_manager import AccountManager

account_mgr = AccountManager()

# Run detection on bank transactions
count = account_mgr.detect_credit_card_payments()
print(f"Detected {count} credit card payments")

# Payments are automatically matched to cards
# Balance is automatically updated
```

## Dashboard UI

### Adding a Mastercard

1. Navigate to "Kreditkort" tab
2. Fill in form:
   - **Kortnamn:** Mastercard Premium
   - **Korttyp:** Select "Mastercard"
   - **Sista 4 siffror:** 2345
   - **Kreditgräns:** 50000
   - **Föregående saldo:** 0 (optional)
   - **Färg:** #EB001B (auto-selected)
3. Click "Lägg till kort"

### Importing CSV

1. In "Kreditkort" tab, scroll to "Importera transaktioner"
2. Select your Mastercard from dropdown
3. Upload CSV file
4. Transactions are automatically imported and categorized

### Viewing Transactions

1. Click on Mastercard card in overview
2. View transaction list with categories
3. Select transaction to edit category
4. Click "Spara" or "Spara och träna AI"

### Managing Payments

Payments from bank accounts are automatically detected and matched. View them in:
- Transaction history (labeled "Inbetalning till kreditkort")
- Card payment history
- Balance updates reflect payments immediately

## Testing

### Running Mastercard Tests

```bash
# Run all Mastercard tests
python -m pytest tests/test_mastercard_workflow.py -v

# Run specific test
python -m pytest tests/test_mastercard_workflow.py::TestMastercardWorkflow::test_mastercard_csv_import -v
```

### Test Coverage

The test suite covers:
1. ✅ CSV import with Swedish format
2. ✅ Auto-categorization of transactions
3. ✅ Payment detection with BG format
4. ✅ Payment matching to specific card
5. ✅ Balance updates after payment
6. ✅ Transaction editing
7. ✅ Summary with category breakdown
8. ✅ Icon and branding
9. ✅ Cash flow separation

## Migration from Other Cards

If you have existing credit card data:

### From Manual Entry
1. Create Mastercard with current balance as `initial_balance`
2. Import future transactions via CSV
3. Payments are matched automatically going forward

### From Other Systems
1. Export transactions to CSV in supported format
2. Create Mastercard with `initial_balance=0`
3. Import CSV
4. Balance will reflect imported transactions

## Technical Architecture

### Data Model

**Card:**
```yaml
id: CARD-abc12345
name: Mastercard Premium
card_type: Mastercard
last_four: "2345"
credit_limit: 50000.0
current_balance: 5000.0
available_credit: 45000.0
display_color: "#EB001B"
icon: mastercard
transactions: []
payment_history: []
status: active
created_at: "2025-10-23 10:00:00"
```

**Transaction:**
```yaml
id: TX-xyz67890
date: "2025-10-15"
description: ICA SUPERMARKET MALMÖ
vendor: ICA SUPERMARKET MALMÖ
amount: -1250.50  # Negative = purchase
category: Mat & Dryck
subcategory: Livsmedel
card_member: EXEMPEL ANVÄNDARE
account_number: "-12345"
created_at: "2025-10-23 10:00:00"
```

### Payment Detection Keywords

```python
keywords = [
    'amex', 'american express', 'american exp', 'am exp',
    'mastercard', 'master card', 'mc card',
    'visa',
    'kreditkort', 'credit card',
    'kortbetalning', 'card payment',
    'cc payment', 'cc-payment',
    'seb kort bank',  # Swedish BG format
    'kort bank'       # Generic Swedish format
]
```

### CSV Parsing

```python
# Auto-detects Swedish format
# Converts dates: MM/DD/YYYY → YYYY-MM-DD
# Converts amounts: "1250,50" → 1250.50
# Filters out payments (negative amounts)
# Negates purchases: 1250.50 → -1250.50 (for internal storage)
```

## Best Practices

### 1. Initial Setup
- Set `initial_balance` to current amount owed when creating card
- Import only new transactions going forward
- Avoid importing historical transactions that are already paid

### 2. CSV Import
- Export monthly statements from Mastercard
- Import as soon as statement is available
- Don't re-import same period (duplicate detection is disabled)

### 3. Payment Matching
- Use consistent payment descriptions in bank
- Include "Mastercard" or last 4 digits in description
- Run `detect_credit_card_payments()` after importing bank statements

### 4. Categorization
- Review auto-categorization periodically
- Edit categories and train AI for better accuracy
- Use consistent category names across all cards

### 5. Balance Management
- Verify balance after imports
- Check payment matching is working
- Review utilization percentage regularly

## Troubleshooting

### Issue: Payments Not Detected

**Solution:**
1. Check payment description contains keyword
2. Add "Mastercard" or last 4 digits to description
3. Run `detect_credit_card_payments()` manually
4. Check card status is 'active'

### Issue: Wrong Balance

**Solution:**
1. Check `initial_balance` was set correctly
2. Verify all transactions imported
3. Check payment matching history
4. Recalculate: balance = initial + sum(transactions)

### Issue: Duplicate Transactions

**Solution:**
- Duplicate detection is disabled to allow legitimate duplicates
- Delete manually if needed
- Don't re-import same CSV file

### Issue: Wrong Categories

**Solution:**
1. Edit transaction category
2. Click "Spara och träna AI"
3. Future similar transactions will use learned category
4. Review training data in `yaml/training_data.yaml`

## Security Notes

- Card data stored in `yaml/credit_cards.yaml`
- Full card numbers are NEVER stored (only last 4 digits)
- Transactions stored locally only
- No external API calls for credit card data
- Clear sensitive data with `clear_data_on_exit()`

## Future Enhancements

Potential improvements:
1. **Automatic Statement Download:** Connect to Mastercard API
2. **Fraud Detection:** Unusual spending patterns
3. **Rewards Tracking:** Points/cashback per transaction
4. **Multi-Currency:** Support for foreign transactions
5. **Budget Alerts:** Notify when approaching limit
6. **Recurring Detection:** Identify subscriptions
7. **Statement Export:** Generate PDF statements

## Related Documentation

- [CREDIT_CARD_IMPLEMENTATION.md](CREDIT_CARD_IMPLEMENTATION.md) - General credit card system
- [SPRINT7_SUMMARY.md](SPRINT7_SUMMARY.md) - Internal transfers and payment matching
- [README.md](README.md) - Main documentation
- `tests/test_mastercard_workflow.py` - Test examples

## Support

For issues or questions:
1. Check test suite for usage examples
2. Review code comments in `modules/core/credit_card_manager.py`
3. Consult general credit card documentation
4. Open issue on GitHub

---

**Implementation Date:** October 23, 2025  
**Status:** Production Ready  
**Test Coverage:** 9/9 tests passing  
**Compatibility:** Works with PR #14 credit card system
