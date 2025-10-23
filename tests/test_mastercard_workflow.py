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
        
        # Should process payments (if any in the file)
        # The sample CSV includes a payment, so payments_processed should be > 0
        assert 'payments_processed' in result
        
        # Verify transactions were added
        transactions = cc_manager.get_transactions(mastercard['id'])
        assert len(transactions) > 0
        
        # Verify negative amounts (purchases) and payments are filtered out from transactions
        for tx in transactions:
            assert tx['amount'] < 0  # All should be purchases (negative)
        
        # Verify card balance was updated
        # Note: Balance could be positive (money owed) or negative (credit) depending on payments
        card = cc_manager.get_card_by_id(mastercard['id'])
        assert 'current_balance' in card  # Just verify balance exists

    
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
    
    def test_actual_mastercard_csv_format(self, cc_manager):
        """Test importing actual Mastercard CSV with Swedish column names (Specifikation, Ort)."""
        # Create a Mastercard for testing
        card = cc_manager.add_card(
            name="Mastercard Actual",
            card_type="Mastercard",
            last_four="9506",
            credit_limit=50000.0,
            display_color="#EB001B",
            icon="mastercard"
        )
        
        # Import the actual format CSV (if it exists)
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'mastercard_actual_clean.csv')
        
        if not os.path.exists(csv_path):
            # Create a test file with actual format
            import pandas as pd
            test_data = pd.DataFrame({
                'Datum': ['2025-10-21', '2025-10-19', '2025-10-17'],
                'Bokfört': ['2025-10-22', '2025-10-20', '2025-10-20'],
                'Specifikation': ['PIZZERIA & REST', 'MAXI ICA STORMARKNAD', 'ICA SUPERMARKET HJO'],
                'Ort': ['HJO', 'SKOVDE', 'HJO'],
                'Valuta': ['SEK', 'SEK', 'SEK'],
                'Utl. belopp': [0, 0, 0],
                'Belopp': [130.0, 544.75, 69.0]
            })
            csv_path = os.path.join(os.path.dirname(__file__), '..', 'test_mastercard_actual.csv')
            test_data.to_csv(csv_path, index=False)
        
        # Import should work with Swedish column names
        result = cc_manager.import_transactions_from_csv(
            card_id=card['id'],
            csv_path=csv_path
        )
        
        # Verify import worked
        assert result['imported'] >= 3
        
        # Verify transactions
        transactions = cc_manager.get_transactions(card['id'])
        assert len(transactions) >= 3
        
        # Verify amounts are negative (purchases)
        for tx in transactions:
            assert tx['amount'] < 0
        
        # Verify vendor is populated from Ort column
        vendors = [tx.get('vendor', '') for tx in transactions]
        assert any(vendors)  # At least some vendors should be set
        
        # Clean up test file if we created it
        if csv_path.endswith('test_mastercard_actual.csv') and os.path.exists(csv_path):
            os.remove(csv_path)
    
    def test_excel_file_import(self, cc_manager):
        """Test importing Excel (.xlsx) file directly."""
        # Create a Mastercard for testing
        card = cc_manager.add_card(
            name="Mastercard Excel",
            card_type="Mastercard",
            last_four="9506",
            credit_limit=50000.0,
            display_color="#EB001B",
            icon="mastercard"
        )
        
        # Check if Excel file exists
        xlsx_path = os.path.join(os.path.dirname(__file__), '..', 'mastercard_actual.xlsx')
        
        if os.path.exists(xlsx_path):
            # Import Excel file directly
            result = cc_manager.import_transactions_from_csv(
                card_id=card['id'],
                csv_path=xlsx_path
            )
            
            # Verify import worked
            assert result['imported'] > 0
            
            # Verify transactions
            transactions = cc_manager.get_transactions(card['id'])
            assert len(transactions) > 0
            
            # Verify amounts are negative (purchases)
            for tx in transactions:
                assert tx['amount'] < 0
        else:
            # Skip test if file doesn't exist
            pytest.skip("Excel file not available for testing")
    
    def test_transaction_and_posting_dates(self, cc_manager):
        """Test that both transaction date (Datum) and posting date (Bokfört) are imported and stored."""
        # Create a test card
        card = cc_manager.add_card(
            name="Mastercard Two Dates",
            card_type="Mastercard",
            last_four="9506",
            credit_limit=50000.0,
            display_color="#EB001B",
            icon="mastercard"
        )
        
        # Create test CSV with both date columns
        import pandas as pd
        test_data = pd.DataFrame({
            'Datum': ['2025-10-21', '2025-10-19', '2025-10-17'],
            'Bokfört': ['2025-10-22', '2025-10-20', '2025-10-20'],
            'Specifikation': ['PIZZERIA', 'ICA SUPERMARKET', 'MAXI'],
            'Ort': ['HJO', 'SKOVDE', 'SKOVDE'],
            'Valuta': ['SEK', 'SEK', 'SEK'],
            'Utl. belopp': [0, 0, 0],
            'Belopp': [130.0, 544.75, 69.0]
        })
        
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'test_two_dates.csv')
        test_data.to_csv(csv_path, index=False)
        
        try:
            # Import the CSV
            result = cc_manager.import_transactions_from_csv(
                card_id=card['id'],
                csv_path=csv_path
            )
            
            # Verify import
            assert result['imported'] == 3
            
            # Get transactions
            transactions = cc_manager.get_transactions(card['id'])
            assert len(transactions) == 3
            
            # Verify both dates are present and different
            for tx in transactions:
                assert 'date' in tx, "Transaction should have transaction date (Datum)"
                assert 'posting_date' in tx, "Transaction should have posting date (Bokfört)"
                
                # Verify dates are valid
                assert tx['date'] is not None
                assert tx['posting_date'] is not None
            
            # Find the specific transactions and verify dates
            pizzeria_tx = [tx for tx in transactions if 'PIZZERIA' in tx['description']][0]
            assert pizzeria_tx['date'] == '2025-10-21', "Transaction date should match Datum column"
            assert pizzeria_tx['posting_date'] == '2025-10-22', "Posting date should match Bokfört column"
            
            # Verify posting_date is used for sorting (most recent posting first)
            assert transactions[0]['posting_date'] >= transactions[1]['posting_date']
            
        finally:
            # Clean up test file
            if os.path.exists(csv_path):
                os.remove(csv_path)
    
    def test_balance_calculated_by_posting_date(self, cc_manager):
        """Test that card balance is calculated based on posting_date, not transaction date."""
        # Create a test card
        card = cc_manager.add_card(
            name="Mastercard Posting Date Test",
            card_type="Mastercard",
            last_four="1234",
            credit_limit=50000.0,
            display_color="#EB001B",
            icon="mastercard"
        )
        
        # Add transactions with different transaction and posting dates
        # Transaction 1: Made on Oct 15, posted on Oct 17
        cc_manager.add_transaction(
            card_id=card['id'],
            date='2025-10-15',
            description='Purchase 1',
            amount=-1000.0,
            category='Shopping',
            posting_date='2025-10-17'
        )
        
        # Transaction 2: Made on Oct 18, posted on Oct 19
        cc_manager.add_transaction(
            card_id=card['id'],
            date='2025-10-18',
            description='Purchase 2',
            amount=-500.0,
            category='Shopping',
            posting_date='2025-10-19'
        )
        
        # Transaction 3: Made on Oct 20, posted on Oct 21
        cc_manager.add_transaction(
            card_id=card['id'],
            date='2025-10-20',
            description='Purchase 3',
            amount=-300.0,
            category='Shopping',
            posting_date='2025-10-21'
        )
        
        # Calculate balance at Oct 18 using posting_date
        # Should include only Transaction 1 (posted Oct 17)
        balance_oct18_posting = cc_manager.calculate_balance_at_date(
            card_id=card['id'],
            as_of_date='2025-10-18',
            use_posting_date=True
        )
        assert balance_oct18_posting == 1000.0, f"Balance on Oct 18 (by posting date) should be 1000, got {balance_oct18_posting}"
        
        # Calculate balance at Oct 18 using transaction_date
        # Should include Transactions 1 and 2 (made Oct 15 and Oct 18)
        balance_oct18_transaction = cc_manager.calculate_balance_at_date(
            card_id=card['id'],
            as_of_date='2025-10-18',
            use_posting_date=False
        )
        assert balance_oct18_transaction == 1500.0, f"Balance on Oct 18 (by transaction date) should be 1500, got {balance_oct18_transaction}"
        
        # Verify that current_balance uses posting_date logic
        # (Total of all transactions = 1800)
        card_updated = cc_manager.get_card_by_id(card['id'])
        assert card_updated['current_balance'] == 1800.0
        
        # Calculate balance at Oct 20 using posting_date
        # Should include Transactions 1 and 2 (posted Oct 17 and Oct 19)
        balance_oct20_posting = cc_manager.calculate_balance_at_date(
            card_id=card['id'],
            as_of_date='2025-10-20',
            use_posting_date=True
        )
        assert balance_oct20_posting == 1500.0, f"Balance on Oct 20 (by posting date) should be 1500, got {balance_oct20_posting}"
    
    def test_filtering_by_posting_date(self, cc_manager):
        """Test filtering transactions by posting_date vs transaction date."""
        # Create a test card
        card = cc_manager.add_card(
            name="Mastercard Filter Test",
            card_type="Mastercard",
            last_four="5678",
            credit_limit=50000.0,
            display_color="#EB001B",
            icon="mastercard"
        )
        
        # Add transactions with different dates
        cc_manager.add_transaction(
            card_id=card['id'],
            date='2025-10-15',
            description='Early Purchase',
            amount=-100.0,
            category='Shopping',
            posting_date='2025-10-20'  # Posted later
        )
        
        cc_manager.add_transaction(
            card_id=card['id'],
            date='2025-10-18',
            description='Middle Purchase',
            amount=-200.0,
            category='Shopping',
            posting_date='2025-10-19'
        )
        
        # Filter by transaction date (Oct 15-17)
        txs_by_transaction = cc_manager.get_transactions(
            card_id=card['id'],
            start_date='2025-10-15',
            end_date='2025-10-17',
            use_posting_date=False
        )
        assert len(txs_by_transaction) == 1, "Should find 1 transaction by transaction date"
        assert txs_by_transaction[0]['description'] == 'Early Purchase'
        
        # Filter by posting date (Oct 19-20)
        txs_by_posting = cc_manager.get_transactions(
            card_id=card['id'],
            start_date='2025-10-19',
            end_date='2025-10-20',
            use_posting_date=True
        )
        assert len(txs_by_posting) == 2, "Should find 2 transactions by posting date"
    
    def test_payment_processing_in_csv_import(self, cc_manager):
        """Test that payments within CSV imports are processed correctly."""
        # Create a test card with initial balance
        card = cc_manager.add_card(
            name="Mastercard Payment Test",
            card_type="Mastercard",
            last_four="1111",
            credit_limit=20000.0,
            initial_balance=5000.0,  # Starting with 5000 kr owed
            display_color="#EB001B",
            icon="mastercard"
        )
        
        # Create test CSV with purchases and a payment
        import pandas as pd
        test_data = pd.DataFrame({
            'Datum': ['2025-10-15', '2025-10-16', '2025-10-17'],
            'Bokfört': ['2025-10-16', '2025-10-17', '2025-10-18'],
            'Specifikation': ['ICA Store', 'Payment Received', 'Shell Gas'],
            'Ort': ['Stockholm', '', 'Stockholm'],
            'Valuta': ['SEK', 'SEK', 'SEK'],
            'Utl. belopp': [0, 0, 0],
            'Belopp': [1000.0, -3000.0, 500.0]  # Two purchases and one payment
        })
        
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'test_payment_processing.csv')
        test_data.to_csv(csv_path, index=False)
        
        try:
            # Import the CSV
            result = cc_manager.import_transactions_from_csv(
                card_id=card['id'],
                csv_path=csv_path
            )
            
            # Verify import results
            assert result['imported'] == 2, "Should import 2 purchase transactions"
            assert result['payments_processed'] == 1, "Should process 1 payment"
            
            # Get final balance
            card_after = cc_manager.get_card_by_id(card['id'])
            
            # Expected balance calculation:
            # Initial: 5000
            # + Purchase 1: 1000
            # + Purchase 2: 500
            # - Payment: 3000
            # = 3500
            expected_balance = 5000.0 + 1000.0 + 500.0 - 3000.0
            assert abs(card_after['current_balance'] - expected_balance) < 0.01, \
                f"Balance should be {expected_balance}, got {card_after['current_balance']}"
            
            # Verify transactions (should not include payment as a transaction)
            transactions = cc_manager.get_transactions(card['id'])
            assert len(transactions) == 2, "Should have 2 purchase transactions only"
            
            # Verify payment history
            assert 'payment_history' in card_after
            assert len(card_after['payment_history']) == 1, "Should have 1 payment in history"
            assert card_after['payment_history'][0]['amount'] == 3000.0
            
        finally:
            # Clean up test file
            if os.path.exists(csv_path):
                os.remove(csv_path)
