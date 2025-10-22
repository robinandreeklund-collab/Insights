"""Unit tests for AI trainer module."""

import pytest
import os
import tempfile
import shutil
from modules.core.ai_trainer import AITrainer


class TestAITrainer:
    """Test cases for AI trainer module."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.trainer = AITrainer(yaml_dir=self.test_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_initialization(self):
        """Test AITrainer initialization."""
        assert self.trainer.yaml_dir == self.test_dir
        assert os.path.exists(self.test_dir)
    
    def test_get_training_data_empty(self):
        """Test getting training data when empty."""
        data = self.trainer.get_training_data()
        assert data == []
    
    def test_add_training_sample(self):
        """Test adding a training sample."""
        self.trainer.add_training_sample(
            description="ICA Supermarket",
            category="Mat & Dryck",
            subcategory="Matinköp"
        )
        
        data = self.trainer.get_training_data()
        assert len(data) == 1
        assert data[0]['description'] == "ICA Supermarket"
        assert data[0]['category'] == "Mat & Dryck"
        assert data[0]['subcategory'] == "Matinköp"
        assert data[0]['manual'] is True
    
    def test_get_training_stats_empty(self):
        """Test getting stats when no training data."""
        stats = self.trainer.get_training_stats()
        assert stats['total_samples'] == 0
        assert stats['manual_samples'] == 0
        assert stats['ready_to_train'] is False
    
    def test_get_training_stats_with_data(self):
        """Test getting stats with training data."""
        self.trainer.add_training_sample("ICA", "Mat & Dryck", "Matinköp")
        self.trainer.add_training_sample("Coop", "Mat & Dryck", "Matinköp")
        
        stats = self.trainer.get_training_stats()
        assert stats['total_samples'] == 2
        assert stats['manual_samples'] == 2
        assert stats['ready_to_train'] is True
        assert 'Mat & Dryck' in stats['categories']
        assert stats['categories']['Mat & Dryck'] == 2
    
    def test_extract_keywords(self):
        """Test keyword extraction."""
        keywords = self.trainer.extract_keywords("ICA Supermarket Örebro")
        assert 'ica' in keywords
        assert 'supermarket' in keywords
        assert 'örebro' in keywords
    
    def test_train_from_samples_insufficient_data(self):
        """Test training with insufficient samples."""
        self.trainer.add_training_sample("ICA", "Mat & Dryck", "Matinköp")
        
        result = self.trainer.train_from_samples()
        assert result['success'] is False
        assert 'Need at least' in result['message']
        assert result['rules_created'] == 0
    
    def test_train_from_samples_success(self):
        """Test successful training."""
        self.trainer.add_training_sample("ICA Supermarket", "Mat & Dryck", "Matinköp")
        self.trainer.add_training_sample("Coop Konsum", "Mat & Dryck", "Matinköp")
        self.trainer.add_training_sample("Shell Bensinstation", "Transport", "Bränsle")
        
        result = self.trainer.train_from_samples()
        assert result['success'] is True
        assert result['rules_created'] >= 1
        assert 'Mat & Dryck' in result['categories_trained'] or 'Transport' in result['categories_trained']
    
    def test_clear_training_data(self):
        """Test clearing training data."""
        self.trainer.add_training_sample("ICA", "Mat & Dryck", "Matinköp")
        self.trainer.add_training_sample("Coop", "Mat & Dryck", "Matinköp")
        
        assert len(self.trainer.get_training_data()) == 2
        
        self.trainer.clear_training_data()
        assert len(self.trainer.get_training_data()) == 0
    
    def test_remove_ai_generated_rules(self):
        """Test removing AI-generated rules."""
        # First, train to create some AI rules
        self.trainer.add_training_sample("ICA", "Mat & Dryck", "Matinköp")
        self.trainer.add_training_sample("Coop", "Mat & Dryck", "Matinköp")
        
        result = self.trainer.train_from_samples()
        assert result['success'] is True
        
        # Now remove AI-generated rules
        removed = self.trainer.remove_ai_generated_rules()
        assert removed >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
