"""Tests for income_tracker module."""

import unittest
import os
import yaml
import tempfile
import shutil
from datetime import datetime

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.core.income_tracker import IncomeTracker


class TestIncomeTracker(unittest.TestCase):
    """Test cases for IncomeTracker class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for test YAML files
        self.test_dir = tempfile.mkdtemp()
        self.tracker = IncomeTracker(yaml_dir=self.test_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
    
    def test_income_tracker_initialization(self):
        """Test IncomeTracker initialization."""
        self.assertIsNotNone(self.tracker)
        self.assertEqual(self.tracker.yaml_dir, self.test_dir)
    
    def test_add_income(self):
        """Test adding income."""
        income = self.tracker.add_income(
            person='Robin',
            account='Test Account',
            amount=30000.0,
            date='2025-01-25',
            description='Monthly salary',
            category='Lön'
        )
        
        self.assertIsNotNone(income)
        self.assertEqual(income['person'], 'Robin')
        self.assertEqual(income['account'], 'Test Account')
        self.assertEqual(income['amount'], 30000.0)
        self.assertEqual(income['date'], '2025-01-25')
        self.assertEqual(income['description'], 'Monthly salary')
        self.assertEqual(income['category'], 'Lön')
        self.assertIn('id', income)
        self.assertIn('created_at', income)
    
    def test_get_incomes(self):
        """Test getting all incomes."""
        # Add multiple incomes
        self.tracker.add_income('Robin', 'Account1', 30000.0, '2025-01-25', category='Lön')
        self.tracker.add_income('Anna', 'Account2', 25000.0, '2025-01-25', category='Lön')
        
        incomes = self.tracker.get_incomes()
        
        self.assertEqual(len(incomes), 2)
    
    def test_get_incomes_by_person(self):
        """Test filtering incomes by person."""
        self.tracker.add_income('Robin', 'Account1', 30000.0, '2025-01-25')
        self.tracker.add_income('Anna', 'Account2', 25000.0, '2025-01-25')
        self.tracker.add_income('Robin', 'Account1', 5000.0, '2025-01-26', category='Bonus')
        
        robin_incomes = self.tracker.get_incomes(person='Robin')
        anna_incomes = self.tracker.get_incomes(person='Anna')
        
        self.assertEqual(len(robin_incomes), 2)
        self.assertEqual(len(anna_incomes), 1)
    
    def test_get_incomes_by_account(self):
        """Test filtering incomes by account."""
        self.tracker.add_income('Robin', 'Account1', 30000.0, '2025-01-25')
        self.tracker.add_income('Robin', 'Account2', 25000.0, '2025-01-25')
        
        account1_incomes = self.tracker.get_incomes(account='Account1')
        account2_incomes = self.tracker.get_incomes(account='Account2')
        
        self.assertEqual(len(account1_incomes), 1)
        self.assertEqual(len(account2_incomes), 1)
    
    def test_get_incomes_by_date_range(self):
        """Test filtering incomes by date range."""
        self.tracker.add_income('Robin', 'Account1', 30000.0, '2025-01-15')
        self.tracker.add_income('Robin', 'Account1', 30000.0, '2025-01-25')
        self.tracker.add_income('Robin', 'Account1', 30000.0, '2025-02-15')
        
        jan_incomes = self.tracker.get_incomes(start_date='2025-01-01', end_date='2025-01-31')
        
        self.assertEqual(len(jan_incomes), 2)
    
    def test_get_monthly_income(self):
        """Test getting monthly income total."""
        self.tracker.add_income('Robin', 'Account1', 30000.0, '2025-01-25')
        self.tracker.add_income('Anna', 'Account2', 25000.0, '2025-01-25')
        self.tracker.add_income('Robin', 'Account1', 5000.0, '2025-01-26', category='Bonus')
        
        total = self.tracker.get_monthly_income('2025-01')
        
        self.assertEqual(total, 60000.0)
    
    def test_get_monthly_income_by_person(self):
        """Test getting monthly income for specific person."""
        self.tracker.add_income('Robin', 'Account1', 30000.0, '2025-01-25')
        self.tracker.add_income('Anna', 'Account2', 25000.0, '2025-01-25')
        
        robin_total = self.tracker.get_monthly_income('2025-01', person='Robin')
        anna_total = self.tracker.get_monthly_income('2025-01', person='Anna')
        
        self.assertEqual(robin_total, 30000.0)
        self.assertEqual(anna_total, 25000.0)
    
    def test_forecast_income(self):
        """Test income forecasting."""
        # Add historical data
        self.tracker.add_income('Robin', 'Account1', 30000.0, '2025-01-25')
        self.tracker.add_income('Robin', 'Account1', 30000.0, '2024-12-25')
        
        forecast = self.tracker.forecast_income(months=3, person='Robin')
        
        self.assertEqual(len(forecast), 3)
        for prediction in forecast:
            self.assertIn('month', prediction)
            self.assertIn('predicted_amount', prediction)
            self.assertIn('confidence', prediction)
    
    def test_get_income_by_person_summary(self):
        """Test getting income summary by person."""
        self.tracker.add_income('Robin', 'Account1', 30000.0, '2025-01-25')
        self.tracker.add_income('Anna', 'Account2', 25000.0, '2025-01-25')
        self.tracker.add_income('Robin', 'Account1', 5000.0, '2025-01-26', category='Bonus')
        
        summary = self.tracker.get_income_by_person(start_date='2025-01-01', end_date='2025-01-31')
        
        self.assertEqual(summary['Robin'], 35000.0)
        self.assertEqual(summary['Anna'], 25000.0)
    
    def test_delete_income(self):
        """Test deleting income."""
        income = self.tracker.add_income('Robin', 'Account1', 30000.0, '2025-01-25')
        income_id = income['id']
        
        # Delete
        result = self.tracker.delete_income(income_id)
        self.assertTrue(result)
        
        # Verify deleted
        incomes = self.tracker.get_incomes()
        self.assertEqual(len(incomes), 0)
    
    def test_delete_nonexistent_income(self):
        """Test deleting non-existent income."""
        result = self.tracker.delete_income('nonexistent-id')
        self.assertFalse(result)
    
    def test_update_income(self):
        """Test updating income."""
        income = self.tracker.add_income('Robin', 'Account1', 30000.0, '2025-01-25')
        income_id = income['id']
        
        # Update
        updated = self.tracker.update_income(income_id, amount=35000.0, description='Updated salary')
        
        self.assertIsNotNone(updated)
        self.assertEqual(updated['amount'], 35000.0)
        self.assertEqual(updated['description'], 'Updated salary')
    
    def test_update_nonexistent_income(self):
        """Test updating non-existent income."""
        result = self.tracker.update_income('nonexistent-id', amount=1000.0)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
