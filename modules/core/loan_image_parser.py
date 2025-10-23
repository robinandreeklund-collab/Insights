"""Loan Image Parser - Extract loan details from images using OCR."""

import re
import sys
from datetime import datetime
from typing import Dict, Optional, List, Any
try:
    from PIL import Image
    import pytesseract
    import cv2
    import numpy as np
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


def check_tesseract_installed():
    """Check if Tesseract OCR executable is installed and accessible."""
    if not OCR_AVAILABLE:
        return False, "Python OCR packages not installed"
    
    try:
        # Try to get Tesseract version to verify it's installed
        pytesseract.get_tesseract_version()
        return True, "Tesseract is installed"
    except pytesseract.TesseractNotFoundError:
        if sys.platform == 'win32':
            return False, (
                "Tesseract OCR är inte installerat på din dator.\n\n"
                "För Windows:\n"
                "1. Ladda ner Tesseract från: https://github.com/UB-Mannheim/tesseract/wiki\n"
                "2. Installera med standardinställningar\n"
                "3. Starta om dashboarden\n\n"
                "Alternativt kan du ange sökvägen manuellt i Python:\n"
                "pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'"
            )
        else:
            return False, (
                "Tesseract OCR är inte installerat.\n\n"
                "För Linux/Mac:\n"
                "sudo apt-get install tesseract-ocr tesseract-ocr-swe  # Ubuntu/Debian\n"
                "brew install tesseract tesseract-lang  # Mac\n\n"
                "Starta sedan om dashboarden."
            )
    except Exception as e:
        return False, f"Kunde inte verifiera Tesseract installation: {str(e)}"


