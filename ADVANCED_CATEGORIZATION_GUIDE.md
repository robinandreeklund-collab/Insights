# Advanced Categorization System - User Guide

## Overview

The Advanced Categorization System in Insights provides intelligent, automated transaction categorization using multiple strategies:

1. **AI Prediction** - Machine learning model trained on your data
2. **Semantic Matching** - Understanding meaning, not just keywords
3. **Rule-Based** - Traditional keyword matching
4. **Manual Override** - With automatic AI training

## Features

### 12 Main Categories

1. **Boende** - Housing and home-related expenses
2. **Transport** - All transportation costs
3. **Mat** - Food and dining
4. **Nöje** - Entertainment and leisure
5. **Hälsa** - Health and wellness
6. **Barn** - Children-related expenses
7. **Kläder** - Clothing and accessories
8. **Kommunikation** - Communication services
9. **Överföring** - Transfers between accounts
10. **Fakturabetalning** - Bill payments
11. **Inkomst** - Income and earnings
12. **Övrigt** - Miscellaneous

### 100+ Subcategories

Each main category has multiple subcategories for detailed tracking:
- **Transport**: Bränsle, Bilförsäkring, Parkering, Tåg, Flyg, Bilhyra, etc.
- **Mat**: Livsmedel, Restaurang, Takeaway, Kafé, etc.
- **Hälsa**: Medicin, Vård, Gym, Tandvård, etc.

## How to Use

### 1. Automatic Categorization

When you import transactions, they are automatically categorized using:

**Priority Order**:
1. **AI Prediction** (if confidence ≥ 65%)
2. **Semantic Matching** (if similarity ≥ 75%)
3. **Rule-Based** (keyword matching)
4. **Default** (Övrigt/Okänd) - flagged for review

### 2. Manual Categorization

**In Admin Dashboard**:

1. Navigate to **Admin** tab
2. Filter transactions (source, date, category, uncategorized)
3. Select transactions using checkboxes
4. Choose category and subcategory from dropdowns
5. Click **"Uppdatera valda"**

**Result**: 
- Transactions updated immediately
- Manual override registered
- AI training data updated
- Counter increments toward auto-retraining (10 overrides)

### 3. Bulk Training

**Train AI with Corrected Transactions**:

1. Select categorized transactions
2. Click **"Träna AI med valda"**
3. Training samples added to AI model

**When to Train**:
- After categorizing 10+ uncategorized transactions
- When you notice incorrect AI predictions
- After importing new CSV files

### 4. Automatic Retraining

The system automatically retrains the AI model when:
- **10 manual overrides** accumulated
- Triggered manually via **"Trigga omträning"** button

**What Happens**:
1. All training samples collected
2. ML model retrained with new data
3. Semantic vectors updated
4. Audit log created
5. Override counter resets to 0

**Result**: Better predictions for future transactions!

## Admin Dashboard Controls

### Statistics Display

**Real-Time Metrics**:
- Total transactions
- Uncategorized count
- Categories available
- AI training samples
- Manual overrides (X/10)

### Categorization Engine

**Engine Status**:
- Active categories: 12
- Confidence threshold: 0.65
- Semantic threshold: 0.75
- Manual overrides: X/10 (until auto-retrain)
- Rules loaded: 285
- Semantic vectors: 191

**Controls**:
- **Trigga omträning**: Manually trigger retraining pipeline
- **Återställ räknare**: Reset manual override counter to 0

### Filtering

**Available Filters**:
- **Källa** (Source): CSV filename
- **Konto** (Account): Account name
- **Kategori** (Category): Any of 12 categories
- **Status**: "Visa okategoriserade" checkbox
- **Datum från/till**: Date range with calendar picker

### Bulk Actions

**Update Categories**:
1. Select transactions (checkbox or "Välj alla")
2. Choose category (e.g., "Transport")
3. Choose subcategory (e.g., "Bränsle")
4. Click "Uppdatera valda"

**Train AI**:
1. Select correctly categorized transactions
2. Click "Träna AI med valda"
3. Samples added to training data

### Category Management

**Create New Category**:
1. Enter category name
2. Enter subcategories (one per line)
3. Click "Skapa"

**Merge Categories**:
1. Select "from" category (will be removed)
2. Select "to" category (will receive all transactions)
3. Click "Slå ihop kategorier"

**Delete Category**:
1. Select category to delete
2. Select category to move transactions to
3. Click "Ta bort kategori"

## Understanding Categorization Sources

Each transaction shows its categorization source:

- **ai**: AI model prediction (ML)
- **semantic**: Semantic similarity match
- **rule**: Keyword rule match
- **manual**: Manually categorized
- **default**: No match found (needs review)

## Confidence Scores

Transactions have confidence scores (0.0 - 1.0):

- **1.0**: Rule-based match (100% confident)
- **0.90+**: High confidence AI/semantic
- **0.65-0.89**: Medium confidence (acceptable)
- **< 0.65**: Low confidence (flagged for review)
- **0.0**: Default fallback (uncategorized)

## Best Practices

### 1. Regular Review

- Check **uncategorized transactions** weekly
- Review **low confidence** predictions (flagged)
- Verify **unusual amounts** or descriptions

### 2. Consistent Categorization

