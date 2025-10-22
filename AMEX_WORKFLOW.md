# Amex Workflow Documentation

## Overview

The Amex workflow in Insights allows you to manage American Express credit card bills with detailed line item tracking. This feature enables you to:

1. **Track cash flow accurately**: The bill total affects your cash flow forecast
2. **Analyze spending patterns**: Line items provide detailed categorization for analysis
3. **Avoid double-counting**: Line items are historical records that don't affect cash balance
4. **Train AI models**: Use line items to improve automatic categorization

## Key Concepts

### Bills vs. Line Items

- **Bill**: Represents the total amount due to Amex, affects cash flow forecast
- **Line Items**: Individual purchases on the card, used for analysis only

### Historical Records

Line items are marked as `is_historical_record: true` and `affects_cash: false`, meaning:
- They appear in category analysis and monthly summaries
- They can be used for AI training
- They do NOT affect your cash balance (to avoid double-counting)

The bill total is what affects your cash flow, not the individual line items.

## Workflow Steps

### 1. Create an Amex Bill Manually

When you receive your Amex bill:

1. Go to the **Fakturor** (Bills) tab
2. Fill in the bill details:
   - **Namn**: "American Express" (or your preferred name)
   - **Belopp**: Total amount due (e.g., 5234.50 SEK)
   - **Förfallodatum**: Due date from your statement
   - **Kategori/Underkategori**: "Övrigt" / "Kreditkort" (or as preferred)
   - **Konto**: The bank account you'll pay from
3. **Check the box** "Detta är en Amex-faktura"
4. Click **Lägg till faktura**

This bill will now appear in your cash flow forecast.

### 2. Import Line Items from Amex CSV

After creating the bill, import the detailed transaction history:

1. Download your Amex CSV from the Amex website
2. In the dashboard, go to **Importera Amex CSV med raduppgifter** section
3. Drag and drop (or click to select) your Amex CSV file
4. The system will:
   - Parse the CSV automatically
   - Detect it's an Amex file
   - Look for a matching bill (by amount, date, and account)
   - Show you a preview with match confidence

### 3. Review and Confirm Linkage

A preview modal will appear showing:

- **File details**: Number of line items, total amount, date range
- **Matched bill**: If found, shows bill name, amount, due date, and match confidence
- **Sample items**: Preview of the first few line items with auto-categorization

Review the information and:
- Click **Bekräfta och importera** to proceed
- Click **Avbryt** to cancel

### 4. View and Edit Line Items

After import:

1. Go to **Amex-fakturor med raduppgifter** section
2. Select your bill from the dropdown
3. View the bill summary and all line items in a table
4. Edit categories if needed:
   - Click on a line item
   - Update vendor, category, subcategory, or other fields
   - Save changes

### 5. Train AI with Line Items

Use line items to improve automatic categorization:

1. In the line items table, select rows you want to use for training
2. Click **Träna AI med valda rader**
3. The selected items are added to `training_data.yaml`
4. Future transactions will be categorized more accurately

### 6. Bank Payment Matching

When the bank payment transaction is imported:

1. Import your bank CSV as usual
2. The bill matcher will detect the payment
3. The bill is marked as "paid"
4. Your cash balance is updated (once)
5. Line items remain as historical records for analysis

## CSV Format

### Amex CSV Format

The system detects Amex CSV files by looking for these columns:

```csv
Date,Description,Card Member,Account #,Amount
2025-10-05,ICA SUPERMARKET,JOHN DOE,*****1234,856.50
2025-10-08,SHELL PETROL STATION,JOHN DOE,*****1234,650.00
```

### Auto-Categorization

Line items are automatically categorized based on vendor keywords:

| Vendor Contains | Category | Subcategory |
|----------------|----------|-------------|
| ICA, Willys, Coop, Hemköp, Lidl | Mat & Dryck | Matinköp |
| Shell, Ingo, Preem, Circle K, OKQ8 | Transport | Drivmedel |
| Netflix, Spotify, HBO, Disney+ | Nöje | Streaming |
| Stadium, Intersport, XXL | Shopping | Sport |
| Restaurant, Café, Pizza, Burger | Mat & Dryck | Restaurang |

You can always edit these categorizations after import.

## Example Workflow

### Complete Example

```
1. Receive Amex bill: 5,234.50 SEK due 2025-11-15
2. Create bill in dashboard:
   - Name: American Express
   - Amount: 5234.50
   - Due date: 2025-11-15
   - Account: PERSONKONTO 1722 20 34439
   - ✓ Check "Detta är en Amex-faktura"
   
3. Download Amex CSV from Amex website
4. Upload CSV in dashboard
5. Review preview:
   - 5 line items found
   - Total: 5,234.50 SEK
   - Match confidence: 100%
   - Matched to "American Express" bill
   
6. Confirm import
7. View line items:
   - 2025-10-05 | ICA Supermarket | 856.50 | Mat & Dryck
   - 2025-10-08 | Shell | 650.00 | Transport
   - 2025-10-12 | Netflix | 119.00 | Nöje
   - 2025-10-15 | Willys | 1,234.00 | Mat & Dryck
   - 2025-10-18 | Stadium | 2,375.00 | Shopping
   
8. Select all 5 items and click "Träna AI"
9. Import bank CSV on 2025-11-14
10. Bill is matched and marked as paid
11. Cash balance decreases by 5,234.50 (once)
12. Line items remain for analysis
```

## Data Structure

### Bill with Line Items (YAML)

