"""
Categorization Engine for Insights

Self-learning classification engine for household financial transactions.
Combines rule-based logic, AI prediction, semantic matching, and manual feedback.
"""

import os
import yaml
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class CategorizationEngine:
    """
    Main categorization engine that orchestrates all categorization strategies.
    
    Prioritization:
    1. Manual override (highest priority)
    2. AI prediction (if confidence >= threshold)
    3. Semantic matching (if similarity >= threshold)
    4. Rule-based matching
    5. Default fallback
    """
    
    def __init__(self, config_path: str = "yaml/categorization_engine.yaml"):
        """Initialize the categorization engine with configuration."""
        self.config_path = config_path
        self.config = self._load_config()
        self.rules = self._load_rules()
        self.semantic_vectors = self._load_semantic_vectors()
        
        # Initialize components
        self.confidence_threshold = self.config.get('confidence_threshold', {}).get('minimum', 0.65)
        self.semantic_threshold = self.config.get('semantic_matching', {}).get('similarity_threshold', 0.75)
        self.retrain_trigger = self.config.get('strategy', {}).get('retrain_trigger', 10)
        
        # Track manual overrides for retraining
        self.manual_override_count = 0
        
        logger.info(f"Categorization Engine initialized with confidence threshold {self.confidence_threshold}")
    
    def _load_config(self) -> Dict:
        """Load main engine configuration."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config.get('categorization_engine', {})
        except FileNotFoundError:
            logger.warning(f"Config file not found: {self.config_path}. Using defaults.")
            return {}
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
    def _load_rules(self) -> Dict:
        """Load categorization rules."""
        rules_path = "yaml/categorization_rules.yaml"
        try:
            with open(rules_path, 'r', encoding='utf-8') as f:
                rules = yaml.safe_load(f)
            return rules.get('categorization_rules', {})
        except Exception as e:
            logger.error(f"Error loading rules: {e}")
            return {}
    
    def _load_semantic_vectors(self) -> Dict:
        """Load semantic vector examples."""
        vectors_path = "yaml/semantic_vectors.yaml"
        try:
            with open(vectors_path, 'r', encoding='utf-8') as f:
                vectors = yaml.safe_load(f)
            return vectors.get('semantic_vectors', {})
        except Exception as e:
            logger.error(f"Error loading semantic vectors: {e}")
            return {}
    
    def categorize(self, 
                  description: str,
                  amount: float = None,
                  merchant: str = None,
                  account_type: str = None,
                  use_ai: bool = True,
                  use_semantic: bool = True) -> Dict:
        """
        Categorize a transaction using all available strategies.
        
        Args:
            description: Transaction description
            amount: Transaction amount (optional)
            merchant: Merchant name (optional)
            account_type: Account type (optional)
            use_ai: Whether to use AI prediction
            use_semantic: Whether to use semantic matching
        
        Returns:
            Dict with category, subcategory, confidence_score, and source
        """
        result = {
            'category': 'Övrigt',
            'subcategory': 'Okänd',
            'confidence_score': 0.0,
            'source': 'default',
            'flagged': False
        }
        
        # Strategy 1: AI Prediction (if enabled and available)
        if use_ai:
            ai_result = self._try_ai_prediction(description, merchant, amount, account_type)
            if ai_result and ai_result['confidence_score'] >= self.confidence_threshold:
                result = ai_result
                result['source'] = 'ai'
                logger.debug(f"AI categorized: {description} -> {result['category']}/{result['subcategory']} ({result['confidence_score']:.2f})")
                return result
        
        # Strategy 2: Semantic Matching (if enabled)
        if use_semantic:
            semantic_result = self._try_semantic_matching(description, merchant)
            if semantic_result and semantic_result['confidence_score'] >= self.semantic_threshold:
                result = semantic_result
                result['source'] = 'semantic'
                logger.debug(f"Semantic matched: {description} -> {result['category']}/{result['subcategory']} ({result['confidence_score']:.2f})")
                return result
        
        # Strategy 3: Rule-based matching
        rule_result = self._try_rule_matching(description, merchant)
        if rule_result:
            result = rule_result
            result['source'] = 'rule'
            logger.debug(f"Rule matched: {description} -> {result['category']}/{result['subcategory']}")
            return result
        
        # Strategy 4: Default fallback
        result['flagged'] = True  # Flag for manual review
        logger.debug(f"No match found for: {description}. Using default.")
        return result
    
    def _try_ai_prediction(self, description: str, merchant: str, amount: float, account_type: str) -> Optional[Dict]:
        """Try AI-based prediction using ML model."""
        try:
            from modules.core.ml_categorizer import MLCategorizer
            
            ml = MLCategorizer()
            if ml.is_trained():
                category = ml.predict(description)
                confidence = ml.get_confidence()
                
                if category and category != 'Övrigt':
                    # Try to split into category/subcategory
                    parts = category.split('/')
                    if len(parts) == 2:
                        return {
                            'category': parts[0],
                            'subcategory': parts[1],
                            'confidence_score': confidence,
                            'flagged': confidence < self.confidence_threshold
                        }
                    else:
                        return {
                            'category': category,
                            'subcategory': 'Övrigt',
                            'confidence_score': confidence,
                            'flagged': confidence < self.confidence_threshold
                        }
        except Exception as e:
            logger.debug(f"AI prediction failed: {e}")
        
        return None
    
    def _try_semantic_matching(self, description: str, merchant: str) -> Optional[Dict]:
        """Try semantic matching using sentence transformers."""
        try:
            from modules.core.semantic_matcher import SemanticMatcher
            
            matcher = SemanticMatcher()
            text = f"{description} {merchant or ''}".strip()
            result = matcher.match(text)
            
            if result and result.get('similarity_score', 0) >= self.semantic_threshold:
                return {
                    'category': result['category'],
                    'subcategory': result['subcategory'],
                    'confidence_score': result['similarity_score'],
                    'flagged': result['similarity_score'] < 0.85
                }
        except Exception as e:
            logger.debug(f"Semantic matching failed: {e}")
        
        return None
    
    def _try_rule_matching(self, description: str, merchant: str) -> Optional[Dict]:
        """Try rule-based matching using keyword patterns."""
        text = f"{description} {merchant or ''}".lower()
        
        # Iterate through all categories and subcategories
        for category, subcategories in self.rules.items():
            if not isinstance(subcategories, dict):
                continue
            
            for subcategory, keywords in subcategories.items():
                if not isinstance(keywords, list):
                    continue
                
                # Check if any keyword matches
                for keyword in keywords:
                    if keyword.lower() in text:
                        return {
                            'category': category,
                            'subcategory': subcategory,
                            'confidence_score': 1.0,  # Rule-based is 100% confident
                            'flagged': False
                        }
        
        return None
    
    def register_manual_override(self, 
                                transaction_id: str,
                                category: str,
                                subcategory: str,
                                description: str,
                                train_ai: bool = True):
        """
        Register a manual override and trigger retraining if threshold is met.
        
        Args:
            transaction_id: Unique transaction ID
            category: Manual category assignment
            subcategory: Manual subcategory assignment  
            description: Transaction description
            train_ai: Whether to add to training data
        """
        self.manual_override_count += 1
        
        # Log the override
        logger.info(f"Manual override registered: {description} -> {category}/{subcategory}")
        
        # Add to training data if requested
        if train_ai:
            try:
                from modules.core.ai_trainer import AITrainer
                trainer = AITrainer()
                trainer.add_training_sample(description, f"{category}/{subcategory}")
                logger.debug(f"Added training sample: {description} -> {category}/{subcategory}")
            except Exception as e:
                logger.error(f"Failed to add training sample: {e}")
        
        # Check if retraining threshold is met
        if self.manual_override_count >= self.retrain_trigger:
            logger.info(f"Retraining threshold ({self.retrain_trigger}) reached. Triggering automatic retraining...")
            self._trigger_retraining()
            self.manual_override_count = 0
    
    def _trigger_retraining(self):
        """Trigger automatic model retraining."""
        try:
            from modules.core.retraining_pipeline import RetrainingPipeline
            pipeline = RetrainingPipeline()
            result = pipeline.run()
            logger.info(f"Automatic retraining completed: {result}")
        except Exception as e:
            logger.error(f"Automatic retraining failed: {e}")
    
    def get_categories(self) -> List[str]:
        """Get list of all available categories."""
        categories = self.config.get('categories', [])
        return [cat['name'] for cat in categories]
    
    def get_subcategories(self, category: str) -> List[str]:
        """Get list of subcategories for a specific category."""
        categories = self.config.get('categories', [])
        for cat in categories:
            if cat['name'] == category:
                return cat.get('subcategories', [])
        return []
    
    def get_stats(self) -> Dict:
        """Get statistics about the categorization engine."""
        return {
            'categories': len(self.get_categories()),
            'confidence_threshold': self.confidence_threshold,
            'semantic_threshold': self.semantic_threshold,
            'manual_overrides_count': self.manual_override_count,
            'retrain_trigger': self.retrain_trigger,
            'rules_loaded': len(self.rules),
            'semantic_vectors_loaded': len(self.semantic_vectors)
        }


def convert_numpy_types(obj):
    """Recursively convert numpy types to native Python types."""
    import numpy as np
    
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj
