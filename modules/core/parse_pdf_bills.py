"""Parse PDF Bills - Extraherar fakturor från PDF-filer."""

import os
from typing import List, Dict, Optional


class PDFBillParser:
    """Parser för att extrahera fakturor från PDF-filer (placeholder implementation)."""
    
    def __init__(self):
        """Initialisera PDF parser."""
        self.supported_formats = ['pdf']
    
    def parse_pdf(self, pdf_path: str) -> List[Dict]:
        """Extrahera fakturor från en PDF-fil.
        
        OBS: Detta är en placeholder-implementation för Sprint 4.
        En fullständig implementation skulle använda bibliotek som pdfplumber
        eller pytesseract för OCR.
        
        Args:
            pdf_path: Sökväg till PDF-filen
            
        Returns:
            Lista med extraherade fakturor
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF-fil hittades inte: {pdf_path}")
        
        # Placeholder: Returnera exempeldata
        # I en riktig implementation skulle vi använda:
        # - pdfplumber för att extrahera text
        # - Regex eller AI för att hitta fakturainformation
        # - OCR för skannade PDF:er
        
        return self._get_example_bills()
    
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
    
    def import_bills_to_manager(self, pdf_path: str, bill_manager) -> int:
        """Importera fakturor från PDF till bill manager.
        
        Args:
            pdf_path: Sökväg till PDF-filen
            bill_manager: Instans av BillManager
            
        Returns:
            Antal importerade fakturor
        """
        bills = self.parse_pdf(pdf_path)
        count = 0
        
        for bill_data in bills:
            bill_manager.add_bill(
                name=bill_data['name'],
                amount=bill_data['amount'],
                due_date=bill_data['due_date'],
                description=bill_data.get('description', ''),
                category=bill_data.get('category', 'Övrigt')
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
