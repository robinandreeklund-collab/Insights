"""Income Tracker - Registrerar och spårar inkomster per person och konto."""

import os
import yaml
import uuid
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict


class IncomeTracker:
    """Hanterar registrering och spårning av inkomster."""
    
    def __init__(self, yaml_dir: str = "yaml"):
        """Initialisera income tracker."""
        self.yaml_dir = yaml_dir
        self.income_file = os.path.join(yaml_dir, "income_tracker.yaml")
        
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
    
    def add_income(
        self,
        person: str,
        account: str,
        amount: float,
        date: str,
        description: str = "",
        category: str = "Lön"
    ) -> Dict:
        """Add a new income entry.
        
        Also creates a corresponding transaction in transactions.yaml so that
        the income is included in forecasts and analytics.
        
        Args:
            person: Person receiving the income
            account: Account where income is deposited
            amount: Income amount
            date: Date in YYYY-MM-DD format
            description: Optional description
            category: Income category (default: Lön)
            
        Returns:
            The created income entry
        """
        # Load existing data
        data = self._load_yaml(self.income_file)
        if 'incomes' not in data:
            data['incomes'] = []
        
        # Create income entry
        income_id = str(uuid.uuid4())
        income = {
            'id': income_id,
            'person': person,
            'account': account,
            'amount': float(amount),
            'date': date,
            'description': description,
            'category': category,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Add to data
        data['incomes'].append(income)
        
        # Save to income tracker
        self._save_yaml(self.income_file, data)
        
        # Also create a transaction for forecasting and analytics
        transactions_file = os.path.join(self.yaml_dir, "transactions.yaml")
        tx_data = self._load_yaml(transactions_file)
        if 'transactions' not in tx_data:
            tx_data['transactions'] = []
        
        # Create transaction with positive amount (income)
        transaction = {
            'id': f"income-{income_id}",
            'account': account,
            'date': date,
            'amount': float(amount),  # Positive for income
            'description': description or f"{category} - {person}",
            'category': category,
            'person': person,
            'is_income': True,
            'income_id': income_id
        }
        
        tx_data['transactions'].append(transaction)
        self._save_yaml(transactions_file, tx_data)
        
        return income
    
    def get_incomes(
        self,
        person: str = None,
        account: str = None,
        start_date: str = None,
        end_date: str = None
    ) -> List[Dict]:
        """Get incomes with optional filters.
        
        Args:
            person: Filter by person
            account: Filter by account
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            List of income entries
        """
        data = self._load_yaml(self.income_file)
        incomes = data.get('incomes', [])
        
        # Apply filters
        if person:
            incomes = [inc for inc in incomes if inc.get('person') == person]
        
        if account:
            incomes = [inc for inc in incomes if inc.get('account') == account]
        
        if start_date:
            incomes = [inc for inc in incomes if inc.get('date', '') >= start_date]
        
        if end_date:
            incomes = [inc for inc in incomes if inc.get('date', '') <= end_date]
        
        # Sort by date (newest first)
        incomes.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        return incomes
    
    def get_monthly_income(self, month: str = None, person: str = None) -> float:
        """Get total income for a month.
        
        Args:
            month: Month in YYYY-MM format. If None, uses current month.
            person: Optional person filter
            
        Returns:
            Total income for the month
        """
        if month is None:
            month = datetime.now().strftime('%Y-%m')
        
        incomes = self.get_incomes(person=person)
        
        # Filter by month
        monthly_incomes = [
            inc for inc in incomes
            if inc.get('date', '').startswith(month)
        ]
        
        total = sum(inc['amount'] for inc in monthly_incomes)
        return round(total, 2)
    
    def forecast_income(self, months: int = 3, person: str = None) -> List[Dict]:
        """Forecast future income based on historical data.
        
        Args:
            months: Number of months to forecast
            person: Optional person filter
            
        Returns:
            List of forecast data points
        """
        # Get historical data (last 6 months)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        
        incomes = self.get_incomes(
            person=person,
            start_date=start_date.strftime('%Y-%m-%d')
        )
        
        # Calculate average monthly income
        monthly_totals = defaultdict(float)
        for inc in incomes:
            month = inc.get('date', '')[:7]
            monthly_totals[month] += inc['amount']
        
        avg_income = 0
        if monthly_totals:
            avg_income = sum(monthly_totals.values()) / len(monthly_totals)
        
        # Generate forecast
        forecast = []
        for i in range(1, months + 1):
            forecast_date = end_date + timedelta(days=30*i)
            forecast.append({
                'month': forecast_date.strftime('%Y-%m'),
                'predicted_amount': round(avg_income, 2),
                'confidence': 'medium'
            })
        
        return forecast
    
    def get_income_by_person(self, start_date: str = None, end_date: str = None) -> Dict[str, float]:
        """Get income totals grouped by person.
        
        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dictionary mapping person to total income
        """
        incomes = self.get_incomes(start_date=start_date, end_date=end_date)
        
        person_totals = defaultdict(float)
        for inc in incomes:
            person = inc.get('person', 'Unknown')
            person_totals[person] += inc['amount']
        
        return dict(person_totals)
    
    def delete_income(self, income_id: str) -> bool:
        """Delete an income entry.
        
        Args:
            income_id: ID of the income to delete
            
        Returns:
            True if deleted, False if not found
        """
        data = self._load_yaml(self.income_file)
        incomes = data.get('incomes', [])
        
        # Find and remove income
        original_length = len(incomes)
        incomes = [inc for inc in incomes if inc.get('id') != income_id]
        
        if len(incomes) < original_length:
            data['incomes'] = incomes
            self._save_yaml(self.income_file, data)
            return True
        
        return False
    
    def update_income(self, income_id: str, **kwargs) -> Optional[Dict]:
        """Update an income entry.
        
        Args:
            income_id: ID of the income to update
            **kwargs: Fields to update
            
        Returns:
            Updated income entry or None if not found
        """
        data = self._load_yaml(self.income_file)
        incomes = data.get('incomes', [])
        
        # Find and update income
        for inc in incomes:
            if inc.get('id') == income_id:
                # Update fields
                for key, value in kwargs.items():
                    if key != 'id':  # Don't allow ID updates
                        inc[key] = value
                
                # Save
                self._save_yaml(self.income_file, data)
                return inc
        
        return None


def add_income(
    person: str,
    account: str,
    amount: float,
    date: str,
    description: str = "",
    category: str = "Lön",
    yaml_dir: str = "yaml"
) -> Dict:
    """Wrapper function to add income."""
    tracker = IncomeTracker(yaml_dir)
    return tracker.add_income(person, account, amount, date, description, category)


def get_monthly_income(month: str = None, person: str = None, yaml_dir: str = "yaml") -> float:
    """Wrapper function to get monthly income."""
    tracker = IncomeTracker(yaml_dir)
    return tracker.get_monthly_income(month, person)


def forecast_income(months: int = 3, person: str = None, yaml_dir: str = "yaml") -> List[Dict]:
    """Wrapper function to forecast income."""
    tracker = IncomeTracker(yaml_dir)
    return tracker.forecast_income(months, person)
