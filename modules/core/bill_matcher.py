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
    
    def match_bills_to_transactions(self, tolerance_days: int = 7, amount_tolerance_percent: float = 5.0) -> List[Dict]:
        """Matcha alla scheduled/pending fakturor mot transaktioner.
        
        Args:
            tolerance_days: Antal dagar före/efter förfallodatum att söka
            amount_tolerance_percent: Tolerans i procent för beloppsmatchning
            
        Returns:
            Lista med matchningar (bill_id, transaction_id, confidence)
        """
        # Get bills that are scheduled or pending (not yet paid)
        scheduled_bills = self.bill_manager.get_bills(status='scheduled')
        pending_bills = self.bill_manager.get_bills(status='pending')
        all_unpaid_bills = scheduled_bills + pending_bills
        
        all_transactions = self.account_manager.get_all_transactions()
        
        matches = []
        
        for bill in all_unpaid_bills:
            match = self._find_matching_transaction(
                bill, 
                all_transactions, 
                tolerance_days,
                amount_tolerance_percent
            )
            
            if match:
                matches.append(match)
                
                # Markera faktura som betald och uppdatera matched_to_bill_id
                self.bill_manager.mark_as_paid(
                    bill['id'], 
                    match['transaction_id']
                )
                
                # Update transaction with matched bill ID
                self._update_transaction_match(match['transaction_id'], bill['id'])
        
        return matches
    
    def _find_matching_transaction(self, bill: Dict, transactions: List[Dict], 
                                   tolerance_days: int, amount_tolerance_percent: float = 5.0) -> Optional[Dict]:
        """Hitta matchande transaktion för en faktura.
        
        Args:
            bill: Faktura att matcha
            transactions: Lista med transaktioner
            tolerance_days: Tolerans i dagar
            amount_tolerance_percent: Tolerans i procent för beloppsmatchning
            
        Returns:
            Dict med matchinformation eller None
        """
        bill_amount = abs(bill.get('amount', 0))
        bill_due_date = bill.get('due_date', '')
        bill_account = bill.get('account_number') or bill.get('account')
        
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
            tx_account = transaction.get('account_number') or transaction.get('account')
            
            # Kontrollera datumintervall
            if not (date_start <= tx_date <= date_end):
                continue
            
            # Kontrollera belopp (måste vara negativt = utgift)
            if transaction.get('amount', 0) >= 0:
                continue
            
            # Check if transaction is already matched
            if transaction.get('matched_to_bill_id'):
                continue
            
            # Beräkna matchningsgrad
            confidence = self._calculate_match_confidence(
                bill, transaction, bill_amount, tx_amount, 
                bill_account, tx_account, amount_tolerance_percent
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
                                    bill_amount: float, tx_amount: float,
                                    bill_account: Optional[str] = None, 
                                    tx_account: Optional[str] = None,
                                    amount_tolerance_percent: float = 5.0) -> float:
        """Beräkna matchningsgrad mellan faktura och transaktion.
        
        Args:
            bill: Faktura
            transaction: Transaktion
            bill_amount: Fakturabelopp (absolut)
            tx_amount: Transaktionsbelopp (absolut)
            bill_account: Normalized account number from bill
            tx_account: Normalized account number from transaction
            amount_tolerance_percent: Tolerans i procent för beloppsmatchning
            
        Returns:
            Confidence score (0-1)
        """
        confidence = 0.0
        
        # Account number matching (very strong signal if both present)
        if bill_account and tx_account:
            # Normalize both account numbers for comparison
            from modules.core.bill_manager import normalize_account_number
            norm_bill_acc = normalize_account_number(bill_account)
            norm_tx_acc = normalize_account_number(tx_account)
            
            if norm_bill_acc and norm_tx_acc and norm_bill_acc == norm_tx_acc:
                confidence += 0.4  # Strong signal for account match
        
        # Exakt beloppsmatchning = +0.5
        if abs(bill_amount - tx_amount) < 0.01:
            confidence += 0.5
        # Endast gör procentuella jämförelser om bill_amount > 0
        elif bill_amount > 0:
            # Nära beloppsmatchning (inom tolerance_percent) = +0.3
            if abs(bill_amount - tx_amount) / bill_amount < (amount_tolerance_percent / 100.0):
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
        
        # Kategori matchning = +0.1 (reduced weight since account is more reliable)
        bill_category = bill.get('category', '').lower()
        tx_category = transaction.get('category', '').lower()
        
        if bill_category == tx_category:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _update_transaction_match(self, transaction_id: str, bill_id: str) -> bool:
        """Update transaction with matched bill ID.
        
        Args:
            transaction_id: ID of the transaction
            bill_id: ID of the matched bill
            
        Returns:
            True if update successful
        """
        # Get all transactions
        all_transactions = self.account_manager.get_all_transactions()
        
        # Find and update the transaction
        for tx in all_transactions:
            if self._get_transaction_id(tx) == transaction_id:
                tx['matched_to_bill_id'] = bill_id
                tx['status'] = 'posted'  # Mark as posted since it matched a bill
                
                # Save updated transactions
                data = self.account_manager._load_yaml(self.account_manager.transactions_file)
                data['transactions'] = all_transactions
                self.account_manager._save_yaml(self.account_manager.transactions_file, data)
                return True
        
        return False
    
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
            if bill.get('status') in ['pending', 'scheduled'] and not bill.get('matched_transaction_id')
        ]
        
        return unmatched
