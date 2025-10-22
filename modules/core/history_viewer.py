"""History Viewer - Visar historisk utgiftsdata, trender och insikter."""

import os
import yaml
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict


class HistoryViewer:
    """Hanterar historisk data, trender och statistik."""
    
    def __init__(self, yaml_dir: str = "yaml"):
        """Initialisera history viewer."""
        self.yaml_dir = yaml_dir
        self.transactions_file = os.path.join(yaml_dir, "transactions.yaml")
        self.accounts_file = os.path.join(yaml_dir, "accounts.yaml")
        self.history_file = os.path.join(yaml_dir, "history.yaml")
        
        # Ensure yaml directory exists
        os.makedirs(yaml_dir, exist_ok=True)
    
    def _load_yaml(self, filepath: str) -> dict:
        """Load YAML file or return default structure."""
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                return data
        return {}
    
    def _load_transactions(self) -> List[Dict]:
        """Load all transactions."""
        data = self._load_yaml(self.transactions_file)
        return data.get('transactions', [])
    
    def get_monthly_summary(self, month: str = None) -> Dict:
        """Get monthly summary of income and expenses.
        
        Args:
            month: Month in format 'YYYY-MM'. If None, uses current month.
            
        Returns:
            Dictionary with monthly summary
        """
        if month is None:
            month = datetime.now().strftime('%Y-%m')
        
        transactions = self._load_transactions()
        
        # Filter transactions for the month
        monthly_txs = [
            tx for tx in transactions
            if tx.get('date', '').startswith(month)
        ]
        
        # Calculate totals
        income = sum(tx['amount'] for tx in monthly_txs if tx['amount'] > 0)
        expenses = sum(abs(tx['amount']) for tx in monthly_txs if tx['amount'] < 0)
        net = income - expenses
        
        # Count transactions
        income_count = len([tx for tx in monthly_txs if tx['amount'] > 0])
        expense_count = len([tx for tx in monthly_txs if tx['amount'] < 0])
        
        # Category breakdown for expenses
        category_breakdown = defaultdict(float)
        for tx in monthly_txs:
            if tx['amount'] < 0:
                category = tx.get('category', 'Okategoriserat')
                category_breakdown[category] += abs(tx['amount'])
        
        return {
            'month': month,
            'income': round(income, 2),
            'expenses': round(expenses, 2),
            'net': round(net, 2),
            'income_count': income_count,
            'expense_count': expense_count,
            'total_transactions': len(monthly_txs),
            'category_breakdown': dict(category_breakdown)
        }
    
    def get_category_trend(self, category: str, months: int = 6) -> List[Dict]:
        """Get category spending trend over time.
        
        Args:
            category: Category name to analyze
            months: Number of months to look back
            
        Returns:
            List of monthly data points
        """
        transactions = self._load_transactions()
        
        # Generate month list
        end_date = datetime.now()
        month_list = []
        for i in range(months):
            month_date = end_date - timedelta(days=30*i)
            month_str = month_date.strftime('%Y-%m')
            month_list.append(month_str)
        month_list.reverse()
        
        # Calculate spending per month
        trend_data = []
        for month in month_list:
            monthly_txs = [
                tx for tx in transactions
                if tx.get('date', '').startswith(month) and
                   tx.get('category') == category and
                   tx['amount'] < 0
            ]
            total = sum(abs(tx['amount']) for tx in monthly_txs)
            trend_data.append({
                'month': month,
                'amount': round(total, 2),
                'count': len(monthly_txs)
            })
        
        return trend_data
    
    def get_account_balance_history(self, account: str = None) -> List[Dict]:
        """Get account balance history over time.
        
        Args:
            account: Account name. If None, returns total for all accounts.
            
        Returns:
            List of balance data points over time
        """
        transactions = self._load_transactions()
        
        # Filter by account if specified
        if account:
            transactions = [tx for tx in transactions if tx.get('account') == account]
        
        # Sort by date
        sorted_txs = sorted(transactions, key=lambda x: x.get('date', ''))
        
        # Calculate running balance
        balance = 0
        history = []
        for tx in sorted_txs:
            balance += tx['amount']
            history.append({
                'date': tx.get('date'),
                'balance': round(balance, 2),
                'transaction_id': tx.get('id')
            })
        
        return history
    
    def get_top_expenses(self, month: str = None, top_n: int = 10) -> List[Dict]:
        """Get top N expenses for a given month.
        
        Args:
            month: Month in format 'YYYY-MM'. If None, uses current month.
            top_n: Number of top expenses to return
            
        Returns:
            List of top expenses
        """
        if month is None:
            month = datetime.now().strftime('%Y-%m')
        
        transactions = self._load_transactions()
        
        # Filter transactions for the month (expenses only)
        monthly_expenses = [
            tx for tx in transactions
            if tx.get('date', '').startswith(month) and tx['amount'] < 0
        ]
        
        # Sort by amount (absolute value)
        sorted_expenses = sorted(
            monthly_expenses,
            key=lambda x: abs(x['amount']),
            reverse=True
        )
        
        # Return top N
        return sorted_expenses[:top_n]
    
    def get_all_months(self) -> List[str]:
        """Get list of all months that have transactions.
        
        Returns:
            List of month strings in YYYY-MM format
        """
        transactions = self._load_transactions()
        
        months = set()
        for tx in transactions:
            date = tx.get('date', '')
            if date:
                month = date[:7]  # YYYY-MM
                months.add(month)
        
        return sorted(list(months), reverse=True)


def get_monthly_summary(month: str = None, yaml_dir: str = "yaml") -> Dict:
    """Wrapper function to get monthly summary."""
    viewer = HistoryViewer(yaml_dir)
    return viewer.get_monthly_summary(month)


def get_category_trend(category: str, months: int = 6, yaml_dir: str = "yaml") -> List[Dict]:
    """Wrapper function to get category trend."""
    viewer = HistoryViewer(yaml_dir)
    return viewer.get_category_trend(category, months)


def get_account_balance_history(account: str = None, yaml_dir: str = "yaml") -> List[Dict]:
    """Wrapper function to get account balance history."""
    viewer = HistoryViewer(yaml_dir)
    return viewer.get_account_balance_history(account)


def get_top_expenses(month: str = None, top_n: int = 10, yaml_dir: str = "yaml") -> List[Dict]:
    """Wrapper function to get top expenses."""
    viewer = HistoryViewer(yaml_dir)
    return viewer.get_top_expenses(month, top_n)
