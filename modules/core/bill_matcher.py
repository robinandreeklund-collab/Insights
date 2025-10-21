"""Bill Matcher - Matchar fakturor mot transaktioner."""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta


class BillMatcher:
    """Matchar fakturor mot transaktioner och uppdaterar betalningsstatus."""
    
    def __init__(self, bill_manager, account_manager):
        """Initialisera bill matcher.
        
        Args:
            bill_manager: Instans av BillManager
            account_manager: Instans av AccountManager
        """
        self.bill_manager = bill_manager
        self.account_manager = account_manager
    
    def match_bills_to_transactions(self, tolerance_days: int = 7) -> List[Dict]:
        """Matcha alla pending fakturor mot transaktioner.
        
        Args:
            tolerance_days: Antal dagar före/efter förfallodatum att söka
            
        Returns:
            Lista med matchningar (bill_id, transaction_id, confidence)
        """
        pending_bills = self.bill_manager.get_bills(status='pending')
        all_transactions = self.account_manager.get_all_transactions()
        
        matches = []
        
        for bill in pending_bills:
            match = self._find_matching_transaction(
                bill, 
                all_transactions, 
                tolerance_days
            )
            
            if match:
                matches.append(match)
                
                # Markera faktura som betald
                self.bill_manager.mark_as_paid(
                    bill['id'], 
                    match['transaction_id']
                )
        
        return matches
    
    def _find_matching_transaction(self, bill: Dict, transactions: List[Dict], 
                                   tolerance_days: int) -> Optional[Dict]:
        """Hitta matchande transaktion för en faktura.
        
        Args:
            bill: Faktura att matcha
            transactions: Lista med transaktioner
            tolerance_days: Tolerans i dagar
            
        Returns:
            Dict med matchinformation eller None
        """
        bill_amount = abs(bill.get('amount', 0))
        bill_due_date = bill.get('due_date', '')
        
        if not bill_due_date:
            return None
        
        try:
            due_date = datetime.strptime(bill_due_date, '%Y-%m-%d')
        except ValueError:
            return None
        
        # Sök transaktioner inom datumfönstret
        date_start = (due_date - timedelta(days=tolerance_days)).strftime('%Y-%m-%d')
        date_end = (due_date + timedelta(days=tolerance_days)).strftime('%Y-%m-%d')
        
        best_match = None
        best_confidence = 0.0
        
        for transaction in transactions:
            tx_date = transaction.get('date', '')
            tx_amount = abs(transaction.get('amount', 0))
            
            # Kontrollera datumintervall
            if not (date_start <= tx_date <= date_end):
                continue
            
            # Kontrollera belopp (måste vara negativt = utgift)
            if transaction.get('amount', 0) >= 0:
                continue
            
            # Beräkna matchningsgrad
            confidence = self._calculate_match_confidence(
                bill, transaction, bill_amount, tx_amount
            )
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = {
                    'bill_id': bill['id'],
                    'transaction_id': self._get_transaction_id(transaction),
                    'confidence': confidence,
                    'amount_diff': abs(bill_amount - tx_amount)
                }
        
        # Returnera endast om confidence är tillräckligt hög
        if best_match and best_confidence >= 0.7:
            return best_match
        
        return None
    
    def _calculate_match_confidence(self, bill: Dict, transaction: Dict, 
                                    bill_amount: float, tx_amount: float) -> float:
        """Beräkna matchningsgrad mellan faktura och transaktion.
        
        Args:
            bill: Faktura
            transaction: Transaktion
            bill_amount: Fakturabelopp (absolut)
            tx_amount: Transaktionsbelopp (absolut)
            
        Returns:
            Confidence score (0-1)
        """
        confidence = 0.0
        
        # Exakt beloppsmatchning = +0.5
        if abs(bill_amount - tx_amount) < 0.01:
            confidence += 0.5
        # Nära beloppsmatchning (inom 5%) = +0.3
        elif abs(bill_amount - tx_amount) / bill_amount < 0.05:
            confidence += 0.3
        # Ungefär rätt belopp (inom 10%) = +0.2
        elif abs(bill_amount - tx_amount) / bill_amount < 0.10:
            confidence += 0.2
        
        # Textmatchning i beskrivning
        bill_name = bill.get('name', '').lower()
        tx_description = transaction.get('description', '').lower()
        
        # Exakt matchning i beskrivning = +0.3
        if bill_name in tx_description or tx_description in bill_name:
            confidence += 0.3
        else:
            # Partiell matchning (gemensamma ord) = +0.2
            bill_words = set(bill_name.split())
            tx_words = set(tx_description.split())
            common_words = bill_words.intersection(tx_words)
            
            if len(common_words) >= 2:
                confidence += 0.2
            elif len(common_words) == 1:
                confidence += 0.1
        
        # Kategori matchning = +0.2
        bill_category = bill.get('category', '').lower()
        tx_category = transaction.get('category', '').lower()
        
        if bill_category == tx_category:
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _get_transaction_id(self, transaction: Dict) -> str:
        """Generera eller hämta unikt ID för transaktion.
        
        Args:
            transaction: Transaktion
            
        Returns:
            Unikt ID för transaktionen
        """
        # Om transaktionen redan har ett ID, använd det
        if 'id' in transaction:
            return transaction['id']
        
        # Annars generera ett baserat på datum, beskrivning och belopp
        date = transaction.get('date', '')
        desc = transaction.get('description', '')[:20]
        amount = transaction.get('amount', 0)
        
        return f"TX-{date}-{desc}-{amount}"
    
    def manual_match(self, bill_id: str, transaction_id: str) -> bool:
        """Manuellt matcha en faktura mot en transaktion.
        
        Args:
            bill_id: ID för fakturan
            transaction_id: ID för transaktionen
            
        Returns:
            True om matchning lyckades
        """
        bill = self.bill_manager.get_bill_by_id(bill_id)
        
        if not bill:
            return False
        
        # Markera faktura som betald med matchad transaktion
        return self.bill_manager.mark_as_paid(bill_id, transaction_id)
    
    def get_unmatched_bills(self) -> List[Dict]:
        """Hämta alla fakturor som inte matchats mot transaktioner.
        
        Returns:
            Lista med omatchade fakturor
        """
        all_bills = self.bill_manager.get_bills()
        unmatched = [
            bill for bill in all_bills 
            if bill.get('status') == 'pending' and not bill.get('matched_transaction_id')
        ]
        
        return unmatched
