"""Tests for person_manager module."""

import pytest
import os
import yaml
from modules.core.person_manager import PersonManager


@pytest.fixture
def temp_yaml_dir(tmp_path):
    """Create a temporary yaml directory for testing."""
    yaml_dir = tmp_path / "yaml"
    yaml_dir.mkdir()
    return str(yaml_dir)


@pytest.fixture
def person_manager(temp_yaml_dir):
    """Create a PersonManager instance with temporary yaml directory."""
    return PersonManager(yaml_dir=temp_yaml_dir)


class TestPersonManager:
    """Test PersonManager functionality."""
    
    def test_add_person(self, person_manager):
        """Test adding a new person."""
        person = person_manager.add_person(
            name="Robin",
            monthly_income=30000.0,
            payment_day=25,
            description="Test person"
        )
        
        assert person['name'] == "Robin"
        assert person['monthly_income'] == 30000.0
        assert person['payment_day'] == 25
        assert person['description'] == "Test person"
        assert 'id' in person
        assert 'created_at' in person
    
    def test_add_person_duplicate(self, person_manager):
        """Test that adding a duplicate person raises error."""
        person_manager.add_person(name="Robin", monthly_income=30000.0)
        
        with pytest.raises(ValueError, match="finns redan"):
            person_manager.add_person(name="Robin", monthly_income=30000.0)
    
    def test_get_persons(self, person_manager):
        """Test retrieving all persons."""
        person_manager.add_person(name="Robin", monthly_income=30000.0)
        person_manager.add_person(name="Evelina", monthly_income=25000.0)
        
        persons = person_manager.get_persons()
        assert len(persons) == 2
        assert persons[0]['name'] == "Robin"
        assert persons[1]['name'] == "Evelina"
    
    def test_get_person_by_name(self, person_manager):
        """Test retrieving person by name."""
        person_manager.add_person(name="Robin", monthly_income=30000.0)
        
        person = person_manager.get_person_by_name("Robin")
        assert person is not None
        assert person['name'] == "Robin"
        
        # Test case insensitivity
        person = person_manager.get_person_by_name("robin")
        assert person is not None
        
        # Test non-existent person
        person = person_manager.get_person_by_name("Unknown")
        assert person is None
    
    def test_update_person(self, person_manager):
        """Test updating person information."""
        person = person_manager.add_person(name="Robin", monthly_income=30000.0, payment_day=25)
        person_id = person['id']
        
        updated = person_manager.update_person(
            person_id=person_id,
            monthly_income=35000.0,
            payment_day=28
        )
        
        assert updated['monthly_income'] == 35000.0
        assert updated['payment_day'] == 28
        assert 'updated_at' in updated
    
    def test_delete_person(self, person_manager):
        """Test deleting a person."""
        person = person_manager.add_person(name="Robin", monthly_income=30000.0)
        person_id = person['id']
        
        result = person_manager.delete_person(person_id)
        assert result is True
        
        persons = person_manager.get_persons()
        assert len(persons) == 0
        
        # Test deleting non-existent person
        result = person_manager.delete_person("non-existent-id")
        assert result is False
    
    def test_get_income_history(self, person_manager, temp_yaml_dir):
        """Test retrieving income history for a person."""
        person_manager.add_person(name="Robin", monthly_income=30000.0)
        
        # Create some income data
        income_data = {
            'incomes': [
                {'person': 'Robin', 'date': '2025-01-25', 'amount': 30000.0},
                {'person': 'Robin', 'date': '2025-02-25', 'amount': 32000.0},
                {'person': 'Robin', 'date': '2025-03-25', 'amount': 31000.0},
                {'person': 'Evelina', 'date': '2025-01-25', 'amount': 25000.0},
            ]
        }
        income_file = os.path.join(temp_yaml_dir, 'income_tracker.yaml')
        with open(income_file, 'w') as f:
            yaml.dump(income_data, f)
        
        history = person_manager.get_income_history('Robin', months=6)
        
        assert len(history) == 3
        assert history[0]['month'] == '2025-01'
        assert history[0]['amount'] == 30000.0
        assert history[1]['month'] == '2025-02'
        assert history[1]['amount'] == 32000.0
    
    def test_get_person_spending_by_category(self, person_manager, temp_yaml_dir):
        """Test retrieving spending breakdown by category for a person."""
        from datetime import datetime, timedelta
        
        person_manager.add_person(name="Robin", monthly_income=30000.0)
        
        # Create recent dates for testing
        recent_date1 = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        recent_date2 = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        recent_date3 = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        
        # Create some credit card data with allocations
        cc_data = {
            'credit_cards': [
                {
                    'name': 'Test Card',
                    'allocations': {
                        'Robin': 0.6,
                        'Evelina': 0.4
                    },
                    'transactions': [
                        {'date': recent_date1, 'amount': -1000.0, 'category': 'Mat & Dryck'},
                        {'date': recent_date2, 'amount': -500.0, 'category': 'Transport'},
                        {'date': recent_date3, 'amount': -2000.0, 'category': 'Mat & Dryck'},
                    ]
                }
            ]
        }
        cc_file = os.path.join(temp_yaml_dir, 'credit_cards.yaml')
        with open(cc_file, 'w') as f:
            yaml.dump(cc_data, f)
        
        spending = person_manager.get_person_spending_by_category('Robin', months=6)
        
        # Robin should get 60% of each category
        assert 'Mat & Dryck' in spending
        assert spending['Mat & Dryck'] == 1800.0  # (1000 + 2000) * 0.6
        assert 'Transport' in spending
        assert spending['Transport'] == 300.0  # 500 * 0.6
    
    def test_update_expected_payout(self, person_manager):
        """Test updating expected payout for a specific month."""
        person_manager.add_person(name="Robin", monthly_income=30000.0)
        
        result = person_manager.update_expected_payout(
            person_name="Robin",
            month="2025-12",
            expected_amount=35000.0
        )
        
        assert result['person'] == "Robin"
        assert result['month'] == "2025-12"
        assert result['expected_amount'] == 35000.0
        
        # Verify it was saved
        expected = person_manager.get_expected_payout("Robin", "2025-12")
        assert expected == 35000.0
    
    def test_get_expected_payout_nonexistent(self, person_manager):
        """Test getting expected payout for non-existent person or month."""
        person_manager.add_person(name="Robin", monthly_income=30000.0)
        
        # Non-existent month
        expected = person_manager.get_expected_payout("Robin", "2025-12")
        assert expected is None
        
        # Non-existent person
        expected = person_manager.get_expected_payout("Unknown", "2025-12")
        assert expected is None
