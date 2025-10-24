"""Admin Dashboard - Manage and train AI on imported transactions."""

import os
import yaml
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import re
from collections import defaultdict


class AdminDashboard:
    """Admin dashboard for training AI and managing categories."""
    
    def __init__(self, yaml_dir: str = "yaml"):
        """Initialize the admin dashboard.
        
        Args:
            yaml_dir: Directory where YAML data is stored
        """
        self.yaml_dir = yaml_dir
        self.transactions_file = os.path.join(yaml_dir, "transactions.yaml")
        self.training_data_file = os.path.join(yaml_dir, "training_data.yaml")
        self.categorization_rules_file = os.path.join(yaml_dir, "categorization_rules.yaml")
        self.categories_file = os.path.join(yaml_dir, "categories.yaml")
        
        os.makedirs(yaml_dir, exist_ok=True)
    
    def _load_yaml(self, filepath: str) -> Dict:
        """Load YAML file or return default structure."""
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                return data
        return {}
    
    def _save_yaml(self, filepath: str, data: Dict) -> None:
        """Save data to YAML file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    def get_all_transactions(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Get all transactions with optional filtering.
        
        Args:
            filters: Dictionary with filter options:
                - source: Filter by source (e.g., 'import.csv', 'manual')
                - date_from: Start date (YYYY-MM-DD)
                - date_to: End date (YYYY-MM-DD)
                - min_amount: Minimum amount
                - max_amount: Maximum amount
                - category: Filter by category
                - uncategorized: If True, only show uncategorized transactions
                - account: Filter by account name
        
        Returns:
            List of filtered transactions
        """
        data = self._load_yaml(self.transactions_file)
        transactions = data.get('transactions', [])
        
        if not filters:
            return transactions
        
        filtered = []
        for tx in transactions:
            # Apply filters
            if filters.get('source') and tx.get('source') != filters['source']:
                continue
            
            if filters.get('date_from'):
                if tx.get('date', '') < filters['date_from']:
                    continue
            
            if filters.get('date_to'):
                if tx.get('date', '') > filters['date_to']:
                    continue
            
            if filters.get('min_amount') is not None:
                if tx.get('amount', 0) < filters['min_amount']:
                    continue
            
            if filters.get('max_amount') is not None:
                if tx.get('amount', 0) > filters['max_amount']:
                    continue
            
            if filters.get('category'):
                if tx.get('category', '') != filters['category']:
                    continue
            
            if filters.get('uncategorized'):
                category = tx.get('category', '')
                if category and category not in ['Okategoriserat', 'Övrigt', '']:
                    continue
            
            if filters.get('account'):
                if tx.get('account', '') != filters['account']:
                    continue
            
            filtered.append(tx)
        
        return filtered
    
    def get_transaction_sources(self) -> List[str]:
        """Get unique sources from all transactions.
        
        Returns:
            List of unique source names
        """
        data = self._load_yaml(self.transactions_file)
        transactions = data.get('transactions', [])
        
        sources = set()
        for tx in transactions:
            source = tx.get('source', 'unknown')
            sources.add(source)
        
        return sorted(list(sources))
    
    def get_uncategorized_count(self) -> int:
        """Get count of uncategorized transactions.
        
        Returns:
            Number of uncategorized transactions
        """
        transactions = self.get_all_transactions({'uncategorized': True})
        return len(transactions)
    
    def update_transaction_category(self, transaction_id: str, category: str, 
                                    subcategory: str) -> bool:
        """Update category for a transaction.
        
        Args:
            transaction_id: ID of the transaction
            category: New category
            subcategory: New subcategory
        
        Returns:
            True if successful, False otherwise
        """
        data = self._load_yaml(self.transactions_file)
        transactions = data.get('transactions', [])
        
        for tx in transactions:
            if tx.get('id') == transaction_id:
                tx['category'] = category
                tx['subcategory'] = subcategory
                self._save_yaml(self.transactions_file, data)
                return True
        
        return False
    
    def bulk_update_categories(self, transaction_ids: List[str], category: str, 
                              subcategory: str) -> int:
        """Update categories for multiple transactions.
        
        Args:
            transaction_ids: List of transaction IDs
            category: New category
            subcategory: New subcategory
        
        Returns:
            Number of transactions updated
        """
        data = self._load_yaml(self.transactions_file)
        transactions = data.get('transactions', [])
        
        updated = 0
        for tx in transactions:
            if tx.get('id') in transaction_ids:
                tx['category'] = category
                tx['subcategory'] = subcategory
                updated += 1
        
        if updated > 0:
            self._save_yaml(self.transactions_file, data)
        
        return updated
    
    def add_to_training_data(self, description: str, category: str, 
                           subcategory: str) -> bool:
        """Add a transaction to training data.
        
        Args:
            description: Transaction description
            category: Category
            subcategory: Subcategory
        
        Returns:
            True if successful
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
        return True
    
    def bulk_train_ai(self, transactions: List[Dict]) -> int:
        """Add multiple transactions to training data.
        
        Args:
            transactions: List of transactions with description, category, subcategory
        
        Returns:
            Number of transactions added to training
        """
        data = self._load_yaml(self.training_data_file)
        if 'training_data' not in data:
            data['training_data'] = []
        
        added = 0
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for tx in transactions:
            description = tx.get('description', '')
            category = tx.get('category', '')
            subcategory = tx.get('subcategory', '')
            
            if not description or not category:
                continue
            
            training_entry = {
                'description': description,
                'category': category,
                'subcategory': subcategory,
                'manual': True,
                'added_at': timestamp
            }
            
            data['training_data'].append(training_entry)
            added += 1
        
        if added > 0:
            self._save_yaml(self.training_data_file, data)
        
        return added
    
    def get_category_statistics(self) -> Dict[str, Any]:
        """Get statistics about categories.
        
        Returns:
            Dictionary with category statistics
        """
        data = self._load_yaml(self.transactions_file)
        transactions = data.get('transactions', [])
        
        # Count transactions per category
        category_counts = defaultdict(int)
        total_amount_by_category = defaultdict(float)
        uncategorized = 0
        
        for tx in transactions:
            category = tx.get('category', 'Okategoriserat')
            amount = abs(tx.get('amount', 0))
            
            if category in ['', 'Okategoriserat', 'Övrigt'] or not category:
                uncategorized += 1
                category = 'Okategoriserat'
            
            category_counts[category] += 1
            total_amount_by_category[category] += amount
        
        # Calculate percentages
        total_transactions = len(transactions)
        category_percentages = {}
        for cat, count in category_counts.items():
            percentage = (count / total_transactions * 100) if total_transactions > 0 else 0
            category_percentages[cat] = round(percentage, 2)
        
        return {
            'total_transactions': total_transactions,
            'uncategorized_count': uncategorized,
            'uncategorized_percentage': round((uncategorized / total_transactions * 100) 
                                             if total_transactions > 0 else 0, 2),
            'category_counts': dict(category_counts),
            'category_percentages': category_percentages,
            'total_amount_by_category': dict(total_amount_by_category)
        }
    
    def get_ai_accuracy_stats(self) -> Dict[str, Any]:
        """Get AI accuracy statistics based on training data.
        
        Returns:
            Dictionary with AI accuracy metrics
        """
        training_data = self._load_yaml(self.training_data_file)
        training_samples = training_data.get('training_data', [])
        
        rules_data = self._load_yaml(self.categorization_rules_file)
        rules = rules_data.get('rules', [])
        
        ai_generated_rules = [r for r in rules if r.get('ai_generated', False)]
        manual_rules = [r for r in rules if not r.get('ai_generated', False)]
        
        # Count manual training samples by date
        samples_by_date = defaultdict(int)
        for sample in training_samples:
            if sample.get('manual', False):
                added_at = sample.get('added_at', '')
                if added_at:
                    date = added_at.split(' ')[0]
                    samples_by_date[date] += 1
        
        # Calculate trend (last 7 days vs previous 7 days)
        today = datetime.now()
        last_7_days = sum(samples_by_date.get((today - timedelta(days=i)).strftime('%Y-%m-%d'), 0) 
                         for i in range(7))
        prev_7_days = sum(samples_by_date.get((today - timedelta(days=i)).strftime('%Y-%m-%d'), 0) 
                         for i in range(7, 14))
        
        return {
            'total_training_samples': len(training_samples),
            'manual_training_samples': len([s for s in training_samples if s.get('manual', False)]),
            'total_rules': len(rules),
            'ai_generated_rules': len(ai_generated_rules),
            'manual_rules': len(manual_rules),
            'training_samples_last_7_days': last_7_days,
            'training_samples_prev_7_days': prev_7_days,
            'samples_by_date': dict(sorted(samples_by_date.items()))
        }
    
    def merge_categories(self, source_category: str, target_category: str) -> int:
        """Merge one category into another.
        
        Args:
            source_category: Category to merge from
            target_category: Category to merge into
        
        Returns:
            Number of transactions updated
        """
        data = self._load_yaml(self.transactions_file)
        transactions = data.get('transactions', [])
        
        updated = 0
        for tx in transactions:
            if tx.get('category') == source_category:
                tx['category'] = target_category
                updated += 1
        
        if updated > 0:
            self._save_yaml(self.transactions_file, data)
        
        # Also update training data
        training_data = self._load_yaml(self.training_data_file)
        training_samples = training_data.get('training_data', [])
        
        for sample in training_samples:
            if sample.get('category') == source_category:
                sample['category'] = target_category
        
        self._save_yaml(self.training_data_file, training_data)
        
        return updated
    
    def delete_category(self, category: str, move_to_category: str = 'Övrigt') -> int:
        """Delete a category and move transactions to another category.
        
        Args:
            category: Category to delete
            move_to_category: Category to move transactions to
        
        Returns:
            Number of transactions updated
        """
        return self.merge_categories(category, move_to_category)
    
    def get_import_errors(self) -> List[Dict]:
        """Get list of import errors from recent imports.
        
        Returns:
            List of import errors with details
        """
        # This is a placeholder - in production, you would track import errors
        # in a separate YAML file or database
        return []
