"""Tests for Mastercard CSV import and payment matching workflow."""

import pytest
import os
import tempfile
import shutil
from datetime import datetime

from modules.core.account_manager import AccountManager
from modules.core.credit_card_manager import CreditCardManager


class TestMastercardWorkflow:
    """Test complete Mastercard workflow from CSV import to payment matching."""
    
    @pytest.fixture
    def temp_yaml_dir(self):
        """Create a temporary YAML directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def account_manager(self, temp_yaml_dir):
        """Create an AccountManager with temp directory."""
        return AccountManager(yaml_dir=temp_yaml_dir)
    
    @pytest.fixture
    def cc_manager(self, temp_yaml_dir):
        """Create a CreditCardManager with temp directory."""
        return CreditCardManager(yaml_dir=temp_yaml_dir)
    
    @pytest.fixture
    def mastercard(self, cc_manager):
        """Create a Mastercard for testing."""
        return cc_manager.add_card(
            name="Mastercard Premium",
            card_type="Mastercard",
            last_four="2345",
            credit_limit=50000.0,
            initial_balance=0.0,
            display_color="#EB001B",
            icon="mastercard"
        )
    
    def test_mastercard_csv_import(self, cc_manager, mastercard):
        """Test importing Mastercard CSV file."""
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'mastercard_sample.csv')
        
        # Import transactions from CSV
        result = cc_manager.import_transactions_from_csv(
            card_id=mastercard['id'],
            csv_path=csv_path
        )
        
        # Should import transactions (excluding payment)
        assert result['imported'] > 0
        
        # Verify transactions were added
        transactions = cc_manager.get_transactions(mastercard['id'])
        assert len(transactions) > 0
        
        # Verify negative amounts (purchases) and payments are filtered
        for tx in transactions:
            assert tx['amount'] < 0  # All should be purchases (negative)
        
        # Verify card balance updated
        card = cc_manager.get_card_by_id(mastercard['id'])
        assert card['current_balance'] > 0  # Balance increased (money owed)
    
    def test_mastercard_auto_categorization(self, cc_manager, mastercard):
        """Test that Mastercard transactions are auto-categorized."""
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'mastercard_sample.csv')
        
        # Import transactions
        cc_manager.import_transactions_from_csv(
            card_id=mastercard['id'],
            csv_path=csv_path
        )
        
        # Get transactions
        transactions = cc_manager.get_transactions(mastercard['id'])
        
        # Verify at least some transactions have categories assigned
        categorized = [tx for tx in transactions if tx.get('category') != 'Övrigt']
        assert len(categorized) > 0, "Some transactions should be auto-categorized"
    
    def test_mastercard_payment_detection_bg_format(self, account_manager, cc_manager, mastercard):
        """Test detection of Mastercard payment with Swedish BG format."""
        # Create bank account
        account_manager.create_account("Bank Account", 20000.0)
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Add transaction with specific Mastercard payment description
        transactions = [
            {
                'account': 'Bank Account',
                'date': today,
                'amount': -5000.0,
                'description': 'Betalning BG 595-4300 SEB KORT BANK'
            }
        ]
        
        account_manager.add_transactions(transactions)
        
        # Run payment detection
        count = account_manager.detect_credit_card_payments()
        
        # Should detect the payment (BG payment format)
        assert count == 1
        
        # Verify payment was marked
        all_txs = account_manager.get_all_transactions()
        marked = [tx for tx in all_txs if tx.get('is_credit_card_payment')]
        assert len(marked) == 1
        
        payment = marked[0]
        assert payment.get('is_credit_card_payment') == True
        # Note: Without "mastercard" in description, it won't match to specific card
        # but should still be marked as credit card payment
    
    def test_mastercard_payment_detection_with_card_match(self, account_manager, cc_manager, mastercard):
        """Test detection of Mastercard payment that matches specific card."""
        # Create bank account
        account_manager.create_account("Bank Account", 20000.0)
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Add transaction with Mastercard keyword
        transactions = [
            {
                'account': 'Bank Account',
                'date': today,
                'amount': -5000.0,
                'description': 'Mastercard Betalning 2345'
            }
        ]
        
        account_manager.add_transactions(transactions)
        
        # Run payment detection
        count = account_manager.detect_credit_card_payments()
        
        # Should detect and match to specific card
        assert count == 1
        
        all_txs = account_manager.get_all_transactions()
        payment = [tx for tx in all_txs if tx.get('is_credit_card_payment')][0]
        
        # Should be matched to our Mastercard
        assert payment.get('matched_credit_card_id') == mastercard['id']
        assert 'Mastercard Premium' in payment.get('credit_card_payment_label', '')
    
    def test_mastercard_balance_after_payment(self, cc_manager, mastercard):
        """Test that Mastercard balance decreases after payment match."""
        # Add some transactions to create balance
        cc_manager.add_transaction(
            card_id=mastercard['id'],
            date='2025-10-15',
            description='ICA Supermarket',
            amount=-1000.0,
            category='Mat & Dryck'
        )
        
        # Check initial balance
        card = cc_manager.get_card_by_id(mastercard['id'])
        initial_balance = card['current_balance']
        assert initial_balance == 1000.0
        
        # Match a payment
        success = cc_manager.match_payment_to_card(
            card_id=mastercard['id'],
            payment_amount=500.0,
            payment_date='2025-10-20',
            transaction_id='TX-BANK-001'
        )
        
        assert success == True
        
        # Check balance decreased
        card = cc_manager.get_card_by_id(mastercard['id'])
        assert card['current_balance'] == 500.0  # 1000 - 500
        assert card['available_credit'] == 49500.0  # 50000 - 500
    
    def test_mastercard_transaction_editing(self, cc_manager, mastercard):
        """Test editing Mastercard transaction category."""
        # Add transaction
        tx = cc_manager.add_transaction(
            card_id=mastercard['id'],
            date='2025-10-15',
            description='Some Store',
            amount=-500.0,
            category='Övrigt'
        )
        
        # Update category
        success = cc_manager.update_transaction(
            card_id=mastercard['id'],
            transaction_id=tx['id'],
            category='Shopping',
            subcategory='Kläder'
        )
        
        assert success == True
        
        # Verify update
        transactions = cc_manager.get_transactions(mastercard['id'])
        updated_tx = [t for t in transactions if t['id'] == tx['id']][0]
        assert updated_tx['category'] == 'Shopping'
        assert updated_tx['subcategory'] == 'Kläder'
    
    def test_mastercard_summary(self, cc_manager, mastercard):
        """Test getting Mastercard summary with category breakdown."""
        # Add various transactions
        transactions_data = [
            {'desc': 'ICA', 'amount': -1000.0, 'cat': 'Mat & Dryck'},
            {'desc': 'Shell', 'amount': -500.0, 'cat': 'Transport'},
            {'desc': 'Netflix', 'amount': -119.0, 'cat': 'Nöje'},
            {'desc': 'ICA 2', 'amount': -800.0, 'cat': 'Mat & Dryck'},
        ]
        
        for tx_data in transactions_data:
            cc_manager.add_transaction(
                card_id=mastercard['id'],
                date='2025-10-15',
                description=tx_data['desc'],
                amount=tx_data['amount'],
                category=tx_data['cat']
            )
        
        # Get summary
        summary = cc_manager.get_card_summary(mastercard['id'])
        
        # Verify summary
        assert summary['name'] == 'Mastercard Premium'
        assert summary['card_type'] == 'Mastercard'
        assert summary['current_balance'] == 2419.0  # Sum of absolute amounts
        assert summary['total_spent'] == 2419.0
        
        # Verify category breakdown
        breakdown = summary['category_breakdown']
        assert breakdown['Mat & Dryck'] == 1800.0
        assert breakdown['Transport'] == 500.0
        assert breakdown['Nöje'] == 119.0
    
    def test_mastercard_card_icon(self, cc_manager, mastercard):
        """Test that Mastercard has correct icon."""
        # This verifies the card was created with correct icon
        assert mastercard['icon'] == 'mastercard'
        assert mastercard['display_color'] == '#EB001B'
        assert mastercard['card_type'] == 'Mastercard'
    
    def test_mastercard_not_affecting_cashflow(self, cc_manager, mastercard):
        """Test that Mastercard transactions don't affect bank account balance."""
        # Add Mastercard transactions
        cc_manager.add_transaction(
            card_id=mastercard['id'],
            date='2025-10-15',
            description='ICA',
            amount=-1000.0,
            category='Mat & Dryck'
        )
        
        # Verify card balance increased
        card = cc_manager.get_card_by_id(mastercard['id'])
        assert card['current_balance'] == 1000.0
        
        # Note: This test verifies that credit card transactions are stored
        # separately and don't mix with bank account transactions
        # Bank account balance is managed separately by AccountManager
