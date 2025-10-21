"""Tests for agent_interface module."""

import unittest
import os
import yaml
import tempfile
import shutil

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.core.agent_interface import AgentInterface


class TestAgentInterface(unittest.TestCase):
    """Test cases for AgentInterface class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for test YAML files
        self.test_dir = tempfile.mkdtemp()
        self.agent = AgentInterface(yaml_dir=self.test_dir)
        
        # Create sample data
        self._create_sample_data()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
    
    def _create_sample_data(self):
        """Create sample data for testing."""
        # Create accounts
        accounts = {
            'accounts': [
                {'name': 'Test Account', 'balance': 10000.0, 'created_at': '2025-01-01'}
            ]
        }
        accounts_file = os.path.join(self.test_dir, 'accounts.yaml')
        with open(accounts_file, 'w', encoding='utf-8') as f:
            yaml.dump(accounts, f)
        
        # Create transactions
        transactions = {
            'transactions': [
                {
                    'id': '1',
                    'date': '2025-01-15',
                    'description': 'Lön',
                    'amount': 30000.0,
                    'account': 'Test Account',
                    'category': 'Inkomst'
                },
                {
                    'id': '2',
                    'date': '2025-01-20',
                    'description': 'Matinköp',
                    'amount': -500.0,
                    'account': 'Test Account',
                    'category': 'Mat & Dryck'
                }
            ]
        }
        transactions_file = os.path.join(self.test_dir, 'transactions.yaml')
        with open(transactions_file, 'w', encoding='utf-8') as f:
            yaml.dump(transactions, f)
    
    def test_agent_interface_initialization(self):
        """Test AgentInterface initialization."""
        self.assertIsNotNone(self.agent)
        self.assertEqual(self.agent.yaml_dir, self.test_dir)
    
    def test_parse_query_balance(self):
        """Test parsing balance query."""
        queries = [
            'Hur mycket saldo har jag?',
            'Vad är mitt balance?',
            'Hur mycket har jag kvar?'
        ]
        
        for query in queries:
            parsed = self.agent.parse_query(query)
            self.assertEqual(parsed['intent'], 'balance_query')
            self.assertEqual(parsed['module'], 'forecast_engine')
    
    def test_parse_query_bill(self):
        """Test parsing bill query."""
        queries = [
            'Visa mina fakturor',
            'Vilka räkningar har jag?',
            'Show bills'
        ]
        
        for query in queries:
            parsed = self.agent.parse_query(query)
            self.assertEqual(parsed['intent'], 'bill_query')
            self.assertEqual(parsed['module'], 'bill_manager')
    
    def test_parse_query_loan(self):
        """Test parsing loan query."""
        queries = [
            'Vilka lån har jag?',
            'Visa mina lån',
            'Show loans'
        ]
        
        for query in queries:
            parsed = self.agent.parse_query(query)
            self.assertEqual(parsed['intent'], 'loan_query')
            self.assertEqual(parsed['module'], 'loan_manager')
    
    def test_parse_query_loan_simulation(self):
        """Test parsing loan simulation query."""
        query = 'Simulera ränta 4.5%'
        parsed = self.agent.parse_query(query)
        
        self.assertEqual(parsed['intent'], 'loan_simulation')
        self.assertEqual(parsed['module'], 'loan_manager')
        self.assertIn('new_rate', parsed['parameters'])
        self.assertEqual(parsed['parameters']['new_rate'], 4.5)
    
    def test_parse_query_income(self):
        """Test parsing income query."""
        queries = [
            'Visa mina inkomster',
            'Hur mycket lön har jag?',
            'Show income'
        ]
        
        for query in queries:
            parsed = self.agent.parse_query(query)
            self.assertEqual(parsed['intent'], 'income_query')
            self.assertEqual(parsed['module'], 'income_tracker')
    
    def test_parse_query_history(self):
        """Test parsing history query."""
        queries = [
            'Visa historik',
            'Vad är trenden?',
            'Show history'
        ]
        
        for query in queries:
            parsed = self.agent.parse_query(query)
            self.assertEqual(parsed['intent'], 'history_query')
            self.assertEqual(parsed['module'], 'history_viewer')
    
    def test_parse_query_top_expenses(self):
        """Test parsing top expenses query."""
        queries = [
            'Största utgifter',
            'Visa mest',
            'Top expenses'
        ]
        
        for query in queries:
            parsed = self.agent.parse_query(query)
            self.assertEqual(parsed['intent'], 'top_expenses')
            self.assertEqual(parsed['module'], 'history_viewer')
    
    def test_parse_query_monthly_summary(self):
        """Test parsing monthly summary query."""
        queries = [
            'Månadssammanfattning',
            'Summary för månad',
            'Monthly summary'
        ]
        
        for query in queries:
            parsed = self.agent.parse_query(query)
            self.assertEqual(parsed['intent'], 'monthly_summary')
            self.assertEqual(parsed['module'], 'history_viewer')
    
    def test_parse_query_unknown(self):
        """Test parsing unknown query."""
        query = 'Random text that doesnt match anything'
        parsed = self.agent.parse_query(query)
        
        self.assertEqual(parsed['intent'], 'unknown')
    
    def test_route_to_module(self):
        """Test routing parsed query to module."""
        parsed = {'module': 'forecast_engine', 'intent': 'balance_query'}
        module = self.agent.route_to_module(parsed)
        
        self.assertEqual(module, 'forecast_engine')
    
    def test_generate_response_balance(self):
        """Test generating response for balance query."""
        parsed = {
            'intent': 'balance_query',
            'module': 'forecast_engine',
            'parameters': {}
        }
        
        response = self.agent.generate_response(parsed)
        
        self.assertIsNotNone(response)
        self.assertIn('saldo', response.lower())
    
    def test_generate_response_unknown(self):
        """Test generating response for unknown query."""
        parsed = {
            'intent': 'unknown',
            'module': None,
            'parameters': {}
        }
        
        response = self.agent.generate_response(parsed)
        
        self.assertIsNotNone(response)
        self.assertIn('förstod inte', response.lower())
    
    def test_log_query_and_response(self):
        """Test logging query and response."""
        query = "Test query"
        response = "Test response"
        
        self.agent.log_query_and_response(query, response)
        
        # Verify log was created
        log_file = os.path.join(self.test_dir, 'agent_queries.yaml')
        self.assertTrue(os.path.exists(log_file))
        
        with open(log_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        self.assertIn('queries', data)
        self.assertTrue(len(data['queries']) > 0)
        self.assertEqual(data['queries'][0]['query'], query)
        self.assertEqual(data['queries'][0]['response'], response)
    
    def test_process_query(self):
        """Test processing complete query."""
        query = "Hur mycket saldo har jag?"
        response = self.agent.process_query(query)
        
        self.assertIsNotNone(response)
        self.assertIsInstance(response, str)
        
        # Verify query was logged
        log_file = os.path.join(self.test_dir, 'agent_queries.yaml')
        self.assertTrue(os.path.exists(log_file))


if __name__ == '__main__':
    unittest.main()