class LoanImageParser:
    """Extract loan information from images using OCR."""
    
    def __init__(self):
        """Initialize the loan image parser."""
        if not OCR_AVAILABLE:
            raise ImportError(
                "OCR dependencies not available. Install with: "
                "pip install pytesseract Pillow opencv-python"
            )
        
        # Check if Tesseract executable is available
        is_installed, message = check_tesseract_installed()
        if not is_installed:
            raise RuntimeError(message)
    
    def parse_loan_image(self, image_path: str) -> Dict[str, Any]:
        """Parse a loan information image and extract key details.
        
        Args:
            image_path: Path to the loan image file
            
        Returns:
            Dictionary with extracted loan details
        """
        # Read and preprocess image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not read image from {image_path}")
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding to improve OCR
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        
        # Perform OCR
        text = pytesseract.image_to_string(thresh, lang='swe+eng')
        
        # Extract fields from OCR text
        loan_data = self._extract_fields(text)
        
        return loan_data
    
    def _extract_fields(self, text: str) -> Dict[str, Any]:
        """Extract loan fields from OCR text.
        
        Args:
            text: OCR extracted text
            
        Returns:
            Dictionary with extracted fields
        """
        lines = text.split('\n')
        loan_data = {
            'loan_number': None,
            'original_amount': None,
            'current_amount': None,
            'amortized': None,
            'base_interest_rate': None,
            'discount': None,
            'effective_interest_rate': None,
            'rate_period': None,
            'binding_period': None,
            'next_change_date': None,
            'disbursement_date': None,
            'borrowers': [],
            'borrower_shares': {},
            'currency': 'SEK',
            'collateral': None,
            'lender': None,
            'payment_interval': None,
            'payment_account': None,
            'repayment_account': None,
            'description': '',
        }
        
        # Extract loan number
        loan_number_match = re.search(r'(?:Lån|Loan|Lånenummer|Loan\s*number)[:\s]*(\d+[-\s]?\d*)', text, re.IGNORECASE)
        if loan_number_match:
            loan_data['loan_number'] = loan_number_match.group(1).strip()
        
        # Extract amounts (look for patterns like "2 000 000", "2.000.000", "2000000")
        # Original amount
        original_patterns = [
            r'(?:Ursprungligt|Original|Huvudbelopp)[:\s]*([0-9\s.,]+)\s*(?:kr|SEK)?',
            r'(?:Principal)[:\s]*([0-9\s.,]+)',
        ]
        for pattern in original_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                loan_data['original_amount'] = self._parse_amount(match.group(1))
                break
        
        # Current amount
        current_patterns = [
            r'(?:Nuvarande|Current|Aktuellt\s*belopp)[:\s]*([0-9\s.,]+)\s*(?:kr|SEK)?',
            r'(?:Saldo|Balance)[:\s]*([0-9\s.,]+)',
        ]
        for pattern in current_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                loan_data['current_amount'] = self._parse_amount(match.group(1))
                break
        
        # Amortized amount
        amortized_patterns = [
            r'(?:Amorterat|Amortized)[:\s]*([0-9\s.,]+)\s*(?:kr|SEK)?',
        ]
        for pattern in amortized_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                loan_data['amortized'] = self._parse_amount(match.group(1))
                break
        
        # Interest rates (look for percentages)
        # Base rate
        base_rate_patterns = [
            r'(?:Basränta|Base\s*rate)[:\s]*([0-9.,]+)\s*%',
            r'(?:Grundränta)[:\s]*([0-9.,]+)\s*%',
        ]
        for pattern in base_rate_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                loan_data['base_interest_rate'] = self._parse_decimal(match.group(1))
                break
        
        # Discount
        discount_patterns = [
            r'(?:Rabatt|Discount)[:\s]*([0-9.,]+)\s*%',
        ]
        for pattern in discount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                loan_data['discount'] = self._parse_decimal(match.group(1))
                break
        
        # Effective interest rate
        effective_patterns = [
            r'(?:Effektiv|Effective)\s*(?:ränta|rate)[:\s]*([0-9.,]+)\s*%',
            r'(?:Årsränta)[:\s]*([0-9.,]+)\s*%',
        ]
        for pattern in effective_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                loan_data['effective_interest_rate'] = self._parse_decimal(match.group(1))
                break
        
        # Rate period
        rate_period_patterns = [
            r'(?:Ränteperiod|Rate\s*period)[:\s]*([0-9]+)\s*(?:mån|months?|år|years?)',
        ]
        for pattern in rate_period_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                loan_data['rate_period'] = match.group(1).strip()
                break
        
        # Binding period
        binding_patterns = [
            r'(?:Bindningstid|Binding\s*period)[:\s]*([0-9]+)\s*(?:mån|months?|år|years?)',
        ]
        for pattern in binding_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                loan_data['binding_period'] = match.group(1).strip()
                break
        
        # Dates (YYYY-MM-DD or DD/MM/YYYY or similar)
        # Next change date
        next_change_patterns = [
            r'(?:Nästa\s*förändring|Next\s*change)[:\s]*(\d{4}[-/]\d{2}[-/]\d{2})',
            r'(?:Nästa\s*förändring|Next\s*change)[:\s]*(\d{2}[-/]\d{2}[-/]\d{4})',
        ]
        for pattern in next_change_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                loan_data['next_change_date'] = self._parse_date(match.group(1))
                break
        
        # Disbursement date
        disbursement_patterns = [
            r'(?:Utbetalning|Disbursement)[:\s]*(\d{4}[-/]\d{2}[-/]\d{2})',
            r'(?:Utbetalning|Disbursement)[:\s]*(\d{2}[-/]\d{2}[-/]\d{4})',
        ]
        for pattern in disbursement_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                loan_data['disbursement_date'] = self._parse_date(match.group(1))
                break
        
        # Borrowers - look for names (this is tricky, we'll look for common patterns)
        borrower_patterns = [
            r'(?:Låntagare|Borrower)[:\s]*([A-ZÅÄÖ][a-zåäö]+\s+[A-ZÅÄÖ][a-zåäö]+)',
        ]
        for pattern in borrower_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                borrower = match.group(1).strip()
                if borrower and borrower not in loan_data['borrowers']:
                    loan_data['borrowers'].append(borrower)
        
        # Currency
        currency_match = re.search(r'\b(SEK|EUR|USD|NOK|DKK)\b', text)
        if currency_match:
            loan_data['currency'] = currency_match.group(1)
        
        # Collateral
        collateral_patterns = [
            r'(?:Säkerhet|Collateral)[:\s]*([^\n]+)',
        ]
        for pattern in collateral_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                loan_data['collateral'] = match.group(1).strip()
                break
        
        # Lender
        lender_patterns = [
            r'(?:Långivare|Lender|Bank)[:\s]*([^\n]+)',
        ]
        for pattern in lender_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                loan_data['lender'] = match.group(1).strip()
                break
        
        # Payment interval
        interval_pattern = r'(?:Betalningsintervall|Payment\s*interval)[:\s]*([^\n]+)'
        match = re.search(interval_pattern, text, re.IGNORECASE)
        if match:
            loan_data['payment_interval'] = match.group(1).strip()
        
        # Account numbers (look for Swedish account number format)
        account_patterns = [
            r'(?:Betalkonto|Payment\s*account)[:\s]*(\d{4}[-\s]?\d+)',
            r'(?:Återbetalkonto|Repayment\s*account)[:\s]*(\d{4}[-\s]?\d+)',
        ]
        payment_match = re.search(account_patterns[0], text, re.IGNORECASE)
        if payment_match:
            loan_data['payment_account'] = payment_match.group(1).replace(' ', '').replace('-', '')
        
        repayment_match = re.search(account_patterns[1], text, re.IGNORECASE)
        if repayment_match:
            loan_data['repayment_account'] = repayment_match.group(1).replace(' ', '').replace('-', '')
        
        return loan_data
    
    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """Parse an amount string to float.
        
        Args:
            amount_str: Amount string like "2 000 000" or "2.000.000,50"
            
        Returns:
            Float value or None
        """
        try:
            # Remove spaces
            cleaned = amount_str.replace(' ', '')
            # Handle European format (. as thousands, , as decimal)
            if ',' in cleaned and '.' in cleaned:
                # European format: 2.000.000,50
                cleaned = cleaned.replace('.', '').replace(',', '.')
            elif ',' in cleaned:
                # Just comma as decimal
                cleaned = cleaned.replace(',', '.')
            # Remove any remaining non-numeric except .
            cleaned = re.sub(r'[^\d.]', '', cleaned)
            return float(cleaned) if cleaned else None
        except (ValueError, AttributeError):
            return None
    
    def _parse_decimal(self, decimal_str: str) -> Optional[float]:
        """Parse a decimal string to float.
        
        Args:
            decimal_str: Decimal string like "3,5" or "3.5"
            
        Returns:
            Float value or None
        """
        try:
            # Replace comma with dot
            cleaned = decimal_str.replace(',', '.')
            return float(cleaned) if cleaned else None
        except (ValueError, AttributeError):
            return None
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse a date string to YYYY-MM-DD format.
        
        Args:
            date_str: Date string in various formats
            
        Returns:
            Date in YYYY-MM-DD format or None
        """
        try:
            # Try different formats
            formats = ['%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y']
            for fmt in formats:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            return None
        except (ValueError, AttributeError):
            return None
    
    def parse_loan_from_base64(self, base64_data: str) -> Dict[str, Any]:
        """Parse a loan image from base64 encoded data.
        
        Args:
            base64_data: Base64 encoded image data
            
        Returns:
            Dictionary with extracted loan details
        """
        import base64
        import io
        
        # Remove data URI prefix if present
        if ',' in base64_data:
            base64_data = base64_data.split(',', 1)[1]
        
        # Decode base64
        image_data = base64.b64decode(base64_data)
        
        # Convert to numpy array
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise ValueError("Could not decode image from base64 data")
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        
        # Perform OCR
        text = pytesseract.image_to_string(thresh, lang='swe+eng')
        
        # Extract fields
        loan_data = self._extract_fields(text)
        
        return loan_data
