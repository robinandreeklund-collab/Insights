"""Amex Parser - Parse American Express CSV files and link to bills."""

import pandas as pd
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import re


class AmexParser:
    """Parser for American Express CSV files."""
    
    def __init__(self, bill_manager=None):
        """Initialize Amex parser.
        
        Args:
            bill_manager: Optional BillManager instance for bill linking
        """
        self.bill_manager = bill_manager
    
    def detect_amex_format(self, df: pd.DataFrame) -> bool:
        """Detect if a DataFrame is in Amex format.
        
        Args:
            df: DataFrame to check
            
        Returns:
            True if Amex format detected
        """
        # Amex CSVs typically have these columns
        amex_columns = ['date', 'description', 'card member', 'account #', 'amount']
        df_columns_lower = [col.lower() for col in df.columns]
        
        # Check if we have the key Amex columns
        has_amex_columns = all(col in df_columns_lower for col in ['date', 'description', 'amount'])
        
        # Also check for "Card Member" which is distinctive to Amex
        has_card_member = 'card member' in df_columns_lower or 'cardmember' in df_columns_lower
        
        return has_amex_columns or has_card_member
    
    def parse_amex_csv(self, csv_path: str) -> Tuple[List[Dict], Dict]:
        """Parse an Amex CSV file and extract line items.
        
        Args:
            csv_path: Path to the Amex CSV file
            
        Returns:
            Tuple of (line_items, metadata)
            - line_items: List of dicts with parsed line item data
            - metadata: Dict with summary info (total_amount, count, date_range)
        """
        # Load CSV
        df = pd.read_csv(csv_path)
        
        # Detect if it's Amex format
        if not self.detect_amex_format(df):
            raise ValueError("CSV does not appear to be in Amex format")
        
        # Normalize column names
        df.columns = [col.lower().strip() for col in df.columns]
        
        # Parse line items
        line_items = []
        
        for idx, row in df.iterrows():
            # Extract date (handle various formats)
            date_str = str(row.get('date', ''))
            try:
                # Try common date formats
                for date_format in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']:
                    try:
                        parsed_date = datetime.strptime(date_str, date_format)
                        date = parsed_date.strftime('%Y-%m-%d')
                        break
                    except ValueError:
                        continue
                else:
                    date = date_str  # Use as-is if parsing fails
            except:
                date = date_str
            
            # Extract description/vendor
            description = str(row.get('description', '')).strip()
            vendor = self._extract_vendor_from_description(description)
            
            # Extract amount
            amount_str = str(row.get('amount', '0'))
            # Remove currency symbols and commas
            amount_str = amount_str.replace('$', '').replace(',', '').strip()
            try:
                amount = abs(float(amount_str))  # Amex amounts are typically positive
            except ValueError:
                amount = 0.0
            
            # Auto-categorize based on vendor/description
            category, subcategory = self._auto_categorize(vendor, description)
            
            line_item = {
                'date': date,
                'vendor': vendor,
                'description': description,
                'amount': amount,
                'category': category,
                'subcategory': subcategory
            }
            
            line_items.append(line_item)
        
        # Calculate metadata
        total_amount = sum(item['amount'] for item in line_items)
        dates = [item['date'] for item in line_items if item['date']]
        
        metadata = {
            'total_amount': total_amount,
            'count': len(line_items),
            'earliest_date': min(dates) if dates else None,
            'latest_date': max(dates) if dates else None,
            'csv_filename': os.path.basename(csv_path)
        }
        
        return line_items, metadata
    
    def _extract_vendor_from_description(self, description: str) -> str:
        """Extract vendor name from description.
        
        Args:
            description: Transaction description
            
        Returns:
            Extracted vendor name
        """
        # Remove common suffixes and clean up
        vendor = description.upper().strip()
        
        # Remove location indicators
        vendor = re.sub(r'\s+\d{5,}$', '', vendor)  # Remove trailing numbers (zip codes)
        vendor = re.sub(r'\s+[A-Z]{2}$', '', vendor)  # Remove trailing state codes
        
        # Take first meaningful part
        parts = vendor.split()
        if len(parts) > 3:
            vendor = ' '.join(parts[:3])
        
        return vendor.title()
    
    def _auto_categorize(self, vendor: str, description: str) -> Tuple[str, str]:
        """Auto-categorize a line item based on vendor/description.
        
        Args:
            vendor: Vendor name
            description: Full description
            
        Returns:
            Tuple of (category, subcategory)
        """
        vendor_lower = vendor.lower()
        desc_lower = description.lower()
        
        # Food & Grocery
        food_keywords = ['ica', 'willys', 'coop', 'hemköp', 'lidl', 'supermarket', 
                        'grocery', 'matbutik', 'market']
        if any(kw in vendor_lower or kw in desc_lower for kw in food_keywords):
            return 'Mat & Dryck', 'Matinköp'
        
        # Fuel
        fuel_keywords = ['shell', 'ingo', 'preem', 'circle k', 'ok', 'q8', 
                        'petrol', 'fuel', 'bensin']
        if any(kw in vendor_lower or kw in desc_lower for kw in fuel_keywords):
            return 'Transport', 'Drivmedel'
        
        # Streaming & Entertainment
        streaming_keywords = ['netflix', 'spotify', 'hbo', 'disney', 'viaplay', 
                             'youtube', 'apple music']
        if any(kw in vendor_lower or kw in desc_lower for kw in streaming_keywords):
            return 'Nöje', 'Streaming'
        
        # Sports & Fitness
        sports_keywords = ['stadium', 'intersport', 'xxl', 'gym', 'fitness', 
                          'sats', 'sport']
        if any(kw in vendor_lower or kw in desc_lower for kw in sports_keywords):
            return 'Shopping', 'Sport'
        
        # Restaurants
        restaurant_keywords = ['restaurant', 'café', 'bar', 'pizza', 'burger', 
                              'mcdonalds', 'max', 'subway']
        if any(kw in vendor_lower or kw in desc_lower for kw in restaurant_keywords):
            return 'Mat & Dryck', 'Restaurang'
        
        # Default
        return 'Övrigt', ''
    
    def find_matching_bill(self, metadata: Dict, tolerance_days: int = 7,
                          amount_tolerance: float = 0.10) -> Optional[Dict]:
        """Find an existing bill that matches the Amex CSV data.
        
        Args:
            metadata: Metadata from parse_amex_csv
            tolerance_days: Days tolerance for date matching
            amount_tolerance: Percentage tolerance for amount matching (0.10 = 10%)
            
        Returns:
            Matching bill dict or None
        """
        if not self.bill_manager:
            return None
        
        # Get all pending Amex bills
        bills = self.bill_manager.get_bills(status='pending')
        amex_bills = [b for b in bills if b.get('is_amex_bill', False)]
        
        total_amount = metadata.get('total_amount', 0)
        latest_date = metadata.get('latest_date', '')
        
        if not latest_date:
            return None
        
        # Find best matching bill
        best_match = None
        best_score = 0.0
        
        for bill in amex_bills:
            score = 0.0
            
            # Check amount match
            bill_amount = bill.get('amount', 0)
            if bill_amount > 0:
                amount_diff = abs(bill_amount - total_amount) / bill_amount
                if amount_diff <= amount_tolerance:
                    # Higher score for closer match
                    score += (1.0 - amount_diff) * 0.6
            
            # Check date proximity (bill due date vs latest transaction date)
            bill_due_date = bill.get('due_date', '')
            if bill_due_date:
                try:
                    due_date = datetime.strptime(bill_due_date, '%Y-%m-%d')
                    latest_tx_date = datetime.strptime(latest_date, '%Y-%m-%d')
                    
                    # Typically bill due date is after latest transaction
                    days_diff = (due_date - latest_tx_date).days
                    
                    if 0 <= days_diff <= tolerance_days * 2:
                        # Score based on proximity
                        score += (1.0 - min(days_diff / (tolerance_days * 2), 1.0)) * 0.4
                except ValueError:
                    pass
            
            if score > best_score:
                best_score = score
                best_match = bill
        
        # Return match if score is high enough
        if best_match and best_score >= 0.5:
            return best_match
        
        return None
    
    def create_linkage_preview(self, line_items: List[Dict], metadata: Dict,
                              matched_bill: Optional[Dict] = None) -> Dict:
        """Create a preview of the proposed linkage.
        
        Args:
            line_items: Parsed line items from CSV
            metadata: Metadata from parsing
            matched_bill: Matched bill (if found)
            
        Returns:
            Dict with preview information for user confirmation
        """
        preview = {
            'line_items_count': metadata.get('count', 0),
            'total_amount': metadata.get('total_amount', 0),
            'date_range': f"{metadata.get('earliest_date', '')} to {metadata.get('latest_date', '')}",
            'csv_filename': metadata.get('csv_filename', ''),
            'matched_bill': None,
            'match_confidence': 0.0,
            'sample_line_items': line_items[:5] if len(line_items) > 5 else line_items,
            'will_create_new_bill': matched_bill is None
        }
        
        if matched_bill:
            preview['matched_bill'] = {
                'id': matched_bill.get('id'),
                'name': matched_bill.get('name'),
                'amount': matched_bill.get('amount'),
                'due_date': matched_bill.get('due_date'),
                'account': matched_bill.get('account')
            }
            
            # Calculate match confidence
            bill_amount = matched_bill.get('amount', 0)
            csv_total = metadata.get('total_amount', 0)
            if bill_amount > 0:
                amount_diff = abs(bill_amount - csv_total) / bill_amount
                preview['match_confidence'] = max(0, 1.0 - amount_diff)
        
        return preview
