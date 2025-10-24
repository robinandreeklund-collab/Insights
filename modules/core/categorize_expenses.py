"""Categorize expenses module for automatic and manual transaction categorization."""

from typing import Dict, Optional, List
import pandas as pd
import yaml
import os
import re

# Try to import ML categorizer
try:
    from modules.core.ml_categorizer import MLCategorizer
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("Warning: ML categorizer not available. Install scikit-learn to enable ML features.")

# Try to import categorization engine
try:
    from modules.core.categorization_engine import CategorizationEngine
    ENGINE_AVAILABLE = True
except ImportError:
    ENGINE_AVAILABLE = False
    print("Warning: Categorization engine not available.")


def load_categorization_rules(rules_file: str = "yaml/categorization_rules.yaml") -> List[dict]:
    """Load categorization rules from YAML file."""
    if os.path.exists(rules_file):
        with open(rules_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
            return data.get('rules', [])
    return []


def save_categorization_rules(rules: List[dict], rules_file: str = "yaml/categorization_rules.yaml") -> None:
    """Save categorization rules to YAML file."""
    with open(rules_file, 'w', encoding='utf-8') as f:
        yaml.dump({'rules': rules}, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def categorize_by_rules(description: str, rules: List[dict]) -> Optional[Dict[str, str]]:
    """
    Categorize a transaction based on rules.
    
    Args:
        description: Transaction description
        rules: List of categorization rules
        
    Returns:
        Dictionary with category and subcategory, or None if no match
    """
    if not description:
        return None
    
    # Sort rules by priority (higher first)
    sorted_rules = sorted(rules, key=lambda r: r.get('priority', 0), reverse=True)
    
    description_lower = description.lower()
    
    for rule in sorted_rules:
        pattern = rule.get('pattern', '')
        if not pattern:
            continue
        
        # Try regex match
        try:
            if re.search(pattern.lower(), description_lower):
                return {
                    'category': rule.get('category', 'Övrigt'),
                    'subcategory': rule.get('subcategory', 'Okategoriserat')
                }
        except re.error:
            # If regex fails, try simple substring match
            if pattern.lower() in description_lower:
                return {
                    'category': rule.get('category', 'Övrigt'),
                    'subcategory': rule.get('subcategory', 'Okategoriserat')
                }
    
    return None


def categorize_by_ai_heuristic(description: str, amount: float, training_data: List[dict]) -> Optional[Dict[str, str]]:
    """
    Simple AI/heuristic categorization based on keywords and training data.
    
    Args:
        description: Transaction description
        amount: Transaction amount
        training_data: List of training data entries
        
    Returns:
        Dictionary with category and subcategory, or None if no match
    """
    if not description:
        return None
    
    description_lower = description.lower()
    
    # Simple keyword-based heuristics
    keyword_categories = {
        'Mat & Dryck': {
            'keywords': ['ica', 'coop', 'hemköp', 'willys', 'lidl', 'mataffär', 'restaurang', 'café', 'pizza', 'burger', 'sushi'],
            'subcategory': 'Matinköp'
        },
        'Transport': {
            'keywords': ['bensin', 'diesel', 'parkering', 'parkera', 'sl ', 'tåg', 'buss', 'taxi', 'uber'],
            'subcategory': 'Bränsle & Parkering'
        },
        'Boende': {
            'keywords': ['hyra', 'el', 'vatten', 'bredband', 'telefon', 'internet', 'försäkring'],
            'subcategory': 'Hyra & Räkningar'
        },
        'Övrigt': {
            'keywords': ['överföring', 'uttag', 'insättning', 'betalning'],
            'subcategory': 'Transaktioner'
        }
    }
    
    # Check keywords
    for category, data in keyword_categories.items():
        for keyword in data['keywords']:
            if keyword in description_lower:
                return {
                    'category': category,
                    'subcategory': data['subcategory']
                }
    
    # Check training data for similar descriptions
    if training_data:
        for entry in training_data:
            train_desc = entry.get('description', '').lower()
            if train_desc and train_desc in description_lower:
                return {
                    'category': entry.get('category', 'Övrigt'),
                    'subcategory': entry.get('subcategory', 'Okategoriserat')
                }
    
    return None


def auto_categorize(data: pd.DataFrame, rules: List[dict] = None, training_data: List[dict] = None, use_ml: bool = True, use_engine: bool = True) -> pd.DataFrame:
    """
    Automatically categorize transactions using rules, ML, and heuristics.
    
    Args:
        data: DataFrame with transaction data
        rules: List of categorization rules (optional, will load from file if not provided)
        training_data: List of training data (optional)
        use_ml: Whether to use ML model for categorization (default: True)
        use_engine: Whether to use advanced categorization engine (default: True)
        
    Returns:
        DataFrame with categorized transactions
    """
    df = data.copy()
    
    # Initialize category columns if they don't exist
    if 'category' not in df.columns:
        df['category'] = ''
    if 'subcategory' not in df.columns:
        df['subcategory'] = ''
    if 'confidence_score' not in df.columns:
        df['confidence_score'] = 0.0
    if 'categorization_source' not in df.columns:
        df['categorization_source'] = ''
    
    # Try to use advanced categorization engine first
    if use_engine and ENGINE_AVAILABLE:
        try:
            engine = CategorizationEngine()
            print(f"Using advanced categorization engine with {engine.get_stats()['categories']} categories")
            
            # Categorize each transaction
            for idx, row in df.iterrows():
                try:
                    # Skip if already categorized
                    if row.get('category') and row.get('subcategory'):
                        continue
                    
                    description = str(row.get('description', ''))
                    amount = float(row.get('amount', 0))
                    merchant = str(row.get('merchant', '')) if 'merchant' in row else None
                    account_type = str(row.get('account_type', '')) if 'account_type' in row else None
                    
                    # Use categorization engine
                    result = engine.categorize(
                        description=description,
                        amount=amount,
                        merchant=merchant,
                        account_type=account_type,
                        use_ai=use_ml,
                        use_semantic=False  # Disable semantic for now due to compatibility issues
                    )
                    
                    # Apply categorization
                    if result:
                        df.at[idx, 'category'] = result['category']
                        df.at[idx, 'subcategory'] = result['subcategory']
                        df.at[idx, 'confidence_score'] = result.get('confidence_score', 0.0)
                        df.at[idx, 'categorization_source'] = result.get('source', 'unknown')
                except Exception as row_error:
                    # If single transaction fails, log and continue with default
                    print(f"Error categorizing transaction at row {idx}: {row_error}")
                    df.at[idx, 'category'] = 'Övrigt'
                    df.at[idx, 'subcategory'] = 'Okategoriserat'
                    df.at[idx, 'confidence_score'] = 0.0
                    df.at[idx, 'categorization_source'] = 'error_fallback'
            
            return df
        except Exception as e:
            import traceback
            print(f"Categorization engine error: {e}")
            traceback.print_exc()
            print("Falling back to legacy method.")
    
    # Fallback to legacy categorization method
    # Load rules if not provided
    if rules is None:
        rules = load_categorization_rules()
    
    # Load training data if not provided
    if training_data is None:
        training_data = []
        training_file = "yaml/training_data.yaml"
        if os.path.exists(training_file):
            with open(training_file, 'r', encoding='utf-8') as f:
                data_dict = yaml.safe_load(f) or {}
                training_data = data_dict.get('training_data', [])
    
    # Initialize ML categorizer if available and requested
    ml_categorizer = None
    if use_ml and ML_AVAILABLE:
        ml_categorizer = MLCategorizer()
        if not ml_categorizer.is_trained:
            # Try to train if we have enough data
            result = ml_categorizer.train()
            if not result['success']:
                ml_categorizer = None
                print(f"ML model not available: {result['message']}")
    
    # Categorize each transaction
    for idx, row in df.iterrows():
        # Skip if already categorized
        if row.get('category') and row.get('subcategory'):
            continue
        
        description = str(row.get('description', ''))
        amount = float(row.get('amount', 0))
        
        # Try rule-based categorization first (highest priority)
        result = categorize_by_rules(description, rules)
        source = 'rule'
        
        # If no rule match, try ML model
        if not result and ml_categorizer is not None:
            result = ml_categorizer.predict(description, return_probability=True)
            source = 'ai'
        
        # If no ML match, try heuristic
        if not result:
            result = categorize_by_ai_heuristic(description, amount, training_data)
            source = 'heuristic'
        
        # Apply categorization
        if result:
            df.at[idx, 'category'] = result['category']
            df.at[idx, 'subcategory'] = result.get('subcategory', '')
            df.at[idx, 'confidence_score'] = result.get('confidence_score', 1.0)
            df.at[idx, 'categorization_source'] = source
        else:
            # Default category
            df.at[idx, 'category'] = 'Övrigt'
            df.at[idx, 'subcategory'] = 'Okategoriserat'
            df.at[idx, 'confidence_score'] = 0.0
            df.at[idx, 'categorization_source'] = 'default'
    
    return df


def manual_override(data: pd.DataFrame, overrides: dict) -> pd.DataFrame:
    """
    Apply manual category overrides to transactions.
    
    Args:
        data: DataFrame with transaction data
        overrides: Dictionary with manual overrides {transaction_id: {category, subcategory}}
        
    Returns:
        DataFrame with updated categories
    """
    df = data.copy()
    
    for tx_id, override in overrides.items():
        mask = df['id'] == tx_id
        if mask.any():
            if 'category' in override:
                df.loc[mask, 'category'] = override['category']
            if 'subcategory' in override:
                df.loc[mask, 'subcategory'] = override['subcategory']
    
    return df


def update_category_map(new_rules: List[dict], rules_file: str = "yaml/categorization_rules.yaml") -> None:
    """
    Update the category mapping with new rules.
    
    Args:
        new_rules: List of new categorization rules
        rules_file: Path to rules file
    """
    existing_rules = load_categorization_rules(rules_file)
    
    # Merge rules (new rules take precedence)
    for new_rule in new_rules:
        # Check if rule with same pattern exists
        existing_idx = None
        for idx, rule in enumerate(existing_rules):
            if rule.get('pattern') == new_rule.get('pattern'):
                existing_idx = idx
                break
        
        if existing_idx is not None:
            # Update existing rule
            existing_rules[existing_idx] = new_rule
        else:
            # Add new rule
            existing_rules.append(new_rule)
    
    save_categorization_rules(existing_rules, rules_file)