- Use same category/subcategory for similar transactions
- Example: All "ICA" → Mat/Livsmedel
- Example: All "Shell" → Transport/Bränsle

### 3. Train Incrementally

- Categorize 5-10 transactions at a time
- Train AI after each batch
- Let auto-retraining trigger naturally

### 4. Monitor Progress

- Check AI training samples count
- Watch manual override counter (X/10)
- Review retraining audit logs

### 5. Use Semantic Matching

- Install `sentence-transformers` for semantic features
- Matches based on meaning, not just keywords
- Example: "Köp av bensin" → Transport/Bränsle

## Common Workflows

### Workflow 1: Import and Categorize New CSV

```
1. Go to "Inmatning" tab
2. Upload CSV file (Nordea, Amex, Mastercard)
3. Import completes with automatic categorization
4. Go to "Admin" tab
5. Filter: "Visa okategoriserade" ✓
6. Review and categorize uncategorized transactions
7. Select all → Choose category → "Uppdatera valda"
8. Click "Träna AI med valda"
9. Auto-retraining triggers at 10 overrides
```

### Workflow 2: Review and Correct AI Predictions

```
1. Go to "Admin" tab
2. Filter by category (e.g., "Transport")
3. Sort by confidence score (look for low scores)
4. Review flagged transactions
5. Correct incorrect categorizations
6. Manual overrides registered automatically
7. AI learns from corrections
```

### Workflow 3: Clean Up Categories

```
1. Go to "Admin" → "Kategorihantering"
2. Tab: "Slå ihop kategorier"
3. Merge similar categories (e.g., "Food" + "Mat" → "Mat")
4. All transactions moved to consolidated category
5. Result: Cleaner category structure
```

### Workflow 4: Manual Retraining

```
1. Go to "Admin" → "Kategoriseringsmotor"
2. Check stats: "Manual overrides: 7/10"
3. Click "Trigga omträning"
4. Pipeline runs (may take 10-30 seconds)
5. Alert: "✓ Omträning slutförd! Prover: 45, Noggrannhet: 89%"
6. Counter reset to 0/10
7. Better predictions start immediately
```

## Troubleshooting

### Issue: Empty Category Dropdowns

**Solution**:
1. Refresh page (F5)
2. Check categorization engine status
3. Verify `categorization_engine.yaml` exists
4. Check console for errors

### Issue: Semantic Matching Not Working

**Solution**:
1. Install sentence-transformers: `pip install sentence-transformers`
2. Restart dashboard
3. Check "Semantic vektorer: 191" in engine status
4. First load downloads model (~90MB)

### Issue: Auto-Retraining Not Triggering

**Solution**:
1. Check counter: "Manual overrides: X/10"
2. Verify training data exists in `yaml/training_data.yaml`
3. Manually trigger: "Trigga omträning"
4. Check logs: `logs/retraining_audit.yaml`

### Issue: Poor Categorization Accuracy

**Solution**:
1. Add more training samples (aim for 10+ per category)
2. Review and correct existing categorizations
3. Use consistent category/subcategory choices
4. Trigger manual retraining
5. Check semantic matching is enabled

### Issue: Performance Slow with Many Transactions

**Solution**:
1. Use filters to reduce displayed transactions
2. Limit date range
3. Filter by specific source or category
4. Pagination automatically limits to 50 per page

## Advanced Features

### Audit Logging

All retraining events logged to `logs/retraining_audit.yaml`:
- Timestamp
- Model version
- Samples used
- Accuracy achieved
- Success/failure status

### Configuration Customization

Edit `yaml/categorization_engine.yaml` to adjust:
- Confidence thresholds
- Semantic similarity thresholds
- Retraining trigger count
- Category definitions

### API Integration

Use categorization engine programmatically:

```python
from modules.core.categorization_engine import CategorizationEngine

engine = CategorizationEngine()
result = engine.categorize(
    description="Tankning Shell",
    amount=-450.00,
    use_ai=True,
    use_semantic=True
)

print(result)
# {
#   'category': 'Transport',
#   'subcategory': 'Bränsle',
#   'confidence_score': 0.95,
#   'source': 'semantic',
#   'flagged': False
# }
```

## Tips for Best Results

1. **Start Small**: Categorize 20-30 transactions manually first
2. **Be Consistent**: Always use same categories for same merchants
3. **Review Regularly**: Weekly checks prevent accumulation
4. **Trust the AI**: After 50+ training samples, AI is usually accurate
5. **Use Semantic**: Install sentence-transformers for 20%+ better accuracy
6. **Monitor Progress**: Watch training samples and accuracy metrics
7. **Clean Categories**: Merge duplicates, delete unused ones
8. **Export Backups**: Regularly backup `yaml/` directory

## Support

For issues or questions:
1. Check this guide first
2. Review `ADMIN_DASHBOARD_GUIDE.md`
3. Check `SECURITY_SUMMARY_ADMIN_DASHBOARD.md`
4. Contact system administrator

## Version Information

- **System**: Insights Advanced Categorization
- **Version**: 1.0 (Sprint 9)
- **Categories**: 12 main, 100+ subcategories
- **Keywords**: 285 rules
- **Semantic Examples**: 191 phrases
- **ML Models**: MultinomialNB + TF-IDF
- **Semantic Engine**: SentenceTransformer (all-MiniLM-L6-v2)
