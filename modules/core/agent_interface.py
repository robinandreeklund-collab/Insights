"""Agent Interface - Tolkar frågor och genererar svar, insikter och simuleringar."""

import os
import yaml
import uuid
import re
from typing import Dict, List, Optional
from datetime import datetime

from .history_viewer import HistoryViewer
from .income_tracker import IncomeTracker
from .forecast_engine import get_forecast_summary, load_transactions
from .loan_manager import LoanManager
from .bill_manager import BillManager
from .account_manager import AccountManager


class AgentInterface:
    """Agent som tolkar naturliga språkfrågor och genererar svar."""
    
    def __init__(self, yaml_dir: str = "yaml"):
        """Initialisera agent interface."""
        self.yaml_dir = yaml_dir
        self.query_log_file = os.path.join(yaml_dir, "agent_queries.yaml")
        
        # Initialize sub-modules
        self.history_viewer = HistoryViewer(yaml_dir)
        self.income_tracker = IncomeTracker(yaml_dir)
        self.loan_manager = LoanManager(yaml_dir)
        self.bill_manager = BillManager(yaml_dir)
        self.account_manager = AccountManager(yaml_dir)
        
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
    
    def parse_query(self, text: str) -> Dict:
        """Parse user query and extract intent and parameters.
        
        Args:
            text: User query in natural language
            
        Returns:
            Dictionary with parsed intent and parameters
        """
        text_lower = text.lower()
        
        # Initialize result
        result = {
            'original_query': text,
            'intent': 'unknown',
            'module': None,
            'parameters': {}
        }
        
        # Pattern matching for different intents
        # Check more specific patterns first to avoid false matches
        
        # Bill/Faktura queries - check first to avoid "visa" matching history
        if any(word in text_lower for word in ['faktura', 'fakturor', 'räkning', 'räkningar', 'bill', 'bills']):
            result['intent'] = 'bill_query'
            result['module'] = 'bill_manager'
            
            # Extract month if mentioned
            month_match = re.search(r'(januari|februari|mars|april|maj|juni|juli|augusti|september|oktober|november|december)', text_lower)
            if month_match:
                result['parameters']['month'] = month_match.group(1)
        
        # Balance/Saldo queries
        elif any(word in text_lower for word in ['saldo', 'balance', 'kvar']):
            result['intent'] = 'balance_query'
            result['module'] = 'forecast_engine'
            
            # Extract month if mentioned
            month_match = re.search(r'(januari|februari|mars|april|maj|juni|juli|augusti|september|oktober|november|december)', text_lower)
            if month_match:
                result['parameters']['month'] = month_match.group(1)
        
        # Loan/Lån queries
        elif any(word in text_lower for word in ['lån', 'loan', 'ränta', 'interest']):
            result['intent'] = 'loan_query'
            result['module'] = 'loan_manager'
            
            # Check for simulation intent
            if any(word in text_lower for word in ['simulera', 'simulate', 'om', 'if', 'ökar', 'minskar']):
                result['intent'] = 'loan_simulation'
                
                # Extract interest rate change
                rate_match = re.search(r'(\d+(?:[.,]\d+)?)\s*%', text)
                if rate_match:
                    result['parameters']['new_rate'] = float(rate_match.group(1).replace(',', '.'))
        
        # Income/Inkomst queries
        elif any(word in text_lower for word in ['inkomst', 'income', 'lön', 'salary']):
            result['intent'] = 'income_query'
            result['module'] = 'income_tracker'
        
        # History/Historik queries
        elif any(word in text_lower for word in ['historik', 'history', 'trend', 'utveckling']):
            result['intent'] = 'history_query'
            result['module'] = 'history_viewer'
            
            # Extract category if mentioned
            categories = ['mat', 'transport', 'boende', 'shopping', 'nöje']
            for cat in categories:
                if cat in text_lower:
                    result['parameters']['category'] = cat.capitalize()
                    break
        
        # Top expenses queries
        elif any(word in text_lower for word in ['största', 'highest', 'top', 'mest']):
            result['intent'] = 'top_expenses'
            result['module'] = 'history_viewer'
        
        # Monthly summary queries
        elif any(word in text_lower for word in ['månad', 'month', 'sammanfattning', 'summary']):
            result['intent'] = 'monthly_summary'
            result['module'] = 'history_viewer'
        
        return result
    
    def route_to_module(self, parsed: Dict) -> str:
        """Route parsed query to appropriate module.
        
        Args:
            parsed: Parsed query dictionary
            
        Returns:
            Module name to handle the query
        """
        return parsed.get('module', 'unknown')
    
    def generate_response(self, parsed: Dict) -> str:
        """Generate response based on parsed query.
        
        Args:
            parsed: Parsed query dictionary
            
        Returns:
            Response text
        """
        intent = parsed.get('intent')
        params = parsed.get('parameters', {})
        
        try:
            # Balance queries
            if intent == 'balance_query':
                accounts = self.account_manager.get_accounts()
                total_balance = sum(acc.get('balance', 0) for acc in accounts)
                
                response = f"Nuvarande totalt saldo: {total_balance:.2f} SEK\n\n"
                
                # Get forecast
                transactions_file = os.path.join(self.yaml_dir, "transactions.yaml")
                forecast = get_forecast_summary(total_balance, transactions_file, 30)
                response += f"Prognos 30 dagar: {forecast['predicted_final_balance']:.2f} SEK\n"
                response += f"Genomsnittlig daglig inkomst: {forecast['avg_daily_income']:.2f} SEK\n"
                response += f"Genomsnittlig daglig utgift: {forecast['avg_daily_expenses']:.2f} SEK"
                
                return response
            
            # Bill queries
            elif intent == 'bill_query':
                bills = self.bill_manager.get_bills(status='pending')
                
                if not bills:
                    return "Inga väntande fakturor hittades."
                
                response = f"Du har {len(bills)} väntande fakturor:\n\n"
                for bill in bills[:5]:  # Show top 5
                    response += f"• {bill['name']}: {bill['amount']:.2f} SEK (förfaller {bill['due_date']})\n"
                
                total = sum(bill['amount'] for bill in bills)
                response += f"\nTotalt: {total:.2f} SEK"
                
                return response
            
            # Loan queries
            elif intent == 'loan_query':
                loans = self.loan_manager.get_loans(status='active')
                
                if not loans:
                    return "Inga aktiva lån hittades."
                
                response = f"Du har {len(loans)} aktivt lån:\n\n"
                for loan in loans:
                    response += f"• {loan['name']}: {loan['remaining_balance']:.2f} SEK\n"
                    response += f"  Ränta: {loan['interest_rate']}%, Månadsbetalning: {loan.get('monthly_payment', 0):.2f} SEK\n\n"
                
                return response
            
            # Loan simulation
            elif intent == 'loan_simulation':
                loans = self.loan_manager.get_loans(status='active')
                
                if not loans:
                    return "Inga aktiva lån att simulera."
                
                new_rate = params.get('new_rate')
                if not new_rate:
                    return "Kunde inte hitta ny ränta i frågan. Ange ränta i procent (t.ex. 4.5%)."
                
                loan = loans[0]  # Simulate for first loan
                simulation = self.loan_manager.simulate_interest_change(loan['id'], new_rate)
                
                response = f"Simulering för {loan['name']}:\n\n"
                response += f"Nuvarande ränta: {simulation['current_rate']}%\n"
                response += f"Ny ränta: {simulation['new_rate']}%\n"
                response += f"Nuvarande månadsbetalning: {simulation['current_monthly_payment']:.2f} SEK\n"
                response += f"Ny månadsbetalning: {simulation['new_monthly_payment']:.2f} SEK\n"
                response += f"Skillnad: {simulation['difference']:.2f} SEK ({simulation['difference_percent']}%)"
                
                return response
            
            # Income queries
            elif intent == 'income_query':
                current_month = datetime.now().strftime('%Y-%m')
                monthly_income = self.income_tracker.get_monthly_income(current_month)
                
                response = f"Inkomst denna månad ({current_month}): {monthly_income:.2f} SEK\n\n"
                
                # Get income by person
                person_income = self.income_tracker.get_income_by_person(
                    start_date=f"{current_month}-01"
                )
                
                if person_income:
                    response += "Per person:\n"
                    for person, amount in person_income.items():
                        response += f"• {person}: {amount:.2f} SEK\n"
                
                return response
            
            # History queries
            elif intent == 'history_query':
                category = params.get('category')
                
                if category:
                    trend = self.history_viewer.get_category_trend(category, months=6)
                    response = f"Trend för {category} (senaste 6 månaderna):\n\n"
                    for data in trend:
                        response += f"• {data['month']}: {data['amount']:.2f} SEK ({data['count']} transaktioner)\n"
                else:
                    months = self.history_viewer.get_all_months()
                    response = f"Tillgängliga månader: {', '.join(months[:6])}"
                
                return response
            
            # Top expenses
            elif intent == 'top_expenses':
                current_month = datetime.now().strftime('%Y-%m')
                top = self.history_viewer.get_top_expenses(current_month, top_n=5)
                
                if not top:
                    return "Inga utgifter hittades för denna månad."
                
                response = f"Största utgifter denna månad:\n\n"
                for i, tx in enumerate(top, 1):
                    response += f"{i}. {tx.get('description', 'N/A')}: {abs(tx['amount']):.2f} SEK\n"
                
                return response
            
            # Monthly summary
            elif intent == 'monthly_summary':
                current_month = datetime.now().strftime('%Y-%m')
                summary = self.history_viewer.get_monthly_summary(current_month)
                
                response = f"Sammanfattning för {summary['month']}:\n\n"
                response += f"Inkomster: {summary['income']:.2f} SEK ({summary['income_count']} transaktioner)\n"
                response += f"Utgifter: {summary['expenses']:.2f} SEK ({summary['expense_count']} transaktioner)\n"
                response += f"Netto: {summary['net']:.2f} SEK\n\n"
                
                if summary['category_breakdown']:
                    response += "Utgifter per kategori:\n"
                    for cat, amount in sorted(summary['category_breakdown'].items(), key=lambda x: x[1], reverse=True):
                        response += f"• {cat}: {amount:.2f} SEK\n"
                
                return response
            
            else:
                return "Jag förstod inte din fråga. Prova att fråga om saldo, fakturor, lån, inkomster eller historik."
        
        except Exception as e:
            return f"Ett fel uppstod: {str(e)}"
    
    def log_query_and_response(self, query: str, response: str) -> None:
        """Log query and response for future analysis.
        
        Args:
            query: User query
            response: Generated response
        """
        data = self._load_yaml(self.query_log_file)
        if 'queries' not in data:
            data['queries'] = []
        
        log_entry = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'query': query,
            'response': response
        }
        
        data['queries'].append(log_entry)
        
        # Keep only last 100 queries
        if len(data['queries']) > 100:
            data['queries'] = data['queries'][-100:]
        
        self._save_yaml(self.query_log_file, data)
    
    def process_query(self, query: str) -> str:
        """Process a query end-to-end.
        
        Args:
            query: User query in natural language
            
        Returns:
            Response text
        """
        # Parse query
        parsed = self.parse_query(query)
        
        # Generate response
        response = self.generate_response(parsed)
        
        # Log query and response
        self.log_query_and_response(query, response)
        
        return response


def process_query(query: str, yaml_dir: str = "yaml") -> str:
    """Wrapper function to process a query."""
    agent = AgentInterface(yaml_dir)
    return agent.process_query(query)
