"""Tests for net_balance_splitter module."""

import pytest
from modules.core.net_balance_splitter import NetBalanceSplitter, calculate_transfer_recommendations


class TestNetBalanceSplitter:
    """Test NetBalanceSplitter functionality."""
    
    def test_initialization(self):
        """Test NetBalanceSplitter initialization."""
        splitter = NetBalanceSplitter()
        assert splitter is not None
    
    def test_calculate_shared_expenses_basic(self):
        """Test basic shared expense calculation."""
        splitter = NetBalanceSplitter()
        
        income_by_person = {
            'Robin': 30000.0,
            'Partner': 20000.0
        }
        
        total_expenses = 10000.0
        
        result = splitter.calculate_shared_expenses(total_expenses, income_by_person)
        
        assert 'Robin' in result
        assert 'Partner' in result
        assert result['Robin']['income'] == 30000.0
        assert result['Partner']['income'] == 20000.0
        
        # Robin earns 60% of total, so should pay 60% of expenses
        assert abs(result['Robin']['expense_share'] - 6000.0) < 0.01
        assert abs(result['Partner']['expense_share'] - 4000.0) < 0.01
    
    def test_calculate_shared_expenses_with_custom_ratios(self):
        """Test shared expense calculation with custom ratios."""
        splitter = NetBalanceSplitter()
        
        income_by_person = {
            'Robin': 30000.0,
            'Partner': 20000.0
        }
        
        custom_ratios = {
            'Robin': 0.5,
            'Partner': 0.5
        }
        
        total_expenses = 10000.0
        
        result = splitter.calculate_shared_expenses(
            total_expenses, 
            income_by_person,
            custom_ratios=custom_ratios
        )
        
        # With 50/50 split
        assert abs(result['Robin']['expense_share'] - 5000.0) < 0.01
        assert abs(result['Partner']['expense_share'] - 5000.0) < 0.01
    
    def test_calculate_shared_expenses_no_income(self):
        """Test shared expense calculation when no income."""
        splitter = NetBalanceSplitter()
        
        income_by_person = {
            'Robin': 0.0,
            'Partner': 0.0
        }
        
        total_expenses = 10000.0
        
        result = splitter.calculate_shared_expenses(total_expenses, income_by_person)
        
        # Should split equally when no income
        assert abs(result['Robin']['expense_share'] - 5000.0) < 0.01
        assert abs(result['Partner']['expense_share'] - 5000.0) < 0.01
    
    def test_calculate_transfer_recommendations(self):
        """Test transfer recommendations calculation."""
        splitter = NetBalanceSplitter()
        
        income_by_person_and_account = {
            'Robin': {
                '1234 56 78901': 30000.0
            },
            'Partner': {
                '2345 67 89012': 20000.0
            }
        }
        
        expenses_by_category = {
            'Boende': 8000.0,
            'Mat & Dryck': 4000.0,
            'Transport': 3000.0
        }
        
        shared_categories = ['Boende', 'Mat & Dryck']
        
        result = splitter.calculate_transfer_recommendations(
            income_by_person_and_account,
            expenses_by_category,
            shared_categories=shared_categories
        )
        
        assert 'total_shared_expenses' in result
        assert result['total_shared_expenses'] == 12000.0  # 8000 + 4000
        
        assert 'persons' in result
        assert 'Robin' in result['persons']
        assert 'Partner' in result['persons']
        
        # Robin should pay 60% of 12000 = 7200
        assert abs(result['persons']['Robin']['should_transfer'] - 7200.0) < 0.01
        # Partner should pay 40% of 12000 = 4800
        assert abs(result['persons']['Partner']['should_transfer'] - 4800.0) < 0.01
    
    def test_split_balance_after_expenses(self):
        """Test balance splitting after expenses."""
        splitter = NetBalanceSplitter()
        
        balances_by_person = {
            'Robin': 30000.0,
            'Partner': 20000.0
        }
        
        expenses_paid = {
            'Robin': 8000.0,
            'Partner': 4000.0
        }
        
        result = splitter.split_balance_after_expenses(
            balances_by_person,
            expenses_paid
        )
        
        # Total paid: 12000
        # Robin should pay 60% of 12000 = 7200, but paid 8000, so +800
        # Partner should pay 40% of 12000 = 4800, but paid 4000, so -800
        assert abs(result['Robin'] - 800.0) < 0.01
        assert abs(result['Partner'] - (-800.0)) < 0.01
    
    def test_wrapper_function(self):
        """Test wrapper function."""
        income_by_person_and_account = {
            'Robin': {'1234 56 78901': 30000.0},
            'Partner': {'2345 67 89012': 20000.0}
        }
        
        expenses_by_category = {
            'Boende': 8000.0,
            'Mat & Dryck': 4000.0
        }
        
        result = calculate_transfer_recommendations(
            income_by_person_and_account,
            expenses_by_category
        )
        
        assert 'total_shared_expenses' in result
        assert 'persons' in result
        assert 'summary' in result
