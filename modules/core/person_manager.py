"""Person Manager - Hantera familjemedlemmar och deras inkomster."""

import os
import yaml
import uuid
from typing import List, Dict, Optional
from datetime import datetime
from collections import defaultdict


class PersonManager:
    """Hanterar personer, deras inkomster och utgifter."""
    
    def __init__(self, yaml_dir: str = "yaml"):
        """Initialisera person manager."""
        self.yaml_dir = yaml_dir
        self.persons_file = os.path.join(yaml_dir, "persons.yaml")
        self.income_file = os.path.join(yaml_dir, "income_tracker.yaml")
        self.transactions_file = os.path.join(yaml_dir, "transactions.yaml")
        self.credit_cards_file = os.path.join(yaml_dir, "credit_cards.yaml")
        
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
    
    def add_person(
        self,
        name: str,
        monthly_income: float = 0.0,
        payment_day: int = 25,
        description: str = ""
    ) -> Dict:
        """Add a new person.
        
        Args:
            name: Person's name
            monthly_income: Expected monthly recurring income
            payment_day: Day of month when income is typically received
            description: Optional description
            
        Returns:
            The created person entry
        """
        data = self._load_yaml(self.persons_file)
        if 'persons' not in data:
            data['persons'] = []
        
        # Check if person already exists
        for person in data['persons']:
            if person['name'].lower() == name.lower():
                raise ValueError(f"Person '{name}' finns redan")
        
        person = {
            'id': str(uuid.uuid4()),
            'name': name,
            'monthly_income': float(monthly_income),
            'payment_day': int(payment_day),
            'description': description,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        data['persons'].append(person)
        self._save_yaml(self.persons_file, data)
        
        return person
    
    def get_persons(self) -> List[Dict]:
        """Get all persons."""
        data = self._load_yaml(self.persons_file)
        return data.get('persons', [])
    
    def get_person_by_id(self, person_id: str) -> Optional[Dict]:
        """Get person by ID."""
        persons = self.get_persons()
        for person in persons:
            if person.get('id') == person_id:
                return person
        return None
    
    def get_person_by_name(self, name: str) -> Optional[Dict]:
        """Get person by name."""
        persons = self.get_persons()
        for person in persons:
            if person.get('name', '').lower() == name.lower():
                return person
        return None
    
    def update_person(
        self,
        person_id: str,
        name: str = None,
        monthly_income: float = None,
        payment_day: int = None,
        description: str = None
    ) -> Dict:
        """Update a person's information."""
        data = self._load_yaml(self.persons_file)
        persons = data.get('persons', [])
        
        for person in persons:
            if person.get('id') == person_id:
                if name is not None:
                    person['name'] = name
                if monthly_income is not None:
                    person['monthly_income'] = float(monthly_income)
                if payment_day is not None:
                    person['payment_day'] = int(payment_day)
                if description is not None:
                    person['description'] = description
                
                person['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self._save_yaml(self.persons_file, data)
                return person
        
        raise ValueError(f"Person med ID '{person_id}' hittades inte")
    
    def delete_person(self, person_id: str) -> bool:
        """Delete a person."""
        data = self._load_yaml(self.persons_file)
        persons = data.get('persons', [])
        
        original_count = len(persons)
        data['persons'] = [p for p in persons if p.get('id') != person_id]
        
        if len(data['persons']) < original_count:
            self._save_yaml(self.persons_file, data)
            return True
        return False
    
    def get_income_history(self, person_name: str, months: int = 6) -> List[Dict]:
        """Get income history for a person over time.
        
        Args:
            person_name: Name of the person
            months: Number of months to look back
            
        Returns:
            List of monthly income data
        """
        income_data = self._load_yaml(self.income_file)
        incomes = income_data.get('incomes', [])
        
        # Filter by person
        person_incomes = [
            inc for inc in incomes 
            if inc.get('person', '').lower() == person_name.lower()
        ]
        
        # Group by month
        monthly_totals = defaultdict(float)
        for inc in person_incomes:
            date = inc.get('date', '')
            if date:
                month = date[:7]  # YYYY-MM
                monthly_totals[month] += inc.get('amount', 0)
        
        # Convert to sorted list
        result = []
        for month in sorted(monthly_totals.keys(), reverse=True)[:months]:
            result.append({
                'month': month,
                'amount': round(monthly_totals[month], 2)
            })
        
        return list(reversed(result))  # Oldest first
    
    def get_person_spending_by_category(self, person_name: str, months: int = 6) -> Dict[str, float]:
        """Get spending breakdown by category for a person.
        
        Uses credit card allocations to determine per-person spending.
        
        Args:
            person_name: Name of the person
            months: Number of months to look back
            
        Returns:
            Dictionary mapping category to total amount spent
        """
        from datetime import datetime, timedelta
        
        # Load credit card data
        cc_data = self._load_yaml(self.credit_cards_file)
        cards = cc_data.get('credit_cards', [])
        
        # Calculate cutoff date
        cutoff_date = (datetime.now() - timedelta(days=30*months)).strftime('%Y-%m-%d')
        
        # Aggregate spending by category
        category_totals = defaultdict(float)
        
        for card in cards:
            transactions = card.get('transactions', [])
            
            # Get allocation for this person (default to 100% if only one person)
            allocations = card.get('allocations', {})
            person_allocation = allocations.get(person_name, 1.0 if len(allocations) == 0 else 0.0)
            
            # Sum transactions by category
            for tx in transactions:
                if tx.get('date', '') >= cutoff_date:
                    category = tx.get('category', 'Okategoriserat')
                    amount = abs(tx.get('amount', 0))
                    
                    # Apply allocation
                    category_totals[category] += amount * person_allocation
        
        # Round values
        return {cat: round(amt, 2) for cat, amt in category_totals.items()}
    
    def update_expected_payout(
        self,
        person_name: str,
        month: str,
        expected_amount: float
    ) -> Dict:
        """Update expected payout for a specific month.
        
        Args:
            person_name: Name of the person
            month: Month in YYYY-MM format
            expected_amount: Expected income for that month
            
        Returns:
            Updated expected payout entry
        """
        data = self._load_yaml(self.persons_file)
        persons = data.get('persons', [])
        
        # Find person
        person = None
        for p in persons:
            if p.get('name', '').lower() == person_name.lower():
                person = p
                break
        
        if not person:
            raise ValueError(f"Person '{person_name}' hittades inte")
        
        # Initialize expected_payouts if not exists
        if 'expected_payouts' not in person:
            person['expected_payouts'] = {}
        
        # Update expected payout
        person['expected_payouts'][month] = float(expected_amount)
        
        self._save_yaml(self.persons_file, data)
        
        return {
            'person': person_name,
            'month': month,
            'expected_amount': expected_amount
        }
    
    def get_expected_payout(self, person_name: str, month: str) -> Optional[float]:
        """Get expected payout for a person in a specific month."""
        person = self.get_person_by_name(person_name)
        if person:
            expected_payouts = person.get('expected_payouts', {})
            return expected_payouts.get(month)
        return None
