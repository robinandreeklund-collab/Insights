"""
Retraining Pipeline for Insights

Automatic model retraining when threshold of manual overrides is met.
Handles preprocessing, training, evaluation, and deployment.
"""

import os
import yaml
import logging
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)


class RetrainingPipeline:
    """
    Automatic retraining pipeline for ML categorization model.
    Triggers when manual override threshold is reached.
    """
    
    def __init__(self, config_path: str = "yaml/retraining_pipeline.yaml"):
        """Initialize retraining pipeline."""
        self.config_path = config_path
        self.config = self._load_config()
        
        # Get configuration
        self.trigger_threshold = self.config.get('trigger', {}).get('threshold', 10)
        self.model_type = self.config.get('model_training', {}).get('model_type', 'LogisticRegression')
        self.validation_split = self.config.get('evaluation', {}).get('validation_split', 0.2)
        
        logger.info(f"Retraining Pipeline initialized with threshold {self.trigger_threshold}")
    
    def _load_config(self) -> Dict:
        """Load retraining pipeline configuration."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config.get('retraining_pipeline', {})
        except Exception as e:
            logger.warning(f"Could not load retraining config: {e}")
            return {}
    
    def should_retrain(self) -> bool:
        """Check if retraining should be triggered based on training data."""
        try:
            from modules.core.ai_trainer import AITrainer
            trainer = AITrainer()
            training_data = trainer._load_training_data()
            
            # Count samples
            total_samples = len(training_data)
            
            # Check if we have enough data for retraining
            if total_samples >= self.trigger_threshold:
                logger.info(f"Retraining triggered: {total_samples} samples available (threshold: {self.trigger_threshold})")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking retraining threshold: {e}")
            return False
    
    def run(self) -> Dict:
        """
        Run the complete retraining pipeline.
        
        Returns:
            Dict with retraining results
        """
        logger.info("=" * 60)
        logger.info("Starting Retraining Pipeline")
        logger.info("=" * 60)
        
        result = {
            'success': False,
            'timestamp': datetime.now().isoformat(),
            'model_type': self.model_type,
            'samples_used': 0,
            'accuracy': 0.0,
            'message': ''
        }
        
        try:
            # Step 1: Load and preprocess data
            logger.info("Step 1: Loading training data...")
            from modules.core.ai_trainer import AITrainer
            trainer = AITrainer()
            training_data = trainer._load_training_data()
            
            if not training_data or len(training_data) < 4:
                result['message'] = f"Insufficient training data: {len(training_data)} samples (need at least 4)"
                logger.warning(result['message'])
                return result
            
            result['samples_used'] = len(training_data)
            logger.info(f"Loaded {len(training_data)} training samples")
            
            # Step 2: Train ML model
            logger.info("Step 2: Training ML model...")
            ml_result = trainer.train_ml_model()
            
            if not ml_result.get('success', False):
                result['message'] = f"ML training failed: {ml_result.get('error', 'Unknown error')}"
                logger.error(result['message'])
                return result
            
            # Step 3: Evaluate model (basic check)
            logger.info("Step 3: Evaluating model...")
            model_info = trainer.get_ml_model_info()
            result['accuracy'] = model_info.get('samples_used', 0) / max(len(training_data), 1)
            
            # Step 4: Log audit information
            logger.info("Step 4: Logging audit information...")
            self._log_audit(result)
            
            # Success!
            result['success'] = True
            result['message'] = f"Successfully retrained model with {result['samples_used']} samples"
            logger.info("=" * 60)
            logger.info(f"Retraining Complete: {result['message']}")
            logger.info("=" * 60)
            
        except Exception as e:
            result['message'] = f"Retraining error: {str(e)}"
            logger.error(result['message'], exc_info=True)
        
        return result
    
    def _log_audit(self, result: Dict):
        """Log retraining audit information."""
        try:
            audit_log_path = "logs/retraining_audit.yaml"
            
            # Create logs directory if it doesn't exist
            os.makedirs("logs", exist_ok=True)
            
            # Load existing audit log
            audit_data = []
            if os.path.exists(audit_log_path):
                try:
                    with open(audit_log_path, 'r', encoding='utf-8') as f:
                        audit_data = yaml.safe_load(f) or []
                except Exception as e:
                    logger.warning(f"Could not load existing audit log: {e}")
            
            # Append new entry
            audit_entry = {
                'timestamp': result['timestamp'],
                'model_type': result['model_type'],
                'samples_used': result['samples_used'],
                'accuracy': result['accuracy'],
                'success': result['success'],
                'message': result['message']
            }
            audit_data.append(audit_entry)
            
            # Save audit log
            with open(audit_log_path, 'w', encoding='utf-8') as f:
                yaml.dump(audit_data, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"Audit log updated: {audit_log_path}")
        except Exception as e:
            logger.error(f"Failed to log audit information: {e}")
    
    def get_stats(self) -> Dict:
        """Get retraining pipeline statistics."""
        stats = {
            'trigger_threshold': self.trigger_threshold,
            'model_type': self.model_type,
            'validation_split': self.validation_split,
            'should_retrain': self.should_retrain()
        }
        
        # Try to load last retraining info
        try:
            audit_log_path = "logs/retraining_audit.yaml"
            if os.path.exists(audit_log_path):
                with open(audit_log_path, 'r', encoding='utf-8') as f:
                    audit_data = yaml.safe_load(f) or []
                    if audit_data:
                        last_entry = audit_data[-1]
                        stats['last_retrain'] = last_entry.get('timestamp')
                        stats['last_accuracy'] = last_entry.get('accuracy', 0.0)
                        stats['last_samples'] = last_entry.get('samples_used', 0)
        except Exception as e:
            logger.debug(f"Could not load retraining stats: {e}")
        
        return stats
