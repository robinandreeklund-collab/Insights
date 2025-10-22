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
        Normalized account number with spaces, original string if no pattern found, or None if account is empty
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
                 subcategory: str = "", account: str = None,
                 is_bill: bool = True, source: str = None,
                 is_amex_bill: bool = False) -> Dict:
        """Lägg till en ny faktura.
        
        Args:
            name: Fakturanamn (t.ex. "Elräkning December")
            amount: Belopp i SEK
            due_date: Förfallodatum (YYYY-MM-DD)
            description: Beskrivning/detaljer
            category: Kategori för fakturan
            subcategory: Underkategori för fakturan (valfritt)
            account: Kontonummer som fakturan ska belasta (valfritt)
            is_bill: True for bill entries (default), False for other scheduled items
            source: Source of the bill (e.g., 'PDF', 'manual', filename)
            is_amex_bill: True if this is an Amex bill that will have line items
            
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
            'bill_due_date': due_date,  # Explicit field for due date
            'description': description,
            'category': category,
            'subcategory': subcategory,
            'account': normalized_account,
            'account_number': normalized_account,  # Explicit field for matching
            'status': 'scheduled',  # scheduled, posted, paid, overdue
            'is_bill': is_bill,
            'source': source or 'manual',
            'source_uploaded_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'paid_at': None,
            'matched_transaction_id': None,
            'matched_to_bill_id': None,  # For reverse matching
            'scheduled_payment_date': None,
            'imported_historical': False,  # Bills are future items
            'is_amex_bill': is_amex_bill,  # Flag for Amex bills
            'line_items': []  # Initialize empty line items array
        }
        
        bills.append(bill)
        self.save_bills(bills)
        return bill
    
    def get_bills(self, status: Optional[str] = None) -> List[Dict]:
        """Hämta fakturor, filtrerat på status om angivet.
        
        Args:
            status: 'scheduled', 'pending', 'posted', 'paid', 'overdue', eller None för alla
            
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
            # Update both 'pending' and 'scheduled' to 'overdue' if past due
            if bill.get('status') in ['pending', 'scheduled'] and bill.get('due_date', '') < today:
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
        
        # Get all bills that are not yet paid (pending, scheduled, or overdue)
        bills = self.get_bills()
        bills = [b for b in bills if b.get('status') in ['pending', 'scheduled', 'overdue']]
        
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
            # Count both 'pending' and 'scheduled' as unpaid
            pending_bills = [b for b in account_bills if b.get('status') in ['pending', 'scheduled']]
            
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
    
    # ===== LINE ITEMS MANAGEMENT FOR AMEX WORKFLOW =====
    
    def add_line_item(self, bill_id: str, vendor: str, description: str, 
                     amount: float, date: str, category: str = "Övrigt",
                     subcategory: str = "") -> Optional[Dict]:
        """Add a line item to an Amex bill.
        
        Args:
            bill_id: ID of the bill to add line item to
            vendor: Vendor/merchant name
            description: Line item description
            amount: Line item amount
            date: Transaction date (YYYY-MM-DD)
            category: Category for the line item
            subcategory: Subcategory for the line item
            
        Returns:
            The created line item dict, or None if bill not found
        """
        bills = self.load_bills()
        
        for bill in bills:
            if bill.get('id') == bill_id:
                # Ensure line_items array exists
                if 'line_items' not in bill:
                    bill['line_items'] = []
                
                # Generate line item ID
                line_item_id = f"LINE-{len(bill['line_items']) + 1:04d}"
                
                line_item = {
                    'id': line_item_id,
                    'date': date,
                    'vendor': vendor,
                    'description': description,
                    'amount': amount,
                    'category': category,
                    'subcategory': subcategory,
                    'is_historical_record': True,  # Always historical for Amex line items
                    'affects_cash': False,  # Does not affect cash flow (bill total does)
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                bill['line_items'].append(line_item)
                self.save_bills(bills)
                return line_item
        
        return None
    
    def update_line_item(self, bill_id: str, line_item_id: str, updates: Dict) -> bool:
        """Update a line item within a bill.
        
        Args:
            bill_id: ID of the bill containing the line item
            line_item_id: ID of the line item to update
            updates: Dict with fields to update
            
        Returns:
            True if update succeeded, False otherwise
        """
        bills = self.load_bills()
        
        for bill in bills:
            if bill.get('id') == bill_id:
                line_items = bill.get('line_items', [])
                for i, item in enumerate(line_items):
                    if item.get('id') == line_item_id:
                        # Update the line item
                        bill['line_items'][i].update(updates)
                        self.save_bills(bills)
                        return True
        
        return False
    
    def delete_line_item(self, bill_id: str, line_item_id: str) -> bool:
        """Delete a line item from a bill.
        
        Args:
            bill_id: ID of the bill containing the line item
            line_item_id: ID of the line item to delete
            
        Returns:
            True if deletion succeeded, False otherwise
        """
        bills = self.load_bills()
        
        for bill in bills:
            if bill.get('id') == bill_id:
                line_items = bill.get('line_items', [])
                initial_count = len(line_items)
                bill['line_items'] = [item for item in line_items 
                                     if item.get('id') != line_item_id]
                
                if len(bill['line_items']) < initial_count:
                    self.save_bills(bills)
                    return True
        
        return False
    
    def get_line_items(self, bill_id: str) -> List[Dict]:
        """Get all line items for a bill.
        
        Args:
            bill_id: ID of the bill
            
        Returns:
            List of line items
        """
        bill = self.get_bill_by_id(bill_id)
        if bill:
            return bill.get('line_items', [])
        return []
    
    def import_line_items_from_csv(self, bill_id: str, line_items: List[Dict]) -> bool:
        """Import multiple line items from CSV data.
        
        Args:
            bill_id: ID of the bill to add line items to
            line_items: List of dicts with line item data (vendor, description, amount, date, etc.)
            
        Returns:
            True if import succeeded, False otherwise
        """
        bills = self.load_bills()
        
        for bill in bills:
            if bill.get('id') == bill_id:
                # Ensure line_items array exists
                if 'line_items' not in bill:
                    bill['line_items'] = []
                
                # Add each line item
                for idx, item_data in enumerate(line_items):
                    line_item_id = f"LINE-{len(bill['line_items']) + 1:04d}"
                    
                    line_item = {
                        'id': line_item_id,
                        'date': item_data.get('date', ''),
                        'vendor': item_data.get('vendor', ''),
                        'description': item_data.get('description', ''),
                        'amount': item_data.get('amount', 0.0),
                        'category': item_data.get('category', 'Övrigt'),
                        'subcategory': item_data.get('subcategory', ''),
                        'is_historical_record': True,
                        'affects_cash': False,
                        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    bill['line_items'].append(line_item)
                
                self.save_bills(bills)
                return True
        
        return False
    
    def get_all_line_items(self, category: Optional[str] = None,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> List[Dict]:
        """Get all line items across all bills with optional filtering.
        
        Useful for creating a pseudo-account view of all Amex transactions.
        
        Args:
            category: Filter by category (optional)
            start_date: Filter by start date (YYYY-MM-DD, optional)
            end_date: Filter by end date (YYYY-MM-DD, optional)
            
        Returns:
            List of all line items with bill context
        """
        bills = self.load_bills()
        all_items = []
        
        for bill in bills:
            line_items = bill.get('line_items', [])
            for item in line_items:
                # Add bill context to each line item
                item_with_context = item.copy()
                item_with_context['bill_id'] = bill.get('id')
                item_with_context['bill_name'] = bill.get('name')
                item_with_context['bill_account'] = bill.get('account')
                
                # Apply filters
                if category and item.get('category') != category:
                    continue
                
                item_date = item.get('date', '')
                if start_date and item_date < start_date:
                    continue
                if end_date and item_date > end_date:
                    continue
                
                all_items.append(item_with_context)
        
        # Sort by date
        all_items.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        return all_items
