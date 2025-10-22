"""AI Trainer - Train categorization models from manual inputs."""

import os
import yaml
from typing import List, Dict, Optional
from datetime import datetime
import re


class AITrainer:
    """Train and manage AI categorization models from training data."""
    
    def __init__(self, yaml_dir: str = "yaml"):
        """Initialize AI trainer."""
        self.yaml_dir = yaml_dir
        self.training_data_file = os.path.join(yaml_dir, "training_data.yaml")
        self.categorization_rules_file = os.path.join(yaml_dir, "categorization_rules.yaml")
        
        # Ensure yaml directory exists
        os.makedirs(yaml_dir, exist_ok=True)
    
    def _load_yaml(self, filepath: str) -> dict:
        """Load YAML file or return default structure."""
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                return data
        return {}
    
    def _save_yaml(self, filepath: str, data: dict) -> None:
        """Save data to YAML file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    def get_training_data(self) -> List[Dict]:
        """Get all training data."""
        data = self._load_yaml(self.training_data_file)
        return data.get('training_data', [])
    
    def add_training_sample(self, description: str, category: str, subcategory: str) -> None:
        """Add a training sample from manual categorization.
        
        Args:
            description: Transaction description
            category: Main category
            subcategory: Subcategory
        """
        data = self._load_yaml(self.training_data_file)
        if 'training_data' not in data:
            data['training_data'] = []
        
        training_entry = {
            'description': description,
            'category': category,
            'subcategory': subcategory,
            'manual': True,
            'added_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        data['training_data'].append(training_entry)
        self._save_yaml(self.training_data_file, data)
    
    def get_training_stats(self) -> Dict:
        """Get statistics about training data.
        
        Returns:
            Dictionary with training statistics
        """
        training_data = self.get_training_data()
        
        if not training_data:
            return {
                'total_samples': 0,
                'manual_samples': 0,
                'categories': {},
                'ready_to_train': False,
                'min_samples_needed': 2
            }
        
        manual_samples = [t for t in training_data if t.get('manual', False)]
        
        # Count samples per category
        category_counts = {}
        for sample in training_data:
            category = sample.get('category', 'Unknown')
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            'total_samples': len(training_data),
            'manual_samples': len(manual_samples),
            'categories': category_counts,
            'ready_to_train': len(manual_samples) >= 2,
            'min_samples_needed': 2
        }
    
    def extract_keywords(self, description: str) -> List[str]:
        """Extract meaningful keywords from a description.
        
        Args:
            description: Transaction description
            
        Returns:
            List of keywords
        """
        # Convert to lowercase and split
        description = description.lower()
        
        # Remove common noise words
        noise_words = {'och', 'eller', 'för', 'från', 'till', 'med', 'av', 'på', 'i', 'en', 'ett', 'den', 'det'}
        
        # Split on non-alphanumeric characters
        words = re.findall(r'\w+', description)
        
        # Filter out noise words and very short words
        keywords = [w for w in words if len(w) > 2 and w not in noise_words]
        
        return keywords[:5]  # Return top 5 keywords
    
    def train_from_samples(self) -> Dict:
        """Train the AI model from training samples.
        
        This creates new categorization rules based on common patterns
        in the training data.
        
        Returns:
            Dictionary with training results
        """
        training_data = self.get_training_data()
        stats = self.get_training_stats()
        
        if not stats['ready_to_train']:
            return {
                'success': False,
                'message': f"Need at least {stats['min_samples_needed']} manual samples to train. Currently have {stats['manual_samples']}.",
                'rules_created': 0
            }
        
        # Group training samples by category
        category_samples = {}
        for sample in training_data:
            if not sample.get('manual', False):
                continue
            
            category = sample.get('category', 'Unknown')
            if category not in category_samples:
                category_samples[category] = []
            category_samples[category].append(sample)
        
        # Load existing rules
        rules_data = self._load_yaml(self.categorization_rules_file)
        existing_rules = rules_data.get('rules', [])
        
        # Create new rules from patterns
        new_rules = []
        for category, samples in category_samples.items():
            # Extract common keywords from descriptions
            for sample in samples:
                description = sample.get('description', '')
                keywords = self.extract_keywords(description)
                
                if not keywords:
                    continue
                
                # Create a rule for the most significant keyword
                primary_keyword = keywords[0]
                
                # Check if this pattern already exists
                pattern_exists = False
                for rule in existing_rules:
                    if primary_keyword.lower() in rule.get('pattern', '').lower():
                        pattern_exists = True
                        break
                
                if not pattern_exists:
                    new_rule = {
                        'pattern': primary_keyword.upper(),
                        'category': category,
                        'subcategory': sample.get('subcategory', ''),
                        'priority': 60,  # Lower than manual rules, higher than default
                        'ai_generated': True,
                        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    new_rules.append(new_rule)
        
        # Add new rules to existing rules
        if new_rules:
            existing_rules.extend(new_rules)
            rules_data['rules'] = existing_rules
            self._save_yaml(self.categorization_rules_file, rules_data)
        
        return {
            'success': True,
            'message': f"Training complete! Created {len(new_rules)} new categorization rules.",
            'rules_created': len(new_rules),
            'categories_trained': list(category_samples.keys())
        }
    
    def clear_training_data(self) -> bool:
        """Clear all training data.
        
        Returns:
            True if successful
        """
        data = {'training_data': []}
        self._save_yaml(self.training_data_file, data)
        return True
    
    def remove_ai_generated_rules(self) -> int:
        """Remove all AI-generated rules.
        
        Returns:
            Number of rules removed
        """
        rules_data = self._load_yaml(self.categorization_rules_file)
        existing_rules = rules_data.get('rules', [])
        
        # Filter out AI-generated rules
        manual_rules = [r for r in existing_rules if not r.get('ai_generated', False)]
        removed_count = len(existing_rules) - len(manual_rules)
        
        if removed_count > 0:
            rules_data['rules'] = manual_rules
            self._save_yaml(self.categorization_rules_file, rules_data)
        
        return removed_count