```yaml
bills:
  - id: BILL-0005
    name: American Express
    amount: 5234.50
    due_date: '2025-11-15'
    description: 'Amex bill - scheduled payment'
    category: 'Övrigt'
    subcategory: 'Kreditkort'
    account: '1722 20 34439'
    status: 'pending'
    is_amex_bill: true
    line_items:
      - id: 'LINE-0001'
        date: '2025-10-05'
        vendor: 'ICA Supermarket'
        description: 'Groceries'
        amount: 856.50
        category: 'Mat & Dryck'
        subcategory: 'Matinköp'
        is_historical_record: true
        affects_cash: false
      # ... more line items
```

### Training Data (YAML)

```yaml
training_data:
  - description: 'ICA Supermarket'
    category: 'Mat & Dryck'
    subcategory: 'Matinköp'
    manual: true
    source: 'amex_line_item'
    added_at: '2025-10-22 15:05:00'
```

## Cash Flow Impact

### Without Amex Workflow

```
Transaction: -5,234.50 SEK (Amex payment)
Cash impact: -5,234.50 SEK ✓
Category analysis: Only sees "Amex payment" in one category
```

### With Amex Workflow

```
Bill: -5,234.50 SEK (affects cash flow forecast)
Line items: 5 items (affect category analysis, NOT cash)
Bank payment: -5,234.50 SEK (affects cash balance once)

Total cash impact: -5,234.50 SEK (correct, no double-counting)
Category analysis: Shows detailed breakdown across multiple categories
```

## Migration Notes

### For Existing Users

If you already have Amex payments in your system:

1. **Old Amex payments**: These remain as regular transactions
2. **New approach**: Create bills for future Amex statements
3. **No data loss**: Your historical data is preserved
4. **Gradual adoption**: Start using the workflow for your next statement

### Backward Compatibility

- Bills without `line_items` continue to work normally
- Bills without `is_amex_bill` flag are treated as regular bills
- Existing bill management features are unchanged

## Best Practices

1. **Create bill first**: Always create the Amex bill before importing the CSV
2. **Match amounts**: Ensure the bill amount matches your Amex statement total
3. **Review preview**: Check the match confidence before confirming
4. **Edit categories**: Review and adjust auto-categorizations as needed
5. **Train AI regularly**: Use "Train with AI" to improve future categorization
6. **One bill per statement**: Create a separate bill for each statement period

## Troubleshooting

### "Ingen matchad faktura hittad"

**Problem**: CSV upload shows no matching bill found

**Solutions**:
1. Verify you created an Amex bill with the checkbox checked
2. Check that the bill amount is close to the CSV total (within 10%)
3. Ensure the bill due date is reasonably close to the CSV transaction dates
4. Create a new Amex bill if needed

### Line Items Not Showing

**Problem**: After import, line items table is empty

**Solutions**:
1. Refresh the page
2. Select the correct bill from the dropdown
3. Check that the import confirmation was successful
4. Verify the CSV format is correct

### Wrong Categories

**Problem**: Line items have incorrect categories

**Solutions**:
1. Edit individual line items to correct categories
2. Use the corrected items for AI training
3. The AI will learn and improve future categorizations

## API Reference

### BillManager Methods

```python
from modules.core.bill_manager import BillManager

manager = BillManager()

# Create Amex bill
bill = manager.add_bill(
    name='American Express',
    amount=5234.50,
    due_date='2025-11-15',
    account='1722 20 34439',
    is_amex_bill=True
)

# Import line items from CSV
line_items = [
    {
        'date': '2025-10-05',
        'vendor': 'ICA',
        'description': 'Groceries',
        'amount': 856.50,
        'category': 'Mat & Dryck',
        'subcategory': 'Matinköp'
    }
]
manager.import_line_items_from_csv(bill['id'], line_items)

# Get line items
items = manager.get_line_items(bill['id'])

# Get all line items across bills
all_items = manager.get_all_line_items(
    category='Mat & Dryck',
    start_date='2025-10-01',
    end_date='2025-10-31'
)
```

### AmexParser Methods

```python
from modules.core.amex_parser import AmexParser
from modules.core.bill_manager import BillManager

bill_manager = BillManager()
parser = AmexParser(bill_manager=bill_manager)

# Parse Amex CSV
line_items, metadata = parser.parse_amex_csv('amex_statement.csv')

# Find matching bill
matched_bill = parser.find_matching_bill(metadata)

# Create preview
preview = parser.create_linkage_preview(line_items, metadata, matched_bill)
```

### AITrainer Methods

```python
from modules.core.ai_trainer import AITrainer

trainer = AITrainer()

# Add line items for training
line_items = [
    {
        'vendor': 'ICA',
        'category': 'Mat & Dryck',
        'subcategory': 'Matinköp'
    }
]
added_count = trainer.add_training_samples_batch(line_items)
```

## Future Enhancements

Planned features for future versions:

1. **Pseudo-account view**: View all Amex line items as a virtual account
2. **Recurring detection**: Identify recurring Amex charges
3. **Budget tracking**: Track spending against category budgets using line items
4. **Multi-card support**: Handle multiple credit cards
5. **Export reports**: Generate spending reports from line items
6. **Automatic categorization**: Pre-train models with common Amex vendors

## Support

For questions or issues with the Amex workflow:

1. Check this documentation
2. Review the example Amex CSV file (`amex_sample.csv`)
3. Check the example bills file (`yaml/bills_example.yaml`)
4. Open an issue on GitHub with:
   - Steps to reproduce
   - Expected vs. actual behavior
   - Sample CSV (remove sensitive data)
