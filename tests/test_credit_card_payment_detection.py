"""Tests for credit card payment detection."""

import pytest
import os
import yaml
import tempfile
import shutil
from datetime import datetime

from modules.core.account_manager import AccountManager
from modules.core.credit_card_manager import CreditCardManager


class TestCreditCardPaymentDetection:
    """Test credit card payment detection functionality."""
    
    @pytest.fixture
    def temp_yaml_dir(self):
        """Create a temporary YAML directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def manager(self, temp_yaml_dir):
        """Create an AccountManager with temp directory."""
        return AccountManager(yaml_dir=temp_yaml_dir)
    
    @pytest.fixture
    def cc_manager(self, temp_yaml_dir):
        """Create a CreditCardManager with temp directory."""
        return CreditCardManager(yaml_dir=temp_yaml_dir)
    
    def test_detect_amex_payment_abbreviated(self, manager, cc_manager):
        """Test detection of American Express payment with abbreviated name."""
        # Create account and Amex card
        manager.create_account("Bank Account", 10000.0)
        card = cc_manager.add_card(
            name="Amex Platinum",
            card_type="American Express",
            last_four="1234",
            credit_limit=50000.0
        )
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        transactions = [
            {
                'account': 'Bank Account',
                'date': today,
                'amount': -5000.0,
                'description': 'Betalning BG 5127-5477 American Exp'  # Abbreviated
            }
        ]
        
        manager.add_transactions(transactions)
        count = manager.detect_credit_card_payments()
        
        # Should detect the payment
        assert count == 1
        
        all_txs = manager.get_all_transactions()
        marked = [tx for tx in all_txs if tx.get('is_credit_card_payment')]
        assert len(marked) == 1
        
        # Should match to specific card
        payment = marked[0]
        assert payment.get('matched_credit_card_id') == card['id']
        assert 'Amex Platinum' in payment.get('credit_card_payment_label', '')
    
    def test_detect_visa_payment(self, manager, cc_manager):
        """Test detection of Visa payment."""
        manager.create_account("Bank Account", 10000.0)
        card = cc_manager.add_card(
            name="Visa Gold",
            card_type="Visa",
            last_four="5678",
            credit_limit=30000.0
        )
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        transactions = [
            {
                'account': 'Bank Account',
                'date': today,
                'amount': -3000.0,
                'description': 'Visa kortbetalning'
            }
        ]
        
        manager.add_transactions(transactions)
        count = manager.detect_credit_card_payments()
        
        assert count == 1
        
        all_txs = manager.get_all_transactions()
        payment = [tx for tx in all_txs if tx.get('is_credit_card_payment')][0]
        assert payment.get('matched_credit_card_id') == card['id']
    
    def test_detect_mastercard_payment(self, manager, cc_manager):
        """Test detection of Mastercard payment."""
        manager.create_account("Bank Account", 10000.0)
        card = cc_manager.add_card(
            name="MC Premium",
            card_type="Mastercard",
            last_four="9012",
            credit_limit=40000.0
        )
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        transactions = [
            {
                'account': 'Bank Account',
                'date': today,
                'amount': -2000.0,
                'description': 'Mastercard payment'
            }
        ]
        
        manager.add_transactions(transactions)
        count = manager.detect_credit_card_payments()
        
        assert count == 1
    
    def test_no_false_positives_for_purchases(self, manager, cc_manager):
        """Test that regular purchases are not marked as credit card payments."""
        manager.create_account("Bank Account", 10000.0)
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        transactions = [
            {
                'account': 'Bank Account',
                'date': today,
                'amount': -150.0,
                'description': 'ICA Supermarket purchase'
            },
            {
                'account': 'Bank Account',
                'date': today,
                'amount': -500.0,
                'description': 'Restaurant dinner'
            }
        ]
        
        manager.add_transactions(transactions)
        count = manager.detect_credit_card_payments()
        
        # Should not detect any
        assert count == 0
    
    def test_payment_without_matching_card(self, manager):
        """Test detection of credit card payment without matching card."""
        manager.create_account("Bank Account", 10000.0)
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        transactions = [
            {
                'account': 'Bank Account',
                'date': today,
                'amount': -1000.0,
                'description': 'Amex payment'
            }
        ]
        
        manager.add_transactions(transactions)
        count = manager.detect_credit_card_payments()
        
        # Should detect but not match to specific card
        assert count == 1
        
        all_txs = manager.get_all_transactions()
        payment = [tx for tx in all_txs if tx.get('is_credit_card_payment')][0]
        assert payment.get('matched_credit_card_id') is None
        assert payment.get('credit_card_payment_label') == "Inbetalning till kreditkort"
    
    def test_skip_positive_amounts(self, manager):
        """Test that positive amounts (income) are not marked as payments."""
        manager.create_account("Bank Account", 10000.0)
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        transactions = [
            {
                'account': 'Bank Account',
                'date': today,
                'amount': 5000.0,  # Positive amount
                'description': 'Amex refund'
            }
        ]
        
        manager.add_transactions(transactions)
        count = manager.detect_credit_card_payments()
        
        # Should not detect (positive amounts are not payments out)
        assert count == 0
