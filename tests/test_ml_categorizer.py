"""Tests for ML Categorizer."""

import unittest
import os
import tempfile
import shutil
import yaml


class TestMLCategorizer(unittest.TestCase):
    """Test cases for ML categorizer."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.yaml_dir = self.test_dir
        
        # Try to import ML categorizer
        try:
            from modules.core.ml_categorizer import MLCategorizer
            self.ml_available = True
            self.categorizer = MLCategorizer(yaml_dir=self.yaml_dir)
        except ImportError:
            self.ml_available = False
            self.categorizer = None
    
    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def _create_training_data(self, num_samples=10):
        """Create sample training data."""
        training_data = []
        
        # Create samples for different categories
        categories_samples = {
            'Mat & Dryck': [
                'ICA Supermarket Stockholm',
                'Coop Konsum Malmö',
                'Restaurang Ming Göteborg',
                'Café Java Stockholm'
            ],
            'Transport': [
                'Shell Bensin Station',
                'SL Access Månadskort',
                'Circle K Diesel',
                'Parkering City P-hus'
            ],
            'Boende': [
                'Hyresbetalning Fastighet AB',
                'Elräkning Eon',
                'Hemförsäkring Folksam'
            ]
        }
        
        for category, descriptions in categories_samples.items():
            for desc in descriptions[:num_samples]:
                training_data.append({
                    'description': desc,
                    'category': category,
                    'subcategory': '',
                    'manual': True,
                    'added_at': '2025-01-01 12:00:00'
                })
        
        # Save training data
        training_file = os.path.join(self.yaml_dir, 'training_data.yaml')
        with open(training_file, 'w', encoding='utf-8') as f:
            yaml.dump({'training_data': training_data}, f)
        
        return training_data
    
    def test_initialization(self):
        """Test ML categorizer initialization."""
        if not self.ml_available:
            self.skipTest("ML features not available (scikit-learn not installed)")
        
        self.assertIsNotNone(self.categorizer)
        self.assertEqual(self.categorizer.yaml_dir, self.yaml_dir)
        self.assertFalse(self.categorizer.is_trained)
    
    def test_train_with_insufficient_data(self):
        """Test training with insufficient data."""
        if not self.ml_available:
            self.skipTest("ML features not available")
        
        result = self.categorizer.train()
        self.assertFalse(result['success'])
        self.assertIn('Need at least 2 training samples', result['message'])
    
    def test_train_with_sufficient_data(self):
        """Test training with sufficient data."""
        if not self.ml_available:
            self.skipTest("ML features not available")
        
        self._create_training_data(num_samples=5)
        
        result = self.categorizer.train()
        self.assertTrue(result['success'])
        self.assertGreater(result['samples_used'], 0)
        self.assertGreater(len(result['categories']), 0)
        self.assertTrue(self.categorizer.is_trained)
    
    def test_predict_without_training(self):
        """Test prediction without training."""
        if not self.ml_available:
            self.skipTest("ML features not available")
        
        result = self.categorizer.predict('ICA Supermarket')
        self.assertIsNone(result)
    
    def test_predict_after_training(self):
        """Test prediction after training."""
        if not self.ml_available:
            self.skipTest("ML features not available")
        
        self._create_training_data(num_samples=5)
        self.categorizer.train()
        
        # Test predictions
        result = self.categorizer.predict('ICA Maxi Stockholm')
        self.assertIsNotNone(result)
        self.assertIn('category', result)
        self.assertEqual(result['method'], 'ml')
    
    def test_predict_with_confidence(self):
        """Test prediction with confidence score."""
        if not self.ml_available:
            self.skipTest("ML features not available")
        
        self._create_training_data(num_samples=5)
        self.categorizer.train()
        
        result = self.categorizer.predict('ICA Supermarket', return_probability=True)
        self.assertIsNotNone(result)
        self.assertIn('confidence', result)
        self.assertGreater(result['confidence'], 0)
        self.assertLessEqual(result['confidence'], 1)
    
    def test_model_persistence(self):
        """Test model saving and loading."""
        if not self.ml_available:
            self.skipTest("ML features not available")
        
        self._create_training_data(num_samples=5)
        self.categorizer.train()
        
        # Create new categorizer instance - should load existing model
        from modules.core.ml_categorizer import MLCategorizer
        new_categorizer = MLCategorizer(yaml_dir=self.yaml_dir)
        
        self.assertTrue(new_categorizer.is_trained)
        self.assertEqual(len(new_categorizer.categories), len(self.categorizer.categories))
    
    def test_get_model_info(self):
        """Test getting model information."""
        if not self.ml_available:
            self.skipTest("ML features not available")
        
        self._create_training_data(num_samples=5)
        self.categorizer.train()
        
        info = self.categorizer.get_model_info()
        self.assertTrue(info['is_trained'])
        self.assertGreater(info['total_samples'], 0)
        self.assertGreater(info['num_categories'], 0)
        self.assertTrue(info['model_file_exists'])


if __name__ == '__main__':
    unittest.main()
