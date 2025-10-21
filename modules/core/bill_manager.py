"""Bill Manager - Hanterar fakturor och betalningar."""

import os
import yaml
from datetime import datetime
from typing import List, Dict, Optional


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
                 description: str = "", category: str = "Övrigt") -> Dict:
        """Lägg till en ny faktura.
        
        Args:
            name: Fakturanamn (t.ex. "Elräkning December")
            amount: Belopp i SEK
            due_date: Förfallodatum (YYYY-MM-DD)
            description: Beskrivning/detaljer
            category: Kategori för fakturan
            
        Returns:
            Den nya fakturan som dict
        """
        bills = self.load_bills()
        
        # Generera ID baserat på antal fakturor
        bill_id = f"BILL-{len(bills) + 1:04d}"
        
        bill = {
            'id': bill_id,
            'name': name,
            'amount': amount,
            'due_date': due_date,
            'description': description,
            'category': category,
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
        for bill in bills:
            if bill.get('status') == 'pending' and bill.get('due_date', '') < today:
                bill['status'] = 'overdue'
        
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
