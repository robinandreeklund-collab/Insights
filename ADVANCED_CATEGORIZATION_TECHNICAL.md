# Advanced Categorization System - Technical Implementation

## Architecture Overview

The Advanced Categorization System consists of four main components working together to provide intelligent transaction categorization.

```
┌─────────────────────────────────────────────────────────┐
│                   Admin Dashboard UI                     │
│         (Dash callbacks, filters, bulk actions)          │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│            Categorization Engine (Orchestrator)          │
│  - Prioritization logic (AI → Semantic → Rules)         │
│  - Manual override tracking (auto-retrain trigger)       │
│  - Statistics and monitoring                             │
└─┬──────────────┬──────────────┬─────────────────────────┘
  │              │              │
  │              │              │
┌─▼─────────┐  ┌─▼─────────┐  ┌─▼──────────────┐
│ ML Model  │  │ Semantic  │  │ Rule-Based     │
│ (MultNB)  │  │ Matcher   │  │ (Keywords)     │
│ TF-IDF    │  │ SBERT     │  │ 285 rules      │
└───────────┘  └───────────┘  └────────────────┘
       │              │              │
       └──────────────┼──────────────┘
                      │
┌─────────────────────▼─────────────────────────┐
│          Retraining Pipeline                   │
│  - Data preprocessing                          │
│  - Model training (auto-trigger @ 10 overrides)│
│  - Evaluation and audit logging                │
└────────────────────────────────────────────────┘
                      │
┌─────────────────────▼─────────────────────────┐
│              YAML Database                     │
│  - transactions.yaml (transaction data)        │
│  - training_data.yaml (AI training samples)    │
│  - categorization_engine.yaml (config)         │
│  - categorization_rules.yaml (keywords)        │
│  - semantic_vectors.yaml (example phrases)     │
└────────────────────────────────────────────────┘
```

## Core Components

### 1. Categorization Engine

**File**: `modules/core/categorization_engine.py`

**Purpose**: Orchestrates all categorization strategies with priority-based fallback.

**Key Methods**:

```python
class CategorizationEngine:
    def __init__(config_path: str)
        # Initialize engine with config, rules, and semantic vectors
        
    def categorize(description, amount, merchant, account_type, 
                   use_ai=True, use_semantic=True) -> Dict
        # Main categorization method
        # Returns: {category, subcategory, confidence_score, source, flagged}
        
    def register_manual_override(transaction_id, category, 
                                 subcategory, description, train_ai=True)
        # Track manual overrides and trigger retraining at threshold
        
    def get_categories() -> List[str]
        # Get all available categories (12)
        
    def get_subcategories(category: str) -> List[str]
        # Get subcategories for a specific category
        
    def get_stats() -> Dict
        # Get engine statistics
```

**Categorization Priority**:
1. AI Prediction (if confidence ≥ 0.65)
2. Semantic Matching (if similarity ≥ 0.75)
3. Rule-Based Matching
4. Default Fallback (flagged)

**Configuration**: `yaml/categorization_engine.yaml`
- 12 categories with subcategories
- Confidence/semantic thresholds
- Retraining trigger (10 overrides)
- Input/output fields definition

### 2. Semantic Matcher

**File**: `modules/core/semantic_matcher.py`

**Purpose**: Semantic similarity matching using SentenceTransformer embeddings.

**Key Methods**:

```python
class SemanticMatcher:
    def __init__(config_path: str)
        # Initialize with SentenceTransformer model
        # Pre-compute embeddings for all category examples
        
    def match(text: str) -> Optional[Dict]
        # Find best semantic match
        # Returns: {category, subcategory, similarity_score, best_example}
        
    def is_available() -> bool
        # Check if semantic matching available
        
    def _compute_example_embeddings()
        # Pre-compute embeddings for 191 category examples
        
    def _cosine_similarity(vec1, vec2_matrix)
        # Compute cosine similarity between vectors
```

**Model**: `all-MiniLM-L6-v2` (SentenceTransformer)
- Fast inference (~10ms per sentence)
- Good Swedish language support
- ~90MB model size

**Configuration**: `yaml/semantic_matcher.yaml`
- Similarity threshold: 0.75
- Model selection
- Fallback behavior

**Semantic Vectors**: `yaml/semantic_vectors.yaml`
- 191 example phrases across all categories
- Organized by category/subcategory
- Pre-computed embeddings cached in memory

### 3. Retraining Pipeline

**File**: `modules/core/retraining_pipeline.py`

**Purpose**: Automatic ML model retraining when threshold reached.

**Key Methods**:

```python
class RetrainingPipeline:
    def __init__(config_path: str)
        # Initialize pipeline configuration
        
    def should_retrain() -> bool
        # Check if retraining should be triggered
        
    def run() -> Dict
        # Execute complete retraining pipeline
        # Returns: {success, timestamp, model_type, samples_used, 
        #          accuracy, message}
        
    def _log_audit(result: Dict)
        # Log retraining event to audit file
        
    def get_stats() -> Dict
        # Get pipeline statistics
```

