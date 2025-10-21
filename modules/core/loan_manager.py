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
                 description: str = "") -> Dict:
        """Lägg till ett nytt lån.
        
        Args:
            name: Lånets namn (t.ex. "Bolån")
            principal: Huvudbelopp (ursprungligt lån)
            interest_rate: Årsränta i procent (t.ex. 3.5 för 3.5%)
            start_date: Startdatum (YYYY-MM-DD)
            term_months: Löptid i månader (default 360 = 30 år)
            fixed_rate_end_date: Datum när bindningstiden slutar (YYYY-MM-DD)
            description: Beskrivning/detaljer
            
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
            'payments': []  # Lista med återbetalningar
        }
        
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
    
    def add_payment(self, loan_id: str, amount: float, payment_date: str) -> bool:
        """Registrera en återbetalning.
        
        Args:
            loan_id: ID för lånet
            amount: Belopp som betalas
            payment_date: Datum för betalningen (YYYY-MM-DD)
            
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
