"""Forecast engine module for predicting future balance and cash flow."""

from typing import List, Dict, Optional
import pandas as pd
import yaml
import os
from datetime import datetime, timedelta


def load_transactions(transactions_file: str = "yaml/transactions.yaml") -> List[dict]:
    """Load transactions from YAML file."""
    if os.path.exists(transactions_file):
        with open(transactions_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
            return data.get('transactions', [])
    return []


def calculate_average_income_and_expenses(transactions: List[dict], days: int = 30) -> Dict[str, float]:
    """
    Calculate average daily income and expenses from historical data.
    
    Excludes internal transfers from calculations.
    
    Args:
        transactions: List of transaction dictionaries
        days: Number of days to look back (default: 30)
        
    Returns:
        Dictionary with avg_daily_income and avg_daily_expenses
    """
    if not transactions:
        return {'avg_daily_income': 0.0, 'avg_daily_expenses': 0.0}
    
    # Filter out internal transfers
    transactions = [tx for tx in transactions if not tx.get('is_internal_transfer', False)]
    
    if not transactions:
        return {'avg_daily_income': 0.0, 'avg_daily_expenses': 0.0}
    
    # Convert to DataFrame for easier processing
    df = pd.DataFrame(transactions)
    
    if 'date' not in df.columns or 'amount' not in df.columns:
        return {'avg_daily_income': 0.0, 'avg_daily_expenses': 0.0}
    
    # Convert date column to datetime
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    
    # Filter to last N days
    cutoff_date = datetime.now() - timedelta(days=days)
    df = df[df['date'] >= cutoff_date]
    
    if df.empty:
        return {'avg_daily_income': 0.0, 'avg_daily_expenses': 0.0}
    
    # Separate income and expenses
    income = df[df['amount'] > 0]['amount'].sum()
    expenses = abs(df[df['amount'] < 0]['amount'].sum())
    
    # Calculate daily averages
    num_days = (df['date'].max() - df['date'].min()).days + 1
    if num_days == 0:
        num_days = 1
    
    return {
        'avg_daily_income': income / num_days,
        'avg_daily_expenses': expenses / num_days
    }


def forecast_balance(current_balance: float, transactions: List[dict], forecast_days: int = 30, 
                    upcoming_bills: List[dict] = None, expected_income: List[dict] = None) -> List[Dict]:
    """
    Forecast balance for the next N days based on historical averages plus upcoming bills and income.
    
    Args:
        current_balance: Current account balance
        transactions: List of historical transactions
        forecast_days: Number of days to forecast (default: 30)
        upcoming_bills: List of upcoming bills with 'due_date' and 'amount'
        expected_income: List of expected income with 'date' and 'amount'
        
    Returns:
        List of dictionaries with date, predicted_balance, cumulative_income, and cumulative_expenses
    """
    # Calculate historical averages
    stats = calculate_average_income_and_expenses(transactions)
    avg_daily_income = stats['avg_daily_income']
    avg_daily_expenses = stats['avg_daily_expenses']
    avg_daily_net = avg_daily_income - avg_daily_expenses
    
    # Build a map of specific transactions by date
    upcoming_bills = upcoming_bills or []
    expected_income = expected_income or []
    
    date_adjustments = {}  # {date_str: {'income': amount, 'expense': amount}}
    
    # Add upcoming bills
    for bill in upcoming_bills:
        date_str = bill.get('due_date', '')
        if date_str:
            if date_str not in date_adjustments:
                date_adjustments[date_str] = {'income': 0, 'expense': 0}
            date_adjustments[date_str]['expense'] += bill.get('amount', 0)
    
    # Add expected income
    for income in expected_income:
        date_str = income.get('date', '')
        if date_str:
            if date_str not in date_adjustments:
                date_adjustments[date_str] = {'income': 0, 'expense': 0}
            date_adjustments[date_str]['income'] += income.get('amount', 0)
    
    # Generate forecast
    forecast = []
    balance = current_balance
    cumulative_income = 0
    cumulative_expenses = 0
    
    for day in range(forecast_days + 1):
        forecast_date = datetime.now() + timedelta(days=day)
        date_str = forecast_date.strftime('%Y-%m-%d')
        
        # Apply specific adjustments for this date
        day_income = avg_daily_income
        day_expense = avg_daily_expenses
        
        if date_str in date_adjustments:
            # Add specific bills/income on top of historical average
            day_income += date_adjustments[date_str]['income']
            day_expense += date_adjustments[date_str]['expense']
        
        forecast.append({
            'date': date_str,
            'predicted_balance': round(balance, 2),
            'cumulative_income': round(cumulative_income, 2),
            'cumulative_expenses': round(cumulative_expenses, 2),
            'day': day
        })
        
        # Update balance and cumulatives for next day
        day_net = day_income - day_expense
        balance += day_net
        cumulative_income += day_income
        cumulative_expenses += day_expense
    
    return forecast


def get_forecast_summary(current_balance: float, transactions_file: str = "yaml/transactions.yaml", 
                         forecast_days: int = 30, upcoming_bills: List[dict] = None, 
                         expected_income: List[dict] = None) -> Dict:
    """
    Get a complete forecast summary with statistics.
    
    Args:
        current_balance: Current account balance
        transactions_file: Path to transactions YAML file
        forecast_days: Number of days to forecast
        upcoming_bills: List of upcoming bills to include in forecast
        expected_income: List of expected income to include in forecast
        
    Returns:
        Dictionary with forecast data and statistics
    """
    transactions = load_transactions(transactions_file)
    stats = calculate_average_income_and_expenses(transactions)
    forecast = forecast_balance(current_balance, transactions, forecast_days, upcoming_bills, expected_income)
    
    # Calculate additional insights
    final_balance = forecast[-1]['predicted_balance'] if forecast else current_balance
    balance_change = final_balance - current_balance
    
    return {
        'current_balance': current_balance,
        'forecast_days': forecast_days,
        'avg_daily_income': round(stats['avg_daily_income'], 2),
        'avg_daily_expenses': round(stats['avg_daily_expenses'], 2),
        'avg_daily_net': round(stats['avg_daily_income'] - stats['avg_daily_expenses'], 2),
        'predicted_final_balance': round(final_balance, 2),
        'predicted_balance_change': round(balance_change, 2),
        'forecast': forecast,
        'warning': 'low_balance' if final_balance < 1000 else None
    }


def get_category_breakdown(transactions: List[dict] = None, transactions_file: str = "yaml/transactions.yaml") -> Dict[str, float]:
    """
    Get expense breakdown by category.
    
    Excludes internal transfers and credit card transactions.
    
    Args:
        transactions: List of transactions (optional, will load from file if not provided)
        transactions_file: Path to transactions YAML file
        
    Returns:
        Dictionary with category totals
    """
    if transactions is None:
        transactions = load_transactions(transactions_file)
    
    if not transactions:
        return {}
    
    # Filter out internal transfers
    transactions = [tx for tx in transactions if not tx.get('is_internal_transfer', False)]
    
    if not transactions:
        return {}
    
    # Convert to DataFrame
    df = pd.DataFrame(transactions)
    
    if 'amount' not in df.columns or 'category' not in df.columns:
        return {}
    
    # Filter to expenses only (negative amounts)
    expenses = df[df['amount'] < 0].copy()
    expenses['amount'] = abs(expenses['amount'])
    
    # Group by category
    category_totals = expenses.groupby('category')['amount'].sum().to_dict()
    
    # Round values
    return {k: round(v, 2) for k, v in category_totals.items()}
