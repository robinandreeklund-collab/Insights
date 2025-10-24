"""ML-based transaction categorizer using scikit-learn MultinomialNB."""

import os
import yaml
import pickle
from typing import Dict, Optional, List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import numpy as np


class MLCategorizer:
    """Machine Learning categorizer using Multinomial Naive Bayes."""
    
    def __init__(self, yaml_dir: str = "yaml"):
        """Initialize ML categorizer.
        
        Args:
            yaml_dir: Directory containing YAML files
        """
        self.yaml_dir = yaml_dir
        self.training_data_file = os.path.join(yaml_dir, "training_data.yaml")
        self.model_file = os.path.join(yaml_dir, "ml_model.pkl")
        self.model = None
        self.categories = []
        self.is_trained = False
        
        # Try to load existing model
        self._load_model()
    
    def _load_yaml(self, filepath: str) -> dict:
        """Load YAML file or return default structure."""
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                return data
        return {}
    
    def _load_model(self) -> bool:
        """Load trained model from file.
        
        Returns:
            True if model loaded successfully, False otherwise
        """
        if os.path.exists(self.model_file):
            try:
                with open(self.model_file, 'rb') as f:
                    model_data = pickle.load(f)
                    self.model = model_data['pipeline']
                    self.categories = model_data['categories']
                    self.is_trained = True
                return True
            except Exception as e:
                print(f"Error loading model: {str(e)}")
                return False
        return False
    
    def _save_model(self) -> None:
        """Save trained model to file."""
        if self.model is not None and self.is_trained:
            model_data = {
                'pipeline': self.model,
                'categories': self.categories
            }
            with open(self.model_file, 'wb') as f:
                pickle.dump(model_data, f)
    
    def get_training_data(self) -> Tuple[List[str], List[str]]:
        """Get training data from YAML file.
        
        Returns:
            Tuple of (descriptions, categories)
        """
        data = self._load_yaml(self.training_data_file)
        training_samples = data.get('training_data', [])
        
        descriptions = []
        categories = []
        
        for sample in training_samples:
            desc = sample.get('description', '').strip()
            cat = sample.get('category', '').strip()
            
            if desc and cat:
                descriptions.append(desc)
                categories.append(cat)
        
        return descriptions, categories
    
    def train(self, min_samples_per_category: int = 2) -> Dict:
        """Train the ML model from training data.
        
        Args:
            min_samples_per_category: Minimum samples needed per category
            
        Returns:
            Dictionary with training results
        """
        descriptions, categories = self.get_training_data()
        
        if len(descriptions) < 2:
            return {
                'success': False,
                'message': f"Need at least 2 training samples. Currently have {len(descriptions)}.",
                'samples_used': 0,
                'categories': []
            }
        
        # Count samples per category
        from collections import Counter
        category_counts = Counter(categories)
        
        # Filter out categories with too few samples
        valid_categories = {cat for cat, count in category_counts.items() 
                          if count >= min_samples_per_category}
        
        if len(valid_categories) < 2:
            return {
                'success': False,
                'message': f"Need at least 2 categories with {min_samples_per_category}+ samples each. "
                          f"Currently have {len(valid_categories)} valid categories.",
                'samples_used': 0,
                'categories': list(valid_categories)
            }
        
        # Filter training data to only include valid categories
        filtered_descriptions = []
        filtered_categories = []
        for desc, cat in zip(descriptions, categories):
            if cat in valid_categories:
                filtered_descriptions.append(desc)
                filtered_categories.append(cat)
        
        # Create and train pipeline
        self.model = Pipeline([
            ('tfidf', TfidfVectorizer(
                max_features=500,
                ngram_range=(1, 2),
                min_df=1,
                lowercase=True,
                strip_accents='unicode'
            )),
            ('clf', MultinomialNB(alpha=0.1))
        ])
        
        self.model.fit(filtered_descriptions, filtered_categories)
        self.categories = sorted(list(valid_categories))
        self.is_trained = True
        
        # Save the trained model
        self._save_model()
        
        return {
            'success': True,
            'message': f"Model trained successfully with {len(filtered_descriptions)} samples across {len(self.categories)} categories.",
            'samples_used': len(filtered_descriptions),
            'categories': self.categories,
            'category_counts': dict(category_counts)
        }
    
    def predict(self, description: str, return_probability: bool = False) -> Optional[Dict[str, str]]:
        """Predict category for a transaction description.
        
        Args:
            description: Transaction description
            return_probability: If True, include prediction probability
            
        Returns:
            Dictionary with category, subcategory (empty), and optional probability
        """
        if not self.is_trained or self.model is None:
            return None
        
        if not description or not description.strip():
            return None
        
        try:
            # Predict category
            predicted_category = str(self.model.predict([description])[0])
            
            result = {
                'category': predicted_category,
                'subcategory': '',  # ML model only predicts main category
                'method': 'ml'
            }
            
            if return_probability:
                # Get prediction probabilities
                probabilities = self.model.predict_proba([description])[0]
                max_prob = float(np.max(probabilities))
                result['confidence'] = round(max_prob, 3)
            
            return result
            
        except Exception as e:
            print(f"Error predicting category: {str(e)}")
            return None
    
    def predict_batch(self, descriptions: List[str]) -> List[Optional[Dict[str, str]]]:
        """Predict categories for multiple descriptions.
        
        Args:
            descriptions: List of transaction descriptions
            
        Returns:
            List of prediction dictionaries
        """
        if not self.is_trained or self.model is None:
            return [None] * len(descriptions)
        
        results = []
        for desc in descriptions:
            results.append(self.predict(desc))
        
        return results
    
    def get_model_info(self) -> Dict:
        """Get information about the trained model.
        
        Returns:
            Dictionary with model information
        """
        descriptions, categories = self.get_training_data()
        
        from collections import Counter
        category_counts = Counter(categories)
        
        return {
            'is_trained': self.is_trained,
            'total_samples': len(descriptions),
            'num_categories': len(self.categories) if self.is_trained else 0,
            'categories': self.categories if self.is_trained else [],
            'model_file_exists': os.path.exists(self.model_file),
            'category_distribution': dict(category_counts)
        }
    
    def retrain_if_needed(self, force: bool = False) -> Dict:
        """Retrain model if there's new training data or force is True.
        
        Args:
            force: Force retraining even if model exists
            
        Returns:
            Dictionary with retraining results
        """
        if force or not self.is_trained:
            return self.train()
        
        return {
            'success': True,
            'message': 'Model already trained. Use force=True to retrain.',
            'samples_used': 0,
            'categories': self.categories
        }
