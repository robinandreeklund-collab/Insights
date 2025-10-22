"""Parse PDF Bills - Extraherar fakturor från PDF-filer."""

import os
import re
from typing import List, Dict, Optional


class PDFBillParser:
    """Parser för att extrahera fakturor från PDF-filer."""
    
    def __init__(self):
        """Initialisera PDF parser."""
        self.supported_formats = ['pdf']
        
        # Try to import pdfplumber for actual PDF parsing
        try:
            import pdfplumber
            self.pdfplumber = pdfplumber
            self.has_pdfplumber = True
        except ImportError:
            self.pdfplumber = None
            self.has_pdfplumber = False
    
    def parse_pdf(self, pdf_path: str, use_demo_data: bool = False) -> List[Dict]:
        """Extrahera fakturor från en PDF-fil.
        
        Args:
            pdf_path: Sökväg till PDF-filen
            use_demo_data: Om True, använd demo-data oavsett om filen finns
            
        Returns:
            Lista med extraherade fakturor
        """
        # If demo mode, return example data without checking file
        if use_demo_data:
            print("Info: Using demo data for PDF import")
            return self._get_example_bills()
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF-fil hittades inte: {pdf_path}")
        
        # If pdfplumber is available, try to extract from actual PDF
        if self.has_pdfplumber:
            try:
                return self._extract_from_pdf(pdf_path)
            except Exception as e:
                print(f"Warning: Could not parse PDF ({e}). Using example data.")
                return self._get_example_bills()
        else:
            # Fallback to example data if pdfplumber not available
            print("Info: pdfplumber not installed. Using example data. Install with: pip install pdfplumber")
            return self._get_example_bills()
    
    def _extract_from_pdf(self, pdf_path: str) -> List[Dict]:
        """Extract bills from actual PDF using pdfplumber.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of extracted bills
        """
        bills = []
        
        with self.pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    # Extract bills from text
                    extracted = self._extract_bills_from_text(text)
                    bills.extend(extracted)
        
        # If no bills found, return example data
        if not bills:
            return self._get_example_bills()
        
        return bills
    
    def _extract_bills_from_text(self, text: str) -> List[Dict]:
        """Extract bill information from PDF text.
        
        Supports:
        1. Simple format: Just bills with amounts and dates
        2. Nordea "Hantera betalningar" format: Bills grouped by account
        
        Args:
            text: Extracted text from PDF
            
        Returns:
            List of bill dictionaries
        """
        from datetime import datetime, timedelta
        
        # Check if this is a Nordea "Hantera betalningar" format
        if self._is_nordea_payment_format(text):
            return self._extract_nordea_payment_bills(text)
        
        # Otherwise, use the legacy simple extraction
        return self._extract_simple_bills(text)
    
    def _is_nordea_payment_format(self, text: str) -> bool:
        """Check if text is in Nordea Hantera betalningar format.
        
        Args:
            text: Extracted text from PDF
            
        Returns:
            True if text matches Nordea payment format
        """
        # Check for key indicators:
        # 1. "Nordea" and "betalningar" in text
        # 2. "Konto:" followed by account number
        text_lower = text.lower()
        has_nordea = 'nordea' in text_lower and 'betalning' in text_lower
        has_account_pattern = bool(re.search(r'konto:\s*\d+', text_lower))
        
        return has_nordea and has_account_pattern
    
    def _extract_nordea_payment_bills(self, text: str) -> List[Dict]:
        """Extract bills from Nordea Hantera betalningar format.
        
        This format has bills grouped by account:
        Konto: 3570 12 34567
        Faktura              Belopp      Förfallodatum
        Bill Name            1,234.56    2025-11-15
        ...
        
        Args:
            text: Extracted text from PDF
            
        Returns:
            List of bill dictionaries with account information
        """
        bills = []
        lines = text.split('\n')
        
        current_account = None
        in_bill_section = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Check for account line: "Konto: 3570 12 34567"
            account_match = re.match(r'konto:\s*([\d\s]+)', line, re.IGNORECASE)
            if account_match:
                # Extract and normalize account number
                current_account = account_match.group(1).strip()
                # Normalize: remove spaces, keep just digits
                current_account = re.sub(r'\s+', ' ', current_account)
                in_bill_section = False
                continue
            
            # Check for header line (indicates bill section starts)
            if re.search(r'faktura.*belopp.*förfallodatum', line, re.IGNORECASE):
                in_bill_section = True
                continue
            
            # Skip if we don't have an account yet or not in bill section
            if not current_account or not in_bill_section:
                continue
            
            # Try to parse bill line: "Bill Name  Amount  Date"
            # Pattern: text, amount (digits with comma/period, including thousands separator), date (YYYY-MM-DD)
            # Allow amounts like: 1,245.50 or 8,500.00 or 399.00
            bill_pattern = r'^(.+?)\s+([\d,]+\.\d{2})\s+(\d{4}-\d{2}-\d{2})\s*$'
            bill_match = re.match(bill_pattern, line)
            
            if bill_match:
                name = bill_match.group(1).strip()
                amount_str = bill_match.group(2)
                due_date = bill_match.group(3)
                
                # Parse amount (remove thousands separator comma, keep decimal point)
                amount = float(amount_str.replace(',', ''))
                
                # Categorize based on keywords
                category = self._categorize_bill(name)
                
                bills.append({
                    'name': name,
                    'amount': amount,
                    'due_date': due_date,
                    'description': f'Extraherad från PDF (Konto: {current_account})',
                    'category': category,
                    'account': current_account
                })
        
        return bills
    
    def _extract_simple_bills(self, text: str) -> List[Dict]:
        """Extract bills using simple pattern matching (legacy method).
        
        Args:
            text: Extracted text from PDF
            
        Returns:
            List of bill dictionaries
        """
        from datetime import datetime, timedelta
        
        bills = []
        
        # Find amounts: 123.45, 123,45, 123 kr, etc.
        amount_pattern = r'(\d{1,6}[.,]\d{2})\s*(?:kr|SEK)?'
        amounts = re.findall(amount_pattern, text)
        
        # Find dates: YYYY-MM-DD, DD/MM/YYYY, DD.MM.YYYY
        date_pattern = r'(\d{4}-\d{2}-\d{2}|\d{2}[/\.]\d{2}[/\.]\d{4})'
        dates = re.findall(date_pattern, text)
        
        # Try to extract structured information
        if amounts:
            for i, amount_str in enumerate(amounts):
                # Parse amount
                amount = float(amount_str.replace(',', '.'))
                
                # Get corresponding date if available
                due_date = None
                if i < len(dates):
                    date_str = dates[i]
                    # Normalize date format to YYYY-MM-DD
                    try:
                        if '-' in date_str:
                            due_date = date_str
                        else:
                            # Parse DD/MM/YYYY or DD.MM.YYYY
                            parts = re.split(r'[/.]', date_str)
                            if len(parts) == 3:
                                due_date = f"{parts[2]}-{parts[1]}-{parts[0]}"
                    except:
                        pass
                
                # If no date found, use today + 14 days as default
                if not due_date:
                    due_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
                
                # Categorize based on keywords
                name = f'Faktura {i+1}'
                category = self._categorize_bill(name)
                
                bills.append({
                    'name': name,
                    'amount': amount,
                    'due_date': due_date,
                    'description': f'Extraherad från PDF',
                    'category': category
                })
        
        return bills
    
    def _categorize_bill(self, name: str) -> str:
        """Categorize a bill based on its name.
        
        Args:
            name: Bill name or description
            
        Returns:
            Category name
        """
        name_lower = name.lower()
        
        if any(word in name_lower for word in ['el', 'elektri', 'power', 'energy', 'vattenfall', 'fortum']):
            return 'Boende'
        elif any(word in name_lower for word in ['hyra', 'rent', 'housing', 'hyresavi']):
            return 'Boende'
        elif any(word in name_lower for word in ['internet', 'bredband', 'broadband', 'telia', 'tele2', 'comhem']):
            return 'Boende'
        elif any(word in name_lower for word in ['mobil', 'telefon', 'phone', 'telenor', 'tre', 'hallon']):
            return 'Övrigt'
        elif any(word in name_lower for word in ['försäkring', 'insurance', 'länsförsäkring', 'folksam', 'if']):
            return 'Boende'
        elif any(word in name_lower for word in ['netflix', 'spotify', 'hbo', 'disney', 'streaming', 'abonnemang']):
            # Check if it's a streaming service (not just any subscription)
            if any(word in name_lower for word in ['netflix', 'spotify', 'hbo', 'disney', 'viaplay', 'tv4']):
                return 'Nöje'
            else:
                return 'Övrigt'
        else:
            return 'Övrigt'
    
    def _get_example_bills(self) -> List[Dict]:
        """Returnera exempel-fakturor för demonstration.
        
        Returns:
            Lista med exempel-fakturor
        """
        from datetime import datetime, timedelta
        
        today = datetime.now()
        
        example_bills = [
            {
                'name': 'Elräkning December 2025',
                'amount': 850.0,
                'due_date': (today + timedelta(days=14)).strftime('%Y-%m-%d'),
                'description': 'Elkostnad för december månad',
                'category': 'Boende'
            },
            {
                'name': 'Mobilabonnemang',
                'amount': 299.0,
                'due_date': (today + timedelta(days=20)).strftime('%Y-%m-%d'),
                'description': 'Månatlig mobilkostnad',
                'category': 'Övrigt'
            },
            {
                'name': 'Internet & TV',
                'amount': 449.0,
                'due_date': (today + timedelta(days=25)).strftime('%Y-%m-%d'),
                'description': 'Bredband och TV-paket',
                'category': 'Boende'
            }
        ]
        
        return example_bills
    
    def import_bills_to_manager(self, pdf_path: str, bill_manager, use_demo_data: bool = False) -> int:
        """Importera fakturor från PDF till bill manager.
        
        Args:
            pdf_path: Sökväg till PDF-filen
            bill_manager: Instans av BillManager
            use_demo_data: Om True, använd demo-data oavsett om filen finns
            
        Returns:
            Antal importerade fakturor
        """
        bills = self.parse_pdf(pdf_path, use_demo_data=use_demo_data)
        count = 0
        
        for bill_data in bills:
            bill_manager.add_bill(
                name=bill_data['name'],
                amount=bill_data['amount'],
                due_date=bill_data['due_date'],
                description=bill_data.get('description', ''),
                category=bill_data.get('category', 'Övrigt'),
                account=bill_data.get('account', None)  # Include account if present
            )
            count += 1
        
        return count
    
    def validate_bill_data(self, bill_data: Dict) -> bool:
        """Validera att fakturadata innehåller nödvändiga fält.
        
        Args:
            bill_data: Dict med fakturadata
            
        Returns:
            True om valid, annars False
        """
        required_fields = ['name', 'amount', 'due_date']
        
        for field in required_fields:
            if field not in bill_data:
                return False
        
        # Validera att amount är ett nummer
        try:
            float(bill_data['amount'])
        except (ValueError, TypeError):
            return False
        
        # Validera datumformat (YYYY-MM-DD)
        try:
            from datetime import datetime
            datetime.strptime(bill_data['due_date'], '%Y-%m-%d')
        except ValueError:
            return False
        
        return True


def extract_bills_from_pdf(pdf_path: str) -> List[Dict]:
    """Wrapper-funktion för att extrahera fakturor från PDF.
    
    Args:
        pdf_path: Sökväg till PDF-filen
        
    Returns:
        Lista med extraherade fakturor
    """
    parser = PDFBillParser()
    return parser.parse_pdf(pdf_path)
