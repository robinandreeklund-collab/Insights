"""Unit tests for forecast_engine module."""

import pytest
from datetime import datetime, timedelta
from modules.core.forecast_engine import (
    calculate_average_income_and_expenses,
    forecast_balance,
    get_forecast_summary,
    get_category_breakdown
)


class TestForecastEngine:
    """Test cases for forecast_engine module."""
    
    def test_calculate_average_income_and_expenses(self):
        """Test calculation of average income and expenses."""
        # Create sample transactions
        today = datetime.now()
        transactions = [
            {'date': today.strftime('%Y-%m-%d'), 'amount': -100.0},
            {'date': (today - timedelta(days=1)).strftime('%Y-%m-%d'), 'amount': -50.0},
            {'date': (today - timedelta(days=2)).strftime('%Y-%m-%d'), 'amount': 500.0},  # Income
        ]
        
        result = calculate_average_income_and_expenses(transactions, days=30)
        
        assert 'avg_daily_income' in result
        assert 'avg_daily_expenses' in result
        assert result['avg_daily_income'] > 0
        assert result['avg_daily_expenses'] > 0
    
    def test_calculate_average_empty_transactions(self):
        """Test with empty transaction list."""
        result = calculate_average_income_and_expenses([], days=30)
        
        assert result['avg_daily_income'] == 0.0
        assert result['avg_daily_expenses'] == 0.0
    
    def test_forecast_balance(self):
        """Test balance forecasting."""
        # Create sample transactions with known pattern
        today = datetime.now()
        transactions = [
            {'date': (today - timedelta(days=i)).strftime('%Y-%m-%d'), 'amount': -10.0}
            for i in range(10)
        ]
        
        forecast = forecast_balance(1000.0, transactions, forecast_days=7)
        
        # Check structure
        assert len(forecast) == 8  # Today + 7 future days
        assert 'date' in forecast[0]
        assert 'predicted_balance' in forecast[0]
        assert 'day' in forecast[0]
        
        # Balance should decrease over time (since we only have expenses)
        assert forecast[0]['predicted_balance'] == 1000.0  # Current balance
        assert forecast[-1]['predicted_balance'] < forecast[0]['predicted_balance']
    
    def test_forecast_with_mixed_transactions(self):
        """Test forecast with both income and expenses."""
        today = datetime.now()
        transactions = [
            {'date': (today - timedelta(days=i)).strftime('%Y-%m-%d'), 'amount': -50.0}
            for i in range(10)
        ] + [
            {'date': (today - timedelta(days=5)).strftime('%Y-%m-%d'), 'amount': 1000.0}  # Big income
        ]
        
        forecast = forecast_balance(500.0, transactions, forecast_days=5)
        
        assert len(forecast) == 6
        # With income, balance might stay stable or grow
        assert forecast[0]['predicted_balance'] == 500.0
    
    def test_get_forecast_summary(self):
        """Test getting complete forecast summary."""
        today = datetime.now()
        transactions = [
            {'date': (today - timedelta(days=i)).strftime('%Y-%m-%d'), 'amount': -30.0}
            for i in range(5)
        ]
        
        # Save transactions to a temp file for testing
        import tempfile
        import yaml
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_file = f.name
            yaml.dump({'transactions': transactions}, f)
        
        try:
            summary = get_forecast_summary(1000.0, temp_file, forecast_days=7)
            
            # Check structure
            assert 'current_balance' in summary
            assert 'forecast_days' in summary
            assert 'avg_daily_income' in summary
            assert 'avg_daily_expenses' in summary
            assert 'avg_daily_net' in summary
            assert 'predicted_final_balance' in summary
            assert 'predicted_balance_change' in summary
            assert 'forecast' in summary
            
            # Check values
            assert summary['current_balance'] == 1000.0
            assert summary['forecast_days'] == 7
            assert len(summary['forecast']) == 8
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_get_category_breakdown(self):
        """Test category breakdown calculation."""
        transactions = [
            {'amount': -100.0, 'category': 'Mat & Dryck'},
            {'amount': -50.0, 'category': 'Mat & Dryck'},
            {'amount': -200.0, 'category': 'Transport'},
            {'amount': 500.0, 'category': 'Inkomster'},  # Should be ignored (positive)
        ]
        
        breakdown = get_category_breakdown(transactions)
        
        assert 'Mat & Dryck' in breakdown
        assert 'Transport' in breakdown
        assert breakdown['Mat & Dryck'] == 150.0  # 100 + 50
        assert breakdown['Transport'] == 200.0
        # Income should not be in breakdown (only expenses)
        assert 'Inkomster' not in breakdown or breakdown['Inkomster'] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
