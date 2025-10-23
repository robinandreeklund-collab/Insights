"""Tests for Credit Card Manager."""

import pytest
import tempfile
import os
import pandas as pd
from modules.core.credit_card_manager import CreditCardManager


class TestCreditCardManager:
    """Test suite for CreditCardManager."""
    
    def test_initialization(self):
        """Test that CreditCardManager initializes correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CreditCardManager(yaml_dir=tmpdir)
            assert os.path.exists(manager.cards_file)
            cards = manager.load_cards()
            assert isinstance(cards, list)
            assert len(cards) == 0
    
    def test_add_card(self):
        """Test adding a credit card."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CreditCardManager(yaml_dir=tmpdir)
            
            card = manager.add_card(
                name="Amex Platinum",
                card_type="American Express",
                last_four="1234",
                credit_limit=50000.0,
                display_color="#006FCF",
                icon="credit-card-alt"
            )
            
            assert card['name'] == "Amex Platinum"
            assert card['card_type'] == "American Express"
            assert card['last_four'] == "1234"
            assert card['credit_limit'] == 50000.0
            assert card['current_balance'] == 0.0
            assert card['available_credit'] == 50000.0
            assert card['status'] == 'active'
            assert 'id' in card
            assert card['id'].startswith('CARD-')
    
    def test_get_cards(self):
        """Test retrieving all cards."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CreditCardManager(yaml_dir=tmpdir)
            
            manager.add_card("Visa Gold", "Visa", "5678", 30000.0)
            manager.add_card("Mastercard Platinum", "Mastercard", "9012", 40000.0)
            
            cards = manager.get_cards()
            assert len(cards) == 2
            assert cards[0]['name'] == "Visa Gold"
            assert cards[1]['name'] == "Mastercard Platinum"
    
    def test_get_card_by_id(self):
        """Test retrieving a card by ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CreditCardManager(yaml_dir=tmpdir)
            
            card1 = manager.add_card("Test Card", "Visa", "1111", 20000.0)
            card2 = manager.get_card_by_id(card1['id'])
            
            assert card2 is not None
            assert card2['id'] == card1['id']
            assert card2['name'] == "Test Card"
    
    def test_update_card(self):
        """Test updating a card."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CreditCardManager(yaml_dir=tmpdir)
            
            card = manager.add_card("Old Name", "Visa", "1234", 25000.0)
            
            success = manager.update_card(card['id'], {
                'name': "New Name",
                'credit_limit': 30000.0
            })
            
            assert success is True
            
            updated_card = manager.get_card_by_id(card['id'])
            assert updated_card['name'] == "New Name"
            assert updated_card['credit_limit'] == 30000.0
    
    def test_delete_card(self):
        """Test deleting a card."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CreditCardManager(yaml_dir=tmpdir)
            
            card = manager.add_card("Delete Me", "Visa", "9999", 10000.0)
            assert len(manager.get_cards()) == 1
            
            success = manager.delete_card(card['id'])
            assert success is True
            assert len(manager.get_cards()) == 0
    
    def test_add_transaction(self):
        """Test adding a transaction to a card."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CreditCardManager(yaml_dir=tmpdir)
            
            card = manager.add_card("Test Card", "Visa", "1234", 50000.0)
            
            tx = manager.add_transaction(
                card_id=card['id'],
                date="2025-10-20",
                description="ICA Supermarket",
                amount=-1250.50,  # Negative for purchase
                category="Mat & Dryck",
                subcategory="Matinköp",
                vendor="ICA"
            )
            
            assert tx is not None
            assert tx['description'] == "ICA Supermarket"
            assert tx['amount'] == -1250.50
            assert tx['category'] == "Mat & Dryck"
            assert 'id' in tx
            
            # Check that balance was updated
            updated_card = manager.get_card_by_id(card['id'])
            assert updated_card['current_balance'] == 1250.50  # Positive balance (owe money)
            assert updated_card['available_credit'] == 50000.0 - 1250.50
    
    def test_add_payment_transaction(self):
        """Test adding a payment transaction."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CreditCardManager(yaml_dir=tmpdir)
            
            card = manager.add_card("Test Card", "Visa", "1234", 50000.0)
            
            # Add a purchase
            manager.add_transaction(card['id'], "2025-10-20", "Store", -1000.0, "Shopping")
            
            # Add a payment
            manager.add_transaction(card['id'], "2025-10-25", "Payment", 1000.0, "Betalning")
            
            updated_card = manager.get_card_by_id(card['id'])
            assert updated_card['current_balance'] == 0.0  # Balanced after payment
            assert updated_card['available_credit'] == 50000.0
    
    def test_get_transactions(self):
        """Test retrieving transactions with filtering."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CreditCardManager(yaml_dir=tmpdir)
            
            card = manager.add_card("Test Card", "Visa", "1234", 50000.0)
            
            manager.add_transaction(card['id'], "2025-10-15", "ICA", -500.0, "Mat & Dryck")
            manager.add_transaction(card['id'], "2025-10-20", "Shell", -650.0, "Transport")
            manager.add_transaction(card['id'], "2025-10-25", "Willys", -800.0, "Mat & Dryck")
            
            # Get all transactions
            all_txs = manager.get_transactions(card['id'])
            assert len(all_txs) == 3
            
            # Filter by category
            food_txs = manager.get_transactions(card['id'], category="Mat & Dryck")
            assert len(food_txs) == 2
            
            # Filter by date range
            date_filtered = manager.get_transactions(
                card['id'],
                start_date="2025-10-20",
                end_date="2025-10-25"
            )
            assert len(date_filtered) == 2
    
    def test_get_card_summary(self):
        """Test getting card summary statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CreditCardManager(yaml_dir=tmpdir)
            
            card = manager.add_card("Test Card", "Visa", "1234", 50000.0)
            
            # Add some transactions
            manager.add_transaction(card['id'], "2025-10-15", "ICA", -1500.0, "Mat & Dryck", vendor="ICA")
            manager.add_transaction(card['id'], "2025-10-20", "Shell", -650.0, "Transport", vendor="Shell")
            manager.add_transaction(card['id'], "2025-10-22", "Willys", -800.0, "Mat & Dryck", vendor="Willys")
            manager.add_transaction(card['id'], "2025-10-25", "Payment", 1000.0, "Betalning")
            
            summary = manager.get_card_summary(card['id'])
            
            assert summary['name'] == "Test Card"
            assert summary['card_type'] == "Visa"
            assert summary['current_balance'] == 1950.0  # 1500 + 650 + 800 - 1000
            assert summary['credit_limit'] == 50000.0
            assert summary['available_credit'] == 50000.0 - 1950.0
            assert summary['total_transactions'] == 4
            assert summary['total_spent'] == 2950.0  # Total purchases
            assert summary['total_payments'] == 1000.0
            
            # Check category breakdown
            assert 'Mat & Dryck' in summary['category_breakdown']
            assert summary['category_breakdown']['Mat & Dryck'] == 2300.0
            assert summary['category_breakdown']['Transport'] == 650.0
            
            # Check top vendors
            assert len(summary['top_vendors']) > 0
            assert summary['top_vendors'][0][0] == 'ICA'  # ICA should be top vendor
    
    def test_match_payment_to_card(self):
        """Test matching a bank payment to a card."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CreditCardManager(yaml_dir=tmpdir)
            
            card = manager.add_card("Test Card", "Visa", "1234", 50000.0)
            
            # Add some purchases
            manager.add_transaction(card['id'], "2025-10-15", "Store", -2500.0, "Shopping")
            
            # Current balance should be 2500
            card_before = manager.get_card_by_id(card['id'])
            assert card_before['current_balance'] == 2500.0
            
            # Match a payment
            success = manager.match_payment_to_card(
                card_id=card['id'],
                payment_amount=2500.0,
                payment_date="2025-10-25",
                transaction_id="TX-BANK-123"
            )
            
            assert success is True
            
            # Balance should now be 0
            card_after = manager.get_card_by_id(card['id'])
            assert card_after['current_balance'] == 0.0
            assert card_after['available_credit'] == 50000.0
            
            # Check that payment transaction was added
            transactions = manager.get_transactions(card['id'])
            payment_tx = [tx for tx in transactions if tx.get('matched_transaction_id')]
            assert len(payment_tx) == 1
            assert payment_tx[0]['matched_transaction_id'] == "TX-BANK-123"
    
    def test_import_transactions_from_csv(self):
        """Test importing transactions from CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CreditCardManager(yaml_dir=tmpdir)
            
            card = manager.add_card("Test Card", "Visa", "1234", 50000.0)
            
            # Create a test CSV file
            csv_data = pd.DataFrame({
                'Date': ['2025-10-15', '2025-10-20', '2025-10-22'],
                'Description': ['ICA Supermarket', 'Shell Gas Station', 'Netflix'],
                'Amount': [-856.50, -650.00, -119.00],
                'Vendor': ['ICA', 'Shell', 'Netflix']
            })
            
            csv_path = os.path.join(tmpdir, 'test_transactions.csv')
            csv_data.to_csv(csv_path, index=False)
            
            # Import transactions
            count = manager.import_transactions_from_csv(card['id'], csv_path)
            
            assert count == 3
            
            # Check that transactions were added
            transactions = manager.get_transactions(card['id'])
            assert len(transactions) == 3
            
            # Check balance
            card_after = manager.get_card_by_id(card['id'])
            assert card_after['current_balance'] == 1625.50  # Sum of all purchases
    
    def test_utilization_calculation(self):
        """Test credit utilization percentage calculation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CreditCardManager(yaml_dir=tmpdir)
            
            card = manager.add_card("Test Card", "Visa", "1234", 10000.0)
            
            # Add transaction for 30% utilization
            manager.add_transaction(card['id'], "2025-10-20", "Store", -3000.0, "Shopping")
            
            summary = manager.get_card_summary(card['id'])
            assert summary['utilization_percent'] == 30.0
    
    def test_get_cards_by_status(self):
        """Test filtering cards by status."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CreditCardManager(yaml_dir=tmpdir)
            
            card1 = manager.add_card("Active Card", "Visa", "1111", 20000.0)
            card2 = manager.add_card("Closed Card", "Mastercard", "2222", 30000.0)
            
            # Close one card
            manager.update_card(card2['id'], {'status': 'closed'})
            
            # Get active cards
            active_cards = manager.get_cards(status='active')
            assert len(active_cards) == 1
            assert active_cards[0]['name'] == "Active Card"
            
            # Get closed cards
            closed_cards = manager.get_cards(status='closed')
            assert len(closed_cards) == 1
            assert closed_cards[0]['name'] == "Closed Card"

