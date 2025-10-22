"""Bill Manager - Hanterar fakturor och betalningar."""

import os
import yaml
import re
from datetime import datetime
from typing import List, Dict, Optional


def normalize_account_number(account: str) -> Optional[str]:
    """Normalize account number from various formats.
    
    Extracts and normalizes patterns like "1722 20 34439" or "MAT 1722 20 34439".
    
    Args:
        account: Account string (may be full name or just number)
        
    Returns:
        Normalized account number with spaces, or original if no pattern found
    """
    if not account:
        return None
    
    # Pattern: 4 digits, optional space, 2 digits, optional space, 5 digits
    pattern = r'\b(\d{4})\s*(\d{2})\s*(\d{5})\b'
    match = re.search(pattern, account)
    
    if match:
        # Return normalized format with spaces
        return f"{match.group(1)} {match.group(2)} {match.group(3)}"
    
    # If no pattern found, return the original (might be a non-standard account)
    return account


class BillManager:
    """Hanterar fakturor, betalningsstatus och schemalagda betalningar."""
    
    def __init__(self, yaml_dir: str = "yaml"):
        """Initialisera bill manager med YAML-katalog."""
        self.yaml_dir = yaml_dir
        self.bills_file = os.path.join(yaml_dir, "bills.yaml")
        self._ensure_bills_file()
    
    def _ensure_bills_file(self):
        """Se till att bills.yaml finns."""
        if not os.path.exists(self.bills_file):
            os.makedirs(self.yaml_dir, exist_ok=True)
            with open(self.bills_file, 'w', encoding='utf-8') as f:
                yaml.dump({'bills': []}, f, default_flow_style=False, allow_unicode=True)
    
    def load_bills(self) -> List[Dict]:
        """Ladda alla fakturor från YAML."""
        self._ensure_bills_file()
        with open(self.bills_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
            return data.get('bills', [])
    
    def save_bills(self, bills: List[Dict]):
        """Spara fakturor till YAML."""
        with open(self.bills_file, 'w', encoding='utf-8') as f:
            yaml.dump({'bills': bills}, f, default_flow_style=False, allow_unicode=True)
    
    def add_bill(self, name: str, amount: float, due_date: str, 
                 description: str = "", category: str = "Övrigt", 
                 subcategory: str = "", account: str = None) -> Dict:
        """Lägg till en ny faktura.
        
        Args:
            name: Fakturanamn (t.ex. "Elräkning December")
            amount: Belopp i SEK
            due_date: Förfallodatum (YYYY-MM-DD)
            description: Beskrivning/detaljer
            category: Kategori för fakturan
            subcategory: Underkategori för fakturan (valfritt)
            account: Kontonummer som fakturan ska belasta (valfritt)
            
        Returns:
            Den nya fakturan som dict
        """
        bills = self.load_bills()
        
        # Generera ID baserat på antal fakturor
        bill_id = f"BILL-{len(bills) + 1:04d}"
        
        # Normalize account number if provided
        normalized_account = normalize_account_number(account) if account else None
        
        bill = {
            'id': bill_id,
            'name': name,
            'amount': amount,
            'due_date': due_date,
            'description': description,
            'category': category,
            'subcategory': subcategory,  # Added subcategory field
            'account': normalized_account,  # Store normalized account number
            'status': 'pending',  # pending, paid, overdue
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'paid_at': None,
            'matched_transaction_id': None,
            'scheduled_payment_date': None
        }
        
        bills.append(bill)
        self.save_bills(bills)
        return bill
    
    def get_bills(self, status: Optional[str] = None) -> List[Dict]:
        """Hämta fakturor, filtrerat på status om angivet.
        
        Args:
            status: 'pending', 'paid', 'overdue', eller None för alla
            
        Returns:
            Lista med fakturor
        """
        bills = self.load_bills()
        
        if status:
            bills = [b for b in bills if b.get('status') == status]
        
        # Uppdatera status för förfallna fakturor
        today = datetime.now().strftime('%Y-%m-%d')
        status_changed = False
        for bill in bills:
            if bill.get('status') == 'pending' and bill.get('due_date', '') < today:
                bill['status'] = 'overdue'
                status_changed = True
        
        if status_changed:
            self.save_bills(bills)
        
        return bills
    
    def get_bill_by_id(self, bill_id: str) -> Optional[Dict]:
        """Hämta en faktura med ID."""
        bills = self.load_bills()
        for bill in bills:
            if bill.get('id') == bill_id:
                return bill
        return None
    
    def update_bill(self, bill_id: str, updates: Dict) -> bool:
        """Uppdatera en faktura.
        
        Args:
            bill_id: ID för fakturan som ska uppdateras
            updates: Dict med fält att uppdatera
            
        Returns:
            True om uppdatering lyckades, annars False
        """
        bills = self.load_bills()
        
        for i, bill in enumerate(bills):
            if bill.get('id') == bill_id:
                bills[i].update(updates)
                self.save_bills(bills)
                return True
        
        return False
    
    def delete_bill(self, bill_id: str) -> bool:
        """Ta bort en faktura.
        
        Args:
            bill_id: ID för fakturan som ska tas bort
            
        Returns:
            True om borttagning lyckades, annars False
        """
        bills = self.load_bills()
        initial_count = len(bills)
        bills = [b for b in bills if b.get('id') != bill_id]
        
        if len(bills) < initial_count:
            self.save_bills(bills)
            return True
        
        return False
    
    def mark_as_paid(self, bill_id: str, transaction_id: Optional[str] = None) -> bool:
        """Markera faktura som betald.
        
        Args:
            bill_id: ID för fakturan
            transaction_id: ID för matchad transaktion (om matchning skett)
            
        Returns:
            True om uppdatering lyckades
        """
        updates = {
            'status': 'paid',
            'paid_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if transaction_id:
            updates['matched_transaction_id'] = transaction_id
        
        return self.update_bill(bill_id, updates)
    
    def schedule_payment(self, bill_id: str, payment_date: str) -> bool:
        """Schemalägg betalning för en faktura.
        
        Args:
            bill_id: ID för fakturan
            payment_date: Datum för schemalagd betalning (YYYY-MM-DD)
            
        Returns:
            True om schemaläggning lyckades
        """
        return self.update_bill(bill_id, {'scheduled_payment_date': payment_date})
    
    def get_upcoming_bills(self, days: int = 30) -> List[Dict]:
        """Hämta kommande fakturor inom X dagar.
        
        Args:
            days: Antal dagar framåt att visa
            
        Returns:
            Lista med kommande fakturor
        """
        from datetime import timedelta
        
        bills = self.get_bills(status='pending')
        today = datetime.now()
        future_date = today + timedelta(days=days)
        
        upcoming = []
        for bill in bills:
            due_date_str = bill.get('due_date', '')
            if due_date_str:
                try:
                    due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
                    if today <= due_date <= future_date:
                        upcoming.append(bill)
                except ValueError:
                    pass
        
        # Sortera på förfallodatum
        upcoming.sort(key=lambda x: x.get('due_date', ''))
        
        return upcoming
    
    def get_bills_by_account(self) -> Dict[str, List[Dict]]:
        """Gruppera fakturor per konto.
        
        Returns:
            Dict med kontonummer som nycklar och listor med fakturor som värden
        """
        from collections import defaultdict
        
        bills = self.get_bills()
        bills_by_account = defaultdict(list)
        
        for bill in bills:
            account = bill.get('account', 'Inget konto angivet')
            bills_by_account[account].append(bill)
        
        return dict(bills_by_account)
    
    def get_account_summary(self) -> List[Dict]:
        """Få sammanfattning av fakturor per konto.
        
        Returns:
            Lista med sammanfattningar för varje konto
        """
        bills_by_account = self.get_bills_by_account()
        summaries = []
        
        for account, account_bills in bills_by_account.items():
            total_amount = sum(bill['amount'] for bill in account_bills)
            pending_bills = [b for b in account_bills if b.get('status') == 'pending']
            
            summaries.append({
                'account': account,
                'bill_count': len(account_bills),
                'pending_count': len(pending_bills),
                'total_amount': total_amount,
                'bills': account_bills
            })
        
        # Sort by account number
        summaries.sort(key=lambda x: x['account'])
        
        return summaries
