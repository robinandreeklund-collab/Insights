"""Net Balance Splitter - Fördelar utgifter och beräknar överföringar till gemensamt konto."""

from typing import List, Dict, Optional
from collections import defaultdict


class NetBalanceSplitter:
    """Beräknar hur mycket varje person ska överföra till gemensamt konto baserat på inkomster och utgifter."""
    
    def __init__(self):
        """Initialisera net balance splitter."""
        pass
    
    def calculate_shared_expenses(
        self,
        total_expenses: float,
        income_by_person: Dict[str, float],
        custom_ratios: Optional[Dict[str, float]] = None
    ) -> Dict[str, Dict[str, float]]:
        """Beräkna hur mycket varje person ska betala av gemensamma utgifter.
        
        Args:
            total_expenses: Totala gemensamma utgifter
            income_by_person: Dict med inkomst per person
            custom_ratios: Valfria anpassade fördelningsandelar (t.ex. {"Robin": 0.6, "Partner": 0.4})
            
        Returns:
            Dict med beräkningar per person:
            {
                'person_name': {
                    'income': float,
                    'expense_share': float,
                    'ratio': float,
                    'should_transfer': float
                }
            }
        """
        result = {}
        
        # Calculate total income
        total_income = sum(income_by_person.values())
        
        if total_income == 0:
            # If no income, split equally
            num_people = len(income_by_person)
            if num_people == 0:
                return result
            
            equal_share = total_expenses / num_people
            for person in income_by_person.keys():
                result[person] = {
                    'income': 0.0,
                    'expense_share': equal_share,
                    'ratio': 1.0 / num_people,
                    'should_transfer': equal_share
                }
            return result
        
        # Calculate ratios
        for person, income in income_by_person.items():
            if custom_ratios and person in custom_ratios:
                # Use custom ratio if provided
                ratio = custom_ratios[person]
            else:
                # Calculate ratio based on income
                ratio = income / total_income
            
            expense_share = total_expenses * ratio
            
            result[person] = {
                'income': income,
                'expense_share': round(expense_share, 2),
                'ratio': round(ratio, 3),
                'should_transfer': round(expense_share, 2)
            }
        
        return result
    
    def calculate_transfer_recommendations(
        self,
        income_by_person_and_account: Dict[str, Dict[str, float]],
        expenses_by_category: Dict[str, float],
        shared_categories: Optional[List[str]] = None,
        custom_ratios: Optional[Dict[str, float]] = None
    ) -> Dict:
        """Beräkna rekommendationer för överföringar till gemensamt konto.
        
        Args:
            income_by_person_and_account: Inkomster per person och konto
                {"Robin": {"1234 56 78901": 30000, "2345 67 89012": 5000}, ...}
            expenses_by_category: Utgifter per kategori
            shared_categories: Lista med kategorier som anses vara gemensamma utgifter
                (default: ["Boende", "Mat & Dryck"])
            custom_ratios: Valfria anpassade fördelningsandelar
            
        Returns:
            Dict med rekommendationer:
            {
                'total_shared_expenses': float,
                'persons': {
                    'person_name': {
                        'total_income': float,
                        'accounts': {account: income},
                        'expense_share': float,
                        'ratio': float,
                        'should_transfer': float
                    }
                },
                'summary': str
            }
        """
        # Default shared categories
        if shared_categories is None:
            shared_categories = ["Boende", "Mat & Dryck"]
        
        # Calculate total shared expenses
        total_shared_expenses = sum(
            amount for category, amount in expenses_by_category.items()
            if category in shared_categories
        )
        
        # Calculate total income per person
        income_by_person = {}
        for person, accounts in income_by_person_and_account.items():
            income_by_person[person] = sum(accounts.values())
        
        # Calculate expense shares
        expense_shares = self.calculate_shared_expenses(
            total_shared_expenses,
            income_by_person,
            custom_ratios
        )
        
        # Build result with account details
        persons = {}
        for person, accounts in income_by_person_and_account.items():
            share_info = expense_shares.get(person, {})
            persons[person] = {
                'total_income': sum(accounts.values()),
                'accounts': accounts,
                'expense_share': share_info.get('expense_share', 0.0),
                'ratio': share_info.get('ratio', 0.0),
                'should_transfer': share_info.get('should_transfer', 0.0)
            }
        
        # Generate summary text
        summary_lines = [
            f"Totala gemensamma utgifter: {total_shared_expenses:,.2f} SEK",
            "",
            "Rekommenderade överföringar:"
        ]
        
        for person, info in persons.items():
            summary_lines.append(
                f"  {person}: {info['should_transfer']:,.2f} SEK ({info['ratio']*100:.1f}% av utgifter)"
            )
        
        summary = "\n".join(summary_lines)
        
        return {
            'total_shared_expenses': total_shared_expenses,
            'persons': persons,
            'summary': summary
        }
    
    def split_balance_after_expenses(
        self,
        balances_by_person: Dict[str, float],
        expenses_paid: Dict[str, float],
        custom_ratios: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """Beräkna vem som ska få tillbaka pengar efter att gemensamma utgifter betalats.
        
        Args:
            balances_by_person: Nuvarande saldo per person
            expenses_paid: Hur mycket varje person har betalat av gemensamma utgifter
            custom_ratios: Valfria anpassade fördelningsandelar
            
        Returns:
            Dict med nettobalans per person (positivt = ska få, negativt = ska betala)
        """
        total_paid = sum(expenses_paid.values())
        
        # Calculate how much each person should have paid
        should_pay = {}
        total_balance = sum(balances_by_person.values())
        
        for person, balance in balances_by_person.items():
            if custom_ratios and person in custom_ratios:
                ratio = custom_ratios[person]
            else:
                ratio = balance / total_balance if total_balance > 0 else 1.0 / len(balances_by_person)
            
            should_pay[person] = total_paid * ratio
        
        # Calculate net balance
        net_balance = {}
        for person in balances_by_person.keys():
            paid = expenses_paid.get(person, 0.0)
            should_have_paid = should_pay.get(person, 0.0)
            # Positive = person paid too much, should get money back
            # Negative = person paid too little, should pay more
            net_balance[person] = round(paid - should_have_paid, 2)
        
        return net_balance


def calculate_transfer_recommendations(
    income_by_person_and_account: Dict[str, Dict[str, float]],
    expenses_by_category: Dict[str, float],
    shared_categories: Optional[List[str]] = None,
    custom_ratios: Optional[Dict[str, float]] = None
) -> Dict:
    """Wrapper function för att beräkna överföringsrekommendationer."""
    splitter = NetBalanceSplitter()
    return splitter.calculate_transfer_recommendations(
        income_by_person_and_account,
        expenses_by_category,
        shared_categories,
        custom_ratios
    )
