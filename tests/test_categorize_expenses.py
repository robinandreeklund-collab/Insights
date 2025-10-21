"""Unit tests for categorize_expenses module."""

import pytest
import pandas as pd
import os
import tempfile
from modules.core.categorize_expenses import (
    categorize_by_rules,
    categorize_by_ai_heuristic,
    auto_categorize,
    load_categorization_rules,
    save_categorization_rules,
    update_category_map
)


class TestCategorizeExpenses:
    """Test cases for categorize_expenses module."""
    
    def test_categorize_by_rules_nordea_fee(self):
        """Test rule-based categorization for Nordea fees."""
        rules = [
            {
                'pattern': 'Nordea Vardagspaket',
                'category': 'Boende',
                'subcategory': 'Bank & Avgifter',
                'priority': 100
            }
        ]
        
        result = categorize_by_rules('Nordea Vardagspaket', rules)
        assert result is not None
        assert result['category'] == 'Boende'
        assert result['subcategory'] == 'Bank & Avgifter'
    
    def test_categorize_by_rules_transfer(self):
        """Test rule-based categorization for transfers."""
        rules = [
            {
                'pattern': 'Överföring',
                'category': 'Överföringar',
                'subcategory': 'Intern överföring',
                'priority': 90
            }
        ]
        
        result = categorize_by_rules('Överföring 1709 20 72840', rules)
        assert result is not None
        assert result['category'] == 'Överföringar'
    
    def test_categorize_by_rules_no_match(self):
        """Test rule-based categorization with no match."""
        rules = [
            {
                'pattern': 'ICA',
                'category': 'Mat & Dryck',
                'subcategory': 'Matinköp',
                'priority': 80
            }
        ]
        
        result = categorize_by_rules('Random transaction', rules)
        assert result is None
    
    def test_categorize_by_ai_heuristic_food(self):
        """Test AI heuristic categorization for food."""
        result = categorize_by_ai_heuristic('ICA Maxi Köping', -200.0, [])
        assert result is not None
        assert result['category'] == 'Mat & Dryck'
        assert result['subcategory'] == 'Matinköp'
    
    def test_categorize_by_ai_heuristic_transport(self):
        """Test AI heuristic categorization for transport."""
        result = categorize_by_ai_heuristic('Parkering P-hus', -50.0, [])
        assert result is not None
        assert result['category'] == 'Transport'
    
    def test_auto_categorize_dataframe(self):
        """Test automatic categorization of a DataFrame."""
        # Create sample data
        data = pd.DataFrame({
            'description': ['Nordea Vardagspaket', 'ICA Maxi', 'Random Store'],
            'amount': [-35.0, -200.0, -50.0]
        })
        
        # Load real rules
        rules = load_categorization_rules()
        
        categorized = auto_categorize(data, rules=rules)
        
        # Check that category columns were added
        assert 'category' in categorized.columns
        assert 'subcategory' in categorized.columns
        
        # Check specific categorizations
        assert categorized.iloc[0]['category'] == 'Boende'  # Nordea fee
        assert categorized.iloc[1]['category'] == 'Mat & Dryck'  # ICA
    
    def test_save_and_load_rules(self):
        """Test saving and loading categorization rules."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_file = f.name
        
        try:
            # Create test rules
            test_rules = [
                {
                    'pattern': 'TEST',
                    'category': 'Test Category',
                    'subcategory': 'Test Subcategory',
                    'priority': 100
                }
            ]
            
            # Save rules
            save_categorization_rules(test_rules, temp_file)
            
            # Load rules
            loaded_rules = load_categorization_rules(temp_file)
            
            assert len(loaded_rules) == 1
            assert loaded_rules[0]['pattern'] == 'TEST'
            assert loaded_rules[0]['category'] == 'Test Category'
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_update_category_map(self):
        """Test updating category mapping with new rules."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_file = f.name
        
        try:
            # Start with initial rules
            initial_rules = [
                {
                    'pattern': 'OLD',
                    'category': 'Old Category',
                    'subcategory': 'Old Sub',
                    'priority': 50
                }
            ]
            save_categorization_rules(initial_rules, temp_file)
            
            # Add new rules
            new_rules = [
                {
                    'pattern': 'NEW',
                    'category': 'New Category',
                    'subcategory': 'New Sub',
                    'priority': 100
                }
            ]
            update_category_map(new_rules, temp_file)
            
            # Load and verify
            all_rules = load_categorization_rules(temp_file)
            assert len(all_rules) == 2
            patterns = [r['pattern'] for r in all_rules]
            assert 'OLD' in patterns
            assert 'NEW' in patterns
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
