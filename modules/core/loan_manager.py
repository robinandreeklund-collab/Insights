"""Loan Manager - Hanterar lån, räntor och återbetalning."""

import os
import yaml
from datetime import datetime
from typing import List, Dict, Optional


class LoanManager:
    """Hanterar lån, ränteberäkningar och återbetalningssimulering."""
    
    def __init__(self, yaml_dir: str = "yaml"):
        """Initialisera loan manager med YAML-katalog."""
        self.yaml_dir = yaml_dir
        self.loans_file = os.path.join(yaml_dir, "loans.yaml")
        self._ensure_loans_file()
    
    def _ensure_loans_file(self):
        """Se till att loans.yaml finns."""
        if not os.path.exists(self.loans_file):
            os.makedirs(self.yaml_dir, exist_ok=True)
            with open(self.loans_file, 'w', encoding='utf-8') as f:
                yaml.dump({'loans': []}, f, default_flow_style=False, allow_unicode=True)
    
    def load_loans(self) -> List[Dict]:
        """Ladda alla lån från YAML."""
        self._ensure_loans_file()
        with open(self.loans_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
            return data.get('loans', [])
    
    def save_loans(self, loans: List[Dict]):
        """Spara lån till YAML."""
        with open(self.loans_file, 'w', encoding='utf-8') as f:
            yaml.dump({'loans': loans}, f, default_flow_style=False, allow_unicode=True)
    
    def add_loan(self, name: str, principal: float, interest_rate: float,
                 start_date: str, term_months: int = 360, 
                 fixed_rate_end_date: Optional[str] = None,
                 description: str = "",
                 **kwargs) -> Dict:
        """Lägg till ett nytt lån.
        
        Args:
            name: Lånets namn (t.ex. "Bolån")
            principal: Huvudbelopp (ursprungligt lån)
            interest_rate: Årsränta i procent (t.ex. 3.5 för 3.5%)
            start_date: Startdatum (YYYY-MM-DD)
            term_months: Löptid i månader (default 360 = 30 år)
            fixed_rate_end_date: Datum när bindningstiden slutar (YYYY-MM-DD)
            description: Beskrivning/detaljer
            **kwargs: Additional loan fields (loan_number, amortized, base_rate, etc.)
            
        Returns:
            Det nya lånet som dict
        """
        loans = self.load_loans()
        
        # Generera ID baserat på antal lån
        loan_id = f"LOAN-{len(loans) + 1:04d}"
        
        loan = {
            'id': loan_id,
            'name': name,
            'principal': principal,
            'current_balance': principal,
            'interest_rate': interest_rate,
            'start_date': start_date,
            'term_months': term_months,
            'fixed_rate_end_date': fixed_rate_end_date,
            'description': description,
            'status': 'active',  # active, paid_off, closed
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'payments': [],  # Lista med återbetalningar
            'interest_payments': []  # Lista med räntebetalningar
        }
        
        # Add extended fields from OCR or manual input
        extended_fields = [
            'loan_number', 'original_amount', 'current_amount', 'amortized',
            'base_interest_rate', 'discount', 'effective_interest_rate',
            'rate_period', 'binding_period', 'next_change_date',
            'disbursement_date', 'borrowers', 'borrower_shares', 'currency',
            'collateral', 'lender', 'payment_interval', 'payment_account',
            'repayment_account'
        ]
        
        for field in extended_fields:
            if field in kwargs and kwargs[field] is not None:
                loan[field] = kwargs[field]
        
        loans.append(loan)
        self.save_loans(loans)
        return loan
    
    def get_loans(self, status: Optional[str] = None) -> List[Dict]:
        """Hämta lån, filtrerat på status om angivet.
        
        Args:
            status: 'active', 'paid_off', 'closed', eller None för alla
            
        Returns:
            Lista med lån
        """
        loans = self.load_loans()
        
        if status:
            loans = [l for l in loans if l.get('status') == status]
        
        return loans
    
    def get_loan_by_id(self, loan_id: str) -> Optional[Dict]:
        """Hämta ett lån med ID."""
        loans = self.load_loans()
        for loan in loans:
            if loan.get('id') == loan_id:
                return loan
        return None
    
    def update_loan(self, loan_id: str, updates: Dict) -> bool:
        """Uppdatera ett lån.
        
        Args:
            loan_id: ID för lånet som ska uppdateras
            updates: Dict med fält att uppdatera
            
        Returns:
            True om uppdatering lyckades, annars False
        """
        loans = self.load_loans()
        
        for i, loan in enumerate(loans):
            if loan.get('id') == loan_id:
                loans[i].update(updates)
                self.save_loans(loans)
                return True
        
        return False
    
    def delete_loan(self, loan_id: str) -> bool:
        """Ta bort ett lån.
        
        Args:
            loan_id: ID för lånet som ska tas bort
            
        Returns:
            True om borttagning lyckades, annars False
        """
        loans = self.load_loans()
        initial_count = len(loans)
        loans = [l for l in loans if l.get('id') != loan_id]
        
        if len(loans) < initial_count:
            self.save_loans(loans)
            return True
        
        return False
    
    def add_payment(self, loan_id: str, amount: float, payment_date: str, 
                    transaction_id: str = None) -> bool:
        """Registrera en återbetalning (amortering).
        
        Args:
            loan_id: ID för lånet
            amount: Belopp som betalas
            payment_date: Datum för betalningen (YYYY-MM-DD)
            transaction_id: Optional transaction ID for linking
            
        Returns:
            True om betalning registrerades
        """
        loan = self.get_loan_by_id(loan_id)
        if not loan:
            return False
        
        # Lägg till betalning i listan
        payment = {
            'date': payment_date,
            'amount': amount,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        if transaction_id:
            payment['transaction_id'] = transaction_id
        
        payments = loan.get('payments', [])
        payments.append(payment)
        
        # Uppdatera nuvarande saldo
        new_balance = loan.get('current_balance', 0) - amount
        
        updates = {
            'payments': payments,
            'current_balance': max(0, new_balance)
        }
        
        # Markera som betald om saldo är 0
        if new_balance <= 0:
            updates['status'] = 'paid_off'
        
        return self.update_loan(loan_id, updates)
    
    def add_interest_payment(self, loan_id: str, amount: float, payment_date: str,
                            transaction_id: str = None) -> bool:
        """Registrera en räntebetalning.
        
        Args:
            loan_id: ID för lånet
            amount: Räntebelopp som betalas
            payment_date: Datum för betalningen (YYYY-MM-DD)
            transaction_id: Optional transaction ID for linking
            
        Returns:
            True om betalning registrerades
        """
        loan = self.get_loan_by_id(loan_id)
        if not loan:
            return False
        
        # Lägg till räntebetalning i listan
        interest_payment = {
            'date': payment_date,
            'amount': amount,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        if transaction_id:
            interest_payment['transaction_id'] = transaction_id
        
        interest_payments = loan.get('interest_payments', [])
        interest_payments.append(interest_payment)
        
        updates = {
            'interest_payments': interest_payments
        }
        
        return self.update_loan(loan_id, updates)
    
    def match_transaction_to_loan(self, transaction: Dict, loan_id: str = None) -> Optional[Dict]:
        """Match a transaction to a loan and update the loan balance.
        
        Args:
            transaction: Transaction dictionary with amount, date, description, etc.
            loan_id: Optional specific loan ID to match to. If None, tries to auto-match.
            
        Returns:
            Dictionary with match result, or None if no match
        """
        # If loan_id is specified, use that loan
        if loan_id:
            loan = self.get_loan_by_id(loan_id)
            if not loan:
                return None
        else:
            # Try to auto-match based on account number or description
            loan = self._auto_match_loan(transaction)
            if not loan:
                return None
        
        # Extract payment amount (negative amounts for payments)
        amount = abs(float(transaction.get('amount', 0)))
        date = transaction.get('date', datetime.now().strftime('%Y-%m-%d'))
        description = transaction.get('description', '').lower()
        
        # Determine if this is amortization or interest payment
        is_interest = any(keyword in description for keyword in ['ränta', 'interest', 'ränteinbetalning'])
        
        # Register payment
        if is_interest:
            success = self.add_interest_payment(loan['id'], amount, date, transaction.get('id'))
            payment_type = 'interest'
        else:
            success = self.add_payment(loan['id'], amount, date, transaction.get('id'))
            payment_type = 'amortization'
        
        if success:
            return {
                'matched': True,
                'loan_id': loan['id'],
                'loan_name': loan['name'],
                'amount': amount,
                'date': date,
                'payment_type': payment_type,
                'new_balance': max(0, loan.get('current_balance', 0) - (amount if not is_interest else 0))
            }
        
        return None
    
    def _auto_match_loan(self, transaction: Dict) -> Optional[Dict]:
        """Try to automatically match a transaction to a loan based on account number or description.
        
        Args:
            transaction: Transaction dictionary
            
        Returns:
            Matched loan or None
        """
        description = transaction.get('description', '').lower()
        account_number = transaction.get('account_number', '')
        loans = self.get_loans(status='active')
        
        # First, try to match by account number
        if account_number:
            for loan in loans:
                payment_account = loan.get('payment_account', '')
                repayment_account = loan.get('repayment_account', '')
                
                # Normalize account numbers for comparison
                normalized_trans_account = account_number.replace('-', '').replace(' ', '')
                normalized_payment = payment_account.replace('-', '').replace(' ', '')
                normalized_repayment = repayment_account.replace('-', '').replace(' ', '')
                
                if normalized_trans_account and (
                    normalized_trans_account == normalized_payment or
                    normalized_trans_account == normalized_repayment
                ):
                    return loan
        
        # Look for loan name, ID, or loan number in transaction description
        for loan in loans:
            loan_name = loan.get('name', '').lower()
            loan_id = loan.get('id', '').lower()
            loan_number = str(loan.get('loan_number', '')).lower()
            
            if loan_name and loan_name in description:
                return loan
            if loan_id and loan_id in description:
                return loan
            if loan_number and loan_number in description:
                return loan
            
            # Check for common loan-related keywords
            loan_keywords = ['bolån', 'billån', 'lån', 'amortering', 'ränta']
            if any(keyword in description for keyword in loan_keywords):
                # Only auto-match if there is exactly one active loan
                if len(loans) == 1:
                    return loan
                else:
                    # Ambiguous: multiple active loans, generic keyword found
                    return None
        
        return None
    
    def get_loan_payment_history(self, loan_id: str) -> List[Dict]:
        """Get payment history for a loan.
        
        Args:
            loan_id: Loan ID
            
        Returns:
            List of payments
        """
        loan = self.get_loan_by_id(loan_id)
        if loan:
            return loan.get('payments', [])
        return []
    
    def calculate_monthly_payment(self, principal: float, interest_rate: float, 
                                  term_months: int) -> float:
        """Beräkna månatlig betalning för annuitetslån.
        
        Args:
            principal: Lånebelopp
            interest_rate: Årsränta i procent
            term_months: Löptid i månader
            
        Returns:
            Månatlig betalning
        """
        if interest_rate == 0:
            return principal / term_months
        
        # Månatlig ränta
        monthly_rate = interest_rate / 100 / 12
        
        # Annuitetsformel
        payment = principal * (monthly_rate * (1 + monthly_rate) ** term_months) / \
                  ((1 + monthly_rate) ** term_months - 1)
        
        return payment
    
    def get_amortization_schedule(self, loan_id: str, months: int = 12) -> List[Dict]:
        """Få amorteringsplan för ett lån.
        
        Args:
            loan_id: ID för lånet
            months: Antal månader att visa
            
        Returns:
            Lista med månadsvis amortering
        """
        loan = self.get_loan_by_id(loan_id)
        if not loan:
            return []
        
        balance = loan.get('current_balance', 0)
        interest_rate = loan.get('interest_rate', 0)
        term_months = loan.get('term_months', 360)
        
        monthly_payment = self.calculate_monthly_payment(balance, interest_rate, term_months)
        monthly_rate = interest_rate / 100 / 12
        
        schedule = []
        current_balance = balance
        
        from datetime import datetime, timedelta
        start_date = datetime.now()
        
        for month in range(months):
            if current_balance <= 0:
                break
            
            interest = current_balance * monthly_rate
            principal_payment = monthly_payment - interest
            current_balance -= principal_payment
            
            month_date = start_date + timedelta(days=30 * month)
            
            schedule.append({
                'month': month + 1,
                'date': month_date.strftime('%Y-%m-%d'),
                'payment': round(monthly_payment, 2),
                'principal': round(principal_payment, 2),
                'interest': round(interest, 2),
                'balance': round(max(0, current_balance), 2)
            })
        
        return schedule
    
    def simulate_interest_change(self, loan_id: str, new_interest_rate: float) -> Dict:
        """Simulera ränteförändring.
        
        Args:
            loan_id: ID för lånet
            new_interest_rate: Ny årsränta i procent
            
        Returns:
            Dict med simuleringsresultat
        """
        loan = self.get_loan_by_id(loan_id)
        if not loan:
            return {}
        
        current_rate = loan.get('interest_rate', 0)
        balance = loan.get('current_balance', 0)
        term_months = loan.get('term_months', 360)
        
        # Beräkna nuvarande månatlig betalning
        current_payment = self.calculate_monthly_payment(balance, current_rate, term_months)
        
        # Beräkna ny månatlig betalning
        new_payment = self.calculate_monthly_payment(balance, new_interest_rate, term_months)
        
        # Beräkna skillnad
        difference = new_payment - current_payment
        difference_percent = (difference / current_payment * 100) if current_payment > 0 else 0
        
        return {
            'loan_name': loan.get('name'),
            'current_balance': balance,
            'current_interest_rate': current_rate,
            'new_interest_rate': new_interest_rate,
            'current_monthly_payment': round(current_payment, 2),
            'new_monthly_payment': round(new_payment, 2),
            'difference': round(difference, 2),
            'difference_percent': round(difference_percent, 2)
        }
