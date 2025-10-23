"""Credit Card Manager - Hanterar kreditkortskonton och transaktioner."""

import os
import yaml
import uuid
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd


class CreditCardManager:
    """Hanterar kreditkortskonton, transaktioner och balansräkning."""
    
    def __init__(self, yaml_dir: str = "yaml"):
        """Initialisera credit card manager med YAML-katalog."""
        self.yaml_dir = yaml_dir
        self.cards_file = os.path.join(yaml_dir, "credit_cards.yaml")
        self._ensure_cards_file()
    
    def _ensure_cards_file(self):
        """Se till att credit_cards.yaml finns."""
        if not os.path.exists(self.cards_file):
            os.makedirs(self.yaml_dir, exist_ok=True)
            with open(self.cards_file, 'w', encoding='utf-8') as f:
                yaml.dump({'cards': []}, f, default_flow_style=False, allow_unicode=True)
    
    def load_cards(self) -> List[Dict]:
        """Ladda alla kreditkort från YAML."""
        self._ensure_cards_file()
        with open(self.cards_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
            return data.get('cards', [])
    
    def save_cards(self, cards: List[Dict]):
        """Spara kreditkort till YAML."""
        with open(self.cards_file, 'w', encoding='utf-8') as f:
            yaml.dump({'cards': cards}, f, default_flow_style=False, allow_unicode=True)
    
    def add_card(self, name: str, card_type: str, last_four: str,
                 credit_limit: float, display_color: str = "#1f77b4",
                 icon: str = "credit-card", initial_balance: float = 0.0) -> Dict:
        """Lägg till ett nytt kreditkort.
        
        Args:
            name: Kortnamn (t.ex. "Amex Platinum", "Mastercard Gold")
            card_type: Korttyp (Amex, Mastercard, Visa, etc)
            last_four: Sista 4 siffrorna på kortet
            credit_limit: Kreditgräns i SEK
            display_color: Färg för visualisering (hex-kod)
            icon: Ikon-namn för kortet
            initial_balance: Föregående saldo/faktura (för om du inte importerar från början)
            
        Returns:
            Det nya kortet som dict
        """
        cards = self.load_cards()
        
        # Generera unikt ID
        card_id = f"CARD-{str(uuid.uuid4())[:8]}"
        
        # Calculate available credit based on initial balance
        available_credit = credit_limit - initial_balance
        
        card = {
            'id': card_id,
            'name': name,
            'card_type': card_type,
            'last_four': last_four,
            'credit_limit': credit_limit,
            'current_balance': initial_balance,  # Start with initial/previous balance
            'available_credit': available_credit,  # Available credit after initial balance
            'display_color': display_color,
            'icon': icon,
            'transactions': [],  # List of transactions
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'active'  # active, closed
        }
        
        cards.append(card)
        self.save_cards(cards)
        return card
    
    def get_cards(self, status: Optional[str] = None) -> List[Dict]:
        """Hämta alla kreditkort, filtrerat på status om angivet.
        
        Args:
            status: 'active' eller 'closed', eller None för alla
            
        Returns:
            Lista med kreditkort
        """
        cards = self.load_cards()
        
        if status:
            cards = [c for c in cards if c.get('status') == status]
        
        return cards
    
    def get_card_by_id(self, card_id: str) -> Optional[Dict]:
        """Hämta ett kreditkort med ID."""
        cards = self.load_cards()
        for card in cards:
            if card.get('id') == card_id:
                return card
        return None
    
    def update_card(self, card_id: str, updates: Dict) -> bool:
        """Uppdatera ett kreditkort.
        
        Args:
            card_id: ID för kortet
            updates: Dict med fält att uppdatera
            
        Returns:
            True om uppdateringen lyckades
        """
        cards = self.load_cards()
        
        for card in cards:
            if card.get('id') == card_id:
                card.update(updates)
                self.save_cards(cards)
                return True
        
        return False
    
    def delete_card(self, card_id: str) -> bool:
        """Ta bort ett kreditkort.
        
        Args:
            card_id: ID för kortet
            
        Returns:
            True om borttagningen lyckades
        """
        cards = self.load_cards()
        initial_count = len(cards)
        cards = [c for c in cards if c.get('id') != card_id]
        
        if len(cards) < initial_count:
            self.save_cards(cards)
            return True
        
        return False
    
    def _is_duplicate_transaction(self, card: Dict, date: str, description: str, 
                                   amount: float, card_member: str = "") -> bool:
        """Check if a transaction already exists to avoid duplicates.
        
        Args:
            card: Card dictionary to check
            date: Transaction date
            description: Transaction description
            amount: Transaction amount
            card_member: Optional card member name
            
        Returns:
            True if duplicate found, False otherwise
        """
        existing_txs = card.get('transactions', [])
        
        # Disable simple duplicate detection to allow multiple transactions
        # with same date/amount/description (e.g., 5 KLM purchases on same day)
        # Instead, we'll use a more sophisticated approach below
        return False
    
    def add_transaction(self, card_id: str, date: str, description: str,
                       amount: float, category: str = "Övrigt",
                       subcategory: str = "", vendor: str = "",
                       card_member: str = "", account_number: str = "",
                       posting_date: str = "", skip_duplicate_check: bool = False) -> Optional[Dict]:
        """Lägg till en transaktion till ett kreditkort.
        
        Args:
            card_id: ID för kortet
            date: Transaktionsdatum (YYYY-MM-DD) - när köpet gjordes
            description: Beskrivning
            amount: Belopp (negativt för utgifter, positivt för återbetalningar)
            category: Kategori
            subcategory: Underkategori
            vendor: Leverantör/handlare
            card_member: Kortmedlem/innehavare (för tvillingkort)
            account_number: Kontonummer (sista 4-5 siffror)
            posting_date: Bokföringsdatum (YYYY-MM-DD) - när transaktionen påverkade saldo
            skip_duplicate_check: Om True, hoppa över duplikatkontroll (används för manuella tillägg)
            
        Returns:
            Den skapade transaktionen, eller None om kortet inte finns eller transaktionen är en duplikat
        """
        cards = self.load_cards()
        
        for card in cards:
            if card.get('id') == card_id:
                # Ensure transactions array exists
                if 'transactions' not in card:
                    card['transactions'] = []
                
                # Check for duplicates (unless explicitly skipped)
                if not skip_duplicate_check:
                    if self._is_duplicate_transaction(card, date, description, amount, card_member):
                        # Duplicate found - skip this transaction
                        return None
                
                # Generate transaction ID
                tx_id = f"TX-{str(uuid.uuid4())[:8]}"
                
                transaction = {
                    'id': tx_id,
                    'date': date,  # Transaction date (när köpet gjordes)
                    'posting_date': posting_date or date,  # Posting date (när det bokfördes), defaults to transaction date
                    'description': description,
                    'vendor': vendor or description,
                    'amount': amount,
                    'category': category,
                    'subcategory': subcategory,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # Add cardholder info if available
                if card_member:
                    transaction['card_member'] = card_member
                if account_number:
                    transaction['account_number'] = account_number
                
                card['transactions'].append(transaction)
                
                # Update card balance
                # Negative amounts increase the balance (purchases)
                # Positive amounts decrease the balance (payments)
                card['current_balance'] = card.get('current_balance', 0.0) - amount
                card['available_credit'] = card.get('credit_limit', 0.0) - card['current_balance']
                
                self.save_cards(cards)
                return transaction
        
        return None
    
    def detect_card_from_csv(self, csv_path: str) -> Optional[str]:
        """Auto-detect which card to import to based on account number in CSV.
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            Card ID if detected, None otherwise
        """
        try:
            df = pd.read_csv(csv_path)  # Read all rows
            df.columns = [col.strip().lower() for col in df.columns]
            
            # Map Swedish column name
            if 'konto #' in df.columns:
                df.rename(columns={'konto #': 'account_number'}, inplace=True)
            
            # Look for account_number column
            if 'account_number' not in df.columns:
                return None
            
            # Extract account numbers from CSV (last 4-5 digits)
            account_numbers = df['account_number'].dropna().astype(str).unique()
            
            # Get all active cards
            cards = self.get_cards(status='active')
            
            # Try to match by last digits
            for account_num in account_numbers:
                # Extract last digits (support both 4 and 5 digit formats)
                account_num_clean = account_num.strip().replace('-', '')
                if len(account_num_clean) >= 4:
                    last_digits = account_num_clean[-5:]  # Get last 5 digits
                    
                    for card in cards:
                        card_last = card.get('last_four', '').strip()
                        # Match either last 4 or last 5 digits
                        if card_last and (last_digits.endswith(card_last) or card_last in last_digits):
                            return card['id']
            
            return None
        except Exception:
            return None
    
    def import_transactions_from_csv(self, card_id: str, csv_path: str) -> Dict[str, int]:
        """Importera transaktioner från CSV eller Excel-fil.
        
        CSV-filen förväntas ha kolumner: Date, Description, Amount
        Excel-filen (.xlsx) konverteras automatiskt till CSV-format
        Valfria kolumner: Vendor, Category, Subcategory, Card_member, Account_number
        
        Stöder både Amex-format (svensk) och generiskt format.
        Hanterar även kortmedlem (cardholder) för att spåra utgifter per person.
        Automatisk dublettdetektering förhindrar att samma transaktion importeras flera gånger.
        
        Args:
            card_id: ID för kortet
            csv_path: Sökväg till CSV- eller Excel-fil (.csv, .xlsx)
            
        Returns:
            Dict med 'imported' (antal nya) och 'duplicates' (antal dubbletter hoppade över)
        """
        card = self.get_card_by_id(card_id)
        if not card:
            return {'imported': 0, 'duplicates': 0}
        
        # Load file - automatically handle CSV or Excel
        file_extension = csv_path.lower().split('.')[-1]
        
        if file_extension == 'xlsx':
            # Read Excel file without skipping rows to get full structure
            # Mastercard Excel exports have multiple sections
            df_raw = pd.read_excel(csv_path, header=None)
            
            all_transactions = []
            current_cardholder = None
            
            # Scan through the file to find all transaction sections
            i = 0
            while i < len(df_raw):
                row = df_raw.iloc[i]
                first_col = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ''
                second_col = str(row.iloc[1]) if len(row) > 1 and pd.notna(row.iloc[1]) else ''
                
                # Check for cardholder line (e.g., "525412******9506  EVELINA FRÖJD")
                if '******' in first_col:
                    current_cardholder = first_col + ' ' + second_col if second_col else first_col
                    i += 1
                    continue
                
                # Check for section markers ("Köp/uttag" or "Totalt övriga händelser")
                if 'Köp/uttag' in first_col or 'övriga händelser' in first_col:
                    section_name = first_col
                    i += 1
                    
                    # Next row should be the header
                    if i < len(df_raw):
                        header_row = df_raw.iloc[i]
                        # Check if it's a proper header row (look for 'Datum' in any column)
                        if any('Datum' in str(cell) for cell in header_row):
                            i += 1
                            
                            # Extract transactions from this section
                            while i < len(df_raw):
                                tx_row = df_raw.iloc[i]
                                first_col_tx = str(tx_row.iloc[0]) if pd.notna(tx_row.iloc[0]) else ''
                                
                                # Check for section end markers
                                if 'Totalt belopp' in first_col_tx or 'Summa' in first_col_tx:
                                    break
                                
                                # Check for cardholder marker (next section starting)
                                if '******' in first_col_tx:
                                    break
                                
                                # Skip rows that are not transaction rows (like "Valutakurs:")
                                try:
                                    # Try to parse the date in 'YYYY-MM-DD' format
                                    datetime.strptime(first_col_tx, "%Y-%m-%d")
                                except (ValueError, TypeError):
                                    i += 1
                                    continue
                                
                                # This is a valid transaction row
                                tx_dict = {
                                    'Datum': tx_row.iloc[0] if pd.notna(tx_row.iloc[0]) else '',
                                    'Bokfört': tx_row.iloc[1] if len(tx_row) > 1 and pd.notna(tx_row.iloc[1]) else '',
                                    'Specifikation': tx_row.iloc[2] if len(tx_row) > 2 and pd.notna(tx_row.iloc[2]) else '',
                                    'Ort': tx_row.iloc[3] if len(tx_row) > 3 and pd.notna(tx_row.iloc[3]) else '',
                                    'Valuta': tx_row.iloc[4] if len(tx_row) > 4 and pd.notna(tx_row.iloc[4]) else '',
                                    'Utl. belopp': tx_row.iloc[5] if len(tx_row) > 5 and pd.notna(tx_row.iloc[5]) else 0,
                                    'Belopp': tx_row.iloc[6] if len(tx_row) > 6 and pd.notna(tx_row.iloc[6]) else 0,
                                    'Kortmedlem': current_cardholder if current_cardholder else ''
                                }
                                all_transactions.append(tx_dict)
                                i += 1
                            continue
                
                i += 1
            
            if all_transactions:
                df = pd.DataFrame(all_transactions)
            else:
                # If no transactions found, return empty
                return {'imported': 0, 'duplicates': 0}
        else:
            # Load CSV file normally
            df = pd.read_csv(csv_path)
        
        # Normalize column names
        df.columns = [col.strip().lower() for col in df.columns]
        
        # Map Swedish/English column names
        column_mapping = {
            'datum': 'date',
            'bokfört': 'posting_date',  # Swedish posting date column
            'beskrivning': 'description',
            'specifikation': 'description',  # Mastercard uses "Specifikation"
            'belopp': 'amount',
            'ort': 'vendor',  # Use city/location as vendor
            'leverantör': 'vendor',
            'kategori': 'category',
            'underkategori': 'subcategory',
            'kortmedlem': 'card_member',
            'konto #': 'account_number'
        }
        
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns and new_col not in df.columns:
                df.rename(columns={old_col: new_col}, inplace=True)
        
        # Required columns
        if 'date' not in df.columns or 'description' not in df.columns or 'amount' not in df.columns:
            raise ValueError("CSV must have Date, Description, and Amount columns")
        
        # Handles Swedish CSV format where amounts like "135,00" use a comma as decimal separator,
        # so we convert to string and replace commas with dots to ensure correct float parsing.
        df['amount'] = df['amount'].astype(str).str.replace(',', '.').str.replace('"', '').str.strip()
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        
        # Parse dates - handle both MM/DD/YYYY and YYYY-MM-DD formats
        if df['date'].dtype == 'object':
            # Try parsing as datetime, pandas will auto-detect format
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            # Convert to string format YYYY-MM-DD
            df['date'] = df['date'].dt.strftime('%Y-%m-%d')
        
        # Parse posting_date if present
        if 'posting_date' in df.columns:
            if df['posting_date'].dtype == 'object':
                df['posting_date'] = pd.to_datetime(df['posting_date'], errors='coerce')
                df['posting_date'] = df['posting_date'].dt.strftime('%Y-%m-%d')
        else:
            # If no posting_date column, use transaction date as posting date
            df['posting_date'] = df['date']
        
        # Detect if this is an Amex CSV format (has positive purchases and negative payments)
        # vs standard format (has negative purchases)
        # Amex format characteristics:
        # 1. Has positive values for purchases
        # 2. May have card_member or account_number columns
        # 3. Most transactions are positive (purchases), payments are less frequent
        has_positive = (df['amount'] > 0).any()
        has_negative = (df['amount'] < 0).any()
        has_amex_columns = 'card_member' in df.columns or 'account_number' in df.columns
        
        # Calculate percentage of positive values
        if len(df) > 0:
            positive_ratio = (df['amount'] > 0).sum() / len(df)
        else:
            positive_ratio = 0
        
        # Amex format if:
        # - Has Amex-specific columns, OR
        # - Has both positive and negative (mixed), OR
        # - Has mostly positive values (>70% are purchases)
        is_amex_format = has_amex_columns or (has_positive and has_negative) or (has_positive and positive_ratio > 0.7)
        
        # Import transactions
        imported_count = 0
        duplicate_count = 0
        
        for _, row in df.iterrows():
            # Skip rows with invalid data
            if pd.isna(row['amount']) or pd.isna(row['date']):
                continue
            
            # For Amex format: skip payments (negative values)
            # For standard format: accept all transactions
            if is_amex_format and row['amount'] < 0:
                continue
            
            # Auto-categorize if not provided
            from modules.core.categorize_expenses import load_categorization_rules, categorize_by_rules, categorize_by_ai_heuristic
            from modules.core.ai_trainer import AITrainer
            
            category = row.get('category', '')
            subcategory = row.get('subcategory', '')
            
            if not category:
                # Try to categorize
                description = str(row['description'])
                rules = load_categorization_rules()
                cat_result = categorize_by_rules(description, rules)
                if cat_result and cat_result.get('category', 'Övrigt') != 'Övrigt':
                    category = cat_result['category']
                    subcategory = cat_result.get('subcategory', '')
                else:
                    # Use AI heuristic (use negative for expense categorization)
                    trainer = AITrainer()
                    training_data = trainer.get_training_data()
                    cat_result = categorize_by_ai_heuristic(description, -abs(row['amount']), training_data)
                    if cat_result:
                        category = cat_result.get('category', 'Övrigt')
                        subcategory = cat_result.get('subcategory', '')
                    else:
                        category = 'Övrigt'
                        subcategory = ''
            
            # Normalize amount based on format
            # In our system, purchases are always stored as negative amounts (money spent)
            if is_amex_format:
                # Amex CSV has purchases as positive, so we negate them
                amount = -abs(row['amount'])
            else:
                # Standard format already has purchases as negative
                amount = float(row['amount'])
            
            # Extract card member/cardholder information
            card_member = row.get('card_member', '')
            account_number = row.get('account_number', '')
            
            # Add transaction (duplicate detection disabled to allow multiple
            # legitimate transactions with same date/amount/description)
            result = self.add_transaction(
                card_id=card_id,
                date=str(row['date']),
                description=str(row['description']),
                amount=amount,
                category=category,
                subcategory=subcategory,
                vendor=str(row.get('vendor', row['description'])),
                card_member=str(card_member) if pd.notna(card_member) else '',
                account_number=str(account_number) if pd.notna(account_number) else '',
                posting_date=str(row.get('posting_date', row['date']))  # Use posting date for balance calculation
            )
            
            if result:
                imported_count += 1
        
        return {'imported': imported_count, 'duplicates': 0}
    
    def get_transactions(self, card_id: str, category: Optional[str] = None,
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None,
                        use_posting_date: bool = False) -> List[Dict]:
        """Hämta transaktioner för ett kort med filtrering.
        
        Args:
            card_id: ID för kortet
            category: Filtrera på kategori (valfritt)
            start_date: Startdatum (YYYY-MM-DD, valfritt)
            end_date: Slutdatum (YYYY-MM-DD, valfritt)
            use_posting_date: Om True, använd posting_date för datumfiltrering istället för transaction date
            
        Returns:
            Lista med transaktioner
        """
        card = self.get_card_by_id(card_id)
        if not card:
            return []
        
        transactions = card.get('transactions', [])
        
        # Apply filters
        filtered = []
        for tx in transactions:
            if category and tx.get('category') != category:
                continue
            
            # Use posting_date for filtering if requested, otherwise use transaction date
            if use_posting_date:
                tx_date = tx.get('posting_date', tx.get('date', ''))
            else:
                tx_date = tx.get('date', '')
            
            if start_date and tx_date < start_date:
                continue
            if end_date and tx_date > end_date:
                continue
            
            filtered.append(tx)
        
        # Sort by posting_date for saldo accuracy, or by date if posting_date not available
        filtered.sort(key=lambda x: x.get('posting_date', x.get('date', '')), reverse=True)
        
        return filtered
    
    def get_card_summary(self, card_id: str, use_posting_date: bool = True) -> Dict:
        """Få sammanfattning för ett kort.
        
        IMPORTANT: Card balance (current_balance) is ALWAYS calculated based on posting_date,
        since this is when transactions actually affect the card statement and balance.
        
        Args:
            card_id: ID för kortet
            use_posting_date: Om True, använd posting_date för trendanalys (default: True för korrekt saldo)
            
        Returns:
            Dict med sammanfattning (balance, limit, transactions, categories, etc)
        """
        card = self.get_card_by_id(card_id)
        if not card:
            return {}
        
        transactions = card.get('transactions', [])
        
        # Calculate stats
        total_spent = sum(abs(tx['amount']) for tx in transactions if tx['amount'] < 0)
        total_payments = sum(tx['amount'] for tx in transactions if tx['amount'] > 0)
        
        # Category breakdown
        category_totals = {}
        for tx in transactions:
            if tx['amount'] < 0:  # Only count purchases
                cat = tx.get('category', 'Övrigt')
                category_totals[cat] = category_totals.get(cat, 0) + abs(tx['amount'])
        
        # Top vendors
        vendor_totals = {}
        for tx in transactions:
            if tx['amount'] < 0:
                vendor = tx.get('vendor', 'Unknown')
                vendor_totals[vendor] = vendor_totals.get(vendor, 0) + abs(tx['amount'])
        
        top_vendors = sorted(vendor_totals.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Cardholder breakdown (for dual/supplementary cards)
        cardholder_totals = {}
        for tx in transactions:
            if tx['amount'] < 0:  # Only count purchases
                member = tx.get('card_member', '')
                if member:
                    cardholder_totals[member] = cardholder_totals.get(member, 0) + abs(tx['amount'])
        
        return {
            'card_id': card_id,
            'name': card['name'],
            'card_type': card['card_type'],
            'current_balance': card.get('current_balance', 0.0),
            'credit_limit': card['credit_limit'],
            'available_credit': card.get('available_credit', card['credit_limit']),
            'utilization_percent': (card.get('current_balance', 0.0) / card['credit_limit'] * 100) if card['credit_limit'] > 0 else 0,
            'total_transactions': len(transactions),
            'total_spent': total_spent,
            'total_payments': total_payments,
            'category_breakdown': category_totals,
            'top_vendors': top_vendors,
            'cardholder_breakdown': cardholder_totals
        }
    
    def calculate_balance_at_date(self, card_id: str, as_of_date: str, 
                                  use_posting_date: bool = True) -> float:
        """Beräkna kortets saldo vid ett specifikt datum.
        
        VIKTIGT: För korrekt saldo, använd alltid posting_date (bokföringsdatum),
        eftersom det är när transaktioner faktiskt påverkar kontoutdraget.
        
        Args:
            card_id: ID för kortet
            as_of_date: Datum att beräkna saldo för (YYYY-MM-DD)
            use_posting_date: Om True, använd posting_date (rekommenderat för korrekt saldo)
            
        Returns:
            Saldo vid det angivna datumet
        """
        card = self.get_card_by_id(card_id)
        if not card:
            return 0.0
        
        transactions = card.get('transactions', [])
        # Start from initial balance if set on the card, otherwise 0.0
        balance = card.get('initial_balance', 0.0)
        
        for tx in transactions:
            # Determine which date to use
            if use_posting_date:
                tx_date = tx.get('posting_date', tx.get('date', ''))
            else:
                tx_date = tx.get('date', '')
            
            # Only include transactions on or before the as_of_date
            if tx_date and tx_date <= as_of_date:
                # Negative amounts increase balance (purchases)
                # Positive amounts decrease balance (payments)
                balance -= tx['amount']
        
        return balance
    
    def match_payment_to_card(self, card_id: str, payment_amount: float,
                             payment_date: str, transaction_id: Optional[str] = None) -> bool:
        """Matcha en betalning från bankkonto till kreditkortet.
        
        Uppdaterar endast kortets saldo. Lägger INTE till betalningen som en transaktion 
        på kreditkortet eftersom betalningar redan finns i bankkontoutdraget.
        
        Args:
            card_id: ID för kortet
            payment_amount: Belopp som betalats (positivt tal)
            payment_date: Betalningsdatum
            transaction_id: ID för banktransaktionen (valfritt)
            
        Returns:
            True om matchningen lyckades
        """
        cards = self.load_cards()
        
        for card in cards:
            if card.get('id') == card_id:
                # Update balance only (don't add payment as transaction)
                # Payments are already in bank account transactions
                card['current_balance'] = card.get('current_balance', 0.0) - payment_amount
                card['available_credit'] = card.get('credit_limit', 0.0) - card['current_balance']
                
                # Track the payment for reference (optional metadata)
                if 'payment_history' not in card:
                    card['payment_history'] = []
                
                card['payment_history'].append({
                    'date': payment_date,
                    'amount': payment_amount,
                    'matched_transaction_id': transaction_id
                })
                
                self.save_cards(cards)
                return True
        
        return False
    
    def update_transaction(self, card_id: str, transaction_id: str, 
                          category: Optional[str] = None,
                          subcategory: Optional[str] = None,
                          description: Optional[str] = None,
                          amount: Optional[float] = None) -> bool:
        """Uppdatera en kreditkortstransaktion.
        
        Args:
            card_id: ID för kortet
            transaction_id: ID för transaktionen
            category: Ny kategori (valfritt)
            subcategory: Ny underkategori (valfritt)
            description: Ny beskrivning (valfritt)
            amount: Nytt belopp (valfritt)
            
        Returns:
            True om uppdateringen lyckades
        """
        cards = self.load_cards()
        
        for card in cards:
            if card.get('id') == card_id:
                transactions = card.get('transactions', [])
                
                for tx in transactions:
                    if tx.get('id') == transaction_id:
                        # Update fields if provided
                        if category is not None:
                            tx['category'] = category
                        if subcategory is not None:
                            tx['subcategory'] = subcategory
                        if description is not None:
                            tx['description'] = description
                        if amount is not None:
                            # Need to recalculate balance
                            old_amount = tx['amount']
                            tx['amount'] = amount
                            
                            # Adjust card balance
                            balance_diff = old_amount - amount
                            card['current_balance'] = card.get('current_balance', 0.0) + balance_diff
                            card['available_credit'] = card.get('credit_limit', 0.0) - card['current_balance']
                        
                        tx['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        self.save_cards(cards)
                        return True
                
                return False
        
        return False
    
    def delete_transaction(self, card_id: str, transaction_id: str) -> bool:
        """Ta bort en kreditkortstransaktion.
        
        Args:
            card_id: ID för kortet
            transaction_id: ID för transaktionen
            
        Returns:
            True om borttagningen lyckades
        """
        cards = self.load_cards()
        
        for card in cards:
            if card.get('id') == card_id:
                transactions = card.get('transactions', [])
                
                # Find and remove transaction
                for i, tx in enumerate(transactions):
                    if tx.get('id') == transaction_id:
                        removed_tx = transactions.pop(i)
                        
                        # Adjust card balance (reverse the transaction)
                        card['current_balance'] = card.get('current_balance', 0.0) - removed_tx['amount']
                        card['available_credit'] = card.get('credit_limit', 0.0) - card['current_balance']
                        
                        self.save_cards(cards)
                        return True
                
                return False
        
        return False