**Pipeline Steps**:
1. Load training data from `yaml/training_data.yaml`
2. Validate minimum data requirements (4+ samples)
3. Train ML model using AITrainer
4. Evaluate model performance
5. Log audit information
6. Update deployment

**Configuration**: `yaml/retraining_pipeline.yaml`
- Trigger threshold: 10 overrides
- Model type: LogisticRegression
- Validation split: 0.2
- Evaluation metrics

**Audit Log**: `logs/retraining_audit.yaml`
- Timestamp of each retraining
- Samples used
- Accuracy achieved
- Success/failure status

### 4. Rule-Based Categorization

**File**: `yaml/categorization_rules.yaml`

**Purpose**: 285 keyword rules for exact matching.

**Structure**:
```yaml
categorization_rules:
  Boende:
    Hyra:
      - "hyra"
      - "hyresavi"
      - "bostadsbolag"
    El:
      - "vattenfall"
      - "eon"
      - "elräkning"
  Transport:
    Bränsle:
      - "shell"
      - "circle k"
      - "tankning"
```

**Matching**:
- Case-insensitive substring matching
- First match wins
- O(n*m) complexity (n=rules, m=description length)
- Very fast (~1ms for 285 rules)

## Integration Points

### Admin Dashboard UI

**File**: `dashboard/dashboard_ui.py`

**New UI Components**:

1. **Categorization Engine Section** (lines 1950-1979)
   - Engine status display
   - Strategy toggles
   - Manual retraining trigger
   - Override counter reset

2. **Enhanced Category Dropdowns** (lines 6217-6241)
   - Populated from categorization engine (12 categories)
   - Dynamic subcategories based on selection
   - Fallback to legacy category manager

3. **Bulk Action Enhancements** (lines 6367-6427)
   - Manual override registration with engine
   - Auto-trigger retraining at threshold
   - Training sample addition

**New Callbacks**:

1. `update_engine_info()` - Display engine status (10s refresh)
2. `handle_engine_actions()` - Handle retraining/reset actions
3. Enhanced `populate_admin_dropdowns()` - Use engine categories
4. Enhanced `update_admin_bulk_subcategories()` - Dynamic subcategories
5. Enhanced `handle_bulk_actions()` - Register manual overrides

### categorize_expenses.py

**File**: `modules/core/categorize_expenses.py`

**Enhanced**: `auto_categorize()` function

**New Parameters**:
- `use_engine=True` - Use advanced categorization engine

**Behavior**:
1. Try categorization engine first (if available)
2. Fallback to legacy method if engine unavailable
3. Add new columns: `confidence_score`, `categorization_source`

**Integration**:
```python
from modules.core.categorization_engine import CategorizationEngine

engine = CategorizationEngine()
for transaction in transactions:
    result = engine.categorize(
        description=transaction['description'],
        amount=transaction['amount'],
        merchant=transaction.get('merchant'),
        account_type=transaction.get('account_type'),
        use_ai=True,
        use_semantic=True
    )
    # Apply result to transaction
```

## Data Flow

### Import and Auto-Categorization

```
CSV Import
    ↓
Read transactions
    ↓
For each transaction:
    ↓
categorize_expenses.auto_categorize()
    ↓
CategorizationEngine.categorize()
    ↓
1. Try AI Prediction (ML Model)
   ├─ confidence >= 0.65? → Use it
   └─ else: continue
    ↓
2. Try Semantic Matching (SBERT)
   ├─ similarity >= 0.75? → Use it
   └─ else: continue
    ↓
3. Try Rule-Based (Keywords)
   ├─ match found? → Use it
   └─ else: continue
    ↓
4. Default Fallback
   └─ Övrigt/Okänd (flagged=True)
    ↓
Return {category, subcategory, confidence, source, flagged}
    ↓
Update transaction
    ↓
Save to transactions.yaml
```

### Manual Override and Retraining

```
User selects transactions in Admin Dashboard
    ↓
User chooses category/subcategory
    ↓
Clicks "Uppdatera valda"
    ↓
admin_dashboard.bulk_update_categories()
    ↓
For each transaction:
    ↓
  Update category in transactions.yaml
    ↓
  engine.register_manual_override()
      ↓
    Increment counter (X/10)
      ↓
    Add to training_data.yaml
      ↓
    Counter == 10?
      ├─ YES: Trigger RetrainingPipeline.run()
      │   ↓
      │ Load training_data.yaml
      │   ↓
      │ Train ML model
      │   ↓
      │ Save model to yaml/ml_model.pkl
      │   ↓
      │ Log audit to logs/retraining_audit.yaml
      │   ↓
      │ Reset counter to 0
      │   ↓
      │ Show success alert
      │
      └─ NO: Continue
    ↓
Return success message
```

## Performance Characteristics

### Categorization Speed

| Method | Time per Transaction | Throughput |
|--------|---------------------|------------|
| Rule-Based | ~1ms | 1000/sec |
| ML Model | ~5ms | 200/sec |
| Semantic | ~10ms | 100/sec |
| Combined | ~15ms | 65/sec |

### Memory Usage

| Component | Memory |
|-----------|--------|
| Categorization Engine | ~10MB |
| Semantic Matcher (with model) | ~150MB |
| ML Model | ~5MB |
| Rules Cache | ~1MB |
| Total | ~166MB |

### Scalability

- **1,000 transactions**: <15 seconds
- **10,000 transactions**: ~2-3 minutes
- **100,000 transactions**: ~20-30 minutes

**Optimization**:
- Batch processing (50 transactions at a time)
- Lazy loading of semantic model
- Cached embeddings for common phrases
- Parallel processing (future enhancement)

## Configuration Files

### categorization_engine.yaml

**Purpose**: Main engine configuration

**Key Settings**:
- `confidence_threshold.minimum`: 0.65
- `semantic_matching.similarity_threshold`: 0.75
- `strategy.retrain_trigger`: 10
- `categories`: 12 categories with subcategories

### categorization_rules.yaml

**Purpose**: Keyword rules

**Format**: YAML with category → subcategory → keywords list
**Size**: 5,620 bytes
**Keywords**: 285 rules across 12 categories

### semantic_vectors.yaml

**Purpose**: Example phrases for semantic matching

**Format**: YAML with category → subcategory → example list
**Size**: 5,087 bytes
**Examples**: 191 phrases across all categories

### semantic_matcher.yaml

**Purpose**: Semantic matcher configuration

**Key Settings**:
- `model`: "all-MiniLM-L6-v2"
- `similarity_threshold`: 0.75
- `fallback`: Use rule-based if below threshold

### retraining_pipeline.yaml

**Purpose**: Retraining pipeline configuration

**Key Settings**:
- `trigger.threshold`: 10
- `model_training.model_type`: "LogisticRegression"
- `evaluation.validation_split`: 0.2
- `deployment.save_model_to`: "models/categorization_model.pkl"

## Dependencies

### Required

- Python 3.10+
- pandas>=2.0.0
- numpy>=1.24.0
- pyyaml>=6.0
- scikit-learn>=1.3.0
- dash>=2.14.0

### Optional (Enhanced Features)

- sentence-transformers>=2.2.0 (for semantic matching)

### Installation

```bash
# Basic installation
pip install -r requirements.txt

# With semantic matching
pip install sentence-transformers
```

## Error Handling

### Graceful Degradation

1. **Semantic Matcher Not Available**
   - Falls back to AI → Rules → Default
   - Logs warning, continues operation

2. **ML Model Not Trained**
   - Skips AI prediction
   - Uses Semantic → Rules → Default

3. **Configuration File Missing**
   - Uses default values
   - Logs warning
   - System remains functional

4. **Training Data Insufficient**
   - Retraining skipped
   - Returns informative error message
   - No data loss

### Error Logging

All errors logged to console with:
- Component name
- Error type
- Stack trace (debug mode)
- Suggested resolution

## Testing

### Test Coverage

- **Unit Tests**: 70+ tests across 5 files
- **Integration Tests**: End-to-end categorization flow
- **Performance Tests**: Benchmarking with large datasets

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific component
pytest tests/test_categorization_engine.py -v

# With coverage
pytest tests/ --cov=modules --cov-report=html
```

## Deployment

### Production Checklist

- [ ] Install all dependencies
- [ ] Configure categorization engine (thresholds)
- [ ] Load initial rules and semantic vectors
- [ ] Train initial ML model (50+ samples)
- [ ] Test semantic matching
- [ ] Enable audit logging
- [ ] Configure backup strategy
- [ ] Monitor performance metrics
- [ ] Set up admin access control

### Backup Strategy

**Critical Files**:
- `yaml/transactions.yaml` - Transaction data
- `yaml/training_data.yaml` - AI training samples
- `yaml/ml_model.pkl` - Trained ML model
- `logs/retraining_audit.yaml` - Audit trail

**Backup Schedule**: Daily automated backups recommended

## Future Enhancements

### Planned Features

1. **Deep Learning Models**
   - DistilBERT for better Swedish support
   - ~95% accuracy vs current ~85%

2. **Active Learning**
   - Intelligent sample selection
   - Request user feedback on uncertain predictions

3. **Multi-Language Support**
   - English, Swedish, Norwegian, Danish
   - Language detection

4. **Performance Optimization**
   - Parallel processing
   - GPU acceleration for semantic matching
   - Caching strategies

5. **Advanced Analytics**
   - Spending patterns detection
   - Anomaly detection
   - Predictive budgeting

## Maintenance

### Regular Tasks

- **Weekly**: Review uncategorized transactions
- **Monthly**: Check retraining audit log
- **Quarterly**: Evaluate category structure
- **Annually**: Review and update rules

### Monitoring Metrics

- Categorization accuracy (target: >85%)
- Uncategorized rate (target: <5%)
- Average confidence score (target: >0.75)
- Training samples per category (target: >20)

## Support

For technical issues or questions:
- Review this document
- Check test files for examples
- Review source code comments
- Contact development team

## Version History

- **1.0** (Sprint 9): Initial release with 12 categories, semantic matching, auto-retraining
